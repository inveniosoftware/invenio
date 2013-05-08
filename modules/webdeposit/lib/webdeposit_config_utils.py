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

from werkzeug.utils import import_string
from invenio.cache import cache
from invenio.sqlalchemyutils import db
from invenio.webuser_flask import current_user
from invenio.webdeposit_model import WebDepositDraft
from invenio.bibworkflow_model import Workflow
from invenio.webinterface_handler_flask_utils import _


class WebDepositConfiguration(object):
    """ Webdeposit configuration class
        Returns configuration for fields based on runtime variables
        or, if not defined, based on the parameters

        @param deposition_type: initialize the class for a deposition type

        @param form_name: initialize the class for a form
            used when a form is defined to load validators and widgets

        @param field_type: initialize the class for a field
            used in the field pre_validate and autocomplete methods
            to load and call them on runtime
    """

    def __init__(self, deposition_type=None, form_type=None, field_type=None):
        self.config = import_string('invenio.webdeposit_config:config')
        self.deposition_type = deposition_type
        self.form_type = form_type
        self.field_type = field_type
        self._runtime_vars_init()

    def _runtime_vars_init(self):
        """ Initializes user_id, deposition type, uuid and form_type
        """

        self.user_id = current_user.get_id()

        if self.deposition_type is None:

            self.runtime_deposition_type = cache.get(str(self.user_id) +
                                                    ":current_deposition_type")
        else:
            self.runtime_deposition_type = None

            #  The uuid is always defined on runtime
        self.uuid = cache.get(str(self.user_id) + ":current_uuid")

        if self.uuid is not None and self.form_type is None:
            webdeposit_draft_query = db.session.query(WebDepositDraft).\
                                     join(Workflow).\
                                     filter(
                                         Workflow.user_id == self.user_id,
                                         WebDepositDraft.uuid == self.uuid)
            # get the draft with the max step
            webdeposit_draft = max(webdeposit_draft_query.all(), key=lambda w: w.step)

            self.runtime_form_type = webdeposit_draft.form_type
        else:
            self.runtime_form_type = None

    #FIXME: Make the deposition_type, form_type and field_type an attribute
    def get_deposition_type(self):
        return self.runtime_deposition_type or self.deposition_type

    def get_form_type(self):
        if self.runtime_form_type is not None:
            return self.runtime_form_type
        else:
            return self.form_type

    def get_field_type(self):
        return self.field_type

    def get_form_title(self, form_type=None):
        """ Returns the title of the form

            @param form_type: the type of the form.
                to use this function it must be defined here
                or at the class construction
        """

        deposition_type = self.get_deposition_type()
        form_type = self.get_form_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if form_type in deposition_config:
                form_config = deposition_config[form_type]
                if 'title' in form_config:
                    return _(form_config['title'])

        return None

    def get_label(self, field_type=None):
        """ Returns the label of the field

            @param field_type: the type of the field.
                to use this function it must be defined here
                or at the class construction
        """

        deposition_type = self.get_deposition_type()
        form_type = self.get_form_type()
        field_type = field_type or self.get_field_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if form_type in deposition_config:
                form_config = deposition_config[form_type]
                if field_type in form_config['fields']:
                    field_config = form_config['fields'][field_type]
                    if 'label' in field_config:
                        return _(field_config['label'])
        else:
            return None

    def get_widget(self, field_type=None):
        """ Returns the widget of the field

            @param field_type: the type of the field.
                to use this function it must be defined here
                or at the class construction
        """

        deposition_type = self.get_deposition_type()
        form_type = self.get_form_type()
        field_type = field_type or self.get_field_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if form_type in deposition_config:
                form_config = deposition_config[form_type]
                if field_type in form_config['fields']:
                    field_config = form_config['fields'][field_type]
                    if 'widget' in field_config:
                        return import_string(_(field_config['widget']))
        else:
            return None

    def get_autocomplete_function(self):
        """ Returns an autocomplete function of the field
        """
        deposition_type = self.get_deposition_type()
        form_type = self.get_form_type()
        field_type = self.get_field_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if form_type in deposition_config:
                form_config = deposition_config[form_type]
                if field_type in form_config['fields']:
                    field_config = form_config['fields'][field_type]
                    if 'autocomplete' in field_config:
                        return import_string(field_config['autocomplete'])
        else:
            return None

    def get_validators(self):
        """ Returns validators function based of the field
        """
        deposition_type = self.get_deposition_type()
        form_type = self.get_form_type()
        field_type = self.get_field_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if form_type in deposition_config:
                form_config = deposition_config[form_type]
                if field_type in form_config['fields']:
                    field_config = form_config['fields'][field_type]
                    if 'validators' in field_config:
                        validators = []
                        for validator in field_config['validators']:
                            validators.append(import_string(validator))
                        return validators
        else:
            return None

    def get_cook_json_function(self, field_type=None):
        deposition_type = self.get_deposition_type()
        form_type = self.get_form_type()
        field_type = field_type or self.get_field_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if form_type in deposition_config:
                form_config = deposition_config[form_type]
                if field_type in form_config['fields']:
                    field_config = form_config['fields'][field_type]
                    if 'cook' in field_config:
                        return import_string(field_config['cook'])
        else:
            return None

    def get_collection(self, deposition_type=None):
        deposition_type = deposition_type or self.get_deposition_type()

        if deposition_type in self.config:
            deposition_config = self.config[deposition_type]
            if 'collection' in deposition_config:
                return deposition_config['collection']
        else:
            return None
