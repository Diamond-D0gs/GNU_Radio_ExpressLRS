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
from gnuradio import gr, analog, blocks, filter
from .fhss_domains import FHSS_DOMAINS, get_additional_domain_settings
from .OTA import OTA_Packet4_s, OTA4_PACKET_SIZE, ELRS4_TELEMETRY_BYTES_PER_CALL, PACKET_TYPE_DATA, PACKET_TYPE_LINKSTATS, PACKET_TYPE_RCDATA, PACKET_TYPE_SYNC

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

    def work(self, input_items, output_items):
        return 0

class elrs_transmitter(gr.hier_block2):
    """
    docstring for block elrs_transmitter
    """
    def __init__(self, domain="FCC915", packet_rate=25, binding_phrase="DefaultBindingPhrase"):
        gr.hier_block2.__init__(self,
            name="elrs_transmitter",
            input_signature=gr.io_signature(1, 1, numpy.dtype(numpy.complex64).itemsize), # type: ignore
            output_signature=gr.io_signature(1, 1, numpy.dtype(numpy.complex64).itemsize)) # type: ignore
        
        # Save the passed parameters.
        self._packet_rate = packet_rate
        self._binding_phrase = binding_phrase
        self._domain = FHSS_DOMAINS[domain]

        # Calculated prameters.
        self._uid = md5(str(f'-DMY_BINDING_PHRASE="{binding_phrase}"').encode('utf-8')).digest()[:6]
        self._packet_time = 1.0 / packet_rate
        
        # Create lock for updating parameters.
        self._lock = Lock()

        # State members.
        self._fhss_handler = FHSSHandler(self._uid, self._domain)
        self._connection_state = ConnectionState.NO_CONNECTION
        self._updated_connection_state = True
        self._thread = Thread(target=self._thread_loop)
        self._thread.daemon = True
        self._stop_thread = False
        self._sync_confirmed = False
        self._packet_counter = 0
        self._tlm_pkt_send_cnt = 0
        self._telemetry_file: None | typing.TextIO = None

        self._additional_settings = get_additional_domain_settings(domain, packet_rate)
        if not self._additional_settings['valid']:
            raise Exception('Invalid domain and packet rate combination!')

        frequency_range = self._domain['stop_freq'] - self._domain['start_freq']
        inter_deci_frac = Fraction(frequency_range, self._additional_settings['bandwidth'])

        resampler_expand_params = {
            'interpolation' : inter_deci_frac.numerator,
            'decimation'    : inter_deci_frac.denominator,
            'taps'          : [],
            'fractional_bw' : 0.04
        }

        self._rational_resampler_expand = filter.rational_resampler_ccc(**resampler_expand_params) # type: ignore

        resampler_shrink_params = {
            'interpolation' : inter_deci_frac.denominator,
            'decimation'    : inter_deci_frac.numerator,
            'taps'          : [],
            'fractional_bw' : 0.04
        }

        self._rational_resampler_expand = filter.rational_resampler_ccc(**resampler_shrink_params) # type: ignore

        shift_signal_gen_params = {
            'sampling_freq' : self._fhss_handler.freq_range,
            'waveform'      : analog.GR_COS_WAVE, # type: ignore
            'wave_freq'     : self._fhss_handler.get_init_freq(),
            'ampl'          : 1,
            'offset'        : 0
        }

        self._shift_signal_gen = analog.sig_source_c(**shift_signal_gen_params) # type: ignore

        lora_rx_params = {
            'center_freq' : 0,
            'print_rx' : [False, False],
            'has_crc' : False, # ExpressLRS utilizes its own CRC.
            'impl_head' : True, # ExpressLRS packets are a fixed, predictable, size for a given configuration.
            'bw' : self._additional_settings['bandwidth'],
            'cr' : self._additional_settings['coding_rate'],
            'sf' : self._additional_settings['spread_factor'],
            'samp_rate' : self._additional_settings['bandwidth'] * 2,
            'pay_len' : OTA4_PACKET_SIZE,
            'ldro_mode' : 0
        }

        self._lora_rx = lora_sdr.lora_sdr_lora_rx(**lora_rx_params)

        lora_tx_params = {
            # 'frame_zero_padd' : 0,
            'has_crc' : False, # ExpressLRS utilizes its own CRC.
            'impl_head' : True, # ExpressLRS packets are a fixed, predictable, size for a given configuration.
            'bw' : self._additional_settings['bandwidth'],
            'cr' : self._additional_settings['coding_rate'],
            'sf' : self._additional_settings['spread_factor'],
            'samp_rate' : self._additional_settings['bandwidth'] * 2,
            'ldro_mode' : 0
        }

        self._lora_tx = lora_sdr.lora_sdr_lora_tx(**lora_tx_params)

        self._proxy_block = proxy_block(self._lora_rx_msg_handler)
        self._multiplier = blocks.multiply_vcc(vlen=1) # type: ignore
        self._divider = blocks.multiply_vcc(vlen=1) # type: ignore
        self._conjugate = blocks.conjugate_cc() # type: ignore

        # self.message_port_register_out(pmt.intern('freq_center')) # type: ignore
        # self.message_port_register_out(pmt.intern('freq_range')) # type: ignore

        self.msg_connect((self._proxy_block, 'out'), (self._lora_tx, 'in'))
        self.msg_connect((self._lora_rx, 'out'), (self._proxy_block, 'in'))

        self.connect((self, 0), (self._divider, 0))
        self.connect(self._shift_signal_gen, self._conjugate)
        self.connect(self._conjugate, (self._divider, 1))
        self.connect(self._divider, (self._lora_rx, 0))

        self.connect((self._lora_tx, 0), (self._multiplier, 0))
        self.connect(self._shift_signal_gen, (self._multiplier, 1))
        self.connect(self._multiplier, (self, 0))

        self._thread.start()

    def _thread_loop(self):
        while not self._stop_thread:
            start_time: float = time.time()

            with self._lock:
                if self._updated_connection_state:
                    self._updated_connection_state = False
                    match self._connection_state:
                        case ConnectionState.NO_CONNECTION:
                            print('ELRS TX: Connection state has updated to "NO_CONNECTION"')
                        case ConnectionState.ESTABLISHING_CONNECTION:
                            print('ELRS TX: Connection state has updated to "ESTABLISHING_CONNECTION"')
                        case ConnectionState.CONNECTED:
                            print('ELRS TX: Connection state has updated to "CONNECTED"')
                        case _:
                            print('ELRS TX: Unknown connection state.')

                match self._connection_state:
                    case ConnectionState.NO_CONNECTION:
                        if self._sync_confirmed:
                            self._connection_state = ConnectionState.CONNECTED
                            self._updated_connection_state = True
                            self._sync_confirmed = False
                        else:
                            backing_bytes = bytearray(OTA4_PACKET_SIZE)
                            ota_packet4_s = OTA_Packet4_s.from_buffer(backing_bytes)
                            ota_packet4_s.type = PACKET_TYPE_SYNC

                            self._proxy_block.post(pmt.intern(backing_bytes.decode('latin-1'))) # type: ignore
                    
                            print('ELRS TX: Sent sync packet.')
                    case ConnectionState.ESTABLISHING_CONNECTION:
                        pass
                    case ConnectionState.CONNECTED:
                        backing_bytes = bytearray(OTA4_PACKET_SIZE)
                        ota_packet4_s = OTA_Packet4_s.from_buffer(backing_bytes)
                        ota_packet4_s.type = PACKET_TYPE_RCDATA
                        ota_packet4_s.rc.ch[:] = self._packet_counter.to_bytes(5, 'little')

                        self._proxy_block.post(pmt.intern(backing_bytes.decode('latin-1'))) # type: ignore

            delta_time = time.time() - start_time
            if delta_time <= self._packet_time:
                time.sleep(self._packet_time - delta_time)
            else:
                print('ELRS TX: Warning! Packet time exceeded!')

    def _lora_rx_msg_handler(self, msg) -> None:
        temp : str = pmt.symbol_to_string(msg) if pmt.is_symbol(msg) else pmt.string_to_string(msg) # type: ignore
        ota4 = OTA_Packet4_s.from_buffer(temp.encode('latin-1')) # type: ignore
        if ota4.type == PACKET_TYPE_LINKSTATS:
            with self._lock:
                self._sync_confirmed = True
                #self._packet_counter += 1
        # elif ota4.type == PACKET_TYPE_RCDATA:
        #     packet_num = int.from_bytes(bytes(ota4.rc.ch), 'little')
        #     print(f'Packet: {packet_num}')
        #     with self._lock:
        #         self._packet_counter += 1