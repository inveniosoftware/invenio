# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Search fixtures."""

from fixture import DataSet

from invenio.config import CFG_SITE_NAME


class CollectionData(DataSet):
    class siteCollection:
        id = 1
        name = CFG_SITE_NAME
        dbquery = None


class FieldData(DataSet):

    class Field_1:
        code = u'anyfield'
        name = u'any field'

    class Field_2:
        code = u'title'
        name = u'title'

    class Field_3:
        code = u'author'
        name = u'author'

    class Field_4:
        code = u'abstract'
        name = u'abstract'

    class Field_5:
        code = u'keyword'
        name = u'keyword'

    class Field_6:
        code = u'reportnumber'
        name = u'report number'

    class Field_7:
        code = u'subject'
        name = u'subject'

    class Field_8:
        code = u'reference'
        name = u'reference'

    class Field_9:
        code = u'fulltext'
        name = u'fulltext'

    class Field_10:
        code = u'collection'
        name = u'collection'

    class Field_11:
        code = u'division'
        name = u'division'

    class Field_12:
        code = u'year'
        name = u'year'

    class Field_13:
        code = u'experiment'
        name = u'experiment'

    class Field_14:
        code = u'recid'
        name = u'record ID'

    class Field_15:
        code = u'isbn'
        name = u'isbn'

    class Field_16:
        code = u'issn'
        name = u'issn'

    class Field_17:
        code = u'coden'
        name = u'coden'

    #class Field_18:
    #    code = u'doi'
    #    name = u'doi'

    class Field_19:
        code = u'journal'
        name = u'journal'

    class Field_20:
        code = u'collaboration'
        name = u'collaboration'

    class Field_21:
        code = u'affiliation'
        name = u'affiliation'

    class Field_22:
        code = u'exactauthor'
        name = u'exact author'

    class Field_23:
        code = u'datecreated'
        name = u'date created'

    class Field_24:
        code = u'datemodified'
        name = u'date modified'

    class Field_25:
        code = u'refersto'
        name = u'refers to'

    class Field_26:
        code = u'citedby'
        name = u'cited by'

    class Field_27:
        code = u'caption'
        name = u'caption'

    class Field_28:
        code = u'firstauthor'
        name = u'first author'

    class Field_29:
        code = u'exactfirstauthor'
        name = u'exact first author'

    class Field_30:
        code = u'authorcount'
        name = u'author count'

    class Field_31:
        code = u'rawref'
        name = u'reference to'

    class Field_32:
        code = u'exacttitle'
        name = u'exact title'

    class Field_33:
        code = u'authorityauthor'
        name = u'authority author'

    class Field_34:
        code = u'authorityinstitute'
        name = u'authority institution'

    class Field_35:
        code = u'authorityjournal'
        name = u'authority journal'

    class Field_36:
        code = u'authoritysubject'
        name = u'authority subject'

    class Field_37:
        code = u'itemcount'
        name = u'item count'

    class Field_38:
        code = u'filetype'
        name = u'file type'

    class Field_39:
        code = u'miscellaneous'
        name = u'miscellaneous'

    class Field_40:
        code = u'referstoexcludingselfcites'
        name = u'refers to excluding self cites'

    class Field_41:
        code = u'citedbyexcludingselfcites'
        name = u'cited by excluding self cites'

    class Field_42:
        code = u'cataloguer'
        name = u'cataloguer nickname'

    class Field_43:
        code = u'filename'
        name = u'file name'

    class Field_44:
        code = u'tag'
        name = u'tag'


class TagData(DataSet):

    class Tag_1:
        value = u'100__a'
        recjson_value = u'main_entry_personal_name.personal_name'
        name = u'first author name'

    class Tag_2:
        value = u'700__a'
        recjson_value = u'added_entry_personal_name.personal_name'
        name = u'additional author name'

    class Tag_3:
        value = u'245__%'
        recjson_value = u'title_statement'
        name = u'main title'

    class Tag_4:
        value = u'246__%'
        recjson_value = u'varying_form_of_title'
        name = u'additional title'

    class Tag_5:
        value = u'520__%'
        recjson_value = u'abstract'
        name = u'abstract'

    class Tag_6:
        value = u'6531_a'
        recjson_value = u'index_term_uncontrolled.uncontrolled_term'
        name = u'keyword'

    class Tag_7:
        value = u'037__a'
        recjson_value = u'source_of_acquisition.stock_number'
        name = u'primary report number'

    class Tag_8:
        value = u'088__a'
        recjson_value = u'report_number.report_number'
        name = u'additional report number'

    class Tag_9:
        value = u'909C0r'
        recjson_value = u'added_report_number'
        name = u'added report number'

    class Tag_10:
        value = u'999C5%'
        recjson_value = u'reference'
        name = u'reference'

    class Tag_11:
        value = u''
        recjson_value = u'_collections'
        name = u'collection identifier'

    class Tag_12:
        value = u'65017a'
        recjson_value = u'subject_added_entry_topical_term.topical_term_or_geographic_name_entry_element'
        name = u'main subject'

    class Tag_13:
        value = u'65027a'
        recjson_value = u'subject_additional.term'
        name = u'additional subject'

    class Tag_14:
        value = u'909C0p'
        recjson_value = u'division'
        name = u'division'

    class Tag_15:
        value = u'909C0y'
        recjson_value = u'year'
        name = u'year'

    class Tag_16:
        value = u'00%'
        recjson_value = u'agency_code,recid,version_id'
        name = u'00x'

    class Tag_17:
        value = u'01%'
        recjson_value = u''
        name = u'01x'

    class Tag_18:
        value = u'02%'
        recjson_value = u'oai,doi,isbn,issn,isn'
        name = u'02x'

    class Tag_19:
        value = u'03%'
        recjson_value = u'code_designation,system_control_number'
        name = u'03x'

    class Tag_20:
        value = u'04%'
        recjson_value = u'language,publishing_country'
        name = u'lang'

    class Tag_21:
        value = u'05%'
        recjson_value = u'library_of_congress_call_number'
        name = u'05x'

    class Tag_22:
        value = u'06%'
        recjson_value = u''
        name = u'06x'

    class Tag_23:
        value = u'07%'
        recjson_value = u''
        name = u'07x'

    class Tag_24:
        value = u'08%'
        recjson_value = u'dewey_decimal_classification_number,other_report_number,report_number,udc'
        name = u'08x'

    class Tag_25:
        value = u'09%'
        recjson_value = u''
        name = u'09x'

    class Tag_26:
        value = u'10%'
        recjson_value = u'authors'
        name = u'10x'

    class Tag_27:
        value = u'11%'
        recjson_value = u'corporate_name[0],meeting_name[0]'
        name = u'11x'

    class Tag_28:
        value = u'12%'
        recjson_value = u''
        name = u'12x'

    class Tag_29:
        value = u'13%'
        recjson_value = u''
        name = u'13x'

    class Tag_30:
        value = u'14%'
        recjson_value = u'main_title_statement,chronological_term'
        name = u'14x'

    class Tag_31:
        value = u'15%'
        recjson_value = u''
        name = u'15x'

    class Tag_32:
        value = u'16%'
        recjson_value = u''
        name = u'16x'

    class Tag_33:
        value = u'17%'
        recjson_value = u''
        name = u'17x'

    class Tag_34:
        value = u'18%'
        recjson_value = u'medium'
        name = u'18x'

    class Tag_35:
        value = u'19%'
        recjson_value = u''
        name = u'19x'

    class Tag_36:
        value = u'20%'
        recjson_value = u''
        name = u'20x'

    class Tag_37:
        value = u'21%'
        recjson_value = u'abbreviated_title'
        name = u'21x'

    class Tag_38:
        value = u'22%'
        recjson_value = u'title_key'
        name = u'22x'

    class Tag_39:
        value = u'23%'
        recjson_value = u''
        name = u'23x'

    class Tag_40:
        value = u'24%'
        recjson_value = u'title_additional,title_other,title,title_parallel,title_translation'
        name = u'24x'

    class Tag_41:
        value = u'25%'
        recjson_value = u'edition_statement'
        name = u'25x'

    class Tag_42:
        value = u'26%'
        recjson_value = u'imprint,prepublication'
        name = u'internal'

    class Tag_43:
        value = u'27%'
        recjson_value = u'address'
        name = u'27x'

    class Tag_44:
        value = u'28%'
        recjson_value = u''
        name = u'28x'

    class Tag_45:
        value = u'29%'
        recjson_value = u''
        name = u'29x'

    class Tag_46:
        value = u'30%'
        recjson_value = u'physical_description'
        name = u'pages'

    class Tag_47:
        value = u'31%'
        recjson_value = u'current_publication_frequency'
        name = u'31x'

    class Tag_48:
        value = u'32%'
        recjson_value = u''
        name = u'32x'

    class Tag_49:
        value = u'33%'
        recjson_value = u'content_type'
        name = u'33x'

    class Tag_50:
        value = u'34%'
        recjson_value = u'medium'
        name = u'34x'

    class Tag_51:
        value = u'35%'
        recjson_value = u''
        name = u'35x'

    class Tag_52:
        value = u'36%'
        recjson_value = u''
        name = u'36x'

    class Tag_53:
        value = u'37%'
        recjson_value = u''
        name = u'37x'

    class Tag_54:
        value = u'38%'
        recjson_value = u''
        name = u'38x'

    class Tag_55:
        value = u'39%'
        recjson_value = u''
        name = u'39x'

    class Tag_56:
        value = u'40%'
        recjson_value = u''
        name = u'40x'

    class Tag_57:
        value = u'41%'
        recjson_value = u''
        name = u'41x'

    class Tag_58:
        value = u'42%'
        recjson_value = u''
        name = u'42x'

    class Tag_59:
        value = u'43%'
        recjson_value = u''
        name = u'43x'

    class Tag_60:
        value = u'44%'
        recjson_value = u''
        name = u'44x'

    class Tag_61:
        value = u'45%'
        recjson_value = u''
        name = u'45x'

    class Tag_62:
        value = u'46%'
        recjson_value = u''
        name = u'46x'

    class Tag_63:
        value = u'47%'
        recjson_value = u''
        name = u'47x'

    class Tag_64:
        value = u'48%'
        recjson_value = u''
        name = u'48x'

    class Tag_65:
        value = u'49%'
        recjson_value = u'series'
        name = u'series'

    class Tag_66:
        value = u'50%'
        recjson_value = u'comment,dissertation_note,restriction_access,other_restriction_access'
        name = u'50x'

    class Tag_67:
        value = u'51%'
        recjson_value = u'time_and_place_of_event_note'
        name = u'51x'

    class Tag_68:
        value = u'52%'
        recjson_value = u'abstract'
        name = u'52x'

    class Tag_69:
        value = u'53%'
        recjson_value = u'funding_info'
        name = u'53x'

    class Tag_70:
        value = u'54%'
        recjson_value = u'copyright_information,language_note,license,source_of_acquisition'
        name = u'54x'

    class Tag_71:
        value = u'55%'
        recjson_value = u'cumulative_index'
        name = u'55x'

    class Tag_72:
        value = u'56%'
        recjson_value = u''
        name = u'56x'

    class Tag_73:
        value = u'57%'
        recjson_value = u''
        name = u'57x'

    class Tag_74:
        value = u'58%'
        recjson_value = u'action_note,source_of_description'
        name = u'58x'

    class Tag_75:
        value = u'59%'
        recjson_value = u'abstract_french,cern_bookshop_statistics,copyright,internal_notes,observation_french,slac_note,type'
        name = u'summary'

    class Tag_76:
        value = u'60%'
        recjson_value = u''
        name = u'60x'

    class Tag_77:
        value = u'61%'
        recjson_value = u''
        name = u'61x'

    class Tag_78:
        value = u'62%'
        recjson_value = u''
        name = u'62x'

    class Tag_79:
        value = u'63%'
        recjson_value = u''
        name = u'63x'

    class Tag_80:
        value = u'64%'
        recjson_value = u'publisher'
        name = u'64x'

    class Tag_81:
        value = u'65%'
        recjson_value = u'keywords'
        name = u'65x'

    class Tag_82:
        value = u'66%'
        recjson_value = u''
        name = u'66x'

    class Tag_83:
        value = u'67%'
        recjson_value = u'administrative_history,source_data_found'
        name = u'67x'

    class Tag_84:
        value = u'68%'
        recjson_value = u'public_general_note'
        name = u'68x'

    class Tag_85:
        value = u'69%'
        recjson_value = u'accelerator_experiment,cataloguer_info,classification_terms,observation,subject_indicator,thesaurus_terms,lexi_keyword'
        name = u'subject'

    class Tag_86:
        value = u'70%'
        recjson_value = u'contributor'
        name = u'70x'

    class Tag_87:
        value = u'71%'
        recjson_value = u'corporate_name[n],meeting_name[n]'
        name = u'71x'

    class Tag_88:
        value = u'72%'
        recjson_value = u'author_archive'
        name = u'author-ad'

    class Tag_89:
        value = u'73%'
        recjson_value = u''
        name = u'73x'

    class Tag_90:
        value = u'74%'
        recjson_value = u''
        name = u'74x'

    class Tag_91:
        value = u'75%'
        recjson_value = u''
        name = u'75x'

    class Tag_92:
        value = u'76%'
        recjson_value = u''
        name = u'76x'

    class Tag_93:
        value = u'77%'
        recjson_value = u'publication_info'
        name = u'77x'

    class Tag_94:
        value = u'78%'
        recjson_value = u''
        name = u'78x'

    class Tag_95:
        value = u'79%'
        recjson_value = u''
        name = u'79x'

    class Tag_96:
        value = u'80%'
        recjson_value = u''
        name = u'80x'

    class Tag_97:
        value = u'81%'
        recjson_value = u''
        name = u'81x'

    class Tag_98:
        value = u'82%'
        recjson_value = u''
        name = u'82x'

    class Tag_99:
        value = u'83%'
        recjson_value = u''
        name = u'83x'

    class Tag_100:
        value = u'84%'
        recjson_value = u''
        name = u'84x'

    class Tag_101:
        value = u'85%'
        recjson_value = u'location,email,email_message,electronic_location'
        name = u'electr'

    class Tag_102:
        value = u'86%'
        recjson_value = u''
        name = u'86x'

    class Tag_103:
        value = u'87%'
        recjson_value = u''
        name = u'87x'

    class Tag_104:
        value = u'88%'
        recjson_value = u''
        name = u'88x'

    class Tag_105:
        value = u'89%'
        recjson_value = u''
        name = u'89x'

    class Tag_106:
        value = u'90%'
        recjson_value = u'journal_info'
        name = u'publication'

    class Tag_107:
        value = u'91%'
        recjson_value = u'status_week,citation,universal_decimal_classification'
        name = u'pub-conf-cit'

    class Tag_108:
        value = u'92%'
        recjson_value = u'other_institution'
        name = u'92x'

    class Tag_109:
        value = u'93%'
        recjson_value = u''
        name = u'93x'

    class Tag_110:
        value = u'94%'
        recjson_value = u''
        name = u'94x'

    class Tag_111:
        value = u'95%'
        recjson_value = u''
        name = u'95x'

    class Tag_112:
        value = u'96%'
        recjson_value = u'aleph_linking_page,base,cataloguer_info,item,owner'
        name = u'catinfo'

    class Tag_113:
        value = u'97%'
        recjson_value = u'system_number'
        name = u'97x'

    class Tag_114:
        value = u'98%'
        recjson_value = u''
        name = u'98x'

    class Tag_115:
        value = u'8564_u'
        recjson_value = u'url.url'
        name = u'url'

    class Tag_116:
        value = u'909C0e'
        recjson_value = u'accelerator_experiment.experiment'
        name = u'experiment'

    class Tag_117:
        value = u'001'
        recjson_value = u'recid'
        name = u'record ID'

    class Tag_118:
        value = u'020__a'
        recjson_value = u'isbn'
        name = u'isbn'

    class Tag_119:
        value = u'022__a'
        recjson_value = u'issn'
        name = u'issn'

    class Tag_120:
        value = u'030__a'
        recjson_value = u''
        name = u'coden'

    class Tag_121:
        value = u'909C4a'
        recjson_value = u'journal_info.doi'
        name = u'doi'

    class Tag_122:
        value = u'850%'
        recjson_value = u''
        name = u'850x'

    class Tag_123:
        value = u'851%'
        recjson_value = u''
        name = u'851x'

    class Tag_124:
        value = u'852%'
        recjson_value = u'location'
        name = u'852x'

    class Tag_125:
        value = u'853%'
        recjson_value = u''
        name = u'853x'

    class Tag_126:
        value = u'854%'
        recjson_value = u''
        name = u'854x'

    class Tag_127:
        value = u'855%'
        recjson_value = u''
        name = u'855x'

    class Tag_128:
        value = u'857%'
        recjson_value = u''
        name = u'857x'

    class Tag_129:
        value = u'858%'
        recjson_value = u''
        name = u'858x'

    class Tag_130:
        value = u'859%'
        recjson_value = u'email_message'
        name = u'859x'

    class Tag_131:
        value = u'909C4%'
        recjson_value = u'journal_info'
        name = u'journal'

    class Tag_132:
        value = u'710__g'
        recjson_value = u'corporate_name[n].collaboration'
        name = u'collaboration'

    class Tag_133:
        value = u'100__u'
        recjson_value = u'authors[0].affiliation'
        name = u'first author affiliation'

    class Tag_134:
        value = u'700__u'
        recjson_value = u'contributor.affiliation'
        name = u'additional author affiliation'

    class Tag_135:
        value = u'8564_y'
        recjson_value = u'url.description'
        name = u'caption'

    class Tag_136:
        value = u'909C4c'
        recjson_value = u'journal_info.pagination'
        name = u'journal page'

    class Tag_137:
        value = u'909C4p'
        recjson_value = u'journal_info.title'
        name = u'journal title'

    class Tag_138:
        value = u'909C4v'
        recjson_value = u'journal_info.volume'
        name = u'journal volume'

    class Tag_139:
        value = u'909C4y'
        recjson_value = u'journal_info.year'
        name = u'journal year'

    class Tag_140:
        value = u'500__a'
        recjson_value = u'commnt'
        name = u'comment'

    class Tag_141:
        value = u'245__a'
        recjson_value = u'title.title'
        name = u'title'

    class Tag_142:
        value = u'245__a'
        recjson_value = u''
        name = u'main abstract'

    class Tag_143:
        value = u'595__a'
        recjson_value = u'internal_notes.internal_note'
        name = u'internal notes'

    class Tag_144:
        value = u'787%'
        recjson_value = u''
        name = u'other relationship entry'

    class Tag_146:
        value = u'400__a'
        recjson_value = u''
        name = u'authority: alternative personal name'

    class Tag_148:
        value = u'110__a'
        recjson_value = u'corporate_name[0].name'
        name = u'authority: organization main name'

    class Tag_149:
        value = u'410__a'
        recjson_value = u''
        name = u'organization alternative name'

    class Tag_150:
        value = u'510__a'
        recjson_value = u''
        name = u'organization main from other record'

    class Tag_151:
        value = u'130__a'
        recjson_value = u''
        name = u'authority: uniform title'

    class Tag_152:
        value = u'430__a'
        recjson_value = u''
        name = u'authority: uniform title alternatives'

    class Tag_153:
        value = u'530__a'
        recjson_value = u''
        name = u'authority: uniform title from other record'

    class Tag_154:
        value = u'150__a'
        recjson_value = u''
        name = u'authority: subject from other record'

    class Tag_155:
        value = u'450__a'
        recjson_value = u''
        name = u'authority: subject alternative name'

    class Tag_156:
        value = u'450__a'
        recjson_value = u''
        name = u'authority: subject main name'

    class Tag_157:
        value = u'031%'
        recjson_value = u''
        name = u'031x'

    class Tag_158:
        value = u'032%'
        recjson_value = u''
        name = u'032x'

    class Tag_159:
        value = u'033%'
        recjson_value = u'code_designation'
        name = u'033x'

    class Tag_160:
        value = u'034%'
        recjson_value = u''
        name = u'034x'

    class Tag_161:
        value = u'035%'
        recjson_value = u'system_control_number'
        name = u'035x'

    class Tag_162:
        value = u'036%'
        recjson_value = u''
        name = u'036x'

    class Tag_163:
        value = u'037%'
        recjson_value = u'primary_report_number'
        name = u'037x'

    class Tag_164:
        value = u'038%'
        recjson_value = u''
        name = u'038x'

    class Tag_165:
        value = u'080%'
        recjson_value = u'udc'
        name = u'080x'

    class Tag_166:
        value = u'082%'
        recjson_value = u'dewey_decimal_classification_number'
        name = u'082x'

    class Tag_167:
        value = u'083%'
        recjson_value = u''
        name = u'083x'

    class Tag_168:
        value = u'084%'
        recjson_value = u'other_report_number'
        name = u'084x'

    class Tag_169:
        value = u'085%'
        recjson_value = u''
        name = u'085x'

    class Tag_170:
        value = u'086%'
        recjson_value = u''
        name = u'086x'

    class Tag_171:
        value = u'240%'
        recjson_value = u''
        name = u'240x'

    class Tag_172:
        value = u'242%'
        recjson_value = u'title_translation'
        name = u'242x'

    class Tag_173:
        value = u'243%'
        recjson_value = u''
        name = u'243x'

    class Tag_174:
        value = u'244%'
        recjson_value = u''
        name = u'244x'

    class Tag_175:
        value = u'247%'
        recjson_value = u''
        name = u'247x'

    class Tag_176:
        value = u'521%'
        recjson_value = u''
        name = u'521x'

    class Tag_177:
        value = u'522%'
        recjson_value = u''
        name = u'522x'

    class Tag_178:
        value = u'524%'
        recjson_value = u''
        name = u'524x'

    class Tag_179:
        value = u'525%'
        recjson_value = u''
        name = u'525x'

    class Tag_180:
        value = u'526%'
        recjson_value = u''
        name = u'526x'

    class Tag_181:
        value = u'650%'
        recjson_value = u'subject'
        name = u'650x'

    class Tag_182:
        value = u'651%'
        recjson_value = u''
        name = u'651x'

    class Tag_183:
        value = u'6531_v'
        recjson_value = u'keywords.v'
        name = u'6531_v'

    class Tag_184:
        value = u'6531_y'
        recjson_value = u'keywords.y'
        name = u'6531_y'

    class Tag_185:
        value = u'6531_9'
        recjson_value = u'keywords.institute'
        name = u'6531_9'

    class Tag_186:
        value = u'654%'
        recjson_value = u''
        name = u'654x'

    class Tag_187:
        value = u'655%'
        recjson_value = u''
        name = u'655x'

    class Tag_188:
        value = u'656%'
        recjson_value = u''
        name = u'656x'

    class Tag_189:
        value = u'657%'
        recjson_value = u''
        name = u'657x'

    class Tag_190:
        value = u'658%'
        recjson_value = u''
        name = u'658x'

    class Tag_191:
        value = u'711%'
        recjson_value = u''
        name = u'711x'

    class Tag_192:
        value = u'900%'
        recjson_value = u'meeting_name'
        name = u'900x'

    class Tag_193:
        value = u'901%'
        recjson_value = u'affiliation'
        name = u'901x'

    class Tag_194:
        value = u'902%'
        recjson_value = u''
        name = u'902x'

    class Tag_195:
        value = u'903%'
        recjson_value = u''
        name = u'903x'

    class Tag_196:
        value = u'904%'
        recjson_value = u''
        name = u'904x'

    class Tag_197:
        value = u'905%'
        recjson_value = u''
        name = u'905x'

    class Tag_198:
        value = u'906%'
        recjson_value = u''
        name = u'906x'

    class Tag_199:
        value = u'907%'
        recjson_value = u''
        name = u'907x'

    class Tag_200:
        value = u'908%'
        recjson_value = u''
        name = u'908x'

    class Tag_201:
        value = u'909C1%'
        recjson_value = u'FIXME_project_info'
        name = u'909C1x'

    class Tag_202:
        value = u'909C5%'
        recjson_value = u'FIXME_909C5'
        name = u'909C5x'

    class Tag_203:
        value = u'909CS%'
        recjson_value = u'FIXME_909CS'
        name = u'909CSx'

    class Tag_204:
        value = u'909CO%'
        recjson_value = u'FIXME_OAI'
        name = u'909COx'

    class Tag_205:
        value = u'909CK%'
        recjson_value = u'FIXME_publishedin'
        name = u'909CKx'

    class Tag_206:
        value = u'909CP%'
        recjson_value = u'photo_information'
        name = u'909CPx'

    class Tag_207:
        value = u'981%'
        recjson_value = u''
        name = u'981x'

    class Tag_208:
        value = u'982%'
        recjson_value = u''
        name = u'982x'

    class Tag_209:
        value = u'983%'
        recjson_value = u''
        name = u'983x'

    class Tag_210:
        value = u'984%'
        recjson_value = u''
        name = u'984x'

    class Tag_211:
        value = u'985%'
        recjson_value = u''
        name = u'985x'

    class Tag_212:
        value = u'986%'
        recjson_value = u''
        name = u'986x'

    class Tag_213:
        value = u'987%'
        recjson_value = u''
        name = u'987x'

    class Tag_214:
        value = u'988%'
        recjson_value = u''
        name = u'988x'

    class Tag_215:
        value = u'989%'
        recjson_value = u''
        name = u'989x'

    class Tag_216:
        value = u'100__0'
        recjson_value = u''
        name = u'author control'

    class Tag_217:
        value = u'110__0'
        recjson_value = u''
        name = u'institute control'

    class Tag_218:
        value = u'130__0'
        recjson_value = u''
        name = u'journal control'

    class Tag_219:
        value = u'150__0'
        recjson_value = u''
        name = u'subject control'

    class Tag_220:
        value = u'260__0'
        recjson_value = u''
        name = u'additional institute control'

    class Tag_221:
        value = u'700__0'
        recjson_value = u''
        name = u'additional author control'

    class Tag_222:
        value = u'003'
        recjson_value = u'agency_code'
        name = u'agency code'

    class Tag_223:
        value = u'909C0b'
        recjson_value = u'FIXME_ALEPH_base_number'
        name = u'FIXME_ALEPH_base_number'

    class Tag_224:
        value = u'909C0a'
        recjson_value = u'FIXME_accelerator'
        name = u'FIXME_accelerator'

    class Tag_225:
        value = u'909C0o'
        recjson_value = u'FIXME_code'
        name = u'FIXME_code'

    class Tag_226:
        value = u'909C2%'
        recjson_value = u'FIXME_909C2'
        name = u'FIXME_909C2'


class FieldTagData(DataSet):

    class FieldTag_10_11:
        score = 100
        tag = TagData.Tag_11
        field = FieldData.Field_10

    class FieldTag_11_14:
        score = 100
        tag = TagData.Tag_14
        field = FieldData.Field_11

    class FieldTag_12_15:
        score = 10
        tag = TagData.Tag_15
        field = FieldData.Field_12

    class FieldTag_13_116:
        score = 10
        tag = TagData.Tag_116
        field = FieldData.Field_13

    class FieldTag_14_117:
        score = 100
        tag = TagData.Tag_117
        field = FieldData.Field_14

    class FieldTag_15_118:
        score = 100
        tag = TagData.Tag_118
        field = FieldData.Field_15

    class FieldTag_16_119:
        score = 100
        tag = TagData.Tag_119
        field = FieldData.Field_16

    class FieldTag_17_120:
        score = 100
        tag = TagData.Tag_120
        field = FieldData.Field_17

    #class FieldTag_18_120:
    #    score = 100
    #    tag = TagData.Tag_121
    #    field = FieldData.Field_18

    class FieldTag_19_131:
        score = 100
        tag = TagData.Tag_131
        field = FieldData.Field_19

    class FieldTag_20_132:
        score = 100
        tag = TagData.Tag_132
        field = FieldData.Field_20

    class FieldTag_21_133:
        score = 100
        tag = TagData.Tag_133
        field = FieldData.Field_21

    class FieldTag_21_134:
        score = 90
        tag = TagData.Tag_134
        field = FieldData.Field_21

    class FieldTag_22_1:
        score = 100
        tag = TagData.Tag_1
        field = FieldData.Field_22

    class FieldTag_22_2:
        score = 90
        tag = TagData.Tag_2
        field = FieldData.Field_22

    class FieldTag_27_135:
        score = 100
        tag = TagData.Tag_135
        field = FieldData.Field_27

    class FieldTag_28_1:
        score = 100
        tag = TagData.Tag_1
        field = FieldData.Field_28

    class FieldTag_29_1:
        score = 100
        tag = TagData.Tag_1
        field = FieldData.Field_29

    class FieldTag_2_3:
        score = 100
        tag = TagData.Tag_3
        field = FieldData.Field_2

    class FieldTag_2_4:
        score = 90
        tag = TagData.Tag_4
        field = FieldData.Field_2

    class FieldTag_30_1:
        score = 100
        tag = TagData.Tag_1
        field = FieldData.Field_30

    class FieldTag_30_2:
        score = 90
        tag = TagData.Tag_2
        field = FieldData.Field_30

    class FieldTag_32_3:
        score = 100
        tag = TagData.Tag_3
        field = FieldData.Field_32

    class FieldTag_32_4:
        score = 90
        tag = TagData.Tag_4
        field = FieldData.Field_32

    class FieldTag_3_1:
        score = 100
        tag = TagData.Tag_1
        field = FieldData.Field_3

    class FieldTag_3_2:
        score = 90
        tag = TagData.Tag_2
        field = FieldData.Field_3

    class FieldTag_4_5:
        score = 100
        tag = TagData.Tag_5
        field = FieldData.Field_4

    class FieldTag_5_6:
        score = 100
        tag = TagData.Tag_6
        field = FieldData.Field_5

    class FieldTag_6_7:
        score = 30
        tag = TagData.Tag_7
        field = FieldData.Field_6

    class FieldTag_6_8:
        score = 10
        tag = TagData.Tag_8
        field = FieldData.Field_6

    class FieldTag_6_9:
        score = 20
        tag = TagData.Tag_9
        field = FieldData.Field_6

    class FieldTag_7_12:
        score = 100
        tag = TagData.Tag_12
        field = FieldData.Field_7

    class FieldTag_7_13:
        score = 90
        tag = TagData.Tag_13
        field = FieldData.Field_7

    class FieldTag_8_10:
        score = 100
        tag = TagData.Tag_10
        field = FieldData.Field_8

    class FieldTag_9_115:
        score = 100
        tag = TagData.Tag_115
        field = FieldData.Field_9

    class FieldTag_33_1:
        score = 100
        tag = TagData.Tag_1
        field = FieldData.Field_33

    class FieldTag_33_146:
        score = 100
        tag = TagData.Tag_146
        field = FieldData.Field_33

    class FieldTag_33_140:
        score = 100
        tag = TagData.Tag_140
        field = FieldData.Field_33

    class FieldTag_34_148:
        score = 100
        tag = TagData.Tag_148
        field = FieldData.Field_34

    class FieldTag_34_149:
        score = 100
        tag = TagData.Tag_149
        field = FieldData.Field_34

    class FieldTag_34_150:
        score = 100
        tag = TagData.Tag_150
        field = FieldData.Field_34

    class FieldTag_35_151:
        score = 100
        tag = TagData.Tag_151
        field = FieldData.Field_35

    class FieldTag_35_152:
        score = 100
        tag = TagData.Tag_152
        field = FieldData.Field_35

    class FieldTag_35_153:
        score = 100
        tag = TagData.Tag_153
        field = FieldData.Field_35

    class FieldTag_36_154:
        score = 100
        tag = TagData.Tag_154
        field = FieldData.Field_36

    class FieldTag_36_155:
        score = 100
        tag = TagData.Tag_155
        field = FieldData.Field_36

    class FieldTag_36_156:
        score = 100
        tag = TagData.Tag_156
        field = FieldData.Field_36

    class FieldTag_39_17:
        score = 10
        tag = TagData.Tag_17
        field = FieldData.Field_39

    class FieldTag_39_18:
        score = 10
        tag = TagData.Tag_18
        field = FieldData.Field_39

    class FieldTag_39_157:
        score = 10
        tag = TagData.Tag_157
        field = FieldData.Field_39

    class FieldTag_39_158:
        score = 10
        tag = TagData.Tag_158
        field = FieldData.Field_39

    class FieldTag_39_159:
        score = 10
        tag = TagData.Tag_159
        field = FieldData.Field_39

    class FieldTag_39_160:
        score = 10
        tag = TagData.Tag_160
        field = FieldData.Field_39

    class FieldTag_39_161:
        score = 10
        tag = TagData.Tag_161
        field = FieldData.Field_39

    class FieldTag_39_162:
        score = 10
        tag = TagData.Tag_162
        field = FieldData.Field_39

    class FieldTag_39_163:
        score = 10
        tag = TagData.Tag_163
        field = FieldData.Field_39

    class FieldTag_39_164:
        score = 10
        tag = TagData.Tag_164
        field = FieldData.Field_39

    class FieldTag_39_20:
        score = 10
        tag = TagData.Tag_20
        field = FieldData.Field_39

    class FieldTag_39_21:
        score = 10
        tag = TagData.Tag_21
        field = FieldData.Field_39

    class FieldTag_39_22:
        score = 10
        tag = TagData.Tag_22
        field = FieldData.Field_39

    class FieldTag_39_23:
        score = 10
        tag = TagData.Tag_23
        field = FieldData.Field_39

    class FieldTag_39_165:
        score = 10
        tag = TagData.Tag_165
        field = FieldData.Field_39

    class FieldTag_39_166:
        score = 10
        tag = TagData.Tag_166
        field = FieldData.Field_39

    class FieldTag_39_167:
        score = 10
        tag = TagData.Tag_167
        field = FieldData.Field_39

    class FieldTag_39_168:
        score = 10
        tag = TagData.Tag_168
        field = FieldData.Field_39

    class FieldTag_39_169:
        score = 10
        tag = TagData.Tag_169
        field = FieldData.Field_39

    class FieldTag_39_170:
        score = 10
        tag = TagData.Tag_170
        field = FieldData.Field_39

    class FieldTag_39_25:
        score = 10
        tag = TagData.Tag_25
        field = FieldData.Field_39

    class FieldTag_39_27:
        score = 10
        tag = TagData.Tag_27
        field = FieldData.Field_39

    class FieldTag_39_28:
        score = 10
        tag = TagData.Tag_28
        field = FieldData.Field_39

    class FieldTag_39_29:
        score = 10
        tag = TagData.Tag_29
        field = FieldData.Field_39

    class FieldTag_39_30:
        score = 10
        tag = TagData.Tag_30
        field = FieldData.Field_39

    class FieldTag_39_31:
        score = 10
        tag = TagData.Tag_31
        field = FieldData.Field_39

    class FieldTag_39_32:
        score = 10
        tag = TagData.Tag_32
        field = FieldData.Field_39

    class FieldTag_39_33:
        score = 10
        tag = TagData.Tag_33
        field = FieldData.Field_39

    class FieldTag_39_34:
        score = 10
        tag = TagData.Tag_34
        field = FieldData.Field_39

    class FieldTag_39_35:
        score = 10
        tag = TagData.Tag_35
        field = FieldData.Field_39

    class FieldTag_39_36:
        score = 10
        tag = TagData.Tag_36
        field = FieldData.Field_39

    class FieldTag_39_37:
        score = 10
        tag = TagData.Tag_37
        field = FieldData.Field_39

    class FieldTag_39_38:
        score = 10
        tag = TagData.Tag_38
        field = FieldData.Field_39

    class FieldTag_39_39:
        score = 10
        tag = TagData.Tag_39
        field = FieldData.Field_39

    class FieldTag_39_171:
        score = 10
        tag = TagData.Tag_171
        field = FieldData.Field_39

    class FieldTag_39_172:
        score = 10
        tag = TagData.Tag_172
        field = FieldData.Field_39

    class FieldTag_39_173:
        score = 10
        tag = TagData.Tag_173
        field = FieldData.Field_39

    class FieldTag_39_174:
        score = 10
        tag = TagData.Tag_174
        field = FieldData.Field_39

    class FieldTag_39_175:
        score = 10
        tag = TagData.Tag_175
        field = FieldData.Field_39

    class FieldTag_39_41:
        score = 10
        tag = TagData.Tag_41
        field = FieldData.Field_39

    class FieldTag_39_42:
        score = 10
        tag = TagData.Tag_42
        field = FieldData.Field_39

    class FieldTag_39_43:
        score = 10
        tag = TagData.Tag_43
        field = FieldData.Field_39

    class FieldTag_39_44:
        score = 10
        tag = TagData.Tag_44
        field = FieldData.Field_39

    class FieldTag_39_45:
        score = 10
        tag = TagData.Tag_45
        field = FieldData.Field_39

    class FieldTag_39_46:
        score = 10
        tag = TagData.Tag_46
        field = FieldData.Field_39

    class FieldTag_39_47:
        score = 10
        tag = TagData.Tag_47
        field = FieldData.Field_39

    class FieldTag_39_48:
        score = 10
        tag = TagData.Tag_48
        field = FieldData.Field_39

    class FieldTag_39_49:
        score = 10
        tag = TagData.Tag_49
        field = FieldData.Field_39

    class FieldTag_39_50:
        score = 10
        tag = TagData.Tag_50
        field = FieldData.Field_39

    class FieldTag_39_51:
        score = 10
        tag = TagData.Tag_51
        field = FieldData.Field_39

    class FieldTag_39_52:
        score = 10
        tag = TagData.Tag_52
        field = FieldData.Field_39

    class FieldTag_39_53:
        score = 10
        tag = TagData.Tag_53
        field = FieldData.Field_39

    class FieldTag_39_54:
        score = 10
        tag = TagData.Tag_54
        field = FieldData.Field_39

    class FieldTag_39_55:
        score = 10
        tag = TagData.Tag_55
        field = FieldData.Field_39

    class FieldTag_39_56:
        score = 10
        tag = TagData.Tag_56
        field = FieldData.Field_39

    class FieldTag_39_57:
        score = 10
        tag = TagData.Tag_57
        field = FieldData.Field_39

    class FieldTag_39_58:
        score = 10
        tag = TagData.Tag_58
        field = FieldData.Field_39

    class FieldTag_39_59:
        score = 10
        tag = TagData.Tag_59
        field = FieldData.Field_39

    class FieldTag_39_60:
        score = 10
        tag = TagData.Tag_60
        field = FieldData.Field_39

    class FieldTag_39_61:
        score = 10
        tag = TagData.Tag_61
        field = FieldData.Field_39

    class FieldTag_39_62:
        score = 10
        tag = TagData.Tag_62
        field = FieldData.Field_39

    class FieldTag_39_63:
        score = 10
        tag = TagData.Tag_63
        field = FieldData.Field_39

    class FieldTag_39_64:
        score = 10
        tag = TagData.Tag_64
        field = FieldData.Field_39

    class FieldTag_39_65:
        score = 10
        tag = TagData.Tag_65
        field = FieldData.Field_39

    class FieldTag_39_66:
        score = 10
        tag = TagData.Tag_66
        field = FieldData.Field_39

    class FieldTag_39_67:
        score = 10
        tag = TagData.Tag_67
        field = FieldData.Field_39

    class FieldTag_39_176:
        score = 10
        tag = TagData.Tag_176
        field = FieldData.Field_39

    class FieldTag_39_177:
        score = 10
        tag = TagData.Tag_177
        field = FieldData.Field_39

    class FieldTag_39_178:
        score = 10
        tag = TagData.Tag_178
        field = FieldData.Field_39

    class FieldTag_39_179:
        score = 10
        tag = TagData.Tag_179
        field = FieldData.Field_39

    class FieldTag_39_180:
        score = 10
        tag = TagData.Tag_180
        field = FieldData.Field_39

    class FieldTag_39_69:
        score = 10
        tag = TagData.Tag_69
        field = FieldData.Field_39

    class FieldTag_39_70:
        score = 10
        tag = TagData.Tag_70
        field = FieldData.Field_39

    class FieldTag_39_71:
        score = 10
        tag = TagData.Tag_71
        field = FieldData.Field_39

    class FieldTag_39_72:
        score = 10
        tag = TagData.Tag_72
        field = FieldData.Field_39

    class FieldTag_39_73:
        score = 10
        tag = TagData.Tag_73
        field = FieldData.Field_39

    class FieldTag_39_74:
        score = 10
        tag = TagData.Tag_74
        field = FieldData.Field_39

    class FieldTag_39_75:
        score = 10
        tag = TagData.Tag_75
        field = FieldData.Field_39

    class FieldTag_39_76:
        score = 10
        tag = TagData.Tag_76
        field = FieldData.Field_39

    class FieldTag_39_77:
        score = 10
        tag = TagData.Tag_77
        field = FieldData.Field_39

    class FieldTag_39_78:
        score = 10
        tag = TagData.Tag_78
        field = FieldData.Field_39

    class FieldTag_39_79:
        score = 10
        tag = TagData.Tag_79
        field = FieldData.Field_39

    class FieldTag_39_80:
        score = 10
        tag = TagData.Tag_80
        field = FieldData.Field_39

    class FieldTag_39_181:
        score = 10
        tag = TagData.Tag_181
        field = FieldData.Field_39

    class FieldTag_39_182:
        score = 10
        tag = TagData.Tag_182
        field = FieldData.Field_39

    class FieldTag_39_183:
        score = 10
        tag = TagData.Tag_183
        field = FieldData.Field_39

    class FieldTag_39_184:
        score = 10
        tag = TagData.Tag_184
        field = FieldData.Field_39

    class FieldTag_39_185:
        score = 10
        tag = TagData.Tag_185
        field = FieldData.Field_39

    class FieldTag_39_186:
        score = 10
        tag = TagData.Tag_186
        field = FieldData.Field_39

    class FieldTag_39_82:
        score = 10
        tag = TagData.Tag_82
        field = FieldData.Field_39

    class FieldTag_39_83:
        score = 10
        tag = TagData.Tag_83
        field = FieldData.Field_39

    class FieldTag_39_84:
        score = 10
        tag = TagData.Tag_84
        field = FieldData.Field_39

    class FieldTag_39_85:
        score = 10
        tag = TagData.Tag_85
        field = FieldData.Field_39

    class FieldTag_39_187:
        score = 10
        tag = TagData.Tag_187
        field = FieldData.Field_39

    class FieldTag_39_88:
        score = 10
        tag = TagData.Tag_88
        field = FieldData.Field_39

    class FieldTag_39_89:
        score = 10
        tag = TagData.Tag_89
        field = FieldData.Field_39

    class FieldTag_39_90:
        score = 10
        tag = TagData.Tag_90
        field = FieldData.Field_39

    class FieldTag_39_91:
        score = 10
        tag = TagData.Tag_91
        field = FieldData.Field_39

    class FieldTag_39_92:
        score = 10
        tag = TagData.Tag_92
        field = FieldData.Field_39

    class FieldTag_39_93:
        score = 10
        tag = TagData.Tag_93
        field = FieldData.Field_39

    class FieldTag_39_94:
        score = 10
        tag = TagData.Tag_94
        field = FieldData.Field_39

    class FieldTag_39_95:
        score = 10
        tag = TagData.Tag_95
        field = FieldData.Field_39

    class FieldTag_39_96:
        score = 10
        tag = TagData.Tag_96
        field = FieldData.Field_39

    class FieldTag_39_97:
        score = 10
        tag = TagData.Tag_97
        field = FieldData.Field_39

    class FieldTag_39_98:
        score = 10
        tag = TagData.Tag_98
        field = FieldData.Field_39

    class FieldTag_39_99:
        score = 10
        tag = TagData.Tag_99
        field = FieldData.Field_39

    class FieldTag_39_100:
        score = 10
        tag = TagData.Tag_100
        field = FieldData.Field_39

    class FieldTag_39_102:
        score = 10
        tag = TagData.Tag_102
        field = FieldData.Field_39

    class FieldTag_39_103:
        score = 10
        tag = TagData.Tag_103
        field = FieldData.Field_39

    class FieldTag_39_104:
        score = 10
        tag = TagData.Tag_104
        field = FieldData.Field_39

    class FieldTag_39_105:
        score = 10
        tag = TagData.Tag_105
        field = FieldData.Field_39

    class FieldTag_39_188:
        score = 10
        tag = TagData.Tag_188
        field = FieldData.Field_39

    class FieldTag_39_189:
        score = 10
        tag = TagData.Tag_189
        field = FieldData.Field_39

    class FieldTag_39_190:
        score = 10
        tag = TagData.Tag_190
        field = FieldData.Field_39

    class FieldTag_39_191:
        score = 10
        tag = TagData.Tag_191
        field = FieldData.Field_39

    class FieldTag_39_192:
        score = 10
        tag = TagData.Tag_192
        field = FieldData.Field_39

    class FieldTag_39_193:
        score = 10
        tag = TagData.Tag_193
        field = FieldData.Field_39

    class FieldTag_39_194:
        score = 10
        tag = TagData.Tag_194
        field = FieldData.Field_39

    class FieldTag_39_195:
        score = 10
        tag = TagData.Tag_195
        field = FieldData.Field_39

    class FieldTag_39_196:
        score = 10
        tag = TagData.Tag_196
        field = FieldData.Field_39

    class FieldTag_39_107:
        score = 10
        tag = TagData.Tag_107
        field = FieldData.Field_39

    class FieldTag_39_108:
        score = 10
        tag = TagData.Tag_108
        field = FieldData.Field_39

    class FieldTag_39_109:
        score = 10
        tag = TagData.Tag_109
        field = FieldData.Field_39

    class FieldTag_39_110:
        score = 10
        tag = TagData.Tag_110
        field = FieldData.Field_39

    class FieldTag_39_111:
        score = 10
        tag = TagData.Tag_111
        field = FieldData.Field_39

    class FieldTag_39_112:
        score = 10
        tag = TagData.Tag_112
        field = FieldData.Field_39

    class FieldTag_39_113:
        score = 10
        tag = TagData.Tag_113
        field = FieldData.Field_39

    class FieldTag_39_197:
        score = 10
        tag = TagData.Tag_197
        field = FieldData.Field_39

    class FieldTag_39_198:
        score = 10
        tag = TagData.Tag_198
        field = FieldData.Field_39

    class FieldTag_39_199:
        score = 10
        tag = TagData.Tag_199
        field = FieldData.Field_39

    class FieldTag_39_200:
        score = 10
        tag = TagData.Tag_200
        field = FieldData.Field_39

    class FieldTag_39_201:
        score = 10
        tag = TagData.Tag_201
        field = FieldData.Field_39

    class FieldTag_39_202:
        score = 10
        tag = TagData.Tag_202
        field = FieldData.Field_39

    class FieldTag_39_203:
        score = 10
        tag = TagData.Tag_203
        field = FieldData.Field_39

    class FieldTag_39_204:
        score = 10
        tag = TagData.Tag_204
        field = FieldData.Field_39

    class FieldTag_39_205:
        score = 10
        tag = TagData.Tag_205
        field = FieldData.Field_39

    class FieldTag_39_206:
        score = 10
        tag = TagData.Tag_206
        field = FieldData.Field_39

    class FieldTag_39_207:
        score = 10
        tag = TagData.Tag_207
        field = FieldData.Field_39

    class FieldTag_39_208:
        score = 10
        tag = TagData.Tag_208
        field = FieldData.Field_39

    class FieldTag_39_209:
        score = 10
        tag = TagData.Tag_209
        field = FieldData.Field_39

    class FieldTag_39_210:
        score = 10
        tag = TagData.Tag_210
        field = FieldData.Field_39

    class FieldTag_39_211:
        score = 10
        tag = TagData.Tag_211
        field = FieldData.Field_39

    class FieldTag_39_212:
        score = 10
        tag = TagData.Tag_212
        field = FieldData.Field_39

    class FieldTag_39_213:
        score = 10
        tag = TagData.Tag_213
        field = FieldData.Field_39

    class FieldTag_39_214:
        score = 10
        tag = TagData.Tag_214
        field = FieldData.Field_39

    class FieldTag_39_215:
        score = 10
        tag = TagData.Tag_215
        field = FieldData.Field_39

    class FieldTag_39_122:
        score = 10
        tag = TagData.Tag_122
        field = FieldData.Field_39

    class FieldTag_39_123:
        score = 10
        tag = TagData.Tag_123
        field = FieldData.Field_39

    class FieldTag_39_124:
        score = 10
        tag = TagData.Tag_124
        field = FieldData.Field_39

    class FieldTag_39_125:
        score = 10
        tag = TagData.Tag_125
        field = FieldData.Field_39

    class FieldTag_39_126:
        score = 10
        tag = TagData.Tag_126
        field = FieldData.Field_39

    class FieldTag_39_127:
        score = 10
        tag = TagData.Tag_127
        field = FieldData.Field_39

    class FieldTag_39_128:
        score = 10
        tag = TagData.Tag_128
        field = FieldData.Field_39

    class FieldTag_39_129:
        score = 10
        tag = TagData.Tag_129
        field = FieldData.Field_39

    class FieldTag_39_130:
        score = 10
        tag = TagData.Tag_130
        field = FieldData.Field_39

    class FieldTag_39_1:
        score = 10
        tag = TagData.Tag_1
        field = FieldData.Field_39

    class FieldTag_39_2:
        score = 10
        tag = TagData.Tag_2
        field = FieldData.Field_39

    class FieldTag_39_216:
        score = 10
        tag = TagData.Tag_216
        field = FieldData.Field_39

    class FieldTag_39_217:
        score = 10
        tag = TagData.Tag_217
        field = FieldData.Field_39

    class FieldTag_39_218:
        score = 10
        tag = TagData.Tag_218
        field = FieldData.Field_39

    class FieldTag_39_219:
        score = 10
        tag = TagData.Tag_219
        field = FieldData.Field_39

    class FieldTag_39_220:
        score = 10
        tag = TagData.Tag_220
        field = FieldData.Field_39

    class FieldTag_39_221:
        score = 10
        tag = TagData.Tag_221
        field = FieldData.Field_39

    class FieldTag_39_223:
        score = 10
        tag = TagData.Tag_223
        field = FieldData.Field_39

    class FieldTag_39_224:
        score = 10
        tag = TagData.Tag_224
        field = FieldData.Field_39

    class FieldTag_39_225:
        score = 10
        tag = TagData.Tag_225
        field = FieldData.Field_39

    class FieldTag_39_226:
        score = 10
        tag = TagData.Tag_226
        field = FieldData.Field_39
