# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
import time
import shutil
import tempfile

from invenio.config import \
     CFG_TMPDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile
from invenio.legacy.bibsched.bibtask import task_low_level_submission, bibtask_allocate_sequenceid

def Insert_Record(parameters, curdir, form, user_info=None):
    """
    Insert record in curdir/recmysql using BibUpload.  The file must
    therefore already have been created prior to this execution of
    this function, for eg. using "Make_Record".
    """
    global rn
    sequence_id = bibtask_allocate_sequenceid(curdir)
    if os.path.exists(os.path.join(curdir, "recmysql")):
        recfile = "recmysql"
    else:
        raise InvenioWebSubmitFunctionError("Could not find record file")
    initial_file = os.path.join(curdir, recfile)
    tmp_fd, final_file = tempfile.mkstemp(dir=CFG_TMPDIR,
                                          prefix="%s_%s" % \
                                          (rn.replace('/', '_'),
                                           time.strftime("%Y-%m-%d_%H:%M:%S")))
    os.close(tmp_fd)
    shutil.copy(initial_file, final_file)
    bibupload_id = task_low_level_submission('bibupload', 'websubmit.Insert_Record', '-r', '-i', final_file, '-P', '3', '-I', str(sequence_id))
    open(os.path.join(curdir, 'bibupload_id'), 'w').write(str(bibupload_id))
    return ""
