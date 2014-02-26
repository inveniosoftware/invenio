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

"""Finding the reference section from the fulltext"""

import re

from invenio.docextract_utils import write_message
from invenio.refextract_re import \
    get_reference_section_title_patterns, \
    get_reference_line_numeration_marker_patterns, \
    regex_match_list, \
    get_post_reference_section_title_patterns, \
    get_post_reference_section_keyword_patterns, \
    re_reference_line_bracket_markers, \
    re_reference_line_dot_markers, \
    re_reference_line_number_markers, \
    re_num


def find_reference_section(docbody):
    """Search in document body for its reference section.

    More precisely, find
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
    ref_details = None
    title_patterns = get_reference_section_title_patterns()

    # Try to find refs section title:
    for reversed_index, line in enumerate(reversed(docbody)):
        title_match = regex_match_list(line, title_patterns)
        if title_match:
            title = title_match.group('title')
            index = len(docbody) - 1 - reversed_index
            temp_ref_details, found_title = find_numeration(docbody[index:index+6], title)
            if temp_ref_details:
                if ref_details and 'title' in ref_details \
                               and ref_details['title'] \
                               and not temp_ref_details['title']:
                    continue
                if ref_details and 'marker' in ref_details \
                               and ref_details['marker'] \
                               and not temp_ref_details['marker']:
                    continue

                ref_details = temp_ref_details
                ref_details['start_line'] = index
                ref_details['title_string'] = title

            if found_title:
                break

    return ref_details


def find_numeration_in_body(docbody):
    marker_patterns = get_reference_line_numeration_marker_patterns()
    ref_details = None
    found_title = False

    # No numeration unless we find one
    ref_details = {
        'title_marker_same_line': False,
        'marker': None,
        'marker_pattern': None,
    }

    for line in docbody:
        # Move past blank lines
        if line.isspace():
            continue

        # Is this line numerated like a reference line?
        m_num = None
        mark_match = regex_match_list(line, marker_patterns)
        if mark_match:
            # Check if it's the first reference
            # Something like [1] or (1), etc.
            try:
                m_num = mark_match.group('marknum')
                if m_num != '1':
                    continue
            except IndexError:
                pass

            mark = mark_match.group('mark')
            mk_ptn = mark_match.re.pattern
            ref_details = {
                'marker': mark,
                'marker_pattern': mk_ptn,
                'title_marker_same_line': False,
            }

            break

    return ref_details, found_title


def find_numeration_in_title(docbody, title):
    ref_details = None
    found_title = False

    try:
        first_line = docbody[0]
    except IndexError:
        return ref_details, found_title

    # Need to escape to avoid problems like 'References['
    title = re.escape(title)

    mk_with_title_ptns = \
       get_reference_line_numeration_marker_patterns(title)
    mk_with_title_match = \
       regex_match_list(first_line, mk_with_title_ptns)
    if mk_with_title_match:
        mk = mk_with_title_match.group('mark')
        mk_ptn = mk_with_title_match.re.pattern
        m_num = re_num.search(mk)
        if m_num and m_num.group(0) == '1':
            # Mark found
            found_title = True
            ref_details = {
                'marker': mk,
                'marker_pattern': mk_ptn,
                'title_marker_same_line': True
            }
        else:
            ref_details = {
                'marker': mk,
                'marker_pattern': mk_ptn,
                'title_marker_same_line': True
            }

    return ref_details, found_title


def find_numeration(docbody, title):
    """Find numeration pattern

    1st try to find numeration in the title
    e.g.
    References [4] Riotto...

    2nd find the numeration alone in the line after the title
    e.g.
    References
    1
    Riotto

    3rnd find the numeration in the following line
    e.g.
    References
    [1] Riotto
    """
    ref_details, found_title = find_numeration_in_title(docbody, title)
    if not ref_details:
        ref_details, found_title = find_numeration_in_body(docbody)

    return ref_details, found_title


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
    marker_patterns = [re_reference_line_bracket_markers]
    return find_reference_section_no_title_generic(docbody, marker_patterns)


def find_reference_section_no_title_via_dots(docbody):
    """This function would generally be used when it was not possible to locate
       the start of a document's reference section by means of its title.
       Instead, this function will look for reference lines that have numeric
       markers of the format 1., 2., etc.
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
    marker_patterns = [re_reference_line_dot_markers]
    return find_reference_section_no_title_generic(docbody, marker_patterns)


def find_reference_section_no_title_via_numbers(docbody):
    """This function would generally be used when it was not possible to locate
       the start of a document's reference section by means of its title.
       Instead, this function will look for reference lines that have numeric
       markers of the format 1, 2, etc.
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
    marker_patterns = [re_reference_line_number_markers]
    return find_reference_section_no_title_generic(docbody, marker_patterns)


def find_reference_section_no_title_generic(docbody, marker_patterns):
    """This function would generally be used when it was not possible to locate
       the start of a document's reference section by means of its title.
       Instead, this function will look for reference lines that have numeric
       markers of the format [1], [2], {1}, {2}, etc.
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
    if not docbody:
        return None

    ref_start_line = ref_line_marker = None

    # try to find first reference line in the reference section:
    found_ref_sect = False

    for reversed_index, line in enumerate(reversed(docbody)):
        mark_match = regex_match_list(line.strip(), marker_patterns)
        if mark_match and mark_match.group('marknum') == '1':
            # Get marker recognition pattern:
            mark_pattern = mark_match.re.pattern

            # Look for [2] in next 10 lines:
            next_test_lines = 10

            index = len(docbody) - reversed_index
            zone_to_check = docbody[index:index+next_test_lines]
            if len(zone_to_check) < 5:
                # We found a 1 towards the end, we assume
                # we only have one reference
                found = True
            else:
                # Check for number 2
                found = False
                for l in zone_to_check:
                    mark_match2 = regex_match_list(l.strip(), marker_patterns)
                    if mark_match2 and mark_match2.group('marknum') == '2':
                        found = True
                        break

            if found:
                # Found next reference line:
                found_ref_sect = True
                ref_start_line = len(docbody) - 1 - reversed_index
                ref_line_marker = mark_match.group('mark')
                ref_line_marker_pattern = mark_pattern
                break

    if found_ref_sect:
        ref_sectn_details = {
            'start_line'             : ref_start_line,
            'title_string'           : None,
            'marker'                 : ref_line_marker.strip(),
            'marker_pattern'         : ref_line_marker_pattern,
            'title_marker_same_line' : False,
        }
    else:
        # didn't manage to find the reference section
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
    section_ended = False
    x = ref_start_line
    if type(x) is not int or x < 0 or \
           x > len(docbody) or len(docbody) < 1:
        # The provided 'first line' of the reference section was invalid.
        # Either it was out of bounds in the document body, or it was not a
        # valid integer.
        # Can't safely find end of refs with this info - quit.
        return None
    # Get patterns for testing line:
    t_patterns = get_post_reference_section_title_patterns()
    kw_patterns = get_post_reference_section_keyword_patterns()

    if None not in (ref_line_marker, ref_line_marker_ptn):
        mk_patterns = [re.compile(ref_line_marker_ptn, re.I|re.UNICODE)]
    else:
        mk_patterns = get_reference_line_numeration_marker_patterns()

    current_reference_count = 0
    while x < len(docbody) and not section_ended:
        # save the reference count
        num_match = regex_match_list(docbody[x].strip(), mk_patterns)
        if num_match:
            try:
                current_reference_count = int(num_match.group('marknum'))
            except (ValueError, IndexError):
                # non numerical references marking
                pass
        # look for a likely section title that would follow a reference section:
        end_match = regex_match_list(docbody[x].strip(), t_patterns)
        if not end_match:
            # didn't match a section title - try looking for keywords that
            # suggest the end of a reference section:
            end_match = regex_match_list(docbody[x].strip(), kw_patterns)
        else:
            # Is it really the end of the reference section? Check within the next
            # 5 lines for other reference numeration markers:
            y = x + 1
            line_found = False
            while y < x + 200 and y < len(docbody) and not line_found:
                num_match = regex_match_list(docbody[y].strip(), mk_patterns)
                if num_match and not num_match.group(0).isdigit():
                    try:
                        num = int(num_match.group('marknum'))
                        if current_reference_count + 1 == num:
                            line_found = True
                    except ValueError:
                        # We have the marknum index so it is
                        # numeric pattern for references like
                        # [1], [2] but this match is not a number
                        pass
                    except IndexError:
                        # We have a non numerical references marking
                        # we don't check for a number continuity
                        line_found = True
                y += 1
            if not line_found:
                # No ref line found-end section
                section_ended = True
        if not section_ended:
            # Does this & the next 5 lines simply contain numbers? If yes, it's
            # probably the axis scale of a graph in a fig. End refs section
            digit_test_str = docbody[x].replace(" ", "").\
                                        replace(".", "").\
                                        replace("-", "").\
                                        replace("+", "").\
                                        replace(u"\u00D7", "").\
                                        replace(u"\u2212", "").\
                                        strip()
            if len(digit_test_str) > 10 and digit_test_str.isdigit():
                # The line contains only digits and is longer than 10 chars:
                y = x + 1
                digit_lines = 4
                num_digit_lines = 1
                while y < x + digit_lines and y < len(docbody):
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
                        # This is a blank line. Don't count it, to accommodate
                        # documents that are double-line spaced:
                        digit_lines += 1
                    y = y + 1
                if num_digit_lines == digit_lines:
                    section_ended = True
            x += 1
    return x - 1


def get_reference_section_beginning(fulltext):

    sect_start = {'start_line'     : None,
                  'end_line'       : None,
                  'title_string'   : None,
                  'marker_pattern' : None,
                  'marker'         : None,
                  'how_found_start': None,
                  }

    ## Find start of refs section:
    sect_start = find_reference_section(fulltext)
    if sect_start is not None:
        sect_start['how_found_start'] = 1
    else:
        ## No references found - try with no title option
        sect_start = find_reference_section_no_title_via_brackets(fulltext)
        if sect_start is not None:
            sect_start['how_found_start'] = 2
        ## Try weaker set of patterns if needed
        if sect_start is None:
            ## No references found - try with no title option (with weaker patterns..)
            sect_start = find_reference_section_no_title_via_dots(fulltext)
            if sect_start is not None:
                sect_start['how_found_start'] = 3
            if sect_start is None:
                ## No references found - try with no title option (with even weaker patterns..)
                sect_start = find_reference_section_no_title_via_numbers(fulltext)
                if sect_start is not None:
                    sect_start['how_found_start'] = 4

    if sect_start:
        write_message('* title %r' % sect_start['title_string'], verbose=3)
        write_message('* marker %r' % sect_start['marker'], verbose=3)
        write_message('* title_marker_same_line %s'
            % sect_start['title_marker_same_line'], verbose=3)
    else:
        write_message('* could not find references section', verbose=3)
    return sect_start
