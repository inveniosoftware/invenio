# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

from invenio.legacy.bibrank.citation_indexer import \
    get_recids_matching_query as bibrank_search, \
    standardize_report_number
from invenio.modules.indexer.tokenizers.BibIndexJournalTokenizer import \
    CFG_JOURNAL_PUBINFO_STANDARD_FORM
from invenio.legacy.bibrank.tag_based_indexer import load_config
from invenio.legacy.search_engine import get_collection_reclist, get_fieldvalues
from intbitset import intbitset


def config_cache(cache={}):
    if 'config' not in cache:
        cache['config'] = load_config('citation')
    return cache['config']


def get_recids_matching_query(p, f, m='e'):
    """Return list of recIDs matching query for pattern and field."""
    config = config_cache()
    recids = bibrank_search(p=p, f=f, config=config, m=m)
    return list(recids)


def format_journal(format_string, mappings):
    """format the publ infostring according to the format"""

    def replace(char, data):
        return data.get(char, char)

    for c in mappings.keys():
        format_string = format_string.replace(c, replace(c, mappings))

    return format_string


def find_journal(citation_element):
    tags_values = {
        '773__p': citation_element['title'],
        '773__v': citation_element['volume'],
        '773__c': citation_element['page'],
        '773__y': citation_element['year'],
    }
    journal_string = format_journal(
        CFG_JOURNAL_PUBINFO_STANDARD_FORM, tags_values)
    return get_recids_matching_query(journal_string, 'journal')


def find_reportnumber(citation_element):
    reportnumber = standardize_report_number(citation_element['report_num'])
    return get_recids_matching_query(reportnumber, 'reportnumber')


def find_doi(citation_element):
    doi_string = citation_element['doi_string']
    return get_recids_matching_query(doi_string, 'doi')


def find_referenced_recid(citation_element):
    el_type = citation_element['type']
    if el_type in FINDERS:
        return FINDERS[el_type](citation_element)
    return []

def find_book(citation_element):
    books_recids = get_collection_reclist('Books')
    search_string = citation_element['title']
    recids = intbitset(get_recids_matching_query(search_string, 'title'))
    recids &= books_recids
    if len(recids) == 1:
        return recids

    if 'year' in citation_element:
        for recid in recids:
            year_tags = get_fieldvalues(recid, '269__c')
            for tag in year_tags:
                if tag == citation_element['year']:
                    return [recid]

    return []


def find_isbn(citation_element):
    books_recids = get_collection_reclist('Books')
    recids = intbitset(get_recids_matching_query(citation_element['ISBN'], 'isbn'))
    return list(recids & books_recids)


FINDERS = {
    'JOURNAL': find_journal,
    'REPORTNUMBER': find_reportnumber,
    'DOI': find_doi,
    'BOOK': find_book,
    'ISBN': find_isbn,
}
