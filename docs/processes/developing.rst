.. This file is part of Invenio
   Copyright (C) 2015, 2016 CERN.

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

============
 Developing
============

::

    Mutable defaults
    The Master
    Is full of regrets
       —-after Yosa Buson (1716-1784)

Developing principles
=====================

.. _contributing-documentation:

1. **Contributing documentation?** ReST and Sphinx. Contribute as code.

.. _contributing-i18n-translations:

2. **Contributing I18N translations?** GNU gettext. See :ref:`i18n`.

.. _contributing-code:

3. **Contributing code?**

   i. Read `The Zen of Python <https://en.wikipedia.org/wiki/Zen_of_Python>`_.

   ii. Read `Python Anti-Patterns
       <http://docs.quantifiedcode.com/python-anti-patterns/>`_.
   iii. Code with style. Plug `pycodestyle
        <https://pypi.python.org/pypi/pycodestyle>`_ (`PEP-8
        <https://www.python.org/dev/peps/pep-0008/>`_), `pydocstyle
        <https://pypi.python.org/pypi/pydocstyle>`_ (`PEP-257
        <https://www.python.org/dev/peps/pep-0257/>`_), `Flake8
        <https://pypi.python.org/pypi/flake8>`_, `ISort
        <https://pypi.python.org/pypi/isort>`_ tools into your editor.


   iv. Use sensible commit history. (See below.)

   v. Run kwalitee checks locally.

      - ``kwalitee check message master..my-feature-branch``
      - ``kwalitee check files master..my-feature-branch``
      - ``kwalitee check authors master..my-feature-branch``
      - ``kwalitee prepare release master..my-feature-branch``

   vi. Follow egoless programming principles. See :ref:`code-of-conduct`.

   vii. Read the following contributing guide and developer guidelines.

.. _contributing-guide:

Contributing guide
==================

.. include:: ../../CONTRIBUTING.rst
   :start-after: and welcome!
