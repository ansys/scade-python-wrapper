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

"""Provides a Python interface for the SCADE Simulator co-simulation interface."""

import ctypes
from enum import Enum


# SsmProxy errors
class SPE(Enum):
    OK = 0

    # 1 - 1000 : Error related to gateway
    E_0001 = 1  # Cannot access project
    E_0002 = 2  # Cannot connect to SCADE on port 6311
    E_0003 = 3  # More than one instance of SCADE is running
    E_0004 = 4  # Cannot connect to SCADE on requested port
    E_0005 = 5  # Not connected to SCADE

    # 1001 - 2000 : Error related to proxy
    E_1001 = 1001  # Error during tcl evaluation of a command
    E_1002 = 1002  # Cannot Access simulator interface
    E_1003 = 1003  # Simulator is not launched
    E_1004 = 1004  # Cannot access simulator command
    E_1005 = 1005  # Cannot access simulator data
    E_1006 = 1006  # Cannot find variable
    E_1007 = 1007  # Undefined error
    E_1008 = 1008  # Cannot start simulator due to configuration or root node
    E_1009 = 1009  # SCADE co simulation is already started


class Buffer:
    def __init__(self):
        self.buffer = b''

    def reset(self):
        self.buffer = b''

    def append(self, text: bytes) -> int:
        self.buffer += text
        return 1


_PFN_STR_APPEND = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.py_object)
_str_append = _PFN_STR_APPEND(lambda value, buffer: buffer.append(value))


class SsmProxy:
    def __init__(
        self,
        dll: str,
        host: str,
        scade: str,
        project: str,
        configuration: str,
        root: str,
        port: int,
    ):
        self._lib = ctypes.cdll.LoadLibrary(dll)

        # no need to specify restype: all the functions return a C int (default)
        self._set_host_name = self._lib.SsmSetHostName
        self._set_host_name.argtypes = [ctypes.c_char_p]
        self._set_scade_install_path = self._lib.SsmSetScadeInstallPath
        self._set_scade_install_path.argtypes = [ctypes.c_char_p]
        self._open_scade_simulator = self._lib.SsmOpenScadeSimulator
        self._open_scade_simulator.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int,
        ]

        self.set_host_name(host)
        self.set_scade_install_path(scade)
        self.open_scade_simulator(project, configuration, root, port)

        self._close_scade_simulator = self._lib.SsmCloseScadeSimulator
        self._close_scade_simulator.argtypes = []
        self._dbg_step = self._lib.SsmDbgStep
        self._dbg_step.argtypes = [ctypes.c_int]
        self._gui_activate = self._lib.SsmGuiActivate
        self._gui_activate.argtypes = []
        self._gui_refresh = self._lib.SsmGuiRefresh
        self._gui_refresh.argtypes = []
        self._set_input = self._lib.SsmSetInput
        self._set_input.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._set_input_vector = self._lib.SsmSetInputVector
        self._set_input_vector.argtypes = [ctypes.c_char_p]
        self._set_connect_retry = self._lib.SsmSetConnectRetry
        self._set_connect_retry.argtypes = [ctypes.c_int]
        self._step = self._lib.SsmStep
        self._step.argtypes = [ctypes.c_int, ctypes.c_int]
        self._pause = self._lib.SsmPause
        self._pause.argtypes = []
        self._save_scenario = self._lib.SsmSaveScenario
        self._save_scenario.argtypes = [ctypes.c_char_p]

        # buffer for conversions
        self._buffer = Buffer()

    def close_scade_simulator(self):
        return SPE(self._close_scade_simulator())

    def dbg_step(self, cycle: int = 1):
        return self._dbg_step(cycle)

    def gui_activate(self):
        return self._gui_activate()

    def gui_refresh(self):
        return self._gui_refresh()

    def open_scade_simulator(self, project: str, configuration: str, root: str, port: int):
        return self._open_scade_simulator(
            bytes(project, 'utf-8'), bytes(configuration, 'utf-8'), bytes(root, 'utf-8'), port
        )

    def set_input(self, input: str, value: str):
        return self._set_input(bytes(input, 'utf-8'), bytes(value, 'utf-8'))

    # additional function used by the wrapper KCG-Python
    def set_c_input(self, input: str, c_pointer, cvt):
        # cvt is expected to be a the conversion function from Type Utils
        self._buffer.reset()
        cvt(c_pointer, _str_append, self._buffer)
        return self._set_input(bytes(input, 'utf-8'), self._buffer.buffer)

    def set_input_vector(self, vector: str):
        return self._set_input_vector(bytes(vector, 'utf-8'))

    def set_connect_retry(self, retry: int):
        return self._set_connect_retry(retry)

    def set_host_name(self, host: str):
        return self._set_host_name(bytes(host, 'utf-8'))

    def set_scade_install_path(self, scade: str):
        return self._set_scade_install_path(bytes(scade, 'utf-8'))

    def step(self, cycle: int = 1, refresh: bool = True):
        return self._step(cycle, refresh)

    def pause(self):
        return self._pause()

    def save_scenario(self, path: str):
        return self._save_scenario(bytes(path, 'utf-8'))

    def __del__(self):
        self.close_scade_simulator()
