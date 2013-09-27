

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

    class Field_33:
        code = u'authorityauthor'
        id = 33
        name = u'authority author'

    class Field_34:
        code = u'authorityinstitution'
        id = 34
        name = u'authority institution'

    class Field_35:
        code = u'authorityjournal'
        id = 35
        name = u'authority journal'

    class Field_36:
        code = u'authoritysubject'
        id = 36
        name = u'authority subject'

    class Field_37:
        code = u'itemcount'
        id = 37
        name = u'item count'

    class Field_38:
        code = u'filetype'
        id = 38
        name = u'file type'

    class Field_39:
        code = u'miscellaneous'
        id = 39
        name = u'miscellaneous'

    class Field_40:
        code = u'tag'
        id = 40
        name = u'tag'


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

    class Tag_146:
        id = 146
        value = u'400__a'
        name = u'authority: alternative personal name'

    class Tag_148:
        id = 148
        value = u'110__a'
        name = u'authority: organization main name'

    class Tag_149:
        id = 149
        value = u'410__a'
        name = u'organization alternative name'

    class Tag_150:
        id = 150
        value = u'510__a'
        name = u'organization main from other record'

    class Tag_151:
        id = 151
        value = u'130__a'
        name = u'authority: uniform title'

    class Tag_152:
        id = 152
        value = u'430__a'
        name = u'authority: uniform title alternatives'

    class Tag_153:
        id = 153
        value = u'530__a'
        name = u'authority: uniform title from other record'

    class Tag_154:
        id = 154
        value = u'150__a'
        name = u'authority: subject from other record'

    class Tag_155:
        id = 155
        value = u'450__a'
        name = u'authority: subject alternative name'

    class Tag_156:
        id = 156
        value = u'450__a'
        name = u'authority: subject main name'

    class Tag_157:
        id = 157
        value = u'031%'
        name = u'031x'

    class Tag_158:
        id = 158
        value = u'032%'
        name = u'032x'

    class Tag_159:
        id = 159
        value = u'033%'
        name = u'033x'

    class Tag_160:
        id = 160
        value = u'034%'
        name = u'034x'

    class Tag_161:
        id = 161
        value = u'035%'
        name = u'035x'

    class Tag_162:
        id = 162
        value = u'036%'
        name = u'036x'

    class Tag_163:
        id = 163
        value = u'037%'
        name = u'037x'

    class Tag_164:
        id = 164
        value = u'038%'
        name = u'038x'

    class Tag_165:
        id = 165
        value = u'080%'
        name = u'080x'

    class Tag_166:
        id = 166
        value = u'082%'
        name = u'082x'

    class Tag_167:
        id = 167
        value = u'083%'
        name = u'083x'

    class Tag_168:
        id = 168
        value = u'084%'
        name = u'084x'

    class Tag_169:
        id = 169
        value = u'085%'
        name = u'085x'

    class Tag_170:
        id = 170
        value = u'086%'
        name = u'086x'

    class Tag_171:
        id = 171
        value = u'240%'
        name = u'240x'

    class Tag_172:
        id = 172
        value = u'242%'
        name = u'242x'

    class Tag_173:
        id = 173
        value = u'243%'
        name = u'243x'

    class Tag_174:
        id = 174
        value = u'244%'
        name = u'244x'

    class Tag_175:
        id = 175
        value = u'247%'
        name = u'247x'

    class Tag_176:
        id = 176
        value = u'521%'
        name = u'521x'

    class Tag_177:
        id = 177
        value = u'522%'
        name = u'522x'

    class Tag_178:
        id = 178
        value = u'524%'
        name = u'524x'

    class Tag_179:
        id = 179
        value = u'525%'
        name = u'525x'

    class Tag_180:
        id = 180
        value = u'526%'
        name = u'526x'

    class Tag_181:
        id = 181
        value = u'650%'
        name = u'650x'

    class Tag_182:
        id = 182
        value = u'651%'
        name = u'651x'

    class Tag_183:
        id = 183
        value = u'6531_v'
        name = u'6531_v'

    class Tag_184:
        id = 184
        value = u'6531_y'
        name = u'6531_y'

    class Tag_185:
        id = 185
        value = u'6531_9'
        name = u'6531_9'

    class Tag_186:
        id = 186
        value = u'654%'
        name = u'654x'

    class Tag_187:
        id = 187
        value = u'655%'
        name = u'655x'

    class Tag_188:
        id = 188
        value = u'656%'
        name = u'656x'

    class Tag_189:
        id = 189
        value = u'657%'
        name = u'657x'

    class Tag_190:
        id = 190
        value = u'658%'
        name = u'658x'

    class Tag_191:
        id = 191
        value = u'711%'
        name = u'711x'

    class Tag_192:
        id = 192
        value = u'900%'
        name = u'900x'

    class Tag_193:
        id = 193
        value = u'901%'
        name = u'901x'

    class Tag_194:
        id = 194
        value = u'902%'
        name = u'902x'

    class Tag_195:
        id = 195
        value = u'903%'
        name = u'903x'

    class Tag_196:
        id = 196
        value = u'904%'
        name = u'904x'

    class Tag_197:
        id = 197
        value = u'905%'
        name = u'905x'

    class Tag_198:
        id = 198
        value = u'906%'
        name = u'906x'

    class Tag_199:
        id = 199
        value = u'907%'
        name = u'907x'

    class Tag_200:
        id = 200
        value = u'908%'
        name = u'908x'

    class Tag_201:
        id = 201
        value = u'909C1%'
        name = u'909C1x'

    class Tag_202:
        id = 202
        value = u'909C5%'
        name = u'909C5x'

    class Tag_203:
        id = 203
        value = u'909CS%'
        name = u'909CSx'

    class Tag_204:
        id = 204
        value = u'909CO%'
        name = u'909COx'

    class Tag_205:
        id = 205
        value = u'909CK%'
        name = u'909CKx'

    class Tag_206:
        id = 206
        value = u'909CP%'
        name = u'909CPx'

    class Tag_207:
        id = 207
        value = u'981%'
        name = u'981x'

    class Tag_208:
        id = 208
        value = u'982%'
        name = u'982x'

    class Tag_209:
        id = 209
        value = u'983%'
        name = u'983x'

    class Tag_210:
        id = 210
        value = u'984%'
        name = u'984x'

    class Tag_211:
        id = 211
        value = u'985%'
        name = u'985x'

    class Tag_212:
        id = 212
        value = u'986%'
        name = u'986x'

    class Tag_213:
        id = 213
        value = u'987%'
        name = u'987x'

    class Tag_214:
        id = 214
        value = u'988%'
        name = u'988x'

    class Tag_215:
        id = 215
        value = u'989%'
        name = u'989x'

    class Tag_216:
        id = 216
        value = u'100__0'
        name = u'author control'

    class Tag_217:
        id = 217
        value = u'110__0'
        name = u'institution control'

    class Tag_218:
        id = 218
        value = u'130__0'
        name = u'journal control'

    class Tag_219:
        id = 219
        value = u'150__0'
        name = u'subject control'

    class Tag_220:
        id = 220
        value = u'260__0'
        name = u'additional institution control'

    class Tag_221:
        id = 221
        value = u'700__0'
        name = u'additional author control'



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

    class Format_27:
        code = u'mobb'
        last_updated = None
        description = u'Mobile brief format.'
        content_type = u'text/html'
        id = 27
        visibility = 0
        name = u'Mobile brief'

    class Format_28:
        code = u'mobd'
        last_updated = None
        description = u'Mobile detailed format.'
        content_type = u'text/html'
        id = 28
        visibility = 0
        name = u'Mobile detailed'


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

    class FieldTag_33_1:
        score = 100
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_33.ref('id')

    class FieldTag_33_146:
        score = 100
        id_tag = TagData.Tag_146.ref('id')
        id_field = FieldData.Field_33.ref('id')

    class FieldTag_33_140:
        score = 100
        id_tag = TagData.Tag_140.ref('id')
        id_field = FieldData.Field_33.ref('id')

    class FieldTag_34_148:
        score = 100
        id_tag = TagData.Tag_148.ref('id')
        id_field = FieldData.Field_34.ref('id')

    class FieldTag_34_149:
        score = 100
        id_tag = TagData.Tag_149.ref('id')
        id_field = FieldData.Field_34.ref('id')

    class FieldTag_34_150:
        score = 100
        id_tag = TagData.Tag_150.ref('id')
        id_field = FieldData.Field_34.ref('id')

    class FieldTag_35_151:
        score = 100
        id_tag = TagData.Tag_151.ref('id')
        id_field = FieldData.Field_35.ref('id')

    class FieldTag_35_152:
        score = 100
        id_tag = TagData.Tag_152.ref('id')
        id_field = FieldData.Field_35.ref('id')

    class FieldTag_35_153:
        score = 100
        id_tag = TagData.Tag_153.ref('id')
        id_field = FieldData.Field_35.ref('id')

    class FieldTag_36_154:
        score = 100
        id_tag = TagData.Tag_154.ref('id')
        id_field = FieldData.Field_36.ref('id')

    class FieldTag_36_155:
        score = 100
        id_tag = TagData.Tag_155.ref('id')
        id_field = FieldData.Field_36.ref('id')

    class FieldTag_36_156:
        score = 100
        id_tag = TagData.Tag_156.ref('id')
        id_field = FieldData.Field_36.ref('id')

    class FieldTag_39_17:
        score = 10
        id_tag = TagData.Tag_17.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_18:
        score = 10
        id_tag = TagData.Tag_18.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_157:
        score = 10
        id_tag = TagData.Tag_157.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_158:
        score = 10
        id_tag = TagData.Tag_158.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_159:
        score = 10
        id_tag = TagData.Tag_159.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_160:
        score = 10
        id_tag = TagData.Tag_160.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_161:
        score = 10
        id_tag = TagData.Tag_161.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_162:
        score = 10
        id_tag = TagData.Tag_162.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_163:
        score = 10
        id_tag = TagData.Tag_163.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_164:
        score = 10
        id_tag = TagData.Tag_164.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_20:
        score = 10
        id_tag = TagData.Tag_20.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_21:
        score = 10
        id_tag = TagData.Tag_21.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_22:
        score = 10
        id_tag = TagData.Tag_22.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_23:
        score = 10
        id_tag = TagData.Tag_23.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_165:
        score = 10
        id_tag = TagData.Tag_165.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_166:
        score = 10
        id_tag = TagData.Tag_166.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_167:
        score = 10
        id_tag = TagData.Tag_167.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_168:
        score = 10
        id_tag = TagData.Tag_168.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_169:
        score = 10
        id_tag = TagData.Tag_169.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_170:
        score = 10
        id_tag = TagData.Tag_170.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_25:
        score = 10
        id_tag = TagData.Tag_25.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_27:
        score = 10
        id_tag = TagData.Tag_27.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_28:
        score = 10
        id_tag = TagData.Tag_28.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_29:
        score = 10
        id_tag = TagData.Tag_29.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_30:
        score = 10
        id_tag = TagData.Tag_30.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_31:
        score = 10
        id_tag = TagData.Tag_31.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_32:
        score = 10
        id_tag = TagData.Tag_32.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_33:
        score = 10
        id_tag = TagData.Tag_33.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_34:
        score = 10
        id_tag = TagData.Tag_34.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_35:
        score = 10
        id_tag = TagData.Tag_35.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_36:
        score = 10
        id_tag = TagData.Tag_36.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_37:
        score = 10
        id_tag = TagData.Tag_37.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_38:
        score = 10
        id_tag = TagData.Tag_38.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_39:
        score = 10
        id_tag = TagData.Tag_39.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_171:
        score = 10
        id_tag = TagData.Tag_171.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_172:
        score = 10
        id_tag = TagData.Tag_172.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_173:
        score = 10
        id_tag = TagData.Tag_173.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_174:
        score = 10
        id_tag = TagData.Tag_174.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_175:
        score = 10
        id_tag = TagData.Tag_175.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_41:
        score = 10
        id_tag = TagData.Tag_41.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_42:
        score = 10
        id_tag = TagData.Tag_42.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_43:
        score = 10
        id_tag = TagData.Tag_43.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_44:
        score = 10
        id_tag = TagData.Tag_44.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_45:
        score = 10
        id_tag = TagData.Tag_45.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_46:
        score = 10
        id_tag = TagData.Tag_46.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_47:
        score = 10
        id_tag = TagData.Tag_47.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_48:
        score = 10
        id_tag = TagData.Tag_48.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_49:
        score = 10
        id_tag = TagData.Tag_49.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_50:
        score = 10
        id_tag = TagData.Tag_50.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_51:
        score = 10
        id_tag = TagData.Tag_51.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_52:
        score = 10
        id_tag = TagData.Tag_52.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_53:
        score = 10
        id_tag = TagData.Tag_53.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_54:
        score = 10
        id_tag = TagData.Tag_54.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_55:
        score = 10
        id_tag = TagData.Tag_55.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_56:
        score = 10
        id_tag = TagData.Tag_56.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_57:
        score = 10
        id_tag = TagData.Tag_57.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_58:
        score = 10
        id_tag = TagData.Tag_58.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_59:
        score = 10
        id_tag = TagData.Tag_59.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_60:
        score = 10
        id_tag = TagData.Tag_60.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_61:
        score = 10
        id_tag = TagData.Tag_61.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_62:
        score = 10
        id_tag = TagData.Tag_62.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_63:
        score = 10
        id_tag = TagData.Tag_63.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_64:
        score = 10
        id_tag = TagData.Tag_64.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_65:
        score = 10
        id_tag = TagData.Tag_65.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_66:
        score = 10
        id_tag = TagData.Tag_66.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_67:
        score = 10
        id_tag = TagData.Tag_67.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_176:
        score = 10
        id_tag = TagData.Tag_176.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_177:
        score = 10
        id_tag = TagData.Tag_177.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_178:
        score = 10
        id_tag = TagData.Tag_178.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_179:
        score = 10
        id_tag = TagData.Tag_179.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_180:
        score = 10
        id_tag = TagData.Tag_180.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_69:
        score = 10
        id_tag = TagData.Tag_69.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_70:
        score = 10
        id_tag = TagData.Tag_70.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_71:
        score = 10
        id_tag = TagData.Tag_71.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_72:
        score = 10
        id_tag = TagData.Tag_72.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_73:
        score = 10
        id_tag = TagData.Tag_73.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_74:
        score = 10
        id_tag = TagData.Tag_74.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_75:
        score = 10
        id_tag = TagData.Tag_75.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_76:
        score = 10
        id_tag = TagData.Tag_76.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_77:
        score = 10
        id_tag = TagData.Tag_77.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_78:
        score = 10
        id_tag = TagData.Tag_78.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_79:
        score = 10
        id_tag = TagData.Tag_79.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_80:
        score = 10
        id_tag = TagData.Tag_80.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_181:
        score = 10
        id_tag = TagData.Tag_181.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_182:
        score = 10
        id_tag = TagData.Tag_182.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_183:
        score = 10
        id_tag = TagData.Tag_183.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_184:
        score = 10
        id_tag = TagData.Tag_184.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_185:
        score = 10
        id_tag = TagData.Tag_185.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_186:
        score = 10
        id_tag = TagData.Tag_186.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_82:
        score = 10
        id_tag = TagData.Tag_82.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_83:
        score = 10
        id_tag = TagData.Tag_83.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_84:
        score = 10
        id_tag = TagData.Tag_84.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_85:
        score = 10
        id_tag = TagData.Tag_85.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_187:
        score = 10
        id_tag = TagData.Tag_187.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_88:
        score = 10
        id_tag = TagData.Tag_88.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_89:
        score = 10
        id_tag = TagData.Tag_89.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_90:
        score = 10
        id_tag = TagData.Tag_90.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_91:
        score = 10
        id_tag = TagData.Tag_91.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_92:
        score = 10
        id_tag = TagData.Tag_92.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_93:
        score = 10
        id_tag = TagData.Tag_93.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_94:
        score = 10
        id_tag = TagData.Tag_94.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_95:
        score = 10
        id_tag = TagData.Tag_95.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_96:
        score = 10
        id_tag = TagData.Tag_96.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_97:
        score = 10
        id_tag = TagData.Tag_97.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_98:
        score = 10
        id_tag = TagData.Tag_98.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_99:
        score = 10
        id_tag = TagData.Tag_99.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_100:
        score = 10
        id_tag = TagData.Tag_100.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_102:
        score = 10
        id_tag = TagData.Tag_102.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_103:
        score = 10
        id_tag = TagData.Tag_103.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_104:
        score = 10
        id_tag = TagData.Tag_104.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_105:
        score = 10
        id_tag = TagData.Tag_105.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_188:
        score = 10
        id_tag = TagData.Tag_188.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_189:
        score = 10
        id_tag = TagData.Tag_189.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_190:
        score = 10
        id_tag = TagData.Tag_190.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_191:
        score = 10
        id_tag = TagData.Tag_191.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_192:
        score = 10
        id_tag = TagData.Tag_192.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_193:
        score = 10
        id_tag = TagData.Tag_193.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_194:
        score = 10
        id_tag = TagData.Tag_194.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_195:
        score = 10
        id_tag = TagData.Tag_195.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_196:
        score = 10
        id_tag = TagData.Tag_196.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_107:
        score = 10
        id_tag = TagData.Tag_107.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_108:
        score = 10
        id_tag = TagData.Tag_108.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_109:
        score = 10
        id_tag = TagData.Tag_109.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_110:
        score = 10
        id_tag = TagData.Tag_110.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_111:
        score = 10
        id_tag = TagData.Tag_111.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_112:
        score = 10
        id_tag = TagData.Tag_112.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_113:
        score = 10
        id_tag = TagData.Tag_113.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_197:
        score = 10
        id_tag = TagData.Tag_197.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_198:
        score = 10
        id_tag = TagData.Tag_198.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_199:
        score = 10
        id_tag = TagData.Tag_199.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_200:
        score = 10
        id_tag = TagData.Tag_200.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_201:
        score = 10
        id_tag = TagData.Tag_201.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_202:
        score = 10
        id_tag = TagData.Tag_202.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_203:
        score = 10
        id_tag = TagData.Tag_203.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_204:
        score = 10
        id_tag = TagData.Tag_204.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_205:
        score = 10
        id_tag = TagData.Tag_205.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_206:
        score = 10
        id_tag = TagData.Tag_206.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_207:
        score = 10
        id_tag = TagData.Tag_207.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_208:
        score = 10
        id_tag = TagData.Tag_208.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_209:
        score = 10
        id_tag = TagData.Tag_209.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_210:
        score = 10
        id_tag = TagData.Tag_210.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_211:
        score = 10
        id_tag = TagData.Tag_211.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_212:
        score = 10
        id_tag = TagData.Tag_212.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_213:
        score = 10
        id_tag = TagData.Tag_213.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_214:
        score = 10
        id_tag = TagData.Tag_214.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_215:
        score = 10
        id_tag = TagData.Tag_215.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_122:
        score = 10
        id_tag = TagData.Tag_122.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_123:
        score = 10
        id_tag = TagData.Tag_123.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_124:
        score = 10
        id_tag = TagData.Tag_124.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_125:
        score = 10
        id_tag = TagData.Tag_125.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_126:
        score = 10
        id_tag = TagData.Tag_126.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_127:
        score = 10
        id_tag = TagData.Tag_127.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_128:
        score = 10
        id_tag = TagData.Tag_128.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_129:
        score = 10
        id_tag = TagData.Tag_129.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_130:
        score = 10
        id_tag = TagData.Tag_130.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_1:
        score = 10
        id_tag = TagData.Tag_1.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_2:
        score = 10
        id_tag = TagData.Tag_2.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_216:
        score = 10
        id_tag = TagData.Tag_216.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_217:
        score = 10
        id_tag = TagData.Tag_217.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_218:
        score = 10
        id_tag = TagData.Tag_218.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_219:
        score = 10
        id_tag = TagData.Tag_219.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_220:
        score = 10
        id_tag = TagData.Tag_220.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_221:
        score = 10
        id_tag = TagData.Tag_221.ref('id')
        id_field = FieldData.Field_39.ref('id')
