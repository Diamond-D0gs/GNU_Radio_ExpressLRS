#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Gabriel Garcia.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from misc import uid_mac_seed_get, OTA_VERSION_ID, PACKET_RATE_LIMIT
from gnuradio import gr
from hashlib import md5
import pmt

class _elrs_transmitter_base(gr.basic_block):
    """
    docstring for block elrs_transmitter
    """
    def __init__(self, domain="FCC915", packet_rate=25, binding_phrase="DefaultBindingPhrase"):
        gr.basic_block.__init__(self, name="elrs_receiver", in_sig=[], out_sig=[])

        self.domain = domain
        self.packet_rate = packet_rate
        self.binding_phrase = binding_phrase

        self.message_port_register_in(pmt.intern("trigger"))
        self.message_port_register_in(pmt.intern("packet in"))
        self.message_port_register_out(pmt.intern("packet out"))