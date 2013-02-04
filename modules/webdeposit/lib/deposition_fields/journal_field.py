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
from wtforms.validators import Required
from invenio.sherpa_romeo import SherpaRomeoSearch
from invenio.webdeposit_workflow_utils import JsonCookerMixinBuilder

__all__ = ['JournalField']


class JournalField(TextField, JsonCookerMixinBuilder('journal')):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-book"></i>'

        # Create our own Required data member
        # for client-side use
        if kwargs.has_key('validators'):
            for v in kwargs.get("validators"):
                if type(v) is Required:
                    self.required = True

        super(JournalField, self).__init__(**kwargs)

    def pre_validate(self, form=None):
        value = self.data
        s = SherpaRomeoSearch()
        s.search_journal(value)
        issn = s.parser.get_issn()
        if type(issn) is str:  # unique journal
            return dict(error=0, error_message='',
                        fields=dict(issn=issn))
        else:
            return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data

        s = SherpaRomeoSearch()
        response = s.search_journal(value)
        return response
