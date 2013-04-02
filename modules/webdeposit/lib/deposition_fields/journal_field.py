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
from invenio.webdeposit_autocomplete_utils import sherpa_romeo_journals
from invenio.webdeposit_validation_utils import sherpa_romeo_journal_validate
from invenio.webdeposit_workflow_utils import JsonCookerMixinBuilder

__all__ = ['JournalField']


class JournalField(WebDepositField, TextField, JsonCookerMixinBuilder('journal')):

    def __init__(self, **kwargs):
        super(JournalField, self).__init__(**kwargs)
        self._icon_html = '<i class="icon-book"></i>'

    def pre_validate(self, form=None):
        return sherpa_romeo_journal_validate(self)

    def autocomplete(self):
        return sherpa_romeo_journals(self.data)
