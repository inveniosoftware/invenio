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

# start remote debugger if appropriate:
from invenio.config import CFG_DEVEL_SITE
if CFG_DEVEL_SITE:
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

# load register_exception() in a gentle way
try:
    from invenio.errorlib import register_exception
except Exception:
    def register_exception(*args, **kwargs):
        pass

# pre-load citation dictionaries upon WSGI application start-up (the
# citation dictionaries are loaded lazily, which is good for CLI
# processes such as bibsched, but for web user queries we want them to
# be available right after web server start-up):
try:
    from invenio.bibrank_citation_searcher import get_cited_by_weight
    get_cited_by_weight([])
except Exception:
    register_exception()

# pre-load docextract knowledge bases
try:
    from invenio.refextract_kbs import get_kbs
    get_kbs()
except Exception:
    register_exception()

# increase compile regexps cache size for further
# speed improvements in docextract
import re
re._MAXCACHE = 2000

# pre-load docextract author regexp
try:
    from invenio.authorextract_re import get_author_regexps
    get_author_regexps()
except Exception:
    register_exception()


try:
    from invenio.webinterface_handler_wsgi import application
finally:
    ## mod_wsgi uses one thread to import the .wsgi file
    ## and a second one to instantiate the application.
    ## Therefore we need to close redundant conenctions that
    ## are allocated on the 1st thread.
    from invenio.dbquery import close_connection
    close_connection()
