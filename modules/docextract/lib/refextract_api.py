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
import sys

from urllib import urlretrieve
from tempfile import mkstemp

from invenio.refextract_engine import (parse_references,
                                       get_plaintext_document_body,
                                       parse_reference_line,
                                       get_kbs,
                                       parse_tagged_reference_line)
from invenio.refextract_text import extract_references_from_fulltext
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibindex_tokenizers.BibIndexJournalTokenizer import (
    CFG_JOURNAL_PUBINFO_STANDARD_FORM, CFG_JOURNAL_TAG)
from invenio.bibdocfile import BibRecDocs, InvenioBibDocFileError
from invenio.search_engine import get_record
from invenio.bibtask import task_low_level_submission
from invenio.bibrecord import (record_delete_fields,
                               record_xml_output,
                               create_record,
                               record_get_field_instances,
                               record_add_fields,
                               record_has_field)
from invenio.refextract_find import (get_reference_section_beginning,
                                     find_numeration_in_body)
from invenio.refextract_text import rebuild_reference_lines
from invenio.refextract_config import CFG_REFEXTRACT_FILENAME
from invenio.config import CFG_TMPSHAREDDIR
from invenio.refextract_tag import tag_reference_line



class FullTextNotAvailable(Exception):
    """Raised when we cannot access the document text"""


class RecordHasReferences(Exception):
    """Raised when
    * we asked to updated references for a record
    * we explicitely asked for not overwriting references for this record
    (via the appropriate function argument)
    * the record has references thus we cannot update them
   """


def extract_references_from_url_xml(url):
    """Extract references from the pdf specified in the url

    The single parameter is the path to the pdf.
    It raises FullTextNotAvailable if the url gives a 404
    The result is given in marcxml.
    """
    filename, dummy = urlretrieve(url)
    try:
        try:
            marcxml = extract_references_from_file_xml(filename)
        except IOError, err:
            if err.code == 404:
                raise FullTextNotAvailable()
            else:
                raise
    finally:
        os.remove(filename)
    return marcxml


def extract_references_from_file_xml(path, recid=None):
    """Extract references from a local pdf file

    The single parameter is the path to the file
    It raises FullTextNotAvailable if the file does not exist
    The result is given in marcxml.
    """
    return extract_references_from_file(path=path, recid=recid).to_xml()


def extract_references_from_file(path, recid=None):
    """Extract references from a local pdf file

    The single parameter is the path to the file
    It raises FullTextNotAvailable if the file does not exist
    The result is given as a bibrecord class.
    """
    if not os.path.isfile(path):
        raise FullTextNotAvailable()

    docbody, dummy = get_plaintext_document_body(path)
    reflines, dummy, dummy = extract_references_from_fulltext(docbody)
    if not len(reflines):
        docbody, dummy = get_plaintext_document_body(path, keep_layout=True)
        reflines, dummy, dummy = extract_references_from_fulltext(docbody)

    return parse_references(reflines, recid=recid)


def extract_references_from_string_xml(source,
                                       is_only_references=True,
                                       recid=None):
    """Extract references from a string

    The single parameter is the document
    The result is given as a bibrecord class.
    """
    r = extract_references_from_string(source=source,
                                       is_only_references=is_only_references,
                                       recid=recid)
    return r.to_xml()


def extract_references_from_string(source,
                                   is_only_references=True,
                                   recid=None):
    """Extract references from a string

    The single parameter is the document
    The result is given in marcxml.
    """
    docbody = source.split('\n')
    if not is_only_references:
        reflines, dummy, dummy = extract_references_from_fulltext(docbody)
    else:
        refs_info = get_reference_section_beginning(docbody)
        if not refs_info:
            refs_info, dummy = find_numeration_in_body(docbody)
            refs_info['start_line'] = 0
            refs_info['end_line'] = len(docbody) - 1,

        reflines = rebuild_reference_lines(docbody, refs_info['marker_pattern'])
    return parse_references(reflines, recid=recid)


def extract_references_from_record(recid):
    """Extract references from a record id

    The single parameter is the document
    The result is given in marcxml.
    """
    path = look_for_fulltext(recid)
    if not path:
        raise FullTextNotAvailable()

    return extract_references_from_file(path, recid=recid)


def extract_references_from_record_xml(recid):
    """Extract references from a record id

    The single parameter is the document
    The result is given in marcxml.
    """
    return extract_references_from_record(recid).to_xml()


def extract_journal_reference(line):
    """Extracts the journal reference from
    MARC field 773 and parses for specific
    journal information.

    Parameter: line - field 773__x, the raw journal ref
    Return: list of tuples with data values"""
    tagged_line = tag_reference_line(line, get_kbs(), {})[0]
    if tagged_line is None:
        return None

    elements, dummy_marker, dummy_stats = parse_tagged_reference_line('', tagged_line, [], [])

    for element in elements:
        if element['type'] == 'JOURNAL':
            return element


def replace_references(recid):
    """Replace references for a record

    The record itself is not updated, the marc xml of the document with updated
    references is returned

    Parameters:
    * recid: the id of the record
    """
    # Parse references
    references_xml = extract_references_from_record_xml(recid)
    references = create_record(references_xml)
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


def update_references(recid, overwrite=True):
    """Update references for a record

    First, we extract references from a record.
    Then, we are not updating the record directly but adding a bibupload
    task in -c mode which takes care of updating the record.

    Parameters:
    * recid: the id of the record
    """

    if not overwrite:
        # Check for references in record
        record = get_record(recid)
        if record and record_has_field(record, '999'):
            raise RecordHasReferences('Record has references and overwrite '
                                      'mode is disabled: %s' % recid)

    if get_fieldvalues(recid, '999C59'):
        raise RecordHasReferences('Record has been curated: %s' % recid)

    # Parse references
    references_xml = extract_references_from_record_xml(recid)

    # Save new record to file
    (temp_fd, temp_path) = mkstemp(prefix=CFG_REFEXTRACT_FILENAME,
                                   dir=CFG_TMPSHAREDDIR)
    temp_file = os.fdopen(temp_fd, 'w')
    temp_file.write(references_xml)
    temp_file.close()

    # Update record
    task_low_level_submission('bibupload', 'refextract', '-P', '4',
                              '-c', temp_path)


def list_pdfs(recid):
    rec_info = BibRecDocs(recid)
    docs = rec_info.list_bibdocs()

    for doc in docs:
        for ext in ('pdf', 'pdfa', 'PDF'):
            try:
                yield doc.get_file(ext)
            except InvenioBibDocFileError:
                pass


def get_pdf_doc(recid):
    try:
        doc = list_pdfs(recid).next()
    except StopIteration:
        doc = None

    return doc


def look_for_fulltext(recid):
    doc = get_pdf_doc(recid)

    path = None
    if doc:
        path = doc.get_full_path()

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
    references, dummy_m, dummy_c, dummy_co = parse_reference_line(text, kbs)

    for elements in references:
        for el in elements:
            if el['type'] == 'JOURNAL':
                field = 'journal'
                pattern = CFG_JOURNAL_PUBINFO_STANDARD_FORM \
                    .replace(CFG_JOURNAL_TAG.replace('%', 'p'), el['title']) \
                    .replace(CFG_JOURNAL_TAG.replace('%', 'v'), el['volume']) \
                    .replace(CFG_JOURNAL_TAG.replace('%', 'c'), el['page']) \
                    .replace(CFG_JOURNAL_TAG.replace('%', 'y'), el['year'])
                break
            elif el['type'] == 'REPORTNUMBER':
                field = 'report'
                pattern = el['report_num']
                break

    return field, pattern.encode('utf-8')


def record_can_extract_refs(recid):
    return not bool(get_fieldvalues(recid, '999C5_'))


def record_can_overwrite_refs(recid):
    if get_fieldvalues(recid, '999C6v'):
        # References extracted by refextract
        if get_fieldvalues(recid, '999C59'):
            # They have been curated
            # To put in the HP and create ticket in the future
            needs_submitting = False
        else:
            # They haven't been curated, we safely extract from the new pdf
            needs_submitting = True
    elif not get_fieldvalues(recid, '999C5_'):
        # No references in the record, we can safely extract
        # new references
        needs_submitting = True
    else:
        # Old record, with either no curated references or references
        # curated by SLAC. We cannot distinguish, so we do nothing
        needs_submitting = False

    return needs_submitting
