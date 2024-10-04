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

"""
Exercise the service' ``generate`` procedure.

These tests verify the code can be generated and are used
to measure the code coverage. The correctness of the generated
Python proxy is ensured by integration tests, with the same models and
configurations, that must be run on host.
"""

from pathlib import Path
import shutil
from typing import Set

import pytest

from ansys.scade.python_wrapper.kcgpython import KcgPython
import ansys.scade.wux.impl.proxyext as wux_proxy
from ansys.scade.wux.test.sctoc_stub import get_stub
from ansys.scade.wux.test.utils import ServiceProxy, reset_test_env
import ansys.scade.wux.wux as wux
from conftest import find_configuration, load_project, load_sdy_application, load_session


@pytest.mark.parametrize(
    'file, display, name, expected',
    [
        (
            'Types/Model/Model.etp',
            None,
            'Python',
            {'types_.py', 'types_.c', 'types_.def'},
        ),
        (
            'Types/Model/Model.etp',
            None,
            'Python IO',
            {'types_io.py', 'types_io.c', 'types_io.def'},
        ),
        (
            'Types/Model/Model.etp',
            None,
            'Python No Cosim',
            {'model.py', 'model.c', 'model.def'},
        ),
        (
            'Display/Model/Variables.etp',
            'Display/Display/Displays.etp',
            'Python',
            {'variables.py', 'variables.c', 'variables.def', 'sdy_variables.py'},
        ),
    ],
)
def test_generate(file: str, display: str, name: str, expected: Set[str], tmpdir):
    # make sure the generation does not fail:
    # generated code tested by integration tests
    reset_test_env()
    stub = get_stub()

    path = Path(__file__).parent / file
    project = load_project(path)
    configuration = find_configuration(project, name)
    # remind the target directory to ease its access for manual verifications
    print('tmpdir:', tmpdir)
    # copy the mapping file to the target directory
    # note: this implies the mapping file already exists and is added to Git
    shutil.copy(path.parent / configuration.name / 'mapping.xml', tmpdir)
    # load the Scade model
    session = load_session(path)
    # side effect: bypass the call to get_roots() that returns nothing when the unit tests are run
    wux.set_sessions([session])
    if display:
        # load mapping data
        mapping = path.with_suffix('.sdy')
        sdy_path = Path(__file__).parent / display
        sdy_application = load_sdy_application(mapping, session.model, sdy_path)
        wux.set_sdy_applications([sdy_application])
        # generate the code for displays
        service = ServiceProxy(wux_proxy)
        service.init(tmpdir, project, configuration)
        status = service.generate(tmpdir, project, configuration)

    service = ServiceProxy(KcgPython)
    service.init(tmpdir, project, configuration)
    status = service.generate(tmpdir, project, configuration)
    assert status
    # minimum assessment: generated files
    files = {Path(_).name for _ in stub.generated_files[KcgPython.tool]}
    print(name, stub.generated_files[KcgPython.tool])
    assert files == expected
