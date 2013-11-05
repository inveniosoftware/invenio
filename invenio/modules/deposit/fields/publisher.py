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
from invenio.modules.deposit.field_base import WebDepositField
from ..processor_utils import sherpa_romeo_publisher_process
from ..autocomplete_utils import sherpa_romeo_publishers

__all__ = ['PublisherField']


class PublisherField(WebDepositField, TextField):
    def __init__(self, **kwargs):
        defaults = dict(
            icon='certificate',
            processors=[sherpa_romeo_publisher_process],
            autocomplete=sherpa_romeo_publishers,
            widget_classes="form-control"
        )
        defaults.update(kwargs)
        super(PublisherField, self).__init__(**defaults)

    # def post_process(self, form, extra_processors=[]):
    #     sherpa_romeo_publisher_validate(self, form) #FIXME
    #     super(PublisherField, self).post_process(form, extra_processors=extra_processors)

    # def autocomplete(self, term, limit): #FIXME
    #      # Load custom auto complete function
    #     autocomplete = self.config.get_autocomplete_function()
    #     if autocomplete is not None:
    #         return autocomplete(self.data)
    #     return sherpa_romeo_publishers(self.data)
