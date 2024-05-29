# Time Division Multiplexing (TDM) sample
#
# Data is sent continuously in main thread.
# Data is received continuously in receive thread.
#
# Use a single port with external cabling to loop back
# signals as described below or connect two ports (both running
# this sample) with external cabling that connects the outputs of
# one port to the inputs of the other port as described below.
#
# WARNING:
# The loopback plug supplied with the SyncLink device is not compatible with
# this sample code. The following connections are required:
# 
# Outputs     Inputs
# TxD     --> RxD (send data output to receive data input)
# RTS     --> DCD (sync pulse output to sync pulse input)
# AUXCLK  --> RxC (send clock output to receive clock input)

import sys
import threading

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port


# get_slot()/set_slot() access individual slots in buffer
#
# - slot may not be integer number of bytes in length
# - slot is stored in integer number of bytes in buffer
# - slot is stored in little endian order in buffer
# - unused most significant bits of slot buffer storage are zero
# 
# example:
# 12-bit slot value 0x123 uses 2 buffer bytes: byte[0]=0x23, byte[1]=0x01
# with the unused most significant 4 bits of byte[1] set to 0

def buffer_bytes_per_slot(bits_per_slot:int) -> int:
    """Return number of bytes needed to store one slot."""
    buffer_bytes_per_slot = int(bits_per_slot/8)
    if bits_per_slot % 8:
        buffer_bytes_per_slot += 1
    return buffer_bytes_per_slot

def get_slot(buf:bytearray, slot_index:int, bits_per_slot:int) -> int:
    """Return slot value from buffer."""
    bytes_per_slot = buffer_bytes_per_slot(bits_per_slot)
    first_byte = bytes_per_slot * slot_index
    value = 0
    for i in range(0, bytes_per_slot):
        value += buf[first_byte + i] << (i * 8)
    return value

def set_slot(buf:bytearray, slot_index:int, bits_per_slot:int, value:int):
    """Set slot value in buffer."""
    bytes_per_slot = buffer_bytes_per_slot(bits_per_slot)
    first_byte = bytes_per_slot * slot_index
    for i in range(0, bytes_per_slot):
        buf[first_byte + i] = (value >> (i * 8)) & 0xff


def receive_thread_func():
    i = 1
    while True:
        # get tdm_frame_count frames
        buf = port.read()
        if not buf:
            break
        print('<<< ' + '{:0>9d}'.format(i) + ' received ' + 
                str(len(buf)) + ' bytes\n', end='')

        if len(buf) != send_size:
            print('<<< ' + 'received length != sent length')
        else:
            # verify received data matches sent data
            for frame in range(0, settings.tdm_frame_count):
                for slot in range(0, settings.tdm_slot_count):
                    index = frame * settings.tdm_slot_count + slot
                    received = get_slot(buf, index, settings.tdm_slot_bits)
                    sent = get_slot(send_buf, index, settings.tdm_slot_bits)
                    if received != sent:
                        print('<<< ERROR frame #' + str(frame + 1) +
                        ' slot #' + str(slot + 1) + ' sent=' + hex(sent) +
                        ' received=' + hex(received) + '\n', end='')
        i += 1


# port name format
# single port adapter: MGHDLCx, x=adapter number
# multiport adapter: MGMPxPy, x=adapter number, y=port number
if len(sys.argv) < 2:
    # no port name on command line, use first enumerated port
    names = Port.enumerate()
    if not names:
        print('no ports available')
        exit()
    port = Port(names[0])
else:
    port = Port(sys.argv[1])
print('TDM sample running on', port.name)

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
settings.protocol = Port.TDM
settings.tdm_sync_frame = False
settings.tdm_sync_delay = 0
settings.tdm_sync_short = False
settings.tdm_sync_invert = False
settings.tdm_frame_count = 10
settings.tdm_slot_bits = 32
settings.tdm_slot_count = 4
settings.msb_first = True
# encoding sets data signal polarity: NRZ=normal, NRZB=inverted
settings.encoding = Port.NRZ
settings.crc = Port.OFF
settings.transmit_clock = Port.INTERNAL
settings.transmit_clock_invert = False
settings.receive_clock = Port.RXC_INPUT
settings.receive_clock_invert = False
settings.internal_clock_rate = 9600
port.apply_settings(settings)

print('press Ctrl-C to stop program')

port.enable_receiver()
receive_thread = threading.Thread(target=receive_thread_func)
receive_thread.start()

# prepare bytearray containing configured number of frames
# tdm_frame_count = count of frames returned by read()
# tdm_slot_count = slots per frame
# tdm_slot_bits = bits per slot (round to integer count of bytes)
#
# write() sends one or more frames (total size must be <= 64K bytes).
# tdm_frame_count only applies to read().
# This sample sends tdm_frame_count frames per write() to keep
# write() and read() loop counts equal.
# send_size MUST be <= port.max_data_size

send_size = settings.tdm_frame_count * settings.tdm_slot_count * \
            buffer_bytes_per_slot(settings.tdm_slot_bits)
send_buf = bytearray(send_size)
for slot in range(0, settings.tdm_frame_count * settings.tdm_slot_count):
    set_slot(send_buf, slot, settings.tdm_slot_bits, 0x12345678)

i = 1
try:
    while True:
        print('>>> ' + '{:0>9d}'.format(i) + ' send ' +
            str(len(send_buf)) + ' bytes\n', end='')
        port.write(send_buf)
        port.flush()
        i += 1
except KeyboardInterrupt:
    print('Ctrl-C pressed')
    port.close()