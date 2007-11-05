# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

import string
import re
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
                   correct=CFG_BIBRECORD_DEFAULT_CORRECT):
    """
    Create list of record from XMLTEXT.  Return a list of objects
    initiated by create_record() function; please see that function's
    docstring.
    """
    global parser
    err = []

    if parser == -1:
        err.append((6, "import error"))
    else:
        pat = r"<record.*?>.*?</record>"
        p = re.compile(pat, re.DOTALL) # DOTALL - to ignore whitespaces
        alist = p.findall(xmltext)

        listofrec = map((lambda x:create_record(x, verbose, correct)),
                        alist)
        return listofrec
    return []

# Record :: {tag : [Field]}
# Field :: (Subfields,ind1,ind2,value)
# Subfields :: [(code,value)]

def create_record(xmltext,
                  verbose=CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL,
                  correct=CFG_BIBRECORD_DEFAULT_CORRECT):
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
    global parser

    try:
        if parser == 2:
            ## the following is because of DTD validation
            t = """<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE collection SYSTEM "file://%s">
            <collection>\n""" % CFG_MARC21_DTD
            t = "%s%s" % (t, xmltext)
            t = "%s</collection>" % t
            xmltext = t
            (rec, er) = create_record_RXP(xmltext, verbose, correct)
        elif parser == 1:
            (rec, er) = create_record_4suite(xmltext, verbose, correct)
        elif parser == 0:
            (rec, er) = create_record_minidom(xmltext, verbose, correct)
        else:
            (rec, er) = (None, "ERROR: No usable XML parsers found.")
        errs = warnings(er)
    except Exception, e:
        print e
        errs = warnings(concat(err))
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
    @return a list of field tuples (Subfields, ind1, ind2, value) where subfields is list of (code, value)
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

def record_add_field(rec, tag, ind1="", ind2="",
                     controlfield_value="",
                     datafield_subfield_code_value_tuples=[],
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

def record_delete_field(rec, tag, ind1="", ind2="", field_number=None):
    """
    delete all fields defined with marc tag 'tag' and indicators 'ind1' and 'ind2'
    from record 'rec'. If field_number is specified, delete only the particualar
    field_number.
    """
    (ind1, ind2) = wash_indicators(ind1, ind2)

    newlist = []
    if rec.has_key(tag):
        if not field_number:
            for field in rec[tag]:
                if not (field[1]==ind1 and field[2]==ind2):
                    newlist.append(field)
        else:
            for field in rec[tag]:
                if not (field[1]==ind1 and field[2]==ind2 and field[3]==field_number):
                    newlist.append(field)
        rec[tag] = newlist

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

def print_rec(rec, format=1, tags=[]):
    """prints a record
       format = 1 -- XML
       format = 2 -- HTML (not implemented)
       @tags: list of tags to be printed
      """

    if format == 1:
        text = record_xml_output(rec, tags)
    else:
        return ''

    return text

def print_recs(listofrec, format=1, tags=[]):
    """prints a list of records
       format = 1 -- XML
       format = 2 -- HTML (not implemented)
       @tags: list of tags to be printed
       if 'listofrec' is not a list it returns empty string
    """
    text = ""

    if type(listofrec).__name__ !='list':
        return ""
    else:
        for rec in listofrec:
            text = "%s\n%s" % (text, print_rec(rec, format, tags))
    return text

def record_xml_output(rec, tags=[]):
    """generates the XML for record 'rec' and returns it as a string
    @rec: record
    @tags: list of tags to be printed
    """
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
    xmltext = "%s</record>" % xmltext
    return xmltext

def records_xml_output(listofrec):
    """generates the XML for the list of records 'listofrec' and returns it as a string"""
    xmltext = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE collection SYSTEM "file://%s">
    <collection>\n""" % CFG_MARC21_DTD

    for rec in listofrec:
        xmltext = "%s%s" % (xmltext, record_xml_output(rec))
    xmltext = "%s</collection>" % xmltext
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

        ord = ord + 1

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

        ord = ord+1

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
        ord = ord + 1

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
        ord = ord + 1

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
        ord = ord + 1

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
        ord = ord + 1

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
        xmltext = "%s  <controlfield tag=\"%s\">%s</controlfield>\n" % (xmltext, tag, encode_for_xml(field[3]))
    else:
        xmltext = "%s  <datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">\n" % (xmltext, tag, field[1], field[2])
        for subfield in field[0]:
            xmltext = "%s%s" % (xmltext, subfield_xml_output(subfield))
        xmltext = "%s </datafield>\n" % xmltext
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

def encode_for_xml(s):
    "Encode special chars in string so that it would be XML-compliant."
    s = string.replace(s, '&', '&amp;')
    s = string.replace(s, '<', '&lt;')
    return s

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
