# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Classifier API - fulltext keyword extractor."""

from __future__ import print_function

import os
import re

from flask import current_app

from invenio.base.globals import cfg
from invenio.utils.filedownload import download_url

from .engine import (
    clean_before_output,
    extract_abbreviations,
    extract_author_keywords,
    extract_composite_keywords,
    extract_single_keywords,
    filter_core_keywords,
    get_keywords_output,
    get_partial_text,
)
from .extractor import text_lines_from_local_file
from .normalizer import cut_references, normalize_fulltext
from .reader import (
    get_cache,
    get_regular_expressions,
    set_cache,
)


def output_keywords_for_sources(input_sources, taxonomy_name, output_mode="text",
                                output_limit=cfg['CLASSIFIER_DEFAULT_OUTPUT_NUMBER'], spires=False,
                                match_mode="full", no_cache=False, with_author_keywords=False,
                                rebuild_cache=False, only_core_tags=False, extract_acronyms=False,
                                **kwargs):
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

        current_app.logger.info("Remote file has %d lines and %d words.".format(
            line_nb, word_nb
        ))
        return get_keywords_from_text(
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

    # Get the fulltext for each source.
    for entry in input_sources:
        current_app.logger.info("Trying to read input file %s." % entry)
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
                                 output_limit=cfg["CLASSIFIER_DEFAULT_OUTPUT_NUMBER"], spires=False,
                                 match_mode="full", no_cache=False, with_author_keywords=False,
                                 rebuild_cache=False, only_core_tags=False, extract_acronyms=False):
    """Output keywords reading a local file.

    Arguments and output are the same as for :see: get_keywords_from_text().
    """
    current_app.logger.info("Analyzing keywords for local file %s." % local_file)
    text_lines = text_lines_from_local_file(local_file)

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
                           output_limit=cfg["CLASSIFIER_DEFAULT_OUTPUT_NUMBER"],
                           spires=False, match_mode="full", no_cache=False,
                           with_author_keywords=False, rebuild_cache=False,
                           only_core_tags=False, extract_acronyms=False):
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
    cache = get_cache(taxonomy_name)
    if not cache:
        set_cache(taxonomy_name,
                  get_regular_expressions(taxonomy_name,
                                          rebuild=rebuild_cache,
                                          no_cache=no_cache))
        cache = get_cache(taxonomy_name)
    _skw = cache[0]
    _ckw = cache[1]
    text_lines = cut_references(text_lines)
    fulltext = normalize_fulltext("\n".join(text_lines))

    if match_mode == "partial":
        fulltext = get_partial_text(fulltext)
    author_keywords = None
    if with_author_keywords:
        author_keywords = extract_author_keywords(_skw, _ckw, fulltext)
    acronyms = {}
    if extract_acronyms:
        acronyms = extract_abbreviations(fulltext)

    single_keywords = extract_single_keywords(_skw, fulltext)
    composite_keywords = extract_composite_keywords(_ckw, fulltext, single_keywords)

    if only_core_tags:
        single_keywords = clean_before_output(filter_core_keywords(single_keywords))
        composite_keywords = filter_core_keywords(composite_keywords)
    else:
        # Filter out the "nonstandalone" keywords
        single_keywords = clean_before_output(single_keywords)

    return get_keywords_output(
        single_keywords=single_keywords,
        composite_keywords=composite_keywords,
        taxonomy_name=taxonomy_name,
        author_keywords=author_keywords,
        acronyms=acronyms,
        output_mode=output_mode,
        output_limit=output_limit,
        spires=spires,
        only_core_tags=only_core_tags
    )
