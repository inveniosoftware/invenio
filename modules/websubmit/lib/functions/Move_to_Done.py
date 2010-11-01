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

__revision__ = "$Id$"

   ## Description:   function Move_to_Done
   ##                This function move the current working directory to the
   ##             /done directory and compress it
   ## Author:         T.Baron
   ## PARAMETERS:    -

import os
import re
import time

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
    data = re.search(".*/([^/]*)/([^/]*)/[^/]*$",curdir)
    dir = data.group(1)
    doctype = data.group(2)
    DONEDIR = "%s/done/%s/%s" % (CFG_WEBSUBMIT_STORAGEDIR,dir,doctype)
    if not os.path.exists(DONEDIR):
        try:
            os.makedirs(DONEDIR)
        except:
            raise InvenioWebSubmitFunctionError("Cannot create done directory %s" % DONEDIR)
    # Moves the files to the done diectory and creates an archive
    rn = rn.replace("/","-")
    namedir = "%s_%s" % (rn,time.strftime("%Y%m%d%H%M%S"))
    FINALDIR = "%s/%s" % (DONEDIR,namedir)
    os.rename(curdir,FINALDIR)
    if CFG_PATH_TAR != "" and CFG_PATH_GZIP != "":
        os.chdir(DONEDIR)
        tar_txt = "%s -cf - %s > %s.tar" % (CFG_PATH_TAR,namedir,namedir)
        os.system(tar_txt)
        zip_txt = "%s %s.tar" % (CFG_PATH_GZIP,namedir)
        os.system(zip_txt)
        rm_txt = "rm -R %s" % namedir
        os.system(rm_txt)
    return ""
