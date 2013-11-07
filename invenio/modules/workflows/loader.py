# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.base.utils import (autodiscover_workflows,
                                autodiscover_widgets)
from invenio.utils.datastructures import LazyDict
from werkzeug.utils import import_string, find_modules

"""
Loader for workflows and widgets
"""


def plugin_builder(plugin):
    plugin_name = plugin.__name__.split('.')[-1]
    if plugin_name == '__init__':
        return

    plugin_candidate = getattr(plugin, plugin_name, None)
    if plugin_candidate is None:
        all_plugins = getattr(plugin, '__all__', [])
        for name in all_plugins:
            candidate = getattr(plugin, name)
            return candidate
    else:
        return plugin_candidate


def load_workflows():
    workflows = {}
    for package in autodiscover_workflows():
        for module in find_modules(package.__name__, include_packages=True):
            workflow = plugin_builder(import_string(module))
            if workflow is not None:
                workflows[workflow.__name__] = workflow

    return workflows


def load_widgets():
    widgets = {}
    for package in autodiscover_widgets():
        for module in find_modules(package.__name__, include_packages=True):
            widget = plugin_builder(import_string(module))
            if widget is not None:
                widgets[widget.__name__] = widget

    return widgets

workflows = LazyDict(load_workflows)
widgets = LazyDict(load_widgets)

__all__ = ['widgets', 'workflows']
