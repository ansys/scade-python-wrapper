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

"""Intermediate model for Python proxy for SCADE standalone DLL."""

from typing import List, Optional, Tuple

import scade.code.suite.mapping.c as c
import scade.code.suite.mapping.model as m

import ansys.scade.python_wrapper.pydata as data


def parse_from_kcg_mapping(mf) -> data.Model:
    """Build the intermediate model from the KCG mapping file."""
    model = data.Model(prefix='kcg')
    # sensors
    for m_sensor in mf.get_all_sensors():
        _build_sensor(model, m_sensor)

    # operators
    for m_op in mf.get_root_operators():
        _build_operator(model, m_op)

    return model


def _build_sensor(model: data.Model, m_sensor: m.Sensor) -> Optional[data.Feature]:
    c_sensor = m_sensor.get_generated()
    c_type = c_sensor.get_type()
    if not c_sensor:
        return None
    sensor = data.Global(
        m_name=m_sensor.get_name(),
        path=m_sensor.get_scade_path(),
        c_name=c_sensor.get_name(),
        c_type=c_type.get_name(),
    )
    sensor.sizes, sensor.type = _build_type(model, c_type)
    model.add_sensor(sensor)
    return sensor


def _build_type(model: data.Model, c_type: c.Type) -> Tuple[List[int], data.Type]:
    """Return a tuple list<size>, <type>."""
    if not c_type:
        return [], None
    elif c_type.is_typedef():
        assert isinstance(c_type, c.TypeDef)  # nosec B101  # addresses linter
        return _build_type(model, c_type.get_aliased_type())
    elif c_type.is_array():
        assert isinstance(c_type, c.Array)  # nosec B101  # addresses linter
        sizes, type_ = _build_type(model, c_type.get_base_type())
        return sizes + [c_type.get_size()], type_

    type_ = model.get_mapped_entity(c_type)
    if not type_:
        c_name = c_type.get_name()
        if c_type.is_predef_type():
            # extract model name from kcg_<name>
            type_ = data.Scalar(m_name=c_name.split('_')[-1], c_name=c_name)
        elif c_type.is_struct():
            assert isinstance(c_type, c.Struct)  # nosec B101  # addresses linter
            type_ = data.Structure(
                m_name=c_type.get_model().get_name() if c_type.get_model() else '',
                c_name=c_name,
                path=c_type.get_model().get_scade_path() if c_type.get_model() else '',
            )
            if c_type.is_context():
                # consider only the interface, if any
                c_fields = [
                    _ for _ in c_type.get_fields() if isinstance(_.get_model(), m.Variable)
                ]
            else:
                c_fields = [_ for _ in c_type.get_fields()]
            for c_field in c_fields:
                assert c_field.get_model()  # nosec B101  # addresses linter
                c_field_type = c_field.get_type()
                field = data.Feature(
                    m_name=c_field.get_model().get_name(),
                    c_name=c_field.get_name(),
                    c_type=c_field_type.get_name(),
                )
                field.sizes, field.type = _build_type(model, c_field_type)
                type_.add_field(field)
                model.map_item(c_field, field)
        else:
            assert c_type.is_enum()  # nosec B101  # addresses linter
            type_ = data.Scalar(
                m_name='int32',
                c_name='kcg_int32',
                path=c_type.get_model().get_scade_path(),
            )

        model.add_type(type_)
        model.map_item(c_type, type_)
    else:
        assert isinstance(type_, data.Type)  # nosec B101  # addresses linter
    return [], type_


def _build_operator(model: data.Model, m_op: m.Operator):
    c_op = m_op.get_generated()
    op = data.Operator(
        m_name=m_op.get_name(),
        c_name=c_op.get_name(),
        path=m_op.get_scade_path(),
        header=c_op.get_header_name(),
    )

    # functions
    op.set_cycle(data.Function(c_name=c_op.get_cycle().get_name()))
    assert op.cycle is not None  # nosec B101  # addresses linter
    pointers = {_.get_name() for _ in c_op.get_cycle().get_parameters() if _.is_pointer()}
    if c_op.get_init():
        op.set_init(data.Function(c_name=c_op.get_init().get_name()))
    if c_op.get_reset():
        op.set_reset(data.Function(c_name=c_op.get_reset().get_name()))

    # TODO?
    # _add_c_type(model, c_op.get_state_vector())
    _, type_ = _build_type(model, c_op.get_input_struct())
    if type_:
        # must be a structure
        assert isinstance(type_, data.Structure)  # nosec B101  # addresses linter
        # no names
        op.set_in_context(data.Context(kind=data.CK.INPUT))
        assert op.in_context is not None  # nosec B101  # addresses linter
        op.in_context.link_type(type_)
        op.in_context.c_type = c_op.get_input_struct().get_name()
        op.in_context.pointer = True
    # TODO?
    # _add_c_type(model, c_op.get_output_struct())
    _, type_ = _build_type(model, c_op.get_context())
    if type_:
        # must be a structure
        assert isinstance(type_, data.Structure)  # nosec B101  # addresses linter
        # no names
        op.set_context(data.Context(kind=data.CK.CONTEXT))
        assert op.context is not None  # nosec B101  # addresses linter
        op.context.link_type(type_)
        op.context.c_type = c_op.get_context().get_name()
        op.context.pointer = True
        # if there is a context, init and op functions must exist
        assert op.init is not None  # nosec B101  # addresses linter
        assert op.reset is not None  # nosec B101  # addresses linter
        op.init.add_parameter(op.context)
        op.reset.add_parameter(op.context)

    for m_input in m_op.get_inputs():
        c_input = m_input.get_generated()
        c_type = c_input.get_type()
        io = data.IO(
            m_name=m_input.get_name(),
            c_name=c_input.get_name(),
            path=m_input.get_scade_path(),
            c_type=c_type.get_name(),
            input=True,
            return_=False,
            pointer=c_input.get_name() in pointers,
        )
        io.sizes, io.type = _build_type(model, c_type)
        op.add_io(io)
        if isinstance(c_input, c.Parameter):
            op.cycle.add_parameter(io)
        else:
            assert op.in_context is not None  # nosec B101  # addresses linter
            op.in_context.add_io(io)
        model.map_item(c_input, io)

    for m_output in m_op.get_outputs():
        c_output = m_output.get_generated()
        if c_output:
            c_type = c_output.get_type()
            io = data.IO(
                m_name=m_output.get_name(),
                c_name=c_output.get_name(),
                path=m_output.get_scade_path(),
                c_type=c_type.get_name(),
                input=False,
                return_=False,
                pointer=c_output.get_name() in pointers,
            )
            io.sizes, io.type = _build_type(model, c_type)
            if isinstance(c_output, c.Parameter):
                op.cycle.add_parameter(io)
            else:
                assert op.context is not None  # nosec B101  # addresses linter
                op.context.add_io(io)
            model.map_item(c_output, io)
        else:
            # single scalar output
            c_type = c_op.get_cycle().get_return_type()
            io = data.IO(
                m_name=m_output.get_name(),
                c_name='',
                path=m_output.get_scade_path(),
                c_type=c_type.get_name(),
                input=False,
                return_=True,
                pointer=False,
            )
            io.sizes, io.type = _build_type(model, c_type)
            op.cycle.link_return(io)
        op.add_io(io)

    # update the parameters of cycle w.r.t. the contexts
    if op.in_context:
        op.cycle.add_parameter(op.in_context)
    if op.context:
        op.cycle.add_parameter(op.context)

    model.add_operator(op)
    model.map_item(c_op, op)
