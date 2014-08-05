# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
from invenio.bibindex_tokenizers.BibIndexFilteringTokenizer import (
    BibIndexFilteringTokenizer,
)
from invenio.bibfield import get_record


class BibIndexDOITokenizer(BibIndexFilteringTokenizer):

    """
        Filtering tokenizer which tokenizes DOI tag (0247_a)
        only if "0247_2" tag is present and its value equals "DOI"
        and 909C4a tag without any constraints.
    """

    def __init__(self, stemming_language=None, remove_stopwords=False,
                 remove_html_markup=False, remove_latex_markup=False):
        self.rules = (('0247_a', '2', 'DOI'), ('909C4a', '', ''))

    def get_tokenizing_function(self, wordtable_type):
        """Returns proper tokenizing function"""
        return self.tokenize

    def tokenize_via_recjson(self, recID):
        """
        Nonmarc version of tokenize function for DOI.
        Note: with nonmarc we don't need to filter anymore.
        We just need to take value from record because we
        use bibfield here.
        """
        rec = get_record(recID)
        values = rec.get('doi', [])
        return values

    def get_nonmarc_tokenizing_function(self, table_type):
        """
        Returns proper tokenizing function for non-marc records.
        """
        return self.tokenize_via_recjson
