# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

import re
from invenio.bibindex_engine_stemmer import stem
from invenio.bibindex_engine_stopwords import is_stopword
from invenio.config import CFG_BIBINDEX_MIN_WORD_LENGTH, \
    CFG_ETCDIR

re_pattern_fuzzy_author_dots = re.compile(r'[\.\-]+')
re_pattern_fuzzy_author_spaces = re.compile(r'\s+')
re_pattern_author_canonical_id = re.compile(r'\.[0-9]+$')


re_unicode_lowercase_a = re.compile(unicode(r"(?u)[áàäâãå]", "utf-8"))
re_unicode_lowercase_ae = re.compile(unicode(r"(?u)[æ]", "utf-8"))
re_unicode_lowercase_e = re.compile(unicode(r"(?u)[éèëê]", "utf-8"))
re_unicode_lowercase_i = re.compile(unicode(r"(?u)[íìïî]", "utf-8"))
re_unicode_lowercase_o = re.compile(unicode(r"(?u)[óòöôõø]", "utf-8"))
re_unicode_lowercase_u = re.compile(unicode(r"(?u)[úùüû]", "utf-8"))
re_unicode_lowercase_y = re.compile(unicode(r"(?u)[ýÿ]", "utf-8"))
re_unicode_lowercase_c = re.compile(unicode(r"(?u)[çć]", "utf-8"))
re_unicode_lowercase_n = re.compile(unicode(r"(?u)[ñ]", "utf-8"))
re_unicode_uppercase_a = re.compile(unicode(r"(?u)[ÁÀÄÂÃÅ]", "utf-8"))
re_unicode_uppercase_ae = re.compile(unicode(r"(?u)[Æ]", "utf-8"))
re_unicode_uppercase_e = re.compile(unicode(r"(?u)[ÉÈËÊ]", "utf-8"))
re_unicode_uppercase_i = re.compile(unicode(r"(?u)[ÍÌÏÎ]", "utf-8"))
re_unicode_uppercase_o = re.compile(unicode(r"(?u)[ÓÒÖÔÕØ]", "utf-8"))
re_unicode_uppercase_u = re.compile(unicode(r"(?u)[ÚÙÜÛ]", "utf-8"))
re_unicode_uppercase_y = re.compile(unicode(r"(?u)[Ý]", "utf-8"))
re_unicode_uppercase_c = re.compile(unicode(r"(?u)[ÇĆ]", "utf-8"))
re_unicode_uppercase_n = re.compile(unicode(r"(?u)[Ñ]", "utf-8"))
re_latex_lowercase_a = re.compile("\\\\[\"H'`~^vu=k]\{?a\}?")
re_latex_lowercase_ae = re.compile("\\\\ae\\{\\}?")
re_latex_lowercase_e = re.compile("\\\\[\"H'`~^vu=k]\\{?e\\}?")
re_latex_lowercase_i = re.compile("\\\\[\"H'`~^vu=k]\\{?i\\}?")
re_latex_lowercase_o = re.compile("\\\\[\"H'`~^vu=k]\\{?o\\}?")
re_latex_lowercase_u = re.compile("\\\\[\"H'`~^vu=k]\\{?u\\}?")
re_latex_lowercase_y = re.compile("\\\\[\"']\\{?y\\}?")
re_latex_lowercase_c = re.compile("\\\\['uc]\\{?c\\}?")
re_latex_lowercase_n = re.compile("\\\\[c'~^vu]\\{?n\\}?")
re_latex_uppercase_a = re.compile("\\\\[\"H'`~^vu=k]\\{?A\\}?")
re_latex_uppercase_ae = re.compile("\\\\AE\\{?\\}?")
re_latex_uppercase_e = re.compile("\\\\[\"H'`~^vu=k]\\{?E\\}?")
re_latex_uppercase_i = re.compile("\\\\[\"H'`~^vu=k]\\{?I\\}?")
re_latex_uppercase_o = re.compile("\\\\[\"H'`~^vu=k]\\{?O\\}?")
re_latex_uppercase_u = re.compile("\\\\[\"H'`~^vu=k]\\{?U\\}?")
re_latex_uppercase_y = re.compile("\\\\[\"']\\{?Y\\}?")
re_latex_uppercase_c = re.compile("\\\\['uc]\\{?C\\}?")
re_latex_uppercase_n = re.compile("\\\\[c'~^vu]\\{?N\\}?")


def lower_index_term(term):
    """
    Return safely lowered index term TERM.  This is done by converting
    to UTF-8 first, because standard Python lower() function is not
    UTF-8 safe.  To be called by both the search engine and the
    indexer when appropriate (e.g. before stemming).

    In case of problems with UTF-8 compliance, this function raises
    UnicodeDecodeError, so the client code may want to catch it.
    """
    return unicode(term, 'utf-8').lower().encode('utf-8')

latex_markup_re = re.compile(
    r"\\begin(\[.+?\])?\{.+?\}|\\end\{.+?}|\\\w+(\[.+?\])?\{(?P<inside1>.*?)\}|\{\\\w+ (?P<inside2>.*?)\}")


def remove_latex_markup(phrase):
    ret_phrase = ''
    index = 0
    for match in latex_markup_re.finditer(phrase):
        ret_phrase += phrase[index:match.start()]
        ret_phrase += match.group('inside1') or match.group('inside2') or ''
        index = match.end()
    ret_phrase += phrase[index:]
    return ret_phrase


def apply_stemming(word, stemming_language):
    """Returns word after applying stemming (if stemming language is set).
       You can change your stemming language in database.

       @param word: word to be checked
       @type word: str
       @param stemming_language: abbreviation of language or None
       @type stemming_language: str
    """
    if stemming_language:
        word = stem(word, stemming_language)
    return word


def remove_stopwords(word, stopwords_kb=False):
    """Returns word after stopword check.
       One must specify the name of the knowledge base.

       @param word: word to be checked
       @type word: str
       @param stopwords_kb: name of the stopwords knowledge base
       @type word: str
    """
    if stopwords_kb:
        stopwords_path = CFG_ETCDIR + "/bibrank/" + stopwords_kb
        if is_stopword(word, stopwords_path):
            return ""
    return word


def length_check(word):
    """Returns word after length check.

       @param word: word to be checked
       @type word: str
    """
    if len(word) < CFG_BIBINDEX_MIN_WORD_LENGTH:
        return ""
    return word


def wash_index_term(term, max_char_length=50, lower_term=True):
    """
    Return washed form of the index term TERM that would be suitable
    for storing into idxWORD* tables.  I.e., lower the TERM if
    LOWER_TERM is True, and truncate it safely to MAX_CHAR_LENGTH
    UTF-8 characters (meaning, in principle, 4*MAX_CHAR_LENGTH bytes).

    The function works by an internal conversion of TERM, when needed,
    from its input Python UTF-8 binary string format into Python
    Unicode format, and then truncating it safely to the given number
    of UTF-8 characters, without possible mis-truncation in the middle
    of a multi-byte UTF-8 character that could otherwise happen if we
    would have been working with UTF-8 binary representation directly.

    Note that MAX_CHAR_LENGTH corresponds to the length of the term
    column in idxINDEX* tables.
    """
    if lower_term:
        washed_term = unicode(term, 'utf-8').lower()
    else:
        washed_term = unicode(term, 'utf-8')
    if len(washed_term) <= max_char_length:
        # no need to truncate the term, because it will fit
        # nicely even if it uses four-byte UTF-8 characters
        return washed_term.encode('utf-8')
    else:
        # truncate the term in a safe position:
        return washed_term[:max_char_length].encode('utf-8')


def wash_author_name(p):
    """
    Wash author name suitable for author searching.  Notably, replace
    dots and hyphens with spaces, and collapse spaces.
    """
    if re_pattern_author_canonical_id.search(p):
        # we have canonical author ID form, so ignore all washing
        return p
    out = re_pattern_fuzzy_author_dots.sub(" ", p)
    out = re_pattern_fuzzy_author_spaces.sub(" ", out)
    return out.strip()
