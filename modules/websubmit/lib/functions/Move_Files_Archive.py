## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from cdsware.file import *

def Move_Files_Archive(parameters,curdir,form):  
    MainDir = "%s/files/MainFiles" % curdir
    IncludeDir = "%s/files/AdditionalFiles" %curdir
    watcheddirs = {'Main':MainDir, 'Additional':IncludeDir}
    for type in watcheddirs.keys():
        dir = watcheddirs[type]
        if os.path.exists(dir):
            formats = {}
            files = os.listdir(dir):
            files.sort()
            for file in files:
                extension = re.sub("^[^\.]*\.","",file)
                if extension == file:
                    extension = ""
                filename = re.sub("\..*","",file)
                if not formats.has_key(filename):
                    formats[filename] = []
                formats[filename].append(extension)
            # first delete all missing files
            bibarchive = BibRecDocs(sysno)
            existingBibdocs = bibarchive.listBibDocs(type)
            if existingBibdocs != None:
                for existingBibdoc in existingBibdocs:
                    if not formats.has_key(existingBibdoc.getFileName()):
                        existingBibdoc.delete()
            # then create/update the new ones
            for key in formats.keys():
                # instanciate bibdoc object
                bibarchive.addFile(path=dir, type=type,filename=key,formats=formats[key])
    return ""
