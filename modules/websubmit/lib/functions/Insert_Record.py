## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import shutil

def Insert_Record(parameters,curdir,form):
    global rn
    if os.path.exists("%s/recmysql" % curdir):
        recfile = "recmysql"
    else:
        raise functionError("Could not find record file")
    initialfile = "%s/%s" % (curdir,recfile)
    finalfile = "%s/%s_%s" % (tmpdir,rn,time.strftime("%Y-%m-%d_%H:%M:%S"))
    shutil.copy(initialfile,finalfile)
    os.system("%s -r -i %s" % (bibupload,finalfile))
    return ""
