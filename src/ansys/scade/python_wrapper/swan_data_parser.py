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

"""Intermediate model for Python proxy for Scade One standalone DLL."""

from enum import Enum
import json
from pathlib import Path
import re

import ansys.scade.python_wrapper.pydata as data


# classes
class EK(Enum):
    """Sections of the KCG mapping file."""

    PREDEFINED = 'predefined_type'
    ARRAY = 'array'
    ENUM = 'enum'
    ENUM_VALUE = 'enum_value'
    STRUCT = 'struct'
    FIELD = 'field'
    OPERATOR = 'operator'
    INPUTS = 'inputs'
    OUTPUTS = 'outputs'
    SENSOR = 'sensor'
    GLOBAL = 'global'
    FUNCTION = 'function'


# mapping code to model
# * key: <code id> or (<code id>, <role>)
# * value: <model id>
_links = {}


# C source files
swan_files = []

# type indexes in the json file, for model and code sections
_m_id_j = {}
_c_id_j = {}


def _get_model(model: data.Model, c_id: int, role: str = None) -> data.Entity:
    m_id = _links.get((c_id, role), c_id)
    return model.get_mapped_entity(m_id)


def _get_model_decl(id: int):
    # a declaration is a tuple <class> <attributes>
    #
    # model counterpart, if any...
    # the structure of the mapping file is not regular, some types have
    # the same ids w/o link, such as structs, and other have different ids
    # and links, like predefined operators
    m_decl = _m_id_j.get(id)
    if not m_decl:
        # try using the links
        m_decl = _m_id_j.get(_links.get(id))
    return m_decl


def parse_from_swan_mapping(mf: Path) -> tuple[data.Model, list]:
    """Build the intermediate model from the KCG mapping file."""
    model = data.Model(prefix='swan')
    with mf.open() as f:
        j = json.load(f)

    # index the declarations
    _index_mapping(model, j)

    # build place-holders for root operators
    _build_model(model, j['model'])

    # mapping
    global _links

    for m in j.get('mapping', []):
        role = m.get('role', None)
        key = (m['code_id'], role) if role else m['code_id']
        _links[key] = m['model_id']

    _build_code(model, j['code'])

    # add additional generated files
    swan_files.append('../cg_map.json')
    swan_files.append('../cg_log.json')

    return model, swan_files


def _index_mapping(model: data.Model, j):
    global _c_id_j, _m_id_j

    # index the used model json records
    for decl in j['model']:
        cls, atts = decl
        try:
            ek = EK(cls)
        except ValueError:
            continue
        if ek == EK.PREDEFINED:
            _m_id_j[atts['id']] = [ek, atts]
        elif ek == EK.ARRAY:
            _m_id_j[atts['id']] = [ek, atts]
        elif cls == EK.ENUM:
            _m_id_j[atts['id']] = [ek, atts]
            for v in atts.get('values', []):
                _m_id_j[v['id']] = [EK.ENUM_VALUE, v]
        elif ek == EK.STRUCT:
            _m_id_j[atts['id']] = [ek, atts]
            for f in atts.get('fields', []):
                _m_id_j[f['id']] = [EK.FIELD, f]
        elif ek == EK.OPERATOR:
            _m_id_j[atts['id']] = [ek, atts]
            for io in atts.get('inputs', []):
                _m_id_j[io['id']] = [EK.INPUTS, io]
            for io in atts.get('outputs', []):
                _m_id_j[io['id']] = [EK.OUTPUTS, io]
        elif ek == EK.SENSOR:
            _m_id_j[atts['id']] = [ek, atts]

    # index the type json records of the code
    for file in j['code']:
        for decl in file['declarations']:
            cls, atts = decl
            try:
                ek = EK(cls)
            except ValueError:
                continue
            if ek in {EK.PREDEFINED, EK.ARRAY, EK.ENUM, EK.STRUCT, EK.GLOBAL}:
                _c_id_j[atts['id']] = [ek, atts]


def _build_typed(model, typed: data.Typed, id: int):
    _, atts = _c_id_j.get(id)
    typed.c_type = atts['name']
    if isinstance(typed, data.Context):
        typed.link_type(_build_type(model, id)[1])
        assert isinstance(typed.type, data.Structure)
    else:
        typed.sizes, typed.type = _build_type(model, id)


def _build_type(model: data.Model, id: int):
    """Return a tuple list<size>, <type>."""
    if not id:
        return [], None

    # retrieve the corresponding json record
    c_ek, c_atts = _c_id_j[id]
    if c_ek == EK.ARRAY:
        sizes, type_ = _build_type(model, c_atts['base_type'])
        return sizes + [c_atts['size']], type_

    type_ = model.get_mapped_entity(id)
    if type_:
        # type already built
        return [], type_

    # model counterpart, if any...
    # the structure of the mapping file is not regular, some types have
    # the same ids w/o link, such as structs, and other have different ids
    # and links, like predefined operators
    m_type_decl = _get_model_decl(id)
    assert not m_type_decl or m_type_decl[0] == c_ek

    m_atts = m_type_decl[1] if m_type_decl else {}

    if c_ek == EK.PREDEFINED:
        type_ = data.Scalar(m_name=m_atts.get('name', ''), c_name=c_atts['name'])
    elif c_ek == EK.STRUCT:
        type_ = data.Structure(c_name=c_atts['name'])
        # model types are unnamed, get the code name if a model exist
        if m_atts:
            type_.m_name = type_.c_name
        for c_field_atts in c_atts['fields']:
            # either field or io
            m_field_decl = _get_model_decl(c_field_atts['id'])
            if not m_field_decl:
                # consider only fields with a counterpart in the model
                continue
            _, m_field_atts = m_field_decl
            field = data.Feature(
                m_name=_get_projected_name(m_field_atts),
                c_name=c_field_atts['name'],
            )
            _build_typed(model, field, c_field_atts['type'])
            type_.add_field(field)
            model.map_item(c_field_atts['id'], field)
    elif c_ek == EK.ENUM:
        type_ = data.Scalar(
            # no name/path for enums
            m_name=m_atts.get('name', 'int32'),
            # need a size for ctypes
            # c_name=c_atts['name'],
            c_name='swan_int32',
            path=m_atts.get('path'),
        )
    else:
        assert False

    model.add_type(type_)
    model.map_item(id, type_)

    return [], type_


def _get_projected_name(atts) -> str:
    name = atts['name']
    projection = atts.get('projection')
    if not projection:
        return name

    # TODO: support all the syntax
    # for now: support one level of groups only,
    #          2024 R1 --> .(<name>).(1)
    #          2024 R2 --> [<name>]
    if isinstance(projection, list):
        # assume 2024 R2
        return projection[0]
    # assume 2024 R1
    m = re.match(r'\.\((.*)\)\.\(1\)', projection)
    if not m:
        print(projection, 'analysis failure')
        return name
    return m.groups()[0]


def _build_model(model: data.Model, j):
    # read a few declarations from the model part of the mapping:
    # -> only root operators
    for cls, atts in j:
        if cls == 'operator':
            if not atts['root']:
                continue
            path = atts['path']
            op = data.Operator(
                m_name=path.split('::')[-1],
                path=path,
            )
            model.add_operator(op)
            model.map_item(atts['id'], op)
            for input in atts.get('inputs', []):
                m_name = _get_projected_name(input)
                io = data.IO(m_name=m_name, input=True)
                op.add_io(io)
                model.map_item(input['id'], io)
            for output in atts.get('outputs', []):
                m_name = _get_projected_name(output)
                io = data.IO(m_name=m_name, input=False)
                op.add_io(io)
                model.map_item(output['id'], io)


def _build_sensor(model: data.Model, c_atts) -> data.Feature:
    m_decl = _m_id_j.get(c_atts['id'])
    if not m_decl:
        return None
    m_ek, m_atts = m_decl
    assert m_ek == EK.SENSOR
    sensor = data.Global(
        m_name=m_atts['path'].split('::')[-1],
        path=m_atts['path'],
        c_name=c_atts['name'],
    )
    _build_typed(model, sensor, c_atts['type'])

    model.add_sensor(sensor)
    model.map_item(c_atts['id'], sensor)
    return sensor


def _build_function(model: data.Model, file, atts):
    for role in 'CycleMethod', 'ResetMethod', 'InitMethod':
        op = _get_model(model, atts['id'], role)
        if op:
            break
    else:
        # not a root operator or unexpected role
        return

    function = data.Function(c_name=atts['name'])
    # link the function to the operator
    if role == 'CycleMethod':
        op.set_cycle(function)
        # get the c_name from the cycle function to ensure uniqueness
        op.c_name = function.c_name
        # opportunity to set this property
        op.header = file['interface_file']
    elif role == 'ResetMethod':
        op.set_reset(function)
    else:
        assert role == 'InitMethod'
        op.set_init(function)

    for parameter in atts.get('parameters', []):
        typed = model.get_mapped_entity(parameter['id'])
        if not typed:
            # might be a context: retrieve it from the type's id
            # * verify it is the context of the operator
            # * create a context instance
            if _get_model(model, parameter['type'], 'ContextType') == op:
                if not op.context:
                    typed = data.Context()
                    op.set_context(typed)
                    model.map_item(parameter['id'], typed)
                else:
                    typed = op.context
        if not typed:
            print('%s/%s: parameter not found' % (op.path, parameter['name']))
        else:
            typed.c_name = parameter['name']
            typed.pointer = parameter['pointer']
            if not typed.type:
                _build_typed(model, typed, parameter['type'])
            function.link_parameter(typed)

    type_id = atts.get('return_type')
    if type_id:
        # must be a single (scalar) output
        # and function must be the cycle function
        io = op.ios[-1]
        assert not io.input
        io.return_ = True
        _build_typed(model, io, type_id)
        assert function == op.cycle
        function.link_return(io)

    if role == 'CycleMethod' and op.context:
        # bind the context to optional ios
        ios = {_.m_name: _ for _ in op.ios}
        for field in op.context.type.fields:
            io = ios.get(field.m_name)
            if io:
                op.context.link_io(io)
                io.sizes = field.sizes
                io.type = field.type
                io.c_name = field.c_name


def _build_code(model: data.Model, j):
    # read the declarations from the code part of the mapping
    for file in j:
        c = file.get('implementation_file')
        if c:
            swan_files.append(c)
            if c == 'swan_elaboration.c':
                model.elaboration = 'swan_elaboration'

        h = file.get('interface_file')
        if h:
            swan_files.append(h)

        for cls, atts in file.get('declarations', []):
            try:
                ek = EK(cls)
            except ValueError:
                continue
            if ek == EK.GLOBAL:
                _build_sensor(model, atts)
            elif ek == EK.FUNCTION:
                _build_function(model, file, atts)
