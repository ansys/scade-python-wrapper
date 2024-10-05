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

Verify the output values are identical to the input values for a
significant set of types.
"""

from pathlib import Path

import pytest

from conftest import build_kcg_proxy, build_swancg_proxy

# fixtures
test_dir = Path(__file__).parent


@pytest.fixture(scope='session')
def proxy_kcg_types() -> bool:
    """Ensure the proxy is built and up-to-date."""
    path = test_dir / 'Types' / 'Model' / 'Model.etp'
    return build_kcg_proxy(path, 'Python')


@pytest.fixture(scope='session')
def proxy_kcg_types_io() -> bool:
    """Ensure the proxy is built and up-to-date."""
    path = test_dir / 'Types' / 'Model' / 'Model.etp'
    return build_kcg_proxy(path, 'Python IO')


@pytest.fixture(scope='session')
def proxy_swang_types() -> bool:
    """Ensure the proxy is built and up-to-date."""
    path = test_dir / 'Types' / 'SOne' / 'Model'
    configuration = test_dir / 'Types' / 'SOne' / 'Proxy' / 'types_.json'
    return build_swancg_proxy(path, configuration)


def set_inputs(root, t):
    for i in range(4):
        t.sensors.faults[i] = i % 2
    for i in range(8):
        root.inBits[i] = (i + 1) % 2
    root.inBool = True
    root.inInt = 31
    root.inReal = 0.5
    root.inChar = 65  # 'A'
    root.inByte = 128
    root.inEnum = 1
    for i, (x, y) in enumerate([(1.0, 2.0), (4.0, 8.0)]):
        root.inLine[i].x = x
        root.inLine[i].y = y
    root.inPoint = t.CPoint_P(4.56, -7.89)
    root.inSpeed = 3.14
    root.inSpeeds = (type(root.inSpeeds))(12.34, 56.78)
    v = (
        (1.0, 2.0, 4.0, 8.0),
        (16.0, 32.0, 64.0, 128.0),
        (256.0, 512.0, 1024.0, 2048.0),
    )
    root.inArrays = (type(root.inArrays))(*v)


def float_cmp(a: float, b: float) -> bool:
    return abs(b - a) < 5.0e-6


def double_cmp(a: float, b: float) -> bool:
    return abs(b - a) < 5.0e-12


def check_outputs(root, t):
    assert root.outSensor0 == t.sensors.faults[0]
    for bi, bo in zip(root.inBits, root.outBits):
        assert bo == bi
    assert root.inBool == root.outBool
    assert root.inInt == root.outInt
    assert float_cmp(root.inReal, root.outReal)
    assert root.inChar == root.outChar
    assert root.inByte == root.outByte
    for li, lo in zip(root.inLine, root.outLine):
        assert lo.x == li.x
        assert lo.y == li.y
    assert root.inEnum == root.outEnum
    assert root.inSpeed == root.outSpeed
    for si, so in zip(root.inSpeeds, root.outSpeeds):
        assert double_cmp(so, si)
    for aai, aao in zip(root.inArrays, root.outArrays):
        for ai, ao in zip(aai, aao):
            assert ao == ai


# unit tests
def test_int_kcg_types(proxy_kcg_types):
    if not proxy_kcg_types:
        print('test skipped')
        return

    # sys.path must have been updated so that types_ is accessible
    import types_ as t

    for root in t.Function(cosim=False), t.Node(cosim=False):
        root.call_reset()
        set_inputs(root, t)
        root.call_cycle()
        check_outputs(root, t)


def test_int_kcg_types_io(proxy_kcg_types_io):
    if not proxy_kcg_types_io:
        print('test skipped')
        return

    # sys.path must have been updated so that types_ is accessible
    import types_io as t

    for root in t.Function(cosim=False), t.Node(cosim=False):
        root.call_reset()
        set_inputs(root, t)
        root.call_cycle()
        check_outputs(root, t)


def test_int_swancg_types(proxy_swang_types):
    if not proxy_swang_types:
        print('test skipped')
        return

    # sys.path must have been updated so that types_ is accessible
    import types_ as t

    for root in t.Function(cosim=False), t.Node(cosim=False):
        root.call_reset()
        set_inputs(root, t)
        root.call_cycle()
        check_outputs(root, t)
