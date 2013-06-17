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


"""
Validators
----------
Following is a short overview over how validators may be defined for fields.

Inline validators (always executed)::

    class MyForm(...):
        myfield = MyField()

        def validate_myfield(form, field):
            raise ValidationError("Message")


External validators (always executed)::

    def my_validator(form, field):
        raise ValidationError("Message")

    class MyForm(...):
            myfield = MyField(validators=[my_validator])


Field defined validators (always executed)::

    class MyField(...):
        # ...
        def pre_validate(self, form):
            raise ValidationError("Message")

Default field validators (executed only if external validators are not defined)::

    class MyField(...):
        def __init__(self, **kwargs):
            defaults = dict(validators=[my_validator])
            defaults.update(kwargs)
            super(MyField, self).__init__(**defaults)


See http://wtforms.simplecodes.com/docs/1.0.4/validators.html for how to
write validators.

Post-processors
---------------
Post processors follows the same pattern as validators. You may thus specify::

 * Inline processors: Form.post_process_<field>(form, field)
 * External processors: def my_processor(form, field) ... myfield = MyField(processors=[my_processor])
 * Field defined processors (please method documentation): Field.post_process(self, form, extra_processors=[])

Auto-complete
-------------
 * External auto-completion function: def my_autocomplete(form, field, limit=50) ... myfield = MyField(autocomplete=my_autocomplete)
 * Field defined auto-completion function (please method documentation): Field.autocomplete(self, form, limit=50)

Rec JSON key
------------

* External defined: myfield = MyField(recjson_key='...')
* Default field defined::

    class MyField(...):
        def __init__(self, **kwargs):
            defaults = {'recjson_key': '...'}
            defaults.update(kwargs)
            super(MyField, self).__init__(**defaults)
"""

from invenio.webdeposit_form import CFG_FIELD_FLAGS
from invenio.webdeposit_cook_json_utils import cook_to_recjson

__all__ = ['WebDepositField']


class WebDepositField(object):
    """
    Base field that all webdeposit fields must inherit from.
    """

    def __init__(self, **kwargs):
        """
        Initialize WebDeposit field.

        Every field is associated with a marc field. To define this association you
        have to specify the `recjson_key` for the bibfield's `JsonReader` or
        the `cook_function` (for more complicated fields).

        @param placeholder: str, Placeholder text for input fields.
        @param icon: Name of icon (rendering of the icon is done by templates)
        @type icon: str
        @param autocomplete: callable, A function to auto-complete values for field.
        @param processors: list of callables, List of processors to run for field.
        @param validators: list of callables, List of WTForm validators. If no validators are provided, validators defined in webdeposit_config will be loaded.
        @param hidden: Set to true to hide field. Default: False
        @type hidden: bool
        @param disabled: Set to true to disable field. Default: False
        @type disabled: bool
        @param recjson_key: Name of recjson key
        @type recjson_key: str
        @param cook_function: the cook function
        @type cook_function: function

        @see http://wtforms.simplecodes.com/docs/1.0.4/validators.html for
             how to write validators.
        @see http://wtforms.simplecodes.com/docs/1.0.4/fields.html for further
             keyword argument that can be provided on field initialization.
        """
        # Pop WebDeposit specific kwargs before calling super()
        self.placeholder = kwargs.pop('placeholder', None)
        self.group = kwargs.pop('group', None)
        self.icon = kwargs.pop('icon', None)
        self.autocomplete = kwargs.pop('autocomplete', None)
        self.processors = kwargs.pop('processors', None)
        self.recjson_key = kwargs.pop('recjson_key', None)
        self.cook_function = kwargs.pop('cook_function', None)

        # Initialize empty message variables, which are usually modified
        # during the post-processing phases.
        self.messages = []
        self.message_state = ''

        # Get flag values (e.g. hidden, disabled) before super() call.
        # See CFG_FIELD_FLAGS for all defined flags.
        flag_values = {}
        for flag in CFG_FIELD_FLAGS:
            flag_values[flag] = kwargs.pop(flag, False)

        # Call super-constructor.
        super(WebDepositField, self).__init__(**kwargs)

        # Set flag values after super() call to ensure, flags set during
        # super() are overwritten.
        for flag, value in flag_values.items():
            if value:
                setattr(self.flags, flag, True)

    def get_recjson_key(self):
        return self.recjson_key

    def has_cook_function(self):
        return self.cook_function is not None

    def has_recjson_key(self):
        return self.recjson_key is not None

    def cook_json(self, json_reader):
        """
        Fills a json_reader object with the field's value
        based on the recjson key

        @param json_reader: BibField's JsonReader object
        """
        cook = None
        if self.has_recjson_key():
            cook = cook_to_recjson(self.get_recjson_key())
        elif self.has_cook_function():
            cook = self.cook_function

        if cook is not None:
            return cook(json_reader, self.data)

        return json_reader

    def uncook_json(self, json_reader, webdeposit_json):
        """
        The opposite of `cook_json` (duh)
        Adds to the webdeposit_json the appropriate value
        from the json_reader based on the recjson key

        You have to retrieve the record with BibField and
        instantiate a json_reader object before starting
        the uncooking

        @param json_reader: BibField's JsonReader object
        @param webdeposit_json: a dictionary
        @return the updated webdeposit_json
        """

        if self.has_recjson_key() and \
                self.recjson_key in json_reader:
            webdeposit_json[self.name] = json_reader[self.recjson_key]
        return webdeposit_json

    def __call__(self, *args, **kwargs):
        """
        Set custom keyword arguments when rendering field
        """
        if 'placeholder' not in kwargs and self.placeholder:
            kwargs['placeholder'] = self.placeholder
        if 'disabled' not in kwargs and self.flags.disabled:
            kwargs['disabled'] = "disabled"
        return super(WebDepositField, self).__call__(*args, **kwargs)

    def post_process(self, form, extra_processors=[], submit=False):
        """
        Post process form before saving.

        Usually you can do some of the following tasks in the post
        processing:

         * Set field flags (e.g. self.flags.hidden = True or
           form.<field>.flags.hidden = True).
         * Set messages (e.g. self.messages.append('text') and
           self.message_state = 'info').
         * Set values of other fields (e.g. form.<field>.data = '').

        Processors may stop the processing chain by raising StopIteration.

        IMPORTANT: By default the method will execute custom post processors
        defined in the webdeposit_config. If you override the method, be
        sure to call this method to ensure extra processors are called::

            super(MyField, self).post_process(form, extra_processors=extra_processors)
        """
        # Run post-processors (either defined)
        stop = False
        for p in (self.processors or []):
            try:
                p(form, self, submit)
            except StopIteration:
                stop = True
                break

        if not stop:
            for p in (extra_processors or []):
                p(form, self, submit)

    def perform_autocomplete(self, form, term, limit=50):
        """
        Run auto-complete method for field. Use Form.autocomplete() to
        perform auto-completion for a field, since it will take care of
        preparing the field with data.
        """
        if self.autocomplete:
            return self.autocomplete(form, term, limit=limit)
        return []

    def add_message(self, state, message):
        """
        Adds a message to display for the field.
        The state can be info, error or success.
        """
        assert state in ['info', 'error', 'success']
        self.message_state = state
        self.messages.append(message)
