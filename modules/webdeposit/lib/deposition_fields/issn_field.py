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
from invenio.webdeposit_workflow_utils import JsonCookerMixinBuilder
from invenio.sherpa_romeo import SherpaRomeoSearch

__all__ = ['ISSNField']


class ISSNField(WebDepositField, TextField, JsonCookerMixinBuilder('issn')):

    def __init__(self, **kwargs):
        super(ISSNField, self).__init__(**kwargs)
        self._icon_html = '<i class="icon-barcode"></i>'

    def pre_validate(self, form=None):
        value = self.data
        if value == "" or value.isspace():
            return dict(error=0, error_message='')
        s = SherpaRomeoSearch()
        s.search_issn(value)
        if s.error:
            return dict(error=1, error_message=s.error_message)

        if s.get_num_hits() == 1:
            journal = s.parser.get_journals(attribute='jtitle')
            journal = journal[0]
            publisher = s.parser.get_publishers(journal=journal)
            if publisher is not None and publisher != []:
                return dict(error=0, error_message='',
                            fields=dict(journal=journal, publisher=publisher['name']))
            else:
                return dict(error=0, error_message='',
                            fields=dict(journal=journal))

        return dict(info=1, info_message="Couldn't find Journal")
