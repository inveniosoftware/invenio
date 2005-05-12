# -*- coding: utf-8 -*-
#! /usr/bin/env python
##
## $Id$
##
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

"""
Compile magic files listed on the command line. Print name of compiled file.
"""

import sys
import os
import magic.magic as magic

magician = magic.open(magic.MAGIC_NONE)

for filename in sys.argv[1:]:
    if os.path.isdir(filename):
        print filename, "is Directory!"
        continue
    if magician.compile(filename) == 0:
        print filename, "compiled OK."
    else:
        print filename, "failed to compile."

