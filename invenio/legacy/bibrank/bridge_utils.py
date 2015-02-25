# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2012, 2013 CERN.
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


import ConfigParser
import re
from six import iteritems
from invenio.legacy.bibrank.bridge_config import CFG_BIBRANK_WRD_CFG_PATH
from invenio.legacy.search_engine import get_fieldvalues
from invenio.legacy.bibindex.adminlib import get_fld_id, get_fld_tags


def get_external_word_similarity_ranker():
    for line in open(CFG_BIBRANK_WRD_CFG_PATH):
        for ranker in ('solr', 'xapian'):
            if 'word_similarity_%s' % ranker in line:
                return ranker
    return False


def get_tags():
    """
    Returns the tags per Solr field as a dictionary.
    """
    tags = {}
    for (field_name, logical_fields) in iteritems(get_logical_fields()):
        tags_of_logical_fields = []
        for logical_field in logical_fields:
            field_id = get_fld_id(logical_field)
            tags_of_logical_fields.extend([tag[3] for tag in get_fld_tags(field_id)])
        tags[field_name] = tags_of_logical_fields
    return tags


def get_logical_fields():
    """
    Returns the logical fields per Solr field as a dictionary.
    """
    fields = {}
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open(CFG_BIBRANK_WRD_CFG_PATH))
    except StandardError:
        return fields

    sections = config.sections()
    field_pattern = re.compile('field[0-9]+')
    for section in sections:
        if field_pattern.search(section):
            field_name = config.get(section, 'name')
            if config.has_option(section, 'logical_fields'):
                logical_fields = config.get(section, 'logical_fields')
                fields[field_name] = [f.strip() for f in logical_fields.split(',')]
    return fields


def get_field_content_in_utf8(recid, field, tag_dict, separator=' '):
    """
    Returns the content of a field comprised of tags
    concatenated in an UTF-8 string.
    """
    content = ''
    try:
        values = []
        for tag in tag_dict[field]:
            values.extend(get_fieldvalues(recid, tag))
        content = unicode(separator.join(values), 'utf-8')
    except:
        pass
    return content
