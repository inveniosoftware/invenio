## $Id$
## CDSware Web Session utilities.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

## read config variables:
#include "config.wml"
#include "configbis.wml"

## fill config variables:
pylibdir = "<LIBDIR>/python"

try:
    import sys
    import os
    import crypt
    import string
    sys.path.append('%s' % pylibdir)
    from cdsware.config import cfg_apache_password_file, cfg_apache_group_file
    from cdsware.search_engine import coll_restricted_p, coll_restricted_group

except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)

<protect>

def auth_apache_user_p(user, password):
    """Check whether user-supplied credentials correspond to valid
    Apache password data file.  Return 0 in case of failure, 1 in case
    of success."""    
    try:
        apache_password_line_for_user = os.popen("grep %s %s" % (user,cfg_apache_password_file), 'r').read()
        password_apache = string.split(string.strip(apache_password_line_for_user),":")[1]
    except: # no pw found, so return not-allowed status
        return 0
    salt = password_apache[:2]
    if crypt.crypt(password, salt) == password_apache:
        return 1
    else:
        return 0

def auth_apache_user_in_groups(user):
    """Return list of Apache groups to which Apache user belong."""
    out = []
    try:        
        pipe_input,pipe_output = os.popen2(["/bin/grep", user, cfg_apache_group_file], 'r')
        for line in pipe_output.readlines():
            out.append(string.split(string.strip(line),":")[0])
    except: # no groups found, so return empty list
        pass
    return out

def auth_apache_user_collection_p(user, password, coll):
    """Check whether user-supplied credentials correspond to valid
    Apache password data file, and whether this user is authorized to
    see the given collections.  Return 0 in case of failure, 1 in case
    of success."""    
    if not auth_apache_user_p(user, password):
        return 0
    if not coll_restricted_p(coll):
        return 1
    if coll_restricted_group(coll) in auth_apache_user_in_groups(user):
        return 1
    else:
        return 0

# test cases:
#print auth_apache_user_p("jane","")
#print auth_apache_user_in_groups("jane")
</protect>
