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

import os
from pathlib import Path
import platform
from subprocess import run
import sys
import winreg as reg

# note: importing apitools modifies sys.path to access SCADE APIs
from ansys.scade.apitools.info import get_scade_home

# must be imported after apitools
# isort: split
import scade
import scade.model.project.stdproject as std
import scade.model.suite as suite
import scade.model.suite.displaycoupling as dc

from ansys.scade.python_wrapper.kcgpython import get_module_name
from ansys.scade.python_wrapper.swanpython import SwanPython

# stub the proxy's entries
import ansys.scade.wux.test.sctoc_stub  # noqa: F401


def _get_scade_one_homes(min='v241', max='v999'):
    """Get the list of Scade One installation directories."""
    if platform.system() != 'Windows':
        return []
    names = []
    try:
        hklm = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Ansys Inc')
    except OSError:
        return []
    for i in range(reg.QueryInfoKey(hklm)[0]):
        name = reg.EnumKey(hklm, i)
        if name < min or name >= max:
            continue
        try:
            dir, _ = reg.QueryValueEx(reg.OpenKey(hklm, r'%s\Ansys Scade One' % name), 'Path')
            names.append((name, dir))
        except FileNotFoundError:
            pass
    dirs = [dir for _, dir in sorted(names, key=lambda x: x[0])]
    return dirs


def load_session(*paths: Path) -> suite.Session:
    """
    Create an instance of Session instance and load the requested models.
    """
    session = suite.Session()
    for path in paths:
        session.load2(str(path))
    return session


def load_project(path: Path) -> std.Project:
    """
    Load a Scade project in a separate environment.

    Note: Undocumented API.
    """
    project = scade.load_project(str(path))
    return project


def load_sdy_application(mapping: Path, model: suite.Model, *displays: Path) -> dc.SdyApplication:
    """Load a Scade Suite - Display mapping file in a separate environment."""
    app = dc.SdyApplication()
    for display in displays:
        app.load_sdy_project_tcl(str(display))
    app.load_mapping_file_tcl(str(mapping))
    app.mapping_file.model = model
    return app


def find_configuration(project: std.Project, name: str) -> std.Configuration:
    for configuration in project.configurations:
        if configuration.name == name:
            return configuration
    assert False


def build_kcg_proxy(path: Path, configuration: str) -> Path | None:
    """
    Build the Python proxy if obsolete or not present.

    This requires the package to be registered to the version of SCADE used
    to run the tests, which is possible only on host systems, with a manual
    installation step.
    """
    project = load_project(path)
    # retrieve the configuration
    conf = find_configuration(project, configuration)
    if not conf:
        print(configuration, 'unknown configuration')
        return None
    default = '$(Configuration)'
    target_dir = project.get_scalar_tool_prop_def('GENERATOR', 'TARGET_DIR', default, conf)
    target_dir = path.parent / target_dir.replace('$(Configuration)', configuration)
    module = get_module_name(project, conf)
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
    return dll if dll.exists() else None


def build_swancg_proxy(project_dir: Path, configuration: Path) -> Path | None:
    """Build the Python proxy if obsolete or not present."""
    s_one_home = 'S_ONE_HOME'
    home = None
    if not os.environ.get(s_one_home):
        homes = _get_scade_one_homes()
        home = homes[-1] if homes else None
    if home:
        os.environ[s_one_home] = home
        print('set S_ONE_HOME to', os.environ.get(s_one_home))
    else:
        print('using S_ONE_HOME =', os.environ.get(s_one_home))
    # the name of the module is the basename of the configuration file
    module = configuration.stem
    # target directory: expected to be the the configuration file's directory
    target_dir = configuration.parent / 'code'
    # the name of the project must be the name of its directory
    project = project_dir / (project_dir.stem + '.sproj')
    cls = SwanPython(
        configuration,
        configuration.stem,
        str(project),
        # options.pep8,
        swan_size='swan_int32',
        swan_false='0',
        swan_true='1',
        # code generation required
        no_cg=False,
        # generate only if the dll is obsolete with respect to the Scade One model files
        all=False,
    )
    cls.main()
    # add the target directory to sys.path
    if str(target_dir) not in sys.path:
        sys.path.append(str(target_dir))
    dll = target_dir / ('%s.dll' % module)
    if home:
        # remove the added variable
        os.environ.pop(s_one_home)
    return dll if dll.exists() else None
