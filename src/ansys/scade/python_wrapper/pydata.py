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

"""
Provides a Python implementation of the ecore data model.

.. Note::

  * Generated parts, enclosed in ``#{{`` and ``#}}`` markers must not be modified
    unless they are themselves enclosed in ``#<<`` and ``#>>`` markers.
  * Do not add your own ``#<<`` and ``#>>`` markers.
"""

#%% begin

#%% import
from enum import Enum
from typing import List

#%% types

#{{type(56)
class CK(Enum):
    CONTEXT, INPUT, OUTPUT = range(1, 4)
#}}type


#%% classes

#{{class(2)
class Entity(object):
    def __init__(self, c_name: str = '', m_name: str = '', path: str = '', *args, **kwargs):
        self.c_name: str = c_name
        self.m_name: str = m_name
        self.path: str = path
        #<<init
        self._owner = None
        #>>init

    @property
    def owner(self) -> 'Entity':
        #<<6
        return self._owner
        #>>6
#}}class


#{{class(18)
class Type(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def scalar(self) -> bool:
        #<<19
        return isinstance(self, Scalar)
        #>>19
#}}class


#{{class(41)
class Typed(Entity):
    def __init__(self, c_type: str = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type: Type = None
        self.c_type: str = c_type
#}}class


#{{class(21)
class Feature(Typed):
    def __init__(self, sizes: List[int] = [], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sizes: List[int] = sizes

    #<<cls
    def scalar(self) -> bool:
        return self.type and self.type.scalar and not self.sizes
    #>>cls
#}}class


#{{class(14)
class IO(Feature):
    def __init__(self, input: bool = False, return_: bool = False, pointer: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input: bool = input
        self.return_: bool = return_
        self.context: Context = None
        self.pointer: bool = pointer
#}}class


#{{class(30)
class Scalar(Type):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#}}class


#{{class(24)
class Structure(Type):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields: List[Feature] = []
        self.context: Context = None

    def add_field(self, field: Feature):
        self.fields.append(field)
        field._owner = self
#}}class


#{{class(20)
class Context(Typed):
    def __init__(self, pointer: bool = False, kind: CK = CK.CONTEXT, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ios: List[IO] = []
        self.pointer: bool = pointer
        self.kind: CK = kind

    #<<cls
    def link_type(self, type_: Type):
        self.type = type_
        type_.context = self

    def link_io(self, io: IO):
        self.ios.append(io)
        io.context = self
    #>>cls
#}}class


#{{class(43)
class Global(Feature):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#}}class


# TODO: link_* for functions
#{{class(38)
class Function(Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameters: List[Typed] = []
        self.return_: Typed = None

    #<<cls
    def link_parameter(self, typed: Typed):
        self.parameters.append(typed)

    def link_return(self, typed: Typed):
        self.return_ = typed
    #>>cls
#}}class


#{{class(7)
class Operator(Entity):
    def __init__(self, header: str = '', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_context: Context = None
        self.context: Context = None
        self.ios: List[IO] = []
        self.cycle: Function = None
        self.init: Function = None
        self.reset: Function = None
        self.header: str = header

    def set_in_context(self, in_context: Context):
        self.in_context = in_context
        in_context._owner = self

    def set_context(self, context: Context):
        self.context = context
        context._owner = self

    def add_io(self, io: IO):
        self.ios.append(io)
        io._owner = self

    def set_cycle(self, cycle: Function):
        self.cycle = cycle
        cycle._owner = self

    def set_init(self, init: Function):
        self.init = init
        init._owner = self

    def set_reset(self, reset: Function):
        self.reset = reset
        reset._owner = self
#}}class


#{{class(26)
class Model(object):
    def __init__(self, prefix: str = '', elaboration: str = '', *args, **kwargs):
        self.types: List[Type] = []
        self.operators: List[Operator] = []
        self.sensors: List[Global] = []
        self.prefix: str = prefix
        self.elaboration: str = elaboration
        #<<init
        # mapping item -> data item
        self._mapping = {}
        #>>init

    def add_type(self, type: Type):
        self.types.append(type)
        type._owner = self

    def add_operator(self, operator: Operator):
        self.operators.append(operator)
        operator._owner = self

    def add_sensor(self, sensor: Global):
        self.sensors.append(sensor)
        sensor._owner = self

    #<<cls
    def get_mapped_entity(self, item: object) -> Entity:
        return self._mapping.get(item, None)

    def map_item(self, item: object, entity: Entity):
        assert entity not in self._mapping
        self._mapping[item] = entity
    #>>cls
#}}class


#%% declarations

#%% end
