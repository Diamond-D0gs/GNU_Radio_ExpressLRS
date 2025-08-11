#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.11.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
import pmt
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import iio
import elrs_transmitter_epy_block_0 as epy_block_0  # embedded python block
import elrs_transmitter_epy_block_1 as epy_block_1  # embedded python block
import gnuradio.lora_sdr as lora_sdr
import sip
import threading



class elrs_transmitter(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "elrs_transmitter")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.freq_center = freq_center = 914700000
        self.freq_stop = freq_stop = freq_center + 100000
        self.freq_start = freq_start = freq_center - 100000
        self.wide_samp_rate = wide_samp_rate = freq_stop - freq_start
        self.bandwidth = bandwidth = 8000 * 1
        self.sf = sf = 7
        self.sdr_samp_rate = sdr_samp_rate = wide_samp_rate
        self.sdr_buffer_size = sdr_buffer_size = 2**14
        self.samp_rate = samp_rate = bandwidth*2
        self.freq_temp = freq_temp = 0
        self.freq_count = freq_count = 8
        self.disable = disable = False
        self.crc = crc = False
        self.cr = cr = 1
        self.counter = counter = 0
        self.binding_phrase = binding_phrase = "TestBindingPhrase"

        ##################################################
        # Blocks
        ##################################################

        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=25,
                decimation=2,
                taps=[],
                fractional_bw=0)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            512, #size
            window.WIN_HAMMING, #wintype
            ((freq_stop + freq_start) / 2), #fc
            (freq_stop - freq_start), #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.0001)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 0)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_win)
        self.lora_sdr_whitening_0 = lora_sdr.whitening(False,False,',','packet_len')
        self.lora_sdr_modulate_0 = lora_sdr.modulate(sf, samp_rate, bandwidth, [18], (int(20*2**sf*samp_rate/bandwidth)),8)
        self.lora_sdr_interleaver_0 = lora_sdr.interleaver(cr, sf, 0, 125000)
        self.lora_sdr_header_0 = lora_sdr.header(False, crc, cr)
        self.lora_sdr_hamming_enc_0 = lora_sdr.hamming_enc(cr, sf)
        self.lora_sdr_gray_demap_0 = lora_sdr.gray_demap(sf)
        self.lora_sdr_add_crc_0 = lora_sdr.add_crc(crc)
        self.iio_pluto_source_0 = iio.fmcomms2_source_fc32('ip:192.168.2.1' if 'ip:192.168.2.1' else iio.get_pluto_uri(), [True, True], sdr_buffer_size)
        self.iio_pluto_source_0.set_len_tag_key('packet_len')
        self.iio_pluto_source_0.set_frequency(int(freq_center))
        self.iio_pluto_source_0.set_samplerate(sdr_samp_rate)
        self.iio_pluto_source_0.set_gain_mode(0, 'slow_attack')
        self.iio_pluto_source_0.set_gain(0, 64)
        self.iio_pluto_source_0.set_quadrature(True)
        self.iio_pluto_source_0.set_rfdc(True)
        self.iio_pluto_source_0.set_bbdc(True)
        self.iio_pluto_source_0.set_filter_params('Auto', '', 0, 0)
        self.iio_pluto_sink_0 = iio.fmcomms2_sink_fc32('ip:192.168.2.1' if 'ip:192.168.2.1' else iio.get_pluto_uri(), [True, True], sdr_buffer_size, False)
        self.iio_pluto_sink_0.set_len_tag_key('')
        self.iio_pluto_sink_0.set_bandwidth(sdr_samp_rate)
        self.iio_pluto_sink_0.set_frequency(int(freq_center))
        self.iio_pluto_sink_0.set_samplerate(sdr_samp_rate)
        self.iio_pluto_sink_0.set_attenuation(0, 10.0)
        self.iio_pluto_sink_0.set_filter_params('Auto', '', 0, 0)
        self.epy_block_1 = epy_block_1.counter_formatter()
        self.epy_block_0 = epy_block_0.fhss_controller(binding_phrase=binding_phrase, freq_start=freq_start, freq_stop=freq_stop, freq_count=freq_count, freq_center=freq_center, disable=disable)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_msgpair_to_var_0 = blocks.msg_pair_to_var(self.set_freq_temp)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.intern(""), 1000)
        self.analog_sig_source_x_0 = analog.sig_source_c(wide_samp_rate, analog.GR_COS_WAVE, freq_temp, 1, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.epy_block_1, 'msg_in'))
        self.msg_connect((self.epy_block_0, 'msg_out'), (self.blocks_msgpair_to_var_0, 'inpair'))
        self.msg_connect((self.epy_block_1, 'msg_out'), (self.epy_block_0, 'msg_in'))
        self.msg_connect((self.epy_block_1, 'msg_out'), (self.lora_sdr_whitening_0, 'msg'))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.blocks_multiply_xx_0, 0), (self.iio_pluto_sink_0, 0))
        self.connect((self.iio_pluto_source_0, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.lora_sdr_add_crc_0, 0), (self.lora_sdr_hamming_enc_0, 0))
        self.connect((self.lora_sdr_gray_demap_0, 0), (self.lora_sdr_modulate_0, 0))
        self.connect((self.lora_sdr_hamming_enc_0, 0), (self.lora_sdr_interleaver_0, 0))
        self.connect((self.lora_sdr_header_0, 0), (self.lora_sdr_add_crc_0, 0))
        self.connect((self.lora_sdr_interleaver_0, 0), (self.lora_sdr_gray_demap_0, 0))
        self.connect((self.lora_sdr_modulate_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.lora_sdr_whitening_0, 0), (self.lora_sdr_header_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_multiply_xx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "elrs_transmitter")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_freq_center(self):
        return self.freq_center

    def set_freq_center(self, freq_center):
        self.freq_center = freq_center
        self.set_freq_start(self.freq_center - 100000)
        self.set_freq_stop(self.freq_center + 100000)
        self.epy_block_0.freq_center = self.freq_center
        self.iio_pluto_sink_0.set_frequency(int(self.freq_center))
        self.iio_pluto_source_0.set_frequency(int(self.freq_center))

    def get_freq_stop(self):
        return self.freq_stop

    def set_freq_stop(self, freq_stop):
        self.freq_stop = freq_stop
        self.set_wide_samp_rate(self.freq_stop - self.freq_start)
        self.epy_block_0.freq_stop = self.freq_stop
        self.qtgui_waterfall_sink_x_0.set_frequency_range(((self.freq_stop + self.freq_start) / 2), (self.freq_stop - self.freq_start))

    def get_freq_start(self):
        return self.freq_start

    def set_freq_start(self, freq_start):
        self.freq_start = freq_start
        self.set_wide_samp_rate(self.freq_stop - self.freq_start)
        self.epy_block_0.freq_start = self.freq_start
        self.qtgui_waterfall_sink_x_0.set_frequency_range(((self.freq_stop + self.freq_start) / 2), (self.freq_stop - self.freq_start))

    def get_wide_samp_rate(self):
        return self.wide_samp_rate

    def set_wide_samp_rate(self, wide_samp_rate):
        self.wide_samp_rate = wide_samp_rate
        self.set_sdr_samp_rate(self.wide_samp_rate)
        self.analog_sig_source_x_0.set_sampling_freq(self.wide_samp_rate)

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        self.set_samp_rate(self.bandwidth*2)

    def get_sf(self):
        return self.sf

    def set_sf(self, sf):
        self.sf = sf
        self.lora_sdr_gray_demap_0.set_sf(self.sf)
        self.lora_sdr_hamming_enc_0.set_sf(self.sf)
        self.lora_sdr_interleaver_0.set_sf(self.sf)

    def get_sdr_samp_rate(self):
        return self.sdr_samp_rate

    def set_sdr_samp_rate(self, sdr_samp_rate):
        self.sdr_samp_rate = sdr_samp_rate
        self.iio_pluto_sink_0.set_bandwidth(self.sdr_samp_rate)
        self.iio_pluto_sink_0.set_samplerate(self.sdr_samp_rate)
        self.iio_pluto_source_0.set_samplerate(self.sdr_samp_rate)

    def get_sdr_buffer_size(self):
        return self.sdr_buffer_size

    def set_sdr_buffer_size(self, sdr_buffer_size):
        self.sdr_buffer_size = sdr_buffer_size

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_freq_temp(self):
        return self.freq_temp

    def set_freq_temp(self, freq_temp):
        self.freq_temp = freq_temp
        self.analog_sig_source_x_0.set_frequency(self.freq_temp)

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
        self.lora_sdr_hamming_enc_0.set_cr(self.cr)
        self.lora_sdr_header_0.set_cr(self.cr)
        self.lora_sdr_interleaver_0.set_cr(self.cr)

    def get_counter(self):
        return self.counter

    def set_counter(self, counter):
        self.counter = counter

    def get_binding_phrase(self):
        return self.binding_phrase

    def set_binding_phrase(self, binding_phrase):
        self.binding_phrase = binding_phrase
        self.epy_block_0.binding_phrase = self.binding_phrase




def main(top_block_cls=elrs_transmitter, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
