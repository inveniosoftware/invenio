..  This file is part of Invenio
    Copyright (C) 2014, 2015 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

Python
======

Coding standards
----------------

We follow `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ and `PEP-257
<https://www.python.org/dev/peps/pep-0257/>`_ and sort imports via ``isort``.
Please plug corresponding checkers such as ``flake8`` to your code editor.

Coding principles
-----------------

We adopt the following principles:

- *Convention over Configuration* means that common building blocks
  are provided for you, so use them! If you are not sure or documentation
  of certain feature is missing, contact the developers.

- *Don't Repeat Yourself (DRY)* to help us keep our software maintainable.
  Duplication of code fragments makes application codebase larger and more
  importantly it can become a source of many errors during future development
  (refactoring).

- *Agile Development* where each iteration should lead to working code in
  relatively short time while incremental steps are small and easy to understand
  by other developers. When you are done with editing do not forget to run the
  tests to make sure that all other modules are working fine.

Anti-patterns
-------------

Learn to recognise and avoid Python `anti-patterns
<http://docs.quantifiedcode.com/python-anti-patterns/index.html>`_.

Entry points
------------

We use Python `entry_points`_ as a way to provide extensions for packages.

.. _entry_points: https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points

