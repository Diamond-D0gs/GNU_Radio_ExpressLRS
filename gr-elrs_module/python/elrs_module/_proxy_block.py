import pmt
from gnuradio import gr

class proxy_block(gr.sync_block):
    def __init__(self, msg_handler):
        gr.sync_block.__init__(
            self,
            name="Callable Message Sink",
            in_sig=None,  # No streaming input
            out_sig=None  # No streaming output
        )
        
        self.message_port_register_in(pmt.intern('in')) # type: ignore
        self.message_port_register_in(pmt.intern('forward')) # type: ignore
        self.message_port_register_out(pmt.intern('out')) # type: ignore

        self.set_msg_handler(pmt.intern('in'), msg_handler) # type: ignore
        self.set_msg_handler(pmt.intern('forward'), self._forward_msg) # type: ignore

    def _forward_msg(self, msg):
        self.message_port_pub(pmt.intern('out'), msg) # type: ignore

    def post(self, msg):
        self.message_port_pub(pmt.intern('out'), msg) # type: ignore
        #print('Message posted')

    def work(self, input_items, output_items):
        return 0