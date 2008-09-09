# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibClassify configuration file.
When writing changes, please either delete the cached ontology in your
temporary directory or use the rebuild-cache option in order to
regenerate the cached ontology.
"""

__revision__ = "$Id$"

import re

# USER AGENT

CFG_BIBCLASSIFY_USER_AGENT = ""

# BIBCLASSIFY VARIABLES

# Number of keywords that are output per default.
CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER = 20

# PARTIAL_TEXT
# Marks the part of the fulltext to keep when running a partial match.
# Each tuple contains the start and end percentages of a section.
CFG_BIBCLASSIFY_PARTIAL_TEXT = ((0, 20), (40, 60))

# WORD TRANSFORMATIONS

# BibClassify creates a regular expression for each label found in the
# ontology.
# If the keyword belongs in 'INVARIABLE_WORDS', we return it whitout any
# change.
# If the keyword is found in 'EXCEPTIONS', we return its attached
# regular expression.
# If the keyword is matched by a regular expression of
# 'UNCHANGE_REGULAR_EXPRESSIONS', we return the keyword without any
# change.
# At last, we perform the sub method of Python's re module using the
# first element of the tuple as the regex and the second element as the
# replacement string.

# Regular expressions found here have been originally based on
# Wikipedia's page on English plural.
# [http://en.wikipedia.org/wiki/English_plural]

CFG_BIBCLASSIFY_INVARIABLE_WORDS = ("any", "big", "chi", "der", "eta", "few",
    "low", "new", "non", "off", "one", "out", "phi", "psi", "rho", "tau",
    "two", "van", "von", "hard", "weak", "four", "anti", "zero", "sinh",
    "open", "high", "data", "dark", "free", "flux", "fine", "final", "heavy",
    "strange")

CFG_BIBCLASSIFY_EXCEPTIONS = {
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
    "muon": r"mu(on)?s?",
    "neutrino": r"n(eutrino|u)s?",
    "reflexion": r"refle(x|ct)ions?",
    "ring": r"rings?",
    "status": r"status(es)?",
    "string": r"strings?",
    "sum": r"sums?",
    "vertex": r"vert(ex(es)?|ices)",
    "vortex": r"vort(ex(es)?|ices)",
    }

CFG_BIBCLASSIFY_UNCHANGE_REGULAR_EXPRESSIONS = (
    re.compile("[^e]ed$"),
    re.compile("ics?$"),
    re.compile("[io]s$"),
    re.compile("ium$"),
    re.compile("less$"),
    re.compile("ous$"),
    )

# IDEAS
# "al$" -> "al(ly)?"

CFG_BIBCLASSIFY_GENERAL_REGULAR_EXPRESSIONS = (
    (re.compile("ing$"), r"(e|er|ing)?"),
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

# PUNCTUATION TRANSFORMATIONS

# When building the regex pattern for each label of the ontology, ew also take
# care of the non-alpha characters. Thereafter are two sets of transformations.
# 'SEPARATORS' contains the transformation for the non-alpha characters that
# can be found between two words.
# 'SYMBOLS' contains punctuation that can be found at the end of a word.
# In both cases, it the separator is not found in the dictionaries, we return
# re.escape(separator)

CFG_BIBCLASSIFY_SEPARATORS = {
    " ": r"[\s-]",
    "-": r"[\s-]?",
    "/": r"[/\s]?",
    "(": r"\s?\(",
    "*": r"[*\s]?",
    "- ": r"\s?\-\s",
    "+ ": r"\s?\+\s",
    }

CFG_BIBCLASSIFY_SYMBOLS = {
    "'": r"\s?\'",
    }

CFG_BIBCLASSIFY_WORD_WRAP = "[^\w-]%s[^\w-]"

# MATCHING

# When searching for composite keywords, we allow two keywords separated by one
# of the component of 'VALID_SEPARATORS' to form a composite keyword. These
# separators contain also the punctuation.

CFG_BIBCLASSIFY_VALID_SEPARATORS = (
    "of", "of a", "of an", "of the", "of this", "of one", "of two", "of three",
    "of new", "of other",  "of many", "of both", "of these", "of each", "is"
    )

# EXPLICIT KEYWORDS

# When looking for the keywords already defined in the document, we run the
# following set of regex.

CFG_BIBCLASSIFY_EXPLICIT_KW_START = \
    re.compile(r"(?i)key[ -]*words?[a-z ]*[.:] *")

CFG_BIBCLASSIFY_EXPLICIT_KW_END = (
    re.compile(r"\n"),
    re.compile(r"\."),
    re.compile(r"\sPACS"),
    re.compile(r"(?i)1[. ]*introduction\W"),
    re.compile(r"(?i)mathematics subject classification\W"),
    )

CFG_BIBCLASSIFY_EXPLICIT_KW_SEPARATION = re.compile(" ?; ?| ?, ?| ?- ")

