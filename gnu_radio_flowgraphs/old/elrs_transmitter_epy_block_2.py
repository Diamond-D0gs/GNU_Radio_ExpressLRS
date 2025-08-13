import numpy as np
import pmt
from gnuradio import gr

class blk(gr.sync_block):
    """
    Custom block to create tx_freq tags from messages.
    This block receives a data stream and asynchronous messages.
    When a 'freq' message arrives, it adds a 'tx_freq' tag
    to the next sample on the output stream.
    """
    def __init__(self):
        gr.sync_block.__init__(
            self,
            name='Custom Message Tagger',
            in_sig=[np.complex64],  # Expecting complex data stream in
            out_sig=[np.complex64] # Outputting complex data stream
        )
        # Register the message input port
        self.message_port_register_in(pmt.intern('msg_in'))
        # Set the function that will handle incoming messages
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)

        # A variable to hold the frequency from a received message
        self.next_freq_to_tag = None

    def handle_msg(self, msg):
        # This function is called by GNU Radio when a message arrives
        # Check if the message is the correct format (a pair)
        if pmt.is_pair(msg):
            # The key is in the 'car' of the pair, value in the 'cdr'
            key = pmt.car(msg)
            if pmt.to_python(key) == 'freq':
                # Store the frequency value. It will be used in the work() function.
                self.next_freq_to_tag = pmt.cdr(msg)

    def work(self, input_items, output_items):
        # The main processing function for the data stream

        # Check if our message handler has stored a new frequency
        if self.next_freq_to_tag is not None:
            # We have a frequency, so create a tag for it.
            # The PlutoSDR Sink requires the key to be "tx_freq".
            key = pmt.intern("tx_freq")
            value = self.next_freq_to_tag

            # Add the tag to the very first sample of this output buffer (index 0)
            self.add_item_tag(0, # Port 0
                              self.nitems_written(0), # Absolute index of the first item
                              key,
                              value)
            
            # Reset the variable so we don't add this tag again until a new message arrives
            self.next_freq_to_tag = None

        # Copy the data from the input to the output
        # This block doesn't modify the data, it just passes it through
        output_items[0][:] = input_items[0]
        
        # Tell GNU Radio how many items we produced
        return len(output_items[0])