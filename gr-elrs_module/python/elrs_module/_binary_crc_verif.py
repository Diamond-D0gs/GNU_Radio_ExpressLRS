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

    def general_work(self, input_items, output_items):
        ninput_items = len(input_items)
        if ninput_items == 0:
            return 0
        
        in0 = input_items[0]

        # Only check for tags if we are not currently accumulating a frame
        if self._curr_payload_len == 0:
            tags = self.get_tags_in_window(0, 0, ninput_items)
            for tag in tags:
                key = pmt.symbol_to_string(tag.key) # type: ignore
                if key == "frame_info":
                    # The PMT API requires 3 arguments for dict_ref
                    pay_len_pmt = pmt.dict_ref(tag.value, pmt.intern("pay_len"), pmt.PMT_NIL) # type: ignore
                    
                    if pmt.is_integer(pay_len_pmt): # type: ignore
                        self._curr_payload_len = pmt.to_long(pay_len_pmt) # type: ignore
                        # Break after finding the first valid tag
                        break 
                    else:
                        self.d_logger.error("Type of 'pay_len' in 'frame_info' tag is not an integer!")

        # Amount of data to consume in this call
        consume = 0
        if self._curr_payload_len > 0:
            # Calculate how many items we can process from the input buffer.
            needed = self._curr_payload_len - len(self._buffer)
            consume = min(ninput_items, needed)
            
            if consume > 0:
                self._buffer.extend(in0[:consume])

            # If the buffer is now full, publish it as a message and reset state.
            if len(self._buffer) == self._curr_payload_len:
                # Create a u8vector from the bytearray to publish
                msg = pmt.init_u8vector(len(self._buffer), self._buffer) # type: ignore
                self.message_port_pub(pmt.intern('out'), msg) # type: ignore
                
                # Reset state for the next frame
                self._curr_payload_len = 0
                self._buffer.clear()

        # Tell the scheduler how many items we consumed
        self.consume(0, consume)
        return 0 # This block produces no stream output, only messages