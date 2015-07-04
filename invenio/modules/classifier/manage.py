# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Perform classifier operations."""

import os
import sys

from flask import current_app

from invenio.ext.script import Manager

from .api import get_keywords_from_local_file

manager = Manager(usage=__doc__)


@manager.option('-f', '--file', dest='filepath',
                help='load knowledge base from this file.')
@manager.option('-k', '--taxonomy', dest='taxonomy',
                help='the taxonomy file to use.')
@manager.option('-o', '--output-mode', dest='output', default="text",
                help='choose output format (text, dict, raw, html, marcxml).')
@manager.option('-n', '--keywords-number', dest='limit', default=20,
                help='the taxonomy file to use.')
@manager.option('-s', '--spires', dest='spires', default=False, action="store_true",
                help='outputs keywords in the SPIRES format.')
@manager.option('-m', '--matching-mode', dest='match_mode', default="full",
                help='choose full or partial searching mode.')
@manager.option('-d', '--detect-author-keywords', dest='with_author_keywords',
                default=False, action="store_true",
                help='detect keywords that are from the authors.')
@manager.option('-e', '--extract-acronyms', dest='extract_acronyms',
                default=False, action="store_true",
                help='outputs a list of acronyms and expansions found.')
@manager.option('--rebuild-cache', dest='rebuild_cache', default=False,
                action="store_true", help='ignores the existing cache and regenerates it')
@manager.option('-r', '--only-core-tags', dest='only_core_tags', default=False,
                action="store_true", help='keep only CORE single and composite keywords.')
@manager.option('--no-cache', dest='no_cache', default=False,
                action="store_true", help='do not cache the taxonomy')
def extract(filepath, taxonomy, output, limit,
            spires, match_mode, with_author_keywords, extract_acronyms,
            rebuild_cache, only_core_tags, no_cache):
    """Run keyword extraction on file.

    .. code-block:: console

        $ inveniomanage classifier extract /path/to/fulltext.pdf /path/to/ontology.rdf

    """
    current_app.logger.info(">>> Going extract keywords from {0} as '{1}'...".format(
        filepath, output
    ))
    if not os.path.isfile(filepath):
        current_app.logger.error(
            "Path to non-existing file\n",
            file=sys.stderr
        )
        sys.exit(1)

    result = get_keywords_from_local_file(
        local_file=filepath,
        taxonomy_name=taxonomy,
        output_mode=output,
        output_limit=limit,
        spires=spires,
        match_mode=match_mode,
        no_cache=no_cache,
        with_author_keywords=with_author_keywords,
        rebuild_cache=rebuild_cache,
        only_core_tags=only_core_tags,
        extract_acronyms=extract_acronyms
    )
    print(result)


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()
