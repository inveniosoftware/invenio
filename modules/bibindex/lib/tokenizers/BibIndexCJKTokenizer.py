# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2014 CERN.
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
"""BibIndexCJKTokenizer: makes search in collections with CJK papers and publications more reliable
   If phrase has characters from CJK language set tokenizer will treat it diffrently than phrase without these chars.
   CJK Tokenizer splits CJK words into single characters (it adds space between every two CJK characters).
"""

import re

from invenio.bibindex_tokenizers.BibIndexDefaultTokenizer import BibIndexDefaultTokenizer

is_character_from_CJK_set = re.compile(u'[\u3400-\u4DBF\u4E00-\u9FFF]')
special_CJK_punctuation = re.compile(
    u'[\uff1a,\uff0c,\u3001,\u3002,\u201c,\u201d]')


def is_from_CJK_set_single_character_match(char):
    if not isinstance(char, unicode):
        char = char.decode("utf8")
    res = is_character_from_CJK_set.match(char)
    if res:
        return True
    return False


def is_from_CJK_set_full_match(text):
    if not isinstance(text, unicode):
        text = text.decode("utf8")
    res = is_character_from_CJK_set.findall(text)
    if len(res) == len(text):
        return True
    return False


def is_there_any_CJK_character_in_text(text):
    if not isinstance(text, unicode):
        text = text.decode("utf8")
    res = is_character_from_CJK_set.search(text)
    if res is not None:
        return True
    return False


def is_non_CJK_expression(word):
    return not is_there_any_CJK_character_in_text(word)


class BibIndexCJKTokenizer(BibIndexDefaultTokenizer):

    """A phrase is split into CJK characters.
       CJK is Chinese, Japanese and Korean unified character set.
       It means that for example, phrase: '据信，新手机更轻'
       will be split into: ['据', '信', '新', '手', '机', '更', '轻']"""

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        """Initialisation"""
        BibIndexDefaultTokenizer.__init__(self, stemming_language,
                                          remove_stopwords,
                                          remove_html_markup,
                                          remove_latex_markup)

    def tokenize_for_words_default(self, phrase):
        """Default tokenize_for_words inherited from default tokenizer"""
        return super(BibIndexCJKTokenizer, self).tokenize_for_words(phrase)

    def tokenize_for_words(self, phrase):
        """
        Splits phrase into words with additional spaces
        between CJK characters to enhance search for CJK papers and stuff.
        If there is no single CJK character in whole phrase it behaves the standard way:
        it splits phrase into words with use of BibIndexDefaultTokenizer's tokenize_for_words.

        @param phrase: CJK phrase to be tokenized
        @type phrase: string

        @return: list of CJK characters and non-CJK words
        @rtype: list of string
        """
        if is_there_any_CJK_character_in_text(phrase):
            # remove special CJK punctuation
            phrase = special_CJK_punctuation.sub("", phrase)
            # first, we split our phrase with default word tokenizer to make it
            # easier later
            pre_tokenized = self.tokenize_for_words_default(phrase)
            # list for keeping CJK chars and non-CJK words
            chars = []
            # every CJK word splits into a set of single characters
            # for example: "春眠暁覚" into ['春','眠','暁','覚']
            words = [word.decode("utf8") for word in pre_tokenized]
            for word in words:
                if is_from_CJK_set_full_match(word):
                    chars.extend(word)
                else:
                    non_chinese = u""
                    for char in word:
                        if is_from_CJK_set_single_character_match(char):
                            if non_chinese:
                                chars.append(non_chinese)
                                non_chinese = u""
                            chars.append(char)
                        else:
                            non_chinese = non_chinese + char
                    if non_chinese:
                        chars.append(non_chinese)
            clean_dict = {}
            for c in chars:
                clean_dict[c] = 1
            chars = [c.encode("utf8") for c in clean_dict.keys()]
            return chars
        else:
            return self.tokenize_for_words_default(phrase)

    def tokenize_for_pairs(self, phrase):
        return []

    def tokenize_for_phrases(self, phrase):
        return []
