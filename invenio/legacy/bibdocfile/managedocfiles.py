# $Id: Revise_Files.py,v 1.37 2009/03/26 15:11:05 jerome Exp $

# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2012, 2013, 2014 CERN.
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
"""
BibDocFile Upload File Interface utils
=====================================

Tools to help with creation of file management interfaces.

Contains the two main functions `create_file_upload_interface' and
`move_uploaded_files_to_storage', which must be run one after the
other:

 - create_file_upload_interface: Generates the HTML of an interface to
   revise files of a given record. The actions on the files are
   recorded in a working directory, but not applied to the record.

 - move_uploaded_files_to_storage: Applies/executes the modifications
   on files as recorded by the `create_file_upload_interface'
   function.

Theses functions are a complex interplay of HTML, Javascript and HTTP
requests. They are not meant to be used in any type of scenario, but
require to be used in extremely specific contexts (Currently in
WebSubmit Response Elements, WebSubmit functions and the BibDocFile
File Management interface).

NOTES:
======

 - Comments are not considered as a property of bibdocfiles, but
   bibdocs: this conflicts with the APIs

FIXME:
======

 - refactor into smaller components. Eg. form processing in
   create_file_upload_interface could be move outside the function.

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

DEPENDENCIES:
=============
  - jQuery Form plugin U{http://jquery.malsup.com/form/}
"""
from six.moves import cPickle
import os
import time
import cgi

from urllib import urlencode

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_SITE_URL, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_TMPSHAREDDIR, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_CERN_SITE, \
     CFG_SITE_RECORD
from invenio.base.i18n import gettext_set_language
from invenio.legacy.bibdocfile.cli import cli_fix_marc
from invenio.legacy.bibdocfile.api import BibRecDocs, \
     decompose_file, calculate_md5, BibDocFile, \
     InvenioBibDocFileError, BibDocMoreInfo
from invenio.legacy.websubmit.functions.Shared_Functions import \
     createRelatedFormats
from invenio.legacy.websubmit.icon_creator import \
     create_icon, InvenioWebSubmitIconCreatorError
from invenio.legacy.websubmit.file_converter import get_missing_formats
from invenio.ext.logging import register_exception
from invenio.legacy.dbquery import run_sql
from invenio.utils.url import create_html_mailto
from invenio.utils.html import escape_javascript_string
from invenio.legacy.bibsched.bibtask import task_low_level_submission, bibtask_allocate_sequenceid
CFG_ALLOWED_ACTIONS = ['revise', 'delete', 'add', 'addFormat']

params_id = 0

def create_file_upload_interface(recid,
                                 form=None,
                                 print_outside_form_tag=True,
                                 print_envelope=True,
                                 include_headers=False,
                                 ln=CFG_SITE_LANG,
                                 minsize='', maxsize='',
                                 doctypes_and_desc=None,
                                 can_delete_doctypes=None,
                                 can_revise_doctypes=None,
                                 can_describe_doctypes=None,
                                 can_comment_doctypes=None,
                                 can_keep_doctypes=None,
                                 can_rename_doctypes=None,
                                 can_add_format_to_doctypes=None,
                                 create_related_formats=True,
                                 can_name_new_files=True,
                                 keep_default=True, show_links=True,
                                 file_label=None, filename_label=None,
                                 description_label=None, comment_label=None,
                                 restrictions_and_desc=None,
                                 can_restrict_doctypes=None,
                                 restriction_label=None,
                                 doctypes_to_default_filename=None,
                                 max_files_for_doctype=None,
                                 sbm_indir=None, sbm_doctype=None, sbm_access=None,
                                 uid=None, sbm_curdir=None,
                                 display_hidden_files=False, protect_hidden_files=True,
                                 defer_related_formats_creation=True):
    """
    Returns the HTML for the file upload interface.

    @param recid: the id of the record to edit files
    @type recid: int or None

    @param form: the form sent by the user's browser in response to a
                 user action. This is used to read and record user's
                 actions.
    @param form: as returned by the interface handler.

    @param print_outside_form_tag: display encapsulating <form> tag or
                                   not
    @type print_outside_form_tag: boolean

    @param print_envelope: (internal parameter) if True, return the
                           encapsulating initial markup, otherwise
                           skip it.
    @type print_envelope: boolean

    @param include_headers: include javascript and css headers in the
                            body of the page. If you set this to
                            False, you must take care of including
                            these headers in your page header. Setting
                            this parameter to True is useful if you
                            cannot change the page header.
    @type include_headers: boolean

    @param ln: language
    @type ln: string

    @param minsize: the minimum size (in bytes) allowed for the
                    uploaded files. Files not big enough are
                    discarded.
    @type minsize: int

    @param maxsize: the maximum size (in bytes) allowed for the
                    uploaded files. Files too big are discarded.
    @type maxsize: int

    @param doctypes_and_desc: the list of doctypes (like 'Main' or
                              'Additional') and their description that users
                              can choose from when adding new files.
                                - When no value is provided, users cannot add new
                                  file (they can only revise/delete/add format)
                                - When a single value is given, it is used as
                                  default doctype for all new documents

                              Order is relevant
                              Eg:
                              [('main', 'Main document'), ('additional', 'Figure, schema. etc')]
    @type doctypes_and_desc: list(tuple(string, string))

    @param restrictions_and_desc: the list of restrictions (like 'Restricted' or
                         'No Restriction') and their description that
                         users can choose from when adding or revising
                         files. Restrictions can then be configured at
                         the level of WebAccess.
                           - When no value is provided, no restriction is
                             applied
                           - When a single value is given, it is used as
                             default resctriction for all documents.
                           - The first value of the list is used as default
                             restriction if the user if not given the
                             choice of the restriction. Order is relevant

                         Eg:
                         [('', 'No restriction'), ('restr', 'Restricted')]
    @type restrictions_and_desc: list(tuple(string, string))

    @param can_delete_doctypes: the list of doctypes that users are
                                allowed to delete.
                                Eg: ['main', 'additional']
                                Use ['*'] for "all doctypes"
    @type can_delete_doctypes: list(string)

    @param can_revise_doctypes: the list of doctypes that users are
                                allowed to revise
                                Eg: ['main', 'additional']
                                Use ['*'] for "all doctypes"
    @type can_revise_doctypes: list(string)

    @param can_describe_doctypes: the list of doctypes that users are
                                  allowed to describe
                                  Eg: ['main', 'additional']
                                  Use ['*'] for "all doctypes"
    @type can_describe_doctypes: list(string)

    @param can_comment_doctypes: the list of doctypes that users are
                                 allowed to comment
                                 Eg: ['main', 'additional']
                                 Use ['*'] for "all doctypes"
    @type can_comment_doctypes: list(string)

    @param can_keep_doctypes: the list of doctypes for which users can
                         choose to keep previous versions visible when
                         revising a file (i.e. 'Keep previous version'
                         checkbox). See also parameter 'keepDefault'.
                         Note that this parameter is ~ignored when
                         revising the attributes of a file (comment,
                         description) without uploading a new
                         file. See also parameter
                         Move_Uploaded_Files_to_Storage.force_file_revision
                         Eg: ['main', 'additional']
                         Use ['*'] for "all doctypes"
    @type can_keep_doctypes: list(string)


    @param can_add_format_to_doctypes: the list of doctypes for which users can
                              add new formats. If there is no value,
                              then no 'add format' link nor warning
                              about losing old formats are displayed.
                              Eg: ['main', 'additional']
                              Use ['*'] for "all doctypes"
    @type can_add_format_to_doctypes: list(string)

    @param can_restrict_doctypes: the list of doctypes for which users can
                             choose the access restrictions when adding or
                             revising a file. If no value is given:
                               - no restriction is applied if none is defined
                                 in the 'restrictions' parameter.
                               - else the *first* value of the 'restrictions'
                                 parameter is used as default restriction.

                             Eg: ['main', 'additional']
                             Use ['*'] for "all doctypes"
    @type can_restrict_doctypes : list(string)

    @param can_rename_doctypes: the list of doctypes that users are allowed
                           to rename (when revising)
                           Eg: ['main', 'additional']
                           Use ['*'] for "all doctypes"
    @type can_rename_doctypes: list(string)

    @param can_name_new_files: if user can choose the name of the files they
                         upload or not
    @type can_name_new_files: boolean

    @param doctypes_to_default_filename: Rename uploaded files to admin-chosen
                                 values. To rename to a value found in a file in curdir,
                                 use 'file:' prefix to specify the file to read from.
                                 Eg:
                                 {'main': 'file:RN', 'additional': 'foo'}

                                 If the same doctype is submitted
                                 several times, a"-%i" suffix is added
                                 to the name defined in the file.

                                 When using 'file:' prefix, the name
                                 is only resolved at the end of the
                                 submission, when attaching the file.

                                 The default filenames are overriden
                                 by user-chosen names if you allow
                                 'can_name_new_files' or
                                 'can_rename_doctypes', excepted if the
                                 name is prefixed with 'file:'.
    @type doctypes_to_default_filename: dict

    @param max_files_for_doctype: the maximum number of files that users can
                          upload for each doctype.
                          Eg: {'main': 1, 'additional': 2}

                          Do not specify the doctype here to have an
                          unlimited number of files for a given
                          doctype.
    @type max_files_for_doctype: dict

    @param create_related_formats: if uploaded files get converted to
                                     whatever format we can or not
    @type create_related_formats: boolean

    @param keep_default: the default behaviour for keeping or not previous
                     version of files when users cannot choose (no
                     value in can_keep_doctypes).
                     Note that this parameter is ignored when revising
                     the attributes of a file (comment, description)
                     without uploading a new file. See also parameter
                     Move_Uploaded_Files_to_Storage.force_file_revision
    @type keep_default: boolean

    @param show_links: if we display links to files when possible or
                         not
    @type show_links: boolean

    @param file_label: the label for the file field
    @type file_label: string

    @param filename_label: the label for the file name field
    @type filename_label: string

    @param description_label: the label for the description field
    @type description_label: string

    @param comment_label: the label for the comments field
    @type comment_label: string

    @param restriction_label: the label in front of the restrictions list
    @type restriction_label: string

    @param sbm_indir: the submission indir parameter, in case the
                      function is used in a WebSubmit submission
                      context.
                      This value will be used to retrieve where to
                      read the current state of the interface and
                      store uploaded files
    @type sbm_indir : string

    @param sbm_doctype: the submission doctype parameter, in case the
                        function is used in a WebSubmit submission
                        context.
                        This value will be used to retrieve where to
                        read the current state of the interface and
                        store uploaded files
    @type sbm_doctype: string

    @param sbm_access: the submission access parameter. Must be
                       specified in the context of WebSubmit
                       submission, as well when used in the
                       WebSubmit Admin file management interface.

                       This value will be used to retrieve where to
                       read the current state of the interface and
                       store uploaded files
    @type sbm_access: string

    @param sbm_curdir: the submission curdir parameter. Must be
                       specified in the context of WebSubmit
                       function Create_Upload_File_Interface.

                       This value will be used to retrieve where to
                       read the current state of the interface and
                       store uploaded files.
    @type sbm_curdir: string

    @param uid: the user id
    @type uid: int

    @param display_hidden_files: if bibdoc containing bibdocfiles
                                 flagged as 'HIDDEN' should be
                                 displayed or not.
    @type display_hidden_files: boolean

    @param protect_hidden_files: if bibdoc containing bibdocfiles
                                 flagged as 'HIDDEN' can be edited
                                 (revise, delete, add format) or not.
    @type protect_hidden_files: boolean

    @param defer_related_formats_creation: should the creation of
                                           "related formats" (See
                                           C{create_related_formats})
                                           be created at offline at a
                                           later stage (default) or
                                           immediately after upload
                                           (False)?
    @type defer_related_formats_creation: boolean

    @return Tuple (errorcode, html)
    """
    # Clean and set up a few parameters
    _ = gettext_set_language(ln)
    body = ''
    if not file_label:
        file_label = _('Choose a file')
    if not filename_label:
        filename_label = _('Name')
    if not description_label:
        description_label = _('Description')
    if not comment_label:
        comment_label = _('Comment')
    if not restriction_label:
        restriction_label = _('Access')
    if not doctypes_and_desc:
        doctypes_and_desc = []
    if not can_delete_doctypes:
        can_delete_doctypes = []
    if not can_revise_doctypes:
        can_revise_doctypes = []
    if not can_describe_doctypes:
        can_describe_doctypes = []
    if not can_comment_doctypes:
        can_comment_doctypes = []
    if not can_keep_doctypes:
        can_keep_doctypes = []
    if not can_rename_doctypes:
        can_rename_doctypes = []
    if not can_add_format_to_doctypes:
        can_add_format_to_doctypes = []
    if not restrictions_and_desc:
        restrictions_and_desc = []
    if not can_restrict_doctypes:
        can_restrict_doctypes = []
    if not doctypes_to_default_filename:
        doctypes_to_default_filename = {}
    if not max_files_for_doctype:
        max_files_for_doctype = {}

    doctypes = [doctype for (doctype, desc) in doctypes_and_desc]

    # Retrieve/build a working directory to save uploaded files and
    # states + configuration.
    working_dir = None
    if sbm_indir and sbm_doctype and sbm_access:
        # Write/read configuration to/from working_dir (WebSubmit mode).
        # Retrieve the interface configuration from the current
        # submission directory.
        working_dir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                              sbm_indir,
                              sbm_doctype,
                              sbm_access)
        try:
            assert(working_dir == os.path.abspath(working_dir))
        except AssertionError:
            register_exception(prefix='Cannot create file upload interface: ' + \
                               + 'missing parameter ',
                               alert_admin=True)
            return (1, "Unauthorized parameters")

        form_url_params = "?" + urlencode({'access': sbm_access,
                                           'indir': sbm_indir,
                                           'doctype': sbm_doctype})
    elif uid and sbm_access:
        # WebSubmit File Management (admin) interface mode.
        # Working directory is in CFG_TMPSHAREDDIR
        working_dir = os.path.join(CFG_TMPSHAREDDIR,
                              'websubmit_upload_interface_config_' + str(uid),
                              sbm_access)
        try:
            assert(working_dir == os.path.abspath(working_dir))
        except AssertionError:
            register_exception(prefix='Some user tried to access ' \
                               + working_dir + \
                               ' which is different than ' + \
                               os.path.abspath(working_dir),
                               alert_admin=True)
            return (1, "Unauthorized parameters")
        if not os.path.exists(working_dir):
            os.makedirs(working_dir)

        form_url_params = "?" + urlencode({'access': sbm_access})
    elif sbm_curdir:
        # WebSubmit Create_Upload_File_Interface.py function
        working_dir = sbm_curdir
        form_url_params = None
    else:
        register_exception(prefix='Some user tried to access ' \
                           + working_dir + \
                           ' which is different than ' + \
                           os.path.abspath(working_dir),
                           alert_admin=True)
        return (1, "Unauthorized parameters")

    # Save interface configuration, if this is the first time we come
    # here, or else load parameters
    try:
        parameters = _read_file_revision_interface_configuration_from_disk(working_dir)
        (minsize, maxsize, doctypes_and_desc, doctypes,
         can_delete_doctypes, can_revise_doctypes,
         can_describe_doctypes,
         can_comment_doctypes, can_keep_doctypes,
         can_rename_doctypes,
         can_add_format_to_doctypes, create_related_formats,
         can_name_new_files, keep_default, show_links,
         file_label, filename_label, description_label,
         comment_label, restrictions_and_desc,
         can_restrict_doctypes,
         restriction_label, doctypes_to_default_filename,
         max_files_for_doctype, print_outside_form_tag,
         display_hidden_files, protect_hidden_files,
         defer_related_formats_creation) = parameters
    except:
        # Initial display of the interface: save configuration to
        # disk for later reuse
        parameters = (minsize, maxsize, doctypes_and_desc, doctypes,
                      can_delete_doctypes, can_revise_doctypes,
                      can_describe_doctypes,
                      can_comment_doctypes, can_keep_doctypes,
                      can_rename_doctypes,
                      can_add_format_to_doctypes, create_related_formats,
                      can_name_new_files, keep_default, show_links,
                      file_label, filename_label, description_label,
                      comment_label, restrictions_and_desc,
                      can_restrict_doctypes,
                      restriction_label, doctypes_to_default_filename,
                      max_files_for_doctype, print_outside_form_tag,
                      display_hidden_files, protect_hidden_files,
                      defer_related_formats_creation)
        _write_file_revision_interface_configuration_to_disk(working_dir, parameters)

    # Get the existing bibdocs as well as the actions performed during
    # the former revise sessions of the user, to build an updated list
    # of documents. We will use it to check if last action performed
    # by user is allowed.
    performed_actions = read_actions_log(working_dir)
    if recid:
        bibrecdocs = BibRecDocs(recid)
        # Create the list of files based on current files and performed
        # actions
        bibdocs = bibrecdocs.list_bibdocs()
    else:
        bibdocs = []

    # "merge":
    abstract_bibdocs = build_updated_files_list(bibdocs,
                                                performed_actions,
                                                recid or -1,
                                                display_hidden_files)

    # If any, process form submitted by user
    if form:
        ## Get and clean parameters received from user
        (file_action, file_target, file_target_doctype,
         keep_previous_files, file_description, file_comment, file_rename,
         file_doctype, file_restriction, uploaded_filename, uploaded_filepath) = \
         wash_form_parameters(form, abstract_bibdocs, can_keep_doctypes,
         keep_default, can_describe_doctypes, can_comment_doctypes,
         can_rename_doctypes, can_name_new_files, can_restrict_doctypes,
         doctypes_to_default_filename, working_dir)

        if protect_hidden_files and \
               (file_action in ['revise', 'addFormat', 'delete']) and \
               is_hidden_for_docname(file_target, abstract_bibdocs):
            # Sanity check. We should not let editing
            file_action = ''
            body += '<script>alert("%s");</script>' % \
                    _("The file you want to edit is protected against modifications. Your action has not been applied")

        ## Check the last action performed by user, and log it if
        ## everything is ok
        if uploaded_filepath and \
               ((file_action == 'add' and (file_doctype in doctypes)) or \
                (file_action == 'revise' and \
                 ((file_target_doctype in can_revise_doctypes) or \
                  '*' in can_revise_doctypes)) or
                (file_action == 'addFormat' and \
                 ((file_target_doctype in can_add_format_to_doctypes) or \
                  '*' in can_add_format_to_doctypes))):
            # A file has been uploaded (user has revised or added a file,
            # or a format)
            dirname, filename, extension = decompose_file(uploaded_filepath)
            os.unlink("%s/myfile" % working_dir)
            if minsize.isdigit() and os.path.getsize(uploaded_filepath) < int(minsize):
                os.unlink(uploaded_filepath)
                body += '<script>alert("%s");</script>' % \
                    (_("The uploaded file is too small (<%(x_size)i o) and has therefore not been considered",
                        x_size=int(minsize))).replace('"', '\\"')
            elif maxsize.isdigit() and os.path.getsize(uploaded_filepath) > int(maxsize):
                os.unlink(uploaded_filepath)
                body += '<script>alert("%s");</script>' % \
                    (_("The uploaded file is too big (>%(x_size)i o) and has therefore not been considered",
                        x_size=int(maxsize))).replace('"', '\\"')
            elif len(filename) + len(extension) + 4 > 255:
                # Max filename = 256, including extension and version that
                # will be appended later by BibDoc
                os.unlink(uploaded_filepath)
                body += '<script>alert("%s");</script>' % \
                    _("The uploaded file name is too long and has therefore not been considered").replace('"', '\\"')

            elif file_action == 'add' and \
                     file_doctype in max_files_for_doctype and \
                     max_files_for_doctype[file_doctype] < \
                     (len([bibdoc for bibdoc in abstract_bibdocs \
                           if bibdoc['get_type'] == file_doctype]) + 1):
                # User has tried to upload more than allowed for this
                # doctype.  Should never happen, unless the user did some
                # nasty things
                os.unlink(uploaded_filepath)
                body += '<script>alert("%s");</script>' % \
                       _("You have already reached the maximum number of files for this type of document").replace('"', '\\"')

            else:
                # Prepare to move file to
                # working_dir/files/updated/doctype/bibdocname/
                folder_doctype = file_doctype or \
                                 bibrecdocs.get_bibdoc(file_target).get_type()
                folder_bibdocname = file_rename or file_target or filename
                new_uploaded_filepath = os.path.join(working_dir, 'files', 'updated',
                                            folder_doctype,
                                            folder_bibdocname, uploaded_filename)

                # First check that we do not conflict with an already
                # existing bibdoc name
                if file_action == "add" and \
                       ((filename in [bibdoc['get_docname'] for bibdoc \
                                      in abstract_bibdocs] and not file_rename) or \
                        file_rename in [bibdoc['get_docname'] for bibdoc \
                                        in abstract_bibdocs]):
                    # A file with that name already exist. Cancel action
                    # and tell user.
                    os.unlink(uploaded_filepath)
                    body += '<script>alert("%s");</script>' % \
                        (_("A file named %(x_name)s already exists. Please choose another name.",
                            x_name=(file_rename or filename))).replace('"', '\\"')

                elif file_action == "revise" and \
                        file_rename != file_target and \
                        file_rename in [bibdoc['get_docname'] for bibdoc \
                                         in abstract_bibdocs]:
                    # A file different from the one to revise already has
                    # the same bibdocname
                    os.unlink(uploaded_filepath)
                    body += '<script>alert("%s");</script>' % \
                        (_("A file named %(x_name)s already exists. Please choose another name.",
                            x_name=file_rename)).replace('"', '\\"')

                elif file_action == "addFormat" and \
                         (extension in \
                          get_extensions_for_docname(file_target,
                                                     abstract_bibdocs)):
                    # A file with that extension already exists. Cancel
                    # action and tell user.
                    os.unlink(uploaded_filepath)
                    body += '<script>alert("%s");</script>' % \
                            (_("A file with format '%(x_name)s' already exists. Please upload another format.",
                                x_name=extension)).replace('"', '\\"')
                elif '.' in file_rename  or '/' in file_rename or "\\" in file_rename or \
                         not os.path.abspath(new_uploaded_filepath).startswith(os.path.join(working_dir, 'files', 'updated')):
                    # We forbid usage of a few characters, for the good of
                    # everybody...
                    os.unlink(uploaded_filepath)
                    body += '<script>alert("%s");</script>' % \
                           _("You are not allowed to use dot '.', slash '/', or backslash '\\\\' in file names. Choose a different name and upload your file again. In particular, note that you should not include the extension in the renaming field.").replace('"', '\\"')
                else:
                    # No conflict with file name

                    # When revising, delete previously uploaded files for
                    # this entry, so that we do not execute the
                    # corresponding action
                    if file_action == "revise":
                        for path_to_delete in \
                                get_uploaded_files_for_docname(working_dir, file_target):
                            delete_file(working_dir, path_to_delete)

                    # Move uploaded file to working_dir/files/updated/doctype/bibdocname/
                    os.renames(uploaded_filepath, new_uploaded_filepath)

                    if file_action == "add":
                        # no need to check bibrecdocs.check_file_exists(new_uploaded_filepath, new_uploaded_format): was done before
                        # Log
                        if file_rename != '':
                            # at this point, bibdocname is specified
                            # name, no need to 'rename'
                            filename = file_rename
                        log_action(working_dir, file_action, filename,
                                   new_uploaded_filepath, file_rename,
                                   file_description, file_comment,
                                   file_doctype, keep_previous_files,
                                   file_restriction,
                                   create_related_formats and defer_related_formats_creation)

                        # Automatically create additional formats when
                        # possible AND wanted
                        additional_formats = []
                        if create_related_formats and not defer_related_formats_creation:
                            additional_formats = createRelatedFormats(new_uploaded_filepath,
                                                                      overwrite=False)

                            for additional_format in additional_formats:
                                # Log
                                log_action(working_dir, 'addFormat', filename,
                                           additional_format, file_rename,
                                           file_description, file_comment,
                                           file_doctype, True, file_restriction)

                if file_action == "revise" and file_target != "":
                    # Log
                    log_action(working_dir, file_action, file_target,
                               new_uploaded_filepath, file_rename,
                               file_description, file_comment,
                               file_target_doctype, keep_previous_files,
                               file_restriction, create_related_formats and defer_related_formats_creation)

                    # Automatically create additional formats when
                    # possible AND wanted
                    additional_formats = []
                    if create_related_formats and not defer_related_formats_creation:
                        additional_formats = createRelatedFormats(new_uploaded_filepath,
                                                                  overwrite=False)

                        for additional_format in additional_formats:
                            # Log
                            log_action(working_dir, 'addFormat',
                                       (file_rename or file_target),
                                       additional_format, file_rename,
                                       file_description, file_comment,
                                       file_target_doctype, True,
                                       file_restriction)

                if file_action == "addFormat" and file_target != "":
                    # We have already checked above that this format does
                    # not already exist.
                    # Log
                    log_action(working_dir, file_action, file_target,
                               new_uploaded_filepath, file_rename,
                               file_description, file_comment,
                               file_target_doctype, keep_previous_files,
                               file_restriction)

        elif file_action in ["add", "addFormat"]:
            # No file found, but action involved adding file: ask user to
            # select a file
            body += """<script>
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
                body += '<script>alert("%s");</script>' % \
                        (_("A file named %(x_name)s already exists. Please choose another name.",
                            x_name=file_rename)).replace('"', '\\"')
            elif file_rename != file_target and \
                     ('.' in file_rename or '/' in file_rename or "\\" in file_rename):
                    # We forbid usage of a few characters, for the good of
                    # everybody...
                body += '<script>alert("%s");</script>' % \
                        _("You are not allowed to use dot '.', slash '/', or backslash '\\\\' in file names. Choose a different name and upload your file again. In particular, note that you should not include the extension in the renaming field.").replace('"', '\\"')
            else:
                # Log
                log_action(working_dir, file_action, file_target,
                           "", file_rename,
                           file_description, file_comment,
                           file_target_doctype, keep_previous_files,
                           file_restriction)


        elif file_action == "delete" and file_target != "" and \
                 ((file_target_doctype in can_delete_doctypes) or \
                  '*' in can_delete_doctypes):
            # Delete previously uploaded files for this entry
            for path_to_delete in get_uploaded_files_for_docname(working_dir, file_target):
                delete_file(working_dir, path_to_delete)
            # Log
            log_action(working_dir, file_action, file_target, "", file_rename,
                       file_description, file_comment, "",
                       keep_previous_files, file_restriction)

    ## Display

    performed_actions = read_actions_log(working_dir)
    #performed_actions = []
    if recid:
        bibrecdocs = BibRecDocs(recid)
        # Create the list of files based on current files and performed
        # actions
        bibdocs = bibrecdocs.list_bibdocs()
    else:
        bibdocs = []

    abstract_bibdocs = build_updated_files_list(bibdocs, performed_actions,
                                                recid or -1, display_hidden_files)
    abstract_bibdocs.sort(lambda x, y: x['order'] - y['order'])

    # Display form and necessary CSS + Javscript
    #body += '<div>'
    #body += css
    js_can_describe_doctypes = repr({}.fromkeys(can_describe_doctypes, ''))
    js_can_comment_doctypes = repr({}.fromkeys(can_comment_doctypes, ''))
    js_can_restrict_doctypes = repr({}.fromkeys(can_restrict_doctypes, ''))

    # Prepare to display file revise panel "balloon".  Check if we
    # should display the list of doctypes or if it is not necessary (0
    # or 1 doctype). Also make sure that we do not exceed the maximum
    # number of files specified per doctype. The markup of the list of
    # doctypes is prepared here, and will be passed as parameter to
    # the display_revise_panel function
    cleaned_doctypes = [doctype for doctype in doctypes if
                        doctype not in max_files_for_doctype or
                        (max_files_for_doctype[doctype] > \
                        len([bibdoc for bibdoc in abstract_bibdocs \
                             if bibdoc['get_type'] == doctype]))]
    doctypes_list = ""
    if len(cleaned_doctypes) > 1:
        doctypes_list = '<select id="fileDoctype" name="fileDoctype" onchange="var idx=this.selectedIndex;var doctype=this.options[idx].value;updateForm(doctype,'+','.join([js_can_describe_doctypes, js_can_comment_doctypes, js_can_restrict_doctypes])+');">' + \
                        '\n'.join(['<option value="' + cgi.escape(doctype, True) + '">' + \
                                   cgi.escape(description) + '</option>' \
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
                        '\n'.join(['<option value="' + cgi.escape(restriction, True) + '">' + \
                                   cgi.escape(description) + '</option>' \
                                   for (restriction, description) \
                                   in restrictions_and_desc]) + \
                        '</select>'
        restrictions_list = '''<label for="restriction">%(restriction_label)s:</label>&nbsp;%(restrictions_list)s&nbsp;<small>[<a href="" onclick="alert('%(restriction_help)s');return false;">?</a>]</small>''' % \
                            {'restrictions_list': restrictions_list,
                             'restriction_label': restriction_label,
                             'restriction_help': _('Choose how you want to restrict access to this file.').replace("'", "\\'")}

    elif len(restrictions_and_desc) == 1:
        restrictions_list = '<select style="display:none" id="fileRestriction" name="fileRestriction"><option value="%(restriction_attr)s">%(restriction)s</option></select>' % {
            'restriction': cgi.escape(restrictions_and_desc[0][0]),
            'restriction_attr': cgi.escape(restrictions_and_desc[0][0], True)
        }
    else:
        restrictions_list = '<select style="display:none" id="fileRestriction" name="fileRestriction"></select>'

    # List the files
    body += '''
<div id="reviseControl">
    <table class="reviseControlBrowser">'''
    i = 0
    for bibdoc in abstract_bibdocs:
        if bibdoc['list_latest_files']:
            i += 1
            body += create_file_row(bibdoc, can_delete_doctypes,
                                    can_rename_doctypes,
                                    can_revise_doctypes,
                                    can_describe_doctypes,
                                    can_comment_doctypes,
                                    can_keep_doctypes,
                                    can_add_format_to_doctypes,
                                    doctypes_list,
                                    show_links,
                                    can_restrict_doctypes,
                                    even=not (i % 2),
                                    ln=ln,
                                    form_url_params=form_url_params,
                                    protect_hidden_files=protect_hidden_files)
    body += '</table>'
    if len(cleaned_doctypes) > 0:
        (revise_panel, javascript_prefix) = javascript_display_revise_panel(action='add', target='', show_doctypes=True, show_keep_previous_versions=False, show_rename=can_name_new_files, show_description=True, show_comment=True, bibdocname='', description='', comment='', show_restrictions=True, restriction=len(restrictions_and_desc) > 0 and restrictions_and_desc[0][0] or '', doctypes=doctypes_list)
        body += '''%(javascript_prefix)s<input type="button" onclick="%(display_revise_panel)s;updateForm('%(defaultSelectedDoctype)s', %(can_describe_doctypes)s, %(can_comment_doctypes)s, %(can_restrict_doctypes)s);return false;" value="%(add_new_file)s"/>''' % \
               {'display_revise_panel': revise_panel,
                'javascript_prefix': javascript_prefix,
                'defaultSelectedDoctype': escape_javascript_string(cleaned_doctypes[0], escape_quote_for_html=True),
                'add_new_file': _("Add new file"),
                'can_describe_doctypes':js_can_describe_doctypes,
                'can_comment_doctypes': repr({}.fromkeys(can_comment_doctypes, '')),
                'can_restrict_doctypes': repr({}.fromkeys(can_restrict_doctypes, ''))}

    body += '</div>'

    if print_envelope:
        # We should print this only if we display for the first time
        body = '<div id="uploadFileInterface">' + body + '</div>'
        if include_headers:
            body = get_upload_file_interface_javascript(form_url_params) + \
                   get_upload_file_interface_css() + \
                   body

        # Display markup of the revision panel. This one is also
        # printed only at the beginning, so that it does not need to
        # be returned with each response
        body += revise_balloon % \
           {'CFG_SITE_URL': CFG_SITE_URL,
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
            'upload': _('Upload'),
            'uploading_label': _('Uploading...'),
            'postprocess_label': _('Please wait...'),
            'submit_or_button': form_url_params and 'button' or 'submit'}
        body += '''
        <input type="hidden" name="recid" value="%(recid)i"/>
        <input type="hidden" name="ln" value="%(ln)s"/>
        ''' % \
        {'recid': recid or -1,
         'ln': ln}

    # End submission button
    if sbm_curdir:
        body += '''<br /><div style="font-size:small">
     <input type="button" class="adminbutton" name="Submit" id="applyChanges" value="%(apply_changes)s" onClick="nextStep();"></div>''' % \
     {'apply_changes': _("Apply changes")}

        # Display a link to support email in case users have problem
        # revising/adding files
        mailto_link = create_html_mailto(email=CFG_SITE_SUPPORT_EMAIL,
                                         subject=_("Need help revising or adding files to record %(recid)s") % \
                                         {'recid': recid or ''},
                                         body=_("""Dear Support,
I would need help to revise or add a file to record %(recid)s.
I have attached the new version to this email.
Best regards""") % {'recid': recid or ''})

        problem_revising = _('Having a problem revising a file? Send the revised version to %(mailto_link)s.') % {'mailto_link': mailto_link}
        if len(cleaned_doctypes) > 0:
            # We can add files, so change note
            problem_revising = _('Having a problem adding or revising a file? Send the new/revised version to %(mailto_link)s.') % {'mailto_link': mailto_link}

        body += '<br />'
        body += problem_revising

    if print_envelope and print_outside_form_tag:
        body = '<form method="post" action="/%s/managedocfilesasync" id="uploadFileForm">' % CFG_SITE_RECORD + body + '</form>'

    return (0, body)

def create_file_row(abstract_bibdoc, can_delete_doctypes,
                    can_rename_doctypes, can_revise_doctypes,
                    can_describe_doctypes, can_comment_doctypes,
                    can_keep_doctypes, can_add_format_to_doctypes,
                    doctypes_list, show_links, can_restrict_doctypes,
                    even=False, ln=CFG_SITE_LANG, form_url_params='',
                    protect_hidden_files=True):
    """
    Creates a row in the files list representing the given abstract_bibdoc

    @param abstract_bibdoc: list of "fake" BibDocs: it is a list of dictionaries
                             with keys 'list_latest_files' and 'get_docname' with
                             values corresponding to what you would expect to receive
                             when calling their counterpart function on a real BibDoc
                             object.

    @param can_delete_doctypes: list of doctypes for which we allow users to delete
                             documents

    @param can_revise_doctypes: the list of doctypes that users are
                             allowed to revise.

    @param can_describe_doctypes: the list of doctypes that users are
                             allowed to describe.

    @param can_comment_doctypes: the list of doctypes that users are
                             allowed to comment.

    @param can_keep_doctypes: the list of doctypes for which users can
                             choose to keep previous versions visible
                             when revising a file (i.e. 'Keep previous
                             version' checkbox).

    @param can_rename_doctypes: the list of doctypes that users are
                             allowed to rename (when revising)

    @param can_add_format_to_doctypes: the list of doctypes for which users can
                             add new formats

    @param show_links: if we display links to files

    @param even: if the row is even or odd on the list
    @type even: boolean

    @param ln: language
    @type ln: string

    @param form_url_params: the
    @type form_url_params: string

    @param protect_hidden_files: if bibdoc containing bibdocfiles
                                 flagged as 'HIDDEN' can be edited
                                 (revise, delete, add format) or not.
    @type protect_hidden_files: boolean

    @return: an HTML formatted "file" row
    @rtype: string
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
    hidden_p = abstract_bibdoc['hidden_p']

    # Main file row
    out = '<tr%s>' % (even and ' class="even"' or '')
    out += '<td class="reviseControlFileColumn"%s>' % (hidden_p and ' style="color:#99F"' or '')
    if not updated and show_links and not hidden_p:
        out += '<a target="_blank" href="' + main_bibdocfile.get_url() \
           + '">'
    out += cgi.escape(abstract_bibdoc['get_docname'])
    if hidden_p:
        out += ' <span style="font-size:small;font-style:italic;color:#888">(hidden)</span>'
    if not updated and show_links and not hidden_p:
        out += '</a>'
    if main_bibdocfile_description:
        out += ' (<em>' + cgi.escape(main_bibdocfile_description) + '</em>)'
    out += '</td>'

    (description, comment) = get_description_and_comment(abstract_bibdoc['list_latest_files'])
    restriction = abstract_bibdoc['get_status']

    # Revise link
    out += '<td class="reviseControlActionColumn">'
    if main_bibdocfile.get_type() in can_revise_doctypes or \
           '*' in can_revise_doctypes and not (hidden_p and protect_hidden_files):
        (revise_panel, javascript_prefix) = javascript_display_revise_panel(
            action='revise',
            target=abstract_bibdoc['get_docname'],
            show_doctypes=False,
            show_keep_previous_versions=(main_bibdocfile.get_type() in can_keep_doctypes) or '*' in can_keep_doctypes,
            show_rename=(main_bibdocfile.get_type() in can_rename_doctypes) or '*' in can_rename_doctypes,
            show_description=(main_bibdocfile.get_type() in can_describe_doctypes) or '*' in can_describe_doctypes,
            show_comment=(main_bibdocfile.get_type() in can_comment_doctypes) or '*' in can_comment_doctypes,
            bibdocname=abstract_bibdoc['get_docname'],
            description=description,
            comment=comment,
            show_restrictions=(main_bibdocfile.get_type() in can_restrict_doctypes) or '*' in can_restrict_doctypes,
            restriction=restriction,
            doctypes=doctypes_list)
        out += '%(javascript_prefix)s[<a href="" onclick="%(display_revise_panel)s;return false;">%(revise)s</a>]' % \
               {'display_revise_panel': revise_panel,
                'javascript_prefix': javascript_prefix,
                'revise': _("revise")
                }

    # Delete link
    if main_bibdocfile.get_type() in can_delete_doctypes or \
           '*' in can_delete_doctypes and not (hidden_p and protect_hidden_files):
        global params_id
        params_id += 1
        out += '''
        <script type="text/javascript">
        /*<![CDATA[*/
        var delete_panel_params_%(id)i = "%(bibdocname)s";
        /*]]>*/
        </script>
        [<a href="" onclick="return askDelete(delete_panel_params_%(id)i, '%(form_url_params)s')">%(delete)s</a>]
        ''' % {'bibdocname': escape_javascript_string(abstract_bibdoc['get_docname'], escape_for_html=False),
               'delete': _("delete"),
               'form_url_params': form_url_params or '',
               'id': params_id}
    out += '''</td>'''

    # Format row
    out += '''<tr%s>
    <td class="reviseControlFormatColumn"%s>
        <img src="%s/img/tree_branch.gif" alt="">
    ''' % (even and ' class="even"' or '', hidden_p and ' style="color:#999"' or '', CFG_SITE_URL)
    for bibdocfile in abstract_bibdoc['list_latest_files']:
        if not updated and show_links and not hidden_p:
            out += '<a target="_blank" href="' + bibdocfile.get_url() + '">'
        out += bibdocfile.get_format().strip('.')
        if not updated and show_links and not hidden_p:
            out += '</a>'
        out += ' '

    for format_to_be_created in abstract_bibdoc['formats_to_be_created']:
        if not hidden_p:
            out += '<span class="reviseControlFormatToBeCreated">' + format_to_be_created.strip('.') + '</span> '

    # Add format link
    out += '<td class="reviseControlActionColumn">'
    if main_bibdocfile.get_type() in can_add_format_to_doctypes or \
           '*' in can_add_format_to_doctypes and not (hidden_p and protect_hidden_files):
        (revise_panel, javascript_prefix) = javascript_display_revise_panel(
            action='addFormat',
            target=abstract_bibdoc['get_docname'],
            show_doctypes=False,
            show_keep_previous_versions=False,
            show_rename=False,
            show_description=False,
            show_comment=False,
            bibdocname='',
            description='',
            comment='',
            show_restrictions=False,
            restriction=restriction,
            doctypes=doctypes_list)
        out += '%(javascript_prefix)s[<a href="" onclick="%(display_revise_panel)s;return false;">%(add_format)s</a>]' % \
        {'display_revise_panel': revise_panel,
         'javascript_prefix': javascript_prefix,
         'add_format':_("add format")}

    out += '</td></tr>'

    return out

def build_updated_files_list(bibdocs, actions, recid, display_hidden_files=False):
    """
    Parses the list of BibDocs and builds an updated version to reflect
    the changes performed by the user of the file

    It is necessary to abstract the BibDocs since user wants to
    perform action on the files that are committed only at the end of
    the session.

    @param bibdocs: the original list of bibdocs on which we want to
                    build a new updated list

    @param actions: the list of actions performed by the user on the
                    files, and that we want to consider to build an
                    updated file list

    @param recid: the record ID to which the files belong

    @param display_hidden_files: if bibdoc containing bibdocfiles
                                 flagged as 'HIDDEN' should be
                                 displayed or not.
    @type display_hidden_files: boolean
    """
    abstract_bibdocs = {}
    create_related_formats_for_bibdocs = {}
    i = 0
    for bibdoc in bibdocs:
        hidden_p = True in [bibdocfile.hidden_p() for bibdocfile in bibdoc.list_latest_files()]
        if CFG_CERN_SITE:
            hidden_p = False # Temporary workaround. See Ticket #846
        if not display_hidden_files and hidden_p:
            # Do not consider hidden files
            continue
        i += 1
        status = bibdoc.get_status()
        if status == "DELETED":
            status = ''
        brd = BibRecDocs(recid)
        abstract_bibdocs[brd.get_docname(bibdoc.id)] = \
            {'list_latest_files': bibdoc.list_latest_files(),
             'get_docname': brd.get_docname(bibdoc.id),
             'updated': False,
             'get_type': bibdoc.get_type(),
             'get_status': status,
             'order': i,
             'hidden_p': hidden_p,
             'formats_to_be_created': []}

    for action, bibdoc_name, file_path, rename, description, \
            comment, doctype, keep_previous_versions, \
            file_restriction, create_related_formats in actions:
        dirname, filename, fileformat = decompose_file(file_path)
        i += 1
        if action in ["add", "revise"] and \
               os.path.exists(file_path):
            checksum = calculate_md5(file_path)
            order = i
            if action == "revise" and \
                   bibdoc_name in abstract_bibdocs:
                # Keep previous values
                order = abstract_bibdocs[bibdoc_name]['order']
                doctype = abstract_bibdocs[bibdoc_name]['get_type']
            if bibdoc_name.strip() == '' and rename.strip() == '':
                bibdoc_name = os.path.extsep.join(filename.split(os.path.extsep)[:-1])
            elif rename.strip() != '' and \
                     bibdoc_name in abstract_bibdocs:
                # Keep previous position
                del abstract_bibdocs[bibdoc_name]

            # First instantiate a fake BibDocMoreInfo object, without any side effect
            more_info = BibDocMoreInfo(1, cache_only = False, initial_data = {})
            if description is not None:
                more_info['descriptions'] = {1: {fileformat:description}}
            if comment is not None:
                more_info['comments'] = {1: {fileformat:comment}}
            abstract_bibdocs[(rename or bibdoc_name)] = \
                {'list_latest_files': [BibDocFile(file_path, [(int(recid), doctype,(rename or bibdoc_name))], version=1,
                                                  docformat=fileformat,
                                                  docid=-1,
                                                  status=file_restriction,
                                                  checksum=checksum,
                                                  more_info=more_info)],
                 'get_docname': rename or bibdoc_name,
                 'get_type': doctype,
                 'updated': True,
                 'get_status': file_restriction,
                 'order': order,
                 'hidden_p': False,
                 'formats_to_be_created': []}
            abstract_bibdocs[(rename or bibdoc_name)]['updated'] = True
            if create_related_formats:
                create_related_formats_for_bibdocs[(rename or bibdoc_name)] = True
        elif action == "revise" and not file_path:
            # revision of attributes of a file (description, name,
            # comment or restriction) but no new file.
            abstract_bibdocs[bibdoc_name]['get_docname'] = rename or bibdoc_name
            abstract_bibdocs[bibdoc_name]['get_status'] = file_restriction
            set_description_and_comment(abstract_bibdocs[bibdoc_name]['list_latest_files'],
                                        description, comment)
            abstract_bibdocs[bibdoc_name]['updated'] = True
        elif action == "delete":
            if bibdoc_name in abstract_bibdocs:
                del abstract_bibdocs[bibdoc_name]
        elif action == "addFormat" and \
               os.path.exists(file_path):
            checksum = calculate_md5(file_path)
            # Preserve type and status
            doctype = abstract_bibdocs[bibdoc_name]['get_type']
            file_restriction = abstract_bibdocs[bibdoc_name]['get_status']
            # First instantiate a fake BibDocMoreInfo object, without any side effect
            more_info = BibDocMoreInfo(1, cPickle.dumps({}))
            if description is not None:
                more_info['descriptions'] = {1: {fileformat:description}}
            if comment is not None:
                more_info['comments'] = {1: {fileformat:comment}}
            abstract_bibdocs[bibdoc_name]['list_latest_files'].append(\
                BibDocFile(file_path, [(int(recid), doctype, (rename or bibdoc_name))], version=1,
                           docformat=fileformat,
                           docid=-1, status='',
                           checksum=checksum, more_info=more_info))
            abstract_bibdocs[bibdoc_name]['updated'] = True

    # For each BibDoc for which we would like to create related
    # formats, do build the list of formats that should be created
    for docname in create_related_formats_for_bibdocs.keys():
        current_files_for_bibdoc = [bibdocfile.get_path() for bibdocfile in abstract_bibdocs[docname]['list_latest_files']]
        missing_formats = []
        for missing_formats_group in get_missing_formats(current_files_for_bibdoc).values():
            missing_formats.extend(missing_formats_group)
            abstract_bibdocs[docname]['formats_to_be_created'] = missing_formats

    return abstract_bibdocs.values()

def _read_file_revision_interface_configuration_from_disk(working_dir):
    """
    Read the configuration of the file revision interface from disk

    @param working_dir: the path to the working directory where we can find
                  the configuration file
    """
    input_file = open(os.path.join(working_dir, 'upload_interface.config'), 'rb')
    configuration = cPickle.load(input_file)
    input_file.close()
    return configuration

def _write_file_revision_interface_configuration_to_disk(working_dir, parameters):
    """
    Write the configuration of the file revision interface to disk

    @param working_dir: the path to the working directory where we should
                  write the configuration.

    @param parameters: the parameters to write to disk
    """
    output = open(os.path.join(working_dir, 'upload_interface.config'), 'wb')
    cPickle.dump(parameters, output)
    output.close()

def log_action(log_dir, action, bibdoc_name, file_path, rename,
               description, comment, doctype, keep_previous_versions,
               file_restriction, create_related_formats=False):
    """
    Logs a new action performed by user on a BibDoc file.

    The log file record one action per line, each column being split
    by '<--->' ('---' is escaped from values 'rename', 'description',
    'comment' and 'bibdoc_name'). The original request for this
    format was motivated by the need to have it easily readable by
    other scripts. Not sure it still makes sense nowadays...

    Newlines are also reserved, and are escaped from the input values
    (necessary for the 'comment' field, which is the only one allowing
    newlines from the browser)

    Each line starts with the time of the action in the following
    format: '2008-06-20 08:02:04 --> '

    @param log_dir: directory where to save the log (ie. working_dir)

    @param action: the performed action (one of 'revise', 'delete',
                   'add', 'addFormat')

    @param bibdoc_name: the name of the bibdoc on which the change is
                        applied

    @param file_path: the path to the file that is going to be
                      integrated as bibdoc, if any (should be""
                      in case of action="delete", or action="revise"
                      when revising only attributes of a file)

    @param rename: the name used to display the bibdoc, instead of the
                   filename (can be None for no renaming)

    @param description: a description associated with the file

    @param comment: a comment associated with the file

    @param doctype: the category in which the file is going to be
                    integrated

    @param keep_previous_versions: if the previous versions of this
                                    file are to be hidden (0) or not (1)

    @param file_restriction: the restriction applied to the
                              file. Empty string if no restriction

    @param create_related_formats: shall we created related formats
                                   for this action? Valid only if
                                   C{action} is 'add' or 'revise'.
    """
    log_file = os.path.join(log_dir, 'bibdocactions.log')
    try:
        file_desc = open(log_file, "a+")
        # We must escape new lines from comments in some way:
        comment = str(comment).replace('\\', '\\\\').replace('\r\n', '\\n\\r')
        msg = action                                 + '<--->' + \
              bibdoc_name.replace('---', '___')      + '<--->' + \
              file_path                              + '<--->' + \
              str(rename).replace('---', '___')      + '<--->' + \
              str(description).replace('---', '___') + '<--->' + \
              comment.replace('---', '___')          + '<--->' + \
              doctype                                + '<--->' + \
              str(int(keep_previous_versions))       + '<--->' + \
              file_restriction                       + '<--->' + \
              str(create_related_formats) + '\n'
        file_desc.write("%s --> %s" %(time.strftime("%Y-%m-%d %H:%M:%S"), msg))
        file_desc.close()
    except Exception as e:
        raise e

def read_actions_log(log_dir):
    """
    Reads the logs of action to be performed on files

    See log_action(..) for more information about the structure of the
    log file.

    @param log_dir: the path to the directory from which to read the
                    log file
    @type log_dir: string
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
                 file_restriction, create_related_formats) = action.rstrip('\n').split('<--->')
            except ValueError as e:
                # Malformed action log
                pass

            # Clean newline-escaped comment:
            comment = comment.replace('\\n\\r', '\r\n').replace('\\\\', '\\')

            # Perform some checking
            if action not in CFG_ALLOWED_ACTIONS:
                # Malformed action log
                pass

            try:
                keep_previous_versions = int(keep_previous_versions)
            except:
                # Malformed action log
                keep_previous_versions = 1
                pass

            create_related_formats = create_related_formats == 'True' and True or False

            actions.append((action, bibdoc_name, file_path, rename, \
                            description, comment, doctype,
                            keep_previous_versions, file_restriction,
                            create_related_formats))
        file_desc.close()
    except:
        pass

    return actions

def javascript_display_revise_panel(action, target, show_doctypes, show_keep_previous_versions, show_rename, show_description, show_comment, bibdocname, description, comment, show_restrictions, restriction, doctypes):
    """
    Returns a correctly encoded call to the javascript function to
    display the revision panel.
    """
    global params_id
    params_id += 1
    javascript_prefix = '''
    <script type="text/javascript">
    /*<![CDATA[*/
    var revise_panel_params_%(id)i = {"action": "%(action)s",
                                      "target": "%(target)s",
                                      "showDoctypes": %(showDoctypes)s,
                                      "showKeepPreviousVersions": %(showKeepPreviousVersions)s,
                                      "showRename": %(showRename)s,
                                      "showDescription": %(showDescription)s,
                                      "showComment": %(showComment)s,
                                      "bibdocname": "%(bibdocname)s",
                                      "description": "%(description)s",
                                      "comment": "%(comment)s",
                                      "showRestrictions": %(showRestrictions)s,
                                      "restriction": "%(restriction)s",
                                      "doctypes": "%(doctypes)s"}
     /*]]>*/
     </script>''' % {'id': params_id,
                   'action': action,
                   'showDoctypes': show_doctypes and 'true' or 'false',
                   'target': escape_javascript_string(target, escape_for_html=False),
                   'bibdocname': escape_javascript_string(bibdocname, escape_for_html=False),
                   'showRename': show_rename and 'true' or 'false',
                   'showKeepPreviousVersions': show_keep_previous_versions and 'true' or 'false',
                   'showComment': show_comment and 'true' or 'false',
                   'showDescription': show_description and 'true' or 'false',
                   'description': description and escape_javascript_string(description, escape_for_html=False) or '',
                   'comment': comment and escape_javascript_string(comment, escape_for_html=False) or '',
                   'showRestrictions': show_restrictions and 'true' or 'false',
                   'restriction': escape_javascript_string(restriction, escape_for_html=False),
                   'doctypes': escape_javascript_string(doctypes, escape_for_html=False)}
    return ('display_revise_panel(this, revise_panel_params_%(id)i)' % {'id': params_id},
            javascript_prefix)

def get_uploaded_files_for_docname(log_dir, docname):
    """
    Given a docname, returns the paths to the files uploaded for this
    revision session.

    @param log_dir: the path to the directory that should contain the
                    uploaded files.

    @param docname: the name of the bibdoc for which we want to
                    retrieve files.
    """
    return [file_path for action, bibdoc_name, file_path, rename, \
            description, comment, doctype, keep_previous_versions , \
            file_restriction, create_related_formats in read_actions_log(log_dir) \
            if bibdoc_name == docname and os.path.exists(file_path)]

def get_bibdoc_for_docname(docname, abstract_bibdocs):
    """
    Given a docname, returns the corresponding bibdoc from the
    'abstract' bibdocs.

    Return None if not found

    @param docname: the name of the bibdoc we want to retrieve

    @param abstract_bibdocs: the list of bibdocs from which we want to
                             retrieve the bibdoc
    """
    bibdocs = [bibdoc for bibdoc in abstract_bibdocs \
               if bibdoc['get_docname'] == docname]
    if len(bibdocs) > 0:
        return bibdocs[0]
    else:
        return None

def get_extensions_for_docname(docname, abstract_bibdocs):
    """
    Returns the list of extensions that exists for given bibdoc
    name in the given 'abstract' bibdocs.

    @param docname: the name of the bibdoc for wich we want to
                    retrieve the available extensions

    @param abstract_bibdocs: the list of bibdocs from which we want to
                             retrieve the bibdoc extensions
    """

    bibdocfiles = [bibdoc['list_latest_files'] for bibdoc \
                   in abstract_bibdocs \
                   if bibdoc['get_docname'] == docname]
    if len(bibdocfiles) > 0:
        # There should always be at most 1 matching docname, or 0 if
        # it is a new file
        return [bibdocfile.get_format() for bibdocfile \
                in bibdocfiles[0]]
    return []

def is_hidden_for_docname(docname, abstract_bibdocs):
    """
    Returns True if the bibdoc with given docname in abstract_bibdocs
    should be hidden. Also return True if docname cannot be found in
    abstract_bibdocs.

    @param docname: the name of the bibdoc for wich we want to
                    check if it is hidden or not

    @param abstract_bibdocs: the list of bibdocs from which we want to
                             look for the given docname
    """
    bibdocs = [bibdoc for bibdoc in abstract_bibdocs \
                   if bibdoc['get_docname'] == docname]
    if len(bibdocs) > 0:
        return bibdocs[0]['hidden_p']
    return True

def get_description_and_comment(bibdocfiles):
    """
    Returns the first description and comment as tuple (description,
    comment) found in the given list of bibdocfile

    description and/or comment can be None.

    This function is needed since we do consider that there is one
    comment/description per bibdoc, and not per bibdocfile as APIs
    state.

    @param bibdocfiles: the list of files of a given bibdoc for which
                        we want to extract the description and comment.
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

    @param abstract_bibdocfiles: the list of 'abstract' files of a
                        given bibdoc for which we want to set the
                        description and comment.

    @param description: the new description
    @param comment: the new comment
    """
    for bibdocfile in abstract_bibdocfiles:
        bibdocfile.description = description
        bibdocfile.comment = comment

def delete_file(working_dir, file_path):
    """
    Deletes a file at given path from the file.
    In fact, we just move it to working_dir/files/trash

    @param working_dir: the path to the working directory
    @param file_path: the path to the file to delete
    """
    if os.path.exists(file_path):
        filename = os.path.split(file_path)[1]
        move_to = os.path.join(working_dir, 'files', 'trash',
                               filename +'_' + str(time.time()))
        os.renames(file_path, move_to)

def wash_form_parameters(form, abstract_bibdocs, can_keep_doctypes,
                         keep_default, can_describe_doctypes,
                         can_comment_doctypes, can_rename_doctypes,
                         can_name_new_files, can_restrict_doctypes,
                         doctypes_to_default_filename, working_dir):
    """
    Washes the (user-defined) form parameters, taking into account the
    current state of the files and the admin defaults.

    @param form: the form of the function

    @param abstract_bibdocs: a representation of the current state of
                             the files, as returned by
                             build_updated_file_list(..)

    @param can_keep_doctypes: the list of doctypes for which we allow
                            users to choose to keep or not the
                            previous versions when revising.
    @type can_keep_doctypes: list

    @param keep_default: the admin-defined default for when users
                         cannot choose to keep or not previous version
                         of a revised file
    @type keep_default: boolean

    @param can_describe_doctypes: the list of doctypes for which we
                                  let users define descriptions.
    @type can_describe_doctypes: list

    @param can_comment_doctypes: the list of doctypes for which we let
                                 users define comments.
    @type can_comment_doctypes: list

    @param can_rename_doctypes: the list of doctypes for which we let
                                users rename bibdoc when revising.
    @type can_rename_doctypes: list

    @param can_name_new_files: if we let users choose a name when
                               adding new files.
    @type can_name_new_files: boolean

    @param can_restrict_doctypes: the list of doctypes for which we
                                  let users define access
                                  restrictions.
    @type can_restrict_doctypes: list

    @param doctypes_to_default_filename: mapping from doctype to
                                         admin-chosen name for
                                         uploaded file.
    @type doctypes_to_default_filename: dict

    @param working_dir: the path to the current working directory
    @type working_dir: string

    @return: tuple (file_action, file_target, file_target_doctype,
        keep_previous_files, file_description, file_comment,
        file_rename, file_doctype, file_restriction) where::

         file_action: *str* the performed action ('add',
                       'revise','addFormat' or 'delete')

         file_target: *str* the bibdocname of the file on which the
                      action is performed (empty string when
                      file_action=='add')

         file_target_doctype: *str* the doctype of the file we will
                               work on.  Eg: ('main',
                               'additional'). Empty string with
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
                           not applicable.

         file_name: *str* the original name of the uploaded file. None
                    if no file uploaded

         file_path: *str* the full path to the file

    @rtype: tuple(string, string, string, boolean, string, string,
                  string, string, string, string, string)
    """
    # Action performed ...
    if "fileAction" in form and \
           form['fileAction'] in CFG_ALLOWED_ACTIONS:
        file_action = str(form['fileAction']) # "add", "revise",
                                              # "addFormat" or "delete"
    else:
        file_action = ""

    # ... on file ...
    if "fileTarget" in form:
        file_target = str(form['fileTarget']) # contains bibdocname
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
    if "fileDoctype" in form and \
           file_action == 'add':
        file_doctype = str(form['fileDoctype'])

    # ... keeping previous version? ...
    if file_target_doctype != '' and \
           "keepPreviousFiles" not in form:
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
    if "description" in form and \
        (((file_action == 'revise' and \
           (file_target_doctype in can_describe_doctypes)) or \
          (file_action == 'add' and \
           (file_doctype in can_describe_doctypes))) \
         or '*' in can_describe_doctypes):
        file_description = str(form['description'])
    else:
        file_description = ''

    # ... and comment? ...
    if "comment" in form and \
        (((file_action == 'revise' and \
           (file_target_doctype in can_comment_doctypes)) or \
          (file_action == 'add' and \
           (file_doctype in can_comment_doctypes))) \
         or '*' in can_comment_doctypes):
        file_comment = str(form['comment'])
    else:
        file_comment = ''

    # ... and rename to ? ...
    if "rename" in form and \
        ((file_action == "revise" and \
          ((file_target_doctype in can_rename_doctypes) or \
           '*'  in can_rename_doctypes)) or \
         (file_action == "add" and \
          can_name_new_files)):
        file_rename = str(form['rename']) # contains new bibdocname if applicable
    elif file_action == "add" and \
             file_doctype in doctypes_to_default_filename:
        # Admin-chosen name.
        file_rename = doctypes_to_default_filename[file_doctype]
        if file_rename.lower().startswith('file:'):
            # We will define name at a later stage, i.e. when
            # submitting the file with bibdocfile. The name will be
            # chosen by reading content of a file in curdir
            file_rename = ''
        else:
            # Ensure name is unique, by appending a suffix
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
    if "fileRestriction" in form:
        # We cannot clean that value as it could be a restriction
        # declared in another submission. We keep this value.
        file_restriction = str(form['fileRestriction'])

    # ... and the file itself ? ...
    if 'myfile' in form and \
           hasattr(form['myfile'], "filename") and \
           form['myfile'].filename:
        dir_to_open = os.path.join(working_dir, 'files', 'myfile')
        if not os.path.exists(dir_to_open):
            try:
                os.makedirs(dir_to_open)
            except:
                pass
                # Shall we continue?
        if os.path.exists(dir_to_open):
            form_field = form['myfile']
            file_name = form_field.filename
            form_file = form_field.file
            ## Before saving the file to disk, wash the filename (in particular
            ## washing away UNIX and Windows (e.g. DFS) paths):
            file_name = os.path.basename(file_name.split('\\')[-1])
            file_name = file_name.strip()
            if file_name != "":
                # This may be dangerous if the file size is bigger than
                # the available memory
                file_path = os.path.join(dir_to_open, file_name)
                if not os.path.exists(file_path):
                    # If file already exists, it means that it was
                    # handled by WebSubmit
                    fp = file(file_path, "wb")
                    chunk = form_file.read(10240)
                    while chunk:
                        fp.write(chunk)
                        chunk = form_file.read(10240)
                    fp.close()
                    fp = open(os.path.join(working_dir, "lastuploadedfile"), "w")
                    fp.write(file_name)
                    fp.close()
                    fp = open(os.path.join(working_dir, 'myfile'), "w")
                    fp.write(file_name)
                    fp.close()
    else:
        file_name = None
        file_path = None

    return (file_action, file_target, file_target_doctype,
            keep_previous_files, file_description, file_comment,
            file_rename, file_doctype, file_restriction, file_name,
            file_path)


def move_uploaded_files_to_storage(working_dir, recid, icon_sizes,
                                   create_icon_doctypes,
                                   force_file_revision):
    """
    Apply the modifications on files (add/remove/revise etc.) made by
    users with one of the compatible interfaces (WebSubmit function
    `Create_Upload_Files_Interface.py'; WebSubmit element or WebSubmit
    File management interface using function
    `create_file_upload_interface').

    This function needs a "working directory" (working_dir) that contains a
    bibdocactions.log file with the list of actions to perform.

    @param working_dir: a path to the working directory containing actions to perform and files to attach
    @type working_dir: string
    @param recid: the recid to modify
    @type recid: int
    @param icon_sizes: the sizes of icons to create, as understood by
                      the websubmit icon creation tool
    @type icon_sizes: list(string)
    @param create_icon_doctypes: a list of doctype for which we want
                                 to create icons
    @type create_icon_doctypes: list(string)
    @param force_file_revision: when revising attributes of a file
                                (comment, description) without
                                uploading a new file, force a revision
                                of the current version (so that old
                                comment, description, etc. is kept
                                or not)
    @type force_file_revision: bool
    """
    # We need to remember of some actions that cannot be performed,
    # because files have been deleted or moved after a renaming.
    # Those pending action must be applied when revising the bibdoc
    # with a file that exists (that means that the bibdoc has not been
    # deleted nor renamed by a later action)
    pending_bibdocs = {}
    newly_added_bibdocs = [] # Does not consider new formats/revisions
    create_related_formats_for_bibdocs = {}
    create_icons_for_bibdocs = {}
    performed_actions = read_actions_log(working_dir)
    sequence_id = bibtask_allocate_sequenceid(working_dir)
    for action, bibdoc_name, file_path, rename, description, \
            comment, doctype, keep_previous_versions, \
            file_restriction, create_related_formats in performed_actions:

        # FIXME: get this out of the loop once changes to bibrecdocs
        # are immediately visible. For the moment, reload the
        # structure from scratch at each step
        bibrecdocs = BibRecDocs(recid)

        if action == 'add':
            new_bibdoc = \
                       add(file_path, bibdoc_name, rename, doctype, description,
                           comment, file_restriction, recid, working_dir, icon_sizes,
                           create_icon_doctypes, pending_bibdocs, bibrecdocs)
            if new_bibdoc:
                newly_added_bibdocs.append(new_bibdoc)

            if create_related_formats:
                # Schedule creation of related formats when possible.
                create_related_formats_for_bibdocs[rename or bibdoc_name] = True

            if doctype in create_icon_doctypes or '*' in create_icon_doctypes:
                # Schedule creation of icons when possible.
                create_icons_for_bibdocs[rename or bibdoc_name] = True

        elif action == 'addFormat':
            add_format(file_path, bibdoc_name, recid, doctype, working_dir,
                       icon_sizes, create_icon_doctypes,
                       pending_bibdocs, bibrecdocs)

            if doctype in create_icon_doctypes or '*' in create_icon_doctypes:
                # Schedule creation of icons when possible.
                create_icons_for_bibdocs[rename or bibdoc_name] = True

        elif action == 'revise':
            new_bibdoc = \
                       revise(file_path, bibdoc_name, rename, doctype,
                              description, comment, file_restriction, icon_sizes,
                              create_icon_doctypes, keep_previous_versions,
                              recid, working_dir, pending_bibdocs,
                              bibrecdocs, force_file_revision)
            if new_bibdoc:
                newly_added_bibdocs.append(new_bibdoc)



            if create_related_formats:
                # Schedule creation of related formats
                create_related_formats_for_bibdocs[rename or bibdoc_name] = True

            if doctype in create_icon_doctypes or '*' in create_icon_doctypes:
                # Schedule creation of icons when possible.
                create_icons_for_bibdocs[rename or bibdoc_name] = True

        elif action == 'delete':
            delete(bibdoc_name, recid, working_dir, pending_bibdocs,
                   bibrecdocs)

    # Finally rename bibdocs that should be named according to a file in
    # curdir (eg. naming according to report number). Only consider
    # file that have just been added.
    parameters = _read_file_revision_interface_configuration_from_disk(working_dir)
    new_names = []
    doctypes_to_default_filename = parameters[22]
    for bibdoc_to_rename in newly_added_bibdocs:
        bibdoc_to_rename_doctype = bibdoc_to_rename.doctype
        rename_to = doctypes_to_default_filename.get(bibdoc_to_rename_doctype, '')
        if rename_to.startswith('file:'):
            # This BibDoc must be renamed. Look for name in working dir
            name_at_filepath = os.path.join(working_dir, rename_to[5:])
            if os.path.exists(name_at_filepath) and \
                   os.path.abspath(name_at_filepath).startswith(working_dir):
                try:
                    rename = file(name_at_filepath).read()
                except:
                    register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                                       'could not read file %s in curdir to rename bibdoc' % \
                                       (name_at_filepath,),
                                       alert_admin=True)
                if rename:
                    file_counter = 2
                    new_filename = rename
                    while bibrecdocs.has_docname_p(new_filename) or (new_filename in new_names):
                        new_filename = rename + '_%i' % file_counter
                        file_counter += 1
                    if create_related_formats_for_bibdocs.has_key(bibdoc_to_rename.get_docname()):
                        create_related_formats_for_bibdocs[bibdoc_to_rename.get_docname()] = new_filename
                    if create_icons_for_bibdocs.has_key(bibdoc_to_rename.get_docname()):
                        create_icons_for_bibdocs[bibdoc_to_rename.get_docname()] = new_filename
                    bibdoc_to_rename.change_name(recid, new_filename)
                    new_names.append(new_filename) # keep track of name, or we have to reload bibrecdoc...
                    _do_log(working_dir, 'Renamed ' + str(bibdoc_to_rename.get_docname()))

    # Delete the HB BibFormat cache in the DB, so that the fulltext
    # links do not point to possible dead files
    run_sql("DELETE LOW_PRIORITY from bibfmt WHERE format='HB' AND id_bibrec=%s", (recid,))

    # Update the MARC
    cli_fix_marc(None, [recid], interactive=False)

    # Schedule related formats creation for selected BibDoc
    if create_related_formats_for_bibdocs:
        additional_params = []
        # Add task sequence ID
        additional_params.append('-I')
        additional_params.append(str(sequence_id))
        additional_params.append("-a")
        additional_params.append("docnames=%s" % '/'.join(create_related_formats_for_bibdocs.keys()))
        task_low_level_submission('bibtasklet', 'bibdocfile', '-N', 'createFormats', '-T', 'bst_create_related_formats', '-a', 'recid=%s' % recid, *additional_params)

    # Schedule icons creation for selected BibDoc
    additional_params = []
    # Add task sequence ID
    additional_params.append('-I')
    additional_params.append(str(sequence_id))
    additional_params.append("-a")
    additional_params.append("docnames=%s" % '/'.join(create_icons_for_bibdocs.keys()))
    additional_params.append("-a")
    additional_params.append("icon_sizes=%s" % ','.join(icon_sizes))
    additional_params.append('-a')
    additional_params.append("add_default_icon=1")
    additional_params.append('-a')
    additional_params.append("inherit_moreinfo=1")
    task_low_level_submission('bibtasklet', 'bibdocfile', '-N', 'createIcons', '-T', 'bst_create_icons', '-a', 'recid=%s' % recid, *additional_params)

def add(file_path, bibdoc_name, rename, doctype, description, comment,
        file_restriction, recid, working_dir, icon_sizes, create_icon_doctypes,
        pending_bibdocs, bibrecdocs):
    """
    Adds the file using bibdocfile CLI

    Return the bibdoc that has been newly added.
    """
    try:
        brd = BibRecDocs(recid)
        if os.path.exists(file_path):
            # Add file
            bibdoc = bibrecdocs.add_new_file(file_path,
                                             doctype,
                                             rename or bibdoc_name,
                                             never_fail=True)

            _do_log(working_dir, 'Added ' + brd.get_docname(bibdoc.id) + ': ' + \
                    file_path)

            # Add description
            if description:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_description(description,
                                           bibdocfile.get_format())
                    _do_log(working_dir, 'Described ' + \
                            brd.get_docname(bibdoc.id) + ': ' + description)

            # Add comment
            if comment:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_comment(comment,
                                       bibdocfile.get_format())
                    _do_log(working_dir, 'Commented ' + \
                            brd.get_docname(bibdoc.id) + ': ' + comment)

            # Set restriction
            bibdoc.set_status(file_restriction)
            _do_log(working_dir, 'Set restriction of ' + \
                    brd.get_docname(bibdoc.id) + ': ' + \
                    file_restriction or '(no restriction)')

            return bibdoc
        else:
            # File has been later renamed or deleted.
            # Remember to add it later if file is found (ie
            # it was renamed)
            pending_bibdocs[bibdoc_name] = (doctype, comment, description, [])

    except InvenioBibDocFileError as e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                           'tried to add already existing file %s ' \
                           'with name %s to record %i.' % \
                           (file_path, bibdoc_name, recid),
                           alert_admin=True)

def add_format(file_path, bibdoc_name, recid, doctype, working_dir,
               icon_sizes, create_icon_doctypes, pending_bibdocs,
               bibrecdocs):
    """
    Adds a new format to a bibdoc using bibdocfile CLI
    """
    try:
        brd = BibRecDocs(recid)
        if os.path.exists(file_path):

            # We must retrieve previous description and comment as
            # adding a file using the APIs reset these values
            prev_desc, prev_comment = None, None
            if bibrecdocs.has_docname_p(bibdoc_name):
                (prev_desc, prev_comment) = \
                            get_description_and_comment(bibrecdocs.get_bibdoc(bibdoc_name).list_latest_files())

            # Add file
            bibdoc = bibrecdocs.add_new_format(file_path,
                                               bibdoc_name,
                                               prev_desc,
                                               prev_comment)
            _do_log(working_dir, 'Added new format to ' + \
                    brd.get_docname(bibdoc.id) + ': ' + file_path)

        else:
            # File has been later renamed or deleted.
            # Remember to add it later if file is found
            if bibdoc_name in pending_bibdocs:
                pending_bibdocs[bibdoc_name][3].append(file_path)
            # else: we previously added a file by mistake. Do
            # not care, it will be deleted
    except InvenioBibDocFileError as e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                           'tried to add already existing format %s ' \
                           'named %s in record %i.' % \
                           (file_path, bibdoc_name, recid),
                               alert_admin=True)

def revise(file_path, bibdoc_name, rename, doctype, description,
           comment, file_restriction, icon_sizes, create_icon_doctypes,
           keep_previous_versions, recid, working_dir, pending_bibdocs,
           bibrecdocs, force_file_revision):
    """
    Revises the given bibdoc with a new file.

    Return the bibdoc that has been newly added. (later: if needed,
    return as tuple the bibdoc that has been revised, or deleted,
    etc.)
    """
    added_bibdoc = None
    try:
        if os.path.exists(file_path) or not file_path:
            brd = BibRecDocs(recid)
            # Perform pending actions
            if bibdoc_name in pending_bibdocs:
                # We have some pending actions to apply before
                # going further.
                if description == '':
                    # Last revision did not include a description.
                    # Use the one of the pending actions
                    description = pending_bibdocs[bibdoc_name][2]
                if comment == '':
                    # Last revision did not include a comment.
                    # Use the one of the pending actions
                    comment = pending_bibdocs[bibdoc_name][1]
                original_bibdoc_name = pending_bibdocs[bibdoc_name][0]
                if not bibrecdocs.has_docname_p(original_bibdoc_name) and file_path:
                    # the bibdoc did not originaly exist, so it
                    # must be added first
                    bibdoc = bibrecdocs.add_new_file(file_path,
                                                     pending_bibdocs[bibdoc_name][0],
                                                     bibdoc_name,
                                                     never_fail=True)
                    _do_log(working_dir, 'Added ' + brd.get_docname(bibdoc.id) + ': ' + \
                            file_path)
                    added_bibdoc = bibdoc

                    # Set restriction
                    bibdoc.set_status(file_restriction)
                    _do_log(working_dir, 'Set restriction of ' + \
                            bibrecdocs.get_docname(bibdoc.id) + ': ' + \
                            file_restriction or '(no restriction)')

                # We must retrieve previous description and comment as
                # revising a file using the APIs reset these values
                prev_desc, prev_comment = None, None
                if bibrecdocs.has_docname_p(bibdoc_name):
                    (prev_desc, prev_comment) = \
                                get_description_and_comment(bibrecdocs.get_bibdoc(bibdoc_name).list_latest_files())

                # Do we have additional formats?
                for additional_format in pending_bibdocs[bibdoc_name][3]:
                    if os.path.exists(additional_format):
                        bibdoc.add_file_new_format(additional_format,
                                                   description=bibdoc.get_description(),
                                                   comment=bibdoc.get_comment())
                        _do_log(working_dir, 'Added new format to' + \
                                brd.get_docname(bibdoc.id) + ': ' + file_path)

                # All pending modification have been applied,
                # so delete
                del pending_bibdocs[bibdoc_name]

            # We must retrieve previous description and comment as
            # revising a file using the APIs reset these values
            prev_desc, prev_comment = None, None
            if bibrecdocs.has_docname_p(bibdoc_name):
                (prev_desc, prev_comment) = \
                            get_description_and_comment(bibrecdocs.get_bibdoc(bibdoc_name).list_latest_files())

            if keep_previous_versions and file_path:
                # Standard procedure, keep previous version
                bibdoc = bibrecdocs.add_new_version(file_path,
                                                    bibdoc_name,
                                                    prev_desc,
                                                    prev_comment)
                _do_log(working_dir, 'Revised ' + brd.get_docname(bibdoc.id) + \
                        ' with : ' + file_path)

            elif file_path:
                # Soft-delete previous versions, and add new file
                # (we need to get the doctype before deleting)
                if bibrecdocs.has_docname_p(bibdoc_name):
                    # Delete only if bibdoc originally
                    # existed
                    bibrecdocs.delete_bibdoc(bibdoc_name)
                    _do_log(working_dir, 'Deleted ' + bibdoc_name)
                try:
                    bibdoc = bibrecdocs.add_new_file(file_path,
                                                     doctype,
                                                     bibdoc_name,
                                                     never_fail=True,
                                                     description=prev_desc,
                                                     comment=prev_comment)
                    _do_log(working_dir, 'Added ' + brd.get_docname(bibdoc.id) + ': ' + \
                            file_path)

                except InvenioBibDocFileError as e:
                    _do_log(working_dir, str(e))
                    register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                                       'tried to revise a file %s ' \
                                       'named %s in record %i.' % \
                                       (file_path, bibdoc_name, recid),
                                       alert_admin=True)
            else:
                # User just wanted to change attribute of the file,
                # not the file itself
                bibdoc = bibrecdocs.get_bibdoc(bibdoc_name)
                (prev_desc, prev_comment) = \
                            get_description_and_comment(bibdoc.list_latest_files())
                if prev_desc is None:
                    prev_desc = ""
                if prev_comment is None:
                    prev_comment = ""
                if force_file_revision and \
                       (description != prev_desc or comment != prev_comment):
                    # FIXME: If we are going to create a new version,
                    # then we should honour the keep_previous_versions
                    # parameter (soft-delete, then add bibdoc, etc)
                    # But it is a bit complex right now...

                    # Trick: we revert to current version, which
                    # creates a revision of the BibDoc
                    bibdoc.revert(bibdoc.get_latest_version())
                    bibdoc = bibrecdocs.get_bibdoc(bibdoc_name)

            # Rename
            if rename and rename != bibdoc_name:
                bibrecdocs.change_name(newname=rename, docid=bibdoc.id)
                _do_log(working_dir, 'renamed ' + bibdoc_name +' to '+ rename)

            # Description
            if description:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_description(description,
                                           bibdocfile.get_format())
                    _do_log(working_dir, 'Described ' + \
                            brd.get_docname(bibdoc.id) + ': ' + description)
            # Comment
            if comment:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_comment(comment,
                                       bibdocfile.get_format())
                    _do_log(working_dir, 'Commented ' + \
                            brd.get_docname(bibdoc.id) + ': ' + comment)

            # Set restriction
            bibdoc.set_status(file_restriction)
            _do_log(working_dir, 'Set restriction of ' + \
                    brd.get_docname(bibdoc.id) + ': ' + \
                    file_restriction or '(no restriction)')
        else:
            # File has been later renamed or deleted.
            # Remember it
            if rename and rename != bibdoc_name:
                pending_bibdocs[rename] = pending_bibdocs[bibdoc_name]

    except InvenioBibDocFileError as e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                           'tried to revise a file %s ' \
                           'named %s in record %i.' % \
                           (file_path, bibdoc_name, recid),
                           alert_admin=True)

    return added_bibdoc

def delete(bibdoc_name, recid, working_dir, pending_bibdocs,
           bibrecdocs):
    """
    Deletes the given bibdoc
    """
    try:
        if bibrecdocs.has_docname_p(bibdoc_name):
            bibrecdocs.delete_bibdoc(bibdoc_name)
            _do_log(working_dir, 'Deleted ' + bibdoc_name)

        if bibdoc_name in pending_bibdocs:
            del pending_bibdocs[bibdoc_name]

    except InvenioBibDocFileError as e:
        # Mmh most probably we deleted two files at the same
        # second. Sleep 1 second and retry...  This might go
        # away one bibdoc improves its way to delete files
        try:
            time.sleep(1)
            bibrecdocs.delete_bibdoc(bibdoc_name)
            _do_log(working_dir, 'Deleted ' + bibdoc_name)
            if bibdoc_name in pending_bibdocs:
                del pending_bibdocs[bibdoc_name]
        except InvenioBibDocFileError as e:
            _do_log(working_dir, str(e))
            _do_log(working_dir, repr(bibrecdocs.list_bibdocs()))
            register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                               'tried to delete a file' \
                               'named %s in record %i.' % \
                               (bibdoc_name, recid),
                               alert_admin=True)

def _do_log(log_dir, msg):
    """
    Log what we have done, in case something went wrong.
    Nice to compare with bibdocactions.log

    Should be removed when the development is over.

    @param log_dir: the path to the working directory
    @type log_dir: string

    @param msg: the message to log
    @type msg: string
    """
    log_file = os.path.join(log_dir, 'performed_actions.log')
    file_desc = open(log_file, "a+")
    file_desc.write("%s --> %s\n" %(time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    file_desc.close()


def _create_icon(file_path, icon_size, docformat='gif', verbosity=9):
    """
    Creates icon of given file.

    Returns path to the icon. If creation fails, return None, and
    register exception (send email to admin).


    @param file_path: full path to icon
    @type file_path: string

    @param icon_size: the scaling information to be used for the
                      creation of the new icon.
    @type icon_size: int

    @param verbosity: the verbosity level under which the program
                      is to run;
    @type verbosity: int
    """
    icon_path = None
    try:
        filename = os.path.splitext(os.path.basename(file_path))[0]
        (icon_dir, icon_name) = create_icon(
            {'input-file':file_path,
             'icon-name': "icon-%s" % filename,
             'multipage-icon': False,
             'multipage-icon-delay': 0,
             'icon-scale': icon_size,
             'icon-file-format': docformat,
             'verbosity': verbosity})
        icon_path = icon_dir + os.sep + icon_name
    except InvenioWebSubmitIconCreatorError as e:
        register_exception(prefix='Icon for file %s could not be created: %s' % \
                           (file_path, str(e)),
                           alert_admin=False)
    return icon_path


def get_upload_file_interface_javascript(form_url_params):
    """
    Returns the Javascript code necessary to run the upload file
    interface.
    """
    javascript = '''
<script type="text/javascript">
<!--
'''
    if form_url_params:
        javascript += '''
// prepare the form when the DOM is ready
$(document).ready(function() {
    var progress = $('.progress');
    var rotatingprogress = $('.rotatingprogress');
    var bar = $('.bar');
    var percent = $('.percent');
    var options = {
        target: '#uploadFileInterface', // target element(s) to be updated with server response
        uploadProgress: function(event, position, total, percentComplete) {
                                    update_progress(progress, bar, percent, percentComplete, rotatingprogress);},
        beforeSubmit: function(arr, $form, options) {
                                    show_upload_progress();
                                    return true;},
        success: showResponse, // post-submit callback
        url: '/%(CFG_SITE_RECORD)s/managedocfilesasync%(form_url_params)s' // override for form's 'action' attribute
    };

    // bind form using 'ajaxForm'
    var this_form = $('form:has(#balloonReviseFileInput)')
    $('#bibdocfilemanagedocfileuploadbutton').click(function() {
                this_form.bibdocfilemanagedocfileuploadbuttonpressed=true;
                this_form.ajaxSubmit(options);
    })

});

// post-submit callback
function showResponse(responseText, statusText)  {
    hide_upload_progress();
    hide_revise_panel();
}
    '''  % {
        'form_url_params': form_url_params,
        'CFG_SITE_RECORD': CFG_SITE_RECORD}

    javascript += '''
/* Record position of the last clicked link that triggered the display
 * of the revise panel
 */
var last_clicked_link = null;

function display_revise_panel(link, params){

        var action = params['action'];
        var target = params['target'];
        var showDoctypes = params['showDoctypes'];
        var showKeepPreviousVersions = params['showKeepPreviousVersions'];
        var showRename = params['showRename'];
        var showDescription = params['showDescription'];
        var showComment = params['showComment'];
        var bibdocname = params['bibdocname'];
        var description = params['description'];
        var comment = params['comment'];
        var showRestrictions = params['showRestrictions'];
        var restriction = params['restriction'];
        var doctypes = params['doctypes'];

        var balloon = document.getElementById("balloon");
        var file_input_block = document.getElementById("balloonReviseFileInputBlock");
        var doctype = document.getElementById("fileDoctypesRow");
        var warningFormats = document.getElementById("warningFormats");
        var keepPreviousVersions = document.getElementById("keepPreviousVersions");
        var renameBox = document.getElementById("renameBox");
        var descriptionBox = document.getElementById("descriptionBox");
        var commentBox = document.getElementById("commentBox");
        var restrictionBox = document.getElementById("restrictionBox");
        var apply_button = document.getElementById("applyChanges");
        var mainForm = getMainForm();
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
        file_input_block.innerHTML = file_input_block.innerHTML; // Trick to reset input field
        doctype.innerHTML = doctypes;
        mainForm.balloonReviseFileKeep.checked = true;
        mainForm.rename.value = bibdocname;
        mainForm.comment.value = comment;
        mainForm.description.value = description;
        var fileRestrictionFound = false;
        for (var i=0; i < mainForm.fileRestriction.length; i++) {
            if (mainForm.fileRestriction[i].value == restriction) {
                    mainForm.fileRestriction.selectedIndex = i;
                    fileRestrictionFound = true;
                }
        }
        if (!fileRestrictionFound) {
            var restrictionItem = new Option(restriction, restriction);
            mainForm.fileRestriction.appendChild(restrictionItem);
            var lastIndex = mainForm.fileRestriction.length - 1;
            mainForm.fileRestriction.selectedIndex = lastIndex;
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
        mainForm.fileAction.value = action;
        mainForm.fileTarget.value = target;

        /* Disable other controls */
        if (apply_button) {
            apply_button.disabled = true;
        }
        /*gray_out(true);*/
}
function hide_revise_panel(){
        var balloon = document.getElementById("balloon");
        var apply_button = document.getElementById("applyChanges");
        balloon.style.display = 'none';
        if (apply_button) {
            apply_button.disabled = false;
        }
        /*gray_out(false);*/
}


/* Intercept ESC key in order to close revise panel*/
document.onkeyup = keycheck;
function keycheck(e){
        var KeyID = (window.event) ? event.keyCode : e.keyCode;
        var upload_in_progress_p = $('.progress').is(":visible") || $('.rotatingprogress').is(":visible")
        if(KeyID==27){
            if (upload_in_progress_p) {
                hide_upload_progress();
            } else {
                hide_revise_panel();
            }
        }
}

/* Update progress bar, show if necessary (and then hide rotating progress indicator) */
function update_progress(progress, bar, percent, percentComplete, rotatingprogress){
    if (rotatingprogress.is(":visible")) {
        $('.rotatingprogress').hide();
        $('.progress').show();
    }
    var percentVal = percentComplete + '%%';
    bar.width(percentVal)
    percent.html(percentVal);

    if (percentComplete == '100') {
        // There might be some lengthy post-processing to do.
        show_upload_progress(post_process_label=true);
    }
}

/* Hide upload/cancel button, show rotating progress indicator */
function show_upload_progress(post_process_label_p) {
    if (!post_process_label_p) { post_process_label_p = false;}

    if (post_process_label_p) {
        /* Show post-process label */
        $('.progress').hide();
        $('.rotatingprogress').hide();
        $('.rotatingpostprocess').show();
    } else {
        /* Show uploading label */
        $('#canceluploadbuttongroup').hide();
        $('.rotatingprogress').show();
    }
}
/* show upload/cancel button, hide any progress indicator */
function hide_upload_progress() {
    $('.progress').hide();
    $('.rotatingprogress').hide();
    $('.rotatingpostprocess').hide();
    $('#canceluploadbuttongroup').show();
    $('.percent').html('0%%');
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

function getMainForm()
{
    return $('form:has(#balloonReviseFileInput)')[0];
}

function nextStep()
{
      if(confirm("You are about to submit the files and end the upload process."))
      {
          var mainForm = getMainForm();
          mainForm.step.value = 2;
          user_must_confirm_before_leaving_page = false;
          mainForm.submit();
      }
      return true;
}

function updateForm(doctype, can_describe_doctypes, can_comment_doctypes, can_restrict_doctypes) {
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

    if (!can_describe_doctypes) {var can_describe_doctypes = [];}
    if (!can_comment_doctypes)  {var can_comment_doctypes = [];}
    if (!can_restrict_doctypes) {var can_restrict_doctypes = [];}

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

function askDelete(bibdocname, form_url_params){
    /*
    Ask user if she wants to delete file
    */
    if (confirm('Are you sure you want to delete '+bibdocname+'?'))
    {
        if (form_url_params) {
            var mainForm = getMainForm();
            mainForm.fileTarget.value = bibdocname;
            mainForm.fileAction.value='delete';
            user_must_confirm_before_leaving_page = false;
            var options = {
                target: '#uploadFileInterface',
                success: showResponse,
                url: '/%(CFG_SITE_RECORD)s/managedocfilesasync' + form_url_params
            };
            $(mainForm).ajaxSubmit(options);
        } else {
            /*WebSubmit function*/
            document.forms[0].fileTarget.value = bibdocname;
            document.forms[0].fileAction.value='delete';
            user_must_confirm_before_leaving_page = false;
            document.forms[0].submit();
        }
    }
    return false;
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
''' % {'CFG_SITE_RECORD': CFG_SITE_RECORD}
    return javascript

def get_upload_file_interface_css():
    """
    Returns the CSS to embed in the page for the upload file interface.
    """
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
.reviseControlFormatToBeCreated{
font-style:italic;
color: #aaa;
}
.optional{
color: #555;
font-size:0.9em;
font-weight:normal
}
.even{
background-color:#ecf3fe;
}
/*
.buttonLikeLink, .buttonLikeLink:visited, .buttonLikeLink:hover{
background-color:#fff;
border:2px outset #555;
color:#000;
padding: 2px 5px;
display:inline-block;
margin:2px;
text-decoration:none;
font-size:small;
cursor: default
}
*/

#balloon table{
border-collapse:collapse;
border-spacing: 0px;
}
#balloon table td.topleft{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_top_left_shadow.png) no-repeat bottom right;
}
#balloon table td.bottomleft{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_bottom_left_shadow.png) no-repeat top right;
}
#balloon table td.topright{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_top_right_shadow.png) no-repeat bottom left;
}
#balloon table td.bottomright{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_bottom_right_shadow.png) no-repeat top left;
}
#balloon table td.top{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_top_shadow.png) repeat-x bottom left;
}
#balloon table td.bottom{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_bottom_shadow.png) repeat-x top left;
}
#balloon table td.left{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_left_shadow.png) repeat-y top right;
text-align:right;
padding:0;
}
#balloon table td.right{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_right_shadow.png) repeat-y top left;
}
#balloon table td.arrowleft{
background: transparent url(%(CFG_SITE_URL)s/img/balloon_arrow_left_shadow.png) no-repeat bottom right;
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
.rotatingprogress, .rotatingpostprocess {
position:relative;
float:right;
padding: 1px;
font-style:italic;
font-size:small;
margin-right: 5px;
display:none;
}

.progress {
position:relative;
width:100%%;
float:left;
border: 1px solid #ddd;
padding: 1px;
border-radius: 3px;
display:none;
}
.bar {
background-color: #dd9700;
width:0%%; height:20px;
border-radius: 3px; }
.percent {
position:absolute;
display:inline-block;
top:3px;
left:45%%;
font-size:small;
color: #514100;
}
-->
</style>
''' % {'CFG_SITE_URL': CFG_SITE_URL}
    return css

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
      <td class="left" vertical-align="center" width="24"><img alt=" " src="../img/balloon_arrow_left_shadow.png" /></td>
      <td class="center">
        <table id="balloonReviseFile">
          <tr>
            <td><label for="balloonReviseFileInput">%(file_label)s:</label><br/>
              <div style="display:none" id="fileDoctypesRow"></div>
              <div id="balloonReviseFileInputBlock"><input type="file" name="myfile" id="balloonReviseFileInput" size="20" /></div>
                          <!--  <input type="file" name="myfile" id="balloonReviseFileInput" size="20" onchange="var name=getElementById('rename');var filename=this.value.split('/').pop().split('.')[0];name.value=filename;"/> -->
              <div id="renameBox" style=""><label for="rename">%(filename_label)s:</label><br/><input type="text" name="rename" id="rename" size="20" autocomplete="off"/></div>
              <div id="descriptionBox" style=""><label for="description">%(description_label)s:</label><br/><input type="text" name="description" id="description" size="20" autocomplete="off"/></div>
              <div id="commentBox" style=""><label for="comment">%(comment_label)s:</label><br/><textarea name="comment" id="comment" rows="3"/></textarea></div>
              <div id="restrictionBox" style="display:none;white-space:nowrap;">%(restrictions)s</div>
              <div id="keepPreviousVersions" style="display:none"><input type="checkbox" id="balloonReviseFileKeep" name="keepPreviousFiles" checked="checked" /><label for="balloonReviseFileKeep">%(previous_versions_label)s</label>&nbsp;<small>[<a href="" onclick="alert('%(previous_versions_help)s');return false;">?</a>]</small></div>
              <p id="warningFormats" style="display:none"><img src="%(CFG_SITE_URL)s/img/warning.png" alt="Warning"/> %(revise_format_warning)s&nbsp;[<a href="" onclick="alert('%(revise_format_help)s');return false;">?</a>]</p>
              <div class="progress"><div class="bar"></div ><div class="percent">0%%</div ></div>
              <div class="rotatingprogress"><img src="/img/ui-anim_basic_16x16.gif" /> %(uploading_label)s</div><div class="rotatingpostprocess"><img src="/img/ui-anim_basic_16x16.gif" /> %(postprocess_label)s</div><div id="canceluploadbuttongroup" style="text-align:right;margin-top:5px"><input type="button" value="%(cancel)s" onclick="javascript:hide_revise_panel();"/> <input type="%(submit_or_button)s" id="bibdocfilemanagedocfileuploadbutton" onclick="show_upload_progress()" value="%(upload)s"/></div>
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
