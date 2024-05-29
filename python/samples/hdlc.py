# HDLC/SDLC protocol sample
# - send data in main thread
# - receive data in receive thread
#
# == Single Port Use ==
# Connect data and clock outputs to data and clock inputs with
# loopback plug or external cabling. Alternatively, set
# settings.internal_loopback = True.
#
# == Two Port Use ==
# Connect ports with crossover cable that:
# - connects data output of each port to data input of other port
# - connects clock output of one port to clock inputs of both ports
# Run sample on both ports.

import sys
import threading

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port

run = True

# frame size sent in this sample
FRAME_SIZE = 100

def receive_thread_func():
    i = 1
    while run:
        # HDLC ignores read size argument, protocol dictates
        # returned buffer size which always contains one frame.
        buf = port.read()
        if not buf:
            break
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' + 
                str(len(buf)) + ' bytes\n', end='')
        i += 1


# port name format
# PCI: /dev/ttySLGx, x=adapter number
# USB: /dev/ttyUSBx, x=adapter number
if len(sys.argv) < 2:
    # no port name on command line, use first enumerated port
    names = Port.enumerate()
    if not names:
        print('no ports available')
        exit()
    port = Port(names[0])
else:
    port = Port(sys.argv[1])
print('HDLC/SDLC sample running on', port.name)

try:
    port.open()
except FileNotFoundError:
    print('port not found')
    exit()
except PermissionError:
    print('access denied or port in use')
    exit()
except OSError:
    print('open error')
    exit()

if port.name.find('USB') != -1:
    # uncomment to select USB interface (RS232,V35,RS422)
    # port.interface = Port.RS422
    if port.interface == Port.OFF:
        print('USB serial interface must be selected.')
        exit()

# If default 14.7456MHz base clock does not allow exact
# internal clock generation of desired rate, uncomment these lines and
# select a new base clock sourced from the frequency synthesizer.
# PCI Express/USB only. See API manual for details.
# fsynth_rate = 16000000
# if port.set_fsynth_rate(fsynth_rate):
#     print('base clock set to', fsynth_rate)
# else:
#     print(fsynth_rate, 'not supported by fsynth')
#     exit()

settings = Port.Settings()
settings.protocol = Port.HDLC
settings.encoding = Port.NRZ
settings.crc = Port.CRC16
settings.transmit_clock = Port.TXC_INPUT
settings.receive_clock = Port.RXC_INPUT
settings.internal_clock_rate = 2400
port.apply_settings(settings)

port.transmit_idle_pattern = 0x7e

print('press Ctrl-C to stop program')

port.enable_receiver()
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
        port.write(buf)
        port.flush()
        i += 1
except KeyboardInterrupt:
    run = False

port.close()