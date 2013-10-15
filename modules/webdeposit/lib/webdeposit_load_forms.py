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
from pprint import pformat
from wtforms import Form
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.pluginutils import PluginContainer


def plugin_builder(plugin_name, plugin_code):
    if plugin_name == '__init__':
        return
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        if issubclass(candidate, Form):
            return candidate

CFG_FORMS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio',
                                         'webdeposit_deposition_forms',
                                         '*_form.py'),
                            plugin_builder=plugin_builder)


forms = {}
for form in CFG_FORMS.itervalues():
    ## Change the names of the forms from the file names to the class names.
    if form is not None:
        forms[form.__name__] = form

## Let's report about broken plugins
import traceback
broken_plugins = CFG_FORMS.get_broken_plugins()
for k in broken_plugins.keys():
    broken_plugins[k] = list(broken_plugins[k])
    broken_plugins[k][2] = traceback.format_exc(broken_plugins[k][2])


open(os.path.join(CFG_LOGDIR, 'broken-deposition-forms.log'), 'w').write(
    pformat(broken_plugins))

__all__ = ['forms']
