#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2025 Gabriel Garcia.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import pmt
import time
import math
import numpy
import ctypes
import typing
from hashlib import md5
from fractions import Fraction
from threading import Thread, Lock
from .fhss_handler import FHSSHandler
from .packet_rates import PACKET_RATES
from .elrs_enums import ConnectionState
from gnuradio import lora_sdr # type: ignore
from gnuradio.filter import pfb
from gnuradio import gr, analog, blocks, filter
from .lora_sdr_lora_rx_mod import lora_sdr_lora_rx_mod
from .lora_sdr_lora_tx_mod import lora_sdr_lora_tx_mod
from .fhss_domains import FHSS_DOMAINS, get_additional_domain_settings
from .OTA import OTA_Packet4_s, OTA4_PACKET_SIZE, ELRS4_TELEMETRY_BYTES_PER_CALL, PACKET_TYPE_DATA, PACKET_TYPE_LINKSTATS, PACKET_TYPE_RCDATA, PACKET_TYPE_SYNC

class _elrs_receiver_internal(gr.sync_block):
    def __init__(self, domain: dict, additional_settings: dict, packet_rate: int, binding_phrase: str):
        gr.sync_block.__init__(self, name="_elrs_receiver_internal", in_sig=[], out_sig=[])

        self.message_port_register_in(pmt.intern('in')) # type: ignore
        self.message_port_register_in(pmt.intern('fhss_request_in')) # type: ignore
        self.message_port_register_out(pmt.intern('out')) # type: ignore
        self.message_port_register_out(pmt.intern('fhss_request_out')) # type: ignore

        self.set_msg_handler(pmt.intern('in'), self._lora_rx_msg_handler) # type: ignore
        self.set_msg_handler(pmt.intern('fhss_request_in'), self._fhss_request_msg_handler) # type: ignore

        self._packet_rate = packet_rate
        self._binding_phrase = binding_phrase
        self._domain = domain
        self._additional_settings = additional_settings
        self._fhss_enabled = True

        self._uid = md5(str(f'-DMY_BINDING_PHRASE="{binding_phrase}"').encode('utf-8')).digest()[:6]
        self._packet_time = 1.0 / packet_rate
        
        self._lock = Lock()

        self._fhss_handler = FHSSHandler(self._uid, self._domain)
        self._connection_state = ConnectionState.NO_CONNECTION
        self._updated_connection_state = True
        self._thread = Thread(target=self._thread_loop)
        self._thread.daemon = True
        self._stop_thread = False
        self._sync_pkt_recv = False
        self._packet_counter = 0
        self._tlm_pkt_send_cnt = 0
        self._telemetry_file: None | typing.TextIO = None
        
        self._thread.start()

    def get_init_freq(self) -> int:
        return self._fhss_handler.get_init_freq()

    def get_freq_range(self) -> int:
        return self._fhss_handler.freq_range
    
    def get_center_freq(self) -> int:
        return self._fhss_handler.get_center_freq()

    def _thread_loop(self):
        with self._lock:
            print(f'ELRS RX: Center freq: {self._fhss_handler.get_center_freq()}')

        while not self._stop_thread:
            start_time: float = time.time()

            with self._lock:
                if self._updated_connection_state:
                    self._updated_connection_state = False
                    match self._connection_state:
                        case ConnectionState.NO_CONNECTION:
                            print('ELRS RX: Connection state has updated to "NO_CONNECTION"')
                        case ConnectionState.ESTABLISHING_CONNECTION:
                            print('ELRS RX: Connection state has updated to "ESTABLISHING_CONNECTION"')
                        case ConnectionState.CONNECTED:
                            print('ELRS RX: Connection state has updated to "CONNECTED"')
                        case _:
                            print('ELRS RX: Unknown connection state.')

                match self._connection_state:
                    case ConnectionState.NO_CONNECTION:
                        if self._sync_pkt_recv:
                            self._connection_state = ConnectionState.ESTABLISHING_CONNECTION
                            self._updated_connection_state = True
                            self._sync_pkt_recv = False
                    case ConnectionState.ESTABLISHING_CONNECTION:
                        backing_bytes = bytearray(OTA4_PACKET_SIZE)
                        ota_packet4_s = OTA_Packet4_s.from_buffer(backing_bytes)
                        ota_packet4_s.type = PACKET_TYPE_LINKSTATS

                        self.message_port_pub(pmt.intern('out'), pmt.init_u8vector(len(backing_bytes), backing_bytes)) # type: ignore

                        self._fhss_handler.set_curr_index(0)
                        self._connection_state = ConnectionState.CONNECTED
                        self._updated_connection_state = True
                    case ConnectionState.CONNECTED:
                        if self._sync_pkt_recv:
                            self._sync_pkt_recv = False

            delta_time = time.time() - start_time
            if delta_time <= self._packet_time:
                time.sleep(self._packet_time - delta_time)
            else:
                print('ELRS RX: Warning! Packet time exceeded!')

    def _lora_rx_msg_handler(self, msg) -> None:
        #print('Entered ELRS RX msg handler')
        temp = bytearray(pmt.u8vector_elements(msg)) # type: ignore
        ota4 = OTA_Packet4_s.from_buffer(temp) # type: ignore
        if ota4.type == PACKET_TYPE_SYNC:
            with self._lock:
                self._sync_pkt_recv = True
                self._packet_counter += 1
        elif ota4.type == PACKET_TYPE_RCDATA:
            packet_num = int.from_bytes(bytes(ota4.payload.rc.ch.raw), 'little')
            print(f'Packet: {packet_num}')
            with self._lock:
                self._packet_counter += 1

        # Not sending telemetry packets currently.
        # if self._packet_counter % self._additional_settings['tlm_ratio'] == 0:
        #     backing_bytes = bytearray(OTA4_PACKET_SIZE)
        #     ota_packet4_s = OTA_Packet4_s.from_buffer(backing_bytes)
        #     ota_packet4_s.type = PACKET_TYPE_LINKSTATS
        #     if self._telemetry_file is not None:
        #         ota_packet4_s.tlm_dl.payload[0 : ELRS4_TELEMETRY_BYTES_PER_CALL - 1] = int(self._telemetry_file.readline(), 16).to_bytes(4, 'little')

        #     pdu = pmt.cons(pmt.PMT_NIL, pmt.init_u8vector(len(backing_bytes), backing_bytes))  # type: ignore
        #     self.message_port_post(pmt.intern('internal_tx_pdu'), pdu) # type: ignore

    def _fhss_request_msg_handler(self, msg) -> None:
        temp: int = 0
        
        if self._fhss_enabled:
            temp = self._fhss_handler.get_curr_freq()
            self._fhss_handler.update_to_next_freq()
        else:
            temp = self._fhss_handler.get_center_freq()
        
        self.message_port_pub(pmt.intern('fhss_request_out'), pmt.from_long(temp)) # type: ignore

class elrs_receiver(gr.hier_block2):
    """
    docstring for block elrs_receiver
    """
    def __init__(self, domain="FCC915", packet_rate=25, binding_phrase="DefaultBindingPhrase"):
        gr.hier_block2.__init__(self,
            name="elrs_receiver",
            input_signature=gr.io_signature(1, 1, numpy.dtype(numpy.complex64).itemsize), # type: ignore
            output_signature=gr.io_signature(1, 1, numpy.dtype(numpy.complex64).itemsize)) # type: ignore
        
        fhss_domain = FHSS_DOMAINS[domain]
        additional_settings = get_additional_domain_settings(domain, packet_rate)
        if additional_settings is None:
            raise Exception('Invalid domain and packet rate combination!')

        self._elrs_rx_internal = _elrs_receiver_internal(fhss_domain, additional_settings, packet_rate, binding_phrase)
        
        # inter_deci_frac = Fraction(self._elrs_rx_internal.get_freq_range(), additional_settings['bandwidth'] * 2)
        # resampler_expand_params = {
        #     'interpolation' : inter_deci_frac.numerator,
        #     'decimation'    : inter_deci_frac.denominator,
        #     'taps'          : [],
        #     'fractional_bw' : 0.4
        # }

        # self._rational_resampler_expand = filter.rational_resampler_ccc(**resampler_expand_params) # type: ignore

        # resampler_shrink_params = {
        #     'interpolation' : inter_deci_frac.denominator,
        #     'decimation'    : inter_deci_frac.numerator,
        #     'taps'          : [],
        #     'fractional_bw' : 0.4
        # }

        # self._rational_resampler_shrink = filter.rational_resampler_ccc(**resampler_shrink_params) # type: ignore

        resampling_rate_expand = self._elrs_rx_internal.get_freq_range() / (additional_settings['bandwidth'] * 2)
        resampling_rate_shrink = (additional_settings['bandwidth'] * 2) / self._elrs_rx_internal.get_freq_range()

        self._resampler_expand = pfb.arb_resampler_ccf(
            rate=resampling_rate_expand,
            taps=None,
            flt_size=32
        )

        self._resampler_shrink = pfb.arb_resampler_ccf(
            rate=resampling_rate_shrink,
            taps=None,
            flt_size=32
        )

        shift_signal_gen_params = {
            'sampling_freq' : self._elrs_rx_internal.get_freq_range(),
            'waveform'      : analog.GR_COS_WAVE, # type: ignore
            'wave_freq'     : self._elrs_rx_internal.get_init_freq() - 3e6,
            'ampl'          : 1,
            'offset'        : 0
        }

        self._shift_signal_gen = analog.sig_source_c(**shift_signal_gen_params) # type: ignore

        lora_rx_params = {
            'center_freq' : self._elrs_rx_internal.get_center_freq(),
            'has_crc' : False,
            'impl_head' : True,
            'bw' : additional_settings['bandwidth'],
            'cr' : additional_settings['coding_rate'],
            'sf' : additional_settings['spread_factor'],
            'samp_rate' : additional_settings['bandwidth'] * 2,
            'pay_len' : OTA4_PACKET_SIZE,
            'ldro_mode' : 0
        }

        self._lora_rx = lora_sdr_lora_rx_mod(**lora_rx_params)

        lora_tx_params = {
            'has_crc' : False,
            'impl_head' : True,
            'bw' : additional_settings['bandwidth'],
            'cr' : additional_settings['coding_rate'],
            'sf' : additional_settings['spread_factor'],
            'samp_rate' : additional_settings['bandwidth'] * 2,
            'ldro_mode' : 0
        }

        self._lora_tx = lora_sdr_lora_tx_mod(**lora_tx_params)

        self._multiplier = blocks.multiply_vcc(vlen=1) # type: ignore
        self._divider = blocks.divide_cc(vlen=1) # type: ignore

        self.msg_connect((self._lora_rx, 'out'), (self._elrs_rx_internal, 'in'))
        self.msg_connect((self._elrs_rx_internal, 'out'), (self._lora_tx, 'in'))

        # self.connect(self, (self._divider, 0))
        # self.connect(self._shift_signal_gen, (self._divider, 1))
        # self.connect(self._divider, self._resampler_shrink)
        # self.connect(self._resampler_shrink, self._lora_rx)

        # self.connect(self._lora_tx, self._resampler_expand)
        # self.connect(self._resampler_expand, (self._multiplier, 0))
        # self.connect(self._shift_signal_gen, (self._multiplier, 1))
        # self.connect(self._multiplier, self)

        self.connect(self._lora_tx, (self, 0))
        self.connect((self, 0), self._lora_rx)