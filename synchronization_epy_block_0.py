"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
from hashlib import md5
import pmt

FHSS_DOMAINS = {
    "AU915" : {
        "start_freq"  : 915500000,
        "stop_freq"    : 926900000,
        "center_freq" : 921000000,
        "freq_count"  : 20
    },
    "FCC915" : {
        "start_freq"  : 903500000,
        "stop_freq"    : 926900000,
        "center_freq" : 915000000,
        "freq_count"  : 40
    },
    "EU868" : {
        "start_freq"  : 865275000,
        "stop_freq"    : 869575000,
        "center_freq" : 868000000,
        "freq_count"  : 13
    },
    "IN866" : {
        "start_freq"  : 865375000,
        "stop_freq"    : 866950000,
        "center_freq" : 866000000,
        "freq_count"  : 4
    },
    "AU433" : {
        "start_freq"  : 433420000,
        "stop_freq"    : 434420000,
        "center_freq" : 434000000,
        "freq_count"  : 3
    },
    "EU433" : {
        "start_freq"  : 433100000,
        "stop_freq"    : 434450000,
        "center_freq" : 434000000,
        "freq_count"  : 3
    },
    "US433" : {
        "start_freq"  : 433250000,
        "stop_freq"    : 438000000,
        "center_freq" : 434000000,
        "freq_count"  : 8
    },
    "US433W" : {
        "start_freq"  : 423500000,
        "stop_freq"    : 438000000,
        "center_freq" : 434000000,
        "freq_count"  : 20
    },
    "ISM2G4" : {
        "start_freq"  : 2400400000,
        "stop_freq"    : 2479400000,
        "center_freq" : 2440000000,
        "freq_count"  : 80
    }
}

PACKET_RATE_LIMIT = 1000
OTA_VERSION_ID = 4

def uid_mac_seed_get(uid: bytes) -> int:
    uid_list = list(uid)
    return ((uid_list[2] << 24) + (uid_list[3] << 16) + (uid_list[4] << 8) + (uid_list[5] ^ OTA_VERSION_ID)) & 0xFFFFFFFF

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
        return self.rng() & 0x1F

class FHSSHandler:
    def __init__(self, uid: bytes, domain_settings: dict[str, int]):
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

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    def __init__(self, domain="FCC915", packet_rate=25, binding_phrase="DefaultBindingPhrase"):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='Embedded Python Block',   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )

        self.message_port_register_in(pmt.intern('trigger'))
        self.set_msg_handler(pmt.intern('trigger'), self._initial_set)

        self.message_port_register_out(pmt.intern('set_period'))
        self.message_port_register_out(pmt.intern('set_frequency'))
        
        if domain in FHSS_DOMAINS:
            self.domain = FHSS_DOMAINS[domain]
        else:
            self.domain = FHSS_DOMAINS["FCC915"]
            print(f'Provided domain, \"{domain}\", is not valid. Defaulting to \"FCC915\".')

        if packet_rate <= PACKET_RATE_LIMIT:
            self.packet_rate = packet_rate
        else:
            self.packet_rate = PACKET_RATE_LIMIT
            print(f'Provided packet rate, {packet_rate}, exceeds packet rate limit of {PACKET_RATE_LIMIT}.')

        self.uid = md5(str(f'-DMY_BINDING_PHRASE="{binding_phrase}"').encode('utf-8')).digest()[:6]
        self.fhss = FHSSHandler(self.uid, self.domain)
        
        self.counter = 0

    def _initial_set(self, msg):
        self.set_msg_handler(pmt.intern('trigger'), self._trigger_handler)
        self.message_port_pub(pmt.intern('set_period'), pmt.cons(pmt.intern("ignored_key"), pmt.from_long(1000 // self.packet_rate)))
        
    def _trigger_handler(self, msg):
        print(f'Test {self.counter}')
        self.counter += 1

    def work(self, input_items, output_items):
        # output_items[0][:] = input_items[0] * self.example_param
        # return len(output_items[0])
        pass
