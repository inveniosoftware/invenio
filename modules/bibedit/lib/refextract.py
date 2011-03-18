# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""This is the main body of refextract. It is used to extract references from
   fulltext PDF documents.
"""

__revision__ = "$Id$"

import sys, re
import os, getopt
from time import mktime, localtime, ctime

# make refextract runnable without having to have done the full Invenio installation:
try:
    from invenio.refextract_config \
           import CFG_REFEXTRACT_VERSION, \
                  CFG_REFEXTRACT_KB_JOURNAL_TITLES, \
                  CFG_REFEXTRACT_KB_REPORT_NUMBERS, \
                  CFG_REFEXTRACT_KB_AUTHORS, \
                  CFG_REFEXTRACT_CTRL_FIELD_RECID, \
                  CFG_REFEXTRACT_TAG_ID_REFERENCE, \
                  CFG_REFEXTRACT_IND1_REFERENCE, \
                  CFG_REFEXTRACT_IND2_REFERENCE, \
                  CFG_REFEXTRACT_SUBFIELD_MARKER, \
                  CFG_REFEXTRACT_SUBFIELD_MISC, \
                  CFG_REFEXTRACT_SUBFIELD_REPORT_NUM, \
                  CFG_REFEXTRACT_SUBFIELD_TITLE, \
                  CFG_REFEXTRACT_SUBFIELD_URL, \
                  CFG_REFEXTRACT_SUBFIELD_DOI, \
                  CFG_REFEXTRACT_SUBFIELD_AUTH, \
                  CFG_REFEXTRACT_SUBFIELD_URL_DESCR, \
                  CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS, \
                  CFG_REFEXTRACT_IND1_EXTRACTION_STATS, \
                  CFG_REFEXTRACT_IND2_EXTRACTION_STATS, \
                  CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS, \
                  CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM, \
                  CFG_REFEXTRACT_MARKER_CLOSING_TITLE, \
                  CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID, \
                  CFG_REFEXTRACT_MARKER_CLOSING_SERIES, \
                  CFG_REFEXTRACT_MARKER_CLOSING_VOLUME, \
                  CFG_REFEXTRACT_MARKER_CLOSING_YEAR, \
                  CFG_REFEXTRACT_MARKER_CLOSING_PAGE, \
                  CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, \
                  CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL, \
                  CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL, \
                  CFG_REFEXTRACT_XML_VERSION, \
                  CFG_REFEXTRACT_XML_COLLECTION_OPEN, \
                  CFG_REFEXTRACT_XML_COLLECTION_CLOSE, \
                  CFG_REFEXTRACT_XML_RECORD_OPEN, \
                  CFG_REFEXTRACT_XML_RECORD_CLOSE
except ImportError:
    CFG_REFEXTRACT_VERSION = "Invenio/%s refextract/%s" % ('standalone', 'standalone')
    CFG_REFEXTRACT_KB_JOURNAL_TITLES = "%s/etc/refextract-journal-titles.kb" % '..'
    CFG_REFEXTRACT_KB_REPORT_NUMBERS = "%s/etc/refextract-report-numbers.kb" % '..'
    CFG_REFEXTRACT_CTRL_FIELD_RECID          = "001" ## control-field recid
    CFG_REFEXTRACT_TAG_ID_REFERENCE          = "999" ## ref field tag
    CFG_REFEXTRACT_IND1_REFERENCE            = "C"   ## ref field ind1
    CFG_REFEXTRACT_IND2_REFERENCE            = "5"   ## ref field ind2
    CFG_REFEXTRACT_SUBFIELD_MARKER           = "o"   ## ref marker subfield
    CFG_REFEXTRACT_SUBFIELD_MISC             = "m"   ## ref misc subfield
    CFG_REFEXTRACT_SUBFIELD_REPORT_NUM       = "r"   ## ref reportnum subfield
    CFG_REFEXTRACT_SUBFIELD_TITLE            = "s"   ## ref title subfield
    CFG_REFEXTRACT_SUBFIELD_URL              = "u"   ## ref url subfield
    CFG_REFEXTRACT_SUBFIELD_URL_DESCR        = "z"   ## ref url-text subfield
    CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS   = "999" ## ref-stats tag
    CFG_REFEXTRACT_IND1_EXTRACTION_STATS     = "C"   ## ref-stats ind1
    CFG_REFEXTRACT_IND2_EXTRACTION_STATS     = "6"   ## ref-stats ind2
    CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS = "a"   ## ref-stats subfield
    CFG_REFEXTRACT_SUBFIELD_AUTH             = "h"   ## ref author subfield
    CFG_REFEXTRACT_SUBFIELD_DOI              = "a"   ## ref doi subfield
    CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM = r"</cds.REPORTNUMBER>"
    CFG_REFEXTRACT_MARKER_CLOSING_TITLE      = r"</cds.TITLE>"
    CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID = r"</cds.TITLEibid>"
    CFG_REFEXTRACT_MARKER_CLOSING_SERIES     = r"</cds.SER>"
    CFG_REFEXTRACT_MARKER_CLOSING_VOLUME     = r"</cds.VOL>"
    CFG_REFEXTRACT_MARKER_CLOSING_YEAR       = r"</cds.YR>"
    CFG_REFEXTRACT_MARKER_CLOSING_PAGE       = r"</cds.PG>"
    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND= r"</cds.AUTHstnd>"
    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL= r"</cds.AUTHetal>"
    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL= r"</cds.AUTHincl>"
    CFG_REFEXTRACT_XML_VERSION          = u"""<?xml version="1.0" encoding="UTF-8"?>"""
    CFG_REFEXTRACT_XML_COLLECTION_OPEN  = u"""<collection xmlns="http://www.loc.gov/MARC21/slim">"""
    CFG_REFEXTRACT_XML_COLLECTION_CLOSE = u"""</collection>\n"""
    CFG_REFEXTRACT_XML_RECORD_OPEN      = u"<record>"
    CFG_REFEXTRACT_XML_RECORD_CLOSE     = u"</record>"

# make refextract runnable without having to have done the full Invenio installation:
try:
    from invenio.config import CFG_PATH_GFILE, CFG_PATH_PDFTOTEXT
except ImportError:
    CFG_PATH_GFILE='/usr/bin/file'
    CFG_PATH_PDFTOTEXT='/usr/bin/pdftotext'

# make refextract runnable without having to have done the full Invenio installation:
try:
    from invenio.textutils import encode_for_xml
except ImportError:
    import string
    def encode_for_xml(s):
        "Encode special chars in string so that it would be XML-compliant."
        s = string.replace(s, '&', '&amp;')
        s = string.replace(s, '<', '&lt;')
        return s

cli_opts = {}

## The minimum length of a reference's misc text to be deemed insignificant.
## Values higher than this value reflect meaningful misc text.
## Hence, upon finding a correct semi-colon, but having current misc text
## length less than this value (without other meaningful reference objects:
## report numbers, titles...) then no split will occur.
## (A higher value will increase splitting strictness. i.e. Fewer splits)
semi_colon_misc_text_sensitivity = 60

## The length of misc text between two adjacent authors which is
## deemed as insignificant. As such, when misc text of a length less
## than this value is found, then the latter author group is dumped into misc.
## (A higher value will increase splitting strictness. i.e. Fewer splits)
adjacent_auth_misc_separation = 10

def massage_arxiv_reportnumber(report_number):
    """arXiv report numbers need some massaging
        to change from arXiv-1234-2233(v8) to arXiv.1234.2233(v8)
              and from arXiv1234-2233(v8) to arXiv.1234.2233(v8)
    """
    ## in coming report_number should start with arXiv
    if report_number.find('arXiv') != 0 :
        return report_number
    words = report_number.split('-')
    if len(words) == 3:  ## case of arXiv-yymm-nnnn  (vn)
        words.pop(0) ## discard leading arXiv
        report_number = 'arXiv:' + '.'.join(words).lower()
    elif len(words) == 2: ## case of arXivyymm-nnnn  (vn)
        report_number = 'arXiv:' + words[0][5:] + '.' + words[1].lower()
    return report_number

def get_subfield_content(line,subfield_code):
    """ Given a line (subfield element) and a xml code attribute for a subfield element,
        return the contents of the subfield element.
    """
    content = line.split('<subfield code="'+subfield_code+'">')[1]
    content = content.split('</subfield>')[0]
    return content

def compress_subfields(out,subfield_code):
    """
    For each datafield, compress multiple subfields of type 'subfield_code' into a single one
    e.g. for MISC text, change xml format from:
           <datafield tag="999" ind1="C" ind2="5">
              <subfield code="o">1.</subfield>
              <subfield code="m">J. Dukelsky, S. Pittel and G. Sierra</subfield>
              <subfield code="s">Rev. Mod. Phys. 76 (2004) 643</subfield>
              <subfield code="m">and this is some more misc text</subfield>
           </datafield>
           <datafield tag="999" ind1="C" ind2="5">
              <subfield code="o">2.</subfield>
              <subfield code="m">J. von Delft and D.C. Ralph,</subfield>
              <subfield code="s">Phys. Rep. 345 (2001) 61</subfield>
           </datafield>
        to:
           <datafield tag="999" ind1="C" ind2="5">
              <subfield code="o">1.</subfield>
              <subfield code="m">J. Dukelsky, S. Pittel and G. Sierra and this is some more misc text</subfield>
              <subfield code="s">Rev. Mod. Phys. 76 (2004) 643</subfield>
           </datafield>
           <datafield tag="999" ind1="C" ind2="5">
              <subfield code="o">2.</subfield>
              <subfield code="m">J. von Delft and D.C. Ralph,</subfield>
              <subfield code="s">Phys. Rep. 345 (2001) 61</subfield>
           </datafield>
           """
    in_lines = out.split('\n')
    ## hold the subfield compressed version of the xml, line by line
    new_rec_lines=[]
    ## Used to indicate when the selected subfield has already been reached inside a particular datafield
    position = 0
    ## Where the concatenated misc text is held before appended at the end
    content_text = ""
    ## Components of the misc subfield elements
    subfield_start = "      <subfield code=\"%s\">" % subfield_code
    subfield_end   = "</subfield>"

    for line in in_lines:
        ## If reached the end of the datafield
        if line.find('</datafield>') != -1:
            if len(content_text) > 0:
                ## Insert the concatenated misc contents back where it was first encountered
                ## (dont RIGHTstrip semi-colons, as these may be needed for &amp; or &lt;)
                new_rec_lines[position] = new_rec_lines[position] + content_text.strip(" ,.").lstrip(" ;")+subfield_end
                content_text = ""
            position = 0
            new_rec_lines.append(line)
        ## Found subfield in question, concatenate subfield contents for this single datafield
        elif line.find(subfield_start.strip()) != -1:
            if position == 0:
                ## Save the position of this found subfield
                ## for later insertion into the same place
                new_rec_lines.append(subfield_start)
                position = len(new_rec_lines) - 1
            new_text = get_subfield_content(line,subfield_code)
            if (len(content_text) > 0) and (len(new_text)) > 0:
                ## Append spaces between merged text, if needed
                if (content_text[-1]+new_text[0]).find(" ") == -1:
                    new_text = " "+new_text
            content_text += new_text
        else:
            new_rec_lines.append(line)

    ## Create the readable file from the list of lines.
    new_out = ''
    for rec in new_rec_lines:
        rec = rec.rstrip()
        if rec:
            new_out += rec + '\n'
    return new_out

def restrict_m_subfields(reference_lines):
    """Remove complete datafields which hold ONLY a single 'm' subfield,
       AND where the misc content is too short or too long to be of use.
       Min and max lengths derived by inspection of actual data. """
    min_length = 12
    max_length = 1024
    m_tag=re.compile('\<subfield code=\"m\"\>(.*?)\<\/subfield\>')
    filter_list = []
    m_restricted = 0
    for i in range(len(reference_lines)): ## set up initial filter
        filter_list.append(1)
    for i in range(len(reference_lines)):
        if m_tag.search(reference_lines[i]):
            if (i - 2) >= 0 and (i + 1) < len(reference_lines):
                if reference_lines[i + 1].find('</datafield>') != -1 and \
                    reference_lines[i - 1].find('<subfield code="o">') != -1 and \
                    reference_lines[i - 2].find('<datafield') != -1:
                    ## If both of these are true then its a solitary "m" tag
                    mlength= len(m_tag.search(reference_lines[i]).group(1))
                    if mlength < min_length or mlength > max_length:
                        filter_list[i-2] = filter_list[i-1] = filter_list[i] = filter_list[i+1] = 0
                        m_restricted += 1
    new_reference_lines = []
    for i in range(len(reference_lines)):
        if filter_list[i]:
            new_reference_lines.append(reference_lines[i])
    return m_restricted,new_reference_lines

def filter_processed_references(out):

    """ apply filters to reference lines found - to remove junk"""
    reference_lines = out.split('\n')

    ## Remove too long and too short m tags
    (m_restricted,ref_lines) = restrict_m_subfields(reference_lines)

    if m_restricted:
        a_tag=re.compile('\<subfield code=\"a\"\>(.*?)\<\/subfield\>')
        for i in range(len(ref_lines)):
            ## Checks to see that the datafield has the attribute ind2="6",
            ## Before looking to see if the subfield code attribute is 'a'
            if ref_lines[i].find('<datafield tag="999" ind1="C" ind2="6">') <> -1 and (len(ref_lines)-1) > i:
                ## For each line in this datafield element, try to find the subfield whose code attribute is 'a'
                while ref_lines[i].find('</datafield>') <> -1 and (len(ref_lines)-1) > i:
                    i+=1
                    ## <subfield code="a">Invenio/X.XX.X refextract/X.XX.X-timestamp-err-repnum-title-URL-misc
                    if a_tag.search(ref_lines[i]):  ## remake the "a" tag for new numbe of "m" tags
                        data = a_tag.search(ref_lines[i]).group(1)
                        words1 = data.split()
                        words2 = words1[-1].split('-')
                        old_m = int(words2[-1])
                        words2[-1] = str(old_m - m_restricted)
                        data1 = '-'.join(words2)
                        words1[-1] = data1
                        new_data = ' '.join(words1)
                        ref_lines[i] = '      <subfield code="a">' + new_data + '</subfield>'
                        break
    new_out = ''
    len_filtered = 0
    for rec in ref_lines:
        rec = rec.rstrip()
        if rec:
            new_out += rec + '\n'
            len_filtered += 1
    if cli_opts['verbosity'] >= 1 and len(reference_lines) != len_filtered:
        sys.stdout.write("-----Filter results: unfilter references line length is %d and filtered length is %d\n" \
              %  (len(reference_lines),len_filtered))

    return new_out

def get_url_repair_patterns():
    """Initialise and return a list of precompiled regexp patterns that
       are used to try to re-assemble URLs that have been broken during
       a document's conversion to plain-text.
       @return: (list) of compiled re regexp patterns used for finding
        various broken URLs.
    """
    file_types_list = []
    file_types_list.append(r'h\s*?t\s*?m')           ## htm
    file_types_list.append(r'h\s*?t\s*?m\s*?l')      ## html
    file_types_list.append(r't\s*?x\s*?t')           ## txt
    file_types_list.append(r'p\s*?h\s*?p')           ## php
    file_types_list.append(r'a\s*?s\s*?p\s*?')       ## asp
    file_types_list.append(r'j\s*?s\s*?p')           ## jsp
    file_types_list.append(r'p\s*?y')                ## py (python)
    file_types_list.append(r'p\s*?l')                ## pl (perl)
    file_types_list.append(r'x\s*?m\s*?l')           ## xml
    file_types_list.append(r'j\s*?p\s*?g')           ## jpg
    file_types_list.append(r'g\s*?i\s*?f')           ## gif
    file_types_list.append(r'm\s*?o\s*?v')           ## mov
    file_types_list.append(r's\s*?w\s*?f')           ## swf
    file_types_list.append(r'p\s*?d\s*?f')           ## pdf
    file_types_list.append(r'p\s*?s')                ## ps
    file_types_list.append(r'd\s*?o\s*?c')           ## doc
    file_types_list.append(r't\s*?e\s*?x')           ## tex
    file_types_list.append(r's\s*?h\s*?t\s*?m\s*?l') ## shtml
    pattern_list = []
    pattern_list.append(re.compile(r'(h\s*t\s*t\s*p\s*\:\s*\/\s*\/)', \
                                    re.I|re.UNICODE))
    pattern_list.append(re.compile(r'(f\s*t\s*p\s*\:\s*\/\s*\/\s*)', \
                                    re.I|re.UNICODE))
    pattern_list.append(re.compile(r'((http|ftp):\/\/\s*[\w\d])', \
                                    re.I|re.UNICODE))
    pattern_list.append(re.compile(r'((http|ftp):\/\/([\w\d\s\._\-])+?\s*\/)', \
                                    re.I|re.UNICODE))
    pattern_list.append(re.compile(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)+)', \
                                    re.I|re.UNICODE))
    p_url = \
     re.compile(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)*([\w\d\_\s\-]+\.\s?[\w\d]+))', \
      re.I|re.UNICODE)
    pattern_list.append(p_url)
    ## some possible endings for URLs:
    for x in file_types_list:
        p_url = \
            re.compile(\
              r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*([\w\d\_\-]+\.' + x + u'))', \
              re.I|re.UNICODE)
        pattern_list.append(p_url)
    ## if url last thing in line, and only 10 letters max, concat them
    p_url = \
        re.compile(\
          r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*\s*?([\w\d\_\.\-]\s?){1,10}\s*)$', \
          re.I|re.UNICODE)
    pattern_list.append(p_url)
    return pattern_list

def get_bad_char_replacements():
    """When a document is converted to plain-text from PDF,
       certain characters may result in the plain-text, that are
       either unwanted, or broken. These characters need to be corrected
       or removed. Examples are, certain control characters that would
       be illegal in XML and must be removed; TeX ligatures (etc); broken
       accents such as umlauts on letters that must be corrected.
       This function returns a dictionary of (unwanted) characters to look
       for and the characters that should be used to replace them.
       @return: (dictionary) - { seek -> replace, } or charsacters to
        replace in plain-text.
    """
    replacements = {
        ## Control characters not allowed in XML:
        u'\u2028' : u"",
        u'\u2029' : u"",
        u'\u202A' : u"",
        u'\u202B' : u"",
        u'\u202C' : u"",
        u'\u202D' : u"",
        u'\u202E' : u"",
        u'\u206A' : u"",
        u'\u206B' : u"",
        u'\u206C' : u"",
        u'\u206D' : u"",
        u'\u206E' : u"",
        u'\u206F' : u"",
        u'\uFFF9' : u"",
        u'\uFFFA' : u"",
        u'\uFFFB' : u"",
        u'\uFFFC' : u"",
        u'\uFEFF' : u"",
        u'\uFFFF' : u"", #Unrecognised characters converted to this
        ## Language Tag Code Points:
        u"\U000E0000" : u"",
        u"\U000E0001" : u"",
        u"\U000E0002" : u"",
        u"\U000E0003" : u"",
        u"\U000E0004" : u"",
        u"\U000E0005" : u"",
        u"\U000E0006" : u"",
        u"\U000E0007" : u"",
        u"\U000E0008" : u"",
        u"\U000E0009" : u"",
        u"\U000E000A" : u"",
        u"\U000E000B" : u"",
        u"\U000E000C" : u"",
        u"\U000E000D" : u"",
        u"\U000E000E" : u"",
        u"\U000E000F" : u"",
        u"\U000E0010" : u"",
        u"\U000E0011" : u"",
        u"\U000E0012" : u"",
        u"\U000E0013" : u"",
        u"\U000E0014" : u"",
        u"\U000E0015" : u"",
        u"\U000E0016" : u"",
        u"\U000E0017" : u"",
        u"\U000E0018" : u"",
        u"\U000E0019" : u"",
        u"\U000E001A" : u"",
        u"\U000E001B" : u"",
        u"\U000E001C" : u"",
        u"\U000E001D" : u"",
        u"\U000E001E" : u"",
        u"\U000E001F" : u"",
        u"\U000E0020" : u"",
        u"\U000E0021" : u"",
        u"\U000E0022" : u"",
        u"\U000E0023" : u"",
        u"\U000E0024" : u"",
        u"\U000E0025" : u"",
        u"\U000E0026" : u"",
        u"\U000E0027" : u"",
        u"\U000E0028" : u"",
        u"\U000E0029" : u"",
        u"\U000E002A" : u"",
        u"\U000E002B" : u"",
        u"\U000E002C" : u"",
        u"\U000E002D" : u"",
        u"\U000E002E" : u"",
        u"\U000E002F" : u"",
        u"\U000E0030" : u"",
        u"\U000E0031" : u"",
        u"\U000E0032" : u"",
        u"\U000E0033" : u"",
        u"\U000E0034" : u"",
        u"\U000E0035" : u"",
        u"\U000E0036" : u"",
        u"\U000E0037" : u"",
        u"\U000E0038" : u"",
        u"\U000E0039" : u"",
        u"\U000E003A" : u"",
        u"\U000E003B" : u"",
        u"\U000E003C" : u"",
        u"\U000E003D" : u"",
        u"\U000E003E" : u"",
        u"\U000E003F" : u"",
        u"\U000E0040" : u"",
        u"\U000E0041" : u"",
        u"\U000E0042" : u"",
        u"\U000E0043" : u"",
        u"\U000E0044" : u"",
        u"\U000E0045" : u"",
        u"\U000E0046" : u"",
        u"\U000E0047" : u"",
        u"\U000E0048" : u"",
        u"\U000E0049" : u"",
        u"\U000E004A" : u"",
        u"\U000E004B" : u"",
        u"\U000E004C" : u"",
        u"\U000E004D" : u"",
        u"\U000E004E" : u"",
        u"\U000E004F" : u"",
        u"\U000E0050" : u"",
        u"\U000E0051" : u"",
        u"\U000E0052" : u"",
        u"\U000E0053" : u"",
        u"\U000E0054" : u"",
        u"\U000E0055" : u"",
        u"\U000E0056" : u"",
        u"\U000E0057" : u"",
        u"\U000E0058" : u"",
        u"\U000E0059" : u"",
        u"\U000E005A" : u"",
        u"\U000E005B" : u"",
        u"\U000E005C" : u"",
        u"\U000E005D" : u"",
        u"\U000E005E" : u"",
        u"\U000E005F" : u"",
        u"\U000E0060" : u"",
        u"\U000E0061" : u"",
        u"\U000E0062" : u"",
        u"\U000E0063" : u"",
        u"\U000E0064" : u"",
        u"\U000E0065" : u"",
        u"\U000E0066" : u"",
        u"\U000E0067" : u"",
        u"\U000E0068" : u"",
        u"\U000E0069" : u"",
        u"\U000E006A" : u"",
        u"\U000E006B" : u"",
        u"\U000E006C" : u"",
        u"\U000E006D" : u"",
        u"\U000E006E" : u"",
        u"\U000E006F" : u"",
        u"\U000E0070" : u"",
        u"\U000E0071" : u"",
        u"\U000E0072" : u"",
        u"\U000E0073" : u"",
        u"\U000E0074" : u"",
        u"\U000E0075" : u"",
        u"\U000E0076" : u"",
        u"\U000E0077" : u"",
        u"\U000E0078" : u"",
        u"\U000E0079" : u"",
        u"\U000E007A" : u"",
        u"\U000E007B" : u"",
        u"\U000E007C" : u"",
        u"\U000E007D" : u"",
        u"\U000E007E" : u"",
        u"\U000E007F" : u"",
        ## Musical Notation Scoping
        u"\U0001D173" : u"",
        u"\U0001D174" : u"",
        u"\U0001D175" : u"",
        u"\U0001D176" : u"",
        u"\U0001D177" : u"",
        u"\U0001D178" : u"",
        u"\U0001D179" : u"",
        u"\U0001D17A" : u"",
        u'\u0001' : u"", ## START OF HEADING
        ## START OF TEXT & END OF TEXT:
        u'\u0002' : u"",
        u'\u0003' : u"",
        u'\u0004' : u"", ## END OF TRANSMISSION
        ## ENQ and ACK
        u'\u0005' : u"",
        u'\u0006' : u"",
        u'\u0007' : u"",     # BELL
        u'\u0008' : u"",     # BACKSPACE
        ## SHIFT-IN & SHIFT-OUT
        u'\u000E' : u"",
        u'\u000F' : u"",
        ## Other controls:
        u'\u0010' : u"", ## DATA LINK ESCAPE
        u'\u0011' : u"", ## DEVICE CONTROL ONE
        u'\u0012' : u"", ## DEVICE CONTROL TWO
        u'\u0013' : u"", ## DEVICE CONTROL THREE
        u'\u0014' : u"", ## DEVICE CONTROL FOUR
        u'\u0015' : u"", ## NEGATIVE ACK
        u'\u0016' : u"", ## SYNCRONOUS IDLE
        u'\u0017' : u"", ## END OF TRANSMISSION BLOCK
        u'\u0018' : u"", ## CANCEL
        u'\u0019' : u"", ## END OF MEDIUM
        u'\u001A' : u"", ## SUBSTITUTE
        u'\u001B' : u"", ## ESCAPE
        u'\u001C' : u"", ## INFORMATION SEPARATOR FOUR (file separator)
        u'\u001D' : u"", ## INFORMATION SEPARATOR THREE (group separator)
        u'\u001E' : u"", ## INFORMATION SEPARATOR TWO (record separator)
        u'\u001F' : u"", ## INFORMATION SEPARATOR ONE (unit separator)
        ## \r -> remove it
        u'\r' : u"",
        ## Strange parantheses - change for normal:
        u'\x1c'   : u'(',
        u'\x1d'   : u')',
        ## Some ff from tex:
        u'\u0013\u0010'   : u'\u00ED',
        u'\x0b'   : u'ff',
        ## fi from tex:
        u'\x0c'   : u'fi',
        ## ligatures from TeX:
        u'\ufb00' : u'ff',
        u'\ufb01' : u'fi',
        u'\ufb02' : u'fl',
        u'\ufb03' : u'ffi',
        u'\ufb04' : u'ffl',
        ## Superscripts from TeX
        u'\u2212' : u'-',
        u'\u2013' : u'-',
        ## Word style speech marks:
        u'\u201d' : u'"',
        u'\u201c' : u'"',
        ## pdftotext has problems with umlaut and prints it as diaeresis
        ## followed by a letter:correct it
        ## (Optional space between char and letter - fixes broken
        ## line examples)
        u'\u00A8 a' : u'\u00E4',
        u'\u00A8 e' : u'\u00EB',
        u'\u00A8 i' : u'\u00EF',
        u'\u00A8 o' : u'\u00F6',
        u'\u00A8 u' : u'\u00FC',
        u'\u00A8 y' : u'\u00FF',
        u'\u00A8 A' : u'\u00C4',
        u'\u00A8 E' : u'\u00CB',
        u'\u00A8 I' : u'\u00CF',
        u'\u00A8 O' : u'\u00D6',
        u'\u00A8 U' : u'\u00DC',
        u'\u00A8 Y' : u'\u0178',
        u'\xA8a' : u'\u00E4',
        u'\xA8e' : u'\u00EB',
        u'\xA8i' : u'\u00EF',
        u'\xA8o' : u'\u00F6',
        u'\xA8u' : u'\u00FC',
        u'\xA8y' : u'\u00FF',
        u'\xA8A' : u'\u00C4',
        u'\xA8E' : u'\u00CB',
        u'\xA8I' : u'\u00CF',
        u'\xA8O' : u'\u00D6',
        u'\xA8U' : u'\u00DC',
        u'\xA8Y' : u'\u0178',
        ## More umlaut mess to correct:
        u'\x7fa' : u'\u00E4',
        u'\x7fe' : u'\u00EB',
        u'\x7fi' : u'\u00EF',
        u'\x7fo' : u'\u00F6',
        u'\x7fu' : u'\u00FC',
        u'\x7fy' : u'\u00FF',
        u'\x7fA' : u'\u00C4',
        u'\x7fE' : u'\u00CB',
        u'\x7fI' : u'\u00CF',
        u'\x7fO' : u'\u00D6',
        u'\x7fU' : u'\u00DC',
        u'\x7fY' : u'\u0178',
        u'\x7f a' : u'\u00E4',
        u'\x7f e' : u'\u00EB',
        u'\x7f i' : u'\u00EF',
        u'\x7f o' : u'\u00F6',
        u'\x7f u' : u'\u00FC',
        u'\x7f y' : u'\u00FF',
        u'\x7f A' : u'\u00C4',
        u'\x7f E' : u'\u00CB',
        u'\x7f I' : u'\u00CF',
        u'\x7f O' : u'\u00D6',
        u'\x7f U' : u'\u00DC',
        u'\x7f Y' : u'\u0178',
        ## pdftotext: fix accute accent:
        u'\x13a' : u'\u00E1',
        u'\x13e' : u'\u00E9',
        u'\x13i' : u'\u00ED',
        u'\x13o' : u'\u00F3',
        u'\x13u' : u'\u00FA',
        u'\x13y' : u'\u00FD',
        u'\x13A' : u'\u00C1',
        u'\x13E' : u'\u00C9',
        u'\x13I' : u'\u00CD',
        u'\x13ı' : u'\u00ED', ## Lower case turkish 'i' (dotless i)
        u'\x13O' : u'\u00D3',
        u'\x13U' : u'\u00DA',
        u'\x13Y' : u'\u00DD',
        u'\x13 a' : u'\u00E1',
        u'\x13 e' : u'\u00E9',
        u'\x13 i' : u'\u00ED',
        u'\x13 o' : u'\u00F3',
        u'\x13 u' : u'\u00FA',
        u'\x13 y' : u'\u00FD',
        u'\x13 A' : u'\u00C1',
        u'\x13 E' : u'\u00C9',
        u'\x13 I' : u'\u00CD',
        u'\x13 ı' : u'\u00ED',
        u'\x13 O' : u'\u00D3',
        u'\x13 U' : u'\u00DA',
        u'\x13 Y' : u'\u00DD',
        u'\u00B4 a' : u'\u00E1',
        u'\u00B4 e' : u'\u00E9',
        u'\u00B4 i' : u'\u00ED',
        u'\u00B4 o' : u'\u00F3',
        u'\u00B4 u' : u'\u00FA',
        u'\u00B4 y' : u'\u00FD',
        u'\u00B4 A' : u'\u00C1',
        u'\u00B4 E' : u'\u00C9',
        u'\u00B4 I' : u'\u00CD',
        u'\u00B4 ı' : u'\u00ED',
        u'\u00B4 O' : u'\u00D3',
        u'\u00B4 U' : u'\u00DA',
        u'\u00B4 Y' : u'\u00DD',
        u'\u00B4a' : u'\u00E1',
        u'\u00B4e' : u'\u00E9',
        u'\u00B4i' : u'\u00ED',
        u'\u00B4o' : u'\u00F3',
        u'\u00B4u' : u'\u00FA',
        u'\u00B4y' : u'\u00FD',
        u'\u00B4A' : u'\u00C1',
        u'\u00B4E' : u'\u00C9',
        u'\u00B4I' : u'\u00CD',
        u'\u00B4ı' : u'\u00ED',
        u'\u00B4O' : u'\u00D3',
        u'\u00B4U' : u'\u00DA',
        u'\u00B4Y' : u'\u00DD',
        ## pdftotext: fix grave accent:
        u'\u0060 a' : u'\u00E0',
        u'\u0060 e' : u'\u00E8',
        u'\u0060 i' : u'\u00EC',
        u'\u0060 o' : u'\u00F2',
        u'\u0060 u' : u'\u00F9',
        u'\u0060 A' : u'\u00C0',
        u'\u0060 E' : u'\u00C8',
        u'\u0060 I' : u'\u00CC',
        u'\u0060 O' : u'\u00D2',
        u'\u0060 U' : u'\u00D9',
        u'\u0060a' : u'\u00E0',
        u'\u0060e' : u'\u00E8',
        u'\u0060i' : u'\u00EC',
        u'\u0060o' : u'\u00F2',
        u'\u0060u' : u'\u00F9',
        u'\u0060A' : u'\u00C0',
        u'\u0060E' : u'\u00C8',
        u'\u0060I' : u'\u00CC',
        u'\u0060O' : u'\u00D2',
        u'\u0060U' : u'\u00D9',
        ## \02C7 : caron
        u'\u02C7C' : u'\u010C',
        u'\u02C7c' : u'\u010D',
        u'\u02C7S' : u'\u0160',
        u'\u02C7s' : u'\u0161',
        u'\u02C7Z' : u'\u017D',
        u'\u02C7z' : u'\u017E',
        ## \027 : aa (a with ring above)
        u'\u02DAa' : u'\u00E5',
        u'\u02DAA' : u'\u00C5',
        ## \030 : cedilla
        u'\u0327c' : u'\u00E7',
        u'\u0327C' : u'\u00C7',
        ## \02DC : tilde
        u'\u02DCn' : u'\u00F1',
        u'\u02DCN' : u'\u00D1',
        u'\u02DCo' : u'\u00F5',
        u'\u02DCO' : u'\u00D5',
        u'\u02DCa' : u'\u00E3',
        u'\u02DCA' : u'\u00C3',
        u'\u02DCs' : u'_', ## no valid 's with tilde' character
    }
    return replacements

## precompile some often-used regexp for speed reasons:
re_regexp_character_class = re.compile(r'\[[^\]]+\]', re.UNICODE)
re_space_comma = re.compile(r'\s,', re.UNICODE)
re_space_semicolon = re.compile(r'\s;', re.UNICODE)
re_space_period = re.compile(r'\s\.', re.UNICODE)
re_colon_space_colon = re.compile(r':\s:', re.UNICODE)
re_comma_space_colon = re.compile(r',\s:', re.UNICODE)
re_space_closing_square_bracket = re.compile(r'\s\]', re.UNICODE)
re_opening_square_bracket_space = re.compile(r'\[\s', re.UNICODE)
re_hyphens = re.compile(\
    r'(\\255|\u02D7|\u0335|\u0336|\u2212|\u002D|\uFE63|\uFF0D)', re.UNICODE)
re_multiple_hyphens = re.compile(r'-{2,}', re.UNICODE)
re_multiple_space = re.compile(r'\s{2,}', re.UNICODE)
re_group_captured_multiple_space = re.compile(r'(\s{2,})', re.UNICODE)
re_colon_not_followed_by_numeration_tag = \
                               re.compile(r':(?!\s*<cds)', re.UNICODE|re.I)


## In certain papers, " bf " appears just before the volume of a
## cited item. It is believed that this is a mistyped TeX command for
## making the volume "bold" in the paper.
## The line may look something like this after numeration has been recognised:
## M. Bauer, B. Stech, M. Wirbel, Z. Phys. bf C : <cds.VOL>34</cds.VOL>
## <cds.YR>(1987)</cds.YR> <cds.PG>103</cds.PG>
## The " bf " stops the title from being correctly linked with its series
## and/or numeration and thus breaks the citation.
## The pattern below is used to identify this situation and remove the
## " bf" component:
re_identify_bf_before_vol = \
                re.compile(r' bf ((\w )?: \<cds\.VOL\>)', \
                            re.UNICODE)

## Patterns used for creating institutional preprint report-number
## recognition patterns (used by function "institute_num_pattern_to_regex"):
   ## Recognise any character that isn't a->z, A->Z, 0->9, /, [, ], ' ', '"':
re_report_num_chars_to_escape = \
                re.compile(r'([^\]A-Za-z0-9\/\[ "])', re.UNICODE)
   ## Replace "hello" with hello:
re_extract_quoted_text = (re.compile(r'\"([^"]+)\"', re.UNICODE), r'\g<1>',)
   ## Replace / [abcd ]/ with /( [abcd])?/ :
re_extract_char_class = (re.compile(r' \[([^\]]+) \]', re.UNICODE), \
                          r'( [\g<1>])?')
###


## URL recognition:
## Stand-alone URL (e.g. http://invenio-software.org/ )
re_raw_url = \
 re.compile(r'((https?|s?ftp):\/\/([\w\d\_\.\-])+(:\d{1,5})?(\/\~([\w\d\_\.\-])+)?(\/([\w\d\_\.\-\?\=])+)*(\/([\w\d\_\-]+\.\w{1,6})?)?)', \
             re.UNICODE|re.I)
## HTML marked-up URL (e.g. <a href="http://invenio-software.org/">
## CERN Document Server Software Consortium</a> )
re_html_tagged_url = \
 re.compile(r'(\<a\s+href\s*=\s*([\'"])?(((https?|s?ftp):\/\/)?([\w\d\_\.\-])+(:\d{1,5})?(\/\~([\w\d\_\.\-])+)?(\/([\w\d\_\.\-\?\=])+)*(\/([\w\d\_\-]+\.\w{1,6})?)?)([\'"])?\>([^\<]+)\<\/a\>)', \
             re.UNICODE|re.I)


## Numeration recognition pattern - used to identify numeration
## associated with a title when marking the title up into MARC XML:
## UPDATED: volume numbers can be two numbers with a hyphen in between!
re_recognised_numeration_for_title_plus_series = \
    re.compile(r'^(\s*\.?,?\s*(?P<series>(?:[A-H]|I{1,3}V?|VI{0,3}))?\s*:?\s\<cds\.VOL\>(?P<vol>(?:\d+|(?:\d+\-\d+)))\<\/cds\.VOL> \<cds\.YR\>\((?P<yr>(?:[1-2]\d\d\d))\)\<\/cds\.YR\> \<cds\.PG\>(?P<pg>(?:[RL]?\d+[c]?))\<\/cds\.PG\>)', re.UNICODE)


## Another numeration pattern. This one is designed to match marked-up
## numeration that is essentially an IBID, but without the word "IBID". E.g.:
## <cds.TITLE>J. Phys. A</cds.TITLE> : <cds.VOL>31</cds.VOL>
## <cds.YR>(1998)</cds.YR> <cds.PG>2391</cds.PG>; : <cds.VOL>32</cds.VOL>
## <cds.YR>(1999)</cds.YR> <cds.PG>6119</cds.PG>.
re_numeration_no_ibid_txt = \
          re.compile(r"""
          ^((\s*;\s*|\s+and\s+)(?P<series>(?:[A-H]|I{1,3}V?|VI{0,3}))?\s*:?\s       ## Leading ; : or " and :", and a possible series letter
          \<cds\.VOL\>(?P<vol>\d+|(?:\d+\-\d+))\<\/cds\.VOL>\s             ## Volume
          \<cds\.YR\>\((?P<yr>[12]\d{3})\)\<\/cds\.YR\>\s                 ## year
          \<cds\.PG\>(?P<pg>[RL]?\d+[c]?)\<\/cds\.PG\>)                   ## page
          """, re.UNICODE|re.VERBOSE)

re_title_followed_by_series_markup_tags = \
     re.compile(r'(\<cds.TITLE(?P<ibid>ibid)?\>([^\<]+)\<\/cds.TITLE(?:ibid)?\>\s*.?\s*\<cds\.SER\>([A-H]|(I{1,3}V?|VI{0,3}))\<\/cds\.SER\>)', re.UNICODE)

re_title_followed_by_implied_series = \
     re.compile(r'(\<cds.TITLE(?P<ibid>ibid)?\>([^\<]+)\<\/cds.TITLE(?:ibid)?\>\s*.?\s*([A-H]|(I{1,3}V?|VI{0,3}))\s+:)', re.UNICODE)


re_punctuation = re.compile(r'[\.\,\;\'\(\)\-]', re.UNICODE)

## The following pattern is used to recognise "citation items" that have been
## identified in the line, when building a MARC XML representation of the line:
re_tagged_citation = re.compile(r"""
          \<cds\.                ## open tag: <cds.
          ((?:TITLE(?P<ibid>ibid)?)  ## a TITLE tag
          |VOL                   ## or a VOL tag
          |YR                    ## or a YR tag
          |PG                    ## or a PG tag
          |REPORTNUMBER          ## or a REPORTNUMBER tag
          |SER                   ## or a SER tag
          |URL                   ## or a URL tag
          |DOI                   ## or a DOI tag
          |AUTH(stnd|etal|incl)) ## or an AUTH tag
          (\s\/)?                ## optional /
          \>                     ## closing of tag (>)
          """, \
                                  re.UNICODE|re.VERBOSE)


## is there pre-recognised numeration-tagging within a
## few characters of the start if this part of the line?
re_tagged_numeration_near_line_start = \
                         re.compile(r'^.{0,4}?<CDS (VOL|SER)>', re.UNICODE)

re_ibid = \
   re.compile(r'(-|\b)?((?:(?:IBID(?!EM))|(?:IBIDEM))\.?(\s([A-H]|(I{1,3}V?|VI{0,3})|[1-3]))?)\s?:', \
               re.UNICODE)

re_matched_ibid = re.compile(r'(?:(?:IBID(?!EM))|(?:IBIDEM))(?:[\.,]{0,2}\s*|\s+)([A-H]|(I{1,3}V?|VI{0,3})|[1-3])?', \
                               re.UNICODE)

re_series_from_numeration = re.compile(r'^\.?,?\s+([A-H]|(I{1,3}V?|VI{0,3}))\s+:\s+', \
                               re.UNICODE)

## Obtain the series character from the standardised title text
## Only used when no series letter is obtained from numeration matching
re_series_from_title = re.compile(r"""
    ([^\s].*?)
    (?:[\s\.]+(?:(?P<open_bracket>\()\s*[Ss][Ee][Rr]\.)?
            ([A-H]|(I{1,3}V?|VI{0,3}))
    )?
    (?(open_bracket)\s*\))$   ## Only match the ending bracket if the opening bracket was found""", \
                               re.UNICODE|re.VERBOSE)

## After having processed a line for titles, it may be possible to find more
## numeration with the aid of the recognised titles. The following 2 patterns
## are used for this:

re_correct_numeration_2nd_try_ptn1 = (re.compile(r"""
  \(?([12]\d{3})([A-Za-z]?)\)?,?\s*        ## Year
  (<cds\.TITLE>(\.|[^<])*<\/cds\.TITLE>)   ## Recognised, tagged title
  ,?\s*
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(\d+|(?:\d+\-\d+))      ## The volume (optional "vol"/"no")
  (,\s*|\s+)
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  \-?                                      ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode('\\g<3> : <cds.VOL>\\g<6></cds.VOL> ' \
                                      '<cds.YR>(\\g<1>)</cds.YR> ' \
                                      '<cds.PG>\\g<8></cds.PG>'))

re_correct_numeration_2nd_try_ptn2 = (re.compile(r"""
  \(?([12]\d{3})([A-Za-z]?)\)?,?\s*        ## Year
  (<cds\.TITLE>(\.|[^<])*<\/cds\.TITLE>)   ## Recognised, tagged title
  ,?\s*
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(\d+|(?:\d+\-\d+))      ## The volume (optional "vol"/"no")
  \s?([A-H])\s?                            ## Series
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  \-?                                      ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode('\\g<3> <cds.SER>\\g<7></cds.SER> : ' \
                                      '<cds.VOL>\\g<6></cds.VOL> ' \
                                      '<cds.YR>(\\g<1>)</cds.YR> ' \
                                      '<cds.PG>\\g<8></cds.PG>'))

## precompile some regexps used to search for and standardize
## numeration patterns in a line for the first time:

## Delete the colon and expressions such as Serie, vol, V. inside the pattern
## <serie : volume> E.g. Replace the string """Series A, Vol 4""" with """A 4"""
re_strip_series_and_volume_labels = (re.compile(r'(Serie\s|\bS\.?\s)?([A-H])\s?[:,]\s?(\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(\d+)', re.UNICODE),
                      unicode('\\g<2> \\g<4>'))


## This pattern is not compiled, but rather included in
## the other numeration paterns:
_sre_non_compiled_pattern_nucphysb_subtitle = \
           r'(?:[\(\[]\s*?(?:[Ff][Ss]|[Pp][Mm])\s*?\d{0,4}\s*?[\)\]])?'


## the 4 main numeration patterns:

## Pattern 0 (was pattern 3): <x, vol, page, year>
re_numeration_vol_nucphys_page_yr = (re.compile(r"""
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?   ## The volume (optional "vol"/"no")
  [,:\s]\s?
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?[pP]?[p]?\.?\s?              ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?,?\s?                    ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  \(?(1\d\d\d|20\d\d)\)?                   ## Year
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<4>)</cds.YR> ' \
                                      '<cds.PG>\\g<3></cds.PG> '))

re_numeration_nucphys_vol_page_yr = (re.compile(r"""
  \b
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?
  ([Vv]o?l?\.?|[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?       ## The volume (optional "vol"/"no")
  [,:\s]\s?
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?,?\s?                    ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  \(?(1\d\d\d|20\d\d)\)?                   ## Year
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<4>)</cds.YR> ' \
                                      '<cds.PG>\\g<3></cds.PG> '))

## Pattern 1: <x, vol, year, page>
## <v, [FS]?, y, p>
re_numeration_vol_nucphys_yr_page = (re.compile(r"""
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?   ## The volume (optional "vol"/"no")
  [,:\s]?\s?
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?
  \((1\d\d\d|20\d\d)\),?\s?                ## Year
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<3>)</cds.YR> ' \
                                      '<cds.PG>\\g<4></cds.PG> '))
## <[FS]?, v, y, p>
re_numeration_nucphys_vol_yr_page = (re.compile(r"""
  \b
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?
  ([Vv]o?l?\.?|[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?       ## The volume (optional "vol"/"no")
  [,:\s]?\s?
  \((1\d\d\d|20\d\d)\),?\s?                ## Year
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<3>)</cds.YR> ' \
                                      '<cds.PG>\\g<4></cds.PG> '))


## Pattern 2: <vol, serie, year, page>
## <v, s, [FS]?, y, p>
re_numeration_vol_series_nucphys_yr_page = (re.compile(r"""
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?   ## The volume (optional "vol"/"no")
  ([A-H])\s?                               ## The series
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?\((1\d\d\d|2-\d\d)\),?\s?    ## Year
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' \\g<3> : ' \
                                      '<cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<4>)</cds.YR> ' \
                                      '<cds.PG>\\g<5></cds.PG> '))
## <v, [FS]?, s, y, p
re_numeration_vol_nucphys_series_yr_page = (re.compile(r"""
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?   ## The volume (optional "vol"/"no")
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?([A-H])\s?                   ## The series
  \((1\d\d\d|20\d\d)\),?\s?                ## Year
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' \\g<3> : ' \
                                      '<cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<4>)</cds.YR> ' \
                                      '<cds.PG>\\g<5></cds.PG> '))



## Pattern 4: <vol, serie, page, year>
## <v, s, [FS]?, p, y>
re_numeration_vol_series_nucphys_page_yr = (re.compile(r"""
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?   ## The volume (optional "vol"/"no")
  ([A-H])[,:\s]\s?                         ## The series
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?[pP]?[p]?\.?\s?              ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?,                        ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  ?\s?\(?(1\d\d\d|20\d\d)\)?               ## Year
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' \\g<3> : ' \
                                      '<cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<5>)</cds.YR> ' \
                                      '<cds.PG>\\g<4></cds.PG> '))

## <v, [FS]?, s, p, y>
re_numeration_vol_nucphys_series_page_yr = (re.compile(r"""
  (\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(?<!(?:\/|\d))(\d+|(?:\d+\-\d+))\s?   ## The volume (optional "vol"/"no")
  """ + \
  _sre_non_compiled_pattern_nucphysb_subtitle + \
  r"""[,;:\s]?([A-H])[,:\s]\s?             ## The series
  [pP]?[p]?\.?\s?                          ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  ,?\s?\(?(1\d\d\d|20\d\d)\)?              ## Year
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' \\g<3> : ' \
                                      '<cds.VOL>\\g<2></cds.VOL> ' \
                                      '<cds.YR>(\\g<5>)</cds.YR> ' \
                                      '<cds.PG>\\g<4></cds.PG> '))

## Pattern 5: <year, vol, page>
re_numeration_yr_vol_page = (re.compile(r"""
  (\b|\()(1\d\d\d|20\d\d)\)?(,\s?|\s)                       ## The year (optional brackets)
  ([Vv]o?l?\.?|[Nn]o\.?)?\s?(\d+|(?:\d+\-\d+))[,:\s]\s?     ## The Volume (optional 'vol.' word
  [pP]?[p]?\.?\s?                                           ## Starting page num: optional Pp.
  ([RL]?\d+[c]?)                           ## 1st part of pagenum(optional R/L)
  (?:\-|\255)?                             ## optional separatr between pagenums
  [RL]?\d{0,6}[c]?                         ## optional 2nd component of pagenum
                                           ## preceeded by optional R/L,followed
                                           ## by optional c
  """, re.UNICODE|re.VERBOSE), \
                              unicode(' : <cds.VOL>\\g<5></cds.VOL> ' \
                                      '<cds.YR>(\\g<2>)</cds.YR> ' \
                                      '<cds.PG>\\g<6></cds.PG> '))


## Pattern used to locate references of a doi inside a citation
## This pattern matches both url (http) and 'doi:' or 'DOI' formats
re_doi = (re.compile("""
    ((\(?[Dd][Oo][Ii](\s)*\)?:?(\s)*)       #'doi:' or 'doi' or '(doi)' (upper or lower case)
    |(https?:\/\/dx\.doi\.org\/))?          #or 'http://dx.doi.org/'    (neither has to be present)
    (10\.                                   #10.                        (mandatory for DOI's)
    \d{4}                                   #[0-9] x4
    \/                                      #/
    [\w\-_;\(\)\/\.]+                       #any character
    [\w\-_;\(\)\/])                         #any character excluding a full stop
    """, re.VERBOSE))


def make_auth_regex_str(etal,initial_surname_author=None,surname_initial_author=None):
    """
        Returns a regular expression to be used to identify groups of author names in a citation.
        This method contains patterns for default authors, so no arguments are needed for the
        most reliable form of matching.

        The returned author pattern is capable of:
        1. Identifying single authors, with at least one initial, of the form:
        'Initial. [surname prefix...] Surname'

        2. Identifying multiple authors, each with at least one initial, of the form:
        'Initial. [surname prefix...] Surname, [and] [Initial. [surname prefix...] Surname ... ]'
        ***(Note that a full stop, hyphen or apostrophe after each initial is
        absolutely vital in identifying authors for both of these above methods.
        Initials must also be uppercase.)***

        3. Capture 'et al' statements at the end of author groups (allows for authors with et al
        to be processed differently from 'standard' authors)

        4. Identifying a single author surname name positioned before the phrase 'et al',
        with no initials: 'Surname et al'

        5. Identifying two author surname name positioned before the phrase 'et al',
        with no initials, but separated by 'and' or '&': 'Surname [and|&] Surname et al'

        6. Identifying authors of the form:
        'Surname Initials, Initials Surname [Initials Surname]...'. Some authors choose
        to represent the most important cited author (in a list of authors) by listing first
        their surname, and then their initials. Since this form has little distinguishing
        characteristics which could be used to create a reliable a pattern, at least one
        standard author must be present after it in order to improve the accuracy.

        7. Capture editor notation, of which can take many forms e.g.
        'eds. editors. edited by. etc.'. Authors captured in this way can be treated as
        'editor groups', and hence processed differently if needed from standard authors

        @param etal: (string) The regular expression used to identify 'etal' notation
        @param author: (string) An optional argument, which replaces the default author
        regex used to identify author groups (initials, surnames... etc)

        @return: (string) The full author group identification regex, which will:
        - detect groups of authors in a range of formats, e.g.:
            C. Hayward, V van Edwards, M. J. Woodbridge, and L. Kelloggs et al.,
        - detect whether the author group has been marked up as editors of the doc.
            (therefore they will NOT be marked up as authors) e.g.:
            ed. C Hayward | (ed) V van Edwards  | ed by, M. J. Woodbridge and V van Edwards
            | L. Kelloggs (editors) | M. Jackson (eds.) | ...
        -detect a maximum of two surnames only if the surname(s) is followed by 'et al'
         (must be separated by 'and' if there are two), e.g.:
            Amaldi et al., | Hayward and Yellow et al.,
    """

    if not initial_surname_author:
        ## Standard author, with a maximum of 6 initials, and a surname.
        ## The Initials MUST be uppercase, and MUST have at least a dot, hypen or apostrophe between them.
        initial_surname_author = u"""
    (
        (?<![Vv]olume\s)(?:[A-Z]((\.)|(\’)|(\-[A-Z]?[\s\.\,\’])) ## Initials (1-6) (EACH MUST PRECEED A DOT, APOS. or HYPHEN) (cannot follow 'Volume\s')
        (?:(?:\-\s)|(?:\s\-)|(?:[\-\s]))?){1,5}

        (?:[A-Za-z]\w{1,2}(?:(?:[\-’'`´]\s?)|(?:\s))){0,2}       ## The surname prefix: 1 or 2, 2-3 character prefixes before the surname (e.g. 'van','de')

        [A-Z]\w+[\-’'`´]?\w*                                     ## The surname, which must start with an upper case character (single hyphen allowed)

       (?:(?:[,\.\;]\s*)|([,\.]?\s+)|($))                        ## A comma, dot or space between authors (or an end of line marker)
    )"""

    if not surname_initial_author:
        ## The author name of the form: 'surname initial(s)'
        ## This is sometimes the represention of the first author found inside an author group.
        ## This author pattern is only used to find a maximum of ONE author inside an author group.
        ## Authors of this form MUST have either a comma after the initials, or an 'and',
        ## which denotes the presence of other authors in the author group.
        surname_initial_author = u"""
    (
                                                                 ## The optional surname prefix:
                                                                 ## 1 or 2, 2-3 character prefixes before the surname (e.g. 'van','de')
        (?:[A-Z]\w{1,2}(?:(?:[\-’'`´]\s?)|(?:\s))){0,2}

        [A-Z]\w+[\-’'`´]?\w*                                     ## The surname, which must start with an upper case character (single hyphen allowed)

        (?:(?:\.?\s)|(?:\.\s?))                                  ## The space between the surname and its initials

        (?<!Volume\s)(?:[A-Z](?:(\.)|(\’)|(\-[A-Z]?[\s\.\,\’]))  ## Initials (1-6) (EACH MUST PRECEED A DOT, APOS. or HYPHEN) (cannot follow 'Volume\s')
        (?:(?:\-\s)|(?:\s\-)|(?:[\-\s]))?){1,5}
                                                                 ## Either a comma or an 'and' MUST be present ... OR an end of line marker
                                                                 ## (maybe some space's between authors)
                                                                 ## Uses positive lookahead assertion
        (?:(?:[\.\;]?\s?(?:(\,\s*)|(?:\s*(?=[Aa][Nn][Dd]\s|\&\s))))|(?:$))
    )"""

    ## Pattern used to locate a GROUP of author names in a reference
    ## The format of an author can take many forms:
    ## J. Bloggs, W.-H. Smith, D. De Samuel, G.L. Bayetian, C. Hayward et al.,
    ## (the use of 'et. al' is a giveaway that the preceeding
    ## text was indeed an author name)
    ## This will also match authors which seem to be labeled as editors (with the phrase 'ed.')
    ## In which case, the author will be thrown away later on.
    ## The regex returned has around 100 named groups already (max), so any new groups must be
    ## started using '?:'

    return r"""
     (^|\s+|\()                                                     ## Must be the start of the line, or a space (or an opening bracket in very few cases)
     (?P<es>                                                        ## Look for editor notation before the author
      ((([Ee][Dd]s?|[Ee]dited|[Ee]ditors?)((\.\s?)|(\.?\s)))                    ## 'eds?. '     | 'ed '      | 'ed.'
      |(([Ee][Dd]s?|[Ee]dited|[Ee]ditions?)((\.\s?)|(\.?\s))by(\s|([:,]\s)))    ## 'eds?. by, ' | 'ed. by: ' | 'ed by '  | 'ed. by '| 'ed by: '
      |(\(\s?([Ee][Dd]s?|[Ee]dited|[Ee]ditors?)((\.\s?)|(\.?\s))?\)))           ## '( eds?. )'  | '(ed.)'    | '(ed )'   | '( ed )' | '(ed)'
     )?

                                                                    ## **** (1) , one or two surnames which MUST end with 'et al' (e.g. Amaldi et al.,)
   (?P<author_names>(
         [A-Z][^0-9_\.\s]{2,20}(?:(?:[,\.]\s*)|(?:[,\.]?\s+))
         (?P<multi_surs>
          (?:(?:[Aa][Nn][Dd]|\&)\s+)                                ## Maybe 'and' or '&' tied with another name
          [A-Z][^0-9_\.\s]{3,20}(?:(?:[,\.]\s*)|(?:[,\.]?\s+))
         )?
         (?P<et2>
            %(etal)s\s*                                             ## et al, MUST BE PRESENT however, for this author form
         )
   )|(?:
                                                                    ## **** (2) , The standard author form.. (e.g. J. Bloggs)
                                                                    ## This author form can either start with a normal 'initial surname' author,
                                                                    ## or it can begin with a single 'surname initial' author

       (?:(?P<sur_initial_auth>%(s_i_author)s)|(?:%(i_s_author)s))  ## The first author in the 'author group'

       (?P<multi_auth>
        (?(sur_initial_auth)                                        ## If an author of the form 'surname initial(s)' was found, require
         (?:(?:[Aa][Nn][Dd]|\&)\s+)?                                ## that at least one standard author follows it.
         %(i_s_author)s
        )
        (?:%(i_s_author)s)*                                         ## Then 0 or more standard author names

        (?:
         (?:(?:[Aa][Nn][Dd]|\&)\s+)                                 ## Maybe 'and' or '&' tied with another name
         %(i_s_author)s
        )?

       )
                                                                    ## 'et al' need not be present for either of 'initial surname' or 'surname initial'
                                                                    ## authors
       (?P<et>
        %(etal)s(?:(?:\s*)|(?:$))
       )?
     )
   )# End of all author name patters

    (?P<ee>                                                                             ## Look for editor notation after the author group...
     ((([Ee][Dd]s?|[Ee]dited|[Ee]ditors?)(([\.\,]{0,2}\s)|([\.\,]{1,2}((\s)|($))?)))    ## 'eds?.'   | 'ed. '   | 'ed '
     |(\(([Ee][Dd]s?|[Ee]dited|[Ee]ditors?)([\.\,]{1,2}((\s)|($))?)?\)))                ## '(eds?.)' | '(ed. )' | '(ed)'
    )?
    \)?                                                             ## A possible closing bracket to finish the author group

    """ % { 'etal'       : etal,
            'i_s_author' : initial_surname_author,
            's_i_author' : surname_initial_author }

## Finding an et. al, before author names indicates a bad match!!!
## I.e. could be a title match... ignore it
etal_matches = (' et al.,',' et. al.,',' et. al.',' et.al.,',' et al.',' et al')

re_etal = u"""[Ee][Tt](?:(?:(?:,|\.)\s*)|(?:(?:,|\.)?\s+))[Aa][Ll][,\.]?[,\.]?"""

re_auth = (re.compile(make_auth_regex_str(re_etal),re.VERBOSE|re.UNICODE))

## Given an Auth hit, some misc text, and then another Auth hit straight after,
## (OR a bad_and was found)
## check the entire misc text to see if is 'looks' like an author group, which didn't match
## as a normal author. In which case, append it to the single author group.
## PLEASE use this pattern only against space stripped text.
## IF a bad_and was found (from above).. do re.search using this pattern
## ELIF an auth-misc-auth combo was hit, do re.match using this pattern

re_weaker_author = """
      (?:([A-Z]((\.\s?)|(\.?\s+)|(\-))){1,5}             ## look closely for initials, and less closely at the last name.
      (?:[^\s_<>0-9]+(?:(?:[,\.]\s*)|(?:[,\.]?\s+)))+)"""

## End of line MUST match, since the next string is definitely a portion of an author group (append '$')
re_auth_near_miss = (re.compile(make_auth_regex_str(re_etal,"("+re_weaker_author+")+$"),re.VERBOSE|re.UNICODE))


def make_extra_author_regex_str():
    """ From the authors knowledge-base, construct a single regex holding the or'd possibilities of patterns
    which should be included in $h subfields. The word 'Collaboration' is also converted to 'Coll', and
    used in finding matches. Letter case is not considered during the search.
    @return: (string) The single pattern built from each line in the author knowledge base.
    """
    def add_to_auth_list(s):
        """ Strip the line, replace spaces with '\s' and append 'the' to the start
        and 's' to the end. Add the prepared line to the list of extra kb authors. """
        s = "(?:the\s)?" + s.strip().replace(' ','\s') + "s?"
        auths.append(s)

    ## Build the 'or'd regular expression of the author lines in the author knowledge base
    auths = []
    fpath = CFG_REFEXTRACT_KB_AUTHORS

    try:
        fh = open(fpath, "r")
    except IOError:
        ## problem opening KB for reading, or problem while reading from it:
        emsg = """Error: Could not build knowledge base containing """ \
               """author patterns - failed """ \
               """to read from KB %(kb)s.\n""" \
               % { 'kb' : fpath }
        sys.stderr.write(emsg)
        sys.stderr.flush()
        sys.exit(1)

    for line_num, rawline in enumerate(fh):
        try:
            rawline = rawline.decode("utf-8")
        except UnicodeError:
            sys.stderr.write("*** Unicode problems in %s for line %s\n" \
                             % (fpath, str(line_num)))
            sys.exit(1)
        if (len(rawline) > 0) and (rawline[0] != '#'):
            add_to_auth_list(rawline)
            ## Shorten collaboration to 'coll'
            if rawline.lower().endswith('collaboration\n'):
                coll_version = rawline[:rawline.lower().find('collaboration\n')]+"coll[\.\,]"
                add_to_auth_list(coll_version.strip().replace(' ','\s')+"s?")

    author_match_re = ""
    if len(auths) > 0:
        for a in auths:
            author_match_re = author_match_re + "(?:"+a+")|"
        author_match_re = "(?:(?:[\(\"]?(?:"+author_match_re[:-1] + ")[\)\"]?[\,\.]?\s?(?:and\s)?)+)"

    return author_match_re

## Create the regular expression used to find user-specified 'extra' authors
## (letter case is not concidered when matching)
re_extra_auth = re.compile(make_extra_author_regex_str(),re.IGNORECASE)

## The different forms of arXiv notation
re_arxiv_notation = re.compile("""
    (arxiv)|(e[\-\s]?print:?\s*arxiv)
    """, re.VERBOSE)

# et. al. before J. /// means J is a journal

## a list of patterns used to try to repair broken URLs within reference lines:
re_list_url_repair_patterns = get_url_repair_patterns()

## a dictionary of undesirable characters and their replacements:
undesirable_char_replacements = get_bad_char_replacements()

## General initiation tasks:

def get_recids_and_filepaths(args):
    """from a list of arguments in the form "recid:filepath"
       (["1:filepath", "2:filepath", [...]])
       split each string into 2 parts: the record ID and the filepath.
       @param args: a list of strings
       @param args: a list of strings
       @return: a list of tuples: [(recid, filepath)]
    """

    jobs = []
    for x in args:
        ## Split a maximum of once so as to cater for file names with colons
        ## (e.g. arXiv names)
        items = x.split(":", 1)
        if len(items) != 2:
            sys.stderr.write(u"W: Recid:filepath argument invalid. Skipping.\n")
            continue
        jobs.append((items[0], items[1]))
    return jobs

## components relating to the standardisation and
## recognition of citations in reference lines:

def repair_broken_urls(line):
    """Attempt to repair broken URLs in a line of text.
       (E.g.: remove spaces from the middle of a URL; something like
       that.)
       @param line: (string) the line in which to check for broken URLs.
       @return: (string) the line after any broken URLs have been repaired.
    """
    def _chop_spaces_in_url_match(m):
        """Suppresses spaces in a matched URL.
        """
        return m.group(1).replace(" ", "")
    for ptn in re_list_url_repair_patterns:
        line = ptn.sub(_chop_spaces_in_url_match, line)
    return line

def replace_undesirable_characters(line):
    """Replace certain bad characters in a text line.
       @param line: (string) the text line in which bad characters are to
        be replaced.
       @return: (string) the text line after the bad characters have been
        replaced.
    """
    bad_chars = undesirable_char_replacements.keys()
    for bad_char in bad_chars:
        try:
            line = line.replace(bad_char, \
                                undesirable_char_replacements[bad_char])
        except UnicodeDecodeError:
            pass
    return line

def remove_and_record_multiple_spaces_in_line(line):
    """For a given string, locate all ocurrences of multiple spaces
       together in the line, record the number of spaces found at each
       position, and replace them with a single space.
       @param line: (string) the text line to be processed for multiple
        spaces.
       @return: (tuple) countaining a dictionary and a string. The
        dictionary contains information about the number of spaces removed
        at given positions in the line. For example, if 3 spaces were
        removed from the line at index '22', the dictionary would be set
        as follows: { 22 : 3 }
        The string that is also returned in this tuple is the line after
        multiple-space ocurrences have replaced with single spaces.
    """
    removed_spaces = {}
    ## get a collection of match objects for all instances of
    ## multiple-spaces found in the line:
    multispace_matches = re_group_captured_multiple_space.finditer(line)
    ## record the number of spaces found at each match position:
    for multispace in multispace_matches:
        removed_spaces[multispace.start()] = (multispace.end() \
                                              - multispace.start() - 1)
    ## now remove the multiple-spaces from the line, replacing with a
    ## single space at each position:
    line = re_group_captured_multiple_space.sub(u' ', line)
    return (removed_spaces, line)

def wash_line(line):
    """Wash a text line of certain punctuation errors, replacing them with
       more correct alternatives.  E.g.: the string 'Yes , I like python.'
       will be transformed into 'Yes, I like python.'
       @param line: (string) the line to be washed.
       @return: (string) the washed line.
    """
    line = re_space_comma.sub(',', line)
    line = re_space_semicolon.sub(';', line)
    line = re_space_period.sub('.', line)
    line = re_colon_space_colon.sub(':', line)
    line = re_comma_space_colon.sub(':', line)
    line = re_space_closing_square_bracket.sub(']', line)
    line = re_opening_square_bracket_space.sub('[', line)
    line = re_hyphens.sub('-', line)
    line = re_colon_not_followed_by_numeration_tag.sub(' ', line)
    line = re_multiple_space.sub(' ', line)
    return line

def order_reportnum_patterns_bylen(numeration_patterns):
    """Given a list of user-defined patterns for recognising the numeration
       styles of an institute's preprint references, for each pattern,
       strip out character classes and record the length of the pattern.
       Then add the length and the original pattern (in a tuple) into a new
       list for these patterns and return this list.
       @param numeration_patterns: (list) of strings, whereby each string is
        a numeration pattern.
       @return: (list) of tuples, where each tuple contains a pattern and
        its length.
    """
    def _compfunc_bylen(a, b):
        """Compares regexp patterns by the length of the pattern-text.
        """
        if a[0] < b[0]:
            return 1
        elif a[0] == b[0]:
            return 0
        else:
            return -1
    pattern_list = []
    for pattern in numeration_patterns:
        base_pattern = re_regexp_character_class.sub('1', pattern)
        pattern_list.append((len(base_pattern), pattern))
    pattern_list.sort(_compfunc_bylen)
    return pattern_list

def create_institute_numeration_group_regexp_pattern(patterns):
    """Using a list of regexp patterns for recognising numeration patterns
       for institute preprint references, ordered by length - longest to
       shortest - create a grouped 'OR' or of these patterns, ready to be
       used in a bigger regexp.
       @param patterns: (list) of strings. All of the numeration regexp
        patterns for recognising an institute's preprint reference styles.
       @return: (string) a grouped 'OR' regexp pattern of the numeration
        patterns. E.g.:
           (?P<num>[12]\d{3} \d\d\d|\d\d \d\d\d|[A-Za-z] \d\d\d)
    """
    grouped_numeration_pattern = u""
    if len(patterns) > 0:
        grouped_numeration_pattern = u"(?P<numn>"
        for pattern in patterns:
            grouped_numeration_pattern += \
                  institute_num_pattern_to_regex(pattern[1]) + u"|"
        grouped_numeration_pattern = \
              grouped_numeration_pattern[0:len(grouped_numeration_pattern) - 1]
        grouped_numeration_pattern += u")"
    return grouped_numeration_pattern

def institute_num_pattern_to_regex(pattern):
    """Given a numeration pattern from the institutes preprint report
       numbers KB, convert it to turn it into a regexp string for
       recognising such patterns in a reference line.
       Change:
           \     -> \\
           9     -> \d
           a     -> [A-Za-z]
           v     -> [Vv]  # Tony for arXiv vN
           mm    -> (0[1-9]|1[0-2])
           yy    -> \d{2}
           yyyy  -> [12]\d{3}
           /     -> \/
           s     -> \s*?
       @param pattern: (string) a user-defined preprint reference numeration
        pattern.
       @return: (string) the regexp for recognising the pattern.
    """
    simple_replacements = [ ('9',    r'\d'),
                            ('a',    r'[A-Za-z]'),
                            ('v',    r'[Vv]'),
                            ('mm',   r'(0[1-9]|1[0-2])'),
                            ('yyyy', r'[12]\d{3}'),
                            ('yy',   r'\d\d'),
                            ('s',    r'\s*?'),
                            (r'/',   r'\/')
                          ]
    ## first, escape certain characters that could be sensitive to a regexp:
    pattern = re_report_num_chars_to_escape.sub(r'\\\g<1>', pattern)

    ## now loop through and carry out the simple replacements:
    for repl in simple_replacements:
        pattern = pattern.replace(repl[0], repl[1])

    ## now replace a couple of regexp-like paterns:
    ## quoted string with non-quoted version ("hello" with hello);
    ## Replace / [abcd ]/ with /( [abcd])?/ :
    pattern = re_extract_quoted_text[0].sub(re_extract_quoted_text[1], \
                                             pattern)
    pattern = re_extract_char_class[0].sub(re_extract_char_class[1], \
                                            pattern)

    ## the pattern has been transformed
    return pattern

def build_reportnum_knowledge_base(fpath):
    """Given the path to a knowledge base file containing the details
       of institutes and the patterns that their preprint report
       numbering schemes take, create a dictionary of regexp search
       patterns to recognise these preprint references in reference
       lines, and a dictionary of replacements for non-standard preprint
       categories in these references.

       The knowledge base file should consist only of lines that take one
       of the following 3 formats:

         #####Institute Name####

       (the name of the institute to which the preprint reference patterns
        belong, e.g. '#####LANL#####', surrounded by 5 # on either side.)

         <pattern>

       (numeration patterns for an institute's preprints, surrounded by
        < and >.)

         seek-term       ---   replace-term
       (i.e. a seek phrase on the left hand side, a replace phrase on the
       right hand side, with the two phrases being separated by 3 hyphens.)
       E.g.:
         ASTRO PH        ---astro-ph

       The left-hand side term is a non-standard version of the preprint
       reference category; the right-hand side term is the standard version.

       If the KB file cannot be read from, or an unexpected line is
       encountered in the KB, an error message is output to standard error
       and execution is halted with an error-code 0.

       @param fpath: (string) the path to the knowledge base file.
       @return: (tuple) containing 2 dictionaries. The first contains regexp
        search patterns used to identify preprint references in a line. This
        dictionary is keyed by a tuple containing the line number of the
        pattern in the KB and the non-standard category string.
        E.g.: (3, 'ASTRO PH').
        The second dictionary contains the standardised category string,
        and is keyed by the non-standard category string. E.g.: 'astro-ph'.
    """
    def _add_institute_preprint_patterns(preprint_classifications,
                                         preprint_numeration_ptns,
                                         preprint_reference_search_regexp_patterns,
                                         standardised_preprint_reference_categories,
                                         kb_line_num):
        """For a list of preprint category strings and preprint numeration
           patterns for a given institute, create the regexp patterns for
           each of the preprint types.  Add the regexp patterns to the
           dictionary of search patterns
           (preprint_reference_search_regexp_patterns), keyed by the line
           number of the institute in the KB, and the preprint category
           search string.  Also add the standardised preprint category string
           to another dictionary, keyed by the line number of its position
           in the KB and its non-standardised version.
           @param preprint_classifications: (list) of tuples whereby each tuple
            contains a preprint category search string and the line number of
            the name of institute to which it belongs in the KB.
            E.g.: (45, 'ASTRO PH').
           @param preprint_numeration_ptns: (list) of preprint reference
            numeration search patterns (strings)
           @param preprint_reference_search_regexp_patterns: (dictionary) of
            regexp patterns used to search in document lines.
           @param standardised_preprint_reference_categories: (dictionary)
            containing the standardised strings for preprint reference
            categories. (E.g. 'astro-ph'.)
           @param kb_line_num: (integer) - the line number int the KB at
            which a given institute name was found.
           @return: None
        """
        if len(preprint_classifications) > 0 and \
           len(preprint_numeration_ptns) > 0:
            ## the previous institute had both numeration styles and categories
            ## for preprint references.
            ## build regexps and add them for this institute:
            ## First, order the numeration styles by line-length, and build a
            ## grouped regexp for recognising numeration:
            ordered_patterns = \
              order_reportnum_patterns_bylen(preprint_numeration_ptns)
            ## create a grouped regexp for numeration part of
            ## preprint reference:
            numeration_regexp = \
              create_institute_numeration_group_regexp_pattern(ordered_patterns)

            ## for each "classification" part of preprint references, create a
            ## complete regex:
            ## will be in the style "(categ)-(numatn1|numatn2|numatn3|...)"
            for classification in preprint_classifications:
                search_pattern_str = r'[^a-zA-Z0-9\/\.\-]((?P<categ>' \
                                     + classification[0] + u')' \
                                     + numeration_regexp + r')'
                re_search_pattern = re.compile(search_pattern_str, \
                                                 re.UNICODE)
                preprint_reference_search_regexp_patterns[(kb_line_num, \
                                                          classification[0])] =\
                                                          re_search_pattern
                standardised_preprint_reference_categories[(kb_line_num, \
                                                          classification[0])] =\
                                                          classification[1]

    preprint_reference_search_regexp_patterns  = {}  ## a dictionary of patterns
                                                     ## used to recognise
                                                     ## categories of preprints
                                                     ## as used by various
                                                     ## institutes
    standardised_preprint_reference_categories = {}  ## dictionary of
                                                     ## standardised category
                                                     ## strings for preprint cats
    current_institute_preprint_classifications = []  ## list of tuples containing
                                                     ## preprint categories in
                                                     ## their raw & standardised
                                                     ## forms, as read from KB
    current_institute_numerations = []               ## list of preprint
                                                     ## numeration patterns, as
                                                     ## read from the KB

    ## pattern to recognise an institute name line in the KB
    re_institute_name = re.compile(r'^\#{5}\s*(.+)\s*\#{5}$', re.UNICODE)

    ## pattern to recognise an institute preprint categ line in the KB
    re_preprint_classification = \
                re.compile(r'^\s*(\w.*?)\s*---\s*(\w.*?)\s*$', re.UNICODE)

    ## pattern to recognise a preprint numeration-style line in KB
    re_numeration_pattern      = re.compile(r'^\<(.+)\>$', re.UNICODE)

    kb_line_num = 0    ## when making the dictionary of patterns, which is
                       ## keyed by the category search string, this counter
                       ## will ensure that patterns in the dictionary are not
                       ## overwritten if 2 institutes have the same category
                       ## styles.

    try:
        fh = open(fpath, "r")
        for rawline in fh:
            kb_line_num += 1
            try:
                rawline = rawline.decode("utf-8")
            except UnicodeError:
                sys.stderr.write("*** Unicode problems in %s for line %s\n" \
                                 % (fpath, str(kb_line_num)))
                sys.exit(1)

            m_institute_name = re_institute_name.search(rawline)
            if m_institute_name is not None:
                ## This KB line is the name of an institute
                ## append the last institute's pattern list to the list of
                ## institutes:
                _add_institute_preprint_patterns(current_institute_preprint_classifications,\
                                                 current_institute_numerations,\
                                                 preprint_reference_search_regexp_patterns,\
                                                 standardised_preprint_reference_categories,\
                                                 kb_line_num)

                ## Now start a new dictionary to contain the search patterns
                ## for this institute:
                current_institute_preprint_classifications = []
                current_institute_numerations = []
                ## move on to the next line
                continue

            m_preprint_classification = \
                                     re_preprint_classification.search(rawline)
            if m_preprint_classification is not None:
                ## This KB line contains a preprint classification for
                ## the current institute
                try:
                    current_institute_preprint_classifications.append((m_preprint_classification.group(1), \
                                                                      m_preprint_classification.group(2)))
                except (AttributeError, NameError):
                    ## didn't match this line correctly - skip it
                    pass
                ## move on to the next line
                continue

            m_numeration_pattern = re_numeration_pattern.search(rawline)
            if m_numeration_pattern is not None:
                ## This KB line contains a preprint item numeration pattern
                ## for the current institute
                try:
                    current_institute_numerations.append(m_numeration_pattern.group(1))
                except (AttributeError, NameError):
                    ## didn't match the numeration pattern correctly - skip it
                    pass
                continue

        _add_institute_preprint_patterns(current_institute_preprint_classifications,\
                                         current_institute_numerations,\
                                         preprint_reference_search_regexp_patterns,\
                                         standardised_preprint_reference_categories,\
                                         kb_line_num)

    except IOError:
        ## problem opening KB for reading, or problem while reading from it:
        emsg = """Error: Could not build knowledge base containing """ \
               """institute preprint referencing patterns - failed """ \
               """to read from KB %(kb)s.\n""" \
               % { 'kb' : fpath }
        sys.stderr.write(emsg)
        sys.stderr.flush()
        sys.exit(1)

    ## return the preprint reference patterns and the replacement strings
    ## for non-standard categ-strings:
    return (preprint_reference_search_regexp_patterns, \
            standardised_preprint_reference_categories)

def build_titles_knowledge_base(fpath):
    """Given the path to a knowledge base file, read in the contents
       of that file into a dictionary of search->replace word phrases.
       The search phrases are compiled into a regex pattern object.
       The knowledge base file should consist only of lines that take
       the following format:
         seek-term       ---   replace-term
       (i.e. a seek phrase on the left hand side, a replace phrase on
       the right hand side, with the two phrases being separated by 3
       hyphens.) E.g.:
         ASTRONOMY AND ASTROPHYSICS              ---Astron. Astrophys.

       The left-hand side term is a non-standard version of the title,
       whereas the right-hand side term is the standard version.
       If the KB file cannot be read from, or an unexpected line is
       encountered in the KB, an error
       message is output to standard error and execution is halted with
       an error-code 0.

       @param fpath: (string) the path to the knowledge base file.
       @return: (tuple) containing a list and a dictionary. The list
        contains compiled regex patterns used as search terms and will
        be used to force searching order to match that of the knowledge
        base.
        The dictionary contains the search->replace terms.  The keys of
        the dictionary are the compiled regex word phrases used for
        searching in the reference lines; The values in the dictionary are
        the replace terms for matches.
    """
    ## Private function used for sorting titles by string-length:
    def _cmp_bystrlen_reverse(a, b):
        """A private "cmp" function to be used by the "sort" function of a
           list when ordering the titles found in a knowledge base by string-
           length - LONGEST -> SHORTEST.
           @param a: (string)
           @param b: (string)
           @return: (integer) - 0 if len(a) == len(b); 1 if len(a) < len(b);
            -1 if len(a) > len(b);
        """
        if len(a) > len(b):
            return -1
        elif len(a) < len(b):
            return 1
        else:
            return 0
    ## Initialise vars:
    ## dictionary of search and replace phrases from KB:
    kb = {}
    standardised_titles = {}
    seek_phrases = []
    ## A dictionary of "replacement terms" (RHS) to be inserted into KB as
    ## "seek terms" later, if they were not already explicitly added
    ## by the KB:
    repl_terms = {}

    ## Pattern to recognise a correct knowledge base line:
    p_kb_line = re.compile('^\s*(?P<seek>[^\s].*?)\s*---\s*(?P<repl>[^\s].*?)\s*$', \
                            re.UNICODE)

    try:
        fh = open(fpath, "r")
        count = 0
        for rawline in fh:

            if rawline.find('\\') != -1:
                continue
            count += 1
            ## Test line to ensure that it is a correctly formatted
            ## knowledge base line:
            try:
                rawline = rawline.decode("utf-8").rstrip("\n")
            except UnicodeError:
                sys.stderr.write("*** Unicode problems in %s for line %s\n" \
                                 % (fpath, str(count)))
                sys.exit(1)

            ## Extract the seek->replace terms from this KB line:
            m_kb_line = p_kb_line.search(rawline)
            if m_kb_line is not None:

                ## good KB line
                ## Add the 'replacement term' into the dictionary of
                ## replacement terms:
                repl_terms[m_kb_line.group('repl')] = None

                ## Get the "seek term":
                seek_phrase = m_kb_line.group('seek')
                if len(seek_phrase) > 1:
                    ## add the phrase from the KB if the 'seek' phrase is longer
                    ## than 1 character:
                    ## compile the seek phrase into a pattern:
                    seek_ptn = re.compile(r'(?<!\/)\b(' + \
                                           re.escape(seek_phrase) + \
                                           r')[^A-Z0-9]', re.UNICODE)
                    if not kb.has_key(seek_phrase):
                        kb[seek_phrase] = seek_ptn
                        standardised_titles[seek_phrase] = \
                                                         m_kb_line.group('repl')
                        seek_phrases.append(seek_phrase)
            else:
                ## KB line was not correctly formatted - die with error
                emsg = """Error: Could not build list of journal titles\n""" \
                       """- KB %(kb)s has errors.\n""" \
                       """- Mapping: %(mapping)s\n""" \
                       % { 'kb' : fpath , 'mapping' : rawline}
                sys.stderr.write(emsg)
                sys.exit(1)
        fh.close()

        ## Now, for every 'replacement term' found in the KB, if it is
        ## not already in the KB as a "search term", add it:
        for repl_term in repl_terms.keys():
            raw_repl_phrase = repl_term.upper()
            raw_repl_phrase = re_punctuation.sub(u' ', raw_repl_phrase)
            raw_repl_phrase = \
                 re_group_captured_multiple_space.sub(u' ', \
                                                       raw_repl_phrase)
            raw_repl_phrase = raw_repl_phrase.strip()
            if not kb.has_key(raw_repl_phrase):
                ## The replace-phrase was not in the KB as a seek phrase
                ## It should be added.
                seek_ptn = re.compile(r'(?<!\/)\b(' + \
                                       re.escape(raw_repl_phrase) + \
                                       r')[^A-Z0-9]', re.UNICODE)
                kb[raw_repl_phrase] = seek_ptn
                standardised_titles[raw_repl_phrase] = \
                                                 repl_term
                seek_phrases.append(raw_repl_phrase)

        ## Sort the titles by string length (long - short)
        seek_phrases.sort(_cmp_bystrlen_reverse)
    except IOError:
        ## problem opening KB for reading, or problem while reading from it:
        emsg = """Error: Could not build list of journal titles - failed """ \
               """to read from KB %(kb)s.\n""" \
               % { 'kb' : fpath }
        sys.stderr.write(emsg)
        sys.stderr.flush()
        sys.exit(1)

    ## return the raw knowledge base:
    return (kb, standardised_titles, seek_phrases)

def standardize_and_markup_numeration_of_citations_in_line(line):
    """Given a reference line, attempt to locate instances of citation
       'numeration' in the line.
       Upon finding some numeration, re-arrange it into a standard
       order, and mark it up with tags.
       Will process numeration in the following order:
            Delete the colon and expressions such as Serie, vol, V.
            inside the pattern <serie : volume>
            E.g.: Replace the string 'Series A, Vol 4' with 'A 4'
            Then, the 4 main numeration patterns:
            Pattern 0 (was pattern 3): <x, vol, page, year>
            <v, [FS]?, p, y>
            <[FS]?, v, p, y>
            Pattern 1: <x, vol, year, page>
            <v, [FS]?, y, p>
            <[FS]?, v, y, p>
            Pattern 2: <vol, serie, year, page>
            <v, s, [FS]?, y, p>
            <v, [FS]?, s, y, p
            Pattern 4: <vol, serie, page, year>
            <v, s, [FS]?, p, y>
            <v, [FS]?, s, p, y>

       @param line: (string) the reference line.
       @return: (string) the reference line after numeration has been checked
        and possibly recognized/marked-up.
    """
    line = re_strip_series_and_volume_labels[0].sub(re_strip_series_and_volume_labels[1], line)
    line = re_numeration_vol_nucphys_page_yr[0].sub(re_numeration_vol_nucphys_page_yr[1], line)
    line = re_numeration_nucphys_vol_page_yr[0].sub(re_numeration_nucphys_vol_page_yr[1], line)
    line = re_numeration_vol_nucphys_yr_page[0].sub(re_numeration_vol_nucphys_yr_page[1], line)
    line = re_numeration_nucphys_vol_yr_page[0].sub(re_numeration_nucphys_vol_yr_page[1], line)
    line = re_numeration_vol_series_nucphys_yr_page[0].sub(re_numeration_vol_series_nucphys_yr_page[1], line)
    line = re_numeration_vol_nucphys_series_yr_page[0].sub(re_numeration_vol_nucphys_series_yr_page[1], line)
    line = re_numeration_vol_series_nucphys_page_yr[0].sub(re_numeration_vol_series_nucphys_page_yr[1], line)
    line = re_numeration_vol_nucphys_series_page_yr[0].sub(re_numeration_vol_nucphys_series_page_yr[1], line)
    line = re_numeration_yr_vol_page[0].sub(re_numeration_yr_vol_page[1], \
                                             line)
    return line

def identify_preprint_report_numbers(line,
                                     preprint_repnum_search_kb,
                                     preprint_repnum_standardised_categs):
    """Attempt to identify all preprint report numbers in a reference
       line.
       Report numbers will be identified, their information (location
       in line, length in line, and standardised replacement version)
       will be recorded, and they will be replaced in the working-line
       by underscores.
       @param line: (string) - the working reference line.
       @param preprint_repnum_search_kb: (dictionary) - contains the
        regexp patterns used to identify preprint report numbers.
       @param preprint_repnum_standardised_categs: (dictionary) -
        contains the standardised 'category' of a given preprint report
        number.
       @return: (tuple) - 3 elements:
           * a dictionary containing the lengths in the line of the
             matched preprint report numbers, keyed by the index at
             which each match was found in the line.
           * a dictionary containing the replacement strings (standardised
             versions) of preprint report numbers that were matched in
             the line.
           * a string, that is the new version of the working reference
             line, in which any matched preprint report numbers have been
             replaced by underscores.
        Returned tuple is therefore in the following order:
            (matched-reportnum-lengths, matched-reportnum-replacements,
             working-line)
    """

    def _by_len(a, b):
        """Comparison function used to sort a list by the length of the
           strings in each element of the list.
        """
        if len(a[1]) < len(b[1]):
            return 1
        elif len(a[1]) == len(b[1]):
            return 0
        else:
            return -1
    repnum_matches_matchlen = {}  ## info about lengths of report numbers
                                  ## matched at given locations in line
    repnum_matches_repl_str = {}  ## standardised report numbers matched
                                  ## at given locations in line

    preprint_repnum_categs = preprint_repnum_standardised_categs.keys()
    preprint_repnum_categs.sort(_by_len)

    ## try to match preprint report numbers in the line:
    for categ in preprint_repnum_categs:
        ## search for all instances of the current report
        ## numbering style in the line:
        repnum_matches_iter = preprint_repnum_search_kb[categ].finditer(line)
        ## for each matched report number of this style:
        for repnum_match in repnum_matches_iter:
            ## Get the matched text for the numeration part of the
            ## preprint report number:
            numeration_match = repnum_match.group('numn')
            ## clean/standardise this numeration text:
            numeration_match = numeration_match.replace(" ", "-")
            numeration_match = re_multiple_hyphens.sub("-", numeration_match)
            numeration_match = numeration_match.replace("/-", "/")
            numeration_match = numeration_match.replace("-/", "/")
            numeration_match = numeration_match.replace("-/-", "/")
            ## replace the found preprint report number in the
            ## string with underscores (this will replace chars in the lower-cased line):
            line = line[0:repnum_match.start(1)] \
                   + "_"*len(repnum_match.group(1)) + line[repnum_match.end(1):]
            ## record the information about the matched preprint report number:
            ## total length in the line of the matched preprint report number:
            repnum_matches_matchlen[repnum_match.start(1)] = \
                                                    len(repnum_match.group(1))
            ## standardised replacement for the matched preprint report number:
            repnum_matches_repl_str[repnum_match.start(1)] = \
                                    preprint_repnum_standardised_categs[categ] \
                                    + numeration_match
    ## return recorded information about matched report numbers, along with
    ## the newly changed working line:
    return (repnum_matches_matchlen, repnum_matches_repl_str, line)

def limit_m_tags(xml_file, length_limit):
    """Limit size of miscellaneous tags"""
    temp_xml_file = xml_file + '.temp'
    try:
        ofilehdl = open(xml_file, 'r')
    except IOError:
        sys.stdout.write("***%s\n\n" % xml_file)
        raise IOError("Cannot open %s to read!" % xml_file)
    try:
        nfilehdl = open(temp_xml_file, 'w')
    except IOError:
        sys.stdout.write("***%s\n\n" % temp_xml_file)
        raise IOError("Cannot open %s to write!" % temp_xml_file)

    for line in ofilehdl:
        line_dec = line.decode("utf-8")
        start_ind = line_dec.find('<subfield code="m">')
        if start_ind != -1:
            ## This line is an "m" line:
            last_ind = line_dec.find('</subfield>')
            if last_ind != -1:
                ## This line contains the end-tag for the "m" section
                leng = last_ind-start_ind - 19
                if leng > length_limit:
                    ## want to truncate on a blank to avoid problems..
                    end = start_ind + 19 + length_limit
                    for lett in range(end - 1, last_ind):
                        xx = line_dec[lett:lett+1]
                        if xx == ' ':
                            break
                        else:
                            end += 1
                    middle = line_dec[start_ind+19:end-1]
                    line_dec = start_ind * ' ' + '<subfield code="m">' + \
                              middle + '  !Data truncated! '  + '</subfield>\n'
        nfilehdl.write("%s" % line_dec.encode("utf-8"))
    nfilehdl.close()
    ## copy back to original file name
    os.rename(temp_xml_file, xml_file)

def identify_and_tag_URLs(line):
    """Given a reference line, identify URLs in the line, record the
       information about them, and replace them with a "<cds.URL />" tag.
       URLs are identified in 2 forms:
        + Raw: http://invenio-software.org/
        + HTML marked-up: <a href="http://invenio-software.org/">CERN Document
          Server Software Consortium</a>
       These URLs are considered to have 2 components: The URL itself
       (url string); and the URL description. The description is effectively
       the text used for the created Hyperlink when the URL is marked-up
       in HTML. When an HTML marked-up URL has been recognised, the text
       between the anchor tags is therefore taken as the URL description.
       In the case of a raw URL recognition, however, the URL itself will
       also be used as the URL description.
       For example, in the following reference line:
        [1] See <a href="http://invenio-software.org/">CERN Document Server
        Software Consortium</a>.
       ...the URL string will be "http://invenio-software.org/" and the URL
       description will be
       "CERN Document Server Software Consortium".
       The line returned from this function will be:
        [1] See <cds.URL />
       In the following line, however:
        [1] See http //invenio-software.org/ for more details.
       ...the URL string will be "http://invenio-software.org/" and the URL
       description will also be "http://invenio-software.org/".
       The line returned will be:
        [1] See <cds.URL /> for more details.

       @param line: (string) the reference line in which to search for URLs.
       @return: (tuple) - containing 2 items:
        + the line after URLs have been recognised and removed;
        + a list of 2-item tuples where each tuple represents a recognised URL
          and its description:
            [(url, url-description), (url, url-description), ... ]
       @Exceptions raised:
        + an IndexError if there is a problem with the number of URLs
          recognised (this should not happen.)
    """
    ## Take a copy of the line:
    line_pre_url_check = line
    ## Dictionaries to record details of matched URLs:
    found_url_full_matchlen = {}
    found_url_urlstring     = {}
    found_url_urldescr      = {}

    ## List to contain details of all matched URLs:
    identified_urls = []

    ## Attempt to identify and tag all HTML-MARKED-UP URLs in the line:
    m_tagged_url_iter = re_html_tagged_url.finditer(line)
    for m_tagged_url in m_tagged_url_iter:
        startposn = m_tagged_url.start()       ## start position of matched URL
        endposn   = m_tagged_url.end()         ## end position of matched URL
        matchlen  = len(m_tagged_url.group(0)) ## total length of URL match

        found_url_full_matchlen[startposn] = matchlen
        found_url_urlstring[startposn]     = m_tagged_url.group(3)
        found_url_urldescr[startposn]      = m_tagged_url.group(15)
        ## temporarily replace the URL match with underscores so that
        ## it won't be re-found
        line = line[0:startposn] + u"_"*matchlen + line[endposn:]


    ## Attempt to identify and tag all RAW (i.e. not
    ## HTML-marked-up) URLs in the line:
    m_raw_url_iter = re_raw_url.finditer(line)
    for m_raw_url in m_raw_url_iter:
        startposn = m_raw_url.start()       ## start position of matched URL
        endposn   = m_raw_url.end()         ## end position of matched URL
        matchlen  = len(m_raw_url.group(0)) ## total length of URL match
        matched_url = m_raw_url.group(1)
        if len(matched_url) > 0 and matched_url[-1] in (".", ","):
            ## Strip the full-stop or comma from the end of the url:
            matched_url = matched_url[:-1]
        found_url_full_matchlen[startposn] = matchlen
        found_url_urlstring[startposn]     = matched_url
        found_url_urldescr[startposn]      = matched_url
        ## temporarily replace the URL match with underscores
        ## so that it won't be re-found
        line = line[0:startposn] + u"_"*matchlen + line[endposn:]

    ## Now that all URLs have been identified, insert them
    ## back into the line, tagged:
    found_url_positions = found_url_urlstring.keys()
    found_url_positions.sort()
    found_url_positions.reverse()
    for url_position in found_url_positions:
        line = line[0:url_position] + "<cds.URL />" \
               + line[url_position + found_url_full_matchlen[url_position]:]

    ## The line has been rebuilt. Now record the information about the
    ## matched URLs:
    found_url_positions = found_url_urlstring.keys()
    found_url_positions.sort()
    for url_position in found_url_positions:
        identified_urls.append((found_url_urlstring[url_position], \
                                found_url_urldescr[url_position]))

    if len(identified_urls) != len(found_url_positions):
        ## Somehow the number of URLs found doesn't match the number of
        ## URLs recorded in "identified_urls". Raise an IndexError.
        msg = """Error: The number of URLs found in the reference line """ \
              """does not match the number of URLs recorded in the """ \
              """list of identified URLs!\nLine pre-URL checking: %s\n""" \
              """Line post-URL checking: %s\n""" \
              % (line_pre_url_check, line)
        raise IndexError(msg)

    ## return the line containing the tagged URLs:
    return (line, identified_urls)

def identify_and_tag_DOI(line):
    """takes a single citation line and attempts to locate any DOI references.
       DOI references are recognised in both http (url) format and also the
       standard DOI notation (DOI: ...)
       @param line: (string) the reference line in which to search for DOI's.
       @return: the tagged line and a list of DOI strings (if any)
    """
    ## Used to hold the DOI strings in the citation line
    doi_strings = []

    ## Run the DOI pattern on the line, returning the re.match objects
    matched_doi = re_doi.finditer(line)
    ## For each match found in the line
    for match in matched_doi:
        ## Store the start and end position
        start = match.start()
        end = match.end()
        ## Get the actual DOI string (remove the url part of the doi string)
        doi_phrase = match.group(6)


        ## Replace the entire matched doi with a tag
        line = line[0:start]+"<cds.DOI />"+line[end:]
        ## Add the single DOI string to the list of DOI strings
        doi_strings.append(doi_phrase)

    return (line, doi_strings)


def identify_and_tag_authors(line):
    """Given a reference, look for a group of author names,
       place tags around the author group, return the newly tagged line.
    """

    def identify_and_tag_extra_authors(line):
        """Given a line where Authors have been tagged, and all other tags and content has
           been replaced with underscores, go through and try to identify extra items of data
           which should be placed into 'h' subfields.
           Later on, these tagged pieces of information will be merged into the content of the
           most recently found author. This is separated from the author tagging procedure since
           separate tags can be used, which won't influence the reference splitting heuristics
           (used when looking at mulitple <AUTH> tags in a line).
        """
        if re_extra_auth:
            extra_authors = re_extra_auth.finditer(line)
            positions = []
            for match in extra_authors:
                positions.append({  'start'       : match.start(),
                                    'end'         : match.end()})
            positions.reverse()
            for p in positions:
                line = line[:p['start']] + "<cds.AUTHincl>" \
                    + line[p['start']:p['end']].strip(".,:;- []") + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL + line[p['end']:]
        return line


    output_line = line
    tmp_line = line
    ## Firstly, go through and change ALL TAGS and their contents to underscores
    ## author content can be checked for underscores later on
    tag_start = tmp_line.find("<cds.")
    url_start = tmp_line.find("<cds.URL />")
    doi_start = tmp_line.find("<cds.DOI />")
    while tag_start != -1:
        if (tag_start == url_start) or (tag_start == doi_start):
            tag_end = tag_start + len("<cds.XXX />")
            line = line[:tag_start]+"_"*(tag_end - tag_start)+line[tag_end:]
            tmp_line = "_"*len(tmp_line[:tag_end]) + tmp_line[tag_end:]

            url_start = tmp_line.find("<cds.URL />")
            doi_start = tmp_line.find("<cds.DOI />")
            tag_start = tmp_line.find("<cds.",tag_end)
        else:
            tag_start_length = (tmp_line.find(">",tag_start) + 1) - tag_start
            final_length = (tmp_line.find(">",tmp_line.find("</cds.",tag_start+tag_start_length)) + 1) - tag_start
            tag_end = tag_start+final_length
            ## Replace title tags, and the title itself with underscores (this line is used to find authors)
            line = line[:tag_start]+("_"*final_length)+line[tag_end:]
            ## Place underscores in the wake of the search
            tmp_line = "_"*len(tmp_line[:tag_end]) + tmp_line[tag_end:]
            tag_start = tmp_line.find("<cds.",tag_end)

    ## Find as many author groups (collections of author names) as possible from the 'title-hidden' line
    matched_authors = re_auth.finditer(line)
    ## If there is at least one matched author group
    if matched_authors:
        matched_positions = []
        preceeding_text_string = line
        preceeding_text_start = 0
        for auth_no, match in enumerate(matched_authors):
            ## Only if there are no underscores or closing arrows found in the matched author group
            ## This must be checked for here, as it cannot be applied to the re without clashing with
            ## other Unicode characters
            if line[match.start():match.end()].find("_") == -1:
                ## Has the group with name 'et' (for 'et al') been found in the pattern?
                ## Has the group with name 'es' (for ed. before the author) been found in the pattern?
                ## Has the group with name 'ee' (for ed. after the author) been found in the pattern?
                matched_positions.append({  'start'       : match.start(),
                                            'end'         : match.end(),
                                            'etal'        : match.group('et'),
                                            'ed_start'    : match.group('es'),
                                            'ed_end'      : match.group('ee'),
                                            'multi_auth'  : match.group('multi_auth'),
                                            'multi_surs'  : match.group('multi_surs'),
                                            'text_before' : preceeding_text_string[preceeding_text_start:match.start()],
                                            'auth_no'     : auth_no,
                                            'author_names': match.group('author_names')})
                ## Save the end of the match, from where to snip the misc text found before an author match
                preceeding_text_start = match.end()

        ## Work backwards to avoid index problems when adding AUTH tags
        matched_positions.reverse()
        for m in matched_positions:
            dump_in_misc = False
            start = m['start']
            end = m['end']

            ## Check the text before the current match to see if it has a bad 'et al'
            lower_text_before = m['text_before'].strip().lower()
            for e in etal_matches:
                if lower_text_before.endswith(e):
                    ## If so, this author match is likely to be a bad match on a missed title
                    dump_in_misc = True
                    break

            ## An AND found here likely indicates a missed author before this text
            ## Thus, triggers weaker author searching, within the previous misc text
            ## (Check the text before the current match to see if it has a bad 'and')
            ## A bad 'and' will only be denoted as such if there exists only one author after it
            ## and the author group is legit (not to be dumped in misc)
            if not dump_in_misc and not (m['multi_auth'] or m['multi_surs']) \
                and (lower_text_before.endswith(' and')):
                ## Search using a weaker author pattern to try and find the missed author(s) (cut away the end 'and')
                weaker_match = re_auth_near_miss.match(m['text_before'])
                if weaker_match and not (weaker_match.group('es') or weaker_match.group('ee')):
                    ## Change the start of the author group to include this new author group
                    start = start - (len(m['text_before']) - weaker_match.start())
                ## Still no match, do not add tags for this author match.. dump it into misc
                else:
                    dump_in_misc = True

            add_to_misc = ""
            ## If a semi-colon was found at the end of this author group, keep it in misc
            ## so that it can be looked at for splitting heurisitics
            if (len(output_line) > m['end']):
                if output_line[m['end']].strip(" ,.") == ';':
                    add_to_misc = ';'

            ## ONLY wrap author data with tags IF there is no evidence that it is an
            ## ed. author. (i.e. The author is not referred to as an editor)
            ## Does this author group string have 'et al.'?
            if m['etal'] and not(m['ed_start'] or m['ed_end'] or dump_in_misc):
                ## Insert the etal tag...
                ## Replace the found 'et al' phrase with the standardised version
                tmp_stnd_etal_line = re.sub(re_etal,'et al',output_line[start:end].strip(".,:;- []()"), re.IGNORECASE)
                output_line = output_line[:start] + "<cds.AUTHetal>" \
                    + tmp_stnd_etal_line \
                    + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL + add_to_misc + output_line[end:]
            elif not(m['ed_start'] or m['ed_end'] or dump_in_misc):
                ## Insert the std (standard) tag
                output_line = output_line[:start] + "<cds.AUTHstnd>" \
                    + output_line[start:end].strip(".,:;- []()") \
                    + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND + add_to_misc + output_line[end:]
            ## Apply the 'include in $h' method to author groups marked as editors
            elif (m['ed_start'] or m['ed_end']):
                if m['multi_auth']:
                    ed_notation = " (eds.)"
                else:
                    ed_notation = " (ed.)"
                ## remove any characters which denote this author group to be editors, just take the
                ## author names, and append '(ed.)'
                output_line = output_line[:start] + "<cds.AUTHincl>" \
                    + m['author_names'].strip(".,:;- []()") \
                    + ed_notation + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL + add_to_misc + output_line[end:]


    ## Now that authors have been tagged, search for the extra information which should be included in $h
    ## Tag for this datafield, merge into one $h subfield later on
    output_line = identify_and_tag_extra_authors(output_line)

    return output_line


def identify_periodical_titles(line,
                               periodical_title_search_kb,
                               periodical_title_search_keys):
    """Attempt to identify all periodical titles in a reference line.
       Titles will be identified, their information (location in line,
       length in line, and non-standardised version) will be recorded,
       and they will be replaced in the working line by underscores.
       @param line: (string) - the working reference line.
       @param periodical_title_search_kb: (dictionary) - contains the
        regexp patterns used to search for a non-standard TITLE in the
        working reference line. Keyed by the TITLE string itself.
       @param periodical_title_search_keys: (list) - contains the non-
        standard periodical TITLEs to be searched for in the line. This
        list of titles has already been ordered and is used to force
        the order of searching.
       @return: (tuple) containing 4 elements:
                        + (dictionary) - the lengths of all titles
                                         matched at each given index
                                         within the line.
                        + (dictionary) - the text actually matched for
                                         each title at each given
                                         index within the line.
                        + (string)     - the working line, with the
                                         titles removed from it and
                                         replaced by underscores.
                        + (dictionary) - the totals for each bad-title
                                         found in the line.
    """
    title_matches_matchlen  = {}  ## info about lengths of periodical titles
                                  ## matched at given locations in the line
    title_matches_matchtext = {}  ## the text matched at the given line
                                  ## location (i.e. the title itself)
    titles_count = {}             ## sum totals of each 'bad title found in
                                  ## line.

    ## Begin searching:
    for title in periodical_title_search_keys:
        ## search for all instances of the current periodical title
        ## in the line:
        title_matches_iter = periodical_title_search_kb[title].finditer(line)

        ## for each matched periodical title:
        for title_match in title_matches_iter:
            if not titles_count.has_key(title):
                ## Add this title into the titles_count dictionary:
                titles_count[title] = 1
            else:
                ## Add 1 to the count for the given title:
                titles_count[title] += 1

            ## record the details of this title match:
            ## record the match length:
            title_matches_matchlen[title_match.start()] = \
                                           len(title_match.group(0)) - 1

            ## record the matched non-standard version of the title:
            title_matches_matchtext[title_match.start()] = title

            ## replace the matched title text in the line it n * '_',
            ## where n is the length of the matched title:
            line = u"".join((line[0:title_match.start(1)],
                            u"_"*len(title_match.group(1)),
                            line[title_match.end(1):]))

    ## return recorded information about matched periodical titles,
    ## along with the newly changed working line:
    return (title_matches_matchlen, title_matches_matchtext, line, titles_count)


def identify_ibids(line):
    """Find IBIDs within the line, record their position and length,
       and replace them with underscores.
       @param line: (string) the working reference line
       @return: (tuple) containing 2 dictionaries and a string:
         Dictionary 1: matched IBID lengths (Key: position of IBID
                       in line; Value: length of matched IBID)
         Dictionary 2: matched IBID text: (Key: position of IBID in
                       line; Value: matched IBID text)
         String:       working line with matched IBIDs removed
    """
    ibid_match_len = {}
    ibid_match_txt = {}
    ibid_matches_iter = re_ibid.finditer(line)
    ## Record details of each matched ibid:
    for m_ibid in ibid_matches_iter:
        ibid_match_len[m_ibid.start()] = len(m_ibid.group(2))
        ibid_match_txt[m_ibid.start()] = m_ibid.group(2)
        ## Replace matched text in line with underscores:
        line = line[0:m_ibid.start(2)] + "_"*len(m_ibid.group(2)) + \
               line[m_ibid.end(2):]
    return (ibid_match_len, ibid_match_txt, line)

def get_replacement_types(titles, reportnumbers):
    """Given the indices of the titles and reportnumbers that have been
       recognised within a reference line, create a dictionary keyed by
       the replacement position in the line, where the value for each
       key is a string describing the type of item replaced at that
       position in the line.
       The description strings are:
           'title'        - indicating that the replacement is a
                            periodical title
           'reportnumber' - indicating that the replacement is a
                            preprint report number.
       @param titles: (list) of locations in the string at which
        periodical titles were found.
       @param reportnumbers: (list) of locations in the string at which
        reportnumbers were found.
       @return: (dictionary) of replacement types at various locations
        within the string.
    """
    rep_types = {}
    for item_idx in titles:
        rep_types[item_idx] = "title"
    for item_idx in reportnumbers:
        rep_types[item_idx] = "reportnumber"
    return rep_types

def account_for_stripped_whitespace(spaces_keys,
                                    removed_spaces,
                                    replacement_types,
                                    len_reportnums,
                                    len_titles,
                                    replacement_index):
    """To build a processed (MARC XML) reference line in which the
       recognised citations such as standardised periodical TITLEs and
       REPORT-NUMBERs have been marked up, it is necessary to read from
       the reference line BEFORE all punctuation was stripped and it was
       made into upper-case. The indices of the cited items in this
       'original line', however, will be different to those in the
       'working-line', in which punctuation and multiple-spaces were
       stripped out. For example, the following reading-line:

        [26] E. Witten and S.-T. Yau, hep-th/9910245.
       ...becomes (after punctuation and multiple white-space stripping):
        [26] E WITTEN AND S T YAU HEP TH/9910245

       It can be seen that the report-number citation (hep-th/9910245) is
       at a different index in the two strings. When refextract searches
       for this citation, it uses the 2nd string (i.e. that which is
       capitalised and has no punctuation). When it builds the MARC XML
       representation of the reference line, however, it needs to read from
       the first string. It must therefore consider the whitespace,
       punctuation, etc that has been removed, in order to get the correct
       index for the cited item. This function accounts for the stripped
       characters before a given TITLE or REPORT-NUMBER index.
       @param spaces_keys: (list) - the indices at which spaces were
        removed from the reference line.
       @param removed_spaces: (dictionary) - keyed by the indices at which
        spaces were removed from the line, the values are the number of
        spaces actually removed from that position.
        So, for example, "3 spaces were removed from position 25 in
        the line."
       @param replacement_types: (dictionary) - at each 'replacement_index'
        in the line, the of replacement to make (title or reportnumber).
       @param len_reportnums: (dictionary) - the lengths of the REPORT-
        NUMBERs matched at the various indices in the line.
       @param len_titles: (dictionary) - the lengths of the various
        TITLEs matched at the various indices in the line.
       @param replacement_index: (integer) - the index in the working line
        of the identified TITLE or REPORT-NUMBER citation.
       @return: (tuple) containing 2 elements:
                        + the true replacement index of a replacement in
                          the reading line;
                        + any extras to add into the replacement index;
    """
    extras = 0
    true_replacement_index = replacement_index
    spare_replacement_index = replacement_index

    for space in spaces_keys:
        if space < true_replacement_index:
            ## There were spaces stripped before the current replacement
            ## Add the number of spaces removed from this location to the
            ## current replacement index:
            true_replacement_index  += removed_spaces[space]
            spare_replacement_index += removed_spaces[space]
        elif (space >= spare_replacement_index) and \
                 (replacement_types[replacement_index] == u"title") and \
                 (space < (spare_replacement_index + \
                           len_titles[replacement_index])):
            ## A periodical title is being replaced. Account for multi-spaces
            ## that may have been stripped from the title before its
            ## recognition:
            spare_replacement_index += removed_spaces[space]
            extras += removed_spaces[space]
        elif (space >= spare_replacement_index) and \
                 (replacement_types[replacement_index] == u"reportnumber") and \
                 (space < (spare_replacement_index + \
                           len_reportnums[replacement_index])):
            ## An institutional preprint report-number is being replaced.
            ## Account for multi-spaces that may have been stripped from it
            ## before its recognition:
            spare_replacement_index += removed_spaces[space]
            extras += removed_spaces[space]

    ## return the new values for replacement indices with stripped
    ## whitespace accounted for:
    return (true_replacement_index, extras)




def create_marc_xml_reference_line(line_marker,
                                   working_line,
                                   found_title_len,
                                   found_title_matchtext,
                                   pprint_repnum_len,
                                   pprint_repnum_matchtext,
                                   identified_dois,
                                   identified_urls,
                                   removed_spaces,
                                   standardised_titles):
    """After the phase of identifying and tagging citation instances
       in a reference line, this function is called to go through the
       line and the collected information about the recognised citations,
       and to transform the line into a string of MARC XML in which the
       recognised citations are grouped under various datafields and
       subfields, depending upon their type.
       @param line_marker: (string) - this is the marker for this
        reference line (e.g. [1]).
       @param working_line: (string) - this is the line before the
        punctuation was stripped. At this stage, it has not been
        capitalised, and neither TITLES nor REPORT NUMBERS have been
        stripped from it. However, any recognised numeration and/or URLs
        have been tagged with <cds.YYYY> tags.
        The working_line could, for example, look something like this:
         [1] CDS <cds.URL description="http //invenio-software.org/">
         http //invenio-software.org/</cds.URL>.
       @param found_title_len: (dictionary) - the lengths of the title
        citations that have been recognised in the line. Keyed by the index
        within the line of each match.
       @param found_title_matchtext: (dictionary) - The text that was found
        for each matched title citation in the line. Keyed by the index within
        the line of each match.
       @param pprint_repnum_len: (dictionary) - the lengths of the matched
        institutional preprint report number citations found within the line.
        Keyed by the index within the line of each match.
       @param pprint_repnum_matchtext: (dictionary) - The matched text for each
        matched institutional report number. Keyed by the index within the line
        of each match.
       @param identified_dois (list) - The list of dois inside the citation
       @identified_urls: (list) - contains 2-cell tuples, each of which
        represents an idenitfied URL and its description string.
        The list takes the order in which the URLs were identified in the line
        (i.e. first-found, second-found, etc).
       @param removed_spaces: (dictionary) - The number of spaces removed from
        the various positions in the line. Keyed by the index of the position
        within the line at which the spaces were removed.
       @param standardised_titles: (dictionary) - The standardised journal
        titles, keyed by the non-standard version of those titles.
       @return: (tuple) of 5 components:
                  ( string  -> a MARC XML-ized reference line.
                    integer -> number of fields of miscellaneous text marked-up
                               for the line.
                    integer -> number of title citations marked-up for the line.
                    integer -> number of institutional report-number citations
                               marked-up for the line.
                    integer -> number of URL citations marked-up for the record.
                    integer -> number of DOI's found for the record
                    integer -> number of author groups found
                  )

    """
    if len(found_title_len) + len(pprint_repnum_len) == 0:
        ## no TITLE or REPORT-NUMBER citations were found within this line,
        ## use the raw line: (This 'raw' line could still be tagged with
        ## recognised URLs or numeration.)
        tagged_line = working_line
    else:
        ## TITLE and/or REPORT-NUMBER citations were found in this line,
        ## build a new version of the working-line in which the standard
        ## versions of the REPORT-NUMBERs and TITLEs are tagged:
        startpos = 0          ## First cell of the reference line...
        previous_match = {}   ## previously matched TITLE within line (used
                              ## for replacement of IBIDs.
        replacement_types = {}
        title_keys = found_title_matchtext.keys()
        title_keys.sort()
        pprint_keys = pprint_repnum_matchtext.keys()
        pprint_keys.sort()
        spaces_keys = removed_spaces.keys()
        spaces_keys.sort()
        replacement_types = get_replacement_types(title_keys, pprint_keys)
        replacement_locations = replacement_types.keys()
        replacement_locations.sort()

        tagged_line = u"" ## This is to be the new 'working-line'. It will
                          ## contain the tagged TITLEs and REPORT-NUMBERs,
                          ## as well as any previously tagged URLs and
                          ## numeration components.
        ## begin:
        for replacement_index in replacement_locations:
            ## first, factor in any stripped spaces before this 'replacement'
            (true_replacement_index, extras) = \
                  account_for_stripped_whitespace(spaces_keys,
                                                  removed_spaces,
                                                  replacement_types,
                                                  pprint_repnum_len,
                                                  found_title_len,
                                                  replacement_index)

            if replacement_types[replacement_index] == u"title":
                ## Add a tagged periodical TITLE into the line:
                (rebuilt_chunk, startpos, previous_match) = \
                    add_tagged_title(reading_line=working_line,
                                     len_title=\
                                       found_title_len[replacement_index],
                                     matched_title=\
                                       found_title_matchtext[replacement_index],
                                     previous_match=previous_match,
                                     startpos=startpos,
                                     true_replacement_index=\
                                       true_replacement_index,
                                     extras=extras,
                                     standardised_titles=\
                                       standardised_titles)
                tagged_line += rebuilt_chunk

            elif replacement_types[replacement_index] == u"reportnumber":
                ## Add a tagged institutional preprint REPORT-NUMBER
                ## into the line:
                (rebuilt_chunk, startpos) = \
                  add_tagged_report_number(reading_line=working_line,
                                           len_reportnum=\
                                           pprint_repnum_len[replacement_index],
                                           reportnum=pprint_repnum_matchtext[replacement_index],
                                           startpos=startpos,
                                           true_replacement_index=\
                                             true_replacement_index,
                                           extras=extras)
                tagged_line += rebuilt_chunk



        ## add the remainder of the original working-line into the rebuilt line:
        tagged_line += working_line[startpos:]

        ## use the recently marked-up title information to identify any
        ## numeration that escaped the last pass:
        tagged_line = _re_identify_numeration(tagged_line)
        ## remove any series tags that are next to title tags, putting
        ## series information into the title tags:
        ## Only do this if the user doesn't want the Inspire journal title output format
        ## otherwise, the series letters are handled elsewhere in the xml conversion process
        #if not cli_opts['inspire']:
        #    tagged_line = move_tagged_series_into_tagged_title(tagged_line)
        tagged_line = wash_line(tagged_line)

    ## Before moving onto creating the XML string... try to find any authors in the line
    ## Found authors are immediately placed into tags (after Titles and Repnum's have been found)
    tagged_line = identify_and_tag_authors(tagged_line)

    ## Now, from the tagged line, create a MARC XML string,
    ## marking up any recognised citations:
    (xml_line, \
     count_misc, \
     count_title, \
     count_reportnum, \
     count_url, \
     count_doi, \
     count_auth_group) = \
         convert_processed_reference_line_to_marc_xml(line_marker, \
                                                      tagged_line.replace('\n',''), \
                                                      identified_dois, \
                                                      identified_urls)
    return (xml_line, count_misc, count_title, \
               count_reportnum, count_url, count_doi, count_auth_group)



def convert_unusable_tag_to_misc(line,
                                 misc_text,
                                 tag_match_end,
                                 closing_tag):
    """Function to remove an unwanted, tagged, citation item from a reference
       line. The tagged item itself is put into the miscellaneous text variable;
       the data up to the closing tag is then trimmed from the beginning of the
       working line. For example, the following working line:
         Example, AN. Testing software; <cds.YR>(2001)</cds.YR>, CERN, Geneva.
       ...would be trimmed down to:
         , CERN, Geneva.
       ...And the Miscellaneous text taken from the start of the line would be:
         Example, AN. Testing software; (2001)
       ...(assuming that the details of <cds.YR> and </cds.YR> were passed to
       the function).
       @param line: (string) - the reference line.
       @param misc_text: (string) - the variable containing the miscellaneous
        text recorded so far.
       @param tag_match_end: (integer) - the index of the end of the opening tag
        in the line.
       @param closing_tag: (string) - the closing tag to look for in the line
        (e.g. </cds.YR>).
       @return: (tuple) - containing misc_text (string) and line (string)
    """

    ## extract the tagged information:
    idx_closing_tag = line.find(closing_tag, tag_match_end)
    ## Sanity check - did we find a closing tag?
    if idx_closing_tag == -1:
        ## no closing tag found - strip the opening tag and move past this
        ## recognised item as it is unusable:
        line = line[tag_match_end:]
    else:
        ## closing tag was found
        misc_text += line[tag_match_end:idx_closing_tag]
        ## now trim the matched item and its tags from the start of the line:
        line = line[idx_closing_tag+len(closing_tag):]
    return (misc_text, line)

def is_in_line_elements(element_type,line_elements):
    """ Checks the list of current elements in the line for the given element type """
    for i, element in enumerate(line_elements):
        if element['type'] == element_type:
            return (True, line_elements[i])
    return False

def check_author_for_ibid(line_elements,author):
    """ Given a list of elements for an *entire* reference line, and the current
        author element to be used for ibids, check to see if that author element needs
        to be inserted into this line, depending on the presence of ibids and whether
        or not there is already an author paired with an ibid.
        Also, if no ibids are present in the line, see if the author element needs
        to be updated, depending on the presence of a normal title and a corresponding
        author group.
        @param line_elements: List of line elements for the entire processed reference
        line
        @param author: The current parent author element to be used with an ibid
        @return: (tuple) - containing a possible new author subfield, and the parent
        author element to be used for future ibids (if any)
    """
    ## Upon splitting, check for ibids in the previous line,
    ## If an appropriate author was found, pair it with this ibid.
    ## (i.e., an author has not been explicitly paired with this ibid already
    ## and an author exists with the parent title to which this ibid refers)
    if (is_in_line_elements("TITLE",line_elements)):
        ## Get the title element for this line
        title_element = is_in_line_elements("TITLE",line_elements)[1]

        if (author != None) and (not is_in_line_elements("AUTH",line_elements)) \
        and (title_element['is_ibid']):
            ## Return the author subfield which needs to be appended for an ibid in the line
            ## No need to reset the author to be used for ibids, since this line holds an ibid
            return """
          <subfield code="%(sf-code-ref-auth)s">%(authors)s</subfield>""" \
                % { 'authors'          : author['auth_txt'].strip('()'),
                    'sf-code-ref-auth' : CFG_REFEXTRACT_SUBFIELD_AUTH,
                  }, author

        ## Set the author for to be used for ibids, when a standard title is present in this line,
        ## as well as an author
        if (not title_element['is_ibid']) and (is_in_line_elements("AUTH",line_elements)):
            ## Set the author to be used for ibids, in the event that a subsequent ibid is found
            ## this author element will be repeated.
            ## This author is only used when an ibid is in a line
            ## and there is no other author found in the line.
            author = is_in_line_elements("AUTH",line_elements)[1]
        ## If there is no author associated with this head title, clear the author to be used for ibids
        elif (not title_element['is_ibid']):
            author = None

    ## If an author does not need to be replicated for an ibid, append nothing to the xml line
    return "", author

def append_datafield_element(line_marker,citation_structure,line_elements,author,xml_line):
    """ Finish the current datafield element and start a new one, with a new
        marker subfield.
        @param line_marker: (string) The line marker which will be the sole
        content of the newly created marker subfield. This will always be the
        first subfield to be created for a new datafield element.
        @return new_datafield: (string) The string holding the relevant
        datafield and subfield tags.
    """
    ## Add an author, if one must be added for ibid's, before splitting this line
    ## Also, if a standard title and an author are both present, save the author for future use
    new_datafield, author = check_author_for_ibid(line_elements,author)
    xml_line += new_datafield
    ## Start the new datafield
    xml_line += """
   </datafield>
   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">
      <subfield code="%(sf-code-ref-marker)s">%(marker-val)s</subfield>""" \
    % {      'df-tag-ref'         : CFG_REFEXTRACT_TAG_ID_REFERENCE,
             'df-ind1-ref'        : CFG_REFEXTRACT_IND1_REFERENCE,
             'df-ind2-ref'        : CFG_REFEXTRACT_IND2_REFERENCE,
             'sf-code-ref-marker' : CFG_REFEXTRACT_SUBFIELD_MARKER,
             'marker-val'         : encode_for_xml(line_marker)
    }
    ## add the past elements for end previous citation to the citation_structure list
    ## (citation_structure is a reference to the initial citation_structure list found in the calling method)
    citation_structure.append(line_elements)

    ## Clear the elements in the referenced list of elements
    del line_elements[0:len(line_elements)]

    return xml_line, author

def start_datafield_element(line_marker):
    """ Start a brand new datafield element with a marker subfield.
        @param line_marker: (string) The line marker which will be the sole
        content of the newly created marker subfield. This will always be the
        first subfield to be created for a new datafield element.
        @return new_datafield: (string) The string holding the relevant
        datafield and subfield tags.
    """
    new_datafield = """   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">
      <subfield code="%(sf-code-ref-marker)s">%(marker-val)s</subfield>""" \
    % {      'df-tag-ref'         : CFG_REFEXTRACT_TAG_ID_REFERENCE,
             'df-ind1-ref'        : CFG_REFEXTRACT_IND1_REFERENCE,
             'df-ind2-ref'        : CFG_REFEXTRACT_IND2_REFERENCE,
             'sf-code-ref-marker' : CFG_REFEXTRACT_SUBFIELD_MARKER,
             'marker-val'         : encode_for_xml(line_marker)
    }
    return new_datafield

def split_on_semi_colon(misc_txt,line_elements,elements_processed,total_elements):
    """ Given some misc text, see if there are any semi-colons which may indiciate that
        a reference line is in fact two separate citations.
        @param misc_txt: (string) The misc_txt to look for semi-colons within.
        @param line_elements: (list) The list of single upper-case chars which
            represent an element of a reference which has been processed.
        @param elements_processed: (integer) The number of elements which have been
            *looked at* for this entire reference line, regardless of splits
        @param citation_elements: (integer) The total number of elements which
            have been identified in the *entire* reference line
        @return: (string) Dipicting where the semi-colon was found in relation to the
            rest of the misc_txt. False if a semi-colon was not found, or one was found
            relating to an escaped piece of text.
    """
    ## If there has already been meaningful information found in the reference
    ## and there are still elements to be processed beyond the element relating to
    ## this misc_txt
    if (((is_in_line_elements("TITLE",line_elements)) or (is_in_line_elements("REPORTNUMBER",line_elements))) or \
        (len(misc_txt) >= semi_colon_misc_text_sensitivity)) and \
        (elements_processed < (total_elements)):

        if (len(misc_txt) >= 4) and \
            ((misc_txt[-5:] == '&amp;') or (misc_txt[-4:] == '&lt;')):
            ## This is a semi-colon which does not indicate a new citation
            return ""
        else:
            ## If a semi-colon is at the end, make sure to append preceeding misc_txt to
            ## the current datafield element
            if misc_txt.strip(" .,")[-1] == ";":
                return "after"
            ## Else, make sure to append the misc_txt to the *newly created datafield element*
            elif misc_txt.strip(" .,")[0] == ";":
                return "before"
    return ""


def dump_or_split_author(misc_txt,line_elements):
    """
        Given the list of current elements, and misc text, try to decide how to use this
        author for splitting heuristics, and see if it is useful. Returning 'dump' indicates
        put this author into misc text, since it had been identified as bad. 'split'
        indicates split the line and place this author into the fresh datafield. The empty string
        indicates add this author as normal to the current xml datafield.

        A line will be split using author information in two situations:
            1. When there already exists a previous author group in the same line
            2. If the only item in the current line is a title, with no misc text
        In both situations, the newly found author element is placed into the newly created
        datafield.

        This method heavily assumes that the first author group found in a single citation is the
        most reliable (In accordance with the IEEE standard, which states that authors should
        be written at the beginning of a citation, in the overwhelming majority of cases).
        @param misc_txt: (string) The misc text for this reference line
        @param line_elements: (list) The list of elements found for this current line
        @return: (string) The action to take to deal with this author.
    """
    ## If an author has already been found in this reference line
    if is_in_line_elements("AUTH",line_elements):

        ## If this author group is directly after another author group,
        ## with minimal misc text between, then this author group is very likely to be wrong.
        if (line_elements[-1]['type'] == "AUTH") \
        and (len(misc_txt) < adjacent_auth_misc_separation):
            return "dump"
        ## Else, trigger a new reference line
        return "split"

    ## In cases where an author is directly after an alone title (ibid or normal, with no misc),
    ## Trigger a new reference line
    if (is_in_line_elements("TITLE",line_elements)) and (len(line_elements) == 1) \
     and (len(misc_txt) == 0):
        return "split"

    return ""


def build_formatted_xml_citation(citation_elements,line_marker):
    """ Create the MARC-XML string of the found reference information which was taken
        from a tagged reference line.
        @param citation_elements: (list) an ordered list of dictionary elements,
        with each element corresponding to a found piece of information from a reference line.
        @param line_marker: (string) The line marker for this single reference line (e.g. [19])
        @return xml_line: (string) The MARC-XML representation of the list of reference elements
    """
    ## Begin the datafield element
    xml_line = start_datafield_element(line_marker)

    ## This will hold the ordering of tags which have been appended to the xml line
    ## This list will be used to control the desisions involving the creation of new citation lines
    ## (in the event of a new set of authors being recognised, or strange title ordering...)
    line_elements = []

    ## This is a list which will hold the current 'over-view' of a single reference line,
    ## as a list of lists, where each list corresponds to the contents of a datafield element
    ## in the xml mark-up
    citation_structure = []
    auth_for_ibid = None
    elements_processed = 0

    for element in citation_elements:
        ## Before going onto checking 'what' the next element is, handle misc text and semi-colons
        ## Multiple misc text subfields will be compressed later
        ## This will also be the only part of the code that deals with MISC tag_typed elements
        if len(element['misc_txt'].strip(" .,")) > 0:
            lower_stripped_misc = element['misc_txt'].lower().strip(".,:;- []")
            ## If misc text is ultimately just a semi-colon, don't add it as a new subfield
            ## But still use it to dictate whether a new citation is created
            if ((element['misc_txt'].strip(" .,") == ";") or \
                ((len(re.sub(re_arxiv_notation,"",lower_stripped_misc)) == 0) and \
                 (element['type'] == 'REPORTNUMBER'))):
                misc_txt = False
            else:
                misc_txt = element['misc_txt']

            ## Now.. if the MISC text is simply a single semi-colon,
            ## AND at least a title or a report number has also been identified..
            ## Mark up as a new citation
            ## (this is done before the 'author choice' is made, as it's more reliable)
            ## (an author choice will not create a new citation if a correct semi-colon is found)
            ## It is important to note that Author tagging helps the accurate detection
            ## a dual citation when looking for semi-colons (by reducing the length of misc text)
            split_sc = split_on_semi_colon(element['misc_txt'],\
                                           line_elements,\
                                           elements_processed,\
                                           len(citation_elements))

            ## Ignore semi-colon splitting heuristics, if the current item is a known ibid.
            #if element['type'] == 'TITLE' and element['is_ibid']:
            #    split_sc = ""

            if split_sc == "after":
                if misc_txt:
                    ## Append the misc subfield, before any of semi-colons (if any),
                    ## only if there is are other elements to be processed after this current element
                    xml_line += """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                            % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                                'misc-val'               : encode_for_xml(misc_txt),
                              }
                ## THEN set as a new citation line
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)
            elif split_sc == "before":
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)
                if misc_txt:
                    ## THEN append the misc text found AFTER the semi-colon (if any)
                    ## Append the misc subfield, before any of semi-colons
                    xml_line += """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                            % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                                'misc-val'               : encode_for_xml(misc_txt),
                              }
            elif misc_txt:
                ## Just append the misc subfield anyway
                ## In the case of:
                ## no semi-colon branch, or this is the last element to be processed, and it is not just a semi-colon
                xml_line += """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                        % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                            'misc-val'               : encode_for_xml(misc_txt),
                          }

        ## Now handle the type dependent actions
        ##TITLE
        if element['type'] == "TITLE":


            ## If a report number has been marked up, and there's misc text before this title and the last tag
            if is_in_line_elements("REPORTNUMBER",line_elements) and \
                (len(re.sub(re_arxiv_notation,"",(element['misc_txt'].lower().strip(".,:;- []")))) > 0):
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)
            elif is_in_line_elements("TITLE",line_elements):
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)

            ## Select the journal title output format
            if cli_opts['inspire']:
                ## ADD to current datafield
                xml_line += """
      <subfield code="%(sf-code-ref-title)s">%(title)s,%(volume)s,%(page)s</subfield>""" \
              % { 'sf-code-ref-title'   : CFG_REFEXTRACT_SUBFIELD_TITLE,
                  'title'               : encode_for_xml(element['title']),
                  'volume'              : encode_for_xml(element['volume']),
                  'page'                : encode_for_xml(element['page']),
                }
            else:
                ## ADD to current datafield
                xml_line += """
      <subfield code="%(sf-code-ref-title)s">%(title)s %(volume)s (%(year)s) %(page)s</subfield>""" \
              % { 'sf-code-ref-title'   : CFG_REFEXTRACT_SUBFIELD_TITLE,
                  'title'               : encode_for_xml(element['title']),
                  'volume'              : encode_for_xml(element['volume']),
                  'year'                : encode_for_xml(element['year']),
                  'page'                : encode_for_xml(element['page']),
                }


            ## Now, if there are any extra (numeration based) IBID's after this title
            if len(element['extra_ibids']) > 0:
                ## At least one IBID is present, these are to be outputted each into their own datafield
                for IBID in element['extra_ibids']:
                    ## %%%%% Set as NEW citation line %%%%%
                    (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                         citation_structure,
                                                                         line_elements,
                                                                         auth_for_ibid,
                                                                         xml_line)
                    if cli_opts['inspire']:
                        xml_line += """
      <subfield code="%(sf-code-ref-title)s">%(title)s,%(volume)s,%(page)s</subfield>""" \
                          % { 'sf-code-ref-title'   : CFG_REFEXTRACT_SUBFIELD_TITLE,
                              'title'               : encode_for_xml(IBID['title']),
                              'volume'              : encode_for_xml(IBID['volume']),
                              'page'                : encode_for_xml(IBID['page']),
                            }
                    else:
                        xml_line += """
      <subfield code="%(sf-code-ref-title)s">%(title)s %(volume)s (%(year)s) %(page)s</subfield>""" \
                          % { 'sf-code-ref-title'   : CFG_REFEXTRACT_SUBFIELD_TITLE,
                              'title'               : encode_for_xml(IBID['title']),
                              'volume'              : encode_for_xml(IBID['volume']),
                              'year'                : encode_for_xml(IBID['year']),
                              'page'                : encode_for_xml(IBID['page']),
                            }
            ## Add a Title element to the past elements list, since we last found an IBID
            line_elements.append(element)

        ##REPORT NUMBER
        elif element['type'] == "REPORTNUMBER":
            report_number = element['report_num']
            ## If a report number has been marked up, and there's misc text before this title and the last tag
            if is_in_line_elements("TITLE",line_elements) and \
                (len(re.sub(re_arxiv_notation,"",(element['misc_txt'].lower().strip(".,:;- []")))) > 0):
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)
            elif is_in_line_elements("REPORTNUMBER",line_elements):
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)
            if report_number.lower().find('arxiv') == 0:
                report_number = massage_arxiv_reportnumber(report_number)
            ## ADD to current datafield
            xml_line += """
      <subfield code="%(sf-code-ref-report-num)s">%(report-number)s</subfield>""" \
                % {'sf-code-ref-report-num' : CFG_REFEXTRACT_SUBFIELD_REPORT_NUM,
                   'report-number'          : encode_for_xml(report_number)
                }
            line_elements.append(element)

        ##URL
        elif element['type'] == "URL":
            if element['url_string'] == element['url_desc']:
                ## Build the datafield for the URL segment of the reference line:
                xml_line += """
      <subfield code="%(sf-code-ref-url)s">%(url)s</subfield>""" \
                    % {    'sf-code-ref-url'       : CFG_REFEXTRACT_SUBFIELD_URL,
                           'url'                   : encode_for_xml(element['url_string'])
                      }
            ## Else, in the case that the url string and the description differ in some way, include them both
            else:
                ## Build the datafield for the URL segment of the reference line:
                xml_line = """
      <subfield code="%(sf-code-ref-url)s">%(url)s</subfield>
      <subfield code="%(sf-code-ref-url-desc)s">%(url-desc)s</subfield>""" \
                    % {  'sf-code-ref-url'          : CFG_REFEXTRACT_SUBFIELD_URL,
                            'sf-code-ref-url-desc'  : CFG_REFEXTRACT_SUBFIELD_URL_DESCR,
                            'url'                   : encode_for_xml(element['url_string']),
                            'url-desc'              : encode_for_xml(element['url_desc'])
                         }
            line_elements.append(element)

        ##DOI
        elif element['type'] == "DOI":
            ## Split on hitting another DOI in the same line
            if is_in_line_elements("DOI",line_elements):
                ## %%%%% Set as NEW citation line %%%%%
                (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                     citation_structure,
                                                                     line_elements,
                                                                     auth_for_ibid,
                                                                     xml_line)
            xml_line += """
      <subfield code="%(sf-code-ref-doi)s">%(doi-val)s</subfield>""" \
                % {     'sf-code-ref-doi'       : CFG_REFEXTRACT_SUBFIELD_DOI,
                        'doi-val'               : encode_for_xml(element['doi_string'])
                 }
            line_elements.append(element)

        ##AUTHOR
        elif element['type'] == "AUTH":

            if element['auth_type'] != 'incl':
                auth_choice = dump_or_split_author(element['misc_txt'],line_elements)
                if auth_choice == "dump":
                    ## This author is no good, place it into misc text
                    xml_line += """
      <subfield code="%(sf-code-ref-misc)s">%(auth-txt)s</subfield>""" \
                         % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                             'auth-txt'               : encode_for_xml(element['auth_txt']).strip('()'),
                          }
                else:
                    ## Either the author denotes a new citation, or it is the first in this reference
                    if auth_choice == "split":
                        ## This author triggered the creation of a new datafield
                        if element['auth_type'] == 'etal' or element['auth_type'] == 'stnd':
                            ## %%%%% Set as NEW citation line %%%%%
                            (xml_line, auth_for_ibid) = append_datafield_element(line_marker,
                                                                                 citation_structure,
                                                                                 line_elements,
                                                                                 auth_for_ibid,
                                                                                 xml_line)
                    ## Add the author subfield with the author text
                    xml_line += """
      <subfield code="%(sf-code-ref-auth)s">%(authors)s</subfield>""" \
                        % {     'authors'               : encode_for_xml(element['auth_txt']).strip('()'),
                                'sf-code-ref-auth'      : CFG_REFEXTRACT_SUBFIELD_AUTH,
                         }

                    line_elements.append(element)

            elif element['auth_type'] == 'incl':
                ## Always include the matched author from the knowledge base into the datafield,
                ## No splitting heuristics are used here. It is purely so that it can be included
                ## with any previously found authors for this datafield.
                xml_line += """
      <subfield code="%(sf-code-ref-auth)s">(%(authors)s)</subfield>""" \
                        % {     'authors'               : encode_for_xml(element['auth_txt']),
                                'sf-code-ref-auth'      : CFG_REFEXTRACT_SUBFIELD_AUTH,
                         }

        ## The number of elements processed
        elements_processed+=1

    ## Append the author, if needed for an ibid, for the last element in the entire line
    ## Don't bother setting the author to be used for ibids, since the line is finished
    xml_line += check_author_for_ibid(line_elements,auth_for_ibid)[0]

    ## Close the ending datafield element
    xml_line += """
   </datafield>\n"""

    return xml_line



def convert_processed_reference_line_to_marc_xml(line_marker,
                                                 line,
                                                 identified_dois,
                                                 identified_urls):

    """ Given a single tagged reference line, convert it to its MARC-XML representation.
        Try to find all tags and extract their contents and their types into corresponding
        dictionary elements. Append each dictionary tag representation onto a list, which
        is given to 'build_formatted_xml_citation()' where the correct xml output will be generated.

        This method is dumb, with very few heuristics. It simply looks for tags, and makes dictionaries
        from the data it finds in a tagged reference line.

        @param line_marker: (string) The line marker for this single reference line (e.g. [19])
        @param line: (string) The tagged reference line.
        @param identified_dois: (list) a list of dois which were found in this line. The ordering of
        dois corresponds to the ordering of tags in the line, reading from left to right.
        @param identified_urls: (list) a list of urls which were found in this line. The ordering of
        urls corresponds to the ordering of tags in the line, reading from left to right.
        @return xml_line: (string) the MARC-XML representation of the tagged reference line
        @return count_*: (integer) the number of * (pieces of info) found in the reference line.
    """

    count_misc = count_title = count_reportnum = count_url = count_doi = count_auth_group = 0
    xml_line = ""
    processed_line = line
    cur_misc_txt = u""

    tag_match = re_tagged_citation.search(processed_line)

    # contains a list of dictionary entries of previously cited items
    citation_elements = []
    # the last tag element found when working from left-to-right across the line
    identified_citation_element = None

    while tag_match is not None:
        ## While there are tags inside this reference line...
        tag_match_start = tag_match.start()
        tag_match_end   = tag_match.end()
        tag_type        = tag_match.group(1)
        cur_misc_txt += processed_line[0:tag_match_start]

        ## Catches both standard titles, and ibid's
        if tag_type.find("TITLE") != -1:
            ## This tag is an identified journal TITLE. It should be followed
            ## by VOLUME, YEAR and PAGE tags.

            ## See if the found title has been tagged as an ibid: <cds.TITLEibid>
            if tag_match.group('ibid'):
                is_ibid = True
                closing_tag_length = len(CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID)
                idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID, \
                                                        tag_match_end)
            else:
                is_ibid = False
                closing_tag_length = len(CFG_REFEXTRACT_MARKER_CLOSING_TITLE)
                ## extract the title from the line:
                idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_TITLE, \
                                                       tag_match_end)


            if idx_closing_tag == -1:
                ## no closing TITLE tag found - get rid of the solitary tag
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:

                ## Closing tag was found:
                ## The title text to be used in the marked-up citation:
                title_text  = processed_line[tag_match_end:idx_closing_tag]

                ## Now trim this matched title and its tags from the start of the line:
                processed_line = processed_line[idx_closing_tag+closing_tag_length:]

                numeration_match = re_recognised_numeration_for_title_plus_series.match(processed_line)
                if numeration_match is not None:
                    ## recognised numeration immediately after the title - extract it:
                    reference_volume = numeration_match.group('vol')
                    reference_year   = numeration_match.group('yr')
                    reference_page   = numeration_match.group('pg')

                    ## This is used on two accounts:
                    ## 1. To get the series char from the title, if no series was found with the numeration
                    ## 2. To always remove any series character from the title match text
                    series_from_title = re_series_from_title.search(title_text)

                    if numeration_match.group('series'):
                        if cli_opts['inspire']:
                            reference_volume = numeration_match.group('series') + reference_volume
                        else:
                            reference_volume = numeration_match.group('series') + " " + reference_volume
                    elif series_from_title and series_from_title.group(3):
                        if cli_opts['inspire']:
                            reference_volume = series_from_title.group(3) + reference_volume
                        else:
                            reference_volume = series_from_title.group(3) + " " + reference_volume

                    if series_from_title.group(1):
                        title_text = series_from_title.group(1)

                    ## Skip past the matched numeration in the working line:
                    processed_line = processed_line[numeration_match.end():]

                    ## 'id_ibid' saves whether THIS TITLE is an ibid or not. (True or False)
                    ## 'extra_ibids' are there to hold ibid's without the word 'ibid', which
                    ## come directly after this title
                    ## i.e., they are recognised using title numeration instead of ibid notation
                    identified_citation_element =   {   'type'       : "TITLE",
                                                        'misc_txt'   : cur_misc_txt,
                                                        'title'      : title_text,
                                                        'volume'     : reference_volume,
                                                        'year'       : reference_year,
                                                        'page'       : reference_page,
                                                        'is_ibid'    : is_ibid,
                                                        'extra_ibids': []
                                                    }
                    count_title += 1
                    cur_misc_txt = u""

                    ## Try to find IBID's after this title, on top of previously found titles that were
                    ## denoted with the word 'IBID'. (i.e. look for IBID's without the word 'IBID' by
                    ## looking at extra numeration after this title)

                    numeration_match = re_numeration_no_ibid_txt.match(processed_line)
                    while numeration_match is not None:

                        reference_volume = numeration_match.group('vol')
                        reference_year   = numeration_match.group('yr')
                        reference_page   = numeration_match.group('pg')

                        if numeration_match.group('series'):
                            if cli_opts['inspire']:
                                reference_volume = numeration_match.group('series') + reference_volume
                            else:
                                reference_volume = numeration_match.group('series') + " " + reference_volume
                        elif series_from_title and series_from_title.group(3):
                            if cli_opts['inspire']:
                                reference_volume = series_from_title.group(3) + reference_volume
                            else:
                                reference_volume = series_from_title.group(3) + " " + reference_volume

                        ## Also remove the series char from the ibid title
                        if series_from_title.group(1):
                            title_text_for_ibid = series_from_title.group(1)

                        ## Skip past the matched numeration in the working line:
                        processed_line = processed_line[numeration_match.end():]

                        ## Takes the just found title text
                        identified_citation_element['extra_ibids'].append(
                                                { 'type'       : "TITLE",
                                                  'misc_txt'   : "",
                                                  'title'      : title_text_for_ibid,
                                                  'volume'     : reference_volume,
                                                  'year'       : reference_year,
                                                  'page'       : reference_page,
                                                })
                        ## Increment the stats counters:
                        count_title += 1

                        title_text = ""
                        reference_volume = ""
                        reference_year = ""
                        reference_page = ""
                        numeration_match = re_numeration_no_ibid_txt.match(processed_line)

                else:
                    ## No numeration was recognised after the title. Add the title into a MISC item instead:
                    cur_misc_txt += "%s" % title_text
                    identified_citation_element = None


        elif tag_type == "REPORTNUMBER":
            ## This tag is an identified institutional report number:

            ## extract the institutional report-number from the line:
            idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM, tag_match_end)
            ## Sanity check - did we find a closing report-number tag?
            if idx_closing_tag == -1:
                ## no closing </cds.REPORTNUMBER> tag found - strip the opening tag and move past this
                ## recognised reportnumber as it is unreliable:
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:
                ## closing tag was found
                report_num = processed_line[tag_match_end:idx_closing_tag]
                ## now trim this matched institutional report-number and its tags from the start of the line:
                processed_line = processed_line[idx_closing_tag+len(CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM):]

                identified_citation_element =   {   'type'       : "REPORTNUMBER",
                                                    'misc_txt'   : "%s" % cur_misc_txt,
                                                    'report_num' : "%s" % report_num,
                                                }
                count_reportnum += 1
                cur_misc_txt = u""


        elif tag_type == "URL":
            ## This tag is an identified URL:

            ## From the "identified_urls" list, get this URL and its
            ## description string:
            url_string = identified_urls[0][0]
            url_desc  = identified_urls[0][1]

            ## Now move past this "<cds.URL />"tag in the line:
            processed_line = processed_line[tag_match_end:]

            ## Delete the information for this URL from the start of the list
            ## of identified URLs:
            identified_urls[0:1] = []

            ## Save the current misc text
            identified_citation_element =   {   'type'       :     "URL",
                                                'misc_txt'   :     "%s" % cur_misc_txt,
                                                'url_string' :     "%s" % url_string,
                                                'url_desc'   :     "%s" % url_desc
                                            }
            count_url += 1
            cur_misc_txt = u""

        elif tag_type == "DOI":
            ## This tag is an identified DOI:

            ## From the "identified_dois" list, get this DOI and its
            ## description string:
            doi_string = identified_dois[0]

            ## Now move past this "<cds.CDS />"tag in the line:
            processed_line = processed_line[tag_match_end:]

            # Remove DOI from the list of DOI strings
            identified_dois[0:1] = []

            #SAVE the current misc text
            identified_citation_element =   {       'type'       : "DOI",
                                                    'misc_txt'   : "%s" % cur_misc_txt,
                                                    'doi_string' : "%s" % doi_string
                                            }

            ## Increment the stats counters:
            count_doi += 1
            cur_misc_txt = u""

        elif tag_type.find("AUTH") <> -1:
            ## This tag is an identified Author:

            auth_type = ""
            ## extract the title from the line:
            if tag_type.find("stnd") <> -1:
                auth_type = "stnd"
                idx_closing_tag_nearest = processed_line.find(\
                    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, tag_match_end)
            elif tag_type.find("etal") <> -1:
                auth_type = "etal"
                idx_closing_tag_nearest = processed_line.find(\
                    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL, tag_match_end)
            elif tag_type.find("incl") <> -1:
                auth_type = "incl"
                idx_closing_tag_nearest = processed_line.find(\
                    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL, tag_match_end)

            if idx_closing_tag_nearest == -1:
                ## no closing </cds.AUTH****> tag found - strip the opening tag
                ## and move past it
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:
                auth_txt = processed_line[tag_match_end:idx_closing_tag_nearest]
                ## Now move past the ending tag in the line:
                processed_line = processed_line[idx_closing_tag_nearest+len("</cds.AUTHxxxx>"):]
                #SAVE the current misc text
                identified_citation_element =   {   'type'       : "AUTH",
                                                    'misc_txt'   : "%s" % cur_misc_txt,
                                                    'auth_txt'   : "%s" % auth_txt,
                                                    'auth_type'  : "%s" % auth_type
                                                }
                ## Increment the stats counters:
                count_auth_group += 1
                cur_misc_txt = u""

        ## These following tags may be found separately;
        ## They are usually found when a "TITLE" tag is hit (ONLY immediately afterwards, however)
        ## Sitting by themselves means they do not have an associated TITLE tag, and should be MISC
        elif tag_type == "SER":
            ## This tag is a SERIES tag; Since it was not preceeded by a TITLE
            ## tag, it is useless - strip the tag and put it into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                           tag_match_end, \
                                           CFG_REFEXTRACT_MARKER_CLOSING_SERIES)
            identified_citation_element = None

        elif tag_type == "VOL":
            ## This tag is a VOLUME tag; Since it was not preceeded by a TITLE
            ## tag, it is useless - strip the tag and put it into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                           tag_match_end, \
                                           CFG_REFEXTRACT_MARKER_CLOSING_VOLUME)
            identified_citation_element = None

        elif tag_type == "YR":
            ## This tag is a YEAR tag; Since it's not preceeded by TITLE and
            ## VOLUME tags, it is useless - strip the tag and put the contents
            ## into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                           tag_match_end, \
                                           CFG_REFEXTRACT_MARKER_CLOSING_YEAR)
            identified_citation_element = None

        elif tag_type == "PG":
            ## This tag is a PAGE tag; Since it's not preceeded by TITLE,
            ## VOLUME and YEAR tags, it is useless - strip the tag and put the
            ## contents into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                           tag_match_end, \
                                           CFG_REFEXTRACT_MARKER_CLOSING_PAGE)
            identified_citation_element = None

        if identified_citation_element <> None:
            ## Append the found tagged data and current misc text
            citation_elements.append(identified_citation_element)
            identified_citation_element = None


        ## Look for the next tag in the processed line:
        tag_match = re_tagged_citation.search(processed_line)


    ## place any remaining miscellaneous text into the
    ## appropriate MARC XML fields:
    cur_misc_txt += processed_line

    ## This MISC element will hold the entire citation in the event
    ## that no tags were found.
    if len(cur_misc_txt.strip(" .;,")) > 0:
        ## Increment the stats counters:
        count_misc += 1
        identified_citation_element =   {   'type'       : "MISC",
                                            'misc_txt'   : "%s" % cur_misc_txt,
                                        }
        citation_elements.append(identified_citation_element)

    ## Now, run the method which will take as input:
    ## 1. A list of dictionaries, where each dictionary is a piece
    ## of citation information corresponding to a tag in the citation.
    ## 2. The line marker for this entire citation line (mulitple citation
    ## 'finds' inside a single citation will use the same marker value)
    ## The resulting xml line will be a properly marked up form of the
    ## citation. It will take into account authors to try and split up
    ## references which should be read as two SEPARATE ones.
    xml_line = build_formatted_xml_citation(citation_elements,line_marker)

    ## return the reference-line as MARC XML:

    return (xml_line, count_misc, count_title, count_reportnum, count_url, count_doi, count_auth_group)

def _re_identify_numeration(line):
    """Look for other numeration in line.
    """
    ## First, attempt to use marked-up titles
    line = re_correct_numeration_2nd_try_ptn1[0].sub(re_correct_numeration_2nd_try_ptn1[1], line)
    line = re_correct_numeration_2nd_try_ptn2[0].sub(re_correct_numeration_2nd_try_ptn2[1], line)
    return line

def add_tagged_report_number(reading_line,
                             len_reportnum,
                             reportnum,
                             startpos,
                             true_replacement_index,
                             extras):
    """In rebuilding the line, add an identified institutional REPORT-NUMBER
       (standardised and tagged) into the line.
       @param reading_line: (string) The reference line before capitalization
        was performed, and before REPORT-NUMBERs and TITLEs were stipped out.
       @param len_reportnum: (integer) the length of the matched REPORT-NUMBER.
       @param reportnum: (string) the replacement text for the matched
        REPORT-NUMBER.
       @param startpos: (integer) the pointer to the next position in the
        reading-line from which to start rebuilding.
       @param true_replacement_index: (integer) the replacement index of the
        matched REPORT-NUMBER in the reading-line, with stripped punctuation
        and whitespace accounted for.
       @param extras: (integer) extras to be added into the replacement index.
       @return: (tuple) containing a string (the rebuilt line segment) and an
        integer (the next 'startpos' in the reading-line).
    """
    rebuilt_line = u""  ## The segment of the line that's being rebuilt to
                        ## include the tagged & standardised REPORT-NUMBER

    ## Fill rebuilt_line with the contents of the reading_line up to the point
    ## of the institutional REPORT-NUMBER. However, stop 1 character before the
    ## replacement index of this REPORT-NUMBER to allow for removal of braces,
    ## if necessary:
    if (true_replacement_index - startpos - 1) >= 0:
        rebuilt_line += reading_line[startpos:true_replacement_index - 1]
    else:
        rebuilt_line += reading_line[startpos:true_replacement_index]

    ## check to see whether the REPORT-NUMBER was enclosed within brackets;
    ## drop them if so:
    if reading_line[true_replacement_index - 1] not in (u"[", u"("):
        ## no braces enclosing the REPORT-NUMBER:
        rebuilt_line += reading_line[true_replacement_index - 1]

    ## Add the tagged REPORT-NUMBER into the rebuilt-line segment:
    rebuilt_line += u"<cds.REPORTNUMBER>%(reportnum)s</cds.REPORTNUMBER>" \
                        % { 'reportnum' : reportnum }

    ## move the pointer in the reading-line past the current match:
    startpos = true_replacement_index + len_reportnum + extras

    ## Move past closing brace for report number (if there was one):
    try:
        if reading_line[startpos] in (u"]", u")"):
            startpos += 1
    except IndexError:
        ## moved past end of line - ignore
        pass

    ## return the rebuilt-line segment and the pointer to the next position in
    ## the reading-line from  which to start rebuilding up to the next match:
    return (rebuilt_line, startpos)

def add_tagged_title_in_place_of_IBID(previous_match,
                                      ibid_series):
    """In rebuilding the line, if the matched TITLE was actually an IBID, this
       function will replace it with the previously matched TITLE, and add it
       into the line, tagged. It will even handle the series letter, if it
       differs. For example, if the previous match is "Nucl. Phys. B", and
       the ibid is "IBID A", the title inserted into the line will be
       "Nucl. Phys. A". Otherwise, if the IBID had no series letter, it will
       simply be replaced by "Nucl. Phys. B" (i.e. the previous match.)
       @param previous_match: (string) - the previously matched TITLE.
       @param ibid_series: (string) - the series of the IBID (if any).
       @return: (tuple) containing a string (the rebuilt line segment) and an
        other string (the newly updated previous-match).
    """

    IBID_start_tag = " <cds.TITLEibid>"

    rebuilt_line = u""
    if ibid_series != "":
        ## This IBID has a series letter. If the previously matched TITLE also
        ## had a series letter and that series letter differs to the one
        ## carried by this IBID, the series letter stored in the previous-match
        ## must be updated to that of this IBID
        ## (i.e. Keep the series letter paired directly with the IBID):
        if previous_match['series'] is not None:
            ## Previous match had a series:
            if previous_match['series'] != ibid_series:
                ## Previous match and this IBID do not have the same series
                previous_match['series'] = ibid_series

            rebuilt_line += IBID_start_tag + "%(previous-match)s" \
                            % { 'previous-match' : previous_match['title'] } + \
                            CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID + \
                            " : " + previous_match['series']
        else:
            ## Previous match had no recognised series but the IBID did. Add a
            ## the series letter to the end of the previous match.
            previous_match['series'] = ibid_series
            rebuilt_line += IBID_start_tag + "%(previous-match)s" \
                           % { 'previous-match' : previous_match['title'] } + \
                           CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID + \
                           " : " + previous_match['series']

    else:
        if previous_match['series'] is not None:
            ## Both the previous match & this IBID have the same series
            rebuilt_line += IBID_start_tag + "%(previous-match)s" \
                            % { 'previous-match' : previous_match['title'] } + \
                            CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID + \
                            " : " + previous_match['series']
        else:
            ## This IBID has no series letter. If a previous series is present append it.
            rebuilt_line += IBID_start_tag + "%(previous-match)s" \
                           % { 'previous-match' : previous_match['title'] } + \
                           CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID

    return (rebuilt_line, previous_match)

def add_tagged_title(reading_line,
                     len_title,
                     matched_title,
                     previous_match,
                     startpos,
                     true_replacement_index,
                     extras,
                     standardised_titles):
    """In rebuilding the line, add an identified periodical TITLE (standardised
       and tagged) into the line.
       @param reading_line: (string) The reference line before capitalization
        was performed, and before REPORT-NUMBERs and TITLEs were stripped out.
       @param len_title: (integer) the length of the matched TITLE.
       @param matched_title: (string) the matched TITLE text.
       @previous_match: (string) the previous periodical TITLE citation to
        have been matched in the current reference line. It is used when
        replacing an IBID instance in the line.
       @param startpos: (integer) the pointer to the next position in the
        reading-line from which to start rebuilding.
       @param true_replacement_index: (integer) the replacement index of the
        matched TITLE in the reading-line, with stripped punctuation and
        whitespace accounted for.
       @param extras: (integer) extras to be added into the replacement index.
       @param standardised_titles: (dictionary) the standardised versions of
        periodical titles, keyed by their various non-standard versions.
       @return: (tuple) containing a string (the rebuilt line segment), an
        integer (the next 'startpos' in the reading-line), and an other string
        (the newly updated previous-match).
    """
    ## Fill 'rebuilt_line' (the segment of the line that is being rebuilt to
    ## include the tagged and standardised periodical TITLE) with the contents
    ## of the reading-line, up to the point of the matched TITLE:
    rebuilt_line = reading_line[startpos:true_replacement_index]
    ## Test to see whether a title or an "IBID" was matched:
    if matched_title.upper().find("IBID") != -1:
        ## This is an IBID
        ## Try to replace the IBID with a title:
        if len(previous_match) > 1:
            ## A title has already been replaced in this line - IBID can be
            ## replaced meaninfully First, try to get the series number/letter
            ## of this IBID:
            m_ibid = re_matched_ibid.search(matched_title)
            try:
                series = m_ibid.group(1)
            except IndexError:
                series = u""
            if series is None:
                series = u""
            ## Replace this IBID with the previous title match, if possible:
            (replaced_ibid_segment, previous_match) = \
                 add_tagged_title_in_place_of_IBID(previous_match, series)
            rebuilt_line += replaced_ibid_segment
            ## Update start position for next segment of original line:
            startpos = true_replacement_index + len_title + extras

            ## Skip past any punctuation at the end of the replacement that was
            ## just made:
            try:
                if reading_line[startpos] in (".", ":", ";", "-"):
                    startpos += 1
            except IndexError:
                ## The match was at the very end of the line
                pass
        else:
            ## no previous title-replacements in this line - IBID refers to
            ## something unknown and cannot be replaced:
            rebuilt_line += \
                reading_line[true_replacement_index:true_replacement_index \
                             + len_title + extras]
            startpos = true_replacement_index + len_title + extras
    else:
        ## This is a normal title, not an IBID
        rebuilt_line += "<cds.TITLE>%(title)s</cds.TITLE>" \
                        % { 'title' : standardised_titles[matched_title] }
        previous_title = standardised_titles[matched_title]
        startpos = true_replacement_index + len_title + extras

        ## Try to get the series of this just added title, by dynamically finding it
        ## from the text after the title tag (rather than from the kb)
        ## Ideally, the series will be found with the numeration after the title
        ## but will also check the ending of the title text if this match fails.
        previous_series_from_numeration = re_series_from_numeration.search(reading_line[startpos:])
        previous_series_from_title = re_series_from_title.search(previous_title)
        ## First, try to obtain the series from the identified numeration
        if previous_series_from_numeration:
            previous_match = {'title':previous_title,
                   'series':previous_series_from_numeration.group(1)}
        ## If it isn't found, try to get it from the standardised title
        ## BUT ONLY if the numeration matched!
        elif previous_series_from_title and previous_series_from_title.group(3):
            previous_match = {'title':previous_series_from_title.group(1),
                    'series':previous_series_from_title.group(3)}
        else:
            previous_match = {'title':previous_title,'series':None}

        ## Skip past any punctuation at the end of the replacement that was
        ## just made:
        try:
            if reading_line[startpos] in (".", ":", ";", "-"):
                startpos += 1
        except IndexError:
            ## The match was at the very end of the line
            pass
        try:
            if reading_line[startpos] == ")":
                startpos += 1
        except IndexError:
            ## The match was at the very end of the line
            pass

    ## return the rebuilt line-segment, the position (of the reading line) from
    ## which the next part of the rebuilt line should be started, and the newly
    ## updated previous match.

    return (rebuilt_line, startpos, previous_match)


def remove_reference_line_marker(line):
    """Trim a reference line's 'marker' from the beginning of the line.
       @param line: (string) - the reference line.
       @return: (tuple) containing two strings:
                 + The reference line's marker (or if there was not one,
                   a 'space' character.
                 + The reference line with it's marker removed from the
                   beginning.
    """
    ## Get patterns to identify reference-line marker patterns:
    marker_patterns = get_reference_line_numeration_marker_patterns()
    line = line.lstrip()

    marker_match = \
        perform_regex_match_upon_line_with_pattern_list(line,
                                                        marker_patterns)

    if marker_match is not None:
        ## found a marker:
        marker_val = marker_match.group(u'mark')
        ## trim the marker from the start of the line:
        line = line[marker_match.end():].lstrip()
    else:
        marker_val = u" "
    return (marker_val, line)

def create_marc_xml_reference_section(ref_sect,
                                      preprint_repnum_search_kb,
                                      preprint_repnum_standardised_categs,
                                      periodical_title_search_kb,
                                      standardised_periodical_titles,
                                      periodical_title_search_keys):
    """Passed a complete reference section, process each line and attempt to
       ## identify and standardise individual citations within the line.
       @param ref_sect: (list) of strings - each string in the list is a
        reference line.
       @param preprint_repnum_search_kb: (dictionary) - keyed by a tuple
        containing the line-number of the pattern in the KB and the non-standard
        category string.  E.g.: (3, 'ASTRO PH'). Value is regexp pattern used to
        search for that report-number.
       @param preprint_repnum_standardised_categs: (dictionary) - keyed by non-
        standard version of institutional report number, value is the
        standardised version of that report number.
       @param periodical_title_search_kb: (dictionary) - keyed by non-standard
        title to search for, value is the compiled regexp pattern used to
        search for that title.
       @param standardised_periodical_titles: (dictionary) - keyed by non-
        standard title to search for, value is the standardised version of that
        title.
       @param periodical_title_search_keys: (list) - ordered list of non-
        standard titles to search for.
       @return: (tuple) of 6 components:
         ( list       -> of strings, each string is a MARC XML-ized reference
                         line.
           integer    -> number of fields of miscellaneous text found for the
                         record.
           integer    -> number of title citations found for the record.
           integer    -> number of institutional report-number citations found
                         for the record.
           integer    -> number of URL citations found for the record.
           integer    -> number of DOI's found
           integer    -> number of author groups found
           dictionary -> The totals for each 'bad title' found in the reference
                         section.
         )
    """
    ## a list to contain the processed reference lines:
    xml_ref_sectn = []
    ## counters for extraction stats:
    count_misc = count_title = count_reportnum = count_url = count_doi = count_auth_group = 0

    ## A dictionary to contain the total count of each 'bad title' found
    ## in the entire reference section:
    record_titles_count = {}

    ## process references line-by-line:
    for ref_line in ref_sect:
        ## initialise some variables:
        ## dictionaries to record information about, and coordinates of,
        ## matched IBID items:
        found_ibids_len = {}
        found_ibids_matchtext = {}
        ## dictionaries to record information about, and  coordinates of,
        ## matched journal title items:
        found_title_len = {}
        found_title_matchtext = {}
        ## dictionaries to record information about, and the coordinates of,
        ## matched preprint report number items
        found_pprint_repnum_matchlens   = {}  ## lengths of given matches of
                                              ## preprint report numbers
        found_pprint_repnum_replstr     = {}  ## standardised replacement
                                              ## strings for preprint report
                                              ## numbers to be substituted into
                                              ## a line

        ## Strip the 'marker' (e.g. [1]) from this reference line:
        (line_marker, working_line1) = \
                      remove_reference_line_marker(ref_line)


        ## Find DOI sections in citation
        (working_line1, identified_dois) = identify_and_tag_DOI(working_line1)


        ## Identify and replace URLs in the line:
        (working_line1, identified_urls) = identify_and_tag_URLs(working_line1)

        ## take a copy of the line as a first working line, clean it of bad
        ## accents, and correct puncutation, etc:
        working_line1 = wash_line(working_line1)

        ## Identify and standardise numeration in the line:
        working_line1 = \
        standardize_and_markup_numeration_of_citations_in_line(working_line1)

        ## Now that numeration has been marked-up, check for and remove any
        ## ocurrences of " bf ":
        working_line1 = re_identify_bf_before_vol.sub(r" \1", working_line1)

        ## Clean the line once more:
        working_line1 = wash_line(working_line1)

        ## Transform the line to upper-case, now making a new working line:
        working_line2 = working_line1.upper()

        ## Strip punctuation from the line:
        working_line2 = re_punctuation.sub(u' ', working_line2)

        ## Remove multiple spaces from the line, recording
        ## information about their coordinates:
        (removed_spaces, working_line2) = \
             remove_and_record_multiple_spaces_in_line(working_line2)

        ## Identify and record coordinates of institute preprint report numbers:
        (found_pprint_repnum_matchlens, \
         found_pprint_repnum_replstr, \
         working_line2) = \
           identify_preprint_report_numbers(working_line2,
                                            preprint_repnum_search_kb,
                                            preprint_repnum_standardised_categs)

        ## Identify and record coordinates of non-standard journal titles:
        (found_title_len, \
         found_title_matchtext, \
         working_line2, \
         line_titles_count) = \
                    identify_periodical_titles(working_line2,
                                               periodical_title_search_kb,
                                               periodical_title_search_keys)

        ## Add the count of 'bad titles' found in this line to the total
        ## for the reference section:
        record_titles_count = sum_2_dictionaries(record_titles_count, \
                                                 line_titles_count)

        ## Attempt to identify, record and replace any IBIDs in the line:
        if (working_line2.upper().find(u"IBID") != -1):
            ## there is at least one IBID in the line - try to
            ## identify its meaning:
            (found_ibids_len, \
             found_ibids_matchtext, \
             working_line2) = identify_ibids(working_line2)
            ## now update the dictionary of matched title lengths with the
            ## matched IBID(s) lengths information:
            found_title_len.update(found_ibids_len)
            found_title_matchtext.update(found_ibids_matchtext)

        ## Using the recorded information, create a MARC XML representation
        ## of the rebuilt line:
        ## At the same time, get stats of citations found in the reference line
        ## (titles, urls, etc):
        (xml_line, this_count_misc, this_count_title, this_count_reportnum, \
          this_count_url, this_count_doi, this_count_auth_group) = \
           create_marc_xml_reference_line(line_marker=line_marker,
                                          working_line=working_line1,
                                          found_title_len=found_title_len,
                                          found_title_matchtext=\
                                            found_title_matchtext,
                                          pprint_repnum_len=\
                                            found_pprint_repnum_matchlens,
                                          pprint_repnum_matchtext=\
                                            found_pprint_repnum_replstr,
                                            identified_dois=identified_dois,
                                          identified_urls=identified_urls,
                                          removed_spaces=removed_spaces,
                                          standardised_titles=\
                                            standardised_periodical_titles)
        count_misc       += this_count_misc
        count_title      += this_count_title
        count_reportnum  += this_count_reportnum
        count_url        += this_count_url
        count_doi        += this_count_doi
        count_auth_group += this_count_auth_group

        ## Append the rebuilt line details to the list of
        ## MARC XML reference lines:
        xml_ref_sectn.append(xml_line)

    ## Return the list of processed reference lines:
    return (xml_ref_sectn, count_misc, count_title, count_reportnum, \
             count_url, count_doi, count_auth_group, record_titles_count)


## Tasks related to extraction of reference section from full-text:

## ----> 1. Removing page-breaks, headers and footers before
##          searching for reference section:

def strip_headers_footers_pagebreaks(docbody,
                                     page_break_posns,
                                     num_head_lines,
                                     num_foot_lines):
    """Remove page-break lines, header lines, and footer lines from the
       document.
       @param docbody: (list) of strings, whereby each string in the list is a
        line in the document.
       @param page_break_posns: (list) of integers, whereby each integer
        represents the index in docbody at which a page-break is found.
       @param num_head_lines: (int) the number of header lines each page in the
        document has.
       @param num_foot_lines: (int) the number of footer lines each page in the
        document has.
       @return: (list) of strings - the document body after the headers,
        footers, and page-break lines have been stripped from the list.
    """
    num_breaks = (len(page_break_posns))
    page_lens = []
    for x in xrange(0, num_breaks):
        if x < num_breaks - 1:
            page_lens.append(page_break_posns[x + 1] - page_break_posns[x])
    page_lens.sort()
    if (len(page_lens) > 0) and \
           (num_head_lines + num_foot_lines + 1 < page_lens[0]):
        ## Safe to chop hdrs & ftrs
        page_break_posns.reverse()
        first = 1
        for i in xrange(0, len(page_break_posns)):
            ## Unless this is the last page break, chop headers
            if not first:
                for dummy in xrange(1, num_head_lines + 1):
                    docbody[page_break_posns[i] \
                            + 1:page_break_posns[i] + 2] = []
            else:
                first = 0
            ## Chop page break itself
            docbody[page_break_posns[i]:page_break_posns[i] + 1] = []
            ## Chop footers (unless this is the first page break)
            if i != len(page_break_posns) - 1:
                for dummy in xrange(1, num_foot_lines + 1):
                    docbody[page_break_posns[i] \
                            - num_foot_lines:page_break_posns[i] \
                            - num_foot_lines + 1] = []
    return docbody

def check_boundary_lines_similar(l_1, l_2):
    """Compare two lists to see if their elements are roughly the same.
    @param l_1: (list) of strings.
    @param l_2: (list) of strings.
    @return: (int) 1/0.
    """
    num_matches = 0
    if (type(l_1) != list) or (type(l_2) != list) or (len(l_1) != len(l_2)):
        ## these 'boundaries' are not similar
        return 0

    num_elements = len(l_1)
    for i in xrange(0, num_elements):
        if l_1[i].isdigit() and l_2[i].isdigit():
            ## both lines are integers
            num_matches = num_matches + 1
        else:
            l1_str = l_1[i].lower()
            l2_str = l_2[i].lower()
            if (l1_str[0] == l2_str[0]) and \
                   (l1_str[len(l1_str) - 1] == l2_str[len(l2_str) - 1]):
                num_matches = num_matches + 1
    if (len(l_1) == 0) or (float(num_matches) / float(len(l_1)) < 0.9):
        return 0
    else:
        return 1

def get_number_header_lines(docbody, page_break_posns):
    """Try to guess the number of header lines each page of a document has.
       The positions of the page breaks in the document are used to try to guess
       the number of header lines.
       @param docbody: (list) of strings - each string being a line in the
        document
       @param page_break_posns: (list) of integers - each integer is the
        position of a page break in the document.
       @return: (int) the number of lines that make up the header of each page.
    """
    remaining_breaks = (len(page_break_posns) - 1)
    num_header_lines = empty_line = 0
    ## pattern to search for a word in a line:
    p_wordSearch = re.compile(unicode(r'([A-Za-z0-9-]+)'), re.UNICODE)
    if remaining_breaks > 2:
        if remaining_breaks > 3:
            # Only check odd page headers
            next_head = 2
        else:
            # Check headers on each page
            next_head = 1
        keep_checking = 1
        while keep_checking:
            cur_break = 1
            if docbody[(page_break_posns[cur_break] \
                        + num_header_lines + 1)].isspace():
                ## this is a blank line
                empty_line = 1

            if (page_break_posns[cur_break] + num_header_lines + 1) \
                   == (page_break_posns[(cur_break + 1)]):
                ## Have reached next page-break: document has no
                ## body - only head/footers!
                keep_checking = 0

            grps_headLineWords = \
                p_wordSearch.findall(docbody[(page_break_posns[cur_break] \
                                              + num_header_lines + 1)])
            cur_break = cur_break + next_head
            while (cur_break < remaining_breaks) and keep_checking:
                grps_thisLineWords = \
                    p_wordSearch.findall(docbody[(page_break_posns[cur_break] \
                                                  + num_header_lines + 1)])
                if empty_line:
                    if len(grps_thisLineWords) != 0:
                        ## This line should be empty, but isn't
                        keep_checking = 0
                else:
                    if (len(grps_thisLineWords) == 0) or \
                           (len(grps_headLineWords) != len(grps_thisLineWords)):
                        ## Not same num 'words' as equivilent line
                        ## in 1st header:
                        keep_checking = 0
                    else:
                        keep_checking = \
                            check_boundary_lines_similar(grps_headLineWords, \
                                                         grps_thisLineWords)
                ## Update cur_break for nxt line to check
                cur_break = cur_break + next_head
            if keep_checking:
                ## Line is a header line: check next
                num_header_lines = num_header_lines + 1
            empty_line = 0
    return num_header_lines

def get_number_footer_lines(docbody, page_break_posns):
    """Try to guess the number of footer lines each page of a document has.
       The positions of the page breaks in the document are used to try to guess
       the number of footer lines.
       @param docbody: (list) of strings - each string being a line in the
        document
       @param page_break_posns: (list) of integers - each integer is the
        position of a page break in the document.
       @return: (int) the number of lines that make up the footer of each page.
    """
    num_breaks = (len(page_break_posns))
    num_footer_lines = 0
    empty_line = 0
    keep_checking = 1
    p_wordSearch = re.compile(unicode(r'([A-Za-z0-9-]+)'), re.UNICODE)
    if num_breaks > 2:
        while keep_checking:
            cur_break = 1
            if page_break_posns[cur_break] - num_footer_lines - 1 < 0 or \
               page_break_posns[cur_break] - num_footer_lines - 1 > \
               len(docbody) - 1:
                ## Be sure that the docbody list boundary wasn't overstepped:
                break
            if docbody[(page_break_posns[cur_break] \
                        - num_footer_lines - 1)].isspace():
                empty_line = 1
            grps_headLineWords = \
                p_wordSearch.findall(docbody[(page_break_posns[cur_break] \
                                              - num_footer_lines - 1)])
            cur_break = cur_break + 1
            while (cur_break < num_breaks) and keep_checking:
                grps_thisLineWords = \
                    p_wordSearch.findall(docbody[(page_break_posns[cur_break] \
                                                  - num_footer_lines - 1)])
                if empty_line:
                    if len(grps_thisLineWords) != 0:
                        ## this line should be empty, but isn't
                        keep_checking = 0
                else:
                    if (len(grps_thisLineWords) == 0) or \
                           (len(grps_headLineWords) != len(grps_thisLineWords)):
                        ## Not same num 'words' as equivilent line
                        ## in 1st footer:
                        keep_checking = 0
                    else:
                        keep_checking = \
                            check_boundary_lines_similar(grps_headLineWords, \
                                                         grps_thisLineWords)
                ## Update cur_break for nxt line to check
                cur_break = cur_break + 1
            if keep_checking:
                ## Line is a footer line: check next
                num_footer_lines = num_footer_lines + 1
            empty_line = 0
    return num_footer_lines

def get_page_break_positions(docbody):
    """Locate page breaks in the list of document lines and create a list
       positions in the document body list.
       @param docbody: (list) of strings - each string is a line in the
        document.
       @return: (list) of integer positions, whereby each integer represents the
        position (in the document body) of a page-break.
    """
    page_break_posns = []
    p_break = re.compile(unicode(r'^\s*?\f\s*?$'), re.UNICODE)
    num_document_lines = len(docbody)
    for i in xrange(num_document_lines):
        if p_break.match(docbody[i]) != None:
            page_break_posns.append(i)
    return page_break_posns

def document_contains_text(docbody):
    """Test whether document contains text, or is just full of worthless
       whitespace.
       @param docbody: (list) of strings - each string being a line of the
        document's body
       @return: (integer) 1 if non-whitespace found in document; 0 if only
        whitespace found in document.
    """
    found_non_space = 0
    for line in docbody:
        if not line.isspace():
            ## found a non-whitespace character in this line
            found_non_space = 1
            break
    return found_non_space

def remove_page_boundary_lines(docbody):
    """Try to locate page breaks, headers and footers within a document body,
       and remove the array cells at which they are found.
       @param docbody: (list) of strings, each string being a line in the
        document's body.
       @return: (list) of strings. The document body, hopefully with page-
        breaks, headers and footers removed. Each string in the list once more
        represents a line in the document.
    """
    number_head_lines = number_foot_lines = 0
    ## Make sure document not just full of whitespace:
    if not document_contains_text(docbody):
        ## document contains only whitespace - cannot safely
        ## strip headers/footers
        return docbody

    ## Get list of index posns of pagebreaks in document:
    page_break_posns = get_page_break_positions(docbody)

    ## Get num lines making up each header if poss:
    number_head_lines = get_number_header_lines(docbody, page_break_posns)

    ## Get num lines making up each footer if poss:
    number_foot_lines = get_number_footer_lines(docbody, page_break_posns)

    ## Remove pagebreaks,headers,footers:
    docbody = strip_headers_footers_pagebreaks(docbody, \
                                               page_break_posns, \
                                               number_head_lines, \
                                               number_foot_lines)

    return docbody

## ----> 2. Finding reference section in full-text:

def _create_regex_pattern_add_optional_spaces_to_word_characters(word):
    """Add the regex special characters (\s*?) to allow optional spaces between
       the characters in a word.
       @param word: (string) the word to be inserted into a regex pattern.
       @return: string: the regex pattern for that word with optional spaces
        between all of its characters.
    """
    new_word = u""
    for ch in word:
        if ch.isspace():
            new_word += ch
        else:
            new_word += ch + unicode(r'\s*?')
    return new_word


def get_reference_section_title_patterns():
    """Return a list of compiled regex patterns used to search for the title of
       a reference section in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    patterns = []
    titles = [ u'references',
               u'references.',
               u'r\u00C9f\u00E9rences',
               u'r\u00C9f\u00C9rences',
               u'reference',
               u'refs',
               u'r\u00E9f\u00E9rence',
               u'r\u00C9f\u00C9rence',
               u'r\xb4ef\xb4erences',
               u'r\u00E9fs',
               u'r\u00C9fs',
               u'bibliography',
               u'bibliographie',
               u'citations' ]
    sect_marker = unicode(r'^\s*?([\[\-\{\(])?\s*?((\w|\d){1,5}([\.\-\,](\w|\d){1,5})?\s*?[\.\-\}\)\]]\s*?)?(?P<title>')
    line_end  = unicode(r'(\s+?s\s*?e\s*?c\s*?t\s*?i\s*?o\s*?n\s*?)?)')
    line_end += unicode(r'($|\s*?[\[\{\(\<]\s*?[1a-z]\s*?[\}\)\>\]]|\:)')

    for t in titles:
        if len(t) > 0:
            ## don't append empty titles:
            t_ptn = re.compile(sect_marker + \
                                _create_regex_pattern_add_optional_spaces_to_word_characters(t) + \
                                line_end, re.I|re.UNICODE)
            patterns.append(t_ptn)
    ## allow e.g.  'N References' to be found where N is an integer
    sect_marker1 = unicode(r'^(\d){1,3}\s*(?P<title>')
    t_ptn = re.compile(sect_marker1 + \
                   _create_regex_pattern_add_optional_spaces_to_word_characters(u'references') + \
                   line_end, re.I|re.UNICODE)
    patterns.append(t_ptn)
    return patterns


def get_reference_line_numeration_marker_patterns(prefix=u''):
    """Return a list of compiled regex patterns used to search for the marker
       of a reference line in a full-text document.
       @param prefix: (string) the possible prefix to a reference line
       @return: (list) of compiled regex patterns.
    """
    compiled_ptns = []
    title = u""
    if type(prefix) in (str, unicode):
        title = prefix
    g_name = unicode(r'(?P<mark>')
    g_close = u')'
    space = unicode(r'\s*?')
    patterns = \
      [ space + title + g_name + unicode(r'\[\s*?(?P<marknum>\d+)\s*?\]') + g_close,
        space + title + g_name + unicode(r'\[\s*?[a-zA-Z]+\s?(\d{1,4}[A-Za-z]?)?\s*?\]') + g_close,
        space + title + g_name + unicode(r'\{\s*?(?P<marknum>\d+)\s*?\}') + g_close,
        space + title + g_name + unicode(r'\<\s*?(?P<marknum>\d+)\s*?\>') + g_close,
        space + title + g_name + unicode(r'\(\s*?(?P<marknum>\d+)\s*?\)') + g_close,
        space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\.') + g_close,
        space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?') + g_close,
        space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\]') + g_close,
        space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\}') + g_close,
        space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\)') + g_close,
        space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\>') + g_close,
        space + title + g_name + unicode(r'\[\s*?\]') + g_close,
        space + title + g_name + unicode(r'\*') + g_close ]
    for p in patterns:
        compiled_ptns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_ptns

def get_first_reference_line_numeration_marker_patterns_via_brackets():
    """Return a list of compiled regex patterns used to search for the first
       reference line in a full-text document.
       The line is considered to start with either: [1] or {1}
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    g_name = unicode(r'(?P<mark>')
    g_close = u')'
    patterns = \
      [ g_name + unicode(r'(?P<left>\[)\s*?(?P<num>\d+)\s*?(?P<right>\])') \
          + g_close,
        g_name + unicode(r'(?P<left>\{)\s*?(?P<num>\d+)\s*?(?P<right>\})') \
          + g_close ]
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns

def get_first_reference_line_numeration_marker_patterns_via_dots():
    """Return a list of compiled regex patterns used to search for the first
       reference line in a full-text document.
       The line is considered to start with : 1. or 2. or 3. etc
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    g_name = unicode(r'(?P<mark>')
    g_close = u')'
    patterns = \
      [ g_name + unicode(r'(?P<left>)\s*?(?P<num>\d+)\s*?(?P<right>\.)')   \
          + g_close]
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns

def get_first_reference_line_numeration_marker_patterns_via_numbers():
    """Return a list of compiled regex patterns used to search for the first
       reference line in a full-text document.
       The line is considered to start with : 1 or 2 etc (just a number)
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    g_name = unicode(r'(?P<mark>')
    g_close = u')'
    patterns = \
      [ g_name + unicode(r'(?P<left>)\s*?(?P<num>\d+)\s*?(?P<right>)')   \
          + g_close]
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns
def get_post_reference_section_title_patterns():
    """Return a list of compiled regex patterns used to search for the title
       of the section after the reference section in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    thead = unicode(r'^\s*?([\{\(\<\[]?\s*?(\w|\d)\s*?[\)\}\>\.\-\]]?\s*?)?')
    ttail = unicode(r'(\s*?\:\s*?)?')
    numatn = unicode(r'(\d+|\w\b|i{1,3}v?|vi{0,3})[\.\,]?\b')
    ## Section titles:
    patterns = [ thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'appendix') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'appendices') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'acknowledgement') + unicode(r's?') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'table') + unicode(r'\w?s?\d?') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'figure') + unicode(r's?') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'annex') + unicode(r's?') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'discussion') + unicode(r's?') + ttail,
                 thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'remercie') + unicode(r's?') + ttail,
                 ## Figure nums:
                 r'^\s*?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'figure') + numatn,
                 r'^\s*?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'fig') + unicode(r'\.\s*?') + numatn,
                 r'^\s*?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'fig') + unicode(r'\.?\s*?\d\w?\b'),
                 ## tables:
                 r'^\s*?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'table') + numatn,
                 r'^\s*?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'tab') + unicode(r'\.\s*?') + numatn,
                 r'^\s*?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'tab') + unicode(r'\.?\s*?\d\w?\b') ]
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns

def get_post_reference_section_keyword_patterns():
    """Return a list of compiled regex patterns used to search for various
       keywords that can often be found after, and therefore suggest the end of,
       a reference section in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    patterns = [ unicode(r'(') + _create_regex_pattern_add_optional_spaces_to_word_characters(u'prepared') + \
                                 unicode(r'|') + _create_regex_pattern_add_optional_spaces_to_word_characters(u'created') + \
                                 unicode(r').*?(AAS\s*?)?\sLATEX'),
                 unicode(r'AAS\s+?LATEX\s+?') + _create_regex_pattern_add_optional_spaces_to_word_characters(u'macros') + u'v',
                 unicode(r'^\s*?') + _create_regex_pattern_add_optional_spaces_to_word_characters(u'This paper has been produced using'),
                 unicode(r'^\s*?') + \
                                 _create_regex_pattern_add_optional_spaces_to_word_characters(u'This article was processed by the author using Springer-Verlag') + \
                                 u' LATEX' ]
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns

def perform_regex_match_upon_line_with_pattern_list(line, patterns):
    """Given a list of COMPILED regex patters, perform the "re.match" operation
       on the line for every pattern.
       Break from searching at the first match, returning the match object.
       In the case that no patterns match, the None type will be returned.
       @param line: (unicode string) to be searched in.
       @param patterns: (list) of compiled regex patterns to search  "line"
        with.
       @return: (None or an re.match object), depending upon whether one of
        the patterns matched within line or not.
    """
    if type(patterns) not in (list, tuple):
        raise TypeError()
    if type(line) not in (str, unicode):
        raise TypeError()

    m = None
    for ptn in patterns:
        m = ptn.match(line)
        if m is not None:
            break
    return m

def perform_regex_search_upon_line_with_pattern_list(line, patterns):
    """Given a list of COMPILED regex patters, perform the "re.search"
       operation on the line for every pattern. Break from searching at the
       first match, returning the match object.  In the case that no patterns
       match, the None type will be returned.
       @param line: (unicode string) to be searched in.
       @param patterns: (list) of compiled regex patterns to search "line" with.
       @return: (None or an re.match object), depending upon whether one of the
        patterns matched within line or not.
    """
    if type(patterns) not in (list, tuple):
        raise TypeError()
    if type(line) not in (str, unicode):
        raise TypeError()

    m = None
    for ptn in patterns:
        m = ptn.search(line)
        if m is not None:
            break
    return m


def find_reference_section(docbody):
    """Search in document body for its reference section. More precisely, find
       the first line of the reference section. Effectively, the function starts
       at the end of a document and works backwards, line-by-line, looking for
       the title of a reference section. It stops when (if) it finds something
       that it considers to be the first line of a reference section.
       @param docbody: (list) of strings - the full document body.
       @return: (dictionary) :
          { 'start_line' : (integer) - index in docbody of 1st reference line,
            'title_string' : (string) - title of the reference section.
            'marker' : (string) - the marker of the first reference line,
            'marker_pattern' : (string) - regexp string used to find the marker,
            'title_marker_same_line' : (integer) - flag to indicate whether the
                                        reference section title was on the same
                                        line as the first reference line's
                                        marker or not. 1 if it was; 0 if not.
          }
                 Much of this information is used by later functions to rebuild
                 a reference section.
         -- OR --
                (None) - when the reference section could not be found.
    """
    ref_start_line = ref_title = ref_line_marker = ref_line_marker_ptn = None
    title_marker_same_line = found_part = None
    if len(docbody) > 0:
        title_patterns = get_reference_section_title_patterns()
        marker_patterns = get_reference_line_numeration_marker_patterns()
        p_num = re.compile(unicode(r'(\d+)'))

        ## Try to find refs section title:
        x = len(docbody) - 1
        found_title = 0
        while x >= 0 and not found_title:
            title_match = \
               perform_regex_search_upon_line_with_pattern_list(docbody[x], \
                                                                title_patterns)
            if title_match is not None:
                temp_ref_start_line = x
                temp_title = title_match.group('title')
                # Need to escape to avoid problems like 'References['
                temp_title = re.escape(temp_title)
                mk_with_title_ptns = \
                   get_reference_line_numeration_marker_patterns(temp_title)
                mk_with_title_match = \
                   perform_regex_search_upon_line_with_pattern_list(docbody[x],\
                                                             mk_with_title_ptns)
                if mk_with_title_match is not None:
                    mk = mk_with_title_match.group('mark')
                    mk_ptn = mk_with_title_match.re.pattern
                    m_num = p_num.search(mk)
                    if m_num is not None and int(m_num.group(0)) == 1:
                        # Mark found.
                        found_title = 1
                        ref_title = temp_title
                        ref_line_marker = mk
                        ref_line_marker_ptn = mk_ptn
                        ref_start_line = temp_ref_start_line
                        title_marker_same_line = 1
                    else:
                        found_part = 1
                        ref_start_line = temp_ref_start_line
                        ref_line_marker = mk
                        ref_line_marker_ptn = mk_ptn
                        ref_title = temp_title
                        title_marker_same_line = 1
                else:
                    try:
                        y = x + 1
                        ## Move past blank lines
                        while docbody[y].isspace() and y < len(docbody):
                            y = y + 1
                        ## Is this line numerated like a reference line?
                        mark_match = perform_regex_match_upon_line_with_pattern_list(docbody[y], marker_patterns)
                        if mark_match is not None:
                            ## Ref line found. What is it?
                            title_marker_same_line = None
                            mark = mark_match.group('mark')
                            mk_ptn = mark_match.re.pattern
                            m_num = p_num.search(mark)
                            if m_num is not None and int(m_num.group(0)) == 1:
                                # 1st ref truly found
                                ref_start_line = temp_ref_start_line
                                ref_line_marker = mark
                                ref_line_marker_ptn = mk_ptn
                                ref_title = temp_title
                                found_title = 1
                            elif m_num is not None and m_num.groups(0) != 1:
                                found_part = 1
                                ref_start_line = temp_ref_start_line
                                ref_line_marker = mark
                                ref_line_marker_ptn = mk_ptn
                                ref_title = temp_title
                            else:
                                if found_part:
                                    found_title = 1
                                else:
                                    found_part = 1
                                    ref_start_line = temp_ref_start_line
                                    ref_title = temp_title
                                    ref_line_marker = mark
                                    ref_line_marker_ptn = mk_ptn
                        else:
                            ## No numeration
                            if found_part:
                                found_title = 1
                            else:
                                found_part = 1
                                ref_start_line = temp_ref_start_line
                                ref_title = temp_title
                    except IndexError:
                        ## References section title was on last line for some
                        ## reason. Ignore
                        pass
            x = x - 1
    if ref_start_line is not None:
        ## return dictionary containing details of reference section:
        ref_sectn_details = { 'start_line' : ref_start_line,
                              'title_string' : ref_title,
                              'marker' : ref_line_marker,
                              'marker_pattern' : ref_line_marker_ptn,
                              'title_marker_same_line' : \
                               (title_marker_same_line is not None and 1) or (0)
                            }
    else:
        ref_sectn_details = None
    return ref_sectn_details

def find_reference_section_no_title_via_brackets(docbody):
    """This function would generally be used when it was not possible to locate
       the start of a document's reference section by means of its title.
       Instead, this function will look for reference lines that have numeric
       markers of the format [1], [2], etc.
       @param docbody: (list) of strings -each string is a line in the document.
       @return: (dictionary) :
         { 'start_line' : (integer) - index in docbody of 1st reference line,
           'title_string' : (None) - title of the reference section
                                     (None since no title),
           'marker' : (string) - the marker of the first reference line,
           'marker_pattern' : (string) - the regexp string used to find the
                                         marker,
           'title_marker_same_line' : (integer) 0 - to signal title not on same
                                       line as marker.
         }
                 Much of this information is used by later functions to rebuild
                 a reference section.
         -- OR --
                (None) - when the reference section could not be found.
    """
    ref_start_line = ref_line_marker = None
    if len(docbody) > 0:
        marker_patterns = get_first_reference_line_numeration_marker_patterns_via_brackets()

        ## try to find first reference line in the reference section:
        x = len(docbody) - 1
        found_ref_sect = 0
        while x >= 0 and not found_ref_sect:
            mark_match = \
                perform_regex_match_upon_line_with_pattern_list(docbody[x], \
                                                                marker_patterns)
            if mark_match is not None and int(mark_match.group('num')) == 1:
                ## Get marker recognition pattern:
                mk_ptn = mark_match.re.pattern

                ## Look for [2] in next 10 lines:
                next_test_lines = 10
                y = x + 1
                temp_found = 0
                while y < len(docbody) and y < x + next_test_lines and not temp_found:
                    mark_match2 = perform_regex_match_upon_line_with_pattern_list(docbody[y], marker_patterns)
                    if (mark_match2 is not None) and \
                           (int(mark_match2.group('num')) == 2) and \
                           (mark_match.group('left') == \
                            mark_match2.group('left')) and \
                            (mark_match.group('right') == \
                             mark_match2.group('right')):
                        ## Found next reference line:
                        temp_found = 1
                    elif y == len(docbody) - 1:
                        temp_found = 1
                    y = y + 1

                if temp_found:
                    found_ref_sect = 1
                    ref_start_line = x
                    ref_line_marker = mark_match.group('mark')
                    ref_line_marker_ptn = mk_ptn
            x = x - 1
    if ref_start_line is not None:
        ref_sectn_details = { 'start_line' : ref_start_line,
                              'title_string' : None,
                              'marker' : ref_line_marker,
                              'marker_pattern' : ref_line_marker_ptn,
                              'title_marker_same_line' : 0
                            }
    else:
        ## didn't manage to find the reference section
        ref_sectn_details = None
    return ref_sectn_details

def find_reference_section_no_title_via_dots(docbody):
    """This function would generally be used when it was not possible to locate
       the start of a document's reference section by means of its title.
       Instead, this function will look for reference lines that have numeric
       markers of the format [1], [2], etc.
       @param docbody: (list) of strings -each string is a line in the document.
       @return: (dictionary) :
         { 'start_line' : (integer) - index in docbody of 1st reference line,
           'title_string' : (None) - title of the reference section
                                     (None since no title),
           'marker' : (string) - the marker of the first reference line,
           'marker_pattern' : (string) - the regexp string used to find the
                                         marker,
           'title_marker_same_line' : (integer) 0 - to signal title not on same
                                       line as marker.
         }
                 Much of this information is used by later functions to rebuild
                 a reference section.
         -- OR --
                (None) - when the reference section could not be found.
    """
    ref_start_line = ref_line_marker = None
    if len(docbody) > 0:
        marker_patterns = get_first_reference_line_numeration_marker_patterns_via_dots()

        ## try to find first reference line in the reference section:
        x = len(docbody) - 1
        found_ref_sect = 0
        while x >= 0 and not found_ref_sect:
            mark_match = \
                perform_regex_match_upon_line_with_pattern_list(docbody[x], \
                                                                marker_patterns)
            if mark_match is not None and int(mark_match.group('num')) == 1:
                ## Get marker recognition pattern:
                mk_ptn = mark_match.re.pattern

                ## Look for [2] in next 10 lines:
                next_test_lines = 10
                y = x + 1
                temp_found = 0
                while y < len(docbody) and y < x + next_test_lines and not temp_found:
                    mark_match2 = perform_regex_match_upon_line_with_pattern_list(docbody[y], marker_patterns)
                    if (mark_match2 is not None) and \
                           (int(mark_match2.group('num')) == 2) and \
                           (mark_match.group('left') == \
                            mark_match2.group('left')) and \
                            (mark_match.group('right') == \
                             mark_match2.group('right')):
                        ## Found next reference line:
                        temp_found = 1
                    elif y == len(docbody) - 1:
                        temp_found = 1
                    y = y + 1

                if temp_found:
                    found_ref_sect = 1
                    ref_start_line = x
                    ref_line_marker = mark_match.group('mark')
                    ref_line_marker_ptn = mk_ptn
            x = x - 1
    if ref_start_line is not None:
        ref_sectn_details = { 'start_line' : ref_start_line,
                              'title_string' : None,
                              'marker' : ref_line_marker,
                              'marker_pattern' : ref_line_marker_ptn,
                              'title_marker_same_line' : 0
                            }
    else:
        ## didn't manage to find the reference section
        ref_sectn_details = None
    return ref_sectn_details

def find_reference_section_no_title_via_numbers(docbody):
    """This function would generally be used when it was not possible to locate
       the start of a document's reference section by means of its title.
       Instead, this function will look for reference lines that have numeric
       markers of the format [1], [2], etc.
       @param docbody: (list) of strings -each string is a line in the document.
       @return: (dictionary) :
         { 'start_line' : (integer) - index in docbody of 1st reference line,
           'title_string' : (None) - title of the reference section
                                     (None since no title),
           'marker' : (string) - the marker of the first reference line,
           'marker_pattern' : (string) - the regexp string used to find the
                                         marker,
           'title_marker_same_line' : (integer) 0 - to signal title not on same
                                       line as marker.
         }
                 Much of this information is used by later functions to rebuild
                 a reference section.
         -- OR --
                (None) - when the reference section could not be found.
    """
    ref_start_line = ref_line_marker = None
    if len(docbody) > 0:
        marker_patterns = get_first_reference_line_numeration_marker_patterns_via_numbers()

        ## try to find first reference line in the reference section:
        x = len(docbody) - 1
        found_ref_sect = 0
        while x >= 0 and not found_ref_sect:
            mark_match = \
                perform_regex_match_upon_line_with_pattern_list(docbody[x], \
                                                                marker_patterns)

            if mark_match is None:
                break
            elif mark_match is not None and int(mark_match.group('num')) == 1:
                ## Get marker recognition pattern:
                mk_ptn = mark_match.re.pattern

                ## Look for [2] in next 10 lines:
                next_test_lines = 10
                y = x + 1
                temp_found = 0
                while y < len(docbody) and y < x + next_test_lines and not temp_found:
                    mark_match2 = perform_regex_match_upon_line_with_pattern_list(docbody[y], marker_patterns)
                    if (mark_match2 is not None) and \
                           (int(mark_match2.group('num')) == 2) and \
                           (mark_match.group('left') == \
                            mark_match2.group('left')) and \
                            (mark_match.group('right') == \
                             mark_match2.group('right')):
                        ## Found next reference line:
                        temp_found = 1
                    elif y == len(docbody) - 1:
                        temp_found = 1
                    y = y + 1

                if temp_found:
                    found_ref_sect = 1
                    ref_start_line = x
                    ref_line_marker = mark_match.group('mark')
                    ref_line_marker_ptn = mk_ptn
            x = x - 1
    if ref_start_line is not None:
        ref_sectn_details = { 'start_line' : ref_start_line,
                              'title_string' : None,
                              'marker' : ref_line_marker,
                              'marker_pattern' : ref_line_marker_ptn,
                              'title_marker_same_line' : 0
                            }
    else:
        ## didn't manage to find the reference section
        ref_sectn_details = None
    return ref_sectn_details

def find_end_of_reference_section(docbody,
                                  ref_start_line,
                                  ref_line_marker,
                                  ref_line_marker_ptn):
    """Given that the start of a document's reference section has already been
       recognised, this function is tasked with finding the line-number in the
       document of the last line of the reference section.
       @param docbody: (list) of strings - the entire plain-text document body.
       @param ref_start_line: (integer) - the index in docbody of the first line
        of the reference section.
       @param ref_line_marker: (string) - the line marker of the first reference
        line.
       @param ref_line_marker_ptn: (string) - the pattern used to search for a
        reference line marker.
       @return: (integer) - index in docbody of the last reference line
         -- OR --
                (None) - if ref_start_line was invalid.
    """
    section_ended = 0
    x = ref_start_line
    if (type(x) is not int) or (x < 0) or \
           (x > len(docbody)) or (len(docbody)<1):
        ## The provided 'first line' of the reference section was invalid.
        ## Either it was out of bounds in the document body, or it was not a
        ## valid integer.
        ## Can't safely find end of refs with this info - quit.
        return None
    ## Get patterns for testing line:
    t_patterns = get_post_reference_section_title_patterns()
    kw_patterns = get_post_reference_section_keyword_patterns()

    if None not in (ref_line_marker, ref_line_marker_ptn):
        mk_patterns = [re.compile(ref_line_marker_ptn, re.I|re.UNICODE)]
    else:
        mk_patterns = get_reference_line_numeration_marker_patterns()

    while ( x < len(docbody)) and (not section_ended):
        ## look for a likely section title that would follow a reference section:
        end_match = perform_regex_search_upon_line_with_pattern_list(docbody[x], t_patterns)
        if end_match is None:
            ## didn't match a section title - try looking for keywords that
            ## suggest the end of a reference section:
            end_match = perform_regex_search_upon_line_with_pattern_list(docbody[x], kw_patterns)
        if end_match is not None:
            ## Is it really the end of the reference section? Check within the next
            ## 5 lines for other reference numeration markers:
            y = x + 1
            line_found = 0
            while (y < x + 6) and ( y < len(docbody)) and (not line_found):
                num_match = perform_regex_search_upon_line_with_pattern_list(docbody[y], mk_patterns)
                if num_match is not None and not num_match.group(0).isdigit():
                    line_found = 1
                y = y + 1
            if not line_found:
                ## No ref line found-end section
                section_ended = 1
        if not section_ended:
            ## Does this & the next 5 lines simply contain numbers? If yes, it's
            ## probably the axis scale of a graph in a fig. End refs section
            digit_test_str = docbody[x].replace(" ", "").\
                                        replace(".", "").\
                                        replace("-", "").\
                                        replace("+", "").\
                                        replace(u"\u00D7", "").\
                                        replace(u"\u2212", "").\
                                        strip()
            if len(digit_test_str) > 10 and digit_test_str.isdigit():
                ## The line contains only digits and is longer than 10 chars:
                y = x + 1
                digit_lines = 4
                num_digit_lines = 1
                while(y < x + digit_lines) and (y < len(docbody)):
                    digit_test_str = docbody[y].replace(" ", "").\
                                     replace(".", "").\
                                     replace("-", "").\
                                     replace("+", "").\
                                     replace(u"\u00D7", "").\
                                     replace(u"\u2212", "").\
                                     strip()
                    if len(digit_test_str) > 10 and digit_test_str.isdigit():
                        num_digit_lines += 1
                    elif len(digit_test_str) == 0:
                        ## This is a blank line. Don't count it, to accommodate
                        ## documents that are double-line spaced:
                        digit_lines += 1
                    y = y + 1
                if num_digit_lines == digit_lines:
                    section_ended = 1
            x = x + 1
    return x - 1

## ----> 3. Found reference section - now take out lines and rebuild them:

def test_for_blank_lines_separating_reference_lines(ref_sect):
    """Test to see if reference lines are separated by blank lines so that
       these can be used to rebuild reference lines.
       @param ref_sect: (list) of strings - the reference section.
       @return: (int) 0 if blank lines do not separate reference lines; 1 if
        they do.
    """
    num_blanks = 0            ## Number of blank lines found between non-blanks
    num_lines = 0             ## Number of reference lines separated by blanks
    blank_line_separators = 0 ## Flag to indicate whether blanks lines separate
                              ## ref lines
    multi_nonblanks_found = 0 ## Flag to indicate whether multiple nonblank
                              ## lines are found together (used because
                              ## if line is dbl-spaced, it isnt a blank that
                              ## separates refs & can't be relied upon)
    x = 0
    max_line = len(ref_sect)
    while x < max_line:
        if not ref_sect[x].isspace():
            ## not an empty line:
            num_lines += 1
            x = x + 1 ## Move past line
            while x < len(ref_sect) and not ref_sect[x].isspace():
                multi_nonblanks_found = 1
                x = x + 1
            x = x - 1
        else:
            ## empty line
            num_blanks += 1
            x = x + 1
            while x < len(ref_sect) and ref_sect[x].isspace():
                x = x + 1
            if x == len(ref_sect):
                ## Blanks at end doc: dont count
                num_blanks -= 1
            x = x - 1
        x = x + 1
    ## Now from the number of blank lines & the number of text lines, if
    ## num_lines > 3, & num_blanks = num_lines, or num_blanks = num_lines - 1,
    ## then we have blank line separators between reference lines
    if (num_lines > 3) and ((num_blanks == num_lines) or \
                            (num_blanks == num_lines - 1)) and \
                            (multi_nonblanks_found):
        blank_line_separators = 1
    return blank_line_separators


def remove_leading_garbage_lines_from_reference_section(ref_sectn):
    """Sometimes, the first lines of the extracted references are completely
       blank or email addresses. These must be removed as they are not
       references.
       @param ref_sectn: (list) of strings - the reference section lines
       @return: (list) of strings - the reference section without leading
        blank lines or email addresses.
    """
    p_email = re.compile(unicode(r'^\s*e\-?mail'), re.UNICODE)
    while (len(ref_sectn) > 0) and (ref_sectn[0].isspace() or \
                                    p_email.match(ref_sectn[0]) is not None):
        ref_sectn[0:1] = []
    return ref_sectn

def correct_rebuilt_lines(rebuilt_lines, p_refmarker):
    """Try to correct any cases where a reference line has been incorrectly
       split based upon a wrong numeration marker. That is to say, given the
       following situation:

       [1] Smith, J blah blah
       [2] Brown, N blah blah see reference
       [56] for more info [3] Wills, A blah blah
       ...

       The first part of the 3rd line clearly belongs with line 2. This function
       will try to fix this situation, to have the following situation:

       [1] Smith, J blah blah
       [2] Brown, N blah blah see reference [56] for more info
       [3] Wills, A blah blah

       If it cannot correctly guess the correct break-point in such a line, it
       will give up and the original list of reference lines will be returned.

       @param rebuilt_lines: (list) the rebuilt reference lines
       @param p_refmarker: (compiled regex pattern object) the pattern used to
        match regex line numeration markers. **MUST HAVE A GROUP 'marknum' to
        encapsulate the mark number!** (e.g. r'\[(?P<marknum>\d+)\]')
       @return: (list) of strings. If necessary, the corrected reference lines.
        Else the orginal 'rebuilt' lines.
    """
    fixed = []
    try:
        m = p_refmarker.match(rebuilt_lines[0])
        last_marknum = int(m.group("marknum"))
        if last_marknum != 1:
            ## Even the first mark isnt 1 - probaby too dangerous to
            ## try to repair
            return rebuilt_lines
    except (IndexError, AttributeError, ValueError):
        ## Sometihng went wrong. Either no references, not a numbered line
        ## marker (int() failed), or no reference line marker (NoneType was
        ## passed). In any case, unable to test for correct reference line
        ## numberring - just return the lines as they were.
        return rebuilt_lines

    ## Loop through each line in "rebuilt_lines" and test the mark at the
    ## beginning.
    ## If current-line-mark = previous-line-mark + 1, the line will be taken to
    ## be correct and appended to the list of fixed-lines. If not, then the loop
    ## will attempt to test whether the current line marker is actually part of
    ## the previous line by looking in the current line for another marker
    ## that has the numeric value of previous-marker + 1. If found, that marker
    ## will be taken as the true marker for the line and the leader of the line
    ## (up to the point of this marker) will be appended to the previous line.
    ## E.g.:
    ## [1] Smith, J blah blah
    ## [2] Brown, N blah blah see reference
    ## [56] for more info [3] Wills, A blah blah
    ## ...
    ##
    ## ...will be transformed into:
    ## [1] Smith, J blah blah
    ## [2] Brown, N blah blah see reference [56] for more info
    ## [3] Wills, A blah blah
    ## ...

    ## first line is correct, to put it into fixed:
    fixed.append(rebuilt_lines[0])
    for x in xrange(1, len(rebuilt_lines)):
        m = p_refmarker.match(rebuilt_lines[x])
        try:
            ## Get the number of this line:
            curline_mark_num = m.group("marknum")
        except AttributeError:
            ## This line does not have a line marker at the start.
            ## Add this line to the end of the previous line.
            fixed[len(fixed) - 1] += rebuilt_lines[x]
        else:
            if int(curline_mark_num) == last_marknum + 1:
                ## The marker number for this reference line is correct.
                ## Append it to the 'fixed' lines and move on.
                fixed.append(rebuilt_lines[x])
                last_marknum += 1
            elif len(rebuilt_lines[x][m.end():].strip()) == 0:
                ## This line consists of a marker-number only - it is not a
                ## correct marker. Append it to the last line.
                fixed[len(fixed) - 1] += rebuilt_lines[x]
            else:
                ## This marker != previous-marker + 1.
                ## May have taken some of the last line into this line.
                ## Can we find the next marker in this line?
                ## Test for this situation:
                ## [54] for more info [3] Wills, A blah blah
                current_line = rebuilt_lines[x]
                m_next_mark = p_refmarker.search(current_line[m.end():])
                while m_next_mark is not None:
                    ## Another "line marker" is present in this line.
                    ## Test it to see if it is equal to the previous
                    ## 'real' marker + 1:
                    if int(m_next_mark.group("marknum")) == \
                       last_marknum + 1:
                        ## This seems to be the marker for the next line.
                        ## Test to see that the marker is followed by
                        ## something meaningful (a letter at least.)
                        ## I.e. We want to fix this:
                        ## [54] for more info [3] Wills, A blah blah
                        ##
                        ## but we don't want to fix this:
                        ## [54] for more info or even reference [3]
                        ##
                        ## as that would be unsafe.
                        m_test_nxt_mark_not_eol = \
                          re.search(re.escape(m_next_mark.group()) \
                                     + '\s*[A-Za-z]', current_line)
                        if m_test_nxt_mark_not_eol is not None:
                            ## move this section back to its real line:

                            ## get the segment of line (before the marker,
                            ## which holds a marker that isn't supposed to
                            ## be next) to be moved back to the previous line
                            ## where it belongs, (append a newline to it too):
                            movesect = \
                               current_line[0:m_test_nxt_mark_not_eol.start()] \
                               + "\n"

                            ## Now get the previous line into a variable
                            ## (without its newline at the end):
                            previous_line = fixed[len(fixed) - 1].rstrip("\n")

                            ## Now append the section which is to be moved to the
                            ## previous line. Check the last character
                            ## of the previous line. If it's a space, then just
                            ## directly append this new section. Else, append a
                            ## space then this new section.
                            if previous_line[len(previous_line)-1] not in (u' ',u'-'):
                                movesect = ' ' + movesect
                            previous_line += movesect
                            fixed[len(fixed) - 1] = previous_line

                            ## Now append the remainder of the current line to
                            ## the list of fixed lines, and move on to the
                            ## next line:
                            fixed.append(current_line[m_test_nxt_mark_not_eol.start():])

                            last_marknum += 1
                            break
                        else:
                            ## The next 'marker' in this line was not followed
                            ## by text. Take from the beginning of this line, to
                            ## the end of this marker, and append it to the end
                            ## of the previous line:
                            previous_line = fixed[len(fixed) - 1].rstrip("\n")
                            movesect = current_line[0:m_next_mark.end()] + "\n"
                            ## Append the section to be moved to the previous
                            ## line variable.
                            ## Check the last character of the previous line.
                            ## If it's a space, then just directly append this
                            ## new section. Else, append a space then this new
                            ## section.
                            if previous_line[len(previous_line)-1] not in (u' ',u'-'):
                                movesect = ' ' + movesect
                            previous_line += movesect
                            fixed[len(fixed) - 1] = previous_line
                            ## Should be blank?
                            current_line = current_line[m_next_mark.end():]

                    else:
                        ## This 'marker' is false - its value is not equal to
                        ## the previous marker + 1
                        previous_line = fixed[len(fixed) - 1].rstrip("\n")
                        movesect = current_line[0:m_next_mark.end()] + "\n"
                        ## Now append the section to be moved to the previous
                        ## line variable.
                        ## Check the last character of the previous line. If
                        ## it's a space, then just directly append this new
                        ## section. Else, append a space then this new section.
                        if previous_line[len(previous_line)-1] not in (u' ',u'-'):
                            movesect = ' ' + movesect
                        previous_line += movesect
                        fixed[len(fixed) - 1] = previous_line
                        current_line = current_line[m_next_mark.end():]

                    ## Get next match:
                    m_next_mark = p_refmarker.search(current_line)

                ## If there was still some of the "current line" left,
                ## append it to the previous line:
                if len(current_line.strip()) > 0:
                    previous_line = fixed[len(fixed) - 1].rstrip("\n")
                    movesect = current_line
                    ## Now append the section to be moved to the previous line
                    ## variable.
                    ## Check the last character of the previous line. If it's a
                    ## space, then just directly append this new section. Else,
                    ## append a space then this new section.
                    if previous_line[len(previous_line)-1] not in (u' ',u'-'):
                        movesect = ' ' + movesect
                    previous_line += movesect
                    fixed[len(fixed) - 1] = previous_line

    return fixed


def wash_and_repair_reference_line(line):
    """Wash a reference line of undesirable characters (such as poorly-encoded
       letters, etc), and repair any errors (such as broken URLs) if possible.
       @param line: (string) the reference line to be washed/repaired.
       @return: (string) the washed reference line.
    """
    ## repair URLs in line:
    line = repair_broken_urls(line)
    ## Replace various undesirable characters with their alternatives:
    line = replace_undesirable_characters(line)
    ## remove instances of multiple spaces from line, replacing with a
    ## single space:
    line = re_multiple_space.sub(u' ', line)
    return line

def rebuild_reference_lines(ref_sectn, ref_line_marker_ptn):
    """Given a reference section, rebuild the reference lines. After translation
       from PDF to text, reference lines are often broken. This is because
       pdftotext doesn't know what is a wrapped-line and what is a genuine new
       line. As a result, the following 2 reference lines:
        [1] See http://invenio-software.org/ for more details.
        [2] Example, AN: private communication (1996).
       ...could be broken into the following 4 lines during translation from PDF
       to plaintext:
        [1] See http://invenio-software.org/ fo
        r more details.
        [2] Example, AN: private communica
        tion (1996).
       Such a situation could lead to a citation being separated across 'lines',
       meaning that it wouldn't be correctly recognised.
       This function tries to rebuild the reference lines. It uses the pattern
       used to recognise a reference line's numeration marker to indicate the
       start of a line. If no reference line numeration was recognised, it will
       simply join all lines together into one large reference line.
       @param ref_sectn: (list) of strings. The (potentially broken) reference
        lines.
       @param ref_line_marker_ptn: (string) - the pattern used to recognise a
        reference line's numeration marker.
       @return: (list) of strings - the rebuilt reference section. Each string
        in the list represents a complete reference line.
    """
    ## initialise some vars:
    rebuilt_references = []
    working_line = u''

    len_ref_sectn = len(ref_sectn)

    if ref_line_marker_ptn is None or \
           type(ref_line_marker_ptn) not in (str, unicode):
        if test_for_blank_lines_separating_reference_lines(ref_sectn):
            ## Use blank lines to separate ref lines
            ref_line_marker_ptn = unicode(r'^\s*$')
        else:
            ## No ref line dividers: unmatchable pattern
            ref_line_marker_ptn = unicode(r'^A$^A$$')
    p_ref_line_marker = re.compile(ref_line_marker_ptn, re.I|re.UNICODE)

    ## Work backwards, starting from the last 'broken' reference line
    ## Append each fixed reference line to rebuilt_references
    for x in xrange(len_ref_sectn - 1, -1, -1):
        current_string = ref_sectn[x].strip()
        ## Try to find the marker for the reference line
        m_ref_line_marker = p_ref_line_marker.match(current_string)
        if m_ref_line_marker is not None:
            ## Reference line marker found! : Append this reference to the
            ## list of fixed references and reset the working_line to 'blank'
            if current_string <> '':
                ## If it's not a blank line to separate refs .
                if current_string[len(current_string) - 1] in (u'-', u' '):
                    ## space or hyphenated word at the end of the
                    ## line - don't add in a space
                    working_line = current_string + working_line
                else:
                    ## no space or hyphenated word at the end of this
                    ## line - add in a space
                    working_line = current_string + u' ' + working_line
            ## Append current working line to the refs list
            working_line = working_line.rstrip()
            working_line = wash_and_repair_reference_line(working_line)
            rebuilt_references.append(working_line)
            working_line = u''
        else:
            if current_string != u'':
                ## Continuation of line
                if current_string[len(current_string) - 1] in (u'-', u' '):
                    ## space or hyphenated word at the end of the
                    ## line - don't add in a space
                    working_line = current_string + working_line
                else:
                    ## no space or hyphenated word at the end of this
                    ## line - add in a space
                    working_line = current_string + u' ' + working_line

    if working_line != u'':
        ## Append last line
        working_line = working_line.rstrip()
        working_line = wash_and_repair_reference_line(working_line)
        rebuilt_references.append(working_line)

    ## a list of reference lines has been built backwards - reverse it:
    rebuilt_references.reverse()
    ## Make sure mulitple markers within references are correctly
    ## in place (compare current marker num with current marker num +1)
    rebuilt_references = correct_rebuilt_lines(rebuilt_references, \
                                               p_ref_line_marker)

    ## For each properly formated reference line, try to identify cases
    ## where there is more than one citation in a single line. This is
    ## done by looking for semi-colons, which could be used to
    ## separate references

    return rebuilt_references

def get_reference_lines(docbody,
                        ref_sect_start_line,
                        ref_sect_end_line,
                        ref_sect_title,
                        ref_line_marker_ptn,
                        title_marker_same_line):
    """After the reference section of a document has been identified, and the
       first and last lines of the reference section have been recorded, this
       function is called to take the reference lines out of the document body.
       The document's reference lines are returned in a list of strings whereby
       each string is a reference line. Before this can be done however, the
       reference section is passed to another function that rebuilds any broken
       reference lines.
       @param docbody: (list) of strings - the entire document body.
       @param ref_sect_start_line: (integer) - the index in docbody of the first
        reference line.
       @param ref_sect_end_line: (integer) - the index in docbody of the last
        reference line.
       @param ref_sect_title: (string) - the title of the reference section
        (e.g. "References").
       @param ref_line_marker_ptn: (string) - the patern used to match the
        marker for each reference line (e.g., could be used to match lines
        with markers of the form [1], [2], etc.)
       @param title_marker_same_line: (integer) - a flag to indicate whether
        or not the reference section title was on the same line as the first
        reference line's marker.
       @return: (list) of strings. Each string is a reference line, extracted
        from the document.
    """
    start_idx = ref_sect_start_line
    if title_marker_same_line:
        ## Title on same line as 1st ref- take title out!
        title_start = docbody[start_idx].find(ref_sect_title)
        if title_start != -1:
            ## Set the first line with no title
            docbody[start_idx] = docbody[start_idx][title_start + \
                                                    len(ref_sect_title):]
    elif ref_sect_title is not None:
        ## Set the start of the reference section to be after the title line
        start_idx += 1

    ## now rebuild reference lines:
    ## (Go through each raw reference line, and format them into a set
    ## of properly ordered lines based on markers)
    if type(ref_sect_end_line) is int:
        ref_lines = \
           rebuild_reference_lines(docbody[start_idx:ref_sect_end_line+1], \
                                   ref_line_marker_ptn)
    else:
        ref_lines = rebuild_reference_lines(docbody[start_idx:], \
                                            ref_line_marker_ptn)
    return ref_lines


## ----> Glue - logic for finding and extracting reference section:

def extract_references_from_fulltext(fulltext):
    """Locate and extract the reference section from a fulltext document.
       Return the extracted reference section as a list of strings, whereby each
       string in the list is considered to be a single reference line.
        E.g. a string could be something like:
        '[19] Wilson, A. Unpublished (1986).
       @param fulltext: (list) of strings, whereby each string is a line of the
        document.
       @return: (list) of strings, where each string is an extracted reference
        line.
    """
    ## Try to remove pagebreaks, headers, footers
    fulltext = remove_page_boundary_lines(fulltext)
    status = 0
    #How ref section found flag
    how_found_start = 0
    ## Find start of refs section:
    ref_sect_start = find_reference_section(fulltext)
    if ref_sect_start is not None: how_found_start = 1
    if ref_sect_start is None:
        ## No references found - try with no title option
        ref_sect_start = find_reference_section_no_title_via_brackets(fulltext)
        if ref_sect_start is not None: how_found_start = 2
        ## Try weaker set of patterns if needed
        if ref_sect_start is None:
            ## No references found - try with no title option (with weaker patterns..)
            ref_sect_start = find_reference_section_no_title_via_dots(fulltext)
            if ref_sect_start is not None: how_found_start = 3
            if ref_sect_start is None:
                ## No references found - try with no title option (with even weaker patterns..)
                ref_sect_start = find_reference_section_no_title_via_numbers(fulltext)
                if ref_sect_start is not None: how_found_start = 4
    if ref_sect_start is None:
        ## No References
        refs = []
        status = 4
        if cli_opts['verbosity'] >= 1:
            sys.stdout.write("-----extract_references_from_fulltext: " \
                             "ref_sect_start is None\n")
    else:
        ## If a reference section was found, however weak
        ref_sect_end = \
           find_end_of_reference_section(fulltext, \
                                         ref_sect_start["start_line"], \
                                         ref_sect_start["marker"], \
                                         ref_sect_start["marker_pattern"])
        if ref_sect_end is None:
            ## No End to refs? Not safe to extract
            refs = []
            status = 5
            if cli_opts['verbosity'] >= 1:
                sys.stdout.write("-----extract_references_from_fulltext: " \
                                 "no end to refs!\n")
        else:
            ## If the end of the reference section was found.. start extraction
            refs = get_reference_lines(fulltext, \
                                       ref_sect_start["start_line"], \
                                       ref_sect_end, \
                                       ref_sect_start["title_string"], \
                                       ref_sect_start["marker_pattern"], \
                                       ref_sect_start["title_marker_same_line"])
    return (refs, status, how_found_start)


## Tasks related to conversion of full-text to plain-text:

def _pdftotext_conversion_is_bad(txtlines):
    """Sometimes pdftotext performs a bad conversion which consists of many
       spaces and garbage characters.
       This method takes a list of strings obtained from a pdftotext conversion
       and examines them to see if they are likely to be the result of a bad
       conversion.
       @param txtlines: (list) of unicode strings obtained from pdftotext
        conversion.
       @return: (integer) - 1 if bad conversion; 0 if good conversion.
    """
    ## Numbers of 'words' and 'whitespaces' found in document:
    numWords = numSpaces = 0
    ## whitespace character pattern:
    p_space = re.compile(unicode(r'(\s)'), re.UNICODE)
    ## non-whitespace 'word' pattern:
    p_noSpace = re.compile(unicode(r'(\S+)'), re.UNICODE)
    for txtline in txtlines:
        numWords = numWords + len(p_noSpace.findall(txtline))
        numSpaces = numSpaces + len(p_space.findall(txtline))
    if numSpaces >= (numWords * 3):
        ## Too many spaces - probably bad conversion
        return 1
    else:
        return 0

def convert_PDF_to_plaintext(fpath):
    """Take the path to a PDF file and run pdftotext for this file, capturing
       the output.
       @param fpath: (string) path to the PDF file
       @return: (list) of unicode strings (contents of the PDF file translated
        into plaintext; each string is a line in the document.)
    """
    status = 0
    doclines = []
    ## Pattern to check for lines with a leading page-break character.
    ## If this pattern is matched, we want to split the page-break into
    ## its own line because we rely upon this for trying to strip headers
    ## and footers, and for some other pattern matching.
    p_break_in_line = re.compile(unicode(r'^\s*?(\f)(?!$)(.*?)$'), re.UNICODE)
    ## build pdftotext command:
    cmd_pdftotext = """%(pdftotext)s -raw -q -enc UTF-8 '%(filepath)s' -""" \
                    % { 'pdftotext' : CFG_PATH_PDFTOTEXT,
                        'filepath'  : fpath.replace("'", "\\'")
                      }
    if cli_opts['verbosity'] >= 1:
        sys.stdout.write("%s\n" % cmd_pdftotext)
    ## open pipe to pdftotext:
    pipe_pdftotext = os.popen("%s" % cmd_pdftotext, 'r')
    ## read back results:
    count = 0
    for docline in pipe_pdftotext:
        unicodeline = docline.decode("utf-8")
        ## Check for a page-break in this line:
        m_break_in_line = p_break_in_line.match(unicodeline)
        if m_break_in_line is None:
            ## There was no page-break in this line. Just add the line:
            doclines.append(unicodeline)
            count += 1
        else:
            ## If there was a page-break character in the same line as some
            ## text, split it out into its own line so that we can later
            ## try to find headers and footers:
            doclines.append(m_break_in_line.group(1))
            doclines.append(m_break_in_line.group(2))
            count += 2
    ## close pipe to pdftotext:
    pipe_pdftotext.close()
    if cli_opts['verbosity'] >= 1:
        sys.stdout.write("-----convert_PDF_to_plaintext found: " \
                         "%s lines of text\n" % str(count))

    ## finally, check conversion result not bad:
    if _pdftotext_conversion_is_bad(doclines):
        status = 2
        doclines = []
    return (doclines, status)

def get_plaintext_document_body(fpath):
    """Given a file-path to a full-text, return a list of unicode strings
       whereby each string is a line of the fulltext.
       In the case of a plain-text document, this simply means reading the
       contents in from the file. In the case of a PDF/PostScript however,
       this means converting the document to plaintext.
       @param: fpath: (string) - the path to the fulltext file
       @return: (list) of strings - each string being a line in the document.
    """
    textbody = []
    status = 0
    if os.access(fpath, os.F_OK|os.R_OK):
        ## filepath OK - attempt to extract references:
        ## get file type:
        pipe_gfile = \
               os.popen("%s '%s'" \
                        % (CFG_PATH_GFILE, fpath.replace("'", "\\'")), "r")
        res_gfile = pipe_gfile.readline()
        pipe_gfile.close()

        if (res_gfile.lower().find("text") != -1 or
           res_gfile.lower().find("txt") != -1) and \
           res_gfile.lower().find("pdf") == -1:
            ## plain-text file: don't convert - just read in:
            textbody = []
            for line in open("%s" % fpath, "r").readlines():
                textbody.append(line.decode("utf-8"))
        elif res_gfile.lower().find("pdf") != -1:
            ## convert from PDF
            (textbody, status) = convert_PDF_to_plaintext(fpath)
    else:
        ## filepath not OK
        status = 1
    return (textbody, status)

def write_raw_references_to_stream(recid, raw_refs, strm=None):
    """Write a lost of raw reference lines to the a given stream.
       Each reference line is preceeded by the record-id. Thus, if for example,
       the following 2 reference lines were passed to this function:
        [1] See http://invenio-software.org/ for more details.
        [2] Example, AN: private communication (1996).
       and the record-id was "1", the raw reference lines printed to the stream
       would be:
        1:[1] See http://invenio-software.org/ for more details.
        1:[2] Example, AN: private communication (1996).
       @param recid: (string) the record-id of the document for which raw
        references are to be written-out.
       @param raw_refs: (list) of strings. The raw references to be written-out.
       @param strm: (open stream object) - the stream object to which the
        references are to be written. If the stream object is not a valid open
        stream (or is None, by default), the standard error stream (sys.stderr)
        will be used by default.
       @return: None.
    """
    if strm is None or type(strm) is not file:
        ## invalid stream supplied - write to sys.stderr
        strm = sys.stderr
    elif strm.closed:
        ## The stream was closed - use stderr:
        strm = sys.stderr
    ## write the reference lines to the stream:
    strm.writelines(map(lambda x: "%(recid)s:%(refline)s\n" \
                        % { 'recid' : recid,
                            'refline' : x.encode("utf-8") }, raw_refs))
    strm.flush()

def usage(wmsg="", err_code=0):
    """Display a usage message for refextract on the standard error stream and
       then exit.
       @param wmsg: (string) - some kind of warning message for the user.
       @param err_code: (integer) - an error code to be passed to sys.exit,
        which is called after the usage message has been printed.
       @return: None.
    """
    if wmsg != "":
        wmsg = wmsg.strip() + "\n"
    msg = """  Usage: refextract [options] recid:file1 [recid:file2 ...]

  refextract tries to extract the reference section from a full-text document.
  Extracted reference lines are processed and any recognised citations are
  marked up using MARC XML. Results are output to the standard output stream.

  Options:
   -h, --help     print this help
   -V, --version  print version information
   -v, --verbose  verbosity level (0=mute, 1=default info msg,
                  2=display reference section extraction analysis,
                  3=display reference line citation processing analysis,
                  9=max information)
   -r, --output-raw-refs
                  output raw references, as extracted from the document.
                  No MARC XML mark-up - just each extracted line, prefixed
                  by the recid of the document that it came from.
   -x, --xmlfile
                  write the extracted references, in xml form, to a file rather
                  than standard output.
   -d, --dictfile
                  write statistics about all matched title abbreviations
                  (i.e. LHS terms in the titles knowledge base) to a file.
   -z, --raw-references
                  treat the input file as pure references. i.e. skip the stage
                  of trying to locate the reference section within a document
                  and instead move to the stage of recognition and
                  standardisation of citations within lines.
   -s, --inspire
                  output journal title numeration in the inspire recognised
                  format: [series]volume,page,year.
   -j, --kb-journal
                  manually specify the location of a journal title knowledge-
                  base file.
   -n, --kb-report-number
                  manually specify the location of a report number knowledge-
                  base file.

  Example: refextract -x /home/chayward/refs.xml 499:/home/chayward/thesis.pdf
"""
    sys.stderr.write(wmsg + msg)
    sys.exit(err_code)

def get_cli_options():
    """Get the various arguments and options from the command line and populate
       a dictionary of cli_options.
       @return: (tuple) of 2 elements. First element is a dictionary of cli
        options and flags, set as appropriate; Second element is a list of cli
        arguments.
    """
    global cli_opts
    ## dictionary of important flags and values relating to cli call of program:
    cli_opts = { 'treat_as_reference_section' : 0,
                 'output_raw'                 : 0,
                 'verbosity'                  : 0,
                 'xmlfile'                    : 0,
                 'dictfile'                   : 0,
                 'inspire'                    : 0,
                 'kb-journal'                 : 0,
                 'kb-report-number'           : 0,
               }

    try:
        myoptions, myargs = getopt.getopt(sys.argv[1:], "hVv:zrx:d:sj:n:", \
                                          ["help",
                                           "version",
                                           "verbose=",
                                           "raw-references",
                                           "output-raw-refs",
                                           "xmlfile=",
                                           "dictfile=",
                                           "inspire",
                                           "kb-journal=",
                                           "kb-report-number="])
    except getopt.GetoptError, err:
        ## Invalid option provided - usage message
        usage(wmsg="Error: %(msg)s." % { 'msg' : str(err) })

    for o in myoptions:
        if o[0] in ("-V","--version"):
            ## version message and exit
            sys.stdout.write("%s\n" % __revision__)
            sys.stdout.flush()
            sys.exit(0)
        elif o[0] in ("-h","--help"):
            ## help message and exit
            usage()
        elif o[0] in ("-r", "--output-raw-refs"):
            cli_opts['output_raw'] = 1
        elif o[0] in ("-v", "--verbose"):
            if not o[1].isdigit():
                cli_opts['verbosity'] = 0
            elif int(o[1]) not in xrange(0, 10):
                cli_opts['verbosity'] = 0
            else:
                cli_opts['verbosity'] = int(o[1])
        elif o[0] in ("-z", "--raw-references"):
            ## treat input as pure reference lines:
            cli_opts['treat_as_reference_section'] = 1
        elif o[0] in ("-x", "--xmlfile"):
            ## Write out MARC XML references to the specified file
            cli_opts['xmlfile'] = o[1]
        elif o[0] in ("-d", "--dictfile"):
            ## Write out the statistics of all titles matched during the
            ## extraction job to the specified file
            cli_opts['dictfile'] = o[1]
        elif o[0] in ("-s", "--inspire"):
            ## Output recognised journal titles in the Inspire compatible
            ## format
            cli_opts['inspire'] = 1
        elif o[0] in ("-j","--kb-journal"):
            ## The location of the journal title kb requested to override
            ## a 'configuration file'-specified kb, holding
            ## 'seek---replace' terms, used when matching titles in references
            cli_opts['kb-journal'] = o[1]
        elif o[0] in ("-n","--kb-report-number"):
            ## The location of the report number kb requested to override
            ## a 'configuration file'-specified kb
            cli_opts['kb-report-number'] = o[1]

    # What journal title format are we using?
    if cli_opts['verbosity'] > 0 and cli_opts['inspire']:
        sys.stdout.write("--- Using inspire journal title form\n")
    elif cli_opts['verbosity'] > 0:
        sys.stdout.write("--- Using invenio journal title form\n")

    if len(myargs) == 0:
        ## no arguments: error message
        usage(wmsg="Error: no full-text.")

    return (cli_opts, myargs)

def display_xml_record(status_code, count_reportnum, count_title, count_url,
                       count_doi, count_misc, count_auth_group, recid, xml_lines):
    """Given a series of MARC XML-ized reference lines and a record-id, write a
       MARC XML record to the stdout stream. Include in the record some stats
       for the extraction job.
       The printed MARC XML record will essentially take the following
       structure:
        <record>
           <controlfield tag="001">1</controlfield>
           <datafield tag="999" ind1="C" ind2="5">
              [...]
           </datafield>
           [...]
           <datafield tag="999" ind1="C" ind2="6">
              <subfield code="a">
        Invenio/X.XX.X refextract/X.XX.X-timestamp-err-repnum-title-URL-misc
              </subfield>
           </datafield>
        </record>
       Timestamp, error(code), reportnum, title, URL, and misc will are of
       course take the relevant values.

       @param status_code: (integer)the status of reference-extraction for the
        given record: was there an error or not? 0 = no error; 1 = error.
       @param count_reportnum: (integer) - the number of institutional
        report-number citations found in the document's reference lines.
       @param count_title: (integer) - the number of journal title citations
        found in the document's reference lines.
       @param count_url: (integer) - the number of URL citations found in the
        document's reference lines.
       @param count_misc: (integer) - the number of sections of miscellaneous
        text (i.e. 999C5$m) from the document's reference lines.
       @param count_auth_group: (integer) - the total number of author groups
        identified ($h)
       @param recid: (string) - the record-id of the given document. (put into
        001 field.)
       @param xml_lines: (list) of strings. Each string in the list contains a
        group of MARC XML 999C5 datafields, making up a single reference line.
        These reference lines will make up the document body.
       @return: The entire MARC XML textual output, plus recognition statistics.
    """
    ## Start with the opening record tag:
    out = u"%(record-open)s\n" \
              % { 'record-open' : CFG_REFEXTRACT_XML_RECORD_OPEN, }

    ## Display the record-id controlfield:
    out += \
     u"""   <controlfield tag="%(cf-tag-recid)s">%(recid)s</controlfield>\n""" \
     % { 'cf-tag-recid' : CFG_REFEXTRACT_CTRL_FIELD_RECID,
         'recid'        : encode_for_xml(recid),
       }

    ## Loop through all xml lines and add them to the output string:
    for line in xml_lines:
        out += line

    ## add the 999C6 status subfields:
    out += u"""   <datafield tag="%(df-tag-ref-stats)s" ind1="%(df-ind1-ref-stats)s" ind2="%(df-ind2-ref-stats)s">
      <subfield code="%(sf-code-ref-stats)s">%(version)s-%(timestamp)s-%(status)s-%(reportnum)s-%(title)s-%(author)s-%(url)s-%(doi)s-%(misc)s</subfield>
   </datafield>\n""" \
        % { 'df-tag-ref-stats'  : CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS,
            'df-ind1-ref-stats' : CFG_REFEXTRACT_IND1_EXTRACTION_STATS,
            'df-ind2-ref-stats' : CFG_REFEXTRACT_IND2_EXTRACTION_STATS,
            'sf-code-ref-stats' : CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS,
            'version'           : CFG_REFEXTRACT_VERSION,
            'timestamp'         : str(int(mktime(localtime()))),
            'status'            : status_code,
            'reportnum'         : count_reportnum,
            'title'             : count_title,
            'author'            : count_auth_group,
            'url'               : count_url,
            'doi'               : count_doi,
            'misc'              : count_misc,
          }

    ## Now add the closing tag to the record:
    out += u"%(record-close)s\n" \
           % { 'record-close' : CFG_REFEXTRACT_XML_RECORD_CLOSE, }

    return out

def sum_2_dictionaries(dicta, dictb):
    """Given two dictionaries of totals, where each total refers to a key
       in the dictionary, add the totals.
       E.g.:  dicta = { 'a' : 3, 'b' : 1 }
              dictb = { 'a' : 1, 'c' : 5 }
              dicta + dictb = { 'a' : 4, 'b' : 1, 'c' : 5 }
       @param dicta: (dictionary)
       @param dictb: (dictionary)
       @return: (dictionary) - the sum of the 2 dictionaries
    """
    dict_out = dicta.copy()
    for key in dictb.keys():
        if dict_out.has_key(key):
            ## Add the sum for key in dictb to that of dict_out:
            dict_out[key] += dictb[key]
        else:
            ## the key is not in the first dictionary - add it directly:
            dict_out[key] = dictb[key]
    return dict_out

def main():
    """Main function.
    """
    global cli_opts
    (cli_opts, cli_args) =  get_cli_options()

    ## A dictionary to contain the counts of all 'bad titles' found during
    ## this reference extraction job:
    all_found_titles_count = {}

    extract_jobs = get_recids_and_filepaths(cli_args)
    if len(extract_jobs) == 0:
        ## no files provided for reference extraction - error message
        usage()

    ## Read the journal titles knowledge base, creating the search
    ## patterns and replace terms. Check for user-specified journal kb.
    if cli_opts['kb-journal'] != 0:
        (title_search_kb, \
         title_search_standardised_titles, \
         title_search_keys) = \
                   build_titles_knowledge_base(cli_opts['kb-journal'])
    else:
        (title_search_kb, \
         title_search_standardised_titles, \
         title_search_keys) = \
                   build_titles_knowledge_base(CFG_REFEXTRACT_KB_JOURNAL_TITLES)

    ## Read the report numbers knowledge base, creating the search
    ## patterns and replace terms. Check for user-specified rep-no kb.
    if cli_opts['kb-report-number'] != 0:
        (preprint_reportnum_sre, \
         standardised_preprint_reportnum_categs) = \
                   build_reportnum_knowledge_base(cli_opts['kb-report-number'])
    else:
        (preprint_reportnum_sre, \
         standardised_preprint_reportnum_categs) = \
                   build_reportnum_knowledge_base(CFG_REFEXTRACT_KB_REPORT_NUMBERS)

    done_coltags = 0 ## flag to signal that the starting XML collection
                     ## tags have been output to either an xml file or stdout

    for curitem in extract_jobs:
        how_found_start = -1  ## flag to indicate how the reference start section was found (or not)
        extract_error = 0  ## extraction was OK unless determined otherwise
        ## reset the stats counters:
        count_misc = count_title = count_reportnum = count_url = count_doi = count_auth_group = 0
        recid = curitem[0]
        if cli_opts['verbosity'] >= 1:
            sys.stdout.write("--- processing RecID: %s pdffile: %s; %s\n" \
                             % (str(curitem[0]), curitem[1], ctime()))

        ## 1. Get this document body as plaintext:
        (docbody, extract_error) = get_plaintext_document_body(curitem[1])
        if extract_error == 1:
            ## Non-existent or unreadable pdf/text directory.
            sys.stderr.write("Error: could not open %s for extraction.\n" \
                             % curitem[1])
            sys.exit(1)
        if extract_error == 0 and len(docbody) == 0:
            extract_error = 3
        if cli_opts['verbosity'] >= 1:
            sys.stdout.write("-----get_plaintext_document_body gave: " \
                             "%s lines, overall error: %s\n" \
                             % (str(len(docbody)), str(extract_error)))

        if not done_coltags:
            ## Output opening XML collection tags:
            ## Initialise ouput xml file if the relevant cli flag/arg exists
            if cli_opts['xmlfile']:
                try:
                    ofilehdl = open(cli_opts['xmlfile'], 'w')
                    ofilehdl.write("%s\n" \
                          % CFG_REFEXTRACT_XML_VERSION.encode("utf-8"))
                    ofilehdl.write("%s\n" \
                          % CFG_REFEXTRACT_XML_COLLECTION_OPEN.encode("utf-8"))
                    ofilehdl.flush()
                except:
                    sys.stdout.write("***%s\n\n" % cli_opts['xmlfile'])
                    raise IOError("Cannot open %s to write!" \
                                  % cli_opts['xmlfile'])
            ## else, write the xml lines to the stdout
            else:
                sys.stdout.write("%s\n" \
                          % CFG_REFEXTRACT_XML_VERSION.encode("utf-8"))
                sys.stdout.write("%s\n" \
                          % CFG_REFEXTRACT_XML_COLLECTION_OPEN.encode("utf-8"))
            done_coltags = 1

        if len(docbody) > 0:
            ## the document body is not empty:
            ## 2. If necessary, locate the reference section:
            if cli_opts['treat_as_reference_section']:
                ## don't search for citations in the document body:
                ## treat it as a reference section:
                reflines = docbody
            else:
                ## launch search for the reference section in the document body:
                (reflines, extract_error, how_found_start) = \
                           extract_references_from_fulltext(docbody)
                if len(reflines) == 0 and extract_error == 0:
                    extract_error = 6
                if cli_opts['verbosity'] >= 1:
                    sys.stdout.write("-----extract_references_from_fulltext " \
                                     "gave len(reflines): %s overall error: " \
                                     "%s\n" \
                                     % (str(len(reflines)), str(extract_error)))

            ## 3. Standardise the reference lines:
            #reflines = test_get_reference_lines()
            (processed_references, count_misc, \
             count_title, count_reportnum, \
             count_url, count_doi, count_auth_group, \
             record_titles_count) = \
              create_marc_xml_reference_section(reflines,
                                                preprint_repnum_search_kb=\
                                                  preprint_reportnum_sre,
                                                preprint_repnum_standardised_categs=\
                                                  standardised_preprint_reportnum_categs,
                                                periodical_title_search_kb=\
                                                  title_search_kb,
                                                standardised_periodical_titles=\
                                                  title_search_standardised_titles,
                                                periodical_title_search_keys=\
                                                  title_search_keys)

            ## Add the count of 'bad titles' found in this line to the total
            ## for the reference section:
            all_found_titles_count = \
                                   sum_2_dictionaries(all_found_titles_count, \
                                                      record_titles_count)


        else:
            ## document body is empty, therefore the reference section is empty:
            reflines = []
            processed_references = []

        ## 4. Display the extracted references, status codes, etc:
        if cli_opts['output_raw']:
            ## now write the raw references to the stream:
            raw_file = str(recid) + '.rawrefs'
            try:
                rawfilehdl = open(raw_file, 'w')
                write_raw_references_to_stream(recid, reflines, rawfilehdl)
                rawfilehdl.close()
            except:
                raise IOError("Cannot open raw ref file: %s to write" \
                              % raw_file)
        ## If found ref section by a weaker method and only found misc/urls then junk it
        ## studies show that such cases are ~ 100% rubbish. Also allowing only
        ## urls found greatly increases the level of rubbish accepted..
        if count_reportnum + count_title == 0 and how_found_start > 2:
            count_misc = count_url = count_doi = count_auth_group = 0
            processed_references = []
            if cli_opts['verbosity'] >= 1:
                sys.stdout.write("-----Found ONLY miscellaneous/Urls so removed it how_found_start=  %d\n" % (how_found_start))
        elif  count_reportnum + count_title  > 0 and how_found_start > 2:
            if cli_opts['verbosity'] >= 1:
                sys.stdout.write("-----Found journals/reports with how_found_start=  %d\n" % (how_found_start))

        ## Display the processed reference lines:
        out = display_xml_record(extract_error, \
                                 count_reportnum, \
                                 count_title, \
                                 count_url, \
                                 count_doi, \
                                 count_misc, \
                                 count_auth_group, \
                                 recid, \
                                 processed_references)

        ## Filter the processed reference lines to remove junk
        out = filter_processed_references(out)  ## Be sure to call this BEFORE compress_subfields
                                                ## since filter_processed_references expects the
                                                ## original xml format.
        ## Compress mulitple 'm' subfields in a datafield
        out = compress_subfields(out,CFG_REFEXTRACT_SUBFIELD_MISC)
        ## Compress multiple 'h' subfields in a datafield
        out = compress_subfields(out,CFG_REFEXTRACT_SUBFIELD_AUTH)

        if cli_opts['verbosity'] >= 1:
            lines = out.split('\n')
            sys.stdout.write("-----display_xml_record gave: %s significant " \
                             "lines of xml, overall error: %s\n" \
                             % (str(len(lines) - 7), extract_error))
        if cli_opts['xmlfile']:
            ofilehdl.write("%s" % (out.encode("utf-8"),))
            ofilehdl.flush()
        else:
            ## Write the record to the standard output stream:
            sys.stdout.write("%s" % out.encode("utf-8"))
            sys.stdout.flush()

    ## If an XML collection was opened, display closing tag
    if done_coltags:
        if (cli_opts['xmlfile']):
            ofilehdl.write("%s\n" \
                          % CFG_REFEXTRACT_XML_COLLECTION_CLOSE.encode("utf-8"))
            ofilehdl.close()
            ## limit m tag data to something less than infinity
            limit_m_tags(cli_opts['xmlfile'], 2024)
        else:
            sys.stdout.write("%s\n" \
                          % CFG_REFEXTRACT_XML_COLLECTION_CLOSE.encode("utf-8"))

    ## If the option to write the statistics about all periodical titles matched
    ## during the extraction-job was selected, do so using the specified file.
    ## Note: the matched titles are the Left-Hand-Side titles in the KB, i.e.
    ## the BAD versions of titles.
    if cli_opts['dictfile']:
        ## title_keys are the titles matched:
        title_keys = all_found_titles_count.keys()
        try:
            dfilehdl = open(cli_opts['dictfile'], "w")
            for ktitle in title_keys:
                dfilehdl.write("%d:%s\n" \
                   % (all_found_titles_count[ktitle], ktitle.encode("utf-8")))
                dfilehdl.flush()
            dfilehdl.close()
        except IOError, (errno, err_string):
            ## There was a problem writing out the statistics
            sys.stderr.write("""Error: Unable to write "matched titles" """ \
                             """statistics to output file %s. """ \
                             """Error Number %d (%s).\n""" \
                             % (cli_opts['dictfile'], errno, err_string))
            sys.exit(1)


def test_get_reference_lines():
    """Returns some test reference lines.
       @return: (list) of strings - the test reference lines. Each
        string in the list is a reference line that should be processed.
    """
    ## new addition: include two references containing a standard DOI and a DOI embedded in an http link (last two references)

    reflines = ["""[1] <a href="http://cdsweb.cern.ch/">CERN Document Server</a> J. Maldacena, Adv. Theor. Math. Phys. 2 (1998) 231; hep-th/9711200. http://cdsweb.cern.ch/ then http://www.itp.ucsb.edu/online/susyc99/discussion/. ; L. Susskind, J. Math. Phys. 36 (1995) 6377; hep-th/9409089. hello world a<a href="http://uk.yahoo.com/">Yahoo!</a>. Fin.""",
                """[1] J. Maldacena, Adv. Theor. Math. Phys. 2 (1998) 231; hep-th/9711200. http://cdsweb.cern.ch/""",
                """[2] S. Gubser, I. Klebanov and A. Polyakov, Phys. Lett. B428 (1998) 105; hep-th/9802109. http://cdsweb.cern.ch/search.py?AGE=hello-world&ln=en""",
                """[3] E. Witten, Adv. Theor. Math. Phys. 2 (1998) 253; hep-th/9802150.""",
                """[4] O. Aharony, S. Gubser, J. Maldacena, H. Ooguri and Y. Oz, hep-th/9905111.""",
                """[5] L. Susskind, J. Math. Phys. 36 (1995) 6377; hep-th/9409089.""",
                """[6] L. Susskind and E. Witten, hep-th/9805114.""",
                """[7] W. Fischler and L. Susskind, hep-th/9806039; N. Kaloper and A. Linde, Phys. Rev. D60 (1999) 105509, hep-th/9904120.""",
                """[8] R. Bousso, JHEP 9906:028 (1999); hep-th/9906022.""",
                """[9] R. Penrose and W. Rindler, Spinors and Spacetime, volume 2, chapter 9 (Cambridge University Press, Cambridge, 1986).""",
                """[10] R. Britto-Pacumio, A. Strominger and A. Volovich, JHEP 9911:013 (1999); hep-th/9905211. blah hep-th/9905211 blah hep-ph/9711200""",
                """[11] V. Balasubramanian and P. Kraus, Commun. Math. Phys. 208 (1999) 413; hep-th/9902121.""",
                """[12] V. Balasubramanian and P. Kraus, Phys. Rev. Lett. 83 (1999) 3605; hep-th/9903190.""",
                """[13] P. Kraus, F. Larsen and R. Siebelink, hep-th/9906127.""",
                """[14] L. Randall and R. Sundrum, Phys. Rev. Lett. 83 (1999) 4690; hep-th/9906064. this is a test RN of a different type: CERN-LHC-Project-Report-2006-003. more text.""",
                """[15] S. Gubser, hep-th/9912001.""",
                """[16] H. Verlinde, hep-th/9906182; H. Verlinde, hep-th/9912018; J. de Boer, E. Verlinde and H. Verlinde, hep-th/9912012.""",
                """[17] E. Witten, remarks at ITP Santa Barbara conference, "New dimensions in field theory and string theory": http://www.itp.ucsb.edu/online/susyc99/discussion/.""",
                """[18] D. Page and C. Pope, Commun. Math. Phys. 127 (1990) 529.""",
                """[19] M. Duff, B. Nilsson and C. Pope, Physics Reports 130 (1986), chapter 9.""",
                """[20] D. Page, Phys. Lett. B79 (1978) 235.""",
                """[21] M. Cassidy and S. Hawking, Phys. Rev. D57 (1998) 2372, hep-th/9709066; S. Hawking, Phys. Rev. D52 (1995) 5681.""",
                """[22] K. Skenderis and S. Solodukhin, hep-th/9910023.""",
                """[23] M. Henningson and K. Skenderis, JHEP 9807:023 (1998), hep-th/9806087.""",
                """[24] C. Fefferman and C. Graham, "Conformal Invariants", in Elie Cartan et les Mathematiques d'aujourd'hui (Asterisque, 1985) 95.""",
                """[25] C. Graham and J. Lee, Adv. Math. 87 (1991) 186. <a href="http://cdsweb.cern.ch/">CERN Document Server</a>""",
                """[26] E. Witten and S.-T. Yau, hep-th/9910245.""",
                """[27] R. Emparan, JHEP 9906:036 (1999); hep-th/9906040.""",
                """[28] A. Chamblin, R. Emparan, C. Johnson and R. Myers, Phys. Rev. D59 (1999) 64010, hep-th/9808177; S. Hawking, C. Hunter and D. Page, Phys. Rev. D59 (1999) 44033, hep-th/9809035.""",
                """[29] S. Sethi and L. Susskind, Phys. Lett. B400 (1997) 265, hep-th/9702101; T. Banks and N. Seiberg, Nucl. Phys. B497 (1997) 41, hep-th/9702187.""",
                """[30] R. Emparan, C. Johnson and R. Myers, Phys. Rev. D60 (1999) 104001; hep-th/9903238.""",
                """[31] S. Hawking, C. Hunter and M. Taylor-Robinson, Phys. Rev. D59 (1999) 064005; hep-th/9811056.""",
                """[32] J. Dowker, Class. Quant. Grav. 16 (1999) 1937; hep-th/9812202.""",
                """[33] J. Brown and J. York, Phys. Rev. D47 (1993) 1407.""",
                """[34] D. Freedman, S. Mathur, A. Matsuis and L. Rastelli, Nucl. Phys. B546 (1999) 96; hep-th/9804058. More text, followed by an IBID A 546 (1999) 96""",
                """[35] D. Freedman, S. Mathur, A. Matsuis and L. Rastelli, Nucl. Phys. B546 (1999) 96; hep-th/9804058. More text, followed by an IBID A""",
                """[37] some misc  lkjslkdjlksjflksj [hep-th/9804058] lkjlkjlkjlkj [hep-th/0001567], hep-th/1212321, some more misc, Nucl. Phys. B546 (1999) 96""",
                """[38] R. Emparan, C. Johnson and R.... Myers, Phys. Rev. D60 (1999) 104001; this is :: .... misc! hep-th/9903238. and some ...,.,.,.,::: more hep-ph/9912000""",
                """[10] A. Ceresole, G. Dall Agata and R. D Auria, JHEP 11(1999) 009, [hep-th/9907216].""",
                """[12] D.P. Jatkar and S. Randjbar-Daemi, Phys. Lett. B460, 281 (1999) [hep-th/9904187].""",
                """[14] G. DallAgata, Phys. Lett. B460, (1999) 79, [hep-th/9904198].""",
                """[13] S.M. Donaldson, Instantons and Geometric Invariant Theory, Comm. Math. Phys., 93, (1984), 453-460.""",
                """[16] Becchi C., Blasi A., Bonneau G., Collina R., Delduc F., Commun. Math. Phys., 1988, 120, 121.""",
                """[26]: N. Nekrasov, A. Schwarz, Instantons on noncommutative R4 and (2, 0) superconformal six-dimensional theory, Comm. Math. Phys., 198, (1998), 689-703.""",
                """[2] H. J. Bhabha, Rev. Mod. Phys. 17, 200(1945); ibid, 21, 451(1949); S. Weinberg, Phys. Rev. 133, B1318(1964); ibid, 134, 882(1964); D. L. Pursey, Ann. Phys(N. Y)32, 157(1965); W. K. Tung, Phys, Rev. Lett. 16, 763(1966); Phys. Rev. 156, 1385(1967); W. J. Hurley, Phys. Rev. Lett. 29, 1475(1972).""",
                """[21] E. Schrodinger, Sitzungsber. Preuss. Akad. Wiss. Phys. Math. Kl. 24, 418(1930); ibid, 3, 1(1931); K. Huang, Am. J. Phys. 20, 479(1952); H. Jehle, Phys, Rev. D3, 306(1971); G. A. Perkins, Found. Phys. 6, 237(1976); J. A. Lock, Am. J. Phys. 47, 797(1979); A. O. Barut et al, Phys. Rev. D23, 2454(1981); ibid, D24, 3333(1981); ibid, D31, 1386(1985); Phys. Rev. Lett. 52, 2009(1984).""",
                """[1] P. A. M. Dirac, Proc. R. Soc. London, Ser. A155, 447(1936); ibid, D24, 3333(1981).""",
                """[40] O.O. Vaneeva, R.O. Popovych and C. Sophocleous, Enhanced Group Analysis and Exact Solutions of Vari-able Coefficient Semilinear Diffusion Equations with a Power Source, Acta Appl. Math., doi:10.1007/s10440-008-9280-9, 46 p., arXiv:0708.3457.""",
                """[41] M. I. Trofimov, N. De Filippis and E. A. Smolenskii. Application of the electronegativity indices of organic molecules to tasks of chemical informatics. Russ. Chem. Bull., 54:2235-2246, 2005. http://dx.doi.org/10.1007/s11172-006-0105-6.""",
                """[42] M. Gell-Mann, P. Ramon ans R. Slansky, in Supergravity, P. van Niewenhuizen and D. Freedman (North-Holland 1979); T. Yanagida, in Proceedings of the Workshop on the Unified Thoery and the Baryon Number in teh Universe, ed. O. Sawaga and A. Sugamoto (Tsukuba 1979); R.N. Mohapatra and G. Senjanovic, Phys. Rev. Lett. 44, 912, (1980).
                """,
                """[43] L.S. Durkin and P. Langacker, Phys. Lett B166, 436 (1986); Amaldi et al., Phys. Rev. D36, 1385 (1987); Hayward and Yellow et al., eds. Phys. Lett B245, 669 (1990); Nucl. Phys. B342, 15 (1990);
                """,
                """[44] M. I. Moli_ero, and J. C. Oller, Performance test of the CMS link alignment system
                """,
                """[45] Hush, D.R., R.Leighton, and B.G. Horne, 1993. "Progress in supervised Neural Netw. What's new since Lippmann?" IEEE Signal Process. Magazine 10, 8-39
                """,
                """[15] Nucl. Phys., B372, 3 (1992); T.G. Rizzo, Phys. Rev. D40, 3035 (1989); Proceedings of the 1990 Summer Study on High Energy Physics. ed E. Berger, June 25-July 13, 1990, Snowmass Colorado (World Scientific, Singapore, 1992) p. 233; V. Barger, J.L. Hewett and T.G. Rizzo, Phys. Rev. D42, 152 (1990); J.L. Hewett, Phys. Lett. B238, 98 (1990);
                """,
                """[234] Hawking S., P. van Niewenhuizen, L.S. Durkin, D. Freeman, some title of some journal
                """,
                """[235] Hawking S., D. Freeman, some title of some journal
                """,
                """[236] Hawking S. and D. Freeman, another random title of some random journal
                """,
                """[237] L.S. Durkin and P. Langacker, Phys. Lett B166, 436 (1986); Amaldi et al., Phys. Rev. D36, 1385 (1987); G. Altarelli et al., Phys. Lett B245, 669 (1990); Nucl. Phys. B342, 15 (1990); Phys. Lett. B261, 146 (1991); ibidem B263, 459 (1991);
                """,
               ]
    return reflines

if __name__ == '__main__':
    main()
