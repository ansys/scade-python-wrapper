# Copyright (C) 2020 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""
Generates parts of the ``pydata.py`` module from its ``pydata.ecore`` model.

This modules is based on internal ``lbsjv`` Python generator for ecore.

Steps for generating the pydata.py:

* Create a virtual Python environment 3.12 or greater
* Install ansys-eseg-lbsjv
* Run this script
"""

from pathlib import Path

import ansys.eseg.lbsjv.ecore as ecore
from ansys.eseg.lbsjv.services import (
    CLASS,
    INIT,
    INTERFACE,
    LINK,
    TYPE,
    InitService,
    PythonModel,
)
from ansys.eseg.lbsjv.vgl import get_manager_instance

target_dir = Path(__file__).parent.parent.parent / 'src' / 'ansys' / 'scade' / 'python_wrapper'
go = get_manager_instance(target_dir, 'python_wrapper')
go.load_environment()

model_dir = Path(__file__).parent.parent / 'Models'
ecore_dir = Path(ecore.__file__).parent / 'model'

# CAUTION: declare the libraries first to make sure binding is performed
#          before the models are preprocessed
emodel = PythonModel(False, 'e', ecore_dir / 'ecore.ecore', '3', library=True)
model = PythonModel(True, '', model_dir / 'pydata.ecore', '1', library=False)

go.add_models([emodel, model])

go.activate_services([CLASS, INIT, INTERFACE, LINK, TYPE])

# customization
InitService.use_args = True

# generate
go.go()
