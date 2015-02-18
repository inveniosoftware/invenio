# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""Indexer fixtures."""

from fixture import DataSet

from invenio.modules.search.fixtures import FieldData


class IdxINDEXData(DataSet):

    """Indexer data."""

    class IdxINDEX_1:
        last_updated = None
        description = u'This index contains words/phrases from global fields.'
        stemming_language = u''
        id = 1
        indexer = u'native'
        name = u'global'
        synonym_kbrs = u'INDEX-SYNONYM-TITLE,exact'
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_2:
        last_updated = None
        description = u'This index contains words/phrases from collection identifiers fields.'
        stemming_language = u''
        id = 2
        indexer = u'native'
        name = u'collection'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_3:
        last_updated = None
        description = u'This index contains words/phrases from abstract fields.'
        stemming_language = u''
        id = 3
        indexer = u'native'
        name = u'abstract'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_4:
        last_updated = None
        description = u'This index contains fuzzy words/phrases from author fields.'
        stemming_language = u''
        id = 4
        indexer = u'native'
        name = u'author'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexAuthorTokenizer'

    class IdxINDEX_5:
        last_updated = None
        description = u'This index contains words/phrases from keyword fields.'
        stemming_language = u''
        id = 5
        indexer = u'native'
        name = u'keyword'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_6:
        last_updated = None
        description = u'This index contains words/phrases from references fields.'
        stemming_language = u''
        id = 6
        indexer = u'native'
        name = u'reference'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_7:
        last_updated = None
        description = u'This index contains words/phrases from report numbers fields.'
        stemming_language = u''
        id = 7
        indexer = u'native'
        name = u'reportnumber'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_8:
        last_updated = None
        description = u'This index contains words/phrases from title fields.'
        stemming_language = u''
        id = 8
        indexer = u'native'
        name = u'title'
        synonym_kbrs = u'INDEX-SYNONYM-TITLE,exact'
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_9:
        last_updated = None
        description = u'This index contains words/phrases from fulltext fields.'
        stemming_language = u''
        id = 9
        indexer = u'native'
        name = u'fulltext'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexFulltextTokenizer'

    class IdxINDEX_10:
        last_updated = None
        description = u'This index contains words/phrases from year fields.'
        stemming_language = u''
        id = 10
        indexer = u'native'
        name = u'year'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexYearTokenizer'

    class IdxINDEX_11:
        last_updated = None
        description = u'This index contains words/phrases from journal publication information fields.'
        stemming_language = u''
        id = 11
        indexer = u'native'
        name = u'journal'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexJournalTokenizer'

    class IdxINDEX_12:
        last_updated = None
        description = u'This index contains words/phrases from collaboration name fields.'
        stemming_language = u''
        id = 12
        indexer = u'native'
        name = u'collaboration'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_13:
        last_updated = None
        description = u'This index contains words/phrases from affiliation fields.'
        stemming_language = u''
        id = 13
        indexer = u'native'
        name = u'affiliation'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_14:
        last_updated = None
        description = u'This index contains exact words/phrases from author fields.'
        stemming_language = u''
        id = 14
        indexer = u'native'
        name = u'exactauthor'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_15:
        last_updated = None
        description = u'This index contains exact words/phrases from figure captions.'
        stemming_language = u''
        id = 15
        indexer = u'native'
        name = u'caption'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_16:
        last_updated = None
        description = u'This index contains fuzzy words/phrases from first author field.'
        stemming_language = u''
        id = 16
        indexer = u'native'
        name = u'firstauthor'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexAuthorTokenizer'

    class IdxINDEX_17:
        last_updated = None
        description = u'This index contains exact words/phrases from first author field.'
        stemming_language = u''
        id = 17
        indexer = u'native'
        name = u'exactfirstauthor'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexExactAuthorTokenizer'

    class IdxINDEX_18:
        last_updated = None
        description = u'This index contains number of authors of the record.'
        stemming_language = u''
        id = 18
        indexer = u'native'
        name = u'authorcount'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexAuthorCountTokenizer'

    class IdxINDEX_19:
        last_updated = None
        description = u'This index contains exact words/phrases from title fields.'
        stemming_language = u''
        id = 19
        indexer = u'native'
        name = u'exacttitle'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_20:
        last_updated = None
        description = u'This index contains words/phrases from author authority records.'
        stemming_language = u''
        id = 20
        indexer = u'native'
        name = u'authorityauthor'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexAuthorTokenizer'

    class IdxINDEX_21:
        last_updated = None
        description = u'This index contains words/phrases from institute authority records.'
        stemming_language = u''
        id = 21
        indexer = u'native'
        name = u'authorityinstitute'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_22:
        last_updated = None
        description = u'This index contains words/phrases from journal authority records.'
        stemming_language = u''
        id = 22
        indexer = u'native'
        name = u'authorityjournal'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_23:
        last_updated = None
        description = u'This index contains words/phrases from subject authority records.'
        stemming_language = u''
        id = 23
        indexer = u'native'
        name = u'authoritysubject'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'

    class IdxINDEX_24:
        last_updated = None
        description = u'This index contains number of copies of items in the library.'
        stemming_language = u''
        id = 24
        indexer = u'native'
        name = u'itemcount'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexItemCountTokenizer'

    class IdxINDEX_25:
        last_updated = None
        description = u'This index contains extensions of files connected to records.'
        stemming_language = u''
        id = 25
        indexer = u'native'
        name = u'filetype'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexFiletypeTokenizer'

    class IdxINDEX_26:
        last_updated = None
        description = u'This index contains words/phrases from miscellaneous fields.'
        stemming_language = u''
        id = 26
        indexer = u'native'
        name = u'miscellaneous'
        synonym_kbrs = u''
        remove_stopwords = u'No'
        remove_html_markup = u'No'
        remove_latex_markup = u'No'
        tokenizer = u'BibIndexDefaultTokenizer'


class IdxINDEXFieldData(DataSet):

    """IdxINDEXField Data."""

    class IdxINDEXField_10_12:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_10.ref('id')
        id_field = FieldData.Field_12.ref('id')

    class IdxINDEXField_11_19:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_11.ref('id')
        id_field = FieldData.Field_19.ref('id')

    class IdxINDEXField_12_20:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_12.ref('id')
        id_field = FieldData.Field_20.ref('id')

    class IdxINDEXField_13_21:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_13.ref('id')
        id_field = FieldData.Field_21.ref('id')

    class IdxINDEXField_14_22:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_14.ref('id')
        id_field = FieldData.Field_22.ref('id')

    class IdxINDEXField_15_27:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_15.ref('id')
        id_field = FieldData.Field_27.ref('id')

    class IdxINDEXField_16_28:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_16.ref('id')
        id_field = FieldData.Field_28.ref('id')

    class IdxINDEXField_17_29:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_17.ref('id')
        id_field = FieldData.Field_29.ref('id')

    class IdxINDEXField_18_30:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_18.ref('id')
        id_field = FieldData.Field_30.ref('id')

    class IdxINDEXField_19_32:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_19.ref('id')
        id_field = FieldData.Field_32.ref('id')

    class IdxINDEXField_1_1:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_1.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class IdxINDEXField_2_10:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_2.ref('id')
        id_field = FieldData.Field_10.ref('id')

    class IdxINDEXField_3_4:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_3.ref('id')
        id_field = FieldData.Field_4.ref('id')

    class IdxINDEXField_4_3:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_4.ref('id')
        id_field = FieldData.Field_3.ref('id')

    class IdxINDEXField_5_5:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_5.ref('id')
        id_field = FieldData.Field_5.ref('id')

    class IdxINDEXField_6_8:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_6.ref('id')
        id_field = FieldData.Field_8.ref('id')

    class IdxINDEXField_7_6:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_7.ref('id')
        id_field = FieldData.Field_6.ref('id')

    class IdxINDEXField_8_2:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_8.ref('id')
        id_field = FieldData.Field_2.ref('id')

    class IdxINDEXField_9_9:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_9.ref('id')
        id_field = FieldData.Field_9.ref('id')

    class IdxINDEXField_20_33:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_20.ref('id')
        id_field = FieldData.Field_33.ref('id')

    class IdxINDEXField_21_34:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_21.ref('id')
        id_field = FieldData.Field_34.ref('id')

    class IdxINDEXField_22_35:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_22.ref('id')
        id_field = FieldData.Field_35.ref('id')

    class IdxINDEXField_23_36:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_23.ref('id')
        id_field = FieldData.Field_36.ref('id')

    class IdxINDEXField_24_37:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_24.ref('id')
        id_field = FieldData.Field_37.ref('id')

    class IdxINDEXField_25_38:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_25.ref('id')
        id_field = FieldData.Field_38.ref('id')

    class IdxINDEXField_26_39:
        regexp_alphanumeric_separators = u''
        regexp_punctuation = u'[.,:;?!"]'
        id_idxINDEX = IdxINDEXData.IdxINDEX_26.ref('id')
        id_field = FieldData.Field_39.ref('id')


class IdxINDEXIdxINDEXData(DataSet):

    """IdxINDEXIdxINDEX Data."""

    class IdxINDEXIdxINDEX_1_2:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_2

    class IdxINDEXIdxINDEX_1_3:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_3

    class IdxINDEXIdxINDEX_1_5:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_5

    class IdxINDEXIdxINDEX_1_7:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_7

    class IdxINDEXIdxINDEX_1_8:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_8

    class IdxINDEXIdxINDEX_1_10:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_10

    class IdxINDEXIdxINDEX_1_11:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_11

    class IdxINDEXIdxINDEX_1_12:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_12

    class IdxINDEXIdxINDEX_1_13:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_13

    class IdxINDEXIdxINDEX_1_19:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_19

    class IdxINDEXIdxINDEX_1_26:
        virtual = IdxINDEXData.IdxINDEX_1
        normal = IdxINDEXData.IdxINDEX_26

__all__ = ('IdxINDEXData', 'IdxINDEXFieldData', 'IdxINDEXIdxINDEXData')
