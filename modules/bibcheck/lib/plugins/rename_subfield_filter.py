# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2016 CERN.
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

"""
Bibcheck plugin to move (rename) a subfield if
pattern matches and complement == False or
pattern does not match and complement = True,
depending on subfield_filter

Example:
[mvtexkey_withSpace]
check = rename_subfield_filter
filter_collection = HEP
check.source_field = "035__a"
check.new_code = "z"
check.pattern = " "
check.complement = false
check.subfield_filter = ["9", "SPIRESTeX"]

[mvtexkey_wrongSyntax]
check = rename_subfield_filter
filter_collection = HEP
check.source_field = "035__a"
check.new_code = "z"
check.pattern = "^[A-Za-z]+:\\d{4}[a-z]{2,3}$"
check.complement = true
check.subfield_filter = ["9", "INSPIRETeX"]
"""


def check_record(record, source_field, new_code,
                 pattern, subfield_filter, complement=False):
    """ Changes the code of a subfield to new_code """
    import re
    from invenio.bibrecord import record_modify_subfield
    assert len(source_field) == 6
    source_field = source_field.replace("_", " ")
    assert len(subfield_filter) == 2
    subfield_filter = tuple(subfield_filter)
    for pos, val in record.iterfield(source_field, subfield_filter):
        pattern_matches = re.search(pattern, val)
        if (pattern_matches and not complement) or \
           (complement and not pattern_matches):
            record_modify_subfield(record, source_field[:3], new_code, val,
                                   pos[2], field_position_local=pos[1])
            record.set_amended('move from %s to %s: %s' %
                               (source_field.replace(" ", "_"), new_code, val))
