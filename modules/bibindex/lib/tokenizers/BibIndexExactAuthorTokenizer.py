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
"""BibIndexExactAuthorTokenizer: performs only washing on author name and leaves it alone
   in the same form.
"""

from invenio.bibindex_engine_washer import wash_author_name
from invenio.bibindex_tokenizers.BibIndexDefaultTokenizer import BibIndexDefaultTokenizer


class BibIndexExactAuthorTokenizer(BibIndexDefaultTokenizer):

    """
    Human name exact tokenizer.
    Old: BibIndexExactNameTokenizer
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        BibIndexDefaultTokenizer.__init__(self, stemming_language,
                                          remove_stopwords,
                                          remove_html_markup,
                                          remove_latex_markup)

    def tokenize_for_phrases(self, s):
        """
        Returns washed autor name.
        """
        return [wash_author_name(s)]
