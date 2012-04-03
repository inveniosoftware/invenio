## $Id: Move_Revised_Files_to_Storage.py,v 1.20 2009/03/26 13:48:42 jerome Exp $

## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""WebSubmit function - Archives files uploaded with the upload file
                        interface.

To be used on par with Create_Upload_Files_Interface.py function:
 - Create_Upload_Files_Interface records the actions performed by user.
 - Move_Uploaded_Files_to_Storage executes the recorded actions.

NOTE:
=====

 - Due to the way WebSubmit works, this function can only work when
   positionned at step 2 in WebSubmit admin, and
   Create_Upload_Files_Interface is at step 1
"""

__revision__ = "$Id$"


from invenio import websubmit_managedocfiles

def Move_Uploaded_Files_to_Storage(parameters, curdir, form, user_info=None):
    """
    The function moves files uploaded using the
    Create_Upload_Files_Interface.py function.

    It reads the action previously performed by the user on the files
    and calls the corresponding functions of bibdocfile.

    @param parameters:(dictionary) - must contain:
      + iconsizes: sizes of the icons to create (when applicable),
                   separated by commas. Eg: 180>,700>

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

    iconsize = parameters.get('iconsize').split(',')
    create_icon_doctypes = parameters.get('createIconDoctypes').split('|')
    force_file_revision = (parameters.get('forceFileRevision') == '1')

    try:
        websubmit_managedocfiles._read_file_revision_interface_configuration_from_disk(curdir)
    except IOError:
        return

    websubmit_managedocfiles.move_uploaded_files_to_storage(curdir,
                                        recid, iconsize,
                                        create_icon_doctypes,
                                        force_file_revision)
