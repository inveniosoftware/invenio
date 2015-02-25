# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""General config file for ES index."""


################ Fields ###############

def get_collections_fields_config():
    """Mapping for collections."""
    mapping = {
        "recid": {"type": "integer"},
        "name": {
            "type": "string",
            "analyzer": "keyword"}}

    return mapping


def get_documents_fields_config():
    """Mapping for documents."""
    mapping = {
        #force recid type to integer for default sorting
        "recid": {"type": "integer"},
        "fulltext": {"type": "string"},
    }
    return mapping


def get_records_fields_config():
    """Mapping for records."""
    from invenio.modules.jsonalchemy.parser import FieldParser
    fields = FieldParser.field_definitions('recordext')
    mapping = {}
    for name, value in fields.iteritems():
        current_mapping = value.get("elasticsearch", {}).get("mapping")
        if current_mapping:
            mapping.update(current_mapping)
    return mapping


################ Highlights ###############

HIGHLIGHTS_BASE_CONFIG = {
    "number_of_fragments": 3,
    "fragment_size": 70
}


def get_records_highlights_config():
    """Get hilights config for records."""
    from invenio.modules.jsonalchemy.parser import FieldParser
    fields = FieldParser.field_definitions('recordext')
    highlights = {}
    for name, value in fields.iteritems():
        current_highlights = value.get("elasticsearch", {}).get("highlights")
        if current_highlights:
            highlights.update(current_highlights)
    config = {
        "fields": highlights
    }
    return config


def get_documents_highlights_config():
    """Get hilights config for fulltext document."""
    config = {
        "fields": {
            "fulltext": HIGHLIGHTS_BASE_CONFIG
        }
    }
    return config


################ Facets ###############

def get_records_facets_config():
    """Get facets config for records."""
    from invenio.modules.jsonalchemy.parser import FieldParser
    fields = FieldParser.field_definitions('recordext')
    facets = {}
    for name, value in fields.iteritems():
        current_facet = value.get("elasticsearch", {}).get("facets")
        if current_facet:
            facets.update(current_facet)
    return facets
