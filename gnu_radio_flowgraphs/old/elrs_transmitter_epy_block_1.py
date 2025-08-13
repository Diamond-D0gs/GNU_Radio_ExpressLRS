import pmt
import numpy as np
from gnuradio import gr

class counter_formatter(gr.sync_block):
    """
    Receives a trigger message. On each trigger, it formats a string
    with the value of a 'counter' variable from the top_block,
    sends it as a new message, and increments the counter.
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name='Counter Formatter',
            in_sig=None,
            out_sig=None)

        self.counter = 0
        self.message_port_register_in(pmt.intern("msg_in"))
        self.message_port_register_out(pmt.intern("msg_out"))
        self.set_msg_handler(pmt.intern("msg_in"), self.handle_msg)

    def handle_msg(self, msg):
        # 1. Format the string using the flowgraph's 'counter' variable
        # Note: self.counter works because the 'counter' Variable block
        # creates a 'self.counter' attribute on the main flowgraph class.
        payload_str = "TEST " + str(self.counter)

        # 2. Create the new PMT message
        output_msg = pmt.intern(payload_str)

        # 3. Publish the new message
        self.message_port_pub(pmt.intern("msg_out"), output_msg)
        
        # 4. Increment the counter for the next time
        self.counter += 1

    def work(self, input_items, output_items):
        # This block only processes messages, so work() does nothing.
        return 0