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

"""Utility functions."""

import re

from invenio.ext.cache import cache
from invenio.ext.sqlalchemy import db
from invenio.modules.knowledge.api import get_kbr_values
from invenio.utils.datastructures import LazyDict

from .models import IdxINDEX, IdxINDEXField
from .registry import tokenizers

field_tokenizer_cache = LazyDict(
    lambda: dict(IdxINDEXField.get_field_tokenizers())
)


@cache.memoize()
def get_idx_indexer(name):
    """Return indexer field value."""
    return db.session.query(IdxINDEX.indexer).filter_by(name=name).scalar()


def load_tokenizers():
    """Load all the bibindex tokenizers and returns it."""
    return dict((module.__name__.split('.')[-1],
                 getattr(module, module.__name__.split('.')[-1], ''))
                for module in tokenizers)


def get_synonym_terms(term, kbr_name, match_type, use_memoise=False):
    """Return list of synonyms for TERM by looking in KBR_NAME.

    :param term: search-time term or index-time term
    :param kbr_name: knowledge base name
    :param match_type: specifies how the term matches against the KBR
        before doing the lookup.  Could be `exact' (default),
        'leading_to_comma', `leading_to_number'.
    :param use_memoise: can we memoise while doing lookups?
    :return: list of term synonyms
    """
    dterms = {}
    # exact match is default:
    term_for_lookup = term
    term_remainder = ''
    from invenio.legacy.bibindex.engine_config import \
        CFG_BIBINDEX_SYNONYM_MATCH_TYPE as MATCH_TYPES
    # but maybe match different term:
    if match_type == MATCH_TYPES['leading_to_comma']:
        mmm = re.match(r'^(.*?)(\s*,.*)$', term)
        if mmm:
            term_for_lookup = mmm.group(1)
            term_remainder = mmm.group(2)
    elif match_type == MATCH_TYPES['leading_to_number']:
        mmm = re.match(r'^(.*?)(\s*\d.*)$', term)
        if mmm:
            term_for_lookup = mmm.group(1)
            term_remainder = mmm.group(2)
    # FIXME: workaround: escaping SQL wild-card signs, since KBR's
    # exact search is doing LIKE query, so would match everything:
    term_for_lookup = term_for_lookup.replace('%', '\\%')
    # OK, now find synonyms:
    for kbr_values in get_kbr_values(kbr_name,
                                     searchkey=term_for_lookup,
                                     searchtype='e',
                                     use_memoise=use_memoise):
        for kbr_value in kbr_values:
            dterms[kbr_value + term_remainder] = 1
    # return list of term synonyms:
    return dterms.keys()
