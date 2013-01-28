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

#import os
#from wtforms import Form
#from invenio.config import CFG_PYLIBDIR
#from invenio.pluginutils import PluginContainer

"""def plugin_builder(plugin_name, plugin_code):
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        if issubclass(candidate, Form):
            return candidate

CFG_FORMS = PluginContainer(os.path.join(CFG_PYLIBDIR, \
                                         'invenio', \
                                         'webdeposit_forms', \
                                         '*.py'), \
                            plugin_builder=plugin_builder)
"""


"""
TODO: Create more doc types and load dynamically
"""

deposition_types = {"First Group": \
                 [{"name": "Article", "dep_type": "Article"}, \
                  {"name": "Thesis", "dep_type": "Thesis"}, \
                  {"name": "Nice Poem", "dep_type": "Poetry"}, \
                 ], \
             "Media": \
                 [{"name": "Photo", "dep_type": "Photo"}, \
                  {"name": "Audio", "dep_type": "Audio"}, \
                  {"name": "Video", "dep_type": "Video"}, \
                 ], \
             "Third Group": []}
