Getting started
===============
To use Ansys SCADE Python Wrapper, you must have a valid license for Ansys SCADE.

For information on getting a licensed copy, see the
`Ansys SCADE Suite <https://www.ansys.com/products/embedded-software/ansys-scade-suite>`_
page on the Ansys website.

Requirements
------------
The ``ansys-scade-python-wrapper`` package supports only the versions of Python delivered with
Ansys SCADE, starting from 2021 R2:

* 2021 R2 through 2023 R1: Python 3.7
* 2023 R2 and later: Python 3.10

Install in user mode
--------------------
The following steps are for installing Ansys SCADE Python Wrapper in user mode.
If you want to contribute to Ansys SCADE Python Wrapper,
see :ref:`contribute_scade_python-wrapper` for the steps for installing in developer mode.

#. Before installing Ansys SCADE Python Wrapper in user mode, run this command to ensure that
   you have the latest version of `pip`_:

   .. code:: bash

      python -m pip install -U pip

#. Install Ansys SCADE Python Wrapper with this command:

   .. code:: bash

       python -m pip install --user ansys-scade-python-wrapper

#. For Ansys SCADE releases 2024 R2 and below, complete the installation with
   these commands:

   .. code:: bash

      python -m ansys.scade.wux.register
      python -m ansys.scade.python_wrapper.register

   .. Note::

      This additional step is not required when installing the package with
      Ansys SCADE Extension Manager.

.. LINKS AND REFERENCES
.. _pip: https://pypi.org/project/pip/
