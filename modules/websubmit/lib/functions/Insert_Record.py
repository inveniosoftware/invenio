## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

__revision__ = "$Id$"

import os
import time
import shutil

from invenio.config import \
     CFG_BINDIR, \
     CFG_TMPDIR
from invenio.websubmit_config import InvenioWebSubmitFunctionError

def Insert_Record(parameters, curdir, form, user_info=None):
    global rn
    if os.path.exists("%s/recmysql" % curdir):
        recfile = "recmysql"
    else:
        raise InvenioWebSubmitFunctionError("Could not find record file")
    initialfile = "%s/%s" % (curdir,recfile)
    finalfile = "%s/%s_%s" % (CFG_TMPDIR,rn,time.strftime("%Y-%m-%d_%H:%M:%S"))
    shutil.copy(initialfile,finalfile)
    os.system("%s/bibupload -r -i %s" % (CFG_BINDIR,finalfile))
    return ""
