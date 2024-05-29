# raw synchronous protocol sample
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
import time

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port


# size of data sent in this sample
DATA_SIZE = 32

# True = continuous send data (no idle between writes)
# False = bursts of data (zeros) separated by idle (ones)
CONTINUOUS_SEND = True

run = True


def display_buf(buf: bytearray):
    """display a buffer of data in hex format, 16 bytes per line"""
    output = ''
    size = len(buf)
    for i in range(0, size):
        if not (i % 16):
            output += '{:0>9x}'.format(i) + ': '
        if i % 16 == 15:
            output += '{:0>2x}'.format(buf[i]) + '\n'
        else:
            output += '{:0>2x}'.format(buf[i]) + ' '
    if size % 16:
        output += '\n'
    print(output, end='')


# Raw mode saves a bit every clock cycle without distinguishing
# between data/idle/noise. There is no framing or byte alignment.
# Sample data = all 0. Idle pattern = all 1.
# Data is shifted 0-7 bits with bytes possibly spanning 2
# read buffer bytes. Serial bit order is LSB first.
def receive_thread_func():
    i = 1
    while run:
        buf = port.read(DATA_SIZE)
        if not buf:
            break
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' + 
              str(len(buf)) + ' bytes\n', end='')
        display_buf(buf)
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
print('raw bitstream sample running on', port.name)

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
    port.interface = Port.RS422
    if port.interface == Port.OFF:
        print('interface disabled, select interface and try again')
        exit()

# If default 14.7456MHz base clock does not allow exact
# internal clock generation of desired rate, uncomment these lines and
# select a new base clock sourced from the frequency synthesizer.
# PCI Express/USB only. See API manual for details.
# fsynth_rate = 10000000
# if port.set_fsynth_rate(fsynth_rate):
#     print('base clock set to', fsynth_rate)
# else:
#     print(fsynth_rate, 'not supported by fsynth')
#     exit()

settings = Port.Settings()
settings.protocol = Port.RAW
settings.encoding = Port.NRZ
settings.crc = Port.OFF
settings.transmit_clock = Port.TXC_INPUT
settings.receive_clock = Port.RXC_INPUT
settings.internal_clock_rate = 10022400
settings.internal_loopback = True
port.apply_settings(settings)

# print settings

print(port.get_settings())

# send all ones when no data is available
port.transmit_idle_pattern = 0x55

# set receive data transfer size: range=1-256, default=256
# < 128  : programmed I/O (PIO), low data rate
# >= 128 : direct memory access (DMA), MUST be multiple of 4
# Lower values reduce receive latency (time from receiving data
# until it becomes available to system) but increase overhead.
port.receive_transfer_size = 8

# set transmit data transfer mode
if CONTINUOUS_SEND:
    port.transmit_transfer_mode = Port.PIO
else:
    port.transmit_transfer_mode = Port.DMA

print('press Ctrl-C to stop program')

port.enable_receiver()
receive_thread = threading.Thread(target=receive_thread_func)
receive_thread.start()

# sample data = all 0
buf = bytearray(DATA_SIZE)
for i in range(0, len(buf)):
    buf[i] = 0x55

i = 1
try:
    while run:
        print('>>> ' + '{:0>9d}'.format(i) + ' send ' +
            str(len(buf)) + ' bytes\n', end='')
        port.write(buf)
        if CONTINUOUS_SEND:
			# prevent idle by keeping send count > 0
			# limit latency by keeping send count < 2*DATA_SIZE
			# latency = time from write to serial data output
            print('>>> wait for send count <= ' +
                str(DATA_SIZE) + '\n', end='')
            while port.transmit_count() > DATA_SIZE:
                time.sleep(0.005)
        else:
            # block until all sent to insert idle between data
            port.flush()
            time.sleep(0.025)
        i += 1
except KeyboardInterrupt:
    run = False

port.close()