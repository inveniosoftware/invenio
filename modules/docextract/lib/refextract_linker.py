# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.bibrank_citation_indexer import INTBITSET_OF_DELETED_RECORDS
from invenio.bibindex_engine import CFG_JOURNAL_PUBINFO_STANDARD_FORM
from invenio.search_engine import search_pattern


def get_recids_matching_query(pvalue, fvalue):
    """Return list of recIDs matching query for PVALUE and FVALUE."""
    recids = search_pattern(p=pvalue, f=fvalue, m='e')
    recids -= INTBITSET_OF_DELETED_RECORDS
    return list(recids)


def format_journal(format_string, mappings):
    """format the publ infostring according to the format"""

    def replace(char, data):
        return data.get(char, char)

    return ''.join(replace(c, mappings) for c in format_string)


def find_journal(citation_element):
    tags_values = {
        '773__p': citation_element['title'],
        '773__v': citation_element['volume'],
        '773__c': citation_element['page'],
        '773__y': citation_element['year'],
    }
    journal_string \
               = format_journal(CFG_JOURNAL_PUBINFO_STANDARD_FORM, tags_values)
    return get_recids_matching_query(journal_string, 'journal')


def find_reportnumber(citation_element):
    reportnumber_string = citation_element['report_num']
    return get_recids_matching_query(reportnumber_string, 'reportnumber')


def find_doi(citation_element):
    doi_string = citation_element['doi_string']
    return get_recids_matching_query(doi_string, 'doi')


def find_referenced_recid(citation_element):
    el_type = citation_element['type']
    if el_type in FINDERS:
        return FINDERS[el_type](citation_element)
    return []


FINDERS = {
    'JOURNAL': find_journal,
    'REPORTNUMBER': find_reportnumber,
    'DOI': find_doi,
}
