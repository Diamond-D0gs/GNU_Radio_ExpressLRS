import pmt
import numpy as np
from gnuradio import gr
from hashlib import md5

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

class fhss_controller(gr.sync_block):
    # This is the corrected line with default values
    def __init__(self, binding_phrase="", freq_start=0.0, freq_stop=0.0, freq_count=1, freq_center=0.0, packet_hop_count=2, disable=False):
        gr.sync_block.__init__(self,
            name='FHSS Controller',
            in_sig=None,
            out_sig=None)
        
        # Store parameters passed from GRC
        self.binding_phrase = binding_phrase
        self.freq_start = freq_start
        self.freq_stop = freq_stop
        self.freq_count = freq_count
        self.freq_center = freq_center
        self.disable = disable
        self.packet_hop_count = packet_hop_count

        # Register message ports
        self.message_port_register_in(pmt.intern("msg_in"))
        self.message_port_register_out(pmt.intern("msg_out"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg)

        # --- Setup logic from your script ---
        self.FHSS_SEQUENCE_LEN = 256
        self.OTA_VERSION_ID = 6
        
        if self.freq_count > 1:
            self.freq_spread = abs(self.freq_stop - self.freq_start) // (self.freq_count - 1)
        else:
            self.freq_spread = 0 # Provide a safe default

        # Add another check for the next line
        if self.freq_count > 0:
            self.num_primary_bands = (self.FHSS_SEQUENCE_LEN // self.freq_count) * self.freq_count
        else:
            self.num_primary_bands = 0 # Provide a safe default

        uid_bytes = md5(str(f'-DMY_BINDING_PHRASE="{binding_phrase}"').encode('utf-8')).digest()[:6]
        self.seed = ((uid_bytes[2] << 24) + (uid_bytes[3] << 16) + (uid_bytes[4] << 8) + (uid_bytes[5] ^ self.OTA_VERSION_ID)) & 0xFFFFFFFF
        self.freq_sequence = []
        self.fhss_index = 0
        self.packet_count = 0
        
        self.build_random_fhss_sequence()

    def elrs_rng(self):
        return ((214013 * self.seed + 2531011) % 2147483648) >> 16
    
    def build_random_fhss_sequence(self):
        # Only build if freq_count is valid
        if self.freq_count < 2: return

        for i in range(self.num_primary_bands):
            self.freq_sequence.append(i % self.freq_count)
        
        for i in range(1, self.num_primary_bands):
             if (i % self.freq_count) != 0:
                offset = (i // self.freq_count) * self.freq_count
                rand = (self.elrs_rng() % (self.freq_count - 1)) + 1
                self.freq_sequence[i], self.freq_sequence[offset + rand] = self.freq_sequence[offset + rand], self.freq_sequence[i]

    def handle_msg(self, msg):
        if not self.disable:
            if self.packet_hop_count % self.packet_count == 0:
                current_freq_index = self.freq_sequence[self.fhss_index]
                absolute_freq = self.freq_start + (current_freq_index * self.freq_spread)
                freq_offset = absolute_freq - self.freq_center

                key = pmt.intern("freq_temp")
                value = pmt.from_double(freq_offset + 3.7e6) # Temp fix
                output_msg = pmt.cons(key, value)

                self.message_port_pub(pmt.intern("msg_out"), output_msg)
                
                self.fhss_index = (self.fhss_index + 1) % self.freq_count

            self.packet_count += 1
        else:
            key = pmt.intern("freq_temp")
            value = pmt.from_double(self.freq_center + 3.7e6) # Temp fix
            output_msg = pmt.cons(key, value)

            self.message_port_pub(pmt.intern("msg_out"), output_msg)


    def work(self, input_items, output_items):
        return 0