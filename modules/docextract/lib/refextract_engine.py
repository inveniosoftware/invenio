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

import sys
import re
import os
import subprocess

from invenio.refextract_config import \
            CFG_REFEXTRACT_XML_VERSION, \
            CFG_REFEXTRACT_XML_COLLECTION_OPEN, \
            CFG_REFEXTRACT_XML_COLLECTION_CLOSE, \
            CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM, \
            CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL, \
            CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, \
            CFG_REFEXTRACT_MARKER_CLOSING_VOLUME, \
            CFG_REFEXTRACT_MARKER_CLOSING_YEAR, \
            CFG_REFEXTRACT_MARKER_CLOSING_PAGE, \
            CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID, \
            CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL, \
            CFG_REFEXTRACT_MARKER_CLOSING_TITLE, \
            CFG_REFEXTRACT_MARKER_CLOSING_SERIES
try:
    from invenio.config import CFG_INSPIRE_SITE
except ImportError:
    CFG_INSPIRE_SITE = False

# make refextract runnable without requiring the full Invenio installation:
from invenio.config import CFG_PATH_GFILE

from invenio.refextract_find import get_reference_section_beginning
from invenio.refextract_text import rebuild_reference_lines
from invenio.refextract_tag import tag_reference_line, \
    sum_2_dictionaries, identify_and_tag_DOI, identify_and_tag_URLs
from invenio.refextract_text import extract_references_from_fulltext
from invenio.refextract_xml import create_xml_record, \
                                   build_formatted_xml_citation
from invenio.docextract_pdf import convert_PDF_to_plaintext
from invenio.docextract_utils import write_message
from invenio.refextract_cli import halt
from invenio.refextract_kbs import get_kbs
from invenio.refextract_re import get_reference_line_numeration_marker_patterns, \
                                  regex_match_list, \
                                  re_tagged_citation, \
                                  re_numeration_no_ibid_txt, \
                                  re_roman_numbers, \
                                  re_recognised_numeration_for_title_plus_series


description = """
Refextract tries to extract the reference section from a full-text document.
Extracted reference lines are processed and any recognised citations are
marked up using MARC XML. Recognises author names, URL's, DOI's, and also
journal titles and report numbers as per the relevant knowledge bases. Results
are output to the standard output stream as default, or instead to an xml file.

"""

# General initiation tasks:

# components relating to the standardisation and
# recognition of citations in reference lines:


def limit_m_tags(xml_file, length_limit):
    """Limit size of miscellaneous tags"""
    temp_xml_file = xml_file + '.temp'
    try:
        ofilehdl = open(xml_file, 'r')
    except IOError:
        write_message("***%s\n" % xml_file, verbose=0)
        halt(err=IOError, msg="Error: Unable to read from '%s'" % xml_file,
             exit_code=1)
    try:
        nfilehdl = open(temp_xml_file, 'w')
    except IOError:
        write_message("***%s\n" % temp_xml_file, verbose=0)
        halt(err=IOError, msg="Error: Unable to write to '%s'" % temp_xml_file,
             exit_code=1)

    for line in ofilehdl:
        line_dec = line.decode("utf-8")
        start_ind = line_dec.find('<subfield code="m">')
        if start_ind != -1:
            # This line is an "m" line:
            last_ind = line_dec.find('</subfield>')
            if last_ind != -1:
                # This line contains the end-tag for the "m" section
                leng = last_ind - start_ind - 19
                if leng > length_limit:
                    # want to truncate on a blank to avoid problems..
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
    # copy back to original file name
    os.rename(temp_xml_file, xml_file)


def remove_reference_line_marker(line):
    """Trim a reference line's 'marker' from the beginning of the line.
       @param line: (string) - the reference line.
       @return: (tuple) containing two strings:
                 + The reference line's marker (or if there was not one,
                   a 'space' character.
                 + The reference line with it's marker removed from the
                   beginning.
    """
    # Get patterns to identify reference-line marker patterns:
    marker_patterns = get_reference_line_numeration_marker_patterns()
    line = line.lstrip()

    marker_match = regex_match_list(line, marker_patterns)

    if marker_match is not None:
        # found a marker:
        marker_val = marker_match.group(u'mark')
        # trim the marker from the start of the line:
        line = line[marker_match.end():].lstrip()
    else:
        marker_val = u" "
    return (marker_val, line)


def roman2arabic(num):
    """Convert numbers from roman to arabic

    This function expects a string like XXII
    and outputs an integer
    """
    t = 0
    p = 0
    for r in num:
        n = 10 ** (205558 % ord(r) % 7) % 9995
        t += n - 2 * p % n
        p = n
    return t


## Transformations

def format_volume(citation_elements):
    """format volume number (roman numbers to arabic)

    When the volume number is expressed in roman numbers (CXXII),
    they are converted to their equivalent in arabic numbers (42)
    """
    re_roman = re.compile(re_roman_numbers + u'$', re.UNICODE)
    for el in citation_elements:
        if el['type'] == 'JOURNAL' and re_roman.match(el['volume']):
            el['volume'] = str(roman2arabic(el['volume'].upper()))
    return citation_elements


def handle_special_journals(citation_elements, kbs):
    """format special journals (like JHEP) volume number

    JHEP needs the volume number prefixed with the year
    e.g. JHEP 0301 instead of JHEP 01
    """
    for el in citation_elements:
        if el['type'] == 'JOURNAL' and el['title'] in kbs['special_journals'] \
                and re.match('\d{1,2}$', el['volume']):

            # Sometimes the page is omitted and the year is written in its place
            # We can never be sure but it's very likely that page > 1900 is
            # actually a year
            if el['year'] == '' and re.match('(19|20)\d{2}$', el['page']):
                el['year'] = el['page']
                el['page'] = '1'

            el['volume'] = el['year'][-2:] + '%02d' % int(el['volume'])

    return citation_elements


def format_report_number(citation_elements):
    """Format report numbers that are missing a dash

    e.g. CERN-LCHH2003-01 to CERN-LHCC-2003-01
    """
    re_report = re.compile(ur'^(?P<name>[A-Z-]+)(?P<nums>[\d-]+)$', re.UNICODE)
    for el in citation_elements:
        if el['type'] == 'REPORTNUMBER':
            m = re_report.match(el['report_num'])
            if m:
                name = m.group('name')
                if not name.endswith('-'):
                    el['report_num'] = m.group('name') + '-' + m.group('nums')
    return citation_elements


def format_hep(citation_elements):
    """Format hep-th report numbers with a dash

    e.g. replaces hep-th-9711200 with hep-th/9711200
    """
    prefixes = ('astro-ph-', 'hep-th-', 'hep-ph-', 'hep-ex-', 'hep-lat-')
    for el in citation_elements:
        if el['type'] == 'REPORTNUMBER':
            for p in prefixes:
                if el['report_num'].startswith(p):
                    el['report_num'] = el['report_num'][:len(p) - 1] + '/' + \
                                                    el['report_num'][len(p):]
    return citation_elements


def format_author_ed(citation_elements):
    for el in citation_elements:
        if el['type'] == 'AUTH':
            el['auth_txt'] = el['auth_txt'].replace('(ed. )', '(ed.)')
            el['auth_txt'] = el['auth_txt'].replace('(eds. )', '(eds.)')
    return citation_elements


def look_for_books(citation_elements, kbs):
    authors = None
    title   = None
    for el in citation_elements:
        if el['type'] == 'AUTH':
            authors = el
            break
    for el in citation_elements:
        if el['type'] == 'QUOTED':
            title = el
            break

    if authors and title:
        if title['title'].upper() in kbs['books']:
            line = kbs['books'][title['title'].upper()]
            el = {'type': 'BOOK',
                  'misc_txt': '',
                  'authors': line[0],
                  'title': line[1],
                  'year': line[2].strip(';')}
            citation_elements.append(el)
            citation_elements.remove(title)

    return citation_elements


def split_volume_from_journal(citation_elements):
    for el in citation_elements:
        if el['type'] == 'JOURNAL' and ';' in el['title']:
            el['title'], series = el['title'].rsplit(';', 1)
            el['volume'] = series + el['volume']
    return citation_elements


## End of elements transformations


def parse_reference_line(ref_line, kbs, bad_titles_count={}):
    """Parse one reference line

    @input a string representing a single reference bullet
    @output parsed references (a list of elements objects)
    """
    # Strip the 'marker' (e.g. [1]) from this reference line:
    (line_marker, ref_line) = remove_reference_line_marker(ref_line)
    # Find DOI sections in citation
    (ref_line, identified_dois) = identify_and_tag_DOI(ref_line)
    # Identify and replace URLs in the line:
    (ref_line, identified_urls) = identify_and_tag_URLs(ref_line)
    # Tag <cds.JOURNAL>, etc.
    tagged_line, bad_titles_count = tag_reference_line(ref_line,
                                                       kbs,
                                                       bad_titles_count)

    # Debug print tagging (authors, titles, volumes, etc.)
    write_message('  * tags %r' % tagged_line, verbose=9)

    # Using the recorded information, create a MARC XML representation
    # of the rebuilt line:
    # At the same time, get stats of citations found in the reference line
    # (titles, urls, etc):
    citation_elements, line_marker, counts = \
        parse_tagged_reference_line(line_marker,
                                    tagged_line,
                                    identified_dois,
                                    identified_urls)

    # Transformations on elements
    citation_elements = split_volume_from_journal(citation_elements)
    citation_elements = format_volume(citation_elements)
    citation_elements = handle_special_journals(citation_elements, kbs)
    citation_elements = format_report_number(citation_elements)
    citation_elements = format_author_ed(citation_elements)
    citation_elements = look_for_books(citation_elements, kbs)
    citation_elements = format_hep(citation_elements)

    return citation_elements, line_marker, counts, bad_titles_count


def parse_references_elements(ref_sect, kbs):
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
    # a list to contain the processed reference lines:
    citations = []
    # counters for extraction stats:
    counts = {
        'misc': 0,
        'title': 0,
        'reportnum': 0,
        'url': 0,
        'doi': 0,
        'auth_group': 0,
    }
    # A dictionary to contain the total count of each 'bad title' found
    # in the entire reference section:
    bad_titles_count = {}

    # process references line-by-line:
    for ref_line in ref_sect:
        citation_elements, line_marker, this_counts, bad_titles_count = \
            parse_reference_line(ref_line, kbs, bad_titles_count)

        # Accumulate stats
        counts = sum_2_dictionaries(counts, this_counts)

        citations.append({'elements'   : citation_elements,
                          'line_marker': line_marker})

    # Return the list of processed reference lines:
    return (citations, counts, bad_titles_count)


def parse_tagged_reference_line(line_marker,
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
        @param which format to use for references,
        roughly "<title> <volume> <page>" or "<title>,<volume>,<page>"
        @return xml_line: (string) the MARC-XML representation of the tagged reference line
        @return count_*: (integer) the number of * (pieces of info) found in the reference line.
    """
    count_misc = count_title = count_reportnum = count_url = count_doi = count_auth_group = 0
    processed_line = line
    cur_misc_txt = u""

    tag_match = re_tagged_citation.search(processed_line)

    # contains a list of dictionary entries of previously cited items
    citation_elements = []
    # the last tag element found when working from left-to-right across the line
    identified_citation_element = None

    while tag_match is not None:
        # While there are tags inside this reference line...
        tag_match_start = tag_match.start()
        tag_match_end   = tag_match.end()
        tag_type        = tag_match.group(1)
        cur_misc_txt += processed_line[0:tag_match_start]

        # Catches both standard titles, and ibid's
        if tag_type.find("JOURNAL") != -1:
            # This tag is an identified journal TITLE. It should be followed
            # by VOLUME, YEAR and PAGE tags.

            # See if the found title has been tagged as an ibid: <cds.JOURNALibid>
            if tag_match.group('ibid'):
                is_ibid = True
                closing_tag_length = len(CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID)
                idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID,
                                                        tag_match_end)
            else:
                is_ibid = False
                closing_tag_length = len(CFG_REFEXTRACT_MARKER_CLOSING_TITLE)
                # extract the title from the line:
                idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_TITLE,
                                                       tag_match_end)

            if idx_closing_tag == -1:
                # no closing TITLE tag found - get rid of the solitary tag
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:

                # Closing tag was found:
                # The title text to be used in the marked-up citation:
                title_text  = processed_line[tag_match_end:idx_closing_tag]

                # Now trim this matched title and its tags from the start of the line:
                processed_line = processed_line[idx_closing_tag+closing_tag_length:]

                numeration_match = re_recognised_numeration_for_title_plus_series.search(processed_line)
                if numeration_match:
                    # recognised numeration immediately after the title - extract it:
                    reference_volume = numeration_match.group('vol')
                    reference_year   = numeration_match.group('yr') or ''
                    reference_page   = numeration_match.group('pg')

                    # This is used on two accounts:
                    # 1. To get the series char from the title, if no series was found with the numeration
                    # 2. To always remove any series character from the title match text
                    # series_from_title = re_series_from_title.search(title_text)
                    #
                    if numeration_match.group('series'):
                        reference_volume = numeration_match.group('series') + reference_volume

                    # Skip past the matched numeration in the working line:
                    processed_line = processed_line[numeration_match.end():]

                    # 'id_ibid' saves whether THIS TITLE is an ibid or not. (True or False)
                    # 'extra_ibids' are there to hold ibid's without the word 'ibid', which
                    # come directly after this title
                    # i.e., they are recognised using title numeration instead of ibid notation
                    identified_citation_element = {   'type'       : "JOURNAL",
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

                    # Try to find IBID's after this title, on top of previously found titles that were
                    # denoted with the word 'IBID'. (i.e. look for IBID's without the word 'IBID' by
                    # looking at extra numeration after this title)

                    numeration_match = re_numeration_no_ibid_txt.match(processed_line)
                    while numeration_match is not None:

                        reference_volume = numeration_match.group('vol')
                        reference_year   = numeration_match.group('yr')
                        reference_page   = numeration_match.group('pg')

                        if numeration_match.group('series'):
                            reference_volume = numeration_match.group('series') + reference_volume

                        # Skip past the matched numeration in the working line:
                        processed_line = processed_line[numeration_match.end():]

                        # Takes the just found title text
                        identified_citation_element['extra_ibids'].append(
                                                { 'type'       : "JOURNAL",
                                                  'misc_txt'   : "",
                                                  'title'      : title_text,
                                                  'volume'     : reference_volume,
                                                  'year'       : reference_year,
                                                  'page'       : reference_page,
                                                })
                        # Increment the stats counters:
                        count_title += 1

                        title_text = ""
                        reference_volume = ""
                        reference_year = ""
                        reference_page = ""
                        numeration_match = re_numeration_no_ibid_txt.match(processed_line)
                else:
                    # No numeration was recognised after the title. Add the title into a MISC item instead:
                    cur_misc_txt += "%s" % title_text
                    identified_citation_element = None

        elif tag_type == "REPORTNUMBER":

            # This tag is an identified institutional report number:

            # extract the institutional report-number from the line:
            idx_closing_tag = processed_line.find(CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM,
                                                  tag_match_end)
            # Sanity check - did we find a closing report-number tag?
            if idx_closing_tag == -1:
                # no closing </cds.REPORTNUMBER> tag found - strip the opening tag and move past this
                # recognised reportnumber as it is unreliable:
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:
                # closing tag was found
                report_num = processed_line[tag_match_end:idx_closing_tag]
                # now trim this matched institutional report-number
                # and its tags from the start of the line:
                ending_tag_pos = idx_closing_tag \
                    + len(CFG_REFEXTRACT_MARKER_CLOSING_REPORT_NUM)
                processed_line = processed_line[ending_tag_pos:]

                identified_citation_element = {'type'       : "REPORTNUMBER",
                                               'misc_txt'   : cur_misc_txt,
                                               'report_num' : report_num}
                count_reportnum += 1
                cur_misc_txt = u""

        elif tag_type == "URL":
            # This tag is an identified URL:

            # From the "identified_urls" list, get this URL and its
            # description string:
            url_string = identified_urls[0][0]
            url_desc  = identified_urls[0][1]

            # Now move past this "<cds.URL />"tag in the line:
            processed_line = processed_line[tag_match_end:]

            # Delete the information for this URL from the start of the list
            # of identified URLs:
            identified_urls[0:1] = []

            # Save the current misc text
            identified_citation_element = {
                'type'       : "URL",
                'misc_txt'   : "%s" % cur_misc_txt,
                'url_string' : "%s" % url_string,
                'url_desc'   : "%s" % url_desc
            }

            count_url += 1
            cur_misc_txt = u""

        elif tag_type == "DOI":
            # This tag is an identified DOI:

            # From the "identified_dois" list, get this DOI and its
            # description string:
            doi_string = identified_dois[0]

            # Now move past this "<cds.CDS />"tag in the line:
            processed_line = processed_line[tag_match_end:]

            # Remove DOI from the list of DOI strings
            identified_dois[0:1] = []

            # SAVE the current misc text
            identified_citation_element = {
                'type'       : "DOI",
                'misc_txt'   : "%s" % cur_misc_txt,
                'doi_string' : "%s" % doi_string
            }

            # Increment the stats counters:
            count_doi += 1
            cur_misc_txt = u""

        elif tag_type.find("AUTH") != -1:
            # This tag is an identified Author:

            auth_type = ""
            # extract the title from the line:
            if tag_type.find("stnd") != -1:
                auth_type = "stnd"
                idx_closing_tag_nearest = processed_line.find(
                    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, tag_match_end)
            elif tag_type.find("etal") != -1:
                auth_type = "etal"
                idx_closing_tag_nearest = processed_line.find(
                    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL, tag_match_end)
            elif tag_type.find("incl") != -1:
                auth_type = "incl"
                idx_closing_tag_nearest = processed_line.find(
                    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL, tag_match_end)

            if idx_closing_tag_nearest == -1:
                # no closing </cds.AUTH****> tag found - strip the opening tag
                # and move past it
                processed_line = processed_line[tag_match_end:]
                identified_citation_element = None
            else:
                auth_txt = processed_line[tag_match_end:idx_closing_tag_nearest]
                # Now move past the ending tag in the line:
                processed_line = processed_line[idx_closing_tag_nearest + len("</cds.AUTHxxxx>"):]
                #SAVE the current misc text
                identified_citation_element = {
                    'type'       : "AUTH",
                    'misc_txt'   : "%s" % cur_misc_txt,
                    'auth_txt'   : "%s" % auth_txt,
                    'auth_type'  : "%s" % auth_type
                }

                # Increment the stats counters:
                count_auth_group += 1
                cur_misc_txt = u""

        # These following tags may be found separately;
        # They are usually found when a "JOURNAL" tag is hit
        # (ONLY immediately afterwards, however)
        # Sitting by themselves means they do not have
        # an associated TITLE tag, and should be MISC
        elif tag_type == "SER":
            # This tag is a SERIES tag; Since it was not preceeded by a TITLE
            # tag, it is useless - strip the tag and put it into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt,
                                           tag_match_end,
                                           CFG_REFEXTRACT_MARKER_CLOSING_SERIES)
            identified_citation_element = None

        elif tag_type == "VOL":
            # This tag is a VOLUME tag; Since it was not preceeded by a TITLE
            # tag, it is useless - strip the tag and put it into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt,
                                           tag_match_end,
                                           CFG_REFEXTRACT_MARKER_CLOSING_VOLUME)
            identified_citation_element = None

        elif tag_type == "YR":
            # This tag is a YEAR tag; Since it's not preceeded by TITLE and
            # VOLUME tags, it is useless - strip the tag and put the contents
            # into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt,
                                           tag_match_end,
                                           CFG_REFEXTRACT_MARKER_CLOSING_YEAR)
            identified_citation_element = None

        elif tag_type == "PG":
            # This tag is a PAGE tag; Since it's not preceeded by TITLE,
            # VOLUME and YEAR tags, it is useless - strip the tag and put the
            # contents into miscellaneous:
            (cur_misc_txt, processed_line) = \
              convert_unusable_tag_to_misc(processed_line, cur_misc_txt,
                                           tag_match_end,
                                           CFG_REFEXTRACT_MARKER_CLOSING_PAGE)
            identified_citation_element = None

        elif tag_type == "QUOTED":
            identified_citation_element, processed_line, cur_misc_txt = \
                map_tag_to_subfield(tag_type,
                                    processed_line[tag_match_end:],
                                    cur_misc_txt,
                                    'title')

        elif tag_type == "ISBN":
            identified_citation_element, processed_line, cur_misc_txt = \
                map_tag_to_subfield(tag_type,
                                    processed_line[tag_match_end:],
                                    cur_misc_txt,
                                    tag_type)

        elif tag_type == "PUBLISHER":
            identified_citation_element, processed_line, cur_misc_txt = \
                map_tag_to_subfield(tag_type,
                                    processed_line[tag_match_end:],
                                    cur_misc_txt,
                                    'publisher')

        if identified_citation_element:
            # Append the found tagged data and current misc text
            citation_elements.append(identified_citation_element)
            identified_citation_element = None

        # Look for the next tag in the processed line:
        tag_match = re_tagged_citation.search(processed_line)

    # place any remaining miscellaneous text into the
    # appropriate MARC XML fields:
    cur_misc_txt += processed_line

    # This MISC element will hold the entire citation in the event
    # that no tags were found.
    if len(cur_misc_txt.strip(" .;,")) > 0:
        # Increment the stats counters:
        count_misc += 1
        identified_citation_element = {
            'type'       : "MISC",
            'misc_txt'   : "%s" % cur_misc_txt,
        }
        citation_elements.append(identified_citation_element)

    return (citation_elements, line_marker, {
        'misc': count_misc,
        'title': count_title,
        'reportnum': count_reportnum,
        'url': count_url,
        'doi': count_doi,
        'auth_group': count_auth_group
    })


def map_tag_to_subfield(tag_type, line, cur_misc_txt, dest):
    """Create a new reference element"""
    closing_tag = '</cds.%s>' % tag_type
    # extract the institutional report-number from the line:
    idx_closing_tag = line.find(closing_tag)
    # Sanity check - did we find a closing tag?
    if idx_closing_tag == -1:
        # no closing </cds.TAG> tag found - strip the opening tag and move past this
        # recognised reportnumber as it is unreliable:
        identified_citation_element = None
        line = line[len('<cds.%s>' % tag_type):]
    else:
        tag_content = line[:idx_closing_tag]
        identified_citation_element = {'type'     : tag_type,
                                       'misc_txt' : cur_misc_txt,
                                       dest       : tag_content}
        ending_tag_pos = idx_closing_tag + len(closing_tag)
        line = line[ending_tag_pos:]
        cur_misc_txt = u""

    return identified_citation_element, line, cur_misc_txt


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

    # extract the tagged information:
    idx_closing_tag = line.find(closing_tag, tag_match_end)
    # Sanity check - did we find a closing tag?
    if idx_closing_tag == -1:
        # no closing tag found - strip the opening tag and move past this
        # recognised item as it is unusable:
        line = line[tag_match_end:]
    else:
        # closing tag was found
        misc_text += line[tag_match_end:idx_closing_tag]
        # now trim the matched item and its tags from the start of the line:
        line = line[idx_closing_tag+len(closing_tag):]
    return (misc_text, line)

# Tasks related to extraction of reference section from full-text:

# ----> 1. Removing page-breaks, headers and footers before
#          searching for reference section:

# ----> 2. Finding reference section in full-text:

# ----> 3. Found reference section - now take out lines and rebuild them:


def remove_leading_garbage_lines_from_reference_section(ref_sectn):
    """Sometimes, the first lines of the extracted references are completely
       blank or email addresses. These must be removed as they are not
       references.
       @param ref_sectn: (list) of strings - the reference section lines
       @return: (list) of strings - the reference section without leading
        blank lines or email addresses.
    """
    p_email = re.compile(ur'^\s*e\-?mail', re.UNICODE)
    while ref_sectn and (ref_sectn[0].isspace() or p_email.match(ref_sectn[0])):
        ref_sectn.pop(0)
    return ref_sectn


# ----> Glue - logic for finding and extracting reference section:


# Tasks related to conversion of full-text to plain-text:

def get_plaintext_document_body(fpath, keep_layout=False):
    """Given a file-path to a full-text, return a list of unicode strings
       whereby each string is a line of the fulltext.
       In the case of a plain-text document, this simply means reading the
       contents in from the file. In the case of a PDF/PostScript however,
       this means converting the document to plaintext.
       @param fpath: (string) - the path to the fulltext file
       @return: (list) of strings - each string being a line in the document.
    """
    textbody = []
    status = 0
    if os.access(fpath, os.F_OK|os.R_OK):
        # filepath OK - attempt to extract references:
        # get file type:
        cmd_pdftotext = [CFG_PATH_GFILE, fpath]
        pipe_pdftotext = subprocess.Popen(cmd_pdftotext, stdout=subprocess.PIPE)
        res_gfile = pipe_pdftotext.stdout.read()

        if (res_gfile.lower().find("text") != -1) and \
            (res_gfile.lower().find("pdf") == -1):
            # plain-text file: don't convert - just read in:
            f = open(fpath, "r")
            try:
                textbody = [line.decode("utf-8") for line in f.readlines()]
            finally:
                f.close()
        elif (res_gfile.lower().find("pdf") != -1) or \
            (res_gfile.lower().find("pdfa") != -1):
            # convert from PDF
            (textbody, status) = convert_PDF_to_plaintext(fpath, keep_layout)
        else:
            # invalid format
            status = 1
    else:
        # filepath not OK
        status = 1
    return (textbody, status)


def write_raw_references_to_stream(recid, raw_refs, strm):
    """Write a list of raw reference lines to the a given stream.
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
    # write the reference lines to the stream:
    for x in raw_refs:
        strm.write("%(recid)s:%(refline)s\n" % {'recid' : recid,
                                                'refline' : x.encode("utf-8")})
    strm.flush()


def extract_one(config, kbs, num, pdf_path):
    """Extract references from one file"""
    write_message("* processing pdffile: %s" % pdf_path, verbose=2)

    # 1. Get this document body as plaintext:
    (docbody, extract_error) = get_plaintext_document_body(pdf_path)

    if extract_error == 1:
        # Non-existent or unreadable pdf/text directory.
        halt(msg="Error: Unable to open '%s' for extraction" \
             % pdf_path, exit_code=1)
    elif extract_error == 0 and len(docbody) == 0:
        halt(msg="Error: Empty document text", exit_code=1)

    write_message("* get_plaintext_document_body gave: " \
                         "%d lines, overall error: %d" \
                         % (len(docbody), extract_error), verbose=2)

    # the document body is not empty:
    # 2. If necessary, locate the reference section:
    if config.treat_as_reference_section:
        # don't search for citations in the document body:
        # treat it as a reference section:
        refs_info = get_reference_section_beginning(docbody)
        docbody = rebuild_reference_lines(docbody, refs_info['marker_pattern'])
        reflines = docbody
        how_found_start = 1
    else:
        # launch search for the reference section in the document body:
        (reflines, extract_error, how_found_start) = \
                   extract_references_from_fulltext(docbody)
        if len(reflines) == 0 and extract_error == 0:
            extract_error = 6
        write_message("* extract_references_from_fulltext " \
                      "gave len(reflines): %d overall error: %d" \
                       % (len(reflines), extract_error), verbose=2)

    # 3. Standardise the reference lines:
    (processed_references, counts, record_titles_count) = \
      parse_references_elements(reflines, kbs)

    processed_references = build_xml_references(processed_references,
                                                config.inspire)

    # 4. Display the extracted references, status codes, etc:
    if config.output_raw:
        write_raw_references(num, reflines)

    # If found ref section by a weaker method and only found misc/urls then junk it
    # studies show that such cases are ~ 100% rubbish. Also allowing only
    # urls found greatly increases the level of rubbish accepted..
    if counts['reportnum'] + counts['title'] == 0 and how_found_start > 2:
        counts.update({'misc': 0, 'url': 0, 'doi': 0, 'auth_group': 0})
        processed_references = []
        write_message("* Found ONLY miscellaneous/Urls so removed it " \
            "how_found_start=  %d" % how_found_start, verbose=2)
    elif counts['reportnum'] + counts['title']  > 0 and how_found_start > 2:
        write_message("* Found journals/reports with how_found_start= " \
            " %d" % how_found_start, verbose=2)

    # Display the processed reference lines:
    out = create_xml_record(counts,
                            num,
                            processed_references,
                            extract_error)

    return out, record_titles_count


def begin_extraction(config, files):
    """Starts the core extraction procedure. [Entry point from main]

       Only refextract_daemon calls this directly, from _task_run_core()
       @param daemon_cli_options: contains the pre-assembled list of cli flags
       and values processed by the Refextract Daemon. This is full only when
       called as a scheduled bibtask inside bibsched.
    """
    # What journal title format are we using?
    if not config.inspire:
        config.inspire = CFG_INSPIRE_SITE

    if config.inspire:
        write_message("Using inspire journal title form", verbose=2)
    else:
        write_message("Using invenio journal title form", verbose=2)

    # Gather fulltext document locations from input arguments
    extract_jobs = files

    # Read the authors knowledge base, creating the search
    # and replace terms
    kbs = get_kbs(custom_kbs_files={
        'authors'       : config.kb_authors,
        'journals'      : config.kb_journals,
        'report-numbers': config.kb_report_numbers,
        'books'         : config.kb_books,
        'conferences'   : config.kb_conferences,
    })

    # A dictionary to contain the counts of all 'bad titles' found during
    # this reference extraction job:
    all_found_titles_count = {}
    # Store xml records here
    output = []

    for num, curitem in enumerate(extract_jobs):
        # Announce the document extraction number
        write_message("Extracting %d of %d" % (num + 1, len(extract_jobs)),
                      verbose=1)

        out, record_titles_count = extract_one(config, kbs, num + 1, curitem)
        # Add the count of 'bad titles' found in this line to the total
        # for the reference section:
        all_found_titles_count = sum_2_dictionaries(all_found_titles_count,
                                                    record_titles_count)

        display_lines_count(out)
        output.append(out)

    # Write our references
    write_references(config, output)

    # If the option to write the statistics about all periodical titles matched
    # during the extraction-job was selected, do so using the specified file.
    # Note: the matched titles are the Left-Hand-Side titles in the KB, i.e.
    # the BAD versions of titles.
    if config.dictfile:
        write_titles_statistics(all_found_titles_count, config.dictfile)


def write_references(config, xml_references):
    """Write marcxml to file

    * Output xml header
    * Output collection opening tag
    * Output xml for each record
    * Output collection closing tag
    """
    if config.xmlfile:
        ofilehdl = open(config.xmlfile, 'w')
    else:
        ofilehdl = sys.stdout

    try:
        print >>ofilehdl, CFG_REFEXTRACT_XML_VERSION.encode("utf-8")
        print >>ofilehdl, CFG_REFEXTRACT_XML_COLLECTION_OPEN.encode("utf-8")
        for out in xml_references:
            print >>ofilehdl, out.encode("utf-8")
        print >>ofilehdl, CFG_REFEXTRACT_XML_COLLECTION_CLOSE.encode("utf-8")
        ofilehdl.flush()
    except IOError, err:
        write_message("%s\n%s\n" % (config.xmlfile, err), \
                          sys.stderr, verbose=0)
        halt(err=IOError, msg="Error: Unable to write to '%s'" \
                 % config.xmlfile, exit_code=1)

    if config.xmlfile:
        ofilehdl.close()
        # limit m tag data to something less than infinity
        limit_m_tags(config.xmlfile, 2048)


def display_lines_count(text):
    """Display lines count

    Give a text, it counts the number of lines in it and displays it
    """
    lines_count = sum([1 for c in text if c == '\n'])
    write_message("* display_xml_record: %d lines" % lines_count, verbose=2)


def write_raw_references(num, reflines):
    """Write raw references to a file

    If you want to save the raw references to a file
    They will be save in the current directory named by their position
    1st file will be named 1.rawrefs
    2nd file will be named 2.rawrefs
    """
    # now write the raw references to the stream:
    raw_file = '%d.rawrefs' % num
    try:
        rawfilehdl = open(raw_file, 'w')
    except IOError:
        halt(err=IOError, msg="Error: Unable to write to '%s'" \
                      % raw_file, exit_code=1)

    try:
        write_raw_references_to_stream(num, reflines, rawfilehdl)
    finally:
        rawfilehdl.close()


def write_titles_statistics(all_found_titles_count, destination_file):
    """Write title statistics to file

    Write statistics from the extraction to a file
    Output file will look like
        3:JHEP
        3:EUR PHYS J
        25:PHYS REV
    """
    try:
        dfilehdl = open(destination_file, "w")
    except IOError, (errno, err_string):
        # There was a problem writing out the statistics
        write_message("""Unable to write "matched titles" """ \
                         """statistics to output file\n""" \
                         """Error Number %d (%s).""" \
                         % (errno, err_string), \
                         sys.stderr, verbose=0)
        halt(err=IOError, msg="Error: Unable to write to '%s'" \
            % destination_file, exit_code=1)

    try:
        for ktitle, kcount in all_found_titles_count.iteritems():
            dfilehdl.write("%d:%s\n" % (kcount, ktitle.encode("utf-8")))
    finally:
        dfilehdl.close()


def build_xml_references(citations, inspire=CFG_INSPIRE_SITE):
    """Build marc xml from a references list

    Transform the reference elements into marc xml
    """
    xml_references = []

    for c in citations:
        # Now, run the method which will take as input:
        # 1. A list of dictionaries, where each dictionary is a piece
        # of citation information corresponding to a tag in the citation.
        # 2. The line marker for this entire citation line (mulitple citation
        # 'finds' inside a single citation will use the same marker value)
        # The resulting xml line will be a properly marked up form of the
        # citation. It will take into account authors to try and split up
        # references which should be read as two SEPARATE ones.
        xml_line = build_formatted_xml_citation(c['elements'],
                                                c['line_marker'],
                                                inspire)
        xml_references.append(xml_line)

    return xml_references


def parse_references(reference_lines, recid=1,
                                    kbs_files=None, inspire=CFG_INSPIRE_SITE):
    """Parse a list of references

    Given a list of raw reference lines (list of strings),
    output the MARC-XML content extracted version
    """
    # RefExtract knowledge bases
    kbs = get_kbs(custom_kbs_files=kbs_files)
    # Identify journal titles, report numbers, URLs, DOIs, and authors...
    (processed_references, counts, dummy_bad_titles_count) = \
                                parse_references_elements(reference_lines, kbs)
    # Generate marc xml using the elements list
    xml_out = build_xml_references(processed_references, inspire)
    # Generate the xml string to be outputted
    return create_xml_record(counts, recid, xml_out)
