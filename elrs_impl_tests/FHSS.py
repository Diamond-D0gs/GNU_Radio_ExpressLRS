FHSS_SEQUENCE_LEN = 256

fhss_domain_configs = {
    "AU915":  (915500000, 926900000, 20, 921000000),
    "FCC915": (903580000, 926900000, 40, 915000000),
    "EU868":  (865275000, 869575000, 13, 868000000),
    "IN866":  (865375000, 866950000, 4,  866000000),
    "AU433":  (433420000, 434420000, 3,  434000000),
    "EU433":  (433100000, 434450000, 3,  434000000),
    "US433":  (433250000, 438000000, 8,  434000000),
    "US433W": (423500000, 438000000, 20, 434000000),
}

class fhss_random:
    def __init__(self, seed):
        self._seed = seed

    def rng(self) -> int:
        self._seed = ((214013 * self._seed + 2531011) % 2147483648) & 0xFFFFFFFF
        return self._seed >> 16
    
    def update_seed(self, new_seed) -> None:
        self._seed = new_seed

    def rng_n(self, max) -> int:
        return self.rng() % max
    
    def rng_8(self) -> int:
        return self.rng() & 0xFF
    
    def rng_5(self) -> int:
        return self.rng() & 0x1F

class FHSSHandler:
    def __init__(self, domain, seed):
        if isinstance(domain, str):
            if domain not in fhss_domain_configs:
                raise ValueError(f'\'{domain}\' is not a valid domain.')
        else:
            raise TypeError(f'\'domain\' must be of type str')
        
        if isinstance(seed, int):
            if (seed < 0) or (seed >= 0xFFFFFFFF):
                raise ValueError(f'\'seed\' is out of bounds (0 <= seed < 2^32).')
        else:
            raise TypeError(f'\'seed\' must be of type int')

        self.fhss_config = fhss_domain_configs[domain]
        
        self.sync_channel = int(self.fhss_config[2] // 2)
        self.freq_spread = int((self.fhss_config[1] - self.fhss_config[0]) // (self.fhss_config[2] - 1))
        self.primary_band_count = int((FHSS_SEQUENCE_LEN // self.fhss_config[2]) * self.fhss_config[2])

        self.fhss_ptr = 0
        self.fhss_sequence = []
        self._build_randomized_fhss_sequence(seed, self.fhss_config)

    def _build_randomized_fhss_sequence(self, seed, fhss_config):
        for i in range(self.primary_band_count):
            temp = i % fhss_config[2]
            if temp == 0:
                self.fhss_sequence.append(self.sync_channel)
            elif temp == self.sync_channel:
                self.fhss_sequence.append(0)
            else:
                self.fhss_sequence.append(temp)

        rng = fhss_random(seed)

        for i in range(self.primary_band_count):
            if (i % fhss_config[2]) != 0:
                rand = rng.rng_n(fhss_config[2] - i) + 1
                offset = (i // fhss_config[2]) * fhss_config[2]
                self.fhss_sequence[i], self.fhss_sequence[offset + rand] = self.fhss_sequence[offset + rand], self.fhss_sequence[i]

    def get_initial_freq(self) -> int:
        return self.fhss_sequence[0]
    
    def get_minimum_freq(self) -> int:
        return self.fhss_config[0]
    
    def get_maximum_freq(self) -> int:
        return self.fhss_config[1]