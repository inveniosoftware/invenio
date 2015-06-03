# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2015 CERN.
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

"""External collection 'core' file.
    Perform search, database access."""

__revision__ = "$Id$"

import warnings

from invenio.utils.deprecation import RemovedInInvenio22Warning

warnings.warn("External collection search will be removed in 2.2. Please check "
              "new Record REST API.",
              RemovedInInvenio22Warning)

import cgi
import sys
from copy import copy

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.config import CFG_SITE_LANG
from invenio.legacy.dbquery import run_sql
from invenio.base.i18n import gettext_set_language

from .config import CFG_EXTERNAL_COLLECTION_TIMEOUT
from .searcher import external_collections_dictionary
from .getter import HTTPAsyncPageGetter, async_download
from .templates import print_results, print_timeout
from .utils import get_collection_id, get_collection_descendants, \
    warning, get_verbose_print

import invenio.legacy.template

from sqlalchemy.exc import OperationalError, ProgrammingError

# Global variables
template = invenio.legacy.template.load('websearch_external_collections')
external_collections_state = None
dico_collection_external_searches = None
dico_collection_seealso = None

#dico_collection_external_searches = {}
#dico_collection_seealso = {}

def print_external_results_overview(req, current_collection, pattern_list, field,
        external_collection, verbosity_level=0, lang=CFG_SITE_LANG, print_overview=True):
    """Print the external collection overview box. Return the selected external collections and parsed query"""
    from invenio.legacy.search_engine import create_basic_search_units
    assert req
    vprint = get_verbose_print(req, 'External collection (print_external_results_overview): ', verbosity_level)

    pattern = bind_patterns(pattern_list)
    vprint(3, 'pattern = %s' % cgi.escape(pattern))

    if not pattern:
        return (None, None, None, None)

    basic_search_units = create_basic_search_units(None, pattern, field)
    vprint(3, 'basic_search_units = %s' % cgi.escape(repr(basic_search_units)))

    (search_engines, seealso_engines) = select_external_engines(current_collection, external_collection)
    vprint(3, 'search_engines = ' + str(search_engines))
    vprint(3, 'seealso_engines = ' + str(seealso_engines))

    search_engines_list = external_collection_sort_engine_by_name(search_engines)
    vprint(3, 'search_engines_list (sorted) : ' + str(search_engines_list))
    if print_overview:
        html = template.external_collection_overview(lang, search_engines_list)
        req.write(html)

    return (search_engines, seealso_engines, pattern, basic_search_units)

def perform_external_collection_search(req, current_collection, pattern_list, field,
        external_collection, verbosity_level=0, lang=CFG_SITE_LANG,
        selected_external_collections_infos=None, print_overview=True,
        print_search_info=True, print_see_also_box=True, print_body=True):
    """Search external collection and print the seealso box."""

    vprint = get_verbose_print(req, 'External collection: ', verbosity_level)

    if selected_external_collections_infos:
        (search_engines, seealso_engines, pattern, basic_search_units) = selected_external_collections_infos
    else:
        (search_engines, seealso_engines, pattern, basic_search_units) = print_external_results_overview(req,
            current_collection, pattern_list, field, external_collection, verbosity_level, lang, print_overview=print_overview)

    if not pattern:
        return

    do_external_search(req, lang, vprint, basic_search_units, search_engines, print_search_info, print_body)
    if print_see_also_box:
        create_seealso_box(req, lang, vprint, basic_search_units, seealso_engines, pattern)
    vprint(3, 'end')

def bind_patterns(pattern_list):
    """Combine a list of patterns in an unique pattern.
    pattern_list[0] should be the standart search pattern,
    pattern_list[1:] are advanced search patterns."""

    # just in case an empty list is fed to this function
    try:
        if pattern_list[0]:
            return pattern_list[0]
    except IndexError:
        return None

    pattern = ""
    for pattern_part in pattern_list[1:]:
        if pattern_part:
            pattern += " " + pattern_part

    return pattern.strip()

# See also box
def create_seealso_box(req, lang, vprint, basic_search_units=None, seealso_engines=None, query=''):
    "Create the box that proposes links to other useful search engines like Google."
    vprint(3, 'Create seealso box')
    seealso_engines_list = external_collection_sort_engine_by_name(seealso_engines)
    vprint(3, 'seealso_engines_list = ' + str(seealso_engines_list))
    links = build_seealso_links(basic_search_units, seealso_engines_list, req, lang, query)
    html = template.external_collection_seealso_box(lang, links)
    req.write(html)

def build_seealso_links(basic_search_units, seealso_engines, req, lang, query):
    """Build the links for the see also box."""
    _ = gettext_set_language(lang)

    links = []
    for engine in seealso_engines:
        url = engine.build_search_url(basic_search_units, req.args, lang)
        user_url = engine.build_user_search_url(basic_search_units, req.args, lang)
        url = user_url or url
        if url:
            links.append('<a class="google" href="%(url)s">%(query)s %(text_in)s %(name)s</a>' % \
                {'url': cgi.escape(url),
                 'query': cgi.escape(query),
                 'text_in': _('in'),
                 'name': _(engine.name)})
    return links

# Selection
def select_external_engines(collection_name, selected_external_searches):
    """Build a tuple of two sets. The first one is the list of engine to use for an external search and the
    second one is for the seealso box."""

    collection_id = get_collection_id(collection_name)
    if not collection_id:
        return (None, None)

    if not type(selected_external_searches) is list:
        selected_external_searches = [selected_external_searches]

    seealso_engines = set()
    search_engines = set()

    if collection_id in dico_collection_seealso:
        seealso_engines = copy(dico_collection_seealso[collection_id])

    if collection_id in dico_collection_external_searches:
        seealso_engines = seealso_engines.union(dico_collection_external_searches[collection_id])

    for ext_search_name in selected_external_searches:
        if ext_search_name in external_collections_dictionary:
            engine = external_collections_dictionary[ext_search_name]
            if engine.parser:
                search_engines.add(engine)
        else:
            warning('select_external_engines: %(ext_search_name)s unknown.' % locals())

    seealso_engines = seealso_engines.difference(search_engines)

    return (search_engines, seealso_engines)

# Search
def do_external_search(req, lang, vprint, basic_search_units, search_engines, print_search_info=True, print_body=True):
    """Make the external search."""
    _ = gettext_set_language(lang)
    vprint(3, 'beginning external search')
    engines_list = []

    for engine in search_engines:
        url = engine.build_search_url(basic_search_units, req.args, lang)
        user_url = engine.build_user_search_url(basic_search_units, req.args, lang)
        if url:
            engines_list.append([url, engine, user_url])

    pagegetters_list = [HTTPAsyncPageGetter(engine[0]) for engine in engines_list]

    def finished(pagegetter, data, current_time, print_search_info=True, print_body=True):
        """Function called, each time the download of a web page finish.
        Will parse and print the results of this page."""
        print_results(req, lang, pagegetter, data, current_time, print_search_info, print_body)

    finished_list = async_download(pagegetters_list, finished, engines_list, CFG_EXTERNAL_COLLECTION_TIMEOUT, print_search_info, print_body)

    for (finished, engine) in zip(finished_list, engines_list):
        if not finished:
            url = engine[2] or engine[0]
            name = engine[1].name
            print_timeout(req, lang, engine[1], name, url)

# Database management
def external_collection_load_states():
    global external_collections_state, dico_collection_external_searches, dico_collection_seealso

    external_collections_state = {}
    dico_collection_external_searches = {}
    dico_collection_seealso = {}

    query = "SELECT collection_externalcollection.id_collection, collection_externalcollection.type, externalcollection.name FROM collection_externalcollection, externalcollection WHERE collection_externalcollection.id_externalcollection = externalcollection.id;"
    try:
        results = run_sql(query)
    except (OperationalError, ProgrammingError):
        results = None
    if results:
        for result in results:
            collection_id = int(result[0])
            search_type = int(result[1])
            engine_name = result[2]

            if engine_name not in external_collections_dictionary:
                warning("No search engine : " + engine_name)
                continue

            engine = external_collections_dictionary[engine_name]

            if collection_id not in external_collections_state:
                external_collections_state[collection_id] = {}
            col_states = external_collections_state[collection_id]

            col_states[engine] = search_type

            dictionary = None

            if search_type == 1:
                dictionary = dico_collection_seealso

            if search_type in [2, 3]:
                dictionary = dico_collection_external_searches

            if dictionary is None:
                continue

            if collection_id not in dictionary:
                dictionary[collection_id] = set()
            engine_set = dictionary[collection_id]
            engine_set.add(engine)

def external_collection_get_state(external_collection, collection_id):
    external_collection_load_states()
    if collection_id not in external_collections_state:
        return 0
    col_states = external_collections_state[collection_id]
    if external_collection not in col_states:
        return 0
    return col_states[external_collection]

def external_collection_get_update_state_list(external_collection, collection_id, state, recurse=False):
    changes = []

    if external_collection_get_state(external_collection, collection_id) != state:
        changes = ['(%(collection_id)d, %(id_externalcollection)d, %(state)d)' %
            {'collection_id': collection_id, 'id_externalcollection': external_collection_getid(external_collection), 'state': state}]

    if not recurse:
        return changes

    for descendant_id in get_collection_descendants(collection_id):
        changes += external_collection_get_update_state_list(external_collection, descendant_id, state)

    return changes

def external_collection_apply_changes(changes_list):
    if not changes_list:
        return

    sql_values = ", ".join(changes_list)
    sql = 'INSERT INTO collection_externalcollection (id_collection, id_externalcollection, type) VALUES ' + sql_values + 'ON DUPLICATE KEY UPDATE type=VALUES(type);'
    run_sql(sql)

# Misc functions
def external_collection_sort_engine_by_name(engines_set):
    """Return a list of sorted (by name) search engines."""
    if not engines_set:
        return []
    engines_list = [engine for engine in engines_set]
    engines_list.sort(lambda x, y: cmp(x.name, y.name))
    return engines_list

# External search ID
def external_collection_getid(external_collection):
    """Return the id of an external_collection. Will create a new entry in DB if needed."""

    if 'id' in external_collection.__dict__:
        return external_collection.id

    query = "SELECT id FROM externalcollection WHERE name='%(name)s';" % {'name': external_collection.name}
    results = run_sql(query)
    if not results:
        query = "INSERT INTO externalcollection (name) VALUES ('%(name)s');" % {'name': external_collection.name}
        run_sql(query)
        return external_collection_getid(external_collection)

    external_collection.id = results[0][0]
    return external_collection.id

def get_external_collection_engine(external_collection_name):
    """Return the external collection engine given its name"""

    if external_collection_name in external_collections_dictionary:
        return external_collections_dictionary[external_collection_name]
    else:
        return None

# Load db infos if it's not already done.
if external_collections_state is None:
    external_collection_load_states()

# Hosted Collections related functions (the following functions should eventually be regrouped as above)
# These functions could eventually be placed into there own file, ex. websearch_hosted_collections.py
def calculate_hosted_collections_results(req, pattern_list, field, hosted_collections, verbosity_level=0,
                                         lang=CFG_SITE_LANG, timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT):
    """Ruturn a list of the various results for a every hosted collection organized in tuples"""

    # normally, the following should be checked before even running this function so the following line could be removed
    if not hosted_collections: return (None, None)

    vprint = get_verbose_print(req, 'Hosted collections: ', verbosity_level)
    vprint(3, 'pattern_list = %s, field = %s' % (cgi.escape(repr(pattern_list)), cgi.escape(field)))

    # firstly we calculate the search parameters, i.e. the actual hosted search engines and the basic search units
    (hosted_search_engines, basic_search_units) = \
    calculate_hosted_collections_search_params(req,
                                               pattern_list,
                                               field,
                                               hosted_collections,
                                               verbosity_level)

    # in case something went wrong with the above calculation just return None
    # however, once we run this function no fail should be expected here
    # UPDATE : let search go on even there are no basic search units (an empty pattern_list and field)
    #if basic_search_units == None or len(hosted_search_engines) == 0: return (None, None)
    if len(hosted_search_engines) == 0: return (None, None)

    # finally return the list of tuples with the results
    return do_calculate_hosted_collections_results(req, lang, vprint, verbosity_level, basic_search_units, hosted_search_engines, timeout)

    vprint(3, 'end')

def calculate_hosted_collections_search_params(req,
                                               pattern_list,
                                               field,
                                               hosted_collections,
                                               verbosity_level=0):
    """Calculate the searching parameters for the selected hosted collections
    i.e. the actual hosted search engines and the basic search units"""

    from invenio.legacy.search_engine import create_basic_search_units
    assert req
    vprint = get_verbose_print(req, 'Hosted collections (calculate_hosted_collections_search_params): ', verbosity_level)

    pattern = bind_patterns(pattern_list)
    vprint(3, 'pattern = %s' % cgi.escape(pattern))

    # if for any strange reason there is no pattern, just return
    # UPDATE : let search go on even there is no pattern (an empty pattern_list and field)
    #if not pattern: return (None, None)

    # calculate the basic search units
    basic_search_units = create_basic_search_units(None, pattern, field)
    vprint(3, 'basic_search_units = %s' % cgi.escape(repr(basic_search_units)))

    # calculate the set of hosted search engines
    hosted_search_engines = select_hosted_search_engines(hosted_collections)
    vprint(3, 'hosted_search_engines = ' + str(hosted_search_engines))

    # no need really to print out a sorted list of the hosted search engines, is there? I'll leave this commented out
    #hosted_search_engines_list = external_collection_sort_engine_by_name(hosted_search_engines)
    #vprint(3, 'hosted_search_engines_list (sorted) : ' + str(hosted_search_engines_list))

    return (hosted_search_engines, basic_search_units)

def select_hosted_search_engines(selected_hosted_collections):
    """Build the set of engines to be used for the hosted collections"""

    if not type(selected_hosted_collections) is list:
        selected_hosted_collections = [selected_hosted_collections]

    hosted_search_engines = set()

    for hosted_collection_name in selected_hosted_collections:
        if hosted_collection_name in external_collections_dictionary:
            engine = external_collections_dictionary[hosted_collection_name]
            # the hosted collection cannot present its results unless it has a parser implemented
            if engine.parser:
                hosted_search_engines.add(engine)
        else:
            warning('select_hosted_search_engines: %(hosted_collection_name)s unknown.' % locals())

    return hosted_search_engines

def do_calculate_hosted_collections_results(req, lang, vprint, verbosity_level, basic_search_units, hosted_search_engines,
                                            timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT):
    """Actually search the hosted collections and return their results and information in a list of tuples.
    One tuple for each hosted collection. Handles timeouts"""

    _ = gettext_set_language(lang)
    if not vprint:
        vprint = get_verbose_print(req, 'Hosted collections (calculate_hosted_collections_search_params): ', verbosity_level)
        # defining vprint at this moment probably means we'll just run this one function at this time, therefore the "verbose"
        # end hosted search string will not be printed (it is normally printed by the initial calculate function)
        # Therefore, either define a flag here to print it by the end of this function or redefine the whole "verbose"
        # printing logic of the above functions
    vprint(3, 'beginning hosted search')

    # list to hold the hosted search engines and their respective search urls
    engines_list = []
    # list to hold the non timed out results
    results_list = []
    # list to hold all the results
    full_results_list = []
    # list to hold all the timeouts
    timeout_list = []

    # in case this is an engine-only list
    if type(hosted_search_engines) is set:
        for engine in hosted_search_engines:
            url = engine.build_search_url(basic_search_units, req.args, lang)
            user_url = engine.build_user_search_url(basic_search_units, req.args, lang)
            if url:
                engines_list.append([url, engine, user_url])
    # in case we are iterating a pre calculated url+engine list
    elif type(hosted_search_engines) is list:
        for engine in hosted_search_engines:
            engines_list.append(engine)
    # in both the above cases we end up with a [[search url], [engine]] kind of list

    # create the list of search urls to be handed to the asynchronous getter
    pagegetters_list = [HTTPAsyncPageGetter(engine[0]) for engine in engines_list]

    # function to be run on every result
    def finished(pagegetter, data, current_time):
        """Function called, each time the download of a web page finish.
        Will parse and print the results of this page."""
        # each pagegetter that didn't timeout is added to this list
        results_list.append((pagegetter, data, current_time))

    # run the asynchronous getter
    finished_list = async_download(pagegetters_list, finished, engines_list, timeout)

    # create the complete list of tuples, one for each hosted collection, with the results and other information,
    # including those that timed out
    for (finished, engine) in zip(finished_list, engines_list): #finished_and_engines_list:
        if finished:
            for result in results_list:
                if result[1] == engine:
                    # the engine is fed the results, it will be parsed later, at printing time
                    engine[1].parser.parse_and_get_results(result[0].data, feedonly=True)
                    ## the list contains:
                    ## * the engine itself: [ search url], [engine]
                    ## * the parsed number of found results
                    ## * the fetching time
                    full_results_list.append(
                        (engine, engine[1].parser.parse_num_results(), result[2])
                    )
                    break
        elif not finished:
            ## the list contains:
            ## * the engine itself: [search url], [engine]
            timeout_list.append(engine)

    return (full_results_list, timeout_list)
