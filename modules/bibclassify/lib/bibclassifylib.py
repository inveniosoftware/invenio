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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Bibclassify keyword extractor command line entry point.
"""

__revision__ = "$Id$"

import os
import rdflib
import re
import random
import cPickle
import sys
import tempfile

try:
    from bibclassify_text_normalizer import normalize_fulltext, cut_references
    from bibclassify_keyword_analyser import get_single_keywords, \
                                             get_composite_keywords, \
                                             get_author_keywords
    from bibclassify_config import CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER, \
        CFG_BIBCLASSIFY_EXCEPTIONS, \
        CFG_BIBCLASSIFY_GENERAL_REGULAR_EXPRESSIONS, \
        CFG_BIBCLASSIFY_INVARIABLE_WORDS, \
        CFG_BIBCLASSIFY_PARTIAL_TEXT, \
        CFG_BIBCLASSIFY_SEPARATORS, \
        CFG_BIBCLASSIFY_SYMBOLS, \
        CFG_BIBCLASSIFY_UNCHANGE_REGULAR_EXPRESSIONS, \
        CFG_BIBCLASSIFY_WORD_WRAP
except ImportError, err:
    print >> sys.stderr, "Error: %s" % err
    sys.exit(1)

# Global variables.
_SKWS = {}
_CKWS = {}

_contains_digit = re.compile("\d")
_starts_with_non = re.compile("(?i)^non[a-z]")
_starts_with_anti = re.compile("(?i)^anti[a-z]")
_split_by_punctuation = re.compile("(\W+)")

class SingleKeyword:
    """A single keyword element that treats and stores information fields
    retrieved from the RDF/SKOS ontology."""
    def __init__(self, store, namespace, subject):
        basic_labels = []
        for label in store.objects(subject, namespace["prefLabel"]):
            basic_labels.append(str(label))

        # The concept (==human-readable label of the keyword) is the first
        # prefLabel.
        self.concept = basic_labels[0]

        for label in store.objects(subject, namespace["altLabel"]):
            basic_labels.append(str(label))

        hidden_labels = []
        for label in store.objects(subject, namespace["hiddenLabel"]):
            hidden_labels.append(unicode(label))

        self.regex = get_searchable_regex(basic_labels, hidden_labels)

        note = str(store.value(subject, namespace["note"], any=True))
        if note is not None:
            self.nostandalone = (note.lower() in
                                ("nostandalone", "nonstandalone"))

        spires = store.value(subject, namespace["spiresLabel"], any=True)
        if spires is not None:
            self.spires = str(spires)


    def __repr__(self):
        return "".join(["<SingleKeyword: ", self.concept, ">"])

class CompositeKeyword:
    """A composite keyword element that treats and stores information fields
    retrieved from the RDF/SKOS ontology."""
    def __init__(self, store, namespace, subject):
        try:
            self.concept = store.value(subject, namespace["prefLabel"],
                                       any=True)
        except KeyError:
            # Keyword has no prefLabel. We can discard that error.
            print >> sys.stderr, ("Keyword with subject %s has no prefLabel" %
                subject)

        small_subject = subject.split("#Composite.")[-1]
        component_positions = []
        for label in store.objects(subject, namespace["compositeOf"]):
            strlabel = str(label).split("#")[-1]
            component_name = label.split("#")[-1]
            component_positions.append((small_subject.find(component_name),
                strlabel))

        self.compositeof = []
        component_positions.sort()
        for position in component_positions:
            self.compositeof.append(position[1])

        spires = store.value(subject, namespace["spiresLabel"], any=True)
        if spires is not None:
            self.spires = spires

        self.regex = []
        for label in store.objects(subject, namespace["altLabel"]):
            pattern = get_regex_pattern(label)
            self.regex.append(re.compile(CFG_BIBCLASSIFY_WORD_WRAP % pattern))

    def __repr__(self):
        return "".join(["<CompositeKeyword: ", self.concept, ">"])

def build_cache(ontology_file, no_cache=False):
    """Builds the cached data by parsing the RDF ontology file."""
    if rdflib.__version__ >= '2.3.2':
        store = rdflib.ConjunctiveGraph()
    else:
        store = rdflib.Graph()
    store.parse(ontology_file)

    namespace = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")

    single_count = 0
    composite_count = 0
    regex_count = 0

    for subject_object in store.subject_objects(namespace["prefLabel"]):
        # Keep only the single keywords.
        # TODO: Remove or alter that condition in order to allow using other
        # ontologies that do not have this composite notion (such as
        # NASA-subjects.rdf)
        if not store.value(subject_object[0], namespace["compositeOf"],
            any=True):
            strsubject = str(subject_object[0]).split("#")[-1]
            _SKWS[strsubject] = SingleKeyword(store, namespace,
                subject_object[0])
            single_count += 1
            regex_count += len(_SKWS[strsubject].regex)

    # Let's go through the composite keywords.
    for subject, pref_label in store.subject_objects(namespace["prefLabel"]):
        # Keep only the single keywords.
        if store.value(subject, namespace["compositeOf"], any=True):
            strsubject = str(subject).split("#")[-1]
            _CKWS[strsubject] = CompositeKeyword(store, namespace, subject)
            composite_count += 1
            regex_count += len(_CKWS[strsubject].regex)

    store.close()

    cached_data = {}
    cached_data["single"] = _SKWS
    cached_data["composite"] = _CKWS

    if not no_cache:
        # Serialize
        try:
            filestream = open(get_cache_file(ontology_file), "w")
            cPickle.dump(cached_data, filestream, 1)
            filestream.close()
        except IOError:
            # Impossible to write the cache.
            return cached_data

    return cached_data

def capitalize_first_letter(word):
    """Returns a regex pattern with the first letter accepting both lowercase
    and uppercase."""
    if word[0].isalpha():
        # These two cases are necessary in order to get a regex pattern
        # starting with '[xX]' and not '[Xx]'. This allows to check for
        # colliding regex afterwards.
        if word[0].isupper():
            return "["+ word[0].swapcase() + word[0] +"]" + word[1:]
        else:
            return "["+ word[0] + word[0].swapcase() +"]" + word[1:]
    return word

def convert_punctuation(punctuation, conversion_table):
    """Returns a regular expression for a punctuation string."""
    if punctuation in conversion_table:
        return conversion_table[punctuation]
    return re.escape(punctuation)

def convert_word(word):
    """Returns the plural form of the word if it exists, the word itself
    otherwise."""
    out = None

    # Acronyms.
    if word.isupper():
        out = word + "s?"
    # Proper nouns or word with digits.
    elif word.istitle():
        out = word + "('?s)?"
    elif _contains_digit.search(word):
        out = word

    if out is not None:
        return out

    # Words with non or anti prefixes.
    if _starts_with_non.search(word):
        word = "non-?" + capitalize_first_letter(convert_word(word[3:]))
    elif _starts_with_anti.search(word):
        word = "anti-?" + capitalize_first_letter(convert_word(word[4:]))

    if out is not None:
        return capitalize_first_letter(out)

    # A few invariable words.
    if word in CFG_BIBCLASSIFY_INVARIABLE_WORDS:
        return capitalize_first_letter(word)

    # Some exceptions that would not produce good results with the set of
    # general_regular_expressions.
    if word in CFG_BIBCLASSIFY_EXCEPTIONS:
        return capitalize_first_letter(CFG_BIBCLASSIFY_EXCEPTIONS[word])

    for regex in CFG_BIBCLASSIFY_UNCHANGE_REGULAR_EXPRESSIONS:
        if regex.search(word) is not None:
            return capitalize_first_letter(word)

    for regex, replacement in CFG_BIBCLASSIFY_GENERAL_REGULAR_EXPRESSIONS:
        stemmed = regex.sub(replacement, word)
        if stemmed != word:
            return capitalize_first_letter(stemmed)

    return capitalize_first_letter(word + "s?")

def get_cache(ontology_file):
    """Get the cached ontology using the cPickle module. No check is done at
    that stage."""
    filestream = open(get_cache_file(ontology_file), "r")
    try:
        cached_data = cPickle.load(filestream)
    except (cPickle.UnpicklingError, AttributeError, DeprecationWarning):
        print >> sys.stderr, "Problem with existing cache. Regenerating."
        filestream.close()
        os.remove(get_cache_file(ontology_file))
        return build_cache(ontology_file)
    filestream.close()

    global _SKWS, _CKWS
    _SKWS = cached_data["single"]
    _CKWS = cached_data["composite"]

    return cached_data

def get_cache_file(ontology_file):
    """Returns the file name of the cached ontology."""
    temp_dir = tempfile.gettempdir()
    cache_file = os.path.basename(ontology_file) + ".db"
    return os.path.join(temp_dir, cache_file)

def get_keywords_from_text(text_lines, ontology_file="", output_mode="text",
                           output_limit=CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER,
                           spires=False, match_mode="full", no_cache=False,
                           with_author_keywords=False):
    """Returns a formatted string containing the keywords for a single
    document. If 'ontology_file' has not been specified, the method
    'get_regular_expressions' must have been run in order to build or
    get the cached ontology."""
    if not ontology_file:
        if not _SKWS or not _CKWS:
            # Cache was not read/created.
            print >> sys.stderr, ("Please specify an ontology file or "
                "use the method 'get_regular_expressions' before "
                "searching for keywords.")
            sys.exit(1)
    else:
        get_regular_expressions(ontology_file, no_cache)

    text_lines = cut_references(text_lines)
    fulltext = normalize_fulltext("\n".join(text_lines))

    author_keywords = None
    if with_author_keywords:
        author_keywords = get_author_keywords(fulltext)

    if match_mode == "partial":
        fulltext = get_partial_text(fulltext)

    single_keywords = get_single_keywords(_SKWS, fulltext)

    composite_keywords = get_composite_keywords(_CKWS, fulltext,
                                                single_keywords)

    return get_keywords_output(single_keywords, composite_keywords,
        author_keywords, output_mode, output_limit, spires)

def get_keywords_output(single_keywords, composite_keywords,
                        author_keywords=None, style="text",
                        output_limit=0, spires=False):
    """Returns a formatted string representing the keywords according
    to the style chosen."""

    # Filter the "nonstandalone" keywords
    single_keywords = filter_nostandalone(single_keywords)

    # Limit the number of keywords to nkeywords.
    single_keywords = resize_keywords_for_output(single_keywords,
        output_limit, single=True)
    composite_keywords = resize_keywords_for_output(composite_keywords,
        output_limit, composite=True)

    if style == "text":
        return output_text(single_keywords, composite_keywords,
            author_keywords, spires)
    elif style == "marcxml":
        return output_marc(single_keywords, composite_keywords, spires)
    elif style == "html":
        return output_html(single_keywords, composite_keywords, spires)

def get_partial_text(fulltext):
    """Returns a shortened version of the fulltext used with the partial
    matching mode. The version is composed of 20% in the beginning and
    20% in the middle of the text."""
    length = len(fulltext)

    get_index = lambda x: int(float(x) / 100 * length)

    partial_text = [fulltext[get_index(start):get_index(end)]
                    for start, end in CFG_BIBCLASSIFY_PARTIAL_TEXT]

    return "\n".join(partial_text)

def get_regular_expressions(ontology_file, rebuild=False, no_cache=False):
    """Returns a list of patterns compiled from the RDF/SKOS taxonomy.
    Uses cache if it exists and if the taxonomy hasn't changed."""
    if os.access(ontology_file, os.R_OK):
        if rebuild or no_cache:
            return build_cache(ontology_file, no_cache)

        if os.access(get_cache_file(ontology_file), os.R_OK):
            if (os.path.getmtime(get_cache_file(ontology_file)) >
               os.path.getmtime(ontology_file)):
                # Cache is more recent than the ontology: use cache.
                return get_cache(ontology_file)
            else:
                # Ontology is more recent than the cache: rebuild cache.
                return build_cache(ontology_file, no_cache)
        else:
            # Cache does not exist. Build cache.
            return build_cache(ontology_file, no_cache)
    else:
        if os.access(get_cache_file(ontology_file), os.R_OK):
            # Ontology file not found. Use the cache instead.
            return get_cache(ontology_file)
        else:
            # Cannot access the ontology nor the cache. Exit.
            print >> sys.stderr, "Neither ontology file nor cache can be read."
            sys.exit(-1)
            return None

def get_searchable_regex(basic_labels, hidden_labels):
    """Returns the searchable regular expressions for the single
    keyword."""
    # Hidden labels are used to store regular expressions.
    hidden_regex_dict = {}
    for hidden_label in hidden_labels:
        if is_regex(hidden_label):
            hidden_regex_dict[hidden_label] = \
                re.compile(CFG_BIBCLASSIFY_WORD_WRAP % hidden_label[1:-1])
        else:
            pattern = get_regex_pattern(hidden_label)
            hidden_regex_dict[hidden_label] = \
                re.compile(CFG_BIBCLASSIFY_WORD_WRAP % pattern)

    # We check if the basic label (preferred or alternative) is matched
    # by a hidden label regex. If yes, discard it.
    regex_dict = {}
    # Create regex for plural forms and add them to the hidden labels.
    for label in basic_labels:
        pattern = get_regex_pattern(label)
        regex_dict[label] = re.compile(CFG_BIBCLASSIFY_WORD_WRAP % pattern)

    # Merge both dictionaries.
    regex_dict.update(hidden_regex_dict)

    return regex_dict.values()

def get_regex_pattern(label):
    """Returns a regular expression of the label that takes care of
    plural and different kinds of separators."""
    parts = _split_by_punctuation.split(label)

    for index, part in enumerate(parts):
        if index % 2 == 0:
            # Word
            if not parts[index].isdigit():
                parts[index] = convert_word(parts[index])
        else:
            # Punctuation
            if not parts[index + 1]:
                # The separator is not followed by another word. Treat
                # it as a symbol.
                parts[index] = convert_punctuation(parts[index],
                    CFG_BIBCLASSIFY_SYMBOLS)
            else:
                parts[index] = convert_punctuation(parts[index],
                    CFG_BIBCLASSIFY_SEPARATORS)

    return "".join(parts)

def is_regex(string):
    """Checks if a concept is a regular expression."""
    return string[0] == "/" and string[-1] == "/"

def output_html(single_keywords, composite_keywords, spires=False):
    """Using the counts for each of the tags, write a simple HTML page
    to standard output containing a tag cloud representation. The CSS
    describes ten levels, each of which has differing font-size's,
    line-height's and font-weight's."""

    lines = []
    lines.append('''<html>
  <head>
    <title>Keyword Cloud</title>
    <style type="text/css">
      <!--
        a { color: #003DF5; text-decoration: none; }
        a:hover { color: #f1f1f1; text-decoration: none;
          background-color: #003DF5; }
        .pagebox { color: #000; margin-left: 1em; margin-bottom: 1em;
          border: 1px solid #000; padding: 1em;
          background-color: #f1f1f1; font-family: arial, sans-serif;
          max-width: 700px; margin: 10px; padding-left: 10px;
          float: left; }
        .pagebox1 { color: #B5B5B5; margin-left: 1em;
          margin-bottom: 1em; border: 1px dotted #B5B5B5;
          padding: 1em; background-color: #f2f2f2;
          font-family: arial, sans-serif; max-width: 300px;
          margin: 10px; padding-left: 10px; float: left; }
        .pagebox2 { color: #000; margin-left: 1em; margin-bottom: 1em;
          border: 0px solid #000; padding: 1em; font-size: x-small;
          font-family: arial, sans-serif; margin: 10px;
          padding-left: 10px; float: left; }''')

    level = (
'''        .level%d { color:#003DF5; font-size:%dpx; line-height:%dpx;
          font-weight:bold; }''')

    for index, size in enumerate(range(12, 40, 3)):
        lines.append(level % (index, size, size + 5))

    level_list = (10, 7.5, 5, 4, 3, 2, 1.7, 1.5, 1.3, 1)
    keyword = ('          <span class="level%d" style="color:%s !important">'
        '%s </span>')

    lines.append("      -->")
    lines.append("    </style>")
    lines.append("  </head>")
    lines.append("  <body>")
    lines.append("    <table>")
    lines.append("      <tr>")
    lines.append('        <div class="pagebox" align="top" />')

    tags = []

    max_counts = [len(single_keywords[0][1]), composite_keywords[0][1]]

    # Add the single tags
    color = "#b5b5b5"
    for subject, spans in single_keywords:
        for index, value in enumerate(level_list):
            if len(spans) <= max_counts[0] / value:
                if spires:
                    obj = spires_label(subject)
                else:
                    obj = _SKWS[subject].concept
                obj = obj.replace(" ", "&#160")
                tags.append(keyword % (index, color, obj))
                break

    # Add the composite tags
    color = "#003df5"
    for subject, count, components in composite_keywords:
        for index, value in enumerate(level_list):
            if count <= max_counts[1] / value:
                if spires:
                    obj = spires_label(subject)
                else:
                    obj = _CKWS[subject].concept
                obj = obj.replace(" ", "&#160")
                tags.append(keyword % (index, color, obj))
                break

    # Appends the keywords in a random way (in order to create the cloud
    # effect)
    while tags:
        index = random.randint(0, len(tags) - 1)
        lines.append(tags[index])
        tags[index] = tags[-1]
        del tags[-1]

    lines.append(" " * 8 + "</div>")
    lines.append(" " * 6 + "</tr>")
    lines.append(" " * 4 + "</table>")
    lines.append(" " * 2 + "</body>")
    lines.append("</html>")

    return "\n".join(lines)

def output_marc(single_keywords, composite_keywords, spires=False):
    """Outputs the keywords in the MARCXML format."""
    marc_pattern = ('<datafield tag="653" ind1="1" ind2=" ">\n'
                    '    <subfield code="a">%s</subfield>\n'
                    '    <subfield code="9">BibClassify/HEP</subfield>\n'
                    '</datafield>\n')

    output = []

    for subject, spans in single_keywords:
        if spires:
            output.append(spires_label(subject))
        else:
            output.append(_SKWS[subject].concept)

    for subject, count, components in composite_keywords:
        if spires:
            output.append(spires_label(subject))
        else:
            output.append(_CKWS[subject].concept)

    return "".join([marc_pattern % keyword for keyword in output])

def output_text(single_keywords=None, composite_keywords=None,
                author_keywords=None, spires=False):
    """Outputs the results obtained in text format."""
    output = []

    if author_keywords is not None:
        output.append("\n\nExplicit keywords:")
        for keyword in author_keywords:
            output.append(keyword)

    if composite_keywords is not None:
        output.append("\n\nComposite keywords:")
        for subject, count, components in composite_keywords:
            if spires:
                concept = spires_label(subject)
            else:
                concept = _CKWS[subject].concept
            output.append("%d  %s %s" % (count, concept, components))

    if single_keywords is not None:
        output.append("\n\nSingle keywords:")
        for subject, spans in single_keywords:
            if spires:
                concept = spires_label(subject)
            else:
                concept = _SKWS[subject].concept
            output.append("%d  %s" % (len(spans), concept))

    return "\n".join(output) + "\n"

def check_ontology(ontology_file):
    """Checks the consistency of the ontology and outputs a list of
    errors and warnings."""
    print "Building graph with Python RDFLib version %s" % rdflib.__version__
    if rdflib.__version__ >= '2.3.2':
        store = rdflib.ConjunctiveGraph()
    else:
        store = rdflib.Graph()

    store.parse(ontology_file)

    print "Graph was successfully built."

    prefLabel = "prefLabel"
    hiddenLabel = "hiddenLabel"
    altLabel = "altLabel"
    composite = "composite"
    compositeOf = "compositeOf"
    note = "note"

    both_skw_and_ckw = []

    # Build a dictionary we will reason on later.
    uniq_subjects = {}
    for subject in store.subjects():
        uniq_subjects[subject] = None

    subjects = {}
    for subject in uniq_subjects:
        strsubject = str(subject).split("#Composite.")[-1]
        strsubject = strsubject.split("#")[-1]
        if (strsubject == "http://cern.ch/thesauri/HEPontology.rdf" or
            strsubject == "compositeOf"):
            continue
        components = {}
        for predicate, value in store.predicate_objects(subject):
            strpredicate = str(predicate).split("#")[-1]
            strobject = str(value).split("#Composite.")[-1]
            strobject = strobject.split("#")[-1]
            components.setdefault(strpredicate, []).append(strobject)
        if strsubject in subjects:
            both_skw_and_ckw.append(strsubject)
        else:
            subjects[strsubject] = components

    print "Ontology contains %s concepts." % len(subjects)

    no_prefLabel = []
    multiple_prefLabels = []
    multiple_notes = []
    bad_notes = []
    # Subjects with no composite or compositeOf predicate
    lonely = []
    both_composites = []
    bad_hidden_labels = {}
    bad_alt_labels = {}
    # Problems with composite keywords
    composite_problem1 = []
    composite_problem2 = []
    composite_problem3 = []
    composite_problem4 = {}
    composite_problem5 = []
    composite_problem6 = []

    stemming_collisions = []
    interconcept_collisions = {}

    for subject, predicates in subjects.iteritems():
        # No prefLabel or multiple prefLabels
        try:
            if len(predicates[prefLabel]) > 1:
                multiple_prefLabels.append(subject)
        except KeyError:
            no_prefLabel.append(subject)

        # Lonely and both composites.
        if not composite in predicates and not compositeOf in predicates:
            lonely.append(subject)
        elif composite in predicates and compositeOf in predicates:
            both_composites.append(subject)

        # Multiple or bad notes
        if note in predicates:
            if len(predicates[note]) > 1:
                multiple_notes.append(subject)
            bad_notes += [(subject, n) for n in predicates[note]
                          if n != "nostandalone"]

        # Bad hidden labels
        if hiddenLabel in predicates:
            for lbl in predicates[hiddenLabel]:
                if lbl.startswith("/") ^ lbl.endswith("/"):
                    bad_hidden_labels.setdefault(subject, []).append(lbl)

        # Bad alt labels
        if altLabel in predicates:
            for lbl in predicates[altLabel]:
                if len(re.findall("/", lbl)) >= 2 or ":" in lbl:
                    bad_alt_labels.setdefault(subject, []).append(lbl)

        # Check composite
        if composite in predicates:
            for ckw in predicates[composite]:
                if ckw in subjects:
                    if compositeOf in subjects[ckw]:
                        if not subject in subjects[ckw][compositeOf]:
                            composite_problem3.append((subject, ckw))
                    else:
                        if not ckw in both_skw_and_ckw:
                            composite_problem2.append((subject, ckw))
                else:
                    composite_problem1.append((subject, ckw))

        # Check compositeOf
        if compositeOf in predicates:
            for skw in predicates[compositeOf]:
                if skw in subjects:
                    if composite in subjects[skw]:
                        if not subject in subjects[skw][composite]:
                            composite_problem6.append((subject, skw))
                    else:
                        if not skw in both_skw_and_ckw:
                            composite_problem5.append((subject, skw))
                else:
                    composite_problem4.setdefault(skw, []).append(subject)

        # Check for stemmed labels
        if compositeOf in predicates:
            labels = (altLabel, hiddenLabel)
        else:
            labels = (prefLabel, altLabel, hiddenLabel)

        patterns = {}
        for label in [lbl for lbl in labels if lbl in predicates]:
            for expression in [expr for expr in predicates[label]
                                    if not is_regex(expr)]:
                pattern = get_regex_pattern(expression)
                interconcept_collisions.setdefault(pattern,
                    []).append((subject, label))
                if pattern in patterns:
                    stemming_collisions.append((subject,
                        patterns[pattern],
                        (label, expression)
                        ))
                else:
                    patterns[pattern] = (label, expression)

    print "\n==== ERRORS ===="

    if no_prefLabel:
        print "\nConcepts with no prefLabel: %d" % len(no_prefLabel)
        print "\n".join(["   %s" % subj for subj in no_prefLabel])
    if multiple_prefLabels:
        print ("\nConcepts with multiple prefLabels: %d" %
            len(multiple_prefLabels))
        print "\n".join(["   %s" % subj for subj in multiple_prefLabels])
    if both_composites:
        print ("\nConcepts with both composite properties: %d" %
            len(both_composites))
        print "\n".join(["   %s" % subj for subj in both_composites])
    if bad_hidden_labels:
        print "\nConcepts with bad hidden labels: %d" % len(bad_hidden_labels)
        for kw, lbls in bad_hidden_labels.iteritems():
            print "   %s:" % kw
            print "\n".join(["      '%s'" % lbl for lbl in lbls])
    if bad_alt_labels:
        print "\nConcepts with bad alt labels: %d" % len(bad_alt_labels)
        for kw, lbls in bad_alt_labels.iteritems():
            print "   %s:" % kw
            print "\n".join(["      '%s'" % lbl for lbl in lbls])
    if both_skw_and_ckw:
        print ("\nKeywords that are both skw and ckw: %d" %
            len(both_skw_and_ckw))
        print "\n".join(["   %s" % subj for subj in both_skw_and_ckw])

    print

    if composite_problem1:
        print "\n".join(["SKW '%s' references an unexisting CKW '%s'." %
            (skw, ckw) for skw, ckw in composite_problem1])
    if composite_problem2:
        print "\n".join(["SKW '%s' references a SKW '%s'." %
            (skw, ckw) for skw, ckw in composite_problem2])
    if composite_problem3:
        print "\n".join(["SKW '%s' is not composite of CKW '%s'." %
            (skw, ckw) for skw, ckw in composite_problem3])
    if composite_problem4:
        for skw, ckws in composite_problem4.iteritems():
            print "SKW '%s' does not exist but is " "referenced by:" % skw
            print "\n".join(["    %s" % ckw for ckw in ckws])
    if composite_problem5:
        print "\n".join(["CKW '%s' references a CKW '%s'." % kw
            for kw in composite_problem5])
    if composite_problem6:
        print "\n".join(["CKW '%s' is not composed by SKW '%s'." % kw
            for kw in composite_problem6])

    print "\n==== WARNINGS ===="

    if multiple_notes:
        print "\nConcepts with multiple notes: %d" % len(multiple_notes)
        print "\n".join(["   %s" % subj for subj in multiple_notes])
    if bad_notes:
        print ("\nConcepts with bad notes: %d" % len(bad_notes))
        print "\n".join(["   '%s': '%s'" % note for note in bad_notes])
    if stemming_collisions:
        print ("\nFollowing keywords have unnecessary labels that have "
            "already been generated by BibClassify.")
        for subj in stemming_collisions:
            print "   %s:\n     %s\n     and %s" % subj

    print "\nFinished."
    sys.exit(0)

def filter_nostandalone(keywords):
    """Returns a copy of the keywords data structure stripped from its
    nonstandalone components."""
    filtered_keywords = {}

    for subject, spans in keywords.iteritems():
        if not _SKWS[subject].nostandalone:
            filtered_keywords[subject] = spans

    return filtered_keywords

def compare_skw(skw0, skw1):
    """Compare 2 single keywords records. First compare the
    occurrences, then the length of the word."""
    list_comparison = cmp(len(skw1[1]), len(skw0[1]))
    if list_comparison:
        return list_comparison
    else:
        return cmp(len(skw1[0]), len(skw0[0]))

def compare_ckw(ckw0, ckw1):
    """Compare 2 composite keywords records. First compare the
    occurrences, then the length of the word, at last the component
    counts."""
    count_comparison = cmp(ckw1[1], ckw0[1])
    if count_comparison:
        return count_comparison
    component_avg0 = sum(ckw0[2]) / len(ckw0[2])
    component_avg1 = sum(ckw1[2]) / len(ckw1[2])
    component_comparison =  cmp(component_avg1, component_avg0)
    if component_comparison:
        return component_comparison
    else:
        return cmp(len(ckw1[0]), len(ckw0[0]))

def resize_keywords_for_output(keywords, limit=20, single=False,
                               composite=False):
    """Returns a resized version of data structures of keywords to the
    given length.  This method takes care of the 'nonstandalone' option
    of the keywords. The single keywords with this option set are
    removed from the dictionary."""
    if not (single ^ composite):
        print >> sys.stderr, "Problem in resize_keywords_for_output."
        sys.exit(1)

    if single:
        keywords = list(keywords.items())
        keywords.sort(compare_skw)
    elif composite:
        keywords.sort(compare_ckw)

    if limit:
        return keywords[:limit]
    else:
        return keywords

def spires_label(subject):
    """Returns the SPIRES representation of a keyword. If the
    spiresLabel is set, then it returns that value otherwise it replaces
    the colon in the prefLabel by a comma."""
    try:
        if subject in _SKWS:
            return _SKWS[subject].spires
    except AttributeError:
        # The keyword doesn't have a SPIRES label.
        return _SKWS[subject].concept

    try:
        return _CKWS[subject].spires
    except AttributeError:
        # The keyword doesn't have a SPIRES label. Build "comp1, comp2".
        components = _CKWS[subject].compositeof
        spires_labels = [spires_label(component) for component in components]
        return ", ".join(spires_labels)

if __name__ == "__main__":
    print >> sys.stderr, "Please use bibclassifycli from now on."
