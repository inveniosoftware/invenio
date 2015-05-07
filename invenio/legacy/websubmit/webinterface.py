# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

import os
import errno
import time
import cgi
import sys
import shutil

from urllib import urlencode
from collections import defaultdict

from invenio.legacy.bibrecord import create_record
from invenio.config import \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_WEBSUBMIT_STORAGEDIR, \
     CFG_TMPDIR, \
     CFG_CERN_SITE
from invenio.utils.crossref import get_marcxml_for_doi, CrossrefError
from invenio.utils import apache
from invenio.legacy.dbquery import run_sql
from invenio.modules.access.engine import acc_authorize_action
from invenio.modules.access.control import acc_is_role
from invenio.legacy.webpage import warning_page
from invenio.legacy.webuser import getUid, page_not_authorized, collect_user_info, \
                            isGuestUser
from invenio.modules.records.access import is_user_owner_of_record
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.utils.url import make_canonical_urlargd, redirect_to_url
from invenio.base.i18n import gettext_set_language
from invenio.legacy.bibdocfile.api import stream_file, \
    decompose_file, propose_next_docname
from invenio.ext.logging import register_exception
from invenio.utils.html import is_html_text_editor_installed
from invenio.legacy.websubmit.icon_creator import create_icon, InvenioWebSubmitIconCreatorError
from invenio.legacy.ckeditor.connector import process_CKEditor_upload, send_response
import invenio.legacy.template
websubmit_templates = invenio.legacy.template.load('websubmit')
from invenio.legacy.websearch.adminlib import get_detailed_page_tabs
from invenio.utils.json import json, CFG_JSON_AVAILABLE
import invenio.legacy.template
from flask import session

webstyle_templates = invenio.legacy.template.load('webstyle')
websearch_templates = invenio.legacy.template.load('websearch')

from invenio.legacy.websubmit.engine import home, action, interface, endaction, makeCataloguesTable

class WebInterfaceSubmitPages(WebInterfaceDirectory):

    _exports = ['summary', 'sub', 'direct', '', 'attachfile', 'uploadfile', \
                'getuploadedfile', 'upload_video', ('continue', 'continue_'), \
                'doilookup']

    def uploadfile(self, req, form):
        """
        Similar to /submit, but only consider files. Nice for
        asynchronous Javascript uploads. Should be used to upload a
        single file.

        Also try to create an icon, and return URL to file(s) + icon(s)

        Authentication is performed based on session ID passed as
        parameter instead of cookie-based authentication, due to the
        use of this URL by the Flash plugin (to upload multiple files
        at once), which does not route cookies.

        FIXME: consider adding /deletefile and /modifyfile functions +
        parsing of additional parameters to rename files, add
        comments, restrictions, etc.
        """
        argd = wash_urlargd(form, {
            'doctype': (str, ''),
            'access': (str, ''),
            'indir': (str, ''),
            'session_id': (str, ''),
            'rename': (str, ''),
            })

        curdir = None
        if "indir" not in form or \
               "doctype" not in form or \
               "access" not in form:
            raise apache.SERVER_RETURN(apache.HTTP_BAD_REQUEST)
        else:
            curdir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                  argd['indir'],
                                  argd['doctype'],
                                  argd['access'])

        user_info = collect_user_info(req)
        if "session_id" in form:
            # Are we uploading using Flash, which does not transmit
            # cookie? The expect to receive session_id as a form
            # parameter.  First check that IP addresses do not
            # mismatch.

            uid = session.uid
            user_info = collect_user_info(uid)
            try:
                act_fd = file(os.path.join(curdir, 'act'))
                action = act_fd.read()
                act_fd.close()
            except:
                action = ""

        try:
            recid_fd = file(os.path.join(curdir, 'SN'))
            recid = recid_fd.read()
            recid_fd.close()
        except:
            recid = ''
        user_is_owner = False
        if recid:
            user_is_owner = is_user_owner_of_record(user_info, recid)

        try:
            categ_fd = file(os.path.join(curdir, 'combo%s' %argd['doctype']))
            categ = categ_fd.read()
            categ_fd.close()
        except IOError:
            categ = '*'

        # Is user authorized to perform this action?
        (auth_code, auth_message) = acc_authorize_action(uid, "submit",
                                                         authorized_if_no_roles=not isGuestUser(uid),
                                                         verbose=0,
                                                         doctype=argd['doctype'],
                                                         act=action,
                                                         categ=categ)
        if acc_is_role("submit", doctype=argd['doctype'], act=action) and auth_code != 0 and not user_is_owner:
            # User cannot submit
            raise apache.SERVER_RETURN(apache.HTTP_UNAUTHORIZED)
        else:
            # Process the upload and get the response
            added_files = {}
            for key, formfields in form.items():
                filename = key.replace("[]", "")
                file_to_open = os.path.join(curdir, filename)
                if hasattr(formfields, "filename") and formfields.filename:
                    dir_to_open = os.path.abspath(os.path.join(curdir,
                                                               'files',
                                                               str(user_info['uid']),
                                                               key))
                    try:
                        assert(dir_to_open.startswith(CFG_WEBSUBMIT_STORAGEDIR))
                    except AssertionError:
                        register_exception(req=req, prefix='curdir="%s", key="%s"' % (curdir, key))
                        raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                    if not os.path.exists(dir_to_open):
                        try:
                            os.makedirs(dir_to_open)
                        except OSError as e:
                            if e.errno != errno.EEXIST:
                                # If the issue is only that directory
                                # already exists, then continue, else
                                # report
                                register_exception(req=req, alert_admin=True)
                                raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                    filename = formfields.filename
                    ## Before saving the file to disc, wash the filename (in particular
                    ## washing away UNIX and Windows (e.g. DFS) paths):
                    filename = os.path.basename(filename.split('\\')[-1])
                    filename = filename.strip()
                    if filename != "":
                        # Check that file does not already exist
                        n = 1
                        while os.path.exists(os.path.join(dir_to_open, filename)):
                            #dirname, basename, extension = decompose_file(new_destination_path)
                            basedir, name, extension = decompose_file(filename)
                            new_name = propose_next_docname(name)
                            filename = new_name + extension
                        # This may be dangerous if the file size is bigger than the available memory
                        fp = open(os.path.join(dir_to_open, filename), "w")
                        fp.write(formfields.file.read())
                        fp.close()
                        fp = open(os.path.join(curdir, "lastuploadedfile"), "w")
                        fp.write(filename)
                        fp.close()
                        fp = open(file_to_open, "w")
                        fp.write(filename)
                        fp.close()
                        try:
                            # Create icon
                            (icon_path, icon_name) = create_icon(
                                { 'input-file'           : os.path.join(dir_to_open, filename),
                                  'icon-name'            : filename, # extension stripped automatically
                                  'icon-file-format'     : 'gif',
                                  'multipage-icon'       : False,
                                  'multipage-icon-delay' : 100,
                                  'icon-scale'           : "300>", # Resize only if width > 300
                                  'verbosity'            : 0,
                                  })

                            icons_dir = os.path.join(os.path.join(curdir,
                                                                  'icons',
                                                                  str(user_info['uid']),
                                                                  key))
                            if not os.path.exists(icons_dir):
                                # Create uid/icons dir if needed
                                try:
                                    os.makedirs(icons_dir)
                                except OSError as e:
                                    if e.errno != errno.EEXIST:
                                        # If the issue is only that
                                        # directory already exists,
                                        # then continue, else report
                                        register_exception(req=req, alert_admin=True)
                                        raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)
                            os.rename(os.path.join(icon_path, icon_name),
                                      os.path.join(icons_dir, icon_name))
                            added_files[key] = {'name': filename,
                                                'iconName': icon_name}
                        except InvenioWebSubmitIconCreatorError as e:
                            # We could not create the icon
                            added_files[key] = {'name': filename}
                            continue
                    else:
                        raise apache.SERVER_RETURN(apache.HTTP_BAD_REQUEST)

            # Send our response
            if CFG_JSON_AVAILABLE:
                return json.dumps(added_files)


    def upload_video(self, req, form):
        """
        A clone of uploadfile but for (large) videos.
        Does not copy the uploaded file to the websubmit directory.
        Instead, the path to the file is stored inside the submission directory.
        """

        def gcd(a, b):
            """ the euclidean algorithm """
            while a:
                a, b = b % a, a
            return b

        from invenio.modules.encoder.extract import extract_frames
        from invenio.modules.encoder.config import CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_DIR, CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_FNAME
        from invenio.modules.encoder.encode import determine_aspect
        from invenio.modules.encoder.utils import probe
        from invenio.modules.encoder.metadata import ffprobe_metadata
        from invenio.legacy.websubmit.config import CFG_WEBSUBMIT_TMP_VIDEO_PREFIX

        argd = wash_urlargd(form, {
            'doctype': (str, ''),
            'access': (str, ''),
            'indir': (str, ''),
            'session_id': (str, ''),
            'rename': (str, ''),
            })

        curdir = None
        if "indir" not in form or \
               "doctype" not in form or \
               "access" not in form:
            raise apache.SERVER_RETURN(apache.HTTP_BAD_REQUEST)
        else:
            curdir = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                  argd['indir'],
                                  argd['doctype'],
                                  argd['access'])

        user_info = collect_user_info(req)
        if "session_id" in form:
            # Are we uploading using Flash, which does not transmit
            # cookie? The expect to receive session_id as a form
            # parameter.  First check that IP addresses do not
            # mismatch.

            uid = session.uid
            user_info = collect_user_info(uid)
            try:
                act_fd = file(os.path.join(curdir, 'act'))
                action = act_fd.read()
                act_fd.close()
            except:
                act = ""

        # Is user authorized to perform this action?
        (auth_code, auth_message) = acc_authorize_action(uid, "submit",
                                                         authorized_if_no_roles=not isGuestUser(uid),
                                                         verbose=0,
                                                         doctype=argd['doctype'],
                                                         act=action)
        if acc_is_role("submit", doctype=argd['doctype'], act=action) and auth_code != 0:
            # User cannot submit
            raise apache.SERVER_RETURN(apache.HTTP_UNAUTHORIZED)
        else:
            # Process the upload and get the response
            json_response = {}
            for key, formfields in form.items():
                filename = key.replace("[]", "")
                if hasattr(formfields, "filename") and formfields.filename:
                    dir_to_open = os.path.abspath(os.path.join(curdir,
                                                               'files',
                                                               str(user_info['uid']),
                                                               key))
                    try:
                        assert(dir_to_open.startswith(CFG_WEBSUBMIT_STORAGEDIR))
                    except AssertionError:
                        register_exception(req=req, prefix='curdir="%s", key="%s"' % (curdir, key))
                        raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                    if not os.path.exists(dir_to_open):
                        try:
                            os.makedirs(dir_to_open)
                        except OSError as e:
                            if e.errno != errno.EEXIST:
                                # If the issue is only that directory
                                # already exists, then continue, else
                                # report
                                register_exception(req=req, alert_admin=True)
                                raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                    filename = formfields.filename
                    ## Before saving the file to disc, wash the filename (in particular
                    ## washing away UNIX and Windows (e.g. DFS) paths):
                    filename = os.path.basename(filename.split('\\')[-1])
                    filename = filename.strip()
                    if filename != "":
                        # Check that file does not already exist
                        while os.path.exists(os.path.join(dir_to_open, filename)):
                            #dirname, basename, extension = decompose_file(new_destination_path)
                            basedir, name, extension = decompose_file(filename)
                            new_name = propose_next_docname(name)
                            filename = new_name + extension

                        #-------------#
                        # VIDEO STUFF #
                        #-------------#

                        ## Remove all previous uploads
                        filelist = os.listdir(os.path.split(formfields.file.name)[0])
                        for afile in filelist:
                            if argd['access'] in afile:
                                os.remove(os.path.join(os.path.split(formfields.file.name)[0], afile))

                        ## Check if the file is a readable video
                        ## We must exclude all image and audio formats that are readable by ffprobe
                        if (os.path.splitext(filename)[1] in ['jpg', 'jpeg', 'gif', 'tiff', 'bmp', 'png', 'tga',
                                                              'jp2', 'j2k', 'jpf', 'jpm', 'mj2', 'biff', 'cgm',
                                                              'exif', 'img', 'mng', 'pic', 'pict', 'raw', 'wmf', 'jpe', 'jif',
                                                              'jfif', 'jfi', 'tif', 'webp', 'svg', 'ai', 'ps', 'psd',
                                                              'wav', 'mp3', 'pcm', 'aiff', 'au', 'flac', 'wma', 'm4a', 'wv', 'oga',
                                                              'm4a', 'm4b', 'm4p', 'm4r', 'aac', 'mp4', 'vox', 'amr', 'snd']
                                                              or not probe(formfields.file.name)):
                            formfields.file.close()
                            raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                        ## We have no "delete" attribute in Python 2.4
                        if sys.hexversion < 0x2050000:
                            ## We need to rename first and create a dummy file
                            ## Rename the temporary file for the garbage collector
                            new_tmp_fullpath = os.path.split(formfields.file.name)[0] + "/" + CFG_WEBSUBMIT_TMP_VIDEO_PREFIX + argd['access'] + "_" + os.path.split(formfields.file.name)[1]
                            os.rename(formfields.file.name, new_tmp_fullpath)
                            dummy = open(formfields.file.name, "w")
                            dummy.close()
                            formfields.file.close()
                        else:
                            # Mark the NamedTemporatyFile as not to be deleted
                            formfields.file.delete = False
                            formfields.file.close()
                            ## Rename the temporary file for the garbage collector
                            new_tmp_fullpath = os.path.split(formfields.file.name)[0] + "/" + CFG_WEBSUBMIT_TMP_VIDEO_PREFIX + argd['access'] + "_" + os.path.split(formfields.file.name)[1]
                            os.rename(formfields.file.name, new_tmp_fullpath)

                        # Write the path to the temp file to a file in STORAGEDIR
                        fp = open(os.path.join(dir_to_open, "filepath"), "w")
                        fp.write(new_tmp_fullpath)
                        fp.close()

                        fp = open(os.path.join(dir_to_open, "filename"), "w")
                        fp.write(filename)
                        fp.close()

                        ## We are going to extract some thumbnails for websubmit ##
                        sample_dir = os.path.join(curdir, 'files', str(user_info['uid']), CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_DIR)
                        try:
                            ## Remove old thumbnails
                            shutil.rmtree(sample_dir)
                        except OSError:
                            register_exception(req=req, alert_admin=False)
                        try:
                            os.makedirs(os.path.join(curdir, 'files', str(user_info['uid']), sample_dir))
                        except OSError:
                            register_exception(req=req, alert_admin=False)
                        try:
                            extract_frames(input_file=new_tmp_fullpath,
                                        output_file=os.path.join(sample_dir, CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_FNAME),
                                        size="600x600",
                                        numberof=5)
                            json_response['frames'] = []
                            for extracted_frame in os.listdir(sample_dir):
                                json_response['frames'].append(extracted_frame)
                        except:
                            ## If the frame extraction fails, something was bad with the video
                            os.remove(new_tmp_fullpath)
                            register_exception(req=req, alert_admin=False)
                            raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                        ## Try to detect the aspect. if this fails, the video is not readable
                        ## or a wrong file might have been uploaded
                        try:
                            (aspect, width, height) = determine_aspect(new_tmp_fullpath)
                            if aspect:
                                aspx, aspy = aspect.split(':')
                            else:
                                the_gcd = gcd(width, height)
                                aspx = str(width / the_gcd)
                                aspy = str(height / the_gcd)
                            json_response['aspx'] = aspx
                            json_response['aspy'] = aspy
                        except TypeError:
                            ## If the aspect detection completely fails
                            os.remove(new_tmp_fullpath)
                            register_exception(req=req, alert_admin=False)
                            raise apache.SERVER_RETURN(apache.HTTP_FORBIDDEN)

                        ## Try to extract some metadata from the video container
                        metadata = ffprobe_metadata(new_tmp_fullpath)
                        json_response['meta_title'] = metadata['format'].get('TAG:title')
                        json_response['meta_description'] = metadata['format'].get('TAG:description')
                        json_response['meta_year'] = metadata['format'].get('TAG:year')
                        json_response['meta_author'] = metadata['format'].get('TAG:author')
                    ## Empty file name
                    else:
                        raise apache.SERVER_RETURN(apache.HTTP_BAD_REQUEST)
                    ## We found our file, we can break the loop
                    break;

            # Send our response
            if CFG_JSON_AVAILABLE:

                dumped_response = json.dumps(json_response)

                # store the response in the websubmit directory
                # this is needed if the submission is not finished and continued later
                response_dir = os.path.join(curdir, 'files', str(user_info['uid']), "response")
                try:
                    os.makedirs(response_dir)
                except OSError:
                    # register_exception(req=req, alert_admin=False)
                    pass
                fp = open(os.path.join(response_dir, "response"), "w")
                fp.write(dumped_response)
                fp.close()

                return dumped_response

    def getuploadedfile(self, req, form):
        """
        Stream uploaded files.

        For the moment, restrict to files in ./curdir/files/uid or
        ./curdir/icons/uid directory, so that we are sure we stream
        files only to the user who uploaded them.
        """
        argd = wash_urlargd(form, {'indir': (str, None),
                                   'doctype': (str, None),
                                   'access': (str, None),
                                   'icon': (int, 0),
                                   'key': (str, None),
                                   'filename': (str, None),
                                   'nowait': (int, 0)})

        if None in argd.values():
            raise apache.SERVER_RETURN(apache.HTTP_BAD_REQUEST)

        uid = getUid(req)

        if argd['icon']:
            file_path = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                     argd['indir'],
                                     argd['doctype'],
                                     argd['access'],
                                     'icons',
                                     str(uid),
                                     argd['key'],
                                     argd['filename']
                                     )
        else:
            file_path = os.path.join(CFG_WEBSUBMIT_STORAGEDIR,
                                     argd['indir'],
                                     argd['doctype'],
                                     argd['access'],
                                     'files',
                                     str(uid),
                                     argd['key'],
                                     argd['filename']
                                     )

        abs_file_path = os.path.abspath(file_path)
        if abs_file_path.startswith(CFG_WEBSUBMIT_STORAGEDIR):
            # Check if file exist. Note that icon might not yet have
            # been created.
            if not argd['nowait']:
                for i in range(5):
                    if os.path.exists(abs_file_path):
                        return stream_file(req, abs_file_path)
                    time.sleep(1)
            else:
                if os.path.exists(abs_file_path):
                        return stream_file(req, abs_file_path)

        # Send error 404 in all other cases
        raise apache.SERVER_RETURN(apache.HTTP_NOT_FOUND)

    def attachfile(self, req, form):
        """
        Process requests received from CKEditor to upload files.
        If the uploaded file is an image, create an icon version
        """
        if not is_html_text_editor_installed():
            return apache.HTTP_NOT_FOUND

        if 'type' not in form:
            form['type'] = 'File'

        if 'upload' not in form or \
               not form['type'] in \
               ['File', 'Image', 'Flash', 'Media']:
            #return apache.HTTP_NOT_FOUND
            pass
        filetype = form['type'].lower()

        uid = getUid(req)


        # URL where the file can be fetched after upload
        user_files_path = os.path.join(CFG_SITE_URL, 'submit', 'getattachedfile', uid)

        # Path to directory where uploaded files are saved
        user_files_absolute_path = os.path.join(CFG_TMPDIR, 'attachfile', uid, filetype)
        try:
            os.makedirs(user_files_absolute_path)
        except:
            pass

        user_info = collect_user_info(req)
        (auth_code, auth_message) = acc_authorize_action(user_info, 'attachsubmissionfile')
        msg = ""
        if user_info['email'] == 'guest':
            # User is guest: must login prior to upload
            msg = 'Please login before uploading file.'
        elif auth_code:
            # User cannot submit
            msg = 'Sorry, you are not allowed to submit files.'
        ## elif len(form['upload']) != 1:
        ##     msg = 'Sorry, you must upload one single file'
        else:
            # Process the upload and get the response
            (msg, uploaded_file_path, uploaded_file_name, uploaded_file_url, callback_function) = \
                  process_CKEditor_upload(form, uid, user_files_path, user_files_absolute_path)

            if uploaded_file_path:
                # Create an icon
                if form.get('type','') == 'Image':
                    try:
                        (icon_path, icon_name) = create_icon(
                            { 'input-file'           : uploaded_file_path,
                              'icon-name'            : os.path.splitext(uploaded_file_name)[0],
                              'icon-file-format'     : os.path.splitext(uploaded_file_name)[1][1:] or 'gif',
                              'multipage-icon'       : False,
                              'multipage-icon-delay' : 100,
                              'icon-scale'           : "700>", # Resize only if width > 700
                              'verbosity'            : 0,
                              })

                        # Move original file to /original dir, and replace it with icon file
                        original_user_files_absolute_path = os.path.join(user_files_absolute_path,
                                                                         'original')
                        if not os.path.exists(original_user_files_absolute_path):
                            # Create /original dir if needed
                            os.mkdir(original_user_files_absolute_path)
                        os.rename(uploaded_file_path,
                                  original_user_files_absolute_path + os.sep + uploaded_file_name)
                        os.rename(icon_path + os.sep + icon_name,
                                  uploaded_file_path)
                    except InvenioWebSubmitIconCreatorError as e:
                        pass

                user_files_path += '/' + filetype + '/' + uploaded_file_name

            else:
                user_files_path = ''
                if not msg:
                    msg = 'No valid file found'

        # Send our response
        send_response(req, msg, user_files_path, callback_function)

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs (for getting
        and putting attachments) Eg:
        /submit/getattachedfile/41336978/image/myfigure.png
        /submit/attachfile/41336978/image/myfigure.png
        """
        if component == 'getattachedfile' and len(path) > 2:

            uid = path[0] # uid of the submitter
            file_type = path[1] # file, image, flash or media (as
                                # defined by CKEditor)

            if file_type in ['file', 'image', 'flash', 'media']:
                file_name = '/'.join(path[2:]) # the filename

                def answer_get(req, form):
                    """Accessing files attached to submission."""
                    form['file'] = file_name
                    form['type'] = file_type
                    form['uid'] = uid
                    return self.getattachedfile(req, form)

                return answer_get, []

        # All other cases: file not found
        return None, []

    def getattachedfile(self, req, form):
        """
        Returns a file uploaded to the submission 'drop box' by the
        CKEditor.
        """
        argd = wash_urlargd(form, {'file': (str, None),
                                   'type': (str, None),
                                   'uid': (int, 0)})

        # Can user view this record, i.e. can user access its
        # attachments?
        uid = getUid(req)
        user_info = collect_user_info(req)

        if not argd['file'] is None:
            # Prepare path to file on disk. Normalize the path so that
            # ../ and other dangerous components are removed.
            path = os.path.abspath(os.path.join(CFG_TMPDIR, 'attachfile',
                                                str(argd['uid']),
                                                argd['type'], argd['file']))

            # Check that we are really accessing attachements
            # directory, for the declared record.
            if path.startswith(os.path.join(CFG_TMPDIR, 'attachfile')) and os.path.exists(path):
                return stream_file(req, path)

        # Send error 404 in all other cases
        return(apache.HTTP_NOT_FOUND)

    def continue_(self, req, form):
        """
        Continue an interrupted submission.
        """
        args = wash_urlargd(form, {'access': (str, ''), 'doctype': (str, '')})
        ln = args['ln']

        _ = gettext_set_language(ln)

        access = args['access']
        doctype = args['doctype']
        if not access or not doctype:
            return warning_page(_("Sorry, invalid arguments"), req=req, ln=ln)
        user_info = collect_user_info(req)
        email = user_info['email']
        res = run_sql("SELECT action, status FROM sbmSUBMISSIONS WHERE id=%s AND email=%s and doctype=%s", (access, email, doctype))
        if res:
            action, status = res[0]
            if status == 'finished':
                return warning_page(_("Note: the requested submission has already been completed"), req=req, ln=ln)
            redirect_to_url(req, CFG_SITE_SECURE_URL + '/submit/direct?' + urlencode({
                'sub': action + doctype,
                'access': access}))
        return warning_page(_("Sorry, you don't seem to have initiated a submission with the provided access number"), req=req, ln=ln)

    def direct(self, req, form):
        """Directly redirected to an initialized submission."""
        args = wash_urlargd(form, {'sub': (str, ''),
                                   'access' : (str, '')})

        sub = args['sub']
        access = args['access']
        ln = args['ln']

        _ = gettext_set_language(ln)

        uid = getUid(req)

        if CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "direct",
                                       navmenuid='submit',
                                       text=_("Submissions are not available"))

        myQuery = req.args
        if not sub:
            return warning_page(_("Sorry, 'sub' parameter missing..."), req, ln=ln)
        res = run_sql("SELECT docname,actname FROM sbmIMPLEMENT WHERE subname=%s", (sub,))
        if not res:
            return warning_page(_("Sorry. Cannot analyse parameter"), req, ln=ln)
        else:
            # get document type
            doctype = res[0][0]
            # get action name
            action = res[0][1]
            # get category
            categ = req.form.get('combo%s' % doctype, '*')
        # retrieve other parameter values
        params = dict(form)

        # Check if user is authorized, based on doctype/action/categ,
        # in order to give guest users a chance to log in if needed:
        (auth_code, auth_message) = acc_authorize_action(req, 'submit',
                                                         authorized_if_no_roles=not isGuestUser(uid),
                                                         verbose=0,
                                                         doctype=doctype,
                                                         act=action,
                                                         categ=categ)
        if not auth_code == 0 and isGuestUser(uid):
            # Propose to login
            redirection_params = params
            redirection_params['referer'] = CFG_SITE_SECURE_URL + req.unparsed_uri
            return redirect_to_url(req, "%s/youraccount/login%s" % (
                CFG_SITE_SECURE_URL,
                make_canonical_urlargd(redirection_params, {})),
                                   norobot=True)
        # else: continue, and let main interface control the access

        # find existing access number
        if not access:
            # create 'unique' access number
            pid = os.getpid()
            now = time.time()
            access = "%i_%s" % (now, pid)
        # retrieve 'dir' value
        res = run_sql ("SELECT dir FROM sbmACTION WHERE sactname=%s", (action,))
        dir = res[0][0]

        mainmenu = req.headers_in.get('referer')

        params['access'] = access
        params['act'] = action
        params['doctype'] = doctype
        params['startPg'] = '1'
        params['mainmenu'] = mainmenu
        params['ln'] = ln
        params['indir'] = dir

        url = "%s/submit?%s" % (CFG_SITE_SECURE_URL, urlencode(params))
        redirect_to_url(req, url)

    def sub(self, req, form):
        """DEPRECATED: /submit/sub is deprecated now, so raise email to the admin (but allow submission to continue anyway)"""
        args = wash_urlargd(form, {'password': (str, '')})
        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../sub/",
                                       navmenuid='submit')
        try:
            raise DeprecationWarning, 'submit/sub handler has been used. Please use submit/direct. e.g. "submit/sub?RN=123@SBIFOO" -> "submit/direct?RN=123&sub=SBIFOO"'
        except DeprecationWarning:
            register_exception(req=req, alert_admin=True)

        ln = args['ln']
        _ = gettext_set_language(ln)
        #DEMOBOO_RN=DEMO-BOOK-2008-001&ln=en&password=1223993532.26572%40APPDEMOBOO
        params = dict(form)
        password = args['password']
        if password:
            del params['password']
            if "@" in password:
                params['access'], params['sub'] = password.split('@', 1)
            else:
                params['sub'] = password
        else:
            args = str(req.args).split('@')
            if len(args) > 1:
                params = {'sub' : args[-1]}
                args = '@'.join(args[:-1])
                params.update(cgi.parse_qs(args))
            else:
                return warning_page(_("Sorry, invalid URL..."), req, ln=ln)
        url = "%s/submit/direct?%s" % (CFG_SITE_SECURE_URL, urlencode(params, doseq=True))
        redirect_to_url(req, url)

    def summary(self, req, form):
        args = wash_urlargd(form, {
            'doctype': (str, ''),
            'act': (str, ''),
            'access': (str, ''),
            'indir': (str, '')})
        ln = args['ln']

        uid = getUid(req)
        if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
            return page_not_authorized(req, "../summary",
                                       navmenuid='submit')

        t = ""
        curdir  = os.path.join(CFG_WEBSUBMIT_STORAGEDIR, args['indir'], args['doctype'], args['access'])
        try:
            assert(curdir == os.path.abspath(curdir))
        except AssertionError:
            register_exception(req=req, alert_admin=True, prefix='Possible cracking tentative: indir="%s", doctype="%s", access="%s"' % (args['indir'], args['doctype'], args['access']))
            return warning_page("Invalid parameters", req, ln)

        subname = "%s%s" % (args['act'], args['doctype'])

        res = run_sql("select sdesc,fidesc,pagenb,level from sbmFIELD where subname=%s "
                      "order by pagenb,fieldnb", (subname,))
        nbFields = 0

        values = []
        for arr in res:
            if arr[0] != "":
                val = {
                       'mandatory' : (arr[3] == 'M'),
                       'value' : '',
                       'page' : arr[2],
                       'name' : arr[0],
                      }
                if os.path.exists(os.path.join(curdir, curdir, arr[1])):
                    fd = open(os.path.join(curdir, arr[1]),"r")
                    value = fd.read()
                    fd.close()
                    value = value.replace("\n"," ")
                    value = value.replace("Select:","")
                else:
                    value = ""
                val['value'] = value
                values.append(val)

        return websubmit_templates.tmpl_submit_summary(
                 ln = args['ln'],
                 values = values,
               )

    def doilookup(self, req, form):
        """
        Returns the metadata from the crossref website based on the DOI.
        """
        args = wash_urlargd(form, {
            'doi': (str, '')})
        response = defaultdict(list)
        if args['doi']:
            doi = args['doi']
            try:
                marcxml_template = get_marcxml_for_doi(doi)
            except CrossrefError:
                # Just ignore Crossref errors
                pass
            else:
                record = create_record(marcxml_template)[0]
                if record:
                    # We need to convert this record structure to a simple dictionary
                    for key, value in record.items():  # key, value = (773, [([('0', 'PER:64142'), ...], ' ', ' ', '', 47)])
                        for val in value:  # val = ([('0', 'PER:64142'), ...], ' ', ' ', '', 47)
                            ind1 = val[1].replace(" ", "_")
                            ind2 = val[2].replace(" ", "_")
                            for (k, v) in val[0]:  # k, v = ('0', 'PER:5409')
                                response[key+ind1+ind2+k].append(v)
            # The output dictionary is something like:
            # {"100__a": ['Smith, J.'],
            #  "700__a": ['Anderson, J.', 'Someoneelse, E.'],
            #  "700__u": ['University1', 'University2']}

        # return dictionary as JSON
        return json.dumps(response)

    def index(self, req, form):

        args = wash_urlargd(form, {
            'c': (str, CFG_SITE_NAME),
            'doctype': (str, ''),
            'act': (str, ''),
            'startPg': (str, "1"),
            'access': (str, ''),
            'mainmenu': (str, ''),
            'fromdir': (str, ''),
            'nextPg': (str, ''),
            'nbPg': (str, ''),
            'curpage': (str, '1'),
            'step': (str, '0'),
            'mode': (str, 'U'),
            })

        ## Strip whitespace from beginning and end of doctype and action:
        args["doctype"] = args["doctype"].strip()
        args["act"] = args["act"].strip()

        def _index(req, c, ln, doctype, act, startPg, access,
                   mainmenu, fromdir, nextPg, nbPg, curpage, step,
                   mode):
            auth_args = {}
            if doctype:
                auth_args['doctype'] = doctype
            if act:
                auth_args['act'] = act
            uid = getUid(req)

            if uid == -1 or CFG_ACCESS_CONTROL_LEVEL_SITE >= 1:
                return page_not_authorized(req, "direct",
                                            navmenuid='submit')

            if CFG_CERN_SITE:
                ## HACK BEGIN: this is a hack for CMS and ATLAS draft
                user_info = collect_user_info(req)
                if doctype == 'CMSPUB' and act == "" and 'cds-admin [CERN]' not in user_info['group'] and not user_info['email'].lower() == 'cds.support@cern.ch':
                    if isGuestUser(uid):
                        return redirect_to_url(req, "%s/youraccount/login%s" % (
                            CFG_SITE_SECURE_URL,
                            make_canonical_urlargd({'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri, 'ln' : args['ln']}, {}))
                                               , norobot=True)
                    if 'cms-publication-committee-chair [CERN]' not in user_info['group']:
                        return page_not_authorized(req, "../submit", text="In order to access this submission interface you need to be member of the CMS Publication Committee Chair.",
                                        navmenuid='submit')
                elif doctype == 'ATLPUB' and 'cds-admin [CERN]' not in user_info['group'] and not user_info['email'].lower() == 'cds.support@cern.ch':
                    if isGuestUser(uid):
                        return redirect_to_url(req, "%s/youraccount/login%s" % (
                            CFG_SITE_SECURE_URL,
                            make_canonical_urlargd({'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri, 'ln' : args['ln']}, {}))
                                               , norobot=True)
                    if 'atlas-gen [CERN]' not in user_info['group']:
                        return page_not_authorized(req, "../submit", text="In order to access this submission interface you need to be member of ATLAS.",
                                        navmenuid='submit')
            ## HACK END

            if doctype == "":
                catalogues_text, at_least_one_submission_authorized, submission_exists = makeCataloguesTable(req, ln=CFG_SITE_LANG)
                if not at_least_one_submission_authorized and submission_exists:

                    if isGuestUser(uid):
                        return redirect_to_url(req, "%s/youraccount/login%s" % (
                            CFG_SITE_SECURE_URL,
                            make_canonical_urlargd({'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri, 'ln' : args['ln']}, {}))
                                            , norobot=True)
                    else:

                        return page_not_authorized(req, "../submit",
                                                   uid=uid,
                                                   navmenuid='submit')
                return home(req, catalogues_text, c, ln)
            elif act == "":
                return action(req, c, ln, doctype)
            elif int(step)==0:
                return interface(req, c, ln, doctype, act, startPg, access, mainmenu, fromdir, nextPg, nbPg, curpage)
            else:
                return endaction(req, c, ln, doctype, act, startPg, access, mainmenu, fromdir, nextPg, nbPg, curpage, step, mode)

        return _index(req, **args)

    # Answer to both /submit/ and /submit
    __call__ = index


# def retrieve_most_recent_attached_file(file_path):
#     """
#     Retrieve the latest file that has been uploaded with the
#     CKEditor. This is the only way to retrieve files that the
#     CKEditor has renamed after the upload.

#     Eg: 'prefix/image.jpg' was uploaded but did already
#     exist. CKEditor silently renamed it to 'prefix/image(1).jpg':
#     >>> retrieve_most_recent_attached_file('prefix/image.jpg')
#     'prefix/image(1).jpg'
#     """
#     (base_path, filename) = os.path.split(file_path)
#     base_name = os.path.splitext(filename)[0]
#     file_ext = os.path.splitext(filename)[1][1:]
#     most_recent_filename = filename
#     i = 0
#     while True:
#         i += 1
#         possible_filename = "%s(%d).%s" % \
#                             (base_name, i, file_ext)
#         if os.path.exists(base_path + os.sep + possible_filename):
#             most_recent_filename = possible_filename
#         else:
#             break

#     return os.path.join(base_path, most_recent_filename)
