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

   ## Description:   function Move_to_Pending
   ##                This function moves the current working directory to
   ##             /pending (usually the document is then waiting for
   ##              approval)
   ## Author:         T.Baron
   ## PARAMETERS:    -

import os

from invenio.config import CFG_WEBSUBMIT_STORAGEDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError

def Move_to_Pending(parameters, curdir, form, user_info=None):
    """
    This function moves the existing submission directory to the
    /opt/invenio/var/data/submit/storage/pending directory. It is
    used to store temporarily this data until it is approved or...
    """
    global rn
    doctype = form['doctype']
    PENDIR = "%s/pending/%s" % (CFG_WEBSUBMIT_STORAGEDIR,doctype)
    if not os.path.exists(PENDIR):
        try:
            os.makedirs(PENDIR)
        except:
            raise InvenioWebSubmitFunctionError("Cannot create pending directory %s" % PENDIR)
    # Moves the files to the pending directory
    rn = rn.replace("/","-")
    namedir = rn
    FINALDIR = "%s/%s" % (PENDIR,namedir)
    os.rename(curdir,FINALDIR)
    return ""
