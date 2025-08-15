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
    from .elrs_module_python import *
except ModuleNotFoundError:
    pass

# import any pure python here
from .elrs_receiver import _elrs_receiver_base
from .elrs_transmitter import elrs_transmitter
from .elrs_receiver import elrs_receiver
#
