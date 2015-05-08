# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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
Check the metadata of the records that contain a DOI by comparing it to the
metadata returned by crossref.
"""

from invenio.utils.crossref import get_metadata_for_dois
from invenio.modules.knowledge.api import get_kbr_values
import difflib
import re

def compare_str(str1, str2):
    """ Return similarity (0.0 to 1.0) between the two strings """
    return difflib.SequenceMatcher(None, str1, str2).ratio()

def xpath_text(doc, query):
    """ Get the text inside the element result of the xpath query """
    nodes = doc.xpath(query)
    if len(nodes) == 0:
        return None
    return nodes[0].text

def get_value(record, tag):
    """ Get the value of a (unique) field or null """
    record_values = list(record.iterfield(tag))
    if len(record_values) == 0:
        return None
    return record_values[0][1]

def compare_metadata(metadata, rec):
    """
    Compare a record with the metadata returned by crossref
    @param rec Record
    @param doc xml.etree.ElementTree representation of the xml returned by crossref
    """
    confidence_different = 0
    msgs = []

    # Check title
    title_crossref = metadata["title"]
    title_record = get_value(rec, "773__p")
    title_similarity = None
    volume_extra = ""
    if title_crossref != "" and title_record is not None:
        # Remove Volume number from the title
        title_crossref = re.sub(":.*$", "", title_crossref)
        if re.search(" [A-Z]$", title_crossref):
            volume_extra = title_crossref[-1]
            title_crossref = title_crossref[:-2]
        title_crossref = re.sub(" (Section|Volume)$", "", title_crossref)
        abbr_title = get_kbr_values("JOURNALS", title_crossref, searchtype='e')
        title_similarity = compare_str(abbr_title, title_record)
        confidence_different += (1 - title_similarity)*2
        if title_similarity < 0.6:
            msgs.append("Incorrect journal name (773__p) or wrongly assigned DOI")

    # Check issn
    issn_crossref = metadata["issn"]
    issn_record = get_value(rec, "022__a")
    if issn_crossref != "" and issn_record is not None and issn_crossref != issn_record:
        confidence_different += 3
        msgs.append("Invalid ISSN (022__a) or wrongly assigned DOI")

    # Check page number
    page_crossref = metadata["page"]
    page_record = get_value(rec, "773__c")
    if page_record is not None and page_crossref != "":
        page_record = page_record.split("-")[0]
        page_crossref = page_crossref.split("-")[0]
        if page_record != page_crossref:
            confidence_different += 3
            msgs.append("Invalid page number (773__c) or wrongly assigned DOI")

    # Check author
    author_crossref = metadata["author"]
    author_record = get_value(rec, "100__a")
    if author_crossref != "" and author_record is not None:
        author_similarity = compare_str(author_crossref, author_record)
        confidence_different += (1 - author_similarity)*1.5
        if author_similarity < 0.7:
            msgs.append("Invalid author (100__a) or wrongly assigned DOI")

    # Check issue
    issue_crossref = metadata["issue"]
    issue_record = get_value(rec, "773__n")
    if issue_crossref != "" and issue_record is not None and issue_crossref != issue_record:
        confidence_different += 2
        msgs.append("Invalid issue (773__n) or wrongly assigned DOI")


    # Check year
    year_crossref = metadata["year"]
    year_record = get_value(rec, "773__y")
    if year_crossref != "" and year_record is not None and year_crossref != year_record:
        confidence_different += 2
        msgs.append("Invalid year (773__y) or wrongly assigned DOI")

    # Check volume
    volume_crossref = metadata["volume"]
    volume_record = get_value(rec, "773__v")
    if volume_crossref != "" and volume_record is not None:
        volume_crossref = volume_extra + volume_crossref
        if volume_crossref != volume_record:
            confidence_different += 2
            msgs.append("Invalid volume (773__v) or wrongly assigned DOI")

    if confidence_different > 4:
        for msg in msgs:
            rec.set_invalid(msg)


def check_records(records, doi_field="0247_a"):
    """
    Check the metadata of the records that contain a DOI by comparing it to the
    metadata returned by crossref.
    """
    records_to_check = {}
    for record in records:
        # FIXME: check the type of the identifier
        for _, doi in record.iterfield(doi_field):
            records_to_check[doi] = record

    metadatas = get_metadata_for_dois(records_to_check.keys())
    for doi, metadata in metadatas.iteritems():
        # Can't compare books yet
        if not metadata["is_book"]:
            compare_metadata(metadata, records_to_check[doi])

