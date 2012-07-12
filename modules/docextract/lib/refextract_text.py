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

import re

from invenio.docextract_pdf import replace_undesirable_characters
from invenio.docextract_utils import write_message

from invenio.docextract_text import join_lines, \
                                    repair_broken_urls, \
                                    re_multiple_space, \
                                    remove_page_boundary_lines

from invenio.refextract_find import find_end_of_reference_section, \
                                    get_reference_section_beginning


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
    # Try to remove pagebreaks, headers, footers
    fulltext = remove_page_boundary_lines(fulltext)
    status = 0
    # How ref section found flag
    how_found_start = 0
    # Find start of refs section
    ref_sect_start = get_reference_section_beginning(fulltext)

    if ref_sect_start is None:
        ## No References
        refs = []
        status = 4
        write_message("* extract_references_from_fulltext: " \
                         "ref_sect_start is None", verbose=2)
    else:
        # If a reference section was found, however weak
        ref_sect_end = \
           find_end_of_reference_section(fulltext,
                                         ref_sect_start["start_line"],
                                         ref_sect_start["marker"],
                                         ref_sect_start["marker_pattern"])
        if ref_sect_end is None:
            # No End to refs? Not safe to extract
            refs = []
            status = 5
            write_message("* extract_references_from_fulltext: " \
                             "no end to refs!", verbose=2)
        else:
            # If the end of the reference section was found.. start extraction
            refs = get_reference_lines(fulltext,
                                       ref_sect_start["start_line"],
                                       ref_sect_end,
                                       ref_sect_start["title_string"],
                                       ref_sect_start["marker_pattern"],
                                       ref_sect_start["title_marker_same_line"],
                                       ref_sect_start["marker"])

    return (refs, status, how_found_start)


def get_reference_lines(docbody,
                        ref_sect_start_line,
                        ref_sect_end_line,
                        ref_sect_title,
                        ref_line_marker_ptn,
                        title_marker_same_line,
                        ref_line_marker):
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
        # Title on same line as 1st ref- take title out!
        title_start = docbody[start_idx].find(ref_sect_title)
        if title_start != -1:
            # Set the first line with no title
            docbody[start_idx] = docbody[start_idx][title_start + \
                                                    len(ref_sect_title):]
    elif ref_sect_title is not None:
        # Set the start of the reference section to be after the title line
        start_idx += 1

    if ref_sect_end_line is not None:
        ref_lines = docbody[start_idx:ref_sect_end_line+1]
    else:
        ref_lines = docbody[start_idx:]

    if ref_sect_title:
        ref_lines = strip_footer(ref_lines, ref_sect_title)
    if not ref_line_marker or not ref_line_marker.isdigit():
        ref_lines = strip_pagination(ref_lines)
    # Now rebuild reference lines:
    # (Go through each raw reference line, and format them into a set
    # of properly ordered lines based on markers)
    return rebuild_reference_lines(ref_lines, ref_line_marker_ptn)


def strip_pagination(ref_lines):
    """Remove footer pagination from references lines"""
    pattern = ur'\(?\[?\d{0,3}\]?\)?\.?\s*$'
    re_footer = re.compile(pattern, re.UNICODE)
    return [l for l in ref_lines if not re_footer.match(l)]


def strip_footer(ref_lines, section_title):
    """Remove footer title from references lines"""
    pattern = ur'\(?\[?\d{0,4}\]?\)?\.?\s*%s\s*$' % re.escape(section_title)
    re_footer = re.compile(pattern, re.UNICODE)
    return [l for l in ref_lines if not re_footer.match(l)]


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

    strip_before = True
    if ref_line_marker_ptn is None or \
           type(ref_line_marker_ptn) not in (str, unicode):
        if test_for_blank_lines_separating_reference_lines(ref_sectn):
            ## Use blank lines to separate ref lines
            ref_line_marker_ptn = ur'^\s*$'
        else:
            ## No ref line dividers: unmatchable pattern
            #ref_line_marker_ptn = ur'^A$^A$$'
            # I am adding a new format, hopefully
            # this case wasn't useful
            # Reference1
            #      etc
            # Reference2
            #      etc
            # We split when there's no identation
            ref_line_marker_ptn = ur'^[^\s]'
            strip_before = False

    write_message('* references separator %s' % ref_line_marker_ptn, verbose=2)
    p_ref_line_marker = re.compile(ref_line_marker_ptn, re.I|re.UNICODE)
    # Work backwards, starting from the last 'broken' reference line
    # Append each fixed reference line to rebuilt_references
    current_ref = None
    for line in reversed(ref_sectn):
        if strip_before:
            current_string = line.strip()
            # Try to find the marker for the reference line
            m_ref_line_marker = p_ref_line_marker.match(current_string)
        else:
            m_ref_line_marker = p_ref_line_marker.match(line)
            current_string = line.strip()

        if m_ref_line_marker and (not current_ref \
                or current_ref == int(m_ref_line_marker.group('num')) + 1):
            # Reference line marker found! : Append this reference to the
            # list of fixed references and reset the working_line to 'blank'
            if current_string != '':
                ## If it's not a blank line to separate refs
                working_line = join_lines(current_string, working_line)
            # Append current working line to the refs list
            working_line = working_line.rstrip()
            working_line = wash_and_repair_reference_line(working_line)
            rebuilt_references.append(working_line)
            try:
                current_ref = int(m_ref_line_marker.group('num'))
            except IndexError:
                pass  # this line doesn't have numbering
            working_line = u''
        else:
            if current_string != u'':
                # Continuation of line
                if current_string[-1] == u'-':
                    # hyphenated word at the end of the
                    # line - don't add in a space
                    working_line = current_string[:-1] + working_line
                elif current_string[-1] == u' ':
                    # space at the end of the
                    # line - don't add in a space
                    working_line = current_string + working_line
                else:
                    # no space or hyphenated word at the end of this
                    # line - add in a space
                    working_line = current_string + u' ' + working_line

    if working_line != u'':
        # Append last line
        working_line = working_line.rstrip()
        working_line = wash_and_repair_reference_line(working_line)
        rebuilt_references.append(working_line)

    # A list of reference lines has been built backwards - reverse it:
    rebuilt_references.reverse()

    # Make sure mulitple markers within references are correctly
    # in place (compare current marker num with current marker num +1)
    rebuilt_references = correct_rebuilt_lines(rebuilt_references, \
                                               p_ref_line_marker)

    # For each properly formated reference line, try to identify cases
    # where there is more than one citation in a single line. This is
    # done by looking for semi-colons, which could be used to
    # separate references
    return rebuilt_references


def wash_and_repair_reference_line(line):
    """Wash a reference line of undesirable characters (such as poorly-encoded
       letters, etc), and repair any errors (such as broken URLs) if possible.
       @param line: (string) the reference line to be washed/repaired.
       @return: (string) the washed reference line.
    """
    # repair URLs in line:
    line = repair_broken_urls(line)
    # Replace various undesirable characters with their alternatives:
    line = replace_undesirable_characters(line)
    # Replace "<title>," with "<title>",
    # common typing mistake
    line = re.sub(ur'"([^"]+),"', ur'"\g<1>",', line)
    line = replace_undesirable_characters(line)
    # Remove instances of multiple spaces from line, replacing with a
    # single space:
    line = re_multiple_space.sub(u' ', line)
    return line


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
            # Even the first mark isnt 1 - probaby too dangerous to
            # try to repair
            return rebuilt_lines
    except (IndexError, AttributeError, ValueError):
        # Sometihng went wrong. Either no references, not a numbered line
        # marker (int() failed), or no reference line marker (NoneType was
        # passed). In any case, unable to test for correct reference line
        # numberring - just return the lines as they were.
        return rebuilt_lines

    # Loop through each line in "rebuilt_lines" and test the mark at the
    # beginning.
    # If current-line-mark = previous-line-mark + 1, the line will be taken to
    # be correct and appended to the list of fixed-lines. If not, then the loop
    # will attempt to test whether the current line marker is actually part of
    # the previous line by looking in the current line for another marker
    # that has the numeric value of previous-marker + 1. If found, that marker
    # will be taken as the true marker for the line and the leader of the line
    # (up to the point of this marker) will be appended to the previous line.
    # E.g.:
    # [1] Smith, J blah blah
    # [2] Brown, N blah blah see reference
    # [56] for more info [3] Wills, A blah blah
    # ...
    #
    # ...will be transformed into:
    # [1] Smith, J blah blah
    # [2] Brown, N blah blah see reference [56] for more info
    # [3] Wills, A blah blah
    # ...

    # first line is correct, to put it into fixed:
    fixed.append(rebuilt_lines[0])
    for x in xrange(1, len(rebuilt_lines)):
        m = p_refmarker.match(rebuilt_lines[x])
        try:
            # Get the number of this line:
            curline_mark_num = m.group("marknum")
        except AttributeError:
            # This line does not have a line marker at the start.
            # Add this line to the end of the previous line.
            fixed[len(fixed) - 1] += rebuilt_lines[x]
        else:
            if int(curline_mark_num) == last_marknum + 1:
                # The marker number for this reference line is correct.
                # Append it to the 'fixed' lines and move on.
                fixed.append(rebuilt_lines[x])
                last_marknum += 1
            elif len(rebuilt_lines[x][m.end():].strip()) == 0:
                # This line consists of a marker-number only - it is not a
                # correct marker. Append it to the last line.
                fixed[len(fixed) - 1] += rebuilt_lines[x]
            else:
                # This marker != previous-marker + 1.
                # May have taken some of the last line into this line.
                # Can we find the next marker in this line?
                # Test for this situation:
                # [54] for more info [3] Wills, A blah blah
                current_line = rebuilt_lines[x]
                m_next_mark = p_refmarker.search(current_line[m.end():])
                while m_next_mark is not None:
                    # Another "line marker" is present in this line.
                    # Test it to see if it is equal to the previous
                    # 'real' marker + 1:
                    if int(m_next_mark.group("marknum")) == \
                       last_marknum + 1:
                        # This seems to be the marker for the next line.
                        # Test to see that the marker is followed by
                        # something meaningful (a letter at least.)
                        # I.e. We want to fix this:
                        # [54] for more info [3] Wills, A blah blah
                        #
                        # but we don't want to fix this:
                        # [54] for more info or even reference [3]
                        #
                        # as that would be unsafe.
                        m_test_nxt_mark_not_eol = \
                          re.search(re.escape(m_next_mark.group()) \
                                     + '\s*[A-Za-z]', current_line)
                        if m_test_nxt_mark_not_eol is not None:
                            # move this section back to its real line:

                            # get the segment of line (before the marker,
                            # which holds a marker that isn't supposed to
                            # be next) to be moved back to the previous line
                            # where it belongs, (append a newline to it too):
                            movesect = \
                               current_line[0:m_test_nxt_mark_not_eol.start()] \
                               + "\n"

                            # Now get the previous line into a variable
                            # (without its newline at the end):
                            previous_line = fixed[len(fixed) - 1].rstrip("\n")

                            # Now append the section which is to be moved to the
                            # previous line. Check the last character
                            # of the previous line. If it's a space, then just
                            # directly append this new section. Else, append a
                            # space then this new section.
                            if previous_line[len(previous_line)-1] not in (u' ', u'-'):
                                movesect = ' ' + movesect
                            previous_line += movesect
                            fixed[len(fixed) - 1] = previous_line

                            # Now append the remainder of the current line to
                            # the list of fixed lines, and move on to the
                            # next line:
                            fixed.append(current_line[m_test_nxt_mark_not_eol.start():])

                            last_marknum += 1
                            break
                        else:
                            # The next 'marker' in this line was not followed
                            # by text. Take from the beginning of this line, to
                            # the end of this marker, and append it to the end
                            # of the previous line:
                            previous_line = fixed[len(fixed) - 1].rstrip("\n")
                            movesect = current_line[0:m_next_mark.end()] + "\n"
                            # Append the section to be moved to the previous
                            # line variable.
                            # Check the last character of the previous line.
                            # If it's a space, then just directly append this
                            # new section. Else, append a space then this new
                            # section.
                            if previous_line[len(previous_line)-1] not in (u' ', u'-'):
                                movesect = ' ' + movesect
                            previous_line += movesect
                            fixed[len(fixed) - 1] = previous_line
                            # Should be blank?
                            current_line = current_line[m_next_mark.end():]

                    else:
                        # This 'marker' is false - its value is not equal to
                        # the previous marker + 1
                        previous_line = fixed[len(fixed) - 1].rstrip("\n")
                        movesect = current_line[0:m_next_mark.end()] + "\n"
                        # Now append the section to be moved to the previous
                        # line variable.
                        # Check the last character of the previous line. If
                        # it's a space, then just directly append this new
                        # section. Else, append a space then this new section.
                        if previous_line[len(previous_line)-1] not in (u' ', u'-'):
                            movesect = ' ' + movesect
                        previous_line += movesect
                        fixed[len(fixed) - 1] = previous_line
                        current_line = current_line[m_next_mark.end():]

                    # Get next match:
                    m_next_mark = p_refmarker.search(current_line)

                # If there was still some of the "current line" left,
                # append it to the previous line:
                if len(current_line.strip()) > 0:
                    previous_line = fixed[len(fixed) - 1].rstrip("\n")
                    movesect = current_line
                    # Now append the section to be moved to the previous line
                    # variable.
                    # Check the last character of the previous line. If it's a
                    # space, then just directly append this new section. Else,
                    # append a space then this new section.
                    if previous_line[len(previous_line)-1] not in (u' ', u'-'):
                        movesect = ' ' + movesect
                    previous_line += movesect
                    fixed[len(fixed) - 1] = previous_line

    return fixed


def test_for_blank_lines_separating_reference_lines(ref_sect):
    """Test to see if reference lines are separated by blank lines so that
       these can be used to rebuild reference lines.
       @param ref_sect: (list) of strings - the reference section.
       @return: (int) 0 if blank lines do not separate reference lines; 1 if
        they do.
    """
    num_blanks = 0             # Number of blank lines found between non-blanks
    num_lines = 0              # Number of reference lines separated by blanks
    blank_line_separators = 0  # Flag to indicate whether blanks lines separate
                               # ref lines
    multi_nonblanks_found = 0  # Flag to indicate whether multiple nonblank
                               # lines are found together (used because
                               # if line is dbl-spaced, it isnt a blank that
                               # separates refs & can't be relied upon)
    x = 0
    max_line = len(ref_sect)
    while x < max_line:
        if not ref_sect[x].isspace():
            # not an empty line:
            num_lines += 1
            x += 1  # Move past line
            while x < len(ref_sect) and not ref_sect[x].isspace():
                multi_nonblanks_found = 1
                x += 1
            x -= 1
        else:
            # empty line
            num_blanks += 1
            x += 1
            while x < len(ref_sect) and ref_sect[x].isspace():
                x += 1
            if x == len(ref_sect):
                # Blanks at end doc: dont count
                num_blanks -= 1
            x -= 1
        x += 1
    # Now from the number of blank lines & the number of text lines, if
    # num_lines > 3, & num_blanks = num_lines, or num_blanks = num_lines - 1,
    # then we have blank line separators between reference lines
    if (num_lines > 3) and ((num_blanks == num_lines) or \
                            (num_blanks == num_lines - 1)) and \
                            (multi_nonblanks_found):
        blank_line_separators = 1
    return blank_line_separators
