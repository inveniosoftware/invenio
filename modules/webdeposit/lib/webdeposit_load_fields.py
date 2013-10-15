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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os
from pprint import pformat
from werkzeug import MultiDict
from wtforms.fields.core import _unset_value
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.pluginutils import PluginContainer


__all__ = ['fields']


def plugin_builder(plugin_name, plugin_code):
    from wtforms import Field
    if plugin_name == '__init__':
        return
    candidates = []
    all = getattr(plugin_code, '__all__', [])
    for name in all:
        candidate = getattr(plugin_code, name, object)
        if issubclass(candidate, Field):
            candidates.append(candidate)
    return candidates


CFG_FIELDS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio',
                                          'webdeposit_deposition_fields',
                                          '*_field.py'),
                             plugin_builder=plugin_builder)


class Fields(object):
    pass

fields = Fields()

for field_list in CFG_FIELDS.itervalues():
    for field in field_list:
        ## Change the names of the fields from the file names to the class names.
        if field is not None:
            setattr(fields, field.__name__, field)


#
# Customize some WTForms fields
#
# Note: Because DynamicFieldList extends fields.FieldList it cannot be
# located in a plugin file.
class DynamicFieldList(fields.FieldList):
    """
    Encapsulate an ordered list of multiple instances of the same field type,
    keeping data as a list.

    Extends WTForm FieldList field to allow dynamic add/remove of enclosed
    fields.
    """
    def __init__(self, *args, **kwargs):
        from invenio.webdeposit_field_widgets import DynamicListWidget
        self.widget = kwargs.pop('widget', DynamicListWidget())
        self.empty_index = kwargs.pop('empty_index', '__index__')
        self.add_label = kwargs.pop('add_label', None)
        super(DynamicFieldList, self).__init__(*args, **kwargs)

    def process(self, formdata, data=_unset_value):
        """
        Adapted from wtforms.FieldList to allow merging content
        formdata and draft data properly.
        """
        self.entries = []
        if data is _unset_value or not data:
            try:
                data = self.default()
            except TypeError:
                data = self.default

        self.object_data = data

        if formdata:
            if self.name not in formdata:
                max_index = max(
                    [len(data)-1] + list(
                        set(self._extract_indices(self.name, formdata))
                    )
                )
                indices = range(0, max_index+1)

                if self.max_entries:
                    indices = indices[:self.max_entries]

                idata = iter(data)
                for index in indices:
                    try:
                        obj_data = next(idata)
                    except StopIteration:
                        obj_data = _unset_value
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
        name = '%s-%s' % (self.short_name, self.empty_index)
        field_id = '%s-%s' % (self.id, self.empty_index)
        field = self.unbound_field.bind(
            form=None, name=name, prefix=self._prefix, id=field_id
        )
        field.process(None, None)
        self.entries.append(field)
        return field

    def get_entries(self):
        """ Filter out empty index entry """
        return filter(
            lambda e: not e.name.endswith(self.empty_index),
            self.entries
        )

    def bound_field(self, idx, force=False):
        """
        Create a bound subfield for this list.
        """
        if idx.isdigit() or idx in [self.empty_index, '__input__'] or force:
            field = self.unbound_field.bind(
                form=None,
                name="%s-%s" % (self.name, idx),
                prefix=self._prefix,
                id="%s-%s" % (self.id, idx),
            )
            return field
        return None


setattr(fields,  DynamicFieldList.__name__,  DynamicFieldList)

## Let's report about broken plugins
open(os.path.join(CFG_LOGDIR, 'broken-deposition-fields.log'), 'w').write(
    pformat(CFG_FIELDS.get_broken_plugins()))
