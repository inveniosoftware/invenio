## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

import os
from six import iteritems
from invenio.legacy.bibdocfile.api import BibRecDocs, decompose_file, normalize_format

def Move_Files_Archive(parameters, curdir, form, user_info=None):
    """DEPRECATED: Use FFT instead."""
    MainDir = "%s/files/MainFiles" % curdir
    IncludeDir = "%s/files/AdditionalFiles" % curdir
    watcheddirs = {'Main' : MainDir, 'Additional' : IncludeDir}
    for type, dir in iteritems(watcheddirs):
        if os.path.exists(dir):
            formats = {}
            files = os.listdir(dir)
            files.sort()
            for file in files:
                dummy, filename, extension = decompose_file(file)
                if filename not in formats:
                    formats[filename] = []
                formats[filename].append(normalize_format(extension))
            # first delete all missing files
            bibarchive = BibRecDocs(sysno)
            existingBibdocs = bibarchive.list_bibdocs(type)
            for existingBibdoc in existingBibdocs:
                if bibarchive.get_docname(existingBibdoc.id) not in formats:
                    existingBibdoc.delete()
            # then create/update the new ones
            for key in formats.keys():
                # instanciate bibdoc object
                bibarchive.add_new_file('%s/%s%s' % (dir, key, formats[key]), doctype=type, never_fail=True)
    return ""
