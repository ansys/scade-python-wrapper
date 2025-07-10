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

"""Wrapper for creating a SCADE standalone DLL and a Python proxy to access it."""

from pathlib import Path
import shutil
import sys
from typing import Optional

from scade.code.suite.mapping.c import MappingFile
import scade.code.suite.sctoc as sctoc  # type: ignore  # CPython module defined dynamically
from scade.code.suite.wrapgen.c import InterfacePrinter
from scade.code.suite.wrapgen.model import MappingHelpers
from scade.model.project.stdproject import Configuration, Project
import scade.model.suite as suite

from ansys.scade.apitools.info import get_scade_home
from ansys.scade.python_wrapper import __version__
from ansys.scade.python_wrapper.kcg_data_parser import parse_from_kcg_mapping
import ansys.scade.python_wrapper.props as props
from ansys.scade.python_wrapper.rd.c_gen import generate_c
from ansys.scade.python_wrapper.rd.def_gen import generate_def
from ansys.scade.python_wrapper.rd.python_gen import (
    PredefInfo,
    generate_python,
    predefs_ctypes,
    predefs_values,
)
import ansys.scade.python_wrapper.utils as utils

# SCADE evaluates the wrappers' main script instead of importing them:
# * this may lead to name conflicts in the global namespace
# * the legacy version of WUX declares a global variable wux
#   -> use wux2 instead of wux to ensure compatibility until
#      the legacy version is updated
import ansys.scade.wux.wux as wux2


class KcgPython:
    """
    Implements the *Proxy for Python* (``PYWRAPPER``) generation module.

    Refer to *Generation Module* in the User Documentation,
    section *3/ Code Integration Toolbox/Declaring Code Generator Extension*.
    """

    # identification
    tool = 'Ansys SCADE Python Wrapper'
    banner = '%s (%s)' % (tool, __version__)

    script_dir = Path(__file__).parent

    def __init__(self):
        # generated C files, for makefile
        self.sources = []
        self.defs = []
        self.libraries = []

        # interface
        self.checked: bool = False

        # settings
        self.cosim = False
        self.kcg_size = ''
        self.kcg_false = ''
        self.kcg_true = ''
        self.pep8 = False
        # graphical panels
        self.displays = False

    @classmethod
    def get_services(cls):
        """Declare the generation service Python Wrapper."""
        cls.instance = KcgPython()
        pyext = (
            '<UNUSED PYWRAPPER>',
            ('-OnInit', cls.instance.init),
            ('-OnGenerate', cls.instance.generate),
        )
        return [pyext]

    def init(self, target_dir: str, project: Project, configuration: Configuration):
        """
        Declare the required generation services and the execution order.

        Refer to *Generation Service* in the User Documentation,
        section *3/ Code Integration Toolbox/Declaring Code Generator Extension*.

        Parameters
        ----------
        target_dir : str
            Target directory for the code generation.

        project : Project
            Input SCADE Suite project.

        configuration : configuration
            SCADE Suite configuration selected for the code generation.
        """
        dependencies = []
        dependencies.append(('Code Generator', ('-Order', 'Before')))
        self.cosim = props.get_bool_tool_prop(
            project, props.PROP_COSIM, props.PROP_COSIM_DEFAULT, configuration
        )
        if self.cosim:
            dependencies.append(('Type Utils', ('-Order', 'Before')))

        panels = [
            _.split(',')
            for _ in project.get_tool_prop_def(
                'GENERATOR', 'DISPLAY_ENABLED_PANELS', [], configuration
            )
        ]
        active_panels = [_ for _ in panels if len(_) > 1 and _[1] != 'None']
        if active_panels:
            # add a dependency to SdyProxyExt and WuxDllExt
            dependencies.append(('WUX2_SDY_PROXY', ('-Order', 'Before')))
            dependencies.append(('WUX2_DLL_EXT', ('-Order', 'Before')))
            self.displays = True

        return dependencies

    def generate(self, target_dir: str, project: Project, configuration: Configuration):
        """
        Generate the code for this generation service.

        Refer to *Generation Service* in the User Documentation,
        section *3/ Code Integration Toolbox/Declaring Code Generator Extension*.

        Parameters
        ----------
        target_dir : str
            Target directory for the code generation.

        project : Project
            Input SCADE Suite project.

        configuration : configuration
            SCADE Suite configuration selected for the code generation.
        """
        print(self.banner)

        wux2.mf = MappingFile((Path(target_dir) / 'mapping.xml').as_posix())
        wux2.mh = MappingHelpers(wux2.mf)
        roots = wux2.mf.get_root_operators()
        wux2.ips = [InterfacePrinter(wux2.mh, root.get_scade_path()) for root in roots]

        # retrieve pragmas, cross-binding...
        sessions = wux2.get_sessions()
        self._cache_data(sessions[0].model, roots, wux2.mf.get_all_sensors())

        # settings
        name = Path(project.pathname).stem
        value = props.get_scalar_tool_prop(
            project, props.PROP_MODULE, props.PROP_MODULE_DEFAULT, configuration
        )
        value = value.replace('$(ProjectName)', utils.title_name(name))
        value = value.replace('$(project_name)', utils.lower_name(name))
        value = value.replace('$(PROJECT_NAME)', utils.upper_name(name))
        value = value.replace('$(projectname)', name)
        self.module = value
        self.kcg_size = props.get_scalar_tool_prop(
            project, props.PROP_KCG_SIZE, props.PROP_KCG_SIZE_DEFAULT, configuration
        )
        self.kcg_false = props.get_scalar_tool_prop(
            project, props.PROP_KCG_FALSE, props.PROP_KCG_FALSE_DEFAULT, configuration
        )
        self.kcg_true = props.get_scalar_tool_prop(
            project, props.PROP_KCG_TRUE, props.PROP_KCG_TRUE_DEFAULT, configuration
        )
        self.pep8 = False
        props.get_bool_tool_prop(project, props.PROP_PEP8, props.PROP_PEP8_DEFAULT, configuration)

        predefs_ctypes['size'] = PredefInfo('ctypes.c_%s' % self.kcg_size, '0')
        predefs_values['false'] = self.kcg_false
        predefs_values['true'] = self.kcg_true

        if self._check():
            # generate
            self._generate_wrappers(target_dir, project, configuration)

            # build
            self._declare_target(target_dir, project, configuration, roots)
            self.checked = True

        return self.checked

    def _cache_data(self, model: suite.Model, roots, sensors):
        """Add cross-references between scade.model.suite and scade.code.suite.mapping.c."""

        # set the elements' pragma in new attributes wrp__xx
        # create associations model <--> mapping in new attributes wrp__xxx
        def find_io(operator: suite.Operator, name: str) -> Optional[suite.LocalVariable]:
            for io in operator.inputs:
                if io.name == name:
                    return io
            for io in operator.hiddens:
                if io.name == name:
                    return io
            for io in operator.outputs:
                if io.name == name:
                    return io
            return None

        for root in roots:
            operator = model.get_object_from_path(root.get_scade_path())
            if not root:
                print(root.get_scade_path() + ': Scade operator not found')
                continue
            # association
            operator.wrp__target = root
            root.wrp__model = operator

            for cio in root.get_inputs() + root.get_outputs():
                variable = find_io(operator, cio.get_name())
                if variable is None:
                    print(cio.get_scade_path() + ': Scade io not found')
                    continue
                # association
                variable.wrp__target = cio
                cio.wrp__model = variable

        for sensor in sensors:
            sensor.wrp__model = model.get_object_from_path(sensor.get_scade_path())
            sensor.wrp__model.wrp__target = sensor

    def _check(self) -> bool:
        """
        Check for possible errors and stop if any.

        This method is a placeholder, there is no check for now.
        """
        checkerrors = [('Checks failed (expand for details)', '')]

        # add checks here
        error = len(checkerrors) > 1

        if error:
            sctoc.add_error('SCADE Python Proxy Checks', 'E_PYWRAPPER', checkerrors)

        return not error

    # -----------------------------------------------------------------------
    # generation
    # -----------------------------------------------------------------------

    def _generate_wrappers(
        self,
        target_dir,
        project,
        configuration,
    ):
        dir = Path(target_dir)
        basename = self.module
        files = []

        model = parse_from_kcg_mapping(wux2.mf)

        # definition file: can't be generated in the target directory
        pathname = dir / 'def' / ('%s.def' % basename)
        pathname.parent.mkdir(exist_ok=True)
        files.append('def/' + pathname.name)
        self.defs.append(pathname.as_posix())
        generate_def(model, pathname, self.cosim, self.banner)

        pathname = dir / ('%s.py' % basename)
        files.append(pathname.name)
        generate_python(model, pathname, cosim=self.cosim, pep8=self.pep8, banner=self.banner)
        if self.cosim:
            # add cosim management functions to the generated file
            self._generate_cosim(target_dir, project, configuration, pathname)

        if self.displays:
            if basename[0].isupper():
                usr = 'Usr' + basename
                sdy = 'Sdy' + basename
            else:
                usr = 'usr_' + basename
                sdy = 'sdy_' + basename
            pathname = dir / ('%s.py' % sdy)
            files.append(pathname.name)
            self._generate_display(project, configuration, pathname, basename, usr)

        pathname = dir / ('%s.c' % basename)
        files.append(pathname.name)
        generate_c(model, pathname, self.banner)
        self.sources.append(str(pathname))

        sctoc.add_generated_files(self.tool, files)

    def _generate_cosim(
        self,
        target_dir: str,
        project: Project,
        configuration: Configuration,
        py_pathname: Path,
    ):
        """Generate the additional files to support co-simulation."""
        with py_pathname.open('a') as f:
            f.write('\n')
            f.write('# co-simulation defaults\n')
            f.write('_scade_dir = r"%s"\n' % str(Path(sys.executable).parent))
            f.write('_host = "127.0.0.1"\n')
            f.write('_project = "%s"\n' % Path(project.pathname).as_posix())
            f.write('_configuration = "Simulation"\n')
            # take the first root
            assert wux2.mf is not None  # nosec B101  # addresses linter
            root = wux2.mf.get_root_operators()[0].get_scade_path().strip('/')
            f.write('_root = "%s"\n' % root)
            port = project.get_scalar_tool_prop_def('SSM', 'PROXYLISTENPORT', '64064', None)
            f.write('_port = %s\n' % port)
            f.write('\n')
            f.write('\n')
            f.write('# allow overriding co-simulation defaults\n')
            f.write('def set_cosim_environment(\n')
            f.write('        scade_dir:str = "",\n')
            f.write('        host:str = "",\n')
            f.write('        project:str = "",\n')
            f.write('        configuration:str = "",\n')
            f.write('        root:str = "",\n')
            f.write('        port:int = 0,\n')
            f.write('    ):\n')
            f.write('    global _scade_dir, _host, _project, _configuration, _root, _port\n')
            f.write('\n')
            f.write('    if scade_dir:\n')
            f.write('        _scade_dir = scade_dir\n')
            f.write('    if host:\n')
            f.write('        _host = host\n')
            f.write('    if project:\n')
            f.write('        _project = project\n')
            f.write('    if configuration:\n')
            f.write('        _configuration = configuration\n')
            f.write('    if root:\n')
            f.write('        _root = root\n')
            f.write('    if port:\n')
            f.write('        _port = port\n')
            f.write('\n')
            f.write('# end of file\n')

    def _generate_display(
        self,
        project: Project,
        configuration: Configuration,
        pathname: Path,
        dll: str,
        usrmodule: str,
    ):
        """
        Generate a proxy for loading the DLLs.

        The proxy has to be completed with a manual definition of the layers' structures.
        """
        specifications = wux2.get_specifications(project, configuration)
        structures = ', '.join(
            ['%sLayer' % layer.name for spec in specifications for layer in spec.layers]
        )

        with open(str(pathname), 'w') as f:
            f.write('import os.path\n')
            f.write('import ctypes\n')
            f.write('from sdyproxy import SdyProxy, SdyLayer\n')
            f.write('from %s import %s\n' % (usrmodule, structures))
            f.write('\n')
            f.write('# load the SCADE executable code\n')
            # do not add suffix for dynamic link libraries: might be .so or .dll
            dll_expr = "os.path.join(os.path.dirname(os.path.realpath(__file__)), '%s')" % dll
            f.write('_lib = ctypes.cdll.LoadLibrary(%s)\n' % dll_expr)
            f.write('_lib.py_load_sdy_dlls()\n')
            f.write('\n')
            f.write('\n')
            f.write('# instantiate the displays\n')
            for spec in specifications:
                layers = ', '.join(
                    ["('{0}', {0}Layer)".format(layer.name) for layer in spec.layers]
                )
                f.write(
                    "sdy_%s = SdyProxy(_lib, '%s', [%s])\n"
                    % (utils.lower_name(spec.basename), spec.prefix, layers)
                )

    # ------------------------------------------------------------------------
    # build
    # ------------------------------------------------------------------------

    def _declare_target(self, target_dir, project, configuration, roots):
        """Declare a DLL rule for the build process."""
        includes = []
        # whitebox simulation
        scade_dir = get_scade_home() / 'SCADE'
        pathname = scade_dir / 'lib' / 'SsmSlaveLib.c'
        self.sources.append(str(pathname))
        include = scade_dir / 'include'
        includes.append(include.as_posix())

        # runtime files
        include = self.script_dir / 'include'
        lib = self.script_dir / 'lib'
        sctoc.add_preprocessor_definitions('WUX_STANDALONE')
        if self.displays:
            sctoc.add_preprocessor_definitions('DLL_EXPORTS')
        includes.append(include.as_posix())
        sctoc.add_include_files(includes, False)
        if self.displays:
            # dllmain for sdy
            pathname = lib / 'sdyproxy.c'
            self.sources.append(str(pathname))

        # ease the usage by copying ssmproxy.py to the target directory
        shutil.copy(lib / 'ssmproxy.py', target_dir)
        if self.displays:
            shutil.copy(lib / 'sdyproxy.py', target_dir)

        exts = project.get_tool_prop_def('GENERATOR', 'OTHER_EXTENSIONS', [], configuration)
        exts.append('Code Generator')
        if self.displays:
            exts.append('WUX')
        if self.cosim:
            exts.append('Type Utils')
        # exts.append('WUX')
        compiler = project.get_scalar_tool_prop_def('SIMULATOR', 'COMPILER', '', configuration)
        if len(compiler) > 2 and (compiler[:2] == 'VC' or compiler[:2] == 'VS'):
            sctoc.add_dynamic_library_rule(
                self.module, self.sources, self.libraries, self.defs, exts, True
            )
        else:
            # assume gcc
            self.libraries.extend(self.defs)
            sctoc.add_dynamic_library_rule(
                self.module, self.sources, self.libraries, [], exts, True
            )


def get_module_name(project: Project, configuration: Configuration) -> str:
    """
    Return the name of the Python proxy module.

    The name is specified in the wrapper's settings and supports
    several macros to comply to the most popular naming rules.

    Parameters
    ----------
    project : Project
        Input SCADE Suite project.

    configuration : configuration
        SCADE Suite configuration selected for the code generation.
    """
    name = Path(project.pathname).stem
    value = props.get_scalar_tool_prop(
        project, props.PROP_MODULE, props.PROP_MODULE_DEFAULT, configuration
    )
    value = value.replace('$(ProjectName)', utils.title_name(name))
    value = value.replace('$(project_name)', utils.lower_name(name))
    value = value.replace('$(PROJECT_NAME)', utils.upper_name(name))
    value = value.replace('$(projectname)', name)
    return value
