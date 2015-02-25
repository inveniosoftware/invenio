# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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
BibClassify text_normalizer.

This module provides methods to clean the text lines. Currently, the methods
are tuned to work with the output of pdftotext and documents in the HEP field.
Methods can be tuned to your needs through the configuration file.

This modules uses the refextract module of BibEdit in order to find the
references section and to replace unicode characters.
"""

import re
import config as bconfig

from six import iteritems

from invenio.legacy.docextract.pdf import replace_undesirable_characters
from invenio.legacy.refextract.find import find_reference_section, find_end_of_reference_section

log = bconfig.get_logger("bibclassify.text_normalizer")

_washing_regex = []


def get_washing_regex():
    global _washing_regex
    if len(_washing_regex):
        return _washing_regex

    washing_regex = [
        # Replace non and anti with non- and anti-. This allows a better
        # detection of keywords such as nonabelian.
        (re.compile(r"(\snon)[- ](\w+)"), r"\1\2"),
        (re.compile(r"(\santi)[- ](\w+)"), r"\1\2"),
        # Remove all leading numbers (e.g. 2-pion -> pion).
        (re.compile(r"\s\d-"), " "),
        # Remove multiple spaces.
        (re.compile(r" +"), " "),
    ]

    # Remove spaces in particle names.
    # Particles with -/+/*
    washing_regex += [(re.compile(r"(\W%s) ([-+*])" % name), r"\1\2")
                      for name in ("c", "muon", "s", "B", "D", "K", "Lambda",
                                   "Mu", "Omega", "Pi", "Sigma", "Tau", "W", "Xi")]

    # Particles followed by numbers
    washing_regex += [(re.compile(r"(\W%s) ([0-9]\W)" % name), r"\1\2")
                      for name in ("a", "b", "c", "f", "h", "s", "B", "D", "H",
                                   "K", "L", "Phi", "Pi", "Psi", "Rho", "Stor", "UA",
                                   "Xi", "Z")]
    washing_regex += [(re.compile(r"(\W%s) ?\( ?([0-9]+) ?\)[A-Z]?" % name),
                       r"\1(\2)")
                      for name in ("CP", "E", "G", "O", "S", "SL", "SO",
                                   "Spin", "SU", "U", "W", "Z")]

    # Particles with '
    washing_regex += [(re.compile(r"(\W%s) ('\W)" % name), r"\1\2")
                      for name in ("Eta", "W", "Z")]

    # Particles with (N)
    washing_regex += [(re.compile(r"(\W%s) ?\( ?N ?\)[A-Z]?" % name), r"\1(N)")
                      for name in ("CP", "GL", "O", "SL", "SO", "Sp", "Spin",
                                   "SU", "U", "W", "Z")]

    # All names followed by ([0-9]{3,4})
    washing_regex.append((re.compile(r"([A-Za-z]) (\([0-9]{3,4}\)\+?)\s"),
                          r"\1\2 "))

    # Some weird names followed by ([0-9]{3,4})
    washing_regex += [(re.compile(r"\(%s\) (\([0-9]{3,4}\))" % name),
                       r"\1\2 ")
                      for name in ("a0", "Ds1", "Ds2", "K\*")]

    washing_regex += [
        # Remove all lonel operators (usually these are errors
        # introduced by pdftotext.)
        (re.compile(r" [+*] "), r" "),
        # Remove multiple spaces.
        (re.compile(r" +"), " "),
        # Remove multiple line breaks.
        (re.compile(r"\n+"), r"\n"),
    ]
    _washing_regex = washing_regex
    return _washing_regex


def normalize_fulltext(fulltext):
    """Returns a 'cleaned' version of the output provided by pdftotext."""
    # We recognize keywords by the spaces. We need these to match the
    # first and last words of the document.
    fulltext = " " + fulltext + " "

    # Replace some weird unicode characters.
    fulltext = replace_undesirable_characters(fulltext)
    # Replace the greek characters by their name.
    fulltext = _replace_greek_characters(fulltext)

    washing_regex = get_washing_regex()

    # Apply the regular expressions to the fulltext.
    for regex, replacement in washing_regex:
        fulltext = regex.sub(replacement, fulltext)

    return fulltext


def cut_references(text_lines):
    """Returns the text lines with the references cut."""
    ref_sect_start = find_reference_section(text_lines)
    if ref_sect_start is not None:
        start = ref_sect_start["start_line"]
        end = find_end_of_reference_section(text_lines, start,
                                            ref_sect_start["marker"], ref_sect_start["marker_pattern"])
        del text_lines[start:end + 1]
    else:
        log.warning("Found no references to remove.")
        return text_lines

    return text_lines


_GREEK_REPLACEMENTS = {
    u'\u00AF': u' ',
    u'\u00B5': u' Mu ',
    u'\u00D7': u' x ',
    u'\u0391': u' Alpha ',
    u'\u0392': u' Beta ',
    u'\u0393': u' Gamma ',
    u'\u0394': u' Delta ',
    u'\u0395': u' Epsilon ',
    u'\u0396': u' Zeta ',
    u'\u0397': u' Eta ',
    u'\u0398': u' Theta ',
    u'\u0399': u' Iota ',
    u'\u039A': u' Kappa ',
    u'\u039B': u' Lambda ',
    u'\u039C': u' Mu ',
    u'\u039D': u' Nu ',
    u'\u039E': u' Xi ',
    u'\u039F': u' Omicron ',
    u'\u03A0': u' Pi ',
    u'\u03A1': u' Rho ',
    u'\u03A3': u' Sigma ',
    u'\u03A4': u' Tau ',
    u'\u03A5': u' Upsilon ',
    u'\u03A6': u' Phi ',
    u'\u03A7': u' Chi ',
    u'\u03A8': u' Psi ',
    u'\u03A9': u' Omega ',
    u'\u03B1': u' Alpha ',
    u'\u03B2': u' Beta ',
    u'\u03B3': u' Gamma ',
    u'\u03B4': u' Delta ',
    u'\u03B5': u' Epsilon ',
    u'\u03B6': u' Zeta ',
    u'\u03B7': u' Eta ',
    u'\u03B8': u' Theta ',
    u'\u03B9': u' Iota ',
    u'\u03BA': u' Kappa ',
    u'\u03BB': u' Lambda ',
    u'\u03BC': u' Mu ',
    u'\u03BD': u' Nu ',
    u'\u03BE': u' Xi ',
    u'\u03BF': u' Omicron ',
    u'\u03C0': u' Pi ',
    u'\u03C1': u' Rho ',
    u'\uC3C2': u' Sigma ',
    u'\u03C3': u' Sigma ',
    u'\u03C4': u' Tau ',
    u'\u03C5': u' Upsilon ',
    u'\u03C6': u' Phi ',
    u'\u03C7': u' Chi ',
    u'\u03C8': u' Psi ',
    u'\u03C9': u' Omega ',
    u'\u03CA': u' Iota ',
    u'\u03CB': u' Upsilon ',
    u'\u03CC': u' Omicron ',
    u'\u03CD': u' Upsilon ',
    u'\u03CE': u' Omega ',
    u'\u03CF': u' Kai ',
    u'\u03D0': u' Beta ',
    u'\u03D1': u' Theta ',
    u'\u03D2': u' Upsilon ',
    u'\u03D3': u' Upsilon ',
    u'\u03D4': u' Upsilon ',
    u'\u03D5': u' Phi ',
    u'\u03D6': u' Pi ',
    u'\u03D7': u' Kai ',
    u'\u03D8': u' Koppa ',
    u'\u03D9': u' Koppa ',
    u'\u03DA': u' Stigma ',
    u'\u03DB': u' Stigma ',
    u'\u03DC': u' Digamma ',
    u'\u03DD': u' Digamma ',
    u'\u03DE': u' Koppa ',
    u'\u03DF': u' Koppa ',
    u'\u03E0': u' Sampi ',
    u'\u03E1': u' Sampi ',
    u'\u03D1': u' Theta ',
    u'\u03D5': u' Phi ',
    u'\u2010': u'-',
    u'\u2011': u'-',
    u'\u2012': u'-',
    u'\u2013': u'-',
    u'\u2014': u'-',
    u'\u2015': u'-',
    u'\u2019': u"'",
    u'\u2032': u"'",
    u'\u2126': u' Omega ',
    u'\u2206': u' Delta ',
    u'\u2212': u'-',
    u'\u2215': u"/",
    u'\u2216': u"\\",
    u'\u2217': u"*",
    u'\u221D': u' Alpha ',
}


def _replace_greek_characters(line):
    """Replace greek characters in a string."""
    for greek_char, replacement in iteritems(_GREEK_REPLACEMENTS):
        try:
            line = line.replace(greek_char, replacement)
        except UnicodeDecodeError:
            log.warning("Unicode decoding error.")
            return ""

    return line

