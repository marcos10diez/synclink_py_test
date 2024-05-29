# 2-wire sample
#
# primary station usage:
# python 2wire.py mghdlc1
#
# secondary station usage:
# python 2wire.py mghdlc2 s
#
# 2-wire/bussed serial connections use a single differential pair for
# send and receive data. Clocks are recovered from the data signal.
# Only one device at a time sends. The transmit data output MUST be
# disabled to allow other devices to send.

import sys
import time

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port

# primary sends data and waits for responses
def run_primary(port):
    print('Running as primary station.')

    # prepare send buffer
    buf = bytearray(100)
    for i in range(0, len(buf)):
        buf[i] = i & 0xff

    i = 1
    while True:
        # enable outputs (RTS on) and disable receiver
        port.rts = True
        port.disable_receiver()

        print('>>> ' + '{:0>9d}'.format(i) + ' send ' +
            str(len(buf)) + ' bytes\n', end='')
        port.write(buf)
        port.flush()

        # disable outputs (RTS off) and enable receiver
        port.rts = False
        port.enable_receiver()

        print('wait for response')
        response = port.read()
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' +
            str(len(response)) + ' byte response\n', end='')

        i += 1


# secondary waits for data and sends responses
def run_secondary(port):
    print('Running as secondary station.')
    response = bytearray.fromhex('ff01')

    i = 1
    while True:
        # disable outputs (RTS off) and enable receiver
        port.rts = False
        port.enable_receiver()

        print('wait for data')
        buf = port.read()
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' +
            str(len(buf)) + ' bytes\n', end='')

        # enable outputs (RTS on) and disable receiver
        port.rts = True
        port.disable_receiver()

        print('>>> ' + '{:0>9d}'.format(i) + ' send ' +
            str(len(response)) + ' byte response\n', end='')
        port.write(response)
        port.flush()

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
print('2-wire HDLC/SDLC sample running on', port.name)

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

settings = Port.Settings()
settings.protocol = Port.HDLC
settings.encoding = Port.MANCHESTER
settings.crc = Port.CRC16
settings.transmit_clock = Port.INTERNAL
settings.receive_clock = Port.RECOVERED
settings.internal_clock_rate = 9600
settings.transmit_preamble_pattern = 0x55
settings.transmit_preamble_bits = 8
port.apply_settings(settings)

port.transmit_idle_pattern = 0x7e

# set RTS to enable/disable outputs
port.rts_output_enable = True

print('press Ctrl-C to stop program')

try:
    if len(sys.argv) < 3:
        run_primary(port)
    else:
        run_secondary(port)
except KeyboardInterrupt:
    port.rts_output_enable = False
    port.close()