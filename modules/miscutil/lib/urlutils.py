# -*- coding: utf-8 -*-
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
""" urlutils: tools for managing URL related problems:
- washing,
- redirection
"""

__lastupdated__ = """$Date$"""
__version__ = "$Id$"

try:
    from mod_python import apache
except ImportError:
    pass

def wash_url_argument(var, new_type):
    """
    Wash argument into 'new_type', that can be 'list', 'str', 'int', 'tuple' or 'dict'.
    If needed, the check 'type(var) is not None' should be done before calling this function
    @param var: variable value
    @param new_type: variable type, 'list', 'str', 'int', 'tuple' or 'dict'
    @return as much as possible, value var as type new_type
            If var is a list, will change first element into new_type.
            If int check unsuccessful, returns 0
    """
    out = []
    if new_type == 'list':  # return lst
        if type(var) is list:
            out = var
        else:
            out = [var]
    elif new_type == 'str':  # return str
        if type(var) is list:
            try:
                out = "%s" % var[0]
            except:
                out = ""
        elif type(var) is str:
            out = var
        else:
            out = "%s" % var
    elif new_type == 'int': # return int
        if type(var) is list:
            try:
                out = int(var[0])
            except:
                out = 0
        elif type(var) is int:
            out = var
        elif type(var) is str:
            try:
                out = int(var)
            except:
                out = 0
        else:
            out = 0
    elif new_type == 'tuple': # return tuple
        if type(var) is tuple:
            out = var
        else:
            out = (var,)
    elif new_type == 'dict': # return dictionary
        if type(var) is dict:
            out = var
        else:
            out = {0:var}
    return out

def redirect_to_url(req, url):
    """
    Redirect current page to url
    @param req: request as received from apache
    @param url: url to redirect to"""
    req.err_headers_out.add("Location", url)
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_PERMANENTLY
