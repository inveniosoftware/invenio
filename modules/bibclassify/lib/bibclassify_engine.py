##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
    from bibclassify_utils import write_message, set_verbose_level
    from bibclassify_acronym_analyzer import get_acronyms
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
    spires=False, verbose=None, only_core_tags=False, extract_acronyms=False):
    """Outputs the keywords for each source in sources."""
    if verbose is not None:
        set_verbose_level(verbose)

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
                if os.path.isfile(entry + filename):
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

            keywords = get_keywords_from_text(text_lines,
                output_mode=output_mode,
                output_limit=output_limit,
                spires=spires,
                match_mode=match_mode,
                with_author_keywords=with_author_keywords,
                only_core_tags=only_core_tags)

            if extract_acronyms:
                acronyms = get_acronyms("\n".join(text_lines))
                if acronyms:
                    acronyms_str = ["\nAcronyms:"]
                    for acronym, expansions in acronyms.iteritems():
                        expansions_str = ", ".join(["%s (%d)" % expansion
                                                    for expansion in expansions])

                        acronyms_str.append("%s  %s" % (acronym, expansions_str))
                    acronyms_str = "\n".join(acronyms_str)
                else:
                    acronyms_str = "\nNo acronyms."

                print keywords + acronyms_str + "\n"
            else:
                print keywords

def output_keywords_for_local_file(local_file, taxonomy, rebuild_cache=False,
    output_mode="text", output_limit=CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER,
    match_mode="full", no_cache=False, with_author_keywords=False,
    spires=False, verbose=None):
    """Outputs the keywords for a local file."""
    if verbose is not None:
        set_verbose_level(verbose)

    write_message("INFO: Analyzing keywords for local file %s." % local_file,
        stream=sys.stderr, verbose=3)
    text_lines = text_lines_from_local_file(local_file)

    return get_keywords_from_text(text_lines,
        output_mode=output_mode,
        output_limit=output_limit,
        taxonomy=taxonomy,
        spires=spires,
        match_mode=match_mode,
        with_author_keywords=with_author_keywords,
        rebuild_cache=rebuild_cache,
        no_cache=no_cache)

def get_keywords_from_local_file(local_file, taxonomy, rebuild_cache=False,
    match_mode="full", no_cache=False, with_author_keywords=False):

    text_lines = text_lines_from_local_file(local_file)

    global _SKWS
    global _CKWS
    if not _SKWS:
        if taxonomy is not None:
            _SKWS, _CKWS = get_regular_expressions(taxonomy,
                rebuild=rebuild_cache, no_cache=no_cache)
        else:
            write_message("ERROR: Please specify an ontology in order to "
                "extract keywords.", stream=sys.stderr, verbose=1)

    text_lines = cut_references(text_lines)
    fulltext = normalize_fulltext("\n".join(text_lines))

    author_keywords = None
    if with_author_keywords:
        author_keywords = get_author_keywords(_SKWS, _CKWS, fulltext)

    if match_mode == "partial":
        fulltext = _get_partial_text(fulltext)

    single_keywords = get_single_keywords(_SKWS, fulltext)

    composite_keywords = get_composite_keywords(_CKWS, fulltext,
        single_keywords)

    return (single_keywords, composite_keywords)

def get_keywords_from_text(text_lines, taxonomy=None, output_mode="text",
    output_limit=CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER, spires=False,
    match_mode="full", no_cache=False, with_author_keywords=False,
    rebuild_cache=False, only_core_tags=False):
    """Returns a formatted string containing the keywords for a single
    document."""
    global _SKWS
    global _CKWS
    if not _SKWS:
        if taxonomy is not None:
            _SKWS, _CKWS = get_regular_expressions(taxonomy,
                rebuild=rebuild_cache, no_cache=no_cache)
        else:
            write_message("ERROR: Please specify an ontology in order to "
                "extract keywords.", stream=sys.stderr, verbose=1)

    text_lines = cut_references(text_lines)
    fulltext = normalize_fulltext("\n".join(text_lines))

    author_keywords = None
    if with_author_keywords:
        author_keywords = get_author_keywords(_SKWS, _CKWS, fulltext)

    if match_mode == "partial":
        fulltext = _get_partial_text(fulltext)

    single_keywords = get_single_keywords(_SKWS, fulltext)

    composite_keywords = get_composite_keywords(_CKWS, fulltext,
        single_keywords)

    return _get_keywords_output(single_keywords, composite_keywords, taxonomy,
        author_keywords, output_mode, output_limit, spires, only_core_tags)

def _get_keywords_output(single_keywords, composite_keywords, taxonomy,
    author_keywords=None, style="text", output_limit=0, spires=False,
    only_core_tags=False):
    """Returns a formatted string representing the keywords according
    to the style chosen."""

    # Filter the "nonstandalone" keywords from the single keywords.
    single_keywords = _filter_nostandalone(single_keywords)

    # Limit the number of keywords to the output limit.
    single_keywords = _get_sorted_skw_matches(single_keywords, output_limit)
    composite_keywords = _resize_ckw_matches(composite_keywords,
        output_limit)

    if style == "text":
        return _output_text(single_keywords, composite_keywords,
            author_keywords, spires, only_core_tags)
    elif style == "marcxml":
        return output_marc(single_keywords, composite_keywords, spires,
        taxonomy)
    elif style == "html":
        return _output_html(single_keywords, composite_keywords, spires)

def _get_author_keywords_output(author_keywords):
    """Formats the output for the author keywords."""
    out = []

    out.append("\nAuthor keywords:")

    for keyword, matches in author_keywords.items():
        skw_matches = matches[0]
        ckw_matches = matches[1]
        matches_str = []
        for ckw_match in ckw_matches:
            matches_str.append(ckw_match[0].concept)
        for skw_match in skw_matches.keys():
            matches_str.append(skw_match.concept)
        if matches_str:
            out.append('"%s" matches "' % keyword + '", "'.join(matches_str) +
                '".')
        else:
            out.append('"%s" matches no keyword.' % keyword)

    return '\n'.join(out)

def _get_partial_text(fulltext):
    """Returns a shortened version of the fulltext used with the partial
    matching mode. The version is composed of 20% in the beginning and
    20% in the middle of the text."""
    length = len(fulltext)

    get_index = lambda x: int(float(x) / 100 * length)

    partial_text = [fulltext[get_index(start):get_index(end)]
                    for start, end in CFG_BIBCLASSIFY_PARTIAL_TEXT]

    return "\n".join(partial_text)

def _output_fieldcodes_text(skw_matches, ckw_matches):
    """Returns the output for the field codes."""
    fieldcodes = {}
    output = []

    for skw, _ in skw_matches:
        for fieldcode in skw.fieldcodes:
            fieldcodes.setdefault(fieldcode, []).append(skw.concept)
    for ckw, _, _ in ckw_matches:
        for fieldcode in ckw.fieldcodes:
            fieldcodes.setdefault(fieldcode, []).append(ckw.concept)

    if fieldcodes:
        output.append('\nField codes:')
        for fieldcode, keywords in fieldcodes.items():
            output.append('%s: %s' % (fieldcode, ', '.join(keywords)))
        return '\n'.join(output)
    else:
        return ''

def _output_core_keywords_text(skw_matches, ckw_matches):
    """Returns the output for the core tags."""
    output, core_keywords = [], []

    for skw, _ in skw_matches:
        if skw.core:
            core_keywords.append(skw.concept)
    for ckw, _, _ in ckw_matches:
        if ckw.core:
            core_keywords.append(ckw.concept)

    if core_keywords:
        output.append("\n%d core keywords:" % len(core_keywords))
        for core_keyword in core_keywords:
            output.append(core_keyword)
    else:
        output.append("\nNo core keywords.")

    return '\n'.join(output)

def _output_html(skw_matches, ckw_matches, spires=False):
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

    max_counts = [len(skw_matches[0][1]), ckw_matches[0][1]]

    # Add the single tags
    color = "#b5b5b5"
    for single_keyword, spans in skw_matches:
        for index, value in enumerate(level_list):
            if len(spans) <= max_counts[0] / value:
                obj = single_keyword.output(spires)
                obj = obj.replace(" ", "&#160")
                tags.append(keyword % (index, color, obj))
                break

    # Add the composite tags
    color = "#003df5"
    for composite_keyword, count, components in ckw_matches:
        for index, value in enumerate(level_list):
            if count <= max_counts[1] / value:
                obj = composite_keyword.output(spires)
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

    lines.append('        </div>\n'
                 '      </tr>\n'
                 '    </table>\n'
                 '  </body>\n'
                 '</html>')

    return "\n".join(lines)

def output_marc(skw_matches, ckw_matches, spires=False, taxonomy='HEP'):
    """Outputs the keywords in the MARCXML format."""
    marc_pattern = ('<datafield tag="653" ind1="1" ind2=" ">\n'
                    '    <subfield code="a">%s</subfield>\n'
                    '    <subfield code="n">%d</subfield>\n'
                    '    <subfield code="9">BibClassify/%s</subfield>\n'
                    '</datafield>\n')

    output = []

    #FIXME this is really bad.
    if type(skw_matches) is list:
        for single_keyword, spans in skw_matches:
            concept = single_keyword.output(spires)
            output.append((concept, len(spans)))
    else:
        for single_keyword, spans in skw_matches.items():
            concept = single_keyword.output(spires)
            output.append((concept, len(spans)))

    for composite_keyword, count, components in ckw_matches:
        concept = composite_keyword.output(spires)
        output.append((concept, count))

    # Transform the taxonomy name into something readable.
    taxonomy = os.path.basename(taxonomy)
    if taxonomy.endswith('.rdf'):
        taxonomy = taxonomy.rstrip('.rdf')

    return "".join([marc_pattern % (keyword, count, taxonomy)
                    for keyword, count in output])

def _output_text(skw_matches=None, ckw_matches=None, author_keywords=None,
    spires=False, only_core_tags=False):
    """Outputs the results obtained in text format."""
    output = []

    if author_keywords is not None:
        output.append(_get_author_keywords_output(author_keywords))

    if ckw_matches is not None:
        output.append("\nComposite keywords:")
        for composite_keyword, count, components in ckw_matches:
            concept = composite_keyword.output(spires)
            output.append("%d  %s %s" % (count, concept, components))

    if skw_matches is not None:
        output.append("\nSingle keywords:")
        for single_keyword, spans in skw_matches:
            concept = single_keyword.output(spires)
            output.append("%d  %s" % (len(spans), concept))

    core_keywords = _output_core_keywords_text(skw_matches, ckw_matches)
    if core_keywords:
        output.append(core_keywords)

    fieldcodes = _output_fieldcodes_text(skw_matches, ckw_matches)
    if fieldcodes:
        output.append(fieldcodes)

    return "\n".join(output) + "\n"

def _filter_nostandalone(kw_matches):
    """Returns a copy of the keywords data structure stripped from its
    nonstandalone components."""
    filtered_kw_matches = {}

    for kw_match, spans in kw_matches.iteritems():
        if not kw_match.nostandalone:
            filtered_kw_matches[kw_match] = spans

    return filtered_kw_matches

def _skw_matches_comparator(skw0_matches, skw1_matches):
    """
    Compares 2 single keywords matches (single_keyword, spans). First
    compare the occurrences, then the length of the word.
    """
    list_comparison = cmp(len(skw1_matches[1]), len(skw0_matches[1]))
    if list_comparison:
        return list_comparison
    else:
        return cmp(len(skw1_matches[0].concept), len(skw0_matches[0].concept))

def _ckw_matches_comparator(ckw0_match, ckw1_match):
    """
    Compares 2 composite keywords matches (composite_keyword, spans,
    components). First compare the occurrences, then the length of
    the word, at last the component counts.
    """
    count_comparison = cmp(ckw1_match[1], ckw0_match[1])
    if count_comparison:
        return count_comparison
    component_avg0 = sum(ckw0_match[2]) / len(ckw0_match[2])
    component_avg1 = sum(ckw1_match[2]) / len(ckw1_match[2])
    component_comparison =  cmp(component_avg1, component_avg0)
    if component_comparison:
        return component_comparison
    else:
        return cmp(len(ckw1_match[0].concept), len(ckw0_match[0].concept))

def _get_sorted_skw_matches(skw_matches, limit=20):
    """Returns a resized version of data structures of keywords to the
    given length."""
    sorted_keywords = list(skw_matches.items())
    sorted_keywords.sort(_skw_matches_comparator)
    return limit and sorted_keywords[:limit] or sorted_keywords

def _resize_ckw_matches(keywords, limit=20):
    """Returns a resized version of the composite_keywords list."""
    keywords.sort(_ckw_matches_comparator)
    return limit and keywords[:limit] or keywords

if __name__ == "__main__":
    write_message("ERROR: Please use bibclassify_cli from now on.",
        stream=sys.stderr, verbose=0)
