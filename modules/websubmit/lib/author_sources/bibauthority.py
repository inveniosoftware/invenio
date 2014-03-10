# This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

from invenio.search_engine import perform_request_search
from invenio.bibfield import get_record
from invenio.bibfield_utils import retrieve_authorid_type,retrieve_authorid_id
from invenio.websubmit_config import CFG_SUBFIELFD_TO_JSON_FIELDS

CFG_SOURCE_NAME = "bibauthority"
CFG_LIMIT_RESULTS = 100

def query_author_source(nickname):
    """
    Query the current database for records that belong to
    the collection "People" and have the string nickname
    inside them, so the can be used for autocompletion.
    """

    # query for matches
    recids = perform_request_search(c="People", p=nickname)
    authors = []

    # Convert the database results into a dictionary with the
    # id fields values cleanly separated from their id type
    # for the frontend javascript code to reconstruct the
    # existing authors list as it was when it was submitted
    for recid in recids[:CFG_LIMIT_RESULTS]:

        record = get_record(recid)

        author = {
            "name": record["authors"][0]["full_name"],
        }
        author.update({
            CFG_SUBFIELFD_TO_JSON_FIELDS["0"].get(retrieve_authorid_type(x["value"])) or retrieve_authorid_type(x["value"]): retrieve_authorid_id(x["value"]) for x in record["system_control_number"] if type(x) is dict
        })

        authors.append(author)

    return authors
