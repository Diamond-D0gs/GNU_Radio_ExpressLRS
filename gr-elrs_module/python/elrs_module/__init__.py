#
# Copyright 2008,2009 Free Software Foundation, Inc.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

# The presence of this file turns this directory into a Python package

'''
This is the GNU Radio ELRS_MODULE module. Place your Python package
description here (python/__init__.py).
'''
import os

# import pybind11 generated symbols into the elrs_module namespace
try:
    # this might fail if the module is python-only
    from .elrs_module_python import * # type: ignore
except ModuleNotFoundError:
    pass

# import any pure python here
from .elrs_receiver import elrs_receiver
from .elrs_transmitter import elrs_transmitter
from .lora_sdr_lora_rx_mod import lora_sdr_lora_rx_mod
from .lora_sdr_lora_tx_mod import lora_sdr_lora_tx_mod
#