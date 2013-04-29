# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from invenio.config import CFG_SITE_NAME
from fixture import DataSet


class CollectionData(DataSet):

    class siteCollection:
        id = 1
        name = CFG_SITE_NAME
        dbquery = None


class FieldData(DataSet):

    class Field_1:
        code = u'anyfield'
        id = 1
        name = u'any field'

    class Field_2:
        code = u'title'
        id = 2
        name = u'title'

    class Field_3:
        code = u'author'
        id = 3
        name = u'author'

    class Field_4:
        code = u'abstract'
        id = 4
        name = u'abstract'

    class Field_5:
        code = u'keyword'
        id = 5
        name = u'keyword'

    class Field_6:
        code = u'reportnumber'
        id = 6
        name = u'report number'

    class Field_7:
        code = u'subject'
        id = 7
        name = u'subject'

    class Field_8:
        code = u'reference'
        id = 8
        name = u'reference'

    class Field_9:
        code = u'fulltext'
        id = 9
        name = u'fulltext'

    class Field_10:
        code = u'collection'
        id = 10
        name = u'collection'

    class Field_11:
        code = u'division'
        id = 11
        name = u'division'

    class Field_12:
        code = u'year'
        id = 12
        name = u'year'

    class Field_13:
        code = u'experiment'
        id = 13
        name = u'experiment'

    class Field_14:
        code = u'recid'
        id = 14
        name = u'record ID'

    class Field_15:
        code = u'isbn'
        id = 15
        name = u'isbn'

    class Field_16:
        code = u'issn'
        id = 16
        name = u'issn'

    class Field_17:
        code = u'coden'
        id = 17
        name = u'coden'

    #class Field_18:
    #    code = u'doi'
    #    id = 18
    #    name = u'doi'

    class Field_19:
        code = u'journal'
        id = 19
        name = u'journal'

    class Field_20:
        code = u'collaboration'
        id = 20
        name = u'collaboration'

    class Field_21:
        code = u'affiliation'
        id = 21
        name = u'affiliation'

    class Field_22:
        code = u'exactauthor'
        id = 22
        name = u'exact author'

    class Field_23:
        code = u'datecreated'
        id = 23
        name = u'date created'

    class Field_24:
        code = u'datemodified'
        id = 24
        name = u'date modified'

    class Field_25:
        code = u'refersto'
        id = 25
        name = u'refers to'

    class Field_26:
        code = u'citedby'
        id = 26
        name = u'cited by'

    class Field_27:
        code = u'caption'
        id = 27
        name = u'caption'

    class Field_28:
        code = u'firstauthor'
        id = 28
        name = u'first author'

    class Field_29:
        code = u'exactfirstauthor'
        id = 29
        name = u'exact first author'

    class Field_30:
        code = u'authorcount'
        id = 30
        name = u'author count'

    class Field_31:
        code = u'rawref'
        id = 31
        name = u'reference to'

    class Field_32:
        code = u'exacttitle'
        id = 32
        name = u'exact title'


class TagData(DataSet):

    class Tag_1:
        id = 1
        value = u'100__a'
        name = u'first author name'

    class Tag_2:
        id = 2
        value = u'700__a'
        name = u'additional author name'

    class Tag_3:
        id = 3
        value = u'245__%'
        name = u'main title'

    class Tag_4:
        id = 4
        value = u'246__%'
        name = u'additional title'

    class Tag_5:
        id = 5
        value = u'520__%'
        name = u'abstract'

    class Tag_6:
        id = 6
        value = u'6531_a'
        name = u'keyword'

    class Tag_7:
        id = 7
        value = u'037__a'
        name = u'primary report number'

    class Tag_8:
        id = 8
        value = u'088__a'
        name = u'additional report number'

    class Tag_9:
        id = 9
        value = u'909C0r'
        name = u'added report number'

    class Tag_10:
        id = 10
        value = u'999C5%'
        name = u'reference'

    class Tag_11:
        id = 11
        value = u'980__%'
        name = u'collection identifier'

    class Tag_12:
        id = 12
        value = u'65017a'
        name = u'main subject'

    class Tag_13:
        id = 13
        value = u'65027a'
        name = u'additional subject'

    class Tag_14:
        id = 14
        value = u'909C0p'
        name = u'division'

    class Tag_15:
        id = 15
        value = u'909C0y'
        name = u'year'

    class Tag_16:
        id = 16
        value = u'00%'
        name = u'00x'

    class Tag_17:
        id = 17
        value = u'01%'
        name = u'01x'

    class Tag_18:
        id = 18
        value = u'02%'
        name = u'02x'

    class Tag_19:
        id = 19
        value = u'03%'
        name = u'03x'

    class Tag_20:
        id = 20
        value = u'04%'
        name = u'lang'

    class Tag_21:
        id = 21
        value = u'05%'
        name = u'05x'

    class Tag_22:
        id = 22
        value = u'06%'
        name = u'06x'

    class Tag_23:
        id = 23
        value = u'07%'
        name = u'07x'

    class Tag_24:
        id = 24
        value = u'08%'
        name = u'08x'

    class Tag_25:
        id = 25
        value = u'09%'
        name = u'09x'

    class Tag_26:
        id = 26
        value = u'10%'
        name = u'10x'

    class Tag_27:
        id = 27
        value = u'11%'
        name = u'11x'

    class Tag_28:
        id = 28
        value = u'12%'
        name = u'12x'

    class Tag_29:
        id = 29
        value = u'13%'
        name = u'13x'

    class Tag_30:
        id = 30
        value = u'14%'
        name = u'14x'

    class Tag_31:
        id = 31
        value = u'15%'
        name = u'15x'

    class Tag_32:
        id = 32
        value = u'16%'
        name = u'16x'

    class Tag_33:
        id = 33
        value = u'17%'
        name = u'17x'

    class Tag_34:
        id = 34
        value = u'18%'
        name = u'18x'

    class Tag_35:
        id = 35
        value = u'19%'
        name = u'19x'

    class Tag_36:
        id = 36
        value = u'20%'
        name = u'20x'

    class Tag_37:
        id = 37
        value = u'21%'
        name = u'21x'

    class Tag_38:
        id = 38
        value = u'22%'
        name = u'22x'

    class Tag_39:
        id = 39
        value = u'23%'
        name = u'23x'

    class Tag_40:
        id = 40
        value = u'24%'
        name = u'24x'

    class Tag_41:
        id = 41
        value = u'25%'
        name = u'25x'

    class Tag_42:
        id = 42
        value = u'26%'
        name = u'internal'

    class Tag_43:
        id = 43
        value = u'27%'
        name = u'27x'

    class Tag_44:
        id = 44
        value = u'28%'
        name = u'28x'

    class Tag_45:
        id = 45
        value = u'29%'
        name = u'29x'

    class Tag_46:
        id = 46
        value = u'30%'
        name = u'pages'

    class Tag_47:
        id = 47
        value = u'31%'
        name = u'31x'

    class Tag_48:
        id = 48
        value = u'32%'
        name = u'32x'

    class Tag_49:
        id = 49
        value = u'33%'
        name = u'33x'

    class Tag_50:
        id = 50
        value = u'34%'
        name = u'34x'

    class Tag_51:
        id = 51
        value = u'35%'
        name = u'35x'

    class Tag_52:
        id = 52
        value = u'36%'
        name = u'36x'

    class Tag_53:
        id = 53
        value = u'37%'
        name = u'37x'

    class Tag_54:
        id = 54
        value = u'38%'
        name = u'38x'

    class Tag_55:
        id = 55
        value = u'39%'
        name = u'39x'

    class Tag_56:
        id = 56
        value = u'40%'
        name = u'40x'

    class Tag_57:
        id = 57
        value = u'41%'
        name = u'41x'

    class Tag_58:
        id = 58
        value = u'42%'
        name = u'42x'

    class Tag_59:
        id = 59
        value = u'43%'
        name = u'43x'

    class Tag_60:
        id = 60
        value = u'44%'
        name = u'44x'

    class Tag_61:
        id = 61
        value = u'45%'
        name = u'45x'

    class Tag_62:
        id = 62
        value = u'46%'
        name = u'46x'

    class Tag_63:
        id = 63
        value = u'47%'
        name = u'47x'

    class Tag_64:
        id = 64
        value = u'48%'
        name = u'48x'

    class Tag_65:
        id = 65
        value = u'49%'
        name = u'series'

    class Tag_66:
        id = 66
        value = u'50%'
        name = u'50x'

    class Tag_67:
        id = 67
        value = u'51%'
        name = u'51x'

    class Tag_68:
        id = 68
        value = u'52%'
        name = u'52x'

    class Tag_69:
        id = 69
        value = u'53%'
        name = u'53x'

    class Tag_70:
        id = 70
        value = u'54%'
        name = u'54x'

    class Tag_71:
        id = 71
        value = u'55%'
        name = u'55x'

    class Tag_72:
        id = 72
        value = u'56%'
        name = u'56x'

    class Tag_73:
        id = 73
        value = u'57%'
        name = u'57x'

    class Tag_74:
        id = 74
        value = u'58%'
        name = u'58x'

    class Tag_75:
        id = 75
        value = u'59%'
        name = u'summary'

    class Tag_76:
        id = 76
        value = u'60%'
        name = u'60x'

    class Tag_77:
        id = 77
        value = u'61%'
        name = u'61x'

    class Tag_78:
        id = 78
        value = u'62%'
        name = u'62x'

    class Tag_79:
        id = 79
        value = u'63%'
        name = u'63x'

    class Tag_80:
        id = 80
        value = u'64%'
        name = u'64x'

    class Tag_81:
        id = 81
        value = u'65%'
        name = u'65x'

    class Tag_82:
        id = 82
        value = u'66%'
        name = u'66x'

    class Tag_83:
        id = 83
        value = u'67%'
        name = u'67x'

    class Tag_84:
        id = 84
        value = u'68%'
        name = u'68x'

    class Tag_85:
        id = 85
        value = u'69%'
        name = u'subject'

    class Tag_86:
        id = 86
        value = u'70%'
        name = u'70x'

    class Tag_87:
        id = 87
        value = u'71%'
        name = u'71x'

    class Tag_88:
        id = 88
        value = u'72%'
        name = u'author-ad'

    class Tag_89:
        id = 89
        value = u'73%'
        name = u'73x'

    class Tag_90:
        id = 90
        value = u'74%'
        name = u'74x'

    class Tag_91:
        id = 91
        value = u'75%'
        name = u'75x'

    class Tag_92:
        id = 92
        value = u'76%'
        name = u'76x'

    class Tag_93:
        id = 93
        value = u'77%'
        name = u'77x'

    class Tag_94:
        id = 94
        value = u'78%'
        name = u'78x'

    class Tag_95:
        id = 95
        value = u'79%'
        name = u'79x'

    class Tag_96:
        id = 96
        value = u'80%'
        name = u'80x'

    class Tag_97:
        id = 97
        value = u'81%'
        name = u'81x'

    class Tag_98:
        id = 98
        value = u'82%'
        name = u'82x'

    class Tag_99:
        id = 99
        value = u'83%'
        name = u'83x'

    class Tag_100:
        id = 100
        value = u'84%'
        name = u'84x'

    class Tag_101:
        id = 101
        value = u'85%'
        name = u'electr'

    class Tag_102:
        id = 102
        value = u'86%'
        name = u'86x'

    class Tag_103:
        id = 103
        value = u'87%'
        name = u'87x'

    class Tag_104:
        id = 104
        value = u'88%'
        name = u'88x'

    class Tag_105:
        id = 105
        value = u'89%'
        name = u'89x'

    class Tag_106:
        id = 106
        value = u'90%'
        name = u'publication'

    class Tag_107:
        id = 107
        value = u'91%'
        name = u'pub-conf-cit'

    class Tag_108:
        id = 108
        value = u'92%'
        name = u'92x'

    class Tag_109:
        id = 109
        value = u'93%'
        name = u'93x'

    class Tag_110:
        id = 110
        value = u'94%'
        name = u'94x'

    class Tag_111:
        id = 111
        value = u'95%'
        name = u'95x'

    class Tag_112:
        id = 112
        value = u'96%'
        name = u'catinfo'

    class Tag_113:
        id = 113
        value = u'97%'
        name = u'97x'

    class Tag_114:
        id = 114
        value = u'98%'
        name = u'98x'

    class Tag_115:
        id = 115
        value = u'8564_u'
        name = u'url'

    class Tag_116:
        id = 116
        value = u'909C0e'
        name = u'experiment'

    class Tag_117:
        id = 117
        value = u'001'
        name = u'record ID'

    class Tag_118:
        id = 118
        value = u'020__a'
        name = u'isbn'

    class Tag_119:
        id = 119
        value = u'022__a'
        name = u'issn'

    class Tag_120:
        id = 120
        value = u'030__a'
        name = u'coden'

    class Tag_121:
        id = 121
        value = u'909C4a'
        name = u'doi'

    class Tag_122:
        id = 122
        value = u'850%'
        name = u'850x'

    class Tag_123:
        id = 123
        value = u'851%'
        name = u'851x'

    class Tag_124:
        id = 124
        value = u'852%'
        name = u'852x'

    class Tag_125:
        id = 125
        value = u'853%'
        name = u'853x'

    class Tag_126:
        id = 126
        value = u'854%'
        name = u'854x'

    class Tag_127:
        id = 127
        value = u'855%'
        name = u'855x'

    class Tag_128:
        id = 128
        value = u'857%'
        name = u'857x'

    class Tag_129:
        id = 129
        value = u'858%'
        name = u'858x'

    class Tag_130:
        id = 130
        value = u'859%'
        name = u'859x'

    class Tag_131:
        id = 131
        value = u'909C4%'
        name = u'journal'

    class Tag_132:
        id = 132
        value = u'710__g'
        name = u'collaboration'

    class Tag_133:
        id = 133
        value = u'100__u'
        name = u'first author affiliation'

    class Tag_134:
        id = 134
        value = u'700__u'
        name = u'additional author affiliation'

    class Tag_135:
        id = 135
        value = u'8564_y'
        name = u'caption'

    class Tag_136:
        id = 136
        value = u'909C4c'
        name = u'journal page'

    class Tag_137:
        id = 137
        value = u'909C4p'
        name = u'journal title'

    class Tag_138:
        id = 138
        value = u'909C4v'
        name = u'journal volume'

    class Tag_139:
        id = 139
        value = u'909C4y'
        name = u'journal year'

    class Tag_140:
        id = 140
        value = u'500__a'
        name = u'comment'

    class Tag_141:
        id = 141
        value = u'245__a'
        name = u'title'

    class Tag_142:
        id = 142
        value = u'245__a'
        name = u'main abstract'

    class Tag_143:
        id = 143
        value = u'595__a'
        name = u'internal notes'

    class Tag_144:
        id = 144
        value = u'787%'
        name = u'other relationship entry'


class FormatData(DataSet):

    class Format_1:
        code = u'hb'
        last_updated = None
        description = u'HTML brief output format, used for search results pages.'
        content_type = u'text/html'
        id = 1
        visibility = 1
        name = u'HTML brief'

    class Format_2:
        code = u'hd'
        last_updated = None
        description = u'HTML detailed output format, used for Detailed record pages.'
        content_type = u'text/html'
        id = 2
        visibility = 1
        name = u'HTML detailed'

    class Format_3:
        code = u'hm'
        last_updated = None
        description = u'HTML MARC.'
        content_type = u'text/html'
        id = 3
        visibility = 1
        name = u'MARC'

    class Format_4:
        code = u'xd'
        last_updated = None
        description = u'XML Dublin Core.'
        content_type = u'text/xml'
        id = 4
        visibility = 1
        name = u'Dublin Core'

    class Format_5:
        code = u'xm'
        last_updated = None
        description = u'XML MARC.'
        content_type = u'text/xml'
        id = 5
        visibility = 1
        name = u'MARCXML'

    class Format_6:
        code = u'hp'
        last_updated = None
        description = u'HTML portfolio-style output format for photos.'
        content_type = u'text/html'
        id = 6
        visibility = 1
        name = u'portfolio'

    class Format_7:
        code = u'hc'
        last_updated = None
        description = u'HTML caption-only output format for photos.'
        content_type = u'text/html'
        id = 7
        visibility = 1
        name = u'photo captions only'

    class Format_8:
        code = u'hx'
        last_updated = None
        description = u'BibTeX.'
        content_type = u'text/html'
        id = 8
        visibility = 1
        name = u'BibTeX'

    class Format_9:
        code = u'xe'
        last_updated = None
        description = u'XML EndNote.'
        content_type = u'text/xml'
        id = 9
        visibility = 1
        name = u'EndNote'

    class Format_10:
        code = u'xn'
        last_updated = None
        description = u'XML NLM.'
        content_type = u'text/xml'
        id = 10
        visibility = 1
        name = u'NLM'

    class Format_11:
        code = u'excel'
        last_updated = None
        description = u'Excel csv output'
        content_type = u'application/ms-excel'
        id = 11
        visibility = 0
        name = u'Excel'

    class Format_12:
        code = u'hs'
        last_updated = None
        description = u'Very short HTML output for similarity box (<i>people also viewed..</i>).'
        content_type = u'text/html'
        id = 12
        visibility = 0
        name = u'HTML similarity'

    class Format_13:
        code = u'xr'
        last_updated = None
        description = u'RSS.'
        content_type = u'text/xml'
        id = 13
        visibility = 0
        name = u'RSS'

    class Format_14:
        code = u'xoaidc'
        last_updated = None
        description = u'OAI DC.'
        content_type = u'text/xml'
        id = 14
        visibility = 0
        name = u'OAI DC'

    class Format_15:
        code = u'hdfile'
        last_updated = None
        description = u'Used to show fulltext files in mini-panel of detailed record pages.'
        content_type = u'text/html'
        id = 15
        visibility = 0
        name = u'File mini-panel'

    class Format_16:
        code = u'hdact'
        last_updated = None
        description = u'Used to display actions in mini-panel of detailed record pages.'
        content_type = u'text/html'
        id = 16
        visibility = 0
        name = u'Actions mini-panel'

    class Format_17:
        code = u'hdref'
        last_updated = None
        description = u'Display record references in References tab.'
        content_type = u'text/html'
        id = 17
        visibility = 0
        name = u'References tab'

    class Format_18:
        code = u'hcs'
        last_updated = None
        description = u'HTML cite summary format, used for search results pages.'
        content_type = u'text/html'
        id = 18
        visibility = 1
        name = u'HTML citesummary'

    class Format_19:
        code = u'xw'
        last_updated = None
        description = u'RefWorks.'
        content_type = u'text/xml'
        id = 19
        visibility = 1
        name = u'RefWorks'

    class Format_20:
        code = u'xo'
        last_updated = None
        description = u'Metadata Object Description Schema'
        content_type = u'application/xml'
        id = 20
        visibility = 1
        name = u'MODS'

    class Format_21:
        code = u'ha'
        last_updated = None
        description = u'Very brief HTML output format for author/paper claiming facility.'
        content_type = u'text/html'
        id = 21
        visibility = 0
        name = u'HTML author claiming'

    class Format_22:
        code = u'xp'
        last_updated = None
        description = u'Sample format suitable for multimedia feeds, such as podcasts'
        content_type = u'application/rss+xml'
        id = 22
        visibility = 0
        name = u'Podcast'

    class Format_23:
        code = u'wapaff'
        last_updated = None
        description = u'cPickled dicts'
        content_type = u'text'
        id = 23
        visibility = 0
        name = u'WebAuthorProfile affiliations helper'

    class Format_24:
        code = u'xe8x'
        last_updated = None
        description = u'XML EndNote (8-X).'
        content_type = u'text/xml'
        id = 24
        visibility = 1
        name = u'EndNote (8-X)'

    class Format_25:
        code = u'hcs2'
        last_updated = None
        description = u'HTML cite summary format, including self-citations counts.'
        content_type = u'text/html'
        id = 25
        visibility = 0
        name = u'HTML citesummary extended'

    class Format_26:
        code = u'dcite'
        last_updated = None
        description = u'DataCite XML format.'
        content_type = u'text/xml'
        id = 26
        visibility = 0
        name = u'DataCite'


class FieldTagData(DataSet):

    class FieldTag_10_11:
        score = 100
        id_tag = TagData.Tag_11.ref('id')
        id_field = FieldData.Field_10.ref('id')

    class FieldTag_11_14:
        score = 100
        id_tag = TagData.Tag_14.ref('id')
        id_field = FieldData.Field_11.ref('id')

    class FieldTag_12_15:
        score = 10
        id_tag = TagData.Tag_15.ref('id')
        id_field = FieldData.Field_12.ref('id')

    class FieldTag_13_116:
        score = 10
        id_tag = TagData.Tag_116.ref('id')
        id_field = FieldData.Field_13.ref('id')

    class FieldTag_14_117:
        score = 100
        id_tag = TagData.Tag_117.ref('id')
        id_field = FieldData.Field_14.ref('id')

    class FieldTag_15_118:
        score = 100
        id_tag = TagData.Tag_118.ref('id')
        id_field = FieldData.Field_15.ref('id')

    class FieldTag_16_119:
        score = 100
        id_tag = TagData.Tag_119.ref('id')
        id_field = FieldData.Field_16.ref('id')

    class FieldTag_17_120:
        score = 100
        id_tag = TagData.Tag_120.ref('id')
        id_field = FieldData.Field_17.ref('id')

    #class FieldTag_18_120:
    #    score = 100
    #    id_tag = TagData.Tag_121.ref('id')
    #    id_field = FieldData.Field_18.ref('id')

    class FieldTag_19_131:
        score = 100
        id_tag = TagData.Tag_131.ref('id')
        id_field = FieldData.Field_19.ref('id')

    class FieldTag_1_100:
        score = 10
        id_tag = TagData.Tag_100.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_102:
        score = 10
        id_tag = TagData.Tag_102.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_103:
        score = 10
        id_tag = TagData.Tag_103.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_104:
        score = 10
        id_tag = TagData.Tag_104.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_105:
        score = 10
        id_tag = TagData.Tag_105.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_106:
        score = 10
        id_tag = TagData.Tag_106.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_107:
        score = 10
        id_tag = TagData.Tag_107.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_108:
        score = 10
        id_tag = TagData.Tag_108.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_109:
        score = 10
        id_tag = TagData.Tag_109.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_110:
        score = 10
        id_tag = TagData.Tag_110.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_111:
        score = 10
        id_tag = TagData.Tag_111.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_112:
        score = 10
        id_tag = TagData.Tag_112.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_113:
        score = 10
        id_tag = TagData.Tag_113.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_114:
        score = 10
        id_tag = TagData.Tag_114.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_122:
        score = 10
        id_tag = TagData.Tag_122.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_123:
        score = 10
        id_tag = TagData.Tag_123.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_124:
        score = 10
        id_tag = TagData.Tag_124.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_125:
        score = 10
        id_tag = TagData.Tag_125.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_126:
        score = 10
        id_tag = TagData.Tag_126.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_127:
        score = 10
        id_tag = TagData.Tag_127.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_128:
        score = 10
        id_tag = TagData.Tag_128.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_129:
        score = 10
        id_tag = TagData.Tag_129.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_130:
        score = 10
        id_tag = TagData.Tag_130.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_16:
        score = 10
        id_tag = TagData.Tag_16.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_17:
        score = 10
        id_tag = TagData.Tag_17.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_18:
        score = 10
        id_tag = TagData.Tag_18.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_19:
        score = 10
        id_tag = TagData.Tag_19.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_20:
        score = 10
        id_tag = TagData.Tag_20.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_21:
        score = 10
        id_tag = TagData.Tag_21.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_22:
        score = 10
        id_tag = TagData.Tag_22.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_23:
        score = 10
        id_tag = TagData.Tag_23.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_24:
        score = 10
        id_tag = TagData.Tag_24.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_25:
        score = 10
        id_tag = TagData.Tag_25.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_26:
        score = 10
        id_tag = TagData.Tag_26.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_27:
        score = 10
        id_tag = TagData.Tag_27.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_28:
        score = 10
        id_tag = TagData.Tag_28.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_29:
        score = 10
        id_tag = TagData.Tag_29.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_30:
        score = 10
        id_tag = TagData.Tag_30.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_31:
        score = 10
        id_tag = TagData.Tag_31.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_32:
        score = 10
        id_tag = TagData.Tag_32.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_33:
        score = 10
        id_tag = TagData.Tag_33.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_34:
        score = 10
        id_tag = TagData.Tag_34.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_35:
        score = 10
        id_tag = TagData.Tag_35.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_36:
        score = 10
        id_tag = TagData.Tag_36.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_37:
        score = 10
        id_tag = TagData.Tag_37.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_38:
        score = 10
        id_tag = TagData.Tag_38.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_39:
        score = 10
        id_tag = TagData.Tag_39.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_40:
        score = 10
        id_tag = TagData.Tag_40.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_41:
        score = 10
        id_tag = TagData.Tag_41.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_42:
        score = 10
        id_tag = TagData.Tag_42.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_43:
        score = 10
        id_tag = TagData.Tag_43.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_44:
        score = 10
        id_tag = TagData.Tag_44.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_45:
        score = 10
        id_tag = TagData.Tag_45.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_46:
        score = 10
        id_tag = TagData.Tag_46.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_47:
        score = 10
        id_tag = TagData.Tag_47.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_48:
        score = 10
        id_tag = TagData.Tag_48.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_49:
        score = 10
        id_tag = TagData.Tag_49.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_50:
        score = 10
        id_tag = TagData.Tag_50.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_51:
        score = 10
        id_tag = TagData.Tag_51.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_52:
        score = 10
        id_tag = TagData.Tag_52.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_53:
        score = 10
        id_tag = TagData.Tag_53.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_54:
        score = 10
        id_tag = TagData.Tag_54.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_55:
        score = 10
        id_tag = TagData.Tag_55.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_56:
        score = 10
        id_tag = TagData.Tag_56.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_57:
        score = 10
        id_tag = TagData.Tag_57.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_58:
        score = 10
        id_tag = TagData.Tag_58.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_59:
        score = 10
        id_tag = TagData.Tag_59.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_60:
        score = 10
        id_tag = TagData.Tag_60.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_61:
        score = 10
        id_tag = TagData.Tag_61.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_62:
        score = 10
        id_tag = TagData.Tag_62.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_63:
        score = 10
        id_tag = TagData.Tag_63.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_64:
        score = 10
        id_tag = TagData.Tag_64.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_65:
        score = 10
        id_tag = TagData.Tag_65.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_66:
        score = 10
        id_tag = TagData.Tag_66.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_67:
        score = 10
        id_tag = TagData.Tag_67.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_68:
        score = 10
        id_tag = TagData.Tag_68.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_69:
        score = 10
        id_tag = TagData.Tag_69.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_70:
        score = 10
        id_tag = TagData.Tag_70.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_71:
        score = 10
        id_tag = TagData.Tag_71.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_72:
        score = 10
        id_tag = TagData.Tag_72.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_73:
        score = 10
        id_tag = TagData.Tag_73.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_74:
        score = 10
        id_tag = TagData.Tag_74.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_75:
        score = 10
        id_tag = TagData.Tag_75.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_76:
        score = 10
        id_tag = TagData.Tag_76.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_77:
        score = 10
        id_tag = TagData.Tag_77.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_78:
        score = 10
        id_tag = TagData.Tag_78.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_79:
        score = 10
        id_tag = TagData.Tag_79.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_80:
        score = 10
        id_tag = TagData.Tag_80.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_81:
        score = 10
        id_tag = TagData.Tag_81.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_82:
        score = 10
        id_tag = TagData.Tag_82.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_83:
        score = 10
        id_tag = TagData.Tag_83.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_84:
        score = 10
        id_tag = TagData.Tag_84.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_85:
        score = 10
        id_tag = TagData.Tag_85.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_86:
        score = 10
        id_tag = TagData.Tag_86.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_87:
        score = 10
        id_tag = TagData.Tag_87.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_88:
        score = 10
        id_tag = TagData.Tag_88.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_89:
        score = 10
        id_tag = TagData.Tag_89.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_90:
        score = 10
        id_tag = TagData.Tag_90.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_91:
        score = 10
        id_tag = TagData.Tag_91.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_92:
        score = 10
        id_tag = TagData.Tag_92.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_93:
        score = 10
        id_tag = TagData.Tag_93.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_94:
        score = 10
        id_tag = TagData.Tag_94.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_95:
        score = 10
        id_tag = TagData.Tag_95.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_96:
        score = 10
        id_tag = TagData.Tag_96.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_97:
        score = 10
        id_tag = TagData.Tag_97.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_98:
        score = 10
        id_tag = TagData.Tag_98.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_1_99:
        score = 10
        id_tag = TagData.Tag_99.ref('id')
        id_field = FieldData.Field_1.ref('id')

    class FieldTag_20_132:
        score = 100
        id_tag = TagData.Tag_132.ref('id')
        id_field = FieldData.Field_20.ref('id')

    class FieldTag_21_133:
        score = 100
        id_tag = TagData.Tag_133.ref('id')
        id_field = FieldData.Field_21.ref('id')

    class FieldTag_21_134:
        score = 90
        id_tag = TagData.Tag_134.ref('id')
        id_field = FieldData.Field_21.ref('id')

    class FieldTag_22_1:
        score = 100
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_22.ref('id')

    class FieldTag_22_2:
        score = 90
        id_tag = TagData.Tag_2.ref('id')
        id_field = FieldData.Field_22.ref('id')

    class FieldTag_27_135:
        score = 100
        id_tag = TagData.Tag_135.ref('id')
        id_field = FieldData.Field_27.ref('id')

    class FieldTag_28_1:
        score = 100
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_28.ref('id')

    class FieldTag_29_1:
        score = 100
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_29.ref('id')

    class FieldTag_2_3:
        score = 100
        id_tag = TagData.Tag_3.ref('id')
        id_field = FieldData.Field_2.ref('id')

    class FieldTag_2_4:
        score = 90
        id_tag = TagData.Tag_4.ref('id')
        id_field = FieldData.Field_2.ref('id')

    class FieldTag_30_1:
        score = 100
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_30.ref('id')

    class FieldTag_30_2:
        score = 90
        id_tag = TagData.Tag_2.ref('id')
        id_field = FieldData.Field_30.ref('id')

    class FieldTag_32_3:
        score = 100
        id_tag = TagData.Tag_3.ref('id')
        id_field = FieldData.Field_32.ref('id')

    class FieldTag_32_4:
        score = 90
        id_tag = TagData.Tag_4.ref('id')
        id_field = FieldData.Field_32.ref('id')

    class FieldTag_3_1:
        score = 100
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_3.ref('id')

    class FieldTag_3_2:
        score = 90
        id_tag = TagData.Tag_2.ref('id')
        id_field = FieldData.Field_3.ref('id')

    class FieldTag_4_5:
        score = 100
        id_tag = TagData.Tag_5.ref('id')
        id_field = FieldData.Field_4.ref('id')

    class FieldTag_5_6:
        score = 100
        id_tag = TagData.Tag_6.ref('id')
        id_field = FieldData.Field_5.ref('id')

    class FieldTag_6_7:
        score = 30
        id_tag = TagData.Tag_7.ref('id')
        id_field = FieldData.Field_6.ref('id')

    class FieldTag_6_8:
        score = 10
        id_tag = TagData.Tag_8.ref('id')
        id_field = FieldData.Field_6.ref('id')

    class FieldTag_6_9:
        score = 20
        id_tag = TagData.Tag_9.ref('id')
        id_field = FieldData.Field_6.ref('id')

    class FieldTag_7_12:
        score = 100
        id_tag = TagData.Tag_12.ref('id')
        id_field = FieldData.Field_7.ref('id')

    class FieldTag_7_13:
        score = 90
        id_tag = TagData.Tag_13.ref('id')
        id_field = FieldData.Field_7.ref('id')

    class FieldTag_8_10:
        score = 100
        id_tag = TagData.Tag_10.ref('id')
        id_field = FieldData.Field_8.ref('id')

    class FieldTag_9_115:
        score = 100
        id_tag = TagData.Tag_115.ref('id')
        id_field = FieldData.Field_9.ref('id')
