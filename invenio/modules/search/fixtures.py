# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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
        code = u'authorityinstitute'
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
        code = u'referstoexcludingselfcites'
        id = 40
        name = u'refers to excluding self cites'

    class Field_41:
        code = u'citedbyexcludingselfcites'
        id = 41
        name = u'cited by excluding self cites'

    class Field_42:
        code = u'cataloguer'
        id = 42
        name = u'cataloguer nickname'

    class Field_43:
        code = u'filename'
        id = 43
        name = u'file name'

    class Field_44:
        code = u'tag'
        id = 44
        name = u'tag'


class TagData(DataSet):

    class Tag_1:
        id = 1
        value = u'100__a'
        recjson_value = u'authors[0].full_name'
        name = u'first author name'

    class Tag_2:
        id = 2
        value = u'700__a'
        recjson_value = u'contributor.full_name'
        name = u'additional author name'

    class Tag_3:
        id = 3
        value = u'245__%'
        recjson_value = u'title'
        name = u'main title'

    class Tag_4:
        id = 4
        value = u'246__%'
        recjson_value = u'title_additional'
        name = u'additional title'

    class Tag_5:
        id = 5
        value = u'520__%'
        recjson_value = u'abstract'
        name = u'abstract'

    class Tag_6:
        id = 6
        value = u'6531_a'
        recjson_value = u'keywords.term'
        name = u'keyword'

    class Tag_7:
        id = 7
        value = u'037__a'
        recjson_value = u'primary_report_number'
        name = u'primary report number'

    class Tag_8:
        id = 8
        value = u'088__a'
        recjson_value = u'report_number.report_number'
        name = u'additional report number'

    class Tag_9:
        id = 9
        value = u'909C0r'
        recjson_value = u'added_report_number'
        name = u'added report number'

    class Tag_10:
        id = 10
        value = u'999C5%'
        recjson_value = u'reference'
        name = u'reference'

    class Tag_11:
        id = 11
        value = u''
        recjson_value = u'_collections'
        name = u'collection identifier'

    class Tag_12:
        id = 12
        value = u'65017a'
        recjson_value = u'subject.term'
        name = u'main subject'

    class Tag_13:
        id = 13
        value = u'65027a'
        recjson_value = u'subject_additional.term'
        name = u'additional subject'

    class Tag_14:
        id = 14
        value = u'909C0p'
        recjson_value = u'division'
        name = u'division'

    class Tag_15:
        id = 15
        value = u'909C0y'
        recjson_value = u'year'
        name = u'year'

    class Tag_16:
        id = 16
        value = u'00%'
        recjson_value = u'agency_code,recid,version_id'
        name = u'00x'

    class Tag_17:
        id = 17
        value = u'01%'
        recjson_value = u''
        name = u'01x'

    class Tag_18:
        id = 18
        value = u'02%'
        recjson_value = u'oai,doi,isbn,issn,isn'
        name = u'02x'

    class Tag_19:
        id = 19
        value = u'03%'
        recjson_value = u'code_designation,system_control_number'
        name = u'03x'

    class Tag_20:
        id = 20
        value = u'04%'
        recjson_value = u'language,publishing_country'
        name = u'lang'

    class Tag_21:
        id = 21
        value = u'05%'
        recjson_value = u'library_of_congress_call_number'
        name = u'05x'

    class Tag_22:
        id = 22
        value = u'06%'
        recjson_value = u''
        name = u'06x'

    class Tag_23:
        id = 23
        value = u'07%'
        recjson_value = u''
        name = u'07x'

    class Tag_24:
        id = 24
        value = u'08%'
        recjson_value = u'dewey_decimal_classification_number,other_report_number,report_number,udc'
        name = u'08x'

    class Tag_25:
        id = 25
        value = u'09%'
        recjson_value = u''
        name = u'09x'

    class Tag_26:
        id = 26
        value = u'10%'
        recjson_value = u'authors'
        name = u'10x'

    class Tag_27:
        id = 27
        value = u'11%'
        recjson_value = u'corporate_name[0],meeting_name[0]'
        name = u'11x'

    class Tag_28:
        id = 28
        value = u'12%'
        recjson_value = u''
        name = u'12x'

    class Tag_29:
        id = 29
        value = u'13%'
        recjson_value = u''
        name = u'13x'

    class Tag_30:
        id = 30
        value = u'14%'
        recjson_value = u'main_title_statement,chronological_term'
        name = u'14x'

    class Tag_31:
        id = 31
        value = u'15%'
        recjson_value = u''
        name = u'15x'

    class Tag_32:
        id = 32
        value = u'16%'
        recjson_value = u''
        name = u'16x'

    class Tag_33:
        id = 33
        value = u'17%'
        recjson_value = u''
        name = u'17x'

    class Tag_34:
        id = 34
        value = u'18%'
        recjson_value = u'medium'
        name = u'18x'

    class Tag_35:
        id = 35
        value = u'19%'
        recjson_value = u''
        name = u'19x'

    class Tag_36:
        id = 36
        value = u'20%'
        recjson_value = u''
        name = u'20x'

    class Tag_37:
        id = 37
        value = u'21%'
        recjson_value = u'abbreviated_title'
        name = u'21x'

    class Tag_38:
        id = 38
        value = u'22%'
        recjson_value = u'title_key'
        name = u'22x'

    class Tag_39:
        id = 39
        value = u'23%'
        recjson_value = u''
        name = u'23x'

    class Tag_40:
        id = 40
        value = u'24%'
        recjson_value = u'title_additional,title_other,title,title_parallel,title_translation'
        name = u'24x'

    class Tag_41:
        id = 41
        value = u'25%'
        recjson_value = u'edition_statement'
        name = u'25x'

    class Tag_42:
        id = 42
        value = u'26%'
        recjson_value = u'imprint,prepublication'
        name = u'internal'

    class Tag_43:
        id = 43
        value = u'27%'
        recjson_value = u'address'
        name = u'27x'

    class Tag_44:
        id = 44
        value = u'28%'
        recjson_value = u''
        name = u'28x'

    class Tag_45:
        id = 45
        value = u'29%'
        recjson_value = u''
        name = u'29x'

    class Tag_46:
        id = 46
        value = u'30%'
        recjson_value = u'physical_description'
        name = u'pages'

    class Tag_47:
        id = 47
        value = u'31%'
        recjson_value = u'current_publication_frequency'
        name = u'31x'

    class Tag_48:
        id = 48
        value = u'32%'
        recjson_value = u''
        name = u'32x'

    class Tag_49:
        id = 49
        value = u'33%'
        recjson_value = u'content_type'
        name = u'33x'

    class Tag_50:
        id = 50
        value = u'34%'
        recjson_value = u'medium'
        name = u'34x'

    class Tag_51:
        id = 51
        value = u'35%'
        recjson_value = u''
        name = u'35x'

    class Tag_52:
        id = 52
        value = u'36%'
        recjson_value = u''
        name = u'36x'

    class Tag_53:
        id = 53
        value = u'37%'
        recjson_value = u''
        name = u'37x'

    class Tag_54:
        id = 54
        value = u'38%'
        recjson_value = u''
        name = u'38x'

    class Tag_55:
        id = 55
        value = u'39%'
        recjson_value = u''
        name = u'39x'

    class Tag_56:
        id = 56
        value = u'40%'
        recjson_value = u''
        name = u'40x'

    class Tag_57:
        id = 57
        value = u'41%'
        recjson_value = u''
        name = u'41x'

    class Tag_58:
        id = 58
        value = u'42%'
        recjson_value = u''
        name = u'42x'

    class Tag_59:
        id = 59
        value = u'43%'
        recjson_value = u''
        name = u'43x'

    class Tag_60:
        id = 60
        value = u'44%'
        recjson_value = u''
        name = u'44x'

    class Tag_61:
        id = 61
        value = u'45%'
        recjson_value = u''
        name = u'45x'

    class Tag_62:
        id = 62
        value = u'46%'
        recjson_value = u''
        name = u'46x'

    class Tag_63:
        id = 63
        value = u'47%'
        recjson_value = u''
        name = u'47x'

    class Tag_64:
        id = 64
        value = u'48%'
        recjson_value = u''
        name = u'48x'

    class Tag_65:
        id = 65
        value = u'49%'
        recjson_value = u'series'
        name = u'series'

    class Tag_66:
        id = 66
        value = u'50%'
        recjson_value = u'comment,dissertation_note,restriction_access,other_restriction_access'
        name = u'50x'

    class Tag_67:
        id = 67
        value = u'51%'
        recjson_value = u'time_and_place_of_event_note'
        name = u'51x'

    class Tag_68:
        id = 68
        value = u'52%'
        recjson_value = u'abstract'
        name = u'52x'

    class Tag_69:
        id = 69
        value = u'53%'
        recjson_value = u'funding_info'
        name = u'53x'

    class Tag_70:
        id = 70
        value = u'54%'
        recjson_value = u'copyright_information,language_note,license,source_of_acquisition'
        name = u'54x'

    class Tag_71:
        id = 71
        value = u'55%'
        recjson_value = u'cumulative_index'
        name = u'55x'

    class Tag_72:
        id = 72
        value = u'56%'
        recjson_value = u''
        name = u'56x'

    class Tag_73:
        id = 73
        value = u'57%'
        recjson_value = u''
        name = u'57x'

    class Tag_74:
        id = 74
        value = u'58%'
        recjson_value = u'action_note,source_of_description'
        name = u'58x'

    class Tag_75:
        id = 75
        value = u'59%'
        recjson_value = u'abstract_french,cern_bookshop_statistics,copyright,internal_notes,observation_french,slac_note,type'
        name = u'summary'

    class Tag_76:
        id = 76
        value = u'60%'
        recjson_value = u''
        name = u'60x'

    class Tag_77:
        id = 77
        value = u'61%'
        recjson_value = u''
        name = u'61x'

    class Tag_78:
        id = 78
        value = u'62%'
        recjson_value = u''
        name = u'62x'

    class Tag_79:
        id = 79
        value = u'63%'
        recjson_value = u''
        name = u'63x'

    class Tag_80:
        id = 80
        value = u'64%'
        recjson_value = u'publisher'
        name = u'64x'

    class Tag_81:
        id = 81
        value = u'65%'
        recjson_value = u'keywords'
        name = u'65x'

    class Tag_82:
        id = 82
        value = u'66%'
        recjson_value = u''
        name = u'66x'

    class Tag_83:
        id = 83
        value = u'67%'
        recjson_value = u'administrative_history,source_data_found'
        name = u'67x'

    class Tag_84:
        id = 84
        value = u'68%'
        recjson_value = u'public_general_note'
        name = u'68x'

    class Tag_85:
        id = 85
        value = u'69%'
        recjson_value = u'accelerator_experiment,cataloguer_info,classification_terms,observation,subject_indicator,thesaurus_terms,lexi_keyword'
        name = u'subject'

    class Tag_86:
        id = 86
        value = u'70%'
        recjson_value = u'contributor'
        name = u'70x'

    class Tag_87:
        id = 87
        value = u'71%'
        recjson_value = u'corporate_name[n],meeting_name[n]'
        name = u'71x'

    class Tag_88:
        id = 88
        value = u'72%'
        recjson_value = u'author_archive'
        name = u'author-ad'

    class Tag_89:
        id = 89
        value = u'73%'
        recjson_value = u''
        name = u'73x'

    class Tag_90:
        id = 90
        value = u'74%'
        recjson_value = u''
        name = u'74x'

    class Tag_91:
        id = 91
        value = u'75%'
        recjson_value = u''
        name = u'75x'

    class Tag_92:
        id = 92
        value = u'76%'
        recjson_value = u''
        name = u'76x'

    class Tag_93:
        id = 93
        value = u'77%'
        recjson_value = u'publication_info'
        name = u'77x'

    class Tag_94:
        id = 94
        value = u'78%'
        recjson_value = u''
        name = u'78x'

    class Tag_95:
        id = 95
        value = u'79%'
        recjson_value = u''
        name = u'79x'

    class Tag_96:
        id = 96
        value = u'80%'
        recjson_value = u''
        name = u'80x'

    class Tag_97:
        id = 97
        value = u'81%'
        recjson_value = u''
        name = u'81x'

    class Tag_98:
        id = 98
        value = u'82%'
        recjson_value = u''
        name = u'82x'

    class Tag_99:
        id = 99
        value = u'83%'
        recjson_value = u''
        name = u'83x'

    class Tag_100:
        id = 100
        value = u'84%'
        recjson_value = u''
        name = u'84x'

    class Tag_101:
        id = 101
        value = u'85%'
        recjson_value = u'location,email,email_message,electronic_location'
        name = u'electr'

    class Tag_102:
        id = 102
        value = u'86%'
        recjson_value = u''
        name = u'86x'

    class Tag_103:
        id = 103
        value = u'87%'
        recjson_value = u''
        name = u'87x'

    class Tag_104:
        id = 104
        value = u'88%'
        recjson_value = u''
        name = u'88x'

    class Tag_105:
        id = 105
        value = u'89%'
        recjson_value = u''
        name = u'89x'

    class Tag_106:
        id = 106
        value = u'90%'
        recjson_value = u'journal_info'
        name = u'publication'

    class Tag_107:
        id = 107
        value = u'91%'
        recjson_value = u'status_week,citation,universal_decimal_classification'
        name = u'pub-conf-cit'

    class Tag_108:
        id = 108
        value = u'92%'
        recjson_value = u'other_institution'
        name = u'92x'

    class Tag_109:
        id = 109
        value = u'93%'
        recjson_value = u''
        name = u'93x'

    class Tag_110:
        id = 110
        value = u'94%'
        recjson_value = u''
        name = u'94x'

    class Tag_111:
        id = 111
        value = u'95%'
        recjson_value = u''
        name = u'95x'

    class Tag_112:
        id = 112
        value = u'96%'
        recjson_value = u'aleph_linking_page,base,cataloguer_info,item,owner'
        name = u'catinfo'

    class Tag_113:
        id = 113
        value = u'97%'
        recjson_value = u'system_number'
        name = u'97x'

    class Tag_114:
        id = 114
        value = u'98%'
        recjson_value = u''
        name = u'98x'

    class Tag_115:
        id = 115
        value = u'8564_u'
        recjson_value = u'url.url'
        name = u'url'

    class Tag_116:
        id = 116
        value = u'909C0e'
        recjson_value = u'accelerator_experiment.experiment'
        name = u'experiment'

    class Tag_117:
        id = 117
        value = u'001'
        recjson_value = u'recid'
        name = u'record ID'

    class Tag_118:
        id = 118
        value = u'020__a'
        recjson_value = u'isbn'
        name = u'isbn'

    class Tag_119:
        id = 119
        value = u'022__a'
        recjson_value = u'issn'
        name = u'issn'

    class Tag_120:
        id = 120
        value = u'030__a'
        recjson_value = u''
        name = u'coden'

    class Tag_121:
        id = 121
        value = u'909C4a'
        recjson_value = u'journal_info.doi'
        name = u'doi'

    class Tag_122:
        id = 122
        value = u'850%'
        recjson_value = u''
        name = u'850x'

    class Tag_123:
        id = 123
        value = u'851%'
        recjson_value = u''
        name = u'851x'

    class Tag_124:
        id = 124
        value = u'852%'
        recjson_value = u'location'
        name = u'852x'

    class Tag_125:
        id = 125
        value = u'853%'
        recjson_value = u''
        name = u'853x'

    class Tag_126:
        id = 126
        value = u'854%'
        recjson_value = u''
        name = u'854x'

    class Tag_127:
        id = 127
        value = u'855%'
        recjson_value = u''
        name = u'855x'

    class Tag_128:
        id = 128
        value = u'857%'
        recjson_value = u''
        name = u'857x'

    class Tag_129:
        id = 129
        value = u'858%'
        recjson_value = u''
        name = u'858x'

    class Tag_130:
        id = 130
        value = u'859%'
        recjson_value = u'email_message'
        name = u'859x'

    class Tag_131:
        id = 131
        value = u'909C4%'
        recjson_value = u'journal_info'
        name = u'journal'

    class Tag_132:
        id = 132
        value = u'710__g'
        recjson_value = u'corporate_name[n].collaboration'
        name = u'collaboration'

    class Tag_133:
        id = 133
        value = u'100__u'
        recjson_value = u'authors[0].affiliation'
        name = u'first author affiliation'

    class Tag_134:
        id = 134
        value = u'700__u'
        recjson_value = u'contributor.affiliation'
        name = u'additional author affiliation'

    class Tag_135:
        id = 135
        value = u'8564_y'
        recjson_value = u'url.description'
        name = u'caption'

    class Tag_136:
        id = 136
        value = u'909C4c'
        recjson_value = u'journal_info.pagination'
        name = u'journal page'

    class Tag_137:
        id = 137
        value = u'909C4p'
        recjson_value = u'journal_info.title'
        name = u'journal title'

    class Tag_138:
        id = 138
        value = u'909C4v'
        recjson_value = u'journal_info.volume'
        name = u'journal volume'

    class Tag_139:
        id = 139
        value = u'909C4y'
        recjson_value = u'journal_info.year'
        name = u'journal year'

    class Tag_140:
        id = 140
        value = u'500__a'
        recjson_value = u'commnt'
        name = u'comment'

    class Tag_141:
        id = 141
        value = u'245__a'
        recjson_value = u'title.title'
        name = u'title'

    class Tag_142:
        id = 142
        value = u'245__a'
        recjson_value = u''
        name = u'main abstract'

    class Tag_143:
        id = 143
        value = u'595__a'
        recjson_value = u'internal_notes.internal_note'
        name = u'internal notes'

    class Tag_144:
        id = 144
        value = u'787%'
        recjson_value = u''
        name = u'other relationship entry'

    class Tag_146:
        id = 146
        value = u'400__a'
        recjson_value = u''
        name = u'authority: alternative personal name'

    class Tag_148:
        id = 148
        value = u'110__a'
        recjson_value = u'corporate_name[0].name'
        name = u'authority: organization main name'

    class Tag_149:
        id = 149
        value = u'410__a'
        recjson_value = u''
        name = u'organization alternative name'

    class Tag_150:
        id = 150
        value = u'510__a'
        recjson_value = u''
        name = u'organization main from other record'

    class Tag_151:
        id = 151
        value = u'130__a'
        recjson_value = u''
        name = u'authority: uniform title'

    class Tag_152:
        id = 152
        value = u'430__a'
        recjson_value = u''
        name = u'authority: uniform title alternatives'

    class Tag_153:
        id = 153
        value = u'530__a'
        recjson_value = u''
        name = u'authority: uniform title from other record'

    class Tag_154:
        id = 154
        value = u'150__a'
        recjson_value = u''
        name = u'authority: subject from other record'

    class Tag_155:
        id = 155
        value = u'450__a'
        recjson_value = u''
        name = u'authority: subject alternative name'

    class Tag_156:
        id = 156
        value = u'450__a'
        recjson_value = u''
        name = u'authority: subject main name'

    class Tag_157:
        id = 157
        value = u'031%'
        recjson_value = u''
        name = u'031x'

    class Tag_158:
        id = 158
        value = u'032%'
        recjson_value = u''
        name = u'032x'

    class Tag_159:
        id = 159
        value = u'033%'
        recjson_value = u'code_designation'
        name = u'033x'

    class Tag_160:
        id = 160
        value = u'034%'
        recjson_value = u''
        name = u'034x'

    class Tag_161:
        id = 161
        value = u'035%'
        recjson_value = u'system_control_number'
        name = u'035x'

    class Tag_162:
        id = 162
        value = u'036%'
        recjson_value = u''
        name = u'036x'

    class Tag_163:
        id = 163
        value = u'037%'
        recjson_value = u'primary_report_number'
        name = u'037x'

    class Tag_164:
        id = 164
        value = u'038%'
        recjson_value = u''
        name = u'038x'

    class Tag_165:
        id = 165
        value = u'080%'
        recjson_value = u'udc'
        name = u'080x'

    class Tag_166:
        id = 166
        value = u'082%'
        recjson_value = u'dewey_decimal_classification_number'
        name = u'082x'

    class Tag_167:
        id = 167
        value = u'083%'
        recjson_value = u''
        name = u'083x'

    class Tag_168:
        id = 168
        value = u'084%'
        recjson_value = u'other_report_number'
        name = u'084x'

    class Tag_169:
        id = 169
        value = u'085%'
        recjson_value = u''
        name = u'085x'

    class Tag_170:
        id = 170
        value = u'086%'
        recjson_value = u''
        name = u'086x'

    class Tag_171:
        id = 171
        value = u'240%'
        recjson_value = u''
        name = u'240x'

    class Tag_172:
        id = 172
        value = u'242%'
        recjson_value = u'title_translation'
        name = u'242x'

    class Tag_173:
        id = 173
        value = u'243%'
        recjson_value = u''
        name = u'243x'

    class Tag_174:
        id = 174
        value = u'244%'
        recjson_value = u''
        name = u'244x'

    class Tag_175:
        id = 175
        value = u'247%'
        recjson_value = u''
        name = u'247x'

    class Tag_176:
        id = 176
        value = u'521%'
        recjson_value = u''
        name = u'521x'

    class Tag_177:
        id = 177
        value = u'522%'
        recjson_value = u''
        name = u'522x'

    class Tag_178:
        id = 178
        value = u'524%'
        recjson_value = u''
        name = u'524x'

    class Tag_179:
        id = 179
        value = u'525%'
        recjson_value = u''
        name = u'525x'

    class Tag_180:
        id = 180
        value = u'526%'
        recjson_value = u''
        name = u'526x'

    class Tag_181:
        id = 181
        value = u'650%'
        recjson_value = u'subject'
        name = u'650x'

    class Tag_182:
        id = 182
        value = u'651%'
        recjson_value = u''
        name = u'651x'

    class Tag_183:
        id = 183
        value = u'6531_v'
        recjson_value = u'keywords.v'
        name = u'6531_v'

    class Tag_184:
        id = 184
        value = u'6531_y'
        recjson_value = u'keywords.y'
        name = u'6531_y'

    class Tag_185:
        id = 185
        value = u'6531_9'
        recjson_value = u'keywords.institute'
        name = u'6531_9'

    class Tag_186:
        id = 186
        value = u'654%'
        recjson_value = u''
        name = u'654x'

    class Tag_187:
        id = 187
        value = u'655%'
        recjson_value = u''
        name = u'655x'

    class Tag_188:
        id = 188
        value = u'656%'
        recjson_value = u''
        name = u'656x'

    class Tag_189:
        id = 189
        value = u'657%'
        recjson_value = u''
        name = u'657x'

    class Tag_190:
        id = 190
        value = u'658%'
        recjson_value = u''
        name = u'658x'

    class Tag_191:
        id = 191
        value = u'711%'
        recjson_value = u''
        name = u'711x'

    class Tag_192:
        id = 192
        value = u'900%'
        recjson_value = u'meeting_name'
        name = u'900x'

    class Tag_193:
        id = 193
        value = u'901%'
        recjson_value = u'affiliation'
        name = u'901x'

    class Tag_194:
        id = 194
        value = u'902%'
        recjson_value = u''
        name = u'902x'

    class Tag_195:
        id = 195
        value = u'903%'
        recjson_value = u''
        name = u'903x'

    class Tag_196:
        id = 196
        value = u'904%'
        recjson_value = u''
        name = u'904x'

    class Tag_197:
        id = 197
        value = u'905%'
        recjson_value = u''
        name = u'905x'

    class Tag_198:
        id = 198
        value = u'906%'
        recjson_value = u''
        name = u'906x'

    class Tag_199:
        id = 199
        value = u'907%'
        recjson_value = u''
        name = u'907x'

    class Tag_200:
        id = 200
        value = u'908%'
        recjson_value = u''
        name = u'908x'

    class Tag_201:
        id = 201
        value = u'909C1%'
        recjson_value = u'FIXME_project_info'
        name = u'909C1x'

    class Tag_202:
        id = 202
        value = u'909C5%'
        recjson_value = u'FIXME_909C5'
        name = u'909C5x'

    class Tag_203:
        id = 203
        value = u'909CS%'
        recjson_value = u'FIXME_909CS'
        name = u'909CSx'

    class Tag_204:
        id = 204
        value = u'909CO%'
        recjson_value = u'FIXME_OAI'
        name = u'909COx'

    class Tag_205:
        id = 205
        value = u'909CK%'
        recjson_value = u'FIXME_publishedin'
        name = u'909CKx'

    class Tag_206:
        id = 206
        value = u'909CP%'
        recjson_value = u'photo_information'
        name = u'909CPx'

    class Tag_207:
        id = 207
        value = u'981%'
        recjson_value = u''
        name = u'981x'

    class Tag_208:
        id = 208
        value = u'982%'
        recjson_value = u''
        name = u'982x'

    class Tag_209:
        id = 209
        value = u'983%'
        recjson_value = u''
        name = u'983x'

    class Tag_210:
        id = 210
        value = u'984%'
        recjson_value = u''
        name = u'984x'

    class Tag_211:
        id = 211
        value = u'985%'
        recjson_value = u''
        name = u'985x'

    class Tag_212:
        id = 212
        value = u'986%'
        recjson_value = u''
        name = u'986x'

    class Tag_213:
        id = 213
        value = u'987%'
        recjson_value = u''
        name = u'987x'

    class Tag_214:
        id = 214
        value = u'988%'
        recjson_value = u''
        name = u'988x'

    class Tag_215:
        id = 215
        value = u'989%'
        recjson_value = u''
        name = u'989x'

    class Tag_216:
        id = 216
        value = u'100__0'
        recjson_value = u''
        name = u'author control'

    class Tag_217:
        id = 217
        value = u'110__0'
        recjson_value = u''
        name = u'institute control'

    class Tag_218:
        id = 218
        value = u'130__0'
        recjson_value = u''
        name = u'journal control'

    class Tag_219:
        id = 219
        value = u'150__0'
        recjson_value = u''
        name = u'subject control'

    class Tag_220:
        id = 220
        value = u'260__0'
        recjson_value = u''
        name = u'additional institute control'

    class Tag_221:
        id = 221
        value = u'700__0'
        recjson_value = u''
        name = u'additional author control'

    class Tag_222:
        id = 222
        value = u'003'
        recjson_value = u'agency_code'
        name = u'agency code'

    class Tag_223:
        id = 223
        value = u'909C0b'
        recjson_value = u'FIXME_ALEPH_base_number'
        name = u'FIXME_ALEPH_base_number'

    class Tag_224:
        id = 224
        value = u'909C0a'
        recjson_value = u'FIXME_accelerator'
        name = u'FIXME_accelerator'

    class Tag_225:
        id = 225
        value = u'909C0o'
        recjson_value = u'FIXME_code'
        name = u'FIXME_code'

    class Tag_226:
        id = 226
        value = u'909C2%'
        recjson_value = u'FIXME_909C2'
        name = u'FIXME_909C2'


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

    class FieldTag_39_223:
        score = 10
        id_tag = TagData.Tag_223.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_224:
        score = 10
        id_tag = TagData.Tag_224.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_225:
        score = 10
        id_tag = TagData.Tag_225.ref('id')
        id_field = FieldData.Field_39.ref('id')

    class FieldTag_39_226:
        score = 10
        id_tag = TagData.Tag_226.ref('id')
        id_field = FieldData.Field_39.ref('id')
