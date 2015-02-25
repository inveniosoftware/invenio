# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
Bibclassify acronym analyser.
"""

from __future__ import print_function

import re

ACRONYM_BRACKETS_REGEX = re.compile("[([] ?(([a-zA-Z]\.?){2,})s? ?[)\]]")
DOTS_REGEX = re.compile("\.")
MAXIMUM_LEVEL = 2
STOPLIST = ("and", "of", "for", "the", "to", "do", "de", "theory",
            "model", "radiation", "scheme", "representation")


def get_acronyms(fulltext):
    """Finds acronyms and expansions from the fulltext.

     If needed, acronyms can already contain a dictionary of previously found
    acronyms that will be merged with the current results."""
    acronyms = {}

    for m in ACRONYM_BRACKETS_REGEX.finditer(fulltext):
        acronym = DOTS_REGEX.sub("", m.group(1))
        potential_expansion = fulltext[m.start() - 80:m.start()].replace("\n",
                                                                         " ")
        # Strip
        potential_expansion = re.sub("(\W).(\W)", "\1\2", potential_expansion)
        potential_expansion = re.sub("(\w)\(s\)\W", "\1", potential_expansion)
        potential_expansion = re.sub("""[^\w'"]+$""", "", potential_expansion)
        potential_expansion = re.sub("[[(].+[\])]", "", potential_expansion)
        potential_expansion = re.sub(" {2,}", " ", potential_expansion)

        # LEVEL 0: expansion between quotes
        # Double quotes
        match = re.search(""""([^"]+)["]$""", potential_expansion)
        if match is None:
            # Single quotes
            match = re.search("""'([^"]+)[']$""", potential_expansion)
        if match is not None:
            if acronym in match.group(1):
                continue

            pattern = ""
            for char in acronym[:-1]:
                pattern += "%s\w+\W*" % char
            pattern += "%s\w+" % acronym[-1]

            if re.search(pattern, match.group(1), re.I) is not None:
                _add_expansion_to_acronym_dict(acronym, match.group(1), 0,
                                               acronyms)
            continue

        pattern = "\W("
        for char in acronym[:-1]:
            pattern += "%s\w+\W+" % char
        pattern += "%s\w+)$" % acronym[-1]

        # LEVEL 1: expansion with uppercase initials
        match = re.search(pattern, potential_expansion)
        if match is not None:
            _add_expansion_to_acronym_dict(acronym, match.group(1), 1, acronyms)
            continue

        # LEVEL 2: expansion with initials
        match = re.search(pattern, potential_expansion, re.I)
        if match is not None:
            _add_expansion_to_acronym_dict(acronym, match.group(1), 2, acronyms)
            continue

        # LEVEL 3: expansion with initials and STOPLIST
        potential_expansion_stripped = " ".join([word for word in
                                                 _words(potential_expansion) if
                                                 word not in STOPLIST])

        match = re.search(pattern, potential_expansion_stripped, re.I)
        if match is not None:
            first_expansion_word = re.search("\w+", match.group(1)).group()
            start = potential_expansion.lower().rfind(first_expansion_word)
            _add_expansion_to_acronym_dict(acronym, potential_expansion[start:],
                                           3, acronyms)
            continue

        # LEVEL 4: expansion with fuzzy initials and stoplist
        reversed_words = _words(potential_expansion_stripped)
        reversed_words.reverse()

        reversed_acronym = list(acronym.lower())
        reversed_acronym.reverse()

        index0 = 0
        index1 = 0
        word = ""
        try:
            while index0 < len(reversed_acronym) and index1 < len(
                    reversed_words):
                word = reversed_words[index1]
                if index0 + 1 < len(reversed_words):
                    next_word = reversed_words[index0 + 1]
                else:
                    next_word = "_"

                char = reversed_acronym[index0]
                if index0 + 1 < len(reversed_acronym):
                    next_char = reversed_acronym[index0 + 1]
                else:
                    next_char = "_"

                if char == next_char and \
                        word.startswith(char) and \
                                word.count(char) > 1 and \
                        not next_word.startswith(char):
                    index0 += 2
                    index1 += 1
                if word.startswith(char):
                    index0 += 1
                    index1 += 1
                elif char in word and \
                        not word.endswith(char) and \
                        word.startswith(next_char):
                    index0 += 2
                    index1 += 1
                else:
                    word = ""
                    break
        except IndexError:
            word = ""

        if not word.startswith(char):
            word = ""

        if word:
            start = potential_expansion.lower().rfind(word)

            _add_expansion_to_acronym_dict(acronym,
                                           potential_expansion[start:], 4,
                                           acronyms)
            continue

        # LEVEL 5: expansion with fuzzy initials
        reversed_words = _words(potential_expansion.lower())
        reversed_words.reverse()

        reversed_acronym = list(acronym.lower())
        reversed_acronym.reverse()

        index0 = 0
        index1 = 0
        word = ""
        try:
            while index0 < len(reversed_acronym) and index1 < len(
                    reversed_words):
                word = reversed_words[index1]
                if index0 + 1 < len(reversed_words):
                    next_word = reversed_words[index0 + 1]
                else:
                    next_word = ""

                char = reversed_acronym[index0]
                if index0 + 1 < len(reversed_acronym):
                    next_char = reversed_acronym[index0 + 1]
                else:
                    next_char = ""

                if char == next_char and word.startswith(char) and \
                                word.count(char) > 1 and \
                        not next_word.startswith(char):
                    index0 += 2
                    index1 += 1
                if word.startswith(char):
                    index0 += 1
                    index1 += 1
                elif char in word and \
                        not word.endswith(char) and \
                        word.startswith(next_char):
                    index0 += 2
                    index1 += 1
                else:
                    word = ""
                    break
        except IndexError:
            word = ""

        if not word.startswith(char):
            word = ""

        if word:
            start = potential_expansion.lower().rfind(word)
            _add_expansion_to_acronym_dict(acronym,
                                           potential_expansion[start:], 5,
                                           acronyms)
            continue

    return acronyms


def _words(expression):
    """Return a list of words of the expression."""
    return re.findall("\w+", expression.lower())


def _add_expansion_to_acronym_dict(acronym, expansion, level, dictionary):
    """Add an acronym to the dictionary.

    Takes care of avoiding duplicates and keeping the expansion marked with
    the best score."""
    if len(acronym) >= len(expansion) or acronym in expansion:
        return

    for punctuation in re.findall("\W", expansion):
        # The expansion contains non-basic punctuation. It is probable
        # that it is invalid. Discard it.
        if punctuation not in (",", " ", "-"):
            return False

    if acronym in dictionary:
        add = True
        for stored_expansion, stored_level in dictionary[acronym]:
            if _equivalent_expansions(stored_expansion, expansion):
                if level < stored_level:
                    dictionary[acronym].remove((stored_expansion, stored_level))
                    break
                else:
                    add = False
        if add:
            dictionary[acronym].append((expansion, level))
            return True
    else:
        dictionary.setdefault(acronym, []).append((expansion, level))
        return True

    return False


def _equivalent_expansions(expansion1, expansion2):
    """Compare two expansions."""
    words1 = _words(expansion1)
    words2 = _words(expansion2)

    simplified_versions = []

    if words1 == words2:
        return True

    for words in (words1, words2):
        store = []
        for word in words:
            store.append(word[:5])
        simplified_versions.append("".join(store))

    return simplified_versions[0] == simplified_versions[1]


if __name__ == "__main__":
    print(get_acronyms(
        "asymptomatically de Sitter(dS). and what one large relative symmetric (LRS) which always has general relativity (GR)"))
