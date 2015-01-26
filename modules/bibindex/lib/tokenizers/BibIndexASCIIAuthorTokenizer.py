# -*- coding:utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibIndexASCIIAuthorTokenizer: tokenizer introduced for author index.
   It tokenizes author name in a fuzzy way. Creates different variants of an author name.
   For example: John Cleese will be tokenized into: 'C John', 'Cleese John', 'John, C', 'John, Cleese'
   Additionally asciifies all strings.
"""

from invenio.bibindex_tokenizers.BibIndexAuthorTokenizer import BibIndexAuthorTokenizer


class BibIndexASCIIAuthorTokenizer(BibIndexAuthorTokenizer):

    """Human name tokenizer.

    Human names are divided into three classes of tokens:
    'lastnames', i.e., family, tribal or group identifiers,
    'nonlastnames', i.e., personal names distinguishing individuals,
    'titles', both incidental and permanent, e.g., 'VIII', '(ed.)', 'Msc'

    All strings are asciified.
    """

    def __init__(self, stemming_language=None, remove_stopwords=False,
                 remove_html_markup=False, remove_latex_markup=False):
        BibIndexAuthorTokenizer.__init__(self, stemming_language,
                                         remove_stopwords,
                                         remove_html_markup,
                                         remove_latex_markup,
                                         True)
