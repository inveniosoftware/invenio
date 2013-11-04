# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

try:
    from invenio.webinterface_handler_wsgi import application
finally:
    ## mod_wsgi uses one thread to import the .wsgi file
    ## and a second one to instantiate the application.
    ## Therefore we need to close redundant conenctions that
    ## are allocated on the 1st thread.
    from invenio.dbquery import close_connection
    close_connection()
