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

"""Unit tests utils."""

from pathlib import Path
from subprocess import run
import sys

# note: importing apitools modifies sys.path to access SCADE APIs
from ansys.scade.apitools.info import get_scade_home

# must be imported after apitools
# isort: split
import scade
import scade.model.project.stdproject as std

from ansys.scade.python_wrapper.kcgpython import KcgPython

# stub the proxy's entries
import ansys.scade.wux.test.sctoc_stub  # noqa: F401


def load_project(path: Path) -> std.Project:
    """
    Load a Scade project in a separate environment.

    Note: Undocumented API.
    """
    project = scade.load_project(str(path))
    return project


def find_configuration(project: std.Project, name: str) -> std.Configuration:
    for configuration in project.configurations:
        if configuration.name == name:
            return configuration
    assert False


def build_proxy(path: Path, configuration: str) -> bool:
    """Build the Python proxy if obsolete or not present."""
    project = load_project(path)
    # retrieve the configuration
    conf = find_configuration(project, configuration)
    if not conf:
        print(configuration, 'unknown configuration')
        return False
    default = '$(Configuration)'
    target_dir = project.get_scalar_tool_prop_def('GENERATOR', 'TARGET_DIR', default, conf)
    target_dir = path.parent / target_dir.replace('$(Configuration)', configuration)
    module = KcgPython.get_module_name(project, conf)
    dll = target_dir / ('%s.dll' % module)
    if not dll.exists():
        obsolete = True
    else:
        # check timestamp versus project files
        ns = dll.stat().st_mtime_ns
        # advised enhancements:
        # * consider libraries
        # * consider only [x]scade files
        paths = [path] + [Path(_.pathname) for _ in project.file_refs]
        for file in paths:
            if file.stat().st_mtime_ns > ns:
                obsolete = True
                break
        else:
            obsolete = False
    if obsolete:
        # run scade -code to rebuild the python proxy
        exe = get_scade_home() / 'SCADE' / 'bin' / 'scade.exe'
        cmd = [exe, '-code', str(path), '-conf', configuration, '-sim']
        cp = run(cmd, capture_output=True, encoding='utf-8')
        if cp.stdout:
            print(cp.stdout)
        if cp.stderr:
            print(cp.stderr)
    # add the directory to sys.path
    if str(target_dir) not in sys.path:
        sys.path.append(str(target_dir))
    return dll.exists()
