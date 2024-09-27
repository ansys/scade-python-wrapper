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

import sys

# py_box.py/py_box.dll are produced from PyBox.etp
# add the target directory to the path if not set by the environment
try:
    import py_box as py_box
except ModuleNotFoundError:
    # PYTHONPATH not set
    from pathlib import Path  # noqa

    script_dir = Path(__file__).parent
    sys.path.append(str(script_dir.parent / 'Model' / 'Python'))
    import py_box as py_box

# get the optional cosimmuation parameter
cosim = sys.argv[-1] == '-cosim'

# set the sensors
# P::offset: float64
py_box.sensors.offset = 0.5

# create an instance of the root operator P::Root
root = py_box.Root(cosim=cosim)
# and reset it
root.call_reset()

# set the inputs
# P::Root/c: bool
root.c = True
# P::Root/v: Speed (defined as float64 ^ 3)
# root.v = (1.0, 2.0, 3.0)
root.v[0] = 1.0
root.v[1] = 2.0
root.v[2] = 3.0
# P::Root/v: float64
root.dt = 0.1

for cycle in range(4):
    # P::Root/i: int32
    root.i = cycle + 1

    # call the cyclic function
    # and force the SCADE Simulator to pause
    root.call_cycle(debug=True)

    # print the results
    # P::Root/pos: Position
    print(root.o, root.pos.x, root.pos.y, root.pos.z)

    # P::Root/c: bool
    root.c = False
