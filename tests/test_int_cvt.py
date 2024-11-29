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

"""
Unit tests for the wrapper's cosimulation conversion functions.

Test objectives:

Verify the conversion functions provide the correct string value
for a significant set of types.

Reminder: The tests using build_kcg_proxy require specific installation
steps, that can't be executed for automated tests on ci-cd runners.
"""

import ctypes
from pathlib import Path
import sys

import pytest

from conftest import build_kcg_proxy


# buffer for C conversion functions
class Buffer:
    def __init__(self):
        self.buffer = ''

    def reset(self):
        self.buffer = ''

    def append(self, text: bytes) -> int:
        self.buffer += str(text, 'utf_8')
        return 1


buffer = Buffer()

PFN_STR_APPEND = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.py_object)
str_append = PFN_STR_APPEND(lambda value, buffer: buffer.append(value))

# fixtures
test_dir = Path(__file__).parent


@pytest.fixture(scope='session')
def proxy_types() -> Path | None:
    """Ensure the proxy is built and up-to-date."""
    path = test_dir / 'Types' / 'Model' / 'Model.etp'
    return build_kcg_proxy(path, 'Python')


def test_int_cvt(proxy_types):
    if proxy_types is None:
        # DLL can't be built on GH runners
        print('test skipped')
        return

    # update sys.path to access the generated files
    old_path = sys.path.copy()
    sys.path.append(str(proxy_types.parent))
    try:
        import types_ as t

        import_error = ''
    except BaseException as e:
        import_error = str(e)
    # restore the path
    sys.path = old_path
    assert import_error == ''

    # bool
    buffer.reset()
    st = t._kcg_bool_cvt(ctypes.byref(ctypes.c_uint8(0)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == 'false'

    buffer.reset()
    st = t._kcg_bool_cvt(ctypes.byref(ctypes.c_uint8(1)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == 'true'

    # char
    buffer.reset()
    st = t._kcg_char_cvt(ctypes.byref(ctypes.c_char(65)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == "'A'"

    # int32
    buffer.reset()
    st = t._kcg_int32_cvt(ctypes.byref(ctypes.c_int(31)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '31'

    # float64
    buffer.reset()
    st = t._kcg_float64_cvt(ctypes.byref(ctypes.c_double(0.5)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '0.5'

    # enum
    buffer.reset()
    st = t._Enum_P_cvt(ctypes.byref(ctypes.c_int(1)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == 'P::V2'

    # bits
    buffer.reset()
    st = t._Bits_P_cvt((ctypes.c_uint8 * 8)(*[_ % 2 for _ in range(8)]), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '(false, true, false, true, false, true, false, true)'

    # byte
    buffer.reset()
    st = t._Byte_P_cvt(ctypes.byref(ctypes.c_uint8(128)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '128'

    # arrays
    buffer.reset()
    v = (
        (1.0, 2.0, 4.0, 8.0),
        (16.0, 32.0, 64.0, 128.0),
        (256.0, 512.0, 1024.0, 2048.0),
    )
    st = t._Arrays_P_cvt(((ctypes.c_float * 4) * 3)(*v), str_append, buffer)
    assert st == 1
    assert (
        buffer.buffer
        == '('
        + ', '.join(
            [
                '(1.0, 2.0, 4.0, 8.0)',
                '(16.0, 32.0, 64.0, 128.0)',
                '(256.0, 512.0, 1024.0, 2048.0)',
            ]
        )
        + ')'
    )

    # line
    buffer.reset()
    st = t._Line_P_cvt((t.CPoint_P * 2)((1.0, 2.0), (4.0, 8.0)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '((1.0, 2.0), (4.0, 8.0))'

    # point
    buffer.reset()
    st = t._Point_P_cvt(ctypes.byref(t.CPoint_P(x=1.0, y=2.0)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '(1.0, 2.0)'

    # speed
    buffer.reset()
    st = t._Speed_P_cvt(ctypes.byref(ctypes.c_double(0.5)), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '0.5'

    # speeds
    buffer.reset()
    st = t._Speeds_P_cvt((ctypes.c_double * 2)(0.5, 2.0), str_append, buffer)
    assert st == 1
    assert buffer.buffer == '(0.5, 2.0)'
