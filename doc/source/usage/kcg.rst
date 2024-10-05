Usage with SCADE Suite
======================

Settings
--------
Select the target ``Proxy for Python`` in the ``Code Integration`` tab.

.. figure:: /_static/integration.png

   Code Integration

The settings page ``Python`` is visible when the target is selected:

.. figure:: /_static/python.png

   Code Integration Python

* Module name (default $(project_name)): Name of the Python proxy.
  Provide either a name or use one of the following macros:

  .. vale off

  * ``$(project_name)``: aaa_BbbCcc --> aaa_bbb_ccc
  * ``$(ProjectName)``: aaa_BbbCcc --> AaaBbbCcc
  * ``$(PROJECT_NAME)``: aaa_BbbCcc --> AAA_BBB_CCC
  * ``$(projectname)``: aaa_BbbCcc --> aaa_BbbCcc (**unchanged**)

  .. vale on

* ``Enable co-simulation`` (default false): When selected, the Python proxy
  contains additional instructions to open a SCADE Simulator session and
  automatically redirects the changes to the inputs and the calls to the
  cyclic function.
* ``kcg_size`` (default int64): Corresponding C type for ``kcg_size``,
  which is defined as `int` by default in ``kcg_types.h``.
* ``kcg_false`` (default 0): Value of ``kcg_false``.
* ``kcg_true`` (default 1): Value of ``kcg_true``.

Code Generation/Build
---------------------

Build the application using the Code Generator target ``Proxy for Python``,
as described in the former section.
This produces a DLL and its Python interface.
The implementation of the generated module relies on the ``ctypes`` module.
This is important to know its usage to access I/Os of complex types,
for example structures and arrays.
