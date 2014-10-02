# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

""" Bibcheck plugin add the DOIs (from crossref) """

from invenio.bibrecord import record_add_field
from invenio.crossrefutils import get_doi_for_records
from invenio.bibupload import find_record_from_doi


def check_records(records, doi_field="0247_a", extra_subfields=(("2", "DOI"), ("9", "bibcheck"))):
    """
    Find the DOI for the records using crossref and add it to the specified
    field.

    This plugin won't ask for the DOI if it's already set.
    """
    records_to_check = {}
    for record in records:
        has_doi = False
        for position, value in record.iterfield("0247_2"):
            if value.lower() == "doi":
                has_doi = True
                break
        if not has_doi:
            records_to_check[record.record_id] = record

    dois = get_doi_for_records(records_to_check.values())
    for record_id, doi in dois.iteritems():
        record = records_to_check[record_id]
        dup_doi_recid = find_record_from_doi(doi)
        if dup_doi_recid:
            record.warn("DOI %s to be added to record %s already exists in record/s %s" % (doi, record_id, dup_doi_recid))
            continue
        subfields = [(doi_field[5], doi.encode("utf-8"))] + map(tuple, extra_subfields)
        record_add_field(record, tag=doi_field[:3], ind1=doi_field[3],
                ind2=doi_field[4], subfields=subfields)
        record.set_amended("Added DOI in field %s" % doi_field)
