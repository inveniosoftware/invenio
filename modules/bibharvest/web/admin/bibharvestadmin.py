## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio BibHarvest Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import invenio.bibharvestadminlib as bhc
from invenio.webpage import page, create_error_box
from invenio.config import CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_LANG
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized

def index(req, ln=CFG_SITE_LANG):
    navtrail_previous_links = bhc.getnavtrail()

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="BibHarvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = bhc.check_user(req,'cfgbibharvest')
    if not auth[0]:
        return page(title="BibHarvest Admin Interface",
                    body=bhc.perform_request_index(ln),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editsource(req, oai_src_id=None, oai_src_name='', oai_src_baseurl='', oai_src_prefix='', oai_src_frequency='', oai_src_config='', oai_src_post='', ln=CFG_SITE_LANG, mtype='', callback='yes', confirm=-1, oai_src_sets=[], oai_src_bibfilter=''):
    navtrail_previous_links = bhc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibharvest/bibharvestadmin.py">BibHarvest Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="BibHarvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = bhc.check_user(req,'cfgbibharvest')
    if not auth[0]:
        if isinstance(oai_src_sets, str):
            oai_src_sets = [oai_src_sets]
        return page(title="Edit OAI Source",
                    body=bhc.perform_request_editsource(oai_src_id=oai_src_id,
                                                        oai_src_name=oai_src_name,
                                                        oai_src_baseurl=oai_src_baseurl,
                                                        oai_src_prefix=oai_src_prefix,
                                                        oai_src_frequency=oai_src_frequency,
                                                        oai_src_config=oai_src_config,
                                                        oai_src_post=oai_src_post,
                                                        oai_src_sets=oai_src_sets,
                                                        oai_src_bibfilter=oai_src_bibfilter,
                                                        ln=ln,
                                                        confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addsource(req, ln=CFG_SITE_LANG, oai_src_name='', oai_src_baseurl ='', oai_src_prefix='', oai_src_frequency='', oai_src_lastrun='', oai_src_config='', oai_src_post='', confirm=-1, oai_src_sets=[], oai_src_bibfilter=''):
    navtrail_previous_links = bhc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibharvest/bibharvestadmin.py">BibHarvest Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="BibHarvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = bhc.check_user(req,'cfgbibharvest')
    if not auth[0]:
        if isinstance(oai_src_sets, str):
            oai_src_sets = [oai_src_sets]
        return page(title="Add new OAI Source",
                    body=bhc.perform_request_addsource(oai_src_name=oai_src_name,
                                                       oai_src_baseurl=oai_src_baseurl,
                                                       oai_src_prefix=oai_src_prefix,
                                                       oai_src_frequency=oai_src_frequency,
                                                       oai_src_lastrun=oai_src_lastrun,
                                                       oai_src_config=oai_src_config,
                                                       oai_src_post=oai_src_post,
                                                       oai_src_sets=oai_src_sets,
                                                       oai_src_bibfilter=oai_src_bibfilter,
                                                       ln=ln,
                                                       confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def delsource(req, oai_src_id=None, ln=CFG_SITE_LANG, confirm=0):
    navtrail_previous_links = bhc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibharvest/bibharvestadmin.py">BibHarvest Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="BibHarvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = bhc.check_user(req,'cfgbibharvest')
    if not auth[0]:
        return page(title="Delete OAI Source",
                    body=bhc.perform_request_delsource(oai_src_id=oai_src_id,
                                                    ln=ln,
                                                    confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)
