Python proxy
============

The structure of the Python proxy is identical for both SCADE Suite
and Scade One models.

The Python module defines:

* A class per structure used in the interfaces of the root operators.
  These classes derive from ``ctypes.Structure``.
* A global variable ``sensors`` with one read/write property per sensor in the
  model.
* A class per root operator which defines:

  * One read/write property per input
  * One read-only property per output
  * Two functions to address the C code:

    * ``call_reset(self) -> None``
    * ``call_cycle(self, cycles: int = 1, refresh: bool = True, debug: bool = False) -> None``

      The ``refresh`` and ``debug`` parameters are used for SCADE Suite co-simulation.

Example
-------

The python module's usage is straightforward:

* Create an instance of a root operator.
* Call its reset function.
* Loop:

  * Set the sensors
  * Set the inputs
  * Call the cyclic function
  * Get the outputs

The script hereafter is an example of client for the following model:

.. image:: /_static/interface.png

.. code::

   # py_box.py/py_box.dll are produced from PyBox.etp
   import py_box
   # set the sensors
   # P::offset: float64
   py_box.sensors.offset = 0.5
   # create an instance of the root operator P::Root
   root = py_box.Root()
   # and reset it
   root.call_reset()
   # set the inputs
   # P::Root/c: bool
   root.c = True
   # P::Root/v: Speed (defined as float64 ^ 3)
   root.v = (1.0, 2.0, 3.0)
   # P::Root/v: float64
   root.dt = 0.1
   for cycle in range(4):
       # P::Root/i: int32
       root.i = cycle + 1
       # call the cyclic function
       root.call_cycle()
       # print the results
       # P::Root/pos: Position
       print(root.o, root.pos.x, root.pos.y, root.pos.z)
       # P::Root/c: bool
       root.c = False

Access to values
----------------

* Scalar values: Use Python literals

  .. code::

     root.valid = True
     root.array[0] = 3.14
     root.points[2].x = 0

* Complex Values: Use ``ctypes`` literals

  Consider the following types:

  .. image:: /_static/types.png

  * OK

    .. code::

       root.array = (ctypes.double*3)([3, 1, 4])
       root.points[2] = CPosition_P(x=1, y=2, z=3)

  * NOK

    .. code::

       root.array = [3, 1, 4]
       root.points[2] = {"x": 1, "y": 2, "z": 3}

Possible enhancement: Support Python arrays and dictionaries for read/write access.

Limitations
-----------

The wrapper does not support for now the ``input_threshold`` and
``global_context`` KCG options.
