# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
    BibIndexRecJsonTokenizer.
    It's an abstract class created only for inheritance purposes.

    Tokenizers which are based on RecJsonTokenizer use bibfield/JsonAlchemy records.
    Logic of the tokenization process is in the functions of bibfield module.
    Tokenizer itself should perform only necessary post-processing.
"""


from invenio.bibindex_tokenizers.BibIndexTokenizer import BibIndexTokenizer


class BibIndexRecJsonTokenizer(BibIndexTokenizer):

    """
        BibIndexRecJsonTokenizer is an abstract tokenizer.
        It should be used only for inheritance.

        It should be a base class for all tokenizers which need to use
        bibfield/JsonAlchemy records.

        Tokenizing function of RecJsonTokenizer takes a bibfield record
        as an argument.
        Main logic of tokenization process stays in bibfield record's
        functions. Tokenizing functions of all tokenizers inheriting after
        RecJsonTokenizer should only do post-processing tasks.

        For example of use please check: BibIndexFiletypeTokenizer
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        pass

    def tokenize(self, record):
        """'record' is a recjson record from bibfield module
           @param urls: recjson record
        """
        raise NotImplementedError

    def get_tokenizing_function(self, wordtable_type):
        raise NotImplementedError

    def tokenize_for_words(self, recid):
        raise NotImplementedError

    def tokenize_for_pairs(self, recid):
        raise NotImplementedError

    def tokenize_for_phrases(self, recid):
        raise NotImplementedError
