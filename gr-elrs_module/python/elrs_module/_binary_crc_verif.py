import pmt
import numpy as np
from gnuradio import gr
from threading import Lock
from typing import Optional

class binary_crc_verify(gr.basic_block):
    def __init__(self):
        gr.basic_block.__init__(self, name="_binary_crc_verify", in_sig=[np.uint8], out_sig=None)
        
        self._buffer = bytearray()
        self._curr_payload_len = 0
        self._buf_offset = 0

        self.message_port_register_out(pmt.intern('out')) # type: ignore

    def forecast(self, noutput_items, ninput_items_required):
        ninput_items_required[0] = 1

    def work(self, input_items, output_items):
        ninput_items = len(input_items[0])
        
        if ninput_items == 0:
            return 0

        # Check for a frame length tag on the first available item.
        tags = self.get_tags_in_window(0, 0, ninput_items, pmt.intern("frame_info"))
        if tags and pmt.dict_has_key(tags[0].value, pmt.intern("pay_len")):
            entry = pmt.dict_ref(tags[0].value, pmt.intern("pay_len"))
            if pmt.is_integer(entry):
                self._curr_payload_len = pmt.to_long(pmt.dict_ref(tags[0].value, pmt.intern("pay_len")))
            else:
                raise TypeError('Type of \'pay_len\' stream tag is not an integer!')

        consume = 0
        if self._curr_payload_len > 0:
            # Calculate how many items we can process from the input buffer.
            consume = min(ninput_items, self._curr_payload_len - len(self._buffer))
            if consume > 0:
                self._buffer.extend(input_items[0][:consume])

            # If the buffer is now full, publish it as a message and reset state.
            if len(self._buffer) == self._curr_payload_len:
                self.message_port_pub(pmt.intern('out'), pmt.init_u8vector(len(self._buffer), self._buffer))
                self._curr_payload_len = 0
                self._buffer.clear()

        return consume