## $Id: Revise_Files.py,v 1.37 2009/03/26 15:11:05 jerome Exp $

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
"""WebSubmit function - Displays a generic interface to upload, delete
                        and revise files.

To be used on par with Move_Uploaded_Files_to_Storage function:
 - Create_Upload_Files_Interface records the actions performed by user.
 - Move_Uploaded_Files_to_Storage execute the recorded actions.


NOTE:
 - Comments are kept until they are changed: it is impossible to
   remove a comment...

 - Due to the way WebSubmit works, this function can only work when
   positionned at step 1 in WebSubmit admin, and
   Move_Uploaded_Files_to_Storage is at step 2

FIXME:

 - better differentiate between revised file, and added format
   (currently when adding a format, the whole bibdoc is marked as
   updated, and all links are removed)

 - After a file has been revised or added, add a 'check' icon

 - One issue: if we allow deletion or renaming, we might lose track of
   a bibdoc: someone adds X, renames X->Y, and adds again another file
   with name X: when executing actions, we will add the second X, and
   rename it to Y
   -> need to go back in previous action when renaming... or check
   that name has never been used..

"""

__revision__ = "$Id$"

from invenio.config import \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL, \
     CFG_SITE_LANG
import os
import time
from invenio.bibdocfile import \
     decompose_file, \
     calculate_md5, \
     BibRecDocs, \
     BibDocFile
from invenio.websubmit_functions.Shared_Functions import \
     createRelatedFormats
from invenio.messages import gettext_set_language, wash_language

allowed_actions = ['revise', 'delete', 'add', 'addFormat']

def Create_Upload_Files_Interface(parameters, curdir, form, user_info=None):
    """
    List files for revisions.

    You should use Move_Uploaded_Files_to_Storage.py function in your
    submission to apply the changes performed by users with this
    interface.

    @param parameters:(dictionary) - must contain:

      + maxsize: the max size allowed for uploaded files

      + minsize: the max size allowed for uploaded files

      + doctypes: the list of doctypes (like 'Main' or 'Additional')
                  and their description that users can choose from
                  when adding new files.
                   - When no value is provided, users cannot add new
                     file (they can only revise/delete/add format)
                   - When a single value is given, it is used as
                     default doctype for all new documents
                  Eg:
                    main=Main document|additional=Figure, schema. etc
                  ('=' separates doctype and description
                   '|' separates each doctype/description group)

      + restrictions: the list of restrictions (like 'Restricted' or
                      'No Restriction') and their description that
                      users can choose from when adding/revising
                      files. Restrictions can then be configured at
                      the level of WebAccess.
                      - When no value is provided, no restriction is
                        applied
                      - When a single value is given, it is used as
                        default resctriction for all documents.
                      - The first value of the list is used as default
                        restriction if the user if not given the
                        choice of the restriction. CHOOSE THE ORDER!
                      Eg:
                        =No restriction|restr=Restricted
                      ('=' separates restriction and description
                      '|' separates each restriction/description group)

      + canDeleteDoctypes: the list of doctypes that users are
                           allowed to delete.
                           Eg:
                             Main|Additional
                           ('|' separated values)
                           Use '*' for all doctypes

      + canReviseDoctypes: the list of doctypes that users are
                           allowed to revise
                           Eg:
                             Main|Additional
                           ('|' separated values)
                           Use '*' for all doctypes

      + canDescribeDoctypes: the list of doctypes that users are
                            allowed to describe
                            Eg:
                              Main|Additional
                            ('|' separated values)
                            Use '*' for all doctypes

      + canCommentDoctypes: the list of doctypes that users are
                            allowed to comment
                            Eg:
                              Main|Additional
                            ('|' separated values)
                            Use '*' for all doctypes

      + canKeepDoctypes: the list of doctypes for which users can
                         choose to keep previous versions visible when
                         revising a file (i.e. 'Keep previous version'
                         checkbox). See also parameter 'keepDefault'.
                         Note that this parameter is ~ignored when
                         revising the attributes of a file (comment,
                         description) without uploading a new
                         file. See also parameter
                         Move_Uploaded_Files_to_Storage.forceFileRevision
                         Eg:
                           Main|Additional
                         ('|' separated values)
                         Use '*' for all doctypes


      + canAddFormatDoctypes: the list of doctypes for which users can
                              add new formats. If there is no value,
                              then no 'add format' link nor warning
                              about losing old formats are displayed.
                              Eg:
                                Main|Additional
                              ('|' separated values)
                              Use '*' for all doctypes

      + canRestrictDoctypes: the list of doctypes for which users can
                             choose the access restrictions when adding or
                             revising a file. If no value is given:
                             - no restriction is applied if none is defined
                               in the 'restrictions' parameter.
                             - else the *first* value of the 'restrictions'
                               parameter is used as default restriction.
                             Eg:
                               Main|Additional
                             ('|' separated values)
                             Use '*' for all doctypes

      + canRenameDoctypes: the list of doctypes that users are allowed
                           to rename (when revising)
                           Eg:
                             Main|Additional
                           ('|' separated values)
                           Use '*' for all doctypes

      + canNameNewFiles: if user can choose the name of the files they
                         upload (1) or not (0)

      + defaultFilenameDoctypes: Rename uploaded files to admin-chosen
                                 values. List here the the files in
                                 current submission directory that
                                 contain the names to use for each doctype.
                                 Eg:
                                 Main=RN|Additional=additional_filename
                                 ('=' separates doctype and file in curdir
                                 '|' separates each doctype/file group).

                                 If the same doctype is submitted
                                 several times, a"-%i" suffix is added
                                 to the name defined in the file.

                                 The default filenames are overriden
                                 by user-chosen names if you allow
                                 'canNameNewFiles' or
                                 'canRenameDoctypes'.

      + maxFilesDoctypes: the maximum number of files that users can
                          upload for each doctype.
                          Eg:
                            Main=1|Additional=2
                          ('|' separated values)

                          Do not specify the doctype here to have an
                          unlimited number of files for a given
                          doctype.

      + createRelatedFormats: if uploaded files get converted to
                              whatever format we can (1) or not (0)

      + keepDefault: the default behaviour for keeping or not previous
                     version of files when users cannot choose (no
                     value in canKeepDoctypes): keep (1) or not (0)
                     Note that this parameter is ignored when revising
                     the attributes of a file (comment, description)
                     without uploading a new file. See also parameter
                     Move_Uploaded_Files_to_Storage.forceFileRevision

      + showLinks: if we display links to files (1) when possible or
                   not (0)

      + fileLabel: the label for the file field

      + filenameLabel: the label for the file name field

      + descriptionLabel: the label for the description field

      + commentLabel: the label for the comments field

      + restrictionLabel: the label in front of the restrictions list

      + startDoc: the name of a file in curdir that contains some
                  text/markup to be printed *before* the file revision
                  box

      + endDoc: the name of a file in curdir that contains some
                text/markup to be printed *after* the file revision
                box

    """
    global sysno
    ln = wash_language(form['ln'])
    _ = gettext_set_language(ln)
    out = ''

    ## Fetch parameters defined for this function
    (minsize, maxsize, doctypes_and_desc, doctypes,
     can_delete_doctypes, can_revise_doctypes, can_describe_doctypes,
     can_comment_doctypes, can_keep_doctypes, can_rename_doctypes,
     can_add_format_to_doctypes, createRelatedFormats_p,
     can_name_new_files, keep_default, show_links, file_label,
     filename_label, description_label, comment_label, startDoc,
     endDoc, restrictions_and_desc, can_restrict_doctypes,
     restriction_label, doctypes_to_default_filename,
     max_files_for_doctype) = \
     wash_function_parameters(parameters, curdir, ln)

    # Get the existing bibdocs as well as the actions performed during
    # the former revise sessions of the user, to build an updated list
    # of documents. We will use it to check if last action performed
    # by user is allowed.
    bibrecdocs = []
    if sysno:
        bibrecdocs = BibRecDocs(sysno)
    bibdocs = bibrecdocs.list_bibdocs()
    performed_actions = read_actions_log(curdir)
    # "merge":
    abstract_bibdocs = build_updated_files_list(bibdocs,
                                                performed_actions,
                                                sysno or -1)

    ## Get and clean parameters received from user
    (file_action, file_target, file_target_doctype,
    keep_previous_files, file_description, file_comment, file_rename,
    file_doctype, file_restriction) = \
    wash_form_parameters(form, abstract_bibdocs, can_keep_doctypes,
    keep_default, can_describe_doctypes, can_comment_doctypes,
    can_rename_doctypes, can_name_new_files, can_restrict_doctypes,
    doctypes_to_default_filename)

    ## Check the last action performed by user, and log it if
    ## everything is ok
    if os.path.exists("%s/myfile" % curdir) and \
           ((file_action == 'add' and (file_doctype in doctypes)) or \
            (file_action == 'revise' and \
             ((file_target_doctype in can_revise_doctypes) or \
              '*' in can_revise_doctypes)) or
            (file_action == 'addFormat' and \
             ((file_target_doctype in can_add_format_to_doctypes) or \
              '*' in can_add_format_to_doctypes))):
        # A file has been uploaded (user has revised or added a file,
        # or a format)
        file_desc = open("%s/myfile" % curdir, "r")
        myfile = file_desc.read()
        file_desc.close()
        dirname, filename, extension = decompose_file(myfile)
        fullpath = os.path.join(curdir, 'files', 'myfile', myfile)
        os.unlink("%s/myfile" % curdir)
        if minsize.isdigit() and os.path.getsize(fullpath) < int(minsize):
            os.unlink(fullpath)
            out += '<script>alert("%s");</script>' % \
                   (_("The uploaded file is too small (<%i o) and has therefore not been considered") % \
                    int(minsize)).replace('"', '\\"')
        elif maxsize.isdigit() and os.path.getsize(fullpath) > int(maxsize):
            os.unlink(fullpath)
            out += '<script>alert("%s");</script>' % \
                   (_("The uploaded file is too big (>%i o) and has therefore not been considered") % \
                    int(maxsize)).replace('"', '\\"')
        elif len(filename) + len(extension) + 4 > 255:
            # Max filename = 256, including extension and version that
            # will be appended later by BibDoc
            os.unlink(fullpath)
            out += '<script>alert("%s");</script>' % \
                   _("The uploaded file name is too long and has therefore not been considered").replace('"', '\\"')

        elif file_action == 'add' and \
                 max_files_for_doctype.has_key(file_doctype) and \
                 max_files_for_doctype[file_doctype] < \
                 (len([bibdoc for bibdoc in abstract_bibdocs \
                       if bibdoc['get_type'] == file_doctype]) + 1):
            # User has tried to upload more than allowed for this
            # doctype.  Should never happen, unless the user did some
            # nasty things
            os.unlink(fullpath)
            out += '<script>alert("%s");</script>' % \
                   _("You have already reached the maximum number of files for this type of document").replace('"', '\\"')

        else:
            # Prepare to move file to
            # curdir/files/updated/doctype/bibdocname/
            folder_doctype = file_doctype or \
                             bibrecdocs.get_bibdoc(file_target).get_type()
            folder_bibdocname = file_rename or file_target or filename
            new_fullpath = os.path.join(curdir, 'files', 'updated',
                                        folder_doctype,
                                        folder_bibdocname, myfile)

            # First check that we do not conflict with an already
            # existing bibdoc name
            if file_action == "add" and \
                   ((filename in [bibdoc['get_docname'] for bibdoc \
                                  in abstract_bibdocs] and not file_rename) or \
                    file_rename in [bibdoc['get_docname'] for bibdoc \
                                 in abstract_bibdocs]):
                # A file with that name already exist. Cancel action
                # and tell user.
                os.unlink(fullpath)
                out += '<script>alert("%s");</script>' % \
                       (_("A file named %s already exists. Please choose another name.") % \
                        (file_rename or filename)).replace('"', '\\"')

            elif file_action == "revise" and \
                 file_rename != file_target and \
                 file_rename in [bibdoc['get_docname'] for bibdoc \
                                in abstract_bibdocs]:
                # A file different from the one to revise already has
                # the same bibdocname
                os.unlink(fullpath)
                out += '<script>alert("%s");</script>' % \
                       (_("A file named %s already exists. Please choose another name.") % \
                        file_rename).replace('"', '\\"')

            elif file_action == "addFormat" and \
                     (extension in \
                       get_extensions_for_docname(file_target,
                                                  abstract_bibdocs)):
                # A file with that extension already exists. Cancel
                # action and tell user.
                os.unlink(fullpath)
                out += '<script>alert("%s");</script>' % \
                       (_("A file with format '%s' already exists. Please upload another format.") % \
                        extension).replace('"', '\\"')
            elif '.' in file_rename  or '/' in file_rename or "\\" in file_rename or \
                     not os.path.abspath(new_fullpath).startswith(os.path.join(curdir, 'files', 'updated')):
                # We forbid usage of a few characters, for the good of
                # everybody...
                os.unlink(fullpath)
                out += '<script>alert("%s");</script>' % \
                       _("You are not allowed to use dot '.', slash '/', or backslash '\\\\' in file names. Choose a different name and upload your file again. In particular, note that you should not include the extension in the renaming field.").replace('"', '\\"')
            else:
                # No conflict with file name

                # When revising, delete previously uploaded files for
                # this entry, so that we do not execute the
                # corresponding action
                if file_action == "revise":
                    for path_to_delete in \
                            get_uploaded_files_for_docname(curdir, file_target):
                        delete(curdir, path_to_delete)

                # Move uploaded file to curdir/files/updated/doctype/bibdocname/
                os.renames(fullpath, new_fullpath)

                if file_action == "add":
                    # if not bibrecdocs.check_file_exists(new_fullpath): # No need to check: done before...
                    # Log
                    if file_rename != '':
                        # at this point, bibdocname is specified
                        # name, no need to 'rename'
                        filename = file_rename
                    log_action(curdir, file_action, filename,
                               new_fullpath, file_rename,
                               file_description, file_comment,
                               file_doctype, keep_previous_files,
                               file_restriction)

                    # Automatically create additional formats when
                    # possible.
                    additional_formats = []
                    if createRelatedFormats_p:
                        additional_formats = createRelatedFormats(new_fullpath,
                                                                  overwrite=False)

                    for additional_format in additional_formats:
                        # Log
                        log_action(curdir, 'addFormat', filename,
                                   additional_format, file_rename,
                                   file_description, file_comment,
                                   file_doctype, True, file_restriction)

            if file_action == "revise" and file_target != "":
                # Log
                log_action(curdir, file_action, file_target,
                           new_fullpath, file_rename,
                           file_description, file_comment,
                           file_target_doctype, keep_previous_files,
                           file_restriction)
                # Automatically create additional formats when
                # possible.
                additional_formats = []
                if createRelatedFormats_p:
                    additional_formats = createRelatedFormats(new_fullpath,
                                                              overwrite=False)

                for additional_format in additional_formats:
                    # Log
                    log_action(curdir, 'addFormat',
                               (file_rename or file_target),
                               additional_format, file_rename,
                               file_description, file_comment,
                               file_target_doctype, True,
                               file_restriction)

            if file_action == "addFormat" and file_target != "":
                # We have already checked above that this format does
                # not already exist.
                # Log
                log_action(curdir, file_action, file_target,
                           new_fullpath, file_rename,
                           file_description, file_comment,
                           file_target_doctype, keep_previous_files,
                           file_restriction)

    elif file_action in ["add", "addFormat"]:
        # No file found, but action involved adding file: ask user to
        # select a file
        out += """<script>
        alert("You did not specify a file. Please choose one before uploading.");
        </script>"""

    elif file_action ==  "revise" and file_target != "":
        # User has chosen to revise attributes of a file (comment,
        # name, etc.) without revising the file itself.
        if file_rename != file_target and \
               file_rename in [bibdoc['get_docname'] for bibdoc \
                               in abstract_bibdocs]:
            # A file different from the one to revise already has
            # the same bibdocname
            out += '<script>alert("%s");</script>' % \
                   (_("A file named %s already exists. Please choose another name.") % \
                    file_rename).replace('"', '\\"')
        else:
            # Log
            log_action(curdir, file_action, file_target,
                       "", file_rename,
                       file_description, file_comment,
                       file_target_doctype, keep_previous_files,
                       file_restriction)


    elif file_action == "delete" and file_target != "" and \
           ((file_target_doctype in can_delete_doctypes) or \
            '*' in can_delete_doctypes):
        # Delete previously uploaded files for this entry
        for path_to_delete in get_uploaded_files_for_docname(curdir, file_target):
            delete(curdir, path_to_delete)
        # Log
        log_action(curdir, file_action, file_target, "", file_rename,
                   file_description, file_comment, "",
                   keep_previous_files, file_restriction)

    ## Display

    # Create the list of files based on current files and performed
    # actions
    performed_actions = read_actions_log(curdir)
    bibdocs = bibrecdocs.list_bibdocs()
    abstract_bibdocs = build_updated_files_list(bibdocs, performed_actions, sysno or -1)
    abstract_bibdocs.sort(lambda x, y: x['order'] - y['order'])

    # Display form and necessary CSS + Javscript
    out += '<center><form>'
    out += css
    out += javascript % {'can_describe_doctypes': repr({}.fromkeys(can_describe_doctypes, '')),
                         'can_comment_doctypes': repr({}.fromkeys(can_comment_doctypes, '')),
                         'can_restrict_doctypes': repr({}.fromkeys(can_restrict_doctypes, ''))}

    # Prepare to display file revise panel "balloon".  Check if we
    # should display the list of doctypes or if it is not necessary (0
    # or 1 doctype). Also make sure that we do not exceed the maximum
    # number of files specified per doctype.
    cleaned_doctypes = [doctype for doctype in doctypes if
                        not max_files_for_doctype.has_key(doctype) or
                        (max_files_for_doctype[doctype] > \
                        len([bibdoc for bibdoc in abstract_bibdocs \
                             if bibdoc['get_type'] == doctype]))]
    doctypes_list = ""
    if len(cleaned_doctypes) > 1:
        doctypes_list = '<select id="fileDoctype" name="fileDoctype" onchange="var idx=this.selectedIndex;var doctype=this.options[idx].value;updateForm(doctype);">' + \
                        '\n'.join(['<option value="' + doctype + '">' + \
                                   description + '</option>' \
                                   for (doctype, description) \
                                   in doctypes_and_desc if \
                                   doctype in cleaned_doctypes]) + \
                        '</select>'
    elif len(cleaned_doctypes) == 1:
        doctypes_list = '<input id="fileDoctype" name="fileDoctype" type="hidden" value="%s" />' % cleaned_doctypes[0]

    # Check if we should display the list of access restrictions or if
    # it is not necessary
    restrictions_list = ""
    if len(restrictions_and_desc) > 1:
        restrictions_list = '<select id="fileRestriction" name="fileRestriction">' + \
                        '\n'.join(['<option value="' + restriction + '">' + \
                                   description + '</option>' \
                                   for (restriction, description) \
                                   in restrictions_and_desc]) + \
                        '</select>'
        restrictions_list = '''<label for="restriction">%(restriction_label)s:</label>&nbsp;%(restrictions_list)s&nbsp;<small>[<a href="" onclick="javascript:alert('%(restriction_help)s');return false;">?</a>]</small>''' % \
                            {'restrictions_list': restrictions_list,
                             'restriction_label': restriction_label,
                             'restriction_help': _('Choose how you want to restrict access to this file.').replace("'", "\\'")}

    elif len(restrictions_and_desc) == 1:
        restrictions_list = '<select style="display:none" id="fileRestriction" name="fileRestriction"><option value="%(restriction)s">%(restriction)s</option></select>' % {'restriction': restrictions_and_desc[0][0]}
    else:
        restrictions_list = '<select style="display:none" id="fileRestriction" name="fileRestriction"></select>'

    out += revise_balloon % \
           {'CFG_SITE_URL': CFG_SITE_URL,
            'doctypes': '<div style="display:none" id="fileDoctypesRow">' + \
                         doctypes_list + '</div>',
            'file_label': file_label,
            'filename_label': filename_label,
            'description_label': description_label,
            'comment_label': comment_label,
            'restrictions': restrictions_list,
            'previous_versions_help': _('You can decide to hide or not previous version(s) of this file.').replace("'", "\\'"),
            'revise_format_help': _('When you revise a file, the additional formats that you might have previously uploaded are removed, since they no longer up-to-date with the new file.').replace("'", "\\'"),
            'revise_format_warning': _('Alternative formats uploaded for current version of this file will be removed'),
            'previous_versions_label': _('Keep previous versions'),
            'cancel': _('Cancel'),
            'upload': _('Upload')}

    # List the files
    out += '''
<div id="reviseControl">
    <table class="reviseControlBrowser">'''
    i = 0
    for bibdoc in abstract_bibdocs:
        if bibdoc['list_latest_files']:
            i += 1
            out += create_file_row(bibdoc, can_delete_doctypes,
                                   can_rename_doctypes,
                                   can_revise_doctypes,
                                   can_describe_doctypes,
                                   can_comment_doctypes,
                                   can_keep_doctypes,
                                   can_add_format_to_doctypes, show_links,
                                   can_restrict_doctypes,
                                   even=not (i % 2),
                                   ln=ln)
    out += '</table>'
    if len(cleaned_doctypes) > 0:
        out += '''<a href="" onclick="javascript:display_revise_panel(this, 'add', '', true, false, %(showRename)s, true, true, '', '', '', true, '%(restriction)s');updateForm('%(defaultSelectedDoctype)s');return false;">%(add_new_file)s</a>
        ''' % {'showRename': can_name_new_files and 'true' or 'false',
               'defaultSelectedDoctype': doctypes[0],
               'add_new_file': _("Add new file"),
               'restriction': len(restrictions_and_desc) > 0 and restrictions_and_desc[0][0] or ''}
    out += '</div>'

    # End submission button
    out += '''<br /><p style="text-align:center;font-size:small">
    <input type="button" height="35" width="250" name="Submit" id="applyChanges" value="%(apply_changes)s" onClick="nextStep();"></p>''' % \
    {'apply_changes': _("Apply changes")}

    if startDoc:
        # Add a prefix
        prefix = read_file(curdir, startDoc)
        if prefix:
            out = prefix + out

    if endDoc:
        # Add a suffix
        suffix = read_file(curdir, endDoc)
        if suffix:
            out += '</center>' + suffix + '<center>'

    # Close form
    out += '</form>'

    # Display a link to support email in case users have problem
    # revising/adding files
    mailto_link = '<a href="mailto:%(CFG_SITE_SUPPORT_EMAIL)s?subject=%(email_subject)s&amp;body=%(email_body)s">%(CFG_SITE_SUPPORT_EMAIL)s</a>' % \
    {'CFG_SITE_SUPPORT_EMAIL': CFG_SITE_SUPPORT_EMAIL,
     'email_subject': "Need%%20help%%20revising%%20or%%20adding%%20record%%20%(sysno)s" % {'sysno': sysno or '(new)'},
     'email_body': "Dear%%20CDS%%20Support,%%0D%%0A%%0D%%0AI%%20need%%20help%%20to%%20revise%%20or%%20add%%20a%%20file%%20in%%20record%%20%(sysno)s.%%20I%%20have%%20attached%%20the%%20new%%20version%%20to%%20this%%20mail.%%0D%%0A%%0D%%0ABest%%20regards" % {'sysno': sysno or '(new)'}}

    problem_revising = _('Having a problem revising a file? Send the revised version to %(mailto_link)s.') % {'mailto_link': mailto_link}
    if len(cleaned_doctypes) > 0:
        # We can add files, so change note
        problem_revising = 'Having a problem adding or revising a file? Send the new/revised version to %(mailto_link)s.' % {'mailto_link': mailto_link}

    out += '<br />'
    out += problem_revising
    out += '</center>'

    return out

def create_file_row(abstract_bibdoc, can_delete_doctypes,
                    can_rename_doctypes, can_revise_doctypes,
                    can_describe_doctypes, can_comment_doctypes,
                    can_keep_doctypes, can_add_format_to_doctypes,
                    show_links, can_restrict_doctypes, even=False,
                    ln=CFG_SITE_LANG):
    """
    Creates a row in the files list.

    Parameters :
           abstract_bibdoc - list of "fake" BibDocs: it is a list of dictionaries
                             with keys 'list_latest_files' and 'get_docname' with
                             values corresponding to what you would expect to receive
                             when calling their counterpart function on a real BibDoc
                             object.

       can_delete_doctypes - list of doctypes for which we allow users to delete
                             documents

       can_revise_doctypes - the list of doctypes that users are
                             allowed to revise.

     can_describe_doctypes - the list of doctypes that users are
                             allowed to describe.

      can_comment_doctypes - the list of doctypes that users are
                             allowed to comment.

         can_keep_doctypes - the list of doctypes for which users can
                             choose to keep previous versions visible
                             when revising a file (i.e. 'Keep previous
                             version' checkbox).

       can_rename_doctypes - the list of doctypes that users are
                             allowed to rename (when revising)

can_add_format_to_doctypes - the list of doctypes for which users can
                             add new formats

                show_links - if we display links to files

                      even - if the row is even or odd on the list
    """
    _ = gettext_set_language(ln)

    # Try to retrieve "main format", to display as link for the
    # file. There is no such concept in BibDoc, but let's just try to
    # get the pdf file if it exists
    main_bibdocfile = [bibdocfile for bibdocfile in abstract_bibdoc['list_latest_files'] \
                       if bibdocfile.get_format().strip('.').lower() == 'pdf']
    if len(main_bibdocfile) > 0:
        main_bibdocfile = main_bibdocfile[0]
    else:
        main_bibdocfile = abstract_bibdoc['list_latest_files'][0]

    main_bibdocfile_description = main_bibdocfile.get_description()
    if main_bibdocfile_description is None:
        main_bibdocfile_description = ''

    updated = abstract_bibdoc['updated'] # Has BibDoc been updated?

    # Main file row
    out = '<tr%s>' % (even and ' class="even"' or '')
    out += '<td class="reviseControlFileColumn">'
    if not updated and show_links:
        out += '<a target="_blank" href="' + main_bibdocfile.get_url() \
           + '">'
    out += abstract_bibdoc['get_docname']
    if not updated and show_links:
        out += '</a>'
    if main_bibdocfile_description:
        out += ' (<em>' + main_bibdocfile_description + '</em>)'
    out += '</td>'

    (description, comment) = get_description_and_comment(abstract_bibdoc['list_latest_files'])
    restriction = abstract_bibdoc['get_status']

    # Revise link
    out += '<td class="reviseControlActionColumn">'
    if main_bibdocfile.get_type() in can_revise_doctypes or \
           '*' in can_revise_doctypes:
        out += '''[<a href="" onclick="javascript:display_revise_panel(this, 'revise', '%(bibdocname)s', false, %(showKeepPreviousVersions)s, %(showRename)s, %(showDescription)s, %(showComment)s, '%(bibdocname)s', '%(description)s', '%(comment)s', %(showRestrictions)s, '%(restriction)s');return false;">%(revise)s</a>]
        ''' % {'bibdocname': abstract_bibdoc['get_docname'].replace("'", "\\'").replace('"', '&quot;'),
               'showRename': ((main_bibdocfile.get_type() in can_rename_doctypes) or \
                              '*' in can_rename_doctypes) and \
                              'true' or 'false',
               'showKeepPreviousVersions': ((main_bibdocfile.get_type() in can_keep_doctypes) or \
                                            '*' in can_keep_doctypes) and \
                                            'true' or 'false',
               'showComment': ((main_bibdocfile.get_type() in can_comment_doctypes) or \
                               '*' in can_comment_doctypes) and \
                               'true' or 'false',
               'showDescription': ((main_bibdocfile.get_type() in can_describe_doctypes) or \
                                   '*' in can_describe_doctypes) and \
                                'true' or 'false',
               'description': description and description.replace("'", "\\'").replace('"', '&quot;') or '',
               'comment': comment and comment.replace("'", "\\'").replace('"', '&quot;') or '',
               'showRestrictions': ((main_bibdocfile.get_type() in can_restrict_doctypes) or \
                                   '*' in can_restrict_doctypes) and \
                                'true' or 'false',
               'restriction': restriction.replace("'", "\\'").replace('"', '&quot;'),
               'revise': _("revise")}

    # Delete link
    if main_bibdocfile.get_type() in can_delete_doctypes or \
           '*' in can_delete_doctypes:
        out += '''[<a href="" onclick="if(confirm('Are you sure you want to delete %(bibdocname)s?')){document.forms[0].fileTarget.value = '%(bibdocname)s';javascript:document.forms[0].fileAction.value='delete';user_must_confirm_before_leaving_page = false;document.forms[0].submit();}return false;">%(delete)s</a>]
        ''' % {'bibdocname': abstract_bibdoc['get_docname'].replace("'", "\\'").replace('"', '&quot;'),
               'delete': _("delete")}
    out += '''</td>'''

    # Format row
    out += '''<tr%s>
    <td class="reviseControlFormatColumn">
        <img src="%s/img/tree_branch.gif" alt="">
    ''' % (even and ' class="even"' or '', CFG_SITE_URL)
    for bibdocfile in abstract_bibdoc['list_latest_files']:
        if not updated and show_links:
            out += '<a target="_blank" href="' + bibdocfile.get_url() + '">'
        out += bibdocfile.get_format().strip('.')
        if not updated and show_links:
            out += '</a>'
        out += ' '

    # Add format link
    out += '<td class="reviseControlActionColumn">'
    if main_bibdocfile.get_type() in can_add_format_to_doctypes or \
           '*' in can_add_format_to_doctypes:
        out += '''[<a href="" onclick="javascript:display_revise_panel(this, 'addFormat', '%(bibdocname)s', false, false, false, false, false, '', '', '', false, '%(restriction)s');return false;">%(add_format)s</a>]
    </td>''' % {'bibdocname': abstract_bibdoc['get_docname'].replace("'", "\\'").replace('"', '&quot;'),
                'add_format': _("add format"),
                'restriction': restriction}
    out += '</td></tr>'

    return out

def log_action(log_dir, action, bibdoc_name, file_path, rename,
               description, comment, doctype, keep_previous_versions,
               file_restriction):
    """
    Logs a new action performed by user on a BibDoc file.

    Parameters:
           log_dir  -  directory where to save the log (ie. curdir)

            action  -  the performed action (one of 'revise', 'delete',
                       'add', 'addFormat')

       bibdoc_name  -  the name of the bibdoc on which the change is
                       applied

         file_path  -  the path to the file that is going to be
                       integrated as bibdoc, if any (should be ""
                       in case of action="delete", or action="revise"
                       when revising only attributes of a file)

            rename  -  the name used to display the bibdoc, instead of
                       the filename (can be None for no renaming)

       description  -  a description associated with the file

           comment  -  a comment associated with the file

           doctype  -  the category in which the file is going to be
                       integrated

    keep_previous_versions - if the previous versions of this file are
                             to be hidden (0) or not (1)

          file_restriction - the restriction applied to the
                             file. Empty string if no restriction

    There is one action per line in the file, each column being split
    by '---' ('---' is escaped from values 'rename', 'description',
    'comment' and 'bibdoc_name')

    Each line starts with the time of the action in the following
    format: '2008-06-20 08:02:04 --> '

    """
    log_file = os.path.join(log_dir, 'bibdocactions.log')
    try:
        file_desc = open(log_file, "a+")
        msg = action                                 + '---' + \
              bibdoc_name.replace('---', '___')      + '---' + \
              file_path                              + '---' + \
              str(rename).replace('---', '___')      + '---' + \
              str(description).replace('---', '___') + '---' + \
              str(comment).replace('---', '___')     + '---' + \
              doctype                                + '---' + \
              str(int(keep_previous_versions))       + '---' + \
              file_restriction + '\n'
        file_desc.write("%s --> %s" %(time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        file_desc.close()
    except Exception ,e:
        raise e

def read_actions_log(log_dir):
    """
    Reads the logs of action to be performed on files

    See log_action(..) for more information about the structure of the
    log file.
    """
    actions = []
    log_file = os.path.join(log_dir, 'bibdocactions.log')
    try:
        file_desc = open(log_file, "r")
        for line in file_desc.readlines():
            (timestamp, action) = line.split(' --> ', 1)
            try:
                (action, bibdoc_name, file_path, rename, description,
                 comment, doctype, keep_previous_versions,
                 file_restriction) = action.rstrip('\n').split('---')
            except ValueError, e:
                # Malformed action log
                pass

            # Perform some checking
            if action not in allowed_actions:
                # Malformed action log
                pass

            try:
                keep_previous_versions = int(keep_previous_versions)
            except:
                # Malformed action log
                keep_previous_versions = 1
                pass

            actions.append((action, bibdoc_name, file_path, rename, \
                            description, comment, doctype,
                            keep_previous_versions, file_restriction))
        file_desc.close()
    except:
        pass

    return actions

def build_updated_files_list(bibdocs, actions, recid):
    """
    Parses the list of BibDocs and builds an updated version to reflect
    the changes performed by the user of the file

    It is necessary to abstract the BibDocs since user wants to
    perform action on the files that are committed only at the end of
    the session.
    """
    abstract_bibdocs = {}
    i = 0
    for bibdoc in bibdocs:
        i += 1
        status = bibdoc.get_status()
        if status == "DELETED":
            status = ''

        abstract_bibdocs[bibdoc.get_docname()] = \
            {'list_latest_files': bibdoc.list_latest_files(),
             'get_docname': bibdoc.get_docname(),
             'updated': False,
             'get_type': bibdoc.get_type(),
             'get_status': status,
             'order': i}

    for action, bibdoc_name, file_path, rename, description, \
            comment, doctype, keep_previous_versions, \
            file_restriction in actions:
        dirname, filename, format = decompose_file(file_path)
        i += 1
        if action in ["add", "revise"] and \
               os.path.exists(file_path):
            checksum = calculate_md5(file_path)
            order = i
            if action == "revise" and \
                   abstract_bibdocs.has_key(bibdoc_name):
                # Keep previous values
                order = abstract_bibdocs[bibdoc_name]['order']
                doctype = abstract_bibdocs[bibdoc_name]['get_type']
            if bibdoc_name.strip() == '' and rename.strip() == '':
                bibdoc_name = os.path.extsep.join(filename.split(os.path.extsep)[:-1])
            elif rename.strip() != '' and \
                     abstract_bibdocs.has_key(bibdoc_name):
                # Keep previous position
                del abstract_bibdocs[bibdoc_name]

            abstract_bibdocs[(rename or bibdoc_name)] = \
                {'list_latest_files': [BibDocFile(file_path, doctype, version=1,
                                                  name=(rename or bibdoc_name),
                                                  format=format,
                                                  recid=int(recid), docid=-1,
                                                  status=file_restriction,
                                                  checksum=checksum,
                                                  description=description,
                                                  comment=comment)],
                 'get_docname': rename or bibdoc_name,
                 'get_type': doctype,
                 'updated': True,
                 'get_status': file_restriction,
                 'order': order}
            abstract_bibdocs[(rename or bibdoc_name)]['updated'] = True
        elif action == "revise" and not file_path:
            # revision of attributes of a file (description, name,
            # comment or restriction) but no new file.
            abstract_bibdocs[bibdoc_name]['get_docname'] = rename or bibdoc_name
            abstract_bibdocs[bibdoc_name]['get_status'] = file_restriction
            set_description_and_comment(abstract_bibdocs[bibdoc_name]['list_latest_files'],
                                        description, comment)
            abstract_bibdocs[bibdoc_name]['updated'] = True
        elif action == "delete":
            if abstract_bibdocs.has_key(bibdoc_name):
                del abstract_bibdocs[bibdoc_name]
        elif action == "addFormat" and \
               os.path.exists(file_path):
            checksum = calculate_md5(file_path)
            # Preserve type and status
            doctype = abstract_bibdocs[bibdoc_name]['get_type']
            file_restriction = abstract_bibdocs[bibdoc_name]['get_status']
            abstract_bibdocs[bibdoc_name]['list_latest_files'].append(\
                BibDocFile(file_path, doctype, version=1,
                           name=(rename or bibdoc_name), format=format,
                           recid=int(recid), docid=-1, status='',
                           checksum=checksum, description=description,
                           comment=comment))
            abstract_bibdocs[bibdoc_name]['updated'] = True

    return abstract_bibdocs.values()

def get_uploaded_files_for_docname(log_dir, docname):
    """
    Given a docname, returns the paths to the files uploaded for this
    revision session.
    """
    return [file_path for action, bibdoc_name, file_path, rename, \
            description, comment, doctype, keep_previous_versions , \
            file_restriction in read_actions_log(log_dir) \
            if bibdoc_name == docname and os.path.exists(file_path)]

def get_bibdoc_for_docname(docname, abstract_bibdocs):
    """
    Given a docname, returns the corresponding bibdoc from the
    'abstract' bibdocs.

    Return None if not found
    """
    bibdocs = [bibdoc for bibdoc in abstract_bibdocs \
               if bibdoc['get_docname'] == docname]
    if len(bibdocs) > 0:
        return bibdocs[0]
    else:
        return None

def get_extensions_for_docname(docname, abstract_bibdocs):
    """Returns the list of extensions that exists for given bibdoc
    name in the given 'abstract' bibdocs."""

    bibdocfiles = [bibdoc['list_latest_files'] for bibdoc \
                   in abstract_bibdocs \
                   if bibdoc['get_docname'] == docname]
    if len(bibdocfiles) > 0:
        # There should always be at most 1 matching docname, or 0 if
        # it is a new file
        return [bibdocfile.get_format() for bibdocfile \
                in bibdocfiles[0]]
    return []

def delete(curdir, file_path):
    """
    Deletes a file at given path from the file.
    In fact, we just move it to curdir/files/trash
    """
    if os.path.exists(file_path):
        filename = os.path.split(file_path)[1]
        move_to = os.path.join(curdir, 'files', 'trash',
                               filename +'_' + str(time.time()))
        os.renames(file_path, move_to)


def wash_function_parameters(parameters, curdir, ln=CFG_SITE_LANG):
    """
    Returns the functions (admin-defined) parameters washed and
    initialized properly, as a tuple:

    Parameters:

        check Create_Upload_Files_Interface(..) docstring

    Returns:

        tuple (minsize, maxsize, doctypes_and_desc, doctypes,
        can_delete_doctypes, can_revise_doctypes,
        can_describe_doctypes can_comment_doctypes, can_keep_doctypes,
        can_rename_doctypes, can_add_format_to_doctypes,
        createRelatedFormats_p, can_name_new_files, keep_default,
        show_links, file_label, filename_label, description_label,
        comment_label, startDoc, endDoc, access_restrictions_and_desc,
        can_restrict_doctypes, restriction_label,
        doctypes_to_default_filename, max_files_for_doctype)
    """
    _ = gettext_set_language(ln)

    # The min and max files sizes that users can upload
    minsize = parameters['minsize']
    maxsize = parameters['maxsize']

    # The list of doctypes + description that users can select when
    # adding new files.  If there are no values, then user cannot add
    # new files.  '|' is used to separate doctypes groups, and '=' to
    # separate doctype and description. Eg:
    # main=Main document|additional=Figure, schema. etc
    doctypes_and_desc = [doctype.strip().split("=") for doctype \
                         in parameters['doctypes'].split('|') \
                         if doctype.strip() != '']
    doctypes = [doctype for (doctype, desc) in doctypes_and_desc]
    doctypes_and_desc = [[doctype, _(desc)] for \
                         (doctype, desc) in doctypes_and_desc]

    # The list of doctypes users are allowed to delete
    # (list of values separated by "|")
    can_delete_doctypes = [doctype.strip() for doctype \
                           in parameters['canDeleteDoctypes'].split('|') \
                           if doctype.strip() != '']

    # The list of doctypes users are allowed to revise
    # (list of values separated by "|")
    can_revise_doctypes = [doctype.strip() for doctype \
                           in parameters['canReviseDoctypes'].split('|') \
                           if doctype.strip() != '']

    # The list of doctypes users are allowed to describe
    # (list of values separated by "|")
    can_describe_doctypes = [doctype.strip() for doctype \
                             in parameters['canDescribeDoctypes'].split('|') \
                             if doctype.strip() != '']

    # The list of doctypes users are allowed to comment
    # (list of values separated by "|")
    can_comment_doctypes = [doctype.strip() for doctype \
                            in parameters['canCommentDoctypes'].split('|') \
                            if doctype.strip() != '']

    # The list of doctypes for which users are allowed to decide
    # if they want to keep old files or not when revising
    # (list of values separated by "|")
    can_keep_doctypes = [doctype.strip() for doctype \
                         in parameters['canKeepDoctypes'].split('|') \
                         if doctype.strip() != '']

    # The list of doctypes users are allowed to rename
    # (list of values separated by "|")
    can_rename_doctypes = [doctype.strip() for doctype \
                           in parameters['canRenameDoctypes'].split('|') \
                           if doctype.strip() != '']

    # The mapping from doctype to default filename.
    # '|' is used to separate doctypes groups, and '=' to
    # separate doctype and file in curdir where the default name is. Eg:
    # main=main_filename|additional=additional_filename. etc
    default_doctypes_and_curdir_files = [doctype.strip().split("=") for doctype \
                                         in parameters['defaultFilenameDoctypes'].split('|') \
                                         if doctype.strip() != '']
    doctypes_to_default_filename = {}
    for doctype, curdir_file in default_doctypes_and_curdir_files:
        default_filename = read_file(curdir, curdir_file)
        if default_filename:
            doctypes_to_default_filename[doctype] = os.path.basename(default_filename)

    # The maximum number of files that can be uploaded for each doctype
    # Eg:
    # main=1|additional=3
    doctypes_and_max_files = [doctype.strip().split("=") for doctype \
                              in parameters['maxFilesDoctypes'].split('|') \
                              if doctype.strip() != '']
    max_files_for_doctype = {}
    for doctype, max_files in doctypes_and_max_files:
        if max_files.isdigit():
            max_files_for_doctype[doctype] = int(max_files)

    # The list of doctypes for which users are allowed to add new formats
    # (list of values separated by "|")
    can_add_format_to_doctypes = [doctype.strip() for doctype \
                               in parameters['canAddFormatDoctypes'].split('|') \
                               if doctype.strip() != '']

    # The list of access restrictions + description that users can
    # select when adding new files.  If there are no values, no
    # restriction is applied .  '|' is used to separate access
    # restrictions groups, and '=' to separate access restriction and
    # description. Eg: main=Main document|additional=Figure,
    # schema. etc
    access_restrictions_and_desc = [access.strip().split("=") for access \
                                    in parameters['restrictions'].split('|') \
                                    if access.strip() != '']
    access_restrictions_and_desc = [[access, _(desc)] for \
                                    (access, desc) in access_restrictions_and_desc]

    # The list of doctypes users are allowed to restrict
    # (list of values separated by "|")
    can_restrict_doctypes = [restriction.strip() for restriction \
                             in parameters['canRestrictDoctypes'].split('|') \
                             if restriction.strip() != '']

    # If we should create additional formats when applicable (1) or
    # not (0)
    try:
        createRelatedFormats_p = int(parameters['createRelatedFormats'])
    except ValueError, e:
        createRelatedFormats_p = False

    # If users can name the files they add
    # Value should be 0 (Cannot rename) or 1 (Can rename)
    try:
        can_name_new_files = int(parameters['canNameNewFiles'])
    except ValueError, e:
        can_name_new_files = False

    # The default behaviour wrt keeping previous files or not.
    # 0 = do not keep, 1 = keep
    try:
        keep_default = int(parameters['keepDefault'])
    except ValueError, e:
        keep_default = False

    # If we display links to files (1) or not (0)
    try:
        show_links = int(parameters['showLinks'])
    except ValueError, e:
        show_links = True

    file_label = parameters['fileLabel']
    if file_label == "":
        file_label = _('Choose a file')

    filename_label = parameters['filenameLabel']
    if filename_label == "":
        filename_label = _('Name')

    description_label = parameters['descriptionLabel']
    if description_label == "":
        description_label = _('Description')

    comment_label = parameters['commentLabel']
    if comment_label == "":
        comment_label = _('Comment')

    restriction_label = parameters['restrictionLabel']
    if restriction_label == "":
        restriction_label = _('Access')

    startDoc = parameters['startDoc']
    endDoc = parameters['endDoc']

    return (minsize, maxsize, doctypes_and_desc, doctypes,
            can_delete_doctypes, can_revise_doctypes,
            can_describe_doctypes, can_comment_doctypes,
            can_keep_doctypes, can_rename_doctypes,
            can_add_format_to_doctypes, createRelatedFormats_p,
            can_name_new_files, keep_default, show_links, file_label,
            filename_label, description_label, comment_label,
            startDoc, endDoc, access_restrictions_and_desc,
            can_restrict_doctypes, restriction_label,
            doctypes_to_default_filename, max_files_for_doctype)


def wash_form_parameters(form, abstract_bibdocs, can_keep_doctypes,
                         keep_default, can_describe_doctypes,
                         can_comment_doctypes, can_rename_doctypes,
                         can_name_new_files, can_restrict_doctypes,
                         doctypes_to_default_filename):
    """
    Washes the (user-defined) form parameters, taking into account the
    current state of the files and the admin defaults.

    Parameters:

        -form: the form of the function

        -abstract_bibdocs: a representation of the current state of
         the files, as returned by build_updated_file_list(..)

        -can_keep_doctypes *list* the list of doctypes for which we
         allow users to choose to keep or not the previous versions
         when revising.

        -keep_default *bool* the admin-defined default for when users
         cannot choose to keep or not previous version of a revised
         file

        -can_describe_doctypes: *list* the list of doctypes for which
         we let users define descriptions.

        -can_comment_doctypes: *list* the list of doctypes for which
         we let users define comments.

        -can_rename_doctypes: *list* the list of doctypes for which we
         let users rename bibdoc when revising.

        -can_name_new_files: *bool* if we let users choose a name when
         adding new files.

        -can_restrict_doctypes: *list* the list of doctypes for which
         we let users define access restrictions.

        -doctypes_to_default_filename: *dict* mapping from doctype to
         admin-chosen name for uploaded file.

    Returns:

        tuple (file_action, file_target, file_target_doctype,
        keep_previous_files, file_description, file_comment,
        file_rename, file_doctype, file_restriction) where:

        file_action: *str* the performed action ('add',
                      'revise','addFormat' or 'delete')

        file_target: *str* the bibdocname of the file on which the
                     action is performed (empty string when
                     file_action=='add')

        file_target_doctype: *str* the doctype of the file we will
                              work on.  Eg: ('Main',
                              'Additional'). Empty string with
                              file_action=='add'.

        keep_previous_files: *bool* if we keep the previous version of
                             the file or not. Only useful when
                             revising files.

        file_description: *str* the user-defined description to apply
                          to the file.  Empty string when no
                          description defined or when not applicable

        file_comment: *str* the user-defined comment to apply to the
                      file.  Empty string when no comment defined or
                      when not applicable

        file_rename: *str* the new name chosen by user for the
                     bibdoc. Empty string when not defined or when not
                     applicable.

        file_doctype: *str* the user-chosen doctype for the bibdoc
                      when file_action=='add', or the current doctype
                      of the file_target in other cases (doctype must
                      be preserved).

        file_restriction: *str* the user-selected restriction for the
                          file. Emptry string if not defined or when
                          not applicable
    """
    # Action performed ...
    if form.has_key("fileAction") and \
           form['fileAction'] in allowed_actions:
        file_action = form['fileAction'] # "add", "revise",
                                         # "addFormat" or "delete"
    else:
        file_action = ""

    # ... on file ...
    if form.has_key("fileTarget"):
        file_target = form['fileTarget'] # contains bibdocname
        # Also remember its doctype to make sure we do valid actions
        # on it
        corresponding_bibdoc = get_bibdoc_for_docname(file_target,
                                                      abstract_bibdocs)
        if corresponding_bibdoc is not None:
            file_target_doctype = corresponding_bibdoc['get_type']
        else:
            file_target_doctype = ""
    else:
        file_target = ""
        file_target_doctype = ""

    # ... with doctype?
    # Only useful when adding file: otherwise fileTarget doctype is
    # preserved
    file_doctype = file_target_doctype
    if form.has_key("fileDoctype") and \
           file_action == 'add':
        file_doctype = form['fileDoctype']

    # ... keeping previous version? ...
    if file_target_doctype != '' and \
           not form.has_key("keepPreviousFiles"):
        # no corresponding key. Two possibilities:
        if file_target_doctype in can_keep_doctypes or \
               '*' in can_keep_doctypes:
            # User decided no to keep
            keep_previous_files = 0
        else:
            # No choice for user. Use default admin has chosen
            keep_previous_files = keep_default
    else:
        # Checkbox seems to be checked ...
        if file_target_doctype in can_keep_doctypes or \
               '*' in can_keep_doctypes:
            # ...and this is allowed
            keep_previous_files = 1
        else:
            # ...but this is not allowed
            keep_previous_files = keep_default

    # ... and decription? ...
    #if file_action == 'add':
        #raise repr((file_target_doctype, can_describe_doctypes))
        #raise repr((form.has_key("description"), (file_target_doctype in can_describe_doctypes), '*' in can_describe_doctypes))
    if form.has_key("description") and \
        (((file_action == 'revise' and \
           (file_target_doctype in can_describe_doctypes)) or \
          (file_action == 'add' and \
           (file_doctype in can_describe_doctypes))) \
         or '*' in can_describe_doctypes):
        file_description = form['description']
    else:
        file_description = ''

    # ... and comment? ...
    if form.has_key("comment") and \
        (((file_action == 'revise' and \
           (file_target_doctype in can_comment_doctypes)) or \
          (file_action == 'add' and \
           (file_doctype in can_comment_doctypes))) \
         or '*' in can_comment_doctypes):
        file_comment = form['comment']
    else:
        file_comment = ''

    # ... and rename to ? ...
    if form.has_key("rename") and \
        ((file_action == "revise" and \
          ((file_target_doctype in can_rename_doctypes) or \
           '*'  in can_rename_doctypes)) or \
         (file_action == "add" and \
          can_name_new_files)):
        file_rename = form['rename'] # contains new bibdocname if applicable
    elif file_action == "add" and \
             doctypes_to_default_filename.has_key(file_doctype):
        # Admin-chosen name. Ensure it is unique by appending a suffix
        file_rename = doctypes_to_default_filename[file_doctype]
        file_counter = 2
        while get_bibdoc_for_docname(file_rename, abstract_bibdocs):
            if file_counter == 2:
                file_rename += '-2'
            else:
                file_rename = file_rename[:-len(str(file_counter))] + \
                              str(file_counter)
            file_counter += 1
    else:
        file_rename = ''

    # ... and file restriction ? ...
    file_restriction = ''
    if form.has_key("fileRestriction"):
        # We cannot clean that value as it could be a restriction
        # declared in another submission. We keep this value.
        file_restriction = form['fileRestriction']

    return (file_action, file_target, file_target_doctype,
            keep_previous_files, file_description, file_comment,
            file_rename, file_doctype, file_restriction)

def get_description_and_comment(bibdocfiles):
    """
    Returns the first description and comment as tuple (description,
    comment) found in the given list of bibdocfile

    description and/or comment can be None.

    This function is needed since we do consider that there is one
    comment/description per bibdoc, and not per bibdocfile as APIs
    state.

    @see: set_description_and_comment
    """
    description = None
    comment = None
    all_descriptions = [bibdocfile.get_description() for bibdocfile \
                        in bibdocfiles
                        if bibdocfile.get_description() not in ['', None]]
    if len(all_descriptions) > 0:
        description = all_descriptions[0]

    all_comments = [bibdocfile.get_comment() for bibdocfile \
                    in bibdocfiles
                    if bibdocfile.get_comment() not in ['', None]]
    if len(all_comments) > 0:
        comment = all_comments[0]

    return (description, comment)

def set_description_and_comment(abstract_bibdocfiles, description, comment):
    """
    Set the description and comment to the given (abstract)
    bibdocfiles.

    description and/or comment can be None.

    This function is needed since we do consider that there is one
    comment/description per bibdoc, and not per bibdocfile as APIs
    state.

    @see: get_description_and_comment
    """
    for bibdocfile in abstract_bibdocfiles:
        bibdocfile.description = description
        bibdocfile.comment = comment

def read_file(curdir, filename):
    """
    Reads a file in curdir.
    Returns None if does not exist, cannot be read, or if file is not
    really in curdir
    """
    try:
        file_path = os.path.abspath(os.path.join(curdir, filename))
        if not file_path.startswith(curdir):
            return None
        file_desc = file(file_path, 'r')
        content = file_desc.read()
        file_desc.close()
    except:
        content = None

    return content

## Javascript + HTML + CSS for the web interface

# The Javascript function embedded in the page to provide interaction
# with the revise panel
javascript = '''
<script type="text/javascript" language="javascript">
<!--

/* Record position of the last clicked link that triggered the display
 * of the revise panel
 */
var last_clicked_link = null;

function display_revise_panel(link, action, target, showDoctypes, showKeepPreviousVersions, showRename, showDescription, showComment, bibdocname, description, comment, showRestrictions, restriction){
        var balloon = document.getElementById("balloon");
        var doctype = document.getElementById("fileDoctypesRow");
        var warningFormats = document.getElementById("warningFormats");
        var keepPreviousVersions = document.getElementById("keepPreviousVersions");
        var renameBox = document.getElementById("renameBox");
        var descriptionBox = document.getElementById("descriptionBox");
        var commentBox = document.getElementById("commentBox");
        var restrictionBox = document.getElementById("restrictionBox");
        var apply_button = document.getElementById("applyChanges");
        last_clicked_link = link;
        var pos;

        /* Show/hide parts of the form */
        if (showDoctypes) {
            doctype.style.display = ''
        } else {
            doctype.style.display = 'none'
        }
        if (action == 'revise' && showKeepPreviousVersions == true){
            warningFormats.style.display = ''
        } else {
            warningFormats.style.display = 'none'
        }
        if ((action == 'revise' || action == 'add') && showRename == true){
            renameBox.style.display = ''
        } else {
            renameBox.style.display = 'none'
        }
        if ((action == 'revise' || action == 'add') && showDescription == true){
            descriptionBox.style.display = ''
        } else {
            descriptionBox.style.display = 'none'
        }
        if ((action == 'revise' || action == 'add') && showComment == true){
            commentBox.style.display = ''
        } else {
            commentBox.style.display = 'none'
        }
        if ((action == 'revise' || action == 'add') && showRestrictions == true){
            restrictionBox.style.display = ''
        } else {
            restrictionBox.style.display = 'none'
        }
        if (action == 'revise' && showKeepPreviousVersions == true) {
            keepPreviousVersions.style.display = ''
        } else {
            keepPreviousVersions.style.display = 'none'
        }
        if (action == 'add') {
            updateForm();
        }
        /* Reset values */
        document.forms[0].balloonReviseFileKeep.checked = true
        document.forms[0].rename.value = bibdocname;
        document.forms[0].comment.value = comment;
        document.forms[0].description.value = description;
        var fileRestrictionFound = false;
        for (var i=0; i < document.forms[0].fileRestriction.length; i++) {
            if (document.forms[0].fileRestriction[i].value == restriction) {
                    document.forms[0].fileRestriction.selectedIndex = i;
                    fileRestrictionFound = true;
                }
        }
        if (!fileRestrictionFound) {
            var restrictionItem = new Option(restriction, restriction);
            document.forms[0].fileRestriction.appendChild(restrictionItem);
            var lastIndex = document.forms[0].fileRestriction.length - 1;
            document.forms[0].fileRestriction.selectedIndex = lastIndex;
        }

        /* Display and move to correct position*/
        pos = findPosition(link)
        balloon.style.display = '';
        balloon.style.position="absolute";
        balloon.style.left = pos[0] + link.offsetWidth +"px";
        balloon.style.top = pos[1] - Math.round(balloon.offsetHeight/2) + 5 + "px";
        balloon.style.zIndex = 1001;
        balloon.style.display = '';

        /* Set the correct action and target file*/
        document.forms[0].fileAction.value = action;
        document.forms[0].fileTarget.value = target;

        /* Disable other controls */
        apply_button.disabled = true;
        /*gray_out(true);*/
}
function hide_revise_panel(){
        var balloon = document.getElementById("balloon");
        var apply_button = document.getElementById("applyChanges");
        balloon.style.display = 'none';
        apply_button.disabled = false;
        /*gray_out(false);*/
}

/* Intercept ESC key in order to close revise panel */
document.onkeyup = keycheck;
function keycheck(e){
        var KeyID = (window.event) ? event.keyCode : e.keyCode;
        if(KeyID==27){
            hide_revise_panel()
        }
}

function findPosition( oElement ) {
  /*Return the x,y position on page of the given object*/
  if( typeof( oElement.offsetParent ) != 'undefined' ) {
    for( var posX = 0, posY = 0; oElement; oElement = oElement.offsetParent ) {
      posX += oElement.offsetLeft;
      posY += oElement.offsetTop;
    }
    return [ posX, posY ];
  } else {
    return [ oElement.x, oElement.y ];
  }
}

function nextStep()
{
      if(confirm("You are about to submit the files and end the upload process."))
      {
          document.forms[0].step.value = 2;
          user_must_confirm_before_leaving_page = false;
          document.forms[0].submit();
      }
      return true;
}

function updateForm(doctype) {
    /* Update the revision panel to hide or not part of the interface
     * based on selected doctype
     *
     * Note: we use a small trick here to use the javascript 'in' operator, which
     * does not work for arrays, but for object => we transform our arrays into
     * objects literal
     */

    /* Get the elements we are going to affect */
    var renameBox = document.getElementById("renameBox");
    var descriptionBox = document.getElementById("descriptionBox");
    var commentBox = document.getElementById("commentBox");
    var restrictionBox = document.getElementById("restrictionBox");

    /* List of allowed doctypes for commenting, describing, etc. set
     * at instantiation time
     */
    var can_describe_doctypes = %(can_describe_doctypes)s
    var can_comment_doctypes = %(can_comment_doctypes)s
    var can_restrict_doctypes = %(can_restrict_doctypes)s

    if ((doctype in can_describe_doctypes) ||
        ('*' in can_describe_doctypes)){
        descriptionBox.style.display = ''
    } else {
        descriptionBox.style.display = 'none'
    }

    if ((doctype in can_comment_doctypes) ||
        ('*' in can_comment_doctypes)){
        commentBox.style.display = ''
    } else {
        commentBox.style.display = 'none'
    }

    if ((doctype in can_restrict_doctypes) ||
        ('*' in can_restrict_doctypes)){
        restrictionBox.style.display = ''
    } else {
        restrictionBox.style.display = 'none'
    }

    /* Move the revise panel accordingly */
    var balloon = document.getElementById("balloon");
    pos = findPosition(last_clicked_link)
    balloon.style.display = '';
    balloon.style.position="absolute";
    balloon.style.left = pos[0] + last_clicked_link.offsetWidth +"px";
    balloon.style.top = pos[1] - Math.round(balloon.offsetHeight/2) + 5 + "px";
    balloon.style.zIndex = 1001;
    balloon.style.display = '';
}

function gray_out(visible) {
    /* Gray out the screen so that user cannot click anywhere else.
       Based on <http://www.hunlock.com/blogs/Snippets:_Howto_Grey-Out_The_Screen>
     */
    var modalShield = document.getElementById('modalShield');
    if (!modalShield) {
        var tbody = document.getElementsByTagName("body")[0];
        var tnode = document.createElement('div');
        tnode.style.position = 'absolute';
        tnode.style.top = '0px';
        tnode.style.left = '0px';
        tnode.style.overflow = 'hidden';
        tnode.style.display = 'none';
        tnode.id = 'modalShield';
        tbody.appendChild(tnode);
        modalShield = document.getElementById('modalShield');
    }

    if (visible){
        // Calculate the page width and height
        var pageWidth = '100%%';
        var pageHeight = '100%%';
        //set the shader to cover the entire page and make it visible.
        modalShield.style.opacity = 0.7;
        modalShield.style.MozOpacity = 0.7;
        modalShield.style.filter = 'alpha(opacity=70)';
        modalShield.style.zIndex = 1000;
        modalShield.style.backgroundColor = '#000000';
        modalShield.style.width = pageWidth;
        modalShield.style.height = pageHeight;
        modalShield.style.display = 'block';
    } else {
        modalShield.style.display = 'none';
    }

}

-->
</script>
'''

# The CSS embedded in the page for the revise panel
css = '''
<style type="text/css">
<!--
#reviseControl{
overflow:auto;
width: 600px;
padding:1px;
}
.reviseControlBrowser{
padding:5px;
background-color:#fff;
border-collapse:collapse;
border-spacing: 0px;
border: 1px solid #999;
}
.reviseControlFileColumn {
padding-right:60px;
padding-left:5px;
text-align: left;
color:#00f;
}
.reviseControlActionColumn,
.reviseControlFormatColumn{
font-size:small;
}
.reviseControlActionColumn,
.reviseControlActionColumn a,
.reviseControlActionColumn a:link,
.reviseControlActionColumn a:hover
.reviseControlActionColumn a:visited{
font-size:small;
color: #060;
text-align:right;
}
.reviseControlFormatColumn,
.reviseControlFormatColumn a,
.reviseControlFormatColumn a:link,
.reviseControlFormatColumn a:hover
.reviseControlFormatColumn a:visited{
font-size:small;
color: #555;
text-align:left;
}
.optional{
color: #555;
font-size:0.9em;
font-weight:normal
}
.even{
background-color:#ecf3fe;
}
#balloon table{
border-collapse:collapse;
border-spacing: 0px;
}
#balloon table td.topleft{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_top_left_shadow.png) no-repeat bottom right;
}
#balloon table td.bottomleft{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_bottom_left_shadow.png) no-repeat top right;
}
#balloon table td.topright{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_top_right_shadow.png) no-repeat bottom left;
}
#balloon table td.bottomright{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_bottom_right_shadow.png) no-repeat top left;
}
#balloon table td.top{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_top_shadow.png) repeat-x bottom left;
}
#balloon table td.bottom{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_bottom_shadow.png) repeat-x top left;
}
#balloon table td.left{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_left_shadow.png) repeat-y top right;
text-align:right;
padding:0;
}
#balloon table td.right{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_right_shadow.png) repeat-y top left;
}
#balloon table td.arrowleft{
background: transparent url(%(CFG_SITE_URL)s/img/balloon/balloon_arrow_left_shadow.png) no-repeat bottom right;
width:24px;
height:27px;
}
#balloon table td.center{
background-color:#ffffea;
}
#balloon label{
font-size:small;
}
#balloonReviseFile{
width:220px;
text-align:left;
}
#warningFormats{
color:#432e11;
font-size:x-small;
text-align:center;
margin: 4px auto 4px auto;
}
#fileDoctype {
margin-bottom:3px;
}
#renameBox, #descriptionBox, #commentBox, #keepPreviousVersions{
margin-top:6px;
}
#description, #comment, #rename {
width:90%%;
}
-->
</style>
''' % {'CFG_SITE_URL': CFG_SITE_URL}

# The HTML markup of the revise panel
revise_balloon = '''
<div id="balloon" style="display:none;">
<input type="hidden" name="fileAction" value="" />
<input type="hidden" name="fileTarget" value="" />
  <table>
    <tr>
      <td class="topleft">&nbsp;</td>
      <td class="top">&nbsp;</td>
      <td class="topright">&nbsp;</td>
    </tr>
    <tr>
      <td class="left" vertical-align="center" width="24"><img alt=" " src="../img/balloon/balloon_arrow_left_shadow.png" /></td>
      <td class="center">
        <table id="balloonReviseFile">
          <tr>
            <td><label for="balloonReviseFileInput">%(file_label)s:</label><br/>
              %(doctypes)s
              <input type="file" name="myfile" id="balloonReviseFileInput" size="20" />
                          <!--  <input type="file" name="myfile" id="balloonReviseFileInput" size="20" onchange="var name=getElementById('rename');var filename=this.value.split('/').pop().split('.')[0];name.value=filename;"/> -->
              <div id="renameBox" style=""><label for="rename">%(filename_label)s:</label><br/><input type="text" name="rename" id="rename" size="20" autocomplete="off"/></div>
              <div id="descriptionBox" style=""><label for="description">%(description_label)s:</label><br/><input type="text" name="description" id="description" size="20" autocomplete="off"/></div>
              <div id="commentBox" style=""><label for="comment">%(comment_label)s:</label><br/><textarea name="comment" id="comment" rows="3"/></textarea></div>
              <div id="restrictionBox" style="display:none">%(restrictions)s</div>
              <div id="keepPreviousVersions" style="display:none"><input type="checkbox" id="balloonReviseFileKeep" name="keepPreviousFiles" checked="checked" /><label for="balloonReviseFileKeep">%(previous_versions_label)s</label>&nbsp;<small>[<a href="" onclick="javascript:alert('%(previous_versions_help)s');return false;">?</a>]</small></div>
              <p id="warningFormats" style="display:none"><img src="%(CFG_SITE_URL)s/img/balloon/warning.png" alt="Warning"/> %(revise_format_warning)s&nbsp;[<a href="" onclick="javascript:alert('%(revise_format_help)s');return false;">?</a>]</p>
              <div style="text-align:right;margin-top:5px"><input type="reset" value="%(cancel)s" onclick="javascript:hide_revise_panel();"/> <input type="submit" value="%(upload)s"/></div>
            </td>
          </tr>
        </table>
      </td>
      <td class="right">&nbsp;</td>
    </tr>
    <tr>
      <td class="bottomleft">&nbsp;</td>
      <td class="bottom">&nbsp;</td>
      <td class="bottomright">&nbsp;</td>
    </tr>
  </table>
</div>
'''
