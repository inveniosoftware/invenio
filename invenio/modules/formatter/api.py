# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2015 CERN.
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

"""Formatter API."""

import zlib

from sqlalchemy.exc import SQLAlchemyError

from invenio.ext.sqlalchemy import db
from invenio.modules.records.models import Record as Bibrec
from invenio.modules.search.models import Tag
from invenio.utils.date import convert_datetime_to_utc_string, strftime

from . import registry
from .models import Bibfmt


def get_creation_date(sysno, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    Returns the creation date of the record 'sysno'.

    :param sysno: the record ID for which we want to retrieve creation date
    :param fmt: output format for the returned date
    :return: creation date of the record
    :rtype: string
    """
    try:
        return convert_datetime_to_utc_string(
            Bibrec.query.get(sysno).creation_date, fmt)

    except SQLAlchemyError:
        return ""


def get_modification_date(sysno, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    Returns the date of last modification for the record 'sysno'.

    :param sysno: the record ID for which we want to retrieve modification date
    :param fmt: output format for the returned date
    :return: modification date of the record
    :rtype: string
    """
    try:
        return convert_datetime_to_utc_string(
            Bibrec.query.get(sysno).modification_date, fmt)

    except SQLAlchemyError:
        return ""


# XML Marc related functions
def get_tag_from_name(name):
    """
    Returns the marc code corresponding the given name

    :param name: name for which we want to retrieve the tag
    :return: a tag corresponding to X{name} or None if not found
    """
    try:
        return Tag.query.filter(Tag.name.like(name)).one().value

    except SQLAlchemyError:
        return None


def get_tags_from_name(name):
    """
    Returns the marc codes corresponding the given name,
    ordered by value

    :param name: name for which we want to retrieve the tags
    :return: list of tags corresponding to X{name} or None if not found
    """
    try:
        return [tag.value for tag in
                Tag.query.filter(Tag.name.like(name))
                .order_by(Tag.value).all()]

    except SQLAlchemyError:
        return None


def tag_exists_for_name(name):
    """
    Returns True if a tag exists for name in 'tag' table.

    :param name: name for which we want to check if a tag exist
    :return: True if a tag exist for X{name} or False
    """
    return (Tag.query.filter(Tag.name.like(name)).count() > 0)


def get_name_from_tag(tag):
    """
    Returns the name corresponding to a marc code

    :param tag: tag to consider
    :return: a name corresponding to X{tag}
    """
    try:
        return Tag.query.filter(Tag.value.like(tag)).one().name

    except SQLAlchemyError:
        return None


def name_exists_for_tag(tag):
    """
    Returns True if a name exists for tag in 'tag' table.

    :param tag: tag for which we want to check if a name exist
    :return: True if a name exist for X{tag} or False
    """
    return (Tag.query.filter(Tag.value.like(tag)).count() > 0)


def get_all_name_tag_mappings():
    """
    Return the list of mappings name<->tag from 'tag' table.

    The returned object is a dict with name as key (if 2 names are the same
    we will take the value of one of them, as we cannot make the difference
    in format templates)

    :return: a dict containing list of mapping in 'tag' table
    """
    result = dict()

    for tag in Tag.query.all():
        result[tag.name] = tag.value

    return result


# Output formats related functions
def get_format_by_code(code):
    """
    Returns the output format object given by code in the database.

    Output formats are located inside 'format' table

    :param code: the code of an output format
    :return: Format object with given ID. None if not found
    """
    f_code = code
    if len(code) > 6:
        f_code = code[:6]
    return registry.output_formats.get(f_code.lower(), {})


def get_format_property(code, property_name, default_value=None):
    """
    Returns the value of a property of the output format given by code.

    If code or property does not exist, return default_value

    :param code: the code of the output format to get the value from
    :param property_name: name of property to return
    :param default_value: value to be returned if format not found
    :return: output format property value
    """
    return get_format_by_code(code).get(property_name, default_value)


def get_output_format_description(code):
    """
    Returns the description of the output format given by code

    If code or description does not exist, return empty string

    :param code: the code of the output format to get the description from
    :return: output format description
    """
    return get_format_property(code, 'description', '')


def get_output_format_visibility(code):
    """
    Returns the visibility of the output format, given by its code

    If code does not exist, return 0

    :param code: the code of an output format
    :return: output format visibility (0 if not visible, 1 if visible
    """
    visibility = get_format_property(code, 'visibility', 0)

    if visibility is not None and int(visibility) in range(0, 2):
        return int(visibility)
    else:
        return 0


def get_output_format_content_type(code):
    """
    Returns the content_type of the output format given by code

    If code or content_type does not exist, return empty string

    :param code: the code of the output format to get the description from
    :return: output format content_type
    """
    return get_format_property(code, 'content_type', '') or ''


def get_preformatted_record(recID, of, decompress=zlib.decompress):
    """
    Returns the preformatted record with id 'recID' and format 'of'

    If corresponding record does not exist for given output format,
    returns None

    :param recID: the id of the record to fetch
    :param of: the output format code
    :param decompress: the method used to decompress
        the preformatted record in database
    :return: formatted record as String, or None if not exist
    """
    try:
        value = Bibfmt.query\
            .filter(Bibfmt.id_bibrec == recID)\
            .filter(Bibfmt.format == of)\
            .one().value

        return str(decompress(value))

    except SQLAlchemyError:
        return None


def get_preformatted_record_date(recID, of):
    """
    Returns the date of the last update of the cache for the considered
    preformatted record in bibfmt

    If corresponding record does not exist for given output format,
    returns None

    :param recID: the id of the record to fetch
    :param of: the output format code
    :return: the date of the last update of the cache, or None if not exist
    """
    try:
        last_updated = Bibfmt.query\
            .filter(Bibfmt.id_bibrec == recID)\
            .filter(Bibfmt.format == of)\
            .one().last_updated

        return strftime("%Y-%m-%d %H:%M:%S", last_updated)

    except SQLAlchemyError:
        return None
