# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from wtforms import TextField
from invenio.webdeposit_field import WebDepositField
from invenio.sherpa_romeo import SherpaRomeoSearch
from invenio.webdeposit_workflow_utils import JsonCookerMixinBuilder

__all__ = ['JournalField']


class JournalField(WebDepositField, TextField, JsonCookerMixinBuilder('journal')):

    def __init__(self, **kwargs):
        super(JournalField, self).__init__(**kwargs)
        self._icon_html = '<i class="icon-book"></i>'

    def pre_validate(self, form=None):
        value = self.data
        if value == "" or value.isspace():
            return dict(error=0, error_message='')

        s = SherpaRomeoSearch()
        s.search_journal(value, 'exact')
        if s.error:
            return dict(info=1, info_message=s.error_message)

        if s.get_num_hits() == 1:
            issn = s.parser.get_journals(attribute='issn')
            if issn != [] and issn is not None:
                issn = issn[0]
                publisher = s.parser.get_publishers(journal=value)
                if publisher is not None and publisher != []:
                    return dict(error=0, error_message='',
                               fields=dict(issn=issn, publisher=publisher['name']))
                return dict(error=0, error_message='',
                            info=1, info_message="Journal's Publisher not found",
                            fields=dict(publisher="", issn=issn))
            else:
                return dict(info=1, info_message="Couldn't find ISSN")
        return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data

        s = SherpaRomeoSearch()
        journals = s.search_journal(value)
        if journals is None:
            return []
        return journals
