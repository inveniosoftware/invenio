# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Implementation of validators, post-processors and auto-complete functions.

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

Default field validators (executed only if external validators are not
defined)::

    class MyField(...):
        def __init__(self, **kwargs):
            defaults = dict(validators=[my_validator])
            defaults.update(kwargs)
            super(MyField, self).__init__(**defaults)


See http://wtforms.simplecodes.com/docs/1.0.4/validators.html for how to
write validators.

Post-processors
---------------
Post processors follows the same pattern as validators. You may thus specify:

- Inline processors:::

    Form.post_process_<field>(form, field)

- External processors:::

    def my_processor(form, field):
        ...
        myfield = MyField(processors=[my_processor])

- Field defined processors (please method documentation):::

    Field.post_process(self, form, extra_processors=[])

Auto-complete
-------------

- External auto-completion function:::

    def my_autocomplete(form, field, limit=50):
        ...
        myfield = MyField(autocomplete=my_autocomplete)

- Field defined auto-completion function (please method documentation):::

    Field.autocomplete(self, form, limit=50)

"""

import warnings

from wtforms import Field

from .form import CFG_FIELD_FLAGS

__all__ = ('WebDepositField', )


class WebDepositField(Field):

    """Base field that all webdeposit fields must inherit from."""

    def __init__(self, *args, **kwargs):
        """
        Initialize WebDeposit field.

        Every field is associated with a marc field. To define this association
        you have to specify the `export_key` for the recordext `Reader` or the
        `cook_function` (for more complicated fields).

        :param placeholder: str, Placeholder text for input fields.
        :param icon: Name of icon (rendering of the icon is done by templates)
        :type icon: str
        :param autocomplete: callable, A function to auto-complete values
                             for field.
        :param processors: list of callables, List of processors to run
                           for field.
        :param validators: list of callables, List of WTForm validators.
                           If no validators are provided, validators defined
                           in webdeposit_config will be loaded.
        :param hidden: Set to true to hide field. Default: False
        :type hidden: bool
        :param disabled: Set to true to disable field. Default: False
        :type disabled: bool
        :param export_key: Name of key to use during export
        :type export_key: str or callable
        :param preamble: Short text that should appear in before the field,
                         usually meant for longer explanations.
        :type preamble: str

        :see http://wtforms.simplecodes.com/docs/1.0.4/validators.html for
             how to write validators.
        :see http://wtforms.simplecodes.com/docs/1.0.4/fields.html for further
             keyword argument that can be provided on field initialization.
        """
        # Pop WebDeposit specific kwargs before calling super()
        self.placeholder = kwargs.pop('placeholder', None)
        self.group = kwargs.pop('group', None)
        self.icon = kwargs.pop('icon', None)
        self.autocomplete = kwargs.pop('autocomplete', None)
        self.autocomplete_fn = kwargs.pop('autocomplete_fn', None)
        self.processors = kwargs.pop('processors', None)
        self.export_key = kwargs.pop('export_key', None)
        self.widget_classes = kwargs.pop('widget_classes', None)
        self.autocomplete_limit = kwargs.pop('autocomplete_limit', 20)
        self.readonly = kwargs.pop('readonly', None)
        self.preamble = kwargs.pop('preamble', None)

        # Initialize empty message variables, which are usually modified
        # during the post-processing phases.
        self._messages = []
        self._message_state = ''

        # Get flag values (e.g. hidden, disabled) before super() call.
        # See CFG_FIELD_FLAGS for all defined flags.
        flag_values = {}
        for flag in CFG_FIELD_FLAGS:
            flag_values[flag] = kwargs.pop(flag, False)

        # Call super-constructor.
        super(WebDepositField, self).__init__(*args, **kwargs)

        # Set flag values after super() call to ensure, flags set during
        # super() are overwritten.
        for flag, value in flag_values.items():
            if value:
                setattr(self.flags, flag, True)

        if callable(self.autocomplete):
            warnings.warn("Autocomplete functions use now "
                          "'autocomplete_fn' attribute",
                          DeprecationWarning)
            self.autocomplete_fn = self.autocomplete
            self.autocomplete = None

    def __call__(self, *args, **kwargs):
        """Set custom keyword arguments when rendering field."""
        if 'placeholder' not in kwargs and self.placeholder:
            kwargs['placeholder'] = self.placeholder
        if 'disabled' not in kwargs and self.flags.disabled:
            kwargs['disabled'] = "disabled"
        if 'class_' in kwargs and self.widget_classes:
            kwargs['class_'] = kwargs['class_'] + self.widget_classes
        elif self.widget_classes:
            kwargs['class_'] = self.widget_classes
        if self.autocomplete:
            kwargs['data-autocomplete'] = self.autocomplete
            kwargs['data-autocomplete-limit'] = self.autocomplete_limit
        elif self.autocomplete_fn:
            kwargs['data-autocomplete'] = "default"
        if self.readonly:
            kwargs['readonly'] = self.readonly
        return super(WebDepositField, self).__call__(*args, **kwargs)

    def reset_field_data(self, exclude=[]):
        """Reset the ``fields.data`` value to that of ``field.object_data``.

        Usually not called directly, but rather through Form.reset_field_data()

        :param exclude: List of formfield names to exclude.
        """
        if self.name not in exclude:
            self.data = self.object_data

    def post_process(self, form=None, formfields=[], extra_processors=[],
                     submit=False):
        """Post process form before saving.

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

            super(MyField, self).post_process(
                form, extra_processors=extra_processors
            )
        """
        # Check if post processing should run for this field
        if self.name in formfields or not formfields:
            stop = False
            for p in (self.processors or []):
                try:
                    p(form, self, submit=submit, fields=formfields)
                except StopIteration:
                    stop = True
                    break

            if not stop:
                for p in (extra_processors or []):
                    p(form, self, submit=submit, fields=formfields)

    def perform_autocomplete(self, form, name, term, limit=50):
        """Run auto-complete method for field.

        This method should not be called directly, instead use
        Form.autocomplete().
        """
        if name == self.name and self.autocomplete_fn:
            return self.autocomplete_fn(form, self, term, limit=limit)
        return None

    def add_message(self, msg, state=None):
        """Add a message.

        :param msg: The message to set
        :param state: State of message; info, warning, error, success.
        """
        self._messages.append(msg)
        if state:
            self._message_state = state

    def set_flags(self, flags):
        """Set field flags."""
        field_flags = flags.get(self.name, [])
        for check_flag in CFG_FIELD_FLAGS:
            setattr(self.flags, check_flag, check_flag in field_flags)

    @property
    def messages(self):
        """Retrieve field messages."""
        if self.errors:
            return {self.name: dict(
                state='error',
                messages=self.errors
            )}
        else:
            return {self.name: dict(
                state=getattr(self, '_message_state', ''),
                messages=self._messages
            )}
