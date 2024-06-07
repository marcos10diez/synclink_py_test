import sys
import threading
import time
import logging

# Configurar logging para mostrar mensajes en la terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    print(output)

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
    
    def __init__(self, port, settings=default_settings(), continuous_send=True):
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
        self.port.timeout = 1  # Añadir tiempo de espera de 1 segundo para las lecturas

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
        logging.debug(f"Sent packet: {packet.hex()}")  # Mensaje de depuración

    def end_transmission(self):
        self.port.write(bytearray([self.start_end_byte]))

    def receive_data(self):
        while True:
            try:
                data = self.port.read(self.packet_size)
                if not data:
                    continue
                self.buffer.extend(data)

                # Mantener el buffer para la búsqueda del byte de inicio y procesamiento del paquete completo
                while len(self.buffer) >= self.packet_size + 2:
                    # Buscar el byte de inicio
                    start_index = self.buffer.find(self.start_end_byte)
                    if start_index == -1:
                        # No se encontró el byte de inicio, descartar solo los primeros bytes
                        self.buffer = self.buffer[-(self.packet_size + 2):]
                        break

                    if start_index > 0:
                        # Eliminar bytes antes del byte de inicio
                        self.buffer = self.buffer[start_index:]

                    # Verificar si hay suficientes datos para un paquete completo + byte de fin
                    if len(self.buffer) < self.packet_size + 2:
                        break  # No hay suficientes datos para un paquete completo + byte de fin

                    # Verificar el byte de fin de transmisión
                    end_index = self.packet_size + 1
                    if self.buffer[end_index] == self.start_end_byte:
                        # Extraer datos del paquete
                        packet_data = self.buffer[1:self.packet_size + 1]
                        yield packet_data[:self.header_size], packet_data[self.header_size:]

                        # Eliminar el paquete procesado y el byte de fin del buffer
                        self.buffer = self.buffer[end_index + 1:]
                    else:
                        # Si no se encontró el byte de fin, eliminar solo el primer byte y continuar
                        self.buffer = self.buffer[1:]
            except Exception as e:
                logging.error(f"Error in receive_data: {e}")  # Mensaje de depuración

    def run(self):
        try:
            while True:
                for header, data in self.receive_data():
                    print(f"Received packet header: \n")
                    display_buf(header)
                    print("\n\n")
                    print(f"Received packet data: \n")
                    display_buf(data)
                    print("\n\n")
                    # Procesar el paquete aquí
        except KeyboardInterrupt:
            logging.info("Stopped by user")

def receive_thread_func(serial_protocol_port):
    while run:
        serial_protocol_port.run()

# Ejemplo de uso
if __name__ == "__main__":
    run = True
    # port name format
    # PCI: /dev/ttySLGx, x=adapter number
    # USB: /dev/ttyUSBx, x=adapter number
    if len(sys.argv) < 2:
        # no port name on command line, use first enumerated port
        names = Port.enumerate()
        if not names:
            logging.error('no ports available')
            exit()
        port = Port(names[0])
    else:
        port = Port(sys.argv[1])
    logging.info('raw bitstream sample running on %s', port.name)

    try:
        port.open()
    except FileNotFoundError:
        logging.error('port not found')
        exit()
    except PermissionError:
        logging.error('access denied or port in use')
        exit()
    except OSError:
        logging.error('open error')
        exit()

    if port.name.find('USB') != -1:
        # uncomment to select interface for USB (RS232,V35,RS422)
        port.interface = Port.RS422
        if port.interface == Port.OFF:
            logging.error('interface disabled, select interface and try again')
            exit()

    serial_protocol_port = SerialProtocolPort(port)

    logging.info(serial_protocol_port.port.get_settings())

    logging.info('press Ctrl-C to stop program')

    serial_protocol_port.port.enable_receiver()
    receive_thread = threading.Thread(target=receive_thread_func, args=(serial_protocol_port,))
    receive_thread.start()

    i = 1
    header = DEFAULT_PACKET_HEADER
    data = DEFAULT_PACKET_DATA
    try:
        while run:
            serial_protocol_port.start_transmission()
            serial_protocol_port.send_packet(header, data)
            serial_protocol_port.end_transmission()
            print(f"Sent packet header: \n")
            display_buf(header)
            print("\n\n")
            print(f"Sent packet data: \n")
            display_buf(data)
            print("\n\n")
            time.sleep(5)
            i += 1
    except KeyboardInterrupt:
        run = False

    port.close()