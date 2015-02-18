# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013,
#               2015 CERN.
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

"""WebSubmit: the mechanism for the submission of new records into Invenio
   via a Web interface.
"""

__revision__ = "$Id$"

# import interesting modules:
import traceback
import string
import os
import sys
import time
import types
import re
import pprint
from urllib import quote_plus
from cgi import escape

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_URL, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_DEVEL_SITE, \
     CFG_SITE_SECURE_URL, \
     CFG_WEBSUBMIT_USE_MATHJAX

from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.webpage import page, error_page, warning_page
from invenio.legacy.webuser import getUid, get_email, collect_user_info, isGuestUser, \
                            page_not_authorized
from invenio.legacy.websubmit.config import CFG_RESERVED_SUBMISSION_FILENAMES, \
    InvenioWebSubmitFunctionError, InvenioWebSubmitFunctionStop, \
    InvenioWebSubmitFunctionWarning
from invenio.base.i18n import gettext_set_language, wash_language
from invenio.legacy.webstat.api import register_customevent
from invenio.ext.logging import register_exception
from invenio.utils.url import make_canonical_urlargd, redirect_to_url
from invenio.legacy.websubmit.admin_engine import string_is_alphanumeric_including_underscore
from invenio.utils.html import get_mathjax_header

from invenio.legacy.websubmit.db_layer import \
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

import invenio.legacy.template
websubmit_templates = invenio.legacy.template.load('websubmit')

from sqlalchemy.exc import SQLAlchemyError as Error


def interface(req,
              c=CFG_SITE_NAME,
              ln=CFG_SITE_LANG,
              doctype="",
              act="",
              startPg=1,
              access="",
              mainmenu="",
              fromdir="",
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
       @param c: (string), defaulted to CFG_SITE_NAME. The name of the Invenio
        installation.
       @param ln: (string), defaulted to CFG_SITE_LANG. The language in which to
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
       @param mainmenu: (string) - contains the URL (minus the Invenio
        home stem) for the submission's home-page. (E.g. If this submission
        is "PICT", the "mainmenu" file would contain "/submit?doctype=PICT".
       @param fromdir: (integer)
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
    user_info = collect_user_info(req)
    uid = user_info['uid']
    uid_email = user_info['email']

    # variable initialisation
    t = ""
    field = []
    fieldhtml = []
    level = []
    fullDesc = []
    text = ''
    check = []
    select = []
    radio = []
    upload = []
    txt = []
    noPage = []
    # Preliminary tasks
    if not access:
        # In some cases we want to take the users directly to the submit-form.
        # This fix makes this possible - as it generates the required access
        # parameter if it is not present.
        pid = os.getpid()
        now = time.time()
        access = "%i_%s" % (now, pid)

    # check we have minimum fields
    if not doctype or not act or not access:
        ## We don't have all the necessary information to go ahead
        ## with this submission:
        return warning_page(_("Not enough information to go ahead with the submission."), req, ln)

    try:
        assert(not access or re.match('\d+_\d+', access))
    except AssertionError:
        register_exception(req=req, prefix='doctype="%s", access="%s"' % (doctype, access))
        return warning_page(_("Invalid parameters"), req, ln)

    if doctype and act:
        ## Let's clean the input
        details = get_details_of_submission(doctype, act)
        if not details:
            return warning_page(_("Invalid doctype and act parameters"), req, ln)
        doctype = details[0]
        act = details[1]

    ## Before continuing to display the submission form interface,
    ## verify that this submission has not already been completed:
    if submission_is_finished(doctype, act, access, uid_email):
        ## This submission has already been completed.
        ## This situation can arise when, having completed a submission,
        ## the user uses the browser's back-button to go back to the form
        ## stage of the submission and then tries to submit once more.
        ## This is unsafe and should not be allowed. Instead of re-displaying
        ## the submission forms, display an error message to the user:
        wrnmsg = """<b>This submission has been completed. Please go to the""" \
                 """ <a href="/submit?doctype=%(doctype)s&amp;ln=%(ln)s">""" \
                 """main menu</a> to start a new submission.</b>""" \
                 % { 'doctype' : quote_plus(doctype), 'ln' : ln }
        return warning_page(wrnmsg, req, ln)


    ## retrieve the action and doctype data:

    ## Concatenate action ID and doctype ID to make the submission ID:
    subname = "%s%s" % (act, doctype)

    ## Get the submission storage directory from the DB:
    submission_dir = get_storage_directory_of_action(act)
    if submission_dir:
        indir = submission_dir
    else:
        ## Unable to determine the submission-directory:
        return warning_page(_("Unable to find the submission directory for the action: %(x_dir)s", x_dir=escape(str(act))), req, ln)

    ## get the document type's long-name:
    doctype_lname = get_longname_of_doctype(doctype)
    if doctype_lname is not None:
        ## Got the doctype long-name: replace spaces with HTML chars:
        docname = doctype_lname.replace(" ", "&nbsp;")
    else:
        ## Unknown document type:
        return warning_page(_("Unknown document type"), req, ln)

    ## get the action's long-name:
    actname = get_longname_of_action(act)
    if actname is None:
        ## Unknown action:
        return warning_page(_("Unknown action"), req, ln)

    ## Get the number of pages for this submission:
    num_submission_pages = get_num_pages_of_submission(subname)
    if num_submission_pages is not None:
        nbpages = num_submission_pages
    else:
        ## Unable to determine the number of pages for this submission:
        return warning_page(_("Unable to determine the number of submission pages."), req, ln)

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
    curdir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, indir, doctype, access)
    try:
        assert(curdir == os.path.abspath(curdir))
    except AssertionError:
        register_exception(req=req, prefix='indir="%s", doctype="%s", access="%s"' % (indir, doctype, access))
        return warning_page(_("Invalid parameters"), req, ln)

    ## if this submission comes from another one (fromdir is then set)
    ## We retrieve the previous submission directory and put it in the proper one
    if fromdir != "":
        olddir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, fromdir, doctype, access)
        try:
            assert(olddir == os.path.abspath(olddir))
        except AssertionError:
            register_exception(req=req, prefix='fromdir="%s", doctype="%s", access="%s"' % (fromdir, doctype, access))
            return warning_page(_("Invalid parameters"), req, ln)

        if os.path.exists(olddir):
            os.rename(olddir, curdir)
    ## If the submission directory still does not exist, we create it
    if not os.path.exists(curdir):
        try:
            os.makedirs(curdir)
        except Exception as e:
            register_exception(req=req, alert_admin=True)
            return warning_page(_("Unable to create a directory for this submission. The administrator has been alerted."), req, ln)

    ## Retrieve the previous page, as submitted to curdir (before we
    ## overwrite it with our curpage as declared from the incoming
    ## form)
    try:
        fp = open(os.path.join(curdir, "curpage"))
        previous_page_from_disk = fp.read()
        fp.close()
    except:
        previous_page_from_disk = "1"

    # retrieve the original main menu url and save it in the "mainmenu" file
    if mainmenu != "":
        fp = open(os.path.join(curdir, "mainmenu"), "w")
        fp.write(mainmenu)
        fp.close()
    # and if the file containing the URL to the main menu exists
    # we retrieve it and store it in the $mainmenu variable
    if os.path.exists(os.path.join(curdir, "mainmenu")):
        fp = open(os.path.join(curdir, "mainmenu"), "r");
        mainmenu = fp.read()
        fp.close()
    else:
        mainmenu = "%s/submit" % (CFG_SITE_URL,)
    # various authentication related tasks...
    if uid_email != "guest" and uid_email != "":
        #First save the username (email address) in the SuE file. This way bibconvert will be able to use it if needed
        fp = open(os.path.join(curdir, "SuE"), "w")
        fp.write(uid_email)
        fp.close()

    if os.path.exists(os.path.join(curdir, "combo%s" % doctype)):
        fp = open(os.path.join(curdir, "combo%s" % doctype), "r");
        categ = fp.read()
        fp.close()
    else:
        categ = req.form.get('combo%s' % doctype, '*')

    # is user authorized to perform this action?
    (auth_code, auth_message) = acc_authorize_action(req, 'submit', \
                                                     authorized_if_no_roles=not isGuestUser(uid), \
                                                     verbose=0, \
                                                     doctype=doctype, \
                                                     act=act, \
                                                     categ=categ)
    if not auth_code == 0:
        return warning_page("""<center><font color="red">%s</font></center>""" % auth_message, req, ln)

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

    ## Let's write in curdir file under curdir the curdir value
    ## in case e.g. it is needed in FFT.
    fp = open(os.path.join(curdir, "curdir"), "w")
    fp.write(curdir)
    fp.close()

    ## Let's write in ln file the current language
    fp = open(os.path.join(curdir, "ln"), "w")
    fp.write(ln)
    fp.close()

    # Save the form fields entered in the previous submission page
    # If the form was sent with the GET method
    form = dict(req.form)
    value = ""
    # we parse all the form variables
    for key, formfields in form.items():
        filename = key.replace("[]", "")
        file_to_open = os.path.join(curdir, filename)
        try:
            assert(file_to_open == os.path.abspath(file_to_open))
        except AssertionError:
            register_exception(req=req, prefix='curdir="%s", filename="%s"' % (curdir, filename))
            return warning_page(_("Invalid parameters"), req, ln)

        # Do not write reserved filenames to disk
        if filename in CFG_RESERVED_SUBMISSION_FILENAMES:
            # Unless there is really an element with that name on this
            # page or previous one (either visited, or declared to be
            # visited), which means that admin authorized it.
            if not ((str(curpage).isdigit() and \
                    filename in [submission_field[3] for submission_field in \
                                 get_form_fields_on_submission_page(subname, curpage)]) or \
                    (str(curpage).isdigit() and int(curpage) > 1 and \
                    filename in [submission_field[3] for submission_field in \
                                 get_form_fields_on_submission_page(subname, int(curpage) - 1)]) or \
                    (previous_page_from_disk.isdigit() and \
                     filename in [submission_field[3] for submission_field in \
                                  get_form_fields_on_submission_page(subname, int(previous_page_from_disk))])):
                # Still this will filter out reserved field names that
                # might have been called by functions such as
                # Create_Modify_Interface function in MBI step, or
                # dynamic fields in response elements, but that is
                # unlikely to be a problem.
                continue

        # Skip variables containing characters that are not allowed in
        # WebSubmit elements
        if not string_is_alphanumeric_including_underscore(filename):
            continue

        # the field is an array
        if isinstance(formfields, types.ListType):
            fp = open(file_to_open, "w")
            for formfield in formfields:
                #stripslashes(value)
                value = specialchars(formfield)
                fp.write(value+"\n")
            fp.close()
        # the field is a normal string
        elif isinstance(formfields, types.StringTypes) and formfields != "":
            value = formfields
            fp = open(file_to_open, "w")
            fp.write(specialchars(value))
            fp.close()
        # the field is a file
        elif hasattr(formfields,"filename") and formfields.filename:
            dir_to_open = os.path.join(curdir, 'files', key)
            try:
                assert(dir_to_open == os.path.abspath(dir_to_open))
                assert(dir_to_open.startswith(CFG_WEBSUBMIT_STORAGEDIR))
            except AssertionError:
                register_exception(req=req, prefix='curdir="%s", key="%s"' % (curdir, key))
                return warning_page(_("Invalid parameters"), req, ln)
            if not os.path.exists(dir_to_open):
                try:
                    os.makedirs(dir_to_open)
                except:
                    register_exception(req=req, alert_admin=True)
                    return warning_page(_("Cannot create submission directory. The administrator has been alerted."), req, ln)
            filename = formfields.filename
            ## Before saving the file to disc, wash the filename (in particular
            ## washing away UNIX and Windows (e.g. DFS) paths):
            filename = os.path.basename(filename.split('\\')[-1])
            filename = filename.strip()
            if filename != "":
                fp = open(os.path.join(dir_to_open, filename), "w")
                while True:
                    buf = formfields.read(10240)
                    if buf:
                        fp.write(buf)
                    else:
                        break
                fp.close()
                fp = open(os.path.join(curdir, "lastuploadedfile"), "w")
                fp.write(filename)
                fp.close()
                fp = open(file_to_open, "w")
                fp.write(filename)
                fp.close()
            else:
                return warning_page(_("No file uploaded?"), req, ln)

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
    the_globals = {
        'doctype' : doctype,
        'action' : action,
        'access' : access,
        'ln' : ln,
        'curdir' : curdir,
        'uid' : uid,
        'uid_email' : uid_email,
        'form' : form,
        'act' : act,
        'action' : act, ## for backward compatibility
        'req' : req,
        'user_info' : user_info,
        'InvenioWebSubmitFunctionError' : InvenioWebSubmitFunctionError,
        '__websubmit_in_jail__' : True,
        '__builtins__' : globals()['__builtins__']
    }

    for field_instance in form_fields:
        full_field = {}

        ## Retrieve the field's description:
        element_descr = get_element_description(field_instance[3])
        try:
            assert(element_descr is not None)
        except AssertionError:
            msg = _("Unknown form field found on submission page.")
            register_exception(req=req, alert_admin=True, prefix=msg)
            ## The form field doesn't seem to exist - return with error message:
            return warning_page(_("Unknown form field found on submission page."), req, ln)

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
            try:
                co = compile (full_field ['htmlcode'].replace("\r\n","\n"), "<string>", "exec")
                the_globals['text'] = ''
                the_globals['custom_level'] = None
                exec co in the_globals
                text = the_globals['text']
                # Also get the custom_level if it's define in the element description
                custom_level = the_globals.get('custom_level')
                # Make sure custom_level has an appropriate value or default to 'O'
                if custom_level not in ('M', 'O', None):
                    custom_level = 'O'
            except:
                register_exception(req=req, alert_admin=True, prefix="Error in evaluating response element %s with globals %s" % (pprint.pformat(full_field), pprint.pformat(the_globals)))
                raise
        else:
            text = websubmit_templates.tmpl_submit_field (ln = ln, field = full_field)
            # Provide a default value for the custom_level
            custom_level = None

        # we now determine the exact type of the created field
        if full_field['type'] not in [ 'D','R']:
            field.append(full_field['name'])
            level.append(custom_level is None and field_instance[5] or custom_level)
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
                combo = ""
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
            level.append(custom_level is None and field_instance[5] or custom_level)
            txt.append(field_instance[6])
            fullDesc.append(field_instance[4])
            check.append(field_instance[7])
            fieldhtml.append(text)
        full_field['fullDesc'] = field_instance[4]
        full_field['text'] = text

        # If a file exists with the name of the field we extract the saved value
        text = ''
        if os.path.exists(os.path.join(curdir, full_field['name'])):
            file = open(os.path.join(curdir, full_field['name']), "r");
            text = file.read()
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
                try:
                    assert(element_descr is not None)
                except AssertionError:
                    msg = _("Unknown form field found on submission page.")
                    register_exception(req=req, alert_admin=True, prefix=msg)
                    ## The form field doesn't seem to exist - return with error message:
                    return warning_page(_("Unknown form field found on submission page."), req, ln)
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
        for i in xrange(nbFields):
            res = 1
            if not os.path.exists(os.path.join(curdir, fullcheck_field[i])):
                res = 0
            else:
                file = open(os.path.join(curdir, fullcheck_field[i]), "r")
                text = file.read()
                if text == '':
                    res = 0
                else:
                    if text == "Select:":
                        res = 0
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
          nextPg = nextPg,
          access = access,
          nbPg = nbPg,
          doctype = doctype,
          act = act,
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
                         returnto = returnto,
                       ),
          mainmenu = mainmenu,
         )

    t += websubmit_templates.tmpl_page_do_not_leave_submission_js(ln)

    # start display:
    req.content_type = "text/html"
    req.send_http_header()
    p_navtrail = """<a href="/submit?ln=%(ln)s" class="navtrail">%(submit)s</a>&nbsp;>&nbsp;<a href="/submit?doctype=%(doctype)s&amp;ln=%(ln)s" class="navtrail">%(docname)s</a>&nbsp;""" % {
                   'submit'  : _("Submit"),
                   'doctype' : quote_plus(doctype),
                   'docname' : docname,
                   'ln' : ln
                 }


    ## add MathJax if wanted
    if CFG_WEBSUBMIT_USE_MATHJAX:
        metaheaderadd = get_mathjax_header(req.is_https())
        metaheaderadd += websubmit_templates.tmpl_mathpreview_header(ln, req.is_https())
    else:
        metaheaderadd = ''

    return page(title= actname,
                body = t,
                navtrail = p_navtrail,
                description = "submit documents",
                keywords = "submit",
                uid = uid,
                language = ln,
                req = req,
                navmenuid='submit',
                metaheaderadd=metaheaderadd)


def endaction(req,
              c=CFG_SITE_NAME,
              ln=CFG_SITE_LANG,
              doctype="",
              act="",
              startPg=1,
              access="",
              mainmenu="",
              fromdir="",
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
       @param c: (string), defaulted to CFG_SITE_NAME. The name of the Invenio
        installation.
       @param ln: (string), defaulted to CFG_SITE_LANG. The language in which to
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
       @param mainmenu: (string) - contains the URL (minus the Invenio
        home stem) for the submission's home-page. (E.g. If this submission
        is "PICT", the "mainmenu" file would contain "/submit?doctype=PICT".
       @param fromdir:
       @param nextPg:
       @param nbPg:
       @param curpage: (integer) - the current submission page number. Defaults
        to 1.
       @param step: (integer) - the current step of the submission. Defaults to
        1.
       @param mode:
    """
    # load the right message language
    _ = gettext_set_language(ln)

    dismode = mode
    ln = wash_language(ln)
    sys.stdout = req
    rn = ""
    t = ""
    # get user ID:
    uid = getUid(req)
    uid_email = get_email(uid)

    ## Get the submission storage directory from the DB:
    submission_dir = get_storage_directory_of_action(act)
    if submission_dir:
        indir = submission_dir
    else:
        ## Unable to determine the submission-directory:
        return warning_page(_("Unable to find the submission directory for the action: %(x_dir)s", x_dir=escape(str(act))), req, ln)
    curdir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, indir, doctype, access)
    if os.path.exists(os.path.join(curdir, "combo%s" % doctype)):
        fp = open(os.path.join(curdir, "combo%s" % doctype), "r");
        categ = fp.read()
        fp.close()
    else:
        categ = req.form.get('combo%s' % doctype, '*')

    # is user authorized to perform this action?
    (auth_code, auth_message) = acc_authorize_action(req, 'submit', \
                                                     authorized_if_no_roles=not isGuestUser(uid), \
                                                     verbose=0, \
                                                     doctype=doctype, \
                                                     act=act, \
                                                     categ=categ)
    if not auth_code == 0:
        return warning_page("""<center><font color="red">%s</font></center>""" % auth_message, req, ln)

    # Preliminary tasks
    ## check we have minimum fields
    if not doctype or not act or not access:
        ## We don't have all the necessary information to go ahead
        ## with this submission:
        return warning_page(_("Not enough information to go ahead with the submission."), req, ln)

    if doctype and act:
        ## Let's clean the input
        details = get_details_of_submission(doctype, act)
        if not details:
            return warning_page(_("Invalid doctype and act parameters"), req, ln)
        doctype = details[0]
        act = details[1]

    try:
        assert(not access or re.match('\d+_\d+', access))
    except AssertionError:
        register_exception(req=req, prefix='doctype="%s", access="%s"' % (doctype, access))
        return warning_page(_("Invalid parameters"), req, ln)

    ## Before continuing to process the submitted data, verify that
    ## this submission has not already been completed:
    if submission_is_finished(doctype, act, access, uid_email):
        ## This submission has already been completed.
        ## This situation can arise when, having completed a submission,
        ## the user uses the browser's back-button to go back to the form
        ## stage of the submission and then tries to submit once more.
        ## This is unsafe and should not be allowed. Instead of re-processing
        ## the submitted data, display an error message to the user:
        wrnmsg = """<b>This submission has been completed. Please go to the""" \
                 """ <a href="/submit?doctype=%(doctype)s&amp;ln=%(ln)s">""" \
                 """main menu</a> to start a new submission.</b>""" \
                 % { 'doctype' : quote_plus(doctype), 'ln' : ln }
        return warning_page(wrnmsg, req, ln)

    ## Get the number of pages for this submission:
    subname = "%s%s" % (act, doctype)

    ## retrieve the action and doctype data
    ## Get the submission storage directory from the DB:
    submission_dir = get_storage_directory_of_action(act)
    if submission_dir:
        indir = submission_dir
    else:
        ## Unable to determine the submission-directory:
        return warning_page(_("Unable to find the submission directory for the action: %(x_dir)s", x_dir=escape(str(act))), req, ln)

    # The following words are reserved and should not be used as field names
    reserved_words = ["stop", "file", "nextPg", "startPg", "access", "curpage", "nbPg", "act", \
                      "indir", "doctype", "mode", "step", "deleted", "file_path", "userfile_name"]
    # This defines the path to the directory containing the action data
    curdir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, indir, doctype, access)
    try:
        assert(curdir == os.path.abspath(curdir))
    except AssertionError:
        register_exception(req=req, prefix='indir="%s", doctype=%s, access=%s' % (indir, doctype, access))
        return warning_page(_("Invalid parameters"), req, ln)

    ## If the submission directory still does not exist, we create it
    if not os.path.exists(curdir):
        try:
            os.makedirs(curdir)
        except Exception as e:
            register_exception(req=req, alert_admin=True)
            return warning_page(_("Unable to create a directory for this submission. The administrator has been alerted."), req, ln)

    # retrieve the original main menu url ans save it in the "mainmenu" file
    if mainmenu != "":
        fp = open(os.path.join(curdir, "mainmenu"), "w")
        fp.write(mainmenu)
        fp.close()
    # and if the file containing the URL to the main menu exists
    # we retrieve it and store it in the $mainmenu variable
    if os.path.exists(os.path.join(curdir, "mainmenu")):
        fp = open(os.path.join(curdir, "mainmenu"), "r");
        mainmenu = fp.read()
        fp.close()
    else:
        mainmenu = "%s/submit" % (CFG_SITE_URL,)

    num_submission_pages = get_num_pages_of_submission(subname)
    if num_submission_pages is not None:
        nbpages = num_submission_pages
    else:
        ## Unable to determine the number of pages for this submission:
        return warning_page(_("Unable to determine the number of submission pages."), \
                        req, ln)

    ## Retrieve the previous page, as submitted to curdir (before we
    ## overwrite it with our curpage as declared from the incoming
    ## form)
    try:
        fp = open(os.path.join(curdir, "curpage"))
        previous_page_from_disk = fp.read()
        fp.close()
    except:
        previous_page_from_disk = str(num_submission_pages)

    ## retrieve the name of the file in which the reference of
    ## the submitted document will be stored
    rn_filename = get_parameter_value_for_doctype(doctype, "edsrn")
    if rn_filename is not None:
        edsrn = rn_filename
    else:
        ## Unknown value for edsrn - set it to an empty string:
        edsrn = ""

    ## Determine whether the action is finished
    ## (ie there are no other steps after the current one):
    finished = function_step_is_last(doctype, act, step)

    ## Let's write in curdir file under curdir the curdir value
    ## in case e.g. it is needed in FFT.
    fp = open(os.path.join(curdir, "curdir"), "w")
    fp.write(curdir)
    fp.close()

    ## Let's write in ln file the current language
    fp = open(os.path.join(curdir, "ln"), "w")
    fp.write(ln)
    fp.close()

    # Save the form fields entered in the previous submission page
    # If the form was sent with the GET method
    form = req.form
    value = ""
    # we parse all the form variables
    for key in form.keys():
        formfields = form[key]
        filename = key.replace("[]", "")

        file_to_open = os.path.join(curdir, filename)
        try:
            assert(file_to_open == os.path.abspath(file_to_open))
            assert(file_to_open.startswith(CFG_WEBSUBMIT_STORAGEDIR))
        except AssertionError:
            register_exception(req=req, prefix='curdir="%s", filename="%s"' % (curdir, filename))
            return warning_page(_("Invalid parameters"), req, ln)

        # Do not write reserved filenames to disk
        if filename in CFG_RESERVED_SUBMISSION_FILENAMES:
            # Unless there is really an element with that name on this
            # page, or on the previously visited one, which means that
            # admin authorized it. Note that in endaction() curpage is
            # equivalent to the "previous" page value
            if not ((previous_page_from_disk.isdigit() and \
                    filename in [submission_field[3] for submission_field in \
                                  get_form_fields_on_submission_page(subname, int(previous_page_from_disk))]) or \
                    (str(curpage).isdigit() and int(curpage) > 1 and \
                     filename in [submission_field[3] for submission_field in \
                                  get_form_fields_on_submission_page(subname, int(curpage) - 1)])):
                # might have been called by functions such as
                # Create_Modify_Interface function in MBI step, or
                # dynamic fields in response elements, but that is
                # unlikely to be a problem.
                continue

        # Skip variables containing characters that are not allowed in
        # WebSubmit elements
        if not string_is_alphanumeric_including_underscore(filename):
            continue

        # the field is an array
        if isinstance(formfields, types.ListType):
            fp = open(file_to_open, "w")
            for formfield in formfields:
                #stripslashes(value)
                value = specialchars(formfield)
                fp.write(value+"\n")
            fp.close()
        # the field is a normal string
        elif isinstance(formfields, types.StringTypes) and formfields != "":
            value = formfields
            fp = open(file_to_open, "w")
            fp.write(specialchars(value))
            fp.close()
        # the field is a file
        elif hasattr(formfields, "filename") and formfields.filename:
            dir_to_open = os.path.join(curdir, 'files', key)
            try:
                assert(dir_to_open == os.path.abspath(dir_to_open))
                assert(dir_to_open.startswith(CFG_WEBSUBMIT_STORAGEDIR))
            except AssertionError:
                register_exception(req=req, prefix='curdir="%s", key="%s"' % (curdir, key))
                return warning_page(_("Invalid parameters"), req, ln)

            if not os.path.exists(dir_to_open):
                try:
                    os.makedirs(dir_to_open)
                except:
                    register_exception(req=req, alert_admin=True)
                    return warning_page(_("Cannot create submission directory. The administrator has been alerted."), req, ln)
            filename = formfields.filename
            ## Before saving the file to disc, wash the filename (in particular
            ## washing away UNIX and Windows (e.g. DFS) paths):
            filename = os.path.basename(filename.split('\\')[-1])
            filename = filename.strip()
            if filename != "":
                fp = open(os.path.join(dir_to_open, filename), "w")
                while True:
                    buf = formfields.file.read(10240)
                    if buf:
                        fp.write(buf)
                    else:
                        break
                fp.close()
                fp = open(os.path.join(curdir, "lastuploadedfile"), "w")
                fp.write(filename)
                fp.close()
                fp = open(file_to_open, "w")
                fp.write(filename)
                fp.close()
            else:
                return warning_page(_("No file uploaded?"), req, ln)
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
        return warning_page(_("Unknown document type"), req, ln)

    ## get the action's long-name:
    actname = get_longname_of_action(act)
    if actname is None:
        ## Unknown action:
        return warning_page(_("Unknown action"), req, ln)

    ## Determine whether the action is finished
    ## (ie there are no other steps after the current one):
    last_step = function_step_is_last(doctype, act, step)

    next_action = '' ## The next action to be proposed to the user

    # Prints the action details, returning the mandatory score
    action_score = action_details(doctype, act)
    current_level = get_level(doctype, act)

    # Calls all the function's actions
    function_content = ''
    try:
        ## Handle the execution of the functions for this
        ## submission/step:
        start_time = time.time()
        (function_content, last_step, action_score, rn) = \
                           print_function_calls(req=req,
                                                doctype=doctype,
                                                action=act,
                                                step=step,
                                                form=form,
                                                start_time=start_time,
                                                access=access,
                                                curdir=curdir,
                                                dismode=mode,
                                                rn=rn,
                                                last_step=last_step,
                                                action_score=action_score,
                                                ln=ln)
    except InvenioWebSubmitFunctionError as e:
        register_exception(req=req, alert_admin=True, prefix='doctype="%s", action="%s", step="%s", form="%s", start_time="%s"' % (doctype, act, step, form, start_time))
        ## There was a serious function-error. Execution ends.
        if CFG_DEVEL_SITE:
            raise
        else:
            return warning_page(_("A serious function-error has been encountered. Adminstrators have been alerted. <br /><em>Please not that this might be due to wrong characters inserted into the form</em> (e.g. by copy and pasting some text from a PDF file)."), req, ln)
    except InvenioWebSubmitFunctionStop as e:
        ## For one reason or another, one of the functions has determined that
        ## the data-processing phase (i.e. the functions execution) should be
        ## halted and the user should be returned to the form interface once
        ## more. (NOTE: Redirecting the user to the Web-form interface is
        ## currently done using JavaScript. The "InvenioWebSubmitFunctionStop"
        ## exception contains a "value" string, which is effectively JavaScript
        ## - probably an alert box and a form that is submitted). **THIS WILL
        ## CHANGE IN THE FUTURE WHEN JavaScript IS REMOVED!**
        if e.value is not None:
            function_content = e.value
        else:
            function_content = e
    else:
        ## No function exceptions (InvenioWebSubmitFunctionStop,
        ## InvenioWebSubmitFunctionError) were raised by the functions. Propose
        ## the next action (if applicable), and log the submission as finished:

        ## If the action was mandatory we propose the next
        ## mandatory action (if any)
        if action_score != -1 and last_step == 1:
            next_action = Propose_Next_Action(doctype, \
                                              action_score, \
                                              access, \
                                              current_level, \
                                              indir)

        ## If we are in the last step of an action, we can update
        ## the "journal of submissions"
        if last_step == 1:
            if uid_email != "" and uid_email != "guest":
                ## update the "journal of submission":
                ## Does the submission already exist in the log?
                submission_exists = \
                     submission_exists_in_log(doctype, act, access, uid_email)
                if submission_exists == 1:
                    ## update the rn and status to finished for this submission
                    ## in the log:
                    update_submission_reference_and_status_in_log(doctype, \
                                                                  act, \
                                                                  access, \
                                                                  uid_email, \
                                                                  rn, \
                                                                  "finished")
                else:
                    ## Submission doesn't exist in log - create it:
                    log_new_completed_submission(doctype, \
                                                 act, \
                                                 access, \
                                                 uid_email, \
                                                 rn)

    ## Having executed the functions, create the page that will be displayed
    ## to the user:
    t = websubmit_templates.tmpl_page_endaction(
          ln = ln,
          # these fields are necessary for the navigation
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
          mainmenu = mainmenu,
          finished = finished,
          function_content = function_content,
          next_action = next_action,
        )

    if finished:
        # register event in webstat
        try:
            register_customevent("websubmissions", [get_longname_of_doctype(doctype)])
        except:
            register_exception(suffix="Do the webstat tables exists? Try with 'webstatadmin --load-config'")
    else:
        t += websubmit_templates.tmpl_page_do_not_leave_submission_js(ln)

    # start display:
    req.content_type = "text/html"
    req.send_http_header()

    p_navtrail = '<a href="/submit?ln='+ln+'" class="navtrail">' + _("Submit") +\
                 """</a>&nbsp;>&nbsp;<a href="/submit?doctype=%(doctype)s&amp;ln=%(ln)s" class="navtrail">%(docname)s</a>""" % {
                   'doctype' : quote_plus(doctype),
                   'docname' : docname,
                   'ln' : ln,
                 }

    ## add MathJax if wanted
    if CFG_WEBSUBMIT_USE_MATHJAX:
        metaheaderadd = get_mathjax_header(req.is_https())
        metaheaderadd += websubmit_templates.tmpl_mathpreview_header(ln, req.is_https())
    else:
        metaheaderadd = ''

    return page(title= actname,
                body = t,
                navtrail = p_navtrail,
                description="submit documents",
                keywords="submit",
                uid = uid,
                language = ln,
                req = req,
                navmenuid='submit',
                metaheaderadd=metaheaderadd)

def home(req, catalogues_text, c=CFG_SITE_NAME, ln=CFG_SITE_LANG):
    """This function generates the WebSubmit "home page".
       Basically, this page contains a list of submission-collections
       in WebSubmit, and gives links to the various document-type
       submissions.
       Document-types only appear on this page when they have been
       connected to a submission-collection in WebSubmit.
       @param req: (apache request object)
       @param catalogues_text (string): the computed catalogues tree
       @param c: (string) - defaults to CFG_SITE_NAME
       @param ln: (string) - The Invenio interface language of choice.
        Defaults to CFG_SITE_LANG (the default language of the installation).
       @return: (string) - the Web page to be displayed.
    """
    ln = wash_language(ln)
    # get user ID:
    try:
        uid = getUid(req)
        user_info = collect_user_info(req)
    except Error as e:
        return error_page(e, req, ln)

    # load the right message language
    _ = gettext_set_language(ln)

    finaltext = websubmit_templates.tmpl_submit_home_page(
                    ln = ln,
                    catalogues = catalogues_text,
                    user_info = user_info,
                )

    return page(title=_("Submit"),
               body=finaltext,
               navtrail=[],
               description="submit documents",
               keywords="submit",
               uid=uid,
               language=ln,
               req=req,
               navmenuid='submit'
               )

def makeCataloguesTable(req, ln=CFG_SITE_LANG):
    """Build the 'catalogues' (submission-collections) tree for
       the WebSubmit home-page. This tree contains the links to
       the various document types in WebSubmit.
       @param req: (dict) - the user request object
        in order to decide whether to display a submission.
       @param ln: (string) - the language of the interface.
        (defaults to 'CFG_SITE_LANG').
       @return: (string, bool, bool) - the submission-collections tree.
            True if there is at least one submission authorized for the user
            True if there is at least one submission
    """
    def is_at_least_one_submission_authorized(cats):
        for cat in cats:
            if cat['docs']:
                return True
            if is_at_least_one_submission_authorized(cat['sons']):
                return True
        return False
    text = ""
    catalogues = []
    ## Get the submission-collections attached at the top level
    ## of the submission-collection tree:
    top_level_collctns = get_collection_children_of_submission_collection(0)
    if len(top_level_collctns) != 0:
        ## There are submission-collections attatched to the top level.
        ## retrieve their details for displaying:
        for child_collctn in top_level_collctns:
            catalogues.append(getCatalogueBranch(child_collctn[0], 1, req))
        text = websubmit_templates.tmpl_submit_home_catalogs(
                 ln=ln,
                 catalogs=catalogues)
        submissions_exist = True
        at_least_one_submission_authorized = is_at_least_one_submission_authorized(catalogues)
    else:
        text = websubmit_templates.tmpl_submit_home_catalog_no_content(ln=ln)
        submissions_exist = False
        at_least_one_submission_authorized = False
    return text, at_least_one_submission_authorized, submissions_exist

def getCatalogueBranch(id_father, level, req):
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
       @param req: (dict) - the user request object in order to decide
        whether to display a submission.
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
    user_info = collect_user_info(req)

    for child_doctype in doctype_children:
        ## To get access to a submission pipeline for a logged in user,
        ## it is decided by any authorization. If none are defined for the action
        ## then a logged in user will get access.
        ## If user is not logged in, a specific rule to allow the action is needed
        if acc_authorize_action(req, 'submit', \
                                authorized_if_no_roles=not isGuestUser(user_info['uid']), \
                                doctype=child_doctype[0])[0] == 0:
            elem['docs'].append(getDoctypeBranch(child_doctype[0]))

    ## Now, get the collection-children of this submission-collection:
    elem['sons'] = []
    collctn_children = \
         get_collection_children_of_submission_collection(id_father)
    for child_collctn in collctn_children:
        elem['sons'].append(getCatalogueBranch(child_collctn[0], level + 1, req))

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


def action(req, c=CFG_SITE_NAME, ln=CFG_SITE_LANG, doctype=""):
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
    except Error as e:
        return error_page(e, req, ln)
    #parses database to get all data
    ## first, get the list of categories
    doctype_categs = get_categories_of_doctype(doctype)
    for doctype_categ in doctype_categs:
        if not acc_authorize_action(req, 'submit', \
                                    authorized_if_no_roles=not isGuestUser(uid), \
                                    verbose=0, \
                                    doctype=doctype, \
                                    categ=doctype_categ[0])[0] == 0:
            # This category is restricted for this user, move on to the next categories.
            continue
        nbCateg = nbCateg+1
        snameCateg.append(doctype_categ[0])
        lnameCateg.append(doctype_categ[1])
    ## Now get the details of the document type:
    doctype_details = get_doctype_details(doctype)
    if doctype_details is None:
        ## Doctype doesn't exist - raise error:
        return warning_page(_("Unable to find document type: %(doctype)s",
                              doctype=escape(str(doctype))), req, ln)
    else:
        docFullDesc  = doctype_details[0]
        # Also update the doctype as returned by the database, since
        # it might have a differnent case (eg. DemOJrN->demoJRN)
        doctype = docShortDesc = doctype_details[1]
        description  = doctype_details[4]

    ## Get the details of the actions supported by this document-type:
    doctype_actions = get_actions_on_submission_page_for_doctype(doctype)
    for doctype_action in doctype_actions:
        if not acc_authorize_action(req, 'submit', \
                                    authorized_if_no_roles=not isGuestUser(uid), \
                                    doctype=doctype, \
                                    act=doctype_action[0])[0] == 0:
            # This action is not authorized for this user, move on to the next actions.
            continue
        ## Get the details of this action:
        action_details = get_action_details(doctype_action[0])
        if action_details is not None:
            actionShortDesc.append(doctype_action[0])
            indir.append(action_details[1])
            actionbutton.append(action_details[4])
            statustext.append(action_details[5])

    if not snameCateg and not actionShortDesc:
        if isGuestUser(uid):
            # If user is guest and does not have access to any of the
            # categories, offer to login.
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd({'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri, 'ln' : ln}, {})),
                                   norobot=True)
        else:
            return page_not_authorized(req, "../submit",
                                       uid=uid,
                                       text=_("You are not authorized to access this submission interface."),
                                       navmenuid='submit')


    ## Send the gathered information to the template so that the doctype's
    ## home-page can be displayed:
    t = websubmit_templates.tmpl_action_page(
          ln=ln,
          uid=uid,
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

    p_navtrail = """<a href="/submit?ln=%(ln)s" class="navtrail">%(submit)s</a>""" % {'submit' : _("Submit"),
                                                                                      'ln' : ln}

    return page(title = docFullDesc,
                body=t,
                navtrail=p_navtrail,
                description="submit documents",
                keywords="submit",
                uid=uid,
                language=ln,
                req=req,
                navmenuid='submit'
               )

def Request_Print(m, txt):
    """The argumemts to this function are the display mode (m) and the text
       to be displayed (txt).
    """
    return txt

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

def print_function_calls(req, doctype, action, step, form, start_time,
    access, curdir, dismode, rn, last_step, action_score,
    ln=CFG_SITE_LANG):
    """ Calls the functions required by an 'action'
    action on a 'doctype' document In supervisor mode, a table of the
    function calls is produced

    @return: (function_output_string, last_step, action_score, rn)
    """
    user_info = collect_user_info(req)
    # load the right message language
    _ = gettext_set_language(ln)
    t = ""
    ## Here follows the global protect environment.
    the_globals = {
        'doctype' : doctype,
        'action' : action,
        'act' : action, ## for backward compatibility
        'step' : step,
        'access' : access,
        'ln' : ln,
        'curdir' : curdir,
        'uid' : user_info['uid'],
        'uid_email' : user_info['email'],
        'rn' : rn,
        'last_step' : last_step,
        'action_score' : action_score,
        '__websubmit_in_jail__' : True,
        'form' : form,
        'user_info' : user_info,
        '__builtins__' : globals()['__builtins__'],
        'Request_Print': Request_Print
    }
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
            try:
                function_name = function[0]
                function_score = function[1]
                currfunction = {
                'name' : function_name,
                'score' : function_score,
                'error' : 0,
                'text' : '',
                }
                #FIXME: deprecated
                from invenio.legacy.websubmit import functions as legacy_functions
                function_path = os.path.join(legacy_functions.__path__[0],
                                             function_name + '.py')
                if os.path.exists(function_path):
                    # import the function itself
                    #function = getattr(invenio.legacy.websubmit.functions, function_name)
                    execfile(function_path, the_globals)
                    if function_name not in the_globals:
                        currfunction['error'] = 1
                    else:
                        the_globals['function'] = the_globals[function_name]

                        # Evaluate the parameters, and place them in an array
                        the_globals['parameters'] = Get_Parameters(function_name, doctype)
                        # Call function:
                        log_function(curdir, "Start %s" % function_name, start_time)
                        try:
                            try:
                                ## Attempt to call the function with 4 arguments:
                                ## ("parameters", "curdir" and "form" as usual),
                                ## and "user_info" - the dictionary of user
                                ## information:
                                ##
                                ## Note: The function should always be called with
                                ## these keyword arguments because the "TypeError"
                                ## except clause checks for a specific mention of
                                ## the 'user_info' keyword argument when a legacy
                                ## function (one that accepts only 'parameters',
                                ## 'curdir' and 'form') has been called and if
                                ## the error string doesn't contain this,
                                ## the TypeError will be considered as a something
                                ## that was incorrectly handled in the function and
                                ## will be propagated as an
                                ## InvenioWebSubmitFunctionError instead of the
                                ## function being called again with the legacy 3
                                ## arguments.
                                func_returnval = eval("function(parameters=parameters, curdir=curdir, form=form, user_info=user_info)", the_globals)
                            except TypeError as err:
                                ## If the error contains the string "got an
                                ## unexpected keyword argument", it means that the
                                ## function doesn't accept the "user_info"
                                ## argument. Test for this:
                                if "got an unexpected keyword argument 'user_info'" in \
                                str(err).lower():
                                    ## As expected, the function doesn't accept
                                    ## the user_info keyword argument. Call it
                                    ## again with the legacy 3 arguments
                                    ## (parameters, curdir, form):
                                    func_returnval = eval("function(parameters=parameters, curdir=curdir, form=form)", the_globals)
                                else:
                                    ## An unexpected "TypeError" was caught.
                                    ## It looks as though the function itself didn't
                                    ## handle something correctly.
                                    ## Convert this error into an
                                    ## InvenioWebSubmitFunctionError and raise it:
                                    msg = "Unhandled TypeError caught when " \
                                        "calling [%s] WebSubmit function: " \
                                        "[%s]: \n%s" % (function_name, str(err), traceback.format_exc())
                                    raise InvenioWebSubmitFunctionError(msg)
                        except InvenioWebSubmitFunctionWarning as err:
                            ## There was an unexpected behaviour during the
                            ## execution. Log the message into function's log
                            ## and go to next function
                            log_function(curdir, "***Warning*** from %s: %s" \
                                        % (function_name, str(err)), start_time)
                            ## Reset "func_returnval" to None:
                            func_returnval = None
                            register_exception(req=req, alert_admin=True, prefix="Warning in executing function %s with globals %s" % (pprint.pformat(currfunction), pprint.pformat(the_globals)))
                        log_function(curdir, "End %s" % function_name, start_time)
                        if func_returnval is not None:
                            ## Append the returned value as a string:
                            currfunction['text'] = str(func_returnval)
                        else:
                            ## The function the NoneType. Don't keep that value as
                            ## the currfunction->text. Replace it with the empty
                            ## string.
                            currfunction['text'] = ""
                else:
                    currfunction['error'] = 1
                functions.append(currfunction)
            except InvenioWebSubmitFunctionStop as err:
                ## The submission asked to stop execution. This is
                ## ok. Do not alert admin, and raise exception further
                log_function(curdir, "***Stop*** from %s: %s" \
                             % (function_name, str(err)), start_time)
                raise
            except:
                register_exception(req=req, alert_admin=True, prefix="Error in executing function %s with globals %s" % (pprint.pformat(currfunction), pprint.pformat(the_globals)))
                raise


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
    return (t, the_globals['last_step'], the_globals['action_score'], the_globals['rn'])


def Propose_Next_Action (doctype, action_score, access, currentlevel, indir, ln=CFG_SITE_LANG):
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

def specialchars(text):
    text = string.replace(text, "&#147;", "\042");
    text = string.replace(text, "&#148;", "\042");
    text = string.replace(text, "&#146;", "\047");
    text = string.replace(text, "&#151;", "\055");
    text = string.replace(text, "&#133;", "\056\056\056");
    return text

def log_function(curdir, message, start_time, filename="function_log"):
    """Write into file the message and the difference of time
    between starttime and current time
    @param curdir:(string) path to the destination dir
    @param message: (string) message to write into the file
    @param starttime: (float) time to compute from
    @param filname: (string) name of log file
    """
    time_lap = "%.3f" % (time.time() - start_time)
    if os.access(curdir, os.F_OK|os.W_OK):
        fd = open("%s/%s" % (curdir, filename), "a+")
        fd.write("""%s --- %s\n""" % (message, time_lap))
        fd.close()
