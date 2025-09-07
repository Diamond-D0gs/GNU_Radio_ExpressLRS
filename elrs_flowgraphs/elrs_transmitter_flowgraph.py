#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: ELRS Transmitter Flowgraph
# Author: Gabriel Garcia
# GNU Radio version: 3.10.1.1

from gnuradio import blocks
import pmt
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
from gnuradio.elrs_module.lora_sdr_lora_tx_mod import lora_sdr_lora_tx_mod
import elrs_transmitter_flowgraph_epy_block_0 as epy_block_0  # embedded python block
import elrs_transmitter_flowgraph_epy_block_2 as epy_block_2  # embedded python block




class elrs_transmitter_flowgraph(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "ELRS Transmitter Flowgraph", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.wide_samp_rate = wide_samp_rate = 926900000 - 903500000
        self.freq_center = freq_center = 914700000
        self.bandwidth = bandwidth = 125e3
        self.sf = sf = 7
        self.samp_rate = samp_rate = bandwidth*2
        self.freq_temp = freq_temp = freq_center
        self.freq_stop = freq_stop = freq_center + (wide_samp_rate // 2)
        self.freq_start = freq_start = freq_center - (wide_samp_rate // 2)
        self.freq_count = freq_count = 20
        self.disable = disable = True
        self.crc = crc = False
        self.cr = cr = 1
        self.counter = counter = 0
        self.binding_phrase = binding_phrase = "TestBindingPhrase"

        ##################################################
        # Blocks
        ##################################################
        self.network_udp_sink_1 = network.udp_sink(gr.sizeof_gr_complex, 1, '127.0.0.1', 1234, 0, 1472, False)
        self.lora_sdr_lora_tx_mod_0 = lora_sdr_lora_tx_mod(
            bw=int(bandwidth),
            cr=1,
            has_crc=False,
            impl_head=True,
            samp_rate=int(samp_rate),
            sf=sf,
            ldro_mode=0,
            frame_zero_padd=128,
            sync_word=[0x12]
        )
        self.epy_block_2 = epy_block_2.elrs_transmitter_data_gen(bindingPhrase=binding_phrase, filepath='/home/gabriel/GNU_Radio_ExpressLRS/test.txt', loopFile=True)
        self.epy_block_0 = epy_block_0.fhss_controller(binding_phrase=binding_phrase, freq_start=freq_start, freq_stop=freq_stop, freq_count=freq_count, freq_center=freq_center, disable=disable)
        self.blocks_msgpair_to_var_0 = blocks.msg_pair_to_var(self.set_freq_temp)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.intern(""), 1000 // 25)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.epy_block_0, 'msg_in'))
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.epy_block_2, 'msg_in'))
        self.msg_connect((self.epy_block_0, 'msg_out'), (self.blocks_msgpair_to_var_0, 'inpair'))
        self.msg_connect((self.epy_block_2, 'msg_out'), (self.lora_sdr_lora_tx_mod_0, 'in'))
        self.connect((self.lora_sdr_lora_tx_mod_0, 0), (self.network_udp_sink_1, 0))


    def get_wide_samp_rate(self):
        return self.wide_samp_rate

    def set_wide_samp_rate(self, wide_samp_rate):
        self.wide_samp_rate = wide_samp_rate
        self.set_freq_start(self.freq_center - (self.wide_samp_rate // 2))
        self.set_freq_stop(self.freq_center + (self.wide_samp_rate // 2))

    def get_freq_center(self):
        return self.freq_center

    def set_freq_center(self, freq_center):
        self.freq_center = freq_center
        self.set_freq_start(self.freq_center - (self.wide_samp_rate // 2))
        self.set_freq_stop(self.freq_center + (self.wide_samp_rate // 2))
        self.set_freq_temp(self.freq_center)
        self.epy_block_0.freq_center = self.freq_center

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        self.set_samp_rate(self.bandwidth*2)

    def get_sf(self):
        return self.sf

    def set_sf(self, sf):
        self.sf = sf
        self.lora_sdr_lora_tx_mod_0.set_sf(self.sf)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_freq_temp(self):
        return self.freq_temp

    def set_freq_temp(self, freq_temp):
        self.freq_temp = freq_temp

    def get_freq_stop(self):
        return self.freq_stop

    def set_freq_stop(self, freq_stop):
        self.freq_stop = freq_stop
        self.epy_block_0.freq_stop = self.freq_stop

    def get_freq_start(self):
        return self.freq_start

    def set_freq_start(self, freq_start):
        self.freq_start = freq_start
        self.epy_block_0.freq_start = self.freq_start

    def get_freq_count(self):
        return self.freq_count

    def set_freq_count(self, freq_count):
        self.freq_count = freq_count
        self.epy_block_0.freq_count = self.freq_count

    def get_disable(self):
        return self.disable

    def set_disable(self, disable):
        self.disable = disable
        self.epy_block_0.disable = self.disable

    def get_crc(self):
        return self.crc

    def set_crc(self, crc):
        self.crc = crc

    def get_cr(self):
        return self.cr

    def set_cr(self, cr):
        self.cr = cr

    def get_counter(self):
        return self.counter

    def set_counter(self, counter):
        self.counter = counter

    def get_binding_phrase(self):
        return self.binding_phrase

    def set_binding_phrase(self, binding_phrase):
        self.binding_phrase = binding_phrase
        self.epy_block_0.binding_phrase = self.binding_phrase




def main(top_block_cls=elrs_transmitter_flowgraph, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
