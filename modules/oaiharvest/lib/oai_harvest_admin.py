## Administrator interface for BibIndex
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

import re
import os
import cgi
import time
import urllib
import tempfile
import datetime

from httplib import InvalidURL
from invenio.config import \
     CFG_SITE_LANG, \
     CFG_TMPDIR, \
     CFG_SITE_URL, \
     CFG_ETCDIR, \
     CFG_BINDIR, \
     CFG_LOGDIR, \
     CFG_SITE_RECORD
from invenio.oai_harvest_config import CFG_OAI_POSSIBLE_POSTMODES
from invenio.bibrankadminlib import \
     write_outcome, \
     addadminbox, \
     tupletotable, \
     createhiddenform
from invenio.legacy.dbquery import run_sql
from invenio.oai_harvest_dblayer import get_holdingpen_day_size

from invenio.oai_harvest_dblayer import get_month_logs_size, \
     get_history_entries_for_day, get_day_logs_size, get_entry_history, \
     get_entry_logs_size, get_holdingpen_entries, delete_holdingpen_entry, \
     get_holdingpen_years, get_holdingpen_month, get_holdingpen_year, \
     get_holdingpen_day_fragment, get_holdingpen_entry_details
from invenio.search_engine import get_record

import invenio.template
from invenio import oai_harvest_daemon
from invenio.legacy.bibrecord.scripts.xmlmarc2textmarc import create_marc_record
from invenio.legacy.bibrecord import create_record
from invenio.utils.url import create_html_link

webstyle_templates = invenio.template.load('webstyle')
oaiharvest_templates = invenio.template.load('oai_harvest')
from invenio.base.i18n import gettext_set_language

tmppath = CFG_TMPDIR + '/oaiharvestadmin.' + str(os.getpid())
guideurl = "help/admin/oaiharvest-admin-guide"
oai_harvest_admin_url = CFG_SITE_URL + \
                        "/admin/oaiharvest/oaiharvestadmin.py"

freqs = [[0, "never"],
         [24, "daily"],
         [168, "weekly"],
         [720, "monthly"] ]

dates = [[0, "from beginning"],
         [1, "from today"]]

def getnavtrail(previous='', ln=CFG_SITE_LANG):
    """Get the navtrail"""
    return oaiharvest_templates.tmpl_getnavtrail(previous=previous,
                                                 ln=ln)

def generate_sources_actions_menu(oai_src_id, ln=CFG_SITE_LANG):
    """
    Create the links/actions to administrate the given OAI source.
    """
    _ = gettext_set_language(ln)
    default_link_argd = {'ln': ln,
                         'oai_src_id': str(oai_src_id)}

    edit_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                 "/editsource",
                                 urlargd=default_link_argd,
                                 link_label=_("edit"))
    del_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                "/delsource",
                                urlargd=default_link_argd,
                                link_label=_("delete"))
    test_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                 "/testsource",
                                 urlargd=default_link_argd,
                                 link_label=_("test"))
    hist_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                 "/viewhistory",
                                 urlargd=default_link_argd,
                                 link_label=_("history"))
    harvest_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                    "/harvest",
                                    urlargd=default_link_argd,
                                    link_label=_("harvest"))

    return edit_link + " / " + del_link + " / " + test_link + \
           " / " + hist_link + " / " + harvest_link

def perform_request_index(ln=CFG_SITE_LANG):
    """start area for administering harvesting from OAI repositories"""
    _ = gettext_set_language(ln)

    titlebar = oaiharvest_templates.tmpl_draw_titlebar(ln=ln, title=_("Overview of sources"), guideurl=guideurl, extraname="add new OAI source" , extraurl="admin/oaiharvest/oaiharvestadmin.py/addsource?ln=" + ln)
    titlebar2 = oaiharvest_templates.tmpl_draw_titlebar(ln=ln, title=_("Harvesting status"), guideurl=guideurl)
    header = ['name', 'baseURL', 'metadataprefix', 'frequency',
              'bibconvertfile', 'postprocess', 'actions']
    header2 = ['name', 'last update']
    oai_src = get_oai_src()
    upd_status = get_update_status()

    sources = []
    for (oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, \
         oai_src_frequency, oai_src_config, oai_src_post, \
         dummy_oai_src_bibfilter, dummy_oai_src_setspecs) in oai_src:

        default_link_argd = {'ln': ln,
                             'oai_src_id': str(oai_src_id)}
        namelinked = create_html_link(urlbase=oai_harvest_admin_url + \
                                      "/editsource",
                                      urlargd=default_link_argd,
                                      link_label=cgi.escape(oai_src_name))
        freq = _("Not Set")
        if oai_src_frequency == 0: freq = _("never")
        elif oai_src_frequency == 24: freq = _("daily")
        elif oai_src_frequency == 168: freq = _("weekly")
        elif oai_src_frequency == 720: freq = _("monthly")
        action = generate_sources_actions_menu(oai_src_id, ln)
        sources.append([namelinked, oai_src_baseurl, oai_src_prefix,
                        freq, oai_src_config, oai_src_post, action])

    updates = []
    for (upd_name, upd_status) in upd_status:
        if not upd_status:
            upd_status = webstyle_templates.tmpl_write_warning(_("Never harvested"))
        else: #cut away leading zeros
            upd_status = re.sub(r'\.[0-9]+$', '', str(upd_status))
        updates.append([upd_name, upd_status])

    (schtime, schstatus) = get_next_schedule()
    if schtime:
        schtime = re.sub(r'\.[0-9]+$', '', str(schtime))

    holdingpen_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                       "/viewholdingpen",
                                       urlargd={'ln': ln},
                                       link_label=_("View Holding Pen"))
    output = titlebar
    output += oaiharvest_templates.tmpl_output_numbersources(ln, get_tot_oai_src())
    output += tupletotable(header=header, tuple=sources)
    output += oaiharvest_templates.tmpl_print_brs(ln, 2)
    output += titlebar2
    output += oaiharvest_templates.tmpl_output_schedule(ln, schtime, str(schstatus))
    output += holdingpen_link
    output += oaiharvest_templates.tmpl_print_brs(ln, 2)
    output += tupletotable(header=header2, tuple=updates)

    return output

def perform_request_editsource(oai_src_id=None, oai_src_name='',
                               oai_src_baseurl='', oai_src_prefix='',
                               oai_src_frequency='',
                               oai_src_config='',
                               oai_src_post='', ln=CFG_SITE_LANG,
                               confirm= -1, oai_src_sets=None,
                               oai_src_bibfilter=''):
    """creates html form to edit a OAI source. this method is calling other methods which again is calling this and sending back the output of the method.
    confirm - determines the validation status of the data input into the form"""
    _ = gettext_set_language(ln)

    if oai_src_id is None:
        return _("No OAI source ID selected.")

    if oai_src_sets is None:
        oai_src_sets = []

    output = ""
    subtitle = oaiharvest_templates.tmpl_draw_subtitle(ln=ln, title="edit source", subtitle="Edit OAI source", guideurl=guideurl)

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

    if confirm in [1, "1"] and not oai_src_name:
        output += webstyle_templates.tmpl_write_warning(_("Please enter a name for the source."))
    elif confirm in [1, "1"] and not oai_src_prefix:
        output += webstyle_templates.tmpl_write_warning(_("Please enter a metadata prefix."))
    elif confirm in [1, "1"] and not oai_src_baseurl:
        output += webstyle_templates.tmpl_write_warning(_("Please enter a base url."))
    elif confirm in [1, "1"] and not oai_src_frequency:
        output += webstyle_templates.tmpl_write_warning(_("Please choose a frequency of harvesting"))
    elif confirm in [1, "1"] and "c" in oai_src_post and (not oai_src_config or validatefile(oai_src_config) != 0):
        output += webstyle_templates.tmpl_write_warning(_("You selected a postprocess mode which involves conversion."))
        output += webstyle_templates.tmpl_write_warning(_("Please enter a valid name of or a full path to a BibConvert config file or change postprocess mode."))
    elif confirm in [1, "1"] and "f" in oai_src_post and (not oai_src_bibfilter or validatefile(oai_src_bibfilter) != 0):
        output += webstyle_templates.tmpl_write_warning(_("You selected a postprocess mode which involves filtering."))
        output += webstyle_templates.tmpl_write_warning(_("Please enter a valid name of or a full path to a BibFilter script or change postprocess mode."))
    elif oai_src_id > -1 and confirm in [1, "1"]:
        if not oai_src_frequency:
            oai_src_frequency = 0
        if not oai_src_config:
            oai_src_config = "NULL"
        if not oai_src_post:
            oai_src_post = []
        res = modify_oai_src(oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_config, oai_src_post, oai_src_sets, oai_src_bibfilter)
        output += write_outcome(res)

    text = oaiharvest_templates.tmpl_print_brs(ln, 1)
    text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, title="Source name", name="oai_src_name", value=oai_src_name)
    text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, title="Base URL", name="oai_src_baseurl", value=oai_src_baseurl)

    sets = findSets(oai_src_baseurl)
    if sets:
        sets.sort()
        # Show available sets to users
        sets_specs = [aset[0] for aset in sets]
        sets_labels = [((aset[1] and aset[0] + ' (' + aset[1] + ')') or aset[0]) \
                       for aset in sets]
        sets_states = [ ((aset[0] in oai_src_sets and 1) or 0) for aset in sets]
        text += oaiharvest_templates.tmpl_admin_checkboxes(ln=ln,
                                                           title="Sets",
                                                           name="oai_src_sets",
                                                           values=sets_specs,
                                                           labels=sets_labels,
                                                           states=sets_states,
                                                           message="Leave all unchecked for non-selective harvesting")
    else:
        # Let user specify sets in free textbox
        text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln,
                                                          title="Sets",
                                                          name='oai_src_sets',
                                                          value=' '.join(oai_src_sets))

    text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, \
                title="Metadata prefix", name="oai_src_prefix", value=oai_src_prefix)
    text += oaiharvest_templates.tmpl_admin_w200_select(ln=ln, \
                title="Frequency", name="oai_src_frequency", \
                valuenil="- select frequency -" , values=freqs, \
                lastval=oai_src_frequency)
    post_values = [mode[0] for mode in CFG_OAI_POSSIBLE_POSTMODES]
    post_labels = [mode[1] for mode in CFG_OAI_POSSIBLE_POSTMODES]
    post_states = [((mode[0] in oai_src_post and 1) or 0) for mode in CFG_OAI_POSSIBLE_POSTMODES]
    text += oaiharvest_templates.tmpl_admin_checkboxes(ln=ln, title="Postprocess",
                                                       name="oai_src_post",
                                                       values=post_values, labels=post_labels, states=post_states,
                                                       message="Leave all unchecked for no post-processing")
    text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, \
                title="BibConvert configuration file (if needed by postprocess)", \
                name="oai_src_config", value=oai_src_config, \
                suffix="<small>Eg: </small><code>oaidc2marcxml.xsl</code>, <code>oaimarc2marcxml.xsl</code><br/>")
    text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, \
                title="BibFilter program (if needed by postprocess)", \
                name="oai_src_bibfilter", value=oai_src_bibfilter)
    text += oaiharvest_templates.tmpl_print_brs(ln, 2)

    output += createhiddenform(action="editsource#1",
                                text=text,
                                button="Modify",
                                oai_src_id=oai_src_id,
                                ln=ln,
                                confirm=1)

    output += oaiharvest_templates.tmpl_print_brs(ln, 2)
    output += create_html_link(urlbase=oai_harvest_admin_url + \
                               "/index",
                               urlargd={'ln': ln},
                               link_label=_("Go back to the OAI sources overview"))

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_addsource(oai_src_name=None, oai_src_baseurl='',
                              oai_src_prefix='', oai_src_frequency='',
                              oai_src_lastrun='', oai_src_config='',
                              oai_src_post=[], ln=CFG_SITE_LANG,
                              confirm= -1, oai_src_sets=None,
                              oai_src_bibfilter=''):
    """creates html form to add a new source"""
    _ = gettext_set_language(ln)

    if oai_src_name is None:
        return "No OAI source name selected."

    if oai_src_sets is None:
        oai_src_sets = []
    subtitle = oaiharvest_templates.tmpl_draw_subtitle(ln=ln,
                                                       title="add source",
                                                       subtitle="Add new OAI source",
                                                       guideurl=guideurl)
    output = ""

    if confirm <= -1:
        text = oaiharvest_templates.tmpl_print_brs(ln, 1)
        text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln,
                                                          title="Enter the base url",
                                                          name="oai_src_baseurl",
                                                          value=oai_src_baseurl + 'http://')
        output = createhiddenform(action="addsource",
                                  text=text,
                                  ln=ln,
                                  button="Validate",
                                  confirm=0)

    if (confirm not in ["-1", -1] and validate(oai_src_baseurl)[0] == 0) or \
           confirm in ["1", 1]:

        if confirm in [1, "1"] and not oai_src_name:
            output += webstyle_templates.tmpl_write_warning(_("Please enter a name for the source."))
        elif confirm in [1, "1"] and not oai_src_prefix:
            output += webstyle_templates.tmpl_write_warning(_("Please enter a metadata prefix."))
        elif confirm in [1, "1"] and not oai_src_frequency:
            output += webstyle_templates.tmpl_write_warning(_("Please choose a frequency of harvesting"))
        elif confirm in [1, "1"] and not oai_src_lastrun:
            output += webstyle_templates.tmpl_write_warning(_("Please choose the harvesting starting date"))
        elif confirm in [1, "1"] and "c" in oai_src_post and (not oai_src_config or validatefile(oai_src_config) != 0):
            output += webstyle_templates.tmpl_write_warning(_("You selected a postprocess mode which involves conversion."))
            output += webstyle_templates.tmpl_write_warning(_("Please enter a valid name of or a full path to a BibConvert config file or change postprocess mode."))
        elif confirm in [1, "1"] and "f" in oai_src_post and (not oai_src_bibfilter or validatefile(oai_src_bibfilter) != 0):
            output += webstyle_templates.tmpl_write_warning(_("You selected a postprocess mode which involves filtering."))
            output += webstyle_templates.tmpl_write_warning(_("Please enter a valid name of or a full path to a BibFilter script or change postprocess mode."))
        elif oai_src_name and confirm in [1, "1"]:
            if not oai_src_frequency:
                oai_src_frequency = 0
            if not oai_src_lastrun:
                oai_src_lastrun = 1
            if not oai_src_config:
                oai_src_config = "NULL"
            if not oai_src_post:
                oai_src_post = []

            res = add_oai_src(oai_src_name, oai_src_baseurl,
                              oai_src_prefix, oai_src_frequency,
                              oai_src_lastrun, oai_src_config,
                              oai_src_post, oai_src_sets,
                              oai_src_bibfilter)
            output += write_outcome(res)


        output += oaiharvest_templates.tmpl_output_validate_info(ln, 0, str(oai_src_baseurl))
        output += oaiharvest_templates.tmpl_print_brs(ln, 2)
        text = oaiharvest_templates.tmpl_admin_w200_text(ln=ln,
                                                         title="Source name",
                                                         name="oai_src_name",
                                                         value=oai_src_name)

        metadatas = findMetadataFormats(oai_src_baseurl)
        if metadatas:
            # Show available metadata to user
            prefixes = []
            for value in metadatas:
                prefixes.append([value, str(value)])
            text += oaiharvest_templates.tmpl_admin_w200_select(ln=ln,
                                                                title="Metadata prefix",
                                                                name="oai_src_prefix",
                                                                valuenil="- select prefix -" ,
                                                                values=prefixes,
                                                                lastval=oai_src_prefix)
        else:
            # Let user specify prefix in free textbox
            text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln,
                                                              title="Metadata prefix",
                                                              name="oai_src_prefix",
                                                              value=oai_src_prefix)

        sets = findSets(oai_src_baseurl)
        if sets:
            sets.sort()
            # Show available sets to users
            sets_specs = [aset[0] for aset in sets]
            sets_labels = [((aset[1] and aset[0] + ' (' + aset[1] + ')') or aset[0]) \
                           for aset in sets]
            sets_states = [ ((aset[0] in oai_src_sets and 1) or 0) \
                            for aset in sets]
            text += oaiharvest_templates.tmpl_admin_checkboxes(ln=ln,
                                                               title="Sets",
                                                               name="oai_src_sets",
                                                               values=sets_specs,
                                                               labels=sets_labels,
                                                               states=sets_states)
        else:
            # Let user specify sets in free textbox
            text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln,
                                                              title="Sets",
                                                              name='oai_src_sets',
                                                              value=' '.join(oai_src_sets))

        text += oaiharvest_templates.tmpl_admin_w200_select(ln=ln, \
                        title="Frequency", name="oai_src_frequency", \
                        valuenil="- select frequency -" , values=freqs, \
                        lastval=oai_src_frequency)
        text += oaiharvest_templates.tmpl_admin_w200_select(ln=ln, \
                        title="Starting date", name="oai_src_lastrun", \
                        valuenil="- select a date -" , values=dates, \
                        lastval=oai_src_lastrun)
        post_values = [mode[0] for mode in CFG_OAI_POSSIBLE_POSTMODES]
        post_labels = [mode[1] for mode in CFG_OAI_POSSIBLE_POSTMODES]
        post_states = [((mode[0] in oai_src_post and 1) or 0) for mode in CFG_OAI_POSSIBLE_POSTMODES]
        text += oaiharvest_templates.tmpl_admin_checkboxes(ln=ln, title="Postprocess",
                                                           name="oai_src_post",
                                                           values=post_values, labels=post_labels, states=post_states,
                                                           message="Leave all unchecked for no post-processing")
        text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, \
                        title="BibConvert configuration file (if needed by postprocess)", \
                        name="oai_src_config", value=oai_src_config)
        text += oaiharvest_templates.tmpl_admin_w200_text(ln=ln, \
                        title="BibFilter program (if needed by postprocess)", \
                        name="oai_src_bibfilter", value=oai_src_bibfilter)
        text += oaiharvest_templates.tmpl_print_brs(ln, 2)


        output += createhiddenform(action="addsource#1",
                                   text=text,
                                   button="Add OAI Source",
                                   oai_src_baseurl=oai_src_baseurl,
                                   ln=ln,
                                   confirm=1)
    elif confirm in ["0", 0] and validate(oai_src_baseurl)[0] > 0:
        # Could not perform first url validation
        output += oaiharvest_templates.tmpl_output_validate_info(ln, 1, str(oai_src_baseurl))
        output += oaiharvest_templates.tmpl_print_brs(ln, 2)
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/addsource",
                                   urlargd={'ln': ln},
                                   link_label=_("Try again with another url"))
        output += " " + _("or") + " "
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/addsource",
                                   urlargd={'ln': ln,
                                            'oai_src_baseurl': oai_src_baseurl,
                                            'confirm': '1'},
                                   link_label=_("Continue anyway"))
        output += oaiharvest_templates.tmpl_print_brs(ln, 1)
        output += " " + _("or") + " "
        output += oaiharvest_templates.tmpl_print_brs(ln, 1)
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/index",
                                   urlargd={'ln': ln},
                                   link_label=_("Go back to the OAI sources overview"))
    elif confirm not in ["-1", -1] and validate(oai_src_baseurl)[0] > 0:
        output += oaiharvest_templates.tmpl_output_validate_info(ln, 1, str(oai_src_baseurl))
        output += oaiharvest_templates.tmpl_print_brs(ln, 2)
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/addsource",
                                   urlargd={'ln': ln},
                                   link_label=_("Try again"))
        output += oaiharvest_templates.tmpl_print_brs(ln, 1)
        output += " " + _("or") + " "
        output += oaiharvest_templates.tmpl_print_brs(ln, 1)
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/index",
                                   urlargd={'ln': ln},
                                   link_label=_("Go back to the OAI sources overview"))
    elif confirm not in ["-1", -1]:
        output += oaiharvest_templates.tmpl_output_error_info(ln, str(oai_src_baseurl), validate(oai_src_baseurl)[1])
        output += oaiharvest_templates.tmpl_print_brs(ln, 2)
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/addsource",
                                   urlargd={'ln': ln},
                                   link_label=_("Try again"))
        output += oaiharvest_templates.tmpl_print_brs(ln, 1)
        output += " " + _("or") + " "
        output += oaiharvest_templates.tmpl_print_brs(ln, 1)
        output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/index",
                                   urlargd={'ln': ln},
                                   link_label=_("Go back to the OAI sources overview"))


    output += oaiharvest_templates.tmpl_print_brs(ln, 2)
    output += create_html_link(urlbase=oai_harvest_admin_url + \
                               "/index",
                               urlargd={'ln': ln},
                               link_label=_("Go back to the OAI sources overview"))

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_delsource(oai_src_id=None, ln=CFG_SITE_LANG, confirm=0):
    """creates html form to delete a source
    """
    _ = gettext_set_language(ln)
    output = ""
    subtitle = ""

    if oai_src_id:
        oai_src = get_oai_src(oai_src_id)
        namesrc = (oai_src[0][1])
        pagetitle = """Delete OAI source: %s""" % cgi.escape(namesrc)
        subtitle = oaiharvest_templates.tmpl_draw_subtitle(ln=ln, \
            title="delete source", subtitle=pagetitle, guideurl=guideurl)
        output = ""

        if confirm in ["0", 0]:
            if oai_src:
                question = """Do you want to delete the OAI source '%s' and all its definitions?""" % cgi.escape(namesrc)
                text = oaiharvest_templates.tmpl_print_info(ln, question)
                text += oaiharvest_templates.tmpl_print_brs(ln, 3)
                output += createhiddenform(action="delsource#5",
                                       text=text,
                                       button="Confirm",
                                       oai_src_id=oai_src_id,
                                       confirm=1)
            else:
                return oaiharvest_templates.tmpl_print_info(ln, "Source specified does not exist.")
        elif confirm in ["1", 1]:
            res = delete_oai_src(oai_src_id)
            if res[0] == 1:
                output += oaiharvest_templates.tmpl_print_info(ln, "Source removed.")
                output += oaiharvest_templates.tmpl_print_brs(ln, 1)
                output += write_outcome(res)
            else:
                output += write_outcome(res)

    output += oaiharvest_templates.tmpl_print_brs(ln, 2)
    output += create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/index",
                                   urlargd={'ln': ln},
                                   link_label=_("Go back to the OAI sources overview"))

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_testsource(oai_src_id=None, ln=CFG_SITE_LANG, record_id=None):
    """Test OAI source page"""
    _ = gettext_set_language(ln)
    if oai_src_id is None:
        return _("No OAI source ID selected.")
    result = ""

    result += oaiharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += oaiharvest_templates.tmpl_draw_titlebar(ln=ln, title=\
        "Record ID ( Recognized by the data source )", guideurl=guideurl)
    record_str = ""
    if record_id != None:
        record_str = str(record_id)
    form_text = oaiharvest_templates.tmpl_admin_w200_text(ln=ln, title=\
        "Record identifier", name="record_id", value=record_str)
    result += createhiddenform(action="testsource",
                               text=form_text,
                               button="Test",
                               oai_src_id=oai_src_id,
                               ln=ln)
    if record_id != None:
        result += oaiharvest_templates.tmpl_draw_titlebar(ln=ln, title=\
            "OAI XML downloaded from the source" , guideurl=guideurl)
        result += oaiharvest_templates.tmpl_embed_document(\
            "/admin/oaiharvest/oaiharvestadmin.py/preview_original_xml?oai_src_id=" \
            + str(oai_src_id) + "&record_id=" \
            + str(record_id))
        result += oaiharvest_templates.tmpl_draw_titlebar(ln=ln, title=\
            "MARC XML after all the transformations", guideurl=guideurl)
        result += oaiharvest_templates.tmpl_embed_document(\
            "/admin/oaiharvest/oaiharvestadmin.py/preview_harvested_xml?oai_src_id=" \
            + str(oai_src_id) + "&record_id=" \
            + str(record_id))
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

def perform_request_viewtasklogs(ln, task_id):
    t_id = int(task_id) # preventing malicious user input
    guideurl = "help/admin/oaiharvest-admin-guide"

    log_name = does_logfile_exist(t_id)
    err_name = does_errfile_exist(t_id)

    result = ""
    result += oaiharvest_templates.tmpl_output_menu(ln, None, guideurl)

    if log_name != None:
        file_descriptor = open(log_name)
        content = file_descriptor.read(-1)
        file_descriptor.close();
        result += oaiharvest_templates.tmpl_draw_titlebar(ln, "Log file : " + \
                                                              log_name, guideurl)

        result += oaiharvest_templates.tmpl_output_scrollable_frame(\
            oaiharvest_templates.tmpl_output_preformatted(content))

    if err_name != None:
        file_descriptor = open(err_name)
        content = file_descriptor.read(-1)
        file_descriptor.close();
        result += oaiharvest_templates.tmpl_print_brs(ln, 2)
        result += oaiharvest_templates.tmpl_draw_titlebar(ln, "Log file : " + \
                                                              err_name, guideurl)
        result += oaiharvest_templates.tmpl_output_scrollable_frame(\
            oaiharvest_templates.tmpl_output_preformatted(content))

    return result

### Probably should be moved to some other data-connection file

def build_history_row(item, ln, show_selection, show_oai_source, show_record_ids, identifier=""):
    def get_cssclass(cssclass):
        if cssclass == "oddtablecolumn":
            return "pairtablecolumn"
        else:
            return "oddtablecolumn"

    cssclass = get_cssclass("pairtablecolumn")
    result = oaiharvest_templates.tmpl_table_row_begin()
    result += oaiharvest_templates.tmpl_table_output_cell(\
        oaiharvest_templates.format_date(item.date_harvested) + " " + \
        oaiharvest_templates.format_time(item.date_harvested), cssclass=cssclass)
    cssclass = get_cssclass(cssclass)
    result += oaiharvest_templates.tmpl_table_output_cell(\
        oaiharvest_templates.format_date(item.date_inserted) + " " + \
        oaiharvest_templates.format_time(item.date_inserted), cssclass=cssclass)

    if show_record_ids:
        record_history_link = create_html_link(urlbase=oai_harvest_admin_url + \
               "/viewentryhistory",
                urlargd={'ln': ln,
                         'oai_id': str(item.oai_id),
                         'start': "0"},
                link_label=str(item.oai_id))
        cssclass = get_cssclass(cssclass)
        result += oaiharvest_templates.tmpl_table_output_cell(record_history_link, \
            cssclass=cssclass)

        record_details_link = create_html_link(CFG_SITE_URL + \
                                               "/"+ CFG_SITE_RECORD +"/" + str(item.record_id),
                                               urlargd={'ln': ln},
                                               link_label=str(item.record_id))
        cssclass = get_cssclass(cssclass)
        result += oaiharvest_templates.tmpl_table_output_cell(record_details_link, \
            cssclass=cssclass)

    cssclass = get_cssclass(cssclass)
    result += oaiharvest_templates.tmpl_table_output_cell(item.inserted_to_db, \
        cssclass=cssclass)

    cssclass = get_cssclass(cssclass)
    task_id = str(item.bibupload_task_id)
    if does_errfile_exist(item.bibupload_task_id) or does_logfile_exist(item.bibupload_task_id):
        task_id = create_html_link(urlbase=oai_harvest_admin_url + \
                                   "/viewtasklogs",
                                   urlargd={'ln': ln,
                                            'task_id': str(item.bibupload_task_id)},
                                   link_label=str(item.bibupload_task_id))
    result += oaiharvest_templates.tmpl_table_output_cell(task_id, cssclass=cssclass)

    if show_selection:
        chkbox = oaiharvest_templates.tmpl_output_checkbox(item.oai_id, identifier, "1")
        cssclass = get_cssclass(cssclass)
        result += oaiharvest_templates.tmpl_table_output_cell(chkbox, \
            cssclass=cssclass)

    if show_oai_source:
        cssclass = get_cssclass(cssclass)
        result += oaiharvest_templates.tmpl_table_output_cell(str(item.oai_src_id), \
            cssclass=cssclass)

    result += oaiharvest_templates.tmpl_table_row_end()
    return result

def build_history_table_header(show_selection=True, show_oai_source=False, \
    show_record_ids=True):

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
    stats = get_month_logs_size(oai_src_id, date)
    headers = build_history_table_header()
    result = oaiharvest_templates.tmpl_table_begin(headers)
    identifiers = {}
    for day in stats:
        result += oaiharvest_templates.tmpl_table_row_begin()
        d_date = datetime.datetime(date.year, date.month, day)
        result += oaiharvest_templates.tmpl_history_table_output_day_cell(d_date, \
            stats[day], oai_src_id, ln, stats[day] > day_limit)
        btn = oaiharvest_templates.tmpl_output_select_day_button(day)
        result += oaiharvest_templates.tmpl_table_output_cell(btn)
        result += oaiharvest_templates.tmpl_table_row_end()
        day_data = get_history_entries_for_day(oai_src_id, d_date, limit=day_limit)
        for item in day_data:
            identifier = oaiharvest_templates.format_date(item.date_harvested) + \
                oaiharvest_templates.format_time(item.date_harvested) + "_" + item.oai_id
            result += build_history_row(item, ln, show_selection=True, show_oai_source=\
                False, show_record_ids=True, identifier=identifier)
            if not identifiers.has_key(item.date_harvested.day):
                identifiers[item.date_harvested.day] = []
            identifiers[item.date_harvested.day].append(identifier)
        if stats[day] > day_limit:
            result += oaiharvest_templates.tmpl_history_table_output_day_details_cell(\
                ln, d_date, oai_src_id)
    result += oaiharvest_templates.tmpl_table_end()
    result += oaiharvest_templates.tmpl_output_identifiers(identifiers)
    return result

def build_history_table(data, ln=CFG_SITE_LANG, show_selection=True, \
    show_oai_source=False, show_record_ids=True):

    headers = build_history_table_header(show_selection=show_selection, \
        show_oai_source=show_oai_source, show_record_ids=show_record_ids)
    result = oaiharvest_templates.tmpl_table_begin(headers)

    identifiers = {}
    for item in data:
        identifier = oaiharvest_templates.format_date(item.date_harvested) + \
            oaiharvest_templates.format_time(item.date_harvested) + "_" + item.oai_id
        result += build_history_row(item, ln, show_selection=show_selection, \
            show_oai_source=show_oai_source, show_record_ids=show_record_ids, \
            identifier=identifier)
        if show_selection:
            if not identifiers.has_key(item.date_harvested.day):
                identifiers[item.date_harvested.day] = []
            identifiers[item.date_harvested.day].append(identifier)
    result += oaiharvest_templates.tmpl_table_end()
    if show_selection:
        result += oaiharvest_templates.tmpl_output_identifiers(identifiers)
    return result

def perform_request_viewhistory(oai_src_id=None, ln=CFG_SITE_LANG, month=None, year=None):

    """ Creates html to view the harvesting history """
    date = datetime.datetime.now()
    if year != None and month != None:
        year = int(year)
        month = int(month)
        date = datetime.datetime(year, month, 1)
    result = ""
    result += oaiharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += oaiharvest_templates.tmpl_output_history_javascript_functions()
    result += oaiharvest_templates.tmpl_output_month_selection_bar(oai_src_id, ln, \
        current_month=month, current_year=year)
    inner_text = build_month_history_table(oai_src_id, date, ln)
    inner_text += oaiharvest_templates.tmpl_print_brs(ln, 1)
    inner_text = oaiharvest_templates.tmpl_output_scrollable_frame(inner_text)
    inner_text += oaiharvest_templates.tmpl_output_selection_bar()
    result += createhiddenform(action="/admin/oaiharvest/oaiharvestadmin.py/reharvest", \
        text=inner_text, button="Reharvest selected records", oai_src_id=\
        oai_src_id, ln=ln)
    return result


def perform_request_viewhistoryday(oai_src_id=None, ln=CFG_SITE_LANG,
                                   month=None, year=None, day=None,
                                   start=0):
    """
    Records history page
    """
    _ = gettext_set_language(ln)
    page_length = 50
    result = ""
    result += oaiharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    considered_date = datetime.datetime.now()
    if year != None and month != None and day != None:
        considered_date = datetime.datetime(year, month, day)
    number_of_records = get_day_logs_size(oai_src_id, considered_date)
    return_to_month_link = create_html_link(
        urlbase=oai_harvest_admin_url + \
        "/viewhistory",
        urlargd={'ln': ln,
                 'oai_src_id': str(oai_src_id),
                 'year': str(considered_date.year),
                 'month': str(considered_date.month)},
        link_label="&lt;&lt; " + _("Return to the month view"))

    next_page_link = ""
    if number_of_records > start + page_length:
        next_page_link = create_html_link(
            urlbase=oai_harvest_admin_url + \
            "/viewhistoryday",
            urlargd={'ln': ln,
                     'oai_src_id': str(oai_src_id),
                     'year': str(considered_date.year),
                     'month': str(considered_date.month),
                     'day': str(considered_date.day),
                     'start': str(start + page_length)},
            link_label=_("Next page") + " &gt;&gt;")
    prev_page_link = ""
    if start > 0:
        new_start = start - page_length
        if new_start < 0:
            new_start = 0
        prev_page_link = create_html_link(
            urlbase=oai_harvest_admin_url + \
            "/viewhistoryday",
            urlargd={'ln': ln,
                     'oai_src_id': str(oai_src_id),
                     'year': str(considered_date.year),
                     'month': str(considered_date.month),
                     'day': str(considered_date.day),
                     'start': str(new_start)},
            link_label="&lt;&lt; " + _("Previous page"))
    last_shown = start + page_length
    if last_shown > number_of_records:
        last_shown = number_of_records
    current_day_records = get_history_entries_for_day(oai_src_id, considered_date, limit=\
        page_length, start=start)
    current_range = "&nbsp;&nbsp;&nbsp;&nbsp;Viewing entries : " + str(start + 1) + "-" + \
        str(last_shown) + "&nbsp;&nbsp;&nbsp;&nbsp;"
    # Building the interface
    result += oaiharvest_templates.tmpl_draw_titlebar(ln, "Viewing history of " + str(year)\
        + "-" + str(month) + "-" + str(day) , guideurl)
    result += prev_page_link + current_range + next_page_link + \
        oaiharvest_templates.tmpl_print_brs(ln, 1)
    result += oaiharvest_templates.tmpl_output_history_javascript_functions()
    inner_text = oaiharvest_templates.tmpl_output_scrollable_frame(build_history_table(\
        current_day_records, ln=ln))
    inner_text += oaiharvest_templates.tmpl_output_selection_bar()
    result += createhiddenform(action="/admin/oaiharvest/oaiharvestadmin.py/reharvest", \
        text=inner_text, button="Reharvest selected records", oai_src_id=oai_src_id, ln=ln)
    result += return_to_month_link + oaiharvest_templates.tmpl_print_brs(ln, 1)
    return result


def perform_request_viewentryhistory(oai_id, ln, start):
    """History of an OAI record"""
    _ = gettext_set_language(ln)
    page_length = 50
    result = ""
    result += oaiharvest_templates.tmpl_output_menu(ln, None, guideurl)

    number_of_records = get_entry_logs_size(oai_id)

    next_page_link = ""
    if number_of_records > start + page_length:
        prev_page_link = create_html_link(
            urlbase=oai_harvest_admin_url + \
            "/viewhistoryday",
            urlargd={'ln': ln,
                     'oai_id': str(oai_id),
                     'start': str(start + page_length)},
            link_label=_("Next page") + " &gt;&gt;")
    prev_page_link = ""
    if start > 0:
        new_start = start - page_length
        if new_start < 0:
            new_start = 0
        prev_page_link = create_html_link(
            urlbase=oai_harvest_admin_url + \
            "/viewhistoryday",
            urlargd={'ln': ln,
                     'oai_id': str(oai_id),
                     'start': str(new_start)},
            link_label="&lt;&lt; " + _("Previous page"))
    last_shown = start + page_length
    if last_shown > number_of_records:
        last_shown = number_of_records
    current_entry_records = get_entry_history(oai_id, limit=page_length, start=start)
    current_range = "&nbsp;&nbsp;&nbsp;&nbsp;Viewing entries : " + str(start + 1) \
        + "-" + str(last_shown) + "&nbsp;&nbsp;&nbsp;&nbsp;"
    # Building the interface
    result += oaiharvest_templates.tmpl_draw_titlebar(ln, "Viewing history of " + \
        str(oai_id) , guideurl)
    result += prev_page_link + current_range + next_page_link + \
        oaiharvest_templates.tmpl_print_brs(ln, 1)
    result += oaiharvest_templates.tmpl_output_history_javascript_functions()
    inner_text = oaiharvest_templates.tmpl_output_scrollable_frame(\
        build_history_table(current_entry_records, ln, show_selection=False, \
        show_oai_source=True, show_record_ids=False))
    result += inner_text
    result += oaiharvest_templates.tmpl_print_brs(ln, 1)
    return result

############################################################
###  The functions allowing to preview the harvested XML ###
############################################################

def harvest_record(record_id , oai_src_baseurl, oai_src_prefix):
    """
       Harvests given record and returns it's string as a result
    """
    command = CFG_BINDIR + "/oaiharvest -vGetRecord -i" + record_id \
              + " -p" + oai_src_prefix + " " + oai_src_baseurl
    program_output = os.popen(command)
    result = program_output.read(-1)
    program_output.close()
    return result

def convert_record(oai_src_config, record_to_convert):
    command = CFG_BINDIR + "/bibconvert -c " + oai_src_config
    (s_in, s_out, s_err) = os.popen3(command)
    s_in.write(record_to_convert)
    s_in.close()
    s_err.readlines()
    result = s_out.read(-1)
    s_err.close()
    s_out.close()
    return result

def format_record(oai_src_bibfilter, record_to_convert, treat_new=False):
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

def harvest_postprocress_record(oai_src_id, record_id, treat_new=False):
    """Havest ther record and postprocess it"""
    oai_src = get_oai_src(oai_src_id)
    oai_src_baseurl = oai_src[0][2]
    oai_src_prefix = oai_src[0][3]
    oai_src_config = oai_src[0][5]
    oai_src_post = oai_src[0][6]
    oai_src_bibfilter = oai_src[0][8]
    result = harvest_record(record_id, oai_src_baseurl, oai_src_prefix)
    if result == None:
        return (False, "Error during harvesting")
    if oai_src_post.find("c") != -1:
        result = convert_record(oai_src_config, result)
        if result == None:
            return (False, "Error during converting")
    if oai_src_post.find("f") != -1:
        fres = format_record(oai_src_bibfilter, result, treat_new=treat_new)
        fname = fres[0]
        if fname != None:
            f = open(fname, "r")
            result = f.read(-1)
            f.close()
            os.remove(fname)
        else:
            return (False, "Error during formatting: " + fres[1] + "\n\n" + fres[2])
    return (True, result)

def upload_record(record=None, uploader_paremeters=None, oai_source_id=None):
    """Upload the given record"""
    if record is None:
        return
    if uploader_paremeters is None:
        uploader_paremeters = ["-r", "-i"]
    (file_descriptor, file_name) = tempfile.mkstemp()
    f = os.fdopen(file_descriptor, "w")
    f.write(record)
    f.close()
    oai_harvest_daemon.call_bibupload(file_name, uploader_paremeters, oai_src_id=oai_source_id)
    #command = CFG_BINDIR + "/bibupload " + uploader_paremeters + " "
    #command += file_name

    #out = os.popen(command)
    #output_data = out.read(-1)
    #out.close()

def perform_request_preview_original_xml(oai_src_id=None, record_id=None):
    """Harvest a record and return it. No side effect, useful for preview"""
    oai_src = get_oai_src(oai_src_id)
    oai_src_baseurl = oai_src[0][2]
    oai_src_prefix = oai_src[0][3]
    record = harvest_record(record_id, oai_src_baseurl, oai_src_prefix)
    return record

def perform_request_preview_harvested_xml(oai_src_id=None, record_id=None):
    return harvest_postprocress_record(oai_src_id, record_id, treat_new=True)

############################################################
### Reharvesting of already existing records             ###
############################################################

def perform_request_reharvest_records(oai_src_id=None, ln=CFG_SITE_LANG, record_ids=None):
    for record_id in record_ids:
        # 1) Run full harvesing process as in the preview scenarios
        transformed = harvest_postprocress_record(oai_src_id, record_id, treat_new=True)[1]
        upload_record(transformed, ["-i", "-r"], oai_src_id)
    result = oaiharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += oaiharvest_templates.tmpl_print_info(ln, "Submitted for insertion into the database")
    return result

def perform_request_harvest_record(oai_src_id=None, ln=CFG_SITE_LANG, record_id=None):
    """ Request for harvesting a new record """
    if oai_src_id is None:
        return "No OAI source ID selected."
    result = ""
    guideurl = "help/admin/oaiharvest-admin-guide"
    result += oaiharvest_templates.tmpl_output_menu(ln, oai_src_id, guideurl)
    result += oaiharvest_templates.tmpl_draw_titlebar(ln=ln, \
        title="Record ID ( Recognized by the data source )", guideurl=guideurl)
    record_str = ""
    if record_id != None:
        record_str = str(record_id)
    form_text = oaiharvest_templates.tmpl_admin_w200_text(ln=ln, \
        title="Record identifier", name="record_id", value=record_str)
    result += createhiddenform(action="harvest",
                               text=form_text,
                               button="Harvest",
                               oai_src_id=oai_src_id,
                               ln=ln)
    if record_id != None:
        # there was a harvest-request
        transformed = harvest_postprocress_record(oai_src_id, record_id)[1]
        upload_record(transformed, ["-i"], oai_src_id)
        result += oaiharvest_templates.tmpl_print_info(ln, "Submitted for insertion into the database")
    return result


############################
### Holding pen support  ###
############################
def build_holdingpen_table(data, ln=CFG_SITE_LANG):
    _ = gettext_set_language(ln)
    result = ""
    headers = ["OAI Record ID", "Insertion Date", "", ""]
    result += oaiharvest_templates.tmpl_table_begin(headers)
    for record in data:
        oai_id = record[0]
        date_inserted = record[1]
        hpupdate_id = record[2]
        # getting the modyfied record's ID
        rec_id = get_holdingpen_entry_details(hpupdate_id)[1]
        result += oaiharvest_templates.tmpl_table_row_begin()
        result += oaiharvest_templates.tmpl_table_output_cell(str(oai_id), cssclass="oddtablecolumn")
        result += oaiharvest_templates.tmpl_table_output_cell(str(date_inserted), cssclass="pairtablecolumn")
        details_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                        "/viewhprecord",
                                        urlargd={'ln': ln,
                                                 'hpupdate_id': str(hpupdate_id)},
                                        link_label=_("Compare with original"))
        result += oaiharvest_templates.tmpl_table_output_cell(details_link, cssclass="oddtablecolumn")
        # creating link to bibedit to apply changes
        apply_link = create_html_link(urlbase=CFG_SITE_URL + '/record/edit/#' + \
                                        'state=hpapply&recid=' + str(rec_id) + \
                                        '&hpid=' + str(hpupdate_id),
                                        urlargd={},
                                        link_label=_("Apply changes"),
                                        escape_urlargd = False)
        result += oaiharvest_templates.tmpl_table_output_cell(apply_link, cssclass="pairtablecolumn")
        delete_hp_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                          "/delhprecord",
                                          urlargd={'ln': ln,
                                                   'hpupdate_id' : str(hpupdate_id)},
                                          link_label=_("Delete from holding pen"))
        result += oaiharvest_templates.tmpl_table_output_cell(delete_hp_link, cssclass="oddtablecolumn")
        result += oaiharvest_templates.tmpl_table_row_end()
    result += oaiharvest_templates.tmpl_table_end()
    return result

def perform_request_viewholdingpen(ln=CFG_SITE_LANG, start=0, limit= -1):
    data = get_holdingpen_entries(start, limit)
    result = ""
    result += build_holdingpen_table(data, ln)
    return result

def perform_request_viewhprecord(hpupdate_id, ln=CFG_SITE_LANG):
    _ = gettext_set_language(ln)
    result = ""
    try:
        (oai_id, record_id, date_inserted, hprecord_content) = get_holdingpen_entry_details(hpupdate_id)
    except:
        return _("Error when retrieving the Holding Pen entry")
    try:
        db_rec = get_record(record_id)
        db_MARC = create_marc_record(db_rec, record_id, {"text-marc": 1, "aleph-marc": 0})
    #import rpdb2; rpdb2.start_embedded_debugger('password', fAllowRemote=True)
        db_content = oaiharvest_templates.tmpl_output_preformatted(db_MARC) # originally .encode("utf-8") ... does ot work
        db_label = "Database version of record" + oaiharvest_templates.tmpl_print_brs(ln, 1)
    except:
        return _("Error when retrieving the record")
    try:
        hp_rec = create_record(hprecord_content)[0]
        hp_MARC = create_marc_record(hp_rec, record_id, {"text-marc": 1, "aleph-marc": 0})
        hp_content = oaiharvest_templates.tmpl_output_preformatted(hp_MARC) # originally .encode("utf-8") ... does ot work
        hp_label = oaiharvest_templates.tmpl_print_brs(ln, 2) + "Holdingpen version of record"\
            + oaiharvest_templates.tmpl_print_brs(ln, 1)
    except:
        return _("Error when formatting the Holding Pen entry. Probably its content is broken")
    submit_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                       "/accepthprecord",
                                   urlargd={'ln': ln,
                                            'hpupdate_id': hpupdate_id},
                                   link_label=_("Accept Holding Pen version"))
    delete_link = create_html_link(urlbase=oai_harvest_admin_url + \
                                       "/delhprecord",
                                   urlargd={'ln': ln,
                                            'oai_id': str(oai_id),
                                            'date_inserted': str(date_inserted)},
                                   link_label=_("Delete from holding pen"))

    result = ""
    result += db_label
    result += db_content
    result += hp_label
    result += hp_content
    result += delete_link + " "
    result += submit_link
    return result

def perform_request_delhprecord(hpupdate_id, ln=CFG_SITE_LANG):
    _ = gettext_set_language(ln)
    delete_holdingpen_entry(hpupdate_id)
    return _("Record deleted from the holding pen")

def perform_request_accepthprecord(hpupdate_id):
    record_xml = get_holdingpen_entry_details(hpupdate_id)[3]
    delete_holdingpen_entry(hpupdate_id)
    upload_record(record_xml)
    return perform_request_view_holdingpen_tree("")


# new functions for the holding pen

def perform_request_gethpall(prefix, filter_key):
    years = get_holdingpen_years(filter_key)
    result = ""
    for year in years:
        result += "<h1 id=\"%s_%s_%s\"><a href='#'>Year %s (%s entries)</a></h1><div>" % (prefix, str(year[0]), filter_key, str(year[0]), str(year[1]))
        months = get_holdingpen_year(year[0], filter_key)
        for month in months:
            result += "<h2 id=\"%s_%s_%s_%s\"><a href='#'>%s-%s (%s entries)</a></h2><div>" % (prefix, year[0], str(month[0]), filter_key, year[0], str(month[0]), str(month[1]))
            days = get_holdingpen_month(year[0], month[0], filter_key)
            for day in days:
                result += "<h3 id=\"%s_%s_%s_%s_%s\"><a href='#'>%s-%s-%s (%s entries)</a></h3><div></div>" % (prefix, year[0], month[0], str(day[0]), filter_key, year[0], month[0], str(day[0]), str(day[1]))
            result += "</div>"
        result += "</div>"
    return result

def perform_request_gethpyears(prefix, filter_key):
    years = get_holdingpen_years(filter_key)
    result = ""
    for year in years:
        result += "<li id=\"%s_%s_%s\"><span>Year %s (%s entries)</span> <ul id=\"%s_%s_%s_ul\"></ul></li>" % (prefix, str(year[0]), filter_key, str(year[0]), str(year[1]), prefix, str(year[0]), filter_key)
    return result

def perform_request_gethpyear(prefix, year, filter_key):
    months = get_holdingpen_year(year, filter_key)
    result = ""
    for month in months:
        result += "<li id=\"%s_%s_%s_%s\"><span>%s-%s (%s entries)</span> <ul id=\"%s_%s_%s_%s_ul\"></ul></li>" % (prefix, year, str(month[0]), filter_key, year, str(month[0]), str(month[1]), prefix, year, str(month[0]), filter_key)
    return result

def perform_request_gethpmonth(prefix, year, month, filter_key):
    days = get_holdingpen_month(year, month, filter_key)
    result = ""
    for day in days:
        result += "<li id=\"%s_%s_%s_%s_%s\"><span>%s-%s-%s (%s entries)</span> <ul id=\"%s_%s_%s_%s_%s_ul\"></ul></li>" % (prefix, year, month, str(day[0]), filter_key, year, month, str(day[0]), str(day[1]), prefix, year, month, str(day[0]), filter_key)
    return result

def perform_request_gethpdayfragment(year, month, day, limit, start, filter_key):
    data = get_holdingpen_day_fragment(year, month, day, limit, start, filter_key)
    return build_holdingpen_table(data, "en")


def view_holdingpen_headers():
    return  oaiharvest_templates.tmpl_view_holdingpen_headers()

def perform_request_view_holdingpen_tree(filter_key):
    return  oaiharvest_templates.tmpl_view_holdingpen_body(\
                filter_key, perform_request_gethpall("holdingpencontainer", filter_key))


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
    except StandardError:
        return ""

def modify_oai_src(oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_config, oai_src_post, oai_src_sets=None, oai_src_bibfilter=''):
    """Modifies a row's parameters"""
    if oai_src_sets is None:
        oai_src_sets = []
    if oai_src_post is None:
        oai_src_post = []
    try:
        run_sql("UPDATE oaiHARVEST SET name=%s WHERE id=%s", (oai_src_name, oai_src_id))
        run_sql("UPDATE oaiHARVEST SET baseurl=%s WHERE id=%s", (oai_src_baseurl, oai_src_id))
        run_sql("UPDATE oaiHARVEST SET metadataprefix=%s WHERE id=%s", (oai_src_prefix, oai_src_id))
        run_sql("UPDATE oaiHARVEST SET frequency=%s WHERE id=%s", (oai_src_frequency, oai_src_id))
        run_sql("UPDATE oaiHARVEST SET bibconvertcfgfile=%s WHERE id=%s", (oai_src_config, oai_src_id))
        run_sql("UPDATE oaiHARVEST SET postprocess=%s WHERE id=%s", ('-'.join(oai_src_post), oai_src_id))
        run_sql("UPDATE oaiHARVEST SET setspecs=%s WHERE id=%s", (' '.join(oai_src_sets), oai_src_id))
        run_sql("UPDATE oaiHARVEST SET bibfilterprogram=%s WHERE id=%s", (oai_src_bibfilter, oai_src_id))
        return (1, "")
    except StandardError, e:
        return (0, e)

def add_oai_src(oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_lastrun, oai_src_config, oai_src_post, oai_src_sets=None, oai_src_bibfilter=''):
    """Adds a new row to the database with the given parameters"""
    if oai_src_sets is None:
        oai_src_sets = []
    try:
        if oai_src_lastrun in [0, "0"]: lastrun_mode = 'NULL'
        else:
            lastrun_mode = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # lastrun_mode = "'"+lastrun_mode+"'"
        run_sql("INSERT INTO oaiHARVEST (id, baseurl, metadataprefix, arguments, comment,  bibconvertcfgfile,  name,  lastrun,  frequency,  postprocess,  bibfilterprogram,  setspecs) VALUES (0, %s, %s, NULL, NULL, %s, %s, %s, %s, %s, %s, %s)", \
                (oai_src_baseurl, oai_src_prefix, oai_src_config, oai_src_name, lastrun_mode, oai_src_frequency, '-'.join(oai_src_post), oai_src_bibfilter, " ".join(oai_src_sets)))
        return (1, "")
    except StandardError, e:
        return (0, e)

def delete_oai_src(oai_src_id):
    """Deletes a row from the database according to its id"""
    try:
        run_sql("DELETE FROM oaiHARVEST WHERE id=%s", (oai_src_id,))
        return (1, "")
    except StandardError, e:
        return (0, e)

def get_tot_oai_src():
    """Returns number of rows in the database"""
    sql = "SELECT COUNT(*) FROM oaiHARVEST"
    res = run_sql(sql)
    return res[0][0]

def get_update_status():
    """Returns a table showing a list of all rows and their LastUpdate status"""
    return run_sql("SELECT name,lastrun FROM oaiHARVEST ORDER BY lastrun desc")

def get_next_schedule():
    """Returns the next scheduled oaiharvestrun tasks"""
    sql = "SELECT runtime,status FROM schTASK WHERE proc='oaiharvest' AND runtime > now() ORDER by runtime LIMIT 1"
    res = run_sql(sql)
    if len(res) > 0:
        return res[0]
    else:
        return ("", "")


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
        grepOUT1 = os.popen('grep -iwc "<OAI-PMH" ' + tmppath).read()
        if int(grepOUT1) == 0:
            # No.. we have an http error
            return (4, os.popen('cat ' + tmppath).read())

        grepOUT2 = os.popen('grep -iwc "<identify>" ' + tmppath).read()
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
        return (4, "An unknown error has occured: %s" % e)
    except InvalidURL, e:
        return (2, "Could not connect with URL %s. Check URL or retry when server is available: %s" % (url, e))

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
            cfgstr = ftmp.read()
            ftmp.close()
            if cfgstr != "":
                #print "Valid!"
                return 0
        except StandardError:
            pass

    # Try to read as complete path
    try:
        ftmp = open(oai_src_config, 'r')
        cfgstr = ftmp.read()
        ftmp.close()
        if cfgstr != "":
            #print "Valid!"
            return 0
        else:
            #print "Not valid!"
            return 1
    except StandardError:
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
    xmlstr = ftmp.read()
    ftmp.close()
    chunks = xmlstr.split('<metadataPrefix>')
    count = 0 # first chunk is invalid
    for chunk in chunks:
        if count != 0:
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
    xmlstr = ftmp.read()
    ftmp.close()
    chunks = xmlstr.split('<set>')
    count = 0 # first chunk is invalid
    for chunk in chunks:
        if count != 0:
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
