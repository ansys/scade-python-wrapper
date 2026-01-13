# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

# variables.py/variables.dll are produced from Variables.etp
from pathlib import Path
import sys
import time

# variables.py/variables.dll are produced from Variables.etp
# add the target directory to the path if not set by the environment
try:
    import variables
except ModuleNotFoundError:
    # PYTHONPATH not set
    from pathlib import Path  # noqa

    script_dir = Path(__file__).parent
    sys.path.append(str(script_dir.parent / 'Model' / 'Python'))
    import variables

from sdy_variables import sdy_speed, sdy_throttles

# get the optional cosimmuation parameter
cosim = sys.argv[-1] == '-cosim'

# create an instance of the root operator P::Root
root = variables.Engine(cosim=cosim)
# and reset it
root.call_reset()

# set the inputs
root.speed = 0.0

# run until one window is closed
while not (sdy_speed.cancelled() or sdy_throttles.cancelled()):
    # call the cyclic function
    root.call_cycle(debug=True)

    # print the results
    print(root.throttle1, '\t', root.throttle2)
    # update the displays
    sdy_speed.lockio()
    sdy_speed.Speed.Speed = root.speed
    sdy_speed.unlockio()
    sdy_speed.draw()
    sdy_throttles.lockio()
    sdy_throttles.Throttles.One = root.throttle1
    sdy_throttles.Throttles.Two = root.throttle2
    sdy_throttles.unlockio()
    sdy_throttles.draw()
    # wait
    time.sleep(0.1)

    root.speed += 0.01
