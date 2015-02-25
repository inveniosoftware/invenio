# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
from invenio.legacy.bibclassify import engine


def bibclassify_exhaustive_call(text_files, taxonomy, rebuild_cache=False,
                                no_cache=False, output_mode='text',
                                output_limit=20, spires=False,
                                match_mode='full', with_author_keywords=False,
                                extract_acronyms=False, only_core_tags=False):
    """Call to bibclassify on a file."""
    output_mode = output_mode.split(",")

    return engine.get_keywords_from_local_file(local_file=text_files,
                                               taxonomy_name=taxonomy,
                                               rebuild_cache=rebuild_cache,
                                               no_cache=no_cache,
                                               output_mode=output_mode,
                                               output_limit=output_limit,
                                               spires=spires,
                                               match_mode=match_mode,
                                               with_author_keywords=with_author_keywords,
                                               extract_acronyms=extract_acronyms,
                                               only_core_tags=only_core_tags,
                                               api=True)


def bibclassify_exhaustive_call_text(text, taxonomy, rebuild_cache=False,
                                     no_cache=False, output_mode='text',
                                     output_limit=20, spires=False,
                                     match_mode='full',
                                     with_author_keywords=False,
                                     extract_acronyms=False,
                                     only_core_tags=False):
    """Call to bibclassify on a text."""
    output_mode = output_mode.split(",")
    if not isinstance(text, list):
        text = [text]
    return engine.get_keywords_from_text(text_lines=text,
                                         taxonomy_name=taxonomy,
                                         rebuild_cache=rebuild_cache,
                                         no_cache=no_cache,
                                         output_mode=output_mode,
                                         output_limit=output_limit,
                                         spires=spires,
                                         match_mode=match_mode,
                                         with_author_keywords=with_author_keywords,
                                         extract_acronyms=extract_acronyms,
                                         only_core_tags=only_core_tags,
                                         api=True)

