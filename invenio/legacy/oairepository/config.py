# This file is part of Invenio.
# Copyright (C) 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAI Repository Configuration."""

from __future__ import unicode_literals

# Maximum number of records to put in a single bibupload
CFG_OAI_REPOSITORY_MARCXML_SIZE = 1000

# A magic value used to specify the global set (e.g. when the admin
# specify a set configuration without putting any setSpec)
# NOTE: if you change this value, please update accordingly the root
# Makefile.am and tabcreate.sql defaults for setSpec column in
# oaiREPOSITORY MySQL table.
CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC = "GLOBAL_SET"
