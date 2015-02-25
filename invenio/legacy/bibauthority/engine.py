# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

# pylint: disable=C0103
"""Invenio BibAuthority Engine."""
from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD, \
    CFG_BIBAUTHORITY_AUTHORITY_SUBFIELDS_TO_INDEX,\
    CFG_BIBAUTHORITY_PREFIX_SEP

import re
from invenio.ext.logging import register_exception
from invenio.legacy.search_engine import search_pattern, \
    record_exists
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.bibauthority.config import \
    CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_IDENTIFIER

def is_authority_record(recID):
    """
    returns whether recID is an authority record

    @param recID: the record id to check
    @type recID: int

    @return: True or False
    """
    # low-level: don't use possibly indexed logical fields !
    return recID in search_pattern(p='980__a:AUTHORITY')

def get_dependent_records_for_control_no(control_no):
    """
    returns a list of recIDs that refer to an authority record containing
    the given control_no.
    E.g. if an authority record has the control number
    "AUTHOR:(CERN)aaa0005" in its '035__a' subfield, then this function will return all
    recIDs of records that contain any 'XXX__0' subfield
    containing "AUTHOR:(CERN)aaa0005"

    @param control_no: the control number for an authority record
    @type control_no: string

    @return: list of recIDs
    """
    # We don't want to return the recID who's control number is control_no
    myRecIDs = _get_low_level_recIDs_intbitset_from_control_no(control_no)
    # Use search_pattern, since we want to find records from both bibliographic
    # as well as authority record collections
    return list(search_pattern(p='"' + control_no+'"') - myRecIDs)

def get_dependent_records_for_recID(recID):
    """
    returns a list of recIDs that refer to an authority record containing
    the given record ID.

    'type' is a string (e.g. "AUTHOR") referring to the type of authority record

    @param recID: the record ID for the authority record
    @type recID: int

    @return: list of recIDs
    """
    recIDs = []

    # get the control numbers
    control_nos = get_control_nos_from_recID(recID)
    for control_no in control_nos:
        recIDs.extend(get_dependent_records_for_control_no(control_no))

    return recIDs

def guess_authority_types(recID):
    """
    guesses the type(s) (e.g. AUTHOR, INSTITUTE, etc.)
    of an authority record (should only have one value)

    @param recID: the record ID of the authority record
    @type recID: int

    @return: list of strings
    """
    types = get_fieldvalues(recID,
                            '980__a',
                            repetitive_values=False) # remove possible duplicates !

    #filter out unwanted information
    while CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_IDENTIFIER in types:
        types.remove(CFG_BIBAUTHORITY_AUTHORITY_COLLECTION_IDENTIFIER)
    types = [_type for _type in types if _type.isalpha()]

    return types

def get_low_level_recIDs_from_control_no(control_no):
    """
    returns the list of EXISTING record ID(s) of the authority records
    corresponding to the given (INVENIO) MARC control_no
    (e.g. 'AUTHOR:(XYZ)abc123')
    (NB: the list should normally contain exactly 1 element)

    @param control_no: a (INVENIO) MARC internal control_no to an authority record
    @type control_no: string

    @return:: list containing the record ID(s) of the referenced authority record
        (should be only one)
    """
    # values returned
#    recIDs = []
    #check for correct format for control_no
#    control_no = ""
#    if CFG_BIBAUTHORITY_PREFIX_SEP in control_no:
#        auth_prefix, control_no = control_no.split(CFG_BIBAUTHORITY_PREFIX_SEP);
#        #enforce expected enforced_type if present
#        if (enforced_type is None) or (auth_prefix == enforced_type):
#            #low-level search needed e.g. for bibindex
#            hitlist = search_pattern(p='980__a:' + auth_prefix)
#            hitlist &= _get_low_level_recIDs_intbitset_from_control_no(control_no)
#            recIDs = list(hitlist)

    recIDs = list(_get_low_level_recIDs_intbitset_from_control_no(control_no))

    # filter out "DELETED" recIDs
    recIDs = [recID for recID in recIDs if record_exists(recID) > 0]

    # normally there should be exactly 1 authority record per control_number
    _assert_unique_control_no(recIDs, control_no)

    # return
    return recIDs

#def get_low_level_recIDs_from_control_no(control_no):
#    """
#    Wrapper function for _get_low_level_recIDs_intbitset_from_control_no()
#    Returns a list of EXISTING record IDs with control_no
#
#    @param control_no: an (INVENIO) MARC internal control number to an authority record
#    @type control_no: string
#
#    @return: list (in stead of an intbitset)
#    """
#    #low-level search needed e.g. for bibindex
#    recIDs = list(_get_low_level_recIDs_intbitset_from_control_no(control_no))
#
#    # filter out "DELETED" recIDs
#    recIDs = [recID for recID in recIDs if record_exists(recID) > 0]
#
#    # normally there should be exactly 1 authority record per control_number
#    _assert_unique_control_no(recIDs, control_no)
#
#    # return
#    return recIDs

def _get_low_level_recIDs_intbitset_from_control_no(control_no):
    """
    returns the intbitset hitlist of ALL record ID(s) of the authority records
    corresponding to the given (INVENIO) MARC control number
    (e.g. '(XYZ)abc123'), (e.g. from the 035 field) of the authority record.

    Note: This function does not filter out DELETED records!!! The caller
    to this function must do this himself.

    @param control_no: an (INVENIO) MARC internal control number to an authority record
    @type control_no: string

    @return:: intbitset containing the record ID(s) of the referenced authority record
        (should be only one)
    """
    #low-level search needed e.g. for bibindex
    hitlist = search_pattern(
        p=CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD + ":" +
        '"' + control_no + '"')

    # return
    return hitlist

def _assert_unique_control_no(recIDs, control_no):
    """
    If there are more than one EXISTING recIDs with control_no, log a warning

    @param recIDs: list of record IDs with control_no
    @type recIDs: list of int

    @param control_no: the control number of the authority record in question
    @type control_no: string
    """

    if len(recIDs) > 1:
        error_message = \
            "DB inconsistency: multiple rec_ids " + \
            "(" + ", ".join([str(recID) for recID in recIDs]) + ") " + \
            "found for authority record control number: " + control_no
        try:
            raise Exception
        except:
            register_exception(prefix=error_message,
                               alert_admin=True,
                               subject=error_message)

def get_control_nos_from_recID(recID):
    """
    get a list of control numbers from the record ID

    @param recID: record ID
    @type recID: int

    @return: authority record control number
    """
    return get_fieldvalues(recID, CFG_BIBAUTHORITY_RECORD_CONTROL_NUMBER_FIELD,
                           repetitive_values=False)

def get_type_from_control_no(control_no):
    """simply returns the authority record TYPE prefix contained in
    control_no or else an empty string.

    @param control_no: e.g. "AUTHOR:(CERN)abc123"
    @type control_no: string

    @return: e.g. "AUTHOR" or ""
    """

    # pattern: any string, followed by the prefix, followed by a parenthesis
    pattern = \
        r'.*' + \
        r'(?=' + re.escape(CFG_BIBAUTHORITY_PREFIX_SEP) + re.escape('(') + r')'
    m = re.match(pattern, control_no)
    return m and m.group(0) or ''

def guess_main_name_from_authority_recID(recID):
    """
    get the main name of the authority record

    @param recID: the record ID of authority record
    @type recID: int

    @return: the main name of this authority record (string)
    """
    #tags where the main authority record name can be found
    main_name_tags = ['100__a', '110__a', '130__a', '150__a']
    main_name = ''
    # look for first match only
    for tag in main_name_tags:
        fieldvalues = get_fieldvalues(recID, tag, repetitive_values=False)
        if len(fieldvalues):
            main_name = fieldvalues[0]
            break
    # return first match, if found
    return main_name

def get_index_strings_by_control_no(control_no):
    """extracts the index-relevant strings from the authority record referenced by
    the 'control_no' parameter and returns it as a list of strings

    @param control_no: a (INVENIO) MARC internal control_no to an authority record
    @type control_no: string (e.g. 'author:(ABC)1234')

    @param expected_type: the type of authority record expected
    @type expected_type: string, e.g. 'author', 'journal' etc.

    @return: list of index-relevant strings from the referenced authority record

    """

    from invenio.legacy.bibindex.engine import list_union

    #return value
    string_list = []
    #1. get recID and authority type corresponding to control_no
    rec_IDs = get_low_level_recIDs_from_control_no(control_no)
    #2. concatenate and return all the info from the interesting fields for this record
    for rec_id in rec_IDs: # in case we get multiple authority records
        for tag in CFG_BIBAUTHORITY_AUTHORITY_SUBFIELDS_TO_INDEX.get(get_type_from_control_no(control_no)):
            new_strings = get_fieldvalues(rec_id, tag)
            string_list = list_union(new_strings, string_list)
    #return
    return string_list
