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

   ## Description:   function Move_to_Pending
   ##                This function moves the current working directory to 
   ##             /pending (usually the document is then waiting for
   ##              approval)
   ## Author:         T.Baron
   ## PARAMETERS:    -

def Move_to_Pending(parameters,curdir,form):
    global rn
    doctype = form['doctype']
    PENDIR = "%s/pending/%s" % (storage,doctype)
    if not os.path.exists(PENDIR):
        try:
            os.makedirs(PENDIR)
        except:
            raise functionError("Cannot create pending directory %s" % PENDIR)
    # Moves the files to the pending directory
    rn = rn.replace("/","-")
    namedir = rn
    FINALDIR = "%s/%s" % (PENDIR,namedir)
    os.rename(curdir,FINALDIR)
    return ""
