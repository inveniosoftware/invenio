# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012 CERN.
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

import cgi
import os

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_TMPDIR, \
     CFG_SITE_URL
import invenio.modules.access.engine as access_manager
from invenio.utils.url import create_html_link
from invenio.legacy.dbquery import run_sql
from invenio.legacy.oairepository.updater import parse_set_definition
from invenio.base.i18n import gettext_set_language
from invenio.ext.logging import register_exception
from invenio.legacy.oairepository.config import CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC

import invenio.legacy.template
oaiharvest_templates = invenio.legacy.template.load('oaiharvest')
webstyle_templates = invenio.legacy.template.load('webstyle')

tmppath = CFG_TMPDIR + '/oairepositoryadmin.' + str(os.getpid())
guideurl = "help/admin/oairepository-admin-guide"
oai_rep_admin_url = CFG_SITE_URL + \
                    "/admin/oairepository/oairepositoryadmin.py"

def getnavtrail(previous = '', ln = CFG_SITE_LANG):
    """Get navtrail"""
    return oaiharvest_templates.tmpl_getnavtrail(previous = previous, ln = ln)

def perform_request_index(ln=CFG_SITE_LANG):
    """OAI Repository admin index"""

    out = '''<p>Define below the sets to expose through the OAI harvesting
    protocol. <br /> You will have to run the
    <a href="%(siteurl)s/help/admin/oairepository-admin-guide?ln=%(ln)s#2.2"><code>oairepositoryupdater</code></a>
    utility to apply the settings you have defined here.</p>''' % {'siteurl': CFG_SITE_URL,
                                                                   'ln': ln}

    header = ['id', 'setSpec',
              'setName', 'collection',
              'p1', 'f1', 'm1', 'op1',
              'p2', 'f2', 'm2', 'op2',
              'p3', 'f3', 'm3', '', '']

    oai_set = get_oai_set()
    sets = []

    for (id, setSpec, setName, setCollection, \
         dummy_setDescription, p1, f1, m1, p2, f2, m2, \
         p3, f3, m3, op1, op2) in oai_set:

        del_request = '<a href="' + CFG_SITE_URL + "/" + \
                      "admin/oairepository/oairepositoryadmin.py/delset?ln=" + \
                      ln + "&amp;oai_set_id=" + str(id) + '">delete</a>'

        edit_request = '<a href="' + CFG_SITE_URL + "/" + \
                       "admin/oairepository/oairepositoryadmin.py/editset?ln=" + \
                       ln + "&amp;oai_set_id=" + str(id) + '">edit</a>'

        edit_request = '<a href="' + CFG_SITE_URL + "/" + \
                       "admin/oairepository/oairepositoryadmin.py/touchset?ln=" + \
                       ln + "&amp;oai_set_id=" + str(id) + '">touch</a>'

        sets.append([id, cgi.escape(setSpec), cgi.escape(setName),
                     cgi.escape(setCollection),
                     cgi.escape(p1), f1, m1, op1,
                     cgi.escape(p2), f2, m2, op2,
                     cgi.escape(p3), f3, m3,
                     del_request, edit_request])

    add_request = '<a href="' + CFG_SITE_URL + "/" + \
                  "admin/oairepository/oairepositoryadmin.py/addset?ln=" + \
                  ln + '">Add new OAI set definition</a>'

    sets.append(['', add_request, '', '', '', '', '',
                 '', '', '', '', '', '', '', '', '', ''])

    out += transform_tuple(header=header, tuple=sets)

    out += "<br /><br />"

    return out


def perform_request_addset(oai_set_name='', oai_set_spec='',
                           oai_set_collection='',
                           oai_set_description='',
                           oai_set_p1='', oai_set_f1='',oai_set_m1='',
                           oai_set_p2='', oai_set_f2='',
                           oai_set_m2='', oai_set_p3='',
                           oai_set_f3='', oai_set_m3='',
                           oai_set_op1='a', oai_set_op2='a',
                           ln=CFG_SITE_LANG, func=0):
    """add a new OAI set"""
    _ = gettext_set_language(ln)
    out  = ""

    if func in ["0", 0]:
        text = input_form(oai_set_name, oai_set_spec,
                          oai_set_collection,
                          oai_set_p1, oai_set_f1,oai_set_m1,
                          oai_set_p2, oai_set_f2,oai_set_m2,
                          oai_set_p3, oai_set_f3, oai_set_m3,
                          oai_set_op1, oai_set_op2)
        out = createform(action="addset",
                         text=text,
                         ln=ln,
                         button="Add new OAI set definition line",
                         func=1)

    if func in ["1", 1]:
        out += "<br />"

        res = add_oai_set(oai_set_name, oai_set_spec,
                          oai_set_collection, oai_set_description,
                          oai_set_p1, oai_set_f1, oai_set_m1,
                          oai_set_p2, oai_set_f2, oai_set_m2,
                          oai_set_p3, oai_set_f3, oai_set_m3,
                          oai_set_op1, oai_set_op2)
        if res[0] == 1:
            out += oaiharvest_templates.tmpl_print_info(ln,
                                                        "OAI set definition %s added." % \
                                                        cgi.escape(oai_set_name))
            out += "<br />"

        out += "<br /><br />"
        out += create_html_link(urlbase=oai_rep_admin_url + \
                                "/index",
                                urlargd={'ln': ln},
                                link_label=_("Return to main selection"))

    return nice_box("", out)


def perform_request_editset(oai_set_id=None, oai_set_name='',
                            oai_set_spec='', oai_set_collection='',
                            oai_set_description='',
                            oai_set_p1='', oai_set_f1='',
                            oai_set_m1='', oai_set_p2='',
                            oai_set_f2='', oai_set_m2='',
                            oai_set_p3='', oai_set_f3='',
                            oai_set_m3='', oai_set_op1='a',
                            oai_set_op2='a', ln=CFG_SITE_LANG,
                            func=0):
    """creates html form to edit an OAI set."""
    _ = gettext_set_language(ln)

    if oai_set_id is None:
        return "No OAI set ID selected."

    out  = ""

    if func in [0, "0"]:

        oai_set = get_oai_set(oai_set_id)
        if not oai_set:
            return "ERROR: oai_set_id %s seems invalid" % oai_set_id
        oai_set_spec = oai_set[0][1]
        oai_set_name = oai_set[0][2]
        oai_set_collection  = oai_set[0][3]
        oai_set_description = oai_set[0][4]
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
            out += oaiharvest_templates.tmpl_print_info(ln, "OAI set definition #%s edited." % oai_set_id)
            out += "<br />"
        else:
            out += webstyle_templates.tmpl_write_warning("A problem was encountered: <br/>" + cgi.escape(res[1]))
            out += "<br />"

    out += "<br />"

    out += create_html_link(urlbase=oai_rep_admin_url + \
                            "/index",
                            urlargd={'ln': ln},
                            link_label=_("Return to main selection"))

    return nice_box("", out)


def perform_request_delset(oai_set_id=None, ln=CFG_SITE_LANG, func=0):
    """creates html form to delete an OAI set"""
    _ = gettext_set_language(ln)
    out = ""

    if oai_set_id:
        oai_set = get_oai_set(oai_set_id)
        if not oai_set:
            return "ERROR: oai_set_id %s seems invalid" % oai_set_id

        if func in ["0", 0]:

            oai_set = get_oai_set(oai_set_id)
            oai_set_spec = oai_set[0][1]
            oai_set_name = oai_set[0][2]
            oai_set_collection = oai_set[0][3]
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
                text = oaiharvest_templates.tmpl_print_info(ln, question)
                text += "<br /><br /><br />"
                text += pagebody_text(
                    cgi.escape("%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s" % \
                               (oai_set_spec,
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
                                oai_set_m3)))

                out += createform(action="delset",
                                       text=text,
                                       button="Delete",
                                       oai_set_id=oai_set_id,
                                       func=1)
            else:
                return oaiharvest_templates.tmpl_print_info(ln, "OAI set does not exist.")
        elif func in ["1", 1]:
            res = delete_oai_set(oai_set_id)
            if res[0] == 1:
                out += oaiharvest_templates.tmpl_print_info(ln, "OAI set definition #%s deleted." % oai_set_id)
                out += "<br />"
            else:
                pass

    out += "<br /><br />"
    out += create_html_link(urlbase=oai_rep_admin_url + \
                                "/index",
                                urlargd={'ln': ln},
                                link_label=_("Return to main selection"))

    return nice_box("", out)

def perform_request_touchset(oai_set_id=None, ln=CFG_SITE_LANG, func=0):
    """creates html form to touch an OAI set"""
    _ = gettext_set_language(ln)
    out = ""

    if oai_set_id:
        oai_set = get_oai_set(oai_set_id)
        if not oai_set:
            return "ERROR: oai_set_id %s seems invalid" % oai_set_id

        oai_set = get_oai_set(oai_set_id)
        oai_set_spec = oai_set[0][1]
        oai_set_name = oai_set[0][2]
        oai_set_collection = oai_set[0][3]
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

        if func in ["0", 0]:

            if oai_set:
                question = _("""Do you want to touch the OAI set %(x_name)s? Note that this will force all clients to re-harvest the whole set.""", x_name=cgi.escape(oai_set_spec))
                text = oaiharvest_templates.tmpl_print_info(ln, question)
                out += createform(action="touchset",
                                    text=text,
                                    button="Touch",
                                    oai_set_id=oai_set_id,
                                    func=1)
            else:
                return oaiharvest_templates.tmpl_print_info(ln, _("OAI set does not exist."))
        elif func in ["1", 1]:
            touch_oai_set(oai_set_spec)
            out += oaiharvest_templates.tmpl_print_info(ln, _("OAI set %(x_name)s touched.", x_name=cgi.escape(oai_set_spec)))
    out += "<br />"
    out += "<br /><br />"
    out += create_html_link(urlbase=oai_rep_admin_url + \
                "/index",
                urlargd={'ln': ln},
                link_label=_("Return to main selection"))

    return nice_box("", out)


def get_oai_set(id=''):
    """Returns a row parameters for a given id"""
    sets = []
    sql = "SELECT id, setSpec, setName, setCollection, setDescription, p1,f1,m1, p2,f2,m2, p3,f3,m3, setDefinition FROM oaiREPOSITORY"
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
    except StandardError as e:
        register_exception(alert_admin=True)
        return str(e)

def touch_oai_set(setSpec):
    """
    Updates the last_updated timestamp of an oai_set. This will cause
    any record belonging to it to be actually re-exported. This is
    useful in case e.g. the format template used to generate an
    export has been amended.

    Note: the last_updated time is in localtime to the server.
    """
    run_sql("UPDATE oaiREPOSITORY SET last_updated=NOW() WHERE setSpec=%s", (setSpec, ))

def modify_oai_set(oai_set_id, oai_set_name, oai_set_spec,
                   oai_set_collection, oai_set_description,
                   oai_set_p1, oai_set_f1,oai_set_m1, oai_set_p2,
                   oai_set_f2, oai_set_m2, oai_set_p3, oai_set_f3,
                   oai_set_m3, oai_set_op1, oai_set_op2):
    """Modifies a row's parameters"""

    try:
        if not oai_set_spec:
            oai_set_spec = CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC
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
        run_sql("""UPDATE oaiREPOSITORY SET
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
    except StandardError as e:
        register_exception(alert_admin=True)
        return (0, str(e))

def add_oai_set(oai_set_name, oai_set_spec, oai_set_collection,
                oai_set_description, oai_set_p1, oai_set_f1,oai_set_m1,
                oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3,
                oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2):
    """Add a definition into the OAI Repository"""
    try:
        if not oai_set_spec:
            oai_set_spec = CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC
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

        run_sql("""INSERT INTO oaiREPOSITORY (id, setName, setSpec,
                           setCollection, setDescription, setDefinition,
                           setRecList, p1, f1, m1, p2, f2, m2, p3, f3, m3)
                         VALUES (0, %s, %s, %s, %s, %s, NULL, %s, %s, %s,
                           %s, %s, %s, %s, %s, %s)""",
                      (oai_set_name, oai_set_spec, oai_set_collection,
                       oai_set_description, set_definition, oai_set_p1,
                       oai_set_f1, oai_set_m1, oai_set_p2, oai_set_f2,
                       oai_set_m2, oai_set_p3, oai_set_f3, oai_set_m3))
        return (1, "")
    except StandardError as e:
        register_exception(alert_admin=True)
        return (0, e)

def delete_oai_set(oai_set_id):
    """"""

    try:
        run_sql("DELETE FROM oaiREPOSITORY WHERE id=%s", (oai_set_id,))
        return (1, "")
    except StandardError as e:
        register_exception(alert_admin=True)
        return (0, e)

def drop_down_menu(boxname, content):
    """
    Returns the code of a drop down menu.

    Parameters:

       boxname - *str* name of the input form

       content - *list(tuple3)* the content of the list. List of items
                 as tuple3 with:
                 - *str* value of the item
                 - *bool* if item is selected of not
                 - *str* label of the item (displayed value)
    """
    text = "<select name=\"%s\">" % boxname

    for (value, selectedflag, txt) in content:
        text += "<option value=\""
        text += "%s\"" % value
        if selectedflag:
            text += ' selected="selected"'
        text += ">%s</option>" % txt
    text += "</select>"
    return text

def create_drop_down_menu_content(sql):
    """
    Create the content to be used in the drop_down_menu(..) function
    from an SQL statement
    """
    content = []

    res = run_sql(sql)
    for item in res:
        tmp_list = []
        tmp_list.append(item)
        tmp_list.append("")
        tmp_list.append(item)
        content.append(tmp_list)
    return content

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

def input_text(title, name, value):
    """"""
    if name is None:
        name = ""
    if value is None:
        value = ""
    text = """<table><tr><td width="100%%"><span class="adminlabel">%s</span></td>""" % title
    text += """<td align="left">
                <input class="admin_w200" type="text" name="%s" value="%s" />
                </td></tr></table>""" % \
    (cgi.escape(name, 1), cgi.escape(value, 1))
    return text

def pagebody_text(title):
    """"""
    text = """<span class="admintd">%s</span>""" % title
    return text

def bar_text(title):
    """"""
    text = """<span class="adminlabel">%s</span>""" % title
    return text

def input_form(oai_set_name, oai_set_spec, oai_set_collection,
               oai_set_p1, oai_set_f1,oai_set_m1,
               oai_set_p2, oai_set_f2,oai_set_m2, oai_set_p3,
               oai_set_f3, oai_set_m3, oai_set_op1, oai_set_op2):
    """returns the standard settings form"""

    modes = {
    'r' : 'Regular Expression',
    'a' : 'All of the words',
    'y' : 'Any of the words',
    'e' : 'Exact phrase',
    'p' : 'Partial phrase'
        }

    mode_dropdown = [['r', '', modes['r']],
                     ['e', '', modes['e']],
                     ['p', '', modes['p']],
                     ['a', '', modes['a']],
                     ['y', '', modes['y']],
                     ['', '', '']]

    operators = {
    'a' : 'AND',
    'o' : 'OR',
    'n' : 'AND NOT',
        }

    mode_operators_1 = [['a', '', operators['a']],
                        ['o', '', operators['o']],
                        ['n', '', operators['n']],
                        ['a', '', '']]

    mode_operators_2 = [['a', '', operators['a']],
                        ['o', '', operators['o']],
                        ['n', '', operators['n']],
                        ['a', '', '']]

    text = "<br />"
    text += "<table><tr><td>"
    text += input_text(title = "OAI Set spec:",
                       name = "oai_set_spec", value = oai_set_spec)
    text += '</td><td colspan="3"><small><small><em>Optional: if you leave it blank it will be automatically set to "%s", with the implicit convention that any record belonging to it can be harvested by not specifying any set.</em> [<a href="http://www.openarchives.org/OAI/openarchivesprotocol.html#set" target="_blank">?</a>]</small></small>' % CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC
    text += "</td></tr><tr><td>"
    text += input_text(title = "OAI Set name:",
                       name = "oai_set_name", value = oai_set_name)
    text += '</td><td colspan="3"><small><small><em>Optional: leave blank if not needed</em> [<a href="http://www.openarchives.org/OAI/openarchivesprotocol.html#Set" target="_blank">?</a>]</small></small>'

    text += "</td></tr><tr><td>&nbsp;</td></tr><tr><td>"
    text += '</td></tr><tr><td colspan="4">Choose below the search query that defines the records that belong to this set:</td></tr><tr><td>'
    text += "</td></tr><tr><td>&nbsp;</td></tr><tr><td>"

#    text += input_text(title = "OAI Set description", name = "oai_set_description", value = oai_set_description)

    #text += "</td><td colspan=2>"

    #menu = create_drop_down_menu_content("SELECT distinct(name) from collection")
    #menu.append(['','',''])

    #if (oai_set_collection):
    #    menu.append([oai_set_collection,'selected',oai_set_collection])
    #else:
    #    menu.append(['','selected','Collection'])

    text += input_text(title = "Collection(s):",
                       name="oai_set_collection",
                       value=oai_set_collection)

    #text += drop_down_menu("oai_set_collection", menu)

    text += '</td><td colspan="3"><small><small>Eg:</small> <code>Published Articles, Preprints, Theses</code><br/><small><em>(collections <b>identifiers</b>, not collections names/translations).</em></small></small></td></tr><tr><td>'

    text += input_text(title = "Phrase:", name =
                       "oai_set_p1", value = oai_set_p1)
    text += "</td><td>"

    fields = create_drop_down_menu_content("SELECT distinct(code) from field")
    fields.append(['', '', ''])
    if (oai_set_f1):
        fields.append([oai_set_f1, 'selected', oai_set_f1])
    else:
        fields.append(['', 'selected', 'Field'])

    if (oai_set_m1):
        mode_dropdown_m1 = [[oai_set_m1, 'selected', modes[oai_set_m1]]]
    else:
        mode_dropdown_m1 = [['', 'selected', 'Mode']]

    text += drop_down_menu("oai_set_f1", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m1", mode_dropdown + mode_dropdown_m1)

    text += "</td><td>"
    if (oai_set_op1):
        mode_operators_1.append([oai_set_op1, 'selected', operators[oai_set_op1]])
    else:
        mode_operators_1.append(['', 'selected', 'Operators'])
    text += drop_down_menu("oai_set_op1", mode_operators_1)
    text += "</td></tr><tr><td>"
    text += input_text(title = "Phrase:", name = "oai_set_p2", value = oai_set_p2)
    text += "</td><td>"

    fields = create_drop_down_menu_content("SELECT distinct(code) from field")
    fields.append(['', '', ''])
    if (oai_set_f2):
        fields.append([oai_set_f2, 'selected', oai_set_f2])
    else:
        fields.append(['', 'selected', 'Field'])
    if (oai_set_m2):
        mode_dropdown_m2 = [[oai_set_m2, 'selected', modes[oai_set_m2]]]
    else:
        mode_dropdown_m2 = [['', 'selected', 'Mode']]

    text += drop_down_menu("oai_set_f2", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m2", mode_dropdown + mode_dropdown_m2)

    text += "</td><td>"
    if (oai_set_op2):
        mode_operators_2.append([oai_set_op2, 'selected', operators[oai_set_op2]])
    else:
        mode_operators_2.append(['', 'selected', 'Operators'])
    text += drop_down_menu("oai_set_op2", mode_operators_2)
    text += "</td></tr><tr><td>"
    text += input_text(title = "Phrase:", name = "oai_set_p3", value = oai_set_p3)
    text += "</td><td>"

    fields = create_drop_down_menu_content("SELECT distinct(code) from field")
    fields.append(['', '', ''])
    if (oai_set_f3):
        fields.append([oai_set_f3, 'selected', oai_set_f3])
    else:
        fields.append(['', 'selected', 'Field'])
    if (oai_set_m3):
        mode_dropdown_m3 = [[oai_set_m3, 'selected', modes[oai_set_m3]]]
    else:
        mode_dropdown_m3 = [['', 'selected', 'Mode']]

    text += drop_down_menu("oai_set_f3", fields)
    text += "</td><td>"
    text += drop_down_menu("oai_set_m3", mode_dropdown + mode_dropdown_m3)

    text += "</td></tr></table>"

    return text

def check_user(req, role, authorized=0):
    """"""
    (auth_code, auth_message) = access_manager.acc_authorize_action(req, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)

def transform_tuple(header, tuple, start='', end=''):
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

def nice_box(header='', content='', cls="admin_wvar"):
    """
    Embed the content into a box with given header

    Parameters:
        header - *str* header of the box
      datalist - *str* the content of the box
           cls - *str* the class of the box

    """

    out  = '''
    <table class="%s" width="95%%">
     <thead>
      <tr>
       <th class="adminheaderleft" colspan="1">%s</th>
      </tr>
     </thead>
     <tbody>
      <tr>
       <td style="vertical-align: top; margin-top: 5px; width: 100%%;">
       %s
       </td>
      </tr>
     </tbody>
    </table>
    ''' % (cls, header, content)

    return out

def extended_input_form(action="", text="", button="func", cnfrm='',
                        **hidden):
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
