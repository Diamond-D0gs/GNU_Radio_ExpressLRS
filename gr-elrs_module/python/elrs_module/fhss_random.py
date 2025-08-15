class FHSSRandom:
    def __init__(self, seed: int):
        self._seed = seed

    def rng_seed(self, new_seed: int) -> None:
        self._seed = new_seed

    def rng(self) -> int:
        return ((214013 * self._seed + 2531011) % 2147483648) >> 16

    def rng_n(self, max: int) -> int:
        return self.rng() % max
    
    def rng_8_bit(self) -> int:
        return self.rng() & 0xFF
    
    def rng_5_bit(self) -> int:
        return self.rng & 0x1F