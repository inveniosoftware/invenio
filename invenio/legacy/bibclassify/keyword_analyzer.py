# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
"""
BibClassify keyword analyser.

This module contains methods to extract keywords from texts. It provides 3
different methods for 3 different types of keywords: single keywords, composite
keywords and author keywords.

This module is STANDALONE safe
"""

from __future__ import print_function

import re
import time

import config as bconfig

log = bconfig.get_logger("bibclassify.keyword_analyzer")

_MAXIMUM_SEPARATOR_LENGTH = max([len(_separator)
                                 for _separator in
                                 bconfig.CFG_BIBCLASSIFY_VALID_SEPARATORS])


# XXX - rebuild this whole thing
def get_single_keywords(skw_db, fulltext):
    """Find single keywords in the fulltext
    @var skw_db: list of KeywordToken objects
    @var fulltext: string, which will be searched
    @return : dictionary of matches in a format {
            <keyword object>, [[position, position...], ],
            ..
            }
    """
    timer_start = time.clock()

    # single keyword -> [spans]
    records = []

    for single_keyword in skw_db.values():
        for regex in single_keyword.regex:
            for match in regex.finditer(fulltext):
                # Modify the right index to put it on the last letter
                # of the word.
                span = (match.span()[0], match.span()[1] - 1)

                # FIXME: expensive!!!
                # Remove the previous records contained by this span
                records = [record for record in records
                           if not _contains_span(span, record[0])]

                add = True
                for previous_record in records:
                    if ((span, single_keyword) == previous_record or
                            _contains_span(previous_record[0], span)):
                        # Match is contained by a previous match.
                        add = False
                        break

                if add:
                    records.append((span, single_keyword))

    # TODO - change to the requested format (I will return to it later)

    # List of single_keywords: {spans: single keyword}
    single_keywords = {}
    for span, single_keyword in records:
        single_keywords.setdefault(single_keyword, [[]])
        single_keywords[single_keyword][0].append(span)

    log.info("Matching single keywords... %d keywords found "
             "in %.1f sec." % (
        len(single_keywords), time.clock() - timer_start),
    )

    return single_keywords

# XXX - rebuild this whole thing
def get_composite_keywords(ckw_db, fulltext, skw_spans):
    """Returns a list of composite keywords bound with the number of
    occurrences found in the text string.
    @var ckw_db: list of KewordToken objects (they are supposed to be composite ones)
    @var fulltext: string to search in
    @skw_spans: dictionary of already identified single keywords
    @return : dictionary of matches in a format {
            <keyword object>, [[position, position...], [info_about_matches] ],
            ..
            }"""
    timer_start = time.clock()

    # Build the list of composite candidates
    ckw_out = {}
    skw_as_components = []

    for composite_keyword in ckw_db.values():
        # Counters for the composite keyword. First count is for the
        # number of occurrences in the whole document and second count
        # is for the human defined keywords.
        ckw_count = 0
        matched_spans = []

        # First search in the fulltext using the regex pattern of the whole
        # composite keyword (including the alternative labels)
        for regex in composite_keyword.regex:
            for match in regex.finditer(fulltext):
                span = list(match.span())
                span[1] -= 1
                span = tuple(span)
                if not span in matched_spans:
                    ckw_count += 1
                    matched_spans.append(span)

        # Get the single keywords locations.
        try:
            components = composite_keyword.compositeof
        except AttributeError:
            print(log.error("Cached ontology is corrupted. Please "
                            "remove the cached ontology in your temporary file."))
            raise Exception('Cached ontology is corrupted')

        spans = []
        try:
            spans = [skw_spans[component][0] for component in components]
        except KeyError:
            # Some of the keyword components are not to be found in the text.
            # Therefore we cannot continue because the match is incomplete.
            continue

        ckw_spans = []
        for index in range(len(spans) - 1):
            len_ckw = len(ckw_spans)
            if ckw_spans:  # cause ckw_spans include the previous
                previous_spans = ckw_spans
            else:
                previous_spans = spans[index]

            for new_span in [(span0, colmd1) for span0 in previous_spans
                             for colmd1 in spans[index + 1]]:
                span = _get_ckw_span(fulltext, new_span)
                if span is not None:
                    ckw_spans.append(span)

            # the spans must be overlapping to be included
            if index > 0 and ckw_spans:
                _ckw_spans = []
                for _span in ckw_spans[len_ckw:]:  # new spans
                    for _colmd2 in ckw_spans[:len_ckw]:
                        s = _span_overlapping(_span, _colmd2)
                        if s:
                            _ckw_spans.append(s)
                ckw_spans = _ckw_spans

        for span in [span for span in ckw_spans
                     if not span in matched_spans]:
            ckw_count += 1
            matched_spans.append(span)

        if ckw_count:
            # Gather the component counts.
            component_counts = []
            for component in components:
                skw_as_components.append(component)
                # Get the single keyword count.
                try:
                    component_counts.append(len(skw_spans[component][0]))
                except KeyError:
                    component_counts.append(0)

            # Store the composite keyword
            ckw_out[composite_keyword] = [matched_spans, component_counts]

    # Remove the single keywords that appear as components from the list
    # of single keywords.
    for skw in skw_as_components:
        try:
            del skw_spans[skw]
        except KeyError:
            pass

    # Remove the composite keywords that are fully present in
    # longer composite keywords
    _ckw_base = filter(lambda x: len(x.compositeof) == 2, ckw_out.keys())
    _ckw_extended = sorted(
        filter(lambda x: len(x.compositeof) > 2, ckw_out.keys()),
        key=lambda x: len(x.compositeof))
    if _ckw_extended:
        max_len = len(_ckw_extended[-1].compositeof)
        candidates = []
        for kw1 in _ckw_base:
            s1 = set(kw1.compositeof)
            for kw2 in _ckw_extended:
                s2 = set(kw2.compositeof)
                if s1.issubset(s2):
                    candidates.append((kw1, kw2))
                    #break  # don't stop because this keyword may be
                    # partly contained by kw_x and kw_y
        for i in range(len(_ckw_extended)):
            kw1 = _ckw_extended[i]
            s1 = set(kw1.compositeof)
            for ii in range(i + 1, len(_ckw_extended)):
                kw2 = _ckw_extended[ii]
                s2 = set(kw2.compositeof)
                if s1.issubset(s2):
                    candidates.append((kw1, kw2))
                    break
        if candidates:
            for kw1, kw2 in candidates:
                match1 = ckw_out[kw1] # subset of the kw2
                match2 = ckw_out[kw2]
                positions1 = match1[0]
                for pos1 in positions1:
                    for pos2 in match2[0]:
                        if _span_overlapping(pos1, pos2):
                            del positions1[positions1.index(pos1)]
                            if len(
                                    positions1) == 0: # if we removed all the matches
                                del ckw_out[kw1]  # also delete the keyword
                            break

    log.info("Matching composite keywords... %d keywords found "
             "in %.1f sec." % (len(ckw_out), time.clock() - timer_start),
    )

    return ckw_out


def get_author_keywords(skw_db, ckw_db, fulltext):
    """Finds out human defined keyowrds in a text string. Searches for
    the string "Keywords:" and its declinations and matches the
    following words."""
    timer_start = time.clock()
    out = {}

    split_string = bconfig.CFG_BIBCLASSIFY_AUTHOR_KW_START.split(fulltext, 1)
    if len(split_string) == 1:
        log.info("Matching author keywords... no keywords marker found.")
        return out

    kw_string = split_string[1]

    for regex in bconfig.CFG_BIBCLASSIFY_AUTHOR_KW_END:
        parts = regex.split(kw_string, 1)
        kw_string = parts[0]

    # We separate the keywords.
    author_keywords = bconfig.CFG_BIBCLASSIFY_AUTHOR_KW_SEPARATION.split(
        kw_string)

    log.info("Matching author keywords... %d keywords found in "
             "%.1f sec." % (len(author_keywords), time.clock() - timer_start))

    for kw in author_keywords:
        # If the author keyword is an acronym with capital letters
        # separated by points, remove the points.
        if re.match('([A-Z].)+$', kw):
            kw = kw.replace('.', '')

        # First try with the keyword as such, then lower it.
        kw_with_spaces = ' %s ' % kw
        matching_skw = get_single_keywords(skw_db, kw_with_spaces)
        matching_ckw = get_composite_keywords(ckw_db, kw_with_spaces,
                                              matching_skw)

        if matching_skw or matching_ckw:
            out[kw] = (matching_skw, matching_ckw)
            continue

        lowkw = kw.lower()

        matching_skw = get_single_keywords(skw_db, ' %s ' % lowkw)
        matching_ckw = get_composite_keywords(ckw_db, ' %s ' % lowkw,
                                              matching_skw)

        out[kw] = (matching_skw, matching_ckw)

    return out


def _get_ckw_span(fulltext, spans):
    """Returns the span of the composite keyword if it is valid. Returns
    None otherwise."""
    if spans[0] < spans[1]:
        words = (spans[0], spans[1])
        dist = spans[1][0] - spans[0][1]
    else:
        words = (spans[1], spans[0])
        dist = spans[0][0] - spans[1][1]

    if dist == 0:
        # Two keywords are adjacent. We have a match.
        return (min(words[0] + words[1]),
                max(words[0] + words[1])) #FIXME: huh, this is a bug?! a sum???
    elif dist <= _MAXIMUM_SEPARATOR_LENGTH:
        separator = fulltext[words[0][1]:words[1][0] + 1]
        # Check the separator.
        if separator.strip() in bconfig.CFG_BIBCLASSIFY_VALID_SEPARATORS:
            return (min(words[0] + words[1]), max(words[0] + words[1]))

    # There is no inclusion.
    return None


def _contains_span(span0, span1):
    """Return true if span0 contains span1, False otherwise."""
    if (span0 == span1 or
                span0[0] > span1[0] or
                span0[1] < span1[1]):
        return False
    return True


def _span_overlapping(aspan, bspan):
    # there are 6 posibilities, 2 are false
    if bspan[0] >= aspan[0]:
        if bspan[0] > aspan[1]:
            return
    else:
        if aspan[0] > bspan[1]:
            return
    return (min(aspan[0], bspan[0]), max(aspan[1], bspan[1]))
