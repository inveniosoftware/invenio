## $Id$

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

__revision__ = "$Id$"

## import interesting modules:
import string
import os
import sys
import time
import types
import re
import shutil
from mod_python import apache

from invenio.config import \
     bibconvert, \
     cdslang, \
     cdsname, \
     images, \
     pylibdir, \
     storage, \
     urlpath, \
     version, \
     weburl
from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_admin import acc_isRole
from invenio.webpage import page, create_error_box
from invenio.webuser import getUid, get_email
from invenio.websubmit_config import *
from invenio.file import *

from invenio.messages import gettext_set_language, wash_language
import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def interface(req, c=cdsname, ln=cdslang, doctype="", act="", startPg=1, indir="", access="", mainmenu="", fromdir="", file="", nextPg="", nbPg="", curpage=1):
    ln = wash_language(ln)

    # load the right message language
    _ = gettext_set_language(ln)

    sys.stdout = req
    # get user ID:
    try:
        uid = getUid(req)
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value, req, c, ln)
    # variable initialisation
    t = ""
    field = []
    fieldhtml = []
    level = []
    fullDesc = []
    text = []
    check = []
    select = []
    radio = []
    upload = []
    txt = []
    noPage = []
    # Preliminary tasks
    # check that the user is logged in
    if uid_email == "" or uid_email == "guest":
        return warningMsg(websubmit_templates.tmpl_warning_message(
                           ln = ln,
                           msg = _("Sorry, you must log in to perform this action.")
                         ), req, ln)
        # warningMsg("""<center><font color="red"></font></center>""",req, ln)
    # check we have minimum fields
    if doctype=="" or act=="" or access=="":
        return errorMsg(_("Invalid parameter"), req, c, ln)
    # retrieve the action and doctype data
    if indir == "":
        res = run_sql("select dir from sbmACTION where sactname=%s", (act,))
        if len(res) == 0:
            return errorMsg(_("Unable to find the submission directory."), req, c, ln)
        else:
            row = res[0]
            indir = row[0]
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE sdocname=%s", (doctype,))
    if len(res) == 0:
        return errorMsg(_("Unknown document type"), req, c, ln)
    else:
        docname = res[0][0]
        docname = string.replace(docname, " ", "&nbsp;")
    res = run_sql("SELECT lactname FROM sbmACTION WHERE sactname=%s", (act,))
    if len(res) == 0:
        return errorMsg(_("Unknown action"), req, c, ln)
    else:
        actname = res[0][0]
        actname = string.replace(actname, " ", "&nbsp;")
    subname = "%s%s" % (act, doctype)
    res = run_sql("SELECT nbpg FROM sbmIMPLEMENT WHERE  subname=%s", (subname,))
    if len(res) == 0:
        return errorMsg(_("Unable to determine the number of submission pages."), req, c, ln)
    else:
        nbpages = res[0][0]
    #Get current page
    if startPg != "" and (curpage=="" or curpage==0):
        curpage = startPg
    # retrieve the name of the file in which the reference of
    # the submitted document will be stored
    res = run_sql("SELECT value FROM sbmPARAMETERS WHERE  doctype=%s and name='edsrn'", (doctype,))
    if len(res) == 0:
        edsrn = ""
    else:
        edsrn = res[0][0]
    # This defines the path to the directory containing the action data
    curdir = "%s/%s/%s/%s" % (storage, indir, doctype, access)
    # if this submission comes from another one ($fromdir is then set)
    # We retrieve the previous submission directory and put it in the proper one
    if fromdir != "":
        olddir = "%s/%s/%s/%s" % (storage, fromdir, doctype, access)
        if os.path.exists(olddir):
            os.rename(olddir, curdir)
    # If the submission directory still does not exist, we create it
    if not os.path.exists(curdir):
        try:
            os.makedirs(curdir)
        except:
            return errorMsg(_("Unable to create a directory for this submission."), req, c, ln)
    # retrieve the original main menu url ans save it in the "mainmenu" file
    if mainmenu != "":
        fp = open("%s/mainmenu" % curdir, "w")
        fp.write(mainmenu)
        fp.close()
    # and if the file containing the URL to the main menu exists
    # we retrieve it and store it in the $mainmenu variable
    if os.path.exists("%s/mainmenu" % curdir):
        fp = open("%s/mainmenu" % curdir, "r");
        mainmenu = fp.read()
        fp.close()
    else:
        mainmenu = "%s/submit" % (urlpath,)
    # various authentication related tasks...
    if uid_email != "guest" and uid_email != "":
        #First save the username (email address) in the SuE file. This way bibconvert will be able to use it if needed
        fp = open("%s/SuE" % curdir, "w")
        fp.write(uid_email)
        fp.close()
    # is user authorized to perform this action?
    (auth_code, auth_message) = acc_authorize_action(uid, "submit", verbose=0, doctype=doctype, act=act)
    if acc_isRole("submit", doctype=doctype, act=act) and auth_code != 0:
        return warningMsg("<center><font color=red>%s</font></center>" % auth_message, req)
    # then we update the "journal of submission"
    res = run_sql("SELECT * FROM sbmSUBMISSIONS WHERE  doctype=%s and action=%s and id=%s and email=%s", (doctype, act, access, uid_email,))
    if len(res) == 0:
        run_sql("INSERT INTO sbmSUBMISSIONS values (%s,%s,%s,'pending',%s,'',NOW(),NOW())", (uid_email, doctype, act, access,))
    else:
        run_sql("UPDATE sbmSUBMISSIONS SET md=NOW() WHERE  doctype=%s and action=%s and id=%s and email=%s", (doctype, act, access, uid_email,))
    # Save the form fields entered in the previous submission page
    # If the form was sent with the GET method
    form = req.form
    value = ""
    # we parse all the form variables
    for key in form.keys():
        formfields = form[key]
        if re.search("\[\]", key):
            filename = key.replace("[]", "")
        else:
            filename = key
        # the field is an array
        if isinstance(formfields, types.ListType):
            fp = open("%s/%s" % (curdir, filename), "w")
            for formfield in formfields:
                #stripslashes(value)
                value = specialchars(formfield)
                fp.write(value+"\n")
            fp.close()
        # the field is a normal string
        elif isinstance(formfields, types.StringTypes) and formfields != "":
            value = formfields
            fp = open("%s/%s" % (curdir, filename), "w")
            fp.write(specialchars(value))
            fp.close()
        # the field is a file
        elif hasattr(formfields,"filename"):
            if not os.path.exists("%s/files/%s" % (curdir, key)):
                try:
                    os.makedirs("%s/files/%s" % (curdir, key))
                except:
                    return errorMsg(_("Cannot create submission directory."), req, c, ln)
            filename = formfields.filename
            if filename != "":
                # This may be dangerous if the file size is bigger than the available memory
                data = formfields.file.read()
                fp = open("%s/files/%s/%s" % (curdir, key, filename), "w")
                fp.write(data)
                fp.close()
                fp = open("%s/lastuploadedfile" % curdir, "w")
                fp.write(filename)
                fp.close()
                fp = open("%s/%s" % (curdir, key), "w")
                fp.write(filename)
                fp.close()
        # if the found field is the reference of the document
        # we save this value in the "journal of submissions"
        if uid_email != "" and uid_email != "guest":
            if key == edsrn:
                run_sql("UPDATE sbmSUBMISSIONS SET reference=%s WHERE  doctype=%s and id=%s and email=%s", (value, doctype, access, uid_email,))
        # Now deal with the cookies
        # If the fields must be saved as a cookie, we do so
        # In this case, the value of the field will be retrieved and
        # displayed as the default value of the field next time the user
        # does a submission
        if value!="":
            res = run_sql("SELECT cookie FROM sbmFIELDDESC WHERE  name=%s", (key,))
            if len(res) > 0:
                if res[0][0] == 1:
                    setCookie(key, value, uid)

    # create interface
    # For each field to be displayed on the page
    subname = "%s%s" % (act, doctype)
    res = run_sql("SELECT * FROM sbmFIELD WHERE  subname=%s and pagenb=%s ORDER BY fieldnb,fieldnb", (subname, curpage,))

    full_fields = []
    values = []
    for arr in res:
        full_field = {}
        # We retrieve its HTML description
        res3 = run_sql("SELECT * FROM sbmFIELDDESC WHERE  name=%s", (arr[3],))
        arr3 = res3[0]
        if arr3[8]==None:
            val=""
        else:
            val=arr3[8]
        # we also retrieve and add the javascript code of the checking function, if needed
        full_field['javascript'] = ''
        if arr[7] != '':
            res2 = run_sql("SELECT chdesc FROM sbmCHECKS WHERE  chname=%s", (arr[7],))
            full_field['javascript'] = res2[0][0]
        full_field['type'] = arr3[3]
        full_field['name'] = arr[3]
        full_field['rows'] = arr3[5]
        full_field['cols'] = arr3[6]
        full_field['val'] = val
        full_field['size'] = arr3[4]
        full_field['maxlength'] = arr3[7]
        full_field['htmlcode'] = arr3[9]
        full_field['typename'] = arr[1]

        # The 'R' fields must be executed in the engine's environment,
        # as the runtime functions access some global and local
        # variables.
        if full_field ['type'] == 'R':
            co = compile (full_field ['htmlcode'].replace("\r\n","\n"), "<string>", "exec")
            exec(co)
        else:
            text = websubmit_templates.tmpl_submit_field (ln = ln, field = full_field)

        # we now determine the exact type of the created field
        if full_field['type'] not in [ 'D','R']:
            field.append(full_field['name'])
            level.append(arr[5])
            fullDesc.append(arr[4])
            txt.append(arr[6])
            check.append(arr[7])
            # If the field is not user-defined, we try to determine its type
            # (select, radio, file upload...)
            # check whether it is a select field or not
            if re.search("SELECT", text, re.IGNORECASE) != None:
                select.append(1)
            else:
                select.append(0)
            # checks whether it is a radio field or not
            if re.search(r"TYPE=[\"']?radio", text, re.IGNORECASE) != None:
                radio.append(1)
            else:
                radio.append(0)
            # checks whether it is a file upload or not
            if re.search(r"TYPE=[\"']?file", text, re.IGNORECASE) != None:
                upload.append(1)
            else:
                upload.append(0)
            # if the field description contains the "<COMBO>" string, replace
            # it by the category selected on the document page submission page
            combofile = "combo%s" % doctype
            if os.path.exists("%s/%s" % (curdir, combofile)):
                f = open("%s/%s" % (curdir, combofile), "r")
                combo = f.read()
                f.close()
            else:
                combo=""
            text = text.replace("<COMBO>", combo)
            # if there is a <YYYY> tag in it, replace it by the current year
            year = time.strftime("%Y");
            text = text.replace("<YYYY>", year)
            # if there is a <TODAY> tag in it, replace it by the current year
            today = time.strftime("%d/%m/%Y");
            text = text.replace("<TODAY>", today)
            fieldhtml.append(text)
        else:
            select.append(0)
            radio.append(0)
            upload.append(0)
            # field.append(value) - initial version, not working with JS, taking a submitted value
            field.append(arr[3])
            level.append(arr[5])
            txt.append(arr[6])
            fullDesc.append(arr[4])
            check.append(arr[7])
            fieldhtml.append(text)
        full_field['fullDesc'] = arr[4]
        full_field['text'] = text

        # If a file exists with the name of the field we extract the saved value
        text = ''
        if os.path.exists("%s/%s" % (curdir, full_field['name'])):
            file = open("%s/%s" % (curdir, full_field['name']), "r");
            text = file.read()
            text = re.compile("[\n\r]*$").sub("", text)
            text = re.compile("\n").sub("\\n", text)
            text = re.compile("\r").sub("", text)
            file.close()
        # Or if a cookie is set
        # If a cookie is found corresponding to the name of the current
        # field, we set the value of the field to the cookie's value
        elif getCookie(full_field['name'], uid) != None:
            value = getCookie(full_field['name'], uid)
            value = re.compile("\r").sub("", value)
            value = re.compile("\n").sub("\\n", value)
            text = value
        values.append(text)

        full_fields.append(full_field)

    returnto = {}
    if int(curpage) == int(nbpages):
        subname = "%s%s" % (act, doctype)
        res = run_sql("SELECT * FROM sbmFIELD WHERE  subname=%s and pagenb!=%s", (subname, curpage,))
        nbFields = 0
        message = ""
        fullcheck_select = []
        fullcheck_radio = []
        fullcheck_upload = []
        fullcheck_field = []
        fullcheck_level = []
        fullcheck_txt = []
        fullcheck_noPage = []
        fullcheck_check = []
        for arr in res:
            if arr[5] == "M":
                res2 = run_sql("SELECT * FROM   sbmFIELDDESC WHERE  name=%s", (arr[3],));
                row2 = res2[0]
                if row2[3] in ['D','R']:
                    if row2[3] == "D":
                        text = row2[9]
                    else:
                        text = eval(row2[9])
                    formfields = text.split(">")
                    for formfield in formfields:
                        match = re.match("name=([^ <>]+)", formfield, re.IGNORECASE)
                        if match != None:
                            names = match.groups
                            for value in names:
                                if value != "":
                                    value = re.compile("[\"']+").sub("", value)
                                    fullcheck_field.append(value)
                                    fullcheck_level.append(arr[5])
                                    fullcheck_txt.append(arr[6])
                                    fullcheck_noPage.append(arr[1])
                                    fullcheck_check.append(arr[7])
                                    nbFields = nbFields+1
                else:
                    fullcheck_noPage.append(arr[1])
                    fullcheck_field.append(arr[3])
                    fullcheck_level.append(arr[5])
                    fullcheck_txt.append(arr[6])
                    fullcheck_check.append(arr[7])
                    nbFields = nbFields+1
        # tests each mandatory field
        fld = 0
        res = 1
        for i in range (0, nbFields):
            res = 1
            if not os.path.exists("%s/%s" % (curdir, fullcheck_field[i])):
                res=0
            else:
                file = open("%s/%s" % (curdir, fullcheck_field[i]), "r")
                text = file.read()
                if text == '':
                    res=0
                else:
                    if text == "Select:":
                        res=0
            if res == 0:
                fld = i
                break
        if not res:
            returnto = {
                         'field' : fullcheck_txt[fld],
                         'page'  : fullcheck_noPage[fld],
                       }

    t += websubmit_templates.tmpl_page_interface(
          ln = ln,
          docname = docname,
          actname = actname,
          curpage = curpage,
          nbpages = nbpages,
          file = file,
          nextPg = nextPg,
          access = access,
          nbPg = nbPg,
          doctype = doctype,
          act = act,
          indir = indir,
          fields = full_fields,
          javascript = websubmit_templates.tmpl_page_interface_js(
                         ln = ln,
                         upload = upload,
                         field = field,
                         fieldhtml = fieldhtml,
                         txt = txt,
                         check = check,
                         level = level,
                         curdir = curdir,
                         values = values,
                         select = select,
                         radio = radio,
                         curpage = curpage,
                         nbpages = nbpages,
                         images = images,
                         returnto = returnto,
                       ),
          images = images,
          mainmenu = mainmenu,
         )

    # start display:
    req.content_type = "text/html"
    req.send_http_header()
    p_navtrail = """<a href="/submit">%(submit)s</a>&nbsp;>&nbsp;<a href="/submit?doctype=%(doctype)s\">%(docname)s</a>&nbsp;""" % {
                   'submit'  : _("Submit"),
                   'doctype' : doctype,
                   'docname' : docname,
                 }
    return page(title= actname,
                body = t,
                navtrail = p_navtrail,
                description = "submit documents in CDSWare",
                keywords = "submit, CDSWare",
                uid = uid,
                language = ln,
                req = req)


def endaction(req, c=cdsname, ln=cdslang, doctype="", act="", startPg=1, indir="", \
              access="", mainmenu="", fromdir="", file="", nextPg="", nbPg="", curpage=1, step=1, mode="U"):
    global rn, sysno, dismode, curdir, uid, uid_email, last_step, action_score

    # load the right message language
    _ = gettext_set_language(ln)

    try:
        rn
    except NameError:
        rn = ""
    dismode = mode
    ln = wash_language(ln)
    sys.stdout = req
    t=""
    # get user ID:
    try:
        uid = getUid(req)
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value, req, c, ln)
    # Preliminary tasks
    # check that the user is logged in
    if uid_email == "" or uid_email == "guest":
        return warningMsg(websubmit_templates.tmpl_warning_message(
                           ln = ln,
                           msg = _("Sorry, you must log in to perform this action.")
                         ), req, ln)
    # check we have minimum fields
    if doctype=="" or act=="" or access=="":
        return errorMsg(_("Invalid parameter"), req, c, ln)
    # retrieve the action and doctype data
    if indir == "":
        res = run_sql("select dir from sbmACTION where sactname=%s", (act,))
        if len(res) == 0:
            return errorMsg(_("Cannot find submission directory."), req, c, ln)
        else:
            row = res[0]
            indir = row[0]
    # The following words are reserved and should not be used as field names
    reserved_words = ["stop", "file", "nextPg", "startPg", "access", "curpage", "nbPg", "act", \
                      "indir", "doctype", "mode", "step", "deleted", "file_path", "userfile_name"]
    # This defines the path to the directory containing the action data
    curdir = "%s/%s/%s/%s" % (storage, indir, doctype, access)
    # If the submission directory still does not exist, we create it
    if not os.path.exists(curdir):
        try:
            os.makedirs(curdir)
        except:
            return errorMsg(_("Cannot create submission directory."), req, c, ln)
    # retrieve the original main menu url ans save it in the "mainmenu" file
    if mainmenu != "":
        fp = open("%s/mainmenu" % curdir, "w")
        fp.write(mainmenu)
        fp.close()
    # and if the file containing the URL to the main menu exists
    # we retrieve it and store it in the $mainmenu variable
    if os.path.exists("%s/mainmenu" % curdir):
        fp = open("%s/mainmenu" % curdir, "r");
        mainmenu = fp.read()
        fp.close()
    else:
        mainmenu = "%s/submit" % (urlpath,)
    # retrieve the name of the file in which the reference of
    # the submitted document will be stored
    res = run_sql("SELECT value FROM sbmPARAMETERS WHERE  doctype=%s and name='edsrn'", (doctype,))
    if len(res) == 0:
        edsrn = ""
    else:
        edsrn = res[0][0]
    # Now we test whether the user has already completed the action and
    # reloaded the page (in this case we don't want the functions to be called
    # once again
    # reloaded = Test_Reload(uid_email,doctype,act,access)
    # if the action has been completed
    #if reloaded:
    #    return warningMsg("<b> Sorry, this action has already been completed. Please go back to the main menu to start a new action.</b>",req)
    # We must determine if the action is finished (ie there is no other steps after the current one
    res = run_sql("SELECT step FROM sbmFUNCTIONS WHERE  action=%s and doctype=%s and step > %s", (act, doctype, step,))
    if len(res) == 0:
        finished = 1
    else:
        finished = 0
    # Save the form fields entered in the previous submission page
    # If the form was sent with the GET method
    form = req.form
    value = ""
    # we parse all the form variables
    for key in form.keys():
        formfields = form[key]
        if re.search("\[\]", key):
            filename = key.replace("[]", "")
        else:
            filename = key
        # the field is an array
        if isinstance(formfields,types.ListType):
            fp = open("%s/%s" % (curdir, filename), "w")
            for formfield in formfields:
                #stripslashes(value)
                value = specialchars(formfield)
                fp.write(value+"\n")
            fp.close()
        # the field is a normal string
        elif isinstance(formfields, types.StringTypes) and formfields != "":
            value = formfields
            fp = open("%s/%s" % (curdir, filename), "w")
            fp.write(specialchars(value))
            fp.close()
        # the field is a file
        elif hasattr(formfields, "filename"):
            if not os.path.exists("%s/files/%s" % (curdir, key)):
                try:
                    os.makedirs("%s/files/%s" % (curdir, key))
                except:
                    return errorMsg("can't create submission directory", req, cdsname, ln)
            filename = formfields.filename
            if filename != "":
                # This may be dangerous if the file size is bigger than the available memory
                data = formfields.file.read()
                fp = open("%s/files/%s/%s" % (curdir, key, filename), "w")
                fp.write(data)
                fp.close()
                fp = open("%s/lastuploadedfile" % curdir, "w")
                fp.write(filename)
                fp.close()
                fp = open("%s/%s" % (curdir, key), "w")
                fp.write(filename)
                fp.close()
        # if the found field is the reference of the document
        # we save this value in the "journal of submissions"
        if uid_email != "" and uid_email != "guest":
            if key == edsrn:
                run_sql("UPDATE sbmSUBMISSIONS SET reference=%s WHERE  doctype=%s and id=%s and email=%s", (value, doctype, access, uid_email,))
        # Now deal with the cookies
        # If the fields must be saved as a cookie, we do so
        # In this case, the value of the field will be retrieved and
        # displayed as the default value of the field next time the user
        # does a submission
        if value!="":
            res = run_sql("SELECT cookie FROM sbmFIELDDESC WHERE  name=%s", (key,))
            if len(res) > 0:
                if res[0][0] == 1:
                    setCookie(key, value, uid)

    # Get document name
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE  sdocname=%s", (doctype,))
    if len(res) > 0:
       docname = res[0][0]
    else:
        return errorMsg(_("Unknown type of document"), req, cdsname, ln)
    # Get action name
    res = run_sql("SELECT lactname FROM sbmACTION WHERE  sactname=%s", (act,))
    if len(res) > 0:
       actname = res[0][0]
    else:
        return errorMsg(_("Unknown action"), req, cdsname, ln)
    # Get number of pages
    subname = "%s%s" % (act, doctype)
    res = run_sql("SELECT nbpg FROM sbmIMPLEMENT WHERE  subname=%s", (subname,))
    if len(res) > 0:
       nbpages = res[0][0]
    else:
        return errorMsg(_("This action does not exist for this document type."), req, cdsname, ln)

    # we specify here whether we are in the last step of the action or not
    res = run_sql("SELECT step FROM   sbmFUNCTIONS WHERE  action=%s and doctype=%s and step>%s", (act, doctype, step,))
    if len(res) == 0:
        last_step = 1
    else:
        last_step = 0

    # Prints the action details, returning the mandatory score
    action_score = action_details(doctype, act)
    current_level = get_level(doctype, act)

    # Calls all the function's actions
    function_content = ''
    try:
        function_content = print_function_calls(doctype=doctype, action=act, step=step, form=form, ln=ln)
    except functionError,e:
        return errorMsg(e.value, req, c, ln)
    except functionStop,e:
        if e.value != None:
            function_content = e.value
        else:
            function_content = e

    # If the action was mandatory we propose the next mandatory action (if any)
    next_action = ''
    if action_score != -1 and last_step == 1:
        next_action = Propose_Next_Action(doctype, action_score, access, current_level, indir)

    # If we are in the last step of an action, we can update the "journal of submissions"
    if last_step == 1:
        if uid_email != "" and uid_email != "guest" and rn != "":
            res = run_sql("SELECT * FROM sbmSUBMISSIONS WHERE  doctype=%s and action=%s and id=%s and email=%s", (doctype, act, access, uid_email,))
            if len(res) == 0:
                run_sql("INSERT INTO sbmSUBMISSIONS values(%s,%s,%s,'finished',%s,%s,NOW(),NOW())", (uid_email, doctype, act, access, rn,))
            else:
               run_sql("UPDATE sbmSUBMISSIONS SET md=NOW(),reference=%s,status='finished' WHERE  doctype=%s and action=%s and id=%s and email=%s", (rn, doctype, act, access, uid_email,))

    t = websubmit_templates.tmpl_page_endaction(
          ln = ln,
          weburl = weburl,
          # these fields are necessary for the navigation
          file = file,
          nextPg = nextPg,
          startPg = startPg,
          access = access,
          curpage = curpage,
          nbPg = nbPg,
          nbpages = nbpages,
          doctype = doctype,
          act = act,
          docname = docname,
          actname = actname,
          indir = indir,
          mainmenu = mainmenu,
          finished = finished,
          images = images,
          function_content = function_content,
          next_action = next_action,
        )

    # start display:
    req.content_type = "text/html"
    req.send_http_header()

    p_navtrail = """<a href="/submit">""" + _("Submit") +\
                 """</a>&nbsp;>&nbsp;<a href="/submit?doctype=%(doctype)s">%(docname)s</a>""" % {
                   'doctype' : doctype,
                   'docname' : docname,
                 }
    return page(title= actname,
                body = t,
                navtrail = p_navtrail,
                description="submit documents in CDSWare",
                keywords="submit, CDSWare",
                uid = uid,
                language = ln,
                req = req)

def home(req, c=cdsname, ln=cdslang):
    """
       Generates and displays the default "home page" for Web-submit - contains a list of links to the various document submissions.
    """
    ln = wash_language(ln)
    # get user ID:
    try:
        uid = getUid(req)
    except Error, e:
        return errorMsg(e.value)
    # start display:
    req.content_type = "text/html"
    req.send_http_header()

    # load the right message language
    _ = gettext_set_language(ln)

    finaltext = websubmit_templates.tmpl_submit_home_page(
                    ln = ln,
                    catalogues = makeCataloguesTable(ln)
                )

    return page(title=_("Submit"),
               body=finaltext,
               navtrail=[],
               description="submit documents in CDSWare",
               keywords="submit, CDSWare",
               uid=uid,
               language=ln,
               req=req
               )

def makeCataloguesTable(ln=cdslang):
    text = ""
    catalogues = []
    queryResult = run_sql("SELECT id_son FROM sbmCOLLECTION_sbmCOLLECTION WHERE id_father=0 ORDER BY catalogue_order");
    if len(queryResult) != 0:
        # Query has executed successfully, so we can proceed to display all
        # catalogues in the EDS system...
        for row in queryResult:
            catalogues.append(getCatalogueBranch(row[0], 1))

        text = websubmit_templates.tmpl_submit_home_catalogs(
                 ln = ln,
                 catalogs = catalogues
               )
    else:
        text = websubmit_templates.tmpl_submit_home_catalog_no_content(ln = ln)
    return text

def getCatalogueBranch(id_father, level):
    elem = {}
    queryResult = run_sql("SELECT name, id FROM   sbmCOLLECTION WHERE  id=%s", (id_father,))
    if len(queryResult) != 0:
        row = queryResult[0]
        elem['name'] = row[0]
        elem['id'] = row[1]
        elem['level'] = level
    # display the son document types
    elem['docs'] = []
    res1 = run_sql("SELECT id_son FROM   sbmCOLLECTION_sbmDOCTYPE WHERE  id_father=%s ORDER BY catalogue_order", (id_father,))
    if len(res1) != 0:
        for row in res1:
            elem['docs'].append(getDoctypeBranch(row[0]))

    elem['sons'] = []
    res2 = run_sql("SELECT id_son FROM   sbmCOLLECTION_sbmCOLLECTION WHERE  id_father=%s ORDER BY catalogue_order", (id_father,))
    if len(res2) != 0:
        for row in res2:
            elem['sons'].append(getCatalogueBranch(row[0], level + 1))

    return elem

def getDoctypeBranch(doctype):
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE  sdocname=%s", (doctype,))
    return {'id' : doctype,
            'name' : res[0][0],
           }

def displayCatalogueBranch(id_father, level, catalogues):
    text = ""
    queryResult = run_sql("SELECT name, id FROM   sbmCOLLECTION WHERE  id=%s", (id_father,))
    if len(queryResult) != 0:
        row = queryResult[0]
        if level == 1:
            text = "<LI><font size=\"+1\"><strong>%s</strong></font>\n" % row[0]
        else:
            if level == 2:
                text = "<LI>%s\n" % row[0]
            else:
                if level > 2:
                    text = "<LI>%s\n" % row[0]
    # display the son document types
    res1 = run_sql("SELECT id_son FROM   sbmCOLLECTION_sbmDOCTYPE WHERE  id_father=%s ORDER BY catalogue_order", (id_father,))
    res2 = run_sql("SELECT id_son FROM   sbmCOLLECTION_sbmCOLLECTION WHERE  id_father=%s ORDER BY catalogue_order", (id_father,))
    if len(res1) != 0 or len(res2) != 0:
        text = text + "<UL>\n"
    if len(res1) != 0:
        for row in res1:
            text = text + displayDoctypeBranch(row[0], catalogues)
    # display the son catalogues
    for row in res2:
        catalogues.append(row[0])
        text = text + displayCatalogueBranch(row[0], level+1, catalogues)
    if len(res1) != 0 or len(res2) != 0:
        text = text + "</UL>\n"
    return text



def displayDoctypeBranch(doctype, catalogues):
    text = ""
    res = run_sql("SELECT ldocname FROM sbmDOCTYPE WHERE  sdocname=%s", (doctype,))
    row = res[0]
    text = "<LI><a href=\"\" onmouseover=\"javascript:popUpTextWindow('%s',true,event);\" onmouseout=\"javascript:popUpTextWindow('%s',false,event);\" onClick=\"document.forms[0].doctype.value='%s';document.forms[0].submit();return false;\">%s</a>\n" % (doctype, doctype, doctype, row[0])
    return text


def action(req, c=cdsname, ln=cdslang, doctype=""):
    # load the right message language
    _ = gettext_set_language(ln)

    nbCateg = 0
    snameCateg = []
    lnameCateg = []
    actionShortDesc = []
    indir = []
    actionbutton = []
    statustext = []
    t = ""
    ln = wash_language(ln)
    # get user ID:
    try:
        uid = getUid(req)
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e.value, req, ln)
    #parses database to get all data
    #first the list of categories
    res = run_sql("SELECT * FROM sbmCATEGORIES WHERE  doctype=%s ORDER BY score ASC, lname ASC", (doctype,))
    if len(res) > 0:
        for arr in res:
            nbCateg = nbCateg+1
            snameCateg.append(arr[1])
            lnameCateg.append(arr[2])
    #then data about the document type
    res = run_sql("SELECT * FROM sbmDOCTYPE WHERE  sdocname=%s", (doctype,))
    if len(res) > 0:
        arr = res[0]
        docFullDesc = arr[0]
        docShortDesc = arr[1]
        description = arr[4]
    else:
        return errorMsg (_("Unable to find document type.") + str(doctype), req)
    #then data about associated actions
    res2 = run_sql("SELECT * FROM sbmIMPLEMENT LEFT JOIN sbmACTION on sbmACTION.sactname=sbmIMPLEMENT.actname WHERE  docname=%s and displayed='Y' ORDER BY sbmIMPLEMENT.buttonorder", (docShortDesc,))
    for arr2 in res2:
        res = run_sql("SELECT * FROM   sbmACTION WHERE  sactname=%s", (arr2[1],))
        for arr in res:
            actionShortDesc.append(arr[1])
            indir.append(arr[2])
            actionbutton.append(arr[5])
            statustext.append(arr[6])

    t = websubmit_templates.tmpl_action_page(
          ln=ln,
          uid=uid, guest=(uid_email == "" or uid_email == "guest"),
          pid = os.getpid(),
          now = time.time(),
          doctype = doctype,
          description = description,
          docfulldesc = docFullDesc,
          snameCateg = snameCateg,
          lnameCateg = lnameCateg,
          actionShortDesc = actionShortDesc,
          indir = indir,
          # actionbutton = actionbutton,
          statustext = statustext,
        )
    
    p_navtrail = """<a href="/submit">%(submit)s</a>""" % {'submit' : _("Submit")}
    
    return page(title = docFullDesc,
                body=t,
                navtrail=p_navtrail,
                description="submit documents in CDSWare",
                keywords="submit, CDSWare",
                uid=uid,
                language=ln,
                req=req
               )


def set_report_number (newrn):
        global uid_email, doctype, access, rn
        # First we save the value in the global object
        rn = newrn
        # then we save this value in the "journal of submissions"
        if uid_email != "" and uid_email != "guest":
            run_sql("UPDATE sbmSUBMISSIONS SET reference=%s WHERE  doctype=%s and id=%s and email=%s", (newrn, doctype, access, uid_email,))

def get_report_number():
    global rn
    return rn

def set_sysno (newsn) :
    global sysno
    sysno = newsn

def get_sysno() :
    global sysno
    return sysno

def Request_Print(m, txt):
    # The argumemts to this function are the display mode (m) and the text to be displayed (txt)
    # If the argument mode is 'ALL' then the text is unconditionally echoed
    # m can also take values S (Supervisor Mode) and U (User Mode). In these
    # circumstances txt is only echoed if the argument mode is the same as
    # the current mode
    global dismode
    if m == "A" or m == dismode:
        return txt
    else:
        return ""

def Evaluate_Parameter (field, doctype):
    # Returns the literal value of the parameter. Assumes that the value is
    # uniquely determined by the doctype, i.e. doctype is the primary key in
    # the table
    # If the table name is not null, evaluate the parameter
    res = run_sql("SELECT value FROM sbmPARAMETERS WHERE doctype=%s and name=%s", (doctype, field,))
    # If no data is found then the data concerning the DEF(ault) doctype is used
    if len(res) == 0:
        res = run_sql("SELECT value FROM sbmPARAMETERS WHERE doctype='DEF' and name=%s", (field,))
    if len(res) == 0:
        return ""
    else:
        if res[0][0] != None:
            return res[0][0]
        else:
            return ""

def Get_Parameters (function, doctype):
    # Returns the function parameters, in an array, for the function
    # Gets a description of the parameter
    parray = {}
    res = run_sql("SELECT * FROM sbmFUNDESC WHERE function=%s", (function,))
    for i in range(0,len(res)):
        parameter = res[i][1]
        parray[parameter] = Evaluate_Parameter (parameter, doctype)
    return parray

def get_level (doctype, action):
    res = run_sql("SELECT * FROM sbmIMPLEMENT WHERE docname=%s and actname=%s", (doctype, action,))
    if len(res) > 0:
        return res[0][9]
    else:
        return 0

def action_details (doctype, action):
    # Prints whether the action is mandatory or optional. The score of the
    # action is returned (-1 if the action was optional)
    res = run_sql("SELECT * FROM sbmIMPLEMENT WHERE docname=%s and actname=%s", (doctype, action,))
    if len(res)>0:
        if res[0][9] != "0":
            return res[0][10]
        else:
            return -1
    else:
        return -1

def print_function_calls (doctype, action, step, form, ln=cdslang):
    # Calls the functions required by an "action" action on a "doctype" document
    # In supervisor mode, a table of the function calls is produced
    global htdocsdir,storage,access,pylibdir,dismode
    t=""
    # Get the list of functions to be called
    res = run_sql("SELECT * FROM sbmFUNCTIONS WHERE action=%s and doctype=%s and step=%s ORDER BY score", (action, doctype, step,))
    # If no data is found then the data concerning the DEF(ault) doctype is used
    if len(res) == 0:
        res = run_sql("SELECT * FROM sbmFUNCTIONS WHERE action=%s and doctype='DEF' and step=%s ORDER BY score", (action, step,))
    if len(res) > 0:
        # while there are functions left...
        functions = []
        for function in res:
            function_name = function[2]
            function_score = function[3]
            currfunction = {
              'name' : function_name,
              'score' : function_score,
              'error' : 0,
              'text' : '',
            }
            if os.path.exists("%s/invenio/websubmit_functions/%s.py" % (pylibdir, function_name)):
                # import the function itself
                #function = getattr(invenio.websubmit_functions, function_name)
                execfile("%s/invenio/websubmit_functions/%s.py" % (pylibdir, function_name), globals())
                if not globals().has_key(function_name):
                    currfunction['error'] = 1
                else:
                    function = globals()[function_name]
                    # Evaluate the parameters, and place them in an array
                    parameters = Get_Parameters(function_name, doctype)
                    # Call function
                    currfunction['text'] = function(parameters, curdir, form)
            else:
                currfunction['error'] = 1
            functions.append(currfunction)

        t = websubmit_templates.tmpl_function_output(
              ln = ln,
              display_on = (dismode == 'S'),
              action = action,
              doctype = doctype,
              step = step,
              functions = functions,
            )
    else :
        if dismode == 'S':
            t = "<br /><br /><b>" + _("The chosen action is not supported by the document type.") + "</b>"
    return t

def Propose_Next_Action (doctype, action_score, access, currentlevel, indir, ln=cdslang):
    global machine, storage, act, rn
    t=""
    res = run_sql("SELECT * FROM sbmIMPLEMENT WHERE docname=%s and level!='0' and level=%s and score>%s ORDER BY score", (doctype, currentlevel, action_score,))
    if len(res) > 0:
        actions = []
        first_score = res[0][10]
        for i in range(0,len(res)):
            action = res[i]
            if action[10] == first_score:
                res2 = run_sql("SELECT dir FROM sbmACTION WHERE sactname=%s", (action[1],))
                nextdir = res2[0][0]
                curraction = {
                  'page' : action[11],
                  'action' : action[1],
                  'doctype' : doctype,
                  'nextdir' : nextdir,
                  'access' : access,
                  'indir' : indir,
                  'name' : action[12],
                }
                actions.append(curraction)

        t = websubmit_templates.tmpl_next_action(
              ln = ln,
              actions = actions,
            )
    return t

def Test_Reload(uid_email, doctype, act, access):
    res = run_sql("SELECT * FROM sbmSUBMISSIONS WHERE doctype=%s and action=%s and id=%s and email=%s and status='finished'", (doctype, act, access, uid_email,))
    if len(res) > 0:
        return 1
    else:
        return 0

class functionError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class functionStop(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def errorMsg(title, req, c=cdsname, ln=cdslang):
    # load the right message language
    _ = gettext_set_language(ln)

    return page(title = _("Error"),
                body = create_error_box(req, title=title, verbose=0, ln=ln),
                description="%s - Internal Error" % c,
                keywords="%s, CDS Invenio, Internal Error" % c,
                language=ln,
                req=req)

def warningMsg(title, req, c=cdsname, ln=cdslang):
    # load the right message language
    _ = gettext_set_language(ln)

    return page(title = _("Warning"),
                body = title,
                description="%s - Internal Error" % c,
                keywords="%s, CDS Invenio, Internal Error" % c,
                language=ln,
                req=req)

def getCookie(name, uid):
    # these are not real http cookies but are stored in the DB
    res = run_sql("select value from sbmCOOKIES where uid=%s and name=%s", (uid, name,))
    if len(res) > 0:
        return res[0][0]
    else:
        return None

def setCookie(name, value, uid):
    # these are not real http cookies but are stored in the DB
    res = run_sql("select id from sbmCOOKIES where uid=%s and name=%s", (uid, name,))
    if len(res) > 0:
        run_sql("update sbmCOOKIES set value=%s where uid=%s and name=%s", (value, uid, name,))
    else:
        run_sql("insert into sbmCOOKIES(name,value,uid) values(%s,%s,%s)", (name, value, uid,))
    return 1

def specialchars(text):
    text = string.replace(text, "&#147;", "\042");
    text = string.replace(text, "&#148;", "\042");
    text = string.replace(text, "&#146;", "\047");
    text = string.replace(text, "&#151;", "\055");
    text = string.replace(text, "&#133;", "\056\056\056");
    return text
