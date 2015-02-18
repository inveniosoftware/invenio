# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2015 CERN.
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

"""Invenio OAI Repository Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import invenio.legacy.oairepository.admin as ora
from invenio.legacy.webpage import page
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.legacy.webuser import getUid, page_not_authorized

from sqlalchemy.exc import SQLAlchemyError as Error


def index(req, ln=CFG_SITE_LANG):
    navtrail_previous_links = ora.getnavtrail(ln=ln)

    try:
        uid = getUid(req)
    except Error as e:
        return page(title="OAI Repository Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = ora.check_user(req, 'cfgoairepository')
    if not auth[0]:

        return page(title="OAI Repository Admin Interface",
                body=ora.perform_request_index(ln),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                lastupdated=__lastupdated__,
                req=req)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addset(req, oai_set_name='', oai_set_spec='', oai_set_collection='', oai_set_description='', oai_set_p1='', oai_set_f1='', oai_set_m1='', oai_set_p2='', oai_set_f2='', oai_set_m2='', oai_set_p3='', oai_set_f3='', oai_set_m3='', oai_set_op1='a', oai_set_op2='a', ln=CFG_SITE_LANG, func=0):

    navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oairepository/oairepositoryadmin.py?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error as e:
        return page(title="OAI Repository Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = ora.check_user(req,'cfgoairepository')
    if not auth[0]:
        return page(title="Add new OAI Set",
                body=ora.perform_request_addset(oai_set_name=oai_set_name,
                                           oai_set_spec=oai_set_spec,
                                           oai_set_collection=oai_set_collection,
                                           oai_set_description=oai_set_description,
                                           oai_set_p1=oai_set_p1,
                                           oai_set_f1=oai_set_f1,
                                           oai_set_m1=oai_set_m1,
                                           oai_set_p2=oai_set_p2,
                                           oai_set_f2=oai_set_f2,
                                           oai_set_m2=oai_set_m2,
                                           oai_set_p3=oai_set_p3,
                                           oai_set_f3=oai_set_f3,
                                           oai_set_m3=oai_set_m3,
                                           oai_set_op1=oai_set_op1,
                                           oai_set_op2=oai_set_op2,
                                           ln=ln,
                                           func=func),
                uid=uid,
                language=ln,
                navtrail = navtrail_previous_links,
                req=req,
                lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def delset(req, oai_set_id=None, ln=CFG_SITE_LANG, func=0):
    navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oairepository/oairepositoryadmin.py?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error as e:
        return page(title="OAI Repository Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = ora.check_user(req,'cfgoairepository')
    if not auth[0]:
        return page(title="Delete OAI Set",
                    body=ora.perform_request_delset(oai_set_id=oai_set_id,
                                                    ln=ln,
                                                    func=func),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def touchset(req, oai_set_id=None, ln=CFG_SITE_LANG, func=0):
    navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oairepository/oairepositoryadmin.py?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error as e:
        return page(title="OAI Repository Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = ora.check_user(req,'cfgoairepository')
    if not auth[0]:
        return page(title="Touch OAI Set",
                    body=ora.perform_request_touchset(oai_set_id=oai_set_id,
                                                    ln=ln,
                                                    func=func),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def editset(req, oai_set_id=None, oai_set_name='', oai_set_spec='', oai_set_collection='', oai_set_description='', oai_set_p1='', oai_set_f1='', oai_set_m1='', oai_set_p2='', oai_set_f2='', oai_set_m2='', oai_set_p3='', oai_set_f3='', oai_set_m3='', oai_set_op1='a', oai_set_op2='a', ln=CFG_SITE_LANG, func=0):

    navtrail_previous_links = ora.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oairepository/oairepositoryadmin.py?ln=%s">OAI Repository Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error as e:
        return page(title="OAI Repository Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = ora.check_user(req,'cfgoairepository')
    if not auth[0]:
        return page(title="Edit OAI Set",
                    body=ora.perform_request_editset(oai_set_id=oai_set_id,
                                                     oai_set_name=oai_set_name,
                                                     oai_set_spec=oai_set_spec,
                                                     oai_set_collection=oai_set_collection,
                                                     oai_set_description=oai_set_description,
                                                     oai_set_p1=oai_set_p1,
                                                     oai_set_f1=oai_set_f1,
                                                     oai_set_m1=oai_set_m1,
                                                     oai_set_p2=oai_set_p2,
                                                     oai_set_f2=oai_set_f2,
                                                     oai_set_m2=oai_set_m2,
                                                     oai_set_p3=oai_set_p3,
                                                     oai_set_f3=oai_set_f3,
                                                     oai_set_m3=oai_set_m3,
                                                     oai_set_op1=oai_set_op1,
                                                     oai_set_op2=oai_set_op2,
                                                     ln=ln,
                                                     func=func),

                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)
