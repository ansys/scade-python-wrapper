# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# example of product search paths
# C:\Program Files\ANSYS Inc\v251\SCADE\SCADE\APIs\Python\lib
# C:\Program Files\ANSYS Inc\v251\SCADE\SCADE\bin

import argparse
from os import environ

from ansys.scade.apitools import declare_project
from ansys.scade.apitools.info import get_scade_home

# apitools must be imported before using any scade.* import
# to make sure sys.path is set properly
# isort: split

from scade.code.suite.sctoc import raw_tcl, sc_to_c_core

parser = argparse.ArgumentParser(description='Python way for scade -code')
parser.add_argument(
    '-p', '--project', metavar='<Scade project>', help='SCADE Suite', required=True
)
parser.add_argument(
    '-c', '--configuration', metavar='<configuration>', help='configuration', required=True
)
parser.add_argument(
    '-a',
    '--action',
    type=str,
    metavar='<action>',
    help='action to perform',
    choices=['Generate', 'Build', 'RebuildAll'],
    default='Generate',
)
options = parser.parse_args()

# set the SCADE environment variable to replicate the behavior
# of STDTCL.EXE. It allows, among other things, to load the libraries
# referenced with $(SCADE).
environ['SCADE'] = str(get_scade_home() / 'SCADE')

declare_project(options.project)

raw_tcl('CgMap init_kcg "%s"' % options.configuration)
raw_tcl('KcgMF init "%s"' % options.configuration)
sc_to_c_core(options.action, options.configuration)

"""
example of command lines, relative to thr file's directory:
-p ../Sandbox/Model/PyBox.etp -c "Python" -a Generate
-p ../Sandbox/Model/PyBox.etp -c "KCG IO" -a Generate
-p ../Display/Model/Variables.etp -c "Python" -a Generate
-p ../Functions/Model/Model.etp -c "Python" -a Generate
-p ../Functions/Model/Model.etp -c "Python IO" -a Generate
"""
