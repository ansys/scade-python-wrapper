# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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
Unregisters the Code Generator extension registry files (SRG).

Refer to the :ref:`installation <getting_started/index:install in user mode>`
steps for more information.

It addresses SCADE 2024 R2 and prior releases.
SCADE 2025 R1 and above use the package's
``ansys.scade.registry`` entry point.
"""

import os
from pathlib import Path
import sys
from typing import Tuple

from ansys.scade.python_wrapper import get_srg_name

_APPDATA = os.getenv('APPDATA')


def _unregister_srg_file(name: str):
    """Delete the srg file from Customize."""
    assert _APPDATA
    dst = Path(_APPDATA, 'SCADE', 'Customize', name)
    dst.unlink(missing_ok=True)


def unregister() -> Tuple[int, str]:
    """Implement the ``ansys.scade.registry/unregister`` entry point."""
    _unregister_srg_file(get_srg_name())
    return (0, '')


def main():
    """Implement the ``ansys.scade.python_wrapper.unregister`` packages's project script."""
    code, message = unregister()
    if message:
        print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == '__main__':
    code = main()
    sys.exit(code)
