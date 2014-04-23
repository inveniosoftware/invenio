## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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


# pylint: disable=W0611
# Disabling unused import pylint check, since these are needed to get
# imported here, and are called later dynamically.

from invenio.bibformat_dblayer import get_tag_from_name

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL, \
    CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_BIBSCHED, \
    CFG_BIBRANK_SHOW_DOWNLOAD_STATS, \
    CFG_WEBAUTHORPROFILE_CACHE_EXPIRED_DELAY_LIVE, \
    CFG_WEBAUTHORPROFILE_USE_ALLOWED_FIELDCODES, \
    CFG_WEBAUTHORPROFILE_ALLOWED_FIELDCODES, \
    CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
    CFG_SITE_NAME, CFG_INSPIRE_SITE, \
    CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, \
    CFG_BIBINDEX_CHARS_PUNCTUATION, \
    CFG_WEBSEARCH_WILDCARD_LIMIT

# maximum number of collaborating authors etc shown in GUI
from invenio.config import CFG_WEBAUTHORPROFILE_MAX_COLLAB_LIST, \
    CFG_WEBAUTHORPROFILE_MAX_KEYWORD_LIST, CFG_WEBAUTHORPROFILE_MAX_FIELDCODE_LIST, \
    CFG_WEBAUTHORPROFILE_MAX_AFF_LIST, CFG_WEBAUTHORPROFILE_MAX_COAUTHOR_LIST, \
    CFG_WEBAUTHORPROFILE_ORCID_ENDPOINT_PUBLIC, CFG_WEBAUTHORPROFILE_ORCID_ENDPOINT_MEMBER


# controlled keyword:
marc_tag_control_keyword = get_tag_from_name('controlled keyword')
if marc_tag_control_keyword:
    CFG_WEBAUTHORPROFILE_KEYWORD_TAG = marc_tag_control_keyword
else:
    CFG_WEBAUTHORPROFILE_KEYWORD_TAG = '695__a'

# subject:
marc_tag_subject = get_tag_from_name('subject')
if marc_tag_subject:
    CFG_WEBAUTHORPROFILE_FIELDCODE_TAG = marc_tag_subject
else:
    CFG_WEBAUTHORPROFILE_FIELDCODE_TAG = '65017a'

# uncontrolled keyword:
marc_tag_uncontrol_keyword = get_tag_from_name('uncontrolled keyword')
if marc_tag_uncontrol_keyword:
    CFG_WEBAUTHORPROFILE_FKEYWORD_TAG = marc_tag_uncontrol_keyword
else:
    CFG_WEBAUTHORPROFILE_FKEYWORD_TAG = '65017a'

# collaboration:
marc_tag_collaboration = get_tag_from_name('collaboration')
if marc_tag_collaboration:
    CFG_WEBAUTHORPROFILE_COLLABORATION_TAG = marc_tag_collaboration
else:
    CFG_WEBAUTHORPROFILE_COLLABORATION_TAG = '65017a'

CFG_WEBAUTHORPROFILE_GENERATED_TIMESTAMP_BOTTOM_POSITION = True


try:
    from cPickle import loads
except ImportError:
    from pickle import loads
from msgpack import packb, unpackb

serialize = packb
deserialize = unpackb

def _deserialize(bin_obj):
    def unpack(bobj):
        try:
            unpacked = unpackb(bobj)
        except:
            unpacked = None
        return unpacked

    unpacked = unpack(bin_obj)
    if isinstance(unpacked, int):
        try:
            return loads(bin_obj)
        except EOFError:
            return unpacked
        except:
            raise Exception()
    return unpacked
