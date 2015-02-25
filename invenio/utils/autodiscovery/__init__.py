# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Invenio import helper functions.

Usage example:
  autodiscover_modules(['invenio'], '.+_tasks')

An import difference from pluginutils is that modules are imported in their
package hierarchy, contrary to pluginutils where modules are imported as
standalone Python modules.
"""

import imp
import re

from werkzeug import find_modules, import_string

from .checkers import create_enhanced_plugin_builder

_RACE_PROTECTION = False


def autodiscover_modules(packages, related_name_re='.+', ignore_exceptions=False):
    """
    Autodiscover function follows the pattern used by Celery.

    @param packages: List of package names to auto discover modules in.
    @type packages: list of str
    @param related_name_re: Regular expression used to match modules names.
    @type related_name_re: str
    @param ignore_exceptions: Ignore exception when importing modules.
    @type ignore_exceptions: bool
    """
    global _RACE_PROTECTION

    if _RACE_PROTECTION:
        return []
    _RACE_PROTECTION = True
    modules = []
    try:
        tmp = [find_related_modules(pkg, related_name_re, ignore_exceptions)
               for pkg in packages]

        for l in tmp:
            for m in l:
                if m is not None:
                    modules.append(m)
    # Workaround for finally-statement
    except:
        _RACE_PROTECTION = False
        raise
    _RACE_PROTECTION = False
    return modules


def find_related_modules(package, related_name_re='.+', ignore_exceptions=False):
    """Given a package name and a module name pattern, tries to find matching
    modules."""
    package_elements = package.rsplit(".", 1)
    try:
        if len(package_elements) == 2:
            pkg = __import__(package_elements[0], globals(), locals(), [package_elements[1]])
            pkg = getattr(pkg, package_elements[1])
        else:
            pkg = __import__(package_elements[0], globals(), locals(), [])
        pkg_path = pkg.__path__
    except AttributeError:
        return []

    # Find all modules named according to related_name
    p = re.compile(related_name_re)
    modules = []

    for name in find_modules(package, include_packages=True):
        if p.match(name.split('.')[-1]):
            try:
                modules.append(import_string(name, silent=ignore_exceptions))
            except Exception as e:
                if not ignore_exceptions:
                    raise e

    return modules


def import_related_module(package, pkg_path, related_name, ignore_exceptions=False):
    """
    Import module from given path
    """
    try:
        imp.find_module(related_name, pkg_path)
    except ImportError:
        return

    try:
        return getattr(
            __import__('%s' % (package), globals(), locals(), [related_name]),
            related_name
        )
    except Exception as e:
        if ignore_exceptions:
            #FIXME remove invenio dependency
            from invenio.ext.logging import register_exception
            register_exception()
        else:
            raise e
