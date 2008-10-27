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
Utilities for special formatting of records.

API functions: highlight, get_contextual_content, encode_for_xml

Used mainly by BibFormat elements.

Depends on search_engine.py for record_exists()

FIXME: currently copies record_exists() code from search engine.  Refactor later.
"""

__revision__ = "$Id$"

import re
import zlib

from invenio.config import \
     CFG_OAI_ID_FIELD
from invenio.dbquery import run_sql

def highlight(text, keywords=[], prefix_tag='<strong>', suffix_tag="</strong>"):
    """
    Returns text with all words highlighted with given tags (this
    function places 'prefix_tag' and 'suffix_tag' before and after
    words from 'keywords' in 'text').

    for example set prefix_tag='<b style="color: black; background-color: rgb(255, 255, 102);">' and suffix_tag="</b>"

    @param text the text to modify
    @param keywords a list of string
    @return highlighted text
    """

    if keywords == []:
        return text

    #FIXME decide if non english accentuated char should be desaccentuaded
    def replace_highlight(match):
        """ replace match.group() by prefix_tag + match.group() + suffix_tag"""
        return prefix_tag + match.group() + suffix_tag

    #Build a pattern of the kind keyword1 | keyword2 | keyword3
    pattern = '|'.join(keywords)
    compiled_pattern = re.compile(pattern, re.IGNORECASE)

    #Replace and return keywords with prefix+keyword+suffix
    return compiled_pattern.sub(replace_highlight, text)

def get_contextual_content(text, keywords, max_lines=2):
    """
    Returns some lines from a text contextually to the keywords in
    'keywords_string'

    @param text the text from which we want to get contextual content
    @param keywords a list of keyword strings ("the context")
    @param max_lines the maximum number of line to return from the record
    @return a string
    """

    def grade_line(text_line, keywords):
        """
        Grades a line according to keywords.

        grade = number of keywords in the line
        """
        grade = 0
        for keyword in keywords:
            grade += text_line.upper().count(keyword.upper())

        return grade

    #Grade each line according to the keywords
    lines = text.split('.')
    #print 'lines: ',lines
    weights = [grade_line(line, keywords) for line in lines]

    #print 'line weights: ', weights
    def grade_region(lines_weight):
        """
        Grades a region. A region is a set of consecutive lines.

        grade = sum of weights of the line composing the region
        """
        grade = 0
        for weight in lines_weight:
            grade += weight
        return grade

    if max_lines > 1:
        region_weights = []
        for index_weight in range(len(weights)- max_lines + 1):
            region_weights.append(grade_region(weights[index_weight:(index_weight+max_lines)]))

        weights = region_weights
    #print 'region weights: ',weights
    #Returns line with maximal weight, and (max_lines - 1) following lines.
    index_with_highest_weight = 0
    highest_weight = 0
    i = 0
    for weight in weights:
        if weight > highest_weight:
            index_with_highest_weight = i
            highest_weight = weight
        i += 1
    #print 'highest weight', highest_weight

    if index_with_highest_weight+max_lines > len(lines):
        return lines[index_with_highest_weight:]
    else:
        return lines[index_with_highest_weight:index_with_highest_weight+max_lines]

def record_get_xml(recID, format='xm', decompress=zlib.decompress,
                   on_the_fly=False):
    """
    Returns an XML string of the record given by recID.

    The function builds the XML directly from the database,
    without using the standard formatting process.

    'format' allows to define the flavour of XML:
        - 'xm' for standard XML
        - 'marcxml' for MARC XML
        - 'oai_dc' for OAI Dublin Core
        - 'xd' for XML Dublin Core

    If record does not exist, returns empty string.

    @param recID the id of the record to retrieve
    @param on_the_fly if False, try to fetch precreated one in database
    @return the xml string of the record
    """
    from invenio.search_engine import record_exists

    def get_fieldvalues(recID, tag):
        """Return list of field values for field TAG inside record RECID."""
        out = []
        if tag == "001___":
            # we have asked for recID that is not stored in bibXXx tables
            out.append(str(recID))
        else:
            # we are going to look inside bibXXx tables
            digit = tag[0:2]
            bx = "bib%sx" % digit
            bibx = "bibrec_bib%sx" % digit
            query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag LIKE '%s'" \
                    "ORDER BY bibx.field_number, bx.tag ASC" % (bx, bibx, recID, tag)
            res = run_sql(query)
            for row in res:
                out.append(row[0])
        return out

    def get_creation_date(recID, fmt="%Y-%m-%d"):
        "Returns the creation date of the record 'recID'."
        out = ""
        res = run_sql("SELECT DATE_FORMAT(creation_date,%s) FROM bibrec WHERE id=%s", (fmt, recID), 1)
        if res:
            out = res[0][0]
        return out

    def get_modification_date(recID, fmt="%Y-%m-%d"):
        "Returns the date of last modification for the record 'recID'."
        out = ""
        res = run_sql("SELECT DATE_FORMAT(modification_date,%s) FROM bibrec WHERE id=%s", (fmt, recID), 1)
        if res:
            out = res[0][0]
        return out

    #_ = gettext_set_language(ln)

    out = ""

    # sanity check:
    record_exist_p = record_exists(recID)
    if record_exist_p == 0: # doesn't exist
        return out

    # print record opening tags, if needed:
    if format == "marcxml" or format == "oai_dc":
        out += "  <record>\n"
        out += "   <header>\n"
        for identifier in get_fieldvalues(recID, CFG_OAI_ID_FIELD):
            out += "    <identifier>%s</identifier>\n" % identifier
        out += "    <datestamp>%s</datestamp>\n" % get_modification_date(recID)
        out += "   </header>\n"
        out += "   <metadata>\n"

    if format.startswith("xm") or format == "marcxml":
        res = None
        if on_the_fly == False:
            # look for cached format existence:
            query = """SELECT value FROM bibfmt WHERE
            id_bibrec='%s' AND format='%s'""" % (recID, format)
            res = run_sql(query, None, 1)
        if res and record_exist_p == 1:
            # record 'recID' is formatted in 'format', so print it
            out += "%s" % decompress(res[0][0])
        else:
            # record 'recID' is not formatted in 'format' -- they are
            # not in "bibfmt" table; so fetch all the data from
            # "bibXXx" tables:
            if format == "marcxml":
                out += """    <record xmlns="http://www.loc.gov/MARC21/slim">\n"""
                out += "        <controlfield tag=\"001\">%d</controlfield>\n" % int(recID)
            elif format.startswith("xm"):
                out += """    <record>\n"""
                out += "        <controlfield tag=\"001\">%d</controlfield>\n" % int(recID)
            if record_exist_p == -1:
                # deleted record, so display only OAI ID and 980:
                oai_ids = get_fieldvalues(recID, CFG_OAI_ID_FIELD)
                if oai_ids:
                    out += "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\"><subfield code=\"%s\">%s</subfield></datafield>\n" % \
                           (CFG_OAI_ID_FIELD[0:3],
                            CFG_OAI_ID_FIELD[3:4],
                            CFG_OAI_ID_FIELD[4:5],
                            CFG_OAI_ID_FIELD[5:6],
                            oai_ids[0])
                out += "<datafield tag=\"980\" ind1=\" \" ind2=\" \"><subfield code=\"c\">DELETED</subfield></datafield>\n"
            else:
                # controlfields
                query = "SELECT b.tag,b.value,bb.field_number FROM bib00x AS b, bibrec_bib00x AS bb "\
                        "WHERE bb.id_bibrec='%s' AND b.id=bb.id_bibxxx AND b.tag LIKE '00%%' "\
                        "ORDER BY bb.field_number, b.tag ASC" % recID
                res = run_sql(query)
                for row in res:
                    field, value = row[0], row[1]
                    value = encode_for_xml(value)
                    out += """        <controlfield tag="%s">%s</controlfield>\n""" % \
                           (encode_for_xml(field[0:3]), value)
                # datafields
                i = 1 # Do not process bib00x and bibrec_bib00x, as
                      # they are controlfields. So start at bib01x and
                      # bibrec_bib00x (and set i = 0 at the end of
                      # first loop)
                for digit1 in range(0, 10):
                    for digit2 in range(i, 10):
                        bx = "bib%d%dx" % (digit1, digit2)
                        bibx = "bibrec_bib%d%dx" % (digit1, digit2)
                        query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                                "WHERE bb.id_bibrec='%s' AND b.id=bb.id_bibxxx AND b.tag LIKE '%s%%' "\
                                "ORDER BY bb.field_number, b.tag ASC" % (bx,
                                                                         bibx,
                                                                         recID,
                                                                         str(digit1)+str(digit2))
                        res = run_sql(query)
                        field_number_old = -999
                        field_old = ""
                        for row in res:
                            field, value, field_number = row[0], row[1], row[2]
                            ind1, ind2 = field[3], field[4]
                            if ind1 == "_" or ind1 == "":
                                ind1 = " "
                            if ind2 == "_" or ind2 == "":
                                ind2 = " "
                            # print field tag
                            if field_number != field_number_old or \
                                   field[:-1] != field_old[:-1]:
                                if field_number_old != -999:
                                    out += """        </datafield>\n"""
                                out += """        <datafield tag="%s" ind1="%s" ind2="%s">\n""" % \
                                       (encode_for_xml(field[0:3]),
                                        encode_for_xml(ind1),
                                        encode_for_xml(ind2))
                                field_number_old = field_number
                                field_old = field
                            # print subfield value
                            value = encode_for_xml(value)
                            out += """            <subfield code="%s">%s</subfield>\n""" % \
                                   (encode_for_xml(field[-1:]), value)

                        # all fields/subfields printed in this run, so close the tag:
                        if field_number_old != -999:
                            out += """        </datafield>\n"""
                    i = 0 # Next loop should start looking at bib%0 and bibrec_bib00x
            # we are at the end of printing the record:
            out += "    </record>\n"

    elif format == "xd" or format == "oai_dc":
        # XML Dublin Core format, possibly OAI -- select only some bibXXx fields:
        out += """    <dc xmlns="http://purl.org/dc/elements/1.1/"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xsi:schemaLocation="http://purl.org/dc/elements/1.1/
                                             http://www.openarchives.org/OAI/1.1/dc.xsd">\n"""
        if record_exist_p == -1:
            out += ""
        else:
            for f in get_fieldvalues(recID, "041__a"):
                out += "        <language>%s</language>\n" % f

            for f in get_fieldvalues(recID, "100__a"):
                out += "        <creator>%s</creator>\n" % encode_for_xml(f)

            for f in get_fieldvalues(recID, "700__a"):
                out += "        <creator>%s</creator>\n" % encode_for_xml(f)

            for f in get_fieldvalues(recID, "245__a"):
                out += "        <title>%s</title>\n" % encode_for_xml(f)

            for f in get_fieldvalues(recID, "65017a"):
                out += "        <subject>%s</subject>\n" % encode_for_xml(f)

            for f in get_fieldvalues(recID, "8564_u"):
                out += "        <identifier>%s</identifier>\n" % encode_for_xml(f)

            for f in get_fieldvalues(recID, "520__a"):
                out += "        <description>%s</description>\n" % encode_for_xml(f)

            out += "        <date>%s</date>\n" % get_creation_date(recID)
        out += "    </dc>\n"


    # print record closing tags, if needed:
    if format == "marcxml" or format == "oai_dc":
        out += "   </metadata>\n"
        out += "  </record>\n"

    return out

def encode_for_xml(s):
    "Encode special chars in string so that it would be XML-compliant."
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    return s

def parse_tag(tag):
    """
    Parse a marc code and decompose it in a table with:
    0-tag 1-indicator1 2-indicator2 3-subfield

    The first 3 chars always correspond to tag.
    The indicators are optional. However they must both be indicated, or both ommitted.
    If indicators are ommitted or indicated with underscore '_', they mean "No indicator".
    "No indicator" is also equivalent indicator marked as whitespace.
    The subfield is optional. It can optionally be preceded by a dot '.' or '$$' or '$'

    Any of the chars can be replaced by wildcard %

    THE FUNCTION DOES NOT CHECK WELLFORMNESS OF 'tag'

    Any empty chars is not considered

    For example:
    >> parse_tag('245COc') = ['245', 'C', 'O', 'c']
    >> parse_tag('245C_c') = ['245', 'C', '', 'c']
    >> parse_tag('245__c') = ['245', '', '', 'c']
    >> parse_tag('245__$$c') = ['245', '', '', 'c']
    >> parse_tag('245__$c') = ['245', '', '', 'c']
    >> parse_tag('245  $c') = ['245', '', '', 'c']
    >> parse_tag('245  $$c') = ['245', '', '', 'c']
    >> parse_tag('245__.c') = ['245', '', '', 'c']
    >> parse_tag('245  .c') = ['245', '', '', 'c']
    >> parse_tag('245C_$c') = ['245', 'C', '', 'c']
    >> parse_tag('245CO$$c') = ['245', 'C', 'O', 'c']
    >> parse_tag('245C_.c') = ['245', 'C', '', 'c']
    >> parse_tag('245$c') = ['245', '', '', 'c']
    >> parse_tag('245.c') = ['245', '', '', 'c']
    >> parse_tag('245$$c') = ['245', '', '', 'c']
    >> parse_tag('245__%') = ['245', '', '', '']
    >> parse_tag('245__$$%') = ['245', '', '', '']
    >> parse_tag('245__$%') = ['245', '', '', '']
    >> parse_tag('245  $%') = ['245', '', '', '']
    >> parse_tag('245  $$%') = ['245', '', '', '']
    >> parse_tag('245$%') = ['245', '', '', '']
    >> parse_tag('245.%') = ['245', '', '', '']
    >> parse_tag('245$$%') = ['245', '', '', '']
    >> parse_tag('2%5$$a') = ['2%5', '', '', 'a']
    """

    p_tag =  ['', '', '', ''] # tag, ind1, ind2, code
    tag = tag.replace(" ", "") # Remove empty characters
    tag = tag.replace("$", "") # Remove $ characters
    tag = tag.replace(".", "") # Remove . characters
    #tag = tag.replace("_", "") # Remove _ characters

    p_tag[0] = tag[0:3] # tag
    if len(tag) == 4:
        p_tag[3] = tag[3] # subfield

    elif len(tag) == 5:
        ind1 = tag[3] # indicator 1
        if ind1 != "_":
            p_tag[1] = ind1

        ind2 = tag[4] # indicator 2
        if ind2 != "_":
            p_tag[2] = ind2

    elif len(tag) == 6:
        p_tag[3] = tag[5] # subfield

        ind1 = tag[3] # indicator 1
        if ind1 != "_":
            p_tag[1] = ind1

        ind2 = tag[4] # indicator 2
        if ind2 != "_":
            p_tag[2] = ind2

    return p_tag
