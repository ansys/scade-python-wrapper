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
Unit tests for the wrapper's Python literal conversion runtime.

Test objectives:

Verify ctypes instances are properly constructed from literals such
as scalar values, lists or dictionaries.
"""

import ctypes as c

import pytest

import ansys.scade.python_wrapper.lib.pywrprt as rt

# define few types


class CPoint(c.Structure):
    _fields_ = [('x', c.c_int), ('y', c.c_int)]


CLine = CPoint * 3


@pytest.mark.parametrize(
    'value, expected',
    [
        (CPoint(1, 2), (1, 2)),
        ([1, c.c_int(2)], (1, 2)),
        ({'x': 1, 'y': 2}, (1, 2)),
        ({'y': 2}, (0, 2)),
        ({'x': 1}, (1, 0)),
    ],
)
def test_point(value, expected):
    # make sure the generation does not fail:
    result = rt.make_value(value, CPoint)
    assert isinstance(result, CPoint)
    assert (result.x, result.y) == expected


@pytest.mark.parametrize(
    'value, expected',
    [
        ((CLine(CPoint(1, 2), CPoint(3, 4), CPoint(5, 6))), 21),
        ((CPoint(1, 2), (3, 4), [5, 6]), 21),
    ],
)
def test_line(value, expected):
    # make sure the generation does not fail:
    result = rt.make_value(value, CLine)
    assert isinstance(result, CLine)
    s = 0
    for p in result:
        s += p.x + p.y
