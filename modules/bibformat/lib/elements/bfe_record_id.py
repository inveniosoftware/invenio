# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints the record ID.
"""

__revision__ = "$Id$"

from invenio.config import CFG_WEBSEARCH_USE_ALEPH_SYSNOS, \
                           CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG

def format_element(bfo):
    """
    Prints the record id.
    """
    if CFG_WEBSEARCH_USE_ALEPH_SYSNOS:
        return bfo.field(CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG)
    else:
        return bfo.control_field('001')
