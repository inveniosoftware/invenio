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


def check_field_existence(record, field, min_value, max_value=None, subfield=None, continuable=True):
    """
    Checks field.subfield existence inside the record according to max and min values

    @param record: BibFieldDict where the record is stored
    @param field: Main json ID or field name to make test on
    @param min_value: Minimum number of occurrences of field.
    If max_value is not present then min_value represents the fix number of times that
    field should be present.
    @param max_value: Maximum number of occurrences of a field, this might be a fix number
    or "n".
    @param subfield: If this parameter is present, instead of applying the checker
    to the field, it is applied to record['field.subfield']

    @note: This checker also modify the record if the field is not repeatable,
    meaning that min_value=1 or min_value=0,max_value=1
    """
    from invenio.bibfield_utils import InvenioBibFieldContinuableError, \
                                       InvenioBibFieldError

    error = continuable and InvenioBibFieldContinuableError or InvenioBibFieldError

    field = '[n]' in field and field[:-3] or field
    key = subfield and "%s.%s" % (field, subfield) or field

    if min_value == 0:  # (0,1), (0,'n'), (0,n)
        if not max_value:
            raise error("Minimun value = 0 and no max value for '%s'" % (key,))
        if key in record:
            value = record[key]
            if max_value == 1 and isinstance(value, list) and len(value) != 1:
                raise error("Field '%s' is not repeatable" % (key,))
            elif max_value != 'n':
                if isinstance(value, list) and len(value) > max_value:
                    raise error("Field '%s' is repeatable only %s times" % (key, max_value))
    elif min_value == 1:  # (1,-) (1,'n'), (1, n)
        if not key in record:
            raise error("Field '%s' is mandatory" % (key,))
        value = record[key]
        if not value:
            raise error("Field '%s' is mandatory" % (key,))
        if not max_value:
            if isinstance(value, list) and len(value) != 1:
                raise error("Field '%s' is mandatory and not repeatable" % (key,))
        elif max_value != 'n':
            if isinstance(value, list) and len(value) > max_value:
                raise error("Field '%s' is mandatory and repeatable only %s times" % (key, max_value))
    else:
        if not key in record:
            raise error("Field '%s' must be present inside the record %s times" % (key, min_value))
        value = record[key]
        if not value:
            raise error("Field '%s' must be present inside the record %s times" % (key, min_value))
        if not max_value:
            if not isinstance(value, list) or len(value) != min_value:
                raise error("Field '%s' must be present inside the record %s times" % (key, min_value))
        else:
            if max_value != 'n' and (not isinstance(value, list) or len(value) < min_value or len(value) > max_value):
                raise error("Field '%s' must be present inside the record between %s and %s times" % (key, min_value, max_value))
            elif not isinstance(value, list) or len(value) < min_value:
                raise error("Field '%s' must be present inside the record between %s and 'n' times" % (key, min_value))
