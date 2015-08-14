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

"""Set of tasks for classification."""


def classify_paper(obj, eng, callback, data,
                   taxonomy, rebuild_cache=False, no_cache=False,
                   output_limit=20, spires=False,
                   match_mode='full', with_author_keywords=False,
                   extract_acronyms=False, only_core_tags=False,
                   fast_mode=False):
    """Extract keywords from data using callback with given taxonomy."""
    from ..errors import TaxonomyError

    output_mode = 'dict'
    if not data:
        obj.log.error("No classification done due to missing data.")
        return

    try:
        result = callback(data, taxonomy,
                          output_mode=output_mode,
                          output_limit=output_limit,
                          spires=spires,
                          match_mode=match_mode,
                          no_cache=no_cache,
                          with_author_keywords=with_author_keywords,
                          rebuild_cache=rebuild_cache,
                          only_core_tags=only_core_tags,
                          extract_acronyms=extract_acronyms)
    except TaxonomyError as e:
        obj.log.exception(e)
        return

    final_result = {"dict": result}
    final_result["fast_mode"] = fast_mode
    # Check if it is not empty output before adding
    output = result.get("complete_output", {}).values()
    if not any(output):
        final_result["dict"] = {}
    name = "classification"
    obj.update_task_results(
        name,
        [{
            "name": name,
            "result": final_result,
            "template": "workflows/results/classifier.html"
        }]
    )


def classify_paper_with_oaiharvester(taxonomy, rebuild_cache=False, no_cache=False,
                                     output_limit=20, spires=False,
                                     match_mode='full', with_author_keywords=False,
                                     extract_acronyms=False, only_core_tags=False,
                                     fast_mode=False):
    """Extract keywords from a pdf file or metadata in a OAI harvest."""
    from ..api import (
        get_keywords_from_text,
        get_keywords_from_local_file,
    )

    def _classify_paper_with_oaiharvester(obj, eng):
        data = None
        is_fast_mode = fast_mode
        if not is_fast_mode:
            if "_result" in obj.extra_data and "pdf" in obj.extra_data["_result"]:
                data = obj.extra_data["_result"]["pdf"]
                callback = get_keywords_from_local_file
            else:
                obj.log.error("No classification done due to missing file.")
        if not data:
            data = [obj.data.get("title", {}).get("title", ""),
                    obj.data.get("abstract", {}).get("summary", "")]
            callback = get_keywords_from_text
            is_fast_mode = True

        classify_paper(obj, eng, callback, data,
                       taxonomy, rebuild_cache,
                       no_cache, output_limit,
                       spires, match_mode, with_author_keywords,
                       extract_acronyms, only_core_tags, is_fast_mode)

    return _classify_paper_with_oaiharvester


def classify_paper_with_deposit(taxonomy, rebuild_cache=False, no_cache=False,
                                output_limit=20, spires=False,
                                match_mode='full', with_author_keywords=False,
                                extract_acronyms=False, only_core_tags=False,
                                fast_mode=False):
    """Extract keywords from a pdf file or metadata in a deposit."""
    from ..api import (
        get_keywords_from_text,
        get_keywords_from_local_file,
    )

    def _classify_paper_with_deposit(obj, eng):
        from invenio_deposit.models import Deposition
        deposition = Deposition(obj)
        data = None
        if not fast_mode:
            for f in deposition.files:
                if f.name and ".pdf" in f.name.lower():
                    data = f.get_syspath()
                    break
            callback = get_keywords_from_local_file
        if not data:
            try:
                metadata = deposition.get_latest_sip().metadata
            except AttributeError as err:
                obj.log.error("Error getting data: {0}".format(err))

            data = [metadata.get("title", {}).get("title", ""),
                    metadata.get("abstract", {}).get("summary", "")]
            callback = get_keywords_from_text

        classify_paper(obj, eng, callback, data,
                       taxonomy, rebuild_cache,
                       no_cache, output_limit,
                       spires, match_mode, with_author_keywords,
                       extract_acronyms, only_core_tags, fast_mode)

    return _classify_paper_with_deposit
