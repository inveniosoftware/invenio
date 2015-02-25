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

"""Invenio BibIndex Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import invenio.legacy.bibindex.adminlib as bic
from invenio.legacy.webpage import page, error_page
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_SITE_NAME
from invenio.legacy.webuser import getUid, page_not_authorized

def deletetag(req, fldID, ln=CFG_SITE_LANG, tagID=-1, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_deletetag(fldID=fldID,
                                               ln=ln,
                                               tagID=tagID,
                                               callback=callback,
                                               confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addtag(req, fldID, ln=CFG_SITE_LANG, name='', value='', recjson_value='', existing_tag=-1, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_addtag(fldID=fldID,
                                            ln=ln,
                                            existing_tag=existing_tag,
                                            value=value,
                                            recjson_value=recjson_value,
                                            name=name,
                                            callback=callback,
                                            confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyfieldtags(req, fldID, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_modifyfieldtags(fldID=fldID,
                                                   ln=ln,
                                                   callback=callback,
                                                   confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addindexfield(req, idxID, ln=CFG_SITE_LANG, fldID='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_addindexfield(idxID=idxID,
                                            ln=ln,
                                            fldID=fldID,
                                            callback=callback,
                                            confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyindexfields(req, idxID, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyindexfields(idxID=idxID,
                                                   ln=ln,
                                                   callback=callback,
                                                   confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showdetailsfieldtag(req, fldID, tagID, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_showdetailsfieldtag(fldID=fldID,
                                                         tagID=tagID,
                                                         ln=ln,
                                                         callback=callback,
                                                         confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showdetailsfield(req, fldID, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_showdetailsfield(fldID=fldID,
                                                      ln=ln,
                                                      callback=callback,
                                                      confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyfield(req, fldID, ln=CFG_SITE_LANG, code='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_modifyfield(fldID=fldID,
                                                 ln=ln,
                                                 code=code,
                                                 callback=callback,
                                                 confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyindex(req, idxID, ln=CFG_SITE_LANG, idxNAME='', idxDESC='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyindex(idxID=idxID,
                                                 ln=ln,
                                                 idxNAME=idxNAME,
                                                 idxDESC=idxDESC,
                                                 callback=callback,
                                                 confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def modifyindexstemming(req, idxID, ln=CFG_SITE_LANG, idxSTEM='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyindexstemming(idxID=idxID,
                                                 ln=ln,
                                                 idxSTEM=idxSTEM,
                                                 callback=callback,
                                                 confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifyindexer(req, idxID, ln=CFG_SITE_LANG, indexer='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyindexer(idxID=idxID,
                                                   ln=ln,
                                                   indexer=indexer,
                                                   callback=callback,
                                                   confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifydependentindexes(req, idxID, ln=CFG_SITE_LANG, newIDs=[], callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Virtual Index",
                    body=bic.perform_modifydependentindexes(idxID=idxID,
                                                            ln=ln,
                                                            newIDs=newIDs,
                                                            callback=callback,
                                                            confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifysynonymkb(req, idxID, ln=CFG_SITE_LANG, idxKB='', idxMATCH='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail()
    navtrail_previous_links += """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a>""" % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifysynonymkb(idxID=idxID,
                                                     ln=ln,
                                                     idxKB=idxKB,
                                                     idxMATCH=idxMATCH,
                                                     callback=callback,
                                                     confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifystopwords(req, idxID, ln=CFG_SITE_LANG, idxSTOPWORDS='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail()
    navtrail_previous_links += """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifystopwords(idxID=idxID,
                                                     ln=ln,
                                                     idxSTOPWORDS=idxSTOPWORDS,
                                                     callback=callback,
                                                     confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifyremovehtml(req, idxID, ln=CFG_SITE_LANG, idxHTML='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail()
    navtrail_previous_links += """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyremovehtml(idxID=idxID,
                                                      ln=ln,
                                                      idxHTML=idxHTML,
                                                      callback=callback,
                                                      confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifyremovelatex(req, idxID, ln=CFG_SITE_LANG, idxLATEX='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail()
    navtrail_previous_links += """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyremovelatex(idxID=idxID,
                                                       ln=ln,
                                                       idxLATEX=idxLATEX,
                                                       callback=callback,
                                                       confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifytokenizer(req, idxID, ln=CFG_SITE_LANG, idxTOK='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail()
    navtrail_previous_links += """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifytokenizer(idxID=idxID,
                                                     ln=ln,
                                                     idxTOK=idxTOK,
                                                     callback=callback,
                                                     confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifytag(req, fldID, tagID, ln=CFG_SITE_LANG, name='', value='', recjson_value='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_modifytag(fldID=fldID,
                                               tagID=tagID,
                                               ln=ln,
                                               name=name,
                                               value=value,
                                               recjson_value=recjson_value,
                                               callback=callback,
                                               confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def deletefield(req, fldID, ln=CFG_SITE_LANG, confirm=0):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_deletefield(fldID=fldID,
                                                 ln=ln,
                                                 confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def deleteindex(req, idxID, ln=CFG_SITE_LANG, confirm=0):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_deleteindex(idxID=idxID,
                                                 ln=ln,
                                                 confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def deletevirtualindex(req, idxID, ln=CFG_SITE_LANG, confirm=0):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req, 'cfgbibindex')
    if not auth[0]:
        return page(title="Manage Indexes",
                    body=bic.perform_deletevirtualindex(idxID=idxID,
                                                        ln=ln,
                                                        confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def showfieldoverview(req, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage logical fields",
                    body=bic.perform_showfieldoverview(ln=ln,
                                                 callback=callback,
                                                 confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editfields(req, ln=CFG_SITE_LANG, callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage logical fields",
                    body=bic.perform_editfields(ln=ln,
                                                callback=callback,
                                                confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editfield(req, fldID, ln=CFG_SITE_LANG, mtype='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_editfield(fldID=fldID,
                                               ln=ln,
                                               mtype=mtype,
                                               callback=callback,
                                               confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editindex(req, idxID, ln=CFG_SITE_LANG, mtype='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_editindex(idxID=idxID,
                                               ln=ln,
                                               mtype=mtype,
                                               callback=callback,
                                               confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editvirtualindex(req, idxID, ln=CFG_SITE_LANG, mtype='', callback='yes', confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)


    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit virtual index",
                    body=bic.perform_editvirtualindex(idxID=idxID,
                                                      ln=ln,
                                                      mtype=mtype,
                                                      callback=callback,
                                                      confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def modifyindextranslations(req, idxID, ln=CFG_SITE_LANG, sel_type='', trans = [], confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_modifyindextranslations(idxID=idxID,
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

def modifyfieldtranslations(req, fldID, ln=CFG_SITE_LANG, sel_type='', trans = [], confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_modifyfieldtranslations(fldID=fldID,
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

def addfield(req, ln=CFG_SITE_LANG, fldNAME='', code='', callback="yes", confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage logical fields",
                    body=bic.perform_addfield(ln=ln,
                                              fldNAME=fldNAME,
                                              code=code,
                                              callback=callback,
                                              confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addindex(req, ln=CFG_SITE_LANG, idxNAME='', callback="yes", confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage Indexes",
                    body=bic.perform_addindex(ln=ln,
                                              idxNAME=idxNAME,
                                              callback=callback,
                                              confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def addvirtualindex(req, ln=CFG_SITE_LANG, idxNEWVID='', idxNEWPID='', callback="yes", confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage Indexes",
                    body=bic.perform_addvirtualindex(ln=ln,
                                                     idxNEWVID=idxNEWVID,
                                                     idxNEWPID=idxNEWPID,
                                                     callback=callback,
                                                     confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def switchtagscore(req, fldID, id_1, id_2, ln=CFG_SITE_LANG):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_switchtagscore(fldID=fldID,
                                                    id_1=id_1,
                                                    id_2=id_2,
                                                    ln=ln),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def removeindexfield(req, idxID, fldID, ln=CFG_SITE_LANG, callback="yes", confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/index">Manage Indexes</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Index",
                    body=bic.perform_removeindexfield(idxID=idxID,
                                                    fldID=fldID,
                                                    ln=ln,
                                                    callback=callback,
                                                    confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def removefieldtag(req, fldID, tagID, ln=CFG_SITE_LANG, callback="yes", confirm=-1):
    navtrail_previous_links = bic.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/bibindex/bibindexadmin.py/field">Manage logical fields</a> """ % (CFG_SITE_URL)

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Edit Logical Field",
                    body=bic.perform_removefieldtag(fldID=fldID,
                                                    tagID=tagID,
                                                    ln=ln,
                                                    callback=callback,
                                                    confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def index(req, ln=CFG_SITE_LANG, mtype='', content=''):
    navtrail_previous_links = bic.getnavtrail()

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage Indexes",
                    body=bic.perform_index(ln=ln,
                                           mtype=mtype,
                                           content=content),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def field(req, ln=CFG_SITE_LANG, mtype='', content=''):
    navtrail_previous_links = bic.getnavtrail()

    try:
        uid = getUid(req)
    except:
        return error_page('Error', req)

    auth = bic.check_user(req,'cfgbibindex')
    if not auth[0]:
        return page(title="Manage logical fields",
                    body=bic.perform_field(ln=ln,
                                           mtype=mtype,
                                           content=content),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)
