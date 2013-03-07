# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
from invenio.dataciteutils import DataciteMetadata

__all__ = ['DOIField']


class DOIField(WebDepositField, TextField, JsonCookerMixinBuilder('doi')):

    def __init__(self, **kwargs):
        super(DOIField, self).__init__(**kwargs)
        self._icon_html = '<i class="icon-barcode"></i>'

    def pre_validate(self, form=None):
        value = self.data
        if value == "" or value.isspace():
            return dict()
        datacite = DataciteMetadata(value)
        if datacite.error:
            return dict(info=1, info_message="Couldn't retrieve doi metadata")

        return dict(fields=dict(publisher=datacite.get_publisher(),
                                title=datacite.get_titles(),
                                date=datacite.get_dates(),
                                abstract=datacite.get_description()),
                    success=1,
                    success_message='Datacite.org metadata imported successfully')
