# -*- coding: utf-8 -*-
# Comments and reviews for records.

# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2015 CERN.
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
Invenio implementation of the connector to CKEditor for file upload.

This is heavily borrowed from FCKeditor 'upload.py' sample connector.
"""
import os
import re
from invenio.legacy.bibdocfile.api import decompose_file, propose_next_docname

allowed_extensions = {}
allowed_extensions['File'] = ['7z','aiff','asf','avi','bmp','csv','doc','fla','flv','gif','gz','gzip','jpeg','jpg','mid','mov','mp3','mp4','mpc','mpeg','mpg','ods','odt','pdf','png','ppt','pxd','qt','ram','rar','rm','rmi','rmvb','rtf','sdc','sitd','swf','sxc','sxw','tar','tgz','tif','tiff','txt','vsd','wav','wma','wmv','xls','xml','zip']

allowed_extensions['Image'] = ['bmp','gif','jpeg','jpg','png']

allowed_extensions['Flash'] = ['swf','flv']

allowed_extensions['Media'] = ['aiff','asf','avi','bmp','fla', 'flv','gif','jpeg','jpg','mid','mov','mp3','mp4','mpc','mpeg','mpg','png','qt','ram','rm','rmi','rmvb','swf','tif','tiff','wav','wma','wmv']

default_allowed_types = ['File', 'Image', 'Flash', 'Media']

def process_CKEditor_upload(form, uid, user_files_path, user_files_absolute_path,
                            recid=None, allowed_types=default_allowed_types):
    """
    Process a file upload request.

    @param form: the form as in req object.
    @type form: dict
    @param uid: the user ID of the user uploading the file.
    @type uid: int
    @param user_files_path: the base URL where the file can be
        accessed from the web after upload.
        Note that you have to implement your own handler to stream the files from the directory
        C{user_files_absolute_path} if you set this value.
    @type user_files_path: string
    @param user_files_absolute_path: the base path on the server where
        the files should be saved.
        Eg:C{%(CFG_DATADIR)s/comments/%(recid)s/%(uid)s}
    @type user_files_absolute_path: string
    @param recid: the record ID for which we upload a file. Leave None if not relevant.
    @type recid: int
    @param allowed_types: types allowed for uploading. These
        are supported by CKEditor: ['File', 'Image', 'Flash', 'Media']
    @type allowed_types: list of strings
    @return: (msg, uploaded_file_path, uploaded_file_name, uploaded_file_url, callback_function)
    """
    msg = ''
    filename = ''
    formfile = None
    uploaded_file_path = ''
    user_files_path = ''

    for key, formfields in form.items():
        if key != 'upload':
            continue
        if hasattr(formfields, "filename") and formfields.filename:
            # We have found our file
            filename = formfields.filename
            formfile = formfields.file
            break

    can_upload_file_p = False
    if not form['type'] in allowed_types:
        # Is the type sent through the form ok?
        msg = 'You are not allowed to upload a file of this type'
    else:
        # Is user allowed to upload such file extension?
        basedir, name, extension = decompose_file(filename)
        extension = extension[1:] # strip leading dot
        if extension in allowed_extensions.get(form['type'], []):
            can_upload_file_p = True

    if not can_upload_file_p:
        msg = 'You are not allowed to upload a file of this type'
    elif filename and formfile:
        ## Before saving the file to disk, wash the filename (in particular
        ## washing away UNIX and Windows (e.g. DFS) paths):
        filename = os.path.basename(filename.split('\\')[-1])
        # Remove \ / | : ? *
	filename = re.sub ( '\\\\|\\/|\\||\\:|\\?|\\*|"|<|>|[\x00-\x1f\x7f-\x9f]/', '_', filename)
        filename = filename.strip()
        if filename != "":
            # Check that file does not already exist
            n = 1
            while os.path.exists(os.path.join(user_files_absolute_path, filename)):
                basedir, name, extension = decompose_file(filename)
                new_name = propose_next_docname(name)
                filename = new_name + extension

            # This may be dangerous if the file size is bigger than the available memory
            fp = open(os.path.join(user_files_absolute_path, filename), "w")
            fp.write(formfile.read())
            fp.close()

            uploaded_file_path = os.path.join(user_files_absolute_path, filename)
            uploaded_file_name = filename

    return (msg, uploaded_file_path, filename, user_files_path, form['CKEditorFuncNum'])

def send_response(req, msg, fileurl, callback_function):
    """
    Send a response to the CKEdtior after a file upload.

    @param req: the request object
    @param msg: the message to send to the user
    @param fileurl: the URL where the newly uploaded file can be found, if any
    @param callback_function: a value returned when calling C{process_CKEditor_upload()}
    """
    req.content_type = 'text/html'
    req.send_http_header()
    req.write('''<html><body><script type="text/javascript">window.parent.CKEDITOR.tools.callFunction(%(function_number)s, '%(url)s', '%(msg)s')</script></body></html>''' % \
              {'function_number': callback_function,
               'url': fileurl,
               'msg': msg.replace("'", "\\'")})
