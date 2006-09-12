# -*- coding: utf-8 -*-
## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""External collection 'core' file.
    Perform search, database access."""

__revision__ = "$Id$"

from copy import copy
from sets import Set

from invenio.config import cdslang
from invenio.dbquery import run_sql 
from invenio.messages import gettext_set_language

from invenio.websearch_external_collections_config import cfg_external_collection_timeout
from invenio.websearch_external_collections_searcher import external_collections_dictionary
from invenio.websearch_external_collections_page_getter import HTTPAsyncPageGetter, async_download
from invenio.websearch_external_collections_templates import print_results, print_timeout
from invenio.websearch_external_collections_utils import get_collection_id, get_collection_descendants, escape_dictionary, \
    warning, get_verbose_print

import invenio.template
template = invenio.template.load('websearch_external_collections')

#dico_collection_external_searches = {}
#dico_collection_seealso = {}

def print_external_results_overview(req, current_collection, pattern_list, field,
        external_collection, verbosity_level=0, lang=cdslang):
    """Print the external collection overview box. Return the selected external collections and parsed query"""
    from invenio.search_engine import create_basic_search_units
    assert req
    vprint = get_verbose_print(req, 'External collection (print_external_results_overview): ', verbosity_level)

    pattern = bind_patterns(pattern_list)
    vprint(3, 'pattern = ' + pattern)

    if not pattern:
        return (None, None, None, None)

    basic_search_units = create_basic_search_units(None, pattern, field)
    vprint(3, 'basic_search_units = ' + str(basic_search_units))

    (search_engines, seealso_engines) = select_external_engines(current_collection, external_collection)
    vprint(3, 'search_engines = ' + str(search_engines))
    vprint(3, 'seealso_engines = ' + str(seealso_engines))

    search_engines_list = external_collection_sort_engine_by_name(search_engines)
    vprint(3, 'search_engines_list (sorted) : ' + str(search_engines_list))
    html = template.external_collection_overview(lang, search_engines_list)
    req.write(html)

    return (search_engines, seealso_engines, pattern, basic_search_units)

def perform_external_collection_search(req, current_collection, pattern_list, field, 
        external_collection, verbosity_level=0, lang=cdslang, selected_external_collections=None):
    """Search external collection and print the seealso box."""
    
    vprint = get_verbose_print(req, 'External collection: ', verbosity_level)

    if selected_external_collections:
        (search_engines, seealso_engines, pattern, basic_search_units) = selected_external_collections
    else:
        (search_engines, seealso_engines, pattern, basic_search_units) = print_external_results_overview(req, 
            current_collection, pattern_list, field, external_collection, verbosity_level, lang)

    if not pattern:
        return

    do_external_search(req, lang, vprint, basic_search_units, search_engines)
    create_seealso_box(req, lang, vprint, basic_search_units, seealso_engines, pattern)
    vprint(3, 'end')

def bind_patterns(pattern_list):
    """Combine a list of patterns in an unique pattern.
    pattern_list[0] should be the standart search pattern,
    pattern_list[1:] are advanced search patterns."""
    if pattern_list[0]:
        return pattern_list[0]

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
    links = build_seealso_links(basic_search_units, seealso_engines_list, lang, query)
    html = template.external_collection_seealso_box(lang, links)
    req.write(html)

def build_seealso_links(basic_search_units, seealso_engines, lang, query):
    """Build the links for the see also box."""
    _ = gettext_set_language(lang)

    links = []
    for engine in seealso_engines:
        url = engine.build_search_url(basic_search_units, lang)
        if url:
            links.append('<a href="%(url)s">%(query)s %(text_in)s %(name)s</a>' % \
                {'query': query, 'text_in': _('in'), 'name': _(engine.name), 'url': url})
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

    seealso_engines = Set()
    search_engines = Set()

    if dico_collection_seealso.has_key(collection_id):
        seealso_engines = copy(dico_collection_seealso[collection_id])

    if dico_collection_external_searches.has_key(collection_id):
        seealso_engines = seealso_engines.union(dico_collection_external_searches[collection_id])

    for ext_search_name in selected_external_searches:
        if external_collections_dictionary.has_key(ext_search_name):
            engine = external_collections_dictionary[ext_search_name]
            if engine.parser:
                search_engines.add(engine)
        else:
            warning('select_external_engines: %(ext_search_name)s unknown.' % locals())

    seealso_engines = seealso_engines.difference(search_engines)

    return (search_engines, seealso_engines)

# Search
def do_external_search(req, lang, vprint, basic_search_units, search_engines):
    """Make the external search."""
    _ = gettext_set_language(lang)
    vprint(3, 'beginning external search')
    engines_list = []

    for engine in search_engines:
        url = engine.build_search_url(basic_search_units, lang)
        if url:
            engines_list.append([url, engine])

    pagegetters_list = [HTTPAsyncPageGetter(engine[0]) for engine in engines_list]

    def finished(pagegetter, data, current_time):
        """Function called, each time the download of a web page finish.
        Will parse and print the results of this page."""
        print_results(req, lang, pagegetter, data, current_time)    

    finished_list = async_download(pagegetters_list, finished, engines_list, cfg_external_collection_timeout)

    for (finished, engine) in zip(finished_list, engines_list):
        if not finished:
            url = engine[0]
            name = engine[1].name
            print_timeout(req, lang, engine[1], name, url)

# Database management
def external_collection_load_states():
    global external_collections_state, dico_collection_external_searches, dico_collection_seealso

    external_collections_state = {}
    dico_collection_external_searches = {}
    dico_collection_seealso = {}

    query = "SELECT collection_externalcollection.id_collection, collection_externalcollection.type, externalcollection.name FROM collection_externalcollection, externalcollection WHERE collection_externalcollection.id_externalcollection = externalcollection.id;"
    results = run_sql(query)
    if results:
        for result in results:
            collection_id = int(result[0])
            search_type = int(result[1])
            engine_name = result[2]

            if not external_collections_dictionary.has_key(engine_name):
                warning("No search engine : " + engine_name)
                continue

            engine = external_collections_dictionary[engine_name]

            if not external_collections_state.has_key(collection_id):
                external_collections_state[collection_id] = {}
            col_states = external_collections_state[collection_id]

            col_states[engine] = search_type

            dictionary = None

            if search_type == 1:
                dictionary = dico_collection_seealso

            if search_type in [2, 3]:
                dictionary = dico_collection_external_searches

            if dictionary == None:
                continue

            if not dictionary.has_key(collection_id):
                dictionary[collection_id] = Set()
            engine_set = dictionary[collection_id]
            engine_set.add(engine)

def external_collection_init():
    """Load db infos if it's not already done."""
    if not external_collection_init.done:
        external_collection_load_states()
        external_collection_init.done = True
external_collection_init.done = False

def external_collection_get_state(external_collection, collection_id):
    external_collection_load_states()
    if not external_collections_state.has_key(collection_id):
        return 0
    col_states = external_collections_state[collection_id]
    if not col_states.has_key(external_collection):
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
    engines_list = [engine for engine in engines_set]
    engines_list.sort(lambda x, y: cmp(x.name, y.name))
    return engines_list

# External search ID
def external_collection_getid(external_collection):
    """Return the id of an external_collection. Will create a new entry in DB if needed."""

    if external_collection.__dict__.has_key('id'):
        return external_collection.id

    query = 'SELECT id FROM externalcollection WHERE name="%(name)s";' % {'name': external_collection.name}
    results = run_sql(query)
    if not results:
        query = 'INSERT INTO externalcollection (name) VALUES ("%(name)s");' % {'name': external_collection.name}
        run_sql(query)
        return external_collection_getid(external_collection)
    
    external_collection.id = results[0][0]
    return external_collection.id

external_collection_init()

