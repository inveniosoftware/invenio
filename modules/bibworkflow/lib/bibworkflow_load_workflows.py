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


workflows = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio',
                                         '*_workflows', '*.py'))

# Let's report about broken plugins
open(os.path.join(CFG_LOGDIR, 'broken-workflows.log'), 'w').write(
    pformat(workflows.get_broken_plugins()))

__all__ = ['workflows']
