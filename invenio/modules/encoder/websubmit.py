# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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
This is an example for a WebSubmit element to upload videos to Invenio,
using BibEncode to generate preview images.

Requirements:

    Server side:
        Fully enabled BibEncode module (Codecs, FFmpeg, Mediainfo ...)
        Uploadify JQuery Plugin
            js/jquery.min.js
            js/jquery.uploadify.min.js
            js/swfobject.js

"""
import os
import pkg_resources

from invenio.modules.encoder.config import (
                    CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_DIR,
                    CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_FNAME
                    )
from invenio.config import CFG_SITE_URL, CFG_PYLIBDIR

def gcd(a,b):
    """ the euclidean algorithm """
    while a:
        a, b = b%a, a
    return b

def get_session_id(req, uid, user_info):
    """
    Returns by all means the current session id of the user.
    Raises ValueError if cannot be found
    """
    # Get the session id
    ## This can be later simplified once user_info object contain 'sid' key
    session_id = None
    try:
        try:
            from flask import session
            session_id = session.sid
        except AttributeError as e:
            # req was maybe not available (for eg. when this is run
            # through Create_Modify_Interface.py)
            session_id = user_info['session']
    except Exception as e:
        raise ValueError("Cannot retrieve user session")

    return session_id

def websubmit_singlepage(curdir, doctype, uid, access, session_id):
    """ Creates a single websubmit response element for the submission
        prototype
    """
    external_js_path = pkg_resources.resource_filename('invenio.modules.encoder', 'websubmit.js')
    external_js_fh = open(external_js_path)
    external_js = external_js_fh.read()
    external_js_fh.close()
    indir = 'running'
    ## Check if we can continue the submission because a video has allready been uploaded
    ## And a response was given by the upload handler in websubmit
    if (os.path.exists(os.path.join(curdir, 'files', str(uid), 'response', 'response'))):
        ## We need to check if the temporary video is still there or has been
        ## eaten by the garbage collector
        file_storing_path = os.path.join(curdir, "files", str(uid), "NewFile", 'filepath')
        try:
            fp = open(file_storing_path)
            fullpath = fp.read()
            fp.close()
            if os.path.exists(fullpath):
                resume = "true"
            else:
                resume = "false"
        except:
            resume = "false"
    else:
        resume = "false"
    body = form_body() % {
               'CFG_SITE_URL' : CFG_SITE_URL,
               'guidelines_url': "localhost"
               }
    javascript = form_javascript() % {
               'CFG_SITE_URL' : CFG_SITE_URL,
               'indir': indir,
               'doctype': doctype,
               'access': access,
               'key': CFG_BIBENCODE_WEBSUBMIT_ASPECT_SAMPLE_DIR,
               'uid': uid,
               'session_id': session_id,
               'resume': resume,
               'external_js': external_js
                }
    return body + javascript

def form_body():
    return """
    <link rel="stylesheet" href="%(CFG_SITE_URL)s/vendors/uploadify/uploadify.css" type="text/css" />
        <div class="websubmit_demovid_form">
            <label for="DEMOVID_TITLE">Title: </label>
            <input type="text" name="DEMOVID_TITLE" id="DEMOVID_TITLE" size="64" maxlength="50"/>

            <label for="DEMOVID_YEAR">Year: </label>
            <input type="text" name="DEMOVID_YEAR" id="DEMOVID_YEAR" size="4" maxlength="4"/>

            <label for="DEMOVID_AU">Author(s), one per line: </label>
            <textarea name="DEMOVID_AU" id="DEMOVID_AU" rows="5" cols="64"></textarea>

            <label for="DEMOVID_DESCR">Description: </label>
            <textarea name="DEMOVID_DESCR" id="DEMOVID_DESCR" rows="5" cols="64"></textarea>

            <div id="websubmit_demovid_preview" style="display: none">
                Video Preview: <br />
                <div id="websubmit_demovid_samples_wrapper">
                    <div id="websubmit_demovid_samples">
                        <!-- SAMPLE FRAMES TO BE INSERTED HERE -->
                    </div>
                </div>
                <label for="Aspect">Aspect Ratio: </label>
                <div class="websubmit_demovid_radio">
                    <input type="radio" name="Aspect" value="16:9" id="Aspect16_9" checked="checked" />
                    <label for="Aspect16_9">16:9</label>
                </div>
                <div class="websubmit_demovid_radio">
                    <input type="radio" name="Aspect" value="4:3" id="Aspect4_3" />
                    <label for="Aspect4_3">4:3</label>
                </div>
                <div class="websubmit_demovid_radio">
                    <input type="radio" name="Aspect" value="Other" id="AspectOther" />
                    <label for="AspectOther">Custom</label>
                    <div id="custom_aspect_input" style="display: inline">
                        <input type="text" id="AspectX" name="AspectX" size="2" value="" /> to
                        <input type="text" id="AspectY" name="AspectY" size="2" value="" />
                    </div>
                </div>
                <input name="DEMOVID_ASPECT" id="DEMOVID_ASPECT" type="hidden" value="">
            </div>

            <div id="websubmit_demovid_error" style="display: none">
                Your video could not be processed.
                The file might be corrupted or its codec(s) might not be supported by Invenio.
                Please verify your video or see the <a href="%(guidelines_url)s">video submission guidelines</a>.
            </div>

            <div>
                <div id="uploadify_loading"><img src="%(CFG_SITE_URL)s/img/loading.gif"/></div>
                <input type="file" size="40" id="uploadFile" name="DEMOVID_FILE"/>
            </div>
        </div>
            """

def form_javascript():
    return """
            <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/jquery/dist/jquery.min.js"></script>
            <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/uploadify/jquery.uploadify.min.js"></script>
            <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/swfobject/swfobject/swfobject.js"></script>
            <script type="text/javascript">
                var global_resume = %(resume)s;
                var global_site_url = "%(CFG_SITE_URL)s";
                var global_indir = "%(indir)s";
                var global_doctype = "%(doctype)s";
                var global_access = "%(access)s";
                var global_uid = "%(uid)s";
                var global_session_id = "%(session_id)s";
                var global_key = "%(key)s";
                %(external_js)s
            </script>
            """
