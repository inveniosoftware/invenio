# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from fixture import DataSet
from invenio.websearch_fixtures import FieldData


class IdxINDEXData(DataSet):

    class IdxINDEX_1:
        last_updated = None
        description = u'This index contains words/phrases from global fields.'
        stemming_language = u''
        id = 1
        indexer = u'native'
        name = u'global'

    class IdxINDEX_2:
        last_updated = None
        description = u'This index contains words/phrases from collection identifiers fields.'
        stemming_language = u''
        id = 2
        indexer = u'native'
        name = u'collection'

    class IdxINDEX_3:
        last_updated = None
        description = u'This index contains words/phrases from abstract fields.'
        stemming_language = u''
        id = 3
        indexer = u'native'
        name = u'abstract'

    class IdxINDEX_4:
        last_updated = None
        description = u'This index contains fuzzy words/phrases from author fields.'
        stemming_language = u''
        id = 4
        indexer = u'native'
        name = u'author'

    class IdxINDEX_5:
        last_updated = None
        description = u'This index contains words/phrases from keyword fields.'
        stemming_language = u''
        id = 5
        indexer = u'native'
        name = u'keyword'

    class IdxINDEX_6:
        last_updated = None
        description = u'This index contains words/phrases from references fields.'
        stemming_language = u''
        id = 6
        indexer = u'native'
        name = u'reference'

    class IdxINDEX_7:
        last_updated = None
        description = u'This index contains words/phrases from report numbers fields.'
        stemming_language = u''
        id = 7
        indexer = u'native'
        name = u'reportnumber'

    class IdxINDEX_8:
        last_updated = None
        description = u'This index contains words/phrases from title fields.'
        stemming_language = u''
        id = 8
        indexer = u'native'
        name = u'title'

    class IdxINDEX_9:
        last_updated = None
        description = u'This index contains words/phrases from fulltext fields.'
        stemming_language = u''
        id = 9
        indexer = u'native'
        name = u'fulltext'

    class IdxINDEX_10:
        last_updated = None
        description = u'This index contains words/phrases from year fields.'
        stemming_language = u''
        id = 10
        indexer = u'native'
        name = u'year'

    class IdxINDEX_11:
        last_updated = None
        description = u'This index contains words/phrases from journal publication information fields.'
        stemming_language = u''
        id = 11
        indexer = u'native'
        name = u'journal'

    class IdxINDEX_12:
        last_updated = None
        description = u'This index contains words/phrases from collaboration name fields.'
        stemming_language = u''
        id = 12
        indexer = u'native'
        name = u'collaboration'

    class IdxINDEX_13:
        last_updated = None
        description = u'This index contains words/phrases from institutional affiliation fields.'
        stemming_language = u''
        id = 13
        indexer = u'native'
        name = u'affiliation'

    class IdxINDEX_14:
        last_updated = None
        description = u'This index contains exact words/phrases from author fields.'
        stemming_language = u''
        id = 14
        indexer = u'native'
        name = u'exactauthor'

    class IdxINDEX_15:
        last_updated = None
        description = u'This index contains exact words/phrases from figure captions.'
        stemming_language = u''
        id = 15
        indexer = u'native'
        name = u'caption'

    class IdxINDEX_16:
        last_updated = None
        description = u'This index contains fuzzy words/phrases from first author field.'
        stemming_language = u''
        id = 16
        indexer = u'native'
        name = u'firstauthor'

    class IdxINDEX_17:
        last_updated = None
        description = u'This index contains exact words/phrases from first author field.'
        stemming_language = u''
        id = 17
        indexer = u'native'
        name = u'exactfirstauthor'

    class IdxINDEX_18:
        last_updated = None
        description = u'This index contains number of authors of the record.'
        stemming_language = u''
        id = 18
        indexer = u'native'
        name = u'authorcount'

    class IdxINDEX_19:
        last_updated = None
        description = u'This index contains exact words/phrases from title fields.'
        stemming_language = u''
        id = 19
        indexer = u'native'
        name = u'exacttitle'


class IdxINDEXFieldData(DataSet):

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