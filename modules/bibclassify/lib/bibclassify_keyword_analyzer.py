# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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
BibClassify keyword analyser.

This module contains methods to extract keywords from texts. It provides 3
different methods for 3 different types of keywords: single keywords, composite
keywords and author keywords.
"""

import re
import sys
import time

try:
    from bibclassify_config import CFG_BIBCLASSIFY_VALID_SEPARATORS, \
        CFG_BIBCLASSIFY_AUTHOR_KW_START, \
        CFG_BIBCLASSIFY_AUTHOR_KW_END, \
        CFG_BIBCLASSIFY_AUTHOR_KW_SEPARATION
    from bibclassify_utils import write_message
except ImportError, err:
    print >> sys.stderr, "Error: %s" % err
    sys.exit(1)

# Retrieve the custom configuration if it exists.
try:
    from bibclassify_config_local import *
except ImportError:
    # No local configuration was found.
    pass

_MAXIMUM_SEPARATOR_LENGTH = max([len(_separator)
    for _separator in CFG_BIBCLASSIFY_VALID_SEPARATORS])

def get_single_keywords(skw_db, fulltext, verbose=True):
    """Returns a dictionary of single keywords bound with the positions
    of the matches in the fulltext.
    Format of the output dictionary is (single keyword: positions)."""
    timer_start = time.clock()

    # Matched span -> single keyword
    records = []

    for single_keyword in skw_db:
        for regex in single_keyword.regex:
            for match in regex.finditer(fulltext):
                # Modify the right index to put it on the last letter
                # of the word.
                span = (match.span()[0], match.span()[1] - 1)

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

    # List of single_keywords: {spans: single keyword}
    single_keywords = {}
    for span, single_keyword in records:
        single_keywords.setdefault(single_keyword, []).append(span)

    if verbose:
        write_message("INFO: Matching single keywords... %d keywords found "
            "in %.1f sec." % (len(single_keywords), time.clock() - timer_start),
            stream=sys.stderr, verbose=3)

    return single_keywords

def get_composite_keywords(ckw_db, fulltext, skw_spans, verbose=True):
    """Returns a list of composite keywords bound with the number of
    occurrences found in the text string.
    Format of the output list is (composite keyword, count, component counts)."""
    timer_start = time.clock()

    # Build the list of composite candidates
    ckw_list = []
    skw_as_components = []

    for composite_keyword in ckw_db:
        # Counters for the composite keyword. First count is for the
        # number of occurrences in the whole document and second count
        # is for the human defined keywords.
        ckw_count = 0
        matched_spans = []

        # Check the alternative labels.
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
            print >> sys.stderr, ("Cached ontology is corrupted. Please "
                "remove the cached ontology in your temporary file.")
            sys.exit(1)
        try:
            spans = [skw_spans[component] for component in components]
        except KeyError:
            # The keyword components are not to be found in the text.
            # This is not a dramatic exception and we can safely ignore
            # it.
            pass
        else:
            ckw_spans = []
            for index in range(len(spans) - 1):
                if ckw_spans:
                    previous_spans = ckw_spans
                else:
                    previous_spans = spans[index]

                ckw_spans = []
                for new_span in [(span0, span1) for span0 in previous_spans
                                                for span1 in spans[index + 1]]:
                    span = _get_ckw_span(fulltext, new_span)
                    if span is not None:
                        ckw_spans.append(span)

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
                    component_counts.append(len(skw_spans[component]))
                except KeyError:
                    component_counts.append(0)

            # Store the composite keyword
            ckw_list.append((composite_keyword, ckw_count, component_counts))

    # Remove the single keywords that appear as components from the list
    # of single keywords.
    for skw in skw_as_components:
        try:
            del skw_spans[skw]
        except KeyError:
            pass

    if verbose:
        write_message("INFO: Matching composite keywords... %d keywords found "
            "in %.1f sec." % (len(ckw_list), time.clock() - timer_start),
            stream=sys.stderr, verbose=3)

    return ckw_list

def get_author_keywords(skw_db, ckw_db, fulltext):
    """Finds out human defined keyowrds in a text string. Searches for
    the string "Keywords:" and its declinations and matches the
    following words."""
    timer_start = time.clock()

    split_string = CFG_BIBCLASSIFY_AUTHOR_KW_START.split(fulltext, 1)
    if len(split_string) == 1:
        write_message("INFO: Matching author keywords... No keywords found.",
        stream=sys.stderr, verbose=3)
        return None

    kw_string = split_string[1]

    for regex in CFG_BIBCLASSIFY_AUTHOR_KW_END:
        parts = regex.split(kw_string, 1)
        kw_string = parts[0]

    # We separate the keywords.
    author_keywords = CFG_BIBCLASSIFY_AUTHOR_KW_SEPARATION.split(kw_string)

    write_message("INFO: Matching author keywords... %d keywords found in "
        "%.1f sec." % (len(author_keywords), time.clock() - timer_start),
        stream=sys.stderr, verbose=3)

    out = {}
    for kw in author_keywords:
        # If the author keyword is an acronym with capital letters
        # separated by points, remove the points.
        if re.match('([A-Z].)+$', kw):
            kw = kw.replace('.', '')

        # First try with the keyword as such, then lower it.
        kw_with_spaces = ' %s ' % kw
        matching_skw = get_single_keywords(skw_db, kw_with_spaces,
            verbose=False)
        matching_ckw = get_composite_keywords(ckw_db, kw_with_spaces,
            matching_skw, verbose=False)

        if matching_skw or matching_ckw:
            out[kw] = (matching_skw, matching_ckw)
            continue

        lowkw = kw.lower()

        matching_skw = get_single_keywords(skw_db, ' %s ' % lowkw, verbose=False)
        matching_ckw = get_composite_keywords(ckw_db, ' %s ' % lowkw,
            matching_skw, verbose=False)

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
        return (min(words[0] + words[1]), max(words[0] + words[1]))
    elif dist <= _MAXIMUM_SEPARATOR_LENGTH:
        separator = fulltext[words[0][1]:words[1][0] + 1]
        # Check the separator.
        if separator.strip() in CFG_BIBCLASSIFY_VALID_SEPARATORS:
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
