# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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

"""
BibClassify configuration file.

When writing changes, please either delete the cached ontology in your
temporary directory or use the rebuild-cache option in order to
regenerate the cached ontology.

If you want to change this configuration, we recommend to create a
local configuration file names 'bibclassify_config_local.py' that
contains the changes to apply.
"""

from __future__ import unicode_literals

import re
import logging
import sys
import os
from invenio import config

VERSION = '0.4.9'

logging_level = logging.ERROR


# ------------- main config -----------

# Save generated kw into the database?
# daemon does that
CFG_DB_SAVE_KW = True

# Number of keywords that are printed by default (this limits single keywords,
# composite keywords, and acronyms - not author keywords)
CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER = 20

# The main marc xml field where to find/save the keywords, including the
# indicators
CFG_MAIN_FIELD = '6531_'

# Other fields to take from the marc xml when generating tagcloud/list of
# keywords.
CFG_OTHER_FIELDS = ['6950_']

# Where to save author supplied keywords
CFG_AUTH_FIELD = ''

# Where to save extracted acronyms
CFG_ACRON_FIELD = ''

# ------------ bibclass config -------

# PARTIAL_TEXT
# Marks the part of the fulltext to keep when running a partial match.
# Each tuple contains the start and end percentages of a section.
CFG_BIBCLASSIFY_PARTIAL_TEXT = ((0, 20), (40, 60))


# Format and output marcxml records in spires format
CFG_SPIRES_FORMAT = False


# The taxonomy used when no taxonomy is specified
CFG_EXTRACTION_TAXONOMY = 'HEP'


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
                                    "low", "new", "non", "off", "one", "out",
                                    "phi", "psi", "rho", "tau",
                                    "two", "van", "von", "hard", "weak", "four",
                                    "anti", "zero", "sinh",
                                    "open", "high", "data", "dark", "free",
                                    "flux", "fine", "final", "heavy",
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
    " ": r"[\s\n-]",
    "-": r"[\s\n-]?",
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
    "of new", "of other", "of many", "of both", "of these", "of each", "is",
    "the"
)

# AUTHOR KEYWORDS

# When looking for the keywords already defined in the document, we run the
# following set of regex.

CFG_BIBCLASSIFY_AUTHOR_KW_START = \
    re.compile(r"(?i)key[ -]*words?[a-z ]*[.:] *")

CFG_BIBCLASSIFY_AUTHOR_KW_END = (
    re.compile(r"\n"),
    re.compile(r"\.\W"),
    re.compile(r"\sPACS"),
    re.compile(r"(?i)1[. ]*introduction\W"),
    re.compile(r"(?i)mathematics subject classification\W"),
)

CFG_BIBCLASSIFY_AUTHOR_KW_SEPARATION = re.compile(" ?; ?| ?, ?| ?- ")


# Modules to call to get output from them
#CFG_EXTERNAL_MODULES = {'webtag' : 'call_from_outside'}
CFG_EXTERNAL_MODULES = {}

log = None
_loggers = []


def get_logger(name):
    """Creates a logger for you - with the parent newseman logger and
    common configuration"""
    if log:
        logger = log.manager.getLogger(name)
    else:
        logger = logging.getLogger(name)
        hdlr = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(levelname)s %(name)s:%(lineno)d    %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(logging_level)
        logger.propagate = 0
    if logger not in _loggers:
        _loggers.append(logger)
    return logger


def set_global_level(level):
    global logging_level
    logging_level = int(level)
    for l in _loggers:
        l.setLevel(logging_level)


log = get_logger('bibclassify')

STANDALONE = False
# Standalone mode has been removed.
#try:
#    import invenio.legacy.search_engine
#except:
#    STANDALONE = True
#    log.warning('Bibclassify is running in a standalone mode, access to database is not supported')


if STANDALONE:
    import tempfile
    # try to find etcdir (first in this directory), and set etc to be one
    # level higher
    etcdir = ' '
    bibetc = os.path.join(os.path.dirname(__file__), 'bibclassify')
    if os.path.isdir(bibetc) and os.access(bibetc, os.W_OK):
        etcdir = os.path.dirname(__file__)

    if not os.path.isdir(etcdir) or not os.access(etcdir, os.W_OK):
        etcdir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../etc"))
        if not os.path.isdir(etcdir) or not os.access(etcdir, os.W_OK):
            etcdir = tempfile.gettempdir()

    log.warning("Setting CFG_CACHEDIR, CFG_WEBDIR, CFG_ETCDIR to: %s" % etcdir)

    # override a few special paths
    config.CFG_CACHEDIR = etcdir
    config.CFG_WEBDIR = etcdir
    config.CFG_ETCDIR = etcdir


# shadow the config variables that bibclassify modules use
CFG_PREFIX = config.CFG_PREFIX
CFG_CACHEDIR = config.CFG_CACHEDIR
CFG_WEBDIR = config.CFG_WEBDIR
CFG_ETCDIR = config.CFG_ETCDIR
CFG_TMPDIR = config.CFG_TMPDIR


# Redefine variable definitions if local config exists
try:
    from invenio import bibclassify_config_local as localconf

    for confid in dir(localconf):
        if 'CFG' in confid:
            if hasattr(config, confid):
                log.info('Overriding global config %s with %s' % (
                    confid, getattr(localconf, confid)))
                setattr(config, confid, getattr(localconf, confid))
            if confid in globals():
                globals()[confid] = getattr(localconf, confid)
                log.info('Overriding bibclassify config %s with %s' % (
                    confid, getattr(localconf, confid)))
except ImportError:
    # No local configuration was found.
    pass

log.info('Initialized bibclassify config')
