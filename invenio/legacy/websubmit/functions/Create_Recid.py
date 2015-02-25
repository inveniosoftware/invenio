# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import os

from invenio.legacy.dbquery import run_sql

def Create_Recid(parameters, curdir, form, user_info=None):
    """
    Reserves a record ID and store under 'curdir/SN'
    """
    global sysno
    if not os.path.exists("%s/SN" % curdir):
        recid = run_sql("insert into bibrec (creation_date,modification_date) values(NOW(),NOW())")
        fp = open("%s/SN" % curdir,"w")
        fp.write(str(recid))
        sysno = recid
    else:
        fp = open("%s/SN" % curdir,"r")
        sysno = fp.read()
        fp.close()
    return ""

