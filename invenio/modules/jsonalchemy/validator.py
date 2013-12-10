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
    invenio.modules.jsonalchemy.validator
    -------------------------------------

    See http://cerberus.readthedocs.org/en/latest
"""

from cerberus import Validator as ValidatorBase
from cerberus import ValidationError, SchemaError
from cerberus import errors

from .reader import FieldParser, ModelParser


class Validator(ValidatorBase):
    """

    """

    def __init__(self, schema=None, transparent_schema_rules=True,
                 ignore_none_values=False, allow_unknown=True):
       super(Validator, self).__init__(schema, transparent_schema_rules,
               ignore_none_values, allow_unknown)

    def _validate(self, document, schema=None, update=False):
        self._errors = {}
        self.update = update

        if schema is not None:
            self.schema = schema
        elif self.schema is None:
            raise SchemaError(errors.ERROR_SCHEMA_MISSING)
        if not isinstance(self.schema, dict):
            raise SchemaError(errors.ERROR_SCHEMA_FORMAT % str(self.schema))

        if document is None:
            raise ValidationError(errors.ERROR_DOCUMENT_MISSING)
        if not hasattr(document, 'get'):
            raise ValidationError(errors.ERROR_DOCUMENT_FORMAT % str(document))
        self.document = document

        special_rules = ["required", "nullable", "type"]
        for field, value in self.document.items():

            if self.ignore_none_values and value is None:
                continue

            definition = self.schema.get(field)
            if definition:
                if isinstance(definition, dict):

                    if definition.get("nullable", False) == True \
                       and value is None:  # noqa
                        continue

                    if 'type' in definition:
                        self._validate_type(definition['type'], field, value)
                        if self.errors:
                            continue

                    definition_rules = [rule for rule in definition.keys()
                                        if rule not in special_rules]
                    for rule in definition_rules:
                        validatorname = "_validate_" + rule.replace(" ", "_")
                        validator = getattr(self, validatorname, None)
                        if validator:
                            validator(definition[rule], field, value)
                        elif not self.transparent_schema_rules:
                            raise SchemaError(errors.ERROR_UNKNOWN_RULE %
                                              (rule, field))
                else:
                    raise SchemaError(errors.ERROR_DEFINITION_FORMAT % field)

            else:
                if not self.allow_unknown:
                    self._error(field, errors.ERROR_UNKNOWN_FIELD)

        if not self.update:
            self._validate_required_fields()

        return len(self._errors) == 0

    def _validate_type_objectid(self, field, value):
       """ 
       Enables validation for `objectid` schema attribute.

       :param field: field name.
       :param value: field value.
       """
       if not re.match('[a-f0-9]{24}', value):
           self._error(field, ERROR_BAD_TYPE % 'ObjectId')
