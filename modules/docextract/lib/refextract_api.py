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

"""This is where all the public API calls are accessible

This is the only file containing public calls and everything that is
present here can be considered private by the invenio modules.
"""


import os

from urllib import urlretrieve
from tempfile import mkstemp

from invenio.refextract_engine import parse_references, \
                                      get_plaintext_document_body, \
                                      parse_reference_line, \
                                      extract_references_from_fulltext, \
                                      get_kbs
from invenio.config import CFG_INSPIRE_SITE
from invenio.bibindex_engine import CFG_JOURNAL_PUBINFO_STANDARD_FORM
from invenio.bibdocfile import BibRecDocs, InvenioWebSubmitFileError
from invenio.search_engine import get_record
from invenio.bibtask import task_low_level_submission
from invenio.bibrecord import record_delete_fields, record_xml_output, \
    create_record, record_get_field_instances, record_add_fields, \
    record_has_field
from invenio.refextract_find import get_reference_section_beginning
from invenio.refextract_text import rebuild_reference_lines
from invenio.refextract_config import CFG_REFEXTRACT_FILENAME
from invenio.config import CFG_TMPSHAREDDIR


class FullTextNotAvailable(Exception):
    """Raised when we cannot access the document text"""


class RecordHasReferences(Exception):
    """Raised when
    * we asked to updated references for a record
    * we explicitely asked for not overwriting references for this record
    (via the appropriate function argument)
    * the record has references thus we cannot update them
   """


def extract_references_from_url_xml(url, inspire=CFG_INSPIRE_SITE):
    """Extract references from the pdf specified in the url

    The single parameter is the path to the pdf.
    It raises FullTextNotAvailable if the url gives a 404
    The result is given in marcxml.
    """
    filename, dummy = urlretrieve(url)
    try:
        try:
            marcxml = extract_references_from_file_xml(filename,
                                                       inspire=inspire)
        except IOError, err:
            if err.code == 404:
                raise FullTextNotAvailable()
            else:
                raise
    finally:
        os.remove(filename)
    return marcxml


def extract_references_from_file_xml(path, recid=1, inspire=CFG_INSPIRE_SITE):
    """Extract references from a local pdf file

    The single parameter is the path to the file
    It raises FullTextNotAvailable if the file does not exist
    The result is given in marcxml.
    """
    if not os.path.isfile(path):
        raise FullTextNotAvailable()

    docbody, dummy = get_plaintext_document_body(path)
    reflines, dummy, dummy = extract_references_from_fulltext(docbody)
    if not len(reflines):
        docbody, dummy = get_plaintext_document_body(path, keep_layout=True)
        reflines, dummy, dummy = extract_references_from_fulltext(docbody)

    return parse_references(reflines, recid=recid, inspire=inspire)


def extract_references_from_string_xml(source, inspire=CFG_INSPIRE_SITE):
    """Extract references from a string

    The single parameter is the document
    The result is given in marcxml.
    """
    docbody = source.split('\n')
    refs_info = get_reference_section_beginning(docbody)
    docbody = rebuild_reference_lines(docbody, refs_info['marker_pattern'])
    reflines, dummy, dummy = extract_references_from_fulltext(docbody)
    return parse_references(reflines, inspire=inspire)


def extract_references_from_record_xml(recid, inspire=CFG_INSPIRE_SITE):
    """Extract references from a record id

    The single parameter is the document
    The result is given in marcxml.
    """
    path = look_for_fulltext(recid)
    if not path:
        raise FullTextNotAvailable()

    return extract_references_from_file_xml(path, recid=recid, inspire=inspire)


def replace_references(recid, inspire=CFG_INSPIRE_SITE):
    """Replace references for a record

    The record itself is not updated, the marc xml of the document with updated
    references is returned

    Parameters:
    * recid: the id of the record
    * inspire: format of ther references
    """
    # Parse references
    references_xml = extract_references_from_record_xml(recid, inspire=inspire)
    references = create_record(references_xml.encode('utf-8'))
    # Record marc xml
    record = get_record(recid)

    if references[0]:
        fields_to_add = record_get_field_instances(references[0],
                                                   tag='999',
                                                   ind1='%',
                                                   ind2='%')
        # Replace 999 fields
        record_delete_fields(record, '999')
        record_add_fields(record, '999', fields_to_add)
        # Update record references
        out_xml = record_xml_output(record)
    else:
        out_xml = None

    return out_xml


def update_references(recid, inspire=CFG_INSPIRE_SITE, overwrite=True):
    """Update references for a record

    First, we extract references from a record.
    Then, we are not updating the record directly but adding a bibupload
    task in -c mode which takes care of updating the record.

    Parameters:
    * recid: the id of the record
    * inspire: format of ther references
    """

    if not overwrite:
        # Check for references in record
        record = get_record(recid)
        if record and record_has_field(record, '999'):
            raise RecordHasReferences(recid)

    # Parse references
    references_xml = extract_references_from_record_xml(recid, inspire=inspire)

    # Save new record to file
    (temp_fd, temp_path) = mkstemp(prefix=CFG_REFEXTRACT_FILENAME,
                                   dir=CFG_TMPSHAREDDIR)
    temp_file = os.fdopen(temp_fd, 'w')
    temp_file.write(references_xml.encode('utf-8'))
    temp_file.close()

    # Update record
    task_low_level_submission('bibupload', 'refextract', '-P', '5',
                              '-c', temp_path)


def look_for_fulltext(recid):
    rec_info = BibRecDocs(recid)
    docs = rec_info.list_bibdocs()

    path = None
    for doc in docs:
        try:
            path = doc.get_file('pdf').get_full_path()
        except InvenioWebSubmitFileError:
            try:
                path = doc.get_file('pdfa').get_full_path()
            except InvenioWebSubmitFileError:
                try:
                    path = doc.get_file('PDF').get_full_path()
                except InvenioWebSubmitFileError:
                    pass

    return path


def record_has_fulltext(recid):
    """Checks if we can access the fulltext for the given recid"""
    path = look_for_fulltext(recid)
    return path is not None


def search_from_reference(text):
    """Convert a raw reference to a search query

    Called by the search engine to convert a raw reference:
    find rawref John, JINST 4 (1994) 45
    is converted to
    journal:"JINST,4,45"
    """
    field = ''
    pattern = ''

    kbs = get_kbs()
    elements, dummy_m, dummy_c, dummy_co = parse_reference_line(text, kbs)

    for el in elements:
        if el['type'] == 'JOURNAL':
            field = 'journal'
            pattern = CFG_JOURNAL_PUBINFO_STANDARD_FORM \
                .replace('773__p', el['title']) \
                .replace('773__v', el['volume']) \
                .replace('773__c', el['page']) \
                .replace('773__y', el['year'])
            break
        elif el['type'] == 'REPORTNUMBER':
            field = 'report'
            pattern = el['report_num']
            break

    return field, pattern.encode('utf-8')
