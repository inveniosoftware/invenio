# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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
BibClassify engine.

This module is the main module of BibClassify. its two main methods are
output_keywords_for_sources and get_keywords_from_text. The first one output
keywords for a list of sources (local files or URLs, PDF or text) while the
second one outputs the keywords for text lines (which are obtained using the
module bibclassify_text_normalizer).

This module also takes care of the different outputs (text, MARCXML or HTML).
But unfortunately there is a confusion between running in a standalone mode
and producing output suitable for printing, and running in a web-based
mode where the webtemplate is used. For the moment the pieces of the representation
code are left in this module.
"""

from __future__ import print_function

import os
import re
from six import iteritems
import config as bconfig

from invenio.legacy.bibclassify import ontology_reader as reader
import text_extractor as extractor
import text_normalizer as normalizer
import keyword_analyzer as keyworder
import acronym_analyzer as acronymer

from invenio.utils.text import encode_for_xml
from invenio.utils.filedownload import download_url

log = bconfig.get_logger("bibclassify.engine")

# ---------------------------------------------------------------------
#                          API
# ---------------------------------------------------------------------


def output_keywords_for_sources(input_sources, taxonomy_name, output_mode="text",
                                output_limit=bconfig.CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER, spires=False,
                                match_mode="full", no_cache=False, with_author_keywords=False,
                                rebuild_cache=False, only_core_tags=False, extract_acronyms=False,
                                api=False, **kwargs):
    """Output the keywords for each source in sources."""
    from invenio.legacy.refextract.engine import get_plaintext_document_body

    # Inner function which does the job and it would be too much work to
    # refactor the call (and it must be outside the loop, before it did
    # not process multiple files)
    def process_lines():
        if output_mode == "text":
            print("Input file: %s" % source)

        line_nb = len(text_lines)
        word_nb = 0
        for line in text_lines:
            word_nb += len(re.findall("\S+", line))

        log.info("Remote file has %d lines and %d words." % (line_nb, word_nb))
        output = get_keywords_from_text(
            text_lines,
            taxonomy_name,
            output_mode=output_mode,
            output_limit=output_limit,
            spires=spires,
            match_mode=match_mode,
            no_cache=no_cache,
            with_author_keywords=with_author_keywords,
            rebuild_cache=rebuild_cache,
            only_core_tags=only_core_tags,
            extract_acronyms=extract_acronyms
        )
        if api:
            return output
        else:
            if isinstance(output, dict):
                for i in output:
                    print(output[i])

    # Get the fulltext for each source.
    for entry in input_sources:
        log.info("Trying to read input file %s." % entry)
        text_lines = None
        source = ""
        if os.path.isdir(entry):
            for filename in os.listdir(entry):
                if filename.startswith('.'):
                    continue
                filename = os.path.join(entry, filename)
                if os.path.isfile(filename):
                    text_lines, dummy = get_plaintext_document_body(filename)
                    if text_lines:
                        source = filename
                        process_lines()
        elif os.path.isfile(entry):
            text_lines, dummy = get_plaintext_document_body(entry)
            if text_lines:
                source = os.path.basename(entry)
                process_lines()
        else:
            # Treat as a URL.
            local_file = download_url(entry)
            text_lines, dummy = get_plaintext_document_body(local_file)
            if text_lines:
                source = entry.split("/")[-1]
                process_lines()


def get_keywords_from_local_file(local_file, taxonomy_name, output_mode="text",
                                 output_limit=bconfig.CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER, spires=False,
                                 match_mode="full", no_cache=False, with_author_keywords=False,
                                 rebuild_cache=False, only_core_tags=False, extract_acronyms=False, api=False,
                                 **kwargs):
    """Output keywords reading a local file.

    Arguments and output are the same as for :see: get_keywords_from_text().
    """
    log.info("Analyzing keywords for local file %s." % local_file)
    text_lines = extractor.text_lines_from_local_file(local_file)

    return get_keywords_from_text(text_lines,
                                  taxonomy_name,
                                  output_mode=output_mode,
                                  output_limit=output_limit,
                                  spires=spires,
                                  match_mode=match_mode,
                                  no_cache=no_cache,
                                  with_author_keywords=with_author_keywords,
                                  rebuild_cache=rebuild_cache,
                                  only_core_tags=only_core_tags,
                                  extract_acronyms=extract_acronyms)


def get_keywords_from_text(text_lines, taxonomy_name, output_mode="text",
                           output_limit=bconfig.CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER,
                           spires=False, match_mode="full", no_cache=False,
                           with_author_keywords=False, rebuild_cache=False,
                           only_core_tags=False, extract_acronyms=False,
                           **kwargs):
    """Extract keywords from the list of strings.

    :param text_lines: list of strings (will be normalized before being
        joined into one string)
    :param taxonomy_name: string, name of the taxonomy_name
    :param output_mode: string - text|html|marcxml|raw
    :param output_limit: int
    :param spires: boolean, if True marcxml output reflect spires codes.
    :param match_mode: str - partial|full; in partial mode only
        beginning of the fulltext is searched.
    :param no_cache: boolean, means loaded definitions will not be saved.
    :param with_author_keywords: boolean, extract keywords from the pdfs.
    :param rebuild_cache: boolean
    :param only_core_tags: boolean
    :return: if output_mode=raw, it will return
        (single_keywords, composite_keywords, author_keywords, acronyms)
        for other output modes it returns formatted string
    """
    cache = reader.get_cache(taxonomy_name)
    if not cache:
        reader.set_cache(taxonomy_name,
                         reader.get_regular_expressions(taxonomy_name,
                                                        rebuild=rebuild_cache,
                                                        no_cache=no_cache))
        cache = reader.get_cache(taxonomy_name)
    _skw = cache[0]
    _ckw = cache[1]
    text_lines = normalizer.cut_references(text_lines)
    fulltext = normalizer.normalize_fulltext("\n".join(text_lines))

    if match_mode == "partial":
        fulltext = _get_partial_text(fulltext)
    author_keywords = None
    if with_author_keywords:
        author_keywords = extract_author_keywords(_skw, _ckw, fulltext)
    acronyms = {}
    if extract_acronyms:
        acronyms = extract_abbreviations(fulltext)

    single_keywords = extract_single_keywords(_skw, fulltext)
    composite_keywords = extract_composite_keywords(_ckw, fulltext, single_keywords)

    if only_core_tags:
        single_keywords = clean_before_output(_filter_core_keywors(single_keywords))
        composite_keywords = _filter_core_keywors(composite_keywords)
    else:
        # Filter out the "nonstandalone" keywords
        single_keywords = clean_before_output(single_keywords)
    return get_keywords_output(single_keywords, composite_keywords, taxonomy_name,
                               author_keywords, acronyms, output_mode, output_limit,
                               spires, only_core_tags)


def extract_single_keywords(skw_db, fulltext):
    """Find single keywords in the fulltext.

    :var skw_db: list of KeywordToken objects
    :var fulltext: string, which will be searched
    :return : dictionary of matches in a format {
            <keyword object>, [[position, position...], ],
            ..
            }
            or empty {}
    """
    return keyworder.get_single_keywords(skw_db, fulltext) or {}


def extract_composite_keywords(ckw_db, fulltext, skw_spans):
    """Returns a list of composite keywords bound with the number of
    occurrences found in the text string.
    :var ckw_db: list of KewordToken objects (they are supposed to be composite ones)
    :var fulltext: string to search in
    :skw_spans: dictionary of already identified single keywords
    :return : dictionary of matches in a format {
            <keyword object>, [[position, position...], [info_about_matches] ],
            ..
            }
            or empty {}
    """
    return keyworder.get_composite_keywords(ckw_db, fulltext, skw_spans) or {}


def extract_abbreviations(fulltext):
    """Extract acronyms from the fulltext
    :var fulltext: utf-8 string
    :return: dictionary of matches in a formt {
          <keyword object>, [matched skw or ckw object, ....]
          }
          or empty {}
    """
    acronyms = {}
    K = reader.KeywordToken
    for k, v in acronymer.get_acronyms(fulltext).items():
        acronyms[K(k, type='acronym')] = v
    return acronyms


def extract_author_keywords(skw_db, ckw_db, fulltext):
    """Finds out human defined keyowrds in a text string. Searches for
    the string "Keywords:" and its declinations and matches the
    following words.

    :var skw_db: list single kw object
    :var ckw_db: list of composite kw objects
    :var fulltext: utf-8 string
    :return: dictionary of matches in a formt {
          <keyword object>, [matched skw or ckw object, ....]
          }
          or empty {}
    """
    akw = {}
    K = reader.KeywordToken
    for k, v in keyworder.get_author_keywords(skw_db, ckw_db, fulltext).items():
        akw[K(k, type='author-kw')] = v
    return akw


# ---------------------------------------------------------------------
#                          presentation functions
# ---------------------------------------------------------------------


def get_keywords_output(single_keywords, composite_keywords, taxonomy_name,
                        author_keywords=None, acronyms=None, style="text", output_limit=0,
                        spires=False, only_core_tags=False):
    """Returns a formatted string representing the keywords according
    to the chosen style. This is the main routing call, this function will
    also strip unwanted keywords before output and limits the number
    of returned keywords
    :var single_keywords: list of single keywords
    :var composite_keywords: list of composite keywords
    :var taxonomy_name: string, taxonomy name
    :keyword author_keywords: dictionary of author keywords extracted from fulltext
    :keyword acronyms: dictionary of extracted acronyms
    :keyword style: text|html|marc
    :keyword output_limit: int, number of maximum keywords printed (it applies
            to single and composite keywords separately)
    :keyword spires: boolen meaning spires output style
    :keyword only_core_tags: boolean
    """
    categories = {}
    # sort the keywords, but don't limit them (that will be done later)
    single_keywords_p = _sort_kw_matches(single_keywords)

    composite_keywords_p = _sort_kw_matches(composite_keywords)

    for w in single_keywords_p:
        categories[w[0].concept] = w[0].type
    for w in single_keywords_p:
        categories[w[0].concept] = w[0].type

    complete_output = _output_complete(single_keywords_p, composite_keywords_p,
                                       author_keywords, acronyms, spires,
                                       only_core_tags, limit=output_limit)
    functions = {"text": _output_text, "marcxml": _output_marc, "html":
                 _output_html, "dict": _output_dict}
    my_styles = {}

    for s in style:
        if s != "raw":
            my_styles[s] = functions[s](complete_output, categories)
        else:
            if output_limit > 0:
                my_styles["raw"] = (_kw(_sort_kw_matches(single_keywords, output_limit)),
                                    _kw(_sort_kw_matches(composite_keywords, output_limit)),
                                    author_keywords,  # this we don't limit (?)
                                    _kw(_sort_kw_matches(acronyms, output_limit)))
            else:
                my_styles["raw"] = (single_keywords_p, composite_keywords_p, author_keywords, acronyms)

    return my_styles


def build_marc(recid, single_keywords, composite_keywords,
               spires=False, author_keywords=None, acronyms=None):
    """Create xml record.

    :var recid: ingeter
    :var single_keywords: dictionary of kws
    :var composite_keywords: dictionary of kws
    :keyword spires: please don't use, left for historical
        reasons
    :keyword author_keywords: dictionary of extracted keywords
    :keyword acronyms: dictionary of extracted acronyms
    :return: str, marxml
    """
    output = ['<collection><record>\n'
              '<controlfield tag="001">%s</controlfield>' % recid]

    # no need to sort
    single_keywords = single_keywords.items()
    composite_keywords = composite_keywords.items()

    output.append(_output_marc(single_keywords, composite_keywords, author_keywords, acronyms))

    output.append('</record></collection>')

    return '\n'.join(output)


def _output_marc(output_complete, categories, kw_field=bconfig.CFG_MAIN_FIELD,
                 auth_field=bconfig.CFG_AUTH_FIELD, acro_field=bconfig.CFG_ACRON_FIELD,
                 provenience='BibClassify'):
    """Output the keywords in the MARCXML format.

    :var skw_matches: list of single keywords
    :var ckw_matches: list of composite keywords
    :var author_keywords: dictionary of extracted author keywords
    :var acronyms: dictionary of acronyms
    :var spires: boolean, True=generate spires output - BUT NOTE: it is
            here only not to break compatibility, in fact spires output
            should never be used for xml because if we read marc back
            into the KeywordToken objects, we would not find them
    :keyword provenience: string that identifies source (authority) that
        assigned the contents of the field
    :return: string, formatted MARC"""

    kw_template = ('<datafield tag="%s" ind1="%s" ind2="%s">\n'
                   '    <subfield code="2">%s</subfield>\n'
                   '    <subfield code="a">%s</subfield>\n'
                   '    <subfield code="n">%s</subfield>\n'
                   '    <subfield code="9">%s</subfield>\n'
                   '</datafield>\n')

    output = []

    tag, ind1, ind2 = _parse_marc_code(kw_field)
    for keywords in (output_complete["Single keywords"], output_complete["Core keywords"]):
        for kw in keywords:
            output.append(kw_template % (tag, ind1, ind2, encode_for_xml(provenience),
                                         encode_for_xml(kw), keywords[kw],
                                         encode_for_xml(categories[kw])))

    for field, keywords in ((auth_field, output_complete["Author keywords"]),
                            (acro_field, output_complete["Acronyms"])):
        if keywords and len(keywords) and field:  # field='' we shall not save the keywords
            tag, ind1, ind2 = _parse_marc_code(field)
            for kw, info in keywords.items():
                output.append(kw_template % (tag, ind1, ind2, encode_for_xml(provenience),
                                             encode_for_xml(kw), '', encode_for_xml(categories[kw])))

    return "".join(output)


def _output_complete(skw_matches=None, ckw_matches=None, author_keywords=None,
                     acronyms=None, spires=False, only_core_tags=False,
                     limit=bconfig.CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER):

    if limit:
        resized_skw = skw_matches[0:limit]
        resized_ckw = ckw_matches[0:limit]
    else:
        resized_skw = skw_matches
        resized_ckw = ckw_matches

    results = {"Core keywords": _get_core_keywords(skw_matches, ckw_matches, spires=spires)}

    if not only_core_tags:
        results["Author keywords"] = _get_author_keywords(author_keywords, spires=spires)
        results["Composite keywords"] = _get_compositekws(resized_ckw, spires=spires)
        results["Single keywords"] = _get_singlekws(resized_skw, spires=spires)
        results["Field codes"] = _get_fieldcodes(resized_skw, resized_ckw, spires=spires)
        results["Acronyms"] = _get_acronyms(acronyms)

    return results


def _output_dict(complete_output, categories):
    return {
        "complete_output": complete_output,
        "categories": categories
    }


def _output_text(complete_output, categories):
    """Output the results obtained in text format.


    :return: str, html formatted output
    """
    output = ""

    for result in complete_output:
        list_result = complete_output[result]
        if list_result:
            list_result_sorted = sorted(list_result, key=lambda x: list_result[x],
                                        reverse=True)
            output += "\n\n{0}:\n".format(result)
            for element in list_result_sorted:
                output += "\n{0} {1}".format(list_result[element], element)

    output += "\n--\n{0}".format(_signature())

    return output


def _output_html(complete_output, categories):
    """Output the same as txt output does, but HTML formatted.

    :var skw_matches: sorted list of single keywords
    :var ckw_matches: sorted list of composite keywords
    :var author_keywords: dictionary of extracted author keywords
    :var acronyms: dictionary of acronyms
    :var spires: boolean
    :var only_core_tags: boolean
    :keyword limit: int, number of printed keywords
    :return: str, html formatted output
    """
    return """<html>
    <head>
      <title>Automatically generated keywords by bibclassify</title>
    </head>
    <body>
    {0}
    </body>
    </html>""".format(
        _output_text(complete_output).replace('\n', '<br>')
    ).replace('\n', '')


def _get_singlekws(skw_matches, spires=False):
    """
    :var skw_matches: dict of {keyword: [info,...]}
    :keyword spires: bool, to get the spires output
    :return: list of formatted keywords
    """
    output = {}
    for single_keyword, info in skw_matches:
        output[single_keyword.output(spires)] = len(info[0])
    return output


def _get_compositekws(ckw_matches, spires=False):
    """
    :var ckw_matches: dict of {keyword: [info,...]}
    :keyword spires: bool, to get the spires output
    :return: list of formatted keywords
    """
    output = {}
    for composite_keyword, info in ckw_matches:
        output[composite_keyword.output(spires)] = {"numbers": len(info[0]),
                                                    "details": info[1]}
    return output


def _get_acronyms(acronyms):
    """Return a formatted list of acronyms."""
    acronyms_str = {}
    if acronyms:
        for acronym, expansions in iteritems(acronyms):
            expansions_str = ", ".join(["%s (%d)" % expansion
                                        for expansion in expansions])
            acronyms_str[acronym] = expansions_str

    return acronyms


def _get_author_keywords(author_keywords, spires=False):
    """Format the output for the author keywords.

    :return: list of formatted author keywors
    """
    out = {}
    if author_keywords:
        for keyword, matches in author_keywords.items():
            skw_matches = matches[0]  # dictionary of single keywords
            ckw_matches = matches[1]  # dict of composite keywords
            matches_str = []
            for ckw, spans in ckw_matches.items():
                matches_str.append(ckw.output(spires))
            for skw, spans in skw_matches.items():
                matches_str.append(skw.output(spires))
            if matches_str:
                out[keyword] = matches_str
            else:
                out[keyword] = 0

    return out


def _get_fieldcodes(skw_matches, ckw_matches, spires=False):
    """Return the output for the field codes.

    :var skw_matches: dict of {keyword: [info,...]}
    :var ckw_matches: dict of {keyword: [info,...]}
    :keyword spires: bool, to get the spires output
    :return: string"""
    fieldcodes = {}
    output = {}

    for skw, _ in skw_matches:
        for fieldcode in skw.fieldcodes:
            fieldcodes.setdefault(fieldcode, set()).add(skw.output(spires))
    for ckw, _ in ckw_matches:

        if len(ckw.fieldcodes):
            for fieldcode in ckw.fieldcodes:
                fieldcodes.setdefault(fieldcode, set()).add(ckw.output(spires))
        else:  # inherit field-codes from the composites
            for kw in ckw.getComponents():
                for fieldcode in kw.fieldcodes:
                    fieldcodes.setdefault(fieldcode, set()).add('%s*' % ckw.output(spires))
                    fieldcodes.setdefault('*', set()).add(kw.output(spires))

    for fieldcode, keywords in fieldcodes.items():
        output[fieldcode] = ', '.join(keywords)

    return output


def _get_core_keywords(skw_matches, ckw_matches, spires=False):
    """Return the output for the field codes.

    :var skw_matches: dict of {keyword: [info,...]}
    :var ckw_matches: dict of {keyword: [info,...]}
    :keyword spires: bool, to get the spires output
    :return: set of formatted core keywords
    """
    output = {}
    category = {}

    def _get_value_kw(kw):
        """Help to sort the Core keywords."""
        i = 0
        while kw[i].isdigit():
            i += 1
        if i > 0:
            return int(kw[:i])
        else:
            return 0

    for skw, info in skw_matches:
        if skw.core:
            output[skw.output(spires)] = len(info[0])
            category[skw.output(spires)] = skw.type
    for ckw, info in ckw_matches:
        if ckw.core:
            output[ckw.output(spires)] = len(info[0])
        else:
            #test if one of the components is  not core
            i = 0
            for c in ckw.getComponents():
                if c.core:
                    output[c.output(spires)] = info[1][i]
                i += 1
    return output


def _filter_core_keywors(keywords):
    matches = {}
    for kw, info in keywords.items():
        if kw.core:
            matches[kw] = info
    return matches


def _signature():
    """Print out the bibclassify signature.

    #todo: add information about taxonomy, rdflib"""

    return 'bibclassify v%s' % (bconfig.VERSION,)


def clean_before_output(kw_matches):
    """Return a clean copy of the keywords data structure.

    Stripped off the standalone and other unwanted elements"""
    filtered_kw_matches = {}

    for kw_match, info in iteritems(kw_matches):
        if not kw_match.nostandalone:
            filtered_kw_matches[kw_match] = info

    return filtered_kw_matches

# ---------------------------------------------------------------------
#                          helper functions
# ---------------------------------------------------------------------


def _skw_matches_comparator(kw0, kw1):
    """
    Compare 2 single keywords objects.

    First by the number of their spans (ie. how many times they were found),
    if it is equal it compares them by lenghts of their labels.
    """
    list_comparison = cmp(len(kw1[1][0]), len(kw0[1][0]))
    if list_comparison:
        return list_comparison

    if kw0[0].isComposite() and kw1[0].isComposite():
        component_avg0 = sum(kw0[1][1]) / len(kw0[1][1])
        component_avg1 = sum(kw1[1][1]) / len(kw1[1][1])
        component_comparison = cmp(component_avg1, component_avg0)
        if component_comparison:
            return component_comparison

    return cmp(len(str(kw1[0])), len(str(kw0[0])))


def _kw(keywords):
    """Turn list of keywords into dictionary."""
    r = {}
    for k, v in keywords:
        r[k] = v
    return r


def _sort_kw_matches(skw_matches, limit=0):
    """Return a resized version of keywords to the given length."""
    sorted_keywords = list(skw_matches.items())
    sorted_keywords.sort(_skw_matches_comparator)
    return limit and sorted_keywords[:limit] or sorted_keywords


def _get_partial_text(fulltext):
    """
    Return a short version of the fulltext used with the partial matching mode.

    The version is composed of 20% in the beginning and 20% in the middle of the
    text."""
    length = len(fulltext)

    get_index = lambda x: int(float(x) / 100 * length)

    partial_text = [fulltext[get_index(start):get_index(end)]
                    for start, end in bconfig.CFG_BIBCLASSIFY_PARTIAL_TEXT]

    return "\n".join(partial_text)


def save_keywords(filename, xml):
    tmp_dir = os.path.dirname(filename)
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    file_desc = open(filename, "w")
    file_desc.write(xml)
    file_desc.close()


def get_tmp_file(recid):
    tmp_directory = "%s/bibclassify" % bconfig.CFG_TMPDIR
    if not os.path.isdir(tmp_directory):
        os.mkdir(tmp_directory)
    filename = "bibclassify_%s.xml" % recid
    abs_path = os.path.join(tmp_directory, filename)
    return abs_path


def _parse_marc_code(field):
    """Parse marc field and return default indicators if not filled in."""
    field = str(field)
    if len(field) < 4:
        raise Exception('Wrong field code: %s' % field)
    else:
        field += '__'
    tag = field[0:3]
    ind1 = field[3].replace('_', '')
    ind2 = field[4].replace('_', '')
    return tag, ind1, ind2


if __name__ == "__main__":
    log.error("Please use bibclassify_cli from now on.")
