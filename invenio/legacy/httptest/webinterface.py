# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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
HTTP Test web interface. This is the place where to put helpers for
regression tests related to HTTP (or WSGI or SSO).
"""

__revision__ = \
     "$Id$"

__lastupdated__ = """$Date$"""

import cgi

from six import iteritems

from invenio.config import CFG_SITE_URL, CFG_TMPDIR
from invenio.legacy.webpage import page
from invenio.ext.legacy.handler import WebInterfaceDirectory, wash_urlargd
from invenio.utils.url import redirect_to_url

class WebInterfaceHTTPTestPages(WebInterfaceDirectory):
    _exports = ["", "post1", "post2", "sso", "dumpreq", "complexpost", "whatismyip", "oraclefriendly"]

    def __call__(self, req, form):
        redirect_to_url(req, CFG_SITE_URL + '/httptest/post1')

    index = __call__

    def _lookup(self, component, path):
        if component == 'hello':
            name = '/'.join(path)
            def hello(req, form):
                return "Hello %s!" % name
            return hello, []
        return None, []

    def sso(self, req, form):
        """ For testing single sign-on """
        req.add_common_vars()
        sso_env = {}
        for var, value in iteritems(req.subprocess_env):
            if var.startswith('HTTP_ADFS_'):
                sso_env[var] = value
        out = "<html><head><title>SSO test</title></head>"
        out += "<body><table>"
        for var, value in iteritems(sso_env):
            out += "<tr><td><strong>%s</strong></td><td>%s</td></tr>" % (var, value)
        out += "</table></body></html>"
        return out

    def dumpreq(self, req, form):
        """
        Dump a textual representation of the request object.
        """
        return "<pre>%s</pre>" % cgi.escape(str(req))

    def post1(self, req, form):
        """
        This is used by WSGI regression test, to test if it's possible
        to upload a file and retrieve it correctly.
        """
        if req.method == 'POST':
            if 'file' in form:
                for row in form['file']:#.file:
                    req.write(row)
            return ''
        else:
            body = """
<form method="post" enctype="multipart/form-data">
<input type="file" name="file" />
<input type="submit" />
</form>"""
        return page("test1", body=body, req=req)

    def post2(self, req, form):
        """
        This is to test L{handle_file_post} function.
        """
        from invenio.legacy.wsgi.utils import handle_file_post
        from invenio.legacy.bibdocfile.api import stream_file
        argd = wash_urlargd(form, {"save": (str, "")})
        if req.method != 'POST':
            body = """<p>Please send a file via POST.</p>"""
            return page("test2", body=body, req=req)
        path, mimetype = handle_file_post(req)
        if argd['save'] and argd['save'].startswith(CFG_TMPDIR):
            open(argd['save'], "w").write(open(path).read())
        return stream_file(req, path, mime=mimetype)

    def oraclefriendly(self, req, form):
        """
        This specifically for batchuploader with the oracle-friendly patch
        """
        from invenio.legacy.wsgi.utils import handle_file_post
        from invenio.legacy.bibdocfile.api import stream_file
        argd = wash_urlargd(form, {"save": (str, ""), "results": (str, "")})
        if req.method != 'POST':
            body = """<p>Please send a FORM via POST.</p>"""
            return page("test2", body=body, req=req)
        if argd['save'] and argd['save'].startswith(CFG_TMPDIR):
            open(argd['save'], "w").write(argd['results'])
        return argd['results']

    def complexpost(self, req, form):
        body = """
            <form action="/httptest/dumpreq" method="POST">
                A file: <input name="file1" type="file" /><br />
                Another file: <input name="file2" type="file" /><br />
                <select name="cars" multiple="multiple">
                    <option value="volvo">Volvo</option>
                    <option value="saab">Saab</option>
                    <option value="fiat" selected="selected">Fiat</option>
                    <option value="audi">Audi</option>
                </select>
                <input type="submit" />
            </form>"""
        return page("Complex POST", body=body, req=req)

    def whatismyip(self, req, form):
        """
        Return the client IP as seen by the server (useful for testing e.g. Robot authentication)
        """
        req.content_type = "text/plain"
        return req.remote_ip
