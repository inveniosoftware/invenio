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
"""BibIndexAuthorCountTokenizer: counts number of authors for any publication
   given by recID. Will look at tags: '100_a' and '700_a' which are:
   'first author name' and 'additional author name'.
"""

from invenio.legacy.bibindex.engine_utils import get_field_count
from invenio.modules.indexer.tokenizers.BibIndexMultiFieldTokenizer import BibIndexMultiFieldTokenizer


class BibIndexAuthorCountTokenizer(BibIndexMultiFieldTokenizer):
    """
        Returns a number of authors who created a publication
        with given recID in the database.

        Takes recID of the record as an argument to tokenizing function.
        Calculates terms based on information from multiple tags.
        For more information on this type of tokenizers take a look on
        BibIndexAuthorCountTokenizer base class.
    """

    def __init__(self, stemming_language = None, remove_stopwords = False, remove_html_markup = False, remove_latex_markup = False):
        self.tags = ['100__a', '700__a']


    def tokenize(self, recID):
        """Uses get_field_count from bibindex.engine_utils
           for finding a number of authors of a publication and pass it in the list"""
        return [str(get_field_count(recID, self.tags)),]


    def get_tokenizing_function(self, wordtable_type):
        return self.tokenize
