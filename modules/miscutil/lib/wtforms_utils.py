# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

from wtforms.widgets import TextInput
from wtforms.fields import Field, TextField, HiddenField
from wtforms import validators
from flask.ext.wtf import Form
from wtforms.ext.csrf.session import SessionSecureForm

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

from flask import session

class InvenioBaseForm(Form, SessionSecureForm):
    SECRET_KEY = 'EPj00jpfj8Gx1SjnyLxwBBSQfnQ9DJYe0Ym'
    TIME_LIMIT = datetime.timedelta(minutes=20)

    def __init__(self, *args, **kwargs):
        super(InvenioBaseForm, self).__init__(*args, csrf_context=session, **kwargs)

class FilterForm(InvenioBaseForm):
    """
    Filter forms contains hidden fields to keep sorting.
    """
    sort_by = HiddenField()
    order = HiddenField()

