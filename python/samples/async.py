# asynchronous/isochronous protocol sample
# - send data in main thread
# - receive data in receive thread
#
# == Single Port Use ==
# Connect TxD data output to RxD data input with
# loopback plug or external cabling. Alternatively, set
# settings.internal_loopback = True.
#
# == Two Port Use ==
# Connect ports with crossover cable that:
# - connects data output of each port to data input of other port
# Run sample on both ports.
#
# Edit ISOCHRONOUS constant below to select isochronous protocol.
# Isochronous uses async framing with an external clock. When using
# isochronous, the clock output (transmit clock) must be connected
# to the RxC clock input.

import sys
import threading

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port

run = True

# set this to True to use isochronous protocol
# or False to use asynchronous protocol
ISOCHRONOUS = False

# bytes per read/write used in sample
DATA_SIZE = 100


def receive_thread_func():
    i = 1
    while run:
        buf = port.read(DATA_SIZE)
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
if (ISOCHRONOUS):
    print('isochronous sample running on', port.name)
else:
    print('asynchronous sample running on', port.name)

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
    # uncomment to select interface for USB (RS232,V35,RS422)
    # port.interface = Port.RS422
    if port.interface == Port.OFF:
        print('interface disabled, select interface and try again')
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
settings.protocol = Port.ASYNC
settings.async_data_bits = 8
settings.async_stop_bits = 1
settings.async_parity = Port.OFF
if ISOCHRONOUS:
    # async_data_rate of 0 = isochronous (external clock)
    settings.async_data_rate = 0
    # receiver uses external clock on RxC input
    settings.receive_clock = Port.RXC_INPUT
    # generate clock on AUXCLK output (connect to RxC input)
    # use generated clock as transmit clock
    settings.internal_clock_rate = 2400
    settings.transmit_clock = Port.INTERNAL
else:
    settings.async_data_rate = 2400
port.apply_settings(settings)

# set receive data transfer size: range=1-256, default=256
# < 128  : programmed I/O (PIO), low data rate
# >= 128 : direct memory access (DMA), MUST be multiple of 4
# Lower values reduce receive latency (time from receiving data
# until it becomes available to system) but increase overhead.
#
# NOTE: async/isoch transfers 2 bytes per character (data + status)
# so a value of 2 transfers each character as it is received.
port.receive_transfer_size = 2

# read waits for at least this much data
port.min_read_size = DATA_SIZE

print('press Ctrl-C to stop program')

port.enable_receiver()
receive_thread = threading.Thread(target=receive_thread_func)
receive_thread.start()

# prepare send buffer
buf = bytearray(DATA_SIZE)
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