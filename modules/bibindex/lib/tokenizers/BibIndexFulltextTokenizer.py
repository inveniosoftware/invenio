# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2014 CERN.
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
"""BibIndexFulltextTokenizer: extracts words form a given document.
   Document is given by its URL.
"""

import os
import sys
import logging
import urllib2
import re


from invenio.config import \
    CFG_SOLR_URL, \
     CFG_XAPIAN_ENABLED, \
     CFG_BIBINDEX_FULLTEXT_INDEX_LOCAL_FILES_ONLY, \
     CFG_BIBINDEX_SPLASH_PAGES
from invenio.htmlutils import get_links_in_html_page
from invenio.websubmit_file_converter import convert_file, get_file_converter_logger
from invenio.solrutils_bibindex_indexer import solr_add_fulltext
from invenio.xapianutils_bibindex_indexer import xapian_add
from invenio.bibdocfile import bibdocfile_url_p, \
    bibdocfile_url_to_bibdoc, download_url, \
     BibRecDocs, InvenioBibDocFileError
from invenio.bibindex_engine_utils import get_idx_indexer
from invenio.bibtask import write_message
from invenio.errorlib import register_exception
from invenio.intbitset import intbitset
from invenio.bibindex_tokenizers.BibIndexDefaultTokenizer import BibIndexDefaultTokenizer


fulltext_added = intbitset()
                           # stores ids of records whose fulltexts have been
                           # added


class BibIndexFulltextTokenizer(BibIndexDefaultTokenizer):

    """
        Exctracts all the words contained in document specified by url.
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        self.verbose = 3
        BibIndexDefaultTokenizer.__init__(self, stemming_language,
                                          remove_stopwords,
                                          remove_html_markup,
                                          remove_latex_markup)

    def set_verbose(self, verbose):
        """Allows to change verbosity level during indexing"""
        self.verbose = verbose

    def tokenize_for_words_default(self, phrase):
        """Default tokenize_for_words inherited from default tokenizer"""
        return super(BibIndexFulltextTokenizer, self).tokenize_for_words(phrase)

    def get_words_from_fulltext(self, url_direct_or_indirect):
        """Returns all the words contained in the document specified by
           URL_DIRECT_OR_INDIRECT with the words being split by various
           SRE_SEPARATORS regexp set earlier.  If FORCE_FILE_EXTENSION is
           set (e.g. to "pdf", then treat URL_DIRECT_OR_INDIRECT as a PDF
           file.  (This is interesting to index Indico for example.)  Note
           also that URL_DIRECT_OR_INDIRECT may be either a direct URL to
           the fulltext file or an URL to a setlink-like page body that
           presents the links to be indexed.  In the latter case the
           URL_DIRECT_OR_INDIRECT is parsed to extract actual direct URLs
           to fulltext documents, for all knows file extensions as
           specified by global CONV_PROGRAMS config variable.
        """
        write_message("... reading fulltext files from %s started" %
                      url_direct_or_indirect, verbose=2)
        try:
            if bibdocfile_url_p(url_direct_or_indirect):
                write_message("... %s is an internal document" %
                              url_direct_or_indirect, verbose=2)
                try:
                    bibdoc = bibdocfile_url_to_bibdoc(url_direct_or_indirect)
                except InvenioBibDocFileError:
                    # Outdated 8564 tag
                    return []
                indexer = get_idx_indexer('fulltext')
                if indexer != 'native':
                    # A document might belong to multiple records
                    for rec_link in bibdoc.bibrec_links:
                        recid = rec_link["recid"]
                        # Adds fulltexts of all files once per records
                        if not recid in fulltext_added:
                            bibrecdocs = BibRecDocs(recid)
                            try:
                                text = bibrecdocs.get_text()
                            except InvenioBibDocFileError:
                                # Invalid PDF
                                continue
                            if indexer == 'SOLR' and CFG_SOLR_URL:
                                solr_add_fulltext(recid, text)
                            elif indexer == 'XAPIAN' and CFG_XAPIAN_ENABLED:
                                xapian_add(recid, 'fulltext', text)

                        fulltext_added.add(recid)
                    # we are relying on an external information retrieval system
                    # to provide full-text indexing, so dispatch text to it and
                    # return nothing here:
                    return []
                else:
                    text = ""
                    if hasattr(bibdoc, "get_text"):
                        text = bibdoc.get_text()
                    return self.tokenize_for_words_default(text)
            else:
                if CFG_BIBINDEX_FULLTEXT_INDEX_LOCAL_FILES_ONLY:
                    write_message("... %s is external URL but indexing only local files" %
                                  url_direct_or_indirect, verbose=2)
                    return []
                write_message("... %s is an external URL" %
                              url_direct_or_indirect, verbose=2)
                urls_to_index = set()
                for splash_re, url_re in CFG_BIBINDEX_SPLASH_PAGES.iteritems():
                    if re.match(splash_re, url_direct_or_indirect):
                        write_message("... %s is a splash page (%s)" %
                                      (url_direct_or_indirect, splash_re), verbose=2)
                        html = urllib2.urlopen(url_direct_or_indirect).read()
                        urls = get_links_in_html_page(html)
                        write_message("... found these URLs in %s splash page: %s" %
                                      (url_direct_or_indirect, ", ".join(urls)), verbose=3)
                        for url in urls:
                            if re.match(url_re, url):
                                write_message(
                                    "... will index %s (matched by %s)" % (url, url_re), verbose=2)
                                urls_to_index.add(url)
                if not urls_to_index:
                    urls_to_index.add(url_direct_or_indirect)
                write_message("... will extract words from %s" %
                              ', '.join(urls_to_index), verbose=2)
                words = {}
                for url in urls_to_index:
                    tmpdoc = download_url(url)
                    file_converter_logger = get_file_converter_logger()
                    old_logging_level = file_converter_logger.getEffectiveLevel(
                    )
                    if self.verbose > 3:
                        file_converter_logger.setLevel(logging.DEBUG)
                    try:
                        try:
                            tmptext = convert_file(
                                tmpdoc, output_format='.txt')
                            text = open(tmptext).read()
                            os.remove(tmptext)

                            indexer = get_idx_indexer('fulltext')
                            if indexer != 'native':
                                if indexer == 'SOLR' and CFG_SOLR_URL:
                                    solr_add_fulltext(
                                        None, text)  # FIXME: use real record ID
                                if indexer == 'XAPIAN' and CFG_XAPIAN_ENABLED:
                                    # xapian_add(None, 'fulltext', text) #
                                    # FIXME: use real record ID
                                    pass
                                # we are relying on an external information retrieval system
                                # to provide full-text indexing, so dispatch text to it and
                                # return nothing here:
                                tmpwords = []
                            else:
                                tmpwords = self.tokenize_for_words_default(
                                    text)
                            words.update(dict(map(lambda x: (x, 1), tmpwords)))
                        except Exception, e:
                            message = 'ERROR: it\'s impossible to correctly extract words from %s referenced by %s: %s' % (
                                url, url_direct_or_indirect, e)
                            register_exception(
                                prefix=message, alert_admin=True)
                            write_message(message, stream=sys.stderr)
                    finally:
                        os.remove(tmpdoc)
                        if self.verbose > 3:
                            file_converter_logger.setLevel(old_logging_level)
                return words.keys()
        except Exception, e:
            message = 'ERROR: it\'s impossible to correctly extract words from %s: %s' % (
                url_direct_or_indirect, e)
            register_exception(prefix=message, alert_admin=True)
            write_message(message, stream=sys.stderr)
            return []

    def tokenize_for_words(self, phrase):
        return self.get_words_from_fulltext(phrase)

    def tokenize_for_pairs(self, phrase):
        return []

    def tokenize_for_phrases(self, phrase):
        return []
