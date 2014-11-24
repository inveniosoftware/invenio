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
    Abstract BibIndexStringTokenizer.
    It is a tokenizer created only for inheritance.
    All string based tokenizers should inherit after this tokenizer.
"""

from invenio.bibindex_tokenizers.BibIndexTokenizer import BibIndexTokenizer


class BibIndexStringTokenizer(BibIndexTokenizer):

    """
       BibIndexStringTokenizer is an abstract tokenizer.
       It should be used only for inheritance.

       This tokenizer should be a base class for tokenizers
       which operates on strings/phrases and splits them
       into multiple terms/tokens.

       Tokenizing functions take phrase as an argument.

       Good examples of StringTokenizer is DeafultTokenizer.
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

    def tokenize_for_words(self, phrase):
        raise NotImplementedError

    def tokenize_for_pairs(self, phrase):
        raise NotImplementedError

    def tokenize_for_phrases(self, phrase):
        raise NotImplementedError
