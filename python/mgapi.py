import ctypes
import errno
import os
import fcntl
import termios
from copy import deepcopy

HDLC_MAX_FRAME_SIZE	= 65535
MAX_ASYNC_TRANSMIT = 4096
MAX_ASYNC_BUFFER_SIZE = 4096

ASYNC_PARITY_NONE = 0
ASYNC_PARITY_EVEN = 1
ASYNC_PARITY_ODD = 2
ASYNC_PARITY_SPACE = 3

HDLC_FLAG_UNDERRUN_ABORT7 = 0x0000
HDLC_FLAG_UNDERRUN_ABORT15 = 0x0001
HDLC_FLAG_UNDERRUN_FLAG = 0x0002
HDLC_FLAG_UNDERRUN_CRC = 0x0004
HDLC_FLAG_SHARE_ZERO = 0x0010
HDLC_FLAG_AUTO_CTS = 0x0020
HDLC_FLAG_AUTO_DCD = 0x0040
HDLC_FLAG_AUTO_RTS = 0x0080
HDLC_FLAG_RXC_DPLL = 0x0100
HDLC_FLAG_RXC_BRG = 0x0200
HDLC_FLAG_RXC_TXCPIN = 0x8000
HDLC_FLAG_RXC_RXCPIN = 0x0000
HDLC_FLAG_TXC_DPLL = 0x0400
HDLC_FLAG_TXC_BRG = 0x0800
HDLC_FLAG_TXC_TXCPIN = 0x0000
HDLC_FLAG_TXC_RXCPIN = 0x0008
HDLC_FLAG_DPLL_DIV8 = 0x1000
HDLC_FLAG_DPLL_DIV16 = 0x2000
HDLC_FLAG_DPLL_DIV32 = 0x0000
HDLC_FLAG_HDLC_LOOPMODE = 0x4000
HDLC_FLAG_RXC_INV = 0x0002
HDLC_FLAG_TXC_INV = 0x0004

HDLC_CRC_NONE = 0
HDLC_CRC_16_CCITT = 1
HDLC_CRC_32_CCITT = 2
HDLC_CRC_MASK = 0x00ff
HDLC_CRC_RETURN_EX = 0x8000

RX_OK = 0
RX_CRC_ERROR = 1

HDLC_TXIDLE_FLAGS = 0
HDLC_TXIDLE_ALT_ZEROS_ONES = 1
HDLC_TXIDLE_ZEROS = 2
HDLC_TXIDLE_ONES = 3
HDLC_TXIDLE_ALT_MARK_SPACE = 4
HDLC_TXIDLE_SPACE = 5
HDLC_TXIDLE_MARK = 6
HDLC_TXIDLE_CUSTOM_8 = 0x10000000
HDLC_TXIDLE_CUSTOM_16 = 0x20000000

HDLC_ENCODING_NRZ = 0
HDLC_ENCODING_NRZB = 1
HDLC_ENCODING_NRZI_MARK = 2
HDLC_ENCODING_NRZI_SPACE = 3
HDLC_ENCODING_NRZI = HDLC_ENCODING_NRZI_SPACE
HDLC_ENCODING_BIPHASE_MARK = 4
HDLC_ENCODING_BIPHASE_SPACE = 5
HDLC_ENCODING_BIPHASE_LEVEL = 6
HDLC_ENCODING_DIFF_BIPHASE_LEVEL = 7

HDLC_PREAMBLE_LENGTH_8BITS = 0
HDLC_PREAMBLE_LENGTH_16BITS = 1
HDLC_PREAMBLE_LENGTH_32BITS = 2
HDLC_PREAMBLE_LENGTH_64BITS = 3

HDLC_PREAMBLE_PATTERN_NONE = 0
HDLC_PREAMBLE_PATTERN_ZEROS = 1
HDLC_PREAMBLE_PATTERN_FLAGS = 2
HDLC_PREAMBLE_PATTERN_10 = 3
HDLC_PREAMBLE_PATTERN_01 = 4
HDLC_PREAMBLE_PATTERN_ONES = 5

MGSL_MODE_ASYNC = 1
MGSL_MODE_HDLC = 2
MGSL_MODE_MONOSYNC = 3
MGSL_MODE_BISYNC = 4
MGSL_MODE_RAW = 6
MGSL_MODE_BASE_CLOCK = 7
MGSL_MODE_XSYNC = 8
MGSL_MODE_USB_PROM = 9
MGSL_MODE_MSC_PROM = 10
MGSL_MODE_TDM = 11

# definitions for building TDM 32-bit options value

# TDM sync frame [bit 20]
TDM_SYNC_FRAME_OFF = 0
TDM_SYNC_FRAME_ON  = 1 << 20

# TDM sync to data delay [bits 19:18]
TDM_SYNC_DELAY_NONE = 0
TDM_SYNC_DELAY_1BIT = 1 << 18
TDM_SYNC_DELAY_2BITS = 2 << 18

# TDM transmit sync width [bit 17]
TDM_TX_SYNC_WIDTH_SLOT = 0
TDM_TX_SYNC_WIDTH_BIT = 1 << 17

# TDM Sync polarity [bit 16]
TDM_SYNC_POLARITY_NORMAL = 0
TDM_SYNC_POLARITY_INVERT = 1 << 16

# TDM RX FRAME COUNT [bits 15:8]
def TDM_RX_FRAME_COUNT(frame_count:int) -> int:
    """Return frame count field specified by frame count."""
    return (frame_count - 1) << 8

# TDM slot count [bits 7:3] : 0=384 slots, 1-31 = 2-32 slots
def TDM_SLOT_COUNT(slot_count:int) -> int:
    """Return slot count field specified by slot count."""
    if slot_count == 384:
        return 0
    return ((slot_count - 1) & 0x1f) << 3

# TDM slot size [bits 2:0]
TDM_SLOT_SIZE_8BITS = 1
TDM_SLOT_SIZE_12BITS = 2
TDM_SLOT_SIZE_16BITS = 3
TDM_SLOT_SIZE_20BITS = 4
TDM_SLOT_SIZE_24BITS = 5
TDM_SLOT_SIZE_28BITS = 6
TDM_SLOT_SIZE_32BITS = 7


MGSL_INTERFACE_MASK = 0xf
MGSL_INTERFACE_DISABLE = 0
MGSL_INTERFACE_RS232 = 1
MGSL_INTERFACE_V35 = 2
MGSL_INTERFACE_RS422 = 3
MGSL_INTERFACE_RS530A = 4
MGSL_INTERFACE_RTS_EN = 0x10
MGSL_INTERFACE_LL = 0x20
MGSL_INTERFACE_RL = 0x40
MGSL_INTERFACE_MSB_FIRST = 0x80
MGSL_INTERFACE_HALF_DUPLEX = 0x100
MGSL_INTERFACE_TERM_OFF = 0x200

MGSL_ENABLE_PIO = ctypes.c_void_p((1 << 31) + 1)
MGSL_ENABLE_DMA = (1 << 30) + 1

def interface_str(if_mode):
        d = '(' + hex(if_mode) + ')'
        interface = if_mode & MGSL_INTERFACE_MASK
        if interface == MGSL_INTERFACE_DISABLE:
            d += ' MGSL_INTERFACE_DISABLE'
        elif interface == MGSL_INTERFACE_RS232:
            d += ' MGSL_INTERFACE_RS232'
        elif interface == MGSL_INTERFACE_V35:
            d += ' MGSL_INTERFACE_V35'
        elif interface == MGSL_INTERFACE_RS422:
            d += ' MGSL_INTERFACE_RS422'
        elif interface == MGSL_INTERFACE_RS530A:
            d += ' MGSL_INTERFACE_RS530A'
        else:
            d += ' unknown interface=' + hex(interface)
        if if_mode & MGSL_INTERFACE_RTS_EN:
            d += ' MGSL_INTERFACE_RTS_EN'
        if if_mode & MGSL_INTERFACE_LL:
            d += ' MGSL_INTERFACE_LL'
        if if_mode & MGSL_INTERFACE_RL:
            d += ' MGSL_INTERFACE_RL'
        if if_mode & MGSL_INTERFACE_MSB_FIRST:
            d += ' MGSL_INTERFACE_MSB_FIRST'
        if if_mode & MGSL_INTERFACE_HALF_DUPLEX:
            d += ' MGSL_INTERFACE_HALF_DUPLEX'
        if if_mode & MGSL_INTERFACE_TERM_OFF:
            d += ' MGSL_INTERFACE_TERM_OFF'
        return d

class MGSL_PARAMS(ctypes.Structure):
    # _pack_ = 8
    _fields_ = [
        ("mode", ctypes.c_ulong),  # protocol selection (MGSL_MODE_XXX)
        ("loopback", ctypes.c_byte),  # 0=normal operation, 1=internal loopback
        ("flags", ctypes.c_ushort),  # misc options (HDLC_FLAG_XXX)
        ("encoding", ctypes.c_byte),  # data encoding (NRZI, NRZ, etc)
        ("clock_speed", ctypes.c_ulong),  # BRG/DPLL rate (sync modes)
        ("addr", ctypes.c_byte),  # HDLC address filter (0xFF=receive all)
        ("crc_type", ctypes.c_ushort),  # frame check selection (HDLC only)
        ("preamble_length", ctypes.c_byte),  # preamble length (8,16,32,64 bits)
        ("preamble", ctypes.c_byte),  # sync mode preamble pattern
        ("data_rate", ctypes.c_ulong),  # async mode data rate
        ("data_bits", ctypes.c_byte),  # async mode data bits (5..8)
        ("stop_bits", ctypes.c_byte),  # async mode stop bits (1..2)
        ("parity", ctypes.c_byte)  # async mode parity bit
    ]

    def mode_str(self):
        if self.mode == MGSL_MODE_ASYNC:
            return 'MGSL_MODE_ASYNC'
        elif self.mode == MGSL_MODE_HDLC:
            return 'MGSL_MODE_HDLC'
        elif self.mode == MGSL_MODE_MONOSYNC:
            return 'MGSL_MODE_MONOSYNC'
        elif self.mode == MGSL_MODE_BISYNC:
            return 'MGSL_MODE_BISYNC'
        elif self.mode == MGSL_MODE_RAW:
            return 'MGSL_MODE_RAW'
        elif self.mode == MGSL_MODE_XSYNC:
            return 'MGSL_MODE_XSYNC'
        elif self.Mode == MGSL_MODE_TDM:
            return 'MGSL_MODE_TDM'
        else:
            return 'unknown mode = ' + hex(self.mode)

    def flags_str(self):
        d = ''
        if self.flags & HDLC_FLAG_UNDERRUN_ABORT7:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_UNDERRUN_ABORT7'
        if self.flags & HDLC_FLAG_UNDERRUN_ABORT15:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_UNDERRUN_ABORT15'
        if self.flags & HDLC_FLAG_UNDERRUN_FLAG:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_UNDERRUN_FLAG'
        if self.flags & HDLC_FLAG_UNDERRUN_CRC:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_UNDERRUN_CRC'
        if self.flags & HDLC_FLAG_SHARE_ZERO:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_SHARE_ZERO'
        if self.flags & HDLC_FLAG_AUTO_CTS:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_AUTO_CTS'
        if self.flags & HDLC_FLAG_AUTO_DCD:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_AUTO_DCD'
        if self.flags & HDLC_FLAG_AUTO_RTS:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_AUTO_RTS'
        if self.flags & HDLC_FLAG_RXC_DPLL:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_RXC_DPLL'
        if self.flags & HDLC_FLAG_RXC_BRG:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_RXC_BRG'
        if not (self.flags & (HDLC_FLAG_RXC_TXCPIN | HDLC_FLAG_RXC_DPLL | HDLC_FLAG_RXC_BRG)):
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_RXC_RXCPIN'
        if self.flags & HDLC_FLAG_RXC_TXCPIN:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_RXC_TXCPIN'
        if self.flags & HDLC_FLAG_TXC_DPLL:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_TXC_DPLL'
        if self.flags & HDLC_FLAG_TXC_BRG:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_TXC_BRG'
        if not (self.flags & (HDLC_FLAG_TXC_RXCPIN | HDLC_FLAG_TXC_DPLL | HDLC_FLAG_TXC_BRG)):
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_TXC_TXCPIN'
        if self.flags & HDLC_FLAG_TXC_RXCPIN:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_TXC_RXCPIN'
        if self.flags & HDLC_FLAG_DPLL_DIV8:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_DPLL_DIV8'
        if self.flags & HDLC_FLAG_DPLL_DIV16:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_DPLL_DIV16'
        if self.flags & (HDLC_FLAG_RXC_DPLL | HDLC_FLAG_TXC_DPLL) and \
           not (self.flags & (HDLC_FLAG_DPLL_DIV8 | HDLC_FLAG_DPLL_DIV16)):
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_DPLL_DIV32'
        if self.flags & HDLC_FLAG_HDLC_LOOPMODE:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_HDLC_LOOPMODE'
        if self.flags & HDLC_FLAG_RXC_INV:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_RXC_INV'
        if self.flags & HDLC_FLAG_TXC_INV:
            if len(d) > 0:
                d += ' + '
            d += 'HDLC_FLAG_TXC_INV'
        return d

    def encoding_str(self):
        if self.encoding == HDLC_ENCODING_NRZ:
            return 'HDLC_ENCODING_NRZ'
        elif self.encoding == HDLC_ENCODING_NRZB:
            return 'HDLC_ENCODING_NRZB'
        elif self.encoding == HDLC_ENCODING_NRZI_MARK:
            return 'HDLC_ENCODING_NRZI_MARK'
        elif self.encoding == HDLC_ENCODING_NRZI_SPACE:
            return 'HDLC_ENCODING_NRZI_SPACE'
        elif self.encoding == HDLC_ENCODING_NRZI:
            return 'HDLC_ENCODING_NRZI'
        elif self.encoding == HDLC_ENCODING_BIPHASE_MARK:
            return 'HDLC_ENCODING_BIPHASE_MARK'
        elif self.encoding == HDLC_ENCODING_BIPHASE_SPACE:
            return 'HDLC_ENCODING_BIPHASE_SPACE'
        elif self.encoding == HDLC_ENCODING_BIPHASE_LEVEL:
            return 'HDLC_ENCODING_BIPHASE_LEVEL'
        elif self.encoding == HDLC_ENCODING_DIFF_BIPHASE_LEVEL:
            return 'HDLC_ENCODING_DIFF_BIPHASE_LEVEL'
        else:
            return 'unknown ' + hex(self.encoding)

    def crc_type_str(self):
        d = ''
        if self.crc_type  & HDLC_CRC_MASK == HDLC_CRC_NONE:
            d += 'HDLC_CRC_NONE'
        elif self.crc_type  & HDLC_CRC_MASK == HDLC_CRC_16_CCITT:
            d += 'HDLC_CRC_16_CCITT'
        elif self.crc_type  & HDLC_CRC_MASK == HDLC_CRC_32_CCITT:
            d += 'HDLC_CRC_32_CCITT'
        else:
            return 'unknown ' + hex(self.crc_type)
        if self.crc_type & HDLC_CRC_RETURN_EX:
            d += " | HDLC_CRC_RETURN_EX"
        return d

    def preamble_length_str(self):
        if self.preamble_length == HDLC_PREAMBLE_LENGTH_8BITS:
            return 'HDLC_PREAMBLE_LENGTH_8BITS'
        elif self.preamble_length == HDLC_PREAMBLE_LENGTH_16BITS:
            return 'HDLC_PREAMBLE_LENGTH_16BITS'
        elif self.preamble_length == HDLC_PREAMBLE_LENGTH_32BITS:
            return 'HDLC_PREAMBLE_LENGTH_32BITS'
        elif self.preamble_length == HDLC_PREAMBLE_LENGTH_64BITS:
            return 'HDLC_PREAMBLE_LENGTH_64BITS'
        else:
            return 'unknown ' + hex(self.preamble_length)

    def preamble_pattern_str(self):
        if self.preamble == HDLC_PREAMBLE_PATTERN_NONE:
            return 'HDLC_PREAMBLE_PATTERN_NONE'
        elif self.preamble == HDLC_PREAMBLE_PATTERN_ZEROS:
            return 'HDLC_PREAMBLE_PATTERN_ZEROS'
        elif self.preamble == HDLC_PREAMBLE_PATTERN_FLAGS:
            return 'HDLC_PREAMBLE_PATTERN_FLAGS'
        elif self.preamble == HDLC_PREAMBLE_PATTERN_10:
            return 'HDLC_PREAMBLE_PATTERN_10'
        elif self.preamble == HDLC_PREAMBLE_PATTERN_01:
            return 'HDLC_PREAMBLE_PATTERN_01'
        elif self.preamble == HDLC_PREAMBLE_PATTERN_ONES:
            return 'HDLC_PREAMBLE_PATTERN_ONES'
        else:
            return 'unknown ' + hex(self.preamble)

    def parity_str(self):
        if self.parity == ASYNC_PARITY_NONE:
            return 'ASYNC_PARITY_NONE'
        elif self.parity == ASYNC_PARITY_EVEN:
            return 'ASYNC_PARITY_EVEN'
        elif self.parity == ASYNC_PARITY_ODD:
            return 'ASYNC_PARITY_ODD'
        else:
            return 'unknown ' + hex(self.parity)

    def __init__(self):
        self.mode = MGSL_MODE_HDLC
        self.loopback = False
        self.flags = HDLC_FLAG_RXC_RXCPIN | HDLC_FLAG_TXC_TXCPIN
        self.encoding = HDLC_ENCODING_NRZ
        self.clock_speed = 0
        self.addr = 0xff
        self.crc_type = HDLC_CRC_16_CCITT
        self.preamble_length = HDLC_PREAMBLE_LENGTH_8BITS
        self.preamble = HDLC_PREAMBLE_PATTERN_NONE
        self.data_rate = 9600
        self.data_bits = 8
        self.stop_bits = 1
        self.parity = ASYNC_PARITY_NONE
 
    def __repr__(self):
        return 'MGSL_PARAMS object at ' + hex(id(self)) + '\n' + \
            'mode = ' + self.mode_str() + '\n' + \
            'loopback = ' + str(self.loopback) + '\n' + \
            'flags = ' + self.flags_str() + '\n' + \
            'encoding = ' + self.encoding_str() + '\n' + \
            'clock_speed = ' + str(self.clock_speed) + '\n' + \
            'addr = ' + hex(self.addr) + '\n' + \
            'crc_type = ' + self.crc_type_str() + '\n' + \
            'preamble_length = ' + self.preamble_length_str() + '\n' + \
            'preamble = ' + self.preamble_pattern_str() + '\n' + \
            'data_rate = ' + str(self.data_rate) + '\n' + \
            'data_bits = ' + str(self.data_bits) + '\n' + \
            'stop_bits = ' + str(self.stop_bits) + '\n' + \
            'parity = ' + self.parity_str() + '\n'

    def __str__(self):
        return self.__repr__()

MICROGATE_VENDOR_ID = 0x13c0
SYNCLINK_DEVICE_ID = 0x0010
MGSCC_DEVICE_ID = 0x0020
SYNCLINK_SCA_DEVICE_I = 0x0030
SYNCLINK_GT_DEVICE_ID = 0x0070
SYNCLINK_GT4_DEVICE_ID = 0x0080
SYNCLINK_AC_DEVICE_ID = 0x0090
SYNCLINK_GT2_DEVICE_ID = 0x00A0
MGSL_MAX_SERIAL_NUMBER = 30

SerialSignal_DCD = 0x01  # Data Carrier Detect (output)
SerialSignal_TXD = 0x02  # Transmit Data (output)
SerialSignal_RI = 0x04   # Ring Indicator (input)
SerialSignal_RXD = 0x08  # Receive Data (input)
SerialSignal_CTS = 0x10  # Clear to Send (input)
SerialSignal_RTS = 0x20  # Request to Send (output)
SerialSignal_DSR = 0x40  # Data Set Ready (input)
SerialSignal_DTR = 0x80  # Data Terminal Ready (output)


class mgsl_icount(ctypes.Structure):
    """Counters of the input lines (CTS, DSR, RI, CD) interrupts."""
    # _pack_ = 8
    _fields_ = [
        ("cts", ctypes.c_uint32),
        ("dsr", ctypes.c_uint32),
        ("rng", ctypes.c_uint32),
        ("dcd", ctypes.c_uint32),
        ("tx", ctypes.c_uint32),
        ("rx", ctypes.c_uint32),
        ("frame", ctypes.c_uint32),
        ("parity", ctypes.c_uint32),
        ("overrun", ctypes.c_uint32),
        ("brk", ctypes.c_uint32),
        ("buf_overrun", ctypes.c_uint32),
        ("txok", ctypes.c_uint32),
        ("txunder", ctypes.c_uint32),
        ("txabort", ctypes.c_uint32),
        ("txtimeout", ctypes.c_uint32),
        ("rxshort", ctypes.c_uint32),
        ("rxlong", ctypes.c_uint32),
        ("rxabort", ctypes.c_uint32),
        ("rxover", ctypes.c_uint32),
        ("rxcrc", ctypes.c_uint32),
        ("rxok", ctypes.c_uint32),
        ("exithunt", ctypes.c_uint32),
        ("rxidle", ctypes.c_uint32)
    ]

    def __init__(self):
        pass

    def __repr__(self):
        return 'mgsl_icount object at ' + hex(id(self)) + '\n' + \
            'cts = ' + hex(self.cts) + '\n' + \
            'dsr = ' + hex(self.dsr) + '\n' + \
            'rng = ' + hex(self.dsr) + '\n' + \
            'dcd = ' + hex(self.dsr) + '\n' + \
            'tx = ' + hex(self.dsr) + '\n' + \
            'rx = ' + hex(self.dsr) + '\n' + \
            'frame = ' + hex(self.dsr) + '\n' + \
            'parity = ' + hex(self.dsr) + '\n' + \
            'overrun = ' + hex(self.dsr) + '\n' + \
            'brk = ' + hex(self.dsr) + '\n' + \
            'buf_overrun = ' + hex(self.dsr) + '\n' + \
            'txok = ' + hex(self.dsr) + '\n' + \
            'txunder = ' + hex(self.dsr) + '\n' + \
            'txabort = ' + hex(self.dsr) + '\n' + \
            'txtimeout = ' + hex(self.dsr) + '\n' + \
            'rxshort = ' + hex(self.dsr) + '\n' + \
            'rxlong = ' + hex(self.dsr) + '\n' + \
            'rxabort = ' + hex(self.dsr) + '\n' + \
            'rxover = ' + hex(self.dsr) + '\n' + \
            'rxcrc = ' + hex(self.dsr) + '\n' + \
            'rxok = ' + hex(self.dsr) + '\n' + \
            'exithunt = ' + hex(self.dsr) + '\n' + \
            'rxidle = ' + hex(self.dsr) + '\n'

    def __str__(self):
        return self.__repr__()


class gpio_desc(ctypes.Structure):
    """General Purpose I/O Descriptor"""
    # _pack_ = 8
    _fields_ = [
        ("state", ctypes.c_uint32),     # signal states
        ("smask", ctypes.c_uint32),     # state mask
        ("dir", ctypes.c_uint32),       # signal directions
        ("dmask", ctypes.c_uint32)      # direction mask
    ]

    def __init__(self):
        self.state = 0
        self.smask = 0
        self.dir = 0
        self.dmask = 0

    def __repr__(self):
        return 'gpio_desc object at ' + hex(id(self)) + '\n' + \
            'state = ' + hex(self.state) + '\n' + \
            'smask = ' + hex(self.smask) + '\n' + \
            'dir = ' + hex(self.dir) + '\n' + \
            'dmask = ' + hex(self.dmask) + '\n'

    def __str__(self):
        return self.__repr__()

#
# Event bit flags for use with MgslWaitEvent
#
MgslEvent_DsrActive = 0x0001
MgslEvent_DsrInactive = 0x0002
MgslEvent_Dsr = 0x0003
MgslEvent_CtsActive = 0x0004
MgslEvent_CtsInactive = 0x0008
MgslEvent_Cts = 0x000c
MgslEvent_DcdActive = 0x0010
MgslEvent_DcdInactive = 0x0020
MgslEvent_Dcd = 0x0030
MgslEvent_RiActive = 0x0040
MgslEvent_RiInactive = 0x0080
MgslEvent_Ri = 0x00c0
MgslEvent_ExitHuntMode = 0x0100
MgslEvent_IdleReceived = 0x0200


#
# definitions for building linux ioctl codes
#
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = ((1 << _IOC_NRBITS)-1)
_IOC_TYPEMASK = ((1 << _IOC_TYPEBITS)-1)
_IOC_SIZEMASK = ((1 << _IOC_SIZEBITS)-1)
_IOC_DIRMASK = ((1 << _IOC_DIRBITS)-1)

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = (_IOC_NRSHIFT+_IOC_NRBITS)
_IOC_SIZESHIFT = (_IOC_TYPESHIFT+_IOC_TYPEBITS)
_IOC_DIRSHIFT = (_IOC_SIZESHIFT+_IOC_SIZEBITS)

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2

def _IOC(dir,type,nr,size):
    return (((dir)  << _IOC_DIRSHIFT) | \
        ((type) << _IOC_TYPESHIFT) | \
        ((nr)   << _IOC_NRSHIFT) | \
        ((size) << _IOC_SIZESHIFT))

def _IO(type, nr):
    return _IOC(_IOC_NONE, type, nr, 0)

def _IOR(type, nr, size):
    return _IOC(_IOC_READ, type, nr, ctypes.sizeof(size))

def _IOW(type,nr,size):
    return _IOC(_IOC_WRITE, type, nr, ctypes.sizeof(size))

def _IOWR(type,nr,size):
    return _IOC(_IOC_READ | _IOC_WRITE, type, nr, ctypes.sizeof(size))


# Private IOCTL codes:
# 
# MGSL_IOCSPARAMS	set MGSL_PARAMS structure values
# MGSL_IOCGPARAMS	get current MGSL_PARAMS structure values
# MGSL_IOCSTXIDLE	set current transmit idle mode
# MGSL_IOCGTXIDLE	get current transmit idle mode
# MGSL_IOCTXENABLE	enable or disable transmitter
# MGSL_IOCRXENABLE	enable or disable receiver
# MGSL_IOCTXABORT	abort transmitting frame (HDLC)
# MGSL_IOCGSTATS	return current statistics
# MGSL_IOCWAITEVENT	wait for specified event to occur
# MGSL_LOOPTXDONE	transmit in HDLC LoopMode done
# MGSL_IOCSIF       set the serial interface type
# MGSL_IOCGIF       get the serial interface type
# MGSL_IOCSXSYNC    set XSYNC options
# MGSL_IOCGXSYNC    get XSYNC options
# MGSL_IOCSTDM      set TDM options
# MGSL_IOCGTDM      get TDM options

MGSL_MAGIC_IOC = ord('m')
MGSL_IOCSPARAMS = _IOW(MGSL_MAGIC_IOC, 0, MGSL_PARAMS)
MGSL_IOCGPARAMS = _IOR(MGSL_MAGIC_IOC, 1, MGSL_PARAMS)
MGSL_IOCSTXIDLE = _IO(MGSL_MAGIC_IOC, 2)
MGSL_IOCGTXIDLE = _IO(MGSL_MAGIC_IOC, 3)
MGSL_IOCTXENABLE = _IO(MGSL_MAGIC_IOC, 4)
MGSL_IOCRXENABLE = _IO(MGSL_MAGIC_IOC, 5)
MGSL_IOCTXABORT = _IO(MGSL_MAGIC_IOC, 6)
MGSL_IOCGSTATS = _IO(MGSL_MAGIC_IOC, 7)
MGSL_IOCWAITEVENT = _IOWR(MGSL_MAGIC_IOC, 8, ctypes.c_int)
MGSL_IOCCLRMODCOUNT = _IO(MGSL_MAGIC_IOC, 15)
MGSL_IOCLOOPTXDONE = _IO(MGSL_MAGIC_IOC, 9)
MGSL_IOCSIF = _IO(MGSL_MAGIC_IOC, 10)
MGSL_IOCGIF = _IO(MGSL_MAGIC_IOC, 11)
MGSL_IOCSGPIO = _IOW(MGSL_MAGIC_IOC, 16, gpio_desc)
MGSL_IOCGGPIO = _IOR(MGSL_MAGIC_IOC, 17, gpio_desc)
MGSL_IOCWAITGPIO = _IOWR(MGSL_MAGIC_IOC, 18, gpio_desc)
MGSL_IOCSXSYNC = _IO(MGSL_MAGIC_IOC, 19)
MGSL_IOCGXSYNC = _IO(MGSL_MAGIC_IOC, 20)
MGSL_IOCSXCTRL = _IO(MGSL_MAGIC_IOC, 21)
MGSL_IOCGXCTRL = _IO(MGSL_MAGIC_IOC, 22)
MGSL_IOCSTDM = _IO(MGSL_MAGIC_IOC, 23)
MGSL_IOCGTDM = _IO(MGSL_MAGIC_IOC, 24)

#
# Object oriented API
#

import os.path

class Port():
    """Object representing a serial communications port."""

    @classmethod
    def enumerate(cls):
        """Return list of port names."""
        ports = []
        names = []

        # look for all /dev/ttyUSB*
        # r=root, d=directories, f = files
        names = os.listdir('/dev')
        for name in names:
            if name.find('ttyUSB') != -1 or \
               name.find('ttySLG') != -1:
                ports.append('/dev/' + name)

        return ports

    # line disciplines
    N_TTY = 0
    N_HDLC = 13

    # serial signal bit flags
    DCD = SerialSignal_DCD  # Data Carrier Detect (output)
    TXD = SerialSignal_TXD  # Transmit Data (output)
    RI = SerialSignal_RI  # Ring Indicator (input)
    RXD = SerialSignal_RXD  # Receive Data (input)
    CTS = SerialSignal_CTS  # Clear to Send (input)
    RTS = SerialSignal_RTS  # Request to Send (output)
    DSR = SerialSignal_DSR  # Data Set Ready (input)
    DTR = SerialSignal_DTR  # Data Terminal Ready (output)

    # Event bit flags for use with wait_event
    DSR_ON = MgslEvent_DsrActive
    DSR_OFF = MgslEvent_DsrInactive
    CTS_ON = MgslEvent_CtsActive
    CTS_OFF = MgslEvent_CtsInactive
    DCD_ON = MgslEvent_DcdActive
    DCD_OFF = MgslEvent_DcdInactive
    RI_ON = MgslEvent_RiActive
    RI_OFF = MgslEvent_RiInactive
    RECEIVE_ACTIVE = MgslEvent_ExitHuntMode
    RECEIVE_IDLE = MgslEvent_IdleReceived

    # serial protocols
    ASYNC = MGSL_MODE_ASYNC
    HDLC = MGSL_MODE_HDLC
    MONOSYNC = MGSL_MODE_MONOSYNC
    BISYNC = MGSL_MODE_BISYNC
    RAW = MGSL_MODE_RAW
    XSYNC = MGSL_MODE_XSYNC
    TDM = MGSL_MODE_TDM

    # serial encodings
    NRZ = HDLC_ENCODING_NRZ
    NRZB = HDLC_ENCODING_NRZB
    NRZI_MARK = HDLC_ENCODING_NRZI_MARK
    NRZI_SPACE = HDLC_ENCODING_NRZI_SPACE
    NRZI = NRZI_SPACE
    FM1 = HDLC_ENCODING_BIPHASE_MARK
    FM0 = HDLC_ENCODING_BIPHASE_SPACE
    MANCHESTER = HDLC_ENCODING_BIPHASE_LEVEL
    DIFF_BIPHASE_LEVEL = HDLC_ENCODING_DIFF_BIPHASE_LEVEL

    # clock sources
    TXC_INPUT = 1
    RXC_INPUT = 2
    INTERNAL = 3
    RECOVERED = 4

    # used with any setting requiring 0
    OFF = 0

    # asynchronous parity
    EVEN = 1
    ODD = 2

    # HDLC/SDLC frame check
    CRC16 = 1
    CRC32 = 2

    # serial interface selection
    RS232 = 1
    V35 = 2
    RS422 = 3
    RS530A = 4

    # transmit transfer modes
    DMA = MGSL_ENABLE_DMA
    PIO = MGSL_ENABLE_PIO

    def events_str(self, events):
        s = ''
        if events & Port.DSR_ON:
            s += 'DSR_ON '
        elif events & Port.DSR_OFF:
            s += 'DSR_OFF '
        if events & Port.CTS_ON:
            s += 'CTS_ON '
        elif events & Port.CTS_OFF:
            s += 'CTS_OFF '
        if events & Port.DCD_ON:
            s += 'DCD_ON '
        elif events & Port.DCD_OFF:
            s += 'DCD_OFF '
        if events & Port.RI_ON:
            s += 'RI_ON '
        elif events & Port.RI_OFF:
            s += 'RI_OFF '
        if events & Port.RECEIVE_ACTIVE:
            s += 'RECEIVE_ACTIVE '
        if events & Port.RECEIVE_IDLE:
            s += 'RECEIVE_IDLE'
        return s

    class Defaults():
        """Persistent default options."""

        def __init__(self):
            self.max_data_size = 4096
            self.interface = Port.OFF
            self.rts_output_enable = False
            self.termination = True

        def interface_str(self):
            if self.interface == Port.OFF:
                return 'OFF'
            elif self.interface == Port.RS232:
                return 'RS232'
            elif self.interface == Port.V35:
                return 'V35'
            elif self.interface == Port.RS422:
                return 'RS422'
            elif self.interface == Port.RS530A:
                return 'RS530A'
            else:
                return 'Unknown=' + str(self.interface)

        def __repr__(self):
            return 'Defaults object at ' + hex(id(self)) + '\n' + \
                'max_data_size = ' + str(self.max_data_size) + '\n' + \
                'interface = ' + self.interface_str() + '\n' + \
                'rts_output_enable = ' + str(self.rts_output_enable) + '\n' + \
                'termination = ' + str(self.termination) + '\n'

        def __str__(self):
            return self.__repr__()

    class Settings():
        """Port settings."""

        def protocol_str(self):
            if self.protocol == Port.ASYNC:
                return 'ASYNC'
            elif self.protocol == Port.HDLC:
                return 'HDLC'
            elif self.protocol == Port.MONOSYNC:
                return 'MONOSYNC'
            elif self.protocol == Port.BISYNC:
                return 'BISYNC'
            elif self.protocol == Port.RAW:
                return 'RAW'
            elif self.protocol == Port.XSYNC:
                return 'XSYNC'
            elif self.protocol == Port.TDM:
                return 'TDM'
            else:
                return 'unknown protocol = ' + hex(self.protocol)

        def encoding_str(self):
            if self.encoding == Port.NRZ:
                return 'NRZ'
            elif self.encoding == Port.NRZB:
                return 'NRZB'
            elif self.encoding == Port.NRZI_MARK:
                return 'NRZI_MARK'
            elif self.encoding == Port.NRZI:
                return 'NRZI'
            elif self.encoding == Port.FM1:
                return 'FM1'
            elif self.encoding == Port.FM0:
                return 'FM0'
            elif self.encoding == Port.MANCHESTER:
                return 'MANCHESTER'
            elif self.encoding == Port.DIFF_BIPHASE_LEVEL:
                return 'DIFF_BIPHASE_LEVEL'
            else:
                return 'unknown ' + hex(self.encoding)

        def clock_str(self, clock):
            if clock == Port.TXC_INPUT:
                return 'TXC_INPUT'
            elif clock == Port.RXC_INPUT:
                return 'RXC_INPUT'
            elif clock == Port.INTERNAL:
                return 'INTERNAL'
            elif clock == Port.RECOVERED:
                return 'RECOVERED'
            else:
                return 'unknown ' + str(clock)

        def crc_str(self):
            if self.crc == Port.OFF:
                return 'OFF'
            elif self.crc == Port.CRC16:
                return 'CRC16'
            elif self.crc == Port.CRC32:
                return 'CRC32'
            else:
                return 'unknown ' + hex(self.crc)

        def parity_str(self):
            if self.async_parity == Port.OFF:
                return 'OFF'
            elif self.async_parity == Port.EVEN:
                return 'EVEN'
            elif self.async_parity == Port.ODD:
                return 'ODD'
            else:
                return 'unknown ' + hex(self.async_parity)

        def __init__(self):
            self.protocol = Port.HDLC
            self.encoding = Port.NRZ
            self.msb_first = False
            self.internal_loopback = False

            self.crc = Port.CRC16
            self.discard_data_with_error = True
            self.discard_received_crc = True

            self.hdlc_address_filter = 0xff

            self.transmit_preamble_pattern = 0x7e
            self.transmit_preamble_bits = 0

            self.recovered_clock_divisor = 16
            self.internal_clock_rate = 0

            self.transmit_clock = Port.TXC_INPUT
            self.transmit_clock_invert = False
            self.receive_clock = Port.RXC_INPUT
            self.receive_clock_invert = False

            self.auto_cts = False
            self.auto_dcd = False
            self.auto_rts = False

            self.async_data_rate = 9600
            self.async_data_bits = 8
            self.async_stop_bits = 1
            self.async_parity = Port.OFF

            self.tdm_sync_frame = False
            self.tdm_sync_delay = 0
            self.tdm_sync_short = False
            self.tdm_sync_invert = False
            self.tdm_frame_count = 1
            self.tdm_slot_count = 2
            self.tdm_slot_bits = 8

            self.xsync_block_size = 0
            self.xsync_sync_size = 4
            self.sync_pattern = 0

            # Linux only
            self.min_read_bytes = 255
            self.read_timer = 0

        def __repr__(self):
            return 'Settings object at ' + hex(id(self)) + '\n' + \
                'protocol = ' + self.protocol_str() + '\n' + \
                'encoding = ' + self.encoding_str() + '\n' + \
                'msb_first = ' + str(self.msb_first) + '\n' + \
                'crc = ' + self.crc_str() + '\n' + \
                'discard_data_with_error = ' + str(self.discard_data_with_error) + '\n' + \
                'discard_received_crc = ' + str(self.discard_received_crc) + '\n' + \
                'hdlc_address_filter = ' + hex(self.hdlc_address_filter) + '\n' + \
                'auto_rts = ' + str(self.auto_rts) + '\n' + \
                'auto_cts = ' + str(self.auto_cts) + '\n' + \
                'auto_dcd = ' + str(self.auto_dcd) + '\n' + \
                'internal_clock_rate = ' + str(self.internal_clock_rate) + '\n' + \
                'transmit_clock = ' + self.clock_str(self.transmit_clock) + '\n' + \
                'transmit_clock_invert = ' + str(self.transmit_clock_invert) + '\n' + \
                'receive_clock = ' + self.clock_str(self.receive_clock) + '\n' + \
                'receive_clock_invert = ' + str(self.receive_clock_invert) + '\n' + \
                'transmit_preamble_pattern = ' + hex(self.transmit_preamble_pattern) + '\n' + \
                'transmit_preamble_bits = ' + str(self.transmit_preamble_bits) + '\n' + \
                'async_data_rate = ' + str(self.async_data_rate) + '\n' + \
                'async_data_bits = ' + str(self.async_data_bits) + '\n' + \
                'async_stop_bits = ' + str(self.async_stop_bits) + '\n' + \
                'async_parity = ' + self.parity_str() + '\n' + \
                'sync_pattern = ' + hex(self.sync_pattern) + '\n' + \
                'xsync_block_size = ' + str(self.xsync_block_size) + '\n' + \
                'xsync_sync_size = ' + str(self.xsync_sync_size) + '\n' + \
                'tdm_sync_frame = ' + str(self.tdm_sync_frame) + '\n' + \
                'tdm_sync_delay = ' + str(self.tdm_sync_delay) + '\n' + \
                'tdm_sync_short = ' + str(self.tdm_sync_short) + '\n' + \
                'tdm_sync_invert = ' + str(self.tdm_sync_invert) + '\n' + \
                'tdm_frame_count = ' + str(self.tdm_frame_count) + '\n' + \
                'tdm_slot_count = ' + str(self.tdm_slot_count) + '\n' + \
                'tdm_slot_bits = ' + str(self.tdm_slot_bits) + '\n' + \
                'internal_loopback = ' + str(self.internal_loopback) + '\n'

        def __str__(self):
            return self.__repr__()


    class GPIO():

        def __init__(self, port, bit):
            self._port = port
            self._bit = bit

        @property
        def state(self) -> bool:
            gpio = self._port.get_gpio()
            if gpio & (1 << self._bit):
                return True
            else:
                return False

        @state.setter
        def state(self, x:bool):
            mask = (1 << self._bit)
            if x:
                value = mask
            else:
                value = 0
            self._port.set_gpio(mask, value)

        @property
        def output(self) -> bool:
            gpio = self._port.get_gpio_direction()
            if gpio & (1 << self._bit):
                return True
            else:
                return False

        @output.setter
        def output(self, x:bool):
            mask = (1 << self._bit)
            if x:
                value = mask
            else:
                value = 0
            self._port.set_gpio_direction(mask, value)

    def is_open(self):
        """Return open state for port."""
        return self._open

    def open(self):
        """Open port."""
        if self.is_open():
            return
        # open serial device with O_NONBLOCK to ignore DCD input
        try:
            self._fd = os.open(self.name, os.O_RDWR | os.O_NONBLOCK)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise FileNotFoundError
            elif e.errno == errno.EPERM or \
                 e.errno == errno.EACCES:
                raise PermissionError
            else:
                raise OSError
        self._open = True
        self.get_defaults()
        self.get_settings()
        self._set_line_discipline()
        self.blocked_io = True
        self.ignore_read_errors = True
        self.receive_transfer_size = 256

    def close(self):
        """Close port."""
        if not self.is_open():
            return
        try:
            # disable receiver and set fill level to default 256
            fcntl.ioctl(self._fd, MGSL_IOCRXENABLE, (256 << 16))
        except OSError:
            pass
        try:
            fcntl.ioctl(self._fd, MGSL_IOCTXENABLE, False)
        except OSError:
            pass
        # return to async protocol on close
        settings = self.Settings()
        settings.protocol = self.ASYNC
        self.apply_settings(settings)
        self._open = False
        os.close(self._fd)
        self._fd = -1

    def write(self, buf:bytearray) -> bool:
        """Write send data to port."""
        try:
            bytes_sent = os.write(self._fd, buf)
            if bytes_sent == len(buf):
                return True
        except OSError:
            pass
        return False

    def flush(self) -> bool:
        """Wait for pending send data to complete."""
        if self.blocked_io:
            if termios.tcdrain(self._fd):
                return False
            return True
        size = ctypes.c_int()
        while True:
            if not fcntl.ioctl(self._fd, termios.TIOCOUTQ, size, True) and \
                not size.value:
                return True
            return False

    def read(self, size:int=None) -> bytearray:
        """Read received data from port."""
        if self._ldisc == self.N_HDLC:
            size = self._defaults.max_data_size
        elif not size:
            size = 1
        else:
            assert size > 0 and size <= self._defaults.max_data_size, \
                'read size must be 1 to max_data_size'
        try:
            buf = os.read(self._fd, size)
            if buf:
                return buf
        except OSError:
            pass
        return None

    def disable_receiver(self):
        """Disable receiver."""
        try:
            fcntl.ioctl(self._fd, MGSL_IOCRXENABLE, False)
        except OSError:
            pass

    def enable_receiver(self):
        """Enable receiver."""
        try:
            fcntl.ioctl(self._fd, MGSL_IOCRXENABLE, True)
        except OSError:
            pass

    def force_idle_receiver(self):
        """Force receiver to idle state (hunt mode)."""
        try:
            fcntl.ioctl(self._fd, MGSL_IOCRXENABLE, 2)
        except OSError:
            pass

    def disable_transmitter(self):
        """Disable transmitter."""
        try:
            fcntl.ioctl(self._fd, MGSL_IOCTXENABLE, False)
        except OSError:
            pass

    def enable_transmitter(self):
        """Enable transmitter."""
        try:
            fcntl.ioctl(self._fd, MGSL_IOCTXENABLE, True)
        except OSError:
            pass

    def wait(self, mask:int) -> int:
        """
        Wait for specified events.
        mask = bitmask of events to wait for
        returns bitmask of events that occurred or 0 if timeout
        If timeout is not specified, this call waits forever.
        """
        try:
            events = ctypes.c_int(mask)
            fcntl.ioctl(self._fd, MGSL_IOCWAITEVENT, events, True)
            return events.value
        except OSError:
            return 0
        
    def set_gpio(self, mask:int, states:int):
        """
        Set GPIO outputs to specified state.
        mask = bit mask of outputs to alter
        states = bit mask of output states
        """
        gpio = gpio_desc()
        gpio.state = states
        gpio.smask = mask
        gpio.dmask = 0  # unused
        gpio.dir = 0  # unused
        try:
            fcntl.ioctl(self._fd, MGSL_IOCSGPIO, gpio)
        except OSError:
            pass

    def get_gpio(self) -> int:
        """Return bitmap of GPIO states."""
        gpio = gpio_desc()
        try:
            fcntl.ioctl(self._fd, MGSL_IOCGGPIO, gpio, True)
            return gpio.state
        except OSError:
            return 0

    def set_gpio_direction(self, mask:int, dir:int):
        """
        Set GPIO signal directions.
        mask = bit mask of GPIO directions to alter
        dir = bit mask of signal direction (0=input,1=output)
        """
        gpio = gpio_desc()
        gpio.state = 0 # unused
        gpio.smask = 0 # unused
        gpio.dmask = mask
        gpio.dir = dir
        try:
            fcntl.ioctl(self._fd, MGSL_IOCSGPIO, gpio)
        except OSError:
            pass

    def get_gpio_direction(self) -> int:
        """
        Return bitmap of GPIO signal directions.
        0 = input, 1 = output
        """
        gpio = gpio_desc()
        try:
            fcntl.ioctl(self._fd, MGSL_IOCGGPIO, gpio, True)
            return gpio.dir
        except OSError:
            return 0

    def _set_line_discipline(self):
        if self._settings.protocol == self.HDLC or \
           self._settings.protocol == self.TDM or \
           (self._settings.protocol == self.XSYNC and \
            self._settings.xsync_block_size):
            self.line_discipline = self.N_HDLC
            self.receive_transfer_size = 256
        else:
            self.line_discipline = self.N_TTY
            # scrub transfer size through itself based on protocol
            self.receive_transfer_size = self._receive_transfer_size
            # set N_TTY options
            options = termios.tcgetattr(self._fd)
            options[0] = 0  # c_iflag
            options[1] = 0  # c_oflag
            # c_cflag
            options[2] = \
                termios.CREAD | termios.CS8 | termios.HUPCL | termios.CLOCAL
            options[3] = 0  # c_lflag
            options[4] = termios.B9600  # dummy ispeed
            options[5] = termios.B9600  # dummy ospeed
            # c_cc
            options[6][termios.VTIME] = self._settings.read_timer
            options[6][termios.VMIN] = self._settings.min_read_bytes
            termios.tcsetattr(self._fd, termios.TCSANOW, options)

    def apply_settings(self, settings):
        """Apply settings in Port.Settings object to port."""
        self._settings = deepcopy(settings)
        self._set_line_discipline()
        self._msb_first = settings.msb_first

        # convert tdm settings to 32 bit tdm_options value

        if settings.tdm_sync_delay == 1:
            tdm_options = TDM_SYNC_DELAY_1BIT
        elif settings.tdm_sync_delay == 2:
            tdm_options = TDM_SYNC_DELAY_2BITS
        else:
            tdm_options = 0

        if settings.tdm_sync_frame:
            tdm_options |= TDM_SYNC_FRAME_ON

        if settings.tdm_sync_short:
            tdm_options |= TDM_TX_SYNC_WIDTH_BIT

        if settings.tdm_sync_invert:
            tdm_options |= TDM_SYNC_POLARITY_INVERT

        # tdm_options[15:8] 8 bit frame count
        # valid tdm_frame_count: 1 to 256
        if settings.tdm_frame_count and (settings.tdm_frame_count < 257):
            tdm_options |= (settings.tdm_frame_count - 1) << 8

        # tdm_options[7:3] 0=384 slots, 1-31 = 2-32 slots
        # valid tdm_slot_count: 384 and 2-32
        if (settings.tdm_slot_count > 1) and (settings.tdm_slot_count < 33):
            tdm_options |= (settings.tdm_slot_count - 1) << 3

        if settings.tdm_slot_bits == 8:
            tdm_options |= TDM_SLOT_SIZE_8BITS
        elif settings.tdm_slot_bits == 12:
            tdm_options |= TDM_SLOT_SIZE_12BITS
        elif settings.tdm_slot_bits == 16:
            tdm_options |= TDM_SLOT_SIZE_16BITS
        elif settings.tdm_slot_bits == 20:
            tdm_options |= TDM_SLOT_SIZE_20BITS
        elif settings.tdm_slot_bits == 24:
            tdm_options |= TDM_SLOT_SIZE_24BITS
        elif settings.tdm_slot_bits == 28:
            tdm_options |= TDM_SLOT_SIZE_28BITS
        else:
            tdm_options |= TDM_SLOT_SIZE_32BITS

        self.tdm_options = tdm_options

        # translate Settings object into base API calls

        params = MGSL_PARAMS()
        params.mode = settings.protocol
        params.loopback = settings.internal_loopback

        params.flags = 0

        if settings.transmit_clock == Port.RXC_INPUT:
            params.flags |= HDLC_FLAG_TXC_RXCPIN
        elif settings.transmit_clock == Port.INTERNAL:
            params.flags |= HDLC_FLAG_TXC_BRG
        elif settings.transmit_clock == Port.RECOVERED:
            params.flags |= HDLC_FLAG_TXC_DPLL
        if settings.transmit_clock_invert:
            params.flags |= HDLC_FLAG_TXC_INV

        if settings.receive_clock == Port.TXC_INPUT:
            params.flags |= HDLC_FLAG_RXC_TXCPIN
        elif settings.receive_clock == Port.INTERNAL:
            params.flags |= HDLC_FLAG_RXC_BRG
        elif settings.receive_clock == Port.RECOVERED:
            params.flags |= HDLC_FLAG_RXC_DPLL
        if settings.receive_clock_invert:
            params.flags |= HDLC_FLAG_RXC_INV

        if settings.auto_rts:
            params.flags |= HDLC_FLAG_AUTO_RTS
        if settings.auto_cts:
            params.flags |= HDLC_FLAG_AUTO_CTS
        if settings.auto_dcd:
            params.flags |= HDLC_FLAG_AUTO_DCD

        params.encoding = settings.encoding
        params.clock_speed = settings.internal_clock_rate

        params.crc_type = settings.crc
        if not settings.discard_data_with_error:
            params.crc_type |= HDLC_CRC_RETURN_EX
        if not settings.discard_received_crc:
            params.crc_type |= HDLC_CRC_RETURN_EX

        params.addr = settings.hdlc_address_filter

        if settings.transmit_preamble_bits == 8:
            params.preamble_length = HDLC_PREAMBLE_LENGTH_8BITS
        elif settings.transmit_preamble_bits == 16:
            params.preamble_length = HDLC_PREAMBLE_LENGTH_16BITS
        elif settings.transmit_preamble_bits == 32:
            params.preamble_length = HDLC_PREAMBLE_LENGTH_32BITS
        elif settings.transmit_preamble_bits == 64:
            params.preamble_length = HDLC_PREAMBLE_LENGTH_64BITS
        else:
            params.preamble_length = HDLC_PREAMBLE_LENGTH_8BITS
            params.preamble = HDLC_PREAMBLE_PATTERN_NONE

        if settings.transmit_preamble_bits == 0:
            params.preamble = HDLC_PREAMBLE_PATTERN_NONE
        elif settings.transmit_preamble_pattern == 0:
            params.preamble = HDLC_PREAMBLE_PATTERN_ZEROS
        elif settings.transmit_preamble_pattern == 0xff:
            params.preamble = HDLC_PREAMBLE_PATTERN_ONES
        elif settings.transmit_preamble_pattern == 0x55:
            params.preamble = HDLC_PREAMBLE_PATTERN_10
        elif settings.transmit_preamble_pattern == 0xaa:
            params.preamble = HDLC_PREAMBLE_PATTERN_01
        elif settings.transmit_preamble_pattern == 0x7e:
            params.preamble = HDLC_PREAMBLE_PATTERN_FLAGS
        else:
            params.preamble = HDLC_PREAMBLE_PATTERN_NONE

        params.data_rate = settings.async_data_rate
        params.data_bits = settings.async_data_bits
        params.stop_bits = settings.async_stop_bits
        params.parity = settings.async_parity

        if settings.protocol == self.XSYNC:
            xctrl = 0
            xctrl |= (settings.xsync_sync_size - 1) << 17
            if settings.xsync_block_size:
                xctrl |= (1 << 16) | (settings.xsync_block_size - 1)
            try:
                fcntl.ioctl(self._fd, MGSL_IOCSXCTRL, xctrl)
            except OSError:
                pass
            try:
                fcntl.ioctl(self._fd, MGSL_IOCSXSYNC, settings.sync_pattern)
            except OSError:
                pass
        elif settings.protocol == self.BISYNC:
            self.transmit_idle_pattern = settings.sync_pattern
        elif settings.protocol == self.MONOSYNC:
            self.transmit_idle_pattern = settings.sync_pattern

        if settings.internal_clock_rate and \
            self.base_clock_rate % (settings.internal_clock_rate * 16):
            # x16 reference clock is not divisor of base clock
            # fall back to x8 reference clock
            params.flags |= HDLC_FLAG_DPLL_DIV8

        try:
            fcntl.ioctl(self._fd, MGSL_IOCSPARAMS, params)
        except OSError:
            pass

    def get_settings(self):
        """Return Port.Settings object containing current settings."""
        params = MGSL_PARAMS()
        try:
            fcntl.ioctl(self._fd, MGSL_IOCGPARAMS, params, True)
        except OSError:
            return None

        settings = Port.Settings()
        settings.protocol = params.mode
        settings.internal_loopback = bool(params.loopback)

        rxc_flags = params.flags & 0x8300
        if rxc_flags & HDLC_FLAG_RXC_BRG:
            settings.receive_clock = Port.INTERNAL
        elif rxc_flags & HDLC_FLAG_RXC_DPLL:
            settings.receive_clock = Port.RECOVERED
        elif rxc_flags & HDLC_FLAG_RXC_TXCPIN:
            settings.receive_clock = Port.TXC_INPUT
        else:
            settings.receive_clock = Port.RXC_INPUT

        if params.flags & HDLC_FLAG_RXC_INV:
            settings.receive_clock_invert = True
        else:
            settings.receive_clock_invert = False

        txc_flags = params.flags & 0x0c08
        if txc_flags & HDLC_FLAG_TXC_BRG:
            settings.transmit_clock = Port.INTERNAL
        elif txc_flags & HDLC_FLAG_TXC_DPLL:
            settings.transmit_clock = Port.RECOVERED
        elif txc_flags & HDLC_FLAG_TXC_RXCPIN:
            settings.transmit_clock = Port.RXC_INPUT
        else:
            settings.transmit_clock = Port.TXC_INPUT

        if params.flags & HDLC_FLAG_TXC_INV:
            settings.transmit_clock_invert = True
        else:
            settings.transmit_clock_invert = False

        if params.flags & HDLC_FLAG_AUTO_RTS:
            settings.auto_rts = True
        else:
            settings.auto_rts = False
        if params.flags & HDLC_FLAG_AUTO_CTS:
            settings.auto_cts = True
        else:
            settings.auto_cts = False
        if params.flags & HDLC_FLAG_AUTO_DCD:
            settings.auto_dcd = True
        else:
            settings.auto_dcd = False

        settings.encoding = params.encoding
        settings.internal_clock_rate = params.clock_speed

        settings.crc = params.crc_type & HDLC_CRC_MASK
        if params.crc_type & HDLC_CRC_RETURN_EX:
            settings.discard_data_with_error = False
        else:
            settings.discard_data_with_error = True
            
        if params.crc_type & HDLC_CRC_RETURN_EX:
            settings.discard_received_crc = False
        else:
            settings.discard_received_crc = True

        settings.hdlc_address_filter = params.addr

        if params.preamble_length == HDLC_PREAMBLE_LENGTH_8BITS:
            settings.transmit_preamble_bits = 8
        elif params.preamble_length == HDLC_PREAMBLE_LENGTH_16BITS:
            settings.transmit_preamble_bits = 16
        elif params.preamble_length == HDLC_PREAMBLE_LENGTH_32BITS:
            settings.transmit_preamble_bits = 32
        elif params.preamble_length == HDLC_PREAMBLE_LENGTH_64BITS:
            settings.transmit_preamble_bits = 64
        else:
            settings.transmit_preamble_bits = 0

        if params.preamble == HDLC_PREAMBLE_PATTERN_ZEROS:
            settings.transmit_preamble_pattern = 0
        elif params.preamble == HDLC_PREAMBLE_PATTERN_ONES:
            settings.transmit_preamble_pattern = 0xff
        elif params.preamble == HDLC_PREAMBLE_PATTERN_10:
            settings.transmit_preamble_pattern = 0x55
        elif params.preamble == HDLC_PREAMBLE_PATTERN_01:
            settings.transmit_preamble_pattern = 0xaa
        elif params.preamble == HDLC_PREAMBLE_PATTERN_FLAGS:
            settings.transmit_preamble_pattern = 0x7e
        else:
            settings.transmit_preamble_pattern = 0
            settings.transmit_preamble_bits = 0

        settings.async_data_rate = params.data_rate
        settings.async_data_bits = params.data_bits
        settings.async_stop_bits = params.stop_bits
        settings.async_parity = params.parity

        settings.xsync_block_size = 0
        settings.sync_pattern = 0
        if settings.protocol == self.XSYNC:
            arg = ctypes.c_int()
            try:
                fcntl.ioctl(self._fd, MGSL_IOCGXCTRL, arg, True)
                settings.xsync_sync_size = ((arg.value >> 17) & 3) + 1
                if arg.value & (1 << 16):
                    settings.xsync_block_size = (arg.value & 0xffff) + 1
            except OSError:
                pass
            try:
                fcntl.ioctl(self._fd, MGSL_IOCGXSYNC, arg, True)
                settings.sync_pattern = arg.value
            except OSError:
                pass
        elif settings.protocol == self.BISYNC:
            settings.sync_pattern = self.transmit_idle_pattern
        elif settings.protocol == self.MONOSYNC:
            settings.sync_pattern = self.transmit_idle_pattern

        self._settings = deepcopy(settings)

        return settings

    @property
    def line_discipline(self) -> int:
        try:
            arg = ctypes.c_int()
            fcntl.ioctl(self._fd, termios.TIOCGETD, arg, True)
            self._ldisc = arg.value
            return arg.value
        except OSError:
            return 0

    @line_discipline.setter
    def line_discipline(self, ldisc:int):
        try:
            arg = ctypes.c_int(ldisc)
            fcntl.ioctl(self._fd, termios.TIOCSETD, arg)
            self._ldisc = ldisc
        except OSError:
            pass
        
    @property
    def transmit_idle_pattern(self) -> int:
        print('get txidle =', self._tx_idle)
        return self._tx_idle & 0xffff

    @transmit_idle_pattern.setter
    def transmit_idle_pattern(self, idle:int):
        if idle == 0x7e:
            self._tx_idle = HDLC_TXIDLE_FLAGS
        elif idle == 0xaa:
            self._tx_idle = HDLC_TXIDLE_ALT_ZEROS_ONES
        elif idle == 0:
            self._tx_idle = HDLC_TXIDLE_ZEROS
        elif idle == 0xff:
            self._tx_idle = HDLC_TXIDLE_ONES
        elif idle < 0x100:
            self._tx_idle = HDLC_TXIDLE_CUSTOM_8 + idle
        else:
            self._tx_idle = HDLC_TXIDLE_CUSTOM_16 + idle
        try:
            fcntl.ioctl(self._fd, MGSL_IOCSTXIDLE, self._tx_idle)
        except OSError:
            pass

    @property
    def signals(self) -> int:
        arg = ctypes.c_int()
        try:
            fcntl.ioctl(self._fd, termios.TIOCMGET, arg, True)
        except OSError:
            return 0
        signals = 0
        if arg.value & termios.TIOCM_DTR:
            signals |= self.DTR
        if arg.value & termios.TIOCM_RTS:
            signals |= self.RTS
        if arg.value & termios.TIOCM_DSR:
            signals |= self.DSR
        if arg.value & termios.TIOCM_CD:
            signals |= self.DCD
        if arg.value & termios.TIOCM_CTS:
            signals |= self.CTS
        if arg.value & termios.TIOCM_RI:
            signals |= self.RI
        return signals

    @signals.setter
    def signals(self, signals:int):
        arg = ctypes.c_int(0)
        if signals & self.DTR:
            arg.value |= termios.TIOCM_DTR
        if signals & self.RTS:
            arg.value |= termios.TIOCM_RTS
        try:
            fcntl.ioctl(self._fd, termios.TIOCMSET, arg)
        except OSError:
            pass

    @property
    def dtr(self) -> bool:
        return bool(self.signals & Port.DTR)

    @dtr.setter
    def dtr(self, x:bool):
        arg = ctypes.c_int(termios.TIOCM_DTR)
        if x:
            code = termios.TIOCMBIS
        else:
            code = termios.TIOCMBIC
        try:
            fcntl.ioctl(self._fd, code, arg)
        except OSError:
            pass

    @property
    def rts(self) -> bool:
        return bool(self.signals & Port.RTS)

    @rts.setter
    def rts(self, x:bool):
        arg = ctypes.c_int(termios.TIOCM_RTS)
        if x:
            code = termios.TIOCMBIS
        else:
            code = termios.TIOCMBIC
        try:
            fcntl.ioctl(self._fd, code, arg)
        except OSError:
            pass

    @property
    def dsr(self) -> bool:
        return bool(self.signals & Port.DSR)

    @property
    def cts(self) -> bool:
        return bool(self.signals & Port.CTS)

    @property
    def dcd(self) -> bool:
        return bool(self.signals & Port.DCD)

    @property
    def ri(self) -> bool:
        return bool(self.signals & Port.RI)

    @property
    def txd(self) -> bool:
        return bool(self.signals & Port.TXD)

    @property
    def rxd(self) -> bool:
        return bool(self.signals & Port.RXD)

    @property
    def ll(self) -> bool:
        if self._get_if() & MGSL_INTERFACE_LL:
            return True
        return False

    @ll.setter
    def ll(self, x:bool):
        if x:
            self._set_if(self._get_if() | MGSL_INTERFACE_LL)
        else:
            self._set_if(self._get_if() & ~MGSL_INTERFACE_LL)

    @property
    def rl(self) -> bool:
        if self._get_if() & MGSL_INTERFACE_RL:
            return True
        return False

    @rl.setter
    def rl(self, x:bool):
        if x:
            self._set_if(self._get_if() | MGSL_INTERFACE_RL)
        else:
            self._set_if(self._get_if() & ~MGSL_INTERFACE_RL)

    def _get_if(self) -> int:
        interface = ctypes.c_int()
        try:
            fcntl.ioctl(self._fd, MGSL_IOCGIF, interface, True)
            return interface.value
        except OSError:
            return 0

    def _set_if(self, interface:int):
        try:
            fcntl.ioctl(self._fd, MGSL_IOCSIF, interface)
        except OSError:
            pass

    @property
    def interface(self) -> int:
        return self._get_if() & MGSL_INTERFACE_MASK

    @interface.setter
    def interface(self, x:int):
        interface = self._get_if()
        interface &= ~MGSL_INTERFACE_MASK
        interface |= x
        self._set_if(interface)

    @property
    def rts_output_enable(self) -> bool:
        return bool(self._get_if() & MGSL_INTERFACE_RTS_EN)

    @rts_output_enable.setter
    def rts_output_enable(self, x:bool):
        if x:
            self._set_if(self._get_if() | MGSL_INTERFACE_RTS_EN)
        else:
            self._set_if(self._get_if() & ~MGSL_INTERFACE_RTS_EN)

    @property
    def base_clock_rate(self) -> int:
        return self._base_clock

    @base_clock_rate.setter
    def base_clock_rate(self, x:int):
        params = MGSL_PARAMS()
        params.mode = MGSL_MODE_BASE_CLOCK
        params.clock_speed = x
        try:
            fcntl.ioctl(self._fd, MGSL_IOCSPARAMS, params)
            self._base_clock = x
        except OSError:
            pass

    @property
    def half_duplex(self) -> bool:
        return bool(self._get_if() & MGSL_INTERFACE_HALF_DUPLEX)

    @half_duplex.setter
    def half_duplex(self, x:bool):
        if x:
            self._set_if(self._get_if() | MGSL_INTERFACE_HALF_DUPLEX)
        else:
            self._set_if(self._get_if() & ~MGSL_INTERFACE_HALF_DUPLEX)

    @property
    def _msb_first(self) -> bool:
        return bool(self._get_if() & MGSL_INTERFACE_MSB_FIRST)

    @_msb_first.setter
    def _msb_first(self, x:bool):
        if x:
            self._set_if(self._get_if() | MGSL_INTERFACE_MSB_FIRST)
        else:
            self._set_if(self._get_if() & ~MGSL_INTERFACE_MSB_FIRST)

    def receive_count(self) -> int:
        try:
            arg = ctypes.c_int()
            fcntl.ioctl(self._fd, termios.TIOCINQ, arg, True)
            return arg.value
        except OSError:
            return 0

    def transmit_count(self) -> int:
        try:
            arg = ctypes.c_int()
            fcntl.ioctl(self._fd, termios.TIOCOUTQ, arg, True)
            return arg.value
        except OSError:
            return 0

    @property
    def blocked_io(self) -> bool:
        return self._blocked_io

    @blocked_io.setter
    def blocked_io(self, x):
        self._blocked_io = x
        flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
        if x:
            flags &= ~os.O_NONBLOCK
        else:
            flags |= os.O_NONBLOCK
        fcntl.fcntl(self._fd, fcntl.F_SETFL, flags)

    @property
    def termination(self) -> bool:
        return not bool(self._get_if() & MGSL_INTERFACE_TERM_OFF)

    @termination.setter
    def termination(self, x):
        if not x:
            self._set_if(self._get_if() | MGSL_INTERFACE_TERM_OFF)
        else:
            self._set_if(self._get_if() & ~MGSL_INTERFACE_TERM_OFF)

    @property
    def tdm_options(self):
        try:
            arg = ctypes.c_int()
            fcntl.ioctl(self._fd, MGSL_IOCGTDM, arg, True)
            return arg.value
        except OSError:
            return 0

    @tdm_options.setter
    def tdm_options(self, x):
        try:
            fcntl.ioctl(self._fd, MGSL_IOCSTDM, x)
        except OSError:
            pass

    def _adjust_receive_transfer_size(self, x:int) -> int:
        # adjust input according to protocol and requirements
        if self._settings.protocol == self.HDLC or \
           self._settings.protocol == self.TDM or \
           x == None:
            x = 256  # default 256 (DMA)
        else:
            if x < 1:
                x = 1
            elif x > 256:
                x = 256
            # async transfers in pairs (data+status)
            if self._settings.protocol == self.ASYNC and x % 2:
                x += 1
            # DMA (>=128) must be multiple of 4
            if x > 128 and x % 4:
                x += 4 - (x % 4)
        return x
        
    @property
    def receive_transfer_size(self) -> int:
        return self._receive_transfer_size

    @receive_transfer_size.setter
    def receive_transfer_size(self, x:int):
        x = self._adjust_receive_transfer_size(x)
        if x == self._receive_transfer_size:
            return  # nothing to do
        try:
            fcntl.ioctl(self._fd, MGSL_IOCRXENABLE, x << 16)
            self._receive_transfer_size = x
        except OSError:
            pass

    @property
    def transmit_transfer_mode(self) -> int:
        return self._transmit_transfer_mode

    @transmit_transfer_mode.setter
    def transmit_transfer_mode(self, x:int):
        if self._settings.protocol == self.HDLC:
            # HDLC always uses DMA
            x = self.DMA
        assert x == self.DMA or x == self.PIO, \
            'invalid transmit_transfer_mode'
        try:
            fcntl.ioctl(self._fd, MGSL_IOCTXENABLE, x)
            self._transmit_transfer_mode = x
        except OSError:
            pass

    @property
    def name(self) -> int:
        """Return port name."""
        return self._name

    def set_defaults(self, defaults):
        return
        # TODO: implement persistent options

    def get_defaults(self):
        if not self.is_open():
            return None
        # TODO: implement persistent options
        return self.Defaults()

    def set_fsynth_rate(self, rate: int) -> bool:
        """
        Set frequency synthesizer to specified rate.
        Return True if success (rate supported), otherwise False.
        """

        # select table and GPIO bit positions for device type
        if self._name.find('ttyUSB') != -1:
            freq_table = usb_table
            mux = self.gpio[23]
            clk = self.gpio[22]
            sel = self.gpio[21]
            dat = self.gpio[20]
        else:
            freq_table = gt4e_table
            mux = self.gpio[15]
            clk = self.gpio[14]
            sel = self.gpio[13]
            dat = self.gpio[12]

        data = 0

        # search for entry for requested output frequency
        for entry in freq_table:
            if entry.freq == rate:
                data = entry.data
                break

        if data == 0:
            return False

        clk.state = False

        # write 132 bit clock program word one bit at a time
        for i in range(0, 132):
            if (i % 32) == 0:
                dword_val = data[int(i/32)]
            if dword_val & (1 << 31):
                dat.state = True
            else:
                dat.state = False
            # pulse clock signal to load next bit
            clk.state = True
            clk.state = False
            dword_val <<= 1

        # pulse select signal to accept new word
        sel.state = True
        sel.state = False

        # set base clock input multiplexer
        # False = fixed frequency oscillator (default 14.7456MHz)
        # True  = frequency syntheziser output
        mux.state = True

        # tell port the new rate
        self.base_clock_rate = rate
        return True

    def __init__(self, name:str):
        self._fd = 0
        self._open = False
        self._tx_idle = HDLC_TXIDLE_FLAGS
        self._name = name
        self._base_clock = 14745600
        self._blocked_io = True
        self._receive_transfer_size = 256
        self._defaults = self.Defaults()
        self._settings = self.Settings()
        self._ldisc = self.N_TTY
        self.gpio = []
        for bit in range(0,32):
            gpio = self.GPIO(self, bit)
            self.gpio.append(gpio)

    def __del__(self):
        if self.is_open():
            self.close()

    def __repr__(self):
        return 'Port object at ' + hex(id(self)) + '\n' + \
            'name = ' + self.name

    def __str__(self):
        return self.__repr__()


# This code programs the frequency synthesizer on the SyncLink GT2e/GT4e
# PCI express serial adapters and SyncLink USB device to a specified frequency
# and selects the synthesizer output as the adapter base clock. ONLY the GT2e/GT4e
# cards and SyncLink USB device have this feature. Copy and paste this code into
# applications that require a non-standard base clock frequency.
#
# SyncLink GT family serial adapters have a fixed 14.7456MHz base clock.
# The serial controller generates data clocks by dividing the base clock
# by an integer. Only discrete data clock values can be generated
# exactly from a given base clock frequency. When an exact data clock
# value is required that cannot be derived by dividing 14.7456MHz by
# and integer, a different base clock value must be used. One way to
# do this is special ordering a different fixed base clock which is
# installed at the factory.
#
# The SyncLink GT2e, GT4e and USB serial devices have both
# a 14.7456MHz fixed base clock and a variable frequency synthesizer.
# The serial controller can use either as the base clock.
#
# The frequency synthesizer is an Integrated Device Technologies (IDT)
# ICS307-3 device. The reference clock input to the synthesizer is
# the fixed 14.7456MHz clock.
# GT2E/GT4E uses synthesizer CLK1 output
# USB uses synthesizer CLK3 output
# Refer to the appropriate hardware user's manual for more details.
#
# The synthesizer SPI programming interface is connected to the serial
# controller general purpose I/O signals. The GPIO portion of the serial
# API is used to program the synthesizer with a 132 bit word. This word
# is calculated using the IDT Versaclock software available at www.idt.com
#
# Contact Microgate for help in producing a programming word for a specific
# frequency output. Several common frequencies are included in this code.
# Maximum supported base clock is 66MHz
#
# Note:
# After programming the frequency synthesizer and selecting it
# as the base clock, each individual port of a card must be configured with
# MgslSetOption(fd, MGSL_OPT_CLOCK_BASE_FREQ, freq_value);
#
# This allows the device driver to correctly calculate divisors
# for a specified data clock rate. All ports on a card share
# a common base clock.

# Each frequency table entry contains an output frequency
# and the associated 132 bit synthesizer programming word
# to produce the frequency.

# The programming word comes from the Versaclock 2 software
# parsed into 5 32-bit integers. The final 4 bits are placed
# in the most significant 4 bits of the final 32-bit integer.
class FREQ_TABLE_ENTRY:
    def __init__(self, freq, data):
        self.freq = freq  # frequency
        self.data = data  # synth programming data


# GT2e/GT4e
#
# Base Clock = dedicated 14.7456MHz oscillator
#
# ICS307-3 (clock):
# - reference clock = 14.7456MHz oscillator
# - VDD = 3.3V
# - CLK1 (pin 8) output drives FPGA fsynth input
gt4e_table = [
    FREQ_TABLE_ENTRY(
        1228800,  [0x1800155E, 0x29A00000, 0x00000000, 0x0000DFFF, 0x60000000]),
    FREQ_TABLE_ENTRY(
        2875000,  [0x08001494, 0x28A00000, 0x00000000, 0x000211FE, 0x20000000]),
    FREQ_TABLE_ENTRY(
        12288000, [0x29BFDC00, 0x61200000, 0x00000000, 0x0000A5FF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        14745600, [0x38003C05, 0x24200000, 0x00000000, 0x000057FF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        16000000, [0x280CFC02, 0x64A00000, 0x00000000, 0x000307FD, 0x20000000]),
    FREQ_TABLE_ENTRY(
        16384000, [0x08001402, 0xA1200000, 0x00000000, 0x0000A5FF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        19660800, [0x08001403, 0xE1200000, 0x00000000, 0x0000A1FF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        20000000, [0x00001403, 0xE0C00000, 0x00000000, 0x00045E02, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        23040000, [0x08001404, 0xA0A00000, 0x00000000, 0x0003A7FC, 0x60000000]),
    FREQ_TABLE_ENTRY(
        24000000, [0x00001404, 0xE1400000, 0x00000000, 0x0003D5FC, 0x20000000]),
    FREQ_TABLE_ENTRY(
        27000000, [0x00001405, 0x60C00000, 0x00000000, 0x00061E04, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        28219200, [0x00001405, 0xA1400000, 0x00000000, 0x0003C1FC, 0x20000000]),
    FREQ_TABLE_ENTRY(
        28800000, [0x18001405, 0x61A00000, 0x00000000, 0x0000EBFF, 0x60000000]),
    FREQ_TABLE_ENTRY(
        30000000, [0x20267C05, 0x64C00000, 0x00000000, 0x00050603, 0x30000000]),
    FREQ_TABLE_ENTRY(
        32000000, [0x21BFDC00, 0x5A400000, 0x00000000, 0x0004D206, 0x30000000]),
    FREQ_TABLE_ENTRY(
        33200000, [0x00001400, 0xD8C00000, 0x00000000, 0x0005E204, 0xB0000000]),
    FREQ_TABLE_ENTRY(
        33320000, [0x08001400, 0xD8A00000, 0x00000000, 0x0001C7FE, 0x60000000]),
    FREQ_TABLE_ENTRY(
        38400000, [0x00001406, 0xE1800000, 0x00000000, 0x00098009, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        40000000, [0x00001406, 0xE1800000, 0x00000000, 0x0009E609, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        45056000, [0x08001406, 0xE0200000, 0x00000000, 0x000217FE, 0x20000000]),
    FREQ_TABLE_ENTRY(
        50000000, [0x00001400, 0x58C00000, 0x00000000, 0x0005E604, 0x70000000]),
    FREQ_TABLE_ENTRY(
        64000000, [0x21BFDC00, 0x12000000, 0x00000000, 0x000F5E14, 0xF0000000])
]


# SyncLink USB
#
# Base Clock = ICS307-3 CLK1 (pin 8) output (power up default = 14.7456MHz)
#
# ICS307-3 (xtal):
# - reference clock = 14.7456MHz xtal
# - VDD = 3.3V
# - CLK3 (pin 14) output drives FPGA fsynth input
# - CLK1 (pin 8)  output drives FPGA base clock input
#
# Note: CLK1 and CLK3 outputs must always be driven to prevent floating
# clock inputs to the FPGA. When calculating programming word with Versaclock,
# select same output on CLK1 and CLK3 or select CLK1 as multiple of CLK3.
usb_table = [
    FREQ_TABLE_ENTRY(
        1228800,  [0x296C1402, 0x25200000, 0x00000000, 0x00009FFF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        2875000,  [0x317C1400, 0x21A00000, 0x00000000, 0x0000BBFE, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        12288000, [0x28401400, 0xE5200000, 0x00000000, 0x00009BFF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        14745600, [0x28481401, 0xE5200000, 0x00000000, 0x0000A5FF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        16000000, [0x284C1402, 0x64A00000, 0x00000000, 0x000307FD, 0x20000000]),
    FREQ_TABLE_ENTRY(
        16384000, [0x28501402, 0xE4A00000, 0x00000000, 0x0001F9FE, 0x20000000]),
    FREQ_TABLE_ENTRY(
        19660800, [0x38541403, 0x65A00000, 0x00000000, 0x0000B1FF, 0xA0000000]),
    FREQ_TABLE_ENTRY(
        20000000, [0x205C1404, 0x65400000, 0x00000000, 0x00068205, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        23040000, [0x38601404, 0xE5A00000, 0x00000000, 0x0001B3FE, 0x60000000]),
    FREQ_TABLE_ENTRY(
        24000000, [0x20601404, 0xE5400000, 0x00000000, 0x0003D5FC, 0x20000000]),
    FREQ_TABLE_ENTRY(
        27000000, [0x20641405, 0x64C00000, 0x00000000, 0x00061E04, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        28219200, [0x20641405, 0x64C00000, 0x00000000, 0x0004F603, 0x70000000]),
    FREQ_TABLE_ENTRY(
        28800000, [0x38641405, 0x65A00000, 0x00000000, 0x0000EBFF, 0x60000000]),
    FREQ_TABLE_ENTRY(
        30000000, [0x20641405, 0x64C00000, 0x00000000, 0x00050603, 0x30000000]),
    FREQ_TABLE_ENTRY(
        32000000, [0x206C1406, 0x65400000, 0x00000000, 0x00049E03, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        33200000, [0x20681405, 0xE4C00000, 0x00000000, 0x00061804, 0x70000000]),
    FREQ_TABLE_ENTRY(
        33320000, [0x21FBB800, 0x05400000, 0x00000000, 0x00038BFC, 0x20000000]),
    FREQ_TABLE_ENTRY(
        38400000, [0x20701406, 0xE5800000, 0x00000000, 0x00098009, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        40000000, [0x20701406, 0xE5800000, 0x00000000, 0x0009E609, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        45056000, [0x28701406, 0xE4200000, 0x00000000, 0x000217FE, 0x20000000]),
    FREQ_TABLE_ENTRY(
        50000000, [0x20741407, 0x65400000, 0x00000000, 0x00068205, 0xF0000000]),
    FREQ_TABLE_ENTRY(
        64000000, [0x20781400, 0x4D400000, 0x00000000, 0x00049E03, 0xF0000000])
]
