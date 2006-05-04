## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio BibEdit Administrator Interface."""

__lastupdated__ = """$Date$"""

from invenio.config import cdslang
from invenio.webpage import page
from invenio.webuser import getUid

__version__ = "$Id$"
    
def index(req, ln=cdslang):
    "BibEdit Admin interface."
    uid = getUid(req)
    return page(title="BibEdit Admin Interface",
                body="TODO",
                uid=uid,
                language=ln,
                navtrail = "FIXME",
                lastupdated=__lastupdated__,
                urlargs=req.args)
