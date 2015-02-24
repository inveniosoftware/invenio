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
webuser_config.py - magic constants for webuser module.
"""

# Used by merge_usera_into_userb, contains the list of which SQL tables refer
# to the external key id_user, and what column contains this information.
CFG_WEBUSER_USER_TABLES = (
    ## The next tables are disabled because they are often too big
    ## and not so critical to deserve merging
    #("rnkPAGEVIEWS", "id_user"),
    #("rnkDOWNLOADS", "id_user"),
    #("session", "uid"),
    ("user_usergroup", "id_user"),
    ("user_accROLE", "id_user"),
    ("user_query", "id_user"),
    ("user_query_basket", "id_user"),
    ("bskREC", "id_user_who_added_item"),
    ("user_bskBASKET", "id_user"),
    ("bskRECORDCOMMENT", "id_user"),
    ("msgMESSAGE", "id_user_from"),
    ("user_msgMESSAGE", "id_user_to"),
    ("cmtRECORDCOMMENT", "id_user"),
    ("cmtACTIONHISTORY", "id_user"),
    ("cmtSUBSCRIPTION", "id_user"),
    ("user_expJOB", "id_user"),
    ("swrCLIENTDATA", "id_user"),
    ("sbmCOOKIES", "uid"),
    ("aidUSERINPUTLOG", "userid"),
)
