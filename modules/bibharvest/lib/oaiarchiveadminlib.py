## $Id$
## Administrator interface for the OAI repository and archive

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

"""CDS Invenio OAI Repository and Archive Administrator Interface."""

__revision__ = "$Id$"

import sys
import cgi
import re
import os
import string
import ConfigParser
import time
import random
import urllib


from invenio.config import \
     CFG_SITE_LANG, \
     CFG_TMPDIR, \
     CFG_VERSION, \
     CFG_SITE_URL
import invenio.access_control_engine as access_manager
from invenio.dbquery import run_sql
from invenio.webpage import page, pageheaderonly, pagefooteronly
from invenio.webuser import getUid, get_email
from invenio.oaiarchive_engine import parse_set_definition
import invenio.template
bibharvest_templates = invenio.template.load('bibharvest')

tmppath = CFG_TMPDIR + '/oaiarchiveadmin.' + str(os.getpid())
guideurl = "help/admin/bibharvest-admin-guide"

def getnavtrail(previous = ''):
    """Get navtrail"""
    return bibharvest_templates.tmpl_getnavtrail(previous = previous, ln = CFG_SITE_LANG)

def perform_request_index(ln=CFG_SITE_LANG):
    """OAI archive admin index"""

    out = '''<p>Define below the sets to expose through the OAI harvesting
    protocol. <br /> You will have to run the
    <a href="%(siteurl)s/help/admin/bibharvest-admin-guide#3.2"><code>oaiarchive</code></a>
    utility to apply the settings you have defined here.</p>''' % {'siteurl': CFG_SITE_URL}

    titlebar = bibharvest_templates.tmpl_draw_titlebar(ln = CFG_SITE_LANG,
                                                       title = "OAI repository",
                                                       guideurl = guideurl,
                                                       extraname = "add new OAI set",
                                                       extraurl = "admin/bibharvest/oaiarchiveadmin.py/addset")

    header = ['id','setSpec','setName','setCollection','p1','f1','m1', 'op1', 'p2','f2','m2', 'op2','p3','f3','m3','','']

    oai_set = get_oai_set()
    sets = []

    for (id, setSpec, setName, setCollection, setDescription, p1, f1, m1, p2, f2, m2, p3, f3, m3, op1, op2) in oai_set:

        del_request = '<a href="' + CFG_SITE_URL + "/" + "admin/bibharvest/oaiarchiveadmin.py/delset?ln=" + ln + "&amp;oai_set_id=" + str(id) + '">delete</a>'

        edit_request = '<a href="' + CFG_SITE_URL + "/" + "admin/bibharvest/oaiarchiveadmin.py/editset?ln=" + ln + "&amp;oai_set_id=" + str(id) + '">edit</a>'

        sets.append([id, setSpec, setName, setCollection, p1,f1,m1, op1,  p2,f2,m2, op2,  p3,f3,m3, del_request, edit_request])

    add_request = '<a href="' + CFG_SITE_URL + "/" + "admin/bibharvest/oaiarchiveadmin.py/addset?ln=" + ln + '">Add new OAI set definition</a>'

    sets.append(['',add_request,'','','','','','','','','','','','','','',''])

    out += transform_tuple(header=header, tuple=sets)

    out += "<br /><br />"

    return out


def perform_request_addset(oai_set_name='', oai_set_spec='', oai_set_collection='', oai_set_description='', oai_set_definition='', oai_set_reclist='', oai_set_p1='', oai_set_f1='',oai_set_m1='', oai_set_p2='', oai_set_f2='', oai_set_m2='', oai_set_p3='', oai_set_f3='', oai_set_m3='', oai_set_op1='a', oai_set_op2='a', ln=CFG_SITE_LANG, func=0):
    """add a new OAI set"""

    out  = ""

    if func in ["0", 0]:
        text   = input_form(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2, ln=CFG_SITE_LANG)
        out = createform(action="addset",
                         text=text,
                         ln=ln,
                         button="Add new OAI set definition line",
                         func=1)
        lnargs = [["ln", ln]]

    if func in ["1", 1]:
        out += "<br />"

        res = add_oai_set(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2)
        if res[0] == 1:
            out += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG,
                                                        "OAI set definition %s added." % oai_set_name)
            out += "<br />"

        lnargs = [["ln", ln]]
        out += "<br /><br />"
        out += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/oaiarchiveadmin.py/index", title = "Return to main selection", args = lnargs)

    body = [out]

    return nice_box("", body)


def perform_request_editset(oai_set_id=None, oai_set_name='', oai_set_spec='', oai_set_collection='', oai_set_description='', oai_set_definition='', oai_set_reclist='', oai_set_p1='', oai_set_f1='', oai_set_m1='', oai_set_p2='', oai_set_f2='', oai_set_m2='', oai_set_p3='', oai_set_f3='', oai_set_m3='', oai_set_op1='a', oai_set_op2='a', ln=CFG_SITE_LANG, func=0):
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
        oai_set_op1 = oai_set[0][14]
        oai_set_op2 = oai_set[0][15]

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
                          oai_set_op1,
                          oai_set_op2,
                          ln=CFG_SITE_LANG)

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
                             oai_set_m3,
                             oai_set_op1,
                             oai_set_op2)
        out += "<br />"
        if res[0] == 1:
            out += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG,
                                                        "OAI set definition #%s edited." % oai_set_id)
            out += "<br />"
        else:
            out += bibharvest_templates.tmpl_print_warning(CFG_SITE_LANG,
                                                           "A problem was encountered: <br/>" + cgi.escape(res[1]))
            out += "<br />"

    lnargs = [["ln", ln]]
    out += "<br />"

    out += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/oaiarchiveadmin.py/index", title = "Return to main selection", args = lnargs)

    body = [out]

    return nice_box("", body)


def perform_request_delset(oai_set_id=None, ln=CFG_SITE_LANG, callback='yes', func=0):
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
            oai_set_op1 = oai_set[0][14]
            oai_set_op2 = oai_set[0][15]

            if oai_set:
                question = """Do you want to delete the OAI definition #%s?""" % oai_set_id
                text = bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, question)
                text += "<br /><br /><br />"
                text += pagebody_text("%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s" % (oai_set_spec,
                                                                               oai_set_name,
                                                                               oai_set_collection,
                                                                               oai_set_p1,
                                                                               oai_set_f1,
                                                                               oai_set_m1,
                                                                               oai_set_op1,
                                                                               oai_set_p2,
                                                                               oai_set_f2,
                                                                               oai_set_m2,
                                                                               oai_set_op2,
                                                                               oai_set_p3,
                                                                               oai_set_f3,
                                                                               oai_set_m3))

                out += createform(action="delset",
                                       text=text,
                                       button="Delete",
                                       oai_set_id=oai_set_id,
                                       func=1)
            else:
                return bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "OAI set does not exist.")
        elif func in ["1", 1]:
            res = delete_oai_set(oai_set_id)
            if res[0] == 1:
                out += bibharvest_templates.tmpl_print_info(CFG_SITE_LANG, "OAI set definition #%s deleted." % oai_set_id)
                out += "<br />"
            else:
                pass

    lnargs = [["ln", ln]]
    out += "<br /><br />"
    out += bibharvest_templates.tmpl_link_with_args(ln = CFG_SITE_LANG, funcurl = "admin/bibharvest/oaiarchiveadmin.py/index", title = "Return to main selection", args = lnargs )

    body = [out]

    return nice_box("", body)

def get_oai_set(id=''):
    """Returns a row parameters for a given id"""
    sets = []
    sql = "SELECT id, setSpec, setName, setCollection, setDescription, p1,f1,m1, p2,f2,m2, p3,f3,m3, setDefinition FROM oaiARCHIVE"
    try:
        if id:
            sql += " WHERE id=%s" % id
        sql += " ORDER BY setSpec asc"
        res = run_sql(sql)
        for row in res:
            set = ['']*16
            set[0] = row[0]
            set[1] = row[1]
            set[2] = row[2]
            params = parse_set_definition(row[14])
            set[3] = params.get('c', '')
            set[5] = params.get('p1', '')
            set[6] = params.get('f1', '')
            set[7] = params.get('m1', '')
            set[8] = params.get('p2', '')
            set[9] = params.get('f2', '')
            set[10] = params.get('m2', '')
            set[11] = params.get('p3', '')
            set[12] = params.get('f3', '')
            set[13] = params.get('m3', '')
            set[14] = params.get('op1', 'a')
            set[15] = params.get('op2', 'a')
            sets.append(set)
        return sets
    except StandardError, e:
        return str(e)

def modify_oai_set(oai_set_id, oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2):
    """Modifies a row's parameters"""

    try:
        set_definition = 'c=' + oai_set_collection + ';' + \
                         'p1=' + oai_set_p1  + ';' + \
                         'f1=' + oai_set_f1  + ';' + \
                         'm1=' + oai_set_m1  + ';' + \
                         'op1='+ oai_set_op1 + ';' + \
                         'p2=' + oai_set_p2  + ';' + \
                         'f2=' + oai_set_f2  + ';' + \
                         'm2=' + oai_set_m2  + ';' + \
                         'op2='+ oai_set_op2 + ';' + \
                         'p3=' + oai_set_p3  + ';' + \
                         'f3=' + oai_set_f3  + ';' + \
                         'm3=' + oai_set_m3  + ';'
        res = run_sql("""UPDATE oaiARCHIVE SET
                            setName=%s,
                            setSpec=%s,
                            setCollection=%s,
                            setDescription=%s,
                            setDefinition=%s,
                            p1=%s,
                            f1=%s,
                            m1=%s,
                            p2=%s,
                            f2=%s,
                            m2=%s,
                            p3=%s,
                            f3=%s,
                            m3=%s
                         WHERE id=%s""",
                      (oai_set_name,
                       oai_set_spec,
                       oai_set_collection,
                       oai_set_description,
                       set_definition,
                       oai_set_p1,
                       oai_set_f1,
                       oai_set_m1,
                       oai_set_p2,
                       oai_set_f2,
                       oai_set_m2,
                       oai_set_p3,
                       oai_set_f3,
                       oai_set_m3,
                       oai_set_id))

        return (1, "")
    except StandardError, e:
        return (0, str(e))

def add_oai_set(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2):
    """Add a definition into the OAI archive"""
    try:
        set_definition = 'c=' + oai_set_collection + ';' + \
                         'p1=' + oai_set_p1  + ';' + \
                         'f1=' + oai_set_f1  + ';' + \
                         'm1=' + oai_set_m1  + ';' + \
                         'op1='+ oai_set_op1 + ';' + \
                         'p2=' + oai_set_p2  + ';' + \
                         'f2=' + oai_set_f2  + ';' + \
                         'm2=' + oai_set_m2  + ';' + \
                         'op2='+ oai_set_op2 + ';' + \
                         'p3=' + oai_set_p3  + ';' + \
                         'f3=' + oai_set_f3  + ';' + \
                         'm3=' + oai_set_m3  + ';'

        res = run_sql("""INSERT INTO oaiARCHIVE (id, setName, setSpec,
                           setCollection, setDescription, setDefinition,
                           setRecList, p1, f1, m1, p2, f2, m2, p3, f3, m3)
                         VALUES (0, %s, %s, %s, %s, %s, NULL, %s, %s, %s,
                           %s, %s, %s, %s, %s, %s)""",
                      (oai_set_name, oai_set_spec, oai_set_collection,
                       oai_set_description, set_definition, oai_set_p1,
                       oai_set_f1, oai_set_m1, oai_set_p2, oai_set_f2,
                       oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3))
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
        if selectedflag:
            text += ' selected="selected"'
        text += ">%s</option>" % txt
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
    out  = '<form action="%s" method="post">\n' % (action, )

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

def input_text(ln, title, name, value):
    """"""
    if name is None:
        name = ""
    if value is None:
        value = ""
    text = """<table><tr><td width="100%%"><span class="adminlabel">%s</span></td>""" % title
    text += """<td align="left"><input class="admin_w200" type="text" name="%s" value="%s" /></td></tr></table>""" % (cgi.escape(name,1), cgi.escape(value, 1))
    return text

def pagebody_text(title):
    """"""
    text = """<span class="admintd">%s</span>""" % title
    return text

def bar_text(title):
    """"""
    text = """<span class="adminlabel">%s</span>""" % title
    return text

def input_form(oai_set_name, oai_set_spec, oai_set_collection, oai_set_description, oai_set_definition, oai_set_reclist, oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2, ln=CFG_SITE_LANG):
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

    operators = {
    'a' : 'AND',
    'o' : 'OR',
    'n' : 'AND NOT',
        }

    mode_operators_1 = [['a','',operators['a']],
                        ['o','',operators['o']],
                        ['n','',operators['n']],
                        ['a','','']]

    mode_operators_2 = [['a','',operators['a']],
                        ['o','',operators['o']],
                        ['n','',operators['n']],
                        ['a','','']]

    text = "<br />"
    text += "<table><tr><td>"
    text += input_text(ln = CFG_SITE_LANG, title = "OAI Set spec:", name = "oai_set_spec", value = oai_set_spec)
    text += "</td></tr><tr><td>"
    text += input_text(ln = CFG_SITE_LANG, title = "OAI Set name:", name = "oai_set_name", value = oai_set_name)

    text += "</td></tr><tr><td>&nbsp;</td></tr><tr><td>"
#    text += input_text(ln = CFG_SITE_LANG, title = "OAI Set description", name = "oai_set_description", value = oai_set_description)

    #text += "</td><td colspan=2>"

    #menu = create_drop_down_menu("SELECT distinct(name) from collection")
    #menu.append(['','',''])

    #if (oai_set_collection):
    #    menu.append([oai_set_collection,'selected',oai_set_collection])
    #else:
    #    menu.append(['','selected','Collection'])

    text += input_text(ln = CFG_SITE_LANG, title = "Collection(s):", name="oai_set_collection", value=oai_set_collection)

    #text += drop_down_menu("oai_set_collection", menu)

    text += '</td><td colspan="3"><small>Eg: <code>Published Articles, Preprints, Theses</code></small></td></tr><tr><td>'
    text += input_text(ln = CFG_SITE_LANG, title = "Phrase:", name = "oai_set_p1", value = oai_set_p1)
    text += "</td><td>"

    fields = create_drop_down_menu("SELECT distinct(code) from field")
    fields.append(['','',''])
    if (oai_set_f1):
        fields.append([oai_set_f1,'selected',oai_set_f1])
    else:
        fields.append(['','selected','Field'])

    if (oai_set_m1):
        mode_dropdown_m1 = [[oai_set_m1, 'selected', modes[oai_set_m1]]]
    else:
        mode_dropdown_m1 = [['', 'selected', 'Mode']]

    text += drop_down_menu("oai_set_f1", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m1", mode_dropdown + mode_dropdown_m1)

    text += "</td><td>"
    if (oai_set_op1):
        mode_operators_1.append([oai_set_op1,'selected',operators[oai_set_op1]])
    else:
        mode_operators_1.append(['','selected','Operators'])
    text += drop_down_menu("oai_set_op1", mode_operators_1)
    text += "</td></tr><tr><td>"
    text += input_text(ln = CFG_SITE_LANG, title = "Phrase:", name = "oai_set_p2", value = oai_set_p2)
    text += "</td><td>"

    fields = create_drop_down_menu("SELECT distinct(code) from field")
    fields.append(['','',''])
    if (oai_set_f2):
        fields.append([oai_set_f2,'selected',oai_set_f2])
    else:
        fields.append(['','selected','Field'])
    if (oai_set_m2):
        mode_dropdown_m2 = [[oai_set_m2, 'selected', modes[oai_set_m2]]]
    else:
        mode_dropdown_m2 = [['', 'selected', 'Mode']]

    text += drop_down_menu("oai_set_f2", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m2", mode_dropdown + mode_dropdown_m2)

    text += "</td><td>"
    if (oai_set_op2):
        mode_operators_2.append([oai_set_op2,'selected',operators[oai_set_op2]])
    else:
        mode_operators_2.append(['','selected','Operators'])
    text += drop_down_menu("oai_set_op2", mode_operators_2)
    text += "</td></tr><tr><td>"
    text += input_text(ln = CFG_SITE_LANG, title = "Phrase:", name = "oai_set_p3", value = oai_set_p3)
    text += "</td><td>"

    fields = create_drop_down_menu("SELECT distinct(code) from field")
    fields.append(['','',''])
    if (oai_set_f3):
        fields.append([oai_set_f3,'selected',oai_set_f3])
    else:
        fields.append(['','selected','Field'])
    if (oai_set_m3):
        mode_dropdown_m3 = [[oai_set_m3,  'selected', modes[oai_set_m3]]]
    else:
        mode_dropdown_m3 = [['', 'selected', 'Mode']]

    text += drop_down_menu("oai_set_f3", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m3", mode_dropdown + mode_dropdown_m3)

    text += "</td></tr></table>"

    return text

def check_user(req, role, adminarea=2, authorized=0):
    """"""
    (auth_code, auth_message) = access_manager.acc_authorize_action(req, role)
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
    for h in header:
        tblstr += '  <th class="adminheader">%s</th>\n' % (h, )
    if tblstr: tblstr = ' <tr>\n%s\n </tr>\n' % (tblstr, )

    tblstr = start + '<table class="admin_wvar_nomargin">\n' + tblstr

    try:
        extra = '<tr>'

        if type(firstrow) not in [int, long, str, dict]:
            for i in range(len(firstrow)): extra += '<td class="%s">%s</td>\n' % (align[i], firstrow[i])
        else:
            extra += '  <td class="%s">%s</td>\n' % (align[0], firstrow)
        #extra += '<td rowspan="%s" style="vertical-align: top">\n%s\n</td>\n</tr>\n' % (len(tuple), extracolumn)
        extra += '</tr>\n'
    except IndexError:
        extra = ''
    tblstr += extra

    j = 1
    for row in tuple[1:]:
        style = ''
        if j % 2:
            style = ' style="background-color: rgb(235, 247, 255);"'
        j += 1
        tblstr += ' <tr%s>\n' % style
        if type(row) not in [int, long, str, dict]:
            for i in range(len(row)): tblstr += '<td class="%s" style="padding:5px 10px;">%s</td>\n' % (align[i], row[i])
        else:
            tblstr += '  <td class="%s" style="padding:5px 10px;">%s</td>\n' % (align[0], row)
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

    out  = '<form action="%s" method="post">\n' % (action, )
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
