# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

"""
BibCatalog utility functions
"""
from invenio.legacy.bibrecord import \
    record_get_field_instances, \
    field_get_subfield_values
from invenio.legacy.bibformat.dblayer import get_tag_from_name


class BibCatalogTagNotFound(Exception):
    pass


def record_in_collection(record, collection):
    """
    Returns True/False if given record is in a given collection (980__a).
    """
    for collection_tag in record_get_field_instances(record, "980"):
        for coll in field_get_subfield_values(collection_tag, 'a'):
            if coll.lower() == collection.lower():
                return True
    return False


def record_id_from_record(record):
    """
    Given a BibRecord object, returns the record id.
    """
    if "001" in record:
        return record['001'][0][3]


def record_get_value_with_provenence(record, provenence_value, provenence_code,
                                     tag, ind1=" ", ind2=" ", code=""):
    """
    Retrieves the value of the given field(s) with given provenence code/value
    combo.

    For example:

    If one would like to extract all subject categories (65017 $a) with a given
    provenence, in this case "arXiv" in $9:

    65017 $ahep-ph$9arXiv
    65017 $ahep-th$9arXiv
    65017 $aMath$9INSPIRE

    this function would return ["hep-ph", "hep-th"]

    Returns a list of subfield values.
    """
    fields = record_get_field_instances(record, tag, ind1, ind2)
    final_values = []
    for subfields, dummy1, dummy2, dummy3, dummy4 in fields:
        for subfield_code, value in subfields:
            if subfield_code == provenence_code and value == provenence_value:
                # We have a hit. Stop to look for right value
                break
        else:
            # No hits.. continue to next field
            continue
        for subfield_code, value in subfields:
            if subfield_code == code:
                # This is the value we are looking for with the correct provenence
                final_values.append(value)
    return final_values


def split_tag_code(code):
    """
    Splits a tag code in the form of "035__a" into a dictionary with
    tag, indicators and subfield code separated.
    """
    while len(code) < 6:
        code += "%"
    return {"tag": code[:3],
            "ind1": code[3],
            "ind2": code[4],
            "code": code[5]}


def load_tag_code_from_name(name):
    """
    Uses BibFormat DB layer API to load a tag code (035__a) from its
    name (ext system ID). Raises an exception if name does not exist.
    """
    tag = get_tag_from_name(name)
    if not tag:
        raise BibCatalogTagNotFound("Tag not found for %s" % (name,))
    return tag
