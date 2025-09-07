import pmt
import time
import ctypes
import numpy as np
from hashlib import md5
from gnuradio import gr
from pathlib import Path
from typing import Optional, TextIO

class Crc2Byte:
    _CRCTAB_LEN = 256

    def __init__(self, bits: int, poly: int):
        if not (8 <= bits <= 16):
            raise ValueError("CRC bit-width must be between 8 and 16.")

        self.bits = bits
        self.poly = poly
        self.bitmask = (1 << self.bits) - 1
        
        # Pre-compute the CRC lookup table
        self.crctab = self._generate_table()

    def _generate_table(self) -> list[int]:
        crctab = [0] * self._CRCTAB_LEN
        highbit = 1 << (self.bits - 1)

        for i in range(self._CRCTAB_LEN):
            crc = i << (self.bits - 8)
            for _ in range(8):
                if crc & highbit:
                    crc = (crc << 1) ^ self.poly
                else:
                    crc = crc << 1
            crctab[i] = crc & self.bitmask
        return crctab

    def calc(self, data: bytes, initial_crc: int = 0) -> int:
        crc = initial_crc

        for byte in data:
            lookup_index = ((crc >> (self.bits - 8)) ^ byte) & 0xFF
            crc = (crc << 8) ^ self.crctab[lookup_index]

        return crc & self.bitmask

# The final, top-level packet structure
class OTA_Packet4_s(ctypes.Structure):
    """
    Main packet structure corresponding to OTA_Packet4_s.
    """
    _pack_ = 1
    _fields_ = [
        # First byte: type and crcHigh
        ("type", ctypes.c_uint8, 2),
        ("crcHigh", ctypes.c_uint8, 6),
        # Main payload union (6 bytes)
        ("payload", ctypes.c_uint8 * 6),
        # Last byte: crcLow
        ("crcLow", ctypes.c_uint8),
    ]

class elrs_receiver_data_gen(gr.sync_block):
    """
    Receives a trigger message. On each trigger, it formats a string
    with the value of a 'counter' variable from the top_block,
    sends it as a new message, and increments the counter.
    """
    def __init__(self, bindingPhrase: str='DefaultBindingPhrase', filepath: str='', loopFile:bool =False):
        gr.sync_block.__init__(self,
            name='ELRS Receiver Data Gen',
            in_sig=None,
            out_sig=None)
        
        self.filepath_str = filepath
        self.filepath = Path(filepath)
        self.file: Optional[TextIO] = None
        self.crc_calc = Crc2Byte(16, 0x3D65)
        self.loop_file: bool = loopFile
        self.done: bool = False

        self.packet_datas: list[bytes] = []
        self.packet_data_dict: dict[bytes, int] = {}

        uid = md5(str(f'-DMY_BINDING_PHRASE="{bindingPhrase}"').encode('utf-8')).digest()[:6]
        self.ota_crc = ((uid[4] << 8) | uid[5]) ^ 4
        
        self.message_port_register_in(pmt.intern("msg_in"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg)

    def handle_msg(self, msg) -> None:
        if not pmt.is_u8vector(msg):
            print('PMT was not of type u8vector!')
            return
        
        ota = OTA_Packet4_s.from_buffer(bytearray(pmt.u8vector_elements(msg)))
        data = bytes(ota.payload)
        
        recv_crc: int = (ota.crcHigh << 8) | ota.crcLow
        data_crc: int = self.crc_calc.calc(data, self.ota_crc)

        print(recv_crc, data_crc)

        print(data.hex())

        if recv_crc != data_crc:
            print('CRC calculated from packet data does not match included CRC!')

    def start(self) -> bool:
        if not self.filepath.is_file():
            print(f'ELRS Transmitter Data Gen: \'{self.filepath_str}\' is not a valid filepath!')
            return False
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                curr_line = file.readline()
                while len(curr_line) != 0:
                    self.packet_datas.append(bytes.fromhex(curr_line))
                    curr_line = file.readline()
        except Exception as e:
            print('ELRS Transmitter Data Gen: Exception occured while trying to open file.\n', e)
            return False
        
        for i in range(len(self.packet_datas)):
            self.packet_data_dict[self.packet_datas[i]] = i

        return True

    def stop(self) -> bool:
        return True

    def work(self, input_items, output_items):
        # This block only processes messages, so work() does nothing.
        return 0