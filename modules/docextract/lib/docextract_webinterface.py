    # -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""DocExtract REST and Web API

Exposes document extration facilities to the world
"""

from tempfile import NamedTemporaryFile

from invenio.webinterface_handler import WebInterfaceDirectory
from invenio.webuser import collect_user_info
from invenio.webpage import page
from invenio.config import CFG_TMPSHAREDDIR, CFG_ETCDIR
from invenio.refextract_api import extract_references_from_file_xml, \
                                   extract_references_from_url_xml, \
                                   extract_references_from_string_xml
from invenio.bibformat_engine import format_record

try:
    from invenio.config import CFG_INSPIRE_SITE
except ImportError:
    CFG_INSPIRE_SITE = False


def check_login(req):
    """Check that the user is logged in"""
    user_info = collect_user_info(req)
    if user_info['email'] == 'guest':
        # 1. User is guest: must login prior to upload
        # return 'Please login before uploading file.'
        pass


def check_url(url):
    """Check that the url we received is not gibberish"""
    return not url.startswith('http://') and \
           not url.startswith('https://') and \
           not url.startswith('ftp://')


def extract_from_pdf_string(pdf, inspire=CFG_INSPIRE_SITE):
    """Extract references from a pdf stored in a string

    Given a string representing a pdf, this function writes the string to
    disk and passes it to refextract.
    We need to create a temoporary file because we need to run pdf2text on it"""
    # Save new record to file
    tf = NamedTemporaryFile(prefix='docextract-pdf',
                            dir=CFG_TMPSHAREDDIR)
    try:
        tf.write(pdf)
        tf.flush()
        refs = extract_references_from_file_xml(tf.name, inspire=inspire)
    finally:
        # Also deletes the file
        tf.close()

    return refs


def make_arxiv_url(arxiv_id):
    """Make a url we can use to download a pdf from arxiv

    Arguments:
    arxiv_id -- the arxiv id of the record to link to
    """
    return "http://arxiv.org/pdf/%s.pdf" % arxiv_id


class WebInterfaceAPIDocExtract(WebInterfaceDirectory):
    """DocExtract REST API"""
    _exports = [
        ('extract-references-pdf', 'extract_references_pdf'),
        ('extract-references-pdf-url', 'extract_references_pdf_url'),
        ('extract-references-txt', 'extract_references_txt'),
    ]

    def extract_references_pdf(self, req, form):
        """Extract references from uploaded pdf"""
        check_login(req)

        if 'pdf' not in form:
            return 'No PDF file uploaded'

        return extract_from_pdf_string(form['pdf'].file.read())

    def extract_references_pdf_url(self, req, form):
        """Extract references from the pdf pointed by the passed url"""
        check_login(req)

        if 'url' not in form:
            return 'No URL specified'

        url = form['url'].value

        if not check_url(url):
            return 'Invalid URL specified'

        return extract_references_from_url_xml(url)

    def extract_references_txt(self, req, form):
        """Extract references from plain text"""
        check_login(req)

        if 'txt' not in form:
            return 'No text specified'

        txt = form['txt'].value

        return extract_references_from_string_xml(txt)


class WebInterfaceDocExtract(WebInterfaceDirectory):
    """DocExtract API"""
    _exports = ['api',
        ('extract-references', 'extract_references'),
        ('example.pdf', 'example_pdf'),
    ]

    api = WebInterfaceAPIDocExtract()

    def example_pdf(self, _req, _form):
        """Serve a test pdf for tests"""
        f = open("%s/docextract/example.pdf" % CFG_ETCDIR, 'rb')
        try:
            return f.read()
        finally:
            f.close()

    def extract_references_template(self):
        """Template for reference extraction page"""
        return """Please specify a pdf or a url or some references to parse

        <form action="extract-references" method="post"
                                            enctype="multipart/form-data">
            <p>PDF: <input type="file" name="pdf" /></p>
            <p>arXiv: <input type="text" name="arxiv" /></p>
            <p>URL: <input type="text" name="url" style="width: 600px;"/></p>
            <textarea name="txt" style="width: 500px; height: 500px;"></textarea>
            <p><input type="submit" /></p>
        </form>
        """

    def extract_references(self, req, form):
        """Refrences extraction page

        This page can be used for authors to test their pdfs against our
        refrences extraction process"""
        user_info = collect_user_info(req)

        # Handle the 3 POST parameters
        if 'pdf' in form and form['pdf'].value:
            pdf = form['pdf'].value
            references_xml = extract_from_pdf_string(pdf)
        elif 'arxiv' in form and form['arxiv'].value:
            url = make_arxiv_url(arxiv_id=form['arxiv'].value)
            references_xml = extract_references_from_url_xml(url)
        elif 'url' in form and form['url'].value:
            url = form['url'].value
            references_xml = extract_references_from_url_xml(url)
        elif 'txt' in form and form['txt'].value:
            txt = form['txt'].value
            references_xml = extract_references_from_string_xml(txt)
        else:
            references_xml = None

        # If we have not uploaded anything yet
        # Display the form that allows us to do so
        if not references_xml:
            out = self.extract_references_template()
        else:
            out = """
            <style type="text/css">
                #referenceinp_link { display: none; }
            </style>
            """
            out += format_record(0,
                                'hdref',
                                xml_record=references_xml.encode('utf-8'),
                                user_info=user_info)

        # Render the page (including header, footer)
        return page(title='References Extractor',
                    body=out,
                    uid=user_info['uid'],
                    req=req)
