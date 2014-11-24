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
"""BibIndexAuthorTokenizer: tokenizer introduced for author index.
   It tokenizes author name in a fuzzy way. Creates different variants of an author name.
   For example: John Cleese will be tokenized into: 'C John', 'Cleese John', 'John, C', 'John, Cleese'
"""


import re

from invenio.config import CFG_BIBINDEX_AUTHOR_WORD_INDEX_EXCLUDE_FIRST_NAMES
from invenio.bibindex_tokenizers.BibIndexDefaultTokenizer import BibIndexDefaultTokenizer


class BibIndexAuthorTokenizer(BibIndexDefaultTokenizer):

    """Human name tokenizer.

    Human names are divided into three classes of tokens:
    'lastnames', i.e., family, tribal or group identifiers,
    'nonlastnames', i.e., personal names distinguishing individuals,
    'titles', both incidental and permanent, e.g., 'VIII', '(ed.)', 'Msc'
    """

    def __init__(self, stemming_language=None, remove_stopwords=False, remove_html_markup=False, remove_latex_markup=False):
        BibIndexDefaultTokenizer.__init__(self, stemming_language,
                                          remove_stopwords,
                                          remove_html_markup,
                                          remove_latex_markup)
        self.single_initial_re = re.compile('^\w\.$')
        self.split_on_re = re.compile('[\.\s-]')
        # lastname_stopwords describes terms which should not be used for indexing,
        # in multiple-word last names.  These are purely conjunctions, serving the
        # same function as the American hyphen, but using linguistic
        # constructs.
        self.lastname_stopwords = set(['y', 'of', 'and', 'de'])

    def scan_string_for_phrases(self, s):
        """Scan a name string and output an object representing its structure.

        @param s: the input to be lexically tagged
        @type s: string

        @return: dict of lexically tagged input items.

            Sample output for the name 'Jingleheimer Schmitt, John Jacob, XVI.' is:
            {
                'TOKEN_TAG_LIST' : ['lastnames', 'nonlastnames', 'titles', 'raw'],
                'lastnames'      : ['Jingleheimer', 'Schmitt'],
                'nonlastnames'   : ['John', 'Jacob'],
                'titles'         : ['XVI.'],
                'raw'            : 'Jingleheimer Schmitt, John Jacob, XVI.'
            }
        @rtype: dict
        """
        retval = {
            'TOKEN_TAG_LIST': ['lastnames', 'nonlastnames', 'titles', 'raw'],
            'lastnames': [],
            'nonlastnames': [],
            'titles': [],
            'raw': s
        }
        l = s.split(',')
        if len(l) < 2:
            # No commas means a simple name
            new = s.strip()
            new = s.split(' ')
            if len(new) == 1:
                retval['lastnames'] = new        # rare single-name case
            else:
                retval['lastnames'] = new[-1:]
                retval['nonlastnames'] = new[:-1]
                for tag in ['lastnames', 'nonlastnames']:
                    retval[tag] = [x.strip() for x in retval[tag]]
                    retval[tag] = [re.split(self.split_on_re, x)
                                   for x in retval[tag]]
                        # flatten sublists
                    retval[tag] = [item for sublist in retval[tag]
                                   for item in sublist]
                    retval[tag] = [x for x in retval[tag] if x != '']
        else:
            # Handle lastname-first multiple-names case
            retval['titles'] = l[2:]             # no titles? no problem
            retval['nonlastnames'] = l[1]
            retval['lastnames'] = l[0]
            for tag in ['lastnames', 'nonlastnames']:
                # pylint: disable=E1101
                retval[tag] = retval[tag].strip()
                # pylint: enable=E1101
                retval[tag] = re.split(self.split_on_re, retval[tag])
                # filter empty strings
                retval[tag] = [x for x in retval[tag] if x != '']
            retval['titles'] = [x.strip() for x in retval['titles'] if x != '']

        return retval

    def parse_scanned_for_phrases(self, scanned):
        """Return all the indexable variations for a tagged token dictionary.

        Does this via the combinatoric expansion of the following rules:
        - Expands first names as name, first initial with period, first initial
            without period.
        - Expands compound last names as each of their non-stopword subparts.
        - Titles are treated literally, but applied serially.

        Please note that titles will be applied to complete last names only.
        So for example, if there is a compound last name of the form,
        "Ibanez y Gracia", with the title, "(ed.)", then only the combination
        of those two strings will do, not "Ibanez" and not "Gracia".

        @param scanned: lexically tagged input items in the form of the output
            from scan()
        @type scanned: dict

        @return: combinatorically expanded list of strings for indexing
        @rtype: list of string
        """

        def _fully_expanded_last_name(first, lastlist, title=None):
            """Return a list of all of the first / last / title combinations.

            @param first: one possible non-last name
            @type first: string

            @param lastlist: the strings of the tokens in the (possibly compound) last name
            @type lastlist: list of string

            @param title: one possible title
            @type title: string
            """
            retval = []
            title_word = ''
            if title != None:
                title_word = ', ' + title

            last = ' '.join(lastlist)
            retval.append(first + ' ' + last + title_word)
            retval.append(last + ', ' + first + title_word)
            for last in lastlist:
                if last in self.lastname_stopwords:
                    continue
                retval.append(first + ' ' + last + title_word)
                retval.append(last + ', ' + first + title_word)

            return retval

        last_parts = scanned['lastnames']
        first_parts = scanned['nonlastnames']
        titles = scanned['titles']

        if len(first_parts) == 0:                       # rare single-name case
            return scanned['lastnames']

        expanded = []
        for exp in self.__expand_nonlastnames(first_parts):
            expanded.extend(_fully_expanded_last_name(exp, last_parts, None))
            for title in titles:
                # Drop titles which are parenthesized.  This eliminates (ed.) from the index, but
                # leaves XI, for example.  This gets rid of the surprising behavior that searching
                # for 'author:ed' retrieves people who have been editors, but whose names aren't
                # Ed.
                # TODO: Make editorship and other special statuses a MARC
                # field.
                if title.find('(') != -1:
                    continue
                # XXX: remember to document that titles can only be applied to
                # complete last names
                expanded.extend(
                    _fully_expanded_last_name(exp, [' '.join(last_parts)], title))

        return sorted(list(set(expanded)))

    def __expand_nonlastnames(self, namelist):
        """Generate every expansion of a series of human non-last names.

        Example:
        "Michael Edward" -> "Michael Edward", "Michael E.", "Michael E", "M. Edward", "M Edward",
                            "M. E.", "M. E", "M E.", "M E", "M.E."
                    ...but never:
                    "ME"

        @param namelist: a collection of names
        @type namelist: list of string

        @return: a greatly expanded collection of names
        @rtype: list of string
        """

        def _expand_name(name):
            """Lists [name, initial, empty]"""
            if name == None:
                return []
            return [name, name[0]]

        def _pair_items(head, tail):
            """Lists every combination of head with each and all of tail"""
            if len(tail) == 0:
                return [head]
            l = []
            l.extend([head + ' ' + tail[0]])
            # l.extend([head + '-' + tail[0]])
            l.extend(_pair_items(head, tail[1:]))
            return l

        def _collect(head, tail):
            """Brings together combinations of things"""

            def _cons(a, l):
                l2 = l[:]
                l2.insert(0, a)
                return l2

            if len(tail) == 0:
                return [head]
            l = []
            l.extend(_pair_items(head, _expand_name(tail[0])))
            l.extend([' '.join(_cons(head, tail)).strip()])
            # l.extend(['-'.join(_cons(head, tail)).strip()])
            l.extend(_collect(head, tail[1:]))
            return l

        def _expand_contract(namelist):
            """Runs collect with every head in namelist and its tail"""
            val = []
            for i in range(len(namelist)):
                name = namelist[i]
                for expansion in _expand_name(name):
                    val.extend(_collect(expansion, namelist[i + 1:]))
            return val

        def _add_squashed(namelist):
            """Finds cases like 'M. E.' and adds 'M.E.'"""
            val = namelist

            def __check_parts(parts):
                if len(parts) < 2:
                    return False
                for part in parts:
                    if not self.single_initial_re.match(part):
                        return False
                return True

            for name in namelist:
                parts = name.split(' ')
                if not __check_parts(parts):
                    continue
                val.extend([''.join(parts)])

            return val

        return _add_squashed(_expand_contract(namelist))

    def tokenize_for_fuzzy_authors(self, phrase):
        """Output the list of strings expanding phrase.

        Does this via the combinatoric expansion of the following rules:
        - Expands first names as name, first initial with period, first initial
            without period.
        - Expands compound last names as each of their non-stopword subparts.
        - Titles are treated literally, but applied serially.

        Please note that titles will be applied to complete last names only.
        So for example, if there is a compound last name of the form,
        "Ibanez y Gracia", with the title, "(ed.)", then only the combination
        of those two strings will do, not "Ibanez" and not "Gracia".

        Old: BibIndexFuzzyAuthorTokenizer

        @param phrase: the input to be lexically tagged
        @type phrase: string

        @return: combinatorically expanded list of strings for indexing
        @rtype: list of string

        @note: A simple wrapper around scan and parse_scanned.
        """
        return self.parse_scanned_for_phrases(self.scan_string_for_phrases(phrase))

    def tokenize_for_phrases(self, phrase):
        """
            Another name for tokenize_for_fuzzy_authors.
            It's for the compatibility.
            See: tokenize_for_fuzzy_authors
        """
        return self.tokenize_for_fuzzy_authors(phrase)

    def tokenize_for_words_default(self, phrase):
        """Default tokenize_for_words inherited from default tokenizer"""
        return super(BibIndexAuthorTokenizer, self).tokenize_for_words(phrase)

    def get_author_family_name_words_from_phrase(self, phrase):
        """ Return list of words from author family names, not his/her first names.

        The phrase is assumed to be the full author name.  This is
        useful for CFG_BIBINDEX_AUTHOR_WORD_INDEX_EXCLUDE_FIRST_NAMES.

        @param phrase: phrase to get family name from
        """
        d_family_names = {}
        # first, treat everything before first comma as surname:
        if ',' in phrase:
            d_family_names[phrase.split(',', 1)[0]] = 1
        # second, try fuzzy author tokenizer to find surname variants:
        for name in self.tokenize_for_phrases(phrase):
            if ',' in name:
                d_family_names[name.split(',', 1)[0]] = 1
        # now extract words from these surnames:
        d_family_names_words = {}
        for family_name in d_family_names.keys():
            for word in self.tokenize_for_words_default(family_name):
                d_family_names_words[word] = 1
        return d_family_names_words.keys()

    def tokenize_for_words(self, phrase):
        """
            If CFG_BIBINDEX_AUTHOR_WORD_INDEX_EXCLUDE_FIRST_NAMES is 1 we tokenize only for family names.
            In other case we perform standard tokenization for words.
        """
        if CFG_BIBINDEX_AUTHOR_WORD_INDEX_EXCLUDE_FIRST_NAMES:
            return self.get_author_family_name_words_from_phrase(phrase)
        else:
            return self.tokenize_for_words_default(phrase)
