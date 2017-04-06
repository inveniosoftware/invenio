# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2017 CERN.
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
Bibcheck plugin to move values of fields matching some pattern to a new field.

The new value is taken from the 'value' named group of 'pattern' (with the
'(?P<value>regexp)' construct), if it matches the value of source_field and put
into new_field. A subfield_filter can be specified to further restrict the
source field. 'additional_subfields' can optionally be set to a list of
constant subfield (code, value) pairs to add, and 'keep_subfields' can
be set to a list of subfield codes to port over to the new field or True to
keep all of them (including the one being matched).

If there is a match, the original field is deleted. By default, the new field
is only created if it does not result in a duplicate value. This behavior can
be disabled by setting allow_duplicates to True.

Example rules:

    [move_KEKSCAN]

    check = move_pattern_to_field
    check.source_field = "8564_u"
    check.new_field = "035__a"
    check.pattern = "^(https?://)?www-lib.kek.jp/cgi-bin/img_index\\?(?P<value>(\\d{2})?\\d{7})$"
    check.subfield_filter = ["y", "KEKSCAN"]
    check.additional_subfields = [["9", "KEKSCAN"]]
    check.allow_duplicates = false
    check.keep_subfields = []
    filter_collection = HEP
    filter_pattern = 8564_u:'kek.jp/cgi-bin' - 035__9:KEKSCAN

"""


import re


def check_record(record, source_field, new_field, pattern,
                 subfield_filter=(None, None), additional_subfields=[],
                 allow_duplicates=False, keep_subfields=[]):

    assert len(source_field) == 6
    assert len(new_field) == 6

    delcount = 0
    regex = re.compile(pattern)
    existing_values = set(val for _, val in record.iterfield(new_field))

    for pos, val in record.iterfield(source_field,
                                     subfield_filter=subfield_filter):
        if val:
            match = regex.match(val)

            if match:
                new_subfields = []
                new_value = match.group('value')

                if allow_duplicates or (
                        new_value != '' and new_value not in existing_values):
                    kept_subfields = (
                        (code, value) for code, value in record.get_subfields(
                            pos - delcount)
                        if keep_subfields == True or code in keep_subfields
                    )
                    existing_values.add(new_value)
                    new_subfields.extend(additional_subfields)
                    new_subfields.extend(kept_subfields)
                    new_subfields.append((new_field[5], new_value),)
                    record.add_field(new_field[:5], '', new_subfields)

                record.delete_field((pos[0][0:3], pos[1] - delcount, None))
                delcount += 1

                record.set_amended(
                    "%s field '%s' containing '%s'"
                    % ('Moved' if new_subfields else 'Removed',
                       source_field, new_value))

            else:
                record.warn('no match for [%s] against [%s]' % (pattern, val))

