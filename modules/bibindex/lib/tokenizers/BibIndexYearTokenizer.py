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
"""BibIndexYearTokenizer: useful for year index. Extracts words (year) from date tags.
"""

from invenio.config import \
    CFG_INSPIRE_SITE
from invenio.bibindex_tokenizers.BibIndexDefaultTokenizer import BibIndexDefaultTokenizer


class BibIndexYearTokenizer(BibIndexDefaultTokenizer):

    """
       Year tokenizer. It tokenizes words from date tags or uses default word tokenizer.
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        BibIndexDefaultTokenizer.__init__(self, stemming_language,
                                          remove_stopwords,
                                          remove_html_markup,
                                          remove_latex_markup)

    def get_words_from_date_tag(self, datestring):
        """
        Special procedure to index words from tags storing date-like
        information in format YYYY or YYYY-MM or YYYY-MM-DD.  Namely, we
        are indexing word-terms YYYY, YYYY-MM, YYYY-MM-DD, but never
        standalone MM or DD.
        """
        out = []
        for dateword in datestring.split():
            # maybe there are whitespaces, so break these too
            out.append(dateword)
            parts = dateword.split('-')
            for nb in range(1, len(parts)):
                out.append("-".join(parts[:nb]))
        return out

    def tokenize_for_words_default(self, phrase):
        """Default tokenize_for_words inherited from default tokenizer"""
        return super(BibIndexYearTokenizer, self).tokenize_for_words(phrase)

    def tokenize_for_words(self, phrase):
        """
            If CFG_INSPIRE_SITE is 1 we perform special tokenization which relies on getting words form date tag.
            In other case we perform default tokenization.
        """
        if CFG_INSPIRE_SITE:
            return self.get_words_from_date_tag(phrase)
        else:
            return self.tokenize_for_words_default(phrase)
