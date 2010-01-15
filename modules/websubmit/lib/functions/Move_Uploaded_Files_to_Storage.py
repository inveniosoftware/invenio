## $Id: Move_Revised_Files_to_Storage.py,v 1.20 2009/03/26 13:48:42 jerome Exp $

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
"""WebSubmit function - Archives files uploaded with the upload file
                        interface.

To be used on par with Create_Upload_Files_Interface.py function:
 - Create_Upload_Files_Interface records the actions performed by user.
 - Move_Uploaded_Files_to_Storage execute the recorded actions.

NOTE:

 - comments are not considered as a property of bibdocfiles, but
   bibdocs: this conflicts with the APIs

 - Due to the way WebSubmit works, this function can only work when
   positionned at step 2 in WebSubmit admin, and
   Create_Upload_Files_Interface is at step 1

FIXME:

 - update with new bibdocfile CLI when it is ready

 - when revising a bibdoc without uploading a new file (eg. revision
   of comment, description), keep_previous_versions is ignored.
"""

__revision__ = "$Id$"

import time
import os

from invenio.websubmit_functions import Create_Upload_Files_Interface
from invenio.bibdocfile import \
     InvenioWebSubmitFileError, \
     BibRecDocs
from invenio.errorlib import register_exception
from invenio.websubmit_icon_creator import \
     create_icon, InvenioWebSubmitIconCreatorError
from invenio.config import CFG_BINDIR
from invenio.dbquery import run_sql
from invenio.shellutils import run_shell_command

def Move_Uploaded_Files_to_Storage(parameters, curdir, form, user_info=None):
    """
    The function moves files uploaded using the
    Create_Upload_Files_Interface.py function.

    It reads the action previously performed by the user on the files
    and calls the corresponding functions of bibdocfile.

    @param parameters:(dictionary) - must contain:
      + iconsize: size of the icon to create (when applicable)

      + createIconDoctypes: the list of doctypes for which an icon
                            should be created.
                            Eg:
                                Figure|Graph
                              ('|' separated values)
                              Use '*' for all doctypes

      + forceFileRevision: when revising attributes of a file
                           (comment, description) without
                           uploading a new file, force a revision of
                           the current version (so that old comment,
                           description, etc. is kept) (1) or not (0).
    """
    global sysno
    recid = int(sysno)

    iconsize = parameters.get('iconsize')
    create_icon_doctypes = parameters.get('createIconDoctypes')
    forceFileRevision = parameters.get('forceFileRevision')

    # We need to remember of some actions that cannot be performed,
    # because files have been deleted or moved after a renaming.
    # Those pending action must be applied when revising the bibdoc
    # with a file that exists (that means that the bibdoc has not been
    # deleted nor renamed by a later action)
    pending_bibdocs = {}

    performed_actions = Create_Upload_Files_Interface.read_actions_log(curdir)
    for action, bibdoc_name, file_path, rename, description, \
            comment, doctype, keep_previous_versions, \
            file_restriction in performed_actions:

        # FIXME: get this out of the loop once changes to bibrecdocs
        # are immediately visible. For the moment, reload the
        # structure from scratch at each step
        bibrecdocs = BibRecDocs(recid)

        if action == 'add':
            add(file_path, bibdoc_name, rename, doctype, description,
                comment, file_restriction, recid, curdir, iconsize,
                create_icon_doctypes, pending_bibdocs, bibrecdocs)

        elif action == 'addFormat':
            add_format(file_path, bibdoc_name, recid, doctype, curdir,
                       iconsize, create_icon_doctypes,
                       pending_bibdocs, bibrecdocs)

        elif action == 'revise':
            revise(file_path, bibdoc_name, rename, doctype,
                   description, comment, file_restriction, iconsize,
                   create_icon_doctypes, keep_previous_versions,
                   recid, curdir, pending_bibdocs,
                   bibrecdocs, forceFileRevision)

        elif action == 'delete':
            delete(bibdoc_name, recid, curdir, pending_bibdocs,
                   bibrecdocs)

    # Update the MARC
    bibdocfile_bin = os.path.join(CFG_BINDIR, 'bibdocfile --yes-i-know')
    run_shell_command(bibdocfile_bin + " --fix-marc --recid=%s", (str(recid),))

    # Delete the HB BibFormat cache in the DB, so that the fulltext
    # links do not point to possible dead files
    run_sql("DELETE from bibfmt WHERE format='HB' AND id_bibrec=%s", (recid,))

def add(file_path, bibdoc_name, rename, doctype, description, comment,
        file_restriction, recid, curdir, iconsize, create_icon_doctypes,
        pending_bibdocs, bibrecdocs):
    """
    Adds the file using bibdocfile CLI
    """
    try:
        if os.path.exists(file_path):
            # Add file
            bibdoc = bibrecdocs.add_new_file(file_path,
                                             doctype,
                                             rename or bibdoc_name,
                                             never_fail=True)
            _do_log(curdir, 'Added ' + bibdoc.get_docname() + ': ' + \
                    file_path)

            # Add icon
            iconpath = ''
            if doctype in create_icon_doctypes or \
                   '*' in create_icon_doctypes:
                iconpath = _create_icon(file_path, iconsize)
                if iconpath is not None:
                    bibdoc.add_icon(iconpath)
                    _do_log(curdir, 'Added icon to ' + \
                            bibdoc.get_docname() + ': ' + iconpath)

            # Add description
            if description:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_description(description,
                                           bibdocfile.get_format())
                    _do_log(curdir, 'Described ' + \
                            bibdoc.get_docname() + ': ' + description)

            # Add comment
            if comment:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_comment(comment,
                                       bibdocfile.get_format())
                    _do_log(curdir, 'Commented ' + \
                            bibdoc.get_docname() + ': ' + comment)

            # Set restriction
            bibdoc.set_status(file_restriction)
            _do_log(curdir, 'Set restriction of ' + \
                    bibdoc.get_docname() + ': ' + \
                    file_restriction or '(no restriction)')

        else:
            # File has been later renamed or deleted.
            # Remember to add it later if file is found (ie
            # it was renamed)
            pending_bibdocs[bibdoc_name] = (doctype, comment, description, [])

    except InvenioWebSubmitFileError, e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                           'tried to add already existing file %s ' \
                           'with name %s to record %i.' % \
                           (file_path, bibdoc_name, recid),
                           alert_admin=True)

def add_format(file_path, bibdoc_name, recid, doctype, curdir,
               iconsize, create_icon_doctypes, pending_bibdocs,
               bibrecdocs):
    """
    Adds a new format to a bibdoc using bibdocfile CLI
    """
    try:
        if os.path.exists(file_path):

            # We must retrieve previous description and comment as
            # adding a file using the APIs reset these values
            prev_desc, prev_comment = None, None
            if bibrecdocs.has_docname_p(bibdoc_name):
                (prev_desc, prev_comment) = \
                            Create_Upload_Files_Interface.get_description_and_comment(bibrecdocs.get_bibdoc(bibdoc_name).list_latest_files())

            # Add file
            bibdoc = bibrecdocs.add_new_format(file_path,
                                               bibdoc_name,
                                               prev_desc,
                                               prev_comment)
            _do_log(curdir, 'Added new format to ' + \
                    bibdoc.get_docname() + ': ' + file_path)

            # Add icon
            iconpath = ''
            if doctype in create_icon_doctypes or \
                   '*' in create_icon_doctypes:
                iconpath = _create_icon(file_path, iconsize)
                if iconpath is not None:
                    bibdoc.add_icon(iconpath)
                    _do_log(curdir, 'Added icon to ' + \
                            bibdoc.get_docname() + ': ' + iconpath)

        else:
            # File has been later renamed or deleted.
            # Remember to add it later if file is found
            if pending_bibdocs.has_key(bibdoc_name):
                pending_bibdocs[bibdoc_name][3].append(file_path)
            # else: we previously added a file by mistake. Do
            # not care, it will be deleted
    except InvenioWebSubmitFileError, e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                           'tried to add already existing format %s ' \
                           'named %s in record %i.' % \
                           (file_path, bibdoc_name, recid),
                               alert_admin=True)

def revise(file_path, bibdoc_name, rename, doctype, description,
           comment, file_restriction, iconsize, create_icon_doctypes,
           keep_previous_versions, recid, curdir, pending_bibdocs,
           bibrecdocs, forceFileRevision):
    """
    Revises the given bibdoc with a new file
    """
    try:
        if os.path.exists(file_path) or not file_path:

            # Perform pending actions
            if pending_bibdocs.has_key(bibdoc_name):
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
                if not bibrecdocs.has_docname_p(original_bibdoc_name) and filepath:
                    # the bibdoc did not originaly exist, so it
                    # must be added first
                    bibdoc = bibrecdocs.add_new_file(file_path,
                                                     pending_bibdocs[bibdoc_name][0],
                                                     bibdoc_name,
                                                     never_fail=True)
                    _do_log(curdir, 'Added ' + bibdoc.get_docname() + ': ' + \
                            file_path)

                    # Set restriction
                    bibdoc.set_status(file_restriction)
                    _do_log(curdir, 'Set restriction of ' + \
                            bibdoc.get_docname() + ': ' + \
                            file_restriction or '(no restriction)')

                # We must retrieve previous description and comment as
                # revising a file using the APIs reset these values
                prev_desc, prev_comment = None, None
                if bibrecdocs.has_docname_p(bibdoc_name):
                    (prev_desc, prev_comment) = \
                                Create_Upload_Files_Interface.get_description_and_comment(bibrecdocs.get_bibdoc(bibdoc_name).list_latest_files())

                # Do we have additional formats?
                for additional_format in pending_bibdocs[bibdoc_name][3]:
                    if os.path.exists(additional_format):
                        bibdoc.add_file_new_format(additional_format,
                                                   description=bibdoc.get_description(),
                                                   comment=bibdoc.get_comment())
                        _do_log(curdir, 'Added new format to' + \
                                bibdoc.get_docname() + ': ' + file_path)

                # All pending modification have been applied,
                # so delete
                del pending_bibdocs[bibdoc_name]

            # We must retrieve previous description and comment as
            # revising a file using the APIs reset these values
            prev_desc, prev_comment = None, None
            if bibrecdocs.has_docname_p(bibdoc_name):
                (prev_desc, prev_comment) = \
                            Create_Upload_Files_Interface.get_description_and_comment(bibrecdocs.get_bibdoc(bibdoc_name).list_latest_files())

            if keep_previous_versions and file_path:
                # Standard procedure, keep previous version
                bibdoc = bibrecdocs.add_new_version(file_path,
                                                    bibdoc_name,
                                                    prev_desc,
                                                    prev_comment)
                _do_log(curdir, 'Revised ' + bibdoc.get_docname() + \
                        ' with : ' + file_path)

            elif file_path:
                # Soft-delete previous versions, and add new file
                # (we need to get the doctype before deleting)
                if bibrecdocs.has_docname_p(bibdoc_name):
                    # Delete only if bibdoc originally
                    # existed
                    bibrecdocs.delete_bibdoc(bibdoc_name)
                    _do_log(curdir, 'Deleted ' + bibdoc_name)
                try:
                    bibdoc = bibrecdocs.add_new_file(file_path,
                                                     doctype,
                                                     bibdoc_name,
                                                     never_fail=True,
                                                     description=prev_desc,
                                                     comment=prev_comment)
                    _do_log(curdir, 'Added ' + bibdoc.get_docname() + ': ' + \
                            file_path)

                except InvenioWebSubmitFileError, e:
                    _do_log(curdir, str(e))
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
                            Create_Upload_Files_Interface.get_description_and_comment(bibdoc.list_latest_files())
                if prev_desc is None:
                    prev_desc = ""
                if prev_comment is None:
                    prev_comment = ""
                if forceFileRevision == '1' and \
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
                bibdoc.change_name(rename)
                _do_log(curdir, 'renamed ' + bibdoc_name +' to '+ rename)

            # Add icon
            if file_path:
                iconpath = ''
                if doctype in create_icon_doctypes or \
                       '*' in create_icon_doctypes:
                    iconpath = _create_icon(file_path, iconsize)
                    if iconpath is not None:
                        bibdoc.add_icon(iconpath)
                        _do_log(curdir, 'Added icon to ' + \
                                bibdoc.get_docname() + ': ' + iconpath)

            # Description
            if description:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_description(description,
                                           bibdocfile.get_format())
                    _do_log(curdir, 'Described ' + \
                            bibdoc.get_docname() + ': ' + description)
            # Comment
            if comment:
                bibdocfiles = bibdoc.list_latest_files()
                for bibdocfile in bibdocfiles:
                    bibdoc.set_comment(comment,
                                       bibdocfile.get_format())
                    _do_log(curdir, 'Commented ' + \
                            bibdoc.get_docname() + ': ' + comment)

            # Set restriction
            bibdoc.set_status(file_restriction)
            _do_log(curdir, 'Set restriction of ' + \
                    bibdoc.get_docname() + ': ' + \
                    file_restriction or '(no restriction)')
        else:
            # File has been later renamed or deleted.
            # Remember it
            if rename and rename != bibdoc_name:
                pending_bibdocs[rename] = pending_bibdocs[bibdoc_name]

    except InvenioWebSubmitFileError, e:
        # Format already existed.  How come? We should
        # have checked this in Create_Upload_Files_Interface.py
        register_exception(prefix='Move_Uploaded_Files_to_Storage ' \
                           'tried to revise a file %s ' \
                           'named %s in record %i.' % \
                           (file_path, bibdoc_name, recid),
                           alert_admin=True)

def delete(bibdoc_name, recid, curdir, pending_bibdocs,
           bibrecdocs):
    """
    Deletes the given bibdoc
    """
    try:
        if bibrecdocs.has_docname_p(bibdoc_name):
            bibrecdocs.delete_bibdoc(bibdoc_name)
            _do_log(curdir, 'Deleted ' + bibdoc_name)

        if pending_bibdocs.has_key(bibdoc_name):
            del pending_bibdocs[bibdoc_name]

    except InvenioWebSubmitFileError, e:
        # Mmh most probably we deleted two files at the same
        # second. Sleep 1 second and retry...  This might go
        # away one bibdoc improves its way to delete files
        try:
            time.sleep(1)
            bibrecdocs.delete_bibdoc(bibdoc_name)
            _do_log(curdir, 'Deleted ' + bibdoc_name)
            if pending_bibdocs.has_key(bibdoc_name):
                del pending_bibdocs[bibdoc_name]
        except InvenioWebSubmitFileError, e:
            _do_log(curdir, str(e))
            _do_log(curdir, repr(bibrecdocs.list_bibdocs()))
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
    """
    log_file = os.path.join(log_dir, 'performed_actions.log')
    file_desc = open(log_file, "a+")
    file_desc.write("%s --> %s\n" %(time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    file_desc.close()

def _create_icon(file_path, icon_size, format='gif', verbosity=9):
    """
    Creates icon of given file.

    Returns path to the icon. If creation fails, return None, and
    register exception (send email to admin).

    Parameters:

       - file_path : *str* full path to icon

       - icon_size : *int* the scaling information to be used for the
                     creation of the new icon.

       - verbosity : *int* the verbosity level under which the program
                     is to run;
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
             'icon-file-format': format,
             'verbosity': verbosity})
        icon_path = icon_dir + os.sep + icon_name
    except InvenioWebSubmitIconCreatorError, e:
        register_exception(prefix='Icon for file %s could not be created: %s' % \
                           (file_path, str(e)),
                           alert_admin=False)
    return icon_path
