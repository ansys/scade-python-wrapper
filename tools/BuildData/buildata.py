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
Generates parts of the ``pydata.py`` module from is ``pydata.ecore`` model.

This modules adapts the ``lbsjv`` generator by overriding and extending its generation services.
"""

from pathlib import Path

from ecore import EClass, EOperation, EParameter, EReference
import lbsjv
from lbsjv import FileType, Language, generator
from lbsjv.defaults import Extension
from lbsjv.generator import (
    ClassService,
    DataTypeService,
    EObjectService,
    GetLowerName,
    InterfaceService,
    Model,
)
from lbsjv.generator.tools import TypedObjectVisitor
from lbsjv.interfaces import IBlockManager

# ---------------------------------------------------------------------------
# redefinitions
# ---------------------------------------------------------------------------


class DataTypedObjectVisitor(TypedObjectVisitor):
    """Redefinition of the visitor for the typed objects."""

    def VisitETypedElement(self, eTypedElement, class_name, reference_name):
        """Add a ``s`` for the collections."""
        super().VisitETypedElement(eTypedElement, class_name, reference_name)
        # default: same name
        eTypedElement.targetVar = GetLowerName(eTypedElement.targetName)
        type = eTypedElement.eType
        if type is not None and type.__dict__.get('targetName') is None:
            pass
        if not type or eTypedElement.upperBound != -1:
            eTypedElement.targetName = eTypedElement.targetVar
        else:
            eTypedElement.targetName = eTypedElement.targetVar + 's'


class DataModel(Model):
    """Customization of the of the default Model."""

    def __init__(self, filename, ident, library):
        super().__init__(filename, ident, library)

    def PrepareTypedObjects(self):
        """Run the customized visitor."""
        DataTypedObjectVisitor().Visit(self.model)


# ---------------------------------------------------------------------------
# new services
# ---------------------------------------------------------------------------


class ExtendedService(EObjectService):
    """Extension of the ecore model."""

    def __init__(self):
        super().__init__(use_args=True, local_typing=True)

    # IService interface
    def Init(self, manager):
        """Initialize the service."""
        super().Init(manager)
        svcclass = self.manager.FindService('class')
        svcclass.AddExtension(AddExtension(self))

    def AddEContents(self, cls: EClass):
        """Prevent the default implementation."""
        # don't need this function
        return None

    # IService interface
    def ExtendData(self, iter):
        """Extend the ecore model."""
        result = super().ExtendData(iter)
        for cls in self.model.iterClasses():
            if not isinstance(cls, EClass) or cls.name == 'EObject':
                continue
            for reference in cls.eReferences:
                # if not reference.containment or not reference.many: continue
                if not reference.containment:
                    continue
                operation = self.AddAdd(cls, reference)
                if operation is not None:
                    cls.eOperations.append(operation)
                result = True
        return result

    def AddAdd(self, cls: EClass, reference: EReference):
        """Add the ``Add`` operations to a class."""
        prefix = 'Add' if reference.many else 'Set'
        name = '%s%s%s' % (prefix, reference.name[0].upper(), reference.name[1:])
        for operation in cls.eOperations:
            if operation.name == name:
                return None
        operation = EOperation(name=name)
        operation._eContainer = cls
        operation.extension = 'add'
        operation.oid = cls.oid + 'add_%s' % reference.oid
        operation.doc = []
        operation.targetName = '%s_%s' % (prefix.lower(), reference.targetVar)
        parameter = EParameter(reference.name, lowerBound=0, upperBound=0)
        parameter._eContainer = operation
        operation.eParameters.append(parameter)
        parameter.eType = reference.eType
        parameter.typingName = parameter.eType.targetName
        parameter.targetName = reference.targetVar
        parameter.initValue = None
        # add the reference to ease flushing the code
        operation.reference = reference

        return operation


# ---------------------------------------------------------------------------
# new extensions
# ---------------------------------------------------------------------------


class AddExtension(Extension):
    """Generation of the operations ``AddXxx``."""

    def __init__(self, service: EObjectService):
        super().__init__('add')
        self.service = service

    def Flush(self, new: bool, data: object, blockManager: IBlockManager):
        """Generate the function body."""
        # data is an operation
        operation = data
        reference = operation.reference

        bm = blockManager
        if reference.many:
            bm.FlushString(
                '        self.%s.append(%s)\n' % (reference.targetName, reference.targetVar)
            )
        else:
            bm.FlushString('        self.%s = %s\n' % (reference.targetName, reference.targetVar))
        bm.FlushString('        %s._owner = self\n' % reference.targetVar)

        return True


# ---------------------------------------------------------------------------
# generation with lbjsv
# ---------------------------------------------------------------------------


def Generate(model, libraries, targetDir):
    """Run the generation."""
    print('generating classes for ' + Path(model).name + '...')

    # load files, replace pathnames by models
    model = DataModel(model, 'Data', False)
    libraries = [DataModel(library, 'N/A', True) for library in libraries]

    # complete the initialization of the models
    for library in libraries:
        library.PrepareModel(checkOid=False)
    model.PrepareModel(checkOid=True)

    path = Path(model.filename)

    go = lbsjv.Manager()
    # languages
    lpy = Language('Python', None, None, '#')
    # file types
    ftpy = FileType('^.*\.py$', Path(generator.__file__).parent / 'pyclass.tp', lpy)
    services = [ClassService(), InterfaceService(), DataTypeService(), ExtendedService()]
    for service in services:
        service.targetDir = targetDir
    env = {'languages': [lpy], 'types': [ftpy], 'services': services}
    go.SetEnvironment(env)
    project = {
        'models': [model],
        'libraries': libraries,
        'files': [str(targetDir / Path(file).name.lower()) for file in [model.filename]],
    }
    # arbitrary name used as template, the file does not exist (yet?)
    go.SetProject(str((targetDir / path.name).with_suffix('.prj')), project)
    go.Go()
    print('...done')


if __name__ == '__main__':
    libraries = [
        (str(Path(generator.__file__).parent.parent.parent / 'ecore' / 'model' / 'ecore.ecore')),
    ]

    # targetDir
    parentDir = Path(__file__).parent.parent
    targetDir = parentDir.parent / 'src' / 'ansys' / 'scade' / 'python_wrapper'
    model = str(parentDir / 'Models' / 'pydata.ecore')
    Generate(model, libraries, targetDir)
