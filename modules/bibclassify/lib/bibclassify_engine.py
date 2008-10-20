# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""
BibClassify engine.

This module is the main module of BibClassify. its two main methods are
output_keywords_for_sources and get_keywords_from_text. The first one output
keywords for a list of sources (local files or URLs, PDF or text) while the
second one outputs the keywords for text lines (which are obtained using the
module bibclassify_text_normalizer).

This module also takes care of the different outputs (text, MARCXML or HTML).
"""

import os
import random
import sys

try:
    from bibclassify_ontology_reader import get_regular_expressions
    from bibclassify_text_extractor import text_lines_from_local_file, \
        text_lines_from_url
    from bibclassify_text_normalizer import normalize_fulltext, cut_references
    from bibclassify_keyword_analyzer import get_single_keywords, \
        get_composite_keywords, get_author_keywords
    from bibclassify_config import CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER, \
        CFG_BIBCLASSIFY_PARTIAL_TEXT, CFG_BIBCLASSIFY_USER_AGENT
    from bibclassify_utils import write_message
except ImportError, err:
    print >> sys.stderr, "Import error: %s" % err
    sys.exit(0)

# Retrieve the custom configuration if it exists.
try:
    from bibclassify_config_local import *
except ImportError:
    # No local configuration was found.
    pass

_SKWS = {}
_CKWS = {}

def output_keywords_for_sources(input_sources, taxonomy, rebuild_cache=False,
    output_mode="text", output_limit=CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER,
    match_mode="full", no_cache=False, with_author_keywords=False,
    spires=False):
    """Outputs the keywords for each source in sources."""
    # Initialize cache
    global _SKWS
    global _CKWS
    _SKWS, _CKWS = get_regular_expressions(taxonomy, rebuild=rebuild_cache,
        no_cache=no_cache)

    # Get the fulltext for each source.
    for entry in input_sources:
        write_message("INFO: Trying input file %s." % entry, stream=sys.stderr,
            verbose=3)
        text_lines = None
        source = ""
        if os.path.isdir(entry):
            for filename in os.listdir(entry):
                if (os.path.isfile(entry + filename):
                    text_lines = text_lines_from_local_file(entry + filename)
                    if text_lines:
                        source = filename
        elif os.path.isfile(entry):
            text_lines = text_lines_from_local_file(entry)
            if text_lines:
                source = os.path.basename(entry)
        else:
            # Treat as a URL.
            text_lines = text_lines_from_url(entry,
                user_agent=CFG_BIBCLASSIFY_USER_AGENT)
            if text_lines:
                source = entry.split("/")[-1]

        if source:
            if output_mode == "text":
                print "Input file: %s" % source
            print get_keywords_from_text(text_lines,
                output_mode=output_mode,
                output_limit=output_limit,
                spires=spires,
                match_mode=match_mode,
                with_author_keywords=with_author_keywords)

def get_keywords_from_text(text_lines, taxonomy=None, output_mode="text",
    output_limit=CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER, spires=False,
    match_mode="full", no_cache=False, with_author_keywords=False,
    rebuild_cache=False):
    """Returns a formatted string containing the keywords for a single
    document."""
    if taxonomy is not None:
        global _SKWS
        global _CKWS
        _SKWS, _CKWS = get_regular_expressions(taxonomy, rebuild=rebuild_cache,
                no_cache=no_cache)

    text_lines = cut_references(text_lines)
    fulltext = normalize_fulltext("\n".join(text_lines))

    author_keywords = None
    if with_author_keywords:
        author_keywords = get_author_keywords(fulltext)

    if match_mode == "partial":
        fulltext = _get_partial_text(fulltext)

    single_keywords = get_single_keywords(_SKWS, fulltext)

    composite_keywords = get_composite_keywords(_CKWS, fulltext,
        single_keywords)

    return _get_keywords_output(single_keywords, composite_keywords,
        author_keywords, output_mode, output_limit, spires)

def _get_keywords_output(single_keywords, composite_keywords,
                        author_keywords=None, style="text",
                        output_limit=0, spires=False):
    """Returns a formatted string representing the keywords according
    to the style chosen."""

    # Filter the "nonstandalone" keywords from the single keywords.
    single_keywords = _filter_nostandalone(single_keywords)

    # Limit the number of keywords to the output limit.
    single_keywords = _resize_single_keywords(single_keywords, output_limit)
    composite_keywords = _resize_composite_keywords(composite_keywords,
        output_limit)

    if style == "text":
        return _output_text(single_keywords, composite_keywords,
            author_keywords, spires)
    elif style == "marcxml":
        return _output_marc(single_keywords, composite_keywords, spires)
    elif style == "html":
        return _output_html(single_keywords, composite_keywords, spires)

def _get_partial_text(fulltext):
    """Returns a shortened version of the fulltext used with the partial
    matching mode. The version is composed of 20% in the beginning and
    20% in the middle of the text."""
    length = len(fulltext)

    get_index = lambda x: int(float(x) / 100 * length)

    partial_text = [fulltext[get_index(start):get_index(end)]
                    for start, end in CFG_BIBCLASSIFY_PARTIAL_TEXT]

    return "\n".join(partial_text)

def _output_html(single_keywords, composite_keywords, spires=False):
    """Using the counts for each of the tags, write a simple HTML page
    to standard output containing a tag cloud representation. The CSS
    describes ten levels, each of which has differing font-size's,
    line-height's and font-weight's."""

    lines = []
    lines.append('''<html>
  <head>
    <title>Keyword Cloud</title>
    <style type="text/css">
      <!--
        a { color: #003DF5; text-decoration: none; }
        a:hover { color: #f1f1f1; text-decoration: none;
          background-color: #003DF5; }
        .pagebox { color: #000; margin-left: 1em; margin-bottom: 1em;
          border: 1px solid #000; padding: 1em;
          background-color: #f1f1f1; font-family: arial, sans-serif;
          max-width: 700px; margin: 10px; padding-left: 10px;
          float: left; }
        .pagebox1 { color: #B5B5B5; margin-left: 1em;
          margin-bottom: 1em; border: 1px dotted #B5B5B5;
          padding: 1em; background-color: #f2f2f2;
          font-family: arial, sans-serif; max-width: 300px;
          margin: 10px; padding-left: 10px; float: left; }
        .pagebox2 { color: #000; margin-left: 1em; margin-bottom: 1em;
          border: 0px solid #000; padding: 1em; font-size: x-small;
          font-family: arial, sans-serif; margin: 10px;
          padding-left: 10px; float: left; }''')

    level = (
'''        .level%d { color:#003DF5; font-size:%dpx; line-height:%dpx;
          font-weight:bold; }''')

    for index, size in enumerate(range(12, 40, 3)):
        lines.append(level % (index, size, size + 5))

    level_list = (10, 7.5, 5, 4, 3, 2, 1.7, 1.5, 1.3, 1)
    keyword = ('          <span class="level%d" style="color:%s !important">'
        '%s </span>')

    lines.append("      -->")
    lines.append("    </style>")
    lines.append("  </head>")
    lines.append("  <body>")
    lines.append("    <table>")
    lines.append("      <tr>")
    lines.append('        <div class="pagebox" align="top" />')

    tags = []

    max_counts = [len(single_keywords[0][1]), composite_keywords[0][1]]

    # Add the single tags
    color = "#b5b5b5"
    for subject, spans in single_keywords:
        for index, value in enumerate(level_list):
            if len(spans) <= max_counts[0] / value:
                if spires:
                    obj = _spires_label(subject)
                else:
                    obj = _SKWS[subject].concept
                obj = obj.replace(" ", "&#160")
                tags.append(keyword % (index, color, obj))
                break

    # Add the composite tags
    color = "#003df5"
    for subject, count, components in composite_keywords:
        for index, value in enumerate(level_list):
            if count <= max_counts[1] / value:
                if spires:
                    obj = _spires_label(subject)
                else:
                    obj = _CKWS[subject].concept
                obj = obj.replace(" ", "&#160")
                tags.append(keyword % (index, color, obj))
                break

    # Appends the keywords in a random way (in order to create the cloud
    # effect)
    while tags:
        index = random.randint(0, len(tags) - 1)
        lines.append(tags[index])
        tags[index] = tags[-1]
        del tags[-1]

    lines.append(" " * 8 + "</div>")
    lines.append(" " * 6 + "</tr>")
    lines.append(" " * 4 + "</table>")
    lines.append(" " * 2 + "</body>")
    lines.append("</html>")

    return "\n".join(lines)

def _output_marc(single_keywords, composite_keywords, spires=False):
    """Outputs the keywords in the MARCXML format."""
    marc_pattern = ('<datafield tag="653" ind1="1" ind2=" ">\n'
                    '    <subfield code="a">%s</subfield>\n'
                    '    <subfield code="9">BibClassify/HEP</subfield>\n'
                    '</datafield>\n')

    output = []

    for subject, spans in single_keywords:
        if spires:
            output.append(_spires_label(subject))
        else:
            output.append(_SKWS[subject].concept)

    for subject, count, components in composite_keywords:
        if spires:
            output.append(_spires_label(subject))
        else:
            output.append(_CKWS[subject].concept)

    return "".join([marc_pattern % keyword for keyword in output])

def _output_text(single_keywords=None, composite_keywords=None,
                author_keywords=None, spires=False):
    """Outputs the results obtained in text format."""
    output = []

    if author_keywords is not None:
        output.append("\nAuthor keywords:")
        for keyword in author_keywords:
            output.append(keyword)

    if composite_keywords is not None:
        output.append("\nComposite keywords:")
        for subject, count, components in composite_keywords:
            if spires:
                concept = _spires_label(subject)
            else:
                concept = _CKWS[subject].concept
            output.append("%d  %s %s" % (count, concept, components))

    if single_keywords is not None:
        output.append("\nSingle keywords:")
        for subject, spans in single_keywords:
            if spires:
                concept = _spires_label(subject)
            else:
                concept = _SKWS[subject].concept
            output.append("%d  %s" % (len(spans), concept))

    return "\n".join(output) + "\n"

def _filter_nostandalone(keywords):
    """Returns a copy of the keywords data structure stripped from its
    nonstandalone components."""
    filtered_keywords = {}

    for subject, spans in keywords.iteritems():
        if not _SKWS[subject].nostandalone:
            filtered_keywords[subject] = spans

    return filtered_keywords

def _single_keywords_comparator(skw0, skw1):
    """Compares 2 single keywords records. First compare the
    occurrences, then the length of the word."""
    list_comparison = cmp(len(skw1[1]), len(skw0[1]))
    if list_comparison:
        return list_comparison
    else:
        return cmp(len(skw1[0]), len(skw0[0]))

def _composite_keywords_comparator(ckw0, ckw1):
    """Compare 2 composite keywords records. First compare the
    occurrences, then the length of the word, at last the component
    counts."""
    count_comparison = cmp(ckw1[1], ckw0[1])
    if count_comparison:
        return count_comparison
    component_avg0 = sum(ckw0[2]) / len(ckw0[2])
    component_avg1 = sum(ckw1[2]) / len(ckw1[2])
    component_comparison =  cmp(component_avg1, component_avg0)
    if component_comparison:
        return component_comparison
    else:
        return cmp(len(ckw1[0]), len(ckw0[0]))

def _resize_single_keywords(keywords, limit=20):
    """Returns a resized version of data structures of keywords to the
    given length."""
    keywords = list(keywords.items())
    keywords.sort(_single_keywords_comparator)
    return keywords[:limit]

def _resize_composite_keywords(keywords, limit=20):
    """Returns a resized version of the composite_keywords list."""
    keywords.sort(_composite_keywords_comparator)
    return keywords[:limit]

def _spires_label(subject):
    """Returns the SPIRES representation of a keyword. If the
    spiresLabel is set, then it returns that value otherwise it replaces
    the colon in the prefLabel by a comma."""
    try:
        if subject in _SKWS:
            return _SKWS[subject].spires
    except AttributeError:
        # The keyword doesn't have a SPIRES label.
        return _SKWS[subject].concept

    try:
        return _CKWS[subject].spires
    except AttributeError:
        # The keyword doesn't have a SPIRES label. Build "comp1, comp2".
        components = _CKWS[subject].compositeof
        _spires_labels = [_spires_label(component) for component in components]
        return ", ".join(_spires_labels)

if __name__ == "__main__":
    write_message("ERROR: Please use bibclassify_cli from now on.",
        stream=sys.stderr, verbose=0)
