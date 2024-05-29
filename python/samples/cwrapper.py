# Loop HDLC data on SyncLink device.
# 
# Use with loopback plug or cable or configure port
# for internal loopback.


import os
import sys
import fcntl
import termios
import threading
import ctypes

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
import mgapi

# Default max frame size for driver.
# This can be increased with driver load option.
MAX_FRAME_SIZE = 4096

# size of frames sent in this sample
FRAME_SIZE = 100

run = True


def check_interface(fd):
    """Verify serial interface is enabled."""
    interface = ctypes.c_int()
    try:
        # get current interface
        fcntl.ioctl(fd, mgapi.MGSL_IOCGIF, interface, True)
    except OSError as e:
        print('ioctl(mgapi.MGSL_IOCGIF) error =', e.errno, e.strerror)
        exit(e.errno)
    
    # set current interface
    # interface.value &= ~mgapi.MGSL_INTERFACE_MASK
    # interface.value |= mgapi.MGSL_INTERFACE_RS422
    # try:
    #     fcntl.ioctl(fd, mgapi.MGSL_IOCSIF, interface.value)
    # except OSError as e:
    #     print('ioctl(mgapi.MGSL_IOCSIF) error =', e.errno, e.strerror)
    #     exit(e.errno)

    if not (interface.value & mgapi.MGSL_INTERFACE_MASK):
        print('Serial interface must be selected.')
        exit(1)

def configure_port(fd):
    # Set line discipline, a software layer between tty devices
    # and user applications that performs intermediate processing.
    # N_HDLC = frame oriented line discipline
    N_HDLC = 13
    ldisc = ctypes.c_int(N_HDLC)
    try:
        fcntl.ioctl(fd, termios.TIOCSETD, ldisc)
    except OSError as e:
        print('ioctl(TIOCSETD) error =', e.errno, e.strerror)
        exit(e.errno)

    # get current device parameters
    params = mgapi.MGSL_PARAMS()
    try:
        fcntl.ioctl(fd, mgapi.MGSL_IOCGPARAMS, params, True)
    except OSError as e:
        print('ioctl(mgapi.MGSL_IOCGPARAMS) error =', e.errno, e.strerror)
        exit(e.errno)

    # modify device parameters
    params.mode = mgapi.MGSL_MODE_HDLC
    params.encoding = mgapi.HDLC_ENCODING_NRZ
    params.crc_type = mgapi.HDLC_CRC_16_CCITT
    params.loopback = False
    params.flags = mgapi.HDLC_FLAG_RXC_RXCPIN + mgapi.HDLC_FLAG_TXC_TXCPIN
    params.clock_speed = 2400

    # set current device parameters
    try:
        fcntl.ioctl(fd, mgapi.MGSL_IOCSPARAMS, params)
    except OSError as e:
        print('ioctl(mgapi.MGSL_IOCSPARAMS) error =', e.errno, e.strerror)
        exit(e.errno)

    # set transmit idle pattern (sent between frames)
    try:
        fcntl.ioctl(fd, mgapi.MGSL_IOCSTXIDLE, mgapi.HDLC_TXIDLE_FLAGS)
    except OSError as e:
        print('ioctl(mgapi.MGSL_IOCSTXIDLE) error =', e.errno, e.strerror)
        exit(e.errno)

    # set receive data transfer size: range=1-256, default=256
    # HDLC protocol must use default 256.
    try:
        fcntl.ioctl(fd, mgapi.MGSL_IOCRXENABLE, 256 << 16)
    except OSError as e:
        print('ioctl(mgapi.MGSL_IOCRXENABLE) error =', e.errno, e.strerror)
        exit(e.errno)

    # set device to blocking mode for reads and writes
    file_flags = fcntl.fcntl(fd, fcntl.F_GETFL) & ~os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, file_flags)


def receive_thread_func():
    global run, fd
    i = 1
    while run:
        try:
            buf = os.read(fd, MAX_FRAME_SIZE)
        except:
            break
        if not buf:
            break
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' + 
              str(len(buf)) + ' bytes\n', end='')
        i += 1


# port names:
# /dev/ttySLGx for PCI cards, x = port number
# /dev/ttyUSBx for USB device, x = port number
if len(sys.argv) < 2:
    port_name = '/dev/ttySLG0'
else:
    port_name = sys.argv[1]
print('C Wrapper HDLC/SDLC sample running on', port_name)

# open serial device with O_NONBLOCK to ignore DCD input
try:
    fd = os.open(port_name, os.O_RDWR | os.O_NONBLOCK)
except OSError as e:
    print('open error =', e.errno, e.strerror)
    exit(e.errno)

# USB device has software selectable serial interface
if port_name.find('ttyUSB') != -1:
    check_interface(fd)

configure_port(fd)

print('press Ctrl-C to stop program')

# enable receiver and start receive thread
try:
    fcntl.ioctl(fd, mgapi.MGSL_IOCRXENABLE, True)
except OSError as e:
    print('ioctl(mgapi.MGSL_IOCRXENABLE) error =', e.errno, e.strerror)
    exit(e.errno)
receive_thread = threading.Thread(target=receive_thread_func)
receive_thread.start()

# prepare send buffer
buf = bytearray(FRAME_SIZE)
for i in range(0, len(buf)):
    buf[i] = i & 0xff

try:
    i = 1
    while run:
        print('>>> ' + '{:0>9d}'.format(i) + ' send ' +
            str(len(buf)) + ' bytes\n', end='')
        if os.write(fd, buf) != len(buf):
            break
        # block until all data sent
        termios.tcdrain(fd)
        i += 1
except:
    run = False

os.close(fd)
