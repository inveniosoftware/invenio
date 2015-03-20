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

from jsonalchemy.jsonext.functions.util_merge_fields_info_list \
    import util_merge_fields_info_list


def sync_corparate_names(self, field_name, connected_field, action):  # pylint: disable=W0613
    """
    Sync meeting names content only when `__setitem__` or similar is used
    """
    if action == 'set':
        if field_name == 'meeting_names' and self.get('meeting_names'):
            self.__setitem__('_first_meeting_name',
                             self['meeting_names'][0],
                             exclude=['connect'])
            if self['meeting_names'][1:]:
                self.__setitem__('_additional_meeting_names',
                                 self['meeting_names'][1:],
                                 exclude=['connect'])
        elif field_name in ('_first_author', '_additional_authors'):
            self.__setitem__(
                'meeting_names',
                util_merge_fields_info_list(self, ['_first_meeting_name',
                                            '_additional_meeting_names']),
                exclude=['connect'])
