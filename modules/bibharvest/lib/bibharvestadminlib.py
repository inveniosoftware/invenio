## Administrator interface for BibIndex
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

"""CDS Invenio Bibharvest Administrator Interface."""

__revision__ = "$Id$"

import re
import os, sys, string
import ConfigParser
import time
import random
import urllib
import tempfile
import datetime

from httplib import InvalidURL
from invenio.config import \
     CFG_SITE_LANG, \
     CFG_TMPDIR, \
     CFG_VERSION, \
     CFG_SITE_URL,\
     CFG_ETCDIR, \
     CFG_BINDIR, \
     CFG_LOGDIR, \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG
from invenio.bibrankadminlib import \
     write_outcome,modify_translations,\
     get_def_name,\
     get_i8n_name,\
     get_name,\
     get_rnk_nametypes,\
     get_languages,\
     check_user,\
     is_adminuser,\
     addadminbox,\
     tupletotable,\
     tupletotable_onlyselected,\
     addcheckboxes,\
     createhiddenform
from invenio.dbquery import run_sql
from invenio.webpage import page, pageheaderonly, pagefooteronly, adderrorbox
from invenio.webuser import getUid, get_email
from invenio.bibharvest_dblayer import get_history_entries, \
    HistoryEntry, get_month_logs_size, get_history_entries_for_day, \
    get_day_logs_size, get_entry_history, get_entry_logs_size, \
    get_holdingpen_entries, delete_holdingpen_entry, get_holdingpen_entry
from invenio.search_engine import search_pattern, get_record
import invenio.template
from invenio import oaiharvestlib
from invenio.xmlmarc2textmarclib import recxml2recmarc, create_marc_record
from invenio import bibformat
from invenio.bibrecord import create_record

bibharvest_templates = invenio.template.load('bibharvest')

tmppath = CFG_TMPDIR + '/bibharvestadmin.' + str(os.getpid())
guideurl = "help/admin/bibharvest-admin-guide"

freqs = [[0, "never"], [24, "daily"], [168, "weekly"], [720, "monthly"] ]
posts = [["h", "harvest only (h)"], ["h-c", "harvest and convert (h-c)"], ["h-u", "harvest and upload (h-u)"], ["h-c-u", "harvest, convert and upload (h-c-u)"], ["h-c-f-u", "harvest, convert, filter, upload (h-c-f-u)"]]
dates = [[0, "from beginning"], [1, "from today"]]

def getnavtrail(previous = ''):
    """Get the navtrail"""
    return bibharvest_templates.tmpl_getnavtrail(previous = previous, ln = CFG_SITE_LANG)

def generate_sources_actions_menu(ln, oai_src_id):
    namelinked_args = []
    namelinked_args.append(["oai_src_id", str(oai_src_id)])
    namelinked_args.append(["ln", ln])
    editACTION = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/editsource", title = "edit", args = namelinked_args)
    delACTION = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/delsource", title = "delete", args = namelinked_args)
    testACTION = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/testsource", title = "test", args = namelinked_args)
    historyACTION = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/viewhistory", title = "history", args = namelinked_args)
    harvestACTION = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/harvest", title = "harvest", args = namelinked_args)
    return editACTION + " / " + delACTION + " / " + testACTION + " / " + historyACTION + " / " + harvestACTION

def generate_oai_source_operations(ln, oai_src_id):
    result = bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, title = "OAI source operations", guideurl=guideurl)
    result += generate_sources_actions_menu(ln, oai_src_id)
    return result

def perform_request_index(ln=CFG_SITE_LANG):
    """start area for administering harvesting from OAI repositories"""

    titlebar = bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, title = "Overview of sources", guideurl = guideurl, extraname = "add new OAI source" , extraurl = "admin/bibharvest/bibharvestadmin.py/addsource" )
    titlebar2 = bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, title = "Harvesting status", guideurl = guideurl)
    header = ['name', 'baseURL', 'metadataprefix', 'frequency', 'bibconvertfile', 'postprocess', 'actions']
    header2 = ['name', 'last update']
    oai_src = get_oai_src()
    upd_status = get_update_status()

    sources = []
    for (oai_src_id,oai_src_name,oai_src_baseurl,oai_src_prefix,oai_src_frequency,oai_src_config,oai_src_post,oai_src_bibfilter,oai_src_setspecs) in oai_src:
        namelinked_args = []
        namelinked_args.append(["oai_src_id", str(oai_src_id)])
        namelinked_args.append(["ln", ln])

        namelinked = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/editsource", title = oai_src_name, args = namelinked_args)
        freq = "Not Set"
        if oai_src_frequency==0: freq = "never"
        elif oai_src_frequency==24: freq = "daily"
        elif oai_src_frequency==168: freq = "weekly"
        elif oai_src_frequency==720: freq = "monthly"
        action = generate_sources_actions_menu(ln, oai_src_id)
        sources.append([namelinked,oai_src_baseurl,oai_src_prefix,freq,oai_src_config,oai_src_post, action])

    updates = []
    for (upd_name, upd_status) in upd_status:
        if not upd_status:
            upd_status =  bibharvest_templates.tmpl_print_warning(CFG_SITE_LANG, "Never harvested")
        else: #cut away leading zeros
            upd_status = re.sub(r'\.[0-9]+$', '', str(upd_status))
        updates.append([upd_name, upd_status])

    (schtime, schstatus) = get_next_schedule()
    if schtime:
        schtime = re.sub(r'\.[0-9]+$', '', str(schtime))


    holdingpen_link = bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/viewholdingpen", title = "View Holding Pen", args = [["ln", str(ln)],])
    output = titlebar
    output += bibharvest_templates.tmpl_output_numbersources(CFG_SITE_LANG, get_tot_oai_src())
    output += tupletotable(header=header, tuple=sources)
    output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
    output += titlebar2
    output += bibharvest_templates.tmpl_output_schedule(CFG_SITE_LANG, schtime, str(schstatus))
    output += holdingpen_link
    output += bibharvest_templates.tmpl_print_brs(ln, 2)
    output += tupletotable(header=header2, tuple=updates)

    return output

def perform_request_editsource(oai_src_id=None, oai_src_name='', oai_src_baseurl='', oai_src_prefix='', oai_src_frequency='', oai_src_config='', oai_src_post='',ln=CFG_SITE_LANG, confirm=-1, oai_src_sets=[], oai_src_bibfilter=''):
    """creates html form to edit a OAI source. this method is calling other methods which again is calling this and sending back the output of the method.
    confirm - determines the validation status of the data input into the form"""

    if oai_src_id is None:
        return "No OAI source ID selected."

    output  = ""
    subtitle = bibharvest_templates.tmpl_draw_subtitle(ln = CFG_SITE_LANG, title = "edit source", subtitle = "Edit OAI source", guideurl = guideurl)

    if confirm in [-1, "-1"]:
        oai_src = get_oai_src(oai_src_id)
        oai_src_name = oai_src[0][1]
        oai_src_baseurl = oai_src[0][2]
        oai_src_prefix = oai_src[0][3]
        oai_src_frequency = oai_src[0][4]
        oai_src_config = oai_src[0][5]
        oai_src_post = oai_src[0][6]
        oai_src_sets = oai_src[0][7].split()
        oai_src_bibfilter = oai_src[0][8]

    text = bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "Source name", name = "oai_src_name", value = oai_src_name)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "Base URL", name = "oai_src_baseurl", value = oai_src_baseurl)

    sets = findSets(oai_src_baseurl)
    if sets:
        # Show available sets to users
        sets_specs = [set[0] for set in sets]
        sets_names = [set[1] for set in sets]
        sets_labels = [((set[1] and set[0]+' ('+set[1]+')') or set[0]) \
                       for set in sets]
        sets_states = [ ((set[0] in oai_src_sets and 1) or 0) for set in sets]
        text += bibharvest_templates.tmpl_admin_checkboxes(ln=CFG_SITE_LANG,
                                                           title="Sets",
                                                           name="oai_src_sets",
                                                           values=sets_specs,
                                                           labels=sets_labels,
                                                           states=sets_states)
    else:
        # Let user specify sets in free textbox
        text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG,
                                                          title = "Sets",
                                                          name='oai_src_sets',
                                                          value=' '.join(oai_src_sets))

    text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "Metadata prefix", name = "oai_src_prefix", value = oai_src_prefix)
    text += bibharvest_templates.tmpl_admin_w200_select(ln = CFG_SITE_LANG, title = "Frequency", name = "oai_src_frequency", valuenil = "- select frequency -" , values = freqs, lastval = oai_src_frequency)
    text += bibharvest_templates.tmpl_admin_w200_select(ln = CFG_SITE_LANG, title = "Postprocess", name = "oai_src_post", valuenil = "- select mode -" , values = posts, lastval = oai_src_post)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "BibConvert configuration file (if needed by postprocess)", name = "oai_src_config", value = oai_src_config)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "BibFilter program (if needed by postprocess)", name = "oai_src_bibfilter", value = oai_src_bibfilter)
    text += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)

    output += createhiddenform(action="editsource#1",
                                text=text,
                                button="Modify",
                                oai_src_id=oai_src_id,
                                ln=ln,
                                confirm=1)

    if confirm in [1, "1"] and not oai_src_name:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a name for the source.")
    elif confirm in [1, "1"] and not oai_src_prefix:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a metadata prefix.")
    elif confirm in [1, "1"] and not oai_src_baseurl:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a base url.")
    elif confirm in [1, "1"] and not oai_src_frequency:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please choose a frequency of harvesting")
    elif confirm in [1, "1"] and not oai_src_post:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please choose a postprocess mode")
    elif confirm in [1, "1"] and oai_src_post.startswith("h-c") and (not oai_src_config or validatefile(oai_src_config)!=0):
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "You selected a postprocess mode which involves conversion.")
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a valid name of or a full path to a BibConvert config file or change postprocess mode.")
    elif oai_src_id > -1 and confirm in [1, "1"]:
        if not oai_src_frequency:
            oai_src_frequency = 0
        if not oai_src_config:
            oai_src_config = "NULL"
        if not oai_src_post:
            oai_src_post = "h"
        res = modify_oai_src(oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_config, oai_src_post, oai_src_sets, oai_src_bibfilter)
        output += write_outcome(res)

    lnargs = [["ln", ln]]
    output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
    output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs )

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_addsource(oai_src_name=None, oai_src_baseurl='', oai_src_prefix='', oai_src_frequency='', oai_src_lastrun='', oai_src_config='', oai_src_post='', ln=CFG_SITE_LANG, confirm=-1, oai_src_sets=[], oai_src_bibfilter=''):
    """creates html form to add a new source"""

    if oai_src_name is None:
        return "No OAI source name selected."

    subtitle = bibharvest_templates.tmpl_draw_subtitle(ln=CFG_SITE_LANG,
                                                       title="add source",
                                                       subtitle="Add new OAI source",
                                                       guideurl=guideurl)
    output  = ""

    if confirm <= -1:
        text = bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        text += bibharvest_templates.tmpl_admin_w200_text(ln=CFG_SITE_LANG,
                                                          title="Enter the base url",
                                                          name="oai_src_baseurl",
                                                          value=oai_src_baseurl+'http://')
        output = createhiddenform(action="addsource",
                                  text=text,
                                  ln=ln,
                                  button="Validate",
                                  confirm=0)

    if (confirm not in ["-1", -1] and validate(oai_src_baseurl)[0] == 0) or \
           confirm in ["1", 1]:
        output += bibharvest_templates.tmpl_output_validate_info(CFG_SITE_LANG, 0, str(oai_src_baseurl))
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
        text = bibharvest_templates.tmpl_admin_w200_text(ln=CFG_SITE_LANG,
                                                         title="Source name",
                                                         name="oai_src_name",
                                                         value=oai_src_name)

        metadatas = findMetadataFormats(oai_src_baseurl)
        if metadatas:
            # Show available metadata to user
            prefixes = []
            for value in metadatas:
                prefixes.append([value, str(value)])
            text += bibharvest_templates.tmpl_admin_w200_select(ln=CFG_SITE_LANG,
                                                                title="Metadata prefix",
                                                                name="oai_src_prefix",
                                                                valuenil="- select prefix -" ,
                                                                values=prefixes,
                                                                lastval=oai_src_prefix)
        else:
            # Let user specify prefix in free textbox
            text += bibharvest_templates.tmpl_admin_w200_text(ln=CFG_SITE_LANG,
                                                              title="Metadata prefix",
                                                              name="oai_src_prefix",
                                                              value=oai_src_prefix)

        sets = findSets(oai_src_baseurl)
        if sets:
            # Show available sets to users
            sets_specs = [set[0] for set in sets]
            sets_names = [set[1] for set in sets]
            sets_labels = [((set[1] and set[0]+' ('+set[1]+')') or set[0]) \
                           for set in sets]
            sets_states = [ ((set[0] in oai_src_sets and 1) or 0) \
                            for set in sets]
            text += bibharvest_templates.tmpl_admin_checkboxes(ln=CFG_SITE_LANG,
                                                               title="Sets",
                                                               name="oai_src_sets",
                                                               values=sets_specs,
                                                               labels=sets_labels,
                                                               states=sets_states)
        else:
            # Let user specify sets in free textbox
            text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG,
                                                              title = "Sets",
                                                              name='oai_src_sets',
                                                              value=' '.join(oai_src_sets))

        text += bibharvest_templates.tmpl_admin_w200_select(ln = CFG_SITE_LANG, title = "Frequency", name = "oai_src_frequency", valuenil = "- select frequency -" , values = freqs, lastval = oai_src_frequency)
        text += bibharvest_templates.tmpl_admin_w200_select(ln = CFG_SITE_LANG, title = "Starting date", name = "oai_src_lastrun", valuenil = "- select a date -" , values = dates, lastval = oai_src_lastrun)
        text += bibharvest_templates.tmpl_admin_w200_select(ln = CFG_SITE_LANG, title = "Postprocess", name = "oai_src_post", valuenil = "- select mode -" , values = posts, lastval = oai_src_post)
        text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "BibConvert configuration file (if needed by postprocess)", name = "oai_src_config", value = oai_src_config)
        text += bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = "BibFilter program (if needed by postprocess)", name = "oai_src_bibfilter", value = oai_src_bibfilter)
        text += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)


        output += createhiddenform(action="addsource#1",
                                   text=text,
                                   button="Add OAI Source",
                                   oai_src_baseurl=oai_src_baseurl,
                                   ln=ln,
                                   confirm=1)
    elif confirm in ["0", 0] and validate(oai_src_baseurl)[0] > 0:
        # Could not perform first url validation
        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_output_validate_info(CFG_SITE_LANG, 1, str(oai_src_baseurl))
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/addsource", title = "Try again with another url", args = [])
        output += """ or """
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/addsource", title = "Continue anyway", args = [['oai_src_baseurl', urllib.urlencode({'':oai_src_baseurl})[1:]], ['confirm', '1']])
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        output += """or"""
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs)
    elif confirm not in ["-1", -1] and validate(oai_src_baseurl)[0] > 0:
        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_output_validate_info(CFG_SITE_LANG, 1, str(oai_src_baseurl))
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/addsource", title = "Try again", args = [])
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        output += """or"""
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs)

    elif confirm not in ["-1", -1]:
        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_output_error_info(CFG_SITE_LANG, str(oai_src_baseurl), validate(oai_src_baseurl)[1])
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/addsource", title = "Try again", args = [])
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        output += """or"""
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs)



    if confirm in [1, "1"] and not oai_src_name:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a name for the source.")
    elif confirm in [1, "1"] and not oai_src_prefix:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a metadata prefix.")
    elif confirm in [1, "1"] and not oai_src_frequency:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please choose a frequency of harvesting")
    elif confirm in [1, "1"] and not oai_src_lastrun:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please choose the harvesting starting date")
    elif confirm in [1, "1"] and not oai_src_post:
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please choose a postprocess mode")
    elif confirm in [1, "1"] and oai_src_post.startswith("h-c") and (not oai_src_config or validatefile(oai_src_config)!=0):
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "You selected a postprocess mode which involves conversion.")
        output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Please enter a valid name of or a full path to a BibConvert config file or change postprocess mode.")
    elif oai_src_name and confirm in [1, "1"]:
        if not oai_src_frequency:
            oai_src_frequency = 0
        if not oai_src_lastrun:
            oai_src_lastrun = 1
        if not oai_src_config:
            oai_src_config = "NULL"
        if not oai_src_post:
            oai_src_post = "h"

        res = add_oai_src(oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_lastrun, oai_src_config, oai_src_post, oai_src_sets, oai_src_bibfilter)
        output += write_outcome(res)

        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs )

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_delsource(oai_src_id=None, ln=CFG_SITE_LANG, callback='yes', confirm=0):
    """creates html form to delete a source
    """

    output = ""
    subtitle = ""

    if oai_src_id:
        oai_src = get_oai_src(oai_src_id)
        namesrc = (oai_src[0][1])
        pagetitle = """Delete OAI source: %s""" % namesrc
        subtitle = bibharvest_templates.tmpl_draw_subtitle(ln = CFG_SITE_LANG, \
            title = "delete source", subtitle = pagetitle, guideurl = guideurl)
        output  = ""

        if confirm in ["0", 0]:
            if oai_src:
                question = """Do you want to delete the OAI source '%s' and all its definitions?""" % namesrc
                text = bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, question)
                text += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 3)
                output += createhiddenform(action="delsource#5",
                                       text=text,
                                       button="Confirm",
                                       oai_src_id=oai_src_id,
                                       confirm=1)
            else:
                return bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Source specified does not exist.")
        elif confirm in ["1", 1]:
            res = delete_oai_src(oai_src_id)
            if res[0] == 1:
                output += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "Source removed.")
                output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 1)
                output += write_outcome(res)
            else:
                output += write_outcome(res)

    lnargs = [["ln", ln]]
    output += bibharvest_templates.tmpl_print_brs(CFG_SITE_LANG, 2)
    output += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, \
        funcurl = "admin/bibharvest/bibharvestadmin.py/index", \
        title = "Go back to the OAI sources overview", args = lnargs )

    body = [output]

    return addadminbox(subtitle, body)


def perform_request_testsource(oai_src_id=None, ln=CFG_SITE_LANG, callback='yes', \
    confirm=0, record_id=None):

    if oai_src_id is None:
        return "No OAI source ID selected."
    result = ""
    guideurl = "help/admin/bibharvest-admin-guide"
    result += bibharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, title = \
        "Record ID ( Recognized by the data source )", guideurl=guideurl)
    record_str = ""
    if record_id != None:
        record_str = str(record_id)
    form_text = bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, title = \
        "Record identifier", name = "record_id", value = record_str)
    result += createhiddenform(action="testsource",
                               text=form_text,
                               button="Test",
                               oai_src_id=oai_src_id,
                               ln=ln,
                               confirm=1)
    if record_id != None:
        result += bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, title = \
            "OAI XML downloaded from the source" , guideurl = guideurl)
        result += bibharvest_templates.tmpl_embed_document( \
            "/admin/bibharvest/bibharvestadmin.py/preview_original_xml?oai_src_id=" \
            + urllib.quote(str(oai_src_id)) + "&record_id=" \
            + urllib.quote(str(record_id)))
        result += bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, title = \
            "MARC XML after all the transformations", guideurl = guideurl)
        result += bibharvest_templates.tmpl_embed_document( \
            "/admin/bibharvest/bibharvestadmin.py/preview_harvested_xml?oai_src_id=" \
            + urllib.quote(str(oai_src_id)) + "&record_id=" \
            + urllib.quote(str(record_id)))
    return result

######################################
###  Displaying bibsched task logs ###
######################################
def does_logfile_exist(task_id):
    """
       returns logfile name if exists. None otherwise
    """
    name = CFG_LOGDIR + "/bibsched_task_" + str(task_id) + ".log"
    if os.path.exists(name):
        return name
    else:
        return None

def does_errfile_exist(task_id):
    """
       returns logfile name if exists. None otherwise
    """
    name = CFG_LOGDIR + "/bibsched_task_" + str(task_id) + ".err"
    if os.path.exists(name):
        return name
    else:
        return None

def perform_request_viewtasklogs(ln, confirm, task_id):
    t_id = int(task_id) # preventing malicious user input
    guideurl = "help/admin/bibharvest-admin-guide"

    log_name = does_logfile_exist(t_id)
    err_name = does_errfile_exist(t_id)

    result = ""
    result += bibharvest_templates.tmpl_output_menu(ln, None, guideurl)

    if log_name != None:
        file = open(log_name)
        content = file.read(-1)
        file.close();
        result += bibharvest_templates.tmpl_draw_titlebar(ln, "Log file : " + \
                                                              log_name, guideurl)

        result += bibharvest_templates.tmpl_output_scrollable_frame(\
            bibharvest_templates.tmpl_output_preformatted(content))

    if err_name != None:
        file = open(err_name)
        content = file.read(-1)
        file.close();
        result += bibharvest_templates.tmpl_print_brs(ln, 2)
        result += bibharvest_templates.tmpl_draw_titlebar(ln, "Log file : " + \
                                                              err_name, guideurl)
        result += bibharvest_templates.tmpl_output_scrollable_frame(\
            bibharvest_templates.tmpl_output_preformatted(content))

    return result

### Probably should be moved to some other data-connection file


def build_history_row(item, ln, show_selection, show_oai_source, show_record_ids, identifier = ""):
    def get_cssclass(cssclass):
        if cssclass == "oddtablecolumn":
            return "pairtablecolumn"
        else:
            return "oddtablecolumn"

    cssclass = get_cssclass("pairtablecolumn")
    result = bibharvest_templates.tmpl_table_row_begin()
    result += bibharvest_templates.tmpl_table_output_cell(\
        bibharvest_templates.format_date(item.date_harvested) + " " + \
        bibharvest_templates.format_time(item.date_harvested), cssclass = cssclass)
    cssclass = get_cssclass(cssclass)
    result += bibharvest_templates.tmpl_table_output_cell(\
        bibharvest_templates.format_date(item.date_inserted) + " " + \
        bibharvest_templates.format_time(item.date_inserted), cssclass = cssclass)

    if show_record_ids:
        record_history_link = bibharvest_templates.tmpl_link_with_args(ln, \
            "/admin/bibharvest/bibharvestadmin.py/viewentryhistory", \
            str(item.oai_id), [["ln", ln], ["oai_id", str(item.oai_id)], \
            ["start", "0"]])
        cssclass = get_cssclass(cssclass)
        result += bibharvest_templates.tmpl_table_output_cell(record_history_link, \
            cssclass = cssclass)

        record_details_link = bibharvest_templates.tmpl_link_with_args(ln, \
            "/record/" + str(item.record_id), str(item.record_id), [["ln",str(ln)],])
        cssclass = get_cssclass(cssclass)
        result += bibharvest_templates.tmpl_table_output_cell(record_details_link, \
            cssclass = cssclass)

    cssclass = get_cssclass(cssclass)
    result += bibharvest_templates.tmpl_table_output_cell(item.inserted_to_db, \
        cssclass = cssclass)

    cssclass = get_cssclass(cssclass)
    task_id = str(item.bibupload_task_id)
    if does_errfile_exist(item.bibupload_task_id) or does_logfile_exist(item.bibupload_task_id):
        task_id = bibharvest_templates.tmpl_link_with_args(ln, \
            "/admin/bibharvest/bibharvestadmin.py/viewtasklogs", str(item.bibupload_task_id),\
            [["ln",str(ln)],["task_id", str(item.bibupload_task_id)]])

    result += bibharvest_templates.tmpl_table_output_cell(task_id, cssclass = cssclass)

    if show_selection:
        chkbox = bibharvest_templates.tmpl_output_checkbox(item.oai_id, identifier, "1")
        cssclass = get_cssclass(cssclass)
        result += bibharvest_templates.tmpl_table_output_cell(chkbox, \
            cssclass = cssclass)

    if show_oai_source:
        cssclass = get_cssclass(cssclass)
        result += bibharvest_templates.tmpl_table_output_cell(str(item.oai_src_id), \
            cssclass = cssclass)

    result += bibharvest_templates.tmpl_table_row_end()
    return result

def build_history_table_header(show_selection = True, show_oai_source = False, \
    show_record_ids = True):

    headers = ["Harvesting Date", "Insert date"]
    if show_record_ids:
        headers += ["Record ID ( OAI )", "Rec. ID <br/>(Invenio)"]
    headers += ["DB", "task <br/> number"]
    if show_selection:
        headers.append("Reharvest")
    if show_oai_source:
        headers.append("Harvested from <br/> source no")
    return headers

def build_month_history_table(oai_src_id, date, ln):
    """ Function formats the historical data
     @param oai_src_id: identifier of the harvesting source
     @param date: date designing the month of interest
     @return: String containing the history table
    """
    day_limit = 10
    orig_data = get_history_entries(oai_src_id, date)
    stats = get_month_logs_size(oai_src_id, date)
    headers = build_history_table_header()
    result = bibharvest_templates.tmpl_table_begin(headers)
    identifiers = {}
    for day in stats:
        result += bibharvest_templates.tmpl_table_row_begin()
        d_date = datetime.datetime(date.year, date.month, day)
        result += bibharvest_templates.tmpl_history_table_output_day_cell(d_date, \
            stats[day], oai_src_id, ln, stats[day] > day_limit)
        btn = bibharvest_templates.tmpl_output_select_day_button(day)
        result += bibharvest_templates.tmpl_table_output_cell(btn)
        result += bibharvest_templates.tmpl_table_row_end()
        day_data = get_history_entries_for_day(oai_src_id, d_date, limit = day_limit)
        for item in day_data:
            identifier = bibharvest_templates.format_date(item.date_harvested) + \
                bibharvest_templates.format_time(item.date_harvested) + "_" + item.oai_id
            result += build_history_row(item, ln, show_selection = True, show_oai_source = \
                False, show_record_ids = True, identifier = identifier)
            if not identifiers.has_key(item.date_harvested.day):
                identifiers[item.date_harvested.day] = []
            identifiers[item.date_harvested.day].append(identifier)
        if stats[day] > day_limit:
            result += bibharvest_templates.tmpl_history_table_output_day_details_cell(\
                ln, d_date, oai_src_id)
    result += bibharvest_templates.tmpl_table_end()
    result += bibharvest_templates.tmpl_output_identifiers(identifiers)
    return result

def build_history_table(data, ln = CFG_SITE_LANG, show_selection = True, \
    show_oai_source = False, show_record_ids = True):

    headers = build_history_table_header(show_selection = show_selection, \
        show_oai_source = show_oai_source, show_record_ids = show_record_ids)
    result = bibharvest_templates.tmpl_table_begin(headers)

    identifiers = {}
    for item in data:
        identifier = bibharvest_templates.format_date(item.date_harvested) + \
            bibharvest_templates.format_time(item.date_harvested) + "_" + item.oai_id
        result += build_history_row(item, ln, show_selection = show_selection,\
            show_oai_source = show_oai_source, show_record_ids = show_record_ids, \
            identifier = identifier)
        if show_selection:
            if not identifiers.has_key(item.date_harvested.day):
                identifiers[item.date_harvested.day] = []
            identifiers[item.date_harvested.day].append(identifier)
    result += bibharvest_templates.tmpl_table_end()
    if show_selection:
        result += bibharvest_templates.tmpl_output_identifiers(identifiers)
    return result

def perform_request_viewhistory(oai_src_id = None, ln = CFG_SITE_LANG, callback = \
    'yes', confirm = 0, month = None, year = None):

    """ Creates html to view the harvesting history """
    date = datetime.datetime.now()
    if year != None and month != None:
        year = int(year)
        month = int(month)
        date = datetime.datetime(year, month, 1)
    result = ""
    result += bibharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += bibharvest_templates.tmpl_output_history_javascript_functions()
    result += bibharvest_templates.tmpl_output_month_selection_bar(oai_src_id, ln, \
        current_month = month, current_year = year)
    inner_text = build_month_history_table(oai_src_id, date, ln)
    inner_text += bibharvest_templates.tmpl_print_brs(ln, 1)
    inner_text = bibharvest_templates.tmpl_output_scrollable_frame(inner_text)
    inner_text += bibharvest_templates.tmpl_output_selection_bar()
    result +=  createhiddenform(action="/admin/bibharvest/bibharvestadmin.py/reharvest", \
        text = inner_text, button = "Reharvest selected records", oai_src_id = \
        oai_src_id, ln = ln)
    return result


def perform_request_viewhistoryday(oai_src_id = None, ln = CFG_SITE_LANG, callback = 'yes',\
    confirm = 0, month = None, year = None, day = None, start = 0):

    page_length = 50
    result = ""
    result += bibharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    considered_date = datetime.datetime.now()
    if year != None and month != None and day != None:
        considered_date = datetime.datetime(year, month, day)
    number_of_records = get_day_logs_size(oai_src_id, considered_date)
    return_to_month_link =  bibharvest_templates.tmpl_link_with_args(ln, \
        "/admin/bibharvest/bibharvestadmin.py/viewhistory", \
        "&lt;&lt; Return to the month view", [["ln", ln], ["oai_src_id",\
        str(oai_src_id)], ["year", str(considered_date.year)], \
        ["month", str(considered_date.month)]])
    next_page_link = ""
    if number_of_records > start + page_length:
        next_page_link = bibharvest_templates.tmpl_link_with_args(ln, \
          "/admin/bibharvest/bibharvestadmin.py/viewhistoryday", \
          "Next page &gt;&gt;", \
          [["ln", ln], ["oai_src_id", str(oai_src_id)], ["year", str(considered_date.year)],\
          ["month", str(considered_date.month)], ["day",  str(considered_date.day)], \
          ["start", str(start + page_length)]])
    prev_page_link = ""
    if start > 0:
        new_start = start - page_length
        if new_start < 0:
            new_start = 0
        prev_page_link = bibharvest_templates.tmpl_link_with_args(ln, \
          "/admin/bibharvest/bibharvestadmin.py/viewhistoryday", \
          "&lt;&lt; Previous page", \
          [["ln", ln], ["oai_src_id", str(oai_src_id)], ["year", str(considered_date.year)],\
          ["month", str(considered_date.month)], ["day",  str(considered_date.day)], \
          ["start", str(new_start)]])
    last_shown = start + page_length
    if last_shown > number_of_records:
        last_shown = number_of_records
    current_day_records = get_history_entries_for_day(oai_src_id, considered_date, limit =\
        page_length, start = start)
    current_range = "&nbsp;&nbsp;&nbsp;&nbsp;Viewing entries : " + str(start + 1) + "-" + \
        str(last_shown) + "&nbsp;&nbsp;&nbsp;&nbsp;"
    # Building the interface
    result += bibharvest_templates.tmpl_draw_titlebar(ln, "Viewing history of " + str(year)\
        + "-" + str(month) + "-" + str(day) , guideurl)
    result += prev_page_link + current_range + next_page_link + \
        bibharvest_templates.tmpl_print_brs(ln, 1)
    result += bibharvest_templates.tmpl_output_history_javascript_functions()
    inner_text = bibharvest_templates.tmpl_output_scrollable_frame(build_history_table(\
        current_day_records, ln=ln))
    inner_text += bibharvest_templates.tmpl_output_selection_bar()
    result +=  createhiddenform(action="/admin/bibharvest/bibharvestadmin.py/reharvest", \
        text = inner_text, button = "Reharvest selected records", oai_src_id = oai_src_id, ln = ln)
    result += return_to_month_link + bibharvest_templates.tmpl_print_brs(ln, 1)
    return result


def perform_request_viewentryhistory(oai_id, ln, confirm, start):
    page_length = 50
    result = ""
    result += bibharvest_templates.tmpl_output_menu(ln, None, guideurl)
    considered_date = datetime.datetime.now()

    number_of_records = get_entry_logs_size(oai_id)

    next_page_link = ""
    if number_of_records > start + page_length:
        next_page_link = bibharvest_templates.tmpl_link_with_args(ln, \
          "/admin/bibharvest/bibharvestadmin.py/viewhistoryday", \
          "Next page &gt;&gt;", \
          [["ln", ln], ["oai_id", str(oai_id)], \
          ["start", str(start + page_length)]])
    prev_page_link = ""
    if start > 0:
        new_start = start - page_length
        if new_start < 0:
            new_start = 0
        prev_page_link = bibharvest_templates.tmpl_link_with_args(ln, \
          "/admin/bibharvest/bibharvestadmin.py/viewhistoryday", \
          "&lt;&lt; Previous page", \
          [["ln", ln], ["oai_id", str(oai_id)], \
          ["start", str(new_start)]])
    last_shown = start + page_length
    if last_shown > number_of_records:
        last_shown = number_of_records
    current_entry_records = get_entry_history(oai_id, limit = page_length, start = start)
    current_range = "&nbsp;&nbsp;&nbsp;&nbsp;Viewing entries : " + str(start + 1) \
        + "-" + str(last_shown) + "&nbsp;&nbsp;&nbsp;&nbsp;"
    # Building the interface
    result += bibharvest_templates.tmpl_draw_titlebar(ln, "Viewing history of " + \
        str(oai_id) , guideurl)
    result += prev_page_link + current_range + next_page_link + \
        bibharvest_templates.tmpl_print_brs(ln, 1)
    result += bibharvest_templates.tmpl_output_history_javascript_functions()
    inner_text = bibharvest_templates.tmpl_output_scrollable_frame(\
        build_history_table(current_entry_records, ln, show_selection = False, \
        show_oai_source = True, show_record_ids = False))
    result += inner_text
    result += bibharvest_templates.tmpl_print_brs(ln, 1)
    return result

############################################################
###  The functions allowing to preview the harvested XML ###
############################################################

def harvest_record(record_id , oai_src_baseurl, oai_src_prefix):
    """
       Harvests given record and returns it's string as a result
    """
    command = CFG_BINDIR + "/bibharvest -vGetRecord -i" + record_id \
              + " -p" + oai_src_prefix + " " + oai_src_baseurl
    program_output = os.popen(command)
    result = program_output.read(-1)
    program_output.close()
    return result

def convert_record(oai_src_config, record_to_convert):
    command = CFG_BINDIR + "/bibconvert -c " + oai_src_config
    (s_in,s_out,s_err) = os.popen3(command)
    s_in.write(record_to_convert)
    s_in.close()
    s_err.readlines()
    result = s_out.read(-1)
    s_err.close()
    s_out.close()
    return result

def format_record(oai_src_bibfilter,  record_to_convert, treat_new = False):
    """
    Formats the record using given formatting program.
    Returns name of the file containing result,
    program output, program error output
    """
    (file_descriptor, file_name) = tempfile.mkstemp()
    f = os.fdopen(file_descriptor, "w")
    f.write(record_to_convert)
    f.close()
    command = oai_src_bibfilter
    if treat_new:
        command += " -n"
    command += " " + file_name
    (program_input, program_output, program_err) = os.popen3(command)
    program_input.close()
    out = program_output.read(-1)
    err = program_err.read(-1)
    program_output.close()
    program_err.close()

    if os.path.exists(file_name + ".insert.xml"):
        return (file_name + ".insert.xml", out, err)
    else:
        return (None, out, err)

def harvest_postprocress_record(oai_src_id, record_id, treat_new = False):
    oai_src = get_oai_src(oai_src_id)
    oai_src_baseurl = oai_src[0][2]
    oai_src_prefix = oai_src[0][3]
    oai_src_config = oai_src[0][5]
    oai_src_post = oai_src[0][6]
    oai_src_sets = oai_src[0][7].split()
    oai_src_bibfilter = oai_src[0][8]
    result = harvest_record(record_id, oai_src_baseurl, oai_src_prefix)
    if result == None:
        return (False, "Error during harvesting")
    if oai_src_post.find("c") != -1:
        result = convert_record(oai_src_config, result)
        if result == None:
            return (False, "Error during converting")
    if oai_src_post.find("f") != -1:
        fres = format_record(oai_src_bibfilter, result, treat_new = treat_new)
        fname = fres[0]
        if fname != None:
            f = open(fname, "r")
            result = f.read(-1)
            f.close()
            os.remove(fname)
        else:
            return (False, "Error during formatting: " + fres[1] + "\n\n" + fres[2])
    return (True, result)

def upload_record(record = None, uploader_paremeters = ["-r", "-i"], oai_source_id = None):
    if record == None:
        return
    (file_descriptor, file_name) = tempfile.mkstemp()
    f = os.fdopen(file_descriptor, "w")
    f.write(record)
    f.close()
    oaiharvestlib.call_bibupload(file_name, uploader_paremeters, oai_src_id = oai_source_id)
    #command = CFG_BINDIR + "/bibupload " + uploader_paremeters + " "
    #command += file_name

    #out = os.popen(command)
    #output_data = out.read(-1)
    #out.close()

def perform_request_preview_original_xml(oai_src_id = None, record_id = None):
    oai_src = get_oai_src(oai_src_id)
    oai_src_baseurl = oai_src[0][2]
    oai_src_prefix = oai_src[0][3]
    oai_src_config = oai_src[0][5]
    oai_src_post = oai_src[0][6]
    oai_src_sets = oai_src[0][7].split()
    oai_src_bibfilter = oai_src[0][8]
    record = harvest_record(record_id, oai_src_baseurl, oai_src_prefix)
    return record

def perform_request_preview_harvested_xml(oai_src_id = None, record_id = None):
    return harvest_postprocress_record(oai_src_id, record_id, treat_new = True)

############################################################
### Reharvesting of already existing records             ###
############################################################

def perform_request_reharvest_records(oai_src_id = None, ln = CFG_SITE_LANG, confirm=0, record_ids = None):
    for record_id in record_ids:
        # 1) Run full harvesing process as in the preview scenarios
        transformed = harvest_postprocress_record(oai_src_id, record_id, treat_new = True)[1]
        upload_record(transformed, ["-i", "-r"], oai_src_id)
    result = bibharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += bibharvest_templates.tmpl_print_info(ln, "Submitted for inserion into the database")
    return result

def perform_request_harvest_record(oai_src_id = None, ln = CFG_SITE_LANG, confirm=0, record_id = None):
    """ Request for harvesting a new record """
    if oai_src_id is None:
        return "No OAI source ID selected."
    result = ""
    guideurl = "help/admin/bibharvest-admin-guide"
    result += bibharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG, \
        title = "Record ID ( Recognized by the data source )", guideurl=guideurl)
    record_str = ""
    if record_id != None:
        record_str = str(record_id)
    form_text = bibharvest_templates.tmpl_admin_w200_text(ln = CFG_SITE_LANG, \
        title = "Record identifier", name = "record_id", value = record_str)
    result += createhiddenform(action="harvest",
                               text=form_text,
                               button="Harvest",
                               oai_src_id=oai_src_id,
                               ln=ln,
                               confirm=1)
    if record_id != None:
        # there was a harvest-request
        transformed = harvest_postprocress_record(oai_src_id, record_id)[1]
        upload_record(transformed, ["-i"], oai_src_id)
        result += bibharvest_templates.tmpl_print_info(ln, "Submitted for inserion into the database")
    return result


############################
### Holding pen support  ###
############################
def build_holdingpen_table(data, ln):
    result = ""
    headers = ["OAI Record ID", "Insertion Date", "", ""]
    result += bibharvest_templates.tmpl_table_begin(headers)
    for record in data:
        oai_id = record[0]
        date_inserted = record[1]
        result += bibharvest_templates.tmpl_table_row_begin()
        result += bibharvest_templates.tmpl_table_output_cell(str(oai_id), cssclass = "oddtablecolumn")
        result += bibharvest_templates.tmpl_table_output_cell(str(date_inserted), cssclass = "pairtablecolumn")
        details_link = bibharvest_templates.tmpl_link_with_args(ln, \
                            "/admin/bibharvest/bibharvestadmin.py/viewhprecord", \
                            "Compare with original", [["ln", ln], \
                            ["oai_id", str(oai_id)], ["date_inserted", str(date_inserted)]])
        result += bibharvest_templates.tmpl_table_output_cell(details_link, cssclass = "oddtablecolumn")
        delete_hp_link = bibharvest_templates.tmpl_link_with_args(ln, \
                            "/admin/bibharvest/bibharvestadmin.py/delhprecord", \
                            "Delete from holding pen", [["ln", ln], \
                            ["oai_id", str(oai_id)], ["date_inserted", str(date_inserted)]])
        result += bibharvest_templates.tmpl_table_output_cell(delete_hp_link, cssclass = "pairtablecolumn")
        result += bibharvest_templates.tmpl_table_row_end()
    result += bibharvest_templates.tmpl_table_end()
    return result

def perform_request_viewholdingpen(ln = CFG_SITE_LANG, confirm=0, start = 0, limit = -1):
    data = get_holdingpen_entries(start, limit)
    result = ""
    result += build_holdingpen_table(data, ln)
    return result

def perform_request_viewhprecord(oai_id, date_inserted, ln = CFG_SITE_LANG, confirm=0):
    result = ""
    record_id = int(search_pattern( p = oai_id, f = CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
                                        m = 'e' ).tolist()[0])
    db_rec = get_record(record_id)
    db_MARC = create_marc_record(db_rec[0], record_id, {"text-marc": 1, "aleph-marc": 0})
    db_content = bibharvest_templates.tmpl_output_preformatted(db_MARC.encode("utf-8"))
    db_label = "Database version of record" + bibharvest_templates.tmpl_print_brs(ln, 1)
    hp_rec = create_record(get_holdingpen_entry(oai_id, date_inserted))
    hp_MARC = create_marc_record(hp_rec[0], record_id, {"text-marc": 1, "aleph-marc": 0})
    hp_content = bibharvest_templates.tmpl_output_preformatted(hp_MARC.encode("utf-8"))
    hp_label = bibharvest_templates.tmpl_print_brs(ln, 2) + "Holdingpen version of record"\
        + bibharvest_templates.tmpl_print_brs(ln, 1)
    submit_link = bibharvest_templates.tmpl_link_with_args(ln,
                      "admin/bibharvest/bibharvestadmin.py/accepthprecord",
                      "Accept Holding Pen version",
                      [["ln", str(ln)], ["oai_id", str(oai_id)], ["date_inserted",
                      str(date_inserted)]])
    delete_link = delete_hp_link = bibharvest_templates.tmpl_link_with_args(ln,
                     "admin/bibharvest/bibharvestadmin.py/delhprecord",
                     "Delete from holding pen", [["ln", ln],
                     ["oai_id", str(oai_id)], ["date_inserted", str(date_inserted)]])
    result = ""
    result += db_label
    result += db_content
    result += hp_label
    result += hp_content
    result += delete_link + " "
    result += submit_link
    return result

def perform_request_delhprecord(oai_id, date_inserted, ln = CFG_SITE_LANG, confirm = 0):
    delete_holdingpen_entry(oai_id, date_inserted)
    return "Record deleted from the holding pen"

def perform_request_accepthprecord(oai_id, date_inserted, ln = CFG_SITE_LANG, confirm = 0):
    record_xml = get_holdingpen_entry(oai_id, date_inserted)
    delete_holdingpen_entry(oai_id, date_inserted)
    upload_record(record_xml)

    return perform_request_viewholdingpen(ln = ln, confirm = confirm, start = 0, limit = -1)
##################################################################
### Here the functions to retrieve, modify, delete and add sources
##################################################################

def get_oai_src(oai_src_id=''):
    """Returns a row parameters for a given id"""
    sql = "SELECT id,name,baseurl,metadataprefix,frequency,bibconvertcfgfile,postprocess,setspecs,bibfilterprogram FROM oaiHARVEST"
    try:
        if oai_src_id:
            sql += " WHERE id=%s" % oai_src_id
        sql += " ORDER BY id asc"
        res = run_sql(sql)
        return res
    except StandardError, e:
        return ""

def modify_oai_src(oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_config, oai_src_post, oai_src_sets=[], oai_src_bibfilter=''):
    """Modifies a row's parameters"""
    try:
        res = run_sql("UPDATE oaiHARVEST SET name=%s WHERE id=%s", (oai_src_name, oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET baseurl=%s WHERE id=%s", (oai_src_baseurl, oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET metadataprefix=%s WHERE id=%s", (oai_src_prefix, oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET frequency=%s WHERE id=%s", (oai_src_frequency, oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET bibconvertcfgfile=%s WHERE id=%s", (oai_src_config, oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET postprocess=%s WHERE id=%s", (oai_src_post, oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET setspecs=%s WHERE id=%s", (' '.join(oai_src_sets), oai_src_id))
        res = run_sql("UPDATE oaiHARVEST SET bibfilterprogram=%s WHERE id=%s", (oai_src_bibfilter, oai_src_id))
        return (1, "")
    except StandardError, e:
        return (0, e)

def add_oai_src(oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_lastrun, oai_src_config, oai_src_post, oai_src_sets=[], oai_src_bibfilter=''):
    """Adds a new row to the database with the given parameters"""
    try:
        if oai_src_lastrun in [0, "0"]: lastrun_mode = 'NULL'
        else:
            lastrun_mode = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # lastrun_mode = "'"+lastrun_mode+"'"
        run_sql("INSERT INTO oaiHARVEST (id, baseurl, metadataprefix, arguments, comment,  bibconvertcfgfile,  name,  lastrun,  frequency,  postprocess,  bibfilterprogram,  setspecs) VALUES (0, %s, %s, NULL, NULL, %s, %s, %s, %s, %s, %s, %s)", \
                (oai_src_baseurl, oai_src_prefix, oai_src_config, oai_src_name, lastrun_mode, oai_src_frequency, oai_src_post, oai_src_bibfilter, " ".join(oai_src_sets)))
        return (1, "")
    except StandardError, e:
        return (0, e)

def delete_oai_src(oai_src_id):
    """Deletes a row from the database according to its id"""
    try:
        res = run_sql("DELETE FROM oaiHARVEST WHERE id=%s" % oai_src_id)
        return (1, "")
    except StandardError, e:
        return (0, e)

def get_tot_oai_src():
    """Returns number of rows in the database"""
    try:
        sql = "SELECT COUNT(*) FROM oaiHARVEST"
        res = run_sql(sql)
        return res[0][0]
    except StandardError, e:
        return ""

def get_update_status():
    """Returns a table showing a list of all rows and their LastUpdate status"""
    try:
        sql = "SELECT name,lastrun FROM oaiHARVEST ORDER BY lastrun desc"
        res = run_sql(sql)
        return res
    except StandardError, e:
        return ""

def get_next_schedule():
    """Returns the next scheduled oaiharvestrun tasks"""
    try:
        sql = "SELECT runtime,status FROM schTASK WHERE proc='oaiharvest' AND runtime > now() ORDER by runtime LIMIT 1"
        res = run_sql(sql)
        if len(res)>0:
            return res[0]
        else:
            return ("", "")
    except StandardError, e:
        return ("","")


def validate(oai_src_baseurl):
    """This function validates a baseURL by opening its URL and 'greping' for the <OAI-PMH> and <Identify> tags:

    Codes:
     0 = okay
     1 = baseURL not valid
     2 = baseURL not found/not existing
     3 = tmp directoy is not writable
     4 = Unknown error

     Returns tuple (code, message)
     """
    try:
        url = oai_src_baseurl + "?verb=Identify"
        urllib.urlretrieve(url, tmppath)

        # First check if we have xml oai-pmh output
        grepOUT1 = os.popen('grep -iwc "<OAI-PMH" '+tmppath).read()
        if int(grepOUT1) == 0:
            # No.. we have an http error
            return (4, os.popen('cat '+tmppath).read())

        grepOUT2 = os.popen('grep -iwc "<identify>" '+tmppath).read()
        if int(grepOUT2) > 0:
            #print "Valid!"
            return (0, '')
        else:
            #print "Not valid!"
            return (1, '')
    except IOError, (errno, strerror):
        # Quick error handling for frequent error codes.
        if errno == 13:
            return (3, "Please check permission on %s and retry" % CFG_TMPDIR)
        elif errno == 2 or errno == 'socket error':
            return (2, "Could not connect with URL %s. Check URL or retry when server is available." % url)
        return (4, strerror)
    except StandardError, e:
        return (4, "An unknown error has occured")
    except InvalidURL, e:
        return (2, "Could not connect with URL %s. Check URL or retry when server is available." % url)

def validatefile(oai_src_config):
    """This function checks whether the given path to text file exists or not
     0 = okay
     1 = file non existing
     """

    CFG_BIBCONVERT_XSL_PATH = "%s%sbibconvert%sconfig" % (CFG_ETCDIR,
                                                          os.sep,
                                                          os.sep)
    path_to_config = (CFG_BIBCONVERT_XSL_PATH + os.sep +
                      oai_src_config)
    if os.path.exists(path_to_config):
        # Try to read in config directory
        try:
            ftmp = open(path_to_config, 'r')
            cfgstr= ftmp.read()
            ftmp.close()
            if cfgstr!="":
                #print "Valid!"
                return 0
        except StandardError, e:
            pass

    # Try to read as complete path
    try:
        ftmp = open(oai_src_config, 'r')
        cfgstr= ftmp.read()
        ftmp.close()
        if cfgstr!="":
            #print "Valid!"
            return 0
        else:
            #print "Not valid!"
            return 1
    except StandardError, e:
        return 1

    return 1

def findMetadataFormats(oai_src_baseurl):
    """This function finds the Metadata formats offered by a OAI repository by analysing the output of verb=ListMetadataFormats"""
    formats = []
    url = oai_src_baseurl + "?verb=ListMetadataFormats"
    try:
        urllib.urlretrieve(url, tmppath)
    except IOError:
        return formats
    ftmp = open(tmppath, 'r')
    xmlstr= ftmp.read()
    ftmp.close()
    chunks = xmlstr.split('<metadataPrefix>')
    count = 0 # first chunk is invalid
    for chunk in chunks:
        if count!=0:
            formats.append(chunk.split('</metadataPrefix>')[0])
        count = count + 1
    return formats

def findSets(oai_src_baseurl):
    """This function finds the sets offered by a OAI repository
    by analysing the output of verb=ListSets.
    Returns list of tuples(SetSpec, SetName)"""
    url = oai_src_baseurl + "?verb=ListSets"
    sets = {}
    try:
        urllib.urlretrieve(url, tmppath)
    except IOError:
        return sets
    ftmp = open(tmppath, 'r')
    xmlstr= ftmp.read()
    ftmp.close()
    chunks = xmlstr.split('<set>')
    count = 0 # first chunk is invalid
    for chunk in chunks:
        if count!=0:
            chunks_set = chunk.split('<setSpec>')[1].split("</setSpec>")
            set_spec = chunks_set[0]
            #chunks_set[1].split('<setName>')
            check_set_2 = chunks_set[1].split("<setName>")
            set_name = None
            if len(check_set_2) > 1:
                set_name = check_set_2[1].split("</setName>")[0]
            sets[set_spec] = [set_spec, set_name]
        count = count + 1
    return sets.values()
