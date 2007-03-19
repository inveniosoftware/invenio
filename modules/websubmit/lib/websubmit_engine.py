## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""WebSubmit: the mechanism for the submission of new records into CDS Invenio
   via a Web interface.
"""

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

from websubmit_dblayer import \
     get_storage_directory_of_action, \
     get_longname_of_doctype, \
     get_longname_of_action, \
     get_num_pages_of_submission, \
     get_parameter_value_for_doctype, \
     submission_exists_in_log, \
     log_new_pending_submission, \
     log_new_completed_submission, \
     update_submission_modified_date_in_log, \
     update_submission_reference_in_log, \
     update_submission_reference_and_status_in_log, \
     get_form_fields_on_submission_page, \
     get_element_description, \
     get_element_check_description, \
     get_form_fields_not_on_submission_page, \
     function_step_is_last, \
     get_collection_children_of_submission_collection, \
     get_submission_collection_name, \
     get_doctype_children_of_submission_collection, \
     get_categories_of_doctype, \
     get_doctype_details, \
     get_actions_on_submission_page_for_doctype, \
     get_action_details, \
     get_parameters_of_function, \
     get_details_of_submission, \
     get_functions_for_submission_step, \
     get_submissions_at_level_X_with_score_above_N, \
     submission_is_finished

import invenio.template
websubmit_templates = invenio.template.load('websubmit')

def interface(req,
              c=cdsname,
              ln=cdslang,
              doctype="",
              act="",
              startPg=1,
              indir="",
              access="",
              mainmenu="",
              fromdir="",
              file="",
              nextPg="",
              nbPg="",
              curpage=1):
    """This function is called after a user has visited a document type's
       "homepage" and selected the type of "action" to perform. Having
       clicked an action-button (e.g. "Submit a New Record"), this function
       will be called . It performs the task of initialising a new submission
       session (retrieving information about the submission, creating a
       working submission-directory, etc), and "drawing" a submission page
       containing the WebSubmit form that the user uses to input the metadata
       to be submitted.
       When a user moves between pages in the submission interface, this
       function is recalled so that it can save the metadata entered into the
       previous page by the user, and draw the current submission-page.

       Note: During a submission, for each page refresh, this function will be
       called while the variable "step" (a form variable, seen by
       websubmit_webinterface, which calls this function) is 0 (ZERO).

       In other words, this function handles the FRONT-END phase of a
       submission, BEFORE the WebSubmit functions are called.

       @param req: (apache request object) *** NOTE: Added into this object, is
        a variable called "form" (req.form). This is added into the object in
        the index function of websubmit_webinterface. It contains a
        "mod_python.util.FieldStorage" instance, that contains the form-fields
        found on the previous submission page.
       @param c: (string), defaulted to cdsname. The name of the CDS Invenio
        installation.
       @param ln: (string), defaulted to cdslang. The language in which to
        display the pages.
       @param doctype: (string) - the doctype ID of the doctype for which the
        submission is being made.
       @param act: (string) - The ID of the action being performed (e.g.
        submission of bibliographic information; modification of bibliographic
        information, etc).
       @param startPg: (integer) - Starting page for the submission? Defaults
        to 1.
       @param indir: (string) - the directory used to store all submissions
        of the given "type" of this submission. For example, if the submission
        is of the type "modify bibliographic information", this variable would
        contain "modify".
       @param access: (string) - the "access" number for the submission
        (e.g. 1174062451_7010). This number is also used as the name for the
        current working submission directory.
       @param mainmenu: (string) - contains the URL (minus the CDS Invenio
        home stem) for the submission's home-page. (E.g. If this submission
        is "PICT", the "mainmenu" file would contain "/submit?doctype=PICT".
       @param fromdir: (integer)
       @param file: (string)
       @param nextPg: (string)
       @param nbPg: (string)
       @param curpage: (integer) - the current submission page number. Defaults
        to 1.
    """

    ln = wash_language(ln)

    # load the right message language
    _ = gettext_set_language(ln)

    sys.stdout = req
    # get user ID:
    try:
        uid = getUid(req)
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e, req, c, ln)
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
    if "" in (doctype, act, access):
        ## We don't have all the necessary information to go ahead
        ## with this submission:
        return errorMsg(_("Invalid parameter"), req, c, ln)

    ## retrieve the action and doctype data:

    ## Concatenate action ID and doctype ID to make the submission ID:
    subname = "%s%s" % (act, doctype)

    if indir == "":
        ## Get the submission storage directory from the DB:
        submission_dir = get_storage_directory_of_action(act)
        if submission_dir not in ("", None):
            indir = submission_dir
        else:
            ## Unable to determine the submission-directory:
            return errorMsg(_("Unable to find the submission directory."), req, c, ln)

    ## get the document type's long-name:
    doctype_lname = get_longname_of_doctype(doctype)
    if doctype_lname is not None:
        ## Got the doctype long-name: replace spaces with HTML chars:
        docname = doctype_lname.replace(" ", "&nbsp;")
    else:
        ## Unknown document type:
        return errorMsg(_("Unknown document type"), req, c, ln)

    ## get the action's long-name:
    action_lname = get_longname_of_action(act)
    if action_lname is not None:
        ## Got the action long-name: replace spaces with HTML chars:
        actname = action_lname.replace(" ", "&nbsp;")
    else:
        ## Unknown action:
        return errorMsg(_("Unknown action"), req, c, ln)

    ## Get the number of pages for this submission:
    num_submission_pages = get_num_pages_of_submission(subname)
    if num_submission_pages is not None:
        nbpages = num_submission_pages
    else:
        ## Unable to determine the number of pages for this submission:
        return errorMsg(_("Unable to determine the number of submission pages."), req, c, ln)

    ## If unknown, get the current page of submission:
    if startPg != "" and curpage in ("", 0):
        curpage = startPg

    ## retrieve the name of the file in which the reference of
    ## the submitted document will be stored
    rn_filename = get_parameter_value_for_doctype(doctype, "edsrn")
    if rn_filename is not None:
        edsrn = rn_filename
    else:
        ## Unknown value for edsrn - set it to an empty string:
        edsrn = ""

    ## This defines the path to the directory containing the action data
    curdir = "%s/%s/%s/%s" % (storage, indir, doctype, access)

    ## if this submission comes from another one (fromdir is then set)
    ## We retrieve the previous submission directory and put it in the proper one
    if fromdir != "":
        olddir = "%s/%s/%s/%s" % (storage, fromdir, doctype, access)
        if os.path.exists(olddir):
            os.rename(olddir, curdir)
    ## If the submission directory still does not exist, we create it
    if not os.path.exists(curdir):
        try:
            os.makedirs(curdir)
        except:
            return errorMsg(_("Unable to create a directory for this submission."), req, c, ln)
    # retrieve the original main menu url and save it in the "mainmenu" file
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
        return warningMsg("""<center><font color="red">%s</font></center>""" % auth_message, req)

    ## update the "journal of submission":
    ## Does the submission already exist in the log?
    submission_exists = \
         submission_exists_in_log(doctype, act, access, uid_email)
    if submission_exists == 1:
        ## update the modification-date of this submission in the log:
        update_submission_modified_date_in_log(doctype, act, access, uid_email)
    else:
        ## Submission doesn't exist in log - create it:
        log_new_pending_submission(doctype, act, access, uid_email)

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

        ## if the found field is the reference of the document,
        ## save this value in the "journal of submissions":
        if uid_email != "" and uid_email != "guest":
            if key == edsrn:
                update_submission_reference_in_log(doctype, access, uid_email, value)

    ## create the interface:
    subname = "%s%s" % (act, doctype)

    ## Get all of the form fields that appear on this page, ordered by fieldnum:
    form_fields = get_form_fields_on_submission_page(subname, curpage)

    full_fields = []
    values = []

    for field_instance in form_fields:
        full_field = {}
        ## Retrieve the field's description:
        element_descr = get_element_description(field_instance[3])
        if element_descr is None:
            ## The form field doesn't seem to exist - return with error message:
            return \
             errorMsg(_("Unknown form field found on submission page."), \
                      req, c, ln)

        if element_descr[8] is None:
            val = ""
        else:
            val = element_descr[8]

        ## we also retrieve and add the javascript code of the checking function, if needed
        ## Set it to empty string to begin with:
        full_field['javascript'] = ''
        if field_instance[7] != '':
            check_descr = get_element_check_description(field_instance[7])
            if check_descr is not None:
                ## Retrieved the check description:
                full_field['javascript'] = check_descr

        full_field['type'] = element_descr[3]
        full_field['name'] = field_instance[3]
        full_field['rows'] = element_descr[5]
        full_field['cols'] = element_descr[6]
        full_field['val'] = val
        full_field['size'] = element_descr[4]
        full_field['maxlength'] = element_descr[7]
        full_field['htmlcode'] = element_descr[9]
        full_field['typename'] = field_instance[1]  ## TODO: Investigate this, Not used?
                                                    ## It also seems to refer to pagenum.

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
            level.append(field_instance[5])
            fullDesc.append(field_instance[4])
            txt.append(field_instance[6])
            check.append(field_instance[7])
            # If the field is not user-defined, we try to determine its type
            # (select, radio, file upload...)
            # check whether it is a select field or not
            if re.search("SELECT", text, re.IGNORECASE) is not None:
                select.append(1)
            else:
                select.append(0)
            # checks whether it is a radio field or not
            if re.search(r"TYPE=[\"']?radio", text, re.IGNORECASE) is not None:
                radio.append(1)
            else:
                radio.append(0)
            # checks whether it is a file upload or not
            if re.search(r"TYPE=[\"']?file", text, re.IGNORECASE) is not None:
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
            field.append(field_instance[3])
            level.append(field_instance[5])
            txt.append(field_instance[6])
            fullDesc.append(field_instance[4])
            check.append(field_instance[7])
            fieldhtml.append(text)
        full_field['fullDesc'] = field_instance[4]
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

        values.append(text)

        full_fields.append(full_field)

    returnto = {}
    if int(curpage) == int(nbpages):
        subname = "%s%s" % (act, doctype)
        other_form_fields = \
              get_form_fields_not_on_submission_page(subname, curpage)
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
        for field_instance in other_form_fields:
            if field_instance[5] == "M":
                ## If this field is mandatory, get its description:
                element_descr = get_element_description(field_instance[3])
                if element_descr is None:
                    ## The form field doesn't seem to exist - return with error message:
                    return \
                     errorMsg(_("Unknown form field found on one of the submission pages."), \
                              req, c, ln)
                if element_descr[3] in ['D', 'R']:
                    if element_descr[3] == "D":
                        text = element_descr[9]
                    else:
                        text = eval(element_descr[9])
                    formfields = text.split(">")
                    for formfield in formfields:
                        match = re.match("name=([^ <>]+)", formfield, re.IGNORECASE)
                        if match is not None:
                            names = match.groups
                            for value in names:
                                if value != "":
                                    value = re.compile("[\"']+").sub("", value)
                                    fullcheck_field.append(value)
                                    fullcheck_level.append(field_instance[5])
                                    fullcheck_txt.append(field_instance[6])
                                    fullcheck_noPage.append(field_instance[1])
                                    fullcheck_check.append(field_instance[7])
                                    nbFields = nbFields + 1
                else:
                    fullcheck_noPage.append(field_instance[1])
                    fullcheck_field.append(field_instance[3])
                    fullcheck_level.append(field_instance[5])
                    fullcheck_txt.append(field_instance[6])
                    fullcheck_check.append(field_instance[7])
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
                description = "submit documents",
                keywords = "submit",
                uid = uid,
                language = ln,
                req = req)


def endaction(req,
              c=cdsname,
              ln=cdslang,
              doctype="",
              act="",
              startPg=1,
              indir="",
              access="",
              mainmenu="",
              fromdir="",
              file="",
              nextPg="",
              nbPg="",
              curpage=1,
              step=1,
              mode="U"):
    """Having filled-in the WebSubmit form created for metadata by the interface
       function, the user clicks a button to either "finish the submission" or
       to "proceed" to the next stage of the submission. At this point, a
       variable called "step" will be given a value of 1 or above, which means
       that this function is called by websubmit_webinterface.
       So, during all non-zero steps of the submission, this function is called.

       In other words, this function is called during the BACK-END phase of a
       submission, in which WebSubmit *functions* are being called.

       The function first ensures that all of the WebSubmit form field values
       have been saved in the current working submission directory, in text-
       files with the same name as the field elements have. It then determines
       the functions to be called for the given step of the submission, and
       executes them.
       Following this, if this is the last step of the submission, it logs the
       submission as "finished" in the journal of submissions.

       @param req: (apache request object) *** NOTE: Added into this object, is
        a variable called "form" (req.form). This is added into the object in
        the index function of websubmit_webinterface. It contains a
        "mod_python.util.FieldStorage" instance, that contains the form-fields
        found on the previous submission page.
       @param c: (string), defaulted to cdsname. The name of the CDS Invenio
        installation.
       @param ln: (string), defaulted to cdslang. The language in which to
        display the pages.
       @param doctype: (string) - the doctype ID of the doctype for which the
        submission is being made.
       @param act: (string) - The ID of the action being performed (e.g.
        submission of bibliographic information; modification of bibliographic
        information, etc).
       @param startPg: (integer) - Starting page for the submission? Defaults
        to 1.
       @param indir: (string) - the directory used to store all submissions
        of the given "type" of this submission. For example, if the submission
        is of the type "modify bibliographic information", this variable would
        contain "modify".
       @param access: (string) - the "access" number for the submission
        (e.g. 1174062451_7010). This number is also used as the name for the
        current working submission directory.
       @param mainmenu: (string) - contains the URL (minus the CDS Invenio
        home stem) for the submission's home-page. (E.g. If this submission
        is "PICT", the "mainmenu" file would contain "/submit?doctype=PICT".
       @param fromdir:
       @param file:
       @param nextPg:
       @param nbPg:
       @param curpage: (integer) - the current submission page number. Defaults
        to 1.
       @param step: (integer) - the current step of the submission. Defaults to
        1.
       @param mode:
    """

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
    t = ""
    # get user ID:
    try:
        uid = getUid(req)
        uid_email = get_email(uid)
    except Error, e:
        return errorMsg(e, req, c, ln)
    # Preliminary tasks
    # check that the user is logged in
    if uid_email == "" or uid_email == "guest":
        return warningMsg(websubmit_templates.tmpl_warning_message(
                           ln = ln,
                           msg = _("Sorry, you must log in to perform this action.")
                         ), req, ln)

    ## check we have minimum fields
    if "" in (doctype, act, access):
        ## We don't have all the necessary information to go ahead
        ## with this submission:
        return errorMsg(_("Invalid parameter"), req, c, ln)


    ## retrieve the action and doctype data
    if indir == "":
        ## Get the submission storage directory from the DB:
        submission_dir = get_storage_directory_of_action(act)
        if submission_dir not in ("", None):
            indir = submission_dir
        else:
            ## Unable to determine the submission-directory:
            return errorMsg(_("Unable to find the submission directory."), \
                            req, c, ln)

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

    ## retrieve the name of the file in which the reference of
    ## the submitted document will be stored
    rn_filename = get_parameter_value_for_doctype(doctype, "edsrn")
    if rn_filename is not None:
        edsrn = rn_filename
    else:
        ## Unknown value for edsrn - set it to an empty string:
        edsrn = ""

    # Now we test whether the user has already completed the action and
    # reloaded the page (in this case we don't want the functions to be called
    # once again
    # reloaded = Test_Reload(uid_email,doctype,act,access)
    # if the action has been completed
    #if reloaded:
    #    return warningMsg("<b> Sorry, this action has already been completed. Please go back to the main menu to start a new action.</b>",req)

    ## Determine whether the action is finished
    ## (ie there are no other steps after the current one):
    finished = function_step_is_last(doctype, act, step)

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
        ## if the found field is the reference of the document
        ## we save this value in the "journal of submissions"
        if uid_email != "" and uid_email != "guest":
            if key == edsrn:
                update_submission_reference_in_log(doctype, access, uid_email, value)

    ## get the document type's long-name:
    doctype_lname = get_longname_of_doctype(doctype)
    if doctype_lname is not None:
        ## Got the doctype long-name: replace spaces with HTML chars:
        docname = doctype_lname.replace(" ", "&nbsp;")
    else:
        ## Unknown document type:
        return errorMsg(_("Unknown document type"), req, c, ln)

    ## get the action's long-name:
    action_lname = get_longname_of_action(act)
    if action_lname is not None:
        ## Got the action long-name: replace spaces with HTML chars:
        actname = action_lname.replace(" ", "&nbsp;")
    else:
        ## Unknown action:
        return errorMsg(_("Unknown action"), req, c, ln)

    ## Get the number of pages for this submission:
    subname = "%s%s" % (act, doctype)
    num_submission_pages = get_num_pages_of_submission(subname)
    if num_submission_pages is not None:
        nbpages = num_submission_pages
    else:
        ## Unable to determine the number of pages for this submission:
        return errorMsg(_("Unable to determine the number of submission pages."), \
                        req, cdsname, ln)

    ## Determine whether the action is finished
    ## (ie there are no other steps after the current one):
    last_step = function_step_is_last(doctype, act, step)

    # Prints the action details, returning the mandatory score
    action_score = action_details(doctype, act)
    current_level = get_level(doctype, act)

    # Calls all the function's actions
    function_content = ''
    try:
        function_content = print_function_calls(doctype=doctype,
                                                action=act,
                                                step=step,
                                                form=form,
                                                ln=ln)
    except functionError,e:
        return errorMsg(e.value, req, c, ln)
    except functionStop,e:
        if e.value is not None:
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
            ## update the "journal of submission":
            ## Does the submission already exist in the log?
            submission_exists = \
                 submission_exists_in_log(doctype, act, access, uid_email)
            if submission_exists == 1:
                ## update the rn and status to finished for this submission in the log:
                update_submission_reference_and_status_in_log(doctype, act,
                                                              access, uid_email,
                                                              rn, "finished")
            else:
                ## Submission doesn't exist in log - create it:
                log_new_completed_submission(doctype, act, access, uid_email, rn)

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
                description="submit documents",
                keywords="submit",
                uid = uid,
                language = ln,
                req = req)

def home(req, c=cdsname, ln=cdslang):
    """This function generates the WebSubmit "home page".
       Basically, this page contains a list of submission-collections
       in WebSubmit, and gives links to the various document-type
       submissions.
       Document-types only appear on this page when they have been
       connected to a submission-collection in WebSubmit.
       @param req: (apache request object)
       @param c: (string) - defaults to cdsname
       @param ln: (string) - The CDS Invenio interface language of choice.
        Defaults to cdslang (the default language of the installation).
       @return: (string) - the Web page to be displayed.
    """
    ln = wash_language(ln)
    # get user ID:
    try:
        uid = getUid(req)
    except Error, e:
        return errorMsg(e, req, c, ln)
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
               description="submit documents",
               keywords="submit",
               uid=uid,
               language=ln,
               req=req
               )

def makeCataloguesTable(ln=cdslang):
    """Build the 'catalogues' (submission-collections) tree for
       the WebSubmit home-page. This tree contains the links to
       the various document types in WebSubmit.
       @param ln: (string) - the language of the interface.
        (defaults to 'cdslang').
       @return: (string) - the submission-collections tree.
    """
    text = ""
    catalogues = []

    ## Get the submission-collections attached at the top level
    ## of the submission-collection tree:
    top_level_collctns = get_collection_children_of_submission_collection(0)
    if len(top_level_collctns) != 0:
        ## There are submission-collections attatched to the top level.
        ## retrieve their details for displaying:
        for child_collctn in top_level_collctns:
            catalogues.append(getCatalogueBranch(child_collctn[0], 1))

        text = websubmit_templates.tmpl_submit_home_catalogs(
                 ln=ln,
                 catalogs=catalogues
               )
    else:
        text = websubmit_templates.tmpl_submit_home_catalog_no_content(ln=ln)
    return text

def getCatalogueBranch(id_father, level):
    """Build up a given branch of the submission-collection
       tree. I.e. given a parent submission-collection ID,
       build up the tree below it. This tree will include
       doctype-children, as well as other submission-
       collections and their children.
       Finally, return the branch as a dictionary.
       @param id_father: (integer) - the ID of the submission-collection
        from which to begin building the branch.
       @param level: (integer) - the level of the current submission-
        collection branch.
       @return: (dictionary) - the branch and its sub-branches.
    """
    elem = {} ## The dictionary to contain this branch of the tree.
    ## First, get the submission-collection-details:
    collctn_name = get_submission_collection_name(id_father)
    if collctn_name is not None:
        ## Got the submission-collection's name:
        elem['name'] = collctn_name
    else:
        ## The submission-collection is unknown to the DB
        ## set its name as empty:
        elem['name'] = ""
    elem['id']    = id_father
    elem['level'] = level

    ## Now get details of the doctype-children of this
    ## submission-collection:
    elem['docs'] = []  ## List to hold the doctype-children
                       ## of the submission-collection
    doctype_children = \
       get_doctype_children_of_submission_collection(id_father)
    for child_doctype in doctype_children:
        elem['docs'].append(getDoctypeBranch(child_doctype[0]))

    ## Now, get the collection-children of this submission-collection:
    elem['sons'] = []
    collctn_children = \
         get_collection_children_of_submission_collection(id_father)
    for child_collctn in collctn_children:
        elem['sons'].append(getCatalogueBranch(child_collctn[0], level + 1))

    ## Now return this branch of the built-up 'collection-tree':
    return elem

def getDoctypeBranch(doctype):
    """Create a document-type 'leaf-node' for the submission-collections
       tree. Basically, this leaf is a dictionary containing the name
       and ID of the document-type submission to which it links.
       @param doctype: (string) - the ID of the document type.
       @return: (dictionary) - the document-type 'leaf node'. Contains
        the following values:
          + id:   (string) - the document-type ID.
          + name: (string) - the (long) name of the document-type.
    """
    ldocname = get_longname_of_doctype(doctype)
    if ldocname is None:
        ldocname = "Unknown Document Type"
    return { 'id' : doctype, 'name' : ldocname, }

def displayCatalogueBranch(id_father, level, catalogues):
    text = ""
    collctn_name = get_submission_collection_name(id_father)
    if collctn_name is None:
        ## If this submission-collection wasn't known in the DB,
        ## give it the name "Unknown Submission-Collection" to
        ## avoid errors:
        collctn_name = "Unknown Submission-Collection"

    ## Now, create the display for this submission-collection:
    if level == 1:
        text = "<LI><font size=\"+1\"><strong>%s</strong></font>\n" \
               % collctn_name
    else:
        ## TODO: These are the same (and the if is ugly.) Why?
        if level == 2:
            text = "<LI>%s\n" % collctn_name
        else:
            if level > 2:
                text = "<LI>%s\n" % collctn_name

    ## Now display the children document-types that are attached
    ## to this submission-collection:
    ## First, get the children:
    doctype_children = get_doctype_children_of_submission_collection(id_father)
    collctn_children = get_collection_children_of_submission_collection(id_father)

    if len(doctype_children) > 0 or len(collctn_children) > 0:
        ## There is something to display, so open a list:
        text = text + "<UL>\n"
    ## First, add the doctype leaves of this branch:
    for child_doctype in doctype_children:
        ## Add the doctype 'leaf-node':
        text = text + displayDoctypeBranch(child_doctype[0], catalogues)

    ## Now add the submission-collection sub-branches:
    for child_collctn in collctn_children:
        catalogues.append(child_collctn[0])
        text = text + displayCatalogueBranch(child_collctn[0], level+1, catalogues)

    ## Finally, close up the list if there were nodes to display
    ## at this branch:
    if len(doctype_children) > 0 or len(collctn_children) > 0:
        text = text + "</UL>\n"

    return text

def displayDoctypeBranch(doctype, catalogues):
    text = ""
    ldocname = get_longname_of_doctype(doctype)
    if ldocname is None:
        ldocname = "Unknown Document Type"
    text = "<LI><a href=\"\" onmouseover=\"javascript:" \
           "popUpTextWindow('%s',true,event);\" onmouseout" \
           "=\"javascript:popUpTextWindow('%s',false,event);\" " \
           "onClick=\"document.forms[0].doctype.value='%s';" \
           "document.forms[0].submit();return false;\">%s</a>\n" \
           % (doctype, doctype, doctype, ldocname)
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
        return errorMsg(e, req, c, ln)
    #parses database to get all data
    ## first, get the list of categories
    doctype_categs = get_categories_of_doctype(doctype)
    for doctype_categ in doctype_categs:
        nbCateg = nbCateg+1
        snameCateg.append(doctype_categ[0])
        lnameCateg.append(doctype_categ[1])

    ## Now get the details of the document type:
    doctype_details = get_doctype_details(doctype)
    if doctype_details is None:
        ## Doctype doesn't exist - raise error:
        return errorMsg (_("Unable to find document type.") + str(doctype), req)
    else:
        docFullDesc  = doctype_details[0]
        docShortDesc = doctype_details[1]
        description  = doctype_details[4]

    ## Get the details of the actions supported by this document-type:
    doctype_actions = get_actions_on_submission_page_for_doctype(doctype)
    for doctype_action in doctype_actions:
        ## Get the details of this action:
        action_details = get_action_details(doctype_action[0])
        if action_details is not None:
            actionShortDesc.append(doctype_action[0])
            indir.append(action_details[1])
            actionbutton.append(action_details[4])
            statustext.append(action_details[5])

    ## Send the gathered information to the template so that the doctype's
    ## home-page can be displayed:
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
                description="submit documents",
                keywords="submit",
                uid=uid,
                language=ln,
                req=req
               )

def Request_Print(m, txt):
    """The argumemts to this function are the display mode (m) and the text
       to be displayed (txt).
       If the argument mode is 'ALL' then the text is unconditionally echoed
       m can also take values S (Supervisor Mode) and U (User Mode). In these
       circumstances txt is only echoed if the argument mode is the same as
       the current mode
    """
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

    ## TODO: The above comment looks like nonesense? This
    ## function only seems to get the values of parameters
    ## from the db...

    ## Get the value for the parameter:
    param_val = get_parameter_value_for_doctype(doctype, field)
    if param_val is None:
        ## Couldn't find a value for this parameter for this doctype.
        ## Instead, try with the default doctype (DEF):
        param_val = get_parameter_value_for_doctype("DEF", field)
    if param_val is None:
        ## There was no value for the parameter for the default doctype.
        ## Nothing can be done about it - return an empty string:
        return ""
    else:
        ## There was some kind of value for the parameter; return it:
        return param_val


def Get_Parameters (function, doctype):
    """For a given function of a given document type, a dictionary
       of the parameter names and values are returned.
       @param function: (string) - the name of the function for which the
        parameters are to be retrieved.
       @param doctype: (string) - the ID of the document type.
       @return: (dictionary) - of the parameters of the function.
        Keyed by the parameter name, values are of course the parameter
        values.
    """
    parray = {}
    ## Get the names of the parameters expected by this function:
    func_params = get_parameters_of_function(function)
    for func_param in func_params:
        ## For each of the parameters, get its value for this document-
        ## type and add it into the dictionary of parameters:
        parameter = func_param[0]
        parray[parameter] = Evaluate_Parameter (parameter, doctype)
    return parray

def get_level(doctype, action):
    """Get the level of a given submission. If unknown, return 0
       as the level.
       @param doctype: (string) - the ID of the document type.
       @param action: (string) - the ID of the action.
       @return: (integer) - the level of the submission; 0 otherwise.
    """
    subm_details = get_details_of_submission(doctype, action)
    if subm_details is not None:
        ## Return the level of this action
        subm_level = subm_details[9]
        try:
            int(subm_level)
        except ValueError:
            return 0
        else:
            return subm_level
    else:
        return 0

def action_details (doctype, action):
    # Prints whether the action is mandatory or optional. The score of the
    # action is returned (-1 if the action was optional)
    subm_details = get_details_of_submission(doctype, action)
    if subm_details is not None:
        if subm_details[9] != "0":
            ## This action is mandatory; return the score:
            return subm_details[10]
        else:
            return -1
    else:
        return -1

def print_function_calls (doctype, action, step, form, ln=cdslang):
    # Calls the functions required by an "action" action on a "doctype" document
    # In supervisor mode, a table of the function calls is produced
    global htdocsdir,storage,access,pylibdir,dismode
    # load the right message language
    _ = gettext_set_language(ln)
    t=""

    ## Get the list of functions to be called
    funcs_to_call = get_functions_for_submission_step(doctype, action, step)

    ## If no functions are found at this step for this doctype,
    ## get the functions for the DEF(ault) doctype:
    if len(funcs_to_call) == 0:
        funcs_to_call = get_functions_for_submission_step("DEF", action, step)
    if len(funcs_to_call) > 0:
        # while there are functions left...
        functions = []
        for function in funcs_to_call:
            function_name = function[0]
            function_score = function[1]
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
    t = ""
    next_submissions = \
         get_submissions_at_level_X_with_score_above_N(doctype, currentlevel, action_score)

    if len(next_submissions) > 0:
        actions = []
        first_score = next_submissions[0][10]
        for action in next_submissions:
            if action[10] == first_score:
                ## Get the submission directory of this action:
                nextdir = get_storage_directory_of_action(action[1])
                if nextdir is None:
                    nextdir = ""
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
    """Look in the submission log to see whether a submission is
       marked as finished.
       @param uid_email: (string) - the email of the submitter.
       @param doctype: (string) - the ID of the document type.
       @param act: (string) - the ID of the action.
       @param access: (string) - the ID of the submission (access No.).
       @return: (integer) - 1 if this is a reload of the page; 0 if not.
    """
    subm_finished = submission_is_finished(doctype, act, access, uid_email)
    if subm_finished == 1:
        return 1
    else:
        return 0

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

def specialchars(text):
    text = string.replace(text, "&#147;", "\042");
    text = string.replace(text, "&#148;", "\042");
    text = string.replace(text, "&#146;", "\047");
    text = string.replace(text, "&#151;", "\055");
    text = string.replace(text, "&#133;", "\056\056\056");
    return text
