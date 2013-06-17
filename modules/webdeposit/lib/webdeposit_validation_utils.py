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
Validation functions
"""

import re
from wtforms.validators import ValidationError, StopValidation, Regexp
from invenio.config import CFG_SITE_NAME


#
# General purpose validators
#
class RequiredIf(object):
    """
    Require field if value of another field is set to a certain value.
    """
    def __init__(self, other_field_name, values, message=None):
        self.other_field_name = other_field_name
        self.values = values
        self.message = message

    def __call__(self, form, field):
        try:
            other_field = getattr(form, self.other_field_name)
            other_val = other_field.data
            if other_val in self.values:
                if not field.data or isinstance(field.data, basestring) \
                   and not field.data.strip():
                    if self.message is None:
                        self.message = 'This field is required.'
                    field.errors[:] = []
                    raise StopValidation(self.message % {
                        'other_field': other_field.label.text,
                        'value': other_val
                    })
        except AttributeError:
            pass


#
# DOI-related validators
#
doi_syntax_validator = Regexp(
    "(^$|(doi:)?10\.\d+(.\d+)*/.*)",
    flags=re.I,
    message="The provided DOI is invalid - it should look similar to "
            "'10.1234/foo.bar'."
)

"""
DOI syntax validator
"""


class InvalidDOIPrefix(object):
    """
    Validates if DOI
    """
    def __init__(self, prefix='10.5072', message=None,
                 message_testing=None):
        """
        @param doi_prefix: DOI prefix, e.g. 10.5072
        """
        self.doi_prefix = prefix
        # Remove trailing slash
        if self.doi_prefix[-1] == '/':
            self.doi_prefix = self.doi_prefix[:-1]

        if not message_testing:
            self.message_testing = "The prefix 10.5072 is invalid. The prefix" \
                "is only used for testing purposes, and no DOIs with this " \
                "prefix are attached to any meaningful content."
        if not message:
            self.message = 'The prefix %(prefix)s is ' \
                'administered automatically by %(CFG_SITE_NAME)s.'

        ctx = dict(
            prefix=prefix,
            CFG_SITE_NAME=CFG_SITE_NAME
        )
        self.message = self.message % ctx
        self.message_testing = self.message_testing % ctx

    def __call__(self, form, field):
        value = field.data

        # Defined prefix
        if value:
            if value.startswith("%s/" % self.doi_prefix):
                raise ValidationError(self.message)

            # Testing name space
            if self.doi_prefix != "10.5072" and value.startswith("10.5072/"):
                raise ValidationError(self.message_testing)


class PreReservedDOI(object):
    """
    Validate that user did not edit pre-reserved DOI.
    """
    def __init__(self, field_name, message=None, prefix='10.5072'):
        self.field_name = field_name
        self.message = message or 'You are not allowed to edit a ' \
                                  'pre-reserved DOI. Click the Pre-reserve ' \
                                  'DOI button to resolve the problem.'
        self.prefix = prefix

    def __call__(self, form, field):
        attr_value = getattr(form, self.field_name).data
        if attr_value and field.data and field.data != attr_value and field.data.startswith("%s/" % self.prefix):
            raise StopValidation(self.message)
        # Stop further validation if DOI equals pre-reserved DOI.
        if attr_value and field.data and field.data == attr_value:
            raise StopValidation()


#
# Aliases
#
required_if = RequiredIf
invalid_doi_prefix_validator = InvalidDOIPrefix
pre_reserved_doi_validator = PreReservedDOI


def number_validate(form, field, submit=False, error_message='It must be a number!'):
    value = field.data or ''
    if value == "" or value.isspace():
        return

    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    if not is_number(value):
        try:
            field.errors.append(error_message)
        except AttributeError:
            field.errors = list(field.process_errors)
            field.errors.append(error_message)
        field.add_message('error', error_message)
        return
