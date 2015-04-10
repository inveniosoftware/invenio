# -*- coding: utf-8 -*-
# This file is part of CDS Invenio.
# Copyright (C) 2013, 2015 CERN.
#
# CDS Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# CDS Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Webtag module configuration."""

from __future__ import unicode_literals

# pylint: disable-msg=W0105

"""InnoDB doesn't support unique constraints of more than 767 bytes total
(user + record + tag). Since the tag can contain 3-byte Unicode characters,
it's limited to allow Unicode strings of the max length:
C{select floor((767 - sum(
       case data_type
           when 'tinyint' then 1
           when 'smallint' then 2
           when 'mediumint' then 3
           when 'int' then 4
           when 'bigint' then 5
       end)) / 3)
  from information_schema.columns
 where table_name = 'tagTAG' and
       column_name in ('id_bibrec', 'id_user')
;}
Using utf8_bin collation to treat tags as case and umlaut sensitive. I.e., treat
'uber', 'über', 'Über' and 'UBER' as four different tags."""

#
# Tag Names
#
CFG_TAGS_NAME_MAX_LENGTH = 253

# MySQL (as of version 5.4) only supports the Basic Multilingual Plane (BMP)
# of Unicode Version 3.0, i.e., up to code point U+FFFF.
CFG_TAGS_MAX_CHARACTER = 65535

#
# Replacements:
#
# List of pairs (regular expression, replacement) that
# will be applied to tag name
# Order: SILENT, then BLOCKING

# Applied first. If these are the only changes to the name, tag is saved
# with changed name
CFG_TAGS_NAME_REPLACEMENTS_SILENT = [
    (r'\s+', ' '),       # merge multiple spaces
    (r'^\s+|\s+$', '')   # remove leading / trailing spaces
]

# Applied after SILENT. If anything is matched here, name is considered invalid
CFG_TAGS_NAME_REPLACEMENTS_BLOCKING = [
    (r'[^\w\s]', ' '),   # remove non-alphanumeric (but not whitespaces)
    (r'\s+', ' '),       # merge multiple spaces
    (r'^\s+|\s+$', '')   # remove leading / trailing spaces
]

#
# User settings
#

CFG_WEBTAG_DEFAULT_USER_SETTINGS = {
    'display_tags': True,
    'display_tags_group': True,
    'display_tags_public': True,
}
