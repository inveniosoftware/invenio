# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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

"""Invenio BibRank Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import invenio.legacy.bibrank.adminlib as brc
#reload(brc)
from invenio.legacy.webpage import page, error_page
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_SITE_NAME
from invenio.legacy.webuser import getUid, page_not_authorized

def index(req, ln=CFG_SITE_LANG):
    navtrail_previous_links = brc.getnavtrail() # + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="BibRank Admin Interface",
                body=brc.perform_index(ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addrankarea(req, ln=CFG_SITE_LANG, rnkcode='', template='', confirm=-1):
    navtrail_previous_links = brc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py/">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="Add new rank method",
                body=brc.perform_addrankarea(rnkcode=rnkcode,
                                             ln=ln,
                                             template=template,
                                             confirm=confirm),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                req=req,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifytranslations(req, rnkID='', ln=CFG_SITE_LANG, sel_type='', trans = [], confirm=0):
    navtrail_previous_links = brc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py/">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="Modify translations",
                    body=brc.perform_modifytranslations(rnkID=rnkID,
                                                        ln=ln,
                                                        sel_type=sel_type,
                                                        trans=trans,
                                                        confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifycollection(req, ln=CFG_SITE_LANG, rnkID='', func='', colID='', confirm=0):
    navtrail_previous_links = brc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py/">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="Modify visibility toward collections",
                body=brc.perform_modifycollection(rnkID=rnkID,
                                                 ln=ln,
                                                 func=func,
                                                 colID=colID,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def deleterank(req, ln=CFG_SITE_LANG, rnkID='', confirm=0):
    navtrail_previous_links = brc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py/">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="Delete rank method",
                body=brc.perform_deleterank(rnkID=rnkID,
                                                 ln=ln,
                                                 confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyrank(req, ln=CFG_SITE_LANG, rnkID='', rnkcode='', template='', cfgfile='', confirm=0):
    navtrail_previous_links = brc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py/">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="Modify rank method",
                body=brc.perform_modifyrank(rnkID=rnkID,
                                            ln=ln,
                                            rnkcode=rnkcode,
                                            cfgfile=cfgfile,
                                            template=template,
                                            confirm=confirm),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showrankdetails(req, ln=CFG_SITE_LANG, rnkID=''):
    navtrail_previous_links = brc.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibrank/bibrankadmin.py/">BibRank Admin Interface</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = brc.check_user(req,'cfgbibrank')
    if not auth[0]:
        return page(title="Rank method details",
                body=brc.perform_showrankdetails(rnkID=rnkID,
                                                 ln=ln),
                uid=uid,
                language=ln,
                req=req,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)
