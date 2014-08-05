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
"""BibIndexDefaultTokenizer: useful for almost all indexes.
   It performs standard tokenization. It splits phrases into words/pairs or doesnt split at all, strips accents,
   removes alphanumeric characters and html and latex markup if we want to. Also can stem words for a given language.
"""

from invenio.bibindex_engine_config import \
    CFG_BIBINDEX_INDEX_TABLE_TYPE
from invenio.htmlutils import remove_html_markup as do_remove_html_markup
from invenio.textutils import wash_for_utf8, strip_accents
from invenio.bibindex_engine_washer import \
    lower_index_term, \
    remove_latex_markup as do_remove_latex_markup, \
    apply_stemming, \
    remove_stopwords as do_remove_stopwords, \
    length_check
from invenio.bibindex_engine_utils import latex_formula_re, \
    re_block_punctuation_begin, \
    re_block_punctuation_end, \
    re_punctuation, \
    re_separators, \
    re_arxiv
from invenio.bibindex_tokenizers.BibIndexStringTokenizer import \
    BibIndexStringTokenizer


class BibIndexDefaultTokenizer(BibIndexStringTokenizer):

    """
        It's a standard tokenizer. It is useful for most of the indexes.
        Its behaviour depends on stemming, remove stopwords, remove html markup and remove latex markup parameters.
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        """initialization"""
        self.stemming_language = stemming_language
        self.remove_stopwords = remove_stopwords
        self.remove_html_markup = remove_html_markup
        self.remove_latex_markup = remove_latex_markup

    def get_tokenizing_function(self, wordtable_type):
        """Picks correct tokenize_for_xxx function depending on type of tokenization (wordtable_type)"""
        if wordtable_type == CFG_BIBINDEX_INDEX_TABLE_TYPE["Words"]:
            return self.tokenize_for_words
        elif wordtable_type == CFG_BIBINDEX_INDEX_TABLE_TYPE["Pairs"]:
            return self.tokenize_for_pairs
        elif wordtable_type == CFG_BIBINDEX_INDEX_TABLE_TYPE["Phrases"]:
            return self.tokenize_for_phrases

    def tokenize_for_words(self, phrase):
        """Return list of words found in PHRASE.  Note that the phrase is
           split into groups depending on the alphanumeric characters and
           punctuation characters definition present in the config file.
        """

        words = {}
        formulas = []
        if self.remove_html_markup and phrase.find("</") > -1:
            phrase = do_remove_html_markup(phrase)
        if self.remove_latex_markup:
            formulas = latex_formula_re.findall(phrase)
            phrase = do_remove_latex_markup(phrase)
            phrase = latex_formula_re.sub(' ', phrase)
        phrase = wash_for_utf8(phrase)
        phrase = lower_index_term(phrase)
        # 1st split phrase into blocks according to whitespace
        for block in strip_accents(phrase).split():
            # 2nd remove leading/trailing punctuation and add block:
            block = re_block_punctuation_begin.sub("", block)
            block = re_block_punctuation_end.sub("", block)
            if block:
                stemmed_block = do_remove_stopwords(block, self.remove_stopwords)
                stemmed_block = length_check(stemmed_block)
                stemmed_block = apply_stemming(
                    stemmed_block, self.stemming_language)
                if stemmed_block:
                    words[stemmed_block] = 1
                if re_arxiv.match(block):
                    # special case for blocks like `arXiv:1007.5048' where
                    # we would like to index the part after the colon
                    # regardless of dot or other punctuation characters:
                    words[block.split(':', 1)[1]] = 1
                # 3rd break each block into subblocks according to punctuation
                # and add subblocks:
                for subblock in re_punctuation.split(block):
                    stemmed_subblock = do_remove_stopwords(
                        subblock, self.remove_stopwords)
                    stemmed_subblock = length_check(stemmed_subblock)
                    stemmed_subblock = apply_stemming(
                        stemmed_subblock, self.stemming_language)
                    if stemmed_subblock:
                        words[stemmed_subblock] = 1
                    # 4th break each subblock into alphanumeric groups and add
                    # groups:
                    for alphanumeric_group in re_separators.split(subblock):
                        stemmed_alphanumeric_group = do_remove_stopwords(
                            alphanumeric_group, self.remove_stopwords)
                        stemmed_alphanumeric_group = length_check(
                            stemmed_alphanumeric_group)
                        stemmed_alphanumeric_group = apply_stemming(
                            stemmed_alphanumeric_group, self.stemming_language)
                        if stemmed_alphanumeric_group:
                            words[stemmed_alphanumeric_group] = 1
        for block in formulas:
            words[block] = 1
        return words.keys()

    def tokenize_for_pairs(self, phrase):
        """Return list of words found in PHRASE.  Note that the phrase is
           split into groups depending on the alphanumeric characters and
           punctuation characters definition present in the config file.
        """

        words = {}
        if self.remove_html_markup and phrase.find("</") > -1:
            phrase = do_remove_html_markup(phrase)
        if self.remove_latex_markup:
            phrase = do_remove_latex_markup(phrase)
            phrase = latex_formula_re.sub(' ', phrase)
        phrase = wash_for_utf8(phrase)
        phrase = lower_index_term(phrase)
        # 1st split phrase into blocks according to whitespace
        last_word = ''
        for block in strip_accents(phrase).split():
            # 2nd remove leading/trailing punctuation and add block:
            block = re_block_punctuation_begin.sub("", block)
            block = re_block_punctuation_end.sub("", block)
            if block:
                block = do_remove_stopwords(block, self.remove_stopwords)
                block = length_check(block)
                block = apply_stemming(block, self.stemming_language)
                # 3rd break each block into subblocks according to punctuation
                # and add subblocks:
                for subblock in re_punctuation.split(block):
                    subblock = do_remove_stopwords(
                        subblock, self.remove_stopwords)
                    subblock = length_check(subblock)
                    subblock = apply_stemming(subblock, self.stemming_language)
                    if subblock:
                        # 4th break each subblock into alphanumeric groups and
                        # add groups:
                        for alphanumeric_group in re_separators.split(subblock):
                            alphanumeric_group = do_remove_stopwords(
                                alphanumeric_group, self.remove_stopwords)
                            alphanumeric_group = length_check(
                                alphanumeric_group)
                            alphanumeric_group = apply_stemming(
                                alphanumeric_group, self.stemming_language)
                            if alphanumeric_group:
                                if last_word:
                                    words[
                                        '%s %s' % (last_word, alphanumeric_group)] = 1
                                last_word = alphanumeric_group
        return words.keys()

    def tokenize_for_phrases(self, phrase):
        """Return list of phrases found in PHRASE.  Note that the phrase is
           split into groups depending on the alphanumeric characters and
           punctuation characters definition present in the config file.
        """
        phrase = wash_for_utf8(phrase)
        return [phrase]

    def get_nonmarc_tokenizing_function(self, table_type):
        """
        Picks correct tokenize_for_xxx function
        depending on the type of tokenization
        for non-marc standards.
        """
        return self.get_tokenizing_function(table_type)
