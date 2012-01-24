# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
'''
bibauthorid_general_utils
    Bibauthorid utilities used by many parts of the framework
'''

import sys

def update_status(percent, comment = ""):
    percent = int(percent * 100)
    comment_len = 40
    if len(comment) < comment_len:
        comment += ' ' * (comment_len - len(comment))
    comment = comment[:comment_len]

    done = percent
    left = 100 - done
    sys.stdout.write("\r[%s%s] %d%% done     %s" %
                ("#" * done,
                 "." * left,
                 percent,
                 comment))


