# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

"""BibClassify ontology reader.

The ontology reader reads currently either a RDF/SKOS taxonomy or a
simple controlled vocabulary file (1 word per line). The first role of
this module is to manage the cached version of the ontology file. The
second role is to hold all methods responsible for the creation of
regular expressions. These methods are grammatically related as we take
care of different forms of the same words.  The grammatical rules can be
configured via the configuration file.

The main method from this module is get_regular_expressions.
"""

from __future__ import print_function

from datetime import datetime, timedelta
from six import iteritems
from six.moves import cPickle

import os
import re
import sys
import tempfile
import time
import urllib2
import traceback
import xml.sax
import thread
import rdflib

from invenio.legacy.bibclassify import config as bconfig
from invenio.modules.classifier.errors import TaxonomyError

log = bconfig.get_logger("bibclassify.ontology_reader")
from invenio import config

from invenio.modules.classifier.registry import taxonomies

# only if not running in a stanalone mode
if bconfig.STANDALONE:
    dbquery = None
    from urllib2 import urlopen
else:
    from invenio.legacy import dbquery
    from invenio.utils.url import make_invenio_opener

    urlopen = make_invenio_opener('BibClassify').open

_contains_digit = re.compile("\d")
_starts_with_non = re.compile("(?i)^non[a-z]")
_starts_with_anti = re.compile("(?i)^anti[a-z]")
_split_by_punctuation = re.compile("(\W+)")

_CACHE = {}


def get_cache(taxonomy_id):
    """Return thread-safe cache for the given taxonomy id.

    :param taxonomy_id: identifier of the taxonomy
    :type taxonomy_id: str

    :return: dictionary object (empty if no taxonomy_id
        is found), you must not change anything inside it.
        Create a new dictionary and use set_cache if you want
        to update the cache!
    """
    # Because of a standalone mode, we don't use the
    # invenio.data_cacher.DataCacher, but it has no effect
    # on proper functionality.

    if taxonomy_id in _CACHE:
        ctime, taxonomy = _CACHE[taxonomy_id]

        # check it is fresh version
        onto_name, onto_path, onto_url = _get_ontology(taxonomy_id)
        cache_path = _get_cache_path(onto_name)

        # if source exists and is newer than the cache hold in memory
        if os.path.isfile(onto_path) and os.path.getmtime(onto_path) > ctime:
            log.info('Forcing taxonomy rebuild as cached'
                     ' version is newer/updated.')
            return {}  # force cache rebuild

        # if cache exists and is newer than the cache hold in memory
        if os.path.isfile(cache_path) and os.path.getmtime(cache_path) > ctime:
            log.info('Forcing taxonomy rebuild as source'
                     ' file is newer/updated.')
            return {}
        log.info('Taxonomy retrieved from cache')
        return taxonomy
    return {}


def set_cache(taxonomy_id, contents):
    """Update cache in a thread-safe manner."""
    lock = thread.allocate_lock()
    lock.acquire()
    try:
        _CACHE[taxonomy_id] = (time.time(), contents)
    finally:
        lock.release()


def get_regular_expressions(taxonomy_name, rebuild=False, no_cache=False):
    """Return a list of patterns compiled from the RDF/SKOS ontology.

    Uses cache if it exists and if the taxonomy hasn't changed.
    """
    # Translate the ontology name into a local path. Check if the name
    # relates to an existing ontology.
    onto_name, onto_path, onto_url = _get_ontology(taxonomy_name)
    if not onto_path:
        raise TaxonomyError("Unable to locate the taxonomy: '%s'."
                            % taxonomy_name)

    cache_path = _get_cache_path(onto_name)
    log.debug('Taxonomy discovered, now we load it '
              '(from cache: %s, onto_path: %s, cache_path: %s)'
              % (not no_cache, onto_path, cache_path))

    if os.access(cache_path, os.R_OK):
        if os.access(onto_path, os.R_OK):
            if rebuild or no_cache:
                log.debug("Cache generation was manually forced.")
                return _build_cache(onto_path, skip_cache=no_cache)
        else:
            # ontology file not found. Use the cache instead.
            log.warning("The ontology couldn't be located. However "
                        "a cached version of it is available. Using it as a "
                        "reference.")
            return _get_cache(cache_path, source_file=onto_path)

        if (os.path.getmtime(cache_path) >
                os.path.getmtime(onto_path)):
            # Cache is more recent than the ontology: use cache.
            log.debug("Normal situation, cache is older than ontology,"
                      " so we load it from cache")
            return _get_cache(cache_path, source_file=onto_path)
        else:
            # Ontology is more recent than the cache: rebuild cache.
            log.warning("Cache '%s' is older than '%s'. "
                        "We will rebuild the cache" %
                        (cache_path, onto_path))
            return _build_cache(onto_path, skip_cache=no_cache)

    elif os.access(onto_path, os.R_OK):
        if not no_cache and\
                os.path.exists(cache_path) and\
                not os.access(cache_path, os.W_OK):
            raise TaxonomyError('We cannot read/write into: %s. '
                                'Aborting!' % cache_path)
        elif not no_cache and os.path.exists(cache_path):
            log.warning('Cache %s exists, but is not readable!' % cache_path)
        log.info("Cache not available. Building it now: %s" % onto_path)
        return _build_cache(onto_path, skip_cache=no_cache)

    else:
        raise TaxonomyError("We miss both source and cache"
                            " of the taxonomy: %s" % taxonomy_name)


def _get_remote_ontology(onto_url, time_difference=None):
    """Check if the online ontology is more recent than the local ontology.

    If yes, try to download and store it in Invenio's cache directory.

    Return a boolean describing the success of the operation.

    :return: path to the downloaded ontology.
    """
    if onto_url is None:
        return False

    dl_dir = ((config.CFG_CACHEDIR or tempfile.gettempdir()) + os.sep +
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
        log.info("The local ontology could not be found.")
    else:
        local_modif_time = datetime(*time.gmtime(local_modif_seconds)[0:6])
        # Let's set a time delta of 1 hour and 10 minutes.
        time_difference = time_difference or timedelta(hours=1, minutes=10)
        download = remote_modif_time > local_modif_time + time_difference
        if download:
            log.info("The remote ontology '%s' is more recent "
                     "than the local ontology." % onto_url)

    if download:
        if not _download_ontology(onto_url, local_file):
            log.warning("Error downloading the ontology from: %s" % onto_url)

    return local_file


def _get_ontology(ontology):
    """Return the (name, path, url) to the short ontology name.

    :param ontology: name of the ontology or path to the file or url.
    """
    onto_name = onto_path = onto_url = None

    # first assume we got the path to the file
    if os.path.exists(ontology):
        onto_name = os.path.split(os.path.abspath(ontology))[1]
        onto_path = os.path.abspath(ontology)
        onto_url = ""
    else:
        # if not, try to find it in a known locations
        discovered_file = _discover_ontology(ontology)
        if discovered_file:
            onto_name = os.path.split(discovered_file)[1]
            onto_path = discovered_file
            # i know, this sucks
            x = ontology.lower()
            if "http:" in x or "https:" in x or "ftp:" in x or "file:" in x:
                onto_url = ontology
            else:
                onto_url = ""
        else:
            # not found, look into a database
            # (it is last because when bibclassify
            # runs in a standalone mode,
            # it has no database - [rca, old-heritage]
            if not bconfig.STANDALONE:
                result = dbquery.run_sql("SELECT name, location from clsMETHOD WHERE name LIKE %s",
                                         ('%' + ontology + '%',))
                for onto_short_name, url in result:
                    onto_name = onto_short_name
                    onto_path = _get_remote_ontology(url)
                    onto_url = url

    return (onto_name, onto_path, onto_url)


def _discover_ontology(ontology_name):
    """Look for the file in a known places.

    Inside invenio/etc/bibclassify and a few other places
    like current directory.

    :param ontology: name or path name or url
    :type ontology: str

    :return: absolute path of a file if found, or None
    """
    last_part = os.path.split(os.path.abspath(ontology_name))[1]
    if last_part in taxonomies:
        return taxonomies.get(last_part)
    elif last_part + ".rdf" in taxonomies:
        return taxonomies.get(last_part + ".rdf")
    else:
        log.debug("No taxonomy with pattern '%s' found" % ontology_name)

    # LEGACY
    possible_patterns = [last_part, last_part.lower()]
    if not last_part.endswith('.rdf'):
        possible_patterns.append(last_part + '.rdf')
    places = [config.CFG_CACHEDIR,
              config.CFG_ETCDIR,
              os.path.join(config.CFG_CACHEDIR, "bibclassify"),
              os.path.join(config.CFG_ETCDIR, "bibclassify"),
              os.path.abspath('.'),
              os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           "../../../etc/bibclassify")),
              os.path.join(os.path.dirname(__file__), "bibclassify"),
              config.CFG_WEBDIR]

    log.debug("Searching for taxonomy using string: %s" % last_part)
    log.debug("Possible patterns: %s" % possible_patterns)
    for path in places:

        try:
            if os.path.isdir(path):
                log.debug("Listing: %s" % path)
                for filename in os.listdir(path):
                    #log.debug('Testing: %s' % filename)
                    for pattern in possible_patterns:
                        filename_lc = filename.lower()
                        if pattern == filename_lc and\
                                os.path.exists(os.path.join(path, filename)):
                            filepath = os.path.abspath(os.path.join(path,
                                                                    filename))
                            if (os.access(filepath, os.R_OK)):
                                log.debug("Found taxonomy at: %s" % filepath)
                                return filepath
                            else:
                                log.warning('Found taxonony at: %s, but it is'
                                            ' not readable. '
                                            'Continue searching...'
                                            % filepath)
        except OSError, os_error_msg:
            log.warning('OS Error when listing path '
                        '"%s": %s' % (str(path), str(os_error_msg)))
    log.debug("No taxonomy with pattern '%s' found" % ontology_name)


class KeywordToken:

    """KeywordToken is a class used for the extracted keywords.

    It can be initialized with values from RDF store or from
    simple strings. Specialty of this class is that objects are
    hashable by subject - so in the dictionary two objects with the
    same subject appears as one -- :see: self.__hash__ and self.__cmp__.
    """

    def __init__(self, subject, store=None, namespace=None, type='HEP'):
        """Initialize KeywordToken with a subject.

        :param subject: string or RDF object
        :param store: RDF graph object
                      (will be used to get info about the subject)
        :param namespace: RDF namespace object, used together with store
        :param type: type of this keyword.
        """
        self.id = subject
        self.type = type
        self.short_id = subject
        self.concept = ""
        self.regex = []
        self.nostandalone = False
        self.spires = False
        self.fieldcodes = []
        self.compositeof = []
        self.core = False
        # True means composite keyword
        self._composite = '#Composite' in subject
        self.__hash = None

        # the tokens are coming possibly from a normal text file
        if store is None:
            subject = subject.strip()
            self.concept = subject
            self.regex = _get_searchable_regex(basic=[subject])
            self.nostandalone = False
            self.fieldcodes = []
            self.core = False
            if subject.find(' ') > -1:
                self._composite = True

        # definitions from rdf
        else:
            self.short_id = self.short_id.split('#')[-1]

            # find alternate names for this label
            basic_labels = []

            # turn those patterns into regexes only for simple keywords
            if self._composite is False:
                try:
                    for label in store.objects(subject,
                                               namespace["prefLabel"]):
                        # XXX shall i make it unicode?
                        basic_labels.append(str(label))
                except TypeError:
                    pass
                self.concept = basic_labels[0]
            else:
                try:
                    self.concept = str(store.value(subject,
                                                   namespace["prefLabel"],
                                                   any=True))
                except KeyError:
                    log.warning("Keyword with subject %s has no prefLabel."
                                " We use raw name" %
                                self.short_id)
                    self.concept = self.short_id

            # this is common both to composite and simple keywords
            try:
                for label in store.objects(subject, namespace["altLabel"]):
                    basic_labels.append(str(label))
            except TypeError:
                pass

            # hidden labels are special (possibly regex) codes
            hidden_labels = []
            try:
                for label in store.objects(subject, namespace["hiddenLabel"]):
                    hidden_labels.append(unicode(label))
            except TypeError:
                pass

            # compile regular expression that will identify this token
            self.regex = _get_searchable_regex(basic_labels, hidden_labels)

            try:
                for note in map(lambda s: str(s).lower().strip(),
                                store.objects(subject, namespace["note"])):
                    if note == 'core':
                        self.core = True
                    elif note in ("nostandalone", "nonstandalone"):
                        self.nostandalone = True
                    elif 'fc:' in note:
                        self.fieldcodes.append(note[3:].strip())
            except TypeError:
                pass

            # spiresLabel does not have multiple values
            spires_label = store.value(subject, namespace["spiresLabel"])
            if spires_label:
                self.spires = str(spires_label)

        # important for comparisons
        self.__hash = hash(self.short_id)

        # extract composite parts ids
        if store is not None and self.isComposite():
            small_subject = self.id.split("#Composite.")[-1]
            component_positions = []
            for label in store.objects(self.id, namespace["compositeOf"]):
                strlabel = str(label).split("#")[-1]
                component_name = label.split("#")[-1]
                component_positions.append((small_subject.find(component_name),
                                            strlabel))
            component_positions.sort()
            if not component_positions:
                log.error("Keyword is marked as composite, "
                          "but no composite components refs found: %s"
                          % self.short_id)
            else:
                self.compositeof = map(lambda x: x[1], component_positions)

    def refreshCompositeOf(self, single_keywords, composite_keywords,
                           store=None, namespace=None):
        """Re-check sub-parts of this keyword.

        This should be called after the whole RDF was processed, because
        it is using a cache of single keywords and if that
        one is incomplete, you will not identify all parts.
        """
        def _get_ckw_components(new_vals, label):
            if label in single_keywords:
                new_vals.append(single_keywords[label])
            elif ('Composite.%s' % label) in composite_keywords:
                for l in composite_keywords['Composite.%s' % label].compositeof:
                    _get_ckw_components(new_vals, l)
            elif label in composite_keywords:
                for l in composite_keywords[label].compositeof:
                    _get_ckw_components(new_vals, l)
            else:
                # One single or composite keyword is missing from the taxonomy.
                # This is due to an error in the taxonomy description.
                message = "The composite term \"%s\""\
                          " should be made of single keywords,"\
                          " but at least one is missing." % self.id
                if store is not None:
                    message += "Needed components: %s"\
                               % list(store.objects(self.id,
                                      namespace["compositeOf"]))
                message += " Missing is: %s" % label
                raise TaxonomyError(message)

        if self.compositeof:
            new_vals = []
            try:
                for label in self.compositeof:
                    _get_ckw_components(new_vals, label)
                self.compositeof = new_vals
            except TaxonomyError as err:
                # the composites will be empty
                # (better than to have confusing, partial matches)
                self.compositeof = []
                log.error(err)

    def isComposite(self):
        """Return value of _composite."""
        return self._composite

    def getComponents(self):
        """Return value of compositeof."""
        return self.compositeof

    def getType(self):
        """Return value of type."""
        return self.type

    def setType(self, value):
        """Set value of value."""
        self.type = value

    def __hash__(self):
        """Return _hash.

        This might change in the future but for the moment we want to
        think that if the concept is the same, then it is the same
        keyword - this sucks, but it is sort of how it is necessary
        to use now.
        """
        return self.__hash

    def __cmp__(self, other):
        """Compare objects using _hash."""
        if self.__hash < other.__hash__():
            return -1
        elif self.__hash == other.__hash__():
            return 0
        else:
            return 1

    def __str__(self, spires=False):
        """Return the best output for the keyword."""
        if spires:
            if self.spires:
                return self.spires
            elif self._composite:
                return self.concept.replace(':', ',')
            # default action
        return self.concept

    def output(self, spires=False):
        """Return string representation with spires value."""
        return self.__str__(spires=spires)

    def __repr__(self):
        """Class representation."""
        return "<KeywordToken: %s>" % self.short_id


def _build_cache(source_file, skip_cache=False):
    """Build the cached data.

    Either by parsing the RDF taxonomy file or a vocabulary file.

    :param source_file: source file of the taxonomy, RDF file
    :param skip_cache: if True, build cache will not be
        saved (pickled) - it is saved as <source_file.db>
    """
    store = rdflib.ConjunctiveGraph()

    if skip_cache:
        log.info("You requested not to save the cache to disk.")
    else:
        cache_path = _get_cache_path(source_file)
        cache_dir = os.path.dirname(cache_path)
        # Make sure we have a cache_dir readable and writable.
        try:
            os.makedirs(cache_dir)
        except:
            pass
        if os.access(cache_dir, os.R_OK):
            if not os.access(cache_dir, os.W_OK):
                raise TaxonomyError("Cache directory exists but is not"
                                    " writable. Check your permissions"
                                    " for: %s" % cache_dir)
        else:
            raise TaxonomyError("Cache directory does not exist"
                                " (and could not be created): %s" % cache_dir)

    timer_start = time.clock()

    namespace = None
    single_keywords, composite_keywords = {}, {}

    try:
        log.info("Building RDFLib's conjunctive graph from: %s" % source_file)
        try:
            store.parse(source_file)
        except urllib2.URLError:
            if source_file[0] == '/':
                store.parse("file://" + source_file)
            else:
                store.parse("file:///" + source_file)

    except rdflib.exceptions.Error as e:
        log.error("Serious error reading RDF file")
        log.error(e)
        log.error(traceback.format_exc())
        raise rdflib.exceptions.Error(e)

    except (xml.sax.SAXParseException, ImportError) as e:
        # File is not a RDF file. We assume it is a controlled vocabulary.
        log.error(e)
        log.warning("The ontology file is probably not a valid RDF file. \
            Assuming it is a controlled vocabulary file.")

        filestream = open(source_file, "r")
        for line in filestream:
            keyword = line.strip()
            kt = KeywordToken(keyword)
            single_keywords[kt.short_id] = kt
        if not len(single_keywords):
            raise TaxonomyError('The ontology file is not well formated')

    else:  # ok, no exception happened
        log.info("Now building cache of keywords")
        # File is a RDF file.
        namespace = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")

        single_count = 0
        composite_count = 0

        subject_objects = store.subject_objects(namespace["prefLabel"])
        for subject, pref_label in subject_objects:
            kt = KeywordToken(subject, store=store, namespace=namespace)
            if kt.isComposite():
                composite_count += 1
                composite_keywords[kt.short_id] = kt
            else:
                single_keywords[kt.short_id] = kt
                single_count += 1

    cached_data = {}
    cached_data["single"] = single_keywords
    cached_data["composite"] = composite_keywords
    cached_data["creation_time"] = time.gmtime()
    cached_data["version_info"] = {'rdflib': rdflib.__version__,
                                   'bibclassify': bconfig.VERSION}
    log.debug("Building taxonomy... %d terms built in %.1f sec." %
              (len(single_keywords) + len(composite_keywords),
               time.clock() - timer_start))

    log.info("Total count of single keywords: %d "
             % len(single_keywords))
    log.info("Total count of composite keywords: %d "
             % len(composite_keywords))

    if not skip_cache:
        cache_path = _get_cache_path(source_file)
        cache_dir = os.path.dirname(cache_path)
        log.debug("Writing the cache into: %s" % cache_path)
        # test again, it could have changed
        if os.access(cache_dir, os.R_OK):
            if os.access(cache_dir, os.W_OK):
                # Serialize.
                filestream = None
                try:
                    filestream = open(cache_path, "wb")
                except IOError as msg:
                    # Impossible to write the cache.
                    log.error("Impossible to write cache to '%s'."
                              % cache_path)
                    log.error(msg)
                else:
                    log.debug("Writing cache to file %s" % cache_path)
                    cPickle.dump(cached_data, filestream, 1)
                if filestream:
                    filestream.close()

            else:
                raise TaxonomyError("Cache directory exists but is not "
                                    "writable. Check your permissions "
                                    "for: %s" % cache_dir)
        else:
            raise TaxonomyError("Cache directory does not exist"
                                " (and could not be created): %s" % cache_dir)

    # now when the whole taxonomy was parsed,
    # find sub-components of the composite kws
    # it is important to keep this call after the taxonomy was saved,
    # because we don't  want to pickle regexes multiple times
    # (as they are must be re-compiled at load time)
    for kt in composite_keywords.values():
        kt.refreshCompositeOf(single_keywords, composite_keywords,
                              store=store, namespace=namespace)

    # house-cleaning
    if store:
        store.close()

    return (single_keywords, composite_keywords)


def _capitalize_first_letter(word):
    """Return a regex pattern with the first letter.

    Accepts both lowercase and uppercase.
    """
    if word[0].isalpha():
        # These two cases are necessary in order to get a regex pattern
        # starting with '[xX]' and not '[Xx]'. This allows to check for
        # colliding regex afterwards.
        if word[0].isupper():
            return "[" + word[0].swapcase() + word[0] + "]" + word[1:]
        else:
            return "[" + word[0] + word[0].swapcase() + "]" + word[1:]
    return word


def _convert_punctuation(punctuation, conversion_table):
    """Return a regular expression for a punctuation string."""
    if punctuation in conversion_table:
        return conversion_table[punctuation]
    return re.escape(punctuation)


def _convert_word(word):
    """Return the plural form of the word if it exists.

    Otherwise return the word itself.
    """
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
    if word in bconfig.CFG_BIBCLASSIFY_INVARIABLE_WORDS:
        return _capitalize_first_letter(word)

    # Some exceptions that would not produce good results with the set of
    # general_regular_expressions.
    regexes = bconfig.CFG_BIBCLASSIFY_EXCEPTIONS
    if word in regexes:
        return _capitalize_first_letter(regexes[word])

    regexes = bconfig.CFG_BIBCLASSIFY_UNCHANGE_REGULAR_EXPRESSIONS
    for regex in regexes:
        if regex.search(word) is not None:
            return _capitalize_first_letter(word)

    regexes = bconfig.CFG_BIBCLASSIFY_GENERAL_REGULAR_EXPRESSIONS
    for regex, replacement in regexes:
        stemmed = regex.sub(replacement, word)
        if stemmed != word:
            return _capitalize_first_letter(stemmed)

    return _capitalize_first_letter(word + "s?")


def _get_cache(cache_file, source_file=None):
    """Get cached taxonomy using the cPickle module.

    No check is done at that stage.

    :param cache_file: full path to the file holding pickled data
    :param source_file: if we discover the cache is obsolete, we
        will build a new cache, therefore we need the source path
        of the cache
    :return: (single_keywords, composite_keywords).
    """
    timer_start = time.clock()

    filestream = open(cache_file, "rb")
    try:
        cached_data = cPickle.load(filestream)
        version_info = cached_data['version_info']
        if version_info['rdflib'] != rdflib.__version__\
                or version_info['bibclassify'] != bconfig.VERSION:
            raise KeyError
    except (cPickle.UnpicklingError, ImportError,
            AttributeError, DeprecationWarning, EOFError):
        log.warning("The existing cache in %s is not readable. "
                    "Removing and rebuilding it." % cache_file)
        filestream.close()
        os.remove(cache_file)
        return _build_cache(source_file)
    except KeyError:
        log.warning("The existing cache %s is not up-to-date. "
                    "Removing and rebuilding it." % cache_file)
        filestream.close()
        os.remove(cache_file)
        if source_file and os.path.exists(source_file):
            return _build_cache(source_file)
        else:
            log.error("The cache contains obsolete data (and it was deleted), "
                      "however I can't build a new cache, the source does not "
                      "exist or is inaccessible! - %s" % source_file)
    filestream.close()

    single_keywords = cached_data["single"]
    composite_keywords = cached_data["composite"]

    # the cache contains only keys of the composite keywords, not the objects
    # so now let's resolve them into objects
    for kw in composite_keywords.values():
        kw.refreshCompositeOf(single_keywords, composite_keywords)

    log.debug("Retrieved taxonomy from cache %s created on %s" %
              (cache_file, time.asctime(cached_data["creation_time"])))

    log.debug("%d terms read in %.1f sec." %
              (len(single_keywords) + len(composite_keywords),
               time.clock() - timer_start))

    return (single_keywords, composite_keywords)


def _get_cache_path(source_file):
    """Return the path where the cache should be written/located.

    :param onto_name: name of the ontology or the full path
    :return: string, abs path to the cache file in the tmpdir/bibclassify
    """
    local_name = os.path.basename(source_file)
    cache_name = local_name + ".db"
    cache_dir = os.path.join(config.CFG_CACHEDIR, "bibclassify")

    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    return os.path.abspath(os.path.join(cache_dir, cache_name))


def _get_last_modification_date(url):
    """Get the last modification date of the ontology."""
    request = urllib2.Request(url)
    request.get_method = lambda: "HEAD"
    http_file = urlopen(request)
    date_string = http_file.headers["last-modified"]
    parsed = time.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")
    return datetime(*(parsed)[0:6])


def _download_ontology(url, local_file):
    """Download the ontology and stores it in CFG_CACHEDIR."""
    log.debug("Copying remote ontology '%s' to file '%s'." % (url,
                                                              local_file))
    try:
        url_desc = urlopen(url)
        file_desc = open(local_file, 'w')
        file_desc.write(url_desc.read())
        file_desc.close()
    except IOError as e:
        print(e)
        return False
    except:
        log.warning("Unable to download the ontology. '%s'" %
                    sys.exc_info()[0])
        return False
    else:
        log.debug("Done copying.")
        return True


def _get_searchable_regex(basic=None, hidden=None):
    """Return the searchable regular expressions for the single keyword."""
    # Hidden labels are used to store regular expressions.
    basic = basic or []
    hidden = hidden or []

    hidden_regex_dict = {}
    for hidden_label in hidden:
        if _is_regex(hidden_label):
            hidden_regex_dict[hidden_label] = \
                re.compile(
                    bconfig.CFG_BIBCLASSIFY_WORD_WRAP % hidden_label[1:-1]
                )
        else:
            pattern = _get_regex_pattern(hidden_label)
            hidden_regex_dict[hidden_label] = re.compile(
                bconfig.CFG_BIBCLASSIFY_WORD_WRAP % pattern
            )

    # We check if the basic label (preferred or alternative) is matched
    # by a hidden label regex. If yes, discard it.
    regex_dict = {}
    # Create regex for plural forms and add them to the hidden labels.
    for label in basic:
        pattern = _get_regex_pattern(label)
        regex_dict[label] = re.compile(
            bconfig.CFG_BIBCLASSIFY_WORD_WRAP % pattern
        )

    # Merge both dictionaries.
    regex_dict.update(hidden_regex_dict)

    return regex_dict.values()


def _get_regex_pattern(label):
    """Return a regular expression of the label.

    This takes care of plural and different kinds of separators.
    """
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
                parts[index] = _convert_punctuation(
                    parts[index],
                    bconfig.CFG_BIBCLASSIFY_SYMBOLS
                )
            else:
                parts[index] = _convert_punctuation(
                    parts[index],
                    bconfig.CFG_BIBCLASSIFY_SEPARATORS
                )

    return "".join(parts)


def _is_regex(string):
    """Check if a concept is a regular expression."""
    return string[0] == "/" and string[-1] == "/"


def check_taxonomy(taxonomy):
    """Check the consistency of the taxonomy.

    Outputs a list of errors and warnings.
    """
    log.info("Building graph with Python RDFLib version %s" %
             rdflib.__version__)

    store = rdflib.ConjunctiveGraph()

    try:
        store.parse(taxonomy)
    except:
        log.error("The taxonomy is not a valid RDF file. Are you "
                  "trying to check a controlled vocabulary?")
        raise TaxonomyError('Error in RDF file')

    log.info("Graph was successfully built.")

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

    log.info("Taxonomy contains %s concepts." % len(subjects))

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

    for subject, predicates in iteritems(subjects):
        # No prefLabel or multiple prefLabels
        try:
            if len(predicates[prefLabel]) > 1:
                multiple_prefLabels.append(subject)
        except KeyError:
            no_prefLabel.append(subject)

        # Lonely and both composites.
        if composite not in predicates and compositeOf not in predicates:
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
                        if subject not in subjects[ckw][compositeOf]:
                            composite_problem3.append((subject, ckw))
                    else:
                        if ckw not in both_skw_and_ckw:
                            composite_problem2.append((subject, ckw))
                else:
                    composite_problem1.append((subject, ckw))

        # Check compositeOf
        if compositeOf in predicates:
            for skw in predicates[compositeOf]:
                if skw in subjects:
                    if composite in subjects[skw]:
                        if subject not in subjects[skw][composite]:
                            composite_problem6.append((subject, skw))
                    else:
                        if skw not in both_skw_and_ckw:
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
                interconcept_collisions.setdefault(pattern, []).\
                    append((subject, label))
                if pattern in patterns:
                    stemming_collisions.append(
                        (subject,
                         patterns[pattern],
                         (label, expression)
                         )
                    )
                else:
                    patterns[pattern] = (label, expression)

    print("\n==== ERRORS ====")

    if no_prefLabel:
        print("\nConcepts with no prefLabel: %d" % len(no_prefLabel))
        print("\n".join(["   %s" % subj for subj in no_prefLabel]))
    if multiple_prefLabels:
        print(("\nConcepts with multiple prefLabels: %d" %
               len(multiple_prefLabels)))
        print("\n".join(["   %s" % subj for subj in multiple_prefLabels]))
    if both_composites:
        print(("\nConcepts with both composite properties: %d" %
               len(both_composites)))
        print("\n".join(["   %s" % subj for subj in both_composites]))
    if bad_hidden_labels:
        print("\nConcepts with bad hidden labels: %d" % len(bad_hidden_labels))
        for kw, lbls in iteritems(bad_hidden_labels):
            print("   %s:" % kw)
            print("\n".join(["      '%s'" % lbl for lbl in lbls]))
    if bad_alt_labels:
        print("\nConcepts with bad alt labels: %d" % len(bad_alt_labels))
        for kw, lbls in iteritems(bad_alt_labels):
            print("   %s:" % kw)
            print("\n".join(["      '%s'" % lbl for lbl in lbls]))
    if both_skw_and_ckw:
        print(("\nKeywords that are both skw and ckw: %d" %
               len(both_skw_and_ckw)))
        print("\n".join(["   %s" % subj for subj in both_skw_and_ckw]))

    print()

    if composite_problem1:
        print("\n".join(["SKW '%s' references an unexisting CKW '%s'." %
                         (skw, ckw) for skw, ckw in composite_problem1]))
    if composite_problem2:
        print("\n".join(["SKW '%s' references a SKW '%s'." %
                         (skw, ckw) for skw, ckw in composite_problem2]))
    if composite_problem3:
        print("\n".join(["SKW '%s' is not composite of CKW '%s'." %
                         (skw, ckw) for skw, ckw in composite_problem3]))
    if composite_problem4:
        for skw, ckws in iteritems(composite_problem4):
            print("SKW '%s' does not exist but is " "referenced by:" % skw)
            print("\n".join(["    %s" % ckw for ckw in ckws]))
    if composite_problem5:
        print("\n".join(["CKW '%s' references a CKW '%s'." % kw
                         for kw in composite_problem5]))
    if composite_problem6:
        print("\n".join(["CKW '%s' is not composed by SKW '%s'." % kw
                         for kw in composite_problem6]))

    print("\n==== WARNINGS ====")

    if bad_notes:
        print(("\nConcepts with bad notes: %d" % len(bad_notes)))
        print("\n".join(["   '%s': '%s'" % _note for _note in bad_notes]))
    if stemming_collisions:
        print("\nFollowing keywords have unnecessary labels that have "
              "already been generated by BibClassify.")
        for subj in stemming_collisions:
            print("   %s:\n     %s\n     and %s" % subj)

    print("\nFinished.")
    sys.exit(0)


def test_cache(taxonomy_name='HEP', rebuild_cache=False, no_cache=False):
    """Test the cache lookup."""
    cache = get_cache(taxonomy_name)
    if not cache:
        set_cache(taxonomy_name, get_regular_expressions(taxonomy_name,
                                                         rebuild=rebuild_cache,
                                                         no_cache=no_cache))
        cache = get_cache(taxonomy_name)
    return (thread.get_ident(), cache)


log.info('Loaded ontology reader')

if __name__ == '__main__':
    test_cache()
