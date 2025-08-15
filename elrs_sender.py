# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: ExpressLRS Sender
# GNU Radio version: 3.10.11.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
import elrs_sender_epy_block_0 as epy_block_0  # embedded python block
import threading







class elrs_sender(gr.hier_block2, Qt.QWidget):
    def __init__(self, domain="FCC915", packet_rate=25):
        gr.hier_block2.__init__(
            self, "ExpressLRS Sender",
                gr.io_signature(0, 0, 0),
                gr.io_signature(0, 0, 0),
        )
        self.message_port_register_hier_out("out")

        Qt.QWidget.__init__(self)
        self.top_layout = Qt.QVBoxLayout()
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)
        self.setLayout(self.top_layout)

        ##################################################
        # Parameters
        ##################################################
        self.domain = domain
        self.packet_rate = packet_rate

        ##################################################
        # Variables
        ##################################################
        self.period = period = 1000

        ##################################################
        # Blocks
        ##################################################

        self.epy_block_0 = epy_block_0.blk(domain=domain, packet_rate=packet_rate)
        self.blocks_msgpair_to_var_0 = blocks.msg_pair_to_var(self.set_period)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.intern("e"), period)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.epy_block_0, 'trigger'))
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self, 'out'))
        self.msg_connect((self.epy_block_0, 'set_period'), (self.blocks_msgpair_to_var_0, 'inpair'))


    def get_domain(self):
        return self.domain

    def set_domain(self, domain):
        self.domain = domain
        self.epy_block_0.domain = self.domain

    def get_packet_rate(self):
        return self.packet_rate

    def set_packet_rate(self, packet_rate):
        self.packet_rate = packet_rate
        self.epy_block_0.packet_rate = self.packet_rate

    def get_period(self):
        return self.period

    def set_period(self, period):
        self.period = period
        self.blocks_message_strobe_0.set_period(self.period)

