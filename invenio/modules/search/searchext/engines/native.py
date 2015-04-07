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

"""Search engine implementation."""

import re
import zlib

from flask import current_app

from intbitset import intbitset

from invenio.base.globals import cfg
from invenio.modules.indexer.models import IdxINDEX
from invenio.modules.indexer.utils import field_tokenizer_cache
from invenio.modules.records import models
from invenio.modules.records.models import Record
from invenio.modules.search.errors import InvenioWebSearchWildcardLimitError
from invenio.modules.search.models import Field
from invenio.modules.search.registry import units
from invenio.utils.serializers import deserialize_via_marshal

re_word = re.compile(r'[\s]')


def search_unit(p, f=None, m=None, wl=0, ignore_synonyms=None):
    """Search for basic search unit.

    The search unit is defined by pattern 'p' and field 'f' and matching type
    'm'.  Return hitset of recIDs.

    All the parameters are assumed to have been previously washed.  'p' is
    assumed to be already a ``basic search unit'' so that it is searched as
    such and is not broken up in any way.  Only wildcard and span queries are
    being detected inside 'p'.

    If CFG_WEBSEARCH_SYNONYM_KBRS is set and we are searching in one of the
    indexes that has defined runtime synonym knowledge base, then look up there
    and automatically enrich search results with results for synonyms.

    In case the wildcard limit (wl) is greater than 0 and this limit is reached
    an InvenioWebSearchWildcardLimitError will be raised.  In case you want to
    call this function with no limit for the wildcard queries, wl should be 0.

    Parameter 'ignore_synonyms' is a list of terms for which we should not try
    to further find a synonym.

    This function is suitable as a low-level API.
    """
    from invenio.modules.indexer.tokenizers.BibIndexCJKTokenizer import (
        BibIndexCJKTokenizer, is_there_any_CJK_character_in_text
    )

    from invenio.legacy.search_engine import (
        get_synonym_terms,
    )

    CFG_WEBSEARCH_SYNONYM_KBRS = current_app.config.get(
        'CFG_WEBSEARCH_SYNONYM_KBRS', {})

    # create empty output results set:
    hitset = intbitset()
    if not p:  # sanity checking
        return hitset

    tokenizer = field_tokenizer_cache.get(f, '')
    hitset_cjk = intbitset()
    if tokenizer == 'BibIndexCJKTokenizer':
        if is_there_any_CJK_character_in_text(p):
            cjk_tok = BibIndexCJKTokenizer()
            chars = cjk_tok.tokenize_for_words(p)
            for char in chars:
                hitset_cjk |= search_unit_in_bibwords(char, f, wl)

    # eventually look up runtime synonyms:
    hitset_synonyms = intbitset()
    if (f or 'anyfield') in CFG_WEBSEARCH_SYNONYM_KBRS:
        if ignore_synonyms is None:
            ignore_synonyms = []
        ignore_synonyms.append(p)
        for p_synonym in get_synonym_terms(
                p,
                CFG_WEBSEARCH_SYNONYM_KBRS[f or 'anyfield'][0],
                CFG_WEBSEARCH_SYNONYM_KBRS[f or 'anyfield'][1]):
            if p_synonym != p and p_synonym not in ignore_synonyms:
                hitset_synonyms |= search_unit(p_synonym, f, m, wl,
                                               ignore_synonyms)

    current_app.logger.debug("search_unit: f={f}, p={p}, m={m}".format(
        f=f, p=p, m=m))
    # look up hits:
    callback = units.get(f, default_search_unit)
    hitset = callback(p, f, m, wl)

    # merge synonym results and return total:
    hitset |= hitset_synonyms
    hitset |= hitset_cjk
    return hitset


def is_marc_tag(f):
    """Return True if the field a MARC tag, e.g. ``980__a``."""
    return f and len(f) >= 2 and str(f[0]).isdigit() and str(f[1]).isdigit()


def default_search_unit(p, f, m, wl):
    """Query correct index type and return hitset."""
    if m == 'a' or m == 'r' or is_marc_tag(f):
        # we are doing either phrase search or regexp search
        index_id = IdxINDEX.get_index_id_from_field(f)
        if index_id != 0:
            if m == 'a' and index_id in IdxINDEX.get_idxpair_field_ids():
                # for exact match on the admin configured fields
                # we are searching in the pair tables
                hitset = search_unit_in_idxpairs(p, f, m or 'a', wl)
            else:
                hitset = search_unit_in_idxphrases(p, f, m or 'a', wl)
        else:
            hitset = search_unit_in_bibxxx(p, f, m or 'a', wl)
    else:
        # we are doing bibwords search by default
        hitset = search_unit_in_bibwords(p, f, wl=wl)
    return hitset


def search_unit_in_bibwords(word, f, decompress=zlib.decompress, wl=0):
    """Search for 'word' inside bibwordsX table for field 'f'.

    :return: hitset of recIDs.
    """
    from invenio.legacy.bibindex.engine_stemmer import stem
    from invenio.legacy.bibindex.engine_washer import (
        lower_index_term,
        wash_index_term,
    )
    # FIXME: Should not be used for journal field.
    hitset = intbitset()  # will hold output result set
    limit_reached = 0  # flag for knowing if the query limit has been reached

    # if no field is specified, search in the global index.
    f = f or 'anyfield'
    index = IdxINDEX.get_from_field(f)
    if index is None:
        return hitset
    model = index.wordf
    stemming_language = index.stemming_language

    # wash 'word' argument and run query:
    if f.endswith('count') and word.endswith('+'):
        # field count query of the form N+ so transform N+ to N->99999:
        word = word[:-1] + '->99999'
    word = word.replace('*', '%')  # we now use '*' as the truncation character
    words = word.split("->", 1)  # check for span query
    if len(words) == 2:
        word0 = re_word.sub('', words[0])
        word1 = re_word.sub('', words[1])
        if stemming_language:
            word0 = lower_index_term(word0)
            word1 = lower_index_term(word1)
            # We remove trailing truncation character before stemming
            if word0.endswith('%'):
                word0 = stem(word0[:-1], stemming_language) + '%'
            else:
                word0 = stem(word0, stemming_language)
            if word1.endswith('%'):
                word1 = stem(word1[:-1], stemming_language) + '%'
            else:
                word1 = stem(word1, stemming_language)

        word0_washed = wash_index_term(word0)
        word1_washed = wash_index_term(word1)
        if f.endswith('count'):
            # field count query; convert to integers in order
            # to have numerical behaviour for 'BETWEEN n1 AND n2' query
            try:
                word0_washed = int(word0_washed)
                word1_washed = int(word1_washed)
            except ValueError:
                pass
        query = model.query.filter(
            model.term.between(word0_washed, word1_washed)
        )
        if wl > 0:
            query = query.limit(wl)
        res = query.values('term', 'hitlist')
        if wl > 0 and len(res) == wl:
            limit_reached = 1  # set the limit reached flag to true
    else:
        word = re_word.sub('', word)
        if stemming_language:
            word = lower_index_term(word)
            # We remove trailing truncation character before stemming
            if word.endswith('%'):
                word = stem(word[:-1], stemming_language) + '%'
            else:
                word = stem(word, stemming_language)
        if word.find('%') >= 0:  # do we have wildcard in the word?
            query = model.query.filter(model.term.like(wash_index_term(word)))
            if wl > 0:
                query.limit(wl)
            res = query.values('term', 'hitlist')
            # set the limit reached flag to true
            limit_reached = wl > 0 and len(res) == wl
        else:
            res = model.query.filter(
                model.term.like(wash_index_term(word))
            ).values('term', 'hitlist')
    # fill the result set:
    for word, hitlist in res:
        # add the results:
        hitset |= intbitset(hitlist)
    # check to see if the query limit was reached
    if limit_reached:
        # raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(hitset)
    # okay, return result set:
    return hitset


def search_unit_in_idxpairs(p, f, m, wl=0):
    """Search for pair 'p' in idxPAIR table for field 'f' and return hitset."""
    from invenio.modules.indexer.tokenizers.BibIndexDefaultTokenizer import (
        BibIndexDefaultTokenizer
    )
    # flag for knowing if the query limit has been reached
    limit_reached = False
    # flag to know when it makes sense to try to do exact matching
    do_exact_search = True
    result_set = intbitset()
    # determine the idxPAIR table to read from
    index = IdxINDEX.get_from_field(f)
    if index is None:
        return intbitset()
    model = index.pairf
    column = model.term
    stemming_language = index.stemming_language
    pairs_tokenizer = BibIndexDefaultTokenizer(stemming_language)

    conditions = []

    if p.startswith("%") and p.endswith("%"):
        p = p[1:-1]
    original_pattern = p
    # we now use '*' as the truncation character
    p = p.replace('*', '%')
    # is it a span query?
    ps = p.split("->", 1)
    if len(ps) == 2 and not (ps[0].endswith(' ') or ps[1].startswith(' ')):
        # so we are dealing with a span query
        pairs_left = pairs_tokenizer.tokenize_for_pairs(ps[0])
        pairs_right = pairs_tokenizer.tokenize_for_pairs(ps[1])
        if not pairs_left or not pairs_right:
            # we are not actually dealing with pairs but with words
            return search_unit_in_bibwords(original_pattern, f, wl=wl)
        elif len(pairs_left) != len(pairs_right):
            # it is kind of hard to know what the user actually wanted
            # we have to do: foo bar baz -> qux xyz, so let's swith to phrase
            return search_unit_in_idxphrases(original_pattern, f, m, wl)
        elif len(pairs_left) > 1 and \
                len(pairs_right) > 1 and \
                pairs_left[:-1] != pairs_right[:-1]:
            # again we have something like: foo bar baz -> abc xyz qux
            # so we'd better switch to phrase
            return search_unit_in_idxphrases(original_pattern, f, m, wl)
        else:
            # finally, we can treat the search using idxPairs
            # at this step we have either: foo bar -> abc xyz
            # or foo bar abc -> foo bar xyz
            conditions.append(
                (column.between(pairs_left[-1], pairs_right[-1]), True)
            )
            # which should be equal with pairs_right[:-1]
            for pair in pairs_left[:-1]:
                conditions.append((column == pair, False))
        do_exact_search = False  # no exact search for span queries
    elif p.find('%') > -1:
        # tokenizing p will remove the '%', so we have to make sure it stays
        replacement = 'xxxxxxxxxx'
        # hopefuly this will not clash with anything in the future
        p = p.replace('%', replacement)
        pairs = pairs_tokenizer.tokenize_for_pairs(p)
        if not pairs:
            # we are not actually dealing with pairs but with words
            return search_unit_in_bibwords(original_pattern, f, wl=wl)
        for pair in pairs:
            if pair.find(replacement) > -1:
                # we replace back the % sign
                pair = pair.replace(replacement, '%')
                conditions.append((column.like(pair), True))
            else:
                conditions.append((column == pair, False))
        do_exact_search = False
    else:
        # normal query
        pairs = pairs_tokenizer.tokenize_for_pairs(p)
        if not pairs:
            # we are not actually dealing with pairs but with words
            return search_unit_in_bibwords(original_pattern, f, wl=wl)
        for pair in pairs:
            conditions.append((column == pair, False))

    for condition, use_query_limit in conditions:
        query = model.query.filter(condition)
        if use_query_limit and wl > 0:
            query = query.limit(wl)
        res = query.values(model.term, model.hitlist)
        limit_reached |= use_query_limit and wl > 0 and len(res) == wl
        if not res:
            return intbitset()
        for pair, hitlist in res:
            hitset_idxpairs = intbitset(hitlist)
            if result_set is None:
                result_set = hitset_idxpairs
            else:
                result_set.intersection_update(hitset_idxpairs)
    # check to see if the query limit was reached
    if limit_reached:
        # raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(result_set)

    # check if we need to eliminate the false positives
    if cfg['CFG_WEBSEARCH_IDXPAIRS_EXACT_SEARCH'] and do_exact_search:
        # we need to eliminate the false positives
        model = IdxINDEX.idxPHRASER(f)
        not_exact_search = intbitset()
        for recid in result_set:
            res = model.query.filter(model.id_bibrec == recid).value(
                model.termlist)
            if res:
                termlist = deserialize_via_marshal(res)
                if not [term for term in termlist
                        if term.lower().find(p.lower()) > -1]:
                    not_exact_search.add(recid)
            else:
                not_exact_search.add(recid)
        # remove the recs that are false positives from the final result
        result_set.difference_update(not_exact_search)
    return result_set or intbitset()


def search_unit_in_idxphrases(p, f, m, wl=0):
    """Searche for phrase 'p' inside idxPHRASE*F table for field 'f'.

    Return hitset of recIDs found. The search type is defined by 'type'
    (e.g. equals to 'r' for a regexp search).
    """
    # call word search method in some cases:
    if f.endswith('count'):
        return search_unit_in_bibwords(p, f, wl=wl)
    # will hold output result set
    hitset = intbitset()
    # flag for knowing if the query limit has been reached
    limit_reached = 0
    # flag for knowing if to limit the query results or not
    use_query_limit = False
    # deduce in which idxPHRASE table we will search:
    model = IdxINDEX.idxPHRASEF(f, fallback=not f)
    if model is None:
        return intbitset()  # phrase index f does not exist

    # detect query type (exact phrase, partial phrase, regexp):
    if m == 'r':
        use_query_limit = True
        column_filter = lambda column: column.op('REGEXP')(p)
    else:
        p = p.replace('*', '%')  # we now use '*' as the truncation character
        ps = p.split("->", 1)  # check for span query:
        if len(ps) == 2 and not (ps[0].endswith(' ') or ps[1].startswith(' ')):
            use_query_limit = True
            column_filter = lambda column: column.between(ps[0], ps[1])
        else:
            if p.find('%') > -1:
                use_query_limit = True
                column_filter = lambda column: column.like(p)
            else:
                column_filter = lambda column: column == p

    # special washing for fuzzy author index:
    # if f in ('author', 'firstauthor', 'exactauthor', 'exactfirstauthor',
    #          'authorityauthor'):
    #    query_params_washed = ()
    #    for query_param in query_params:
    #        query_params_washed += (wash_author_name(query_param),)
    #    query_params = query_params_washed

    query = model.query.filter(column_filter(model.term))
    # perform search:
    if use_query_limit and wl > 0:
        query = query.limit(wl)

    results = query.values('hitlist')
    limit_reached = use_query_limit and wl > 0 and len(results) == wl
    # fill the result set:
    for row in results:
        hitset |= intbitset(row[0])
    # check to see if the query limit was reached
    if limit_reached:
        # raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(hitset)
    # okay, return result set:
    return hitset


def search_unit_in_bibxxx(p, f, m, wl=0):
    """Search for pattern 'p' inside bibxxx tables for field 'f'.

    Returns hitset of recIDs found. The search type is defined by 'type'
    (e.g. equals to 'r' for a regexp search).
    """
    # call word search method in some cases:
    if f and (f == 'journal' or f.endswith('count')):
        return search_unit_in_bibwords(p, f, wl=wl)

    hitset = intbitset()
    # flag for knowing if the query limit has been reached
    limit_reached = False
    # flag for knowing if to limit the query results or not
    use_query_limit = False
    # replace truncation char '*' in field definition
    if f is not None:
        f = f.replace('*', '%')

    if m == 'r':
        use_query_limit = True
        column_filter = lambda column: column.op('REGEXP')(p)
    else:
        p = p.replace('*', '%')  # we now use '*' as the truncation character
        ps = p.split("->", 1)  # check for span query:
        if len(ps) == 2 and not (ps[0].endswith(' ') or ps[1].startswith(' ')):
            use_query_limit = True
            column_filter = lambda column: column.between(ps[0], ps[1])
        else:
            if p.find('%') > -1:
                use_query_limit = True
                column_filter = lambda column: column.like(p)
            else:
                column_filter = lambda column: column == p

    # construct 'tl' which defines the tag list (MARC tags) to search in:
    tl = []
    if len(f) >= 2 and str(f[0]).isdigit() and str(f[1]).isdigit():
        tl.append(f)  # 'f' seems to be okay as it starts by two digits
    else:
        # deduce desired MARC tags on the basis of chosen 'f'
        tl = Field.get_field_tags(f)
        if not tl:
            # f index does not exist, nevermind
            pass
    # okay, start search:
    for t in tl:
        # construct and run query:
        if t == "001":
            column = Record.id
            query = Record.query.filter(column_filter(column))
        else:
            # deduce into which bibxxx table we will search:
            digit1, digit2 = int(t[0]), int(t[1])
            model = getattr(models, 'Bib{0}{1}x'.format(digit1, digit2))
            column_condition = column_filter(model.value)

            if len(t) != 6 or t[-1:] == '%':
                # only the beginning of field 't' is defined, so add wildcard
                # character:
                tag_condition = model.tag.like(t + '%')
            else:
                tag_condition = model.tag == t

            query = model.query.join(model.bibrecs).filter(
                column_condition, tag_condition)
            column = 'id_bibrec'

        if use_query_limit and wl > 0:
            query = query.limit(wl)
        res = query.values(column)
        res = intbitset([row[0] for row in res])
        limit_reached |= use_query_limit and len(res) > 0 and len(res) == wl
        hitset |= res

    # check to see if the query limit was reached
    if limit_reached:
        # raise an exception, so we can print a nice message to the user
        raise InvenioWebSearchWildcardLimitError(hitset)
    return hitset
