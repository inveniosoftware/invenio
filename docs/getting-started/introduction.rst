..  This file is part of Invenio
    Copyright (C) 2014 CERN.

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

.. _intro:

=======================
Introduction to Invenio
=======================

.. contents::
    :local:
    :depth: 1

What is a Registry?
===================

Registries are used as a mechanism to support pluggable architecture
using Python packages. A registry item is a Python package, class,
function or file that is registered with application.

Registries can be configured in several ways. Usually using a config
variable or `entry_points`_.

A Invenio instance can consist of multiple packages, giving way
to high adaptability and horizontal scaling.

.. _Flask-Registry: http://flask-registry.rtfd.org/
.. _entry_points: https://pythonhosted.org/setuptools/pkg_resources.html#entry-points

What do I need?
===============

.. sidebar:: Version Requirements
    :subtitle: Invenio version 2.0 runs on

    - Python ❨2.6, 2.7, *3.3 coming soon* ❩

    This is the last version to support Python 2.6,
    and from the next version Python 2.7 or newer is required.
    The last version to support Python 2.4 was Invenio series 1.2.

*Invenio* requires a relational database backend to store information.
MySQL or PostgreSQL (*coming soon*) are required for basic
functionality, but there's also support for a MongoDB of other
experimental NoSQL solutions, including using SQLite for local
development.

Get Started
===========

If this is the first time you're trying to use Invenio, or you are
new to Invenio 2.0 coming from previous versions then you should read our
getting started tutorials:

- :ref:`first-steps`

..
    - :ref:`next-steps`
