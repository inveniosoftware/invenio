# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012 CERN.
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

"""
mod_wsgi Invenio application loader.
"""

from invenio import config

# start remote debugger if appropriate:
if 'remote-debugger' in getattr(config, 'CFG_DEVEL_TOOLS', []):
    try:
        from invenio import remote_debugger
        remote_debugger.start_file_changes_monitor()
    except:
        pass

# wrap warnings (usually from sql queries) to log the traceback
# of their origin for debugging
try:
    from invenio.errorlib import wrap_warn
    wrap_warn()
except:
    pass

# pre-load citation dictionaries upon WSGI application start-up (the
# citation dictionaries are loaded lazily, which is good for CLI
# processes such as bibsched, but for web user queries we want them to
# be available right after web server start-up):
try:
    from invenio.bibrank_citation_searcher import get_citedby_hitset, \
         get_refersto_hitset
    get_citedby_hitset(None)
    get_refersto_hitset(None)
except:
    pass

## You can't write to stdout in mod_wsgi, but some of our
## dependecies do this! (e.g. 4Suite)
import sys
sys.stdout = sys.stderr

from invenio.webinterface_handler_flask import create_invenio_flask_app
application = create_invenio_flask_app()

if 'werkzeug-debugger' in getattr(config, 'CFG_DEVEL_TOOLS', []):
    from werkzeug.debug import DebuggedApplication
    application = DebuggedApplication(application, evalex=True)