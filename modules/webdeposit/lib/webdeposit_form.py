# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

from invenio.wtforms_utils import InvenioForm as Form
from invenio.webdeposit_cook_json_utils import cook_files, uncook_files

CFG_GROUPS_META = {
    'classes': None,
    'indication': None,
    'description': None
}
"""
Default group metadata.
"""

CFG_FIELD_FLAGS = [
    'hidden',
    'disabled'
]
"""
List of WTForm field flags to be saved in draft.

See more about WTForm field flags on:
http://wtforms.simplecodes.com/docs/1.0.4/fields.html#wtforms.fields.Field.flags
"""

"""
Form customization

you can customize the following for the form

_title: str, the title to be rendered on top of the form
_subtitle: str/html. explanatory text to be shown under the title.
_drafting: bool, show or hide the drafts at the right of the form

"""


class WebDepositForm(Form):

    """ Generic WebDeposit Form class """

    def __init__(self, **kwargs):
        super(WebDepositForm, self).__init__(**kwargs)
        self._messages = None

        self.groups_meta = {}
        if hasattr(self, 'groups'):
            for idx, group in enumerate(self.groups):
                group_name = group[0]
                fields = group[1]
                for field in fields:
                    setattr(self[field], 'group', group_name)

                self.groups_meta[group_name] = CFG_GROUPS_META.copy()
                if len(group) == 3:  # If group has metadata
                    self.groups_meta[group_name].update(group[2])

        if not hasattr(self, 'template'):
            self.template = 'webdeposit_add.html'

        if not hasattr(self, '_drafting'):
            self._drafting = True

        self.type = self.__class__.__name__

    def reset_field_data(self, exclude=[]):
        """
        Reset the fields.data value to that of field.object_data.

        Useful after initializing a form with both formdata and draftdata where
        the formdata is missing field values (usually because we are saving a
        single field).

        @param exclude: List of field names to exclude.
        """
        for name, field in self._fields.items():
            if name not in exclude:
                field.data = field.object_data

    def cook_json(self, json_reader):
        for field in self._fields.values():
            try:
                json_reader = field.cook_json(json_reader)
            except AttributeError:
                # Some fields (eg. SubmitField) don't have a cook json function
                pass

        json_reader = cook_files(json_reader, self.files)

        return json_reader

    def uncook_json(self, json_reader, webdeposit_json, recid=None):
        for field in self._fields.values():
            if hasattr(field, 'uncook_json'):
                # WTFields are not mapped with rec json
                webdeposit_json = field.uncook_json(json_reader,
                                                    webdeposit_json)

        webdeposit_json = uncook_files(webdeposit_json, recid=recid,
                                       json_reader=json_reader)
        return webdeposit_json

    def get_groups(self):
        """
        Get a list of the (group metadata, list of fields)-tuples

        The last element of the list has no group metadata (i.e. None),
        and contains the list of fields not assigned to any group.
        """
        fields_included = set()
        field_groups = []

        if hasattr(self, 'groups'):
            for group in self.groups:
                group_obj = {
                    'name': group[0],
                    'meta': CFG_GROUPS_META.copy(),
                }

                fields = []
                for field_name in group[1]:
                    fields.append(self[field_name])
                    fields_included.add(field_name)

                if len(group) == 3:
                    group_obj['meta'].update(group[2])

                field_groups.append((group_obj, fields))

        # Append missing fields not defined in groups
        rest_fields = []
        for field in self:
            if field.name not in fields_included:
                rest_fields.append(field)
        if rest_fields:
            field_groups.append((None, rest_fields))

        return field_groups

    @property
    def json_data(self):
        """
        Return form data in a format suitable for the standard JSON encoder, by
        calling Field.json_data() on each field if it exists, otherwise is uses
        the value of Field.data.
        """
        return dict(
            (name, f.json_data() if getattr(f, 'json_data', None) else f.data)
            for name, f in self._fields.items()
        )

    def get_template(self):
        """
        Get template to render this form.
        Define a data member `template` to customize which template to use.

        By default, it will render the template `webdeposit_add.html`

        """

        return [self.template]

    def post_process(self, fields=[], submit=False):
        """
        Run form post-processing by calling `post_process` on each field,
        passing any extra `Form.post_process_<fieldname>` processors to the
        field.

        If ``fields'' are specified, only the given fields' processors will be
        run (which may touch all fields of the form).

        The post processing allows the form to alter other fields in the form,
        via e.g. contacting external services (e.g a DOI field could retrieve
        title, authors from CrossRef/DataCite).
        """
        for name, field, in self._fields.items():
            if not fields or name in fields:
                inline = getattr(
                    self.__class__, 'post_process_%s' % name, None)
                if inline is not None:
                    extra = [inline]
                else:
                    extra = []
                field.post_process(self, extra_processors=extra, submit=False)

    def autocomplete(self, field_name, term, limit=50):
        """
        Auto complete a form field.

        Assumes that formdata has already been loaded by into the form, so that
        the search term can be access by field.data.
        """
        if field_name in self._fields:
            return self._fields[field_name].perform_autocomplete(
                self,
                term,
                limit=limit,
            )[:limit]
        return []

    @property
    def messages(self):
        """
        Return a dictionary of form messages.
        """
        _messages = dict(
            (
                name,
                {
                    'state': f.message_state
                             if hasattr(f, 'message_state') and f.message_state
                             else '',
                    'messages': f.messages,
                }
            ) for name, f in self._fields.items()
        )

        if self.errors:
            _messages.update(dict(
                (
                    name,
                    {
                        'state': 'error',
                        'messages': messages,
                    }
                ) for name, messages in self.errors.items()

            ))
        return _messages

    @property
    def flags(self):
        """
        Return dictionary of fields and their set flags

        Note only flags from CFG_FIELD_FLAGS that is set to True are returned.
        """
        return dict(
            (
                name,
                filter(lambda flag: getattr(f.flags, flag), CFG_FIELD_FLAGS)
            ) for name, f in self._fields.items()
        )
