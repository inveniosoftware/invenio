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

"""
Extended WTForms field

Classes TimeField, DatePickerWidget, DateTimePickerWidget and TimePickerWidget
are taken from `flask-admin` extension.

:copyright: (c) 2011 by wilsaj.
:license: BSD, see LICENSE for more details.
:source: https://raw.github.com/wilsaj/flask-admin/master/flask_admin/wtforms.py
"""
import datetime
import time

from flask import session
from wtforms.form import Form as WTForm
from wtforms.widgets import TextInput, HTMLString, html_params
from wtforms.fields import Field, TextField, HiddenField, FileField
from flask.ext.wtf import Form
from wtforms.ext.csrf.session import SessionSecureForm
from wtforms.compat import text_type
#from invenio.config import CFG_SITE_SECRET_KEY


class RowWidget(object):
    """
    Renders a list of fields as a set of table rows with th/td pairs.
    """
    def __init__(self):
        pass

    def __call__(self, field, **kwargs):
        html = []
        hidden = ''
        for subfield in field:
            if subfield.type == 'HiddenField':
                hidden += text_type(subfield)
            else:
                html.append('%s%s' % (hidden, text_type(subfield(class_="span1", placeholder=subfield.label.text))))
                hidden = ''
        if hidden:
            html.append(hidden)
        return HTMLString(''.join(html))


class TimeField(Field):
    """A text field which stores a `time.time` matching a format."""
    widget = TextInput()

    def __init__(self, label=None, validators=None,
                 format='%H:%M:%S', **kwargs):
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.format = format

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or u''

    def process_formdata(self, valuelist):
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
    TextInput widget that adds a 'datepicker' class to the html input
    element; this makes it easy to write a jQuery selector that adds a
    UI widget for date picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datepicker %s' % c
        return super(DatePickerWidget, self).__call__(field, **kwargs)


class DateTimePickerWidget(TextInput):
    """TextInput widget that adds a 'datetimepicker' class to the html
    adds a UI widget for datetime picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'datetimepicker %s' % c
        return super(DateTimePickerWidget, self).__call__(field, **kwargs)


class TimePickerWidget(TextInput):
    """TextInput widget that adds a 'timepicker' class to the html
    input element; this makes it easy to write a jQuery selector that
    adds a UI widget for time picking.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'timepicker %s' % c
        return super(TimePickerWidget, self).__call__(field, **kwargs)


class AutocompleteField(TextField):
    def __init__(self, label=None, validators=None, data_provide="typeahead", data_source=None, **kwargs):
        super(AutocompleteField, self).__init__(label, validators, **kwargs)
        if data_source:
            self.widget = TypeheadWidget(data_source, data_provide)


class TypeheadWidget(object):
    def __init__(self, autocomplete_list, data_provide):
        if callable(autocomplete_list):
            self.autocomplete_list = autocomplete_list()
        else:
            self.autocomplete_list = '["{}"]'.format('","'.join(autocomplete_list))
        self.data_provide = data_provide

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'text')
        kwargs.setdefault('data-provide', self.data_provide)
        kwargs.setdefault('data-source', self.autocomplete_list)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        return HTMLString(u'<input %s />' % html_params(name=field.name, **kwargs))


def has_file_field(form):
    """Test whether or not a form has a FileField in it. This is used
    to know whether or not we need to set enctype to
    multipart/form-data.
    """
    for field in form:
        if isinstance(field, FileField):
            return True

    return False


class FilterTextField(TextField):
    alias = None

    def __init__(self, *args, **kwargs):
        self.alias = kwargs.get('alias')
        if 'alias' in kwargs:
            del kwargs['alias']
        super(TextField, self).__init__(*args, **kwargs)
        if not self.raw_data:
            self.raw_data = []

    def _value(self):
        if self.raw_data:
            return self.raw_data.pop()
        return u''


class InvenioForm(WTForm):
    @property
    def required_field_names(self):
        return [field.name for field in self if hasattr(field, 'required')]


class InvenioBaseForm(Form, SessionSecureForm):
    #SECRET_KEY = CFG_SITE_SECRET_KEY
    TIME_LIMIT = 1200.0

    def __init__(self, *args, **kwargs):
        super(InvenioBaseForm, self).__init__(*args, csrf_context=session, **kwargs)

    def add_fields(self, name, field):
        self.__setattr__(name, field)


class FilterForm(InvenioBaseForm):
    """
    Filter forms contains hidden fields to keep sorting.
    """
    sort_by = HiddenField()
    order = HiddenField()
