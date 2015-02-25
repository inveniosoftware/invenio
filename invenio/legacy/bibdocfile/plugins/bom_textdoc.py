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


"""BibObject Module providing BibObject prividing features for documents containing text (not necessarily as the main part of the content)"""

import os
import re
from datetime import datetime

from invenio.config import CFG_BIBINDEX_PERFORM_OCR_ON_DOCNAMES
from invenio.legacy.bibdocfile.api import BibDoc, InvenioBibDocFileError
from invenio.legacy.dbquery import run_sql
from invenio.ext.logging import register_exception

_RE_PERFORM_OCR = re.compile(CFG_BIBINDEX_PERFORM_OCR_ON_DOCNAMES)

class BibTextDoc(BibDoc):
    def get_text(self, version=None):
        """
        @param version: the requested version. If not set, the latest version
            will be used.
        @type version: integer
        @return: the textual content corresponding to the specified version
            of the document.
        @rtype: string
        """
        if version is None:
            version = self.get_latest_version()
        if self.has_text(version):
            return open(os.path.join(self.basedir, '.text;%i' % version)).read()
        else:
            return ""

    def is_ocr_required(self):
        """
        Return True if this document require OCR in order to extract text from it.
        """
        for bibrec_link in self.bibrec_links:
            if _RE_PERFORM_OCR.match(bibrec_link['docname']):
                return True
        return False

    def get_text_path(self, version=None):
        """
        @param version: the requested version. If not set, the latest version
            will be used.
        @type version: int
        @return: the full path to the textual content corresponding to the specified version
            of the document.
        @rtype: string
        """
        if version is None:
            version = self.get_latest_version()
        if self.has_text(version):
            return os.path.join(self.basedir, '.text;%i' % version)
        else:
            return ""

    def extract_text(self, version=None, perform_ocr=False, ln='en'):
        """
        Try what is necessary to extract the textual information of a document.

        @param version: the version of the document for which text is required.
            If not specified the text will be retrieved from the last version.
        @type version: integer
        @param perform_ocr: whether to perform OCR.
        @type perform_ocr: bool
        @param ln: a two letter language code to give as a hint to the OCR
            procedure.
        @type ln: string
        @raise InvenioBibDocFileError: in case of error.
        @note: the text is extracted and cached for later use. Use L{get_text}
            to retrieve it.
        """
        from invenio.legacy.websubmit.file_converter import get_best_format_to_extract_text_from, convert_file, InvenioWebSubmitFileConverterError
        if version is None:
            version = self.get_latest_version()
        docfiles = self.list_version_files(version)
        ## We try to extract text only from original or OCRed documents.
        filenames = [docfile.get_full_path() for docfile in docfiles if 'CONVERTED' not in docfile.flags or 'OCRED' in docfile.flags]
        try:
            filename = get_best_format_to_extract_text_from(filenames)
        except InvenioWebSubmitFileConverterError:
            ## We fall back on considering all the documents
            filenames = [docfile.get_full_path() for docfile in docfiles]
            try:
                filename = get_best_format_to_extract_text_from(filenames)
            except InvenioWebSubmitFileConverterError:
                open(os.path.join(self.basedir, '.text;%i' % version), 'w').write('')
                return
        try:
            convert_file(filename, os.path.join(self.basedir, '.text;%i' % version), '.txt', perform_ocr=perform_ocr, ln=ln)
            if version == self.get_latest_version():
                run_sql("UPDATE bibdoc SET text_extraction_date=NOW() WHERE id=%s", (self.id, ))
        except InvenioWebSubmitFileConverterError as e:
            register_exception(alert_admin=True, prefix="Error in extracting text from bibdoc %i, version %i" % (self.id, version))
            raise InvenioBibDocFileError, str(e)

    def pdf_a_p(self):
        """
        @return: True if this document contains a PDF in PDF/A format.
        @rtype: bool"""
        return self.has_flag('PDF/A', 'pdf')

    def has_text(self, require_up_to_date=False, version=None):
        """
        Return True if the text of this document has already been extracted.

        @param require_up_to_date: if True check the text was actually
            extracted after the most recent format of the given version.
        @type require_up_to_date: bool
        @param version: a version for which the text should have been
            extracted. If not specified the latest version is considered.
        @type version: integer
        @return: True if the text has already been extracted.
        @rtype: bool
        """
        if version is None:
            version = self.get_latest_version()
        if os.path.exists(os.path.join(self.basedir, '.text;%i' % version)):
            if not require_up_to_date:
                return True
            else:
                docfiles = self.list_version_files(version)
                text_md = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.basedir, '.text;%i' % version)))
                for docfile in docfiles:
                    if text_md <= docfile.md:
                        return False
                return True
        return False
    def __repr__(self):
        return 'BibTextDoc(%s, %s, %s)' % (repr(self.id),  repr(self.doctype), repr(self.human_readable))

def supports(doctype, extensions):
    return doctype == "Fulltext" or reduce(lambda x, y: x or y.startswith(".pdf") or y.startswith(".ps") , extensions, False)

def create_instance(docid=None, doctype='Main', human_readable=False, # pylint: disable=W0613
                    initial_data = None):
    return BibTextDoc(docid=docid, human_readable=human_readable,
                      initial_data = initial_data)
