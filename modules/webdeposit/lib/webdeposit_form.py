# -*- coding: utf-8 -*-
# #
# # This file is part of Invenio.
# # Copyright (C) 2013 CERN.
# #
# # Invenio is free software; you can redistribute it and/or
# # modify it under the terms of the GNU General Public License as
# # published by the Free Software Foundation; either version 2 of the
# # License, or (at your option) any later version.
# #
# # Invenio is distributed in the hope that it will be useful, but
# # WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# # General Public License for more details.
# #
# # You should have received a copy of the GNU General Public License
# # along with Invenio; if not, write to the Free Software Foundation, Inc.,
# # 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

from wtforms import Label
from invenio.wtforms_utils import InvenioForm as Form
from invenio.webdeposit_config_utils import WebDepositConfiguration
from invenio.webdeposit_cook_json_utils import cook_files


class WebDepositForm(Form):

    """ Generic WebDeposit Form class """

    def __init__(self, **kwargs):
        super(WebDepositForm, self).__init__(**kwargs)

        # Load and apply configuration from config file
        self.config = WebDepositConfiguration(form_type=self.__class__.__name__)

        custom_title = self.config.get_form_title(self.__class__.__name__)
        if custom_title is not None:
            self._title = custom_title

        for field in self._fields.values():
            custom_label = self.config.get_label(field.__class__.__name__)
            if custom_label is not None:
                setattr(field, 'label', Label(field.id, custom_label))

            custom_widget = self.config.get_widget(field.__class__.__name__)
            if custom_widget is not None:
                setattr(field, 'widget', custom_widget)

    def cook_json(self, json_reader):
        for field in self._fields.values():
            try:
                json_reader = field.cook_json(json_reader)
            except AttributeError:
                # Some fields (eg. SubmitField) don't have a cook json function
                pass
        json_reader = cook_files(json_reader, self.files)
        return json_reader
