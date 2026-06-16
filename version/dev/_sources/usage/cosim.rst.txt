White-Box Simulation with SCADE Suite
=====================================

Usage
-----

When the ``Enable co-simulation`` option is set, the wrapper produces
additional code to connect to the SCADE Simulator, based on the ``ssmproxy.py``
library file, which is copied to the target directory for convenience.
It relies on the C API for Co-Simulation:
Cf. the *Using Simulation API for Co-Simulation* section in the *SCADE Suite User Manual*
for details.

The ``call_cycle`` method presents two additional inputs:

* ``refresh: bool = True``: to refresh the SCADE Suite Simulation
  interface.
* ``debug: bool = False``: to pause the SCADE Simulator and wait for its
  Go button being pressed.

To use the co-simulation, you **must** build your model **twice**,
using the **same** root operator:

* Using the target ``Proxy for Python`` with the ``Enable co-simulation``
  option set.
* Using the configuration ``Simulation``.

.. Note::

   The Python class for the root operator has a parameter ``cosim: bool = True``.
   When the parameter is set to ``False``, the co-simulation is deactivated:
   You can alternate both modes without rebuilding the proxy.

Basic Customization
-------------------

The co-simulation requires several parameters that are initialized as follows
by default:

* ``scade_dir: str``: Path to the SCADE `bin` directory.

  Default: The directory of the tool used to produce the Python proxy,
  for example ``r"C:\Program Files\ANSYS Inc\v242\SCADE\SCADE\bin"``.
* ``host: str``: Hostname to connect and run the SCADE Simulator.

  Default: `"127.0.0.1"`
* ``project: str``: Path to the SCADE Suite project.

  Default: Path to the project used to build the Python proxy.
* ``configuration: str``: Name of the configuration used by the SCADE
  Simulator.

  Default: ``"Simulation"``
* ``root: str``: Path to the root operator.

  Default: Root operator of the configuration used to produce the Python proxy.
* ``port: int``: Port used for the communication.

  Default: Port number specified in the project's Simulation properties, ``64064`` by default.

Use the ``set_cosim_environment`` function, defined in the Python proxy,
to override any of these parameters before creating the instance of the
root operator.

Advanced Customization
----------------------

It is possible to create your own instance of SCADE Simulator proxy,
the ``SsmProxy`` class, including using a derived class.
This allows using all the capabilities of the *API for Co-Simulation* to tune
the co-simulation with respect to your environment.

The client script must create an instance of this class, and declare it using
the ``set_ssm_proxy`` function. This must be done before creating the instance
of the Python proxy for the root operator.
