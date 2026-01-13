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

"""Provides a Python interface for the SCADE Display graphical panels."""

import ctypes
from typing import List, Tuple


class SdyLayer(ctypes.Structure):
    """Opaque declaration of a layer."""

    pass


class SdyProxy:
    """Python interface for the SCADE Display graphical panels."""

    def __init__(self, lib, basename: str, layer_types: List[Tuple[str, SdyLayer]]):
        self._lib = lib
        # self._lib.py_load_sdy_dlls()

        # predefined interface
        for name in ['init', 'draw', 'lockio', 'unlockio', 'cancelled']:
            layer_fct = getattr(self._lib, f'{basename}__{name}')
            layer_fct.argtypes = []
            layer_fct.restype = ctypes.c_int
            setattr(self, f'_{name}', layer_fct)
        self.init()
        # layer functions
        for layer_name, layer_type in layer_types:
            layer_fct = getattr(self._lib, f'{basename}_L_{layer_name}')
            layer_fct.argtypes = []
            layer_fct.restype = ctypes.c_void_p
            setattr(self, f'{layer_name}', layer_type.from_address(layer_fct()))

    def init(self) -> int:
        """Call DLL's ``init`` function."""
        return self._init()  # type: ignore  # method added dynamically
        # return self._init()

    def draw(self) -> int:
        """Call DLL's ``draw`` function."""
        return self._draw()  # type: ignore  # method added dynamically

    def lockio(self) -> int:
        """Call DLL's ``lockio`` function."""
        return self._lockio()  # type: ignore  # method added dynamically

    def unlockio(self) -> int:
        """Call DLL's ``unlockio`` function."""
        return self._unlockio()  # type: ignore  # method added dynamically

    def cancelled(self) -> bool:
        """Call DLL's ``cancelled`` function."""
        return self._cancelled() != 0  # type: ignore  # method added dynamically

    # def __del__(self):
    #     self._lib.py_unload_sdy_dlls()
