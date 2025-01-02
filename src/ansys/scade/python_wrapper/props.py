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

"""Defines the properties used for the settings."""

from typing import List

from scade.model.project.stdproject import Annotable, Configuration

# properties
_PRAGMA = 'kcgpy'

# settings
_TOOL = 'PYEXT'
PROP_MODULE = 'MODULE'
PROP_MODULE_DEFAULT = '$(project_name)'
PROP_COSIM = 'COSIM'
PROP_COSIM_DEFAULT = False
PROP_KCG_SIZE = 'KCG_SIZE'
PROP_KCG_SIZE_DEFAULT = 'int64'
PROP_KCG_TRUE = 'KCG_TRUE'
PROP_KCG_TRUE_DEFAULT = '1'
PROP_KCG_FALSE = 'KCG_FALSE'
PROP_KCG_FALSE_DEFAULT = '0'
PROP_PEP8 = 'PEP8'
PROP_PEP8_DEFAULT = True

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def get_tool_prop(
    object: Annotable, name: str, default: List[str], configuration: Configuration = None
) -> List[str]:
    """Get the values of a property for the current tool."""
    return object.get_tool_prop_def(_TOOL, name, default, configuration)


def get_scalar_tool_prop(
    object: Annotable, name: str, default: str, configuration: Configuration = None
) -> str:
    """Get the value of a scalar property for the current tool."""
    return object.get_scalar_tool_prop_def(_TOOL, name, default, configuration)


def get_bool_tool_prop(
    object: Annotable, name: str, default: bool, configuration: Configuration = None
) -> bool:
    """Get the bool value of a property for the current tool."""
    return object.get_bool_tool_prop_def(_TOOL, name, default, configuration)


def set_tool_prop(
    object: Annotable,
    name: str,
    values: List[str],
    default: List[str],
    configuration: Configuration = None,
):
    """Set the values of a property for the current tool."""
    object.set_tool_prop_def(_TOOL, name, values, default, configuration)


def set_scalar_tool_prop(
    object: Annotable, name: str, value: str, default: str, configuration: Configuration = None
):
    """Get the scalar value of a property for the current tool."""
    object.set_scalar_tool_prop_def(_TOOL, name, value, default, configuration)


def set_bool_tool_prop(
    object: Annotable, name: str, value: bool, default: bool, configuration: Configuration = None
):
    """Set the bool value of a property for the current tool."""
    object.set_bool_tool_prop_def(_TOOL, name, value, default, configuration)
