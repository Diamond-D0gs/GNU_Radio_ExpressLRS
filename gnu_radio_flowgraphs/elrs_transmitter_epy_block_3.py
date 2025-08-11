import numpy as np
import pmt
from gnuradio import gr

class blk(gr.sync_block):
    """
    Takes a message pair ('freq': 123.45) and converts it
    to a dictionary {'freq': 123.45} for the Soapy Sink command port.
    """
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='Pair to Soapy CMD',
            in_sig=None,
            out_sig=None)
        self.message_port_register_in(pmt.intern('msg_in'))
        self.message_port_register_out(pmt.intern('cmd_out'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)

    def handle_msg(self, msg):
        if pmt.is_pair(msg):
            # The key for the Soapy Sink frequency setting is 'freq'
            key = pmt.intern("freq")
            value = pmt.cdr(msg)

            # Create an empty dictionary
            cmd_dict = pmt.make_dict()
            # Add our key-value pair
            cmd_dict = pmt.dict_add(cmd_dict, key, value)

            # Publish the dictionary to the output port
            self.message_port_pub(pmt.intern('cmd_out'), cmd_dict)