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

"""Provides the Ansys SCADE Python Wrapper's Settings page."""

from typing import List

import scade
from scade.model.project.stdproject import Configuration, Project
from scade.tool.suite.gui.settings import Page as SettingsPage
from scade.tool.suite.gui.widgets import CheckBox, EditBox, Label, Widget

import ansys.scade.python_wrapper.props as props

# ---------------------------------------------------------------------------
# globals
# ---------------------------------------------------------------------------

# default value, for compatibility with TCL pages
H_BUTTON = 20
H_COMBO = 130
H_EDIT = 20
H_LABEL = 20
H_LIST = 130
H_TREE = 30
# width of ... buttons
W_DOTS = 20

# position / size for labels of the first columns
xl1 = 17
wl1 = 140
# position / size for fields of the first columns
xf1 = 160
wf1 = 190
# space between two lines
dy = 30

# ---------------------------------------------------------------------------
# reusable control library
# ---------------------------------------------------------------------------


class LabelEditBox(EditBox):
    """Label and EditBox in the same line."""

    def __init__(self, owner, text: str, wl: int, x=10, y=10, w=50, h=14, **kwargs):
        self.label = Label(owner, text, x=x, y=y + 4, w=wl, h=H_LABEL)
        super().__init__(owner, x=x + wl, y=y, w=w - wl, h=H_EDIT, **kwargs)
        self.owner = owner

    def on_layout(self):
        """Layout the control."""
        self.set_constraint(Widget.RIGHT, self.owner, Widget.RIGHT, -xl1)


class CheckBoxEx(CheckBox):
    """Resizable CheckBox."""

    def __init__(self, owner, text: str, x=10, y=10, w=50, h=14, **kwargs):
        super().__init__(owner, text, x=x, y=y, w=w, h=H_BUTTON, **kwargs)
        self.owner = owner

    def on_layout(self):
        """Layout the control."""
        pass


class PageUtils:
    """Utilities for settings pages."""

    def __init__(self):
        scade.output('initialized controls\n')
        # self.controls = []

    def add_edit(self, y: int, text: str) -> EditBox:
        """Add an edit box."""
        edit = LabelEditBox(self, text, wl1, x=xl1, y=y, w=wl1 + wf1)
        self.controls.append(edit)
        return edit

    def add_cb(self, y: int, text: str) -> CheckBox:
        """Add a check box."""
        cb = CheckBoxEx(self, text, x=xl1, y=y, w=wl1 + wf1)
        self.controls.append(cb)
        return cb

    def layout_controls(self):
        """Layout the controls."""
        for control in self.controls:
            control.on_layout()


class SettingsPageEx(SettingsPage, PageUtils):
    """Extended settings page."""

    def __init__(self, *args):
        super(PageUtils, self).__init__()
        super().__init__(*args)
        # runtime properties
        self.controls = []
        # get, set, prop, prop_default
        self.properties: List[callable, callable, str, str] = []

    def on_layout(self):
        """Layout the page."""
        self.layout_controls()

    def on_close(self):
        """Close the page."""
        pass

    def on_display(self, project: Project, configuration: Configuration):
        """Display the page."""
        for _, pfnset, name, default in self.properties:
            if isinstance(default, bool):
                value = props.get_bool_tool_prop(project, name, default, configuration)
            else:
                value = props.get_scalar_tool_prop(project, name, default, configuration)
            pfnset(value)

    def on_validate(self, project: Project, configuration: Configuration):
        """Validate the page."""
        for pfnget, _, name, default in self.properties:
            value = pfnget()
            if isinstance(value, bool):
                props.set_bool_tool_prop(project, name, value, default, configuration)
            else:
                props.set_scalar_tool_prop(project, name, value, default, configuration)


# ---------------------------------------------------------------------------
# settings pages
# ---------------------------------------------------------------------------

TITLE = 'Python'


class SettingsPagePython(SettingsPageEx):
    """Settings page for Python Wrapper."""

    def __init__(self):
        super().__init__(TITLE)

        # controls
        self.ed_module = None
        self.cb_cosim = None
        self.ed_size = None
        self.ed_false = None
        self.ed_true = None
        self.cb_pep8 = None

    def on_build(self):
        """Build the page."""
        # alignment for the first line
        y = 10

        self.ed_module = self.add_edit(y, '&Module name:')
        y += dy
        self.cb_cosim = self.add_cb(y, '&Enable co-simulation')
        y += dy
        self.ed_size = self.add_edit(y, 'kcg_&size:')
        y += dy
        self.ed_false = self.add_edit(y, 'kcg_&false:')
        y += dy
        self.ed_true = self.add_edit(y, 'kcg_&true:')
        y += dy
        # remove the option, requirements to be refined
        # self.cb_pep8 = self.add_cb(y, '&Apply PEP8 naming rules'); y += dy

        self.properties = [
            (
                self.ed_module.get_name,
                self.ed_module.set_name,
                props.PROP_MODULE,
                props.PROP_MODULE_DEFAULT,
            ),
            (
                self.cb_cosim.get_check,
                self.cb_cosim.set_check,
                props.PROP_COSIM,
                props.PROP_COSIM_DEFAULT,
            ),
            (
                self.ed_size.get_name,
                self.ed_size.set_name,
                props.PROP_KCG_SIZE,
                props.PROP_KCG_SIZE_DEFAULT,
            ),
            (
                self.ed_false.get_name,
                self.ed_false.set_name,
                props.PROP_KCG_FALSE,
                props.PROP_KCG_FALSE_DEFAULT,
            ),
            (
                self.ed_true.get_name,
                self.ed_true.set_name,
                props.PROP_KCG_TRUE,
                props.PROP_KCG_TRUE_DEFAULT,
            ),
            # (self.cb_pep8.get_check, self.cb_pep8.set_check, PROP_PEP8, PROP_PEP8_DEFAULT)
        ]


# ---------------------------------------------------------------------------
# GUI items
# ---------------------------------------------------------------------------

SettingsPagePython()
