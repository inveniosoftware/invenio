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

   ## Description:   function Print_Success_MBI
   ##                This function displays a message telling the user the
   ##             modification has been taken into account
   ## Author:         T.Baron
   ## PARAMETERS:    -

def Print_Success_MBI(parameters,curdir,form):
    global rn
    t="<B>Modification completed!</B><br><BR>"
    t+="These modifications on document %s will be processed as quickly as possible and made <br>available on the %s Server</b>" % (rn,cdsname)
    return t

