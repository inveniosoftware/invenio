# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Extended WTForms field.

Classes TimeField, DatePickerWidget, DateTimePickerWidget and TimePickerWidget
are taken from `flask-admin` extension.

:copyright: (c) 2011 by wilsaj.
:license: BSD, see LICENSE for more details.
:source: https://raw.github.com/wilsaj/flask-admin/master/flask_admin/wtforms.py
"""
import datetime

import time

from flask import current_app, session
from flask_wtf import Form

from wtforms.compat import text_type
from wtforms.ext.csrf.session import SessionSecureForm
from wtforms.fields import Field, FileField, HiddenField, StringField
from wtforms.form import Form as WTForm
from wtforms.widgets import HTMLString, TextInput, html_params


class RowWidget(object):

    """Renders a list of fields as a set of table rows with th/td pairs."""

    def __init__(self, **kwargs):
        """Init class."""
        self.defaults = kwargs

    def __call__(self, field, class_='', row_class='row', **kwargs):
        """There are Bootstrap 3 specific improvements for row wrapping."""
        html = []
        hidden = ''
        arguments = self.defaults
        arguments.update(kwargs)
        classes = arguments.get('classes', {})
        for i, subfield in enumerate(field):
            if subfield.type == 'HiddenField':
                hidden += text_type(subfield)
            else:
                wrapper_class = classes.get(i, '')
                html.append('%s<div class="%s">%s</div>' % (
                    hidden,
                    wrapper_class,
                    text_type(subfield(
                        class_=class_,
                        placeholder=subfield.label.text))))
                hidden = ''
        if hidden:
            html.append(hidden)
        return HTMLString('<div class="%s">' % (row_class, ) +
                          ''.join(html) + '</div>')


class TimeField(Field):

    """A text field which stores a `time.time` matching a format."""

    widget = TextInput()

    def __init__(self, label=None, validators=None,
                 format='%H:%M:%S', **kwargs):
        """Init."""
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or u''

    def process_formdata(self, valuelist):
        """Join time string."""
        if valuelist:
            time_str = u' '.join(valuelist)
            try:
                timetuple = time.strptime(time_str, self.format)
                self.data = datetime.time(*timetuple[3:6])
            except ValueError:
                self.data = None
                raise


class DatePickerWidget(TextInput):

    """
    TextInput widget that adds a 'datepicker' class.

    TextInput widget that adds a 'datepicker' class to the html input
    element; this makes it easy to write a jQuery selector that adds a
    UI widget for date picking.
    """

    def __call__(self, field, **kwargs):
        """Call."""
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datepicker %s' % c
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(TextInput):

    """
    TextInput widget that adds a 'datetimepicker' class.

    TextInput widget that adds a 'datetimepicker' class to the html
    adds a UI widget for datetime picking.
    """

    def __call__(self, field, **kwargs):
        """Add class datepicker."""
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datetimepicker %s' % c
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class TimePickerWidget(TextInput):

    """
    TextInput widget that adds a 'timepicker' class.

    TextInput widget that adds a 'timepicker' class to the html
    input element; this makes it easy to write a jQuery selector that
    adds a UI widget for time picking.
    """

    def __call__(self, field, **kwargs):
        """Add class timepicker."""
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'timepicker %s' % c
        return super(TimePickerWidget, self).__call__(field, **kwargs)


class AutocompleteField(StringField):

    """Text field with simple autocompletion."""

    def __init__(self, label=None, validators=None, data_provide="typeahead",
                 data_source=None, **kwargs):
        """Init."""
        super(AutocompleteField, self).__init__(label, validators, **kwargs)
        if data_source:
            self.widget = TypeheadWidget(data_source, data_provide)


class TypeheadWidget(object):

    """TextInput that use typeahead for autocompletion."""

    def __init__(self, autocomplete_list, data_provide):
        """Init autocompletion."""
        if callable(autocomplete_list):
            self.autocomplete_list = autocomplete_list()
        else:
            self.autocomplete_list = '["{}"]'.format(
                '","'.join(autocomplete_list))
        self.data_provide = data_provide

    def __call__(self, field, **kwargs):
        """Define special attributes."""
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'text')
        kwargs.setdefault('data-provide', self.data_provide)
        kwargs.setdefault('data-source', self.autocomplete_list)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        return HTMLString(u'<input %s />' % html_params(name=field.name,
                                                        **kwargs))


class RemoteAutocompleteField(StringField):

    """Define a text field with autocompletion from remote.

    How to use it:

    First, use RemoteAutocompleteField in a form.

    .. code-block:: python

        class MyForm(InvenioBaseForm):
                myfield = RemoteAutocompleteField(
                    'My Label',
                    # remote url where the field can ask suggestions
                    remote='/api/path/to/query?query=%QUERY',
                    # minimum length to start query
                    min_length=3,
                    # highlight the results in suggestions
                    highlight='true',
                    # field to use as key to submit with the form
                    data_key='field_to_use_as_key',
                    # field to visualize in the input field
                    data_value='field_to_visualize'
                )

    Then, create the API function that returns suggestions from
    url path `/api/path/to/query`.

    Note: you should return the results in JSON format, like:

    .. code-block:: javascript

        {
            "results": [
                {
                    field_to_use_as_key: 'my_key_1',
                    field_to_visualize: 'my_label_1'
                },
                {
                    field_to_use_as_key: 'my_key_2',
                    field_to_visualize: 'my_label_2'
                },
            ]
        }

    After that, you should manually initialize the javascript.

    To do that, for example, you can create a javascript init
    file `init.js` into your module's directory.

    E.g: `invenio/modules/mymodule/static/js/mymodule/init.js`:

    .. code-block:: javascript

        require([
            'js/remote.autocomplete.field'
        ], function(autocomplete) {
            // init the javascript interface
            autocomplete.attachTo($('input.remote-typeahead-widget'))
        })

    Finally, if you create a new `init.js` file, you need to
    add this in your bundle in your `bundles.py` file.

    E.g:

        .. code-block:: python

            js = Bundle(
                'js/mymodule/init.js',
                filters=RequireJSFilter(exclude=[_j, _i]),
                output="mymodule-init.js",
                weight=50
            )
    """

    def __init__(self, label=None, validators=None, remote=None,
                 min_length=None, highlight=None,
                 data_key=None, data_value=None, *args, **kwargs):
        """Init class."""
        super(RemoteAutocompleteField, self).__init__(label, validators,
                                                      *args, **kwargs)
        self.kwargs = {}
        self.kwargs['data-remoteautocomplete-remote'] = remote or ''
        self.kwargs['data-remoteautocomplete-minLength'] = min_length or 3
        self.kwargs['data-remoteautocomplete-highlight'] = highlight or 'true'
        self.kwargs['data-remoteautocomplete-data-key'] = data_key or ''
        self.kwargs['data-remoteautocomplete-data-value'] = data_value or ''
        self.widget = RemoteTypeheadWidget(label, **kwargs)

    def set_remote(self, value):
        """Update remote url."""
        self.widget.set_remote(value)


class RemoteTypeheadWidget(TextInput):

    """Typeahead widget that acquire data from remote."""

    def __init__(self, label, **kwargs):
        """Init class."""
        self.label = label
        self.kwargs = {}
        super(RemoteTypeheadWidget, self).__init__()

    def __call__(self, field, **kwargs):
        """Configure the html field."""
        kwargs.update(field.kwargs)
        kwargs.update(self.kwargs)
        kwargs['class_'] = kwargs['class_'] + ' remote-typeahead-widget '
        return super(RemoteTypeheadWidget, self).__call__(field, **kwargs)

    def set_remote(self, value):
        """Update remote url."""
        self.kwargs['data-remoteautocomplete-remote'] = value


def has_file_field(form):
    """
    Test whether or not a form has a FileField in it.

    This is used to know whether or not we need to set enctype to
    multipart/form-data.
    """
    for field in form:
        if isinstance(field, FileField):
            return True

    return False


class FilterStringField(StringField):

    """Define a FilterStringField."""

    alias = None

    def __init__(self, *args, **kwargs):
        """Init."""
        self.alias = kwargs.get('alias')
        if 'alias' in kwargs:
            del kwargs['alias']
        super(FilterStringField, self).__init__(*args, **kwargs)
        if not self.raw_data:
            self.raw_data = []

    def _value(self):
        if self.raw_data:
            return self.raw_data.pop()
        return u''


class InvenioForm(WTForm):

    """Define a Invenio Form."""

    @property
    def required_field_names(self):
        """Return all required field names."""
        return [field.name for field in self if hasattr(field, 'required')]


class InvenioBaseForm(Form, SessionSecureForm):

    """Define a InvenioBaseForm."""

    # SECRET_KEY = CFG_SITE_SECRET_KEY
    TIME_LIMIT = 1200.0

    def __init__(self, *args, **kwargs):
        """Init."""
        super(InvenioBaseForm, self).__init__(
            *args, csrf_context=session, **kwargs
        )

    def add_fields(self, name, field):
        """Add a field."""
        self.__setattr__(name, field)

    def validate_csrf_token(self, field):
        """Disable CRSF proection during testing."""
        if current_app.testing:
            return
        super(InvenioBaseForm, self).validate_csrf_token(field)


class FilterForm(InvenioBaseForm):

    """Filter forms contains hidden fields to keep sorting."""

    sort_by = HiddenField()
    order = HiddenField()
