# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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
WebDoc web interface, handling URLs such as </help/foo?ln=el>.
"""

import cgi
import os
import fcntl

from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webpage import page
from invenio.legacy.webuser import getUid, collect_user_info, page_not_authorized
from invenio.legacy.webdoc.api import get_webdoc_parts, webdoc_dirs
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.legacy.bibdocfile.api import stream_file

from invenio.utils.json import json, json_unicode_to_utf8

from invenio.modules.access.engine import acc_authorize_action


# Add here mapping to dynamic pages
# We can map any /info/some-page to a dynamic page
MAPPINGS = {}
try:
    # Adding mappings in webdoc_info_mappings overwrite Invenio default
    # ones
    from invenio.webdoc_info_mappings import MAPPINGS as EXTRA_MAPPINGS #pylint:  disable-msg=E0611
    MAPPINGS.update(EXTRA_MAPPINGS)
except ImportError:
    pass

INFO_PREFIX = webdoc_dirs["info"][0]


class WebInterfaceInfoPages(WebInterfaceDirectory):
    """Defines the set of documentation pages, usually installed under /help."""

    _exports = ['', 'manage', 'explorer']

    def __init__(self, webdocname=''):
        """Constructor."""
        self.webdocname = webdocname

    def _lookup(self, component, path):
        """This handler parses dynamic URLs."""
        key = tuple([component] + path)
        # List of dynamic mappings
        if key in MAPPINGS:
            return MAPPINGS[key](), path[-1:]

        try:
            if path[-1] != '':
                webdocname = path[-1]
                return WebInterfaceInfoPages(webdocname), []
        except IndexError:
            # First level URLs, like /info/test.webdoc
            return WebInterfaceInfoPages(component), []
        return None, []

    def __call__(self, req, form):
        """Serve webdoc page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        file_requested_ext = os.path.splitext(req.uri)
        if file_requested_ext:
            uri_parts = req.uri.split(os.sep)
            location = INFO_PREFIX + os.sep + os.sep.join(uri_parts[uri_parts.index('info') + 1:])
            # Make sure that the file to be opened is inside of the info space
            if file_in_info_space(location) and os.path.isfile(location):
                stream_file(req, location)
                return

        return display_webdoc_page(self.webdocname, categ="info", ln=argd['ln'], req=req)

    index = __call__

    def manage(self, req, form):
        """ Web interface for the management of the info space """
        uid = getUid(req)
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})

        # If it is an Ajax request, extract any JSON data.
        ajax_request = False
        if 'jsondata' in form:
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            ajax_request = True
            json_response = {}

        # Authorization.
        user_info = collect_user_info(req)
        if user_info['email'] == 'guest':
            # User is not logged in.
            if not ajax_request:
                # Do not display the introductory recID selection box to guest
                # users (as it used to be with v0.99.0):
                dummy_auth_code, auth_message = acc_authorize_action(req,
                                                                     'runinfomanager')
                referer = '/info'
                return page_not_authorized(req=req, referer=referer,
                                           text=auth_message)
            else:
                # Session has most likely timed out.
                json_response.update({'status': "timeout"})
                return json.dumps(json_response)
        # Handle request.
        if not ajax_request:
            body, errors, warnings = perform_request_init_info_interface()
            title = 'Info Space Manager'
            return page(title=title,
                        body=body,
                        errors=errors,
                        warnings=warnings,
                        uid=uid,
                        language=argd['ln'],
                        req=req)
        else:
            # Handle AJAX request.
            if json_data["action"] == "listFiles":
                json_response.update(perform_request_edit_file(json_data["filename"]))
                try:
                    return json.dumps(json_response)
                except UnicodeDecodeError:
                    # Error decoding, the file can be a pdf, image or any kind
                    # of file non-editable
                    return json.dumps({"status": "error_file_not_readable"})

            if json_data["action"] == "saveContent":
                return json.dumps(perform_request_save_file(json_data["filename"],
                                                            json_data["filecontent"]))

    def explorer(self, req, form):
        """ Handles requests from the jQuery FileTree plugin in order to return
        all filenames under the root dir (indicated in the 'dir' GET parameter)
        """
        argd = wash_urlargd(form, {'dir': (str, '')})

        root_dir = INFO_PREFIX + os.sep + argd['dir']

        file_html_list = ['<ul class="jqueryFileTree" style="display: none;">']
        try:
            file_html_list = ['<ul class="jqueryFileTree" style="display: none;">']
            for f in os.listdir(root_dir):
                ff = os.path.join(root_dir, f)
                if os.path.isdir(ff):
                    file_html_list.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (argd["dir"] + f, f))
                else:
                    e = os.path.splitext(f)[1][1:]  # get .ext and remove dot
                    file_html_list.append('<li class="file ext_%s"><a href="#" rel="%s">%s</a></li>' % (e, argd["dir"] + f, f))
            file_html_list.append('</ul>')
        except Exception, e:
            file_html_list.append('Could not load directory: %s' % str(e))

        return ''.join(file_html_list)


def display_webdoc_page(webdocname, categ="help", ln=CFG_SITE_LANG, req=None):
    """Display webdoc page WEBDOCNAME in language LN."""

    _ = gettext_set_language(ln)

    uid = getUid(req)

    # wash arguments:
    if not webdocname:
        webdocname = 'info'

    # get page parts in given language:
    if webdocname != 'contents':
        page_parts = get_webdoc_parts(webdocname, parts=['title', 'body',
                                                         'navtrail', 'lastupdated',
                                                         'description', 'keywords'],
                                      categ=categ,
                                      update_cache_mode=0,
                                      ln=CFG_SITE_LANG,
                                      req=req)
    else:
        # Print Table of Contents
        pass

    # set page title:
    page_title = page_parts.get('title', '')

    # set page navtrail:
    page_navtrail = page_parts.get('navtrail', '')

    # set page body:
    page_body = page_parts.get('body', '')
    if not page_body:
        page_body = '<p>' + (_("Sorry, page %(x_page)s does not seem to exist.",
                    x_page=('<strong>' + cgi.escape(webdocname) + '</strong>'))
            ) + '</p>'

    # set page description:
    page_description = page_parts.get('description', '')

    # set page keywords:
    page_keywords = page_parts.get('keywords', '')

    # display page:
    return page(title=page_title,
                body=page_body,
                navtrail=page_navtrail,
                description=page_description,
                keywords=page_keywords,
                uid=uid,
                language=CFG_SITE_LANG,
                req=req,
                navmenuid=categ)


###### Helper functions for web interface manager ######

def perform_request_init_info_interface():
    """ Handle initial page request to the info space manager """
    errors = []
    warnings = []
    body = ''

    # Add scripts (the ordering is NOT irrelevant).
    scripts = [
        'vendors/jquery-ui/jquery-ui.min.js',
        'vendors/json2/json2.js',
        'js/info-space-manager.js',
        'js/jqueryFileTree/jqueryFileTree.js'
    ]

    for script in scripts:
        body += '<script type="text/javascript" src="%s/%s">' \
            '</script>\n' % (CFG_SITE_URL, script)

    ckeditor_scripts = ['ckeditor.js', 'adapters/jquery.js']
    for script in ckeditor_scripts:
        body += '    <script type="text/javascript" src="%s/ckeditor/%s">' \
            '</script>\n' % (CFG_SITE_URL, script)

    body += '<link href="%s/js/jqueryFileTree/jqueryFileTree.css" rel="stylesheet" type="text/css">' % CFG_SITE_URL
    body += "<style>"
    body += """
            #InfoFilesList {
                max-width: 300px;
                margin: 20px 20px 20px 20px;
            }

            #status_msg {
                display: none;
            }

            .error {
                color: red;
            }

            .success {
                color: green;
                margin: 0 0 10px 10px;
            }
            """
    body += "</style>"

    body += '<div id="InfoFilesList"></div>'
    body += """ <div id="InfoFilesEdit">
                    <div id="status_msg"></div>
                    <div id="editor_div"></div>
                </div>
            """

    return body, errors, warnings


def perform_request_edit_file(filename):
    """ Handles the edit request of a file. Gets the file content and
    returns it inside of a textarea """
    file_path = INFO_PREFIX + filename
    response = {}
    if not file_in_info_space(file_path):
        response["status"] = "error_forbidden_path"
        return response
    try:
        file_content = open(file_path).read()
    except IOError:
        response["status"] = "error_file_not_readable"
    else:
        editor = "<textarea id='editor'>%s</textarea>" % file_content
        button_div = "<div id='button_div'><input class='formbutton' id='savebtn' type='button' value='Save changes'></div>"
        response["html_content"] = editor + button_div
    return response


def perform_request_save_file(filename, filecontent):
    """ Handles the save request for the given file name and file content

        @param filename: relative path of the file to save
        @type filename: str
        @param filecontent: content to be written in the file
        @type filecontent: str

        @return: dict with key "status", possible codes are:
            error_forbidden_path
            error_file_not_writable
            save_success
        @rtype: dict
    """
    response = {}
    file_path = INFO_PREFIX + filename
    if not file_in_info_space(file_path):
        response["status"] = "error_forbidden_path"
        return response
    try:
        file_desc = open(file_path, 'w')
        # Lock the file while writing to avoid clashes among users
        fcntl.lockf(file_desc.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            file_desc.write(filecontent)
        finally:
            fcntl.lockf(file_desc.fileno(), fcntl.LOCK_UN)
        response["status"] = "save_success"
    except IOError:
        response["status"] = "error_file_not_writable"
    return response


def file_in_info_space(location):
    """ Checks if location is under the info file system hierarchy """
    location = os.path.realpath(location)
    return location.startswith(os.path.realpath(INFO_PREFIX))
