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
"""BibIndexCountryTokenizer: tokenizer for country names.
   Will look at tags '100__u' and '700__u' of the record, then at tags '371__d'
   and '371__g' (country name and code) of the affiliateted institutes.
"""

import re
from invenio.search_engine_utils import get_fieldvalues
from invenio.docextract_record import get_record
from invenio.bibindex_tokenizers.BibIndexMultiFieldTokenizer import (
    BibIndexMultiFieldTokenizer,
)
from invenio.search_engine import (
    search_pattern,
    get_collection_reclist
)
from invenio.bibknowledge import (
    get_kb_mapping,
    kb_mapping_exists
)
from invenio.intbitset import intbitset
from invenio.bibindex_engine_config import CFG_BIBINDEX_INDEX_TABLE_TYPE
from invenio.bibindex_engine_washer import remove_stopwords
from invenio.config import CFG_WEBSEARCH_INSTITUTION_COLLECTIONS


class BibIndexCountryTokenizer(BibIndexMultiFieldTokenizer):
    """This tokenizer returns the countries of the institutions affiliated
       with the authors of the publication given by recID.

       Uses KB COUNTRYCODE-TO-COUNTRY

       Assumes that:
       * COUNTRYCODE-TO-COUNTRY is a complete, one-to-one, list of rules
         "country code" --> "country name"
       * the value of the 371__d and 371__g tags in the institution records
         are contained also in the COUNTRYCODE-TO-COUNTRY kb
    """

    # 100__u: first author affiliation (es. INFN di Padova, Italy)
    # 700__u: non-first authors affiliation
    institution_tags = ['100__u', '700__u']
    institution_name_field = "110__u"
    # 371__d: full name of the country (es. Italy)
    # 371__g: country code (es. IT)
    # 371__x: flag for secondary address (es. secondary)
    address_field = '371'
    country_name_subfield = 'd'
    country_code_subfield = 'g'
    secondary_address_subfield = 'x'

    kb_country_codes = "COUNTRYCODE-TO-COUNTRY"

    re_words = re.compile(r"[\w']+")

    def __init__(self, stemming_language=None, remove_stopwords=False,
                 remove_html_markup=False, remove_latex_markup=False):
        self.remove_stopwords = remove_stopwords

    def _tokenize_from_country_name_tag(self, instID):
        """Get country name and country code tokens reading the
           country_name_tag tag from record instID.
           Returns a list of tokens (empty if something fails)
        """
        tokens = []
        record = get_record(instID)

        # Read the country name tags that are not marked as secondary
        country_name_list = []
        for field in record[self.address_field]:
            if "secondary" not in field.get_subfield_values(
                    self.secondary_address_subfield):
                country_name_list += field.get_subfield_values(
                    self.country_name_subfield
                )

        country_name_list = [s.encode('utf-8') for s in country_name_list]

        for country_name in country_name_list:
            # Find the country code using KB
            kb_country_code = get_kb_mapping(
                kb_name=self.kb_country_codes,
                value=country_name
            )
            if kb_country_code:
                country_code = kb_country_code["key"]

                if country_name and country_code:
                    tokens += [country_name, country_code]

        return tokens

    def _tokenize_from_country_code_tag(self, instID):
        """Get country name and country code tokens reading the
           country_code_tag tag from record instID.
           Returns a list of tokens (empty if something fails)
        """
        tokens = []
        record = get_record(instID)

        # Read the country code tags that are not marked as secondary
        country_code_list = []
        for field in record[self.address_field]:
            if "secondary" not in field.get_subfield_values(
                    self.secondary_address_subfield):
                country_code_list += field.get_subfield_values(
                    self.country_code_subfield
                )

        country_code_list = [s.encode('utf-8') for s in country_code_list]

        for country_code in country_code_list:
            # Find the country name using KB
            kb_country_name = get_kb_mapping(
                kb_name=self.kb_country_codes,
                key=country_code
            )
            if kb_country_name:
                country_name = kb_country_name["value"]

                if country_name and country_code:
                    tokens += [country_name, country_code]

        return tokens

    def tokenize_for_phrases(self, recID):
        """Get the country names and country codes of the institutions
           affiliated with the authors of the publication
        """

        # Get the name of the institution affiliated
        institution_names = []
        for tag in self.institution_tags:
            institution_names += get_fieldvalues(recID, tag)

        # Get the hitset of all the institutes
        institution_collection_hitset = intbitset([])
        for collection in CFG_WEBSEARCH_INSTITUTION_COLLECTIONS:
            institution_collection_hitset += get_collection_reclist(collection)

        # Search for the institution name and get a list of institution ids
        institution_ids = intbitset([])
        for name in institution_names:
            result_hitset = search_pattern(
                p=name,
                f=self.institution_name_field
            )
            institution_hitset = result_hitset & institution_collection_hitset
            institution_ids += list(institution_hitset)

        # Get the country tokens
        tokens = []
        for instID in institution_ids:
            tokens += self._tokenize_from_country_name_tag(instID)
            tokens += self._tokenize_from_country_code_tag(instID)

        # Remove duplicates
        tokens = list(set(tokens))

        return tokens

    def tokenize_for_words(self, recID):
        """Get the words componing the country names and country codes of the
           institutions affiliated with the authors of the publication
        """

        # Splits phrase tokens
        phrase_tokens = self.tokenize_for_phrases(recID)
        tokens = []
        for phrase in phrase_tokens:
            # If phrase is a country code be careful, because codes like IT
            # may be removed by remove_stopwords()
            if kb_mapping_exists(self.kb_country_codes, phrase):
                tokens.append(phrase)
            else:
                word_list = self.re_words.findall(phrase)
                for word in word_list:
                    word = remove_stopwords(word, self.remove_stopwords)
                    if word:
                        tokens.append(word)

        # Remove duplicates
        tokens = list(set(tokens))

        return tokens

    def tokenize_for_pairs(self, recID):
        """Get the pairs componing the country names and country codes of the
           institutions affiliated with the authors of the publication
        """

        # Splits phrase tokens
        phrase_tokens = self.tokenize_for_phrases(recID)
        tokens = []
        for phrase in phrase_tokens:
            word_list = self.re_words.findall(phrase)
            last_word = ""
            for word in word_list:
                word = remove_stopwords(word, self.remove_stopwords)
                if word:
                    if last_word:
                        tokens.append(last_word+" "+word)
                    last_word = word

        # Remove duplicates
        tokens = list(set(tokens))

        return tokens

    def get_tokenizing_function(self, wordtable_type):
        """Picks correct tokenize_for_xxx function depending on type of
           tokenization (wordtable_type)
        """
        if wordtable_type == CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]:
            return self.tokenize_for_words
        elif wordtable_type == CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"]:
            return self.tokenize_for_pairs
        elif wordtable_type == CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]:
            return self.tokenize_for_phrases
