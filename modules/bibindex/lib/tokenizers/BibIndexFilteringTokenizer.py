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
from invenio.search_engine import get_record
from invenio.bibrecord import record_get_field_instances
from invenio.bibindex_tokenizers.BibIndexMultiFieldTokenizer import BibIndexMultiFieldTokenizer


class BibIndexFilteringTokenizer(BibIndexMultiFieldTokenizer):

    """
        This tokenizer would tokenize phrases from tag
        only if another tag was present in the record's metadata,
        for example it would tokenize phrases from 100__a
        only if 100__u was found in the record's metadata.

        This tokenizer is abstract and it shouldn't be used
        for indexes. Insted of using this tokenizer one can
        create another tokenizer iheriting after this one.

        To create new tokenizer based on BibIndexFilteringTokenizer
        you need to specify rules of tokenizing in self.rules
        property.

        Examples:
        1) Let's say we want to tokenize data only from 100__a if 100__u is present:
            set: self.rules = (('100__a', 'u', ''),)
        2) We want to tokenize data from '0247_a' if '0247_2' == 'DOI':
            set: self.rules = (('0247_2', '2', 'DOI'),)
        3) We want to tokenize data from '0247_a' if '0247_2' == 'DOI' and all data
           from '100__a' with no constraints:
           set: self.rules = (('0247_2', '2', 'DOI'), ('100__a', '', ''))

        Definition of 'rules' tuple:
        (tag_to_take_phrases_from, value_of_sub_tag or '', necessary_value_of_sub_tag or '')

        Note: there is no get_tokenizing_function() to make this tokenizer abstract.
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        self.rules = ()

    def tokenize(self, recID):
        phrases = []
        try:
            rec = get_record(recID)

            for rule in self.rules:
                tag_to_index, necessary_tag, necessary_value = rule
                core_tag = tag_to_index[0:3]
                ind = tag_to_index[3:5]
                sub_tag = tag_to_index[5]

                fields = [dict(instance[0])
                          for instance in record_get_field_instances(rec, core_tag, ind[0], ind[1])]
                for field in fields:
                    tag_condition = necessary_tag and field.has_key(
                        necessary_tag) or necessary_tag == ''
                    value_condition = necessary_value and field.get(necessary_tag, '') == necessary_value or \
                        necessary_value == ''
                    if tag_condition and field.has_key(sub_tag) and value_condition:
                        phrases.append(field[sub_tag])
            return phrases
        except KeyError:
            return []
        return phrases

    def tokenize_via_recjson(self, recID):
        """
        TODO: implementation needs to be introduced
        in order to work with non-marc standards.
        """
        return []
