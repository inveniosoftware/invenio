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

   ## Description:   function Move_From_Pending
   ##                This function retrieves an old submisison directory which
   ##             had been saved in /pending and moves all the data files
   ##             in the current working directory
   ## Author:         T.Baron
   ## PARAMETERS:    -

import os

from invenio.config import CFG_WEBSUBMIT_STORAGEDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError

def Move_From_Pending(parameters, curdir, form, user_info=None):
    """
    This function retrieves the data of a submission which was
    temporarily stored in the 'pending' directory (waiting for an
    approval for example), and moves it to the current action
    directory.
    """
    global rn
    doctype = form['doctype']
    srcdir = "%s/pending/%s/%s" % (CFG_WEBSUBMIT_STORAGEDIR,doctype,rn)
    if os.path.exists(srcdir):
        if rn != "":
            files = os.listdir(srcdir)
            for file in files:
                os.rename("%s/%s" % (srcdir,file), "%s/%s" % (curdir,file))
            os.rmdir(srcdir)
    else:
        raise InvenioWebSubmitFunctionError("Move_From_Pending: Cannot retrieve reference information %s" % srcdir)
    return ""

