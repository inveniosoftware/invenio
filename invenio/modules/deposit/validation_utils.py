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

"""Validation functions."""

import re

from flask import current_app

from invenio.utils import persistentid as pidutils

import six

from wtforms.validators import StopValidation, ValidationError


#
# General purpose validators
#
class ListLength(object):

    """Require number of elements.

    :param min_num: Minimum number of elements.
    :param max_num: Maximum number of elements.
    :param element_filter: Callable used to filter the list prior to testing
        the number of elements. Useful to remove empty elements.
    """
    def __init__(self, min_num=None, max_num=None,
                 element_filter=lambda x: True):
        self.min = min_num
        self.max = max_num
        self.element_filter = element_filter

    def __call__(self, form, field):
        test_list = []
        if self.min or self.max:
            test_list = filter(self.element_filter, field.data)

        if self.min:
            if self.min > len(test_list):
                raise ValidationError(
                    "Minimum %s %s required." % (
                        self.min,
                        "entry is" if self.min == 1 else "entries are"
                    )
                )
        if self.max:
            if self.max < len(test_list):
                raise ValidationError(
                    "Maximum %s %s allowed." % (
                        self.max,
                        "entry is" if self.max == 1 else "entries are"
                    )
                )


class RequiredIf(object):

    """Require field if value of another field is set to a certain value."""

    def __init__(self, other_field_name, values, message=None):
        self.other_field_name = other_field_name
        self.values = values
        self.message = message

    def __call__(self, form, field):
        try:
            other_field = getattr(form, self.other_field_name)
            other_val = other_field.data
            for v in self.values:
                # Check if field value is required
                if (callable(v) and v(other_val)) or (other_val == v):
                    # Field value is required - check the value
                    if not field.data or \
                            isinstance(field.data, six.string_types) \
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


class NotRequiredIf(RequiredIf):

    """Do not require field if another field contains a certain value."""

    def __call__(self, form, field):
        try:
            other_field = getattr(form, self.other_field_name)
            other_val = other_field.data
            for v in self.values:
                # Check if field value is not required.
                if (callable(v) and v(other_val)) or (other_val == v):
                    raise StopValidation()
        except AttributeError:
            pass


class Unchangeable(object):
    def __call__(self, form, field):
        field.data = field.object_data


def number_validate(form, field, submit=False,
                    error_message='It must be a number!'):
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
        raise ValidationError(error_message)

#
# DOI-related validators
#


def doi_syntax_validator(form, field):
    """DOI syntax validator. Deprecated.

    :param field: validated field.
    :param form: validated form.
    """
    import warnings
    warnings.warn("Please use DOISyntaxValidator instead.", DeprecationWarning)
    return DOISyntaxValidator()(form, field)


class DOISyntaxValidator(object):

    """DOI syntax validator."""

    pattern = "(^$|(doi:)?10\.\d+(.\d+)*/.*)"

    def __init__(self, message=None):
        """Constructor.

        :param message: message to override the default one.
        """
        self.regexp = re.compile(self.pattern, re.I)
        self.message = message if message else (
            "The provided DOI is invalid - it should look similar to "
            "'10.1234/foo.bar'.")

    def __call__(self, form, field):
        """Validate.

        :param field: validated field.
        :param form: validated form.
        """
        doi = field.data
        if doi and not self.regexp.match(doi):
            # no point to further validate DOI which is invalid
            raise StopValidation(self.message)


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
            CFG_SITE_NAME=current_app.config['CFG_SITE_NAME']
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


class MintedDOIValidator(object):
    """
    Validates if DOI
    """
    def __init__(self, prefix='10.5072', message=None):
        """
        @param doi_prefix: DOI prefix, e.g. 10.5072
        """
        self.doi_prefix = prefix
        # Remove trailing slash
        if self.doi_prefix[-1] == '/':
            self.doi_prefix = self.doi_prefix[:-1]

        if not message:
            self.message = 'You cannot change an already registered DOI.'

        ctx = dict(
            prefix=prefix,
            CFG_SITE_NAME=current_app.config['CFG_SITE_NAME']
        )
        self.message = self.message % ctx

    def __call__(self, form, field):
        if field.object_data and \
           field.object_data.startswith("%s/" % self.doi_prefix):
            # We have a DOI and it's our own DOI.
            if field.data != field.object_data:
                raise ValidationError(self.message)
            else:
                raise StopValidation()
        else:
            raise ValidationError(self.message)


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
        if isinstance(attr_value, dict):
            attr_value = attr_value['doi']
        if attr_value and field.data and field.data != attr_value \
           and field.data.startswith("%s/" % self.prefix):
            raise StopValidation(self.message)
        # Stop further validation if DOI equals pre-reserved DOI.
        if attr_value and field.data and field.data == attr_value:
            raise StopValidation()


class PidValidator(object):
    """
    Validate that value is a persistent identifier understood by us.
    """
    def __init__(self, message=None):
        self.message = message or "Not a valid persistent identifier"

    def __call__(self, form, field):
        schemes = pidutils.detect_identifier_schemes(field.data)
        if not schemes:
            raise ValidationError(self.message)


#
# Aliases
#
required_if = RequiredIf
not_required_if = NotRequiredIf
unchangeable = Unchangeable
list_length = ListLength
invalid_doi_prefix_validator = InvalidDOIPrefix
minted_doi_validator = MintedDOIValidator
pre_reserved_doi_validator = PreReservedDOI
pid_validator = PidValidator
