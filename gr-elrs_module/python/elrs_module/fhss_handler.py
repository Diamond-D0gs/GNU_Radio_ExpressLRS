class FHSSHandler:
    def __init__(self, uid: bytes, domain_settings: dict[str, dict[str, int]]):
        self.sync_channel = domain_settings['freq_count'] // 2
        self.freq_range = domain_settings['stop_freq'] - domain_settings['start_freq']
        self.freq_spread = self.freq_range // (domain_settings['freq_count'] - 1)
        self.band_count = (256 // domain_settings['freq_count']) * domain_settings['freq_count']
        self.rand = FHSSRandom(uid_mac_seed_get(uid))
        self.config = domain_settings

        self._frequencies = list()
        self._index = 0

        for i in range(self.band_count):
            if i % domain_settings['freq_count'] == 0:
                self._frequencies.append(self.sync_channel)
            elif i % domain_settings['freq_count'] == self.sync_channel:
                self._frequencies.append(0)
            else:
                self._frequencies.append(i % domain_settings['freq_count'])

        for i in range(self.band_count):
            if i % domain_settings['freq_count'] != 0:
                offset = (i // domain_settings['freq_count']) * domain_settings['freq_count']
                rand = self.rand.rng_n(domain_settings['freq_count'] - 1) + 1
                self._frequencies[i], self._frequencies[offset + rand] = self._frequencies[offset + rand], self._frequencies[i]

    def get_init_freq(self) -> int:
        return self.config['start_freq'] + (self.sync_channel * self.freq_spread)
    
    def get_curr_index(self) -> int:
        return self._index
    
    def on_sync_channel(self) -> int:
        return self._frequencies[self._index] == self.sync_channel
    
    def set_curr_index(self, index: int) -> None:
        self._index = index % self.band_count