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

DEFAULT_PACKET_HEADER = bytes(range(0xFF, 0xFF - 16 * 0x11, -0x11))
DEFAULT_PACKET_DATA = bytes([(i // 3) * 0x11 for i in range(48)])

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

class SerialProtocolPort:
    def default_settings():
        settings = Port.Settings()
        settings.protocol = Port.RAW
        settings.encoding = Port.NRZ
        settings.crc = Port.OFF
        settings.transmit_clock = Port.TXC_INPUT
        settings.receive_clock = Port.RXC_INPUT
        settings.internal_clock_rate = 115200
        settings.internal_loopback = False
        return settings
    
    def __init__(self, port, settings=default_settings(), continuous_send = True):
        # Default serial protocol port settings
        self.port = port
        self.settings = settings
        self.idle_byte = 0xFF
        self.start_end_byte = 0x00
        self.packet_size = 64
        self.header_size = 16
        self.data_size = 48
        self.buffer = bytearray()
        self.port.apply_settings(self.settings)
        self.port.transmit_idle_pattern = self.idle_byte
        self.port.receive_transfer_size = 64
        # set transmit data transfer mode
        if continuous_send:
            self.port.transmit_transfer_mode = Port.PIO
        else:
            self.port.transmit_transfer_mode = Port.DMA

    def start_transmission(self):
        self.port.write(bytearray([self.start_end_byte]))

    def send_packet(self, header, data):
        if len(header) != self.header_size or len(data) != self.data_size:
            raise ValueError("Invalid packet size")
        packet = header + data
        self.port.write(packet)

    def end_transmission(self):
        self.port.write(bytearray([self.start_end_byte]))

    def receive_data(self):
        while True:
            data = self.port.read(self.packet_size)
            self.buffer.extend(data)

            while len(self.buffer) >= self.packet_size:
                start_index = self.buffer.find(self.start_byte)
                if start_index == -1:
                    # No start byte found, discard leading bytes
                    self.buffer = self.buffer[-self.packet_size:]
                    break
                
                if start_index > 0:
                    # Remove leading bytes before the start byte
                    self.buffer = self.buffer[start_index:]
                
                if len(self.buffer) < self.packet_size + 1:
                    break  # Not enough data for a full packet + end byte
                
                packet_data = self.buffer[1:self.packet_size + 1]  # Extract packet data
                yield packet_data[:self.header_size], packet_data[self.header_size:]  # Return header and data separately

                if self.buffer[self.packet_size] == self.start_end_byte:
                    # If the next byte is the start byte, there's a new packet
                    self.buffer = self.buffer[self.packet_size:]
                else:
                    # Otherwise, it's the end of transmission or more idle bytes
                    self.buffer = self.buffer[self.packet_size + 1:]
                    break

    def run(self):
        try:
            while True:
                for header, data in self.receive_data():
                    print(f"Received packet header: \n")
                    display_buf(header)
                    print(f"Received packet data: \n")
                    display_buf(data)
                    # Procesar el paquete aquí
        except KeyboardInterrupt:
            print("Stopped by user")




# size of data sent in this sample
DATA_SIZE = 64

# True = continuous send data (no idle between writes)
# False = bursts of data (zeros) separated by idle (ones)
CONTINUOUS_SEND = True

run = True





# Raw mode saves a bit every clock cycle without distinguishing
# between data/idle/noise. There is no framing or byte alignment.
# Sample data = all 0. Idle pattern = all 1.
# Data is shifted 0-7 bits with bytes possibly spanning 2
# read buffer bytes. Serial bit order is LSB first.
def receive_thread_func(serial_protocol_port):
    while run:
        serial_protocol_port.run()


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

# settings = Port.Settings()
# settings.protocol = Port.RAW
# settings.encoding = Port.NRZ
# settings.crc = Port.OFF
# settings.transmit_clock = Port.TXC_INPUT
# settings.receive_clock = Port.RXC_INPUT
# settings.internal_clock_rate = 115200
# settings.internal_loopback = False
# port.apply_settings(settings)

serial_protocol_port = SerialProtocolPort(port)

# print settings

print(serial_protocol_port.port.get_settings())

# send all ones when no data is available
# port.transmit_idle_pattern = 0xFF

# set receive data transfer size: range=1-256, default=256
# < 128  : programmed I/O (PIO), low data rate
# >= 128 : direct memory access (DMA), MUST be multiple of 4
# Lower values reduce receive latency (time from receiving data
# until it becomes available to system) but increase overhead.
# port.receive_transfer_size = 8

# # set transmit data transfer mode
# if CONTINUOUS_SEND:
#     port.transmit_transfer_mode = Port.PIO
# else:
#     port.transmit_transfer_mode = Port.DMA

print('press Ctrl-C to stop program')

serial_protocol_port.port.enable_receiver()
receive_thread = threading.Thread(target=receive_thread_func)
receive_thread.start()

# # sample data = all 0
# buf = bytearray(DATA_SIZE)
# for i in range(0, len(buf)):
#     buf[i] = 0x00

i = 1
header = DEFAULT_PACKET_HEADER
data = DEFAULT_PACKET_DATA
try:
    while run:
        serial_protocol_port.send_packet(header, data)

        print(f"Sent packet header: \n")
        display_buf(header)
        print(f"Sent packet data: \n")
        display_buf(data)
        time.sleep(5)
        i += 1
except KeyboardInterrupt:
    run = False

port.close()