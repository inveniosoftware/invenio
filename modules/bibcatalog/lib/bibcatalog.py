# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2013 CERN.
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
Provide a "ticket" interface with a request tracker.
See: https://twiki.cern.ch/twiki/bin/view/Inspire/SystemDesignBibCatalogue
This creates an instance of the class that has been configured for this installation,
or returns None if no ticket system is configured.
"""
from invenio.config import CFG_BIBCATALOG_SYSTEM

if CFG_BIBCATALOG_SYSTEM == 'RT':
    from invenio.bibcatalog_system_rt import BibCatalogSystemRT
    bibcatalog_system = BibCatalogSystemRT()
elif CFG_BIBCATALOG_SYSTEM == 'EMAIL':
    from invenio.bibcatalog_system_email import BibCatalogSystemEmail
    bibcatalog_system = BibCatalogSystemEmail()
else:
    from invenio.bibcatalog_system_dummy import BibCatalogSystemDummy


def get_bibcatalog_system():
    if CFG_BIBCATALOG_SYSTEM == 'RT':
        bc_system = BibCatalogSystemRT()
    else:
        bc_system = BibCatalogSystemDummy()

    return bc_system


class BibCatalogProxy(object):
    def __init__(self):
        self._bibcatalog_system = None

    def _init(self):
        self._bibcatalog_system = get_bibcatalog_system()

    def __getattr__(self, *args):
        if not self._bibcatalog_system:
            self._init()

        return getattr(self._bibcatalog_system, *args)

    def __repr__(self):
        if self._bibcatalog_system:
            return "BibCatalogProxy for %s" % repr(self._bibcatalog_system)
        else:
            return object.__repr__(self)


BIBCATALOG_SYSTEM = BibCatalogProxy()
