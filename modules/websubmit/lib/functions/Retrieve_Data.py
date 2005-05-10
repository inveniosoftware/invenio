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

   ## Description:   function Get_Field
   ##                This function returns the value of the specified field
   ##             from the specified document
   ## Author:         T.Baron
   ##
   ## PARAMETERS:    fieldname: marc21 code
   ##                bibrec: system number of the bibliographic record

from cdsware.search_engine import search_pattern, perform_request_search, print_record

def Get_Field(fieldname,bibrec):
    value = string.strip(print_record(int(bibrec),'tm',fieldname))
    return value

