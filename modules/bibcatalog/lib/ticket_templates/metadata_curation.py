# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

"""
BibCatalog template
"""
from invenio.config import CFG_SITE_URL
from invenio.legacy.bibrecord import \
    record_get_field_values, \
    record_get_field_value
from invenio.legacy.bibcatalog.utils import \
    record_in_collection, \
    record_get_value_with_provenence, \
    record_id_from_record, \
    split_tag_code, \
    load_tag_code_from_name, \
    BibCatalogTagNotFound


def check_record(ticket, record):  # pylint: disable-msg=W0613
    """
    Checks to see if we should create a ticket.

    @param ticket: a ticket object as created by BibCatalogTicket() containing
                   the subject, body and queue to create a ticket in.
    @type ticket: record object of BibCatalogTicket.

    @param record: a recstruct object as created by bibrecord.create_record()
    @type record: record object of BibRecord.

    @return: returns True if record is a 'ARTICLE' record.
    @rtype: bool
    """
    return record_in_collection(record, "ARTICLE")


def generate_ticket(ticket, record):
    """
    Generates a ticket to be created, filling subject, body and queue values
    of the passed BibCatalogTicket object. The enriched object is returned.

    @param ticket: a ticket object as created by BibCatalogTicket() containing
                   the subject, body and queue to create a ticket in.
    @type ticket: record object of BibCatalogTicket.

    @param record: a recstruct object as created by bibrecord.create_record()
    @type record: record object of BibRecord.

    @return: the modified ticket object to create.
    @rtype: BibCatalogTicket
    """
    title_code = load_tag_code_from_name("title")
    abstract_code = load_tag_code_from_name("abstract")

    try:
        date_code = load_tag_code_from_name("date")
    except BibCatalogTagNotFound:
        date_code = load_tag_code_from_name("year")

    category_code = load_tag_code_from_name("subject")

    try:
        notes_code = load_tag_code_from_name("note")
    except BibCatalogTagNotFound:
        notes_code = load_tag_code_from_name("comment")

    first_author_code = load_tag_code_from_name("first author name")
    additional_author_code = load_tag_code_from_name("additional author name")

    try:
        external_id_code = load_tag_code_from_name("ext system ID")
    except BibCatalogTagNotFound:
        external_id_code = load_tag_code_from_name("primary report number")

    # List of extra info to print in the ticket.
    extra_info = []
    recid = record_id_from_record(record)

    arxiv_id = _get_minimal_arxiv_id(record, external_id_code)
    if arxiv_id:
        # We have an arxiv id - we can add special info:
        extra_info.append("ABSTRACT: http://arxiv.org/abs/%s" % (arxiv_id,))
        extra_info.append("PDF: http://arxiv.org/pdf/%s" % (arxiv_id,))

        categories = record_get_value_with_provenence(record=record,
                                                      provenence_code="2",
                                                      provenence_value="arXiv",
                                                      **split_tag_code(category_code))
        comments = record_get_value_with_provenence(record=record,
                                                    provenence_code="9",
                                                    provenence_value="arXiv",
                                                    **split_tag_code(notes_code))
        external_ids = arxiv_id
        subject = "ARXIV:" + arxiv_id
    else:
        # Not an arxiv record - Lets get generic info
        categories = record_get_value_with_provenence(record=record,
                                                      provenence_code="2",
                                                      provenence_value="SzGeCERN",
                                                      **split_tag_code(category_code))
        comments = record_get_field_values(rec=record,
                                           **split_tag_code(notes_code))
        external_id_list = record_get_field_values(rec=record,
                                                   **split_tag_code(external_id_code))
        external_ids = ", ".join(external_id_list)
        subject = "Record #%s %s" % (recid, external_ids)

    authors = record_get_field_values(record, **split_tag_code(first_author_code)) + \
              record_get_field_values(record, **split_tag_code(additional_author_code))

    text = """
%(submitdate)s

External IDs: %(external_ids)s

Title: %(title)s

Authors: %(authors)s

Categories: %(categories)s

Comments: %(comments)s

%(abstract)s

%(extra_info)s

Edit the record now: %(editurl)s

""" \
    % {
        'external_ids': external_ids,
        'submitdate': record_get_field_value(record, **split_tag_code(date_code)),
        'extra_info': "\n".join(extra_info),
        'title': record_get_field_value(record, **split_tag_code(title_code)),
        'comments': "; ".join(comments),
        'categories': " ".join(categories),
        'authors': " / ".join(authors[:10]),
        'abstract': record_get_field_value(record, **split_tag_code(abstract_code)),
        'editurl': "%s/record/edit/%s" % (CFG_SITE_URL, recid),
    }
    # To avoid errors with string formatting later, we are escaping %'s
    ticket.subject = subject
    ticket.body = text.replace('%', '%%')
    ticket.queue = "Test"
    return ticket


def _get_minimal_arxiv_id(record, tag_code):
    """
    Returns the OAI arXiv id in the given record skipping the prefixes.
    I.e. oai:arxiv.org:1234.1234 becomes 1234.1234 and oai:arxiv.org:hep-ex/2134123
    becomes hep-ex/2134123. Used for searching.
    """
    values = record_get_field_values(record,
                                     **split_tag_code(tag_code))
    for value in values:
        if 'arXiv' in value:
            return value.split(':')[-1]
