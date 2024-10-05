Usage with Scade One
====================

The tool, run through the Command Line Interface, launches ``swan-cg`` with a
configuration, builds the corresponding DLL, and generates the Python proxy
for the DLL.

Configuration
-------------

The syntax of the configuration file is provided in the
*JSON Schema Syntax of Code Generator Configuration File*
section of the user documentation.

However, it is easier to derive the configuration file from a template,
``config.json``, you obtain with a Code Generator job:

.. figure:: /_static/sone.png
   :width: 90%

   Scade One configuration

Create your configuration file from the template and edit it with
respect to your model. For example:

.. code:: json

   {
       "files": [
           "../PyBox/assets/P.swan",
           "../PyBox/assets/P.swani",
           "../stdlib/assets/stdlib.swan"
       ],
       "roots": [
           "P::Root"
       ],
       "target_dir": ".",
       "target": "C",
       "name_length": 200,
       "significance_length": 31
   }

Command Line Interface
----------------------

The tool has the following parameters:

.. code:: bash

   usage: swanpython.py [-h] [-v] -n <name> [-p <project>] [--size <swan_size>] [--false <swan_false>]
                        [--true <swan_true>]
                        cmdjson

   Scade One Python Proxy

   positional arguments:
     cmdjson               swan code gen settings file

   options:
     -h, --help            show this help message and exit
     -v, --version         display the version
     -n <name>, --name <name>
                           name of the output python module
     -p <project>, --project <project>
                           Swan project file (*.sproj)
     --size <swan_size>   type of swan_size
     --false <swan_false>  value of swan_false
     --true <swan_true>    value of swan_true

* You must set the ``S_ONE_HOME`` environment variable to the installation of Scade One
  to consider, for example:

  ``set S_ONE_HOME=C:\Program Files\ANSYS Inc\v242\Scade One``
* The Scade One project is only used to access the resources for imported code.
  For now, the wrapper supports only header files, for imported types and macros.

Once the package is installed in a Python 3.10 environment, that can be
virtual, the tool can be run using three different modes.

For example:

.. code:: bash

  > python .../lib/site_packages/ansys/scade/python_wrapper/swanpython.py -n my_module cmd.json
  > python -m ansys.scade.python_wrapper.swanpython -n my_module cmd.json
  > ansys_scade_python_wrapper_swanpython.exe -n my_module cmd.json

This produces ``my_module.dll`` and ``my_module.py``.
