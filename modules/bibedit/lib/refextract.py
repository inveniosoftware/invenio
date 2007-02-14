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

"""This is the main body of refextract. It is used to extract references from
   fulltext PDF documents.
"""

__revision__ = "$Id$"

try:
    import sys, re, sre
    import os, getopt, cgi
    from cStringIO import StringIO
    from time import mktime, localtime
    from invenio.refextract_config import *
    from invenio.config import CFG_PATH_GFILE
except ImportError, err:
    raise ImportError(err)


def get_url_repair_patterns():
    """Initialise and return a list of precompiled regexp patterns that are used to
       try to re-assemble URLs that have been broken during a document's conversion
       to plain-text.
       @return: (list) of compiled sre regexp patterns used for finding various
        broken URLs.
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
    pattern_list.append(sre.compile(r'(h\s*t\s*t\s*p\s*\:\s*\/\s*\/)', \
                                    sre.I|sre.UNICODE))
    pattern_list.append(sre.compile(r'(f\s*t\s*p\s*\:\s*\/\s*\/\s*)', \
                                    sre.I|sre.UNICODE))
    pattern_list.append(sre.compile(r'((http|ftp):\/\/\s*[\w\d])', \
                                    sre.I|sre.UNICODE))
    pattern_list.append(sre.compile(r'((http|ftp):\/\/([\w\d\s\._\-])+?\s*\/)', \
                                    sre.I|sre.UNICODE))
    pattern_list.append(sre.compile(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)+)', \
                                    sre.I|sre.UNICODE))
    p_url = \
     sre.compile(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)*([\w\d\_\s\-]+\.\s?[\w\d]+))', \
      sre.I|sre.UNICODE)
    pattern_list.append(p_url)
    ## some possible endings for URLs:
    for x in file_types_list:
        p_url = \
            sre.compile(\
              r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*([\w\d\_\-]+\.' + x + u'))', \
              sre.I|sre.UNICODE)
        pattern_list.append(p_url)
    ## if url last thing in line, and only 10 letters max, concat them
    p_url = \
        sre.compile(\
          r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*\s*?([\w\d\_\.\-]\s?){1,10}\s*)$', \
          sre.I|sre.UNICODE)
    pattern_list.append(p_url)
    return pattern_list

def get_bad_char_replacements():
    """When a document is converted to plain-text from PDF, certain characters may result in the
       plain-text, that are either unwanted, or broken. These characters need to be corrected or
       removed. Examples are, certain control characters that would be illegal in XML and must be
       removed; TeX ligatures (etc); broken accents such as umlauts on letters that must be corrected.
       This function returns a dictionary of (unwanted) characters to look for and the characters
       that should be used to replace them.
       @return: (dictionary) - { seek -> replace, } or charsacters to replace in plain-text.
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
        ## pdftotext has problems with umlaut and prints it as diaeresis followed by a letter:correct it
        ## (Optional space between char and letter - fixes broken line examples)
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
    }
    return replacements

## precompile some often-used regexp for speed reasons:
sre_regexp_character_class               = sre.compile(r'\[[^\]]+\]', sre.UNICODE)
sre_space_comma                          = sre.compile(r'\s,', sre.UNICODE)
sre_space_semicolon                      = sre.compile(r'\s;', sre.UNICODE)
sre_space_period                         = sre.compile(r'\s\.', sre.UNICODE)
sre_colon_space_colon                    = sre.compile(r':\s:', sre.UNICODE)
sre_comma_space_colon                    = sre.compile(r',\s:', sre.UNICODE)
sre_space_closing_square_bracket         = sre.compile(r'\s\]', sre.UNICODE)
sre_opening_square_bracket_space         = sre.compile(r'\[\s', sre.UNICODE)
sre_hyphens = sre.compile(r'(\\255|\u02D7|\u0335|\u0336|\u2212|\u002D|\uFE63|\uFF0D)', sre.UNICODE)
sre_multiple_hyphens                     = sre.compile(r'-{2,}', sre.UNICODE)
sre_multiple_space                       = sre.compile(r'\s{2,}', sre.UNICODE)
sre_group_captured_multiple_space        = sre.compile(r'(\s{2,})', sre.UNICODE)
sre_colon_not_followed_by_numeration_tag = sre.compile(r':(?!\s*<cds)', sre.UNICODE|sre.I)


## Patterns used for creating institutional preprint report-number
## recognition patterns (used by function "institute_num_pattern_to_regex"):
   ## Recognise any character that isn't a->z, A->Z, 0->9, /, [, ], ' ', '"':
sre_report_num_chars_to_escape = sre.compile(r'([^\]A-Za-z0-9\/\[ "])', sre.UNICODE)
   ## Replace "hello" with hello:
sre_extract_quoted_text = (sre.compile(r'\"([^"]+)\"', sre.UNICODE), r'\g<1>',)
   ## Replace / [abcd ]/ with /( [abcd])?/ :
sre_extract_char_class = (sre.compile(r' \[([^\]]+) \]', sre.UNICODE), r'( [\g<1>])?')
###


## URL recognition:
## Stand-alone URL (e.g. http //cdsware.cern.ch/ )
sre_raw_url = \
 sre.compile(r'((https?|s?ftp) \/\/([\w\d\_\.\-])+(\/([\w\d\_\.\-])+)*(\/([\w\d\_\-]+\.\w{1,6})?)?)', \
             sre.UNICODE|sre.I)
## HTML marked-up URL (e.g. <a href="http //cdsware.cern.ch/">CERN Document Server Software Consortium</a> )
sre_html_tagged_url = \
 sre.compile(r'(\<a\s+href\s*=\s*([\'"])?(((https?|s?ftp) \/\/)?([\w\d\_\.\-])+(\/([\w\d\_\.\-])+)*(\/([\w\d\_\-]+\.\w{1,6})?)?)([\'"])?\>([^\<]+)\<\/a\>)', \
             sre.UNICODE|sre.I)


## Numeration recognition pattern - used to identify numeration associated with a title when
## marking the title up into MARC XML:
sre_recognised_numeration_for_title = \
     sre.compile(r'^(\s*.?,?\s*:\s\<cds\.VOL\>(\d+)\<\/cds\.VOL> \<cds\.YR\>\(([1-2]\d\d\d)\)\<\/cds\.YR\> \<cds\.PG\>([RL]?\d+[c]?)\<\/cds\.PG\>)', sre.UNICODE)

sre_title_followed_by_series_markup_tags = \
     sre.compile(r'(\<cds.TITLE\>([^\<]+)\<\/cds.TITLE\>\s*.?\s*\<cds\.SER\>([A-H]|(I{1,3}V?|VI{0,3}))\<\/cds\.SER\>)', sre.UNICODE)

sre_punctuation = sre.compile(r'[\.\,\;\'\(\)\-]', sre.UNICODE)

#sre_tagged_citation = sre.compile(r'\<cds\.(TITLE|VOL|YR|PG|REPORTNUMBER|SER|URL).*?\>', sre.UNICODE)
sre_tagged_citation = sre.compile(r'\<cds\.(TITLE|VOL|YR|PG|REPORTNUMBER|SER|URL)( description=\"[^\"]*\")?\>', sre.UNICODE)

## is there pre-recognised numeration-tagging within a few characters of the start if this part of the line?
sre_tagged_numeration_near_line_start = sre.compile(r'^.{0,4}?<CDS (VOL|SER)>', sre.UNICODE)


sre_ibid = sre.compile(r'(-|\b)(IBID\.?( ([A-H]|(I{1,3}V?|VI{0,3})|[1-3]))?)\s?:', sre.UNICODE)
sre_matched_ibid = sre.compile(r'IBID\.?\s?([A-H]|(I{1,3}V?|VI{0,3})|[1-3])?', sre.UNICODE)

sre_title_series = sre.compile(r'\, +([A-H]|(I{1,3}V?|VI{0,3}))$', sre.UNICODE)

## After having processed a line for titles, it may be possible to find more numeration with the
## aid of the recognised titles. The following 2 patterns are used for this:

sre_correct_numeration_2nd_try_ptn1 = \
    (sre.compile(r'\(?([12]\d{3})([A-Za-z]?)\)?,? *(<cds\.TITLE>(\.|[^<])*<\/cds\.TITLE>),? *(\b[Vv]o?l?\.?)?\s?(\d+)(,\s*|\s+)[pP]?[p]?\.?\s?([RL]?\d+[c]?)\-?[RL]?\d{0,6}[c]?', sre.UNICODE), \
                                        '\\g<1>\\g<2>, \\g<3> \\g<6> (\\g<1>) \\g<8>'
    )
sre_correct_numeration_2nd_try_ptn2 = \
    (sre.compile(r'\(?([12]\d{3})([A-Za-z]?)\)?,? *(<cds\.TITLE>(\.|[^<])*<\/cds\.TITLE>),? *(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)\-?[RL]?\d{0,6}[c]?', sre.UNICODE), \
                                        '\\g<1>\\g<2>, \\g<3> \\g<6> \\g<7> \\g<8> (\\g<1>)'
    )

## precompile some regexps used to search for and standardize numeration patterns in a line for the first time:

## Delete the colon and expressions such as Serie, vol, V. inside the pattern <serie : volume>
## E.g.: Replace the string """Series A, Vol 4""" with """A 4"""
sre_strip_series_and_volume_labels = (sre.compile(r'(Serie\s|\bS\.?\s)?([A-H])\s?[:,]\s?(\b[Vv]o?l?\.?)?\s?(\d+)', sre.UNICODE),
                      unicode('\\g<2> \\g<4>'))


## This pattern is not compiled, but rather included in the other numeration paterns:
_sre_non_compiled_pattern_nucphysb_subtitle = r'(?:[\(\[]\s*?(?:[Ff][Ss]|[Pp][Mm])\s*?\d{0,4}\s*?[\)\]])?'

## the 4 main numeration patterns:


## Pattern 0 (was pattern 3): <x, vol, page, year>
sre_numeration_vol_nucphys_page_yr = (sre.compile(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?[,:\s]\s?' +\
                                                   _sre_non_compiled_pattern_nucphysb_subtitle +\
                                                   r'[,;:\s]?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(?([1-2]\d\d\d)\)?', \
                                                   sre.UNICODE), \
                                          unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<3></cds.PG> '))

sre_numeration_nucphys_vol_page_yr = (sre.compile(r'\b' + _sre_non_compiled_pattern_nucphysb_subtitle +\
     r'[,;:\s]?([Vv]o?l?\.?)?\s?(\d+)\s?[,:\s]\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(?([1-2]\d\d\d)\)?', sre.UNICODE),\
                      unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<3></cds.PG> '))

## Pattern 1: <x, vol, year, page>
## <v, [FS]?, y, p>
sre_numeration_vol_nucphys_yr_page = (sre.compile(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?' +\
                                 _sre_non_compiled_pattern_nucphysb_subtitle +\
                                 r'[,;:\s]?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?', sre.UNICODE),\
                      unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<3>)</cds.YR> <cds.PG>\\g<4></cds.PG> '))
## <[FS]?, v, y, p>
sre_numeration_nucphys_vol_yr_page = (sre.compile(r'\b' + _sre_non_compiled_pattern_nucphysb_subtitle +\
     r'[,;:\s]?([Vv]o?l?\.?)?\s?(\d+)\s?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?', re.UNICODE),\
                      unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<3>)</cds.YR> <cds.PG>\\g<4></cds.PG> '))


## Pattern 2: <vol, serie, year, page>
## <v, s, [FS]?, y, p>
sre_numeration_vol_series_nucphys_yr_page = (sre.compile(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])\s?' + _sre_non_compiled_pattern_nucphysb_subtitle +\
                                 r'[,;:\s]?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?', re.UNICODE),\
                      unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<5></cds.PG> '))
## <v, [FS]?, s, y, p
sre_numeration_vol_nucphys_series_yr_page = (sre.compile(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?' + _sre_non_compiled_pattern_nucphysb_subtitle +\
                      r'[,;:\s]?([A-H])\s?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?', re.UNICODE),\
                      unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<5></cds.PG> '))



## Pattern 4: <vol, serie, page, year>
## <v, s, [FS]?, p, y>
sre_numeration_vol_series_nucphys_page_yr = (sre.compile(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])[,:\s]\s?' + _sre_non_compiled_pattern_nucphysb_subtitle +\
                      r'[,;:\s]?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(([1-2]\d\d\d)\)', re.UNICODE),\
                      unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<5>)</cds.YR> <cds.PG>\\g<4></cds.PG> '))

## <v, [FS]?, s, p, y>
sre_numeration_vol_nucphys_series_page_yr = (sre.compile(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?' + _sre_non_compiled_pattern_nucphysb_subtitle +\
                      r'[,;:\s]?([A-H])[,:\s]\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(([1-2]\d\d\d)\)', re.UNICODE),\
                      unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<5>)</cds.YR> <cds.PG>\\g<4></cds.PG> '))


## a list of patterns used to try to repair broken URLs within reference lines:
sre_list_url_repair_patterns = get_url_repair_patterns()

## a dictionary of undesirable characters and their replacements:
undesirable_char_replacements = get_bad_char_replacements()




## General initiation tasks:

def get_recids_and_filepaths(args):
    """from a list of arguments in the form "recid:filepath" (["1:filepath", "2:filepath", [...]])
       split each string into 2 parts: the record ID and the filepath.
       @param args: a list of strings
       @return: a list of tuples: [(recid, filepath)]
    """
    jobs = []
    for x in args:
        items = x.split(":")
        if len(items) != 2:
            sys.stderr.write(u"W: Recid:filepath argument invalid. Skipping.\n")
            continue
        jobs.append((items[0], items[1]))
    return jobs

## components relating to the standardisation and recognition of citations in reference lines:

def repair_broken_urls(line):
    """Attempt to repair broken URLs in a line of text. (E.g.: remove spaces from the middle of
       a URL; something like that.)
       @param line: (string) the line in which to check for broken URLs.
       @return: (string) the line after any broken URLs have (hopefully!) been repaired.
    """
    def _chop_spaces_in_url_match(m):
        return m.group(1).replace(" ", "")
    for ptn in sre_list_url_repair_patterns:
        line = ptn.sub(_chop_spaces_in_url_match, line)
    return line

def replace_undesirable_characters(line):
    """Replace certain bad characters in a text line.
       @param line: (string) the text line in which bad characters are to be replaced.
       @return: (string) the text line after the bad characters have been replaced.
    """
    bad_chars = undesirable_char_replacements.keys()
    for bad_char in bad_chars:
        try:
            line = line.replace(bad_char, undesirable_char_replacements[bad_char])
        except UnicodeDecodeError:
            pass
    return line

def remove_and_record_multiple_spaces_in_line(line):
    """For a given string, locate all ocurrences of multiple spaces together in the line, record the
       number of spaces found at each position, and replace them with a single space.
       @param line: (string) the text line to be processed for multiple spaces.
       @return: (tuple) countaining a dictionary and a string. The dictionary contains information about
        the number of spaces removed at given positions in the line. For example, if 3 spaces were removed
        from the line at index '22', the dictionary would be set as follows: { 22 : 3 }
        The string that is also returned in this tuple is the line after multiple-space ocurrences have
        replaced with single spaces.
    """
    removed_spaces = {}
    ## get a collection of match objects for all instances of multiple-spaces found in the line:
    multispace_matches = sre_group_captured_multiple_space.finditer(line)
    ## record the number of spaces found at each match position:
    for multispace in multispace_matches:
        removed_spaces[multispace.start()] = (multispace.end() - multispace.start() - 1)
    ## now remove the multiple-spaces from the line, replacing with a single space at each position:
    line = sre_group_captured_multiple_space.sub(u' ', line)
    return (removed_spaces, line)

def wash_line(line):
    """Wash a text line of certain punctuation errors, replacing them with more correct
       alternatives.  E.g.: the string 'Yes , I like python.' will be transformed into
       'Yes, I like python.'
       @param line: (string) the line to be washed.
       @return: (string) the washed line.
    """
    line = sre_space_comma.sub(',', line)
    line = sre_space_semicolon.sub(';', line)
    line = sre_space_period.sub('.', line)
    line = sre_colon_space_colon.sub(':', line)
    line = sre_comma_space_colon.sub(':', line)
    line = sre_space_closing_square_bracket.sub(']', line)
    line = sre_opening_square_bracket_space.sub('[', line)
    line = sre_hyphens.sub('-', line)
    line = sre_colon_not_followed_by_numeration_tag.sub(' ', line)
    line = sre_multiple_space.sub(' ', line)
    return line

def _order_institute_preprint_reference_numeration_patterns_by_length(numeration_patterns):
    """Given a list of user-defined patterns for recognising the numeration styles of an institute's
       preprint references, for each pattern, strip out character classes and record the length of the pattern.
       Then add the length and the original pattern (in a tuple) into a new list for these patterns and return
       this list.
       @param numeration_patterns: (list) of strings, whereby each string is a numeration pattern.
       @return: (list) of tuples, where each tuple contains a pattern and its length.
    """
    def _compfunc_bylen(a, b):
        if a[0] < b[0]:
            return 1
        elif a[0] == b[0]:
            return 0
        else:
            return -1
    pattern_list = []
    for pattern in numeration_patterns:
        base_pattern = sre_regexp_character_class.sub('1', pattern)
        pattern_list.append((len(base_pattern), pattern))
    pattern_list.sort(_compfunc_bylen)
    return pattern_list

def create_institute_numeration_group_regexp_pattern(patterns):
    """Using a list of regexp patterns for recognising numeration patterns for institute preprint references,
       ordered by length - longest to shortest - create a grouped 'OR' or of these patterns, ready to be used
       in a bigger regexp.
       @param patterns: (list) of strings. All of the numeration regexp patterns for recognising an institute's preprint
        reference styles.
       @return: (string) a grouped 'OR' regexp pattern of the numeration patterns. E.g.:
           (?P<num>[12]\d{3} \d\d\d|\d\d \d\d\d|[A-Za-z] \d\d\d)
    """
    grouped_numeration_pattern = u""
    if len(patterns) > 0:
        grouped_numeration_pattern = u"(?P<numn>"
        for pattern in patterns:
            grouped_numeration_pattern += institute_num_pattern_to_regex(pattern[1]) + u"|"
        grouped_numeration_pattern = grouped_numeration_pattern[0:len(grouped_numeration_pattern) - 1]
        grouped_numeration_pattern += u")"
    return grouped_numeration_pattern

def institute_num_pattern_to_regex(pattern):
    """Given a numeration pattern from the institutes preprint report numbers KB,
       convert it to turn it into a regexp string for recognising such patterns in
       a reference line.
       Change:
           \     -> \\
           9     -> \d
           a     -> [A-Za-z]
           mm    -> (0[1-9]|1[0-2])
           yy    -> \d{2}
           yyyy  -> [12]\d{3}
           /     -> \/
           s     -> \s*?
       @param pattern: (string) a user-defined preprint reference numeration pattern.
       @return: (string) the regexp for recognising the pattern.
    """
    simple_replacements = [ ('9',    r'\d'),
                            ('a',    r'[A-Za-z]'),
                            ('mm',   r'(0[1-9]|1[0-2])'),
                            ('yyyy', r'[12]\d{3}'),
                            ('yy',   r'\d\d'),
                            ('s',    r'\s*?'),
                            (r'/',   r'\/')
                          ]
    ## first, escape certain characters that could be sensitive to a regexp:
    pattern = sre_report_num_chars_to_escape.sub(r'\\\g<1>', pattern)

    ## now loop through and carry out the simple replacements:
    for repl in simple_replacements:
        pattern = pattern.replace(repl[0], repl[1])

    ## now replace a couple of regexp-like paterns:
        ## quoted string with non-quoted version ("hello" with hello);
        ## Replace / [abcd ]/ with /( [abcd])?/ :
    pattern = sre_extract_quoted_text[0].sub(sre_extract_quoted_text[1], pattern)
    pattern = sre_extract_char_class[0].sub(sre_extract_char_class[1], pattern)

    ## the pattern has been transformed
    return pattern

def build_institutes_preprints_numeration_knowledge_base(fpath):
    """Given the path to a knowledge base file containing the details of institutes and the patterns
       that their preprint report numberring schemes take, create a dictionary of regexp search patterns
       to recognise these preprint references in reference lines, and a dictionary of replacements for
       non-standard preprint categories in these references.

       The knowledge base file should consist only of lines that take one of the following 3 formats:

         #####Institute Name####

       (the name of the institute to which the preprint reference patterns belong, e.g. '#####LANL#####',
        surrounded by 5 # on either side.)

         <pattern>

       (numeration patterns for an institute's preprints, surrounded by < and >.)

         seek-term       ---   replace-term
       (i.e. a seek phrase on the left hand side, a replace phrase on the right hand side, with
       the two phrases being separated by 3 hyphens.) E.g.:
         ASTRO PH        ---astro-ph
         
       The left-hand side term is a non-standard version of the preprint reference category; the right-hand
       side term is the standard version.

       If the KB file cannot be read from, or an unexpected line is encountered in the KB, an error
       message is output to standard error and execution is halted with an error-code 0.

       @param fpath: (string) the path to the knowledge base file.
       @return: (tuple) containing 2 dictionaries. The first contains regexp search patterns used to identify
        preprint references in a line. This dictionary is keyed by a tuple containing the line number of the
        pattern in the KB and the non-standard category string.  E.g.: (3, 'ASTRO PH').
        The second dictionary contains the standardised category string, and is keyed by the non-standard
        category string. E.g.: 'astro-ph'.
    """
    def _add_institute_preprint_patterns(preprint_classifications, preprint_numeration_ptns,\
                                         preprint_reference_search_regexp_patterns, \
                                         standardised_preprint_reference_categories, kb_line_num):
        """For a list of preprint category strings and preprint numeration patterns for a given institute,
           create the regexp patterns for each of the preprint types.  Add the regexp patterns to the dictionary
           of search patterns (preprint_reference_search_regexp_patterns), keyed by the line number of the institute
           in the KB, and the preprint category search string.  Also add the standardised preprint category string
           to another dictionary, keyed by the line number of its position in the KB and its non-standardised
           version.
           @param preprint_classifications: (list) of tuples whereby each tuple contains a preprint category search
            string and the line number of the name of institute to which it belongs in the KB. E.g.: (45, 'ASTRO PH').
           @param preprint_numeration_ptns: (list) of preprint reference numeration search patterns (strings)
           @param preprint_reference_search_regexp_patterns: (dictionary) of regexp patterns used to search in
            document lines.
           @param standardised_preprint_reference_categories: (dictionary) containing the standardised strings for
            preprint reference categories. (E.g. 'astro-ph'.)
           @param kb_line_num: (integer) - the line number int the KB at which a given institute name was found.
           @return: None
        """
        if len(preprint_classifications) > 0 and \
           len(preprint_numeration_ptns) > 0:
            ## the previous institute had both numeration styles and categories for preprint references.
            ## build regexps and add them for this institute:
            ## First, order the numeration styles by line-length, and build a grouped regexp for recognising numeration:
            ordered_patterns = _order_institute_preprint_reference_numeration_patterns_by_length(preprint_numeration_ptns)
            ## create a grouped regexp for numeration part of preprint reference:
            numeration_regexp = create_institute_numeration_group_regexp_pattern(ordered_patterns)

            ## for each "classification" part of preprint references, create a complete regex:
            ## will be in the style "(categ)-(numatn1|numatn2|numatn3|...)"
            for classification in preprint_classifications:
                search_pattern_str = r'\b((?P<categ>' + classification[0] + u')' + numeration_regexp + r')'
                sre_search_pattern = sre.compile(search_pattern_str, sre.UNICODE)
                preprint_reference_search_regexp_patterns[(kb_line_num, classification[0])]  = sre_search_pattern
                standardised_preprint_reference_categories[(kb_line_num, classification[0])] = classification[1]

    preprint_reference_search_regexp_patterns  = {}  ## a dictionary of paterns used to recognise categories of
                                                     ## preprints as used by various institutes
    standardised_preprint_reference_categories = {}  ## dictionary of standardised category strings for preprint cats
    current_institute_preprint_classifications = []  ## list of tuples containing preprint categories in their raw and
                                                     ## standardised forms, as read from the KB
    current_institute_numerations = []               ## list of preprint numeration patterns, as read from the KB
    sre_institute_name          = sre.compile(r'^\#{5}\s*(.+)\s*\#{5}$', sre.UNICODE)  ## pattern to recognise an
                                                                                       ## institute name line in KB
    sre_preprint_classification = sre.compile(r'^\s*(\w.*?)\s*---\s*(\w.*?)\s*$', sre.UNICODE) ## pattern to recognise
                                                                                               ## an institute preprint
                                                                                               ## categ line in KB
    sre_numeration_pattern      = sre.compile(r'^\<(.+)\>$', sre.UNICODE)         ## pattern to recognise a preprint
                                                                                  ## numeration-style line in KB
    kb_line_num = 0    ## when making the dictionary of patterns, which is keyed by the category search string,
                       ## this counter will ensure that patterns in the dictionary are not overwritten if 2
                       ## institutes have the same category styles.

    try:
        fh = open(fpath, "r")
        for rawline in fh:
            rawline = rawline.decode("utf-8")
            kb_line_num += 1
            m_institute_name = sre_institute_name.search(rawline)
            if m_institute_name is not None:
                ## This KB line is the name of an institute
                institute_name = m_institute_name.group(1)
                ## append the last institute's pattern list to the list of institutes:
                _add_institute_preprint_patterns(current_institute_preprint_classifications,\
                                                 current_institute_numerations,\
                                                 preprint_reference_search_regexp_patterns, \
                                                 standardised_preprint_reference_categories, kb_line_num)

                ## Now start a new dictionary to contain the search patterns for this institute:
                current_institute_preprint_classifications = []
                current_institute_numerations = []
                ## move on to the next line
                continue

            m_preprint_classification = sre_preprint_classification.search(rawline)
            if m_preprint_classification is not None:
                ## This KB line contains a preprint classification for the current institute
                try:
                    current_institute_preprint_classifications.append((m_preprint_classification.group(1), \
                                                                      m_preprint_classification.group(2)))
                except (AttributeError, NameError):
                    ## didn't match this line correctly - skip it
                    pass
                ## move on to the next line
                continue

            m_numeration_pattern = sre_numeration_pattern.search(rawline)
            if m_numeration_pattern is not None:
                ## This KB line contains a preprint item numeration pattern for the current institute
                try:
                    current_institute_numerations.append(m_numeration_pattern.group(1))
                except (AttributeError, NameError):
                    ## didn't match the numeration pattern correctly - skip it
                    pass
                continue

        _add_institute_preprint_patterns(current_institute_preprint_classifications,\
                                         current_institute_numerations,\
                                         preprint_reference_search_regexp_patterns, \
                                         standardised_preprint_reference_categories, kb_line_num)

    except IOError:
        ## problem opening KB for reading, or problem while reading from it:
        emsg = """Error: Could not build knowledge base containing institute preprint referencing"""\
               """ patterns - failed to read from KB %(kb)s.\n""" \
               % { 'kb' : fpath }
        sys.stderr.write(emsg)
        sys.stderr.flush()
        sys.exit(0)

    ## return the preprint reference patterns and the replacement strings for non-standard categ-strings:
    return (preprint_reference_search_regexp_patterns, standardised_preprint_reference_categories)

def build_titles_knowledge_base(fpath):
    """Given the path to a knowledge base file, read in the contents of that file into a dictionary
       of search->replace word phrases. The search phrases are compiled into a regex pattern object.
       The knowledge base file should consist only of lines that take the following format:
         seek-term       ---   replace-term
       (i.e. a seek phrase on the left hand side, a replace phrase on the right hand side, with
       the two phrases being separated by 3 hyphens.) E.g.:
         ASTRONOMY AND ASTROPHYSICS              ---Astron. Astrophys.

       The left-hand side term is a non-standard version of the title, whereas the right-hand side
       term is the standard version.
       If the KB file cannot be read from, or an unexpected line is encountered in the KB, an error
       message is output to standard error and execution is halted with an error-code 0.

       @param fpath: (string) the path to the knowledge base file.
       @return: (tuple) containing a list and a dictionary. The list contains compiled regex patterns
        used as search terms and will be used to force searching order to match that of the knowledge
        base.
        The dictionary contains the search->replace terms.  The keys of the dictionary are the compiled
        regex word phrases used for searching in the reference lines; The values in the dictionary are
        the replace terms for matches.
    """
    ## Initialise vars:
    ## dictionary of search and replace phrases from KB:
    kb = {}
    standardised_titles = {}
    seek_phrases = []
    
    ## Pattern to recognise a correct knowledge base line:
    p_kb_line = sre.compile('^\s*(?P<seek>\w.*?)\s*---\s*(?P<repl>\w.*?)\s*$', sre.UNICODE)

    try:
        fh = open(fpath, "r")
        for rawline in fh:
            ## Test line to ensure that it is a correctly formatted knowledge base line:
            m_kb_line = p_kb_line.search(rawline.decode("utf-8").rstrip("\n"))

            if m_kb_line is not None:
                ## good KB line
                seek_phrase = m_kb_line.group('seek')
                if len(seek_phrase) > 1:
                    ## add the phrase from the KB if the 'seek' phrase is longer than 1 character:
                    ## compile the seek phrase into a pattern:
                    seek_ptn = sre.compile(r'(?<!\/)\b(' + sre.escape(seek_phrase) + r')[^A-Z0-9]', sre.UNICODE)
                    if not kb.has_key(seek_phrase):
                        kb[seek_phrase] = seek_ptn
                        standardised_titles[seek_phrase] = m_kb_line.group('repl')
                        seek_phrases.append(seek_phrase)
            else:
                ## KB line was not correctly formatted - die with error
                emsg = """Error: Could not build list of journal titles - KB %(kb)s has errors.\n""" \
                       % { 'kb' : fpath }
                sys.stderr.write(emsg)
                sys.exit(0)
        fh.close()
    except IOError:
        ## problem opening KB for reading, or problem while reading from it:
        emsg = """Error: Could not build list of journal titles - failed to read from KB %(kb)s.\n""" \
               % { 'kb' : fpath }
        sys.stderr.write(emsg)
        sys.stderr.flush()
        sys.exit(0)

    ## return the raw knowledge base:
    return (kb, standardised_titles, seek_phrases)

## NICK - 2007/01/11
def standardize_and_markup_numeration_of_citations_in_line(line):
    """Given a reference line, attepmt to locate instances of citation 'numeration' in the line.
       Upon finding some numeration, re-arrange it into a standard order, and mark it up with tags.
       Will process numeration in the following order:
            Delete the colon and expressions such as Serie, vol, V. inside the pattern <serie : volume>
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
       @return: (string) the reference line after numeration has been checked and possibly
        recognized/marked-up.
    """
    line = sre_strip_series_and_volume_labels[0].sub(sre_strip_series_and_volume_labels[1], line)
    line = sre_numeration_vol_nucphys_page_yr[0].sub(sre_numeration_vol_nucphys_page_yr[1], line)
    line = sre_numeration_nucphys_vol_page_yr[0].sub(sre_numeration_nucphys_vol_page_yr[1], line)
    line = sre_numeration_vol_nucphys_yr_page[0].sub(sre_numeration_vol_nucphys_yr_page[1], line)
    line = sre_numeration_nucphys_vol_yr_page[0].sub(sre_numeration_nucphys_vol_yr_page[1], line)
    line = sre_numeration_vol_series_nucphys_yr_page[0].sub(sre_numeration_vol_series_nucphys_yr_page[1], line)
    line = sre_numeration_vol_nucphys_series_yr_page[0].sub(sre_numeration_vol_nucphys_series_yr_page[1], line)
    line = sre_numeration_vol_series_nucphys_page_yr[0].sub(sre_numeration_vol_series_nucphys_page_yr[1], line)
    line = sre_numeration_vol_nucphys_series_page_yr[0].sub(sre_numeration_vol_nucphys_series_page_yr[1], line)
    return line

def identify_preprint_report_numbers(line,
                                     preprint_repnum_search_kb,
                                     preprint_repnum_standardised_categs):
    """Attempt to identify all preprint report numbers in a reference line.
       Report numbers will be identified, their information (location in line, length in line, and
       standardised replacement version) will be record, and they will be replaced in the working-
       line by underscores.
       @param line: (string) - the working reference line.
       @param preprint_repnum_search_kb: (dictionary) - contains the regexp patterns used to identify preprint
        report numbers.
       @param preprint_repnum_standardised_categs: (dictionary) - contains the standardised 'category' of a given
        preprint report number.
       @return: (tuple) - 3 elements:
           * a dictionary containing the lengths in the line of the matched preprint report numbers, keyed by the
             index at which each match was found in the line.
           * a dictionary containing the replacement strings (standardised versions) of preprint report numbers
             that were matched in the line.
           * a string, that is the new version of the working reference line, in which any matched preprint report
             numbers have been replaced by underscores.
        Returned tuple is therefore in the following order:
            (matched-reportnum-lengths, matched-reportnum-replacements, working-line)
    """
    def _by_len(a, b):
        """Comparison function used to sort a list by the length of the strings in
           each element of the list.
        """
        if len(a[1]) < len(b[1]):
            return 1
        elif len(a[1]) == len(b[1]):
            return 0
        else:
            return -1
    repnum_matches_matchlen = {}  ## info about lengths of report numbers matched at given locations in line
    repnum_matches_repl_str = {}  ## standardised report numbers matched at given locations in line

    preprint_repnum_categs = preprint_repnum_standardised_categs.keys()
    preprint_repnum_categs.sort(_by_len)

    ## try to match preprint report numbers in the line:
    for categ in preprint_repnum_categs:
        ## search for all instances of the current report numbering style in the line:
        repnum_matches_iter = preprint_repnum_search_kb[categ].finditer(line)
        ## for each matched report number of this style:
        for repnum_match in repnum_matches_iter:
            ## Get the matched text for the numeration part of the preprint report number:
            numeration_match = repnum_match.group('numn')
            ## clean/standardise this numeration text:
            numeration_match = numeration_match.replace(" ", "-")
            numeration_match = sre_multiple_hyphens.sub("-", numeration_match)
            numeration_match = numeration_match.replace("/-", "/")
            numeration_match = numeration_match.replace("-/", "/")
            numeration_match = numeration_match.replace("-/-", "/")
            ## replace the found preprint report number in the string with underscores:
            line = line[0:repnum_match.start()] + "_"*len(repnum_match.group(0)) + line[repnum_match.end():]
            ## record the information about the matched preprint report number:
            ## total length in the line of the matched preprint report number:
            repnum_matches_matchlen[repnum_match.start()] = len(repnum_match.group(0))
            ## standardised replacement for the matched preprint report number:
            repnum_matches_repl_str[repnum_match.start()] = preprint_repnum_standardised_categs[categ] + numeration_match

    ## return recorded information about matched report numbers, along with the newly changed working line:
    return (repnum_matches_matchlen, repnum_matches_repl_str, line)

def identify_and_tag_URLs(line):
    """Given a reference line, identify URLs in the line and tag them between <cds.URL> tags.
       URLs are identified in 2 forms:
        + Raw: http //cdsware.cern.ch/
        + HTML marked-up: <a href="http //cdsware.cern.ch/">CERN Document Server Software Consortium</a>
       These URLs are considered to have 2 components: The URL itself (url string); and the URL
       description. The description is effectively the text used for the created Hyperlink when the
       URL is marked-up in HTML. When an HTML marked-up URL has been recognised, the text between the
       anchor tags is therefore taken as the URL description. In the case of a raw URL recognition,
       however, the URL itself will also be used as the URL description. For example, in the
       following reference line:
        [1] See <a href="http //cdsware.cern.ch/">CERN Document Server Software Consortium</a>.
       ...the URL string will be "http //cdsware.cern.ch/" and the URL description will be
       "CERN Document Server Software Consortium". The line returned will therefore be:
        [1] See <cds.URL description="http //cdsware.cern.ch/">CERN Document Server Software
        Consortium</cds.URL>.
       In the following line, however:
        [1] See http //cdsware.cern.ch/ for more details.
       ...the URL string will be "http //cdsware.cern.ch/" and the URL description will also be
       "http //cdsware.cern.ch/". The line returned will therefore be:
        [1] See <cds.URL description="http //cdsware.cern.ch/">http //cdsware.cern.ch/</cds.URL>
         for more details.
       Note that URLs recognised may not have the colon separator in the protocol. This is because
       in the step prior to the calling of this function, colons will have been removed from the
       line so that numeration (as found in journal article citations) could be identified and
       tagged.
       @param line: (string) the reference line in which to search for URLs.
       @return: (string) the reference line in which any recognised URLs have been tagged.
    """
    ## Dictionaries to record details of matched URLs:
    found_url_full_matchlen = {}
    found_url_urlstring     = {}
    found_url_urldescr      = {}

    ## Attempt to identify and tag all HTML-MARKED-UP URLs in the line:
    m_tagged_url_iter = sre_html_tagged_url.finditer(line)
    for m_tagged_url in m_tagged_url_iter:
        startposn = m_tagged_url.start()       ## start position of matched URL
        endposn   = m_tagged_url.end()         ## end position of matched URL
        matchlen  = len(m_tagged_url.group(0)) ## total length of URL match
        found_url_full_matchlen[startposn] = matchlen
        found_url_urlstring[startposn]     = m_tagged_url.group(3)
        found_url_urldescr[startposn]      = m_tagged_url.group(12)
        ## temporarily replace the URL match with underscores so that it won't be re-found
        line = line[0:startposn] + u"_"*matchlen + line[endposn:]

    ## Attempt to identify and tag all RAW (i.e. not HTML-marked-up) URLs in the line:
    m_raw_url_iter = sre_raw_url.finditer(line)
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
        ## temporarily replace the URL match with underscores so that it won't be re-found
        line = line[0:startposn] + u"_"*matchlen + line[endposn:]

    ## Now that all URLs have been identified, insert them back into the line, tagged:
    found_url_positions = found_url_urlstring.keys()
    found_url_positions.sort()
    extras_from_previous_url = 0
    for url_position in found_url_positions:
        line = line[0:url_position + extras_from_previous_url] \
               + """<cds.URL description="%(url-description)s">%(url)s</cds.URL>""" \
               % { 'url-description' : found_url_urldescr[url_position],
                   'url'             : found_url_urlstring[url_position],
                 } \
               + line[url_position+found_url_full_matchlen[url_position]+extras_from_previous_url:]
        extras_from_previous_url += len("""<cds.URL description=""></cds.URL>""") \
                                    + len(found_url_urldescr[url_position])

    ## return the line containing the tagged URLs:
    return line

def identify_periodical_titles(line, periodical_title_search_kb, periodical_title_search_keys):
    """Attempt to identify all periodical titles in a reference line.
       Titles will be identified, their information (location in line, length in line, and non-
       standardised version) will be record, and they will be replaced in the working line by
       underscores.
       @param line: (string) - the working reference line.
       @param periodical_title_search_kb: (dictionary) - contains the regexp patterns used to
        search for a non-standard TITLE in the working reference line. Keyed by the TITLE string
        itself.
       @param periodical_title_search_keys: (list) - contains the non-standard periodical TITLEs
        to be searched for in the line. This list of titles has already been ordered and is used
        to force the order of searching.
       @return: (tuple) containing 3 elements:
                        + (dictionary) - the lengths of all titles matched at each given index
                                         within the line.
                        + (dictionary) - the text actually matched for each title at each given
                                         index within the line.
                        + (string)     - the working line, with the titles removed from it and
                                         replaced by underscores.
    """
    title_matches_matchlen  = {}  ## info about lengths of periodical titles matched at given locations in the line
    title_matches_matchtext = {}  ## the text matched at the given line location (i.e. the title itself)

    ## Split the line into segments based on "</CDS PG>" ocurrences. Since the name of a periodical should
    ## come before the numeration, "</CDS PG>" should mark the end of the recognised numeration and should be the
    ## splitting point.
    ## By splitting the line into segments that each contain only one instance of numeration, it can be said that at most,
    ## there can only be one "meaningful" (one that can be linked to the numeration information) periodical in that segment.
    ## This means that after identifying a title that is next to the numeration in the line, there should be no others in
    ## the line and it should be possible to stop searching in the line for other titles.
    line_segments = map(lambda x: ((x.find("<CDS PG>") != -1) and (x + "</CDS PG>") or (x)), line.split("</CDS PG>"))
    if line_segments[len(line_segments) - 1] == "":
        ## if the last element in the list of line segments is empty, drop it:
        line_segments = line_segments[0:len(line_segments) - 1]

    num_segments = len(line_segments)
    len_previous_segments = 0  ## the combined length of previous line segments. Used to determine correct position
                               ## in the line of a matched title, when dealing with line segments.

    ## Begin searching:
    ## for each line segment:
    for i in xrange(0, num_segments):
        if line_segments[i].find("<CDS ") == -1:
            ## no recognised numeration in this line - don't bother to search for titles as they will be useless:
            continue
        segment_match = 0  ## reset the segment-match flag as we start to check for titles in a new segment
        for title in periodical_title_search_keys:
            if segment_match != 0:
                ## a usable title match has been found in the current line-segment - discontinue testing for
                ## titles in this segment:
                break
            ## search for all instances of the current periodical title in the current line-segment:
            title_matches_iter = periodical_title_search_kb[title].finditer(line_segments[i])
            
            ## for each matched periodical title:
            for title_match in title_matches_iter:
                ## record the details of this title match:
                ## record the match length:
                title_matches_matchlen[len_previous_segments + title_match.start()] = len(title_match.group(0)) - 1
                ## record the matched non-standard version of the title:
                title_matches_matchtext[len_previous_segments + title_match.start()] = title
                ## replace the matched title text in the line it n * '-', where n is the length of the matched title:
                line_segments[i] = line_segments[i][0:title_match.start(1)] + "_"*len(title_match.group(1)) \
                                   + line_segments[i][title_match.end(1):]

                ## is this match next to the numeration tags? If yes, drop out of loop:
                if sre_tagged_numeration_near_line_start.match(line_segments[i][title_match.end():]) is not None:
                    ## Found a good match - drop out of this loop:
                    segment_match = 1
                    break
        ## add the length of this segment to the combined length of previous segments:
        len_previous_segments += len(line_segments[i])

    ## rebuild a complete line from the segments:
    processed_line = "".join(line_segments)

    ## return recorded information about matched periodical titles,
    ## along with the newly changed working line:
    return (title_matches_matchlen, title_matches_matchtext, processed_line)

def identify_ibids(line):
    """Find IBIDs within the line, record their position and length, and replace them with underscores.
       @param line: (string) the working reference line
       @return: (tuple) containing 2 dictionaries and a string:
         Dictionary 1: matched IBID lengths (Key: position of IBID in line; Value: length of matched IBID)
         Dictionary 2: matched IBID text: (Key: position of IBID in line; Value: matched IBID text)
         String:       working line with matched IBIDs removed
    """
    ibid_match_len = {}
    ibid_match_txt = {}
    ibid_matches_iter = sre_ibid.finditer(line)
    ## Record details of each matched ibid:
    for m_ibid in ibid_matches_iter:
        ibid_match_len[m_ibid.start()] = len(m_ibid.group(2))
        ibid_match_txt[m_ibid.start()] = m_ibid.group(2)
        ## Replace matched text in line with underscores:
        line = line[0:m_ibid.start(2)] + "_"*len(m_ibid.group(2)) + line[m_ibid.end(2):]
    return (ibid_match_len, ibid_match_txt, line)

def get_replacement_types(titles, reportnumbers):
    """Given the indices of the titles and reportnumbers that have been recognised within
       a reference line, create a dictionary keyed by the replacement position in the line,
       where the value for each key is a string describing the type of item replaced at that
       position in the line.
       The description strings are:
           'title'        - indicating that the replacement is a periodical title
           'reportnumber' - indicating that the replacement is a preprint report number.
       @param titles: (list) of locations in the string at which periodical titles were found.
       @param reportnumbers: (list) of locations in the string at which reportnumbers were found.
       @return: (dictionary) of replacement types at various locations within the string.
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
    """To build a processed (MARC XML) reference line in which the recognised citations such
       as standardised periodical TITLEs and REPORT-NUMBERs have been marked up, it is necessary
       to read from the reference line BEFORE all punctuation was stripped and it was made into
       upper-case. The indices of the cited items in this 'original line', however, will be
       different to those in the 'working-line', in which punctuation and multiple-spaces were
       stripped out. For example, the following reading-line:

        [26] E. Witten and S.-T. Yau, hep-th/9910245.
       ...becomes (after punctuation and multiple white-space stripping):
        [26] E WITTEN AND S T YAU HEP TH/9910245

       It can be seen that the report-number citation (hep-th/9910245) is at a different index
       in the two strings. When refextract searches for this citation, it uses the 2nd string
       (i.e. that which is capitalised and has no punctuation). When it builds the MARC XML
       representation of the reference line, however, it needs to read from the first string.
       It must therefore consider the whitespace, punctuation, etc that has been removed, in
       order to get the correct index for the cited item. This function accounts for the stripped
       characters before a given TITLE or REPORT-NUMBER index.
       @param spaces_keys: (list) - the indices at which spaces were removed from the
        reference line.
       @param removed_spaces: (dictionary) - keyed by the indices at which spaces were removed
        from the line, the values are the number of spaces actually removed from that position.
        So, for example, "3 spaces were removed from position 25 in the line."
       @param replacement_types: (dictionary) - at each 'replacement_index' in the line, the
        of replacement to make (title or reportnumber).
       @param len_reportnums: (dictionary) - the lengths of the REPORT-NUMBERs matched at the
        various indices in the line.
       @param len_titles: (dictionary) - the lengths of the various TITLEs matched at the
        various indices in the line.
       @param replacement_index: (integer) - the index in the working line of the identified
        TITLE or REPORT-NUMBER citation.
       @return: (tuple) containing 2 elements:
                        + the true replacement index of a replacement in the reading line;
                        + any extras to add into the replacement index;
    """
    extras = 0
    true_replacement_index = replacement_index
    spare_replacement_index = replacement_index

    for space in spaces_keys:
        if space < true_replacement_index:
            ## There were spaces stripped before the current replacement - add the number of spaces removed from
            ## this location to the current replacement index:
            true_replacement_index  += removed_spaces[space]
            spare_replacement_index += removed_spaces[space]
        elif (space >= spare_replacement_index) and (replacement_types[replacement_index] == u"title") \
             and (space < (spare_replacement_index + len_titles[replacement_index])):
            ## A periodical title is being replaced. Account for multi-spaces that may have been stripped
            ## from the title before its recognition:
            spare_replacement_index += removed_spaces[space]
            extras += removed_spaces[space]
        elif (space >= spare_replacement_index) and (replacement_types[replacement_index] == u"reportnumber") \
             and (space < (spare_replacement_index + len_reportnums[replacement_index])):
            ## An institutional preprint report-number is being replaced. Account for multi-spaces that may
            ## have been stripped from it before its recognition:
            spare_replacement_index += removed_spaces[space]
            extras += removed_spaces[space]

    ## return the new values for replacement indices with stripped whitespace accounted for:
    return (true_replacement_index, extras)


def create_marc_xml_reference_line(working_line,
                                   found_title_len,
                                   found_title_matchtext,
                                   pprint_repnum_len,
                                   pprint_repnum_matchtext,
                                   removed_spaces,
                                   standardised_titles):
    """After the phase of identifying and tagging citation instances in a reference line,
       this function is called to go through the line and the collected information about
       the recognised citations, and to transform the line into a string of MARC XML in
       which the recognised citations are grouped under various datafields and subfields,
       depending upon their type.
       @param working_line: (string) - the is the line before the punctuation was stripped.
        At this stage, it has not been capitalised, and neither TITLES nor REPORT NUMBERS
        have been stripped from it. However, any recognised numeration and/or URLs have
        been tagged with <cds.YYYY> tags.
        The working_line could, for example, look something like this:
         [1] CDS <cds.URL description="http //cdsware.cern.ch/">http //cdsware.cern.ch/</cds.URL>.
       @param found_title_len: (dictionary) - the lengths of the title citations that have
        been recognised in the line. Keyed by the index within the line of each match.
       @param found_title_matchtext: (dictionary) - The text that was found for each matched
        title citation in the line. Keyed by the index within the line of each match.
       @param pprint_repnum_len: (dictionary) - the lengths of the matched institutional
        preprint report number citations found within the line. Keyed by the index within
        the line of each match.
       @param pprint_repnum_matchtext: (dictionary) - The matched text for each matched
        institutional report number. Keyed by the index within the line of each match.
       @param removed_spaces: (dictionary) - The number of spaces removed from the various
        positions in the line. Keyed by the index of the position within the line at which
        the spaces were removed.
       @param standardised_titles: (dictionary) - The standardised journal titles, keyed
        by the non-standard version of those titles.
       @return: (tuple) of 5 components:
                  ( string  -> a MARC XML-ized reference line.
                    integer -> number of fields of miscellaneous text marked-up for the line.
                    integer -> number of title citations marked-up for the line.
                    integer -> number of institutional report-number citations marked-up
                     for the line.
                    integer -> number of URL citations marked-up for the record.
                  )

    """
    if len(found_title_len) + len(pprint_repnum_len) == 0:
        ## no TITLE or REPORT-NUMBER citations were found within this line, use the raw line:
        ## (This 'raw' line could still be tagged with recognised URLs or numeration.)
        tagged_line = working_line
    else:
        ## TITLE and/or REPORT-NUMBER citations were found in this line, build a new
        ## version of the working-line in which the standard versions of the REPORT-NUMBERs
        ## and TITLEs are tagged:
        startpos = 0          ## First cell of the reference line...
        previous_match = u""  ## previously matched TITLE within line (used for replacement
                              ## of IBIDs.
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

        tagged_line = u"" ## This is to be the new 'working-line'. It will contain the
                          ## tagged TITLEs and REPORT-NUMBERs, as well as any previously
                          ## tagged URLs and numeration components.
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
                                       len_title=found_title_len[replacement_index],
                                       matched_title=found_title_matchtext[replacement_index],
                                       previous_match=previous_match,
                                       startpos=startpos,
                                       true_replacement_index=true_replacement_index,
                                       extras=extras,
                                       standardised_titles=standardised_titles)
                tagged_line += rebuilt_chunk

            elif replacement_types[replacement_index] == u"reportnumber":
                ## Add a tagged institutional preprint REPORT-NUMBER into the line:
                (rebuilt_chunk, startpos) = \
                      add_tagged_report_number(reading_line=working_line,
                                               len_reportnum=pprint_repnum_len[replacement_index],
                                               reportnum=pprint_repnum_matchtext[replacement_index],
                                               startpos=startpos,
                                               true_replacement_index=true_replacement_index,
                                               extras=extras)
                tagged_line += rebuilt_chunk

        ## add the remainder of the original working-line into the rebuilt line:
        tagged_line += working_line[startpos:]
        ## use the recently marked-up title information to identify any numeration that escaped the last pass:
        tagged_line = _re_identify_numeration(tagged_line)
        ## remove any series tags that are next to title tags, putting series information into the title tags:
        tagged_line = move_tagged_series_into_tagged_title(tagged_line)
        tagged_line = wash_line(tagged_line)

    ## Now, from the tagged line, create a MARC XML string, marking up any recognised citations:
    (xml_line, count_misc, count_title, count_reportnum, count_url) = \
               convert_processed_reference_line_to_marc_xml(tagged_line)
    return (xml_line, count_misc, count_title, count_reportnum, count_url)

def _refextract_markup_title_as_marcxml(title, volume, year, page, misc_text=""):
    """Given a title, its numeration and some optional miscellaneous text, return a
       string containing the MARC XML version of this information. E.g. for the
       miscellaneous text "S. D. Hsu and M. Schwetz ", the title "Nucl. Phys., B",
       the volume "572", the year "2000" and the page number "211" return the following
       MARC XML string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="m">S. D. Hsu and M. Schwetz </subfield>
           <subfield code="s">Nucl. Phys., B 572 (2000) 211</subfield>
        </datafield>
       In the event that the miscellaneous text string is zero-length, there will be
       no $m subfield present in the returned XML.
       @param title: (string) - the cited title.
       @param volume: (string) - the volume of the cited title.
       @param year: (string) - the year of the cited title.
       @param page: (string) - the page of the cited title.
       @param misc_text: (string) - the miscellaneous text to be marked up.
       @return: (string) MARC XML representation of the cited title and its miscellaneous
        text.
    """
    ## First, determine whether there is need of a misc subfield:
    if len(misc_text) > 0:
        ## create a misc subfield to be included in the MARC XML:
        xml_misc_subfield = """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                    'misc-val'               : cgi.escape(misc_text, 1),
                  }
    else:
        ## the misc subfield is not needed
        xml_misc_subfield = ""
    ## Build the datafield for the report number segment of the reference line:
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">%(misc-subfield)s
      <subfield code="%(sf-code-ref-title)s">%(title)s %(volume)s (%(year)s) %(page)s</subfield>
   </datafield>
"""               % { 'df-tag-ref'             : CFG_REFEXTRACT_TAG_ID_REFERENCE,
                      'df-ind1-ref'            : CFG_REFEXTRACT_IND1_REFERENCE,
                      'df-ind2-ref'            : CFG_REFEXTRACT_IND2_REFERENCE,
                      'sf-code-ref-title'      : CFG_REFEXTRACT_SUBFIELD_TITLE,
                      'misc-subfield'          : xml_misc_subfield,
                      'title'                  : cgi.escape(title, 1),
                      'volume'                 : cgi.escape(volume, 1),
                      'year'                   : cgi.escape(year, 1),
                      'page'                   : cgi.escape(page, 1),
                    }
    return xml_line

def _refextract_markup_title_followed_by_report_number_as_marcxml(title, volume, year, page,
                                                                  report_number, misc_text=""):
    """Given a title (and its numeration), a report number, and some optional
       miscellaneous text, return a string containing the MARC XML version of this
       information. E.g. for the miscellaneous text "S. D. Hsu and M. Schwetz ",
       the report number "hep-th/1111111", the title "Nucl. Phys., B", the volume "572",
       the year "2000", and the page number "211", return the following
       MARC XML string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="m">S. D. Hsu and M. Schwetz </subfield>
           <subfield code="r">hep-th/1111111</subfield>
           <subfield code="s">Nucl. Phys., B 572 (2000) 211</subfield>
        </datafield>
       In the event that the miscellaneous text string is zero-length, there will be
       no $m subfield present in the returned XML.
       @param title: (string) - the cited title.
       @param volume: (string) - the volume of the cited title.
       @param year: (string) - the year of the cited title.
       @param page: (string) - the page of the cited title.
       @param report_number: (string) - the institutional report number to be marked up.
       @param misc_text: (string) - the miscellaneous text to be marked up.
       @return: (string) MARC XML representation of the cited title and its miscellaneous
        text.
    """
    ## First, determine whether there is need of a misc subfield:
    if len(misc_text) > 0:
        ## create a misc subfield to be included in the MARC XML:
        xml_misc_subfield = """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                    'misc-val'               : cgi.escape(misc_text, 1),
                  }
    else:
        ## the misc subfield is not needed
        xml_misc_subfield = ""
    ## Build the datafield for the report number segment of the reference line:
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">%(misc-subfield)s
      <subfield code="%(sf-code-ref-title)s">%(title)s %(volume)s (%(year)s) %(page)s</subfield>
      <subfield code="%(sf-code-ref-report-num)s">%(report-number)s</subfield>
   </datafield>
"""               % { 'df-tag-ref'             : CFG_REFEXTRACT_TAG_ID_REFERENCE,
                      'df-ind1-ref'            : CFG_REFEXTRACT_IND1_REFERENCE,
                      'df-ind2-ref'            : CFG_REFEXTRACT_IND2_REFERENCE,
                      'sf-code-ref-title'      : CFG_REFEXTRACT_SUBFIELD_TITLE,
                      'sf-code-ref-report-num' : CFG_REFEXTRACT_SUBFIELD_REPORT_NUM,
                      'misc-subfield'          : xml_misc_subfield,
                      'title'                  : cgi.escape(title, 1),
                      'volume'                 : cgi.escape(volume, 1),
                      'year'                   : cgi.escape(year, 1),
                      'page'                   : cgi.escape(page, 1),
                      'report-number'          : cgi.escape(report_number, 1),
                    }
    return xml_line

def _refextract_markup_report_number_followed_by_title_as_marcxml(title, volume, year, page,
                                                                  report_number, misc_text=""):
    """Given a title (and its numeration), a report number, and some optional
       miscellaneous text, return a string containing the MARC XML version of this
       information. E.g. for the miscellaneous text "S. D. Hsu and M. Schwetz ",
       the title "Nucl. Phys., B", the volume "572", the year "2000", the page
       number "211", and the report number "hep-th/1111111", return the following
       MARC XML string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="m">S. D. Hsu and M. Schwetz </subfield>
           <subfield code="s">Nucl. Phys., B 572 (2000) 211</subfield>
           <subfield code="r">hep-th/1111111</subfield>
        </datafield>
       In the event that the miscellaneous text string is zero-length, there will be
       no $m subfield present in the returned XML.
       @param title: (string) - the cited title.
       @param volume: (string) - the volume of the cited title.
       @param year: (string) - the year of the cited title.
       @param page: (string) - the page of the cited title.
       @param report_number: (string) - the institutional report number to be marked up.
       @param misc_text: (string) - the miscellaneous text to be marked up.
       @return: (string) MARC XML representation of the cited title and its miscellaneous
        text.
    """
    ## First, determine whether there is need of a misc subfield:
    if len(misc_text) > 0:
        ## create a misc subfield to be included in the MARC XML:
        xml_misc_subfield = """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                    'misc-val'               : cgi.escape(misc_text, 1),
                  }
    else:
        ## the misc subfield is not needed
        xml_misc_subfield = ""
    ## Build the datafield for the report number segment of the reference line:
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">%(misc-subfield)s
      <subfield code="%(sf-code-ref-report-num)s">%(report-number)s</subfield>
      <subfield code="%(sf-code-ref-title)s">%(title)s %(volume)s (%(year)s) %(page)s</subfield>
   </datafield>
"""               % { 'df-tag-ref'             : CFG_REFEXTRACT_TAG_ID_REFERENCE,
                      'df-ind1-ref'            : CFG_REFEXTRACT_IND1_REFERENCE,
                      'df-ind2-ref'            : CFG_REFEXTRACT_IND2_REFERENCE,
                      'sf-code-ref-title'      : CFG_REFEXTRACT_SUBFIELD_TITLE,
                      'sf-code-ref-report-num' : CFG_REFEXTRACT_SUBFIELD_REPORT_NUM,
                      'misc-subfield'          : xml_misc_subfield,
                      'title'                  : cgi.escape(title, 1),
                      'volume'                 : cgi.escape(volume, 1),
                      'year'                   : cgi.escape(year, 1),
                      'page'                   : cgi.escape(page, 1),
                      'report-number'          : cgi.escape(report_number, 1),
                    }
    return xml_line

def _refextract_markup_reportnumber_as_marcxml(report_number, misc_text=""):
    """Given a report number and some optional miscellaneous text, return a string
       containing the MARC XML version of this information. E.g. for the miscellaneous
       text "Example, AN " and the institutional report number "hep-th/1111111", return
       the following MARC XML string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="m">Example, AN </subfield>
           <subfield code="r">hep-th/1111111</subfield>
        </datafield>
       In the event that the miscellaneous text string is zero-length, there will be
       no $m subfield present in the returned XML.
       @param report_number: (string) - the institutional report number to be marked up.
       @param misc_text: (string) - the miscellaneous text to be marked up.
       @return: (string) MARC XML representation of the report number and its miscellaneous
        text.
    """
    ## First, determine whether there is need of a misc subfield:
    if len(misc_text) > 0:
        ## create a misc subfield to be included in the MARC XML:
        xml_misc_subfield = """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                    'misc-val'               : cgi.escape(misc_text, 1),
                  }
    else:
        ## the misc subfield is not needed
        xml_misc_subfield = ""
    ## Build the datafield for the report number segment of the reference line:
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">%(misc-subfield)s
      <subfield code="%(sf-code-ref-report-num)s">%(report-number)s</subfield>
   </datafield>
"""               % { 'df-tag-ref'             : CFG_REFEXTRACT_TAG_ID_REFERENCE,
                      'df-ind1-ref'            : CFG_REFEXTRACT_IND1_REFERENCE,
                      'df-ind2-ref'            : CFG_REFEXTRACT_IND2_REFERENCE,
                      'sf-code-ref-report-num' : CFG_REFEXTRACT_SUBFIELD_REPORT_NUM,
                      'misc-subfield'          : xml_misc_subfield,
                      'report-number'          : cgi.escape(report_number, 1),
                    }
    return xml_line

def _refextract_markup_url_as_marcxml(url_string, url_description, misc_text=""):
    """Given a URL, a URL description, and some optional miscellaneous text, return a string
       containing the MARC XML version of this information. E.g. for the miscellaneous
       text "Example, AN ", the URL "http://cdsweb.cern.ch/", and the URL description
       "CERN Document Server", return the following MARC XML string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="m">Example, AN </subfield>
           <subfield code="u">http://cdsweb.cern.ch/</subfield>
           <subfield code="z">CERN Document Server</subfield>
        </datafield>
       In the event that the miscellaneous text string is zero-length, there will be
       no $m subfield present in the returned XML.
       @param url_string: (string) - the URL to be marked up.
       @param url_description: (string) - the description of the URL to be marked up.
       @param misc_text: (string) - the miscellaneous text to be marked up.
       @return: (string) MARC XML representation of the URL, its description, and its
        miscellaneous text.
    """
    ## First, determine whether there is need of a misc subfield:
    if len(misc_text) > 0:
        ## create a misc subfield to be included in the MARC XML:
        xml_misc_subfield = """
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>""" \
                % { 'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                    'misc-val'               : cgi.escape(misc_text, 1),
                  }
    else:
        ## the misc subfield is not needed
        xml_misc_subfield = ""
    ## Build the datafield for the URL segment of the reference line:
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">%(misc-subfield)s
      <subfield code="%(sf-code-ref-url)s">%(url)s</subfield>
      <subfield code="%(sf-code-ref-url-descr)s">%(url-descr)s</subfield>
   </datafield>
"""               % { 'df-tag-ref'             : CFG_REFEXTRACT_TAG_ID_REFERENCE,
                      'df-ind1-ref'            : CFG_REFEXTRACT_IND1_REFERENCE,
                      'df-ind2-ref'            : CFG_REFEXTRACT_IND2_REFERENCE,
                      'sf-code-ref-url'        : CFG_REFEXTRACT_SUBFIELD_URL,
                      'sf-code-ref-url-descr'  : CFG_REFEXTRACT_SUBFIELD_URL_DESCR,
                      'misc-subfield'          : xml_misc_subfield,
                      'url'                    : cgi.escape(url_string, 1),
                      'url-descr'              : cgi.escape(url_description, 1),
                    }
    return xml_line

def _refextract_markup_reference_line_marker_as_marcxml(marker_text):
    """Given a reference line marker, return a string containing the MARC XML version of
       the marker. E.g. for the line marker "[1]", return the following xml string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="o">[1]</subfield>
        </datafield>
       @param marker_text: (string) the reference line marker to be marked up as MARC XML
       @return: (string) MARC XML representation of the marker line.
    """
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">
      <subfield code="%(sf-code-ref-marker)s">%(marker-val)s</subfield>
   </datafield>
""" % { 'df-tag-ref'         : CFG_REFEXTRACT_TAG_ID_REFERENCE,
        'df-ind1-ref'        : CFG_REFEXTRACT_IND1_REFERENCE,
        'df-ind2-ref'        : CFG_REFEXTRACT_IND2_REFERENCE,
        'sf-code-ref-marker' : CFG_REFEXTRACT_SUBFIELD_MARKER,
        'marker-val'         : cgi.escape(marker_text, 1),
      }
    return xml_line

def _refextract_markup_miscellaneous_text_as_marcxml(misc_text):
    """Given some miscellaneous text, return a string containing the MARC XML version of
       the string. E.g. for the misc_text string "testing", return the following xml string:
        <datafield tag="999" ind1="C" ind2="5">
           <subfield code="m">testing</subfield>
        </datafield>
       @param misc_text: (string) the miscellaneous text to be marked up as MARC XML
       @return: (string) MARC XML representation of the miscellaneous text.
    """
    xml_line = \
"""   <datafield tag="%(df-tag-ref)s" ind1="%(df-ind1-ref)s" ind2="%(df-ind2-ref)s">
      <subfield code="%(sf-code-ref-misc)s">%(misc-val)s</subfield>
   </datafield>
"""           % { 'df-tag-ref'             : CFG_REFEXTRACT_TAG_ID_REFERENCE,
                  'df-ind1-ref'            : CFG_REFEXTRACT_IND1_REFERENCE,
                  'df-ind2-ref'            : CFG_REFEXTRACT_IND2_REFERENCE,
                  'sf-code-ref-misc'       : CFG_REFEXTRACT_SUBFIELD_MISC,
                  'misc-val'               : cgi.escape(misc_text, 1),
                }
    return xml_line

def _convert_unusable_tag_to_misc(line, misc_text, tag_match_start, tag_match_end, closing_tag):
    """Function to remove an unwanted, tagged, citation item from a reference line. Everything
       prior to the opening tag, as well as the tagged item itself, is put into the miscellaneous
       text variable; the data up to the closing tag is then trimmed from the beginning of the
       working line. For example, the following working line:
         Example, AN. Testing software; <cds.YR>(2001)</cds.YR>, CERN, Geneva.
       ...would be trimmed down to:
         , CERN, Geneva.
       ...And the Miscellaneous text taken from the start of the line would be:
         Example, AN. Testing software; (2001)
       ...(assuming that the details of <cds.YR> and </cds.YR> were passed to the function).
       @param line: (string) - the reference line.
       @param misc_text: (string) - the variable containing the miscellaneous text recorded so far.
       @param tag_match_start: (integer) - the index of the start of the opening tag in the line.
       @param tag_match_end: (integer) - the index of the end of the opening tag in the line.
       @param closing_tag: (string) - the closing tag to look for in the line (e.g. </cds.YR>).
       @return: (tuple) - containing misc_text (string) and line (string)
    """
    misc_text += line[0:tag_match_start]
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

def convert_processed_reference_line_to_marc_xml(line):
    """Given a processed reference line, convert it to MARC XML.
       @param line: (string) - the processed reference line, in which
        the recognised citations have been tagged.
       @return: (tuple) -
          + xml_line (string) - the reference line with all of its
            identified citations marked up into the various subfields.
          + count_misc (integer) - number of sections of miscellaneous
             found in the line
          + count_title (integer) - number of title-citations found in
            the line
          + count_reportnum (integer) - number of report numbers found
            in the line
          + count_url (integer) - number of URLs found in the line
    """
    count_misc = count_title = count_reportnum = count_url = 0
    xml_line = ""
    previously_cited_item = None
    processed_line = line.lstrip()

    ## 1. Extract reference line marker (e.g. [1]) from start of line and tag it:
    ## get patterns to identify numeration markers at the start of lines:
    marker_patterns = get_reference_line_numeration_marker_patterns()
    marker_match = perform_regex_match_upon_line_with_pattern_list(processed_line, marker_patterns)

    if marker_match is not None:
        ## found a marker:
        marker_val = marker_match.group(u'mark')
        ## trim the marker from the start of the line:
        processed_line = processed_line[marker_match.end():].lstrip()
    else:
        marker_val = u" "

    ## Now display the marker in marked-up XML:
    xml_line += _refextract_markup_reference_line_marker_as_marcxml(marker_val)

    ## 2. Loop through remaining identified segments in line and tag them into MARC XML segments:
    cur_misc_txt = u""  ## a marker to hold gathered miscellaneous text before a citation
    tag_match = sre_tagged_citation.search(processed_line)
    while tag_match is not None:
        ## found a tag - process it:
        tag_match_start = tag_match.start()
        tag_match_end   = tag_match.end()
        tag_type        = tag_match.group(1)

        if tag_type == "TITLE":
            ## This tag is an identified journal TITLE. It should be followed by VOLUME,
            ## YEAR and PAGE tags.
            cur_misc_txt += processed_line[0:tag_match_start]
            ## extract the title from the line:
            idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_TITLE, tag_match_end)
            ## Sanity check - did we find a closing TITLE tag?
            if idx_closing_tag == -1:
                ## no closing </cds.TITLE> tag found - strip the opening tag and move past it
                processed_line = processed_line[tag_match_end:]
            else:
                ## Closing tag was found:
                title_text  = processed_line[tag_match_end:idx_closing_tag]
                ## Now trim this matched title and its tags from the start of the line:
                processed_line = processed_line[idx_closing_tag+len(CFG_REFEXTRACT_MARKER_CLOSING_TITLE):]

                ## Was this title followed by the tags of recognised VOLUME, YEAR and PAGE objects?
                numeration_match = sre_recognised_numeration_for_title.match(processed_line)
                if numeration_match is not None:
                    ## recognised numeration immediately after the title - extract it:
                    reference_volume = numeration_match.group(2)
                    reference_year   = numeration_match.group(3)
                    reference_page   = numeration_match.group(4)
                    ## Skip past the matched numeration in the working line:
                    processed_line = processed_line[numeration_match.end():]

                    if previously_cited_item is None:
                        ## There is no previously cited item - this should be added as the previously
                        ## cited item:
                        previously_cited_item = { 'type'       : "TITLE",
                                                  'misc_txt'   : cur_misc_txt,
                                                  'title'      : title_text,
                                                  'volume'     : reference_volume,
                                                  'year'       : reference_year,
                                                  'page'       : reference_page,
                                                }
                        ## Now empty the miscellaneous text and title components:
                        cur_misc_txt = ""
                        title_text = ""
                        reference_volume = ""
                        reference_year = ""
                        reference_page = ""
                    elif (previously_cited_item is not None) and \
                         (previously_cited_item['type'] == "REPORTNUMBER") and \
                         (len(cur_misc_txt.lower().replace("arxiv", "").strip(".,:;- []")) == 0):
                        ## This TITLE belongs with the REPORT NUMBER before it - add them both into
                        ## the same datafield tag (REPORT NUMBER first, TITLE second):
                        prev_report_num = previously_cited_item['report_num']
                        prev_misc_txt   = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                        xml_line += \
                           _refextract_markup_title_followed_by_report_number_as_marcxml(title_text,
                                                                                         reference_volume,
                                                                                         reference_year,
                                                                                         reference_page,
                                                                                         prev_report_num,
                                                                                         prev_misc_txt)
                        ## Increment the stats counters:
##                         if len(prev_misc_txt) > 0:
##                             count_misc += 1
                        count_title += 1
                        count_reportnum += 1

                        ## reset the various variables:
                        previously_cited_item = None
                        cur_misc_txt = u""
                        title_text = ""
                        reference_volume = ""
                        reference_year = ""
                        reference_page = ""
                    else:
                        ## either the previously cited item is NOT a REPORT NUMBER, or this cited TITLE
                        ## is preceeded by miscellaneous text. In either case, the two cited objects are
                        ## not the same and do not belong together in the same datafield.
                        if previously_cited_item['type'] == "REPORTNUMBER":
                            ## previously cited item was a REPORT NUMBER.
                            ## Add previously cited REPORT NUMBER to XML string:
                            prev_report_num = previously_cited_item['report_num']
                            prev_misc_txt   = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                            xml_line += _refextract_markup_reportnumber_as_marcxml(prev_report_num,
                                                                                   prev_misc_txt)
                            ## Increment the stats counters:
##                             if len(prev_misc_txt) > 0:
##                                 count_misc += 1
                            count_reportnum += 1
                        elif previously_cited_item['type'] == "TITLE":
                            ## previously cited item was a TITLE.
                            ## Add previously cited TITLE to XML string:
                            prev_title    = previously_cited_item['title']
                            prev_volume   = previously_cited_item['volume']
                            prev_year     = previously_cited_item['year']
                            prev_page     = previously_cited_item['page']
                            prev_misc_txt = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                            xml_line += _refextract_markup_title_as_marcxml(prev_title, prev_volume,
                                                                            prev_year, prev_page, prev_misc_txt)
                            ## Increment the stats counters:
##                             if len(prev_misc_txt) > 0:
##                                 count_misc += 1
                            count_title += 1

                        ## Now add the current cited item into the previously cited item marker
                        previously_cited_item = { 'type'       : "TITLE",
                                                  'misc_txt'   : cur_misc_txt,
                                                  'title'      : title_text,
                                                  'volume'     : reference_volume,
                                                  'year'       : reference_year,
                                                  'page'       : reference_page,
                                                }
                        ## empty miscellaneous text
                        cur_misc_txt = u""
                        title_text = ""
                        reference_volume = ""
                        reference_year = ""
                        reference_page = ""
                else:
                    ## No numeration was recognised after the title. Add the title into misc and carry on:
                    cur_misc_txt += " %s" % title_text

        elif tag_type == "REPORTNUMBER":
            ## This tag is an identified institutional report number:
            ## Account for the miscellaneous text before the citation:
            cur_misc_txt += processed_line[0:tag_match_start]
            ## extract the institutional report-number from the line:
            idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM, tag_match_end)
            ## Sanity check - did we find a closing report-number tag?
            if idx_closing_tag == -1:
                ## no closing </cds.REPORTNUMBER> tag found - strip the opening tag and move past this
                ## recognised reportnumber as it is unreliable:
                processed_line = processed_line[tag_match_end:]
            else:
                ## closing tag was found
                report_num = processed_line[tag_match_end:idx_closing_tag]
                ## now trim this matched institutional report-number and its tags from the start of the line:
                processed_line = processed_line[idx_closing_tag+len(CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM):]

                ## Now, if there was a previous TITLE citation and this REPORT NUMBER citation one has no
                ## miscellaneous text after punctuation has been stripped, the two refer to the same object,
                ## so group them under the same datafield:
                if previously_cited_item is None:
                    ## There is no previously cited item - this should be added as the previously
                    ## cited item:
                    previously_cited_item = { 'type'       : "REPORTNUMBER",
                                              'misc_txt'   : "%s" % cur_misc_txt,
                                              'report_num' : "%s" % report_num,
                                            }
                    ## empty miscellaneous text
                    cur_misc_txt = u""
                    report_num = u""
                elif (previously_cited_item is not None) and \
                     (previously_cited_item['type'] == "TITLE") and \
                     (len(cur_misc_txt.lower().replace("arxiv", "").strip(".,:;- []")) == 0):
                    ## This REPORT NUMBER belongs with the title before it - add them both into
                    ## the same datafield tag (TITLE first, REPORT NUMBER second):
                    prev_title    = previously_cited_item['title']
                    prev_volume   = previously_cited_item['volume']
                    prev_year     = previously_cited_item['year']
                    prev_page     = previously_cited_item['page']
                    prev_misc_txt = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                    xml_line += \
                      _refextract_markup_title_followed_by_report_number_as_marcxml(prev_title,
                                                                                    prev_volume,
                                                                                    prev_year,
                                                                                    prev_page,
                                                                                    report_num,
                                                                                    prev_misc_txt)
                    ## Increment the stats counters:
##                     if len(prev_misc_txt) > 0:
##                         count_misc += 1
                    count_title += 1
                    count_reportnum += 1

                    ## Reset variables:
                    previously_cited_item = None
                    cur_misc_txt = u""
                else:
                    ## either the previously cited item is NOT a TITLE, or this cited REPORT NUMBER
                    ## is preceeded by miscellaneous text. In either case, the two cited objects are
                    ## not the same and do not belong together in the same datafield.
                    if previously_cited_item['type'] == "REPORTNUMBER":
                        ## previously cited item was a REPORT NUMBER.
                        ## Add previously cited REPORT NUMBER to XML string:
                        prev_report_num = previously_cited_item['report_num']
                        prev_misc_txt   = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                        xml_line += _refextract_markup_reportnumber_as_marcxml(prev_report_num,
                                                                               prev_misc_txt)
                        ## Increment the stats counters:
##                         if len(prev_misc_txt) > 0:
##                             count_misc += 1
                        count_reportnum += 1
                    elif previously_cited_item['type'] == "TITLE":
                        ## previously cited item was a TITLE.
                        ## Add previously cited TITLE to XML string:
                        prev_title    = previously_cited_item['title']
                        prev_volume   = previously_cited_item['volume']
                        prev_year     = previously_cited_item['year']
                        prev_page     = previously_cited_item['page']
                        prev_misc_txt = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                        xml_line += _refextract_markup_title_as_marcxml(prev_title, prev_volume,
                                                                        prev_year, prev_page, prev_misc_txt)
                        ## Increment the stats counters:
##                         if len(prev_misc_txt) > 0:
##                             count_misc += 1
                        count_title += 1
                    ## Now add the current cited item into the previously cited item marker
                    previously_cited_item = { 'type'       : "REPORTNUMBER",
                                              'misc_txt'   : "%s" % cur_misc_txt,
                                              'report_num' : "%s" % report_num,
                                            }
                    ## empty miscellaneous text
                    cur_misc_txt = u""
                    report_num = u""

        elif tag_type == "URL":
            ## This tag is an identified URL:
            ## Account for the miscellaneous text before the URL:
            cur_misc_txt += processed_line[0:tag_match_start]
            ## extract the URL information from within the tags in the line:
            idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_URL, tag_match_end)
            ## Sanity check - did we find a closing URL tag?
            if idx_closing_tag == -1:
                ## no closing </cds.URL> tag found - strip the opening tag and move past it
                processed_line = processed_line[tag_match_end:]
            else:
                ## Closing tag was found:
                ## First, get the URL string from between the tags:
                url_string = processed_line[tag_match_end:idx_closing_tag]

                ## Now, get the URL description string from within the opening cds tag. E.g.:
                ## from <cds.URL description="abc"> get the "abc" value:
                opening_url_tag = processed_line[tag_match_start:tag_match_end]
                if opening_url_tag.find(u"""<cds.URL description=\"""") != -1:
                    ## the description is present - extract it:
                    ## (Stop 2 characters before the end of the string - we assume they are the
                    ## closing characters '">'.
                    url_descr = opening_url_tag[22:-2]
                else:
                    ## There is no description - description should now be the url string:
                    url_descr = url_string
                ## now trim this URL and its tags from the start of the line:
                processed_line = processed_line[idx_closing_tag+len(CFG_REFEXTRACT_MARKER_CLOSING_URL):]

                ## Build the MARC XML representation of this identified URL:
                if previously_cited_item is not None:
                    ## There was a previously cited item. We must convert it to XML before we can
                    ## convert this URL to XML:
                    if previously_cited_item['type'] == "REPORTNUMBER":
                        ## previously cited item was a REPORT NUMBER.
                        ## Add previously cited REPORT NUMBER to XML string:
                        prev_report_num = previously_cited_item['report_num']
                        prev_misc_txt   = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                        xml_line += _refextract_markup_reportnumber_as_marcxml(prev_report_num,
                                                                               prev_misc_txt)
                        ## Increment the stats counters:
##                         if len(prev_misc_txt) > 0:
##                             count_misc += 1
                        count_reportnum += 1
                    elif previously_cited_item['type'] == "TITLE":
                        ## previously cited item was a TITLE.
                        ## Add previously cited TITLE to XML string:
                        prev_title    = previously_cited_item['title']
                        prev_volume   = previously_cited_item['volume']
                        prev_year     = previously_cited_item['year']
                        prev_page     = previously_cited_item['page']
                        prev_misc_txt = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
                        xml_line += _refextract_markup_title_as_marcxml(prev_title, prev_volume,
                                                                        prev_year, prev_page, prev_misc_txt)
                        ## Increment the stats counters:
##                         if len(prev_misc_txt) > 0:
##                             count_misc += 1
                        count_title += 1
                    ## Empty the previously-cited item place-holder:
                    previously_cited_item = None
                ## Now convert this URL to MARC XML
                cur_misc_txt = cur_misc_txt.lstrip(".;, ").rstrip()
                if url_string.find("http //") == 0:
                    url_string = u"http://" + url_string[7:]
                elif url_string.find("ftp //") == 0:
                    url_string = u"ftp://" + url_string[6:]
                if url_descr.find("http //") == 0:
                    url_descr = u"http://" + url_descr[7:]
                elif url_descr.find("ftp //") == 0:
                    url_descr = u"ftp://" + url_descr[6:]
                xml_line += \
                          _refextract_markup_url_as_marcxml(url_string, url_descr, cur_misc_txt)
                ## Increment the stats counters:
##                 if len(cur_misc_txt) > 0:
##                     count_misc += 1
                count_url += 1
                cur_misc_txt = u""

        elif tag_type == "SER":
            ## This tag is a SERIES tag; Since it was not preceeded by a TITLE tag,
            ## it is useless - strip the tag and put it into miscellaneous:
            (cur_misc_txt, processed_line) = \
                         _convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                                       tag_match_start,tag_match_end,
                                                       CFG_REFEXTRACT_MARKER_CLOSING_SERIES)

        elif tag_type == "VOL":
            ## This tag is a VOLUME tag; Since it was not preceeded by a TITLE tag,
            ## it is useless - strip the tag and put it into miscellaneous:
            (cur_misc_txt, processed_line) = \
                         _convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                                       tag_match_start,tag_match_end,
                                                       CFG_REFEXTRACT_MARKER_CLOSING_VOLUME)

        elif tag_type == "YR":
            ## This tag is a YEAR tag; Since it's not preceeded by TITLE and VOLUME tags, it
            ## is useless - strip the tag and put the contents into miscellaneous:
            (cur_misc_txt, processed_line) = \
                         _convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                                       tag_match_start,tag_match_end,
                                                       CFG_REFEXTRACT_MARKER_CLOSING_YEAR)

        elif tag_type == "PG":
            ## This tag is a PAGE tag; Since it's not preceeded by TITLE, VOLUME and YEAR tags,
            ## it is useless - strip the tag and put the contents into miscellaneous:
            (cur_misc_txt, processed_line) = \
                         _convert_unusable_tag_to_misc(processed_line, cur_misc_txt, \
                                                       tag_match_start,tag_match_end,
                                                       CFG_REFEXTRACT_MARKER_CLOSING_PAGE)

        else:
            ## Unknown tag - discard as miscellaneous text:
            cur_misc_txt += processed_line[0:tag_match.end()]
            processed_line = processed_line[tag_match.end():]

        ## Look for the next tag in the processed line:
        tag_match = sre_tagged_citation.search(processed_line)

    ## If a previously cited item remains, convert it into MARC XML:
    if previously_cited_item is not None:
        if previously_cited_item['type'] == "REPORTNUMBER":
            ## previously cited item was a REPORT NUMBER.
            ## Add previously cited REPORT NUMBER to XML string:
            prev_report_num = previously_cited_item['report_num']
            prev_misc_txt   = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
            xml_line += _refextract_markup_reportnumber_as_marcxml(prev_report_num,
                                                                   prev_misc_txt)
            ## Increment the stats counters:
##             if len(prev_misc_txt) > 0:
##                 count_misc += 1
            count_reportnum += 1
        elif previously_cited_item['type'] == "TITLE":
            ## previously cited item was a TITLE.
            ## Add previously cited TITLE to XML string:
            prev_title    = previously_cited_item['title']
            prev_volume   = previously_cited_item['volume']
            prev_year     = previously_cited_item['year']
            prev_page     = previously_cited_item['page']
            prev_misc_txt = previously_cited_item['misc_txt'].lstrip(".;, ").rstrip()
            xml_line += _refextract_markup_title_as_marcxml(prev_title, prev_volume,
                                                            prev_year, prev_page, prev_misc_txt)
            ## Increment the stats counters:
##             if len(prev_misc_txt) > 0:
##                 count_misc += 1
            count_title += 1
        ## free up previously_cited_item:
        previously_cited_item = None

    ## place any remaining miscellaneous text into the appropriate MARC XML fields:
    cur_misc_txt += processed_line
    if len(cur_misc_txt.strip(" .;,")) > 0:
        ## The remaining misc text is not just a full-stop or semi-colon. Add it:
        xml_line += _refextract_markup_miscellaneous_text_as_marcxml(cur_misc_txt)
        ## Increment the stats counters:
        count_misc += 1

    ## return the reference-line as MARC XML:
    return (xml_line, count_misc, count_title, count_reportnum, count_url)

def move_tagged_series_into_tagged_title(line):
    ## TODO: TEST ME!
    ## Seek a marked-up series occurrence in line:
    m_tagged_series = sre_title_followed_by_series_markup_tags.search(line)
    while m_tagged_series is not None:
        ## tagged series found in line - try to remove it and put it into the title:
        entire_match = m_tagged_series.group(0) ## the entire match (e.g.<cds.TITLE>xxxxx</cds.TITLE <cds.SER>A</cds.SER>)
        title_match = m_tagged_series.group(2)  ## the string matched between <cds.TITLE></cds.TITLE> tags
        series_match = m_tagged_series.group(3) ## the series information matched between <cds.SER></cds.SER> tags.
        corrected_title_text = title_match
        ## If there is no comma in the matched title, add one to the end of it before the series info is
        ## added. If there is already a comma present, discard the series info (as there is already a series)
        if corrected_title_text.find(",") != -1:
            corrected_title_text = corrected_title_text.rstrip()
            if corrected_title_text[-1] == ".":
                corrected_title_text += ", %s" % series_match
            else:
                corrected_title_text += "., %s" % series_match
        line = re.sub("%s" % re.escape(entire_match), "<cds.TITLE>%s</cds.TITLE>" % corrected_title_text, line, 1)
        m_tagged_series = sre_title_followed_by_series_markup_tags.search(line)
    return line

def _re_identify_numeration(line):
    """Look for other numeration in line.
    """
    ## First, attempt to use marked-up titles 
    line = sre_correct_numeration_2nd_try_ptn1[0].sub(sre_correct_numeration_2nd_try_ptn1[1], line)
    line = sre_correct_numeration_2nd_try_ptn2[0].sub(sre_correct_numeration_2nd_try_ptn2[1], line)
    return line

def add_tagged_report_number(reading_line,
                             len_reportnum,
                             reportnum,
                             startpos,
                             true_replacement_index,
                             extras):
    """In rebuilding the line, add an identified institutional REPORT-NUMBER (standardised
       and tagged) into the line.
       @param reading_line: (string) The reference line before capitalization was performed, and
        before REPORT-NUMBERs and TITLEs were stipped out.
       @param len_reportnum: (integer) the length of the matched REPORT-NUMBER.
       @param reportnum: (string) the replacement text for the matched REPORT-NUMBER.
       @param startpos: (integer) the pointer to the next position in the reading-line
        from which to start rebuilding.
       @param true_replacement_index: (integer) the replacement index of the matched REPORT-
        NUMBER in the reading-line, with stripped punctuation and whitespace accounted for.
       @param extras: (integer) extras to be added into the replacement index.
       @return: (tuple) containing a string (the rebuilt line segment) and an
        integer (the next 'startpos' in the reading-line).
    """
    rebuilt_line = u""  ## The segment of the line that is being rebuilt to include the
                        ## tagged and standardised institutional REPORT-NUMBER
    
    ## Fill rebuilt_line with the contents of the reading_line up to the point of the
    ## institutional REPORT-NUMBER. However, stop 1 character before the replacement
    ## index of this REPORT-NUMBER to allow for removal of braces, if necessary:
    if (true_replacement_index - startpos - 1) >= 0:
        rebuilt_line += reading_line[startpos:true_replacement_index - 1]
    else:
        rebuilt_line += reading_line[startpos:true_replacement_index]

    ## check to see whether the REPORT-NUMBER was enclosed within brackets; drop them if so:
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
    
    ## return the rebuilt-line segment and the pointer to the next position in the
    ## reading-line from  which to start rebuilding up to the next match:
    return (rebuilt_line, startpos)

def add_tagged_title_in_place_of_IBID(ibid_string,
                                      previous_match,
                                      ibid_series):
    """In rebuilding the line, if the matched TITLE was actually an IBID, this
       function will replace it with the previously matched TITLE, and add it
       into the line, tagged. It will even handle the series letter, if it differs.
       For example, if the previous match is "Nucl. Phys., B", and the ibid is
       "IBID A", the title inserted into the line will be "Nucl. Phys., A".
       Otherwise, if the IBID had no series letter, it will simply be replaced
       by "Nucl. Phys., B" (i.e. the previous match.)
       @param ibid_string: (string) - the matched IBID.
       @param previous_match: (string) - the previously matched TITLE.
       @param ibid_series: (string) - the series of the IBID (if any).
       @return: (tuple) containing a string (the rebuilt line segment) and an
        other string (the newly updated previous-match).
    """
    rebuilt_line = u""
    if ibid_series != "":
        ## This IBID has a series letter. If the previously matched TITLE also had a series letter
        ## and that series letter differs to the one carried by this IBID, the series letter stored in
        ## the previous-match must be updated to that of this IBID:
        if previous_match.find(",") != -1:
            ## Presence of comma in previous match could mean it has a series:
            m_previous_series = sre_title_series.search(previous_match)
            if m_previous_series is not None:
                previous_series = m_previous_series.group(1)
                if previous_series == ibid_series:
                    ## Both the previous match and this IBID have the same series
                    rebuilt_line += " <cds.TITLE>%(previous-match)s</cds.TITLE>" \
                                    % { 'previous-match' : previous_match }
                else:
                    ## Previous match and this IBID do not have the same series
                    previous_match = sre.sub("(\\.?)(,?) %s$" % previous_series, \
                                             "\\g<1>\\g<2> %s" % ibid_series, previous_match)
                    rebuilt_line += " <cds.TITLE>%(previous-match)s</cds.TITLE>" \
                                    % { 'previous-match' : previous_match }
            else:
                ## Series info of previous match is not a letter or roman numeral;
                ## cannot be sure about meaning of IBID - dont replace it
                rebuilt_line += ibid_string
        else:
            ## previous match had no series letter, but the IBID did. Add the a comma
            ## followed by a series letter to the end of the previous match
            ## Now add the previous match into the rebuilt-line:
            previous_match = previous_match.rstrip()
            if previous_match[-1] == ".":
                ## Previous match ended with a full-stop. Add a comma, then the IBID series
                previous_match += ", %(ibid-series)s" % { 'ibid-series' : ibid_series }
            else:
                ## Previous match did not end with a full-stop. Add a full-stop then the comma,
                ## then the IBID series
                previous_match += "., %(ibid-series)s" % { 'ibid-series' : ibid_series }
            rebuilt_line += " <cds.TITLE>%(previous-match)s</cds.TITLE>" \
                           % { 'previous-match' : previous_match }
    else:
        ## IBID's series letter is empty - Replace as-is:
        rebuilt_line += " <cds.TITLE>%(previous-match)s</cds.TITLE>" \
                       % { 'previous-match' : previous_match }
    return (rebuilt_line, previous_match)

def add_tagged_title(reading_line,
                     len_title,
                     matched_title,
                     previous_match,
                     startpos,
                     true_replacement_index,
                     extras,
                     standardised_titles):
    """In rebuilding the line, add an identified periodical TITLE (standardised and
       tagged) into the line.
       @param reading_line: (string) The reference line before capitalization was performed, and
        before REPORT-NUMBERs and TITLEs were stipped out.
       @param len_title: (integer) the length of the matched TITLE.
       @param matched_title: (string) the matched TITLE text.
       @previous_match: (string) the previous periodical TITLE citation to have been matched
        in the current reference line. It is used when replacing an IBID instance in the line.
       @param startpos: (integer) the pointer to the next position in the reading-line
        from which to start rebuilding.
       @param true_replacement_index: (integer) the replacement index of the matched TITLE
        in the reading-line, with stripped punctuation and whitespace accounted for.
       @param extras: (integer) extras to be added into the replacement index.
       @param standardised_titles: (dictionary) the standardised versions of periodical
        titles, keyed by their various non-standard versions.
       @return: (tuple) containing a string (the rebuilt line segment), an
        integer (the next 'startpos' in the reading-line), and an other string
        (the newly updated previous-match).
    """
    ## Fill 'rebuilt_line' (the segment of the line that is being rebuilt to include the
    ## tagged and standardised periodical TITLE) with the contents of the reading-line,
    ## up to the point of the matched TITLE:
    rebuilt_line = reading_line[startpos:true_replacement_index]
    ## Test to see whether a title or an "IBID" was matched:
    if matched_title.upper().find("IBID") != -1:
        ## This is an IBID
        ## Try to replace the IBID with a title:
        if previous_match != "":
            ## A title has already been replaced in this line - IBID can be replaced meaninfully
            ## First, try to get the series number/letter of this IBID:
            m_ibid = sre_matched_ibid.search(matched_title)
            try:
                series = m_ibid.group(1)
            except IndexError:
                series = u""
            if series is None:
                series = u""
            ## Replace this IBID with the previous title match, if possible:
            (replaced_ibid_segment, previous_match) = \
                 add_tagged_title_in_place_of_IBID(matched_title,
                                                   previous_match, series)
            rebuilt_line += replaced_ibid_segment
            ## Update start position for next segment of original line:
            startpos = true_replacement_index + len_title + extras

            ## Skip past any punctuation at the end of the replacement that was just made:
            if reading_line[startpos] in (".", ":", ";"):
                startpos += 1
        else:
            ## no previous title-replacements in this line - IBID refers to something unknown and
            ## cannot be replaced:
            rebuilt_line += \
                reading_line[true_replacement_index:true_replacement_index + len_title + extras]
            startpos = true_replacement_index + len_title + extras
    else:
        ## This is a normal title, not an IBID
        rebuilt_line += "<cds.TITLE>%(title)s</cds.TITLE>" % { 'title' : standardised_titles[matched_title] }
        previous_match = standardised_titles[matched_title]
        startpos = true_replacement_index + len_title + extras
        ## Skip past any punctuation at the end of the replacement that was just made:
        if reading_line[startpos] in (".", ":", ";"):
            startpos += 1

    ## return the rebuilt line-segment, the position (of the reading line) from which the
    ## next part of the rebuilt line should be started, and the newly updated previous match.
    return (rebuilt_line, startpos, previous_match)

def create_marc_xml_reference_section(ref_sect,
                                      preprint_repnum_search_kb,
                                      preprint_repnum_standardised_categs,
                                      periodical_title_search_kb,
                                      standardised_periodical_titles,
                                      periodical_title_search_keys):
    """Passed a complete reference section, process each line and attempt to identify and standardise
       individual citations within the line.
       @param ref_sect: (list) of strings - each string in the list is a reference line.
       @param preprint_repnum_search_kb: (dictionary) - keyed by a tuple (containing the line-number
                                               of the pattern in the KB and the non-standard
                                               category string.  E.g.: (3, 'ASTRO PH'). Value is
                                               regexp pattern used to search for that report-number.
       @param preprint_repnum_standardised_categs: (dictionary) - keyed by non-standard version of
                                               institutional report number, value is the standardised
                                               version of that report number.
       @param periodical_title_search_kb: (dictionary) - keyed by non-standard title to search for,
                                               value is the compiled regexp pattern used to search
                                               for that title.
       @param standardised_periodical_titles: (dictionary) - keyed by non-standard title to search for,
                                               value is the standardised version of that title.
       @param periodical_title_search_keys: (list) - ordered list of non-standard titles to search for.
       @return: (tuple) of 5 components:
                  ( list    -> of strings, each string is a MARC XML-ized reference line.
                    integer -> number of fields of miscellaneous text found for the record.
                    integer -> number of title citations found for the record.
                    integer -> number of institutional report-number citations found for
                     the record.
                    integer -> number of URL citations found for the record.
                  )
    """
    ## a list to contain the processed reference lines:
    xml_ref_sectn = []
    ## counters for extraction stats:
    count_misc = count_title = count_reportnum = count_url = 0

    ## process references line-by-line:
    for ref_line in ref_sect:
        ## initialise some variables:
        found_item = 0
        citation_match = 0
        ## dictionaries to record information about, and coordinates of, matched IBID items:
        found_ibids_len = {}
        found_ibids_matchtext = {}
        ## dictionaries to record information about, and  coordinates of, matched journal title items:
        found_title_len = {}
        found_title_matchtext = {}
        ## dictionaries to record information about, and the coordinates of, matched preprint report
        ## number items
        found_pprint_repnum_matchlens     = {}    ## lengths of given matches of preprint report numbers
        found_pprint_repnum_replstr       = {}    ## standardised replacement strings for preprint report numbers
                                                  ## to be substituted into a line

        ## take a copy of the line as a first working line, clean it of bad accents, and correct puncutation, etc:
        working_line1 = wash_line(ref_line)

        ## Identify and standardise numeration in the line:
        working_line1 = standardize_and_markup_numeration_of_citations_in_line(working_line1)

        ## Identify and replace URLs in the line:
        working_line1 = identify_and_tag_URLs(working_line1)

        ## Clean the line once more:
        working_line1 = wash_line(working_line1)

        ## Transform the line to upper-case, now making a new working line:
        working_line2 = working_line1.upper()

        ## Strip punctuation from the line:
        working_line2 = sre_punctuation.sub(u' ', working_line2)

        ## Remove multiple spaces from the line, recording information about their coordinates:
        (removed_spaces, working_line2) = remove_and_record_multiple_spaces_in_line(working_line2)

        ## Identify and record coordinates of institute preprint report numbers:
        (found_pprint_repnum_matchlens, found_pprint_repnum_replstr, working_line2) = \
                                    identify_preprint_report_numbers(working_line2,
                                                                     preprint_repnum_search_kb,
                                                                     preprint_repnum_standardised_categs)

        ## Identify and record coordinates of non-standard journal titles:
        (found_title_len, found_title_matchtext, working_line2) = \
                          identify_periodical_titles(working_line2,
                                                     periodical_title_search_kb,
                                                     periodical_title_search_keys)

        ## Attempt to identify, record and replace any IBIDs in the line:
        if working_line2.upper().find(u"IBID") != -1:
            ## there is at least one IBID in the line - try to identify its meaning:
            (found_ibids_len, found_ibids_matchtext, working_line2) = identify_ibids(working_line2)
            ## now update the dictionary of matched title lengths with the matched IBID(s) lengths information:
            found_title_len.update(found_ibids_len)
            found_title_matchtext.update(found_ibids_matchtext)

        ## Using the recorded information, create a MARC XML representation of the rebuilt line:
        ## At the same time, get stats of citations found in the reference line (titles, urls, etc):
        (xml_line, this_count_misc, this_count_title, \
         this_count_reportnum, this_count_url) = \
             create_marc_xml_reference_line(working_line=working_line1,
                                            found_title_len=found_title_len,
                                            found_title_matchtext=found_title_matchtext,
                                            pprint_repnum_len=found_pprint_repnum_matchlens,
                                            pprint_repnum_matchtext=found_pprint_repnum_replstr,
                                            removed_spaces=removed_spaces,
                                            standardised_titles=standardised_periodical_titles)
        count_misc      += this_count_misc
        count_title     += this_count_title
        count_reportnum += this_count_reportnum
        count_url       += this_count_url

        ## Append the rebuilt line details to the list of MARC XML reference lines:
        xml_ref_sectn.append(xml_line)

    ## Return thereturn  list of processed reference lines:
    return (xml_ref_sectn, count_misc, count_title, count_reportnum, count_url)


## Tasks related to extraction of reference section from full-text:

## ----> 1. Removing page-breaks, headers and footers before searching for reference section:

def strip_headers_footers_pagebreaks(docbody, page_break_posns, num_head_lines, num_foot_lines):
    """Remove page-break lines, header lines, and footer lines from the document.
       @param docbody: (list) of strings, whereby each string in the list is a line in the document.
       @param page_break_posns: (list) of integers, whereby each integer represents the index in docbody
        at which a page-break is found.
       @param num_head_lines: (int) the number of header lines each page in the document has.
       @param num_foot_lines: (int) the number of footer lines each page in the document has.
       @return: (list) of strings - the document body after the headers, footers, and page-break lines
        have been stripped from the list.
    """
    num_breaks = (len(page_break_posns))
    page_lens = []
    for x in xrange(0, num_breaks):
        if x < num_breaks - 1:
            page_lens.append(page_break_posns[x + 1] - page_break_posns[x])
    page_lens.sort()
    if (len(page_lens) > 0) and (num_head_lines + num_foot_lines + 1 < page_lens[0]):
        ## Safe to chop hdrs & ftrs
        page_break_posns.reverse()
        first = 1
        for i in xrange(0, len(page_break_posns)):
            ## Unless this is the last page break, chop headers
            if not first:
                for j in xrange(1, num_head_lines + 1):
                    docbody[page_break_posns[i] + 1:page_break_posns[i] + 2] = []
            else:
                first = 0
            ## Chop page break itself
            docbody[page_break_posns[i]:page_break_posns[i] + 1] = []
            ## Chop footers (unless this is the first page break)
            if i != len(page_break_posns) - 1:
                for k in xrange(1, num_foot_lines + 1):
                    docbody[page_break_posns[i] - num_foot_lines:page_break_posns[i] - num_foot_lines + 1] = []
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
            if (l1_str[0] == l2_str[0]) and (l1_str[len(l1_str) - 1] == l2_str[len(l2_str) - 1]):
                num_matches = num_matches + 1
    if (len(l_1) == 0) or (float(num_matches) / float(len(l_1)) < 0.9):
        return 0
    else:
        return 1

def get_number_header_lines(docbody, page_break_posns):
    """Try to guess the number of header lines each page of a document has.
       The positions of the page breaks in the document are used to try to guess
       the number of header lines.
       @param docbody: (list) of strings - each string being a line in the document
       @param page_break_posns: (list) of integers - each integer is the position of a
        page break in the document.
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
            if docbody[(page_break_posns[cur_break] + num_header_lines + 1)].isspace():
                ## this is a blank line
                empty_line = 1
            
            if (page_break_posns[cur_break] + num_header_lines + 1) == (page_break_posns[(cur_break + 1)]):
                # Have reached next page-break: document has no body - only head/footers!
                keep_checking = 0
            
            grps_headLineWords = p_wordSearch.findall(docbody[(page_break_posns[cur_break] + num_header_lines + 1)])
            cur_break = cur_break + next_head
            while (cur_break < remaining_breaks) and keep_checking:
                grps_thisLineWords = p_wordSearch.findall(docbody[(page_break_posns[cur_break]+ num_header_lines + 1)])
                if empty_line:
                    if len(grps_thisLineWords) != 0:
                        ## This line should be empty, but isn't
                        keep_checking = 0
                else:
                    if (len(grps_thisLineWords) == 0) or (len(grps_headLineWords) != len(grps_thisLineWords)):
                        ## Not same num 'words' as equivilent line in 1st header:
                        keep_checking = 0
                    else:
                        keep_checking = check_boundary_lines_similar(grps_headLineWords, grps_thisLineWords)
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
       @param docbody: (list) of strings - each string being a line in the document
       @param page_break_posns: (list) of integers - each integer is the position of a
        page break in the document.
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
            if docbody[(page_break_posns[cur_break] - num_footer_lines - 1)].isspace():
                empty_line = 1
            grps_headLineWords = p_wordSearch.findall(docbody[(page_break_posns[cur_break] - num_footer_lines - 1)])
            cur_break = cur_break + 1
            while (cur_break < num_breaks) and keep_checking:
                grps_thisLineWords = p_wordSearch.findall(docbody[(page_break_posns[cur_break] - num_footer_lines - 1)])
                if empty_line:
                    if len(grps_thisLineWords) != 0:
                        ## this line should be empty, but isn't
                        keep_checking = 0
                else:
                    if (len(grps_thisLineWords) == 0) or (len(grps_headLineWords) != len(grps_thisLineWords)):
                        ## Not same num 'words' as equivilent line in 1st footer:
                        keep_checking = 0
                    else:
                        keep_checking = check_boundary_lines_similar(grps_headLineWords, grps_thisLineWords)
                ## Update cur_break for nxt line to check
                cur_break = cur_break + 1
            if keep_checking:
                ## Line is a footer line: check next
                num_footer_lines = num_footer_lines + 1
            empty_line = 0
    return num_footer_lines

def get_page_break_positions(docbody):
    """Locate page breaks in the list of document lines and create a list positions in the
       document body list.
       @param docbody: (list) of strings - each string is a line in the document.
       @return: (list) of integer positions, whereby each integer represents the position (in
        the document body) of a page-break.
    """
    page_break_posns = []
    p_break = re.compile(unicode(r'^\s*?\f\s*?$'), re.UNICODE)
    num_document_lines = len(docbody)
    for i in xrange(num_document_lines):
        if p_break.match(docbody[i]) != None:
            page_break_posns.append(i)
    return page_break_posns

def document_contains_text(docbody):
    """Test whether document contains text, or is just full of worthless whitespace.
       @param docbody: (list) of strings - each string being a line of the document's body
       @return: (integer) 1 if non-whitespace found in document; 0 if only whitespace found in document.
    """
    found_non_space = 0
    for line in docbody:
        if not line.isspace():
            ## found a non-whitespace character in this line
            found_non_space = 1
            break
    return found_non_space

def remove_page_boundary_lines(docbody):
    """Try to locate page breaks, headers and footers within a document body, and remove
       the array cells at which they are found.
       @param docbody: (list) of strings, each string being a line in the document's body.
       @return: (list) of strings. The document body, hopefully with page-breaks, headers
        and footers removed. Each string in the list once more represents a line in the
        document.
    """
    number_head_lines = number_foot_lines = 0
    ## Make sure document not just full of whitespace:
    if not document_contains_text(docbody):
        ## document contains only whitespace - cannot safely strip headers/footers
        return docbody
    
    ## Get list of index posns of pagebreaks in document:
    page_break_posns = get_page_break_positions(docbody)
    
    ## Get num lines making up each header if poss:
    number_head_lines = get_number_header_lines(docbody, page_break_posns)

    ## Get num lines making up each footer if poss:
    number_foot_lines = get_number_footer_lines(docbody, page_break_posns)

    ## Remove pagebreaks,headers,footers:
    docbody = strip_headers_footers_pagebreaks(docbody, page_break_posns, number_head_lines, number_foot_lines)

    return docbody

## ----> 2. Finding reference section in full-text:

def _create_regex_pattern_add_optional_spaces_to_word_characters(word):
    """Add the regex special characters (\s*?) to allow optional spaces between the
       characters in a word.
       @param word: (string) the word to be inserted into a regex pattern.
       @return: string: the regex pattern for that word with optional spaces between all
        of its characters.
    """
    new_word = u""
    for ch in word:
        if ch.isspace():
            new_word += ch
        else:
            new_word += ch + unicode(r'\s*?')
    return new_word


def get_reference_section_title_patterns():
    """Return a list of compiled regex patterns used to search for the title of a reference section
       in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    patterns = []
    titles = [ u'references',
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
            t_ptn = sre.compile(sect_marker + \
                                _create_regex_pattern_add_optional_spaces_to_word_characters(t) + \
                                line_end, sre.I|sre.UNICODE)
            patterns.append(t_ptn)
    return patterns


def get_reference_line_numeration_marker_patterns(prefix=u''):
    """Return a list of compiled regex patterns used to search for the marker of a reference line
       in a full-text document.
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
    patterns = [ space + title + g_name + unicode(r'\[\s*?(?P<linenumber>\d+)\s*?\]') + g_close,
                 space + title + g_name + unicode(r'\[\s*?[a-zA-Z]+\s?(\d{1,4}[A-Za-z]?)?\s*?\]') + g_close,
                 space + title + g_name + unicode(r'\{\s*?\d+\s*?\}') + g_close,
                 space + title + g_name + unicode(r'\<\s*?\d+\s*?\>') + g_close,
                 space + title + g_name + unicode(r'\(\s*?\d+\s*?\)') + g_close,
                 space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\.') + g_close,
                 space + title + g_name + unicode(r'\d+\s*?') + g_close,
                 space + title + g_name + unicode(r'\d+\s*?\]') + g_close,
                 space + title + g_name + unicode(r'\d+\s*?\}') + g_close,
                 space + title + g_name + unicode(r'\d+\s*?\)') + g_close,
                 space + title + g_name + unicode(r'\d+\s*?\>') + g_close,
                 space + title + g_name + unicode(r'\[\s*?\]') + g_close,
                 space + title + g_name + unicode(r'\*') + g_close ]
    for p in patterns:
        compiled_ptns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_ptns

def get_first_reference_line_numeration_marker_patterns():
    """Return a list of compiled regex patterns used to search for the first reference line
       in a full-text document.
       The line is considered to start with either: [1] or {1}
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    g_name = unicode(r'(?P<mark>')
    g_close = u')'
    patterns = [ g_name + unicode(r'(?P<left>\[)\s*?(?P<num>\d+)\s*?(?P<right>\])') + g_close,
                 g_name + unicode(r'(?P<left>\{)\s*?(?P<num>\d+)\s*?(?P<right>\})') + g_close ]
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns

def get_post_reference_section_title_patterns():
    """Return a list of compiled regex patterns used to search for the title of the section
       after the reference section in a full-text document.
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
    """Return a list of compiled regex patterns used to search for various keywords that can often be found after,
       and therefore suggest the end of, a reference section in a full-text document.
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
    """Given a list of COMPILED regex patters, perform the "re.match" operation on the line for every pattern.
       Break from searching at the first match, returning the match object.  In the case that no patterns match,
       the None type will be returned.
       @param line: (unicode string) to be searched in.
       @param patterns: (list) of compiled regex patterns to search  "line" with.
       @return: (None or an re.match object), depending upon whether one of the patterns matched within line
        or not.
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
    """Given a list of COMPILED regex patters, perform the "re.search" operation on the line for every pattern.
       Break from searching at the first match, returning the match object.  In the case that no patterns match,
       the None type will be returned.
       @param line: (unicode string) to be searched in.
       @param patterns: (list) of compiled regex patterns to search  "line" with.
       @return: (None or an re.match object), depending upon whether one of the patterns matched within line
        or not.
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
    """Search in document body for its reference section. More precisely, find the
       first line of the reference section. Effectively, the function starts at the
       end of a document and works backwards, line-by-line, looking for the title of
       a reference section. It stops when (if) it finds something that it considers
       to be the first line of a reference section.
       @param docbody: (list) of strings - the full document body.
       @return: (dictionary) :
                 { 'start_line' : (integer) - index in docbody of first reference line,
                   'title_string' : (string) - title of the reference section.
                   'marker' : (string) - the marker of the first reference line,
                   'marker_pattern' : (string) - the regexp string used to find the marker,
                   'title_marker_same_line' : (integer) - a flag to indicate whether the
                                               reference section title was on the same line
                                               as the first reference line's marker or not.
                                               1 if it was; 0 if it was not.
                 }
                 Much of this information is used by later functions to rebuild a reference
                 section.
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
            title_match = perform_regex_search_upon_line_with_pattern_list(docbody[x], title_patterns)
            if title_match is not None:
                temp_ref_start_line = x
                temp_title = title_match.group('title')
                mk_with_title_ptns = get_reference_line_numeration_marker_patterns(temp_title)
                mk_with_title_match = perform_regex_search_upon_line_with_pattern_list(docbody[x], mk_with_title_ptns)
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
                                    ref_title=temp_title
                                    ref_line_marker = mark
                                    ref_line_marker_ptn = mk_ptn
                        else:
                            ## No numeration
                            if found_part:
                                found_title = 1
                            else:
                                found_part = 1
                                ref_start_line = temp_ref_start_line
                                ref_title=temp_title
                    except IndexError:
                        ## References section title was on last line for some reason. Ignore
                        pass
            x = x - 1
    if ref_start_line is not None:
        ## return dictionary containing details of reference section:
        ref_sectn_details = { 'start_line' : ref_start_line,
                              'title_string' : ref_title,
                              'marker' : ref_line_marker,
                              'marker_pattern' : ref_line_marker_ptn,
                              'title_marker_same_line' : (title_marker_same_line is not None and 1) or (0)
                            }
    else:
        ref_sectn_details = None
    return ref_sectn_details

def find_reference_section_no_title(docbody):
    """This function would generally be used when it was not possible to locate the start of a
       document's reference section by means of its title.  Instead, this function will look for
       reference lines that have numeric markers of the format [1], [2], etc.
       @param docbody: (list) of strings - each string is a line in the document.
       @return: (dictionary) :
                 { 'start_line' : (integer) - index in docbody of first reference line,
                   'title_string' : (None) - title of the reference section None since no title,
                   'marker' : (string) - the marker of the first reference line,
                   'marker_pattern' : (string) - the regexp string used to find the marker,
                   'title_marker_same_line' : (integer) 0 - to signal title not on same line as
                                               marker.
                 }
                 Much of this information is used by later functions to rebuild a reference
                 section.
         -- OR --
                (None) - when the reference section could not be found.
    """
    ref_start_line = ref_line_marker = None
    if len(docbody) > 0:
        marker_patterns = get_first_reference_line_numeration_marker_patterns()

        ## try to find first reference line in the reference section:
        x = len(docbody) - 1
        found_ref_sect = 0
        while x >= 0 and not found_ref_sect:
            mark_match = perform_regex_match_upon_line_with_pattern_list(docbody[x], marker_patterns)
            if mark_match is not None and int(mark_match.group('num')) == 1:
                ## Get marker recognition pattern:
                mk_ptn = mark_match.re.pattern

                ## Look for [2] in next 10 lines:
                next_test_lines = 10
                y = x + 1
                temp_found = 0
                while y < len(docbody) and y < x + next_test_lines and not temp_found:
                    mark_match2 = perform_regex_match_upon_line_with_pattern_list(docbody[y], marker_patterns)
                    if (mark_match2 is not None) and (int(mark_match2.group('num')) == 2) and \
                           (mark_match.group('left') == mark_match2.group('left')) and (mark_match.group('right') == mark_match2.group('right')):
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


def find_end_of_reference_section(docbody, ref_start_line, ref_line_marker, ref_line_marker_ptn):
    """Given that the start of a document's reference section has already been recognised, this
       function is tasked with finding the line-number in the document of the last line of the
       reference section.
       @param docbody: (list) of strings - the entire plain-text document body.
       @param ref_start_line: (integer) - the index in docbody of the first line of the reference section.
       @param ref_line_marker: (string) - the line marker of the first reference line.
       @param ref_line_marker_ptn: (string) - the pattern used to search for a reference line marker.
       @return: (integer) - index in docbody of the last reference line
         -- OR --
                (None) - if ref_start_line was invalid.
    """
    section_ended = 0
    x = ref_start_line
    if (type(x) is not int) or (x < 0) or (x > len(docbody)) or (len(docbody)<1):
        ## The provided 'first line' of the reference section was invalid. Either it
        ## was out of bounds in the document body, or it was not a valid integer.
        ## Can't safely find end of refs with this info - quit! exit!
        return None
    ## Get patterns for testing line:
    t_patterns = get_post_reference_section_title_patterns()
    kw_patterns = get_post_reference_section_keyword_patterns()
    
    if None not in (ref_line_marker, ref_line_marker_ptn):
        mk_patterns = [sre.compile(ref_line_marker_ptn, sre.I|sre.UNICODE)]
    else:
        mk_patterns = get_reference_line_numeration_marker_patterns()
    garbage_digit_pattern = sre.compile(unicode(r'^\s*?([\+\-]?\d+?(\.\d+)?\s*?)+?\s*?$'), sre.UNICODE)

    while ( x < len(docbody)) and (not section_ended):
        ## look for a likely section title that would follow a reference section:
        end_match = perform_regex_search_upon_line_with_pattern_list(docbody[x], t_patterns)
        if end_match is None:
            ## didn't match a section title - try looking for keywords that suggest the end of a reference section:
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
            ## Does this & the next 5 lines simply contain numbers? If yes, it's probably the axis
            ## scale of a graph in a fig. End refs section
            dm = garbage_digit_pattern.match(docbody[x])
            if dm is not None:
                y = x + 1
                digit_lines = 4
                num_digit_lines = 1
                while(y < x + digit_lines) and (y < len(docbody)):
                    dm = garbage_digit_pattern.match(docbody[y])
                    if dm is not None:
                        num_digit_lines += 1
                    y = y + 1
                if num_digit_lines == digit_lines:
                    section_ended = 1
            x = x + 1
    return x - 1

## ----> 3. Found reference section - now take out lines and rebuild them:

def test_for_blank_lines_separating_reference_lines(ref_sect):
    """Test to see if reference lines are separated by blank lines so that these can be used
       to rebuild reference lines.
       @param ref_sect: (list) of strings - the reference section.
       @return: (int) 0 if blank lines do not separate reference lines; 1 if they do.
    """
    num_blanks = 0            ## Number of blank lines found between non-blanks
    num_lines = 0             ## Number of reference lines separated by blanks
    blank_line_separators = 0 ## Flag to indicate whether blanks lines separate ref lines
    multi_nonblanks_found = 0 ## Flag to indicate whether multiple nonblank lines are found together (used because
                              ## if line is dbl-spaced, it isnt a blank that separates refs & can't be relied upon)
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
            while x< len(ref_sect) and ref_sect[x].isspace():
                x = x + 1
            if x == len(ref_sect):
                ## Blanks at end doc: dont count
                num_blanks -= 1
            x = x - 1
        x = x + 1
    ## Now from the number of blank lines & the number of text lines, if num_lines > 3, & num_blanks = num_lines,
    ## or num_blanks = num_lines - 1, then we have blank line separators between reference lines
    if (num_lines > 3) and ((num_blanks == num_lines) or (num_blanks == num_lines - 1)) and (multi_nonblanks_found):
        blank_line_separators = 1
    return blank_line_separators


def remove_leading_garbage_lines_from_reference_section(ref_sectn):
    """Sometimes, the first lines of the extracted references are completely blank or email addresses.
       These must be removed as they are not references.
       @param ref_sectn: (list) of strings - the reference section lines
       @return: (list) of strings - the reference section without leading blank lines or email addresses.
    """
    p_email = re.compile(unicode(r'^\s*e\-?mail'), re.UNICODE)
    while (len(ref_sectn) > 0) and (ref_sectn[0].isspace() or p_email.match(ref_sectn[0]) is not None):
        ref_sectn[0:1] = []
    return ref_sectn

def correct_rebuilt_lines(rebuilt_lines, p_refmarker):
    """Try to correct any cases where a reference line has been incorrectly split based upon
       a wrong numeration marker. That is to say, given the following situation:

       [1] Smith, J blah blah
       [2] Brown, N blah blah see reference
       [56] for more info [3] Wills, A blah blah
       ...

       The first part of the 3rd line clearly belongs with line 2. This function will try to fix this situation,
       to have the following situation:

       [1] Smith, J blah blah
       [2] Brown, N blah blah see reference [56] for more info
       [3] Wills, A blah blah

       If it cannot correctly guess the correct break-point in such a line, it will give up and the original
       list of reference lines will be returned.

       @param rebuilt_lines: (list) the rebuilt reference lines
       @param p_refmarker: (compiled regex pattern object) the pattern used to match regex line numeration
        markers. **MUST HAVE A GROUP 'marknum' to encapsulate the mark number!** (e.g. r'\[(?P<marknum>\d+)\]')
       @return: (list) of strings. If necessary, the corrected reference lines. Else the orginal 'rebuilt' lines.
    """
    fixed = []
    unsafe = 0
    try:
        m = p_refmarker.match(rebuilt_lines[0])
        last_marknum = int(m.group("marknum"))
        if last_marknum != 1:
            ## Even the first mark isnt 1 - probaby too dangerous to try to repair
            return rebuilt_lines
    except (IndexError, AttributeError, ValueError):
        ## Sometihng went wrong. Either no references, not a numbered line marker (int() failed), or
        ## no reference line marker (NoneType was passed). In any case, unable to test for correct
        ## reference line numberring - just return the lines as they were.
        return rebuilt_lines

    ## Loop through each line in "rebuilt_lines" and test the mark at the beginning.
    ## If current-line-mark = previous-line-mark + 1, the line will be taken to be correct and appended
    ## to the list of fixed-lines. If not, then the loop will attempt to test whether the current line
    ## marker is actually part of the previous line by looking in the current line for another marker
    ## that has the numeric value of previous-marker + 1. If found, that marker will be taken as the true
    ## marker for the line and the leader of the line (up to the point of this marker) will be appended
    ## to the revious line. E.g.:
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
    try:
        for x in xrange(1, len(rebuilt_lines)):
            m = p_refmarker.match(rebuilt_lines[x])
            try:
                if int(m.group("marknum")) == last_marknum + 1:
                    ## The marker number for this reference line is correct.
                    ## Append it to the 'fixed' lines and move on.
                    fixed.append(rebuilt_lines[x])
                    last_marknum += 1
                    continue
                elif len(rebuilt_lines[x][m.end():].strip()) == 0:
                    ## This line consists of a marker-number only - it is not a
                    ## correct marker. Append it to the last line.
                    fixed[len(fixed) - 1] += rebuilt_lines[x]
                    continue
                else:
                    ## This marker != previous-marker + 1.
                    ## May have taken some of the last line into this line. Can we find the
                    ## next marker in this line?
                    ## Test for this situation:
                    ## [54] for more info [3] Wills, A blah blah
                    m_fix = p_refmarker.search(rebuilt_lines[x][m.end():])

                    if m_fix is not None and int(m_fix.group("marknum")) == last_marknum + 1:
                        ## found next marker in line. Test to see that marker is followed by
                        ## something meaningful i.e. a letter at least (name).
                        ## I.e. We want to fix this:
                        ## [54] for more info [3] Wills, A blah blah
                        ##
                        ## but we don't want to fix this:
                        ## [54] for more info or even reference [3]
                        ##
                        ## as that would be unsafe.
                        m_test_nxt_mark_not_eol = \
                          re.search(re.escape(m_fix.group()) + '\s*[A-Za-z]', rebuilt_lines[x])
                        if m_test_nxt_mark_not_eol is not None:
                            ## move this section back to its real line:

                            ## get the segment of this line to be moved to the previous line
                            ## (append a newline to it too):
                            movesect = rebuilt_lines[x][0:m_test_nxt_mark_not_eol.start()] + "\n"

                            ## Now get the previous line into a variable (without its newline at the end):
                            previous_line = fixed[len(fixed) - 1].rstrip("\n")

                            ## Now append the section to be moved to the previous line variable.
                            ## Check the last character of the previous line. If it's a space, then
                            ## just directly append this new section. Else, append a space then this new section.
                            previous_line += "%s%s" % ((previous_line[len(previous_line) - 1] != " " and " ") or (""), movesect)

                            fixed[len(fixed) - 1] = previous_line

                            ## Now append the remainder of the current line to the list of fixed lines, and move on to the
                            ## next line:
                            fixed.append(rebuilt_lines[x][m_test_nxt_mark_not_eol.start():])
                            
                            last_marknum += 1
                            continue
                        else:
                            ## The next marker in the line was not followed by text. It is unsafe to move it.
                            ## Give up trying to correct these reference lines - it's not safe to continue.
                            unsafe = 1
                            break
                    else:
                        ## Unable to find another marker in the line that starts with the incorrect marker.
                        ## It is therefore unsafe to attempt to correct the lines: just return the original lines.
                        unsafe = 1
                        break
            except AttributeError:
                ## This line does not have a line marker at the start! This line shall be added to the end of the previous line.
                fixed[len(fixed) - 1] += rebuilt_lines[x]
                continue
    except IndexError:
        ## Somewhere, the boundaries of the list of references were over-stepped. Just return the original set of reference lines.
        unsafe = 1
    if unsafe:
        ## return the original set of references.
        return rebuilt_lines
    else:
        ## return the newly corrected references.
        return fixed

def wash_and_repair_reference_line(line):
    """Wash a reference line of undesirable characters (such as poorly-encoded letters, etc),
       and repair any errors (such as broken URLs) if possible.
       @param line: (string) the reference line to be washed/repaired.
       @return: (string) the washed reference line.
    """
    ## repair URLs in line:
    line = repair_broken_urls(line)
    ## Replace various undesirable characters with their alternatives:
    line = replace_undesirable_characters(line)
    ## remove instances of multiple spaces from line, replacing with a single space:
    line = sre_multiple_space.sub(u' ', line)
    return line

def rebuild_reference_lines(ref_sectn, ref_line_marker_ptn):
    """Given a reference section, rebuild the reference lines. After translation from PDF to text,
       reference lines are often broken. This is because pdftotext doesn't know what is a wrapped-
       line and what is a genuine new line. As a result, the following 2 reference lines:
        [1] See http://cdsware.cern.ch/ for more details.
        [2] Example, AN: private communication (1996).
       ...could be broken into the following 4 lines during translation from PDF to plaintext:
        [1] See http://cdsware.cern.ch/ fo
        r more details.
        [2] Example, AN: private communica
        tion (1996).
       Such a situation could lead to a citation being separated across 'lines', meaning that it
       wouldn't be correctly recognised.
       This function tries to rebuild the reference lines. It uses the pattern used to recognise a
       reference line's numeration marker to indicate the start of a line. If no reference line
       numeration was recognised, it will simply join all lines together into one large reference line.
       @param ref_sectn: (list) of strings. The (potentially broken) reference lines.
       @param ref_line_marker_ptn: (string) - the pattern used to recognise a reference line's
        numeration marker.
       @return: (list) of strings - the rebuilt reference section. Each string in the list
        represents a complete reference line.
    """
    ## initialise some vars:
    rebuilt_references = []
    working_line = u''

    len_ref_sectn = len(ref_sectn)
    
    if ref_line_marker_ptn is None or type(ref_line_marker_ptn) not in (str, unicode):
        if test_for_blank_lines_separating_reference_lines(ref_sectn):
            ## Use blank lines to separate ref lines
            ref_line_marker_ptn = unicode(r'^\s*$')
        else:
            ## No ref line dividers: unmatchable pattern
            ref_line_marker_ptn = unicode(r'^A$^A$$')
    p_ref_line_marker = re.compile(ref_line_marker_ptn, re.I|re.UNICODE)

    for x in xrange(len_ref_sectn - 1, -1, -1):
        current_string = ref_sectn[x].strip()
        m_ref_line_marker = p_ref_line_marker.match(current_string)
        if m_ref_line_marker is not None:
            ## Ref line start marker
            if current_string == '':
                ## Blank line to separate refs. Append the current working line to the refs list
                working_line = working_line.rstrip()
                working_line = wash_and_repair_reference_line(working_line)
                rebuilt_references.append(working_line)
                working_line = u''
            else:
                if current_string[len(current_string) - 1] in (u'-', u' '):
                    ## space or hyphenated word at the end of the line - don't add in a space
                    working_line = current_string + working_line
                else:
                    ## no space or hyphenated word at the end of this line - add in a space
                    working_line = current_string + u' ' + working_line
                working_line = working_line.rstrip()
                working_line = wash_and_repair_reference_line(working_line)
                rebuilt_references.append(working_line)
                working_line = u''
        else:
            if current_string != u'':
                ## Continuation of line
                if current_string[len(current_string) - 1] in (u'-', u' '):
                    ## space or hyphenated word at the end of the line - don't add in a space
                    working_line = current_string + working_line
                else:
                    ## no space or hyphenated word at the end of this line - add in a space
                    working_line = current_string + u' ' + working_line
    
    if working_line != u'':
        ## Append last line
        working_line = working_line.rstrip()
        working_line = wash_and_repair_reference_line(working_line)
        rebuilt_references.append(working_line)

    ## a list of reference lines has been built backwards - reverse it:
    rebuilt_references.reverse()

    rebuilt_references = correct_rebuilt_lines(rebuilt_references, p_ref_line_marker)
    return rebuilt_references

def get_reference_lines(docbody, ref_sect_start_line, ref_sect_end_line, \
                        ref_sect_title, ref_line_marker_ptn, title_marker_same_line):
    """After the reference section of a document has been identified, and the first and last lines
       of the reference section have been recorded, this function is called to take the reference
       lines out of the document body. The document's reference lines are returned in a list of
       strings whereby each string is a reference line. Before this can be done however, the
       reference section is passed to another function that rebuilds any broken reference lines.
       @param docbody: (list) of strings - the entire document body.
       @param ref_sect_start_line: (integer) - the index in docbody of the first reference line.
       @param ref_sect_end_line: (integer) - the index in docbody of the last reference line.
       @param ref_sect_title: (string) - the title of the reference section (e.g. "References").
       @param ref_line_marker_ptn: (string) - the patern used to match the marker for each
        reference line (e.g., could be used to match lines with markers of the form [1], [2], etc.)
       @param title_marker_same_line: (integer) - a flag to indicate whether or not the reference
        section title was on the same line as the first reference line's marker.
       @return: (list) of strings. Each string is a reference line, extracted from the document.
    """
    start_idx = ref_sect_start_line
    if title_marker_same_line:
        ## Title on same line as 1st ref- take title out!
        title_start = docbody[start_idx].find(ref_sect_title)
        if title_start != -1:
            docbody[start_idx] = docbody[start_idx][title_start + len(ref_sect_title):]
    elif ref_sect_title is not None:
        ## Pass title line
        start_idx += 1

    ## now rebuild reference lines:
    if type(ref_sect_end_line) is int:
        ref_lines = rebuild_reference_lines(docbody[start_idx:ref_sect_end_line+1], ref_line_marker_ptn)
    else:
        ref_lines = rebuild_reference_lines(docbody[start_idx:], ref_line_marker_ptn)
    return ref_lines


## ----> Glue - logic for finding and extracting reference section:

def extract_references_from_fulltext(fulltext):
    """Locate and extract the reference section from a fulltext document.
       Return the extracted reference section as a list of strings, whereby each
       string in the list is considered to be a single reference line.
        E.g. a string could be something like:
        '[19] Wilson, A. Unpublished (1986).
       @param fulltext: (list) of strings, whereby each string is a line of the document.
       @return: (list) of strings, where each string is an extracted reference line.
    """
    ## Try to remove pagebreaks, headers, footers
    fulltext = remove_page_boundary_lines(fulltext)

    ## Find start of refs section:
    ref_sect_start = find_reference_section(fulltext)
    if ref_sect_start is None:
        ## No references found
        ref_sect_start = find_reference_section_no_title(fulltext)
    if ref_sect_start is None:
        ## No References
        refs = []
    else:
        ref_sect_end = find_end_of_reference_section(fulltext, ref_sect_start["start_line"], \
                                                     ref_sect_start["marker"], ref_sect_start["marker_pattern"])
        if ref_sect_end is None:
            ## No End to refs? Not safe to extract
            refs = []
        else:
            ## Extract
            refs = get_reference_lines(fulltext, ref_sect_start["start_line"], ref_sect_end, \
                                       ref_sect_start["title_string"], ref_sect_start["marker_pattern"], \
                                       ref_sect_start["title_marker_same_line"])
    return refs


## Tasks related to conversion of full-text to plain-text:

def _pdftotext_conversion_is_bad(txtlines):
    """Sometimes pdftotext performs a bad conversion which consists of many spaces and garbage characters.
       This method takes a list of strings obtained from a pdftotext conversion and examines them to see if
       they are likely to be the result of a bad conversion.
       @param txtlines: (list) of unicode strings obtained from pdftotext conversion.
       @return: (integer) - 1 if bad conversion; 0 if good conversion.
    """
    ## Numbers of 'words' and 'whitespaces' found in document:
    numWords = numSpaces = 0
    ## whitespace line pattern:
    ws_patt = re.compile(unicode(r'^\s+$'), re.UNICODE)
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
    """Take the path to a PDF file and run pdftotext for this file, capturing the
       output.
       @param fpath: (string) path to the PDF file
       @return: (list) of unicode strings (contents of the PDF file translated into plaintext;
        each string is a line in the document.)
    """
    doclines = []
    ## build pdftotext command:
    cmd_pdftotext = """%(pdftotext)s -raw -q -enc UTF-8 %(filepath)s -""" % { 'pdftotext' : CFG_PATH_PDFTOTEXT,
                                                                              'filepath'  : fpath }
    ## open pipe to pdftotext:
    pipe_pdftotext = os.popen("%s" % cmd_pdftotext, 'r')
    ## read back results:
    for docline in pipe_pdftotext:
        doclines.append(docline.decode("utf-8"))
    ## close pipe to pdftotext:
    pipe_pdftotext.close()

    ## finally, check conversion result not bad:
    if _pdftotext_conversion_is_bad(doclines):
        doclines = []
    return doclines

def convert_document_to_plaintext(fpath):
    """Given the path to a file, convert it to plaintext and return the content as a list, whereby
       each line of text in the document file is a string in the list.
       @param fpath: (string) the path to the file to be converted to text
       @return: list of strings (the plaintext body of the file)
    """
    doc_plaintext = []
    pipe_gfile = os.popen("%s %s" % (CFG_PATH_GFILE, fpath), "r")
    res_gfile = pipe_gfile.readline()
    pipe_gfile.close()
    if res_gfile.lower().find("pdf") != -1:
        ## convert from PDF
        doc_plaintext = convert_PDF_to_plaintext(fpath)
    return doc_plaintext

def get_plaintext_document_body(fpath):
    """Given a file-path to a full-text, return a list of unicode strings whereby each string
       is a line of the fulltext.
       In the case of a plain-text document, this simply means reading the contents in from the
       file.  In the case of a PDF/PostScript however, this means converting the document to
       plaintext.
       @param: fpath: (string) - the path to the fulltext file
       @return: (list) of strings - each string being a line in the document.
    """
    textbody = []
    if os.access(fpath, os.F_OK|os.R_OK):
        # filepath OK - attempt to extract references:
        ## get file type:
        pipe_gfile = os.popen("%s %s" % (CFG_PATH_GFILE, fpath), "r")
        res_gfile = pipe_gfile.readline()
        pipe_gfile.close()
        
        if res_gfile.lower().find("text") != -1 and \
           res_gfile.lower().find("postscript") == -1 and \
           res_gfile.lower().find("pdf") == -1:
            ## plain-text file: don't convert - just read in:
            #textbody = open("%s" % fpath, "r").readlines()
            textbody = []
            for line in open("%s" % fpath, "r").readlines():
                textbody.append(line.decode("utf-8"))
        else:
            ## assume file needs to be converted to text:
            textbody = convert_document_to_plaintext(fpath)
    else:
        ## filepath not OK
        raise IOError("Could not find file %s" % fpath)
    return textbody

def write_raw_references_to_stream(recid, raw_refs, strm=None):
    """Write a lost of raw reference lines to the a given stream.
       Each reference line is preceeded by the record-id. Thus, if for example,
       the following 2 reference lines were passed to this function:
        [1] See http://cdsware.cern.ch/ for more details.
        [2] Example, AN: private communication (1996).
       and the record-id was "1", the raw reference lines printed to the stream would be:
        1:[1] See http://cdsware.cern.ch/ for more details.
        1:[2] Example, AN: private communication (1996).
       @param recid: (string) the record-id of the document for which raw references are
        to be written-out.
       @param raw_refs: (list) of strings. The raw references to be written-out.
       @param strm: (open stream object) - the stream object to which the references are to be
        written. If the stream object is not a valid open stream (or is None, by default), the
        standard error stream (sys.stderr) will be used by default.
       @return: None.
    """
    if strm is None:
        ## no stream supplied - write to sys.stderr
        strm = sys.stderr
    try:
        ## check that stream is open:
        strm.flush()
    except:
        ## it isn't - default to sys.stderr
        strm = sys.stderr
    strm.writelines(map(lambda x: "%(recid)s:%(refline)s\n" % { 'recid' : recid, 'refline' : x.encode("utf-8") }, raw_refs))
    strm.flush()

def usage(wmsg="", err_code=0):
    """Display a usage message for refextract on the standard error stream and then exit.
       @param wmsg: (string) - some kind of warning message for the user.
       @param err_code: (integer) - an error code to be passed to sys.exit, which is called
        after the usage message has been printed.
       @return: None.
    """
    if wmsg != "":
        wmsg = wmsg.strip() + "\n"
    msg = """Usage: refextract [options] recid:file1 [recid:file2 ...]
  refextract tries to extract the reference section from a full-text document.
  Extracted reference lines are processed and any recognised citations are marked
  up using MARC XML. Results are output to the standard output stream.
  
  Options: 
   -h, --help     print this help
   -V, --version  print version information
   -v, --verbose  verbosity level (0=mute, 1=default info msg,
		  2=display reference section extraction analysis,
                  3=display reference line citation processing analysis, 
		  9=max information)
   -r, --output-raw-refs
                  output raw references, as extracted from the document. No MARC XML
                  mark-up - just each extracted line, prefixed by the recid of the document
                  that it came from.
   -z, --raw-references
                  treat the input file as pure references. i.e. skip the stage of trying to
                  locate the reference section within a document and instead move to the
                  stage of recognition and standardisation of citations within lines.

  Example: refextract 499:thesis.pdf
"""
    sys.stderr.write(wmsg + msg)
    sys.exit(err_code)

def get_cli_options():
    """Get the various arguments and options from the command line and populate
       a dictionary of cli_options.
       @return: (tuple) of 2 elements. First element is a dictionary of cli options and
        flags, set as appropriate; Second element is a list of cli arguments.
    """
    ## dictionary of important flags and values relating to cli call of program:
    cli_opts = { 'treat_as_reference_section' : 0,
                 'output_raw'                 : 0,
                 'verbosity'                  : 0,
               }

    try:
        myoptions, myargs = getopt.getopt(sys.argv[1:], "hVv:zr", \
                                          ["help",
                                           "version",
                                           "verbose=",
                                           "raw-references",
                                           "output-raw-refs"])
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
        elif o[0] in ("-z", "--raw-citations"):
            ## treat input as pure reference lines:
            cli_opts['treat_as_reference_section'] = 1

    if len(myargs) == 0:
        ## no arguments: error message
        usage(wmsg="Error: no full-text.")

    return (cli_opts, myargs)

def display_xml_record(status_code, count_reportnum,
                       count_title, count_url, count_misc, recid, xml_lines):
    """Given a series of MARC XML-ized reference lines and a record-id, write a
       MARC XML record to the stdout stream. Include in the record some stats for
       the extraction job.
       The printed MARC XML record will essentially take the following structure:
        <record>
           <controlfield tag="001">1</controlfield>
           <datafield tag="999" ind1="C" ind2="5">
              ...
           </datafield>
           [...]
           <datafield tag="999" ind1="C" ind2="6">
              <subfield code="a">
                CDS Invenio/0.92.0 refextract/0.92.0-timestamp-error-reportnum-title-URL-misc
              </subfield>
           </datafield>
        </record>
       Timestamp, error(code), reportnum, title, URL, and misc will are of course take
       the relevant values.

       @param status_code: (integer)the status of reference-extraction for the given
        record: was there an error or not? 0 = no error; 1 = error.
       @param count_reportnum: (integer) - the number of institutional report-number
        citations found in the document's reference lines.
       @param count_title: (integer) - the number of journal title citations found
        in the document's reference lines.
       @param count_url: (integer) - the number of URL citations found in the
        document's reference lines.
       @param count_misc: (integer) - the number of sections of miscellaneous text
        (i.e. 999C5$m) from the document's reference lines.
       @param recid: (string) - the record-id of the given document. (put into 001
        field.)
       @param xml_lines: (list) of strings. Each string in the list contains a group
        of MARC XML 999C5 dtafields, making up a single reference line. These reference
        lines will make up the document body.
       @return: None
    """
    ## Start with the opening record tag:
    out = u"%(record-open)s\n" % { 'record-open' : CFG_REFEXTRACT_XML_RECORD_OPEN, }

    ## Display the record-id controlfield:
    out += u"""   <controlfield tag="%(cf-tag-recid)s">%(recid)s</controlfield>\n""" \
            % { 'cf-tag-recid' : CFG_REFEXTRACT_CTRL_FIELD_RECID,
                'recid'        : cgi.escape(recid, 1),
              }

    ## Loop through all xml lines and add them to the output string:
    for line in xml_lines:
        out += line

    ## add the 999C6 status subfields:
    out += u"""   <datafield tag="%(df-tag-ref-stats)s" ind1="%(df-ind1-ref-stats)s" ind2="%(df-ind2-ref-stats)s">
      <subfield code="%(sf-code-ref-stats)s">%(version)s-%(timestamp)s-%(status)s-%(reportnum)s-%(title)s-%(url)s-%(misc)s</subfield>
   </datafield>\n""" % { 'df-tag-ref-stats'  : CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS,
                         'df-ind1-ref-stats' : CFG_REFEXTRACT_IND1_EXTRACTION_STATS,
                         'df-ind2-ref-stats' : CFG_REFEXTRACT_IND2_EXTRACTION_STATS,
                         'sf-code-ref-stats' : CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS,
                         'version'           : CFG_REFEXTRACT_VERSION,
                         'timestamp'         : str(int(mktime(localtime()))),
                         'status'            : status_code,
                         'reportnum'         : count_reportnum,
                         'title'             : count_title,
                         'url'               : count_url,
                         'misc'              : count_misc,
                       }

    ## Now add the closing tag to the record:
    out += u"%(record-close)s\n" % { 'record-close' : CFG_REFEXTRACT_XML_RECORD_CLOSE, }

    ## Write the record to the standard output stream:
    sys.stdout.write("%s" % (out.encode("utf-8"),))
    sys.stdout.flush()
    return


def main():
    """Main function.
    """
    (cli_opts, cli_args) =  get_cli_options()

    extract_jobs = get_recids_and_filepaths(cli_args)
    if len(extract_jobs) == 0:
        ## no files provided for reference extraction - error message
        usage()

    ## Read the journal titles knowledge base, creating the search patterns and replace terms:
    (title_search_kb, title_search_standardised_titles, title_search_keys) = \
                     build_titles_knowledge_base(CFG_REFEXTRACT_KB_JOURNAL_TITLES)
    (preprint_reportnum_sre, standardised_preprint_reportnum_categs) = \
                     build_institutes_preprints_numeration_knowledge_base(CFG_REFEXTRACT_KB_REPORT_NUMBERS)

    done_coltags = 0 ## flag to signal that the XML collection tags have been output

    for curitem in extract_jobs:
        extract_error = 0  ## extraction was OK unless determined otherwise
        ## reset the stats counters:
        count_misc = count_title = count_reportnum = count_url = 0
        recid = curitem[0]

        if not done_coltags:
            ## Output opening XML collection tags:
            sys.stdout.write("%s\n" % (CFG_REFEXTRACT_XML_VERSION.encode("utf-8"),))
            sys.stdout.write("%s\n" % (CFG_REFEXTRACT_XML_COLLECTION_OPEN.encode("utf-8"),))
            done_coltags = 1

        ## 1. Get this document body as plaintext:
        docbody = get_plaintext_document_body(curitem[1])

        if len(docbody) > 0:
            ## the document body is not empty:
            ## 2. If necessary, locate the reference section:
            if cli_opts['treat_as_reference_section']:
                ## don't search for citations in the document body: treat it as a reference section:
                reflines = docbody
            else:
                ## launch search for the reference section in the document body:
                reflines = extract_references_from_fulltext(docbody)
                

            ## 3. Standardise the reference lines:
#            reflines = test_get_reference_lines()
            (processed_references, count_misc, \
             count_title, count_reportnum, count_url) = \
              create_marc_xml_reference_section(reflines,
                                                preprint_repnum_search_kb=preprint_reportnum_sre,
                                                preprint_repnum_standardised_categs=\
                                                      standardised_preprint_reportnum_categs,
                                                periodical_title_search_kb=title_search_kb,
                                                standardised_periodical_titles=title_search_standardised_titles,
                                                periodical_title_search_keys=title_search_keys)
        else:
            ## document body is empty, therefore the reference section is empty:
            reflines = []
            processed_references = []

        ## 4. Display the extracted references, status codes, etc:
        if cli_opts['output_raw']:
            ## now write the raw references to the stream:
            write_raw_references_to_stream(recid, reflines, sys.stderr)

        ## Display the processed reference lines:
        display_xml_record(extract_error, count_reportnum,
                           count_title, count_url, count_misc, recid, processed_references)
    ## If an XML collection was opened, display closing tag
    if done_coltags:
        sys.stdout.write("%s\n" % (CFG_REFEXTRACT_XML_COLLECTION_CLOSE.encode("utf-8"),))





def test_get_reference_lines():
    """Returns some test reference lines.
       @return: (list) of strings - the test reference lines. Each
        string in the list is a reference line that should be processed.
    """
    reflines = ["""[1] J. Maldacena, Adv. Theor. Math. Phys. 2 (1998) 231; hep-th/9711200. http://cdsweb.cern.ch/""",
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
                """[36] whatever http://cdsware.cern.ch/""",
                """[37] some misc  lkjslkdjlksjflksj [hep-th/9804058] lkjlkjlkjlkj [hep-th/0001567], hep-th/1212321, some more misc, Nucl. Phys. B546 (1999) 96""",
                """[38] R. Emparan, C. Johnson and R.... Myers, Phys. Rev. D60 (1999) 104001; this is :: .... misc! hep-th/9903238. and some ...,.,.,.,::: more hep-ph/9912000""",
                ]
    return reflines
