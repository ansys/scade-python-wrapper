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


"""Python proxy for Scade One standalone DLL."""

import argparse
import json
import os
from os.path import abspath, relpath
from pathlib import Path
import re
from shutil import copy
import string
import subprocess

from ansys.scade.python_wrapper.rd.c_gen import generate_c
from ansys.scade.python_wrapper.rd.def_gen import generate_def
from ansys.scade.python_wrapper.rd.python_gen import (
    PredefInfo,
    generate_python,
    predefs_ctypes,
    predefs_values,
)
from ansys.scade.python_wrapper.swan_data_parser import parse_from_swan_mapping


class SwanPython:
    # identification
    tool = 'Scade One Python Proxy'
    version = '1.7.1'

    def __init__(
        self,
        cmdjson: Path,
        name: str,
        project: str,
        # pep8: bool,
        swan_size: str,
        swan_false: str,
        swan_true: str,
        no_cg: bool = False,
        all: bool = False,
    ):
        self.banner = '{0} {1}'.format(self.tool, self.version)
        self.cmdjson = cmdjson
        if project != '':
            self.project = Path(project).absolute()
        else:
            self.project = None
        with self.cmdjson.open() as f:
            j = json.load(f)
        self.target_dir = self.cmdjson.parent / j.get('target_dir', '.') / 'code'
        self.assets = [cmdjson.parent / _ for _ in j.get('files', [])]
        self.mf = self.target_dir.parent / 'cg_map.json'

        self.module = name

        self.swan_files = self.target_dir / 'swan_files.txt'
        self.swanpython_files = self.target_dir / 'swanpython_files.txt'
        self.pep8 = False  # pep8
        self.swan_size = swan_size
        self.swan_false = swan_false
        self.swan_true = swan_true
        self.CREATE_NO_WINDOW = 0x08000000
        # generated C files, for makefile
        self.sources = []
        self.defs = []
        self.lib_dir = Path(__file__).parent.parent / 'lib'
        self.no_cg = no_cg
        self.all = all

        # dictionary of project and dependencies as json trees, indexed by path
        # empty when the parameter project is not provided
        self.projects = {}

    def main(self):
        print(self.banner)

        # get the list of involved projects
        self.load_projects()

        # generate swan code
        ok = self.generate_code()
        if not ok:
            return

        # options
        predefs_ctypes['size'] = PredefInfo('ctypes.c_%s' % self.swan_size, '0')
        predefs_values['false'] = self.swan_false
        predefs_values['true'] = self.swan_true

        # generate wrappers
        ok = self.generate_wrappers()
        if not ok:
            return

        # build
        ok = self.build()
        if not ok:
            return

    def load_projects(self):
        # retrieve all projects with dependencies
        if self.project:
            self.load_project(self.project)

    def load_project(self, path: Path):
        if path in self.projects:
            # dependency already loaded
            return
        if path.is_file():
            with path.open() as f:
                project = json.load(f)
                # add the project to the list
                self.projects[path] = project
            for dependency in project.get('Dependencies', []):
                if dependency != '':
                    # use variable posix syntax $(...) -> ${...}
                    pattern = r'\$(\()(.+?)(\))'
                    dependency = re.sub(pattern, r'${\2}', dependency)
                    # add the built-in variable for libraries
                    kw = {
                        'SCADE_ONE_LIBRARIES_DIR': Path(
                            os.environ['S_ONE_HOME'], 'Libraries'
                        ).as_posix()
                    }
                    dependency = string.Template(dependency).safe_substitute(os.environ, **kw)
                    # restore $() for unexpanded variables
                    pattern = r'\$(\{)(.+?)(\})'
                    dependency = re.sub(pattern, r'$(\2)', dependency)
                    new_project = path.parent.joinpath(dependency).resolve()
                    self.load_project(new_project)

    # -----------------------------------------------------------------------
    # generation
    # -----------------------------------------------------------------------

    def is_obsolete(self) -> bool:
        dll = self.target_dir / ('%s.dll' % self.module)
        if not dll.exists():
            return True
        ns = dll.stat().st_mtime_ns
        for path in self.assets:
            if not path.exists() or path.stat().st_mtime_ns > ns:
                return True
        return False

    def generate_code(self) -> bool:
        # S_ONE_HOME must exist even if no code is generated
        if 'S_ONE_HOME' in os.environ:
            if self.no_cg:
                return True
            if not self.is_obsolete() and not self.all:
                return True
            cmd = [
                os.path.join(os.environ['S_ONE_HOME'], 'tools', 'swan_cg.exe'),
                str(self.cmdjson),
            ]
            gencode = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=self.CREATE_NO_WINDOW,
            )
            if gencode.stdout:
                print(gencode.stdout)
            if gencode.stderr:
                print(gencode.stderr)
            return gencode.returncode == 0
        else:
            print(
                'Error, set the S_ONE_HOME environment variable to the Scade One installation path'
            )
            return False

    def generate_wrappers(self):
        self.target_dir.mkdir(exist_ok=True)
        files = []

        model, swan_files_list = parse_from_swan_mapping(self.mf)
        if not model:
            # something went wrong, do not continue
            return False

        # generate swan_files.txt for files generated by KCG swan
        start = abspath(self.swan_files.parent)
        with self.swan_files.open('w') as f:
            # add files generated by Swan
            for file in swan_files_list:
                f.write(relpath(abspath(self.target_dir / file), start).replace('\\', '/') + '\n')

        # definition file: can't be generated in the target directory
        pathname = self.target_dir / ('%s.def' % self.module)
        files.append(pathname)
        self.defs.append(pathname.as_posix())
        generate_def(model, pathname, False, self.banner)

        pathname = self.target_dir / ('%s.py' % self.module)
        files.append(pathname)
        generate_python(model, pathname, cosim=False, pep8=self.pep8, banner=self.banner)

        pathname = self.target_dir / ('%s.c' % self.module)
        files.append(pathname)
        generate_c(model, pathname, self.banner)

        # copy Makefile
        pathname = self.lib_dir / 'Makefile'
        copy(pathname, self.target_dir)
        files.append(self.target_dir / 'Makefile')

        # generate swan_config.h
        pathname = self.target_dir / 'swan_config.h'
        files.append(pathname)
        self.generate_swan_config(pathname)

        print('generated Python wrapper:')

        start = abspath(self.swanpython_files.parent)
        with self.swanpython_files.open('w') as f:
            # add files generated by swanpython.py
            for file in files:
                f.write(relpath(abspath(file), start) + '\n')
                print('    {}'.format(file))
        print('')
        return True

    def build(self):
        if 'S_ONE_HOME' in os.environ:
            new_env = os.environ.copy()
            new_env['PATH'] = (
                os.path.join(new_env['S_ONE_HOME'], 'contrib', 'mingw64', 'bin')
                + ';'
                + new_env['PATH']
            )
            new_env['INCLUDE'] = r'%S_ONE_HOME%\contrib\mingw64\include'
            new_env['LIB'] = r'%S_ONE_HOME%\contrib\mingw64\lib'
            cmd = [
                'mingw32-make.exe',
                '-j',
                '4',
                '-C',
                str(self.target_dir),
                '-f',
                'Makefile',
                'MODULE={}'.format(self.module),
            ]
            build = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=self.CREATE_NO_WINDOW,
                env=new_env,
                shell=True,
            )
            if build.returncode == 0:
                print(build.stdout)
                return True
            else:
                print(build.stderr)
                return False
        else:
            print(
                'Error, set the S_ONE_HOME environment variable to the Scade One installation path'
            )
            return False

    def generate_swan_config(self, swan_config_pathname: Path):
        includes = ''
        resources = []
        for path, project in self.projects.items():
            for resource in project.get('Resources', ''):
                resource_kind = resource.get('Kind', '')
                resource_path = resource['Path']
                if resource_kind == 'ImportedTypes' or resource_kind == 'HeaderFile':
                    new_resource = path.parent.joinpath(resource_path).resolve()
                    if new_resource not in resources:
                        resources.append(new_resource)
        for resource in resources:
            includes = includes + '\n' + '#include "{}"'.format(str(resource))

        # create swan_config.h
        swan_config_default_file = self.lib_dir / 'swan_config_default.h'
        with swan_config_default_file.open() as f:
            swan_config_default = f.read()
        swan_config = swan_config_default.replace(
            '#include <string.h>', '#include <string.h>' + includes
        )
        with swan_config_pathname.open(mode='w') as f:
            f.write(swan_config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=SwanPython.tool)
    parser.add_argument('cmdjson', help='swan code gen settings file')
    parser.add_argument('-v', '--version', action='store_true', help='display the version')
    parser.add_argument(
        '-n', '--name', metavar='<name>', help='name of the output python module', required=True
    )
    parser.add_argument(
        '-p', '--project', metavar='<project>', help='Swan project file (*.sproj)', default=''
    )
    parser.add_argument('-a', '--all', action='store_true', help='force rebuild')
    # option not completed
    # parser.add_argument('-8', '--pep8', action='store_true', help='apply PEP8 naming rules')
    parser.add_argument(
        '--size', metavar='<swan_size>', help='type of swan_size', default='swan_int32'
    )
    parser.add_argument('--false', metavar='<swan_false>', help='value of swan_false', default='0')
    parser.add_argument('--true', metavar='<swan_true>', help='value of swan_true', default='1')
    # ease debug
    parser.add_argument('--no_cg', action='store_true', help='do not run swan_cg')

    options = parser.parse_args()

    cmdjson = Path(options.cmdjson)
    if cmdjson.is_file():
        cls = SwanPython(
            cmdjson,
            options.name,
            options.project,
            # options.pep8,
            options.size,
            options.false,
            options.true,
            options.no_cg,
            options.all,
        )
        if options.version:
            print('tool version %s %s' % (cls.tool, cls.version))

        cls.main()
    else:
        print("Error, {} file doesn't exist".format(str(cmdjson)))
