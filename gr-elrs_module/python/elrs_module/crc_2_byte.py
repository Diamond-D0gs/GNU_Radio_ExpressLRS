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