# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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


def util_merge_fields_info_list(self, fields, keep_first=False,  # pylint: disable=W0102
                                default_first_value=None, default_value=[]):
    """
    Merge into one list all the fields listed.

    :param fields: Ordered list of fields to merge in the output
    :param keep_first: If set to ``True`` the position of the first field is
        kept even though if its value is ``None``.
    :param default_first_value: If ``keep_first`` is set to ``True`` this will
        be used as default value in case the first field is not in ``self``
    :param default_value: Default value to be used for all the fields, set to
        empty list as if the field is not present will not in the output.

    :return: ``List`` (might be empty or ``[None]``)
    """
    if keep_first:
        list_ = self.get(fields.pop(0), default_first_value)
        if not isinstance(list_, list):
            list_ = [list_]
    else:
        list_ = []

    for field in fields:
        value = self.get(field, default_value)
        if isinstance(value, list):
            list_.extend(value)
        else:
            list_.append(value)
    return list_
