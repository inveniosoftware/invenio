# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibRecord - XML MARC processing library for CDS Invenio.

For API, see create_record(), record_get_field_instances() and friends
in the source code of this file in the section entitled INTERFACE.

Note: Does not access the database, the input is MARCXML only.
"""

__revision__ = "$Id$"

### IMPORT INTERESTING MODULES AND XML PARSERS

import re, sys
try:
    import psyco
    psycho_available  = 1
except ImportError:
    psycho_available = 0

from invenio.bibrecord_config import CFG_MARC21_DTD, \
                                     CFG_BIBRECORD_WARNING_MSGS, \
                                     CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL, \
                                     CFG_BIBRECORD_DEFAULT_CORRECT, \
                                     CFG_BIBRECORD_PARSERS_AVAILABLE
from invenio.config import CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG
from invenio.textutils import encode_for_xml
# find out about the best usable parser:
err = []
parser = -1
pyrxp_parser = None # pyRXP parser instance
if 2 in CFG_BIBRECORD_PARSERS_AVAILABLE:
    try:
        import pyRXP
        parser = 2
        def warnCB(s):
            """ function used to treat the PyRXP parser warnings"""
            global err
            err.append((0, 'Parse warning:\n'+s))

        pyrxp_parser = pyRXP.Parser(ErrorOnValidityErrors=0,
                                    ProcessDTD=1,
                                    ErrorOnUnquotedAttributeValues=0,
                                    warnCB = warnCB,
                                    srcName='string input')
    except ImportError:
        pass
if parser == -1 and \
       1 in CFG_BIBRECORD_PARSERS_AVAILABLE:
    try:
        from Ft.Xml.Domlette import NonvalidatingReader
        parser = 1
    except ImportError:
        pass
if parser == -1 and \
       0 in CFG_BIBRECORD_PARSERS_AVAILABLE:
    try:
        from xml.dom.minidom import parseString
        parser = 0
    except ImportError:
        pass

### INTERFACE / VISIBLE FUNCTIONS

def create_records(xmltext,
                   verbose=CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL,
                   correct=CFG_BIBRECORD_DEFAULT_CORRECT,
                   force_parser=None):
    """
    Create list of record from XMLTEXT.  Return a list of objects
    initiated by create_record() function; please see that function's
    docstring.
    """
    global parser, err
    err = []

    if parser == -1:
        err.append((6, "import error"))
    else:
        pat = r"<record.*?>.*?</record>"
        p = re.compile(pat, re.DOTALL) # DOTALL - to ignore whitespaces
        alist = p.findall(xmltext)

        listofrec = map((lambda x:create_record(x, verbose, correct,
            force_parser)), alist)
        return listofrec
    return []

# Record :: {tag : [Field]}
# Field :: (Subfields,ind1,ind2,value)
# Subfields :: [(code,value)]

def create_record(xmltext,
                  verbose=CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL,
                  correct=CFG_BIBRECORD_DEFAULT_CORRECT,
                  force_parser=None):
    """
    Create a record object from XMLTEXT and return it.

    Uses pyRXP if installed else uses 4Suite domlette or xml.dom.minidom.

    The returned object is a tuple (record, status_code, list_of_errors), where
    status_code is 0 when there are errors, 1 when no errors.

    The return record structure is as follows:
    Record := {tag : [Field]}
    Field := (Subfields, ind1, ind2, value)
    Subfields := [(code, value)]

    For example:
                                   ______
                                  |record|
                                   ------
           __________________________|____________________________________________
           |record['001']                |record['909']           |record['520']  |
           |                             |                        |               |
    [list of fields]                [list of fields]       [list of fields]      ...
           |                       ______|______________          |
           |[0]                   |[0]          |[1]    |         |[0]
        ___|_____            _____|___       ___|_____ ...    ____|____
       |Field 001|          |Field 909|     |Field 909|      |Field 520|
        ---------            ---------       ---------        ---------
         |     __________________|______________    |             |
        ...   |[0]            |[1]    |[2]      |  ...           ...
              |               |       |         |
        [list of subfields]  'C'     '4'
           ___|_______________________________________________
           |                     |                            |
    ('a', 'a value')  ('b', 'value for subfield b')     ('a', 'another value for another a')

    @param xmltext an XML string representation of the record to create
    @param verbose the level of verbosity: 0(silent) 1-2 (warnings) 3(strict:stop when errors)
    @param correct 1 to enable correction of xmltext syntax. Else 0.
    @return a tuple (record, status_code, list_of_errors), where status_code is 0 where there are errors, 1 when no errors
    """
    global parser, err

    if not force_parser:
        # If the parser is not specified, use the best parser available.
        force_parser = parser

    try:
        if force_parser == 2:
            ## the following is because of DTD validation
            if correct:
                ## Note that with pyRXP < 1.13 a memory leak
                ## has been found involving DTD parsing.
                ## So enable correction only if you have
                ## pyRXP 1.13 or greater.
                t = """<?xml version="1.0" encoding="UTF-8"?>
                <!DOCTYPE collection SYSTEM "file://%s">
                <collection>\n""" % CFG_MARC21_DTD
                t += str(xmltext)
                t += "</collection>"
                xmltext = t
            (rec, er) = create_record_RXP(xmltext, verbose, correct)
        elif force_parser == 1:
            (rec, er) = create_record_4suite(xmltext, verbose, correct)
        elif force_parser == 0:
            (rec, er) = create_record_minidom(xmltext, verbose, correct)
        else:
            (rec, er) = (None, "ERROR: No usable XML parsers found.")
        errs = warnings(er)
        err = []
    except Exception, e:
        sys.stderr.write("%s" % e)
        sys.stderr.flush()
        errs = warnings(concat(err))
        err = []
        return (None, 0, errs)

    if errs == []:
        return (rec, 1, errs)
    else:
        return (rec, 0, errs)

def record_get_field_instances(rec, tag="", ind1="", ind2=""):
    """
    Returns the list of field instances for the specified tag and indicators
    of the record (rec).

    Returns empty list if not found.
    If tag is empty string, returns all fields

    Parameters (tag, ind1, ind2) can contain wildcard %.

    @param rec a record structure as returned by create_record()
    @param tag a 3 characters long string
    @param ind1 a 1 character long string
    @param ind2 a 1 character long string
    @param code a 1 character long string
    @return a list of field tuples (Subfields, ind1, ind2, value, field_number) where subfields is list of (code, value)
    """
    out = []

    (ind1, ind2) = wash_indicators(ind1, ind2)

    if tag:
        if '%' in tag:
            #Wildcard in tag. Check all possible
            for field_tag in rec.keys():
                if tag_matches_pattern(field_tag, tag):
                    for possible_field_instance in rec[field_tag]:
                        if (ind1 == '%' or possible_field_instance[1] == ind1) and \
                               (ind2 == '%' or possible_field_instance[2] == ind2):
                            out.append(possible_field_instance)
        else:
            #Completely defined tag. Use dict
            if record_has_field(rec, tag):
                for possible_field_instance in rec[tag]:
                    if (ind1 == '%' or possible_field_instance[1] == ind1) and \
                           (ind2 == '%' or possible_field_instance[2] == ind2):
                        out.append(possible_field_instance)
    else:
        return rec.items()
    return out

def record_has_field(rec, tag):
    """checks whether record 'rec' contains tag 'tag'"""
    return rec.has_key(tag)

def record_add_field(rec, tag, ind1=' ', ind2=' ',
                     controlfield_value="",
                     datafield_subfield_code_value_tuples=None,
                     desired_field_number=-1):
    """
    Add a new field TAG to record REC with the following values:

       In case of creating a controlfield, only one argument matters:

           controlfield_value - value of the control field, in case
                                this field is a controlfield.

       In case of creating a datafield, only these arguments matter:

           ind1, ind2 - indicators of the datafield

           datafield_subfield_code_value_tuples - list of subfield code and
             value tuples, e.g.: [('a', 'Ellis, J'), ('e', 'editor')]

       The new field will have a field number DESIRED_FIELD_NUMBER, if
       this one is positive and is not yet taken by some other already
       existing field; otherwise the new field will be added at the
       end of the record.

    Return the field number of newly created field.
    """
    if datafield_subfield_code_value_tuples is None:
        datafield_subfield_code_value_tuples = []
    (ind1, ind2) = wash_indicators(ind1, ind2)

    # detect field number to be used for insertion:
    existing_field_numbers = [len(fi)==5 and fi[4] or 0 for fis in rec.values() for fi in fis]
    if desired_field_number == -1 or desired_field_number in existing_field_numbers:
        try:
            newfield_number = 1 + max(existing_field_numbers)
        except ValueError:
            newfield_number = 1
    else:
        newfield_number = desired_field_number

    # create new field object:
    if controlfield_value:
        newfield = ([], ind1, ind2, str(controlfield_value), newfield_number)
    else:
        newfield = (datafield_subfield_code_value_tuples, ind1, ind2, "", newfield_number)

    # add it to the record structure:
    if rec.has_key(tag):
        rec[tag].append(newfield)
    else:
        rec[tag] = [newfield]

    # return new field number:
    return newfield_number

def record_delete_field(rec, tag, ind1=' ', ind2=' ', field_number=None):
    """
    Delete all/some fields defined with MARC tag 'tag' and indicators
    'ind1' and 'ind2' from record 'rec'. If 'field_number' is None,
    then delete all the field instances.  Otherwise delete only the
    field instance corresponding to given 'field_number'.
    """
    (ind1, ind2) = wash_indicators(ind1, ind2)

    newlist = []
    if rec.has_key(tag):
        if field_number is None:
            for field in rec[tag]:
                if not (field[1]==ind1 and field[2]==ind2):
                    newlist.append(field)
        else:
            for field in rec[tag]:
                if not (field[1]==ind1 and field[2]==ind2 and field[4]==field_number):
                    newlist.append(field)
        if newlist:
            rec[tag] = newlist
        else:
            del rec[tag]

def record_delete_field_from(rec, tag, field_number):
    """Delete field from position specified by tag and field number."""

    newlist = []
    if rec.has_key(tag):
        for field in rec[tag]:
            if not field[4]==field_number:
                newlist.append(field)
        if newlist:
            rec[tag] = newlist
        else:
            del rec[tag]

def record_delete_subfield(rec, tag, subfield, ind1=' ', ind2=' '):
    ind1, ind2 = wash_indicators(ind1, ind2)
    newlist = []
    if rec.has_key(tag):
        for field in rec[tag]:
            if (field[1] == ind1 and field[2] == ind2):
                newsublist = []
                for sf in field[0]:
                    if (sf[0] != subfield):
                        newsublist.append(sf)
                if newsublist != []:
                    newlist.append((newsublist, field[1], field[2], field[3], field[4]))
            else:
                newlist.append(field)
        rec[tag] = newlist

def record_delete_subfield_from(rec, tag, field_number, subfield_index):
    """Delete subfield from position specified by tag, field number and subfield index."""
    if rec.has_key(tag):
        for field in rec[tag]:
            if field[4] == field_number:
                try:
                    field[0].pop(subfield_index)
                except IndexError:
                    pass
                if not field[0]:
                    rec[tag].remove(field)
                    if not rec[tag]:
                        del rec[tag]

def record_add_or_modify_subfield(record, field, subfield, ind1, ind2, value):
    """
       Modifies ( if exists) or creates ( if does not exist) subfield of a given field of record.
       @param record record to be modified
       @param field field tag
       @subfield subfield tag
       @ind1
       @ind2
       @value : value to be added
    """
    ind1, ind2 = wash_indicators(ind1, ind2)
    if (record.has_key(field)):
        subfields = record_get_field_instances(rec = record, \
                                                     tag = field, \
                                                     ind1 = ind1, \
                                                     ind2 = ind2)[0][0]
        sfieldind = -1
        for ind in range(0,len(subfields)):
            if subfields[ind][0] == subfield:
                sfieldind = ind
                break

        if sfieldind == -1:
            subfields.append((subfield, value))
        else:
            subfields[sfieldind] = (subfield, value)
    else:
        record_add_field(rec = record, tag = field, \
                             ind1 = ind1, ind2 = ind2, \
                             datafield_subfield_code_value_tuples= \
                             [(subfield, value)])

def record_add_subfield(record, field, ind1, ind2, subfield, value):
    """
       Adds a subfield to given fiels

    """
    ind1, ind2 = wash_indicators(ind1, ind2)
    if (record.has_key(field)):
        record[field][0][0].append((subfield, value))
    else:
        record_add_field(rec = record, tag = field, \
                             ind1 = ind1, ind2 = ind2, \
                             datafield_subfield_code_value_tuples= \
                             [(subfield, value)])

def record_add_subfield_into(rec, tag, field_number, subfield, value,
                             subfield_index=None):
    """
    Add subfield into position specified by tag, field number and optionally by subfield index.
    """
    if rec.has_key(tag):
        for field in rec[tag]:
            if field[4] == field_number:
                if subfield_index is None:
                    field[0].append((subfield, value))
                else:
                    field[0].insert(subfield_index, (subfield, value))

def record_modify_controlfield(rec, tag, field_number, value):
    """Modify controlfield at position specified by tag and field number."""
    if int(tag) < 10 and rec.has_key(tag):
        for i in range(len(rec[tag])):
            if rec[tag][i][4] == field_number:
                rec[tag][i] = ([], " ", " ", value, rec[tag][i][4])

def record_modify_subfield(rec, tag, field_number, subfield, value,
                           subfield_index):
    """Modify subfield at position specified by tag, field number and subfield index."""
    if rec.has_key(tag):
        for field in rec[tag]:
            if field[4] == field_number:
                try:
                    field[0][subfield_index] = (subfield, value)
                except IndexError:
                    pass

def record_move_subfield(rec, tag, field_number, subfield_index, new_subfield_index):
    """Move subfield at position specified by tag, field number and subfield index to new subfield index."""
    if rec.has_key(tag):
        for field in rec[tag]:
            if field[4] == field_number:
                try:
                    subfield = field[0].pop(subfield_index)
                    field[0].insert(new_subfield_index, subfield)
                except IndexError:
                    pass

def record_does_field_exist(record, field, ind1, ind2):
    """
    Returns True if specified record exists and False otherwise
    """
    if record_get_field_instances(rec = record, \
                                      tag = field, \
                                      ind1 = ind1, \
                                      ind2 = ind2) == []:
        return False
    else:
        return True

def record_filter_fields(record, ffunction):
    """
        Produces a filtered sequence of fields from record
        @param record - record o be processed
        @param ffunction - predicate telling if a given field should
           be included in the sequence. Takes two arguments: field tag, field body
    """
    for fields in record:
        for field in record[fields]:
            if (ffunction(fields, field)):
                yield field


def record_replace_in_subfields(record, field, subfield, ind1, ind2, original, value):
    """
        Replaces specified string with another in a given subfields
        (Only if whole field is equal to selected pattern)
    """
    for r_field in record_filter_fields(record,lambda code, f: code == field and f[1]==ind1 and f[2] == ind2):
        subfields = []
        for subf in r_field[0]:
            if subf[0] == subfield and subf[1] == original:
                subfields.append((subf[0], value))
            else:
                subfields.append((subf[0], subf[1]))
        r_field[0][:] = subfields


def tag_matches_pattern(tag, pattern):
    """
    Returns true if MARC 'tag' matches a 'pattern'.

    'pattern' is plain text, with % as wildcard

    Both parameters must be 3 characters long strings.

    For e.g.
    >> tag_matches_pattern("909", "909") -> True
    >> tag_matches_pattern("909", "9%9") -> True
    >> tag_matches_pattern("909", "9%8") -> False

    @param tag a 3 characters long string
    @param pattern a 3 characters long string
    @return False or True
    """
    return (pattern[0] == '%' or tag[0] == pattern[0]) and \
           (pattern[1] == '%' or tag[1] == pattern[1]) and \
           (pattern[2] == '%' or tag[2] == pattern[2])

def record_get_field_value(rec, tag, ind1="", ind2="", code=""):
    """
    Returns first (string) value that matches specified field (tag, ind1, ind2, code)
    of the record (rec).

    Returns empty string if not found.

    Parameters (tag, ind1, ind2, code) can contain wildcard %.

    Difference between wildcard % and empty '':

    - Empty char specifies that we are not interested in a field which
      has one of the indicator(s)/subfield specified.

    - Wildcard specifies that we are interested in getting the value
      of the field whatever the indicator(s)/subfield is.

    For e.g. consider the following record in MARC:
      100C5  $$a val1
      555AB  $$a val2
      555AB      val3
      555    $$a val4
      555A       val5

      >> record_get_field_value(record, '555', 'A', '', '')
      >> "val5"
      >> record_get_field_value(record, '555', 'A', '%', '')
      >> "val3"
      >> record_get_field_value(record, '555', 'A', '%', '%')
      >> "val2"
      >> record_get_field_value(record, '555', 'A', 'B', '')
      >> "val3"
      >> record_get_field_value(record, '555', '', 'B', 'a')
      >> ""
      >> record_get_field_value(record, '555', '', '', 'a')
      >> "val4"
      >> record_get_field_value(record, '555', '', '', '')
      >> ""
      >> record_get_field_value(record, '%%%', '%', '%', '%')
      >> "val1"


    @param rec a record structure as returned by create_record()
    @param tag a 3 characters long string
    @param ind1 a 1 character long string
    @param ind2 a 1 character long string
    @param code a 1 character long string
    @return string value (empty if nothing found)
    """
    ## Note: the code is quite redundant for speed reasons (avoid calling
    ## functions or doing tests inside loops)

    (ind1, ind2) = wash_indicators(ind1, ind2)

    if '%' in tag:
        # Wild card in tag. Must find all corresponding fields
        # fields_for_tag = (rec[field_tag] for field_tag in rec.keys() if tag_matches_pattern(field_tag, tag))
        if code == '':
            # Code not specified.
            for field_tag in rec.keys():
                if tag_matches_pattern(field_tag, tag):
                    fields = rec[field_tag]
                    for field in fields:
                        if (ind1 == '%' or field[1] == ind1) and \
                               (ind2 == '%' or field[2] == ind2):
                            # Return matching field value if not empty
                            if field[3] != "":
                                return field[3]
        elif code == '%':
            # Code is wildcard. Take first subfield of first matching field
            for field_tag in rec.keys():
                if tag_matches_pattern(field_tag, tag):
                    fields = rec[field_tag]
                    for field in fields:
                        if (ind1 == '%' or field[1] == ind1) and \
                               (ind2 == '%' or field[2] == ind2) and \
                               (len(field[0]) > 0):
                            return field[0][0][1]
        else:
            # Code is specified. Take corresponding one
            for field_tag in rec.keys():
                if tag_matches_pattern(field_tag, tag):
                    fields = rec[field_tag]
                    for field in fields:
                        if (ind1 == '%' or field[1] == ind1) and \
                               (ind2 == '%' or field[2] == ind2):
                            for subfield in field[0]:
                                if subfield[0] == code:
                                    return subfield[1]

    else:
        # Tag is completely specified. Use tag as dict key
        if rec.has_key(tag):
            fields = rec[tag]
            if code == '':
                # Code not specified.
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2):
                        # Return matching field value if not empty
                        # or return "" empty if not exist.
                        if field[3] != "":
                            return field[3]

            elif code == '%':
                # Code is wildcard. Take first subfield of first matching field
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2) and \
                           (len(field[0]) > 0):
                        return field[0][0][1]
            else:
                # Code is specified. Take corresponding one
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2):
                        for subfield in field[0]:
                            if subfield[0] == code:
                                return subfield[1]
    # Nothing was found
    return ""

def record_get_field_values(rec, tag, ind1="", ind2="", code=""):
    """
    Returns the list of (string) values for the specified field (tag, ind1, ind2, code)
    of the record (rec).

    Returns empty list if not found.

    Parameters (tag, ind1, ind2, code) can contain wildcard %.

    @param rec a record structure as returned by create_record()
    @param tag a 3 characters long string
    @param ind1 a 1 character long string
    @param ind2 a 1 character long string
    @param code a 1 character long string
    @return a list of strings
    """
    tmp = []

    (ind1, ind2) = wash_indicators(ind1, ind2)

    if '%' in tag:
        # Wild card in tag. Must find all corresponding tags and fields
        keys = rec.keys()
        tags = [k for k in keys if tag_matches_pattern(k, tag)]
        if code == '' :
            # Code not specified. Consider field value (without subfields)
            for tag in tags:
                fields = rec[tag]
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2) and field[3] != '':
                        tmp.append(field[3])
        elif code == '%':
            # Code is wildcard. Consider all subfields
            for tag in tags:
                fields = rec[tag]
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2):
                        for subfield in field[0]:
                            tmp.append(subfield[1])
        else:
            # Code is specified. Consider all corresponding subfields
            for tag in tags:
                fields = rec[tag]
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2):
                        for subfield in field[0]:
                            if subfield[0] == code:
                                tmp.append(subfield[1])
    else:
        # Tag is completely specified. Use tag as dict key
        if rec and rec.has_key(tag):
            fields = rec[tag]
            if code == '' :
                # Code not specified. Consider field value (without subfields)
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2) and field[3] != '':
                        tmp.append(field[3])
            elif code == '%':
                # Code is wildcard. Consider all subfields
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2):
                        for subfield in field[0]:
                            tmp.append(subfield[1])
            else:
                # Code is specified. Take corresponding one
                for field in fields:
                    if (ind1 == '%' or field[1] == ind1) and \
                           (ind2 == '%' or field[2] == ind2):
                        for subfield in field[0]:
                            if subfield[0] == code:
                                tmp.append(subfield[1])

    # If tmp was not set, nothing was found
    return tmp

def print_rec(rec, format=1, tags=None):
    """prints a record
       format = 1 -- XML
       format = 2 -- HTML (not implemented)
       @tags: list of tags to be printed
      """

    if tags is None:
        tags = []
    if format == 1:
        text = record_xml_output(rec, tags)
    else:
        return ''

    return text

def print_recs(listofrec, format=1, tags=None):
    """prints a list of records
       format = 1 -- XML
       format = 2 -- HTML (not implemented)
       @tags: list of tags to be printed
       if 'listofrec' is not a list it returns empty string
    """
    if tags is None:
        tags = []
    text = ""

    if type(listofrec).__name__ !='list':
        return ""
    else:
        for rec in listofrec:
            text = "%s\n%s" % (text, print_rec(rec, format, tags))
    return text

def record_xml_output(rec, tags=None):
    """generates the XML for record 'rec' and returns it as a string
    @rec: record
    @tags: list of tags to be printed
    """
    if tags is None:
        tags = []
    xmltext = "<record>\n"
    if tags and "001" not in tags:
        tags.append("001")
    if rec:
        # add the tag 'tag' to each field in rec[tag]
        fields = []
        for tag in rec.keys():
            if not tags or tag in tags:
                for field in rec[tag]:
                    fields.append((tag, field))
        record_order_fields(fields)
        for field in fields:
            xmltext += str(field_xml_output(field[1], field[0]))
    xmltext += "</record>"
    return xmltext

def records_xml_output(listofrec):
    """generates the XML for the list of records 'listofrec' and returns it as a string"""
    xmltext = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE collection SYSTEM "file://%s">
    <collection>\n""" % CFG_MARC21_DTD

    for rec in listofrec:
        xmltext += str(record_xml_output(rec))
    xmltext += "</collection>"
    return xmltext

def field_get_subfield_instances(field):
    """returns the list of subfields associated with field 'field'"""
    return field[0]

def field_get_subfield_values(field_instance, code):
    """Return subfield CODE values of the field instance FIELD."""
    out = []
    for sf_code, sf_value in field_instance[0]:
        if sf_code == code:
            out.append(sf_value)
    return out

def field_add_subfield(field, code, value):
    """adds a subfield to field 'field'"""
    field[0].append(create_subfield(code, value))


### IMPLEMENTATION / INVISIBLE FUNCTIONS

def create_record_RXP(xmltext,
                      verbose=CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL,
                      correct=CFG_BIBRECORD_DEFAULT_CORRECT):
    """
    creates a record object and returns it
    uses the RXP parser

    If verbose>3 then the parser will be strict and will stop in case of well-formedness errors
    or DTD errors
    If verbose=0, the parser will not give warnings
    If 0<verbose<=3, the parser will not give errors, but will warn the user about possible mistakes

    correct != 0 -> We will try to correct errors such as missing attributtes
    correct = 0 -> there will not be any attempt to correct errors

    """

    record = {}
    global err
    global pyrxp_parser

    ord = 1 # this is needed because of the record_xml_output function, where we need to know
            # the order of the fields


    TAG, ATTRS, CHILD_LIST = range(3)

    if verbose > 3:
        pyrxp_parser.ErrorOnValidityErrors = 1
        pyrxp_parser.ErrorOnUnquotedAttributeValues = 1

    if correct:
        (rec, e) = wash(xmltext)
        err.extend(e)
        return (rec, e)

    root1 = pyrxp_parser.parse(xmltext) #root = (tagname, attr_dict, child_list, reserved)

    if root1[0] == 'collection':
        recs = [t for t in root1[CHILD_LIST] if type(t).__name__ == 'tuple' and t[TAG] == "record"]
        if recs != []:
            root = recs[0]
        else:
            root = None
    else:
        root = root1

    # get childs of 'controlfield'
    childs_controlfield = []
    if not root[2] is None:
        childs_controlfield = [t for t in root[CHILD_LIST] if type(t).__name__ == 'tuple' and t[TAG] == "controlfield"]

    # get childs of 'datafield'
    childs_datafield = []
    if not root[CHILD_LIST] is None:
        childs_datafield = [t for t in root[CHILD_LIST] if type(t).__name__ == 'tuple' and t[TAG] == "datafield"]

    for controlfield in childs_controlfield:
        s = controlfield[ATTRS]["tag"]
        value = ''
        if not controlfield is None:
            value = ''.join([n for n in controlfield[CHILD_LIST] if type(n).__name__ == 'str'])

        name = type(value).__name__

        if name in ["int", "long"] :
            st = str(value)
        elif name in ['str', 'unicode']:
            st = value
        else:
            if verbose:
                err.append((7, 'Type found: ' + name))
            st = "" # the type of value is not correct. (user insert something like a list...)


        field = ([], " ", " ", st, ord) #field = (subfields, ind1, ind2,value,ord)

        if record.has_key(s):
            record[s].append(field)
        else:
            record[s] = [field]

        ord += 1

    for datafield in childs_datafield:

        #create list of subfields
        subfields = []

        childs_subfield = []
        if not datafield[CHILD_LIST] is None:
            childs_subfield = [t for t in datafield[CHILD_LIST] if type(t).__name__ == 'tuple' and t[0] == "subfield"]

        for subfield in childs_subfield:
            value = ''
            if not subfield is None:
                value = ''.join([n for n in subfield[CHILD_LIST] if type(n).__name__ == 'str'])
                                       #get_string_value(subfield)
            if subfield[ATTRS].has_key('code'):
                subfields.append((subfield[ATTRS]["code"], value))
            else:
                subfields.append(('!', value))

        #create field

        if datafield[ATTRS].has_key('tag'):
            s = datafield[ATTRS]["tag"]
        else:
            s = '!'

        if datafield[ATTRS].has_key('ind1'):
            ind1 = datafield[ATTRS]["ind1"]
        else:
            ind1 = '!'

        if datafield[ATTRS].has_key('ind2'):
            ind2 = datafield[ATTRS]["ind2"]
        else:
            ind2 = '!'

        (ind1, ind2) = wash_indicators(ind1, ind2)
        field = (subfields, ind1, ind2, "", ord)

        if record.has_key(s):
            record[s].append(field)
        else:
            record[s] = [field]

        ord += 1

    return (record, err)

def create_record_minidom(xmltext,
                          verbose=CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL,
                          correct=CFG_BIBRECORD_DEFAULT_CORRECT):
    """
    creates a record object and returns it
    uses xml.dom.minidom
    """

    record = {}
    ord = 1
    global err

    if correct:
        xmlt = xmltext
        (rec, e) = wash(xmlt, 0)
        err.extend(e)
        return (rec, err)

    dom = parseString(xmltext)
    root = dom.childNodes[0]

    if root.tagName == 'collection':
        record_nodes = [child
                       for child in root.childNodes
                       if child.nodeName == 'record']
        if record_nodes:
            root = record_nodes[0]
        else:
            return ({}, "No records were found")

    for controlfield in get_childs_by_tag_name(root, "controlfield"):
        s = controlfield.getAttribute("tag")

        text_nodes = controlfield.childNodes
        v = u''.join([ n.data for n in text_nodes ]).encode("utf-8")

        name = type(v).__name__
        if (name in ["int", "long"]) :
            field = ([], " ", " ", str(v), ord) # field = (subfields, ind1, ind2,value)
        elif name in ['str', 'unicode']:
            field = ([], " ", " ", v, ord)
        else:
            if verbose:
                err.append((7, 'Type found: ' + name))

            field = ([], " ", " ", "", ord)# the type of value is not correct. (user insert something like a list...)

        if record.has_key(s):
            record[s].append(field)
        else:
            record[s] = [field]
        ord += 1

    for datafield in get_childs_by_tag_name(root, "datafield"):
        subfields = []

        for subfield in get_childs_by_tag_name(datafield, "subfield"):
            text_nodes = subfield.childNodes
            v = u''.join([ n.data for n in text_nodes ]).encode("utf-8")
            code = subfield.getAttributeNS(None,'code').encode("utf-8")
            if code != '':
                subfields.append((code, v))
            else:
                subfields.append(('!', v))

        s = datafield.getAttribute("tag").encode("utf-8")
        if s == '':
            s = '!'

        ind1 = datafield.getAttribute("ind1").encode("utf-8")
        ind2 = datafield.getAttribute("ind2").encode("utf-8")
        (ind1, ind2) = wash_indicators(ind1, ind2)

        if record.has_key(s):
            record[s].append((subfields, ind1, ind2, "", ord))
        else:
            record[s] = [(subfields, ind1, ind2, "", ord)]
        ord += 1

    return (record, err)


def create_record_4suite(xmltext,
                         verbose=CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL,
                         correct=CFG_BIBRECORD_DEFAULT_CORRECT):
    """
    creates a record object and returns it
    uses 4Suite domlette
    """

    record = {}
    global err

    if correct:
        xmlt = xmltext
        (rec, e) = wash(xmlt, 1)
        err.extend(e)
        return (rec, e)

    dom = NonvalidatingReader.parseString(xmltext, "urn:dummy")

    root = dom.childNodes[0]

    if root.tagName == 'collection':
        record_nodes = [child
                       for child in root.childNodes
                       if child.nodeName == 'record']
        if record_nodes:
            root = record_nodes[0]
        else:
            return ({}, "No records were found")

    ord = 1
    for controlfield in get_childs_by_tag_name(root, "controlfield"):
        s = controlfield.getAttributeNS(None, "tag")

        text_nodes = controlfield.childNodes
        v = u''.join([n.data for n in text_nodes]).encode("utf-8")

        name = type(v).__name__
        if (name in ["int", "long"]) :
            field = ([], " ", " ", str(v), ord) # field = (subfields, ind1, ind2,value)
        elif name in ['str', 'unicode']:
            field = ([], " ", " ", v, ord)
        else:
            if verbose:
                err.append((7, 'Type found: ' + name))

            field = ([], " ", " ", "", ord)# the type of value is not correct. (user insert something like a list...)


        if record.has_key(s):
            record[s].append(field)
        else:
            record[s] = [field]
        ord += 1

    for datafield in get_childs_by_tag_name(root, "datafield"):
        subfields = []

        for subfield in get_childs_by_tag_name(datafield, "subfield"):
            text_nodes = subfield.childNodes
            v = u''.join([n.data for n in text_nodes]).encode("utf-8")

            code = subfield.getAttributeNS(None, 'code').encode("utf-8")
            if code != '':
                subfields.append((code, v))
            else:
                subfields.append(('!', v))

        s = datafield.getAttributeNS(None, "tag").encode("utf-8")
        if s == '':
            s = '!'

        ind1 = datafield.getAttributeNS(None, "ind1").encode("utf-8")
        ind2 = datafield.getAttributeNS(None, "ind2").encode("utf-8")
        (ind1, ind2) = wash_indicators(ind1, ind2)

        if record.has_key(s):
            record[s].append((subfields, ind1, ind2, "", ord))
        else:
            record[s] = [(subfields, ind1, ind2, "", ord)]
        ord += 1

    return (record, err)

def record_order_fields(rec, fun="order_by_ord"):
    """orders field inside record 'rec' according to a function"""
    rec.sort(eval(fun))
    return

def record_order_subfields(rec, fun="order_by_code"):
    """orders subfield inside record 'rec' according to a function"""
    for tag in rec:
        for field in rec[tag]:
            field[0].sort(eval(fun))
    return

def concat(alist):
    """concats a list of lists"""
    newl = []
    for l in alist:
        newl.extend(l)
    return newl

def create_subfield(code, value):
    """Create a subfield object and return it."""
    if type(value).__name__ in ["int", "long"]:
        s = str(value)
    else:
        s = value
    subfield = (code, s)
    return subfield

def field_xml_output(field, tag):
    """generates the XML for field 'field' and returns it as a string"""
    xmltext = ""
    if field[3] != "":
        xmltext += "  <controlfield tag=\"%s\">%s</controlfield>\n" % (tag, encode_for_xml(field[3]))
    else:
        xmltext += "  <datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">\n" % (tag, field[1], field[2])
        for subfield in field[0]:
            xmltext += str(subfield_xml_output(subfield))
        xmltext += "  </datafield>\n"
    return xmltext

def subfield_xml_output(subfield):
    """generates the XML for a subfield object and return it as a string"""
    xmltext = "    <subfield code=\"%s\">%s</subfield>\n" % (subfield[0], encode_for_xml(subfield[1]))
    return xmltext

def order_by_ord(field1, field2):
    """function used to order the fields according to their ord value"""
    return cmp(field1[1][4], field2[1][4])

def order_by_code(subfield1, subfield2):
    """function used to order the subfields according to their code value"""
    return cmp(subfield1[0], subfield2[0])

def get_childs_by_tag_name(node, local):
    """retrieves all childs from node 'node' with name 'local' and returns them as a list"""
    cNodes = list(node.childNodes)
    res = [child for child in cNodes if child.nodeName == local]
    return res

def get_string_value(node):
    """gets all child text nodes of node 'node' and returns them as a unicode string"""
    text_nodes = node.childNodes
    return u''.join([ n.data for n in text_nodes ])

def get_childs_by_tag_name_RXP(listofchilds, tag):
    """retrieves all childs from 'listofchilds' with tag name 'tag' and returns them as a list.
       listofchilds is a list returned by the RXP parser
    """
    l = []
    if not listofchilds is None:
        l = [t for t in listofchilds if type(t).__name__ == 'tuple' and t[0] == tag]
    return l

def getAttribute_RXP(root, attr):
    """ returns the attributte 'attr' from root 'root'
        root is a node returned by RXP parser
    """
    try:
        return u''.join(root[1][attr])
    except KeyError:
        return ""

def get_string_value_RXP(node):
    """gets all child text nodes of node 'node' and returns them as a unicode string"""
    if not node is None:
        return ''.join([ n for n in node[2] if type(n).__name__ == 'str'])
    else:
        return ""

def print_errors(alist):
    """ creates a unique string with the strings in list, using '\n' as a separator """
    text = ""
    for l in alist:
        text = '%s\n%s'% (text, l)
    return text

def wash_indicators(ind1, ind2):
    """
    Wash the values of the indicators.  An empty string or an
    underscore is replaced by a blank space.

    @return a tuple (ind1_washed, ind2_washed)
    """

    if ind1 == '' or ind1 == '_':
        ind1 = ' '

    if ind2 == '' or ind2 == '_':
        ind2 = ' '

    return (ind1, ind2)

def wash(xmltext, parser=2):
    """
    Check the structure of the xmltext. Returns a record structure and a list of errors.
    parser = 1 - 4_suite
    parser = 2 - pyRXP
    parser = 0 - minidom
    """

    errors = []
    i, e1 = tagclose('datafield', xmltext)
    j, e2 = tagclose('controlfield', xmltext)
    k, e3 = tagclose('subfield', xmltext)
    w, e4 = tagclose('record', xmltext)
    errors.extend(e1)
    errors.extend(e2)
    errors.extend(e3)
    errors.extend(e4)

    if i and j and k and w and parser > -1:
        if parser == 2:
            (rec, ee) = create_record_RXP(xmltext, 0, 0)
        elif parser == 1:
            (rec, ee) = create_record_4suite(xmltext, 0, 0)
        elif parser == 0:
            (rec, ee) = create_record_minidom(xmltext, 0, 0)
        else:
            (rec, ee) = (None, "ERROR: No usable XML parsers found.")
    else:
        return (None, errors)

    keys = rec.keys()

    for tag in keys:
        upper_bound = '999'
        n = len(tag)

        if n > 3:
            i = n-3
            while i > 0:
                upper_bound = '%s%s' % ('0', upper_bound)
                i = i - 1

        if tag == '!': # missing tag
            errors.append((1, '(field number(s): ' + ([f[4] for f in rec[tag]]).__str__() + ')'))
            v = rec[tag]
            rec.__delitem__(tag)
            rec['000'] = v
            tag = '000'
        elif not (("001" <= tag <= upper_bound) or \
                  tag in ('FMT', 'FFT')):
            errors.append(2)
            v = rec[tag]
            rec.__delitem__(tag)
            rec['000'] = v
            tag = '000'

        fields = []
        for field in rec[tag]:
            if field[0] == [] and field[3] == '': ## datafield without any subfield
                errors.append((8,'(field number: ' + field[4].__str__() + ')'))

            subfields = []
            for subfield in field[0]:
                if subfield[0] == '!':
                    errors.append((3,'(field number: ' + field[4].__str__() + ')'))
                    newsub = ('', subfield[1])
                else:
                    newsub = subfield
                subfields.append(newsub)

            if field[1] == '!':
                errors.append((4,'(field number: ' + field[4].__str__() + ')'))
                ind1 = " "
            else:
                ind1 = field[1]

            if field[2] == '!':
                errors.append((5,'(field number: ' + field[4].__str__() + ')'))
                ind2 = " "
            else:
                ind2 = field[2]

            newf = (subfields, ind1, ind2, field[3], field[4])
            fields.append(newf)

        rec[tag] = fields

    return (rec, errors)

def tagclose(tagname, xmltext):
    """ checks if an XML document does not hae any missing tag with name tagname
    """
    errors = []
    pat_open = '<' + tagname + '.*?>'
    pat_close = '</' + tagname + '>'
    p_open = re.compile(pat_open, re.DOTALL) # DOTALL - to ignore whitespaces
    p_close = re.compile(pat_close, re.DOTALL)
    list1 = p_open.findall(xmltext)
    list2 = p_close.findall(xmltext)

    if len(list1)!=len(list2):
        errors.append((99,'(Tagname : ' + tagname + ')'))
        return (0, errors)
    else:
        return (1, errors)

def warning(code):
    """ It returns a warning message of code 'code'.
        If code = (cd, str) it returns the warning message of code 'cd'
        and appends str at the end"""

    ws = CFG_BIBRECORD_WARNING_MSGS
    s = ''

    if type(code).__name__ == 'str':
        return code

    if type(code).__name__ == 'tuple':
        if type(code[1]).__name__ == 'str':
            s = code[1]
            c = code[0]
    else:
        c = code
    if ws.has_key(c):
        return ws[c]+s
    else:
        return ""

def warnings(l):
    """it applies the function warning to every element in l"""
    alist = []
    for w in l:
        alist.append(warning(w))
    return alist

def choose(cond, a, b):
    """ Simple implementation of c-like ? operator ( Just for the further code clarity)
        a,b are function arguments which calculate the result ( just in order to have the
        lazy evaluation)
    """
    if cond:
        return a()
    else:
        return b()

def compare_lists(list1, list2, comparer):
    """
    Compares twolists using given comparing function
    @param list1 first list to compare
    @param list2 second list to compare
    @param comparer -  a function taking two arguments ( element of list 1, element of list 2) and
    @retrun  True or False depending if the values are the same
    """
    len1 = len(list1)
    len2 = len(list2)
    if len1 != len2:
        return False
    result = True
    for ind in range(0,len1):
        if not comparer(list1[ind],list2[ind]):
            result = False
    return result

def record_field_diff(rec1, rec2, field):
    """
       Compares given field in two records.
       returns a list containing at most one element
       If the fields are identical ( that means have the same order, the same
        subfields), empty list is returned.
       If the field is removed in second record, [(field, 'r')] is returned
       If the field is added in second record, [(field, 'a', new_value)] is returned
       If the field is changed [(field, 'c', new_value)] is returned
    """
    subfields1 = choose(rec1[0].has_key(field), lambda: rec1[0][field], lambda: [])
    subfields2 = choose(rec2[0].has_key(field), lambda: rec2[0][field], lambda: [])
    if subfields1 == [] and subfields2 == []:
        return []
    if subfields1 == []:
        return [(field, 'a', subfields2)]
    if subfields2 == []:
        return [(field, 'r', subfields1)]
    #we can not use simple == operator due to the numeric field which can be different in both records
    #hopefully, we can compare element by element because order of subfields must be preserved
    #   comparer function compares the exact values and indicators 1 and 2
    are_identical = compare_lists(subfields1, subfields2, lambda el1,el2: \
                                  (el1[0] == el2[0]) and (el1[1] == el2[1]) and (el1[2] == el2[2]))
    return choose(are_identical, lambda: [], lambda: [(field, 'c', subfields1,  subfields2)])

def record_diff(rec1, rec2):
    """  Compares two given records
         Considers the change of order of fields as a change
         @param rec1 - First record
         @param rec2 - Second record

         @return list of differences. Each difference is of a form:
          (field_id, 'r') - if field field_id exists in rec1 but not in rec2
          (field_id, 'a', new_value) - if field field_id exists in rec2 but not in rec1
          (field_id, 'c', new_value) - if field field_id exists in both records, but
          it's value has changed
          new_value describes the new value of a given field ( which allows to reconstruct new record from the old one)
    """
    result = []
    for field in rec1[0].keys():
        result += record_field_diff(rec1, rec2, field)
    for field in rec2[0].keys():
        if not rec1[0].has_key(field):
            result += [(field, 'a', rec2[0][field] )]
    return result

def record_extract_oai_id(record):
    # Searching for oai ids.
    tag = CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3]
    ind1 = CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3]
    ind2 = CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4]
    subfield = CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5]
    values = record_get_field_values(record, tag, ind1, ind2, subfield)
    oai_id_regexp = "oai[a-zA-Z0-9/.:]+"
    for id in values:
        if re.match(oai_id_regexp, str(id).strip()) != None:
            return str(id).strip()
    return ""

if psycho_available == 1:
    #psyco.full()
    psyco.bind(wash)
    psyco.bind(create_record_4suite)
    psyco.bind(create_record_RXP)
    psyco.bind(create_record_minidom)
    psyco.bind(record_order_subfields)
    psyco.bind(field_get_subfield_values)
    psyco.bind(create_records)
    psyco.bind(create_record)
    psyco.bind(record_get_field_instances)
    psyco.bind(record_get_field_value)
    psyco.bind(record_get_field_values)
