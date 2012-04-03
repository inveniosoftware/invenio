# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
Utilities for special formatting of records.

API functions: highlight, get_contextual_content, encode_for_xml

Used mainly by BibFormat elements.
"""

__revision__ = "$Id$"

import re
import zlib
import shlex
from subprocess import *

from invenio.config import \
     CFG_OAI_ID_FIELD, \
     CFG_WEBSEARCH_FULLTEXT_SNIPPETS, \
     CFG_WEBSEARCH_FULLTEXT_SNIPPETS_WORDS, \
     CFG_INSPIRE_SITE
from invenio.dbquery import run_sql
from invenio.urlutils import string_to_numeric_char_reference
from invenio.textutils import encode_for_xml
from invenio.shellutils import run_shell_command
from invenio.search_engine_utils import get_fieldvalues

def highlight_matches(text, compiled_pattern, \
                      prefix_tag='<strong>', suffix_tag="</strong>"):
    """
    Highlight words in 'text' matching the 'compiled_pattern'

    @param text: the text in which we want to "highlight" parts
    @param compiled_pattern: the parts to highlight
    @type compiled_pattern: a compiled regular expression
    @param prefix_tag: prefix to use before each matching parts
    @param suffix_tag: suffix to use after each matching parts
    @return: a version of input X{text} with words matching X{compiled_pattern} surrounded by X{prefix_tag} and X{suffix_tag}
    """

    #Add 'prefix_tag' and 'suffix_tag' before and after 'match'
    #FIXME decide if non english accentuated char should be desaccentuaded
    def replace_highlight(match):
        """ replace match.group() by prefix_tag + match.group() + suffix_tag"""
        return prefix_tag + match.group() + suffix_tag

    #Replace and return keywords with prefix+keyword+suffix
    return compiled_pattern.sub(replace_highlight, text)

def highlight(text, keywords=None, \
              prefix_tag='<strong>', suffix_tag="</strong>"):
    """
    Returns text with all words highlighted with given tags (this
    function places 'prefix_tag' and 'suffix_tag' before and after
    words from 'keywords' in 'text').

    for example set prefix_tag='<b style="color: black; background-color: rgb(255, 255, 102);">' and suffix_tag="</b>"

    @param text: the text to modify
    @param keywords: a list of string
    @param prefix_tag: prefix to use before each matching parts
    @param suffix_tag: suffix to use after each matching parts
    @return: highlighted text
    """

    if not keywords:
        return text

    escaped_keywords = []
    for k in keywords:
        escaped_keywords.append(re.escape(k))
    #Build a pattern of the kind keyword1 | keyword2 | keyword3
    pattern = '|'.join(escaped_keywords)
    compiled_pattern = re.compile(pattern, re.IGNORECASE)

    #Replace and return keywords with prefix+keyword+suffix
    return highlight_matches(text, compiled_pattern, \
                             prefix_tag, suffix_tag)

def get_contextual_content(text, keywords, max_lines=2):
    """
    Returns some lines from a text contextually to the keywords in
    'keywords_string'

    @param text: the text from which we want to get contextual content
    @param keywords: a list of keyword strings ("the context")
    @param max_lines: the maximum number of line to return from the record
    @return: a string
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
    If the record is deleted, returns an empty MARCXML (with recid
    controlfield, OAI ID fields and 980__c=DELETED)

    @param recID: the id of the record to retrieve
    @param format: the format to use
    @param on_the_fly: if False, try to fetch precreated one in database
    @param decompress: the library to use to decompress cache from DB
    @return: the xml string of the record
    """
    from invenio.search_engine import record_exists

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
                from invenio.search_engine import get_merged_recid
                # obtain the recid of the new record
                merged_recid = str(get_merged_recid(recID))
                out += "<datafield tag=\"970\" ind1=\" \" ind2=\" \"><subfield code=\"d\">%s</subfield></datafield>\n" % merged_recid
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

    @param tag: tag to parse
    @return: a canonical form of the input X{tag}
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

def get_all_fieldvalues(recID, tags_in):
    """
    Returns list of values that belong to fields in tags_in for record
    with given recID.

    Note that when a partial 'tags_in' is specified (eg. '100__'), the
    subfields of all corresponding datafields are returned all 'mixed'
    together. Eg. with::
      123 100__ $a Ellis, J $u CERN
      123 100__ $a Smith, K
    >>> get_all_fieldvalues(123, '100__')
    ['Ellis, J', 'CERN', 'Smith, K']

    @param recID: record ID to consider
    @param tags_in: list of tags got retrieve
    @return: a list of values corresponding to X{tags_in} found in X{recID}
    """
    out = []
    if type(tags_in) is not list:
        tags_in = [tags_in, ]

    dict_of_tags_out = {}
    if not tags_in:
        for i in range(0, 10):
            for j in range(0, 10):
                dict_of_tags_out["%d%d%%" % (i, j)] = '%'
    else:
        for tag in tags_in:
            if len(tag) == 0:
                for i in range(0, 10):
                    for j in range(0, 10):
                        dict_of_tags_out["%d%d%%" % (i, j)] = '%'
            elif len(tag) == 1:
                for j in range(0, 10):
                    dict_of_tags_out["%s%d%%" % (tag, j)] = '%'
            elif len(tag) <= 5:
                dict_of_tags_out["%s%%" % tag] = '%'
            else:
                dict_of_tags_out[tag[0:5]] = tag[5:6]
    tags_out = dict_of_tags_out.keys()
    tags_out.sort()
    # search all bibXXx tables as needed:
    for tag in tags_out:
        digits = tag[0:2]
        try:
            intdigits = int(digits)
            if intdigits < 0 or intdigits > 99:
                raise ValueError
        except ValueError:
            # invalid tag value asked for
            continue
        bx = "bib%sx" % digits
        bibx = "bibrec_bib%sx" % digits
        query = "SELECT b.tag,b.value,bb.field_number FROM %s AS b, %s AS bb "\
                "WHERE bb.id_bibrec=%%s AND b.id=bb.id_bibxxx AND b.tag LIKE %%s"\
                "ORDER BY bb.field_number, b.tag ASC" % (bx, bibx)
        res = run_sql(query, (recID, str(tag)+dict_of_tags_out[tag]))
        # go through fields:
        for row in res:
            field, value, field_number = row[0], row[1], row[2]
            out.append(value)

    return out


re_bold_latex = re.compile('\$?\\\\textbf\{(?P<content>.*?)\}\$?')
re_emph_latex = re.compile('\$?\\\\emph\{(?P<content>.*?)\}\$?')
re_generic_start_latex = re.compile('\$?\\\\begin\{(?P<content>.*?)\}\$?')
re_generic_end_latex = re.compile('\$?\\\\end\{(?P<content>.*?)\}\$?')
re_verbatim_env_latex = re.compile('\\\\begin\{verbatim.*?\}(?P<content>.*?)\\\\end\{verbatim.*?\}')

def latex_to_html(text):
    """
    Do some basic interpretation of LaTeX input. Gives some nice
    results when used in combination with MathJax.

    @param text: input "LaTeX" markup to interpret
    @return: a representation of input LaTeX more suitable for HTML
    """
    # Process verbatim environment first
    def make_verbatim(match_obj):
        """Replace all possible special chars by HTML character
        entities, so that they are not interpreted by further commands"""
        return '<br/><pre class="tex2math_ignore">' + \
               string_to_numeric_char_reference(match_obj.group('content')) + \
               '</pre><br/>'

    text = re_verbatim_env_latex.sub(make_verbatim, text)

    # Remove trailing "line breaks"
    text = text.strip('\\\\')

    # Process special characters
    text = text.replace("\\%", "%")
    text = text.replace("\\#", "#")
    text = text.replace("\\$", "$")
    text = text.replace("\\&", "&amp;")
    text = text.replace("\\{", "{")
    text = text.replace("\\}", "}")
    text = text.replace("\\_", "_")
    text = text.replace("\\^{} ", "^")
    text = text.replace("\\~{} ", "~")
    text = text.replace("\\textregistered", "&#0174;")
    text = text.replace("\\copyright", "&#0169;")
    text = text.replace("\\texttrademark", "&#0153; ")

    # Remove commented lines and join lines
    text = '\\\\'.join([line for line in text.split('\\\\') \
                        if not line.lstrip().startswith('%')])

    # Line breaks
    text = text.replace('\\\\', '<br/>')

    # Non-breakable spaces
    text = text.replace('~', '&nbsp;')

    # Styled text
    def make_bold(match_obj):
        "Make the found pattern bold"
        # FIXME: check if it is valid to have this inside a formula
        return '<b>' + match_obj.group('content') + '</b>'
    text = re_bold_latex.sub(make_bold, text)

    def make_emph(match_obj):
        "Make the found pattern emphasized"
        # FIXME: for the moment, remove as it could cause problem in
        # the case it is used in a formula. To be check if it is valid.
        return ' ' + match_obj.group('content') + ''
    text = re_emph_latex.sub(make_emph, text)

    # Lists
    text = text.replace('\\begin{enumerate}', '<ol>')
    text = text.replace('\\end{enumerate}', '</ol>')
    text = text.replace('\\begin{itemize}', '<ul>')
    text = text.replace('\\end{itemize}', '</ul>')
    text = text.replace('\\item', '<li>')

    # Remove remaining non-processed tags
    text = re_generic_start_latex.sub('', text)
    text = re_generic_end_latex.sub('', text)

    return text

def get_pdf_snippets(recID, patterns,
                     nb_words_around=CFG_WEBSEARCH_FULLTEXT_SNIPPETS_WORDS,
                     max_snippets=CFG_WEBSEARCH_FULLTEXT_SNIPPETS):
    """
    Extract text snippets around 'patterns' from the newest PDF file of 'recID'
    The search is case-insensitive.
    The snippets are meant to look like in the results of the popular search
    engine: using " ... " between snippets.
    For empty patterns it returns ""

    @param recID: record ID to consider
    @param patterns: list of patterns to retrieve
    @param nb_words_around: max number of words around the matched pattern
    @param max_snippets: max number of snippets to include
    @return: snippet
    """
    from invenio.bibdocfile import BibRecDocs

    text_path = ""
    text_path_courtesy = ""
    for bd in BibRecDocs(recID).list_bibdocs():
        if bd.get_text():
            text_path = bd.get_text_path()
            text_path_courtesy = bd.get_status()
            if CFG_INSPIRE_SITE and not text_path_courtesy:
                # get courtesy from doctype, since docstatus was empty:
                text_path_courtesy = bd.get_type()
                if text_path_courtesy == 'INSPIRE-PUBLIC':
                    # but ignore 'INSPIRE-PUBLIC' doctype
                    text_path_courtesy = ''
            break # stop at the first good PDF textable file

    if text_path:
        out = get_text_snippets(text_path, patterns, nb_words_around, max_snippets)
        if not out:
            # no hit, so check stemmed versions:
            from invenio.bibindex_engine_stemmer import stem
            stemmed_patterns = [stem(p, 'en') for p in patterns]
            out = get_text_snippets(text_path, stemmed_patterns,
                                    nb_words_around, max_snippets, False)
        if out:
            out_courtesy = ""
            if text_path_courtesy:
                out_courtesy = '<strong>Snippets courtesy of ' + text_path_courtesy + '</strong><br>'
            return """<div class="snippetbox">%s%s</div>""" % (out_courtesy, out)
        else:
            return ""
    else:
        return ""

def get_text_snippets(textfile_path, patterns, nb_words_around, max_snippets, \
                      right_boundary = True):
    """
    Extract text snippets around 'patterns' from file found at 'textfile_path'
    The snippets are meant to look like in the results of the popular search
    engine: using " ... " between snippets.
    For empty patterns it returns ""
    The idea is to first produce big snippets with grep and then narrow them
    using the cut_out_snippet function.
    TODO: - distinguish the beginning of sentences and try to make the snippets
    start there

    @param textfile_path: path to a text file to extract snippet from
    @param patterns: list of patterns to retrieve
    @param nb_words_around: max number of words around the matched pattern
    @param max_snippets: max number of snippets to include
    @param right_boundary: match the right word boundary or not
    @return: snippet
    """

    if len(patterns) == 0:
        return ""

    # escape the parenthesis unless there is no space between then (e.g. U(1))
    # escaping of spaces is done later - only for grepping .
    escaped_keywords = []
    for w in patterns:
        #if there are both '(' and ')' in one word we leave them
        if w.count('(') or w.count(')'):
            if re.match("\w*\(\w*\)\w*", w):
                w1 = w.replace('(', '\(')
                escaped_keywords.append(w1.replace(')', '\)'))
            else:
                w1 = w.replace('(', '')
                escaped_keywords.append(w1.replace(')', ''))
        else:
            escaped_keywords.append(w)
    # the max number of words that the snippets can have for this record
    words_left = max_snippets * (nb_words_around * 2 + 1)
    # Assuming that there will be at least one word per line we can produce the
    # big snippets like this
    # FIXME: the ligature replacement should be done at the textification time;
    # then the sed expression can go away here.
    sed_cmd = "sed \'s/ﬀ/ff/g; s/ﬁ/fi/g; s/ﬂ/fl/g; s/ﬃ/ffi/g; s/ﬄ/ffl/g\' " \
              + textfile_path
    grep_args = [str(nb_words_around), str(nb_words_around), str(max_snippets)]
    grep_cmd = "grep -i -E -A%s -B%s -m%s"
    for p in escaped_keywords:
        grep_cmd += " -e \"(\\b|\\s)\"%s"
        if right_boundary:
            grep_cmd += "\"(\\b|\\s)\""
        # space escaping needed for grepping for phrases
        grep_args.append(p.replace(' ', '\ '))
    sed_call = shlex.split(sed_cmd)
    grep_call = shlex.split(grep_cmd % tuple(grep_args))
    p1 = Popen(sed_call, stdout=PIPE)
    p2 = Popen(grep_call, stdin=p1.stdout, stdout=PIPE)
    output = p2.communicate()[0]

    result = []
    big_snippets = output.split("--")

    # cut the snippets to match the nb_words_around parameter precisely:
    for s in big_snippets:
        if words_left > 0:
            #using patterns instead of escaped_keywords to make phase search work
            #FIXME: parenthesis are not displayed in snippets
            (small_snippets, words_left) = cut_out_snippet(s, patterns, \
             nb_words_around, words_left, right_boundary)
            #count words
            result += small_snippets
    # combine snippets
    out = ""
    count = 0
    for snippet in result:
        if snippet and count < max_snippets:
            if out:
                out += "<br>"
            out += "..." + snippet + "..."
            count += 1
    return out



def get_tokens(text):
    """
    Tokenize the words in the text

    @param text: text to extract token from
    @return: a list of tokens
    """

    b_pattern = '\\W+'
    tokens = []
    comp_p_b = re.compile(b_pattern, re.IGNORECASE | re.UNICODE)
    previous = 0
    for match in comp_p_b.finditer(text):
        (s, e) = match.span()
        if previous < s:
            tokens.append((previous, s))
        previous = e
    return tokens


def cut_out_snippet(text, patterns, nb_words_around, max_words, right_boundary = True):
    """
    Cut out one ore more snippets, limits to max_words param.
    The snippet can include many occurances of the patterns if they are not
    further appart than 2 * nb_words_around.

    @param text: the text to process
    @param patterns: the patterns to match
    @param nb_words_around: max number of words around the matched pattern
    @param max_words: maximum number of words in the snippet
    @param right_boundary: match the right word boundary or not
    @return: a tuple (list of snippets, max_words (?))
    """

    #index in 'matches'
    next_pattern = 0
    #get token representing words in text
    tokens = get_tokens(text)

    #Build a pattern of the kind keyword1 | keyword2 | keyword3
    if right_boundary:
        pattern = '(\\b)(' + '|'.join(patterns) + ')(\\b)'
    else:
        pattern = '(\\b)(' + '|'.join(patterns) + ')'
    compiled_pattern = re.compile(pattern, re.IGNORECASE | re.UNICODE)

    matches = []
    for x in compiled_pattern.finditer(text):
        matches.append((x.start(), x.end()))

    def matches_any(index):
        """
        Is text[index] a beginning of a pattern?
        """
        if next_pattern < len(matches) and tokens[index][0] == matches[next_pattern][0]:
            return True
        else:
            return False

    snippets = []
    snippet = ""
    last_written_word = -1
    i = 0
    # next_pattern was set above
    #FIXME: it would be better to generate all matching snippets and then score them,
    #choose the most relevant ones.
    while i < len(tokens) and max_words > 3:

        (s, e) = tokens[i]
        # For the last snippet for this record:
        # make the nb_words_around smaller if required by max_words
        # to make sure that at least one pattern is included
        while nb_words_around * 2 + 1 > max_words:
            nb_words_around -= 1

        #can be first or a following pattern in this snippet
        if matches_any(i):
            (sm,em) = matches[next_pattern]
            #move pointer
            next_pattern += 1
            # add part before first or following occurance of a word
            j = max(last_written_word + 1, i - nb_words_around)
            snippet += ' ' + text[tokens[j][0]:tokens[i-1][1]]
            # write the pattern
            snippet += (" " + text[sm:em])
            while tokens[i][1] < em:
                i += 1
            last_written_word = i

            # write the suffix. If pattern found, break
            j = 1
            while j <= nb_words_around and i + j < len(tokens):
                if matches_any(i+j):
                    break
                else:
                    snippet += (" " + text[tokens[i+j][0]:tokens[i+j][1]])
                    last_written_word = i + j
                    j += 1
            i += j
        else:
            i += 1
        # if the snippet is ready (i.e. we didn't just find a new match)
        if snippet != "" and i < len(tokens) and not matches_any(i):
            split_snippet = snippet.split()
            #temporary rule of a thumb to make sure snippets aren't too long
            if len(split_snippet) > nb_words_around * 4:
                snippet = " ".join(split_snippet[0:(nb_words_around * 3)])
            max_words -= len(snippet.split()) #potentially new length
            snippets.append(highlight_matches(snippet, compiled_pattern))
            snippet = ""

    return (snippets, max_words)

