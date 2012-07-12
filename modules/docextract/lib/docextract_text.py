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

"""Various utilities to manipulate or clean text"""

import re

re_space_comma = re.compile(ur'\s,', re.UNICODE)
re_space_semicolon = re.compile(ur'\s;', re.UNICODE)
re_space_period = re.compile(ur'\s\.', re.UNICODE)
re_colon_space_colon = re.compile(ur':\s:', re.UNICODE)
re_comma_space_colon = re.compile(ur',\s:', re.UNICODE)
re_space_closing_square_bracket = re.compile(ur'\s\]', re.UNICODE)
re_opening_square_bracket_space = re.compile(ur'\[\s', re.UNICODE)
re_hyphens = re.compile(
    ur'(\\255|\u02D7|\u0335|\u0336|\u2212|\u002D|\uFE63|\uFF0D)', re.UNICODE)
re_colon_not_followed_by_numeration_tag = \
                               re.compile(ur':(?!\s*<cds)', re.UNICODE|re.I)
re_multiple_space = re.compile(ur'\s{2,}', re.UNICODE)

re_group_captured_multiple_space = re.compile(ur'(\s{2,})', re.UNICODE)


def get_url_repair_patterns():
    """Initialise and return a list of precompiled regexp patterns that
       are used to try to re-assemble URLs that have been broken during
       a document's conversion to plain-text.
       @return: (list) of compiled re regexp patterns used for finding
        various broken URLs.
    """
    file_types_list = [
        ur'h\s*t\s*m',          # htm
        ur'h\s*t\s*m\s*l',      # html
        ur't\s*x\s*t'           # txt
        ur'p\s*h\s*p'           # php
        ur'a\s*s\s*p\s*'        # asp
        ur'j\s*s\s*p',          # jsp
        ur'p\s*y',              # py (python)
        ur'p\s*l',              # pl (perl)
        ur'x\s*m\s*l',          # xml
        ur'j\s*p\s*g',          # jpg
        ur'g\s*i\s*f'           # gif
        ur'm\s*o\s*v'           # mov
        ur's\s*w\s*f'           # swf
        ur'p\s*d\s*f'           # pdf
        ur'p\s*s'               # ps
        ur'd\s*o\s*c',          # doc
        ur't\s*e\s*x',          # tex
        ur's\s*h\s*t\s*m\s*l',  # shtml
    ]

    pattern_list = [
        ur'(h\s*t\s*t\s*p\s*\:\s*\/\s*\/)',
        ur'(f\s*t\s*p\s*\:\s*\/\s*\/\s*)',
        ur'((http|ftp):\/\/\s*[\w\d])',
        ur'((http|ftp):\/\/([\w\d\s\._\-])+?\s*\/)',
        ur'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)+)',
        ur'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)*([\w\d\_\s\-]+\.\s?[\w\d]+))',
    ]
    pattern_list = [re.compile(p, re.I|re.UNICODE) for p in pattern_list]

    ## some possible endings for URLs:
    p = ur'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*([\w\d\_\-]+\.%s))'
    for extension in file_types_list:
        p_url = re.compile(p % extension, re.I|re.UNICODE)
        pattern_list.append(p_url)

    ## if url last thing in line, and only 10 letters max, concat them
    p_url = re.compile(
        r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*\s*?([\w\d\_\.\-]\s?){1,10}\s*)$',
        re.I|re.UNICODE)
    pattern_list.append(p_url)

    return pattern_list

## a list of patterns used to try to repair broken URLs within reference lines:
re_list_url_repair_patterns = get_url_repair_patterns()


def join_lines(line1, line2):
    """Join 2 lines of text

    >>> join_lines('abc', 'de')
    'abcde'
    >>> join_lines('a-', 'b')
    'ab'
    """
    if line1[-1] == u'-':
        ## hyphenated word at the end of the
        ## line - don't add in a space and remove hyphen
        line1 = line1[:-1]
    elif line1[-1] != u' ':
        ## no space at the end of this
        ## line, add in a space
        line1 = line1 + u' '
    return line1 + line2


def repair_broken_urls(line):
    """Attempt to repair broken URLs in a line of text.

    E.g.: remove spaces from the middle of a URL; something like that.

    @param line: (string) the line in which to check for broken URLs.
    @return: (string) the line after any broken URLs have been repaired.
    """
    def _chop_spaces_in_url_match(m):
        """Suppresses spaces in a matched URL."""
        return m.group(1).replace(" ", "")
    for ptn in re_list_url_repair_patterns:
        line = ptn.sub(_chop_spaces_in_url_match, line)
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
    # get a collection of match objects for all instances of
    # multiple-spaces found in the line:
    multispace_matches = re_group_captured_multiple_space.finditer(line)
    # record the number of spaces found at each match position:
    for multispace in multispace_matches:
        removed_spaces[multispace.start()] = \
            (multispace.end() - multispace.start() - 1)
    # now remove the multiple-spaces from the line, replacing with a
    # single space at each position:
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


def get_page_break_positions(docbody):
    """Locate page breaks in the list of document lines and create a list
       positions in the document body list.
       @param docbody: (list) of strings - each string is a line in the
        document.
       @return: (list) of integer positions, whereby each integer represents the
        position (in the document body) of a page-break.
    """
    page_break_posns = []
    p_break = re.compile(ur'^\s*\f\s*$', re.UNICODE)
    num_document_lines = len(docbody)
    for i in xrange(num_document_lines):
        if p_break.match(docbody[i]) != None:
            page_break_posns.append(i)
    return page_break_posns


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
    remaining_breaks = len(page_break_posns) - 1
    num_header_lines = empty_line = 0
    ## pattern to search for a word in a line:
    p_wordSearch = re.compile(ur'([A-Za-z0-9-]+)', re.UNICODE)
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
    num_breaks = len(page_break_posns)
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
    num_breaks = len(page_break_posns)
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
            num_matches += 1
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
