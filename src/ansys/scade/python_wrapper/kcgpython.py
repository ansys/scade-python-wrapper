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

"""Wrapper for creating a SCADE standalone DLL and a Python proxy to access it."""

import os
from pathlib import Path
import shutil
import sys
from typing import List, Optional

from scade.code.suite.mapping.c import MappingFile
import scade.code.suite.sctoc as sctoc
from scade.code.suite.wrapgen.c import InterfacePrinter
from scade.code.suite.wrapgen.model import MappingHelpers
from scade.model.project.stdproject import Configuration, Project
import scade.model.suite as suite

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
import ansys.scade.wux.impl.display as wuxdisplay


class KcgPython:
    """
    Implements the *Proxy for Python* (``PYWRAPPER``) generation module.

    Refer to *Generation Module* in the User Documentation,
    section *3/ Code Integration Toolbox/Declaring Code Generator Extension*.
    """

    # identification
    tool = 'Ansys SCADE Python Wrapper'
    banner = '%s (%s)' % (tool, __version__)

    script_path = Path(__file__)
    script_dir = script_path.parent

    # generated C files, for makefile
    sources = []
    defs = []
    libraries = []

    # interface
    checked: bool = False

    # settings
    cosim = False
    kcg_size = ''
    kcg_false = ''
    kcg_true = ''
    pep8 = False
    # graphical panels
    panels = []
    displays = False

    @classmethod
    def get_services(cls):
        """Declare the generation service Python Wrapper."""
        pyext = (
            '<UNUSED PYWRAPPER>',
            ('-OnInit', KcgPython.init),
            ('-OnGenerate', KcgPython.generate),
        )
        return [pyext]

    @classmethod
    def init(cls, target_dir: str, project: Project, configuration: Configuration):
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
        cls.cosim = props.get_bool_tool_prop(
            project, props.PROP_COSIM, props.PROP_COSIM_DEFAULT, configuration
        )
        if cls.cosim:
            dependencies.append(('Type Utils', ('-Order', 'Before')))

        cls.panels = project.get_tool_prop_def(
            'GENERATOR', 'DISPLAY_ENABLED_PANELS', [], configuration
        )
        if cls.panels:
            # add a dependency to SdyExt and WuxDllExt
            dependencies.append(('WUX2_SDY', ('-Order', 'Before')))
            dependencies.append(('WUX2_DLL_EXT', ('-Order', 'Before')))

        return dependencies

    @classmethod
    def generate(cls, target_dir: str, project: Project, configuration: Configuration):
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
        print(cls.banner)

        mf = MappingFile((Path(target_dir) / 'mapping.xml').as_posix())
        mh = MappingHelpers(mf)
        roots = mf.get_root_operators()
        ips = [InterfacePrinter(mh, root.get_scade_path()) for root in roots]

        # only one scade model
        assert len(suite.get_roots()) == 1
        model = suite.get_roots()[0].model

        # retrieve pragmas, cross-binding...
        cls._cache_data(model, roots, mf.get_all_sensors())

        # settings
        name = Path(project.pathname).stem
        value = props.get_scalar_tool_prop(
            project, props.PROP_MODULE, props.PROP_MODULE_DEFAULT, configuration
        )
        value = value.replace('$(ProjectName)', utils.title_name(name))
        value = value.replace('$(project_name)', utils.lower_name(name))
        value = value.replace('$(PROJECT_NAME)', utils.upper_name(name))
        value = value.replace('$(projectname)', name)
        cls.module = value
        cls.kcg_size = props.get_scalar_tool_prop(
            project, props.PROP_KCG_SIZE, props.PROP_KCG_SIZE_DEFAULT, configuration
        )
        cls.kcg_false = props.get_scalar_tool_prop(
            project, props.PROP_KCG_FALSE, props.PROP_KCG_FALSE_DEFAULT, configuration
        )
        cls.kcg_true = props.get_scalar_tool_prop(
            project, props.PROP_KCG_TRUE, props.PROP_KCG_TRUE_DEFAULT, configuration
        )
        cls.pep8 = False
        props.get_bool_tool_prop(project, props.PROP_PEP8, props.PROP_PEP8_DEFAULT, configuration)

        predefs_ctypes['size'] = PredefInfo('ctypes.c_%s' % cls.kcg_size, '0')
        predefs_values['false'] = cls.kcg_false
        predefs_values['true'] = cls.kcg_true

        if cls._check():
            # generate
            cls._generate_wrappers(target_dir, project, configuration, mf, mh, ips)

            # build
            cls._declare_target(target_dir, project, configuration, roots)
            cls.checked = True

        return cls.checked

    @classmethod
    def _cache_data(cls, model: suite.Model, roots, sensors):
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

    @classmethod
    def _check(cls) -> bool:
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

    @classmethod
    def _generate_wrappers(
        cls,
        target_dir,
        project,
        configuration,
        mf: MappingFile,
        mh: MappingHelpers,
        ips: List[InterfacePrinter],
    ):
        dir = Path(target_dir)
        basename = cls.module
        files = []

        model = parse_from_kcg_mapping(mf)

        # definition file: can't be generated in the target directory
        pathname = dir / 'def' / ('%s.def' % basename)
        pathname.parent.mkdir(exist_ok=True)
        files.append('def/' + pathname.name)
        cls.defs.append(pathname.as_posix())
        generate_def(model, pathname, cls.cosim, cls.banner)

        pathname = dir / ('%s.py' % basename)
        files.append(pathname.name)
        generate_python(model, pathname, cosim=cls.cosim, pep8=cls.pep8, banner=cls.banner)
        if cls.cosim:
            # add cosim management functions to the generated file
            cls._generate_cosim(target_dir, project, configuration, mf, mh, pathname)

        if cls.displays:
            if basename[0].isupper():
                usr = 'Usr' + basename
                sdy = 'Sdy' + basename
            else:
                usr = 'usr_' + basename
                sdy = 'sdy_' + basename
            pathname = dir / ('%s.py' % sdy)
            files.append(pathname.name)
            cls._generate_display(project, pathname, basename, usr)

        pathname = dir / ('%s.c' % basename)
        files.append(pathname.name)
        generate_c(model, pathname, cls.banner)
        cls.sources.append(str(pathname))

        sctoc.add_generated_files(cls.tool, files)

    @classmethod
    def _generate_cosim(
        cls,
        target_dir: str,
        project: Project,
        configuration: Configuration,
        mf: MappingFile,
        mh: MappingHelpers,
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
            root = mf.get_root_operators()[0].get_scade_path().strip('/')
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

    @classmethod
    def _generate_display(cls, project: Project, pathname: Path, dll: str, usrmodule: str):
        """
        Generate a proxy for loading the DLLs.

        The proxy has to be completed with a manual definition of the layers' structures.
        """
        specifications = wuxdisplay.sdy_specifications
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

    @classmethod
    def _declare_target(cls, target_dir, project, configuration, roots):
        """Declare a DLL rule for the build process."""
        includes = []
        # whitebox simulation
        scade_dir = Path(os.environ['SCADE'])
        pathname = scade_dir / 'lib' / 'SsmSlaveLib.c'
        cls.sources.append(str(pathname))
        include = scade_dir / 'include'
        includes.append(include.as_posix())

        # runtime files
        include = Path(cls.script_dir).parent / 'include'
        lib = Path(cls.script_dir).parent / 'lib'
        sctoc.add_preprocessor_definitions('WUX_STANDALONE')
        if cls.displays:
            sctoc.add_preprocessor_definitions('DLL_EXPORTS')
        includes.append(include.as_posix())
        sctoc.add_include_files(includes, False)
        if cls.displays:
            # dllmain for sdy
            pathname = lib / 'sdyproxy.c'
            cls.sources.append(str(pathname))

        # ease the usage by copying ssmproxy.py to the target directory
        shutil.copy(lib / 'ssmproxy.py', target_dir)
        if cls.displays:
            shutil.copy(lib / 'sdyproxy.py', target_dir)

        exts = project.get_tool_prop_def('GENERATOR', 'OTHER_EXTENSIONS', [], configuration)
        exts.append('Code Generator')
        if cls.displays:
            exts.append('WUX')
        if cls.cosim:
            exts.append('Type Utils')
        # exts.append('WUX')
        compiler = project.get_scalar_tool_prop_def('SIMULATOR', 'COMPILER', '', configuration)
        if len(compiler) > 2 and (compiler[:2] == 'VC' or compiler[:2] == 'VS'):
            sctoc.add_dynamic_library_rule(
                cls.module, cls.sources, cls.libraries, cls.defs, exts, True
            )
        else:
            # assume gcc
            cls.libraries.extend(cls.defs)
            sctoc.add_dynamic_library_rule(cls.module, cls.sources, cls.libraries, [], exts, True)
