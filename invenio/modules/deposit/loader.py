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

import os
import warnings
from pprint import pformat
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.pluginutils import PluginContainer


def plugin_builder(plugin_name, plugin_code):
    if plugin_name == '__init__':
        return
    all = getattr(plugin_code, '__all__')
    for name in all:
        return getattr(plugin_code, name)


loaded_deposition_types = PluginContainer(
    os.path.join(
        CFG_PYLIBDIR,
        'invenio',
        'webdeposit_workflows',
        '*_metadata.py'
    ),
    plugin_builder=plugin_builder
)

"""
Create a dict with groups, names and deposition types
in order to render the deposition type chooser page

Used to load all the definitions of webdeposit workflow.
They must be defined in the deposition_types folder with
filname '*_metadata.py'. Also if you want to rename the workflow, you can
redefine the __all__ variable.


Example of definition:

__all__ = ['MyDeposition']

class MyDeposition(DepositionType):
    # Define the list of functions you want to run for this workflow
    workflow = [function1(), function2(), function3()]

    # Define the name to be rendered for the deposition
    dep_type = "My Deposition"

    # Define the name in plural
    plural = "My depositions"

    # Define in which deposition group it will belong
    group = "My Depositions Group"

    # Enable the deposition
    enabled = True
"""

deposition_types = {}
deposition_default = None


for deposition_type in loaded_deposition_types.values():
    if deposition_type and deposition_type.is_enabled():
        deposition_types[deposition_type.__name__] = deposition_type
        if deposition_type.is_default():
            if deposition_default is not None:
                warnings.warn(
                    "%s is overwriting already set default deposition %s." % (
                        deposition_type.__name__,
                        deposition_default.__name__
                    ),
                    RuntimeWarning
                )
            deposition_default = deposition_type

## Let's report about broken plugins
open(os.path.join(CFG_LOGDIR, 'broken-depositions.log'), 'w').write(
    pformat(loaded_deposition_types.get_broken_plugins()))

__all__ = ['deposition_types', 'deposition_default']
