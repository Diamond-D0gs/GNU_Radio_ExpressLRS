"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt

FHSS_DOMAINS = {
    "AU915" : {
        "start_freq"  : 915500000,
        "end_freq"    : 926900000,
        "center_freq" : 921000000,
        "freq_count"  : 20
    },
    "FCC915" : {
        "start_freq"  : 903500000,
        "end_freq"    : 926900000,
        "center_freq" : 915000000,
        "freq_count"  : 40
    },
    "EU868" : {
        "start_freq"  : 865275000,
        "end_freq"    : 869575000,
        "center_freq" : 868000000,
        "freq_count"  : 13
    },
    "IN866" : {
        "start_freq"  : 865375000,
        "end_freq"    : 866950000,
        "center_freq" : 866000000,
        "freq_count"  : 4
    },
    "AU433" : {
        "start_freq"  : 433420000,
        "end_freq"    : 434420000,
        "center_freq" : 434000000,
        "freq_count"  : 3
    },
    "EU433" : {
        "start_freq"  : 433100000,
        "end_freq"    : 434450000,
        "center_freq" : 434000000,
        "freq_count"  : 3
    },
    "US433" : {
        "start_freq"  : 433250000,
        "end_freq"    : 438000000,
        "center_freq" : 434000000,
        "freq_count"  : 8
    },
    "US433W" : {
        "start_freq"  : 423500000,
        "end_freq"    : 438000000,
        "center_freq" : 434000000,
        "freq_count"  : 20
    },
    "ISM2G4" : {
        "start_freq"  : 2400400000,
        "end_freq"    : 2479400000,
        "center_freq" : 2440000000,
        "freq_count"  : 80
    }
}

PACKET_RATE_LIMIT = 1000

class FHSSHandler:
    def __init__(self, domain_settings: dict[str, dict[str, int]]):
        self.frequency_sequence: list[int] = list()
        self.frequency_index: int = 0

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    def __init__(self, domain="FCC915", packet_rate=25):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='Embedded Python Block',   # will show up in GRC
            in_sig=[],
            out_sig=[]
        )

        self.message_port_register_in(pmt.intern('trigger'))
        self.set_msg_handler(pmt.intern('trigger'), self._initial_set)

        self.message_port_register_out(pmt.intern('set_period'))
        
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
        
        self.counter = 0

        print('done 1')

    def _initial_set(self, msg):
        self.set_msg_handler(pmt.intern('trigger'), self._trigger_handler)
        self.message_port_pub(pmt.intern('set_period'), pmt.cons(pmt.intern("ignored_key"), pmt.from_long(1000 // self.packet_rate)))
        print('done 2')
        
    def _trigger_handler(self, msg):
        print(f'Test {self.counter}')
        self.counter += 1

    def work(self, input_items, output_items):
        # output_items[0][:] = input_items[0] * self.example_param
        # return len(output_items[0])
        pass
