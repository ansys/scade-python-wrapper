.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the project.

.. vale off

.. towncrier release notes start

`2.3.0 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.3.0>`_ - March 18, 2026
=============================================================================================

.. tab-set::


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Maintenance missing or outdated check-vulnerabilities and check-actions-security ansys actions
          - `#54 <https://github.com/ansys/scade-python-wrapper/pull/54>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - chore(deps): bump the dependencies group with 2 updates
          - `#25 <https://github.com/ansys/scade-python-wrapper/pull/25>`_

        * - chore(deps): bump ansys-sphinx-theme[autoapi] from 1.2.6 to 1.3.2 in the dependencies group
          - `#26 <https://github.com/ansys/scade-python-wrapper/pull/26>`_

        * - chore(deps): bump the dependencies group with 3 updates
          - `#30 <https://github.com/ansys/scade-python-wrapper/pull/30>`_, `#36 <https://github.com/ansys/scade-python-wrapper/pull/36>`_

        * - chore(deps): bump pytest-cov from 6.0.0 to 6.1.1 in the dependencies group
          - `#33 <https://github.com/ansys/scade-python-wrapper/pull/33>`_


  .. tab-item:: Miscellaneous

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - Chore(deps): bump ansys/actions from 9 to 10 in the actions group
          - `#35 <https://github.com/ansys/scade-python-wrapper/pull/35>`_

        * - Fix: enhance robustness
          - `#37 <https://github.com/ansys/scade-python-wrapper/pull/37>`_

        * - Docs: update ``contributors.md`` with the latest contributors
          - `#39 <https://github.com/ansys/scade-python-wrapper/pull/39>`_

        * - Chore(deps): bump the actions group with 2 updates
          - `#42 <https://github.com/ansys/scade-python-wrapper/pull/42>`_

        * - Chore(deps): bump build from 1.2.2.post1 to 1.3.0 in the dependencies group
          - `#43 <https://github.com/ansys/scade-python-wrapper/pull/43>`_

        * - Chore(deps): bump the actions group across 1 directory with 5 updates
          - `#50 <https://github.com/ansys/scade-python-wrapper/pull/50>`_

        * - Chore: Update missing or outdated files
          - `#51 <https://github.com/ansys/scade-python-wrapper/pull/51>`_

        * - Chore: Update license headers
          - `#53 <https://github.com/ansys/scade-python-wrapper/pull/53>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - chore: update CHANGELOG for v2.2.0
          - `#22 <https://github.com/ansys/scade-python-wrapper/pull/22>`_

        * - chore: update CHANGELOG for v2.2.2
          - `#24 <https://github.com/ansys/scade-python-wrapper/pull/24>`_

        * - chore: update CHANGELOG for v2.2.3
          - `#29 <https://github.com/ansys/scade-python-wrapper/pull/29>`_

        * - Fix: Remove Scade One integration as it is now part of the product.
          - `#44 <https://github.com/ansys/scade-python-wrapper/pull/44>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - chore(deps): bump ansys/actions from 8 to 9 in the actions group
          - `#32 <https://github.com/ansys/scade-python-wrapper/pull/32>`_

        * - refactor: Use ansys-eseg-lbsjv 0.1.0 for generating `pydata.py`
          - `#34 <https://github.com/ansys/scade-python-wrapper/pull/34>`_

        * - Bump actions/download-artifact from 6.0.0 to 7.0.0 in the actions group
          - `#55 <https://github.com/ansys/scade-python-wrapper/pull/55>`_

        * - Bump the dependencies group across 1 directory with 6 updates
          - `#56 <https://github.com/ansys/scade-python-wrapper/pull/56>`_

        * - Bump Python and SCADE versions
          - `#58 <https://github.com/ansys/scade-python-wrapper/pull/58>`_


`2.2.3 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.2.3>`_ - March 20, 2025
=============================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - feat: Add register and unregister entry points for Extensions Manager
          - `#28 <https://github.com/ansys/scade-python-wrapper/pull/28>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - ci: Fix steps for creating a release
          - `#27 <https://github.com/ansys/scade-python-wrapper/pull/27>`_


`2.2.2 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.2.2>`_ - 2025-01-22
=========================================================================================

Fixed
^^^^^

- fix: documentation link `#23 <https://github.com/ansys/scade-python-wrapper/pull/23>`_

`2.2.0 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.2.0>`_ - 2025-01-22
===============================================================================================

Fixed
^^^^^

- fix: trusted publisher permissions `#21 <https://github.com/ansys/scade-python-wrapper/pull/21>`_


Documentation
^^^^^^^^^^^^^

- chore: update CHANGELOG for v2.1.0 `#20 <https://github.com/ansys/scade-python-wrapper/pull/20>`_


Test
^^^^

- test: Fix the tests that produce a DLL `#13 <https://github.com/ansys/scade-python-wrapper/pull/13>`_

`2.1.0 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.1.0>`_ - 2025-01-20
=========================================================================================

Added
^^^^^

- feat: Accept Python literals for inputs `#19 <https://github.com/ansys/scade-python-wrapper/pull/19>`_


Fixed
^^^^^

- fix: technical review `#12 <https://github.com/ansys/scade-python-wrapper/pull/12>`_
- fix: Avoid name conflict with legacy WrapUtilsEx 1.x `#18 <https://github.com/ansys/scade-python-wrapper/pull/18>`_


Dependencies
^^^^^^^^^^^^

- chore(deps): bump the dependencies group with 4 updates `#9 <https://github.com/ansys/scade-python-wrapper/pull/9>`_
- chore(deps): bump the dependencies group across 1 directory with 4 updates `#16 <https://github.com/ansys/scade-python-wrapper/pull/16>`_


Documentation
^^^^^^^^^^^^^

- chore: update CHANGELOG for v2.0.0 `#6 <https://github.com/ansys/scade-python-wrapper/pull/6>`_
- chore: update CHANGELOG for v2.0.1 `#8 <https://github.com/ansys/scade-python-wrapper/pull/8>`_
- docs: Add minimal doc-strings. `#10 <https://github.com/ansys/scade-python-wrapper/pull/10>`_
- docs: review of user documentation `#11 <https://github.com/ansys/scade-python-wrapper/pull/11>`_


Maintenance
^^^^^^^^^^^

- chore(deps): bump codecov/codecov-action from 4 to 5 in the actions group `#15 <https://github.com/ansys/scade-python-wrapper/pull/15>`_


Test
^^^^

- chore: Update license headers `#17 <https://github.com/ansys/scade-python-wrapper/pull/17>`_

`2.0.1 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.0.1>`_ - 2024-10-10
=========================================================================================

Fixed
^^^^^

- fix: Fix the path of the registered scripts `#7 <https://github.com/ansys/scade-python-wrapper/pull/7>`_

`2.0.0 <https://github.com/ansys/scade-python-wrapper/releases/tag/v2.0.0>`_ - 2024-10-10
=========================================================================================

Added
^^^^^

- feat: Migrate the original repository to GitHub `#1 <https://github.com/ansys/scade-python-wrapper/pull/1>`_


Fixed
^^^^^

- fix: Minor issues `#5 <https://github.com/ansys/scade-python-wrapper/pull/5>`_


Dependencies
^^^^^^^^^^^^

- Bump the dependencies group with 4 updates `#3 <https://github.com/ansys/scade-python-wrapper/pull/3>`_


Maintenance
^^^^^^^^^^^

- Bump the actions group with 2 updates `#2 <https://github.com/ansys/scade-python-wrapper/pull/2>`_
- ci: Activate the unit tests `#4 <https://github.com/ansys/scade-python-wrapper/pull/4>`_

.. vale on
