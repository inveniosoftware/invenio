# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

"""
BibClassify ontology reader.

The ontology reader reads currently either a RDF/SKOS taxonomy or a
simple controlled vocabulary file (1 word per line). The first role of
this module is to manage the cached version of the ontology file. The
second role is to hold all methods responsible for the creation of
regular expressions. These methods are grammatically related as we take
care of different forms of the same words.  The grammatical rules can be
configured via the configuration file.

The main method from this module is get_regular_expressions.
"""

from datetime import datetime, timedelta
import cPickle
import os
import rdflib
import re
import sys
import tempfile
import time
import urllib2

try:
    from invenio.config import CFG_CACHEDIR
    from invenio.dbquery import run_sql
except ImportError:
    # Running in standalone.
    CFG_CACHEDIR = tempfile.gettempdir()

try:
    from bibclassify_config import CFG_BIBCLASSIFY_WORD_WRAP, \
        CFG_BIBCLASSIFY_INVARIABLE_WORDS, CFG_BIBCLASSIFY_EXCEPTIONS, \
        CFG_BIBCLASSIFY_UNCHANGE_REGULAR_EXPRESSIONS, \
        CFG_BIBCLASSIFY_GENERAL_REGULAR_EXPRESSIONS, \
        CFG_BIBCLASSIFY_SEPARATORS, CFG_BIBCLASSIFY_SYMBOLS
    from bibclassify_utils import write_message
except ImportError, err:
    print >> sys.stderr, "Import error: %s" % err
    sys.exit(0)

# Retrieve the custom configuration if it exists.
try:
    from bibclassify_config_local import *
except ImportError:
    # No local configuration was found.
    pass

_contains_digit = re.compile("\d")
_starts_with_non = re.compile("(?i)^non[a-z]")
_starts_with_anti = re.compile("(?i)^anti[a-z]")
_split_by_punctuation = re.compile("(\W+)")

_cache_location = None

single_keywords_by_subject = {}
composite_keywords_by_subject = {}

single_keywords_by_concept = {}
composite_keywords_by_concept = {}

def get_regular_expressions(ontology, rebuild=False, no_cache=False):
    """Returns a list of patterns compiled from the RDF/SKOS ontology.
    Uses cache if it exists and if the ontology hasn't changed."""

    # Translate the ontology name into a local path. Check if the name
    # relates to an existing ontology.
    ontology_names = _get_ontology_path(ontology)
    if ontology_names is not None:
        onto_long_name, onto_url = ontology_names
        onto_path = os.path.join(CFG_CACHEDIR, 'bibclassify', onto_long_name)
    else:
        write_message("ERROR: Unable to understand the ontology name "
            "provided: '%s'." % ontology, stream=sys.stderr, verbose=0)
        sys.exit(0)

    # If a new remote ontology can be found, then download it.
    new_ontology = _download_remote_ontology(onto_url)

    if new_ontology:
        # A new ontology has been downloaded. Rebuild the cache.
        return _build_cache(onto_path, no_cache=no_cache)

    if os.access(onto_path, os.R_OK):
        # Can read from the ontology.
        if rebuild or no_cache:
            write_message("INFO: Cache generation is manually forced.",
                stream=sys.stderr, verbose=3)
            return _build_cache(onto_path, no_cache=no_cache)

        if os.access(_get_cache_path(onto_path), os.R_OK):
            if (os.path.getmtime(_get_cache_path(onto_path)) >
                os.path.getmtime(onto_path)):
                # Cache is more recent than the ontology: use cache.
                return _get_cache(onto_path)
            else:
                # Ontology is more recent than the cache: rebuild cache.
                if not no_cache:
                    write_message("WARNING: The ontology '%s' has changed "
                        "since the last cache generation." % ontology,
                        stream=sys.stderr, verbose=2)
                return _build_cache(onto_path, no_cache=no_cache)
        else:
            # Cache does not exist. Build cache.
            return _build_cache(onto_path, no_cache=no_cache)
    else:
        if os.access(_get_cache_path(onto_path), os.R_OK):
            # ontology file not found. Use the cache instead.
            write_message("WARNING: The ontology couldn't be located. However "
                "a cached version of it is available. Using it as a "
                "reference.", stream=sys.stderr, verbose=2)
            return _get_cache(onto_path)
        else:
            # Cannot access the ontology nor the cache. Exit.
            write_message("ERROR: Neither the ontology file nor a cached "
                "version of it could be found.", stream=sys.stderr, verbose=0)
            sys.exit(0)
            return None

def _download_remote_ontology(onto_url, time_difference=None):
    """Checks if the online ontology is more recent than the local ontology. If
    yes, try to download and store it in Invenio's cache directory. Return a
    boolean describing the success of the operation."""
    if onto_url is None:
        return False

    dl_dir = ((CFG_CACHEDIR or tempfile.gettempdir()) + os.sep +
        "bibclassify" + os.sep)
    if not os.path.exists(dl_dir):
        os.mkdir(dl_dir)

    local_file = dl_dir + os.path.basename(onto_url)
    remote_modif_time = _get_last_modification_date(onto_url)
    try:
        local_modif_seconds = os.path.getmtime(local_file)
    except OSError:
        # The local file does not exist. Download the ontology.
        download = True
        write_message("INFO: The local ontology could not be found.",
            stream=sys.stderr, verbose=3)
    else:
        local_modif_time = datetime(*time.gmtime(local_modif_seconds)[0:6])
        # Let's set a time delta of 1 hour and 10 minutes.
        time_difference = time_difference or timedelta(hours=1, minutes=10)
        download = remote_modif_time > local_modif_time + time_difference
        if download:
            write_message("INFO: The remote ontology '%s' is more recent "
                "than the local ontology." % onto_url, stream=sys.stderr,
                verbose=3)

    if download:
        return _download_ontology(onto_url, local_file)
    else:
        return False

def _get_ontology_path(ontology):
    """Returns the path to the short ontology name."""
    if os.access(ontology, os.R_OK):
        return (ontology, None)
    else:
        result = run_sql("SELECT name, location from clsMETHOD")
        for onto_short_name, onto_url in result:
            onto_long_name = os.path.basename(onto_url)
            if ontology in (onto_short_name, onto_long_name, onto_url):
                return (onto_long_name, onto_url)
        return None

class SingleKeyword:
    """A single keyword element that treats and stores information
    fields retrieved from the RDF/SKOS taxonomy."""
    def __init__(self, subject, store=None, namespace=None):
        """Inits a SingleKeyword object with a subject string and the RDFLib
        taxonomy object."""
        if store is None:
            self.concept = subject
            self.regex = _get_searchable_regex(basic=[subject])
            self.nostandalone = False
            self.spires = ""
            self.fieldcodes = []
            self.core = False
        else:
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

            self.regex = _get_searchable_regex(basic_labels, hidden_labels)

            self.core = False
            self.nostandalone = False
            for note in map(lambda s: str(s).lower().strip(),
                store.objects(subject, namespace["note"])):
                if note == 'core':
                    self.core = True
                if note in ("nostandalone", "nonstandalone"):
                    self.nostandalone = True

            self.spires = store.value(subject, namespace["spiresLabel"], any=True)
            if self.spires is not None:
                self.spires = str(self.spires)

            self.fieldcodes = []
            for code in store.objects(subject, namespace["field"]):
                self.fieldcodes.append(str(code))

    def output(self, spires=False):
        """Returns the best output for the keyword."""
        if spires:
            if self.spires:
                return self.spires
            else:
                return self.concept
        else:
            return self.concept

    def __repr__(self):
        return "<SingleKeyword: %s>" % self.concept

class CompositeKeyword:
    """A composite keyword element that treats and stores information
    fields retrieved from the RDF/SKOS taxonomy."""
    def __init__(self, store, namespace, subject):
        small_subject = subject.split("#Composite.")[-1]

        try:
            self.concept = store.value(subject, namespace["prefLabel"],
                any=True)
        except KeyError:
            # Keyword has no prefLabel. We can discard that error.
            write_message("WARNING: Keyword with subject %s has no prefLabel" %
                small_subject, stream=sys.stderr, verbose=2)

        component_positions = []
        for label in store.objects(subject, namespace["compositeOf"]):
            strlabel = str(label).split("#")[-1]
            component_name = label.split("#")[-1]
            component_positions.append((small_subject.find(component_name),
                strlabel))

        self.compositeof = []
        component_positions.sort()
        try:
            for position in component_positions:
                self.compositeof.append(single_keywords_by_subject[position[1]])
        except KeyError:
            # One single keyword is not present in the taxonomy. This
            # is due to an error in the taxonomy description.
            self.compositeof = []

        self.core = False
        for note in map(lambda s: str(s).lower().strip(),
            store.objects(subject, namespace["note"])):
            if note == 'core':
                self.core = True

        self.spires = store.value(subject, namespace["spiresLabel"], any=True)
        if self.spires is not None:
            self.spires = self.spires

        self.regex = []
        for label in store.objects(subject, namespace["altLabel"]):
            pattern = _get_regex_pattern(label)
            self.regex.append(re.compile(CFG_BIBCLASSIFY_WORD_WRAP % pattern))

        self.fieldcodes = []
        for code in store.objects(subject, namespace["field"]):
            self.fieldcodes.append(str(code))

    def output(self, spires=False):
        """Returns the best output for the keyword."""
        if spires:
            if self.spires:
                return self.spires
            else:
                return self.concept.replace(":", ",")
        else:
            return self.concept

    def __repr__(self):
        return "<CompositeKeyword: %s>" % self.concept

def _build_cache(source_file, no_cache=False):
    """Builds the cached data by parsing the RDF taxonomy file or a
    vocabulary file."""
    if rdflib.__version__ >= '2.3.2':
        store = rdflib.ConjunctiveGraph()
    else:
        store = rdflib.Graph()

    timer_start = time.clock()

    global single_keywords_by_subject
    global composite_keywords_by_subject
    single_keywords, composite_keywords = [], []

    try:
        write_message("INFO: Building RDFLib's conjunctive graph.",
            stream=sys.stderr, verbose=3)
        store.parse(source_file)
    except:
        # File is not a RDF file. We assume it is a controlled vocabulary.
        write_message("INFO: The ontology file is not a valid RDF file. "
            "Assuming it is a controlled vocabulary file.", stream=sys.stderr,
            verbose=3)
        filestream = open(source_file, "r")
        for line in filestream:
            keyword = line.strip()
            single_keywords.append(SingleKeyword(keyword))
    else:
        write_message("INFO: Building cache from RDF file %s." % source_file,
            stream=sys.stderr, verbose=3)
        # File is a RDF file.
        namespace = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")

        single_count = 0
        composite_count = 0

        for subject_object in store.subject_objects(namespace["prefLabel"]):
            # Keep only the single keywords.
            # FIXME: Remove or alter that condition in order to allow using
            # other ontologies that do not have this composite notion (such
            # as NASA-subjects.rdf)
            if not store.value(subject_object[0], namespace["compositeOf"],
                any=True):
                skw = SingleKeyword(subject_object[0], store=store,
                    namespace=namespace)
                single_keywords.append(skw)
                subject = str(subject_object[0]).split("#")[-1]
                single_keywords_by_subject[subject] = skw
                single_count += 1

        # Let's go through the composite keywords.
        for subject, pref_label in \
            store.subject_objects(namespace["prefLabel"]):
            # Keep only the single keywords.
            if store.value(subject, namespace["compositeOf"], any=True):
                strsubject = str(subject).split("#")[-1]
                composite_keywords.append(CompositeKeyword(store,
                    namespace, subject))
                composite_count += 1

        store.close()

    cached_data = {}
    cached_data["single"] = single_keywords
    cached_data["composite"] = composite_keywords
    cached_data["creation_time"] = time.gmtime()

    write_message("INFO: Building taxonomy... %d terms built in %.1f sec." %
        (len(single_keywords) + len(composite_keywords),
        time.clock() - timer_start), stream=sys.stderr, verbose=3)

    if not no_cache:
        # Serialize.
        try:
            filestream = open(_get_cache_path(source_file), "w")
        except IOError:
            # Impossible to write the cache.
            write_message("ERROR: Impossible to write cache to %s." %
                _get_cache_path(source_file), stream=sys.stderr, verbose=1)
            return (single_keywords, composite_keywords)
        else:
            write_message("INFO: Writing cache to file %s." %
                _get_cache_path(source_file), stream=sys.stderr, verbose=3)
            cPickle.dump(cached_data, filestream, 1)
            filestream.close()

    return (single_keywords, composite_keywords)

def _capitalize_first_letter(word):
    """Returns a regex pattern with the first letter accepting both lowercase
    and uppercase."""
    if word[0].isalpha():
        # These two cases are necessary in order to get a regex pattern
        # starting with '[xX]' and not '[Xx]'. This allows to check for
        # colliding regex afterwards.
        if word[0].isupper():
            return "[" + word[0].swapcase() + word[0] +"]" + word[1:]
        else:
            return "[" + word[0] + word[0].swapcase() +"]" + word[1:]
    return word

def _convert_punctuation(punctuation, conversion_table):
    """Returns a regular expression for a punctuation string."""
    if punctuation in conversion_table:
        return conversion_table[punctuation]
    return re.escape(punctuation)

def _convert_word(word):
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
        word = "non-?" + _capitalize_first_letter(_convert_word(word[3:]))
    elif _starts_with_anti.search(word):
        word = "anti-?" + _capitalize_first_letter(_convert_word(word[4:]))

    if out is not None:
        return _capitalize_first_letter(out)

    # A few invariable words.
    if word in CFG_BIBCLASSIFY_INVARIABLE_WORDS:
        return _capitalize_first_letter(word)

    # Some exceptions that would not produce good results with the set of
    # general_regular_expressions.
    if word in CFG_BIBCLASSIFY_EXCEPTIONS:
        return _capitalize_first_letter(CFG_BIBCLASSIFY_EXCEPTIONS[word])

    for regex in CFG_BIBCLASSIFY_UNCHANGE_REGULAR_EXPRESSIONS:
        if regex.search(word) is not None:
            return _capitalize_first_letter(word)

    for regex, replacement in CFG_BIBCLASSIFY_GENERAL_REGULAR_EXPRESSIONS:
        stemmed = regex.sub(replacement, word)
        if stemmed != word:
            return _capitalize_first_letter(stemmed)

    return _capitalize_first_letter(word + "s?")

def _get_cache(source_file):
    """Get the cached taxonomy using the cPickle module. No check is done at
    that stage."""
    timer_start = time.clock()

    cache_file = _get_cache_path(source_file)
    filestream = open(cache_file, "r")
    try:
        cached_data = cPickle.load(filestream)
    except (cPickle.UnpicklingError, AttributeError, DeprecationWarning):
        write_message("WARNING: The existing cache in %s is not readable. "
            "Rebuilding it." %
            cache_file, stream=sys.stderr, verbose=3)
        filestream.close()
        os.remove(cache_file)
        return _build_cache(source_file)
    filestream.close()

    single_keywords = cached_data["single"]
    composite_keywords = cached_data["composite"]

    write_message("INFO: Found ontology cache created on %s." %
        time.asctime(cached_data["creation_time"]), stream=sys.stderr,
        verbose=3)

    write_message("INFO: Retrieved cache... %d terms read in %.1f sec." %
        (len(single_keywords) + len(composite_keywords),
        time.clock() - timer_start), stream=sys.stderr, verbose=3)

    return (single_keywords, composite_keywords)

def _get_cache_path(source_file):
    """Returns the file name of the cached taxonomy."""
    global _cache_location

    relative_dir = "bibclassify"
    cache_name = os.path.basename(source_file) + ".db"

    if _cache_location is not None:
        # The location of the cache has been previously found.
        return _cache_location
    else:
        # Find the most probable location of the cache. First consider
        # Invenio's temp directory then the system temp directory.
        if os.access(CFG_CACHEDIR, os.W_OK):
            tmp_dir = CFG_CACHEDIR
        else:
            tmp_dir = tempfile.gettempdir()

        absolute_dir = os.path.join(tmp_dir, relative_dir)
        # Test bibclassify's directory in the temp directory.
        if not os.path.exists(absolute_dir):
            try:
                os.mkdir(absolute_dir)
            except:
                write_message("WARNING: Impossible to write in the temp "
                    "directory %s." % tmp_dir, stream=sys.stderr,
                    verbose=2)
                _cache_location = ""
                return _cache_location

        # At that time, the bibclassify's directory should exist. Test if it's
        # readable and writable.
        if os.access(absolute_dir, os.R_OK) and os.access(absolute_dir,
            os.W_OK):
            _cache_location = os.path.join(absolute_dir, cache_name)
            return _cache_location
        else:
            write_message("WARNING: Cache directory does exist but is not "
                "accessible. Check your permissions.", stream=sys.stderr,
                verbose=2)
            _cache_location = ""
            return _cache_location

def _get_last_modification_date(url):
    """Get the last modification date of the ontology."""
    request = urllib2.Request(url)
    request.get_method = lambda: "HEAD"
    http_file = urllib2.urlopen(request)
    date_string = http_file.headers["last-modified"]
    parsed = time.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
    return datetime(*(parsed)[0:6])

def _download_ontology(url, local_file):
    """Downloads the ontology and stores it in CFG_CACHEDIR."""
    write_message("INFO: Copying remote ontology '%s' to file '%s'." % (url,
        local_file), stream=sys.stderr, verbose=3)
    try:
        url_desc = urllib2.urlopen(url)
        file_desc = open(local_file, 'w')
        file_desc.write(url_desc.read())
        file_desc.close()
    except IOError, e:
        print e
        return False
    except:
        write_message("WARNING: Unable to download the ontology. '%s'" %
            sys.exc_info()[0], stream=sys.stderr, verbose=2)
        return False
    else:
        write_message("INFO: Done copying.", stream=sys.stderr, verbose=3)
        return True

def _get_searchable_regex(basic=None, hidden=None):
    """Returns the searchable regular expressions for the single
    keyword."""
    # Hidden labels are used to store regular expressions.
    basic = basic or []
    hidden = hidden or []

    hidden_regex_dict = {}
    for hidden_label in hidden:
        if _is_regex(hidden_label):
            hidden_regex_dict[hidden_label] = \
                re.compile(CFG_BIBCLASSIFY_WORD_WRAP % hidden_label[1:-1])
        else:
            pattern = _get_regex_pattern(hidden_label)
            hidden_regex_dict[hidden_label] = \
                re.compile(CFG_BIBCLASSIFY_WORD_WRAP % pattern)

    # We check if the basic label (preferred or alternative) is matched
    # by a hidden label regex. If yes, discard it.
    regex_dict = {}
    # Create regex for plural forms and add them to the hidden labels.
    for label in basic:
        pattern = _get_regex_pattern(label)
        regex_dict[label] = re.compile(CFG_BIBCLASSIFY_WORD_WRAP % pattern)

    # Merge both dictionaries.
    regex_dict.update(hidden_regex_dict)

    return regex_dict.values()

def _get_regex_pattern(label):
    """Returns a regular expression of the label that takes care of
    plural and different kinds of separators."""
    parts = _split_by_punctuation.split(label)

    for index, part in enumerate(parts):
        if index % 2 == 0:
            # Word
            if not parts[index].isdigit() and len(parts[index]) > 1:
                parts[index] = _convert_word(parts[index])
        else:
            # Punctuation
            if not parts[index + 1]:
                # The separator is not followed by another word. Treat
                # it as a symbol.
                parts[index] = _convert_punctuation(parts[index],
                    CFG_BIBCLASSIFY_SYMBOLS)
            else:
                parts[index] = _convert_punctuation(parts[index],
                    CFG_BIBCLASSIFY_SEPARATORS)

    return "".join(parts)

def _is_regex(string):
    """Checks if a concept is a regular expression."""
    return string[0] == "/" and string[-1] == "/"

def check_taxonomy(taxonomy):
    """Checks the consistency of the taxonomy and outputs a list of
    errors and warnings."""
    write_message("INFO: Building graph with Python RDFLib version %s" %
        rdflib.__version__, stream=sys.stdout, verbose=0)

    if rdflib.__version__ >= '2.3.2':
        store = rdflib.ConjunctiveGraph()
    else:
        store = rdflib.Graph()

    try:
        store.parse(taxonomy)
    except:
        write_message("ERROR: The taxonomy is not a valid RDF file. Are you "
            "trying to check a controlled vocabulary?", stream=sys.stdout,
            verbose=0)
        sys.exit(0)

    write_message("INFO: Graph was successfully built.", stream=sys.stdout,
        verbose=0)

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

    write_message("INFO: Taxonomy contains %s concepts." % len(subjects),
        stream=sys.stdout, verbose=0)

    no_prefLabel = []
    multiple_prefLabels = []
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
            bad_notes += [(subject, n) for n in predicates[note]
                          if n not in ('nostandalone', 'core')]

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
                                    if not _is_regex(expr)]:
                pattern = _get_regex_pattern(expression)
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
