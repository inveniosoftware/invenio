# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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
from invenio.legacy.bibdocfile.api import BibRecDocs, decompose_file

def Add_Files(parameters, curdir, form, user_info=None):
    """DEPRECATED: Use FFT instead."""
    if os.path.exists("%s/files" % curdir):
        bibrecdocs = BibRecDocs(sysno)
        for current_file in os.listdir("%s/files" % curdir):
            fullpath = "%s/files/%s" % (curdir,current_file)
            dummy, filename, extension = decompose_file(current_file)
            if extension and extension[0] != ".":
                extension = '.' + extension
            if not bibrecdocs.check_file_exists(fullpath, extension):
                bibrecdocs.add_new_file(fullpath, "Main", never_fail=True)
    return ""
