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
"""
    BibIndexMultiFieldTokenizer.
    Base class for tokenizers that work on more than one field
    and possibly on more than one phrase at a time.
"""

from invenio.bibindex_tokenizers.BibIndexTokenizer import BibIndexTokenizer


class BibIndexMultiFieldTokenizer(BibIndexTokenizer):

    """
       BibIndexMultiFieldTokenizer is an abstract tokenizer.
       It should be used only for inheritance.

       This tokenizer should be a base class for more complicated
       tokenizers which tokenizing functions perform calculations
       on per record basis and NOT per string basis (look for
       BibIndexDefaultTokenizer if you want to know more about the
       latter type of tokenization).

       Tokenizing functions take as an argument recID of the record
       we want to perform calculations on.
       Example:

       class BibIndexComplicatedTokenizer(BibIndexMultiFieldTokenizer):
            (...)
       recID = 10
       a = BibIndexComplicatedTokenizer()
       res = a.tokenize_for_words(recID)

       Good examples of MultiFieldTokenizer are JournalTokenizer and
       AuthorCountTokenizer.
       Both return results after processing more than one field/tag
       of the record (for more information check these tokenizers).

    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        """@param stemming_language: dummy
           @param remove_stopwords: dummy
           @param remove_html_markup: dummy
           @param remove_latex_markup: dummy
        """
        pass

    def get_tokenizing_function(self, wordtable_type):
        """Picks correct tokenize_for_xxx function depending on type of tokenization (wordtable_type)"""
        raise NotImplementedError

    def tokenize_for_words(self, recid):
        raise NotImplementedError

    def tokenize_for_pairs(self, recid):
        raise NotImplementedError

    def tokenize_for_phrases(self, recid):
        raise NotImplementedError
