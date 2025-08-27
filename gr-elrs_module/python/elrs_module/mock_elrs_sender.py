from .fhss_handler import FHSSHandler
from typing import Optional, TextIO
from threading import Thread, Lock
from pathlib import Path
from gnuradio import gr
from hashlib import md5
import time
import pmt

class MockELRSSender(gr.sync_block):
    def __init__(self, filepath: str='', binding_phrase: str='DefaultBindingPhrase', packet_rate: int=25, start_freq: int=903500000, stop_freq: int=926900000, center_freq: int=915000000, freq_count: int=40, packet_hop_interval: int=2, timing_adjust: float=1.0):
        gr.sync_block.__init__(
            self,
            name='Mock ELRS Sender',
            in_sig=None,  # No streaming input
            out_sig=None  # No streaming output
        )

        self.message_port_register_out(pmt.intern('freq_update')) # type: ignore
        self.message_port_register_out(pmt.intern('out')) # type: ignore

        self.filepath_str = filepath
        self.filepath = Path(filepath)
        self.file: Optional[TextIO] = None
        self.binding_phrase = binding_phrase
        self.packet_hop_interval = packet_hop_interval
        self.packet_rate = packet_rate
        self.packet_dispatch_time = packet_rate / 1000.0
        self.timing_adjust = timing_adjust
        self.packet_count: int = 0

        self.uid = md5(str(f'-DMY_BINDING_PHRASE="{binding_phrase}"').encode('utf-8')).digest()[:6]

        self.domain_settings = {
            'start_freq'  : start_freq,
            'stop_freq'   : stop_freq,
            'center_freq' : center_freq,
            'freq_count'  : freq_count
        }

        self.fhss_handler = FHSSHandler(self.uid, self.domain_settings)

        self.lock = Lock()
        self.stop_thread = False
        self.thread = Thread(target=self._thread_loop)
        self.thread.daemon = True

    def start(self) -> bool:
        if not self.filepath.is_file():
            print(f'Mock ELRS Sender: \'{self.filepath_str}\' is not a valid filepath!')
            return False
        
        self.file = open(self.filepath, 'r', encoding='utf-8')

        self.message_port_pub(pmt.intern('freq_update'), pmt.from_long(self.fhss_handler.get_curr_freq())) # type: ignore
        self.fhss_handler.update_to_next_freq()

        self.thread.start()

        return True

    def stop(self) -> bool:
        with self.lock:
            self.stop_thread = True
        
        time.sleep(0.1)

        self.file.close()

        return True


    def _thread_loop(self) -> None:
        while True:
            start_time = time.time()

            with self.lock:
                if self.stop_thread:
                    return
                
            if self.packet_count != 0 and self.packet_count % self.packet_hop_interval == 0:
                self.message_port_pub(pmt.intern('freq_update'), pmt.from_long(self.fhss_handler.get_curr_freq())) # type: ignore
                self.fhss_handler.update_to_next_freq()
                
            curr_line: str = self.file.readline()
            if len(curr_line) == 0:
                print('Mock ELRS Sender: All lines have been read out of test file, terminating transmission thread.')
                return
            
            curr_bytes = bytearray.fromhex(curr_line)
            self.message_port_pub(pmt.intern('out'), pmt.init_u8vector(len(curr_bytes), curr_bytes)) # type: ignore
            self.packet_count += 1

            with self.lock:
                if self.stop_thread:
                    return
            
            time.sleep(max(0, ((self.packet_dispatch_time * self.timing_adjust) - (time.time() - start_time))))
                

    def work(self, input_items, output_items) -> None:
        return -1