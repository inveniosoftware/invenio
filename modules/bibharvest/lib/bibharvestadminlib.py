## $Id$
## Administrator interface for BibIndex

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import cgi
import re
import Numeric
import os, sys, string
import ConfigParser
import time
import random
import urllib
import sre

from invenio.config import \
     cdslang, \
     tmpdir, \
     version, \
     weburl,\
     etcdir
from invenio.bibrankadminlib import \
     write_outcome,modify_translations,\
     get_def_name,\
     get_i8n_name,\
     get_name,\
     get_rnk_nametypes,\
     get_languages,\
     check_user,\
     is_adminuser,\
     adderrorbox,\
     addadminbox,\
     tupletotable,\
     tupletotable_onlyselected,\
     addcheckboxes,\
     createhiddenform,\
     serialize_via_numeric_array_dumps,\
     serialize_via_numeric_array_compr,\
     serialize_via_numeric_array_escape,\
     serialize_via_numeric_array,\
     deserialize_via_numeric_array,\
     serialize_via_marshal,\
     deserialize_via_marshal
from invenio.dbquery import run_sql, escape_string
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.webuser import getUid, get_email

import invenio.template
bibharvest_templates = invenio.template.load('bibharvest')

tmppath = tmpdir + '/bibharvestadmin.' + str(os.getpid())
guideurl = "admin/bibharvest/guide.html"

freqs = [[0, "never"], [24, "daily"], [168, "weekly"], [720, "monthly"] ]
posts = [["h", "harvest only (h)"], ["h-c", "harvest and convert (h-c)"], ["h-u", "harvest and upload (h-u)"], ["h-c-u", "harvest, convert and upload (h-c-u)"]]
dates = [[0, "from beginning"], [1, "from today"]]

def getnavtrail(previous = ''):
    """Get the navtrail"""
    return bibharvest_templates.tmpl_getnavtrail(previous = previous, ln = cdslang)    

def perform_request_index(ln=cdslang):
    """start area for administering harvesting from OAI repositories"""

    titlebar = bibharvest_templates.tmpl_draw_titlebar(ln = cdslang, weburl = weburl, title = "Overview of sources", guideurl = guideurl, extraname = "add new OAI source" , extraurl = "admin/bibharvest/bibharvestadmin.py/addsource" ) 
    titlebar2 = bibharvest_templates.tmpl_draw_titlebar(ln = cdslang, weburl = weburl, title = "Harvesting status", guideurl = guideurl) 
    header = ['name', 'baseURL', 'metadataprefix', 'frequency', 'bibconvertfile', 'postprocess', 'actions']
    header2 = ['name', 'last update']
    oai_src = get_oai_src()
    upd_status = get_update_status()

    sources = []
    for (oai_src_id,oai_src_name,oai_src_baseurl,oai_src_prefix,oai_src_frequency,oai_src_config,oai_src_post, oai_src_setspecs) in oai_src:
        namelinked_args = []
        namelinked_args.append(["oai_src_id", str(oai_src_id)]) 
        namelinked_args.append(["ln", ln])
        namelinked = bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/editsource", title = oai_src_name, args = namelinked_args)
        freq = "Not Set"
        if oai_src_frequency==0: freq = "never"
        elif oai_src_frequency==24: freq = "daily"
        elif oai_src_frequency==168: freq = "weekly"
        elif oai_src_frequency==720: freq = "monthly"
        editACTION = bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/editsource", title = "edit", args = namelinked_args)
        delACTION = bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/delsource", title = "delete", args = namelinked_args)
        action = editACTION + " / " + delACTION
        sources.append([namelinked,oai_src_baseurl,oai_src_prefix,freq,oai_src_config,oai_src_post, action])

    updates = []
    for (upd_name, upd_status) in upd_status:
        if not upd_status:
            upd_status =  bibharvest_templates.tmpl_print_warning(cdslang, "Never harvested")
        else: #cut away leading zeros
            upd_status = sre.sub(r'\.[0-9]+$', '', str(upd_status))
        updates.append([upd_name, upd_status])

    (schtime, schstatus) = get_next_schedule()
    if schtime:
        schtime = sre.sub(r'\.[0-9]+$', '', str(schtime))

    output = titlebar 
    output += bibharvest_templates.tmpl_output_numbersources(cdslang, get_tot_oai_src())
    output += tupletotable(header=header, tuple=sources)
    output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
    output += titlebar2
    output += bibharvest_templates.tmpl_output_schedule(cdslang, schtime, str(schstatus))
    output += tupletotable(header=header2, tuple=updates)
    
    return output

def perform_request_editsource(oai_src_id=None, oai_src_name='', oai_src_baseurl='', oai_src_prefix='', oai_src_frequency='', oai_src_config='', oai_src_post='',ln=cdslang, confirm=-1, oai_src_sets=[]):
    """creates html form to edit a OAI source. this method is calling other methods which again is calling this and sending back the output of the method.
    confirm - determines the validation status of the data input into the form"""

    if oai_src_id is None:
        return "No OAI source ID selected."

    output  = ""
    subtitle = bibharvest_templates.tmpl_draw_subtitle(ln = cdslang, weburl = weburl, title = "edit source", subtitle = "Edit OAI source", guideurl = guideurl)
    
    if confirm in [-1, "-1"]:
        oai_src = get_oai_src(oai_src_id)
        oai_src_name = oai_src[0][1]
        oai_src_baseurl = oai_src[0][2]
        oai_src_prefix = oai_src[0][3]
        oai_src_frequency = oai_src[0][4]
        oai_src_config = oai_src[0][5]
        oai_src_post = oai_src[0][6]
        oai_src_sets = oai_src[0][7]
        
    text = bibharvest_templates.tmpl_print_brs(cdslang, 1)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "Source name", name = "oai_src_name", value = oai_src_name)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "Base URL", name = "oai_src_baseurl", value = oai_src_baseurl)
    sets = findSets(oai_src_baseurl)
    sets_specs = [set[0] for set in sets]
    sets_names = [set[1] for set in sets]
    sets_labels = [((set[1] and set[0]+' ('+set[1]+')') or set[0]) \
                   for set in sets]
    sets_states = [ ((set[0] in oai_src_sets and 1) or 0) for set in sets]
    text += bibharvest_templates.tmpl_admin_checkboxes(ln = cdslang,
                                                       title = "Sets",
                                                       names = sets_specs,
                                                       labels = sets_labels,
                                                       states = sets_states)
    
    text += bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "Metadata prefix", name = "oai_src_prefix", value = oai_src_prefix)
    text += bibharvest_templates.tmpl_admin_w200_select(ln = cdslang, title = "Frequency", name = "oai_src_frequency", valuenil = "- select frequency -" , values = freqs, lastval = oai_src_frequency)
    text += bibharvest_templates.tmpl_admin_w200_select(ln = cdslang, title = "Postprocess", name = "oai_src_post", valuenil = "- select mode -" , values = posts, lastval = oai_src_post)
    text += bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "BibConvert configuration file", name = "oai_src_config", value = oai_src_config)
    text += bibharvest_templates.tmpl_print_brs(cdslang, 2)

    output += createhiddenform(action="editsource#1",
                                text=text,
                                button="Modify",
                                oai_src_id=oai_src_id,
                                ln=ln,
                                confirm=1)

    if confirm in [1, "1"] and not oai_src_name:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a name for the source.") 
    elif confirm in [1, "1"] and not oai_src_prefix:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a metadata prefix.") 
    elif confirm in [1, "1"] and not oai_src_baseurl:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a base url.") 
    elif confirm in [1, "1"] and not oai_src_frequency:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please choose a frequency of harvesting") 
    elif confirm in [1, "1"] and not oai_src_post:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please choose a postprocess mode") 
    elif confirm in [1, "1"] and (oai_src_post=="h-c" or oai_src_post=="h-c-u") and (not oai_src_config or validatefile(oai_src_config)!=0):
        output += bibharvest_templates.tmpl_print_info(cdslang, "You selected a postprocess mode which involves conversion.") 
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a valid full path to a bibConvert config file or change postprocess mode.") 
    elif oai_src_id > -1 and confirm in [1, "1"]:
        if not oai_src_frequency:
            oai_src_frequency = 0
        if not oai_src_config:
            oai_src_config = "NULL"
        if not oai_src_post:
            oai_src_post = "h"
        res = modify_oai_src(oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_config, oai_src_post, oai_src_sets)
        output += write_outcome(res)

    lnargs = [["ln", ln]]
    output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
    output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs )

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_addsource(oai_src_name=None, oai_src_baseurl='', oai_src_prefix='', oai_src_frequency='', oai_src_lastrun='', oai_src_config='', oai_src_post='', ln=cdslang, confirm=-1, oai_src_sets=[]):
    """creates html form to add a new source"""

    if oai_src_name is None:
        return "No OAI source name selected."

    subtitle = bibharvest_templates.tmpl_draw_subtitle(ln = cdslang, weburl = weburl, title = "add source", subtitle = "Add new OAI source", guideurl = guideurl)
    output  = ""

    if confirm <= -1:
        text = bibharvest_templates.tmpl_print_brs(cdslang, 1)
        text += bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "Enter the base url", name = "oai_src_baseurl", value = oai_src_baseurl)
        output = createhiddenform(action="addsource",
                                  text=text,
                                  ln=ln,
                                  button="Validate",
                                  confirm=0)

    if confirm not in ["-1", -1] and validate(oai_src_baseurl) == 0:
        output += bibharvest_templates.tmpl_output_validate_info(cdslang, 0, str(oai_src_baseurl))
        output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
        text = bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "Source name", name = "oai_src_name", value = oai_src_name)

        metadatas = findMetadataFormats(oai_src_baseurl)
        prefixes = []
        for value in metadatas:
            prefixes.append([value, str(value)])
        text += bibharvest_templates.tmpl_admin_w200_select(ln = cdslang, title = "Metadata prefix", name = "oai_src_prefix", valuenil = "- select prefix -" , values = prefixes, lastval = oai_src_prefix)

        sets = findSets(oai_src_baseurl)
        sets_specs = [set[0] for set in sets]
        sets_names = [set[1] for set in sets]
        sets_labels = [((set[1] and set[0]+' ('+set[1]+')') or set[0]) \
                      for set in sets]
        sets_states = [ ((set[0] in oai_src_sets and 1) or 0) for set in sets]
        text += bibharvest_templates.tmpl_admin_checkboxes(ln = cdslang,
                                                           title = "Sets",
                                                           names = sets_specs,
                                                           labels = sets_labels ,
                                                           states=sets_states)
        
        text += bibharvest_templates.tmpl_admin_w200_select(ln = cdslang, title = "Frequency", name = "oai_src_frequency", valuenil = "- select frequency -" , values = freqs, lastval = oai_src_frequency)
        text += bibharvest_templates.tmpl_admin_w200_select(ln = cdslang, title = "Starting date", name = "oai_src_lastrun", valuenil = "- select a date -" , values = dates, lastval = oai_src_lastrun)
        text += bibharvest_templates.tmpl_admin_w200_select(ln = cdslang, title = "Postprocess", name = "oai_src_post", valuenil = "- select mode -" , values = posts, lastval = oai_src_post)
        text += bibharvest_templates.tmpl_admin_w200_text(ln = cdslang, title = "Bibconvert configuration file", name = "oai_src_config", value = oai_src_config)
        text += bibharvest_templates.tmpl_print_brs(cdslang, 2)

        
        output += createhiddenform(action="addsource#1",
                                   text=text,
                                   button="Add OAI Source",
                                   oai_src_baseurl=oai_src_baseurl,
                                   ln=ln,
                                   confirm=1)

    elif confirm not in ["-1", -1] and validate(oai_src_baseurl) == 1:
        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_output_validate_info(cdslang, 1, str(oai_src_baseurl))
        output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/addsource", title = "Try again", args = [])
        output += bibharvest_templates.tmpl_print_brs(cdslang, 1)
        output += """or"""
        output += bibharvest_templates.tmpl_print_brs(cdslang, 1)
        output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs)

    elif confirm not in ["-1", -1]:
        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_output_error_info(cdslang, str(oai_src_baseurl), str(validate(oai_src_baseurl)))
        output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/addsource", title = "Try again", args = [])
        output += bibharvest_templates.tmpl_print_brs(cdslang, 1)
        output += """or"""
        output += bibharvest_templates.tmpl_print_brs(cdslang, 1)
        output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs)



    if confirm in [1, "1"] and not oai_src_name:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a name for the source.") 
    if confirm in [1, "1"] and not oai_src_prefix:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a metadata prefix.") 
    if confirm in [1, "1"] and not oai_src_frequency:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please choose a frequency of harvesting") 
    if confirm in [1, "1"] and not oai_src_lastrun:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please choose the harvesting starting date")
    if confirm in [1, "1"] and not oai_src_post:
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please choose a postprocess mode") 
    if confirm in [1, "1"] and (oai_src_post=="h-c" or oai_src_post=="h-c-u") and (not oai_src_config or validatefile(oai_src_config)!=0):
        output += bibharvest_templates.tmpl_print_info(cdslang, "You selected a postprocess mode which involves conversion.") 
        output += bibharvest_templates.tmpl_print_info(cdslang, "Please enter a valid full path to a bibConvert config file or change postprocess mode.") 
    elif oai_src_name and confirm in [1, "1"]:
        if not oai_src_frequency:
            oai_src_frequency = 0
        if not oai_src_lastrun:
            oai_src_lastrun = 1        
        if not oai_src_config:
            oai_src_config = "NULL"
        if not oai_src_post:
            oai_src_post = "h"

        res = add_oai_src(oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_lastrun, oai_src_config, oai_src_post, oai_src_sets)
        output += write_outcome(res) 

        lnargs = [["ln", ln]]
        output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
        output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs )

    body = [output]

    return addadminbox(subtitle, body)

def perform_request_delsource(oai_src_id=None, ln=cdslang, callback='yes', confirm=0):
    """creates html form to delete a source
    """

    output = ""
    subtitle = ""
   
    if oai_src_id:
        oai_src = get_oai_src(oai_src_id)
        namesrc = (oai_src[0][1])
        pagetitle = """Delete OAI source: %s""" % namesrc
        subtitle = bibharvest_templates.tmpl_draw_subtitle(ln = cdslang, weburl = weburl, title = "delete source", subtitle = pagetitle, guideurl = guideurl)
        output  = ""

        if confirm in ["0", 0]:
            if oai_src:
                question = """Do you want to delete the OAI source '%s' and all its definitions?""" % namesrc
                text = bibharvest_templates.tmpl_print_info(cdslang, question)
                text += bibharvest_templates.tmpl_print_brs(cdslang, 3)
                output += createhiddenform(action="delsource#5",
                                       text=text,
                                       button="Confirm",
                                       oai_src_id=oai_src_id,
                                       confirm=1)
            else:
                return bibharvest_templates.tmpl_print_info(cdslang, "Source specified does not exist.") 
        elif confirm in ["1", 1]:
            res = delete_oai_src(oai_src_id)
            if res[0] == 1:
                output += bibharvest_templates.tmpl_print_info(cdslang, "Source removed.")
                output += bibharvest_templates.tmpl_print_brs(cdslang, 1)
                output += write_outcome(res)
            else:
                output += write_outcome(res)
                
    lnargs = [["ln", ln]]
    output += bibharvest_templates.tmpl_print_brs(cdslang, 2)
    output += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/bibharvestadmin.py/index", title = "Go back to the OAI sources overview", args = lnargs )

    body = [output]

    return addadminbox(subtitle, body)


##################################################################
### Here the functions to retrieve, modify, delete and add sources
##################################################################

def get_oai_src(oai_src_id=''):
    """Returns a row parameters for a given id"""
    sql = "SELECT id,name,baseurl,metadataprefix,frequency,bibconvertcfgfile,postprocess, setspecs FROM oaiHARVEST"
    try:
        if oai_src_id:
            sql += " WHERE id=%s" % oai_src_id
        sql += " ORDER BY id asc"
        res = run_sql(sql)
        return res
    except StandardError, e:
        return ""

def modify_oai_src(oai_src_id, oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_config, oai_src_post, oai_src_sets=[]):
    """Modifies a row's parameters"""
    
    try:
        sql = "UPDATE oaiHARVEST SET name='%s' WHERE id=%s" % (escape_string(oai_src_name), oai_src_id)
        res = run_sql(sql)
        sql = "UPDATE oaiHARVEST SET baseurl='%s' WHERE id=%s" % (escape_string(oai_src_baseurl), oai_src_id)
        res = run_sql(sql)
        sql = "UPDATE oaiHARVEST SET metadataprefix='%s' WHERE id=%s" % (escape_string(oai_src_prefix), oai_src_id)
        res = run_sql(sql)
        sql = "UPDATE oaiHARVEST SET frequency='%s' WHERE id=%s" % (escape_string(oai_src_frequency), oai_src_id)
        res = run_sql(sql)
        sql = "UPDATE oaiHARVEST SET bibconvertcfgfile='%s' WHERE id=%s" % (escape_string(oai_src_config), oai_src_id)
        res = run_sql(sql)
        sql = "UPDATE oaiHARVEST SET postprocess='%s' WHERE id=%s" % (escape_string(oai_src_post), oai_src_id)
        res = run_sql(sql)
        sql = "UPDATE oaiHARVEST SET setspecs='%s' WHERE id=%s" % (escape_string(' '.join(oai_src_sets)), oai_src_id)
        res = run_sql(sql)
        return (1, "")
    except StandardError, e:
        return (0, e)

def add_oai_src(oai_src_name, oai_src_baseurl, oai_src_prefix, oai_src_frequency, oai_src_lastrun, oai_src_config, oai_src_post, oai_src_sets=[]):
    """Adds a new row to the database with the given parameters"""
    try:
        if oai_src_lastrun in [0, "0"]: lastrun_mode = 'NULL'
        else:
            lastrun_mode = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # lastrun_mode = "'"+lastrun_mode+"'"
        sql = "insert into oaiHARVEST values (0, '%s', '%s', NULL, NULL, '%s', '%s', '%s', '%s', '%s', '%s')" % (escape_string(oai_src_baseurl), escape_string(oai_src_prefix), escape_string(oai_src_config), escape_string(oai_src_name), escape_string(lastrun_mode), escape_string(oai_src_frequency), escape_string(oai_src_post), escape_string(" ".join(oai_src_sets)))
        res = run_sql(sql)
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
        sql = "select count(*) FROM oaiHARVEST"
        res = run_sql(sql)
        return res[0][0]
    except StandardError, e:
        return ""

def get_update_status():
    """Returns a table showing a list of all rows and their LastUpdate status"""
    try:
        sql = "select name,lastrun from oaiHARVEST order by lastrun desc"
        res = run_sql(sql)
        return res
    except StandardError, e:
        return ""

def get_next_schedule():
    """Returns the next scheduled oaiharvestrun tasks"""
    try:
        sql = "select runtime,status from schTASK where proc='oaiharvest' and runtime > now() ORDER by runtime limit 1"
        res = run_sql(sql)
        if len(res)>0:
            return res[0]
        else:
            return ("", "")
    except StandardError, e:
        return ("","")
    

def validate(oai_src_baseurl):
    """This function validates a baseURL by opening its URL and 'greping' for the <OAI-PMH> and <Identify> tags:
     0 = okay
     1 = baseURL non existing
     """
    try:
        url = oai_src_baseurl + "?verb=Identify"
        urllib.urlretrieve(url, tmppath)

        # First check if we have xml oai-pmh output
        grepOUT1 = os.popen('grep -iwc "<OAI-PMH" '+tmppath).read()
        if int(grepOUT1) == 0:
            # No.. we have an http error
            return os.popen('cat '+tmppath).read()

        grepOUT2 = os.popen('grep -iwc "<identify>" '+tmppath).read()
        if int(grepOUT2) > 0:
            #print "Valid!"
            return 0
        else:
            #print "Not valid!"
            return 1
        
    except StandardError, e:
        return 1

def validatefile(oai_src_config):
    """This function checks whether the given path to text file exists or not
     0 = okay
     1 = file non existing
     """

    CFG_BIBCONVERT_XSL_PATH = "%s%sbibconvert%sconfig" % (etcdir,
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
    url = oai_src_baseurl + "?verb=ListMetadataFormats"
    urllib.urlretrieve(url, tmppath)
    formats = []
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
    urllib.urlretrieve(url, tmppath)
    sets = []
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
            sets.append([set_spec, set_name])
        count = count + 1
    return sets
