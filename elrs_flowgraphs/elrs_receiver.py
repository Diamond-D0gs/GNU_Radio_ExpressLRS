#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: ELRS Receiver
# Author: Gabriel Garcia
# GNU Radio version: 3.10.1.1

from packaging.version import Version as StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import analog
from gnuradio import blocks
from gnuradio import filter
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
from gnuradio.elrs_module.lora_sdr_lora_rx_mod import lora_sdr_lora_rx_mod
import elrs_receiver_epy_block_0 as epy_block_0  # embedded python block
import elrs_receiver_epy_block_2 as epy_block_2  # embedded python block



from gnuradio import qtgui

class elrs_receiver(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "ELRS Receiver", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("ELRS Receiver")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
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

        self.settings = Qt.QSettings("GNU Radio", "elrs_receiver")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

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
        self.rational_resampler_xxx_0_0 = filter.rational_resampler_ccc(
                interpolation=5,
                decimation=448,
                taps=[],
                fractional_bw=0)
        self.qtgui_waterfall_sink_x_0_0 = qtgui.waterfall_sink_c(
            512, #size
            window.WIN_RECTANGULAR, #wintype
            (freq_stop + freq_start) / 2, #fc
            freq_stop - freq_start, #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0_0.set_update_time(0.01)
        self.qtgui_waterfall_sink_x_0_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0_0.set_intensity_range(-140, 0)

        self._qtgui_waterfall_sink_x_0_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_0_win)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            512, #size
            window.WIN_RECTANGULAR, #wintype
            (freq_stop + freq_start) / 2, #fc
            bandwidth, #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.01)
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
        self.network_udp_source_0 = network.udp_source(gr.sizeof_gr_complex, 1, 1234, 0, 1472, True, True, False)
        self.lora_sdr_lora_rx_mod_0 = lora_sdr_lora_rx_mod(
            center_freq=868100000,
            bw=125000,
            cr=1,
            has_crc=False,
            impl_head=True,
            pay_len=8,
            samp_rate=250000,
            sf=7,
            sync_word=[0x12],
            soft_decoding=False,
            ldro_mode=2
        )
        self.epy_block_2 = epy_block_2.elrs_receiver_data_gen(bindingPhrase=binding_phrase, filepath='/home/gabriel/GNU_Radio_ExpressLRS/test.txt', loopFile=True)
        self.epy_block_0 = epy_block_0.fhss_controller(binding_phrase=binding_phrase, freq_start=freq_start, freq_stop=freq_stop, freq_count=freq_count, freq_center=freq_center, disable=disable)
        self.blocks_msgpair_to_var_0 = blocks.msg_pair_to_var(self.set_freq_temp)
        self.blocks_divide_xx_0 = blocks.divide_cc(1)
        self.analog_sig_source_x_0 = analog.sig_source_c(wide_samp_rate, analog.GR_COS_WAVE, freq_temp, 1, 0, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0, 'msg_out'), (self.blocks_msgpair_to_var_0, 'inpair'))
        self.msg_connect((self.lora_sdr_lora_rx_mod_0, 'out'), (self.epy_block_0, 'msg_in'))
        self.msg_connect((self.lora_sdr_lora_rx_mod_0, 'out'), (self.epy_block_2, 'msg_in'))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_divide_xx_0, 1))
        self.connect((self.blocks_divide_xx_0, 0), (self.rational_resampler_xxx_0_0, 0))
        self.connect((self.network_udp_source_0, 0), (self.blocks_divide_xx_0, 0))
        self.connect((self.network_udp_source_0, 0), (self.qtgui_waterfall_sink_x_0_0, 0))
        self.connect((self.rational_resampler_xxx_0_0, 0), (self.lora_sdr_lora_rx_mod_0, 0))
        self.connect((self.rational_resampler_xxx_0_0, 0), (self.qtgui_waterfall_sink_x_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "elrs_receiver")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_wide_samp_rate(self):
        return self.wide_samp_rate

    def set_wide_samp_rate(self, wide_samp_rate):
        self.wide_samp_rate = wide_samp_rate
        self.set_freq_start(self.freq_center - (self.wide_samp_rate // 2))
        self.set_freq_stop(self.freq_center + (self.wide_samp_rate // 2))
        self.analog_sig_source_x_0.set_sampling_freq(self.wide_samp_rate)

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
        self.qtgui_waterfall_sink_x_0.set_frequency_range((self.freq_stop + self.freq_start) / 2, self.bandwidth)

    def get_sf(self):
        return self.sf

    def set_sf(self, sf):
        self.sf = sf

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_freq_temp(self):
        return self.freq_temp

    def set_freq_temp(self, freq_temp):
        self.freq_temp = freq_temp
        self.analog_sig_source_x_0.set_frequency(self.freq_temp)

    def get_freq_stop(self):
        return self.freq_stop

    def set_freq_stop(self, freq_stop):
        self.freq_stop = freq_stop
        self.epy_block_0.freq_stop = self.freq_stop
        self.qtgui_waterfall_sink_x_0.set_frequency_range((self.freq_stop + self.freq_start) / 2, self.bandwidth)
        self.qtgui_waterfall_sink_x_0_0.set_frequency_range((self.freq_stop + self.freq_start) / 2, self.freq_stop - self.freq_start)

    def get_freq_start(self):
        return self.freq_start

    def set_freq_start(self, freq_start):
        self.freq_start = freq_start
        self.epy_block_0.freq_start = self.freq_start
        self.qtgui_waterfall_sink_x_0.set_frequency_range((self.freq_stop + self.freq_start) / 2, self.bandwidth)
        self.qtgui_waterfall_sink_x_0_0.set_frequency_range((self.freq_stop + self.freq_start) / 2, self.freq_stop - self.freq_start)

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




def main(top_block_cls=elrs_receiver, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

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
