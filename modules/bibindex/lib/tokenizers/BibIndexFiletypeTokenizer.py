# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013, 2014 CERN.
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
"""BibIndexFiletypeTokenizer: 'tokenizes' for file extensions.
   Tokenizer is adapted to work with bibfield and its get_record function.
"""


from invenio.bibindex_tokenizers.BibIndexRecJsonTokenizer import BibIndexRecJsonTokenizer


class BibIndexFiletypeTokenizer(BibIndexRecJsonTokenizer):

    """
        Tokenizes for file extensions.
        Tokenizer is adapted to work with bibfield and its get_record function.

        It accepts as an input a record created by a get_record function:

        from bibfield import get_record
        record16 = get_record(16)
        tokenizer = BibIndexFiletypeTokenizer()
        new_words = tokenizer.tokenize(record16)
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        pass

    def tokenize(self, record):
        """'record' is a recjson record from bibfield.

           Function uses derived field 'filetypes'
           from the record.

           @param urls: recjson record
        """
        values = []
        try:
            if record.has_key('filetypes'):
                values = record['filetypes']
        except KeyError:
            pass
        except TypeError:
            return []
        return values

    def tokenize_for_words(self, record):
        return self.tokenize(record)

    def tokenize_for_pairs(self, record):
        return self.tokenize(record)

    def tokenize_for_phrases(self, record):
        return self.tokenize(record)

    def get_tokenizing_function(self, wordtable_type):
        return self.tokenize
