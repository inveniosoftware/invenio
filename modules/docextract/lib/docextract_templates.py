# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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


"""DocExtract templates for the web API"""


class Template(object):

    def tmpl_web_form(self):
        """Template for extraction page"""
        return """
        <style type="text/css">
            #extract_form input.urlinput { width: 600px; }
            #extract_form textarea { width: 500px; height: 500px; }
        </style>

        <p>Please specify a pdf or a url or some references to parse</p>

        <form action="" method="post" id="extract_form"
              enctype="multipart/form-data">
            <p>PDF: <input type="file" name="pdf" /></p>
            <p>arXiv: <input type="text" name="arxiv" /></p>
            <p>URL: <input type="text" name="url" class="urlinput" /></p>
            <textarea name="txt"></textarea>
            <p><input type="submit" /></p>
        </form>
        """

    def tmpl_web_result(self, references_html):
        """Template header for extraction page result"""
        out = """
        <style type="text/css">
            #referenceinp_link { display: none; }
        </style>
        """
        return out + references_html
