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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Loads the available workflows for BibWorkflow
"""
import os
from pprint import pformat
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.pluginutils import PluginContainer


def plugin_builder(plugin_name, plugin_code):
    if plugin_name == '__init__':
        return

    plugin_candidate = getattr(plugin_code, plugin_name, None)
    if plugin_candidate is None:
        all_plugins = getattr(plugin_code, '__all__')
        for name in all_plugins:
            candidate = getattr(plugin_code, name)
            return candidate
    else:
        return plugin_candidate

loaded_workflows = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio',
                                   '*_workflows', '*.py'),
                                   plugin_builder=plugin_builder)

workflows = {}
for workflow in loaded_workflows.values():
    if workflow is not None:
        workflows[workflow.__name__] = workflow

# Let's report about broken plugins
open(os.path.join(CFG_LOGDIR, 'broken-workflows.log'), 'w').write(
    pformat(loaded_workflows.get_broken_plugins()))

__all__ = ['workflows']
