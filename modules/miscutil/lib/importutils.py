# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio import helper functions."""

from __future__ import absolute_import

import imp
import importlib
import itertools
import glob
import os

_RACE_PROTECTION = False


def autodiscover_modules(packages, related_name_glob='*_tasks.py'):
    """
    Autodiscover function follows the pattern used by Celery itself.
    """
    global _RACE_PROTECTION

    if _RACE_PROTECTION:
        return
    _RACE_PROTECTION = True
    try:
        return list(
            itertools.chain.from_iterable(
                filter(
                    lambda x: x is not None,
                    [find_related_modules(pkg, related_name_glob)
                     for pkg in packages]
                )
            ))
    finally:
        _RACE_PROTECTION = False


def find_related_modules(package, related_name_glob):
    """Given a package name and a module name, tries to find that
    module."""
    try:
        pkg_path = importlib.import_module(package).__path__
    except AttributeError:
        return

    # Find all modules named according to related_name
    candidates = [os.path.basename(m)[:-3] for m in glob.glob(
                  os.path.join(pkg_path[0], related_name_glob)
                  )]

    modules = []
    for related_name in candidates:
        modules.append(import_related_module(package, pkg_path, related_name))

    if not modules:
        return
    return modules


def import_related_module(package, pkg_path, related_name):
    """
    Import module from given path
    """
    try:
        imp.find_module(related_name, pkg_path)
    except ImportError:
        return

    return importlib.import_module('{0}.{1}'.format(package, related_name))
