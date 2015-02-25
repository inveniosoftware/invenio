# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import re

from unidecode import unidecode

from invenio.legacy.refextract.config import \
    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL, \
    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL, \
    CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND, \
    CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID, \
    CFG_REFEXTRACT_MARKER_OPENING_TITLE_IBID, \
    CFG_REFEXTRACT_MARKER_OPENING_COLLABORATION, \
    CFG_REFEXTRACT_MARKER_CLOSING_COLLABORATION

from invenio.legacy.docextract.text import remove_and_record_multiple_spaces_in_line

from invenio.legacy.refextract.regexs import \
    re_ibid, \
    re_doi, \
    re_raw_url, \
    re_series_from_numeration, \
    re_punctuation, \
    re_correct_numeration_2nd_try_ptn1, \
    re_correct_numeration_2nd_try_ptn2, \
    re_correct_numeration_2nd_try_ptn3, \
    re_correct_numeration_2nd_try_ptn4, \
    re_numeration_nucphys_vol_page_yr, \
    re_numeration_vol_subvol_nucphys_yr_page, \
    re_numeration_nucphys_vol_yr_page, \
    re_multiple_hyphens, \
    re_numeration_vol_page_yr, \
    re_numeration_vol_yr_page, \
    re_numeration_vol_nucphys_series_yr_page, \
    re_numeration_vol_series_nucphys_page_yr, \
    re_numeration_vol_nucphys_series_page_yr, \
    re_html_tagged_url, \
    re_numeration_yr_vol_page, \
    re_numeration_vol_nucphys_page_yr, \
    re_wash_volume_tag, \
    re_numeration_vol_nucphys_yr_subvol_page, \
    re_quoted, \
    re_isbn, \
    re_arxiv, \
    re_arxiv_5digits, \
    re_new_arxiv, \
    re_new_arxiv_5digits, \
    re_pos, \
    re_pos_year_num, \
    re_series_from_numeration_after_volume, \
    RE_OLD_ARXIV, \
    RE_ARXIV_CATCHUP, \
    RE_ATLAS_CONF_PRE_2010, \
    RE_ATLAS_CONF_POST_2010

from invenio.legacy.authorextract.regexs import (
    get_author_regexps,
    etal_matches,
    re_ed_notation,
    re_etal)
from invenio.legacy.docextract.text import wash_line


def tag_reference_line(line, kbs, record_titles_count):
    # take a copy of the line as a first working line, clean it of bad
    # accents, and correct puncutation, etc:
    working_line1 = wash_line(line)

    # Identify volume for POS journal
    working_line1 = tag_pos_volume(working_line1)

    # Clean the line once more:
    working_line1 = wash_line(working_line1)

    # We identify quoted text
    # This is useful for books matching
    # This is also used by the author tagger to remove quoted
    # text which is a sign of a title and not an author
    working_line1 = tag_quoted_text(working_line1)

    # Identify ISBN (for books)
    working_line1 = tag_isbn(working_line1)

    # Identify arxiv reports
    working_line1 = tag_arxiv(working_line1)
    working_line1 = tag_arxiv_more(working_line1)
    # Identify volume for POS journal
    # needs special handling because the volume contains the year
    working_line1 = tag_pos_volume(working_line1)
    # Identify ATL-CONF and ATLAS-CONF report numbers
    # needs special handling because it has 2 formats depending on the year
    # and a 2 years digit format to convert
    working_line1 = tag_atlas_conf(working_line1)

    # Identify journals with regular expression
    # Some journals need to match exact regexps because they can
    # conflict with other elements
    # e.g. DAN is also a common first name
    standardised_titles = kbs['journals'][1]
    standardised_titles.update(kbs['journals_re'])
    journals_matches = identifiy_journals_re(working_line1, kbs['journals_re'])

    # Remove identified tags
    working_line2 = strip_tags(working_line1)

    # Transform the line to upper-case, now making a new working line:
    working_line2 = working_line2.upper()

    # Strip punctuation from the line:
    working_line2 = re_punctuation.sub(u' ', working_line2)

    # Remove multiple spaces from the line, recording
    # information about their coordinates:
    removed_spaces, working_line2 = \
         remove_and_record_multiple_spaces_in_line(working_line2)

    # Identify and record coordinates of institute preprint report numbers:
    found_pprint_repnum_matchlens, found_pprint_repnum_replstr, working_line2 =\
       identify_report_numbers(working_line2, kbs['report-numbers'])

    # Identify and record coordinates of non-standard journal titles:
    journals_matches_more, working_line2, line_titles_count = \
        identify_journals(working_line2, kbs['journals'])
    journals_matches.update(journals_matches_more)

    # Add the count of 'bad titles' found in this line to the total
    # for the reference section:
    record_titles_count = sum_2_dictionaries(record_titles_count,
                                             line_titles_count)

    # Attempt to identify, record and replace any IBIDs in the line:
    if (working_line2.upper().find(u"IBID") != -1):
        # there is at least one IBID in the line - try to
        # identify its meaning:
        found_ibids_matchtext, working_line2 = \
            identify_ibids(working_line2)
        # now update the dictionary of matched title lengths with the
        # matched IBID(s) lengths information:
        journals_matches.update(found_ibids_matchtext)

    publishers_matches = identify_publishers(working_line2, kbs['publishers'])

    tagged_line = process_reference_line(
        working_line=working_line1,
        journals_matches=journals_matches,
        pprint_repnum_len=found_pprint_repnum_matchlens,
        pprint_repnum_matchtext=found_pprint_repnum_replstr,
        publishers_matches=publishers_matches,
        removed_spaces=removed_spaces,
        standardised_titles=standardised_titles,
        kbs=kbs,
    )

    return tagged_line, record_titles_count


def process_reference_line(working_line,
                           journals_matches,
                           pprint_repnum_len,
                           pprint_repnum_matchtext,
                           publishers_matches,
                           removed_spaces,
                           standardised_titles,
                           kbs):
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
    if len(journals_matches) + len(pprint_repnum_len) + len(publishers_matches) == 0:
        # no TITLE or REPORT-NUMBER citations were found within this line,
        # use the raw line: (This 'raw' line could still be tagged with
        # recognised URLs or numeration.)
        tagged_line = working_line
    else:
        # TITLE and/or REPORT-NUMBER citations were found in this line,
        # build a new version of the working-line in which the standard
        # versions of the REPORT-NUMBERs and TITLEs are tagged:
        startpos = 0          # First cell of the reference line...
        previous_match = {}   # previously matched TITLE within line (used
                              # for replacement of IBIDs.
        replacement_types = {}
        journals_keys = journals_matches.keys()
        journals_keys.sort()
        reports_keys = pprint_repnum_matchtext.keys()
        reports_keys.sort()
        publishers_keys = publishers_matches.keys()
        publishers_keys.sort()
        spaces_keys = removed_spaces.keys()
        spaces_keys.sort()
        replacement_types = get_replacement_types(journals_keys,
                                                  reports_keys,
                                                  publishers_keys)
        replacement_locations = replacement_types.keys()
        replacement_locations.sort()

        tagged_line = u""  # This is to be the new 'working-line'. It will
                           # contain the tagged TITLEs and REPORT-NUMBERs,
                           # as well as any previously tagged URLs and
                           # numeration components.
        # begin:
        for replacement_index in replacement_locations:
            # first, factor in any stripped spaces before this 'replacement'
            true_replacement_index, extras = \
                  account_for_stripped_whitespace(spaces_keys,
                                                  removed_spaces,
                                                  replacement_types,
                                                  pprint_repnum_len,
                                                  journals_matches,
                                                  replacement_index)

            if replacement_types[replacement_index] == u"journal":
                # Add a tagged periodical TITLE into the line:
                rebuilt_chunk, startpos, previous_match = \
                    add_tagged_journal(
                        reading_line=working_line,
                        journal_info=journals_matches[replacement_index],
                        previous_match=previous_match,
                        startpos=startpos,
                        true_replacement_index=true_replacement_index,
                        extras=extras,
                        standardised_titles=standardised_titles)
                tagged_line += rebuilt_chunk

            elif replacement_types[replacement_index] == u"reportnumber":
                # Add a tagged institutional preprint REPORT-NUMBER
                # into the line:
                rebuilt_chunk, startpos = \
                  add_tagged_report_number(
                    reading_line=working_line,
                    len_reportnum=pprint_repnum_len[replacement_index],
                    reportnum=pprint_repnum_matchtext[replacement_index],
                    startpos=startpos,
                    true_replacement_index=true_replacement_index,
                    extras=extras)
                tagged_line += rebuilt_chunk

            elif replacement_types[replacement_index] == u"publisher":
                rebuilt_chunk, startpos = \
                  add_tagged_publisher(
                    reading_line=working_line,
                    matched_publisher=publishers_matches[replacement_index],
                    startpos=startpos,
                    true_replacement_index=true_replacement_index,
                    extras=extras,
                    kb_publishers=kbs['publishers'])
                tagged_line += rebuilt_chunk

        # add the remainder of the original working-line into the rebuilt line:
        tagged_line += working_line[startpos:]

        # we have all the numeration
        # we can make sure there's no space between the volume
        # letter and the volume number
        # e.g. B 20 -> B20
        tagged_line = wash_volume_tag(tagged_line)

    # Try to find any authors in the line
    tagged_line = identify_and_tag_authors(tagged_line, kbs['authors'])
    # Try to find any collaboration in the line
    tagged_line = identify_and_tag_collaborations(tagged_line,
                                                  kbs['collaborations'])

    return tagged_line.replace('\n', '')


def wash_volume_tag(line):
    return re_wash_volume_tag[0].sub(re_wash_volume_tag[1], line)


def tag_isbn(line):
    """Tag books ISBN"""
    return re_isbn.sub(ur'<cds.ISBN>\g<code></cds.ISBN>', line)


def tag_quoted_text(line):
    """Tag quoted titles

    We use titles for pretty display of references that we could not
    associate we record.
    We also use titles for recognising books.
    """
    return re_quoted.sub(ur'<cds.QUOTED>\g<title></cds.QUOTED>', line)


def tag_arxiv(line):
    """Tag arxiv report numbers

    We handle arXiv in 2 ways:
    * starting with arXiv:1022.1111
    * this format exactly 9999.9999
    We also format the output to the standard arxiv notation:
    * arXiv:2007.12.1111
    * arXiv:2007.12.1111v2
    """
    def tagger(match):
        groups = match.groupdict()
        if match.group('suffix'):
            groups['suffix'] = ' ' + groups['suffix']
        else:
            groups['suffix'] = ''
        return u'<cds.REPORTNUMBER>arXiv:%(year)s'\
            u'%(month)s.%(num)s%(suffix)s' \
            u'</cds.REPORTNUMBER>' % groups

    line = re_arxiv_5digits.sub(tagger, line)
    line = re_arxiv.sub(tagger, line)
    line = re_new_arxiv_5digits.sub(tagger, line)
    line = re_new_arxiv.sub(tagger, line)
    return line


def tag_arxiv_more(line):
    """Tag old arxiv report numbers

    Either formats:
    * hep-th/1234567
    * arXiv:1022111 [hep-ph] which transforms to hep-ph/1022111
    """
    line = RE_ARXIV_CATCHUP.sub(ur"\g<suffix>/\g<year>\g<month>\g<num>", line)

    for report_re, report_repl in RE_OLD_ARXIV:
        report_number = report_repl + ur"/\g<num>"
        line = report_re.sub(u'<cds.REPORTNUMBER>' + report_number
                                                     + u'</cds.REPORTNUMBER>',
                             line)
    return line


def tag_pos_volume(line):
    """Tag POS volume number

    POS is journal that has special volume numbers
    e.g. PoS LAT2007 (2007) 369
    """
    def tagger(match):
        groups = match.groupdict()
        try:
            year = match.group('year')
        except IndexError:
            # Extract year from volume name
            # which should always include the year
            g = re.search(re_pos_year_num, match.group('volume_num'), re.UNICODE)
            year = g.group(0)

        if year:
            groups['year'] = ' <cds.YR>(%s)</cds.YR>' % year.strip().strip('()')
        else:
            groups['year'] = ''

        return '<cds.JOURNAL>PoS</cds.JOURNAL>' \
            ' <cds.VOL>%(volume_name)s%(volume_num)s</cds.VOL>' \
            '%(year)s' \
            ' <cds.PG>%(page)s</cds.PG>' % groups

    for p in re_pos:
        line = p.sub(tagger, line)

    return line


def tag_atlas_conf(line):
    line = RE_ATLAS_CONF_PRE_2010.sub(
        ur'<cds.REPORTNUMBER>ATL-CONF-\g<code></cds.REPORTNUMBER>', line)
    line = RE_ATLAS_CONF_POST_2010.sub(
        ur'<cds.REPORTNUMBER>ATLAS-CONF-\g<code></cds.REPORTNUMBER>', line)
    return line


def identifiy_journals_re(line, kb_journals):
    matches = {}
    for pattern, dummy_journal in kb_journals:
        match = re.search(pattern, line)
        if match:
            matches[match.start()] = match.group(0)
    return matches


def find_numeration_more(line):
    """Look for other numeration in line."""
    # First, attempt to use marked-up titles
    patterns = (
        re_correct_numeration_2nd_try_ptn1,
        re_correct_numeration_2nd_try_ptn2,
        re_correct_numeration_2nd_try_ptn3,
        re_correct_numeration_2nd_try_ptn4,
    )
    for pattern in patterns:
        match = pattern.search(line)
        if match:
            info = match.groupdict()
            series = extract_series_from_volume(info['vol'])
            if not info['vol_num']:
                info['vol_num'] = info['vol_num_alt']
            if not info['vol_num']:
                info['vol_num'] = info['vol_num_alt2']
            return {'year': info.get('year', None),
                    'series': series,
                    'volume': info['vol_num'],
                    'page': info['page'],
                    'page_end': info['page_end'],
                    'len': len(info['aftertitle'])}

    return None


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
    rebuilt_line = u""  # The segment of the line that's being rebuilt to
                        # include the tagged & standardised REPORT-NUMBER

    # Fill rebuilt_line with the contents of the reading_line up to the point
    # of the institutional REPORT-NUMBER. However, stop 1 character before the
    # replacement index of this REPORT-NUMBER to allow for removal of braces,
    # if necessary:
    if (true_replacement_index - startpos - 1) >= 0:
        rebuilt_line += reading_line[startpos:true_replacement_index - 1]
    else:
        rebuilt_line += reading_line[startpos:true_replacement_index]

    # Add the tagged REPORT-NUMBER into the rebuilt-line segment:
    rebuilt_line += u"<cds.REPORTNUMBER>%(reportnum)s</cds.REPORTNUMBER>" \
                        % {'reportnum' : reportnum}

    # Move the pointer in the reading-line past the current match:
    startpos = true_replacement_index + len_reportnum + extras

    # Move past closing brace for report number (if there was one):
    try:
        if reading_line[startpos] in (u"]", u")"):
            startpos += 1
    except IndexError:
        # moved past end of line - ignore
        pass

    # return the rebuilt-line segment and the pointer to the next position in
    # the reading-line from  which to start rebuilding up to the next match:
    return rebuilt_line, startpos


def add_tagged_journal_in_place_of_IBID(previous_match):
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

    return " %s%s%s" % (CFG_REFEXTRACT_MARKER_OPENING_TITLE_IBID,
                       previous_match['title'],
                       CFG_REFEXTRACT_MARKER_CLOSING_TITLE_IBID)


def extract_series_from_volume(volume):
    patterns = (re_series_from_numeration,
                re_series_from_numeration_after_volume)
    for p in patterns:
        match = p.search(volume)
        if match:
            return match.group(1)
    return None


def create_numeration_tag(info):
    if info['series']:
        series_and_volume = info['series'] + info['volume']
    else:
        series_and_volume = info['volume']
    numeration_tags = u' <cds.VOL>%s</cds.VOL>' % series_and_volume
    if info.get('year', False):
        numeration_tags += u' <cds.YR>(%(year)s)</cds.YR>' % info
    if info.get('page_end', False):
        numeration_tags += u' <cds.PG>%(page)s-%(page_end)s</cds.PG>' % info
    else:
        numeration_tags += u' <cds.PG>%(page)s</cds.PG>' % info
    return numeration_tags


def add_tagged_journal(reading_line,
                       journal_info,
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
       @param previous_match: (dict) the previous periodical TITLE citation to
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
    old_startpos = startpos
    old_previous_match = previous_match
    skip_numeration = False
    series = None

    def skip_ponctuation(line, pos):
        # Skip past any punctuation at the end of the replacement that was
        # just made:
        try:
            while line[pos] in (".", ":", "-", ")"):
                pos += 1
        except IndexError:
            # The match was at the very end of the line
            pass

        return pos

    # Fill 'rebuilt_line' (the segment of the line that is being rebuilt to
    # include the tagged and standardised periodical TITLE) with the contents
    # of the reading-line, up to the point of the matched TITLE:
    rebuilt_line = reading_line[startpos:true_replacement_index]

    # Test to see whether a title or an "IBID" was matched:
    if journal_info.upper().find("IBID") != -1:
        # This is an IBID
        # Try to replace the IBID with a title:
        if previous_match:
            # Replace this IBID with the previous title match, if possible:
            rebuilt_line += add_tagged_journal_in_place_of_IBID(previous_match)
            series = previous_match['series']
            # Update start position for next segment of original line:
            startpos = true_replacement_index + len(journal_info) + extras
            startpos = skip_ponctuation(reading_line, startpos)
        else:
            rebuilt_line = ""
            skip_numeration = True
    else:
        if ';' in standardised_titles[journal_info]:
            title, series = \
                              standardised_titles[journal_info].rsplit(';', 1)
            series = series.strip()
            previous_match = {'title': title,
                              'series': series}
        else:
            title = standardised_titles[journal_info]
            previous_match = {'title': title,
                              'series': None}

        # This is a normal title, not an IBID
        rebuilt_line += "<cds.JOURNAL>%s</cds.JOURNAL>" % title
        startpos = true_replacement_index + len(journal_info) + extras
        startpos = skip_ponctuation(reading_line, startpos)

    if not skip_numeration:
        # Check for numeration
        numeration_line = reading_line[startpos:]
        # First look for standard numeration
        numerotation_info = find_numeration(numeration_line)
        if not numerotation_info:
            numeration_line = rebuilt_line + " " + numeration_line
            # Now look for more funky numeration
            # With possibly some elements before the journal title
            numerotation_info = find_numeration_more(numeration_line)

        if not numerotation_info:
            startpos = old_startpos
            previous_match = old_previous_match
            rebuilt_line = ""
        else:
            if series and not numerotation_info['series']:
                numerotation_info['series'] = series
            startpos += numerotation_info['len']
            rebuilt_line += create_numeration_tag(numerotation_info)

            previous_match['series'] = numerotation_info['series']

    # return the rebuilt line-segment, the position (of the reading line) from
    # which the next part of the rebuilt line should be started, and the newly
    # updated previous match.
    return rebuilt_line, startpos, previous_match


def add_tagged_publisher(reading_line,
                         matched_publisher,
                         startpos,
                         true_replacement_index,
                         extras,
                         kb_publishers):
    """In rebuilding the line, add an identified periodical TITLE (standardised
       and tagged) into the line.
       @param reading_line: (string) The reference line before capitalization
        was performed, and before REPORT-NUMBERs and TITLEs were stripped out.
       @param len_title: (integer) the length of the matched TITLE.
       @param matched_title: (string) the matched TITLE text.
       @param previous_match: (string) the previous periodical TITLE citation to
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
    # Fill 'rebuilt_line' (the segment of the line that is being rebuilt to
    # include the tagged and standardised periodical TITLE) with the contents
    # of the reading-line, up to the point of the matched TITLE:
    rebuilt_line = reading_line[startpos:true_replacement_index]
    # This is a normal title, not an IBID
    rebuilt_line += "<cds.PUBLISHER>%(title)s</cds.PUBLISHER>" \
                    % {'title' : kb_publishers[matched_publisher]['repl']}
    # Compute new start pos
    startpos = true_replacement_index + len(matched_publisher) + extras

    # return the rebuilt line-segment, the position (of the reading line) from
    # which the next part of the rebuilt line should be started, and the newly
    # updated previous match.

    return rebuilt_line, startpos


def get_replacement_types(titles, reportnumbers, publishers):
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
        rep_types[item_idx] = "journal"
    for item_idx in reportnumbers:
        rep_types[item_idx] = "reportnumber"
    for item_idx in publishers:
        rep_types[item_idx] = "publisher"
    return rep_types


def account_for_stripped_whitespace(spaces_keys,
                                    removed_spaces,
                                    replacement_types,
                                    len_reportnums,
                                    journals_matches,
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
            # There were spaces stripped before the current replacement
            # Add the number of spaces removed from this location to the
            # current replacement index:
            true_replacement_index += removed_spaces[space]
            spare_replacement_index += removed_spaces[space]
        elif space >= spare_replacement_index and \
                 replacement_types[replacement_index] == u"journal" and \
                 space < (spare_replacement_index +
                                     len(journals_matches[replacement_index])):
            # A periodical title is being replaced. Account for multi-spaces
            # that may have been stripped from the title before its
            # recognition:
            spare_replacement_index += removed_spaces[space]
            extras += removed_spaces[space]
        elif space >= spare_replacement_index and \
                 replacement_types[replacement_index] == u"reportnumber" and \
                 space < (spare_replacement_index +
                           len_reportnums[replacement_index]):
            # An institutional preprint report-number is being replaced.
            # Account for multi-spaces that may have been stripped from it
            # before its recognition:
            spare_replacement_index += removed_spaces[space]
            extras += removed_spaces[space]

    # return the new values for replacement indices with stripped
    # whitespace accounted for:
    return true_replacement_index, extras


def strip_tags(line):
    # Firstly, go through and change ALL TAGS and their contents to underscores
    # author content can be checked for underscores later on
    # Note that we don't have embedded tags this is why
    # we can do this
    re_tag = re.compile(ur'<cds\.[A-Z]+>[^<]*</cds\.[A-Z]+>|<cds\.[A-Z]+ />',
                        re.UNICODE)
    for m in re_tag.finditer(line):
        chars_count = m.end() - m.start()
        line = re_tag.sub('_'*chars_count, line, count=1)
    return line


def identify_and_tag_collaborations(line, collaborations_kb):
    """Given a line where Authors have been tagged, and all other tags
       and content has been replaced with underscores, go through and try
       to identify extra items of data which should be placed into 'h'
       subfields.
       Later on, these tagged pieces of information will be merged into
       the content of the most recently found author. This is separated
       from the author tagging procedure since separate tags can be used,
       which won't influence the reference splitting heuristics
       (used when looking at mulitple <AUTH> tags in a line).
    """
    for dummy_collab, re_collab in collaborations_kb.iteritems():
        matches = re_collab.finditer(strip_tags(line))

        for match in reversed(list(matches)):
            line = line[:match.start()] \
                + CFG_REFEXTRACT_MARKER_OPENING_COLLABORATION \
                + match.group(1).strip(".,:;- [](){}") \
                + CFG_REFEXTRACT_MARKER_CLOSING_COLLABORATION \
                + line[match.end():]

    return line


def identify_and_tag_authors(line, authors_kb):
    """Given a reference, look for a group of author names,
       place tags around the author group, return the newly tagged line.
    """
    re_auth, re_auth_near_miss = get_author_regexps()

    # Replace authors which do not convert well from utf-8
    for pattern, repl in authors_kb:
        line = line.replace(pattern, repl)

    output_line = line

    # We matched authors here
    line = strip_tags(output_line)
    matched_authors = list(re_auth.finditer(line))
    # We try to have better results by unidecoding
    unidecoded_line = strip_tags(unidecode(output_line))
    matched_authors_unidecode = list(re_auth.finditer(unidecoded_line))

    if len(matched_authors_unidecode) > len(matched_authors):
        output_line = unidecode(output_line)
        matched_authors = matched_authors_unidecode

    # If there is at least one matched author group
    if matched_authors:
        matched_positions = []
        preceeding_text_string = line
        preceeding_text_start = 0
        for auth_no, match in enumerate(matched_authors):
            # Only if there are no underscores or closing arrows found in the matched author group
            # This must be checked for here, as it cannot be applied to the re without clashing with
            # other Unicode characters
            if line[match.start():match.end()].find("_") == -1:
                # Has the group with name 'et' (for 'et al') been found in the pattern?
                # Has the group with name 'es' (for ed. before the author) been found in the pattern?
                # Has the group with name 'ee' (for ed. after the author) been found in the pattern?
                matched_positions.append({
                    'start'       : match.start(),
                    'end'         : match.end(),
                    'etal'        : match.group('et') or match.group('et2'),
                    'ed_start'    : match.group('es'),
                    'ed_end'      : match.group('ee'),
                    'multi_auth'  : match.group('multi_auth'),
                    'multi_surs'  : match.group('multi_surs'),
                    'text_before' : preceeding_text_string[preceeding_text_start:match.start()],
                    'auth_no'     : auth_no,
                    'author_names': match.group('author_names')
                })
                # Save the end of the match, from where to snip the misc text found before an author match
                preceeding_text_start = match.end()

        # Work backwards to avoid index problems when adding AUTH tags
        matched_positions.reverse()
        for m in matched_positions:
            dump_in_misc = False
            start = m['start']
            end = m['end']

            # Check the text before the current match to see if it has a bad 'et al'
            lower_text_before = m['text_before'].strip().lower()
            for e in etal_matches:
                if lower_text_before.endswith(e):
                    ## If so, this author match is likely to be a bad match on a missed title
                    dump_in_misc = True
                    break

            # An AND found here likely indicates a missed author before this text
            # Thus, triggers weaker author searching, within the previous misc text
            # (Check the text before the current match to see if it has a bad 'and')
            # A bad 'and' will only be denoted as such if there exists only one author after it
            # and the author group is legit (not to be dumped in misc)
            if not dump_in_misc and not (m['multi_auth'] or m['multi_surs']) \
                    and (lower_text_before.endswith(' and')):
                # Search using a weaker author pattern to try and find the missed author(s) (cut away the end 'and')
                weaker_match = re_auth_near_miss.match(m['text_before'])
                if weaker_match and not (weaker_match.group('es') or weaker_match.group('ee')):
                    # Change the start of the author group to include this new author group
                    start = start - (len(m['text_before']) - weaker_match.start())
                # Still no match, do not add tags for this author match.. dump it into misc
                else:
                    dump_in_misc = True

            add_to_misc = ""
            # If a semi-colon was found at the end of this author group, keep it in misc
            # so that it can be looked at for splitting heurisitics
            if len(output_line) > m['end']:
                if output_line[m['end']].strip(" ,.") == ';':
                    add_to_misc = ';'

            # Standardize eds. notation
            tmp_output_line = re.sub(re_ed_notation, '(ed.)',
                output_line[start:end], re.IGNORECASE)
            # Standardize et al. notation
            tmp_output_line = re.sub(re_etal, 'et al.',
                tmp_output_line, re.IGNORECASE)
            # Strip
            tmp_output_line = tmp_output_line.lstrip('.').strip(",:;- [](")
            if not tmp_output_line.endswith('(ed.)'):
                tmp_output_line = tmp_output_line.strip(')')

            # ONLY wrap author data with tags IF there is no evidence that it is an
            # ed. author. (i.e. The author is not referred to as an editor)
            # Does this author group string have 'et al.'?
            if m['etal'] and not (m['ed_start'] or m['ed_end'] or dump_in_misc):
                output_line = output_line[:start] \
                    + "<cds.AUTHetal>" \
                    + tmp_output_line \
                    + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_ETAL \
                    + add_to_misc \
                    + output_line[end:]
            elif not (m['ed_start'] or m['ed_end'] or dump_in_misc):
                # Insert the std (standard) tag
                output_line = output_line[:start] \
                    + "<cds.AUTHstnd>" \
                    + tmp_output_line \
                    + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_STND \
                    + add_to_misc \
                    + output_line[end:]
            # Apply the 'include in $h' method to author groups marked as editors
            elif m['ed_start'] or m['ed_end']:
                ed_notation = " (eds.)"
                # Standardize et al. notation
                tmp_output_line = re.sub(re_etal, 'et al.',
                    m['author_names'], re.IGNORECASE)
                # remove any characters which denote this author group
                # to be editors, just take the
                # author names, and append '(ed.)'
                output_line = output_line[:start] \
                    + "<cds.AUTHincl>" \
                    + tmp_output_line.strip(",:;- [](") \
                    + ed_notation \
                    + CFG_REFEXTRACT_MARKER_CLOSING_AUTHOR_INCL \
                    + add_to_misc \
                    + output_line[end:]

    return output_line


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
        if 'key' in dict_out:
            # Add the sum for key in dictb to that of dict_out:
            dict_out[key] += dictb[key]
        else:
            # the key is not in the first dictionary - add it directly:
            dict_out[key] = dictb[key]
    return dict_out


def identify_ibids(line):
    """Find IBIDs within the line, record their position and length,
       and replace them with underscores.
       @param line: (string) the working reference line
       @return: (tuple) containing 2 dictionaries and a string:
         Dictionary:   matched IBID text: (Key: position of IBID in
                       line; Value: matched IBID text)
         String:       working line with matched IBIDs removed
    """
    ibid_match_txt = {}
    # Record details of each matched ibid:
    for m_ibid in re_ibid.finditer(line):
        ibid_match_txt[m_ibid.start()] = m_ibid.group(0)
        # Replace matched text in line with underscores:
        line = line[0:m_ibid.start()] + \
               "_" * len(m_ibid.group(0)) + \
               line[m_ibid.end():]

    return ibid_match_txt, line


def find_all(string, sub):
    listindex = []
    offset = 0
    i = string.find(sub, offset)
    while i >= 0:
        listindex.append(i)
        i = string.find(sub, i + 1)
    return listindex


def find_numeration(line):
    """Given a reference line, attempt to locate instances of citation
       'numeration' in the line.
       @param line: (string) the reference line.
       @return: (string) the reference line after numeration has been checked
        and possibly recognized/marked-up.
    """
    patterns = (
        # vol,page,year
        re_numeration_vol_page_yr,
        re_numeration_vol_nucphys_page_yr,
        re_numeration_nucphys_vol_page_yr,
        # With sub volume
        re_numeration_vol_subvol_nucphys_yr_page,
        re_numeration_vol_nucphys_yr_subvol_page,
        # vol,year,page
        re_numeration_vol_yr_page,
        re_numeration_nucphys_vol_yr_page,
        re_numeration_vol_nucphys_series_yr_page,
        # vol,page,year
        re_numeration_vol_series_nucphys_page_yr,
        re_numeration_vol_nucphys_series_page_yr,
        # year,vol,page
        re_numeration_yr_vol_page,
    )

    for pattern in patterns:
        match = pattern.match(line)
        if match:
            info = match.groupdict()
            series = info.get('series', None)
            if not series:
                series = extract_series_from_volume(info['vol'])
            if not info['vol_num']:
                info['vol_num'] = info['vol_num_alt']
            if not info['vol_num']:
                info['vol_num'] = info['vol_num_alt2']
            return {'year': info.get('year', None),
                    'series': series,
                    'volume': info['vol_num'],
                    'page': info['page'],
                    'page_end': info['page_end'],
                    'len': match.end()}

    return None


def identify_journals(line, kb_journals):
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
    periodical_title_search_kb = kb_journals[0]
    periodical_title_search_keys = kb_journals[2]

    title_matches = {}            # the text matched at the given line
                                  # location (i.e. the title itself)
    titles_count = {}             # sum totals of each 'bad title found in
                                  # line.

    # Begin searching:
    for title in periodical_title_search_keys:
        # search for all instances of the current periodical title
        # in the line:
        # for each matched periodical title:
        for title_match in periodical_title_search_kb[title].finditer(line):

            if title not in titles_count:
                # Add this title into the titles_count dictionary:
                titles_count[title] = 1
            else:
                # Add 1 to the count for the given title:
                titles_count[title] += 1

            # record the details of this title match:
            # record the match length:
            title_matches[title_match.start()] = title

            len_to_replace = len(title)

            # replace the matched title text in the line it n * '_',
            # where n is the length of the matched title:
            line = u"".join((line[:title_match.start()],
                             u"_" * len_to_replace,
                             line[title_match.start() + len_to_replace:]))

    # return recorded information about matched periodical titles,
    # along with the newly changed working line:
    return title_matches, line, titles_count


def identify_report_numbers(line, kb_reports):
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

    repnum_matches_matchlen = {}  # info about lengths of report numbers
                                  # matched at given locations in line
    repnum_matches_repl_str = {}  # standardised report numbers matched
                                  # at given locations in line

    repnum_search_kb, repnum_standardised_categs = kb_reports
    repnum_categs = repnum_standardised_categs.keys()
    repnum_categs.sort(_by_len)

    # Handle CERN/LHCC/98-013
    line = line.replace('/', ' ')

    # try to match preprint report numbers in the line:
    for categ in repnum_categs:
        # search for all instances of the current report
        # numbering style in the line:
        repnum_matches_iter = repnum_search_kb[categ].finditer(line)

        # for each matched report number of this style:
        for repnum_match in repnum_matches_iter:
            # Get the matched text for the numeration part of the
            # preprint report number:
            numeration_match = repnum_match.group('numn')
            # clean/standardise this numeration text:
            numeration_match = numeration_match.replace(" ", "-")
            numeration_match = re_multiple_hyphens.sub("-", numeration_match)
            numeration_match = numeration_match.replace("/-", "/")
            numeration_match = numeration_match.replace("-/", "/")
            numeration_match = numeration_match.replace("-/-", "/")

            # replace the found preprint report number in the
            # string with underscores
            # (this will replace chars in the lower-cased line):
            line = line[0:repnum_match.start(1)] \
                   + "_"*len(repnum_match.group(1)) + line[repnum_match.end(1):]

            # record the information about the matched preprint report number:
            # total length in the line of the matched preprint report number:
            repnum_matches_matchlen[repnum_match.start(1)] = \
                                                    len(repnum_match.group(1))
            # standardised replacement for the matched preprint report number:
            repnum_matches_repl_str[repnum_match.start(1)] = \
                                    repnum_standardised_categs[categ] \
                                    + numeration_match

    # return recorded information about matched report numbers, along with
    # the newly changed working line:
    return repnum_matches_matchlen, repnum_matches_repl_str, line


def identify_publishers(line, kb_publishers):
    matches_repl = {}  # standardised report numbers matched
                       # at given locations in line

    for abbrev, info in kb_publishers.iteritems():
        for match in info['pattern'].finditer(line):
            # record the matched non-standard version of the publisher:
            matches_repl[match.start(0)] = abbrev

    return matches_repl


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
    # Take a copy of the line:
    line_pre_url_check = line
    # Dictionaries to record details of matched URLs:
    found_url_full_matchlen = {}
    found_url_urlstring     = {}
    found_url_urldescr      = {}

    # List to contain details of all matched URLs:
    identified_urls = []

    # Attempt to identify and tag all HTML-MARKED-UP URLs in the line:
    m_tagged_url_iter = re_html_tagged_url.finditer(line)
    for m_tagged_url in m_tagged_url_iter:
        startposn = m_tagged_url.start()        # start position of matched URL
        endposn   = m_tagged_url.end()          # end position of matched URL
        matchlen  = len(m_tagged_url.group(0))  # total length of URL match

        found_url_full_matchlen[startposn] = matchlen
        found_url_urlstring[startposn]     = m_tagged_url.group('url')
        found_url_urldescr[startposn]      = m_tagged_url.group('desc')
        # temporarily replace the URL match with underscores so that
        # it won't be re-found
        line = line[0:startposn] + u"_"*matchlen + line[endposn:]

    # Attempt to identify and tag all RAW (i.e. not
    # HTML-marked-up) URLs in the line:
    m_raw_url_iter = re_raw_url.finditer(line)
    for m_raw_url in m_raw_url_iter:
        startposn   = m_raw_url.start()        # start position of matched URL
        endposn     = m_raw_url.end()          # end position of matched URL
        matchlen    = len(m_raw_url.group(0))  # total length of URL match
        matched_url = m_raw_url.group('url')

        if len(matched_url) > 0 and matched_url[-1] in (".", ","):
            # Strip the full-stop or comma from the end of the url:
            matched_url = matched_url[:-1]

        found_url_full_matchlen[startposn] = matchlen
        found_url_urlstring[startposn]     = matched_url
        found_url_urldescr[startposn]      = matched_url
        # temporarily replace the URL match with underscores
        # so that it won't be re-found
        line = line[0:startposn] + u"_"*matchlen + line[endposn:]

    # Now that all URLs have been identified, insert them
    # back into the line, tagged:
    found_url_positions = found_url_urlstring.keys()
    found_url_positions.sort()
    found_url_positions.reverse()
    for url_position in found_url_positions:
        line = line[0:url_position] + "<cds.URL />" \
               + line[url_position + found_url_full_matchlen[url_position]:]

    # The line has been rebuilt. Now record the information about the
    # matched URLs:
    found_url_positions = found_url_urlstring.keys()
    found_url_positions.sort()
    for url_position in found_url_positions:
        identified_urls.append((found_url_urlstring[url_position],
                                found_url_urldescr[url_position]))

    # Somehow the number of URLs found doesn't match the number of
    # URLs recorded in "identified_urls". Raise an IndexError.
    msg = """Error: The number of URLs found in the reference line """ \
          """does not match the number of URLs recorded in the """ \
          """list of identified URLs!\nLine pre-URL checking: %s\n""" \
          """Line post-URL checking: %s\n""" \
          % (line_pre_url_check, line)
    assert len(identified_urls) == len(found_url_positions), msg

    # return the line containing the tagged URLs:
    return line, identified_urls


def identify_and_tag_DOI(line):
    """takes a single citation line and attempts to locate any DOI references.
       DOI references are recognised in both http (url) format and also the
       standard DOI notation (DOI: ...)
       @param line: (string) the reference line in which to search for DOI's.
       @return: the tagged line and a list of DOI strings (if any)
    """
    # Used to hold the DOI strings in the citation line
    doi_strings = []

    # Run the DOI pattern on the line, returning the re.match objects
    matched_doi = re_doi.finditer(line)
    # For each match found in the line
    for match in reversed(list(matched_doi)):
        # Store the start and end position
        start = match.start()
        end = match.end()
        # Get the actual DOI string (remove the url part of the doi string)
        doi_phrase = match.group(6)

        # Replace the entire matched doi with a tag
        line = line[0:start] + "<cds.DOI />" + line[end:]
        # Add the single DOI string to the list of DOI strings
        doi_strings.append(doi_phrase)

    doi_strings.reverse()
    return line, doi_strings
