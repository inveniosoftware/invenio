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


"""This module makes all WTForms fields available in WebDeposit.

This module makes all WTForms fields available in WebDeposit, and ensure that
they subclass WebDepositField for added functionality

The code is basically identical to importing all the WTForm fields and for each
field make a subclass according to the pattern (using FloatField as
an example):

.. code-block:: python

    class FloatField(WebDepositField, wtforms.FloatField):
        pass
"""

import itertools

from werkzeug import MultiDict

import wtforms

from wtforms.fields.core import Flags
from wtforms.utils import unset_value

from ..field_base import WebDepositField


__all__ = ['FormField', 'FieldList', 'DynamicFieldList']

for attr_name in dir(wtforms):
    attr = getattr(wtforms, attr_name)
    try:
        if issubclass(attr, wtforms.Field):
            # From a WTForm field, dynamically create a new class the same name
            # as the WTForm field (inheriting from WebDepositField() and the
            # WTForm field itself). Store the new class in the current module
            # with the same name as the WTForms.
            #
            # For further information please see Python reference documentation
            # for globals() and type() functions.
            globals()[attr_name] = type(
                str(attr_name),
                (WebDepositField, attr),
                {}
            )
            __all__.append(attr_name)
    except TypeError:
        pass


class FlagProxy(object):
    def __init__(self, obj):
        self._obj = obj

    def __getattr__(self, k):
        result = getattr(self._obj._flags, k)

        if k in self._obj._populate:
            for f in self._obj.form._fields:
                x = getattr(self._obj.form._fields[f].flags, k)
                if x:
                    result = x

        return result

    def __setattr__(self, k, v):
        if k.startswith('_'):
            dict.__setattr__(self, k, v)
        else:
            setattr(self._obj._flags, k, v)


#
# Special needs for field enclosures
#
class FormField(WebDepositField, wtforms.FormField):

    """Deposition form field."""

    def __init__(self, *args, **kwargs):
        """Init."""
        if 'autocomplete' in kwargs:
            raise TypeError('FormField cannot take autocomplete argument. '
                            'Instead, define it on the enclosed fields.')
        if 'placeholder' in kwargs:
            raise TypeError('FormField cannot take placeholder argument. '
                            'Instead, define it on the enclosed fields.')
        if 'processors' in kwargs:
            raise TypeError('FormField cannot take processors. '
                            'Instead, define them on the enclosed fields.')
        self._flags = Flags()
        self._populate = kwargs.pop('populate', ['required'])
        super(FormField, self).__init__(*args, **kwargs)

    def reset_field_data(self, exclude=[]):
        """Reset the ``fields.data`` value to that of ``field.object_data``.

        Usually not called directly, but rather through
        ``Form.reset_field_data()``.

        :param exclude: List of formfield names to exclude.
        """
        self.form.reset_field_data(exclude=exclude)

    def process(self, formdata, data=unset_value):
        """Preprocess formdata in case we are passed a JSON data structure."""
        if formdata and self.name in formdata:
            if not isinstance(formdata[self.name], dict):
                raise ValueError("Got unexpected value type")

            formdata = formdata[self.name]
            formdata = MultiDict(dict([
                ("%s%s%s" % (self.name, self.separator, k), v)
                for k, v in formdata.items()
            ]))

        super(FormField, self).process(formdata, data=data)

    def post_process(self, form=None, formfields=[], extra_processors=[],
                     submit=False):
        """Run post process on each subfield.

        Run post process on each subfield as well as extra processors defined
        on form.
        """
        # Ignore extra_processors on purpose (as they are not allowed for
        # field enclosures)
        self.form.post_process(form=self.form, formfields=formfields,
                               submit=submit)

    def perform_autocomplete(self, form, name, term, limit=50):
        """Run auto-complete method for field.

        This method should not be called directly, instead use
        Form.autocomplete().
        """
        if name.startswith(self.name + self.separator):
            form = self.form_class(prefix=self.name + self.separator)
            return form.autocomplete(name, term, limit=limit, _form=form)
        return None

    def get_flags(self, filter_func=None):
        """Get flags."""
        flags = self.form.get_flags(filter_func=filter_func)
        flags[self.name] = filter_func(self)
        return flags

    def set_flags(self, flags):
        """Set flags."""
        self.form.set_flags(flags)
        super(FormField, self).set_flags(flags)

    @property
    def flags(self):
        """Get flags in form of a proxy.

        This proxy accumulats flags stored in this object and all children
        fields.
        """
        return FlagProxy(self)

    @flags.setter
    def flags(self, v):
        """Set flags stored in this object."""
        if not isinstance(v, FlagProxy):
            self._flags = v

    @property
    def json_data(self):
        """Json data property."""
        return self.form.json_data

    @property
    def messages(self):
        """Message property."""
        _messages = self.form.messages
        _messages.update(super(FormField, self).messages)
        return _messages


class FieldList(WebDepositField, wtforms.FieldList):

    """Deposition field list."""

    def __init__(self, *args, **kwargs):
        """Init."""
        if 'autocomplete' in kwargs:
            raise TypeError('FieldList does not accept autocomplete argument.'
                            'Instead, define it on the enclosed field.')
        if 'placeholder' in kwargs:
            raise TypeError('FieldList does not accept placeholder argument. '
                            'Instead, define it on the enclosed field.')
        if 'processors' in kwargs:
            raise TypeError('FieldList does not accept processors. '
                            'Instead, define them on the enclosed field.')
        super(FieldList, self).__init__(*args, **kwargs)

    def get_entries(self):
        """Get entries."""
        # Needed so subclasses can customize which entries are returned
        return self.entries

    def _add_entry(self, *args, **kwargs):
        try:
            return super(FieldList, self)._add_entry(*args, **kwargs)
        except ValueError as e:
            self.process_errors.append(e.args[0])

    def _extract_indices(self, prefix, formdata):
        """
        Yield indices of any keys with given prefix.

        formdata must be an object which will produce keys when iterated.  For
        example, if field 'foo' contains keys 'foo-0-bar', 'foo-1-baz', then
        the numbers 0 and 1 will be yielded, but not neccesarily in order.
        """
        # Add fix for non-standard separator
        separator = '-'
        if issubclass(self.unbound_field.field_class, FormField):
            separator = self.unbound_field.kwargs.get('separator', '-')
        offset = len(prefix) + 1
        for k in formdata:
            if k.startswith(prefix):
                k = k[offset:].split(separator, 1)[0]
                if k.isdigit():
                    yield int(k)

    def reset_field_data(self, exclude=[]):
        """Reset the fields.data value to that of field.object_data.

        Usually not called directly, but rather through Form.reset_field_data()

        :param exclude: List of formfield names to exclude.
        """
        if self.name not in exclude:
            for subfield in self.get_entries():
                subfield.reset_field_data(exclude=exclude)

    def validate(self, form, extra_validators=tuple()):
        """Adapted to use self.get_entries() instead of self.entries."""
        self.errors = list(self.process_errors)

        # Run validators on all entries within
        for subfield in self.get_entries():
            if not subfield.validate(form):
                self.errors.append(subfield.errors)

        chain = itertools.chain(self.validators, extra_validators)
        self._run_validation_chain(form, chain)

        return len(self.errors) == 0

    def process(self, *args, **kwargs):
        """Process."""
        self.process_errors = []
        return super(FieldList, self).process(*args, **kwargs)

    def post_process(self, form=None, formfields=[], extra_processors=[],
                     submit=False):
        """Run post process on each subfield.

        Run post process on each subfield as well as extra processors defined
        on form.
        """
        for subfield in self.get_entries():
            # Ignore extra_processors on purpose (as they are not allowed for
            # field enclosures)
            subfield.post_process(
                form=form, formfields=formfields, extra_processors=[],
                submit=submit
            )

    def perform_autocomplete(self, form, name, term, limit=50):
        """Run auto-complete method for field.

        This method should not be called directly, instead use
        ``Form.autocomplete()``.
        """
        separator = '-'
        if issubclass(self.unbound_field.field_class, FormField):
            separator = self.unbound_field.kwargs.get('separator', '-')
        offset = len(self.name) + 1

        if name.startswith(self.name):
            idx = name[offset:].split(separator, 1)[0]
            field = self.bound_field(idx)
            if field:
                return field.perform_autocomplete(form, name, term,
                                                  limit=limit)
        return None

    def bound_field(self, idx):
        """Create a bound field for index."""
        if idx.isdigit():
            field = self.unbound_field.bind(
                form=None,
                name="%s-%s" % (self.name, idx),
                prefix=self._prefix,
                id="%s-%s" % (self.id, idx),
            )
            return field
        return None

    def get_flags(self, filter_func=None):
        """Get flags."""
        flags = {}
        for f in self.get_entries():
            if hasattr(f, 'get_flags'):
                flags.update(f.get_flags(filter_func=filter_func))
            else:
                flags.update({f.name: filter_func(f)})
        flags[self.name] = filter_func(self)
        return flags

    def set_flags(self, flags):
        """Set flags."""
        for f in self.get_entries():
            f.set_flags(flags)
        super(FieldList, self).set_flags(flags)

    @property
    def json_data(self):
        """Json data property."""
        return [
            f.json_data if getattr(f, 'json_data', None) else f.data
            for f in self.get_entries()
        ]

    @property
    def data(self):
        """Adapted to use self.get_entries() instead of self.entries."""
        return [f.data for f in self.get_entries()]

    @property
    def messages(self):
        """Message."""
        _messages = {}

        for f in self.get_entries():
            _messages.update(f.messages)

        _messages.update(super(FieldList, self).messages)
        return _messages


class DynamicFieldList(FieldList):

    """Encapsulate an ordered list of multiple instances of the same field type.

    Encapsulate an ordered list of multiple instances of the same field type,
    keeping data as a list.

    Extends WTForm FieldList field to allow dynamic add/remove of enclosed
    fields.
    """

    def __init__(self, *args, **kwargs):
        """Init."""
        from ..field_widgets import DynamicListWidget
        self.widget = kwargs.pop('widget', DynamicListWidget())
        self.empty_index = kwargs.pop('empty_index', '__index__')
        self.add_label = kwargs.pop('add_label', None)
        super(DynamicFieldList, self).__init__(*args, **kwargs)

    def process(self, formdata, data=unset_value):
        """Adapted from wtforms.FieldList.

        Adapted from wtforms.FieldList to allow merging content
        formdata and draft data properly.
        """
        self.process_errors = []
        self.entries = []
        if data is unset_value or not data:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        if formdata:
            if self.name not in formdata:
                max_index = max(
                    [len(data) - 1] + list(
                        set(self._extract_indices(self.name, formdata))
                    )
                )
                indices = range(0, max_index + 1)

                if self.max_entries:
                    indices = indices[:self.max_entries]

                idata = iter(data)
                for index in indices:
                    try:
                        obj_data = next(idata)
                    except StopIteration:
                        obj_data = unset_value
                    self._add_entry(formdata, obj_data, index=index)
            else:
                # Update keys in formdata, to allow proper form processing
                self.raw_data = formdata.getlist(self.name)
                for index, raw_entry in enumerate(self.raw_data):
                    entry_formdata = MultiDict({
                        "%s-%s" % (self.name, index): raw_entry
                    })
                    self._add_entry(entry_formdata, index=index)
        else:
            for obj_data in data:
                self._add_entry(formdata, obj_data)

        while len(self.entries) < self.min_entries:
            self._add_entry(formdata)
        self._add_empty_entry()

    def _add_empty_entry(self):
        kwargs = dict(
            form=None,
            name='%s-%s' % (self.short_name, self.empty_index),
            prefix=self._prefix,
            id='%s-%s' % (self.id, self.empty_index),
        )
        _meta = getattr(self, 'meta', None)
        if _meta is not None:
            kwargs['_meta'] = _meta
        field = self.unbound_field.bind(**kwargs)
        field.process(None, None)
        self.entries.append(field)
        return field

    def get_entries(self):
        """Filter out empty index entry."""
        return filter(
            lambda e: not e.name.endswith(self.empty_index),
            self.entries
        )

    def bound_field(self, idx, force=False):
        """Create a bound subfield for this list."""
        if idx.isdigit() or idx in [self.empty_index, '__input__'] or force:
            kwargs = dict(
                form=None,
                name='%s-%s' % (self.name, idx),
                prefix=self._prefix,
                id='%s-%s' % (self.id, idx),
            )
            _meta = getattr(self, 'meta', None)
            if _meta is not None:
                kwargs['_meta'] = _meta
            field = self.unbound_field.bind(**kwargs)
            return field
        return None
