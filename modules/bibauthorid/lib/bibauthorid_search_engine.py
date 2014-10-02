# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

""" Approximate search engine for authors. """

from invenio.bibauthorid_config import QGRAM_LEN, MATCHING_QGRAMS_PERCENTAGE, \
    MAX_T_OCCURANCE_RESULT_LIST_CARDINALITY, MIN_T_OCCURANCE_RESULT_LIST_CARDINALITY

from multiprocessing import Queue, Process, Pool
import re
# from threading import Thread
from operator import itemgetter
from itertools import groupby, chain
from msgpack import packb as serialize
from msgpack import unpackb as deserialize

from invenio.textutils import translate_to_ascii
from invenio.intbitset import intbitset
from invenio.bibauthorid_name_utils import create_indexable_name, split_name_parts
from invenio.bibauthorid_dbinterface import get_confirmed_name_to_authors_mapping, \
    get_author_to_name_and_occurrence_mapping, \
    populate_table, set_inverted_lists_ready, \
    set_dense_index_ready, search_engine_is_operating, \
    get_indexed_strings, get_author_groups_from_string_ids, \
    get_name_variants_for_authors, get_inverted_lists

from invenio.bibauthorid_general_utils import memoized

indexable_name_re = re.compile("[^a-zA-Z,\s]")

# Memoize some functions
translate_to_ascii = memoized(translate_to_ascii)
split_name_parts = memoized(split_name_parts)


def get_qgrams_from_string(s, q):
    '''
    It decomposes the given string to its qgrams. The qgrams of a string are
    its substrings of length q. For example the 2-grams (q=2) of the string
    'cathey' are (ca,at,th,he,ey).

    @param string: string to be decomposed
    @type string: str
    @param q: length of the grams
    @type q: int

    @return: the string qgrams ordered accordingly to the position they withhold in the string
    @rtype: list [str,]
    '''
    return [s[x:x + q] for x in range(0, len(s) - q + 1)]


#
#
# Indexing            ###
#
#


def create_bibauthorid_indexer():
    '''
    It constructs the disk-based indexer. It consists of the dense index which
    maps a name to the set of authors who withhold that name and the inverted
    lists which map a qgram to the set of name ids that share that qgram.
    '''

    names_to_authors_mapping = get_confirmed_name_to_authors_mapping()
    indexable_names_to_authors_mapping = index_author_names(names_to_authors_mapping)

    if not indexable_names_to_authors_mapping:
        return

    author_to_name_and_occurrence_mapping = get_author_to_name_and_occurrence_mapping()

    # Convenient for assigning the same identifier
    # to each indexable name in different threads.
    indexable_names = indexable_names_to_authors_mapping.keys()

    # If an exception/error occurs in any of the threads it is
    # not detectable, hence inter-thread communication is used.
    queue = Queue()

    dense_index = Process(target=create_dense_index, args=(indexable_names_to_authors_mapping, indexable_names, queue))
    inverted_list = Process(target=create_inverted_lists, args=(indexable_names, queue))

    print 'index'
    dense_index.start()
    print 'done'
    print 'inverted'
    inverted_list.start()
    print 'done'

    dense_index.join()
    inverted_list.join()

    for _ in range(2):
        all_ok, error = queue.get(block=True)
        if not all_ok:
            raise error

    cache_name_variants_of_authors(author_to_name_and_occurrence_mapping)
    set_dense_index_ready()


def _split_and_index(el):
    name, pids = el
    asciified_name = translate_to_ascii(name)[0]
    split_name = split_name_parts(indexable_name_re.sub(' ', asciified_name))
    indexable_name = create_indexable_name(split_name)
    surname = split_name[0] + ','
    indexable_surname = create_indexable_name([surname, [], [], []])
    return (name, pids, indexable_name, indexable_surname)


def index_author_names(names_to_authors_mapping):
    '''
    It makes a mapping which associates an indexable name to the authors who
    carry that name.

    @param indexable_names_to_authors_mapping: mapping between indexable names
        and authors who carry that name
    @type indexable_names_to_authors_mapping: dict {str: set(int,)}
    @param names_to_authors_mapping: mappping between names and authors who carry that name
    @type names_to_authors_mapping: dict {str: set(int,)}
    '''
    indexable_names_to_authors_mapping = dict()
    values = map(_split_and_index, list(names_to_authors_mapping.iteritems()))

    for name, pids, indexable_name, indexable_surname in values:

        if indexable_name:
            try:
                indexable_names_to_authors_mapping[indexable_name][0] |= pids
            except KeyError:
                indexable_names_to_authors_mapping[indexable_name] = [pids, indexable_surname]

        if indexable_surname:
            try:
                indexable_names_to_authors_mapping[indexable_surname][0] |= pids
            except KeyError:
                indexable_names_to_authors_mapping[indexable_surname] = [pids, '']

    return indexable_names_to_authors_mapping


def create_inverted_lists(indexable_names, queue):
    '''
    It saves in the disk the inverted lists which map a qgram to the set of
    name ids that share that qgram. It does so by decomposing each name into
    its qgrams and adds its id to the corresponding inverted list.

    @param indexable_names: indexable names
    @type indexable_names: list
    @param queue: queue used for inter-thread communication
    @type queue: Queue
    '''
    def _create_inverted_lists(indexable_names):
        inverted_lists = dict()
        string_id = 0
        for name in indexable_names:
            qgrams = set(get_qgrams_from_string(name, QGRAM_LEN))
            for qgram in qgrams:
                try:
                    inverted_list, cardinality = inverted_lists[qgram]
                    inverted_list.add(string_id)
                    inverted_lists[qgram][1] = cardinality + 1
                except KeyError:
                    inverted_lists[qgram] = [set([string_id]), 1]
            string_id += 1

        args = list()
        for qgram in inverted_lists:
            inverted_list, cardinality = inverted_lists[qgram]
            args += [qgram, serialize(list(inverted_list)), cardinality]

        populate_table('aidINVERTEDLISTS', ['qgram', 'inverted_list', 'list_cardinality'], args)
        set_inverted_lists_ready()

    result = (True, None)

    try:
        _create_inverted_lists(indexable_names)
    except Exception as e:
        result = (False, e)

    queue.put(result)


def create_dense_index(indexable_names_to_authors_mapping, indexable_names, queue):
    '''
    It saves in the disk the dense index which maps an indexable name to the
    set of authors who carry that name. Each indexable name is assigned a
    unique id.

    @param indexable_names_to_authors_mapping: mapping between indexable names
        and authors who carry that name
    @type indexable_names_to_authors_mapping: dict
    @param indexable_names: indexable names
    @type indexable_names: list
    @param queue: queue used for inter-thread communication
    @type queue: Queue
    '''
    def _create_dense_index(indexable_names_to_authors_mapping, indexable_names):
        args = list()
        string_id = 0
        for name in indexable_names:
            authors, indexable_surname = indexable_names_to_authors_mapping[name]
            args += [string_id, name, serialize(list(authors)), 0, indexable_surname]
            string_id += 1

        populate_table('aidDENSEINDEX', ['id', 'indexable_string', 'personids', 'flag', 'indexable_surname'], args)

    result = (True, None)

    try:
        _create_dense_index(indexable_names_to_authors_mapping, indexable_names)
    except Exception as e:
        result = (False, e)

    queue.put(result)


def cache_name_variants_of_authors(author_to_name_and_occurrence_mapping):
    args = list()
    for author, names_and_occurrence in author_to_name_and_occurrence_mapping.iteritems():
        indexable_names_and_occurrence = dict()
        for name, occurrences in names_and_occurrence.iteritems():
            asciified_name = translate_to_ascii(name)[0]
            indexable_name = create_indexable_name(split_name_parts(indexable_name_re.sub(' ', asciified_name)))
            try:
                indexable_names_and_occurrence[indexable_name] += occurrences
            except KeyError:
                indexable_names_and_occurrence[indexable_name] = occurrences

        args += [author, serialize(indexable_names_and_occurrence), 1]

    populate_table('aidDENSEINDEX', ['id', 'personids', 'flag'], args, empty_table_first=False)


#
#
# Querying            ###
#
#


def find_personids_by_name(query_string, trust_is_operating=False):
    '''
    It returns all the authors that match the query string, sorted by compatibility.

    WARNING: this is just querying the search engine, for a proper person search query one
    should use person_search_engine_query in bibauthorid_dbinterface

    @param query_string: the query string
    @type query_string: str

    @return: author identifiers
    @rtype: list [int,]
    '''
    if not trust_is_operating:
        search_engine_is_oper = search_engine_is_operating()
        if not search_engine_is_oper:
            return None

    asciified_qstring = translate_to_ascii(query_string)[0]
    indexable_qstring = create_indexable_name(split_name_parts(indexable_name_re.sub(' ', asciified_qstring)))

    surname = split_name_parts(query_string)[0] + ','
    asciified_qstring_sur = translate_to_ascii(surname)[0]
    indexable_qstring_sur = create_indexable_name(split_name_parts(indexable_name_re.sub(' ', asciified_qstring_sur)))

    qstring_first_names = indexable_qstring.split(' ')[len(indexable_qstring_sur.split(' ')):]

    string_ids = solve_T_occurence_problem(indexable_qstring) | solve_T_occurence_problem(indexable_qstring_sur)
    if not string_ids:
        return list()

    strings_to_ids_mapping = get_indexed_strings(string_ids)

    passing_string_ids, surname_score_cache = remove_false_positives(indexable_qstring_sur, strings_to_ids_mapping)

    if not passing_string_ids:
        return list()

    author_groups = get_author_groups_from_string_ids(passing_string_ids)

    authors = set()
    for author_group in author_groups:
        authors |= set(deserialize(author_group[0]))

    author_to_names_mapping = get_name_variants_for_authors(authors)

    surname_score_clusters = create_surname_score_clusters(
        indexable_qstring_sur,
        author_to_names_mapping,
        surname_score_cache,
        strings_to_ids_mapping)

    sorted_authors = sort_authors(
        indexable_qstring,
        qstring_first_names,
        surname_score_clusters,
        author_to_names_mapping,
        strings_to_ids_mapping)

    return sorted_authors


def solve_T_occurence_problem(query_string):
    '''
    It solves a 'T-occurence problem' which is defined as follows: find the
    string ids that appear at least T times in the inverted lists which
    correspond to each of the query string qgrams. T respresents the number of
    qgrams that the query string and the strings in the result dataset must
    share. If the result dataset is bigger than a threshold it tries to limit
    it further.

    @param query_string: the query string
    @type query_string: str

    @return: strings that share T (or more) common qgrams with the query string
    @rtype: intbitset intbitset(int,)
    '''
    qgrams = set(get_qgrams_from_string(query_string, QGRAM_LEN))
    if not qgrams:
        return intbitset()

    inverted_lists = get_inverted_lists(qgrams)
    if not inverted_lists:
        return intbitset()

    inverted_lists = sorted(inverted_lists, key=itemgetter(1), reverse=True)
    T = int(MATCHING_QGRAMS_PERCENTAGE * len(inverted_lists))
    string_ids = intbitset(deserialize(inverted_lists[0][0]))

    for i in range(1, T):
        inverted_list = intbitset(deserialize(inverted_lists[i][0]))
        string_ids &= inverted_list

    for i in range(T, len(inverted_lists)):
        if len(string_ids) < MAX_T_OCCURANCE_RESULT_LIST_CARDINALITY:
            break
        inverted_list = intbitset(deserialize(inverted_lists[i][0]))
        string_ids_temp = string_ids & inverted_list
        if len(string_ids_temp) > MIN_T_OCCURANCE_RESULT_LIST_CARDINALITY:
            string_ids = string_ids_temp
        else:
            break

    return string_ids


def remove_false_positives(query_surname, strings_to_ids_mapping):
    '''
    @param query_string:
    @type query_string: str
    @param strings_to_ids_mapping:
    @type strings_to_ids_mapping: dict
    @param surname_score_cache:
    @type surname_score_cache: dict

    @return:
    @rtype: list [int,]
    '''
    passing_string_ids = list()
    surname_score_cache = dict()

    for string, vals in strings_to_ids_mapping.iteritems():
        surname = vals['surname']
        score = calculate_string_score(query_surname, surname)

        if surname not in surname_score_cache:
            surname_score_cache[surname] = score

        if score >= 0.9:
            passing_string_ids.append(vals['sid'])

    return passing_string_ids, surname_score_cache


def get_first_names_from_indexable_string(indexable_string, strings_to_ids_mapping):
    '''

    @param indexable_string:
    @type indexable_string: str

    @return:
    @rtype: list [str,]
    '''
    try:
        surname = strings_to_ids_mapping[indexable_string]['surname']
    except KeyError:
        surname = ''

    return indexable_string.split(' ')[len(surname.split(' ')):]


def calculate_string_score(query_string, candidate_string):
    '''

    @param query_string:
    @type query_string: str
    @param candidate_string:
    @type candidate_string: str

    @return:
    @rtype: int
    '''
    lenqs = len(query_string)
    lencs = len(candidate_string)

    if lenqs > lencs:
        candidate_string = candidate_string + ' ' * (lenqs - lencs)
    elif lencs > lenqs:
        query_string = query_string + ' ' * (lencs - lenqs)

    match_score_vector = [int(x == y) for x, y in zip(query_string, candidate_string)]
    n = len(query_string)
    score = sum([f(match_score_vector[i], i, n + 1) for i in range(n)])

    return score


def f(l, i, n):
    '''
    Geometric serie normalized to sum 1 depending on the number of sums n, and
    with a member partnership controller l (0 or 1). The last addendum is
    always zero, hence it may be useful to call this with n+1 for string
    comparison purposes.

    @param l:
    @type l: int
    @param i:
    @type i: int
    @param n:
    @type n: int

    @return:
    @rtype: int
    '''
    return l * (n - i - 1) * 2. / (n * (n - 1))


def create_surname_score_clusters(query_surname, author_to_names_mapping, surname_score_cache, strings_to_ids_mapping):
    '''

    @param query_string:
    @type query_string: str
    @param author_to_names_mapping:
    @type author_to_names_mapping: dict
    @param surname_score_cache:
    @type surname_score_cache: dict

    @return:
    @rtype: dict {int: [int,]}
    '''
    authors_surname_scores = list()
    for author, names in author_to_names_mapping.iteritems():
        surname_scores = list()
        for name in names:
            try:
                surname = strings_to_ids_mapping[name]['surname']
            except KeyError:
                surname = ""
            try:
                current_score = surname_score_cache[surname]
            except KeyError:
                current_score = calculate_string_score(query_surname, surname)
                surname_score_cache[surname] = current_score
            surname_scores.append(current_score)

        authors_surname_scores.append((author, max(surname_scores)))

    authors_surname_scores = sorted(authors_surname_scores, key=itemgetter(1), reverse=True)

    surname_score_clusters = dict()
    for score, authors in groupby(authors_surname_scores, key=itemgetter(1)):
        surname_score_clusters[score] = [author[0] for author in authors]

    return surname_score_clusters


def sort_authors(
    indexable_string,
    query_names,
    surname_score_clusters,
    author_to_names_mapping,
        strings_to_ids_mapping):
    '''

    @param indexable_string:
    @type indexable_string: str
    @param surname_score_clusters:
    @type surname_score_clusters: dict
    @param author_to_names_mapping:
    @type author_to_names_mapping: dict

    @return:
    @rtype: list [int,]
    '''
    sorted_authors = list()
    query_names_num = len(query_names)
    sorted_surname_scores = sorted(surname_score_clusters.keys(), reverse=True)

    for surname_score in sorted_surname_scores:
        author_scores = list()
        authors = surname_score_clusters[surname_score]

        for author in authors:
            max_name_score = -1
            max_name_score_occurrences = 0
            names = author_to_names_mapping[author]

            for name in names:
                candidate_names = get_first_names_from_indexable_string(name, strings_to_ids_mapping)
                candidate_names_num = len(candidate_names)
                min_names_num = min(query_names_num, candidate_names_num)

                score = 0
                for i in range(min_names_num):
                    score += calculate_string_score(query_names[i], candidate_names[i])

                occurrences = author_to_names_mapping[author][name]
                if score > max_name_score:
                    max_name_score_occurrences = occurrences
                    max_name_score = score
                elif score == max_name_score and max_name_score_occurrences < occurrences:
                    max_name_score_occurrences = occurrences

            author_scores.append((author, max_name_score, max_name_score_occurrences))

        sorted_authors += [author for author, _, _ in sorted(author_scores, key=itemgetter(1, 2), reverse=True)]

    return sorted_authors
