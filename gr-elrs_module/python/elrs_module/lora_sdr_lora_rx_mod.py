# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: lora_sdr_lora_rx_binary
# Description: Complete LoRa receiver that outputs binary u8vector messages.
# GNU Radio version: 3.10.x.x

from gnuradio import gr
from gnuradio import lora_sdr # type: ignore
from ._binary_crc_verif import binary_crc_verify

class lora_sdr_lora_rx_mod(gr.hier_block2):
    def __init__(self, center_freq=868100000, bw=125000, cr=1, has_crc=True, impl_head=False, pay_len=255, samp_rate=250000, sf=7,sync_word=[0x12], soft_decoding=False, ldro_mode=2):
        gr.hier_block2.__init__(
            self, "lora_sdr_lora_rx_mod",
                gr.io_signature(1, 1, gr.sizeof_gr_complex*1), # type: ignore
                # MODIFICATION: The hier block no longer has a streaming output.
                gr.io_signature(0, 0, 0), # type: ignore
        )

        # The message port 'out' is still the primary output.
        self.message_port_register_hier_out("out")

        ##################################################
        # Parameters (Removed print_rx as it was tied to the old block)
        ##################################################
        self.bw = bw
        self.cr = cr
        self.has_crc = has_crc
        self.impl_head = impl_head
        self.pay_len = pay_len
        self.samp_rate = samp_rate
        self.sf = sf
        self.soft_decoding = soft_decoding
        self.center_freq = center_freq
        self.sync_word = sync_word

        ##################################################
        # Blocks
        ##################################################
        # MODIFICATION: Replace the original lora_sdr.crc_verif with your custom binary_crc_verify block.
        # The arguments for printing are no longer needed.
        self.binary_crc_verify_0 = binary_crc_verify()

        # All other blocks from the original RX chain remain the same.
        self.lora_sdr_header_decoder_0 = lora_sdr.header_decoder(impl_head, cr, pay_len, has_crc,ldro_mode, False) # Set print_header to False
        self.lora_sdr_hamming_dec_0 = lora_sdr.hamming_dec(soft_decoding)
        self.lora_sdr_gray_mapping_0 = lora_sdr.gray_mapping(soft_decoding)
        self.lora_sdr_frame_sync_0 = lora_sdr.frame_sync(center_freq, bw, sf, impl_head, sync_word,int(samp_rate/bw),8)
        self.lora_sdr_fft_demod_0 = lora_sdr.fft_demod( soft_decoding, True)
        self.lora_sdr_dewhitening_0 = lora_sdr.dewhitening()
        self.lora_sdr_deinterleaver_0 = lora_sdr.deinterleaver(soft_decoding)

        ##################################################
        # Connections
        ##################################################
        # MODIFICATION: The output message from your new block connects to the hier block's output.
        self.msg_connect((self.binary_crc_verify_0, 'out'), (self, 'out'))

        self.msg_connect((self.lora_sdr_header_decoder_0, 'frame_info'), (self.lora_sdr_frame_sync_0, 'frame_info'))

        # MODIFICATION: The streaming output from dewhitening now feeds into your new block.
        self.connect((self.lora_sdr_dewhitening_0, 0), (self.binary_crc_verify_0, 0))

        # MODIFICATION: The hier block's streaming output is no longer connected.
        # self.connect((self.lora_sdr_crc_verif_0, 0), (self, 0)) # This line is removed.

        # All other internal connections remain the same.
        self.connect((self.lora_sdr_deinterleaver_0, 0), (self.lora_sdr_hamming_dec_0, 0))
        self.connect((self.lora_sdr_fft_demod_0, 0), (self.lora_sdr_gray_mapping_0, 0))
        self.connect((self.lora_sdr_frame_sync_0, 0), (self.lora_sdr_fft_demod_0, 0))
        self.connect((self.lora_sdr_gray_mapping_0, 0), (self.lora_sdr_deinterleaver_0, 0))
        self.connect((self.lora_sdr_hamming_dec_0, 0), (self.lora_sdr_header_decoder_0, 0))
        self.connect((self.lora_sdr_header_decoder_0, 0), (self.lora_sdr_dewhitening_0, 0))
        self.connect((self, 0), (self.lora_sdr_frame_sync_0, 0))

    # All getters and setters remain the same for dynamic control.
    def get_bw(self):
        return self.bw

    def set_bw(self, bw):
        self.bw = bw

    def get_cr(self):
        return self.cr

    def set_cr(self, cr):
        self.cr = cr

    def get_has_crc(self):
        return self.has_crc

    def set_has_crc(self, has_crc):
        self.has_crc = has_crc

    def get_impl_head(self):
        return self.impl_head

    def set_impl_head(self, impl_head):
        self.impl_head = impl_head

    def get_pay_len(self):
        return self.pay_len

    def set_pay_len(self, pay_len):
        self.pay_len = pay_len

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_sf(self):
        return self.sf

    def set_sf(self, sf):
        self.sf = sf

    def get_soft_decoding(self):
        return self.soft_decoding

    def set_soft_decoding(self, soft_decoding):
        self.soft_decoding = soft_decoding