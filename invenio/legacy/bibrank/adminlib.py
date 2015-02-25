# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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
# Youshould have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio BibRank Administrator Interface."""

__revision__ = "$Id$"

import os
import ConfigParser

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_URL
from invenio.base.helpers import utf8ifier
import invenio.modules.access.engine as acce
from invenio.base.i18n import language_list_long
from invenio.legacy.dbquery import run_sql, wash_table_column_name
from invenio.modules.ranker.registry import configuration


def getnavtrail(previous=''):
    navtrail = """<a class="navtrail" href="%s/help/admin">Admin Area</a> """ % (
        CFG_SITE_URL,)
    navtrail = navtrail + previous
    return navtrail


def check_user(req, role, adminarea=2, authorized=0):
    (auth_code, auth_message) = is_adminuser(req, role)
    if not authorized and auth_code != 0:
        return ("false", auth_message)
    return ("", auth_message)


def is_adminuser(req, role):
    """check if user is a registered administrator. """
    return acce.acc_authorize_action(req, role)


def perform_index(ln=CFG_SITE_LANG):
    """create the bibrank main area menu page."""

    header = ['Code', 'Translations', 'Collections', 'Rank method']
    rnk_list = get_def_name('', "rnkMETHOD")
    actions = []

    for (rnkID, name) in rnk_list:
        actions.append([name])

        for col in [(('Modify', 'modifytranslations'),),
                    (('Modify', 'modifycollection'),),
                    (('Show Details', 'showrankdetails'),
                     ('Modify', 'modifyrank'),
                     ('Delete', 'deleterank'))]:
            actions[-1].append('<a href="%s/admin/bibrank/bibrankadmin.py/%s?rnkID=%s&amp;ln=%s">%s</a>' %
                               (CFG_SITE_URL, col[0][1], rnkID, ln, col[0][0]))
            for (str, function) in col[1:]:
                actions[-1][-1] += ' / <a href="%s/admin/bibrank/bibrankadmin.py/%s?rnkID=%s&amp;ln=%s">%s</a>' % (
                    CFG_SITE_URL, function, rnkID, ln, str)

    output = """
    <a href="%s/admin/bibrank/bibrankadmin.py/addrankarea?ln=%s">Add new rank method</a><br /><br />
    """ % (CFG_SITE_URL, ln)

    output += tupletotable(header=header, tuple=actions)
    return addadminbox("""Overview of rank methods&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibrank-admin-guide#mi">?</a>]</small>""" % CFG_SITE_URL, datalist=[output, ''])


def perform_modifycollection(rnkID='', ln=CFG_SITE_LANG, func='', colID='', confirm=0):
    """Modify which collections the rank method is visible to"""

    output = ""
    subtitle = ""

    if rnkID:
        rnkNAME = get_def_name(rnkID, "rnkMETHOD")[0][1]

        if func in ["0", 0] and confirm in ["1", 1]:
            finresult = attach_col_rnk(rnkID, colID)
        elif func in ["1", 1] and confirm in ["1", 1]:
            finresult = detach_col_rnk(rnkID, colID)

        if colID:
            colNAME = get_def_name(colID, "collection")[0][1]
        subtitle = """Step 1 - Select collection to enable/disable rank method '%s' for""" % rnkNAME
        output  = """
        <dl>
        <dt>The rank method is currently enabled for these collections:</dt>
        <dd>
        """
        col_list = get_rnk_col(rnkID, ln)
        if not col_list:
            output += """No collections"""
        else:
            for (id, name) in col_list:
                output += """%s, """ % name
        output += """</dd>
        </dl>
        """

        col_list = get_def_name('', "collection")
        col_rnk = dict(get_rnk_col(rnkID))
        col_list = filter(lambda x: x[0] not in col_rnk, col_list)

        if col_list:
            text  = """
            <span class="adminlabel">Enable for:</span>
            <select name="colID" class="admin_w200">
            <option value="">- select collection -</option>
            """

            for (id, name) in col_list:
                text += """<option value="%s" %s>%s</option>""" % (id, (func in ["0", 0] and confirm in [
                                                                   "0", 0] and colID and int(colID) == int(id)) and 'selected="selected"' or '', name)
            text += """</select>"""
            output += createhiddenform(action="modifycollection",
                                       text=text,
                                       button="Enable",
                                       rnkID=rnkID,
                                       ln=ln,
                                       func=0,
                                       confirm=1)

        if confirm in ["0", 0] and func in ["0", 0] and colID:
            subtitle = "Step 2 - Confirm to enable rank method for the chosen collection"
            text = "<b><p>Please confirm to enable rank method '%s' for the collection '%s'</p></b>" % (
                rnkNAME, colNAME)
            output += createhiddenform(action="modifycollection",
                                       text=text,
                                       button="Confirm",
                                       rnkID=rnkID,
                                       ln=ln,
                                       colID=colID,
                                       func=0,
                                       confirm=1)
        elif confirm in ["1", 1] and func in ["0", 0] and colID:
            subtitle = "Step 3 - Result"
            output += write_outcome(finresult)
        elif confirm not in ["0", 0] and func in ["0", 0]:
            output += """<b><span class="info">Please select a collection.</span></b>"""

        col_list = get_rnk_col(rnkID, ln)
        if col_list:
            text  = """
            <span class="adminlabel">Disable for:</span>
            <select name="colID" class="admin_w200">
            <option value="">- select collection -</option>
            """

            for (id, name) in col_list:
                text += """<option value="%s" %s>%s</option>""" % (id, (func in ["1", 1] and confirm in [
                                                                   "0", 0] and colID and int(colID) == int(id)) and 'selected="selected"' or '', name)
            text += """</select>"""
            output += createhiddenform(action="modifycollection",
                                       text=text,
                                       button="Disable",
                                       rnkID=rnkID,
                                       ln=ln,
                                       func=1,
                                       confirm=1)

        if confirm in ["1", 1] and func in ["1", 1] and colID:
            subtitle = "Step 3 - Result"
            output += write_outcome(finresult)
        elif confirm not in ["0", 0] and func in ["1", 1]:
            output += """<b><span class="info">Please select a collection.</span></b>"""

    body = [output]

    return addadminbox(subtitle + """&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibrank-admin-guide#mc">?</a>]</small>""" % CFG_SITE_URL, body)


def perform_modifytranslations(rnkID, ln, sel_type, trans, confirm, callback='yes'):
    """Modify the translations of a rank method"""

    output = ''
    subtitle = ''
    langs = get_languages()
    langs.sort()

    if confirm in ["2", 2] and rnkID:
        finresult = modify_translations(
            rnkID, langs, sel_type, trans, "rnkMETHOD")

    rnk_name = get_def_name(rnkID, "rnkMETHOD")[0][1]
    rnk_dict = dict(
        get_i8n_name('', ln, get_rnk_nametypes()[0][0], "rnkMETHOD"))
    if rnkID and int(rnkID) in rnk_dict:
        rnkID = int(rnkID)
        subtitle = """<a name="3">3. Modify translations for rank method '%s'</a>""" % rnk_name

        if type(trans) is str:
            trans = [trans]
        if sel_type == '':
            sel_type = get_rnk_nametypes()[0][0]

        header = ['Language', 'Translation']

        actions = []

        text  = """
        <span class="adminlabel">Name type</span>
        <select name="sel_type" class="admin_w200">
        """

        types = get_rnk_nametypes()
        if len(types) > 1:
            for (key, value) in types:
                text += """<option value="%s" %s>%s""" % (
                    key, key == sel_type and 'selected="selected"' or '', value)
                trans_names = get_name(rnkID, ln, key, "rnkMETHOD")
                if trans_names and trans_names[0][0]:
                    text += ": %s" % trans_names[0][0]
                text += "</option>"
            text += """</select>"""

            output += createhiddenform(action="modifytranslations",
                                       text=text,
                                       button="Select",
                                       rnkID=rnkID,
                                       ln=ln,
                                       confirm=0)

        if confirm in [-1, "-1", 0, "0"]:
            trans = []
            for key, value in langs:
                try:
                    trans_names = get_name(rnkID, key, sel_type, "rnkMETHOD")
                    trans.append(trans_names[0][0])
                except StandardError as e:
                    trans.append('')

        for nr in range(0, len(langs)):
            actions.append(["%s" % (langs[nr][1],)])
            actions[-1].append(
                '<input type="text" name="trans" size="30" value="%s"/>' % trans[nr])

        text = tupletotable(header=header, tuple=actions)
        output += createhiddenform(action="modifytranslations",
                                   text=text,
                                   button="Modify",
                                   rnkID=rnkID,
                                   sel_type=sel_type,
                                   ln=ln,
                                   confirm=2)

        if sel_type and len(trans) and confirm in ["2", 2]:
            output += write_outcome(finresult)

    body = [output]

    return addadminbox(subtitle + """&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibrank-admin-guide#mt">?</a>]</small>""" % CFG_SITE_URL, body)


def perform_addrankarea(rnkcode='', ln=CFG_SITE_LANG, template='', confirm=-1):
    """form to add a new rank method with these values:"""

    subtitle = 'Step 1 - Create new rank method'
    output  = """
    <dl>
     <dt>BibRank code:</dt>
     <dd>A unique code that identifies a rank method, is used when running the bibrank daemon and used to name the configuration file for the method.
     <br />The template files includes the necessary parameters for the chosen rank method, and only needs to be edited with the correct tags and paths.
     <br />For more information, please go to the <a title="See guide" href="%s/help/admin/bibrank-admin-guide">BibRank guide</a> and read the section about adding a rank method</dd>
    </dl>
    """ % CFG_SITE_URL
    text = """
    <span class="adminlabel">BibRank code</span>
    <input class="admin_wvar" type="text" name="rnkcode" value="%s" />
    """ % (rnkcode)

    text += """<br />
    <span class="adminlabel">Cfg template</span>
    <select name="template" class="admin_w200">
    <option value="">No template</option>
    """

    templates = get_templates()
    for templ in templates:
        text += """<option value="%s" %s>%s</option>""" % (
            templ, template == templ and 'selected="selected"' or '', templ[9:len(templ) - 4])
    text += """</select>"""

    output += createhiddenform(action="addrankarea",
                               text=text,
                               button="Add rank method",
                               ln=ln,
                               confirm=1)

    if rnkcode:
        if confirm in ["0", 0]:
            subtitle = 'Step 2 - Confirm addition of rank method'
            text = """<b>Add rank method with BibRank code: '%s'.</b>""" % (
                rnkcode)
            if template:
                text += """<br /><b>Using configuration template: '%s'.</b>""" % (
                    template)
            else:
                text += """<br /><b>Create empty configuration file.</b>"""
            output += createhiddenform(action="addrankarea",
                                       text=text,
                                       rnkcode=rnkcode,
                                       button="Confirm",
                                       template=template,
                                       confirm=1)

        elif confirm in ["1", 1]:
            rnkID = add_rnk(rnkcode)
            subtitle = "Step 3 - Result"
            if rnkID[0] == 1:
                rnkID = rnkID[1]
                text = """<b><span class="info">Added new rank method with BibRank code '%s'</span></b>""" % rnkcode
                try:
                    if template:
                        infile = open(configuration.get(template, ''), 'r')
                        indata = infile.readlines()
                        infile.close()
                    else:
                        indata = ()
                    file = open(
                        configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''), 'w')
                    for line in indata:
                        file.write(line)
                    file.close()
                    if template:
                        text += """<b><span class="info"><br />Configuration file created using '%s' as template.</span></b>""" % template
                    else:
                        text += """<b><span class="info"><br />Empty configuration file created.</span></b>"""
                except StandardError as e:
                    text += """<b><span class="info"><br />Sorry, could not create configuration file: '%s.cfg', either because it already exists, or not enough rights to create file. <br />Please create the file in the path given.</span></b>""" % (
                        configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''), )
            else:
                text = """<b><span class="info">Sorry, could not add rank method, rank method with the same BibRank code probably exists.</span></b>"""
            output += text
    elif not rnkcode and confirm not in [-1, "-1"]:
        output += """<b><span class="info">Sorry, could not add rank method, not enough data submitted.</span></b>"""

    body = [output]

    return addadminbox(subtitle + """&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibrank-admin-guide#ar">?</a>]</small>""" % CFG_SITE_URL, body)


def perform_modifyrank(rnkID, rnkcode='', ln=CFG_SITE_LANG, template='', cfgfile='', confirm=0):
    """form to modify a rank method

    rnkID - id of the rank method
    """

    if not rnkID:
        return "No ranking method selected."
    if not get_rnk_code(rnkID):
        return "Ranking method %s does not seem to exist." % str(rnkID)

    subtitle = 'Step 1 - Please modify the wanted values below'
    if not rnkcode:
        oldcode = get_rnk_code(rnkID)[0]
    else:
        oldcode = rnkcode

    output  = """
    <dl>
     <dd>When changing the BibRank code of a rank method, you must also change any scheduled tasks using the old value.
     <br />For more information, please go to the <a title="See guide" href="%s/help/admin/bibrank-admin-guide">BibRank guide</a> and read the section about modifying a rank method's  BibRank code.</dd>
    </dl>
    """ % CFG_SITE_URL

    text = """
     <span class="adminlabel">BibRank code</span>
     <input class="admin_wvar" type="text" name="rnkcode" value="%s" />
     <br />
    """ % (oldcode)

    try:
        text += """<span class="adminlabel">Cfg file</span>"""
        textarea = ""
        if cfgfile:
            textarea += cfgfile
        else:
            file = open(
                configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''))
            for line in file.readlines():
                textarea += line
        text += """<textarea class="admin_wvar" name="cfgfile" rows="15" cols="70">""" + \
            textarea + """</textarea>"""
    except StandardError as e:
        text += """<b><span class="info">Cannot load file, either it does not exist, or not enough rights to read it: '%s.cfg'<br />Please create the file in the path given.</span></b>""" % (
            configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''), )

    output += createhiddenform(action="modifyrank",
                               text=text,
                               rnkID=rnkID,
                               button="Modify",
                               confirm=1)

    if rnkcode and confirm in ["1", 1] and get_rnk_code(rnkID)[0][0] != rnkcode:
        oldcode = get_rnk_code(rnkID)[0][0]
        result = modify_rnk(rnkID, rnkcode)
        subtitle = "Step 3 - Result"
        if result:
            text = """<b><span class="info">Rank method modified.</span></b>"""
            try:
                file = open(configuration.get(oldcode + '.cfg', ''), 'r')
                file2 = open(configuration.get(rnkcode + '.cfg', ''), 'w')
                lines = file.readlines()
                for line in lines:
                    file2.write(line)
                file.close()
                file2.close()
                os.remove(configuration.get(oldcode + '.cfg', ''))
            except StandardError as e:
                text = """<b><span class="info">Sorry, could not change name of cfg file, must be done manually: '%s.cfg'</span></b>""" % (
                    configuration.get(oldcode + '.cfg', ''), )
        else:
            text = """<b><span class="info">Sorry, could not modify rank method.</span></b>"""
        output += text

    if cfgfile and confirm in ["1", 1]:
        try:
            file = open(
                configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''), 'w')
            file.write(cfgfile)
            file.close()
            text = """<b><span class="info"><br />Configuration file modified: '%s/bibrank/%s.cfg'</span></b>""" % (
                configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''), )
        except StandardError as e:
            text = """<b><span class="info"><br />Sorry, could not modify configuration file, please check for rights to do so: '%s.cfg'<br />Please modify the file manually.</span></b>""" % (
                configuration.get(get_rnk_code(rnkID)[0][0] + '.cfg', ''), )
        output += text

    finoutput = addadminbox(
        subtitle + """&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibrank-admin-guide#mr">?</a>]</small>""" % CFG_SITE_URL, [output])
    output = ""

    text = """
    <span class="adminlabel">Select</span>
    <select name="template" class="admin_w200">
    <option value="">- select template -</option>
    """
    templates = get_templates()
    for templ in templates:
        text += """<option value="%s" %s>%s</option>""" % (
            templ, template == templ and 'selected="selected"' or '', templ[9:len(templ) - 4])
    text += """</select><br />"""

    output += createhiddenform(action="modifyrank",
                               text=text,
                               rnkID=rnkID,
                               button="Show template",
                               confirm=0)

    try:
        if template:
            textarea = ""
            text = """<span class="adminlabel">Content:</span>"""
            file = open(configuration.get(template, ''), 'r')
            lines = file.readlines()
            for line in lines:
                textarea += line
            file.close()
            text += """<textarea class="admin_wvar" readonly="true" rows="15" cols="70">""" + \
                textarea + """</textarea>"""
            output += text
    except StandardError as e:
        output += """Cannot load file, either it does not exist, or not enough rights to read it: '%s'""" % (
            configuration.get(template, ''), )

    finoutput += addadminbox("View templates", [output])
    return finoutput


def perform_deleterank(rnkID, ln=CFG_SITE_LANG, confirm=0):
    """form to delete a rank method
    """
    subtitle = ''
    output  = """
    <span class="warning">
    <dl>
     <dt><strong>WARNING:</strong></dt>
     <dd><strong>When deleting a rank method, you also deletes all data related to the rank method, like translations, which collections
     it was attached to and the data necessary to rank the searchresults. Any scheduled tasks using the deleted rank method will also stop working.
     <br /><br />For more information, please go to the <a title="See guide" href="%s/help/admin/bibrank-admin-guide">BibRank guide</a> and read the section regarding deleting a rank method.</strong></dd>
    </dl>
    </span>
    """ % CFG_SITE_URL

    if rnkID:
        if confirm in ["0", 0]:
            rnkNAME = get_def_name(rnkID, "rnkMETHOD")[0][1]
            subtitle = 'Step 1 - Confirm deletion'
            text = """Delete rank method '%s'.""" % (rnkNAME)
            output += createhiddenform(action="deleterank",
                                       text=text,
                                       button="Confirm",
                                       rnkID=rnkID,
                                       confirm=1)
        elif confirm in ["1", 1]:
            try:
                rnkNAME = get_def_name(rnkID, "rnkMETHOD")[0][1]
                rnkcode = get_rnk_code(rnkID)[0][0]
                table = ""
                try:
                    config = ConfigParser.ConfigParser()
                    config.readfp(
                        open(configuration.get(rnkcode + ".cfg"), 'r'))
                    table = config.get(
                        config.get('rank_method', "function"), "table")
                except Exception:
                    pass
                result = delete_rnk(rnkID, table)
                subtitle = "Step 2 - Result"
                if result:
                    text = """<b><span class="info">Rank method deleted</span></b>"""
                    try:
                        os.remove(configuration.get(rnkcode + ".cfg"))
                        text += """<br /><b><span class="info">Configuration file deleted: '%s.cfg'.</span></b>"""  % (
                            configuration.get(rnkcode + ".cfg"), )
                    except StandardError as e:
                        text += """<br /><b><span class="info">Sorry, could not delete configuration file: '%s/bibrank/%s.cfg'.</span><br />Please delete the file manually.</span></b>""" % (
                            configuration.get(rnkcode + ".cfg"), )
                else:
                    text = """<b><span class="info">Sorry, could not delete rank method</span></b>"""
            except StandardError as e:
                text = """<b><span class="info">Sorry, could not delete rank method, most likely already deleted</span></b>"""
            output = text

    body = [output]

    return addadminbox(subtitle + """&nbsp;&nbsp;&nbsp;<small>[<a title="See guide" href="%s/help/admin/bibrank-admin-guide#dr">?</a>]</small>""" % CFG_SITE_URL, body)


def perform_showrankdetails(rnkID, ln=CFG_SITE_LANG):
    """Returns details about the rank method given by rnkID"""

    if not rnkID:
        return "No ranking method selected."
    if not get_rnk_code(rnkID):
        return "Ranking method %s does not seem to exist." % str(rnkID)

    subtitle = """Overview <a href="%s/admin/bibrank/bibrankadmin.py/modifyrank?rnkID=%s&amp;ln=%s">[Modify]</a>""" % (
        CFG_SITE_URL, rnkID, ln)
    text  = """
    BibRank code: %s<br />
    Last updated by BibRank:
    """ % (get_rnk_code(rnkID)[0][0])
    if get_rnk(rnkID)[0][2]:
        text += "%s<br />" % get_rnk(rnkID)[0][2]
    else:
        text += "Not yet run.<br />"
    output = addadminbox(subtitle, [text])

    subtitle = """Rank method statistics"""
    text = ""
    try:
        text = "Not yet implemented"
    except StandardError as e:
        text = "BibRank not yet run, cannot show statistics for method"
    output += addadminbox(subtitle, [text])

    subtitle = """Attached to collections <a href="%s/admin/bibrank/bibrankadmin.py/modifycollection?rnkID=%s&amp;ln=%s">[Modify]</a>""" % (
        CFG_SITE_URL, rnkID, ln)
    text = ""
    col = get_rnk_col(rnkID, ln)
    for key, value in col:
        text += "%s<br />" % value
    if not col:
        text += "No collections"
    output += addadminbox(subtitle, [text])

    subtitle = """Translations <a href="%s/admin/bibrank/bibrankadmin.py/modifytranslations?rnkID=%s&amp;ln=%s">[Modify]</a>""" % (
        CFG_SITE_URL, rnkID, ln)
    prev_lang = ''
    trans = get_translations(rnkID)
    types = get_rnk_nametypes()
    types = dict(map(lambda x: (x[0], x[1]), types))
    text = ""
    languages = dict(get_languages())
    if trans:
        for lang, type, name in trans:
            if lang and lang in languages and type and name:
                if prev_lang != lang:
                    prev_lang = lang
                    text += """%s: <br />""" % (languages[lang])
                if type in types:
                    text += """<span style="margin-left: 10px">'%s'</span><span class="note">(%s)</span><br />""" % (
                        name, types[type])
    else:
        text = """No translations exists"""
    output += addadminbox(subtitle, [text])

    subtitle = """Configuration file: '%s/bibrank/%s.cfg' <a href="%s/admin/bibrank/bibrankadmin.py/modifyrank?rnkID=%s&amp;ln=%s">[Modify]</a>""" % (
        CFG_ETCDIR, get_rnk_code(rnkID)[0][0], CFG_SITE_URL, rnkID, ln)
    text = ""
    try:
        file = open(configuration.get(get_rnk_code(rnkID)[0][0] + ".cfg", ''))
        text += """<pre>"""
        for line in file.readlines():
            text += line
        text += """</pre>"""
    except StandardError as e:
        text = """Cannot load file, either it does not exist, or not enough rights to read it."""
    output += addadminbox(subtitle, [text])

    return output


def compare_on_val(second, first):
    return cmp(second[1], first[1])


def get_rnk_code(rnkID):
    """Returns the name from rnkMETHOD based on argument
    rnkID - id from rnkMETHOD"""

    try:
        res = run_sql("SELECT name FROM rnkMETHOD where id=%s" % (rnkID))
        return res
    except StandardError as e:
        return ()


def get_rnk(rnkID=''):
    """Return one or all rank methods
    rnkID - return the rank method given, or all if not given"""

    try:
        if rnkID:
            res = run_sql(
                "SELECT id,name,DATE_FORMAT(last_updated, '%%Y-%%m-%%d %%H:%%i:%%s') from rnkMETHOD WHERE id=%s" % rnkID)
        else:
            res = run_sql(
                "SELECT id,name,DATE_FORMAT(last_updated, '%%Y-%%m-%%d %%H:%%i:%%s') from rnkMETHOD")
        return res
    except StandardError as e:
        return ()


def get_translations(rnkID):
    """Returns the translations in rnkMETHODNAME for a rankmethod
    rnkID - the id of the rankmethod from rnkMETHOD """

    try:
        res = run_sql(
            "SELECT ln, type, value FROM rnkMETHODNAME where id_rnkMETHOD=%s ORDER BY ln,type" % (rnkID))
        return res
    except StandardError as e:
        return ()


def get_rnk_nametypes():
    """Return a list of the various translationnames for the rank methods"""

    type = []
    type.append(('ln', 'Long name'))
    #type.append(('sn', 'Short name'))
    return type


def get_col_nametypes():
    """Return a list of the various translationnames for the rank methods"""

    type = []
    type.append(('ln', 'Long name'))
    return type


def get_rnk_col(rnkID, ln=CFG_SITE_LANG):
    """ Returns a list of the collections the given rank method is attached to
    rnkID - id from rnkMETHOD"""

    try:
        res1 = dict(run_sql(
            "SELECT id_collection, '' FROM collection_rnkMETHOD WHERE id_rnkMETHOD=%s" % rnkID))
        res2 = get_def_name('', "collection")
        result = filter(lambda x: x[0] in res1, res2)
        return result
    except StandardError as e:
        return ()


def get_templates():
    """Read CFG_ETCDIR/bibrank and returns a list of all files with 'template' """

    templates = []
    files = configuration.itervalues()
    for file in files:
        if str.find(file, "template_") != -1:
            templates.append(file)
    return templates


def attach_col_rnk(rnkID, colID):
    """attach rank method to collection
    rnkID - id from rnkMETHOD table
    colID - id of collection, as in collection table """

    try:
        res = run_sql(
            "INSERT INTO collection_rnkMETHOD(id_collection, id_rnkMETHOD) values (%s,%s)" % (colID, rnkID))
        return (1, "")
    except StandardError as e:
        return (0, e)


def detach_col_rnk(rnkID, colID):
    """detach rank method from collection
    rnkID - id from rnkMETHOD table
    colID - id of collection, as in collection table """

    try:
        res = run_sql(
            "DELETE FROM collection_rnkMETHOD WHERE id_collection=%s AND id_rnkMETHOD=%s" % (colID, rnkID))
        return (1, "")
    except StandardError as e:
        return (0, e)


def delete_rnk(rnkID, table=""):
    """Deletes all data for the given rank method
    rnkID - delete all data in the tables associated with ranking and this id """

    try:
        res = run_sql("DELETE FROM rnkMETHOD WHERE id=%s" % rnkID)
        res = run_sql(
            "DELETE FROM rnkMETHODNAME WHERE id_rnkMETHOD=%s" % rnkID)
        res = run_sql(
            "DELETE FROM collection_rnkMETHOD WHERE id_rnkMETHOD=%s" % rnkID)
        res = run_sql(
            "DELETE FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s" % rnkID)
        if table:
            res = run_sql("truncate %s" % table)
            res = run_sql("truncate %sR" % table[:-1])
        return (1, "")
    except StandardError as e:
        return (0, e)


def modify_rnk(rnkID, rnkcode):
    """change the code for the rank method given
    rnkID - change in rnkMETHOD where id is like this
    rnkcode - new value for field 'name' in rnkMETHOD """

    try:
        res = run_sql(
            "UPDATE rnkMETHOD set name=%s WHERE id=%s", (rnkcode, rnkID))
        return (1, "")
    except StandardError as e:
        return (0, e)


def add_rnk(rnkcode):
    """Adds a new rank method to rnkMETHOD
    rnkcode - the "code" for the rank method, to be used by bibrank daemon """

    try:
        res = run_sql("INSERT INTO rnkMETHOD (name) VALUES (%s)", (rnkcode,))
        res = run_sql("SELECT id FROM rnkMETHOD WHERE name=%s", (rnkcode,))
        if res:
            return (1, res[0][0])
        else:
            raise StandardError
    except StandardError as e:
        return (0, e)


def addadminbox(header='', datalist=[], cls="admin_wvar"):
    """used to create table around main data on a page, row based.

      header - header on top of the table

    datalist - list of the data to be added row by row

         cls - possible to select wich css-class to format the look of the table."""

    if len(datalist) == 1:
        per = '100'
    else:
        per = '75'

    output = '<table class="%s" ' % (cls, ) + 'width="95%">\n'
    output += """
     <thead>
      <tr>
       <th class="adminheaderleft" colspan="%s">%s</th>
      </tr>
     </thead>
     <tbody>
    """ % (len(datalist), header)

    output += '      <tr>\n'

    output += """
    <td style="vertical-align: top; margin-top: 5px; width: %s;">
     %s
    </td>
    """ % (per + '%', datalist[0])

    if len(datalist) > 1:
        output += """
        <td style="vertical-align: top; margin-top: 5px; width: %s;">
         %s
        </td>
        """ % ('25%', datalist[1])

    output += '      </tr>\n'

    output += """
     </tbody>
    </table>
    """

    return output


def tupletotable(header=[], tuple=[], start='', end='', extracolumn='', highlight_rows_p=False, alternate_row_colors_p=False):
    """create html table for a tuple.

         header - optional header for the columns

          tuple - create table of this

          start - text to be added in the beginning, most likely beginning of a form

            end - text to be added in the end, mot likely end of a form.

    extracolumn - mainly used to put in a button.

      highlight_rows_p - if the cursor hovering a row should highlight the full row or not

alternate_row_colors_p - if alternate background colours should be used for the rows
    """

    # study first row in tuple for alignment
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
    if tblstr:
        tblstr = ' <tr>\n%s\n </tr>\n' % (tblstr, )

    tblstr = start + '<table class="admin_wvar_nomargin">\n' + tblstr

    # extra column
    try:
        extra = '<tr class="%s">' % (
            highlight_rows_p and 'admin_row_highlight' or '')

        if type(firstrow) not in [int, long, str, dict]:
            # for data in firstrow: extra += '<td class="%s">%s</td>\n' % ('admintd', data)
            for i in range(len(firstrow)):
                extra += '<td class="{0}">{1}</td>\n'.format(
                    align[i], firstrow[i])
        else:
            extra += '  <td class="%s">%s</td>\n' % (align[0], firstrow)
        extra += '<td class="extracolumn" rowspan="%s" style="vertical-align: top;">\n%s\n</td>\n</tr>\n' % (
            len(tuple), extracolumn)
    except IndexError:
        extra = ''
    tblstr += extra

    # for i in range(1, len(tuple)):
    j = 0
    for row in tuple[1:]:
        j += 1
        tblstr += ' <tr class="%s %s">\n' % (highlight_rows_p and 'admin_row_highlight' or '',
                                             (j % 2 and alternate_row_colors_p) and 'admin_row_color' or '')
        # row = tuple[i]
        if type(row) not in [int, long, str, dict]:
            # for data in row: tblstr += '<td class="admintd">%s</td>\n' % (data,)
            for i in range(len(row)):
                tblstr += '<td class="{0}">{1}</td>\n'.format(align[i], utf8ifier(row[i]))
        else:
            tblstr += '  <td class="%s">%s</td>\n' % (align[0], row)
        tblstr += ' </tr> \n'

    tblstr += '</table> \n '
    tblstr += end

    return tblstr


def tupletotable_onlyselected(header=[], tuple=[], selected=[], start='', end='', extracolumn=''):
    """create html table for a tuple.

        header - optional header for the columns

         tuple - create table of this

      selected - indexes of selected rows in the tuple

         start - put this in the beginning

           end - put this in the beginning

   extracolumn - mainly used to put in a button"""

    tuple2 = []

    for index in selected:
        tuple2.append(tuple[int(index) - 1])

    return tupletotable(header=header,
                        tuple=tuple2,
                        start=start,
                        end=end,
                        extracolumn=extracolumn)


def addcheckboxes(datalist=[], name='authids', startindex=1, checked=[]):
    """adds checkboxes in front of the listdata.

      datalist - add checkboxes in front of this list

          name - name of all the checkboxes, values will be associated with this name

    startindex - usually 1 because of the header

       checked - values of checkboxes to be pre-checked """

    if not type(checked) is list:
        checked = [checked]
    for row in datalist:
        # always box, check another place
        if 1 or row[0] not in [-1, "-1", 0, "0"]:
            chkstr = str(startindex) in checked and 'checked="checked"' or ''
            row.insert(
                0, '<input type="checkbox" name="%s" value="%s" %s />' % (name, startindex, chkstr))
        else:
            row.insert(0, '')
        startindex += 1
    return datalist


def createhiddenform(action="", text="", button="confirm", cnfrm='', **hidden):
    """create select with hidden values and submit button

      action - name of the action to perform on submit

        text - additional text, can also be used to add non hidden input

      button - value/caption on the submit button

       cnfrm - if given, must check checkbox to confirm

    **hidden - dictionary with name=value pairs for hidden input """

    output = '<form action="%s" method="post">\n' % (action, )
    output += '<table>\n<tr><td style="vertical-align: top">'
    # output += text.decode('utf-8')
    output += text
    if cnfrm:
        output += ' <input type="checkbox" name="confirm" value="1"/>'
    for key in hidden.keys():
        if type(hidden[key]) is list:
            for value in hidden[key]:
                output += ' <input type="hidden" name="%s" value="%s"/>\n' % (
                    key, value)
        else:
            output += ' <input type="hidden" name="%s" value="%s"/>\n' % (
                key, hidden[key])
    output += '</td><td style="vertical-align: bottom">'
    output += ' <input class="btn btn-default" type="submit" value="%s"/>\n' % (
        button, )
    output += '</td></tr></table>'
    output += '</form>\n'

    return output


def get_languages():
    languages = []
    for (lang, lang_namelong) in language_list_long():
        languages.append((lang, lang_namelong))
    languages.sort()
    return languages


def get_def_name(ID, table):
    """Returns a list of the names, either with the name in the current language, the default language, or just the name from the given table
    ln - a language supported by Invenio
    type - the type of value wanted, like 'ln', 'sn'"""

    name = "name"
    if table[-1:].isupper():
        name = "NAME"

    try:
        if ID:
            res = run_sql("SELECT id,name FROM %s where id=%s" % (table, ID))
        else:
            res = run_sql("SELECT id,name FROM %s" % table)
        res = list(res)
        res.sort(compare_on_val)
        return res
    except StandardError as e:
        return []


def get_i8n_name(ID, ln, rtype, table):
    """Returns a list of the names, either with the name in the current language, the default language, or just the name from the given table
    ln - a language supported by Invenio
    type - the type of value wanted, like 'ln', 'sn'"""

    name = "name"
    if table[-1:].isupper():
        name = "NAME"
    try:
        res = ""
        if ID:
            res = run_sql("SELECT id_%s,value FROM %s%s where type='%s' and ln='%s' and id_%s=%s" % (
                table, table, name, rtype, ln, table, ID))
        else:
            res = run_sql("SELECT id_%s,value FROM %s%s where type='%s' and ln='%s'" % (
                table, table, name, rtype, ln))
        if ln != CFG_SITE_LANG:
            if ID:
                res1 = run_sql("SELECT id_%s,value FROM %s%s WHERE ln='%s' and type='%s' and id_%s=%s" % (
                    table, table, name, CFG_SITE_LANG, rtype, table, ID))
            else:
                res1 = run_sql("SELECT id_%s,value FROM %s%s WHERE ln='%s' and type='%s'" % (
                    table, table, name, CFG_SITE_LANG, rtype))
            res2 = dict(res)
            result = filter(lambda x: x[0] not in res2, res1)
            res = res + result
        if ID:
            res1 = run_sql("SELECT id,name FROM %s where id=%s" % (table, ID))
        else:
            res1 = run_sql("SELECT id,name FROM %s" % table)
        res2 = dict(res)
        result = filter(lambda x: x[0] not in res2, res1)
        res = res + result
        res = list(res)
        res.sort(compare_on_val)
        return res
    except StandardError as e:
        raise StandardError


def get_name(ID, ln, rtype, table, id_column=None):
    """Returns the value from the table name based on arguments
    ID - id
    ln - a language supported by Invenio
    type - the type of value wanted, like 'ln', 'sn'
    table - tablename
    id_column - name of the column with identifier. If None, expect column to be named 'id_%s' % table
    """

    name = "name"
    if table[-1:].isupper():
        name = "NAME"

    if id_column:
        id_column = wash_table_column_name(id_column)

    try:
        res = run_sql("SELECT value FROM %s%s WHERE type='%s' and ln='%s' and %s=%s" % (
            table, name, rtype, ln, (id_column or 'id_%s' % wash_table_column_name(table)), ID))
        return res
    except StandardError as e:
        return ()


def modify_translations(ID, langs, sel_type, trans, table, id_column=None):
    """add or modify translations in tables given by table
    frmID - the id of the format from the format table
    sel_type - the name type
    langs - the languages
    trans - the translations, in same order as in langs
    table - the table
    id_column - name of the column with identifier. If None, expect column to be named 'id_%s' % table
    """

    name = "name"
    if table[-1:].isupper():
        name = "NAME"

    id_column = id_column or 'id_%s' % table
    if id_column:
        id_column = wash_table_column_name(id_column)
    try:
        for nr in range(0, len(langs)):
            res = run_sql("SELECT value FROM %s%s WHERE %s=%%s AND type=%%s AND ln=%%s" % (table, name, id_column),
                          (ID, sel_type, langs[nr][0]))
            if res:
                if trans[nr]:
                    res = run_sql("UPDATE %s%s SET value=%%s WHERE %s=%%s AND type=%%s AND ln=%%s" % (table, name, id_column),
                                  (trans[nr], ID, sel_type, langs[nr][0]))
                else:
                    res = run_sql("DELETE FROM %s%s WHERE %s=%%s AND type=%%s AND ln=%%s" % (table, name, id_column),
                                  (ID, sel_type, langs[nr][0]))
            else:
                if trans[nr]:
                    res = run_sql("INSERT INTO %s%s (%s, type, ln, value) VALUES (%%s,%%s,%%s,%%s)" % (table, name, id_column),
                                  (ID, sel_type, langs[nr][0], trans[nr]))
        return (1, "")
    except StandardError as e:
        return (0, e)


def write_outcome(res):
    """
    Write the outcome of an update of some settings.

    Parameter 'res' is a tuple (int, str), where 'int' is 0 when there
    is an error to display, and 1 when everything went fine. 'str' is
    a message displayed when there is an error.
    """

    if res and res[0] == 1:
        return """<b><span class="info">Operation successfully completed.</span></b>"""
    elif res:
        return """<b><span class="info">Operation failed. Reason:</span></b><br />%s""" % res[1]
