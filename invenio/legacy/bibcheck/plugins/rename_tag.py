# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

""" Bibcheck plugin to move (rename) fields"""

def check_record(record, old_tag, new_tag):
    """ Changes the tag of fields with tag old_tag to new_tag"""
    if new_tag in record:
        record.warn("Record already has tag %s, not overwriting", new_tag)
    elif old_tag in record:
        record[new_tag] = record.pop(old_tag)
        record.set_amended("Renamed tag %s to %s" % (old_tag, new_tag))

