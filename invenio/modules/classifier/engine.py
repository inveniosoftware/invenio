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

"""Classifier engine responsible for outputting keywords from various sources.

These sources can be PDF documents, general text, path to files or lines of
text and keywords are outputted in different formats (text, MARCXML or HTML).
"""

from __future__ import print_function

import os

from invenio.base.globals import cfg
from invenio.utils.text import encode_for_xml

from six import iteritems

from .acronymer import get_acronyms
from .keyworder import (
    get_author_keywords,
    get_composite_keywords,
    get_single_keywords,
)
from .reader import KeywordToken


def extract_single_keywords(skw_db, fulltext):
    """Find single keywords in the fulltext.

    :param skw_db: list of KeywordToken objects
    :param fulltext: string, which will be searched
    :return : dictionary of matches in a format {
            <keyword object>, [[position, position...], ],
            ..
            }
            or empty {}
    """
    return get_single_keywords(skw_db, fulltext) or {}


def extract_composite_keywords(ckw_db, fulltext, skw_spans):
    """Return a list of composite keywords bound with the number of occurrences.

    :param ckw_db: list of KewordToken objects (they are supposed to be composite ones)
    :param fulltext: string to search in
    :param skw_spans: dictionary of already identified single keywords

    :return : dictionary of matches in a format {
            <keyword object>, [[position, position...], [info_about_matches] ],
            ..
            }
            or empty {}
    """
    return get_composite_keywords(ckw_db, fulltext, skw_spans) or {}


def extract_abbreviations(fulltext):
    """Extract acronyms from the fulltext.

    :param fulltext: utf-8 string
    :return: dictionary of matches in a formt {
          <keyword object>, [matched skw or ckw object, ....]
          }
          or empty {}
    """
    acronyms = {}
    for k, v in get_acronyms(fulltext).items():
        acronyms[KeywordToken(k, type='acronym')] = v
    return acronyms


def extract_author_keywords(skw_db, ckw_db, fulltext):
    """Find out human defined keywords in a text string.

    Searches for the string "Keywords:" and its declinations and matches the
    following words.

    :param skw_db: list single kw object
    :param ckw_db: list of composite kw objects
    :param fulltext: utf-8 string
    :return: dictionary of matches in a formt {
          <keyword object>, [matched skw or ckw object, ....]
          }
          or empty {}
    """
    akw = {}
    for k, v in get_author_keywords(skw_db, ckw_db, fulltext).items():
        akw[KeywordToken(k, type='author-kw')] = v
    return akw


def get_keywords_output(single_keywords, composite_keywords, taxonomy_name,
                        author_keywords=None, acronyms=None, output_mode="text",
                        output_limit=0, spires=False, only_core_tags=False):
    """Return a formatted string representing the keywords in the chosen style.

    This is the main routing call, this function will
    also strip unwanted keywords before output and limits the number
    of returned keywords.

    :param single_keywords: list of single keywords
    :param composite_keywords: list of composite keywords
    :param taxonomy_name: string, taxonomy name
    :param author_keywords: dictionary of author keywords extracted from fulltext
    :param acronyms: dictionary of extracted acronyms
    :param output_mode: text|html|marc
    :param output_limit: int, number of maximum keywords printed (it applies
            to single and composite keywords separately)
    :param spires: boolen meaning spires output style
    :param only_core_tags: boolean
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
    functions = {
        "text": _output_text,
        "marcxml": _output_marc,
        "html": _output_html,
        "dict": _output_dict
    }

    if output_mode != "raw":
        return functions[output_mode](complete_output, categories)
    else:
        if output_limit > 0:
            return (
                _kw(_sort_kw_matches(single_keywords, output_limit)),
                _kw(_sort_kw_matches(composite_keywords, output_limit)),
                author_keywords,  # this we don't limit (?)
                _kw(_sort_kw_matches(acronyms, output_limit))
            )
        else:
            return (single_keywords_p, composite_keywords_p,
                    author_keywords, acronyms)


def build_marc(recid, single_keywords, composite_keywords,
               spires=False, author_keywords=None, acronyms=None):
    """Create xml record.

    :var recid: integer
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

    output.append(_output_marc(
        single_keywords,
        composite_keywords,
        author_keywords,
        acronyms
    ))

    output.append('</record></collection>')

    return '\n'.join(output)


def _output_marc(output_complete, categories,
                 kw_field=cfg["CLASSIFIER_RECORD_KEYWORD_FIELD"],
                 auth_field=cfg["CLASSIFIER_RECORD_KEYWORD_AUTHOR_FIELD"],
                 acro_field=cfg["CLASSIFIER_RECORD_KEYWORD_ACRONYM_FIELD"],
                 provenience='Classifier'):
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
    :return: string, formatted MARC
    """
    kw_template = ('<datafield tag="%s" ind1="%s" ind2="%s">\n'
                   '    <subfield code="2">%s</subfield>\n'
                   '    <subfield code="a">%s</subfield>\n'
                   '    <subfield code="n">%s</subfield>\n'
                   '    <subfield code="9">%s</subfield>\n'
                   '</datafield>\n')

    output = []

    tag, ind1, ind2 = _parse_marc_code(kw_field)
    for keywords in (output_complete["Single keywords"],
                     output_complete["Core keywords"]):
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
                     limit=cfg["CLASSIFIER_DEFAULT_OUTPUT_NUMBER"]):

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

    output += "\n--"

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
      <title>Automatically generated keywords by Classifier</title>
    </head>
    <body>
    {0}
    </body>
    </html>""".format(
        _output_text(complete_output).replace('\n', '<br>')
    ).replace('\n', '')


def _get_singlekws(skw_matches, spires=False):
    """Get single keywords.

    :var skw_matches: dict of {keyword: [info,...]}
    :keyword spires: bool, to get the spires output
    :return: list of formatted keywords
    """
    output = {}
    for single_keyword, info in skw_matches:
        output[single_keyword.output(spires)] = len(info[0])
    return output


def _get_compositekws(ckw_matches, spires=False):
    """Get composite keywords.

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
    :return: string
    """
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
            # test if one of the components is  not core
            i = 0
            for c in ckw.getComponents():
                if c.core:
                    output[c.output(spires)] = info[1][i]
                i += 1
    return output


def filter_core_keywords(keywords):
    """Only return keywords that are CORE."""
    matches = {}
    for kw, info in keywords.items():
        if kw.core:
            matches[kw] = info
    return matches


def clean_before_output(kw_matches):
    """Return a clean copy of the keywords data structure.

    Stripped off the standalone and other unwanted elements.
    """
    filtered_kw_matches = {}

    for kw_match, info in iteritems(kw_matches):
        if not kw_match.nostandalone:
            filtered_kw_matches[kw_match] = info

    return filtered_kw_matches

# ---------------------------------------------------------------------
#                          helper functions
# ---------------------------------------------------------------------


def _skw_matches_comparator(kw0, kw1):
    """Compare 2 single keywords objects.

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


def get_partial_text(fulltext):
    """Return a short version of the fulltext used with the partial matching mode.

    The version is composed of 20% in the beginning and 20% in the middle of the
    text.
    """
    def _get_index(x):
        return int(float(x) / 100 * len(fulltext))

    partial_text = [fulltext[_get_index(start):_get_index(end)]
                    for start, end in cfg["CLASSIFIER_PARTIAL_TEXT_PERCENTAGES"]]

    return "\n".join(partial_text)


def save_keywords(filename, xml):
    """Save keyword XML to filename."""
    tmp_dir = os.path.dirname(filename)
    if not os.path.isdir(tmp_dir):
        os.mkdir(tmp_dir)

    file_desc = open(filename, "w")
    file_desc.write(xml)
    file_desc.close()


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
