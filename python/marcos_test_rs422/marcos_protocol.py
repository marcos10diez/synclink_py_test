from mgapi import Port

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

class SerialProtocolPort:
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
                    print(f"Received packet header: {header}")
                    print(f"Received packet data: {data}")
                    # Procesar el paquete aquí
        except KeyboardInterrupt:
            print("Stopped by user")