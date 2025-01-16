# Copyright (C) 2020 - 2025 ANSYS, Inc. and/or its affiliates.
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
Provides a ctypes factory for common Python literals.

The content of this module is included in the generated Python proxy.
"""

import ctypes

# begin-include


def make_array(raw_values, type_: type):
    """Return a ctypes array from a Python array."""
    assert issubclass(type_, ctypes.Array)
    return type_(*[make_value(_, type_._type_) for _ in raw_values])


def make_structure(raw_value, type_: type):
    """Return a ctypes structure from a Python dictionary or iterable."""
    assert issubclass(type_, ctypes.Structure)
    if isinstance(raw_value, dict):
        raw_values = [raw_value.get(_[0]) for _ in type_._fields_]
    else:
        # assume value is iterable and ordered
        raw_values = raw_value
    values = [
        field[1]() if value is None else make_value(value, field[1])
        for field, value in zip(type_._fields_, raw_values)
    ]
    return type_(*values)


def make_value(value, type_: type):
    """Return a ctypes value from a Python literal."""
    if isinstance(value, type_):
        return value
    if issubclass(type_, ctypes.Structure):
        return make_structure(value, type_)
    elif issubclass(type_, ctypes.Array):
        return make_array(value, type_)
    else:
        # assume scalar value
        return value


# end-include
