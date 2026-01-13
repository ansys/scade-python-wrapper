# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

"""Provides a Python interface to the SCADE DLL."""

# design note: linters complain about unknown attributes such as py_name, py_value, etc.
# these attributes are added dynamically to SCADE Python API entities at startup.
# there are two workarounds, not applied since they would introduce too much noise in this file:
# * add type: ignore comments
# * use setattr/getattr functions

# TODO:
# * error (or warning multiple instances not supported) with global context
# * rename when name of io is either a Python keyword or conflicts with one of:
#   * call_reset
#   * call_init
#   * call_cycle
#   * out_c
#   * in_c
# * declare a structure of classes corresponding to the package hierarchy
# * refactor the design:
#   * rely more on c_op.get_cycle().get_parameters() to simply the algorithms

from collections import namedtuple
from keyword import iskeyword
from pathlib import Path
from typing import Optional

import ansys.scade.python_wrapper.pydata as data
import ansys.scade.python_wrapper.utils as utils

PredefInfo = namedtuple('PredefInfo', ['type_name', 'init_value'])

predefs_ctypes = {
    'int8': PredefInfo('ctypes.c_int8', '0'),
    'int16': PredefInfo('ctypes.c_int16', '0'),
    'int32': PredefInfo('ctypes.c_int32', '0'),
    'int64': PredefInfo('ctypes.c_int64', '0'),
    'uint8': PredefInfo('ctypes.c_uint8', '0'),
    'uint16': PredefInfo('ctypes.c_uint16', '0'),
    'uint32': PredefInfo('ctypes.c_uint32', '0'),
    'uint64': PredefInfo('ctypes.c_uint64', '0'),
    'bool': PredefInfo('ctypes.c_uint8', '0'),
    'char': PredefInfo('ctypes.c_int8', '0'),
    'float32': PredefInfo('ctypes.c_float', '0.0'),
    'float64': PredefInfo('ctypes.c_double', '0.0'),
    'size': PredefInfo('ctypes.c_int64', '0'),
}

predefs_native = {
    'int8': PredefInfo('int', '0'),
    'int16': PredefInfo('int', '0'),
    'int32': PredefInfo('int', '0'),
    'int64': PredefInfo('int', '0'),
    'uint8': PredefInfo('int', '0'),
    'uint16': PredefInfo('int', '0'),
    'uint32': PredefInfo('int', '0'),
    'uint64': PredefInfo('int', '0'),
    'bool': PredefInfo('bool', 'False'),
    'char': PredefInfo('int', '0'),
    'float32': PredefInfo('float', '0.0'),
    'float64': PredefInfo('float', '0.0'),
    'size': PredefInfo('int', '0'),
}

predefs_values = {'false': '0', 'true': '1'}


# side effects
_pep8 = None


def _get_predef_info(c_type_name: str, native: bool) -> Optional[PredefInfo]:
    if native:
        return predefs_native[c_type_name] if c_type_name in predefs_native else None
    else:
        return predefs_ctypes[c_type_name] if c_type_name in predefs_ctypes else None


# def _get_array_base_type_and_sizes(c_array: c.Array) -> Tuple[c.Type, List[int]]:
#     sizes = [c_array.get_size()]
#     base_type = c_array.get_base_type()
#     while base_type.is_array():
#         sizes.append(base_type.get_size())
#         base_type = base_type.get_base_type()
#     return base_type, sizes


def _get_python_name(name: str) -> str:
    return name + '_' if iskeyword(name) else name


def _get_python_type_name(type_: data.Type, native: bool, sizes=None) -> str:
    # make anonymous structures, that must be contexts, private
    if type_.scalar:
        # must be a predefined type
        # TODO: what about imported scalar types?
        pi = _get_predef_info(type_.m_name, native)
        assert pi is not None  # nosec B101  # addresses linter
        name = pi.type_name
    else:
        # the type names are less visible: use the path to ensure a unique name
        assert isinstance(type_, data.Structure)  # nosec B101  # addresses linter
        prefix = '' if type_.m_name else '_'
        if not native:
            prefix += 'C'
        if False and type_.m_name:
            # the type names are less visible: use the path to ensure a unique name
            name = '_'.join(type_.path.strip('/').split('::'))
            # prefix = ''
        else:
            name = type_.c_name
            # prefix = '_'
        if _pep8:
            name = utils.title_name(name)
        name = prefix + name
    name = _get_python_name(name)

    if sizes:
        return '(%s * %s)' % (name, ' * '.join([str(_) for _ in sizes]))
    else:
        return name


def _get_python_typed_name(typed: data.Typed) -> str:
    name = typed.m_name if typed.m_name else typed.c_name
    return utils.lower_name(name) if _pep8 else name


def _get_python_operator_name(operator: data.Operator) -> str:
    # assume there are no conflicts: ignore the packages and
    # get the model name of the operator
    name = operator.m_name
    return _get_python_name(utils.title_name(name) if _pep8 else name)


def _get_cvt_name(typed: data.Typed) -> str:
    return '_%s_cvt' % (utils.lower_name(typed.c_type) if _pep8 else typed.c_type)


def _cache(model: data.Model):
    # add runtime attributes in the model:
    # .py_name (Feature): name of the property for read/write access or structure's field
    # .py_member (Global, IO, Context): name of class member for storing the feature
    # .py_value (Global, IO): whether it is an allocated scalar data
    #       some members are pointers to scalar values, that must be dereferenced, when:
    #       * it is a reference to a C global variable (sensor)
    #       * it is an output, neither in the context or the returned value of the cycle function
    for sensor in model.sensors:
        name = _get_python_typed_name(sensor)
        sensor.py_name = _get_python_name(name)
        sensor.py_member = 'self._' + name
        sensor.py_value = sensor.py_member + '.value' if sensor.scalar() else sensor.py_member

    for type_ in model.types:
        if not type_.scalar:
            for field in type_.fields:
                field.py_name = _get_python_name(_get_python_typed_name(field))

    for operator in model.operators:
        if operator.in_context:
            operator.in_context.py_member = 'self._in_c'
        if operator.context:
            operator.context.py_member = 'self._out_c'

        for io in operator.ios:
            name = _get_python_typed_name(io)
            io.py_name = _get_python_name(name)
            if io.return_:
                # unique scalar output
                io.py_member = 'self._' + name
                io.py_value = io.py_member
            elif io.input:
                if io.context:
                    io.py_member = io.context.py_member + '.' + io.py_name
                else:
                    io.py_member = 'self._' + name
                io.py_value = io.py_member
            else:
                # output, always a pointer, whether it is in the context or not
                io.py_member = 'self._' + name
                io.py_value = io.py_member + '.value' if io.scalar() else io.py_member


def generate_python(
    model: data.Model, py_pathname: Path, cosim: bool, pep8: bool, banner: str = ''
) -> None:
    """Generate the Python wrapping file for the DLL."""
    global _pep8

    def write_accessors(typed: data.Feature):
        # typed is either a sensor or an i/o
        type_ = typed.type
        assert type_ is not None  # nosec B101  # addresses linter
        # generate setters for sensors and inputs
        if isinstance(typed, data.Global):
            setter = True
        else:
            assert isinstance(typed, data.IO)  # nosec B101  # addresses linter
            setter = typed.input
        # TODO: no name for not scalar types
        if typed.scalar():
            type_name = _get_python_type_name(type_, True)
            arg_type = ': %s' % type_name
            return_type = ' -> %s' % type_name
        else:
            arg_type = ''
            return_type = ''
        f.write('    @property\n')
        ctx = typed.context if isinstance(typed, data.IO) else None
        if cosim:
            c_name = typed.c_name if typed.c_name else typed.py_name
            if ctx:
                cvt_field = '%s._ptr_%s' % (ctx.py_member, c_name)
            elif type_.scalar:
                cvt_field = 'ctypes.pointer(%s)' % typed.py_member
            else:
                cvt_field = typed.py_member
        f.write('    def %s(self)%s:\n' % (typed.py_name, return_type))
        if cosim and setter and not typed.scalar():
            f.write(
                "        if _proxy: self.modified_inputs['%s'] = (%s, %s)\n"
                % (typed.path, cvt_field, _get_cvt_name(typed))
            )
        if type_.m_name == 'bool' and typed.scalar():
            f.write('        return %s == %s\n' % (typed.py_value, predefs_values['true']))
        else:
            f.write('        return %s\n' % typed.py_value)
        f.write('\n')
        if setter:
            f.write('    @%s.setter\n' % typed.py_name)
            f.write('    def %s(self, value%s) -> None:\n' % (typed.py_name, arg_type))
            if type_.m_name == 'bool' and typed.scalar():
                f.write(
                    '        %s = %s if value else %s\n'
                    % (typed.py_value, predefs_values['true'], predefs_values['false'])
                )
            else:
                if ctx or typed.scalar():
                    f.write('        %s = value\n' % typed.py_value)
                else:
                    py_type = _get_python_type_name(typed.type, False, typed.sizes)
                    f.write('        %s = make_value(value, %s)\n' % (typed.py_value, py_type))
            if cosim:
                f.write(
                    "        if _proxy: _proxy.set_c_input('%s', %s, %s)\n"
                    % (typed.path, cvt_field, _get_cvt_name(typed))
                )
            f.write('\n')

    _cache(model)

    _pep8 = pep8

    # types
    # output contexts are opaque: do not consider them
    struct_types = [
        _
        for _ in model.types
        if isinstance(_, data.Structure) and (not _.context or _.context.kind != data.CK.CONTEXT)
    ]
    if cosim:
        # types used in the interface, initialized from the list of sensors
        c_interface_types = {_.c_type for _ in model.sensors}

    with py_pathname.open('w') as f:
        if banner:
            f.write('# generated by %s\n' % banner)
            f.write('\n')
        f.write('from pathlib import Path\n')
        f.write('import ctypes\n')
        if cosim:
            f.write('from ssmproxy import SsmProxy\n')
        f.write('\n')
        f.write('\n')
        f.write('# load the SCADE executable code\n')
        f.write("_lib = ctypes.cdll.LoadLibrary(str(Path(__file__).with_suffix('')))\n")
        if model.elaboration:
            f.write('\n')
            f.write('elaboration_fct = _lib.%s\n' % model.elaboration)
            f.write('elaboration_fct.argtypes = []\n')
            f.write('elaboration_fct.restype = ctypes.c_void_p\n')
            f.write('elaboration_fct()\n')
        f.write('\n')
        if cosim:
            f.write('\n')
            f.write('_proxy = None\n')
            f.write('\n')
            f.write('\n')
            f.write('def set_ssm_proxy(proxy: SsmProxy):\n')
            f.write('    global _proxy\n')
            f.write('    _proxy = proxy\n')
            f.write('\n')

        f.write('\n')
        f.write('def make_value(value, type_: type):\n')
        f.write('    """Return a ctypes value from a Python literal."""\n')
        f.write('    return type_(*value) if isinstance(value, tuple) else value\n')
        f.write('\n')

        if model.sensors:
            f.write('\n')
            f.write('# sensors\n')
            f.write('class _Sensors:\n')
            f.write('    def __init__(self):\n')
            for sensor in model.sensors:
                assert sensor.type is not None  # nosec B101  # addresses linter
                type_name = _get_python_type_name(sensor.type, False, sensor.sizes)
                f.write(
                    '        %s = %s.in_dll(_lib, "%s")\n'
                    % (sensor.py_member, type_name, sensor.c_name)
                )
            f.write('\n')

            for sensor in model.sensors:
                write_accessors(sensor)

            f.write('\n')
            f.write('# unique instance\n')
            f.write('sensors = _Sensors()\n')
            f.write('\n')

        if struct_types:
            f.write('\n')
            f.write('# C structures')
            if len([_ for _ in struct_types if _.m_name]) != 0:
                # generate an intermediate structure to access the fields by index
                # for user defined structures
                f.write('\n')
                f.write('\n')
                f.write(
                    'class SequencedStructure(ctypes.Structure):\n'
                    '    def __getitem__(self, key):\n'
                    '        field = self._fields_[key][0]\n'
                    "        return eval(f'self.{field}')\n"
                    '\n'
                    '    def __setitem__(self, key, value):\n'
                    '        field = self._fields_[key][0]\n'
                    "        exec(f'self.{field} = {value}')\n"
                )
                f.write('\n')
                parent_struct = 'SequencedStructure'
            else:
                parent_struct = 'ctypes.Structure'
        for struct in struct_types:
            f.write('\n')
            struct_name = _get_python_type_name(struct, False)
            f.write('class %s(%s):\n' % (struct_name, parent_struct))
            if struct.context:
                # consider only the ios (i.e. elements in the model), if any
                fields = [_ for _ in struct.fields if _.m_name]
            else:
                # must be a user type
                fields = struct.fields
            f.write(
                '    _fields_ = [%s]\n'
                % ',\n                '.join(
                    [
                        ("('%s', %s)" % (_.py_name, _get_python_type_name(_.type, False, _.sizes)))
                        for _ in fields
                    ]
                )
            )
            if cosim and struct.context:
                if struct.context.kind == data.CK.INPUT:
                    f.write('\n\n')
                    f.write('    def __init__(self, *args, **kw):\n')
                    f.write('        super().__init__(*args, **kw)\n')
                    f.write('\n')
                    f.write('        for name, type_ in self._fields_:\n')
                    f.write('            offset = getattr(%s, name).offset\n' % struct_name)
                    f.write('            ptr = ctypes.pointer(type_.from_buffer(self, offset))\n')
                    f.write("            # self.__dict__['_ptr_%s' % name] = ptr\n")
                    f.write("            setattr(self, '_ptr_%s' % name, ptr)\n")

            f.write('\n')

        for op in sorted(model.operators, key=lambda o: o.path):
            f.write('\n')
            f.write('class %s:\n' % _get_python_operator_name(op))
            f.write('    def __init__(self, cosim: bool = True):\n')
            if cosim:
                f.write('        if cosim and not _proxy:\n')
                f.write('            # create a cosim proxy instance with default values\n')
                f.write('            proxy = SsmProxy(\n')
                f.write('                str(Path(__file__).with_suffix("")),\n')
                f.write('                _host,\n')
                f.write('                _scade_dir,\n')
                f.write('                _project,\n')
                f.write('                _configuration,\n')
                f.write('                _root,\n')
                f.write('                _port,\n')
                f.write('            )\n')
                f.write('            set_ssm_proxy(proxy)\n')
                f.write('\n')
            if op.in_context:
                assert op.in_context.type is not None  # nosec B101  # addresses linter
                f.write(
                    '        %s = %s()\n'
                    % (op.in_context.py_member, _get_python_type_name(op.in_context.type, False))
                )
            if op.context:
                f.write('        alloc_fct = _lib.py_alloc_%s\n' % op.c_name)
                f.write('        alloc_fct.argtypes = []\n')
                f.write('        alloc_fct.restype = ctypes.c_void_p\n')
                f.write('        context = alloc_fct()\n')
                f.write(
                    '        %s = ctypes.c_void_p.from_address(context)\n' % (op.context.py_member)
                )
                if op.context.ios:
                    f.write(
                        '        offsets = (ctypes.c_int64 * %d).in_dll(_lib, "py_offsets_%s")\n'
                        % (len(op.context.ios), op.c_name)
                    )
            if op.reset:
                f.write('        self.reset_fct = _lib.%s\n' % (op.reset.c_name))
                f.write('        self.reset_fct.restype = ctypes.c_void_p\n')
            assert op.cycle is not None  # nosec B101  # addresses linter
            f.write('        self.cycle_fct = _lib.%s\n' % (op.cycle.c_name))
            f.write('        self.cycle_fct.argtypes = [\n')
            for parameter in op.cycle.parameters:
                assert isinstance(parameter, (data.IO, data.Context))  # nosec B101  # addresses linter
                if isinstance(parameter, data.Context) and parameter.kind == data.CK.CONTEXT:
                    # opaque pointer
                    py_type = 'ctypes.c_void_p'
                else:
                    sizes = None if isinstance(parameter, data.Context) else parameter.sizes
                    assert parameter.type is not None  # nosec B101  # addresses linter
                    py_type = _get_python_type_name(parameter.type, False, sizes)
                if parameter.pointer:
                    py_type = 'ctypes.POINTER(%s)' % py_type
                f.write('            %s,\n' % py_type)
            f.write('        ]\n')
            return_type = op.cycle.return_.type if op.cycle.return_ else None
            if return_type:
                f.write(
                    '        self.cycle_fct.restype = %s\n'
                    % _get_python_type_name(return_type, False)
                )
            else:
                f.write('        self.cycle_fct.restype = ctypes.c_void_p\n')
            if cosim:
                f.write('        # set of accessed structured inputs: arrays/structures\n')
                f.write('        self.modified_inputs = {}\n')
            index = 0
            for io in op.ios:
                # if io.py_member != io.py_value:
                assert io.type is not None  # nosec B101  # addresses linter
                if not io.input and io.context:
                    # use the offset
                    py_type = _get_python_type_name(io.type, False, io.sizes)
                    f.write(
                        '        %s = %s.from_address(context + offsets[%d])\n'
                        % (io.py_member, py_type, index)
                    )
                    index += 1
                elif not io.context:
                    py_type = _get_python_type_name(io.type, False, io.sizes)
                    f.write('        %s = %s()\n' % (io.py_member, py_type))

            if op.context:
                f.write('\n')
                f.write('    def __del__(self):\n')
                # TODO: separate_io
                f.write('        free_fct = _lib.py_free_%s\n' % op.c_name)
                f.write('        free_fct.argtypes = [ctypes.c_void_p]\n')
                f.write('        free_fct.restype = None\n')
                f.write('        free_fct(ctypes.byref(%s))\n' % op.context.py_member)
            f.write('\n')
            f.write('    def call_reset(self) -> None:\n')
            if op.reset:
                # TODO: reuse function.parameters instead of hard-coding op.context
                arg = ('ctypes.byref(%s)' % op.context.py_member) if op.reset.parameters else ''
                f.write('        self.reset_fct(%s)\n' % arg)
            else:
                f.write('        # no reset function\n')
                f.write('        pass\n')
            f.write('\n')
            # when co-simulation if off, parameters refresh and debug are unused
            # but still declared to ensure client source code compatibility
            f.write(
                '    def call_cycle(self, cycles: int = 1, refresh: bool = True, '
                'debug: bool = False) -> None:\n'
            )
            if cosim:
                f.write('        if _proxy:\n')
                f.write('            # flush modified inputs\n')
                f.write('            for input, (pointer, cvt) in self.modified_inputs.items():\n')
                f.write('                _proxy.set_c_input(input, pointer, cvt)\n')
                f.write('            self.modified_inputs.clear()\n')
            args = [_.py_member for _ in op.cycle.parameters]
            if op.cycle.return_:
                # must be a function with a single scalar output
                result = op.cycle.return_.py_member + ' = '
            else:
                result = ''
            f.write('        for i in range(cycles):\n')
            f.write('            %sself.cycle_fct(\n' % result)
            for arg in args:
                f.write('                %s,\n' % arg)
            f.write('            )\n')
            if cosim:
                f.write(
                    '            if _proxy: _proxy.dbg_step(cycles) '
                    'if debug else _proxy.step(cycles, refresh)\n'
                )
            f.write('\n')

            # declare I/O accessors
            for io in op.ios:
                # r/w properties (r not mandatory for inputs, can be useful)
                write_accessors(io)
                if cosim:
                    c_interface_types.add(io.c_type)

        if cosim:
            f.write('\n')
            f.write('def _cvt(fct):\n')
            f.write('    fct.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.py_object]\n')
            f.write('    return fct\n')
            f.write('\n')

            for c_type in sorted(c_interface_types):
                # TODO: share code with _get_cvt_name
                f.write(
                    '_%s_cvt = _cvt(_lib.%s_to_string)\n'
                    % ((utils.lower_name(c_type) if _pep8 else c_type), c_type)
                )
            f.write('\n')

        if not cosim:
            f.write('# end of file\n')
        # else: file completed by main program
