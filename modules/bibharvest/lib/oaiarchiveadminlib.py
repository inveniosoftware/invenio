## $Id$
## Administrator interface for the OAI repository and archive

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

"""CDS Invenio OAI Repository and Archive Administrator Interface."""

__revision__ = "$Id$"

import sys
import cgi
import re
import Numeric
import os
import string
import ConfigParser
import time
import random
import urllib
import sre
from mod_python import apache

from invenio.config import \
     cdslang, \
     tmpdir, \
     version, \
     weburl
import invenio.access_control_engine as access_manager
from invenio.dbquery import run_sql, escape_string
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.webuser import getUid, get_email

import invenio.template
bibharvest_templates = invenio.template.load('bibharvest')

tmppath = tmpdir + '/oaiarchiveadmin.' + str(os.getpid())
guideurl = "admin/bibharvest/guide.html"

def getnavtrail(previous = ''):
    """Get navtrail"""
    return bibharvest_templates.tmpl_getnavtrail(previous = previous, ln = cdslang)

def perform_request_index(ln=cdslang):
    """OAI archive admin index"""

    titlebar = bibharvest_templates.tmpl_draw_titlebar(ln = cdslang,
                                                       weburl = weburl,
                                                       title = "OAI repository",
                                                       guideurl = guideurl,
                                                       extraname = "add new OAI set",
                                                       extraurl = "admin/bibharvest/oaiarchiveadmin.py/addset")

    header = ['id','setSpec','setName','setCollection','p1','f1','m1','p2','f2','m2','p3','f3','m3','','','']

    oai_set = get_oai_set()

    sets = []
    
    for (id, setSpec, setName, setCollection, setDescription, p1, f1, m1, p2, f2, m2, p3, f3, m3) in oai_set:

        del_request = '<a href="' + weburl + "/" + "admin/bibharvest/oaiarchiveadmin.py/delset?ln=" + ln + "&oai_set_id=" + str(id) + '">delete</a>'
        
        edit_request = '<a href="' + weburl + "/" + "admin/bibharvest/oaiarchiveadmin.py/editset?ln=" + ln + "&oai_set_id=" + str(id) + '">edit</a>'

        sets.append([id, setSpec, setName, setCollection, p1,f1,m1, p2,f2,m2, p3,f3,m3, del_request, edit_request])

    add_request = '<a href="' + weburl + "/" + "admin/bibharvest/oaiarchiveadmin.py/addset?ln=" + ln + '">Add new OAI set definition</a>'
    
    sets.append(['',add_request,'','','','','','','','','','','',''])

    out = transform_tuple(header=header, tuple=sets)
    
    out += "<br><br>"

    return out


def perform_request_addset(oai_set_name='', oai_set_spec='', oai_set_collection='', oai_set_description='', oai_set_definition='', oai_set_reclist='', oai_set_p1='', oai_set_f1='',oai_set_m1='', oai_set_p2='', oai_set_f2='', oai_set_m2='', oai_set_p3='', oai_set_f3='', oai_set_m3='', ln=cdslang, func=0):
    """add a new OAI set"""

    out  = ""

    if func in ["0", 0]:
        text   = input_form(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, ln=cdslang)
        out = createform(action="addset",
                                  text=text,
                                  ln=ln,
                                  button="Add new OAI set definition line",
                                  func=1)
        lnargs = [["ln", ln]]

    if func in ["1", 1]:
        out += "<br><br>"

        res = add_oai_set(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3)


        lnargs = [["ln", ln]]
        out += "<br><br>"
        out += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/oaiarchiveadmin.py/index", title = "Return to main selection", args = lnargs)

    try:
        body = [out, extra]
    except NameError:
        body = [out]

    return nice_box("", body)


def perform_request_editset(oai_set_id=None, oai_set_name='', oai_set_spec='', oai_set_collection='', oai_set_description='', oai_set_definition='', oai_set_reclist='', oai_set_p1='', oai_set_f1='', oai_set_m1='', oai_set_p2='', oai_set_f2='', oai_set_m2='', oai_set_p3='', oai_set_f3='', oai_set_m3='', ln=cdslang, func=0):
    """creates html form to edit an OAI set."""

    if oai_set_id is None:
        return "No OAI set ID selected."

    out  = ""

    if func in [0, "0"]:

        oai_set = get_oai_set(oai_set_id)
        oai_set_spec = oai_set[0][1]
        oai_set_name = oai_set[0][2]
        oai_set_collection  = oai_set[0][3]
        oai_set_description = oai_set[0][4]
        oai_set_definition  = ''
        oai_set_reclist     = ''
        oai_set_p1 = oai_set[0][5]
        oai_set_f1 = oai_set[0][6]
        oai_set_m1 = oai_set[0][7]
        oai_set_p2 = oai_set[0][8]
        oai_set_f2 = oai_set[0][9]
        oai_set_m2 = oai_set[0][10]
        oai_set_p3 = oai_set[0][11]
        oai_set_f3 = oai_set[0][12]
        oai_set_m3 = oai_set[0][13]

        text = input_form(oai_set_name,
                          oai_set_spec,
                          oai_set_collection,
                          oai_set_description,
                          oai_set_definition,
                          oai_set_reclist,
                          oai_set_p1,
                          oai_set_f1,
                          oai_set_m1,
                          oai_set_p2,
                          oai_set_f2,
                          oai_set_m2,
                          oai_set_p3,
                          oai_set_f3,
                          oai_set_m3,
                          ln=cdslang)

        out += extended_input_form(action="editset",
                                text=text,
                                button="Modify",
                                oai_set_id=oai_set_id,
                                ln=ln,
                                func=1)

    if func in [1, "1"]:
        res = modify_oai_set(oai_set_id,
                             oai_set_name,
                             oai_set_spec,
                             oai_set_collection,
                             oai_set_description,
                             oai_set_p1,
                             oai_set_f1,
                             oai_set_m1,
                             oai_set_p2,
                             oai_set_f2,
                             oai_set_m2,
                             oai_set_p3,
                             oai_set_f3,
                             oai_set_m3)

    lnargs = [["ln", ln]]
    out += "<br><br>"
    out += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/oaiarchiveadmin.py/index", title = "Return to main selection", args = lnargs)

    try:
        body = [out, extra]
    except NameError:
        body = [out]

    return nice_box("", body)


def perform_request_delset(oai_set_id=None, ln=cdslang, callback='yes', func=0):
    """creates html form to delete an OAI set"""

    out = ""

    if oai_set_id:
        oai_set = get_oai_set(oai_set_id)
        nameset = (oai_set[0][1])
        pagetitle = """Delete OAI set: %s""" % nameset

        if func in ["0", 0]:

            oai_set = get_oai_set(oai_set_id)
            oai_set_spec = oai_set[0][1]
            oai_set_name = oai_set[0][2]
            oai_set_collection = oai_set[0][3]
            oai_set_description = oai_set[0][4]
            oai_set_definition = ''
            oai_set_reclist = ''
            oai_set_p1 = oai_set[0][5]
            oai_set_f1 = oai_set[0][6] 
            oai_set_m1 = oai_set[0][7] 
            oai_set_p2 = oai_set[0][8] 
            oai_set_f2 = oai_set[0][9] 
            oai_set_m2 = oai_set[0][10]
            oai_set_p3 = oai_set[0][11]
            oai_set_f3 = oai_set[0][12]
            oai_set_m3 = oai_set[0][13]

            if oai_set:
                question = """Do you want to delete the OAI definition #%s?""" % oai_set_id
                text = bibharvest_templates.tmpl_print_info(cdslang, question)
                text += "<br><br><br>"
                text += pagebody_text("%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s" % (oai_set_spec,
                                                                               oai_set_name,
                                                                               oai_set_collection,
                                                                               oai_set_p1,
                                                                               oai_set_f1,
                                                                               oai_set_m1,
                                                                               oai_set_p2,
                                                                               oai_set_f2,
                                                                               oai_set_m2,
                                                                               oai_set_p3,
                                                                               oai_set_f3,
                                                                               oai_set_m3))

                out += createform(action="delset",
                                       text=text,
                                       button="Delete",
                                       oai_set_id=oai_set_id,
                                       func=1)
            else:
                return bibharvest_templates.tmpl_print_info(cdslang, "OAI set does not exist.")
        elif func in ["1", 1]:
            res = delete_oai_set(oai_set_id)
            if res[0] == 1:
                out += bibharvest_templates.tmpl_print_info(cdslang, "OAI set definition #%s deleted." % oai_set_id)
                out += "<br>"
            else:
                pass
                
    lnargs = [["ln", ln]]
    out += "<br><br>"
    out += bibharvest_templates.tmpl_link_with_args(ln = cdslang, weburl = weburl, funcurl = "admin/bibharvest/oaiarchiveadmin.py/index", title = "Return to main selection", args = lnargs )

    try:
        body = [out, extra]
    except NameError:
        body = [out]

    return nice_box("", body)

def get_oai_set(id=''):
    """Returns a row parameters for a given id"""
    sql = "SELECT id, setSpec, setName, setCollection, setDescription, p1,f1,m1, p2,f2,m2, p3,f3,m3 FROM oaiARCHIVE"
    try:
        if id:
            sql += " WHERE id=%s" % id
        sql += " ORDER BY setSpec asc"
        res = run_sql(sql)
        return res
    except StandardError, e:
        return ""

def modify_oai_set(oai_set_id, oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3):
    """Modifies a row's parameters"""
    
    try:
        sql = "UPDATE oaiARCHIVE SET setName='%s' WHERE id=%s" % (escape_string(oai_set_name), oai_set_id)
        res = run_sql(sql)
        sql = "UPDATE oaiARCHIVE SET setSpec='%s' WHERE id=%s" % (escape_string(oai_set_spec), oai_set_id)
        res = run_sql(sql)
        sql = "UPDATE oaiARCHIVE SET setCollection='%s' WHERE id=%s" % (escape_string(oai_set_collection), oai_set_id)
        res = run_sql(sql)
        sql = "UPDATE oaiARCHIVE SET setDescription='%s' WHERE id=%s" % (escape_string(oai_set_description), oai_set_id)
        res = run_sql(sql)
        sql = "UPDATE oaiARCHIVE SET p1='%s' WHERE id=%s" % (escape_string(oai_set_p1), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET f1='%s' WHERE id=%s" % (escape_string(oai_set_f1), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET m1='%s' WHERE id=%s" % (escape_string(oai_set_m1), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET p2='%s' WHERE id=%s" % (escape_string(oai_set_p2), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET f2='%s' WHERE id=%s" % (escape_string(oai_set_f2), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET m2='%s' WHERE id=%s" % (escape_string(oai_set_m2), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET p3='%s' WHERE id=%s" % (escape_string(oai_set_p3), oai_set_id)
        res = run_sql(sql)                                                              
        sql = "UPDATE oaiARCHIVE SET f3='%s' WHERE id=%s" % (escape_string(oai_set_f3), oai_set_id)
        res = run_sql(sql)                                                                                 
        sql = "UPDATE oaiARCHIVE SET m3='%s' WHERE id=%s" % (escape_string(oai_set_m3), oai_set_id)
        res = run_sql(sql)
        return (1, "")
    except StandardError, e:
        return (0, e)

def add_oai_set(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3):
    """Add a definition into the OAI archive"""
    try:
        sql = "insert into oaiARCHIVE values (0, '%s', '%s', '%s', '%s', '%s', NULL, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
            escape_string(oai_set_name), \
            escape_string(oai_set_spec), \
            escape_string(oai_set_collection), \
            escape_string(oai_set_description), \
            escape_string(oai_set_definition), \
            escape_string(oai_set_p1), \
            escape_string(oai_set_f1), \
            escape_string(oai_set_m1), \
            escape_string(oai_set_p2), \
            escape_string(oai_set_f2), \
            escape_string(oai_set_m2), \
            escape_string(oai_set_p3), \
            escape_string(oai_set_f3), \
            escape_string(oai_set_m3)  \
            )
            
        res = run_sql(sql)
        return (1, "")
    except StandardError, e:
        return (0, e)
    
def delete_oai_set(oai_set_id):
    """"""

    try:
        res = run_sql("DELETE FROM oaiARCHIVE WHERE id=%s" % oai_set_id)
        return (1, "")
    except StandardError, e:
        return (0, e)

def drop_down_menu(boxname, list=['Select', 'selected', 'select']):
    """"""

    text = "<select name=\"%s\">" % boxname
    
    for (value, selectedflag, txt) in list:
        text += "<option value=\""
        text += "%s\"" % value
        text += " selected=\"%s\">" % selectedflag
        text += "%s" % txt
    text += "</select>"
    return text

def create_drop_down_menu(sql):
    """"""
    list = []

    res = run_sql(sql)
    for item in res:
        tmp_list = []
        tmp_list.append(item)
        tmp_list.append("")
        tmp_list.append(item)
        list.append(tmp_list)
    return list

def createform(action="", text="", button="func", cnfrm='', **hidden):
    """"""
    out  = '<form action="%s" method="POST">\n' % (action, )

    out += text
    if cnfrm:
        out += ' <input type="checkbox" name="func" value="1"/>' 
    for key in hidden.keys():
        if type(hidden[key]) is list:
            for value in hidden[key]:
                out += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, value)
        else:
            out += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, hidden[key])

    out += ' <input class="adminbutton" type="submit" value="%s"/>\n' % (button, )
    out += '</form>\n'

    return out


def oai_table(ln=cdslang):
    """"""
    
    titlebar = bibharvest_templates.tmpl_draw_titlebar(ln = cdslang, weburl = weburl, title = "OAI repository", guideurl = guideurl, extraname = "add new OAI set" , extraurl = "admin/bibharvest/oaiarchiveadmin.py/addset" )
    header = ['id', 'setSpec', 'setName', 'setCollection', 'p1', 'f1', 'm1', 'p2', 'f2', 'm2', 'p3', 'f3', 'm3', '', '']
    oai_set = get_oai_set()

    sets = []
    for (id, setSpec, setName, setCollection, setDescription, p1,f1,m1, p2,f2,m2, p3,f3,m3) in oai_set:
        del_request = '<a href="' + weburl + "/" + "admin/bibharvest/oaiarchiveadmin.py/delset?ln=" + ln + "&oai_set_id=" + str(id) + '">delete</a>'

        sets.append([id, setSpec, setName, setCollection, p1,f1,m1, p2,f2,m2, p3,f3,m3, del_request])

    add_request = '<a href="' + weburl + "/" + "admin/bibharvest/oaiarchiveadmin.py/addset?ln=" + ln + '">Add new OAI set definition</a>'
    sets.append(['',add_request,'','','','','','','','','','','',''])
    
    out = transform_tuple(header=header, tuple=sets)
    out += "<br><br>"
    
    return out
    
def input_text(ln, title, name, value):
    """"""
    text = """<table><tr><td width=100><span class="adminlabel">%s</span></td>""" % title
    text += """<td align=left><input class="admin_w200" type="text" name="%s" value="%s" /></td></tr></table>""" % (cgi.escape(name,1), cgi.escape(value, 1))  
    return text

def pagebody_text(title):
    """"""
    text = """<span class="admintd">%s</span>""" % title
    return text

def bar_text(title):
    """"""
    text = """<span class="adminlabel">%s</span>""" % title
    return text

def input_form(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, ln=cdslang):
    """"""
    
    modes = {
    'r' : 'Regular Expression',
    'a' : 'All of the words',
    'y' : 'Any of the words',
    'e' : 'Exact phrase',
    'p' : 'Partial phrase'
        }

    mode_dropdown = [['r','',modes['r']],
                     ['e','',modes['e']],
                     ['p','',modes['p']],
                     ['a','',modes['a']],
                     ['y','',modes['y']],
                     ['','','']]

    text = "<br>"
    text += "<table><tr><td>"
    text += input_text(ln = cdslang, title = "OAI Set spec:", name = "oai_set_spec", value = oai_set_spec)
    text += "</td></tr><tr><td>"
    text += input_text(ln = cdslang, title = "OAI Set name:", name = "oai_set_name", value = oai_set_name)

    text += "</td></tr><tr><td>"
#    text += input_text(ln = cdslang, title = "OAI Set description", name = "oai_set_description", value = oai_set_description)
    text += "</td><td colspan=2>"

    menu = create_drop_down_menu("SELECT distinct(name) from collection")
    menu.append(['','',''])

    if (oai_set_collection):
        menu.append([oai_set_collection,'selected',oai_set_collection])
    else:
        menu.append(['','selected','Collection'])
        

    text += drop_down_menu("oai_set_collection", menu)
    
    text += "</td></tr><tr><td>"
    text += input_text(ln = cdslang, title = "Phrase:", name = "oai_set_p1", value = oai_set_p1)
    text += "</td><td>"

    fields = create_drop_down_menu("SELECT distinct(code) from field")
    fields.append(['','',''])
    if (oai_set_f1):
        fields.append([oai_set_f1,'selected',oai_set_f1])
    else:    
        fields.append(['','selected','Field'])

    if (oai_set_m1):
        mode_dropdown.append([oai_set_m1,'selected',modes[oai_set_m1]])
    else:    
        mode_dropdown.append(['','selected','Mode'])

    text += drop_down_menu("oai_set_f1", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m1", mode_dropdown)
    
    text += "</td><td>"
    text += bar_text(" and")
    text += "</td></tr><tr><td>"
    text += input_text(ln = cdslang, title = "Phrase:", name = "oai_set_p2", value = oai_set_p2)
    text += "</td><td>"

    fields = create_drop_down_menu("SELECT distinct(code) from field")
    fields.append(['','',''])
    if (oai_set_f2):
        fields.append([oai_set_f2,'selected',oai_set_f2])
    else:
        fields.append(['','selected','Field'])
    if (oai_set_m2):
        mode_dropdown.append([oai_set_m2,'selected',modes[oai_set_m2]])
    else:
        mode_dropdown.append(['','selected','Mode'])
    
    text += drop_down_menu("oai_set_f2", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m2", mode_dropdown)

    text += "</td><td>"
    text += bar_text(" and")
    text += "</td></tr><tr><td>"
    text += input_text(ln = cdslang, title = "Phrase:", name = "oai_set_p3", value = oai_set_p3)
    text += "</td><td>"

    fields = create_drop_down_menu("SELECT distinct(code) from field")
    fields.append(['','',''])
    if (oai_set_f3):
        fields.append([oai_set_f3,'selected',oai_set_f3])
    else:
        fields.append(['','selected','Field'])
    if (oai_set_m3):
        mode_dropdown.append([oai_set_m3,'selected',modes[oai_set_m3]])
    else:
        mode_dropdown.append(['','selected','Mode'])

    text += drop_down_menu("oai_set_f3", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m3", mode_dropdown)
                           
    text += "</td></tr></table>"

    return text

def check_user(uid, role, adminarea=2, authorized=0):
    """"""
    (auth_code, auth_message) = access_manager.acc_authorize_action(uid, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)

def transform_tuple(header=[], tuple=[], start='', end='', extracolumn=''):
    """"""

    align = []
    try:
        firstrow = tuple[0]
    
        if type(firstrow) in [int, long]: 
            align = ['admintdright']
        elif type(firstrow) in [str, dict]:
            align = ['admintdleft']
        else:
            for item in firstrow:
                if type(item) is int:
                    align.append('admintdright')
                else:
                    align.append('admintdleft')
    except IndexError:
        firstrow = []
                        
    tblstr = ''
    for h in header + ['']:
        tblstr += '  <th class="adminheader">%s</th>\n' % (h, )
    if tblstr: tblstr = ' <tr>\n%s\n </tr>\n' % (tblstr, )
    
    tblstr = start + '<table class="admin_wvar_nomargin">\n' + tblstr
    
    try: 
        extra = '<tr>'

        if type(firstrow) not in [int, long, str, dict]:
            for i in range(len(firstrow)): extra += '<td class="%s">%s</td>\n' % (align[i], firstrow[i])
        else:
            extra += '  <td class="%s">%s</td>\n' % (align[0], firstrow)
        extra += '<td rowspan="%s" style="vertical-align: top">\n%s\n</td>\n</tr>\n' % (len(tuple), extracolumn)
    except IndexError:
        extra = ''
    tblstr += extra

    for row in tuple[1:]:
        tblstr += ' <tr>\n'
        if type(row) not in [int, long, str, dict]:
            for i in range(len(row)): tblstr += '<td class="%s">%s</td>\n' % (align[i], row[i])
        else:
            tblstr += '  <td class="%s">%s</td>\n' % (align[0], row)
        tblstr += ' </tr> \n'

    tblstr += '</table> \n '
    tblstr += end
    
    return tblstr

def nice_box(header='', datalist=[], cls="admin_wvar"):
    """"""

    if len(datalist) == 1: per = '100'
    else: per = '75'
    
    out  = '<table class="%s" ' % (cls, ) + 'width="95%">\n'
    out += """
     <thead>
      <tr>
       <th class="adminheaderleft" colspan="%s">%s</th>
      </tr>
     </thead>
     <tbody>
    """ % (len(datalist), header)

    out += '      <tr>\n'

    out += """
    <td style="vertical-align: top; margin-top: 5px; width: %s;">
     %s 
    </td>
    """ % (per+'%', datalist[0])

    if len(datalist) > 1:
        out += """
        <td style="vertical-align: top; margin-top: 5px; width: %s;">
         %s 
        </td>
        """ % ('25%', datalist[1])
        
    out += '      </tr>\n'
    
    out += """
     </tbody>
    </table>
    """

    return out

def extended_input_form(action="", text="", button="func", cnfrm='', **hidden):
    """"""
    
    out  = '<form action="%s" method="POST">\n' % (action, )
    out += '<table>\n<tr><td style="vertical-align: top">'
    out += text
    if cnfrm:
        out += ' <input type="checkbox" name="func" value="1"/>' 
    for key in hidden.keys():
        if type(hidden[key]) is list:
            for value in hidden[key]:
                out += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, value)
        else:
            out += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, hidden[key])
    out += '</td><td style="vertical-align: bottom">'
    out += ' <input class="adminbutton" type="submit" value="%s"/>\n' % (button, )
    out += '</td></tr></table>'
    out += '</form>\n'

    return out
