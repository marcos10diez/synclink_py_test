# bisync/monosync protocol sample
# - send data in main thread
# - receive data in receive thread
#
# Bisync and monosync protocols are identical except the length
# of the sync pattern (bisync=16 bits, monosync=8 bits). Edit the
# settings.protocol assignment below to select protocol.
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
import time
import threading

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port

run = True

# True = bisync, False = monosync
BISYNC = True

# Sample sync pattern. Actual values are application dependent.
# Bisync protocol uses 16-bit sync pattern (LSB first).
# Monosync protocol uses 8-bit sync pattern (LSB only).
SYNC_LSB = 0x67
SYNC_MSB = 0x98

# Sample block boundary patterns. Actual values are application dependent.
START_OF_BLOCK = 0x55
END_OF_BLOCK = 0xaa

BYTES_PER_READ = 8

# block size used by this sample
BLOCK_SIZE = 100

# Assemble receive data into application defined block bounded by
# start/end of block bytes. One block may span multiple read() calls.
# Sample block format will differ from actual application.
#
# - enable receiver (hardware searches for sync pattern)
# - after sync detection, read() returns data byte aligned to sync
# - call read() in loop looking for start/end of block bytes
# - on block completion, disable receiver
#
# This sample assumes blocks are not byte aligned to each other.
# The receiver is disabled after receiving a block and enabled to receive
# next block to force search for sync pattern (and byte alignment)
# for each block.
#
# Actual applications may send multiple byte aligned blocks.
# In this case the receiver remains enabled between blocks. The application
# is responsible for determining when the receiver must resync between blocks.

def receive_block(port: Port) -> bytearray:
    block = bytearray()  # assembled data block
    sob = False  # start of block flag
    eob = False  # end of block flag

    while run:
        buf = port.read(BYTES_PER_READ)
        if not buf:
            return None
        # print('<<< read ' + str(len(buf)) + ' bytes\n', end='')

        if not sob:
            sob_index = buf.find(START_OF_BLOCK)
            if sob_index == -1:
                continue
            # print('<<< start of block')
            sob = True
            buf = buf[sob_index:]  # discard leading bytes

        eob_index = buf.find(END_OF_BLOCK)
        if eob_index != -1:
            # print('<<< end of block')
            eob = True
            block.extend(buf[:eob_index+1])  # discard trailing bytes
            break

        block.extend(buf)
        if len(buf) > BLOCK_SIZE:
            # possible corrupt data or false sync
            # print('<<< block exceeds expected size')
            break

    # restart receiver to clear buffer and search for next sync
    port.disable_receiver()
    port.enable_receiver()

    if eob:
        return block
    else:
        return None


def receive_thread_func():
    i = 1
    while run:
        buf = receive_block(port)
        if not buf:
            break
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' + 
              str(len(buf)) + ' byte block\n', end='')
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
if BISYNC:
    print('bisync sample running on', port.name)
else:
    print('monosync sample running on', port.name)

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
if BISYNC:
    settings.protocol = Port.BISYNC
    settings.sync_pattern = (SYNC_MSB << 8) | SYNC_LSB
else:
    settings.protocol = Port.MONOSYNC
    settings.sync_pattern = SYNC_LSB
settings.encoding = Port.NRZ
settings.crc = Port.OFF
settings.transmit_clock = Port.TXC_INPUT
settings.receive_clock = Port.RXC_INPUT
settings.internal_clock_rate = 2400
port.apply_settings(settings)

# set receive data transfer size: range=1-256, default=256
# < 128  : programmed I/O (PIO), low data rate
# >= 128 : direct memory access (DMA), MUST be multiple of 4
# Lower values reduce receive latency (time from receiving data
# until it becomes available to system) but increase overhead.
port.receive_transfer_size = BYTES_PER_READ

print('press Ctrl-C to stop program')

port.enable_receiver()
receive_thread = threading.Thread(target=receive_thread_func)
receive_thread.start()

# prepare data block
block = bytearray(BLOCK_SIZE)
block[0] = START_OF_BLOCK
block[len(block)-1] = END_OF_BLOCK

# prepare leading sync(s)
leading_sync = bytearray()
leading_sync.append(SYNC_LSB)
if settings.protocol == Port.BISYNC:
    leading_sync.append(SYNC_MSB)

# prepare write buffer
# Application MUST prepend leading sync pattern to block.
# Some applications may require multiple leading sync patterns.
buf = leading_sync + block

i = 1
try:
    while run:
        print('>>> ' + '{:0>9d}'.format(i) + ' write ' +
            str(len(buf)) + ' bytes\n', end='')
        port.write(buf)
        port.flush()
        # disable transmitter to stop sending sync pattern
        port.disable_transmitter()
        # application specific delay to allow remote receiver to reset
        time.sleep(0.1)
        i += 1
except KeyboardInterrupt:
    run = False

port.close()
