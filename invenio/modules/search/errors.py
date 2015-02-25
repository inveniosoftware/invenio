# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012,
# 2013, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


class InvenioWebSearchUnknownCollectionError(Exception):
    """Exception for bad collection."""

    def __init__(self, colname):
        """Initialisation."""
        self.colname = colname

    def __str__(self):
        """String representation."""
        return repr(self.colname)


class InvenioWebSearchWildcardLimitError(Exception):
    """Exception raised when query limit reached."""

    def __init__(self, res):
        """Initialization."""
        self.res = res

class InvenioWebSearchReferstoLimitError(Exception):
    """Raise when CFG_WEBSEARCH_MAX_RECORDS_REFERSTO limit is reached."""

    def __init__(self, res):
        """Initialization."""
        self.res = res

class InvenioWebSearchCitedbyLimitError(Exception):
    """Raise when CFG_WEBSEARCH_MAX_RECORDS_CITEDBY limit is reached."""

    def __init__(self, res):
        """Initialization."""
        self.res = res
