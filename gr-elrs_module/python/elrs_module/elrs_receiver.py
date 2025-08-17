#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Gabriel Garcia.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import time
import math
import numpy
from hashlib import md5
from fractions import Fraction
from threading import Thread, Lock
from fhss_handler import FHSSHandler
from packet_rates import PACKET_RATES
from elrs_enums import ConnectionState
from gnuradio import gr, analog, blocks, filter
from fhss_domains import FHSS_DOMAINS, get_additional_domain_settings

class elrs_receiver(gr.sync_block):
    """
    docstring for block elrs_receiver
    """
    def __init__(self, domain="FCC915", packet_rate=25, binding_phrase="DefaultBindingPhrase"):
        gr.sync_block.__init__(self,
            name="elrs_receiver",
            in_sig=[numpy.dtype(numpy.complex64).itemsize],
            out_sig=[numpy.dtype(numpy.complex64).itemsize])
        
        # Save the passed parameters.
        self._packet_rate = packet_rate
        self._binding_phrase = binding_phrase
        self._domain = FHSS_DOMAINS['domain']

        # Calculated prameters.
        self._uid = md5(str(f'-DMY_BINDING_PHRASE="{binding_phrase}"').encode('utf-8')).digest()[:6]
        
        # Create lock for updating parameters.
        self._lock = Lock()

        # State members.
        self._fhss_handler = FHSSHandler(self._uid, self._domain)
        self._connection_state = ConnectionState.NO_CONNECTION
        self._thread = Thread(target=self._thread_loop)
        self._thread.daemon = True
        self._stop_thread = False

        self._additional_settings = get_additional_domain_settings(domain, packet_rate)
        if not self._additional_settings['valid']:
            raise Exception('Invalid domain and packet rate combination!')

        frequency_range = self._domain['stop_freq'] - self._domain['start_freq']
        inter_deci_frac = Fraction(frequency_range, self._additional_settings['bandwidth'])

        resampler_params = {
            'interpolation' : inter_deci_frac.numerator,
            'decimation'    : inter_deci_frac.denominator,
            'taps'          : [],
            'fractional_bw' : 0.04
        }

        self._rational_resampler = filter.rational_resampler_ccc(**resampler_params) # type: ignore

        shift_signal_gen_params = {
            'sampling_freq' : self._fhss_handler.freq_range,
            'waveform'      : analog.GR_COS_WAVE, # type: ignore
            'frequency'     : self._fhss_handler.get_init_freq(),
            'amplitude'     : 1,
            'offset'        : 0
        }

        self._shift_signal_gen = analog.sig_source_c(**shift_signal_gen_params) # type: ignore

        lora_rx_params = {
            'has_crc' : True,
            'center_freq' : 0,
            'print_rx' : [False, False],
            'bw' : self._additional_settings['bandwidth'],
            'cr' : self._additional_settings['coding_rate'],
            'sf' : self._additional_settings['spread_factor'],
            'samp_rate' : self._additional_settings['bandwidth'] * 2
        }

        self._multiplier = gr.multiply_cc(2) # type: ignore

    def _thread_loop(self):
        while not self._stop_thread:
            self._lock.acquire()
            try: 
                match self._connection_state:
                    case ConnectionState.NO_CONNECTION:
                        if self._fhss_handler.sync_channel:
                            pass
                    case ConnectionState.ESTABLISHING_CONNECTION:
                        pass
                    case ConnectionState.CONNECTED:
                        pass
            finally:
                self._lock.release()

            time.sleep(1.0 / self._packet_rate)

    def work(self, input_items, output_items):
        # For this sample code, the general block is made to behave like a sync block
        ninput_items = min([len(items) for items in input_items])
        noutput_items = min(len(output_items[0]), ninput_items)
        output_items[0][:noutput_items] = input_items[0][:noutput_items]
        self.consume_each(noutput_items)
        return noutput_items