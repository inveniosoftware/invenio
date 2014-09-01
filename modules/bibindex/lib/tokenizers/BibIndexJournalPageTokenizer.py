# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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
"""BibIndexJournalPageTokenizer: tokenizer that extracts the page range and
   the first page from the given phrase
"""

import re
from invenio.bibindex_tokenizers.BibIndexStringTokenizer import (
    BibIndexStringTokenizer
)


class BibIndexJournalPageTokenizer(BibIndexStringTokenizer):
    """ Tokenizer that extracts the page range and the first page
    """

    prefix_re = re.compile(r"^[a-z]+\.", flags=re.IGNORECASE)
    page_range_re = re.compile(r"[a-z]*\d*-[a-z]*\d*", flags=re.IGNORECASE)
    first_page_re = re.compile(r"[a-z]*\d*", flags=re.IGNORECASE)

    def tokenize(self, phrase):
        """ Returns the phrase, the page range and the first page. """
        tokens = [phrase]

        # remove the prefix, if any
        clean_phrase = self.prefix_re.sub("", phrase, count=1)

        # extract page range
        page_range_match = self.page_range_re.search(clean_phrase)
        if page_range_match:
            tokens.append(page_range_match.group())

        # extract first page
        first_page_match = self.first_page_re.search(clean_phrase)
        if first_page_match:
            tokens.append(first_page_match.group())

        # remove duplicates
        return list(set(tokens))

    def get_tokenizing_function(self, wordtable_type):
        """Picks correct tokenize function."""
        return self.tokenize
