## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012 CERN.
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

"""Invenio OAI Harvest Administrator Interface."""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import datetime
import urllib

import invenio.oai_harvest_admin as oha
from invenio.jsonutils import json
from invenio.webpage import page
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.dbquery import Error
from invenio.webuser import getUid, page_not_authorized
from invenio.bibrankadminlib import check_user
from invenio.oai_harvest_dblayer import get_holdingpen_day_size
from invenio.oai_harvest_config import CFG_OAI_POSSIBLE_POSTMODES
from invenio.webinterface_handler import wash_urlargd

def index(req, ln=CFG_SITE_LANG):
    """Main OAI Harvest admin page"""
    navtrail_previous_links = oha.getnavtrail(ln=ln)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        return page(title="OAI Harvest Admin Interface",
                    body=oha.perform_request_index(ln),
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def editsource(req, **kwargs):
    form = dict(req.form)
    content = {'oai_src_id': (str, None),
               'oai_src_name': (str, ""),
               'oai_src_baseurl': (str, ""),
               'oai_src_prefix': (str, ""),
               'oai_src_frequency': (str, ""),
               'oai_src_comment': (str, ""),
               'oai_src_post': (list, None),
               'ln': (str, "en"),
               'confirm': (int, -1),
               'oai_src_sets': (list, None)}
    # Grab list of defined post-process arguments to select from POST-data. e.g. ('c_cfg-file', str)
    post_arguments = [("%s_%s" % (mode[0], arg['name']), type(arg['value'])) \
                      for mode in CFG_OAI_POSSIBLE_POSTMODES \
                      for arg in mode[2]]
    for argument_name, argument_type in post_arguments:
        if argument_type == str:
            content[argument_name] = (str, "")
        elif argument_type == list:
            content[argument_name] = (list, [])

    argd = wash_urlargd(form, content)
    oai_src_id = argd['oai_src_id']
    oai_src_name = argd['oai_src_name']
    oai_src_baseurl = argd['oai_src_baseurl']
    oai_src_prefix = argd['oai_src_prefix']
    oai_src_frequency = argd['oai_src_frequency']
    oai_src_comment = argd['oai_src_comment']
    oai_src_post = argd['oai_src_post']
    ln = argd['ln']
    confirm = argd['confirm']
    oai_src_sets = argd['oai_src_sets']
    if oai_src_sets == None:
        oai_src_sets = []

    oai_src_args = {}
    for argument_name, dummy in post_arguments:
        oai_src_args[argument_name] = argd[argument_name]

    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        if isinstance(oai_src_sets, str):
            oai_src_sets = [oai_src_sets]
        return page(title="Edit OAI Source",
                    metaheaderadd=oha.getheader(),
                    body=oha.perform_request_editsource(oai_src_id=oai_src_id,
                                                        oai_src_name=oai_src_name,
                                                        oai_src_baseurl=oai_src_baseurl,
                                                        oai_src_prefix=oai_src_prefix,
                                                        oai_src_frequency=oai_src_frequency,
                                                        oai_src_post=oai_src_post,
                                                        oai_src_sets=oai_src_sets,
                                                        oai_src_comment=oai_src_comment,
                                                        oai_src_args=oai_src_args,
                                                        ln=ln,
                                                        confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def addsource(req, **kwargs):
    post_arguments = [("%s_%s" % (mode[0], arg['name']), type(arg['value'])) \
                       for mode in CFG_OAI_POSSIBLE_POSTMODES \
                       for arg in mode[2]]
    form = dict(req.form)
    content = {'ln': (str, "en"),
               'oai_src_name': (str, ""),
               'oai_src_baseurl': (str, ""),
               'oai_src_prefix': (str, ""),
               'oai_src_frequency': (str, ""),
               'oai_src_lastrun': (str, ""),
               'oai_src_comment': (str, ""),
               'oai_src_post': (list, None),
               'confirm': (int, -1),
               'oai_src_sets': (list, None)}
    for argument_name, argument_type in post_arguments:
        if argument_type == str:
            content[argument_name] = (str, "")
        elif argument_type == list:
            content[argument_name] = (list, [])

    argd = wash_urlargd(form, content)
    ln = argd['ln']
    oai_src_name = argd['oai_src_name']
    oai_src_baseurl = argd['oai_src_baseurl']
    oai_src_prefix = argd['oai_src_prefix']
    oai_src_frequency = argd['oai_src_frequency']
    oai_src_lastrun = argd['oai_src_lastrun']
    oai_src_comment = argd['oai_src_comment']
    oai_src_post = argd['oai_src_post']
    confirm = argd['confirm']
    oai_src_sets = argd['oai_src_sets']
    if oai_src_sets == None:
        oai_src_sets = []
    if oai_src_post == None:
        oai_src_post = []

    oai_src_args = {}
    for argument_name, dummy in post_arguments:
        oai_src_args[argument_name] = argd[argument_name]

    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        if isinstance(oai_src_sets, str):
            oai_src_sets = [oai_src_sets]
        return page(title="Add new OAI Source",
                    metaheaderadd=oha.getheader(),
                    body=oha.perform_request_addsource(oai_src_name=oai_src_name,
                                                       oai_src_baseurl=oai_src_baseurl,
                                                       oai_src_prefix=oai_src_prefix,
                                                       oai_src_frequency=oai_src_frequency,
                                                       oai_src_lastrun=oai_src_lastrun,
                                                       oai_src_post=oai_src_post,
                                                       oai_src_sets=oai_src_sets,
                                                       oai_src_args=oai_src_args,
                                                       oai_src_comment=oai_src_comment,
                                                       ln=ln,
                                                       confirm=confirm),
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    req=req,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def delsource(req, oai_src_id=None, ln=CFG_SITE_LANG, confirm=0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)

    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="Delete OAI Source",
                    body=oha.perform_request_delsource(oai_src_id=oai_src_id,
                                                    ln=ln,
                                                    confirm=confirm),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def testsource(req, oai_src_id=None, ln=CFG_SITE_LANG, record_id=None):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)

    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="Test OAI Source",
                    body=oha.perform_request_testsource(oai_src_id=oai_src_id,
                                                        ln=ln,
                                                        record_id=record_id),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def viewhistory(req, oai_src_id=0, ln=CFG_SITE_LANG, year = None, month = None):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    d_date = datetime.datetime.now()
    if year == None:
        year = d_date.year
    if month == None:
        month = d_date.month
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="View OAI source harvesting history",
                    body=oha.perform_request_viewhistory(oai_src_id=oai_src_id,
                                                    ln=ln,
                                                    year=int(year),
                                                    month=int(month)),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def viewhistoryday(req, oai_src_id=0, ln=CFG_SITE_LANG, year=None, month=None, day=None, start=0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    d_date = datetime.datetime.now()
    if year == None:
        year = d_date.year
    if month == None:
        month = d_date.month
    if day == None:
        day = d_date.day
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="View OAI source harvesting history",
                    body=oha.perform_request_viewhistoryday(oai_src_id=oai_src_id,
                                                    ln=ln,
                                                    year=int(year),
                                                    month=int(month),
                                                    day=int(day),
                                                    start=int(start)),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def viewentryhistory(req, oai_id=0, ln=CFG_SITE_LANG, start = 0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="View OAI source harvesting history (single record)",
                    body=oha.perform_request_viewentryhistory(oai_id=str(oai_id),
                                                    ln=ln,
                                                    start=int(start)),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def viewtasklogs(req, ln=CFG_SITE_LANG, task_id=0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        # Page refreshes every minute
        return page(title="View bibsched task logs",
                    body=oha.perform_request_viewtasklogs(ln=ln,
                                                          task_id=int(task_id)),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    metaheaderadd='<meta http-equiv="refresh" content="60" />')
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def viewhprecord(req, ln=CFG_SITE_LANG, hpupdate_id=0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="Holding Pen Record",
                    body=oha.perform_request_viewhprecord(hpupdate_id=hpupdate_id,
                                                          ln=ln),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def accepthprecord(req, ln=CFG_SITE_LANG, hpupdate_id = 0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="Holding Pen Record",
                    metaheaderadd = oha.view_holdingpen_headers(),
                    body=oha.perform_request_accepthprecord(hpupdate_id = hpupdate_id),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def delhprecord(req, ln=CFG_SITE_LANG, hpupdate_id=0):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="Holding Pen Record",
                    body=oha.perform_request_delhprecord(hpupdate_id=hpupdate_id,
                                                            ln=ln),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def reharvest(req, oai_src_id=None, ln=CFG_SITE_LANG, **records):
    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        return page(title="OAI source - reharvesting records",
                    body=oha.perform_request_reharvest_records(oai_src_id=oai_src_id,
                                                    ln=ln, record_ids = records),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def harvest(req, oai_src_id=None, ln=CFG_SITE_LANG, record_id=None,
            enable_reporting=None, confirm=0):
    form = dict(req.form)
    content = {
               'confirm': (int, confirm),
               'enable_reporting': (str, enable_reporting),
               'record_id': (str, record_id),
               'oai_src_id': (str, oai_src_id),
               'ln': (str, ln),
               }
    argd = wash_urlargd(form, content)

    navtrail_previous_links = oha.getnavtrail(' &gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py?ln=%s">OAI Harvest Admin Interface</a> ' \
                                              % (CFG_SITE_URL, ln), ln=ln)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=argd['ln'],
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        return page(title="OAI source - harvesting new records",
                    body=oha.perform_request_harvest_record(oai_src_id=argd['oai_src_id'],
                                                            ln=argd['ln'], record_id=argd['record_id'],
                                                            uid=uid, confirm=argd['confirm'],
                                                            enable_reporting=argd['enable_reporting']),
                    uid=uid,
                    language=argd['ln'],
                    req=req,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def preview_original_xml(req, oai_src_id=None, ln=CFG_SITE_LANG, record_id=None):
    navtrail_previous_links = oha.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py">OAI Harvest Admin Interface</a> """ % (CFG_SITE_URL)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        if (record_id == None) or (oai_src_id == None):
            req.content_type = "text/plain";
            req.write("No record number provided")
            return
        req.content_type = "text/xml"
        return oha.perform_request_preview_original_xml(oai_src_id, record_id)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)


def preview_harvested_xml(req, oai_src_id=None, ln=CFG_SITE_LANG, record_id=None):
    navtrail_previous_links = oha.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py">OAI Harvest Admin Interface</a> """ % (CFG_SITE_URL)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAI Harvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail = navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req,'cfgoaiharvest')
    if not auth[0]:
        if (record_id == None) or (oai_src_id == None):
            req.content_type = "text/plain";
            req.write("No record number provided")
            return
        content = oha.perform_request_preview_harvested_xml(oai_src_id, record_id)
        if content[0]:
            req.content_type = "text/xml"
        else:
            req.content_type = "text/plain"
        return content[1]
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)

def getHoldingPenData(req, elementId):
    try:
        getUid(req)
    except Error:
        return "unauthorised access !"
    auth = check_user(req, 'cfgoaiharvest')
    if auth[0]:
        return "unauthorised access !"

    elements = elementId.split("_")
    resultHtml = None

    if len(elements) == 2:
        filter_key = elements[1]
        resultHtml = oha.perform_request_gethpyears(elements[0], filter_key)
    elif len(elements) == 3:
        # only the year is specified
        filter_key = elements[2]
        nodeYear = int(elements[1])
        resultHtml = oha.perform_request_gethpyear(elements[0], nodeYear, filter_key)

    elif len(elements) == 4:
        # year and month specified
        nodeYear = int(elements[1])
        nodeMonth = int(elements[2])
        filter_key = elements[3]
        resultHtml = oha.perform_request_gethpmonth(elements[0], nodeYear, nodeMonth, filter_key)

    elif len(elements) == 5:
        # year, month and day specified - returning the entries themselves
        nodeYear = int(elements[1])
        nodeMonth = int(elements[2])
        nodeDay = int(elements[3])
        filter_key = elements[4]
        daySize = get_holdingpen_day_size(nodeYear, nodeMonth, nodeDay, filter_key)
        urlFilter = urllib.quote(filter_key)
        resultHtml = oha.perform_request_gethpdayfragment(nodeYear, nodeMonth, nodeDay, daySize, 0, urlFilter)
    else:
        # nothing of the above. error
        resultHtml = "Wrong request"
    return json.dumps({"elementId": elementId, "html": resultHtml})

def get_entries_fragment(req, year, month, day, start, limit, filter, pagerPrefix, pageNumber):
    """ Serve the request of getting only part of the result set """
    try:
        getUid(req)
    except Error:
        return "unauthorised access !"
    result = { "pagerPrefix": pagerPrefix,
               "pageNumber": pageNumber,
        }
    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        return oha.perform_request_gethpdayfragment(int(year), int(month), int(day), int(limit), int(start), filter_key)
    else:
        return "unauthorised access !"

def viewholdingpen(req, filter_key = "", ln=CFG_SITE_LANG):
    navtrail_previous_links = oha.getnavtrail() + """&gt; <a class="navtrail" href="%s/admin/oaiharvest/oaiharvestadmin.py">OAIHarvest Admin Interface</a> """ % (CFG_SITE_URL)
    try:
        uid = getUid(req)
    except Error, e:
        return page(title="OAIHarvest Admin Interface - Error",
                    body=e,
                    uid=uid,
                    language=ln,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__,
                    req=req)
    auth = check_user(req, 'cfgoaiharvest')
    if not auth[0]:
        return page(title="Holding Pen",
                    metaheaderadd=oha.view_holdingpen_headers(),
                    body=oha.perform_request_view_holdingpen_tree(filter_key),
                    uid=uid,
                    language=ln,
                    req=req,
                    navtrail=navtrail_previous_links,
                    lastupdated=__lastupdated__)
    else:
        return page_not_authorized(req=req, text=auth[1], navtrail=navtrail_previous_links)
