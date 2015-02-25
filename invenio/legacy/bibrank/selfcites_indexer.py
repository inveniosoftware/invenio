# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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
"""Self-citations indexer

We store the records and authors in a faster to access way than directly
accessing the bibrecs tables.

We have 3 tables:
 1. rnkAUTHORS to associate records to authors in a speedy way
 2. rnkEXTENDEDAUTHORS to associate co-authors with bibrecs
    for a given bibrec, it provides a fast way to access all the authors of
    the bibrec but also the people they have written papers with
 3. rnkSELFCITES used by search_engine_summarizer for displaying the self-
    citations count.
"""

from itertools import chain
import ConfigParser

from invenio.modules.formatter.utils import parse_tag
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.bibrank.citation_indexer import tagify
from invenio.config import CFG_BIBRANK_SELFCITES_PRECOMPUTE
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibrank.citation_searcher import get_cited_by
from invenio.modules.ranker.registry import configuration


def load_config_file(key):
    """Load config file containing the authors, co-authors tags #"""
    filename = configuration.get(key + '.cfg', '')
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(filename))
    except StandardError:
        raise Exception('Unable to load config file %s' % filename)
    return config


def get_personids_from_record(record):
    """Returns all the personids associated to a record.

    We limit the result length to 20 authors, after which it returns an
    empty set for performance reasons
    """
    ids = get_authors_of_claimed_paper(record)
    if 0 < len(ids) <= 20:
        person_ids = set(ids)
    else:
        person_ids = set()

    return person_ids


def get_authors_tags():
    """
    Get the tags for main author, coauthors, alternative authors from config
    """
    config = load_config_file('citation')
    function = config.get("rank_method", "function")

    tags_names = [
        'first_author',
        'additional_author',
        'alternative_author_name',
        'collaboration_name',
    ]

    tags = {}
    for t in tags_names:
        r_tag = config.get(function, t)
        tags[t] = tagify(parse_tag(r_tag))

    return tags


def get_authors_from_record(recID, tags):
    """Get all authors for a record

    We need this function because there's 3 different types of authors
    and to fetch each one of them we need look through MARC tags
    """
    authors_list = chain(
         get_fieldvalues(recID, tags['first_author']),
         get_fieldvalues(recID, tags['additional_author']),
         get_fieldvalues(recID, tags['alternative_author_name']))
    authors = set(hash(author) for author in list(authors_list)[:21])

    return authors


def get_collaborations_from_record(recID, tags):
    """Get all collaborations for a record"""
    return get_fieldvalues(recID, tags['collaboration_name'])


def compute_self_citations(recid, tags, authors_fun):
    """Compute the self-citations

    We return the total numbers of citations minus the number of self-citations
    Args:
     - recid: record id
     - lciters: list of record ids citing this record
     - authors_cache: the authors cache which will be used to store an author
                      friends (to not compute friends twice)
     - tags: the tag number for author, coauthors, collaborations,
             required since it depends on how the marc was defined
    """
    citers = get_cited_by(recid)
    if not citers:
        return set()

    self_citations = set()

    authors = frozenset(get_authors_from_record(recid, tags))

    collaborations = None
    if not authors or len(authors) > 20:
        collaborations = frozenset(
            get_collaborations_from_record(recid, tags))

    if collaborations:
        # Use collaborations names
        for cit in citers:
            cit_collaborations = frozenset(
                get_collaborations_from_record(cit, tags))
            if collaborations.intersection(cit_collaborations):
                self_citations.add(cit)
    else:
        # Use authors names
        for cit in citers:
            cit_authors = get_authors_from_record(cit, tags)
            if (not authors or len(cit_authors) > 20) and \
                get_collaborations_from_record(cit, tags):
                # Record from a collaboration that cites
                # a record from an author, it's fine
                pass
            else:
                cit_coauthors = frozenset(authors_fun(cit, tags))
                if authors.intersection(cit_coauthors):
                    self_citations.add(cit)

    return self_citations


def fetch_references(recid):
    """Fetch the references stored in the self-citations table for given record

    We need to store the references to make sure that when we do incremental
    updates of the table, we update all the related records properly
    """
    sql = "SELECT `references` FROM rnkSELFCITES WHERE id_bibrec = %s"
    try:
        references = run_sql(sql, (recid, ))[0][0]
    except IndexError:
        references = ''

    if references:
        ids = set(int(ref) for ref in references.split(','))
    else:
        ids = set()

    return ids


def get_precomputed_self_cites_list(recids):
    """Fetch pre-computed self-cites data for given records"""
    in_sql = ','.join('%s' for dummy in recids)
    sql = """SELECT id_bibrec, count
             FROM rnkSELFCITES
             WHERE id_bibrec IN (%s)""" % in_sql
    return run_sql(sql, recids)


def get_precomputed_self_cites(recid):
    """Fetch pre-computed self-cites data for given record"""
    sql = "SELECT count FROM rnkSELFCITES WHERE id_bibrec = %s"
    try:
        r = run_sql(sql, (recid, ))[0][0]
    except IndexError:
        r = None
    return r


def compute_friends_self_citations(recid, tags):
    def coauthors(recid, tags):
        return set(get_record_coauthors(recid)) \
               | set(get_authors_from_record(recid, tags))
    return compute_self_citations(recid, tags, coauthors)


def compute_simple_self_citations(recid, tags):
    """Simple compute self-citations

    The purpose of this algorithm is to provide an alternate way to compute
    self-citations that we can use at runtime.
    Here, we only check for authors citing themselves.
    """
    return compute_self_citations(recid, tags, get_authors_from_record)


def get_self_citations_count(recids, algorithm='simple',
                                  precompute=CFG_BIBRANK_SELFCITES_PRECOMPUTE):
    """Depending on our site we config, we either:
    * compute self-citations (using a simple algorithm)
    * or fetch self-citations from pre-computed table"""
    total_cites = 0

    if not precompute:
        tags = get_authors_tags()
        selfcites_fun = ALL_ALGORITHMS[algorithm]

        for recid in recids:
            citers = get_cited_by(recid)
            self_cites = selfcites_fun(recid, tags)
            total_cites += len(citers) - len(self_cites)
    else:
        results = get_precomputed_self_cites_list(recids)

        results_dict = {}
        for r in results:
            results_dict[r[0]] = r[1]

        for r in recids:
            citers = get_cited_by(r)
            self_cites = results_dict.get(r, 0)
            total_cites += len(citers) - self_cites

    return total_cites


def update_self_cites_tables(recid, config, tags):
    """For a given record update all self-cites table if needed"""
    authors = get_authors_from_record(recid, tags)

    if 0 < len(authors) <= 20:
        # Updated reords cache table
        deleted_authors, added_authors = store_record(recid, authors)
        if deleted_authors or added_authors:
            # Update extended authors table
            store_record_coauthors(recid,
                                   authors,
                                   deleted_authors,
                                   added_authors,
                                   config)


def store_record(recid, authors):
    """
    For a given record, updates if needed the db table (rnkRECORDSCACHE)
    storing the association of recids and authorids

    Returns true if the database has been modified
    """
    sql = 'SELECT authorid FROM rnkRECORDSCACHE WHERE id_bibrec = %s'
    rows = run_sql(sql, (recid, ))
    old_authors = set(r[0] for r in rows)

    if authors != old_authors:
        deleted_authors = old_authors.difference(authors)
        added_authors = authors.difference(old_authors)
        for authorid in deleted_authors:
            run_sql("""DELETE FROM rnkRECORDSCACHE
                       WHERE id_bibrec = %s""", (recid, ))
        for authorid in added_authors:
            run_sql("""INSERT IGNORE INTO rnkRECORDSCACHE (id_bibrec, authorid)
                       VALUES (%s,%s)""", (recid, authorid))
        return deleted_authors, added_authors

    return set(), set()


def get_author_coauthors_list(personids, config):
    """
    Get all the authors that have written a paper with any of the given authors
    """
    personids = list(personids)
    if not personids:
        return ()

    cluster_threshold = config['friends_threshold']
    in_sql = ','.join('%s' for r in personids)
    coauthors = (r[0] for r in run_sql("""
        SELECT a.authorid FROM rnkRECORDSCACHE as a
        JOIN rnkRECORDSCACHE as b ON a.id_bibrec = b.id_bibrec
        WHERE b.authorid IN (%s)
        GROUP BY a.authorid
        HAVING count(a.authorid) >= %s""" % (in_sql, cluster_threshold),
        personids))

    return chain(personids, coauthors)


def store_record_coauthors(recid, authors, deleted_authors,
                                                        added_authors, config):
    """Fill table used by get_record_coauthors()"""
    if deleted_authors:
        to_process = authors
    else:
        to_process = added_authors

    for personid in get_author_coauthors_list(deleted_authors, config):
        run_sql('DELETE FROM rnkEXTENDEDAUTHORS WHERE'
                ' id = %s AND authorid = %s', (recid, personid))

    for personid in get_author_coauthors_list(to_process, config):
        run_sql('INSERT IGNORE INTO rnkEXTENDEDAUTHORS (id, authorid) '
                'VALUES (%s,%s)', (recid, personid))


def get_record_coauthors(recid):
    """
    Get all the authors that have written a paper with any of the authors of
    given bibrec
    """
    sql = 'SELECT authorid FROM rnkEXTENDEDAUTHORS WHERE id = %s'
    return (r[0] for r in run_sql(sql, (recid, )))


SELFCITES_CONFIG = load_config_file('selfcites')

ALL_ALGORITHMS = {
    'friends': compute_friends_self_citations,
    'simple': compute_simple_self_citations,
}
