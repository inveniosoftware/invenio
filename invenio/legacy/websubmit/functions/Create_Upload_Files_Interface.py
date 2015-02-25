# $Id: Revise_Files.py,v 1.37 2009/03/26 15:11:05 jerome Exp $

# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
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
"""WebSubmit function - Displays a generic interface to upload, delete
                        and revise files.

To be used on par with Move_Uploaded_Files_to_Storage function:
 - Create_Upload_Files_Interface records the actions performed by user.
 - Move_Uploaded_Files_to_Storage execute the recorded actions.


NOTE:
=====
 - Due to the way WebSubmit works, this function can only work when
   positionned at step 1 in WebSubmit admin, and
   Move_Uploaded_Files_to_Storage is at step 2

FIXME:
======

 - One issue: if we allow deletion or renaming, we might lose track of
   a bibdoc: someone adds X, renames X->Y, and adds again another file
   with name X: when executing actions, we will add the second X, and
   rename it to Y
   -> need to go back in previous action when renaming... or check
   that name has never been used..

"""

__revision__ = "$Id$"

import os

from invenio.config import \
     CFG_SITE_LANG
from invenio.base.i18n import gettext_set_language, wash_language
from invenio.legacy.bibdocfile.managedocfiles import create_file_upload_interface

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


      + deferRelatedFormatsCreation: if creation of related format is
                                     scheduled to be run later,
                                     offline (1, default) or
                                     immediately/online just after the
                                     user has uploaded the file
                                     (0). Setting immediate conversion
                                     enables workflows to process the
                                     created files in following
                                     functions, but "blocks" the user.

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
     max_files_for_doctype, deferRelatedFormatsCreation_p) = \
     wash_function_parameters(parameters, curdir, ln)


    try:
        recid = int(sysno)
    except:
        recid = None

    out += '<center>'
    out += startDoc
    out += create_file_upload_interface(recid,
                                        form=form,
                                        print_outside_form_tag=True,
                                        print_envelope=True,
                                        include_headers=True,
                                        ln=ln,
                                        minsize=minsize, maxsize=maxsize,
                                        doctypes_and_desc=doctypes_and_desc,
                                        can_delete_doctypes=can_delete_doctypes,
                                        can_revise_doctypes=can_revise_doctypes,
                                        can_describe_doctypes=can_describe_doctypes,
                                        can_comment_doctypes=can_comment_doctypes,
                                        can_keep_doctypes=can_keep_doctypes,
                                        can_rename_doctypes=can_rename_doctypes,
                                        can_add_format_to_doctypes=can_add_format_to_doctypes,
                                        create_related_formats=createRelatedFormats_p,
                                        can_name_new_files=can_name_new_files,
                                        keep_default=keep_default, show_links=show_links,
                                        file_label=file_label, filename_label=filename_label,
                                        description_label=description_label, comment_label=comment_label,
                                        restrictions_and_desc=restrictions_and_desc,
                                        can_restrict_doctypes=can_restrict_doctypes,
                                        restriction_label=restriction_label,
                                        doctypes_to_default_filename=doctypes_to_default_filename,
                                        max_files_for_doctype=max_files_for_doctype,
                                        sbm_indir=None, sbm_doctype=None, sbm_access=None,
                                        uid=None, sbm_curdir=curdir,
                                        defer_related_formats_creation=deferRelatedFormatsCreation_p)[1]
    out += endDoc
    out += '</center>'


    return out

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
        doctypes_to_default_filename, max_files_for_doctype,
        deferRelatedFormatsCreation_p)
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
        createRelatedFormats_p = bool(int(parameters['createRelatedFormats']))
    except ValueError as e:
        createRelatedFormats_p = False

    # If we should create additional formats right now (1) or
    # later (0)
    try:
        deferRelatedFormatsCreation_p = bool(int(parameters['deferRelatedFormatsCreation']))
    except ValueError, e:
        deferRelatedFormatsCreation_p = True

    # If users can name the files they add
    # Value should be 0 (Cannot rename) or 1 (Can rename)
    try:
        can_name_new_files = int(parameters['canNameNewFiles'])
    except ValueError as e:
        can_name_new_files = False

    # The default behaviour wrt keeping previous files or not.
    # 0 = do not keep, 1 = keep
    try:
        keep_default = int(parameters['keepDefault'])
    except ValueError as e:
        keep_default = False

    # If we display links to files (1) or not (0)
    try:
        show_links = int(parameters['showLinks'])
    except ValueError as e:
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

    prefix = read_file(curdir, startDoc)
    if prefix is None:
        prefix = ""

    suffix = read_file(curdir, endDoc)
    if suffix is None:
        suffix = ""

    return (minsize, maxsize, doctypes_and_desc, doctypes,
            can_delete_doctypes, can_revise_doctypes,
            can_describe_doctypes, can_comment_doctypes,
            can_keep_doctypes, can_rename_doctypes,
            can_add_format_to_doctypes, createRelatedFormats_p,
            can_name_new_files, keep_default, show_links, file_label,
            filename_label, description_label, comment_label,
            prefix, suffix, access_restrictions_and_desc,
            can_restrict_doctypes, restriction_label,
            doctypes_to_default_filename, max_files_for_doctype,
            deferRelatedFormatsCreation_p)

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

