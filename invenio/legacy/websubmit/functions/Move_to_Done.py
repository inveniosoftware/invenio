## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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

__revision__ = "$Id$"

   ## Description:   function Move_to_Done
   ##                This function move the current working directory to the
   ##             /done directory and compress it
   ## Author:         T.Baron
   ## PARAMETERS:    -

import os
import re
import time
import subprocess
import shutil

from invenio.config import \
     CFG_PATH_GZIP, \
     CFG_PATH_TAR, \
     CFG_WEBSUBMIT_STORAGEDIR
from invenio.websubmit_config import InvenioWebSubmitFunctionError

def Move_to_Done(parameters, curdir, form, user_info=None):
    """
    This function moves the existing submission directory to the
    /opt/invenio/var/data/submit/storage/done directory.
    Then it tars and gzips the directory.
    """
    global rn
    data = re.search(".*/([^/]*)/([^/]*)/[^/]*$", curdir)
    dir = data.group(1)
    doctype = data.group(2)
    donedir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, "done", dir, doctype)
    if not os.path.exists(donedir):
        try:
            os.makedirs(donedir)
        except:
            raise InvenioWebSubmitFunctionError("Cannot create done directory %s" % donedir)
    # Moves the files to the done diectory and creates an archive
    rn = rn.replace("/", "-").replace(" ","")
    namedir = "%s_%s" % (rn, time.strftime("%Y%m%d%H%M%S"))
    finaldir = os.path.join(donedir, namedir)
    os.rename(curdir, finaldir)
    if CFG_PATH_TAR != "" and CFG_PATH_GZIP != "":
        if subprocess.Popen([CFG_PATH_TAR, '-czf', '%s.tar.gz' % namedir, namedir], cwd=donedir).wait() == 0:
            shutil.rmtree(finaldir)
    return ""
