# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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
Solr utilities.
"""


from invenio.config import CFG_SOLR_URL
from invenio.legacy.miscutil.solrutils_config import CFG_SOLR_INVALID_CHAR_RANGES
from invenio.ext.logging import register_exception


if CFG_SOLR_URL:
    import solr
    SOLR_CONNECTION = solr.SolrConnection(CFG_SOLR_URL) # pylint: disable=E1101


def replace_invalid_solr_characters(utext):
    def replace(x):
        o = ord(x)
        for r in CFG_SOLR_INVALID_CHAR_RANGES:
            if r[0] <= o <= r[1]:
                return r[2]
        return x

    utext_elements = map(replace, utext)
    return ''.join(utext_elements)


def solr_add_fulltext(recid, text):
    """
    Helper function that dispatches TEXT to Solr for given record ID.
    Returns True/False upon success/failure.
    """
    if recid:
        try:
            utext = unicode(text, 'utf-8')
            utext = replace_invalid_solr_characters(utext)
            SOLR_CONNECTION.add(id=recid, abstract="", author="", fulltext=utext, keyword="", title="")
            return True
        except (UnicodeDecodeError, UnicodeEncodeError):
            # forget about bad UTF-8 files
            pass
        except:
            # In case anything else happens
            register_exception(alert_admin=True)
    return False


def solr_commit():
    try:
        # Commits might cause an exception, most likely a
        # timeout while hitting a background merge
        # Changes will then be committed later by the
        # calling (periodical) task
        # Also, autocommits can be used in the solrconfig
        SOLR_CONNECTION.commit()
    except:
        register_exception(alert_admin=True)
