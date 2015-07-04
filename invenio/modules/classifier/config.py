# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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

"""Classifier configuration file."""

from __future__ import unicode_literals

import re


CLASSIFIER_DEFAULT_OUTPUT_NUMBER = 20
"""Number of keywords that are printed by default.
This limits single keywords, composite keywords, and acronyms - not author keywords."""

CLASSIFIER_RECORD_KEYWORD_FIELD = '6531_'
"""The main marc xml field where to find/save the keywords."""

CLASSIFIER_RECORD_KEYWORD_OTHER_FIELDS = ['6950_']
"""Other fields to take from the marc xml when generating list of keywords."""

CLASSIFIER_RECORD_KEYWORD_AUTHOR_FIELD = ''
"""Where to save author supplied keywords."""

CLASSIFIER_RECORD_KEYWORD_ACRONYM_FIELD = ''
"""Where to save extracted acronyms."""

CLASSIFIER_PARTIAL_TEXT_PERCENTAGES = ((0, 20), (40, 60))
"""Marks the part of the fulltext to keep when running a partial match.
Each tuple contains the start and end percentages of a section."""

CLASSIFIER_INVARIABLE_WORDS = (
    "any", "big", "chi", "der", "eta", "few",
    "low", "new", "non", "off", "one", "out",
    "phi", "psi", "rho", "tau",
    "two", "van", "von", "hard", "weak", "four",
    "anti", "zero", "sinh",
    "open", "high", "data", "dark", "free",
    "flux", "fine", "final", "heavy",
    "strange"
)
"""If the keyword belongs in 'INVARIABLE_WORDS', we return it without any change."""

CLASSIFIER_EXCEPTIONS = {
    "aluminium": r"alumini?um",
    "aluminum": r"alumini?um",
    "analysis": r"analy[sz]is",
    "analyzis": r"analy[sz]is",
    "behavior": r"behaviou?rs?",
    "behaviour": r"behaviou?rs?",
    "color": r"colou?rs?",
    "colour": r"colou?rs?",
    "deflexion": r"defle(x|ct)ions?",
    "flavor": r"flavou?rs?",
    "flavour": r"flavou?rs?",
    "gas": r"gas(s?es)?",
    "lens": r"lens(es)?",
    "matrix": r"matri(x(es)?|ces)",
    "muon": r"muons?",
    "neutrino": r"neutrinos?",
    "reflexion": r"refle(x|ct)ions?",
    "ring": r"rings?",
    "status": r"status(es)?",
    "string": r"strings?",
    "sum": r"sums?",
    "vertex": r"vert(ex(es)?|ices)",
    "vortex": r"vort(ex(es)?|ices)",
}
"""If the keyword is found in 'EXCEPTIONS', we return its attached regular expression."""

CLASSIFIER_UNCHANGE_REGULAR_EXPRESSIONS = (
    re.compile("[^e]ed$"),
    re.compile("ics?$"),
    re.compile("[io]s$"),
    re.compile("ium$"),
    re.compile("less$"),
    re.compile("ous$"),
)
"""If the keyword is matched by a regular expression of
'UNCHANGE_REGULAR_EXPRESSIONS', we return the keyword without any
change.
"""

CLASSIFIER_GENERAL_REGULAR_EXPRESSIONS = (
    (re.compile("ional"), r"ional(ly)?"),
    (re.compile("([ae])n(ce|t)$"), r"\1n(t|ces?)"),
    (re.compile("og(ue)?$"), r"og(ue)?s?"),
    (re.compile("([^aeiouyc])(re|er)$"), r"\1(er|re)s?"),
    (re.compile("([aeiouy])[sz]ation$"), r"\1[zs]ations?"),
    (re.compile("([aeiouy])[sz]ation$"), r"\1[zs]ations?"),
    (re.compile("([^aeiou])(y|ies)$"), r"\1(y|ies)"),
    (re.compile("o$"), r"o(e?s)?"),
    (re.compile("(x|sh|ch|ss)$"), r"\1(es)?"),
    (re.compile("f$"), r"(f|ves)"),
    (re.compile("ung$"), r"ung(en)?"),
    (re.compile("([^aiouy])s$"), r"\1s?"),
    (re.compile("([^o])us$"), r"\1(i|us(es)?)"),
    (re.compile("um$"), r"(a|ums?)"),
)
"""The classifier creates a regular expression for each label found in the ontology.

At last, we perform the sub method of Python's re module using the
first element of the tuple as the regex and the second element as the
replacement string.

Regular expressions found here have been originally based on
Wikipedia's page on English plural.
[http://en.wikipedia.org/wiki/English_plural]
"""

CLASSIFIER_SEPARATORS = {
    " ": r"[\s\n-]",
    "-": r"[\s\n-]?",
    "/": r"[/\s]?",
    "(": r"\s?\(",
    "*": r"[*\s]?",
    "- ": r"\s?\-\s",
    "+ ": r"\s?\+\s",
}
"""The transformation for the non-alpha characters that can be found between two words."""

CLASSIFIER_SYMBOLS = {
    "'": r"\s?\'",
}
"""The punctuation that can be found at the end of a word."""

CLASSIFIER_WORD_WRAP = "[^\w-]%s[^\w-]"
"""Regular expression to wrap words."""

CLASSIFIER_VALID_SEPARATORS = (
    "of", "of a", "of an", "of the", "of this", "of one", "of two", "of three",
    "of new", "of other", "of many", "of both", "of these", "of each", "is",
    "the"
)
"""When searching for composite keywords, we allow two keywords separated by one
of the component of 'VALID_SEPARATORS' to form a composite keyword. These
separators contain also the punctuation."""


CLASSIFIER_AUTHOR_KW_START = \
    re.compile(r"(?i)key[ -]*words?[a-z ]*[.:] *")

CLASSIFIER_AUTHOR_KW_END = (
    re.compile(r"\n"),
    re.compile(r"\.\W"),
    re.compile(r"\sPACS"),
    re.compile(r"(?i)1[. ]*introduction\W"),
    re.compile(r"(?i)mathematics subject classification\W"),
)

CLASSIFIER_AUTHOR_KW_SEPARATION = re.compile(" ?; ?| ?, ?| ?- ")
