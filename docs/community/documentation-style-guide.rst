..
    This file is part of Invenio.
    Copyright (C) 2017-2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _documentation-style-guide:

=========================
Documentation Style Guide
=========================


About this guide
----------------
Starting to write documentation can seem like a daunting task, but remember
that not only other members of the community but you yourself will use this
valuable resource.

This guide is meant to help by providing you with quick pointers and
inform you as to what you should cover when writing documentation.

General style and tone
----------------------
It's best to address the reader in a clear, concise and conversational style.
Most of all, try to use a friendly tone. This makes the reading more engaging
and easier to follow. Also, avoid using jargon, idioms and abbreviations
as the reader may not be familiar with them.

Writing structure, language and grammar
---------------------------------------
When writing, you should try to be economical and clear in expression.
Below you can find some useful tips about how to achieve this:

- use diagrams to better illustrate concepts (see diagrams_)
- limit each paragraph to a single idea
    - if necessary, make use of multiple subsections, like `here <https://invenio-records-rest.readthedocs.io/en/latest/usage.html#access-control>`_
- convey the idea in the first sentence of the paragraph
- limit paragraphs to 6 sentences
- try to use short sentences, up to 25 words
- do not start all sentences with the same phrase
- use the active voice

======================================================================   ===============================================================
Do                                                                       Don't
======================================================================   ===============================================================
to use the files module, you require...                                  using the files modules requires...
======================================================================   ===============================================================

- use the present tense

======================================================================   ===============================================================
Do                                                                       Don't
======================================================================   ===============================================================
you need permissions to access...                                        you will need permissions to access...
======================================================================   ===============================================================

- choose short and clear declarative sentences
- use "you" to address the reader

=====================================   ===============================
Do                                      Don't
=====================================   ===============================
You can request a record...             A record can be requested
=====================================   ===============================

- use "we" when referring to the Invenio community

=====================================   ===============================
Do                                      Don't
=====================================   ===============================
We recommend using the module...        The recommended module is...
=====================================   ===============================

- choose the shorter form of a word, if applicable

=====================================   ===============================
Do                                      Don't
=====================================   ===============================
has                                     possesses
=====================================   ===============================

- start conditional phrases with the conditional part, so that the reader
  may skip the rest if it does not apply

=======================================  =====================================
Do                                       Don't
=======================================  =====================================
If you delete a record, you will not...  You will not...if you delete a record
=======================================  =====================================

- avoid using modifiers that do not add value, for example, starting a
  sentence with "There are/is"

=======================================  =====================================
Do                                       Don't
=======================================  =====================================
To start...                              There are several ways to start...
Click the button...                      Simply click the button...
To start, use...                         It's very easy to start, use...
Click the next...                        Please click the next...
=======================================  =====================================

- first mention the objective of an action and only afterwards its
  description, for example "To do X, click Y..."

=======================================  =====================================
Do                                       Don't
=======================================  =====================================
To do X, click Y                         Click Y, to do X
=======================================  =====================================

- do repeat nouns instead of using pronouns, in cases where there are more
  than one subjects, to avoid ambiguity:

======================================================================   ===============================================================
Do                                                                       Don't
======================================================================   ===============================================================
if you create a file in a specific bucket, make sure the file is named   if you create a file in a specific bucket, make sure it's named
======================================================================   ===============================================================

Technical writing style guidelines
----------------------------------
Keep in mind that the person reading your documentation may have no
knowledge of what the module does.
Always give a general, brief overview of any new term and explain its
function and purpose.
Remember to be consistent, do not use different words for the same
concept throughout the text.

Highlighting and formatting
---------------------------
Formatting guidelines:

- use camel case or snake case where appropriate and do not split
  object/function names into separate words
- use angle brackets for placeholders
- do not include the command line prompt ($) when writing commands
- separate commands from their output
- use the :code:`:code:` tag for commands, objects, field names, filenames,
  directories, paths, etc.
- use the :code:`:py:function:` tag along with the fully qualified name
  of the function when mentioning it, so that it will point to the API docs

============================================  ===============================
Do                                            Don't
============================================  ===============================
:code:`:py:func:`invenio.app.function_name``  :code:`:code:`function_name``
:code:`:py:class:`invenio.__init__``          invenio.__init
:code:`:py:data:`invenio.config.DATA``        ``:code:`invenio.config.DATA```
============================================  ===============================

- use normal style for string and integer field values

Code samples
------------
- keep a maximum column width of 80 for every code block in order not to
  have any horizontal scrolling
- Use ``doctest`` whenever possible to make sure that the documented code
  works; if not possible, use simple code blocks

.. _diagrams:

Diagrams
--------
For drawing diagrams, you can use draw.io. It provides you with the
option of exporting the diagram in XML format. You can replace the png file
from the ``docs/_static/`` subfolder and then update the XML source in
``docs/diagrams`` and push it to Git.
See an example of the `file structure <filestructure_>`_.

Deprecations, Notes, Warnings
-----------------------------
Code changes oftentimes and users need to be notified of upcoming deprecations,
new security issues, vulnerabilities or just informed about a particular
thing they may not be aware of.
It's important to make good use of deprecation notices, notes and warnings,
to improve the user's experience and save them time.

Deprecations
============
Use the :code:`deprecated` directive when planning to remove a piece of
functionality in future releases and inform the user as to what they should
use instead. Example::

    .. deprecated:: 3.1
       Use :func:`spam` instead.

.. deprecated:: 3.1
   Use ``:func:`spam``` instead.

Warnings
========
Communicate important information such as security issues using the :code:`warning`
directive. Provide all the information necessary in complete sentences. Example::

    .. warning::
       This script performs non-reversible operations...

.. warning::
   This script performs non-reversible operations...

Notes
=====
Make the user aware of something important that they may not know using the :code:`note`
directive. Example::

    .. note::
       This function is not suitable for...

.. note::
   This function is not suitable for...

.. _filestructure:

File Structure
--------------
.. code-block:: shell

    |-- ...
    |-- docs
    |   |-- _static
    |   |   |-- ...
    |   |-- diagrams
    |   |   |-- ...
    |   |-- ...
    |-- <module_name>
    |   |-- __init__.py
    |   |-- config.py
    |   |-- ...
    |-- AUTHORS.rst
    |-- CHANGES.rst
    |-- CONTRIBUTING.rst
    |-- INSTALL.rst
    |-- README.rst
    |-- OVERVIEW.rst
    `-- tests
        |-- ...

AUTHORS.rst
===========
What is it?
^^^^^^^^^^^
The AUTHORS file identifies the contributors of the project.


CHANGES.rst
===========
What is it?
^^^^^^^^^^^
The CHANGES file contains a list of the notable changes in reverse
chronological order for each version of the module.
This allows users to easily and quickly see what changes have been made for
each release.

Some useful tips for the changelog:

* make it human readable
* stick to one subsection for each version
* use the following tags to describe changes:

  * Adds, for any new features
  * Changes, for any changes in the current functionality or code base
  * Deprecates, for anything that will be removed in future releases
  * Removes, for anything that was removed in the current release
  * Fixes, for any bug fixes
  * Security, for any security-related changes

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses all types of users.


CONTRIBUTING.rst
================
What is it?
^^^^^^^^^^^
The contribution guidelines defined in this file serve to communicate how people
should contribute to the project.
It helps them open useful issues and make well-formed Pull Requests that
conform to the expectations of the project maintainers.
It lists the types of contributions one may make for the particular project
and how to do it.
It also includes a quick Get Started section that explains the basic
steps going from forking to submitting a Pull Request.
Finally, it lists the Pull Request guidelines (see `Invenio PR guidelines <https://invenio.readthedocs.io/en/latest/community/contribution-guide.html>`_).

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses new contributors and developers.

INSTALL.rst
===========
What is it?
^^^^^^^^^^^
The INSTALL file provides the user with installation instructions.
It should contain a brief description of the installation process
and one or more commands to install the module.
It also specifies any available install options.

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses all types of users.


README.rst
==========
What is it?
^^^^^^^^^^^^^^^^^^^^^
The README file should contain a very broad, big picture view of what
the module provides along with a bulleted list of its features.
It's recommended to avoid lengthy abstracts, try to keep it to 3 or 5 sentences.
Engage the reader by describing as soon as possible:

- what the module does
- how it can be used
- and why it should be used

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses all types of users.


OVERVIEW.rst
============
What is it?
^^^^^^^^^^^
The OVERVIEW file should contain a brief look at the key concepts and
terms of the module (have a look at `invenio-access <https://invenio-access.readthedocs.io/en/latest/overview.html>`_)
which should be introduced and explained in plain English.
Advanced technical information or code examples should be avoided,
as they will be covered in the Usage section.

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses all types of users.


Configuration
=============

Location: :code:`__init__.py`

What is it?
^^^^^^^^^^^
Most Invenio modules have configuration options and it is recommended to have
extensive docstrings in the configuration file with usage examples,
such that the configuration documentation generated is useful for both
newcomers as well as experienced developers.

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses new contributors, developers and system administrators who
just install Invenio.

Usage
=====

Location: :code:`config.py`

What is it?
^^^^^^^^^^^
It provides a detailed walk-through of the features of the module along with
code examples.
After providing a brief look at the module's features, create a small example
app with the minimal dependencies and walk the user through the setup,
then through each feature.
The reader will be able to quickly set up and use the module, while the
doctests will ensure that the examples are always up-to-date.

Who should I address?
^^^^^^^^^^^^^^^^^^^^^
This file addresses newcomers and developers.

Next steps
----------
If you need more information about reStructuredText/Sphinx syntax, have a look
at `this cheatsheet <https://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html>`_.
