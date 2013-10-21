# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
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


def check_field_type(record, field, field_type, subfield=None, continuable=True):
    """
    Checks if record[field.subfield] is of type "field_type"

    @note: If record[field.subfield] is a list or a dictionary then it checks
    every single element inside is type is a "system type"

    @param record: BibFieldDict where the record is stored
    @param field: Main json ID or field name to make test on
    @param field_type: Field_Type defined by the user inside bibfield_types or a system type
    i.e.: "datetime.datetime"
    @param subfield: If this parameter is present, instead of applying the checker
    to the field, it is applied to record['field.subfield']

    """
    field = '[n]' in field and field[:-3] or field
    key = subfield and "%s.%s" % (field, subfield) or field
    if not key in record:
        return

    import os
    from invenio.config import CFG_PYLIBDIR
    from invenio.pluginutils import PluginContainer
    CFG_BIBFIELD_TYPES = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibfield_functions', 'is_type_*.py'))

    from invenio.bibfield_utils import InvenioBibFieldContinuableError, \
                                       InvenioBibFieldError

    error = continuable and InvenioBibFieldContinuableError or InvenioBibFieldError

    new_type = 'is_type_%s' % (field_type, )

    if new_type in CFG_BIBFIELD_TYPES:
        globals()[new_type] = CFG_BIBFIELD_TYPES[new_type]
        if not eval('%s(record[key])' % (new_type,)):
            raise error("Field %s should be of type '%s'" % (key, field_type))
    else:
        if not check_field_sys_type(record[key], field_type):
            raise error("Field %s should be of type '%s'" % (key, field_type))


def check_field_sys_type(value, field_type):
    """
    Helper function to check if value is of field_type
    """
    if isinstance(value, list):
        for element in value:
            if not check_field_sys_type(element, field_type):
                return False
    elif isinstance(value, dict):
        for element in value.itervalues():
            if not check_field_sys_type(element, field_type):
                return False
    elif value:
        new_type = field_type.split('.')[0]
        globals()[new_type] = __import__(new_type)
        if not isinstance(value, eval(field_type)):
            return False
    return True
