# -*- coding: utf-8 -*-
## Comments and reviews for records.

## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011 CERN.
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
"""
Invenio implementation of the connector to FCKEditor for file upload.

This is heavily borrowed from FCKeditor 'upload.py' sample connector.
"""
import os
from invenio.fckeditor.editor.filemanager.connectors.py.fckcommands import \
     UploadFileCommandMixin, \
     CreateFolderCommandMixin
from invenio.fckeditor.editor.filemanager.connectors.py.fckconnector import FCKeditorConnectorBase
from invenio.fckeditor.editor.filemanager.connectors.py.fckoutput import \
     BaseHttpMixin, \
     BaseHtmlMixin, \
     BaseXmlMixin


class FCKeditorConnectorInvenio(FCKeditorConnectorBase,
                                UploadFileCommandMixin,
                                CreateFolderCommandMixin,
                                BaseHttpMixin, BaseHtmlMixin,
                                BaseXmlMixin):
    """
    Invenio connector for the upload of files from the FCKeditor.

    Check webcomment_webinterface for an example of use of this class.
    """

    def __init__(self, args, recid, uid, allowed_commands,
                 allowed_types, user_files_path,
                 user_files_absolute_path):
        """Constructor

        Parameters:

                     args - *dict* the arguments submitted via
                            GET/POST

                     uid - the user id of the submitted

         allowed_commands - *list* commands allowed for
                            uploading. These are supported by
                            FCKeditor: ['QuickUpload', 'FileUpload',
                            'GetFolders', 'GetFoldersAndFiles',
                            'CreateFolder' ] but this connector only
                            support 'QuickUpload'

            allowed_types - *list* types allowed for uploading. These
                            are supported by FCKeditor: ['File',
                            'Image', 'Flash', 'Media']

          user_files_path - *str* the URL where the file should be
                            accessible after upload. Eg:
                            %(CFG_SITE_URL)s/%(CFG_SITE_RECORD)s/%(recid)i/comments/attachments/get/%(uid)s
                            (the next parts of the URL will be append
                            automatically)

 user_files_absolute_path - *str* the path to the directory on the
                            server where the files will be saved. Eg:
                            %(CFG_PREFIX)s/var/data/comments/%(recid)s/%(uid)s
                            (the next parts of the path will be append
                            automatically)
        """
        self.request = args
        self.headers = [] # Clean Headers
        self.uid = uid
        self.recid = recid
        self.allowed_commands = allowed_commands
        self.allowed_types = allowed_types
        self.user_files_path = user_files_path
        self.user_files_absolute_path = user_files_absolute_path

    def setHeader(self, key, value):
        """
        Set a new header that will be sent when answering the user.
        """
        self.headers.append((key, value))
        return

    def doResponse(self):
        """Main function. Process the request, set
        headers and return a string as response.

        You should check authorizations prior to calling this
        function.
        """
        # The file type (from the QueryString, by default 'File').
        resource_type = self.request.get('type', 'File')


        command = 'QuickUpload' # only supported one for the moment

        # Check if it is an allowed command
        if not command in self.allowed_commands:
            return self.sendUploadResults( 1, '', '', 'The %s command isn\'t allowed' % command )

        if not resource_type in self.allowed_types:
            return self.sendUploadResults( 1, '', '', 'Invalid type specified' )

        # Setup paths
        self.userFilesFolder = self.user_files_absolute_path + '/' + resource_type.lower()
        self.webUserFilesFolder = self.user_files_path + '/' + resource_type.lower()

        # Ensure that the directory exists.
        if not os.path.exists(self.userFilesFolder):
            try:
                self.createServerFolder(self.userFilesFolder)
            except Exception, e:
                return self.sendError(1, "This connector couldn\'t access to local user\'s files directories.  Please check the UserFilesAbsolutePath in \"editor/filemanager/connectors/py/config.py\" and try again. ")

        # File upload doesn't have to return XML, so intercept here
        return self.uploadFile(resource_type, '/')
