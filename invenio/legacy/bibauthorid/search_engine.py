# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014 CERN.
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

""" Author search engine. """

from .config import QGRAM_LEN, MATCHING_QGRAMS_PERCENTAGE, \
    MAX_T_OCCURANCE_RESULT_LIST_CARDINALITY, MIN_T_OCCURANCE_RESULT_LIST_CARDINALITY, \
    NAME_SCORE_COEFFICIENT

from Queue import Queue
from threading import Thread
from operator import itemgetter
from msgpack import packb as serialize
from msgpack import unpackb as deserialize

from invenio.utils.text import translate_to_ascii
from intbitset import intbitset
from .name_utils import create_indexable_name, distance, split_name_parts
from .dbinterface import get_confirmed_name_to_authors_mapping, get_authors_data_from_indexable_name_ids, get_inverted_lists, \
                         set_inverted_lists_ready, set_dense_index_ready, populate_table, search_engine_is_operating


def get_qgrams_from_string(string, q):
    '''
    It decomposes the given string to its qgrams. The qgrams of a string are its substrings of length q.
    For example the 2-grams (q=2) of string cathey are (ca,at,th,he,ey).

    @param string: the string to be decomposed
    @type string: str
    @param q: the length of the grams
    @type q: int

    @return: the string qgrams ordered accordingly to the position they withhold in the string
    @rtype: list
    '''
    qgrams = list()

    for i in range(len(string)+1-q):
        qgrams.append(string[i:i+q])

    return qgrams


def create_dense_index(name_pids_dict, names_list, q):
    '''
    It builds the dense index which maps a name to the set of personids whi withhold that name.
    Each entry in the dense index is identified by a unique id called name id.

    @param name_pids_dict:
    @type name_pids_dict: dict
    @param names_list: the names to be indexed
    @type names_list: list
    '''
    def _create_dense_index(name_pids_dict, names_list):
        name_id = 0
        args = list()

        for name in names_list:
            person_name, personids = name_pids_dict[name]
            args += [name_id, person_name, serialize(list(personids))]
            name_id += 1

        populate_table('aidDENSEINDEX', ['name_id','person_name','personids'], args)
        set_dense_index_ready()


    result = (True, None)

    try:
        _create_dense_index(name_pids_dict, names_list)
    except Exception as e:
        result = (False, e)

    q.put(result)


def create_inverted_lists(names_list, q):
    '''
    It builds the inverted index which maps a qgram to the set of name ids that share that qgram.
    To construct the index it decomposes each name string into its qgrams and adds its id to the
    corresponding inverted list.

    @param names_list: the names to be indexed
    @type names_list: list
    '''
    def create_inverted_lists_worker(names_list):
        name_id = 0
        inverted_lists = dict()

        for name in names_list:
            qgrams = set(get_qgrams_from_string(name, QGRAM_LEN))
            for qgram in qgrams:
                try:
                    inverted_list, cardinality = inverted_lists[qgram]
                    inverted_list.add(name_id)
                    inverted_lists[qgram][1] = cardinality + 1
                except KeyError:
                    inverted_lists[qgram] = [set([name_id]), 1]
            name_id += 1

        args = list()

        for qgram in inverted_lists.keys():
            inverted_list, cardinality = inverted_lists[qgram]
            args += [qgram, serialize(list(inverted_list)), cardinality]

        populate_table('aidINVERTEDLISTS', ['qgram','inverted_list','list_cardinality'], args)
        set_inverted_lists_ready()


    result = (True, None)

    try:
        create_inverted_lists_worker(names_list)
    except Exception as e:
        result = (False, e)

    q.put(result)


def create_bibauthorid_indexer():
    '''
    It constructs the disk-based indexer. It consists of the dense index (which maps a name
    to the set of personids who withhold that name) and the inverted lists (which map a qgram
    to the set of name ids that share that qgram).
    '''
    name_pids_dict = get_confirmed_name_to_authors_mapping()
    if not name_pids_dict:
        return

    indexable_name_pids_dict = dict()

    for name in name_pids_dict.keys():
        asciified_name = translate_to_ascii(name)[0]
        indexable_name = create_indexable_name(asciified_name)
        if indexable_name:
            try:
                asciified_name, pids = indexable_name_pids_dict[indexable_name]
                updated_pids = pids | name_pids_dict[name]
                indexable_name_pids_dict[indexable_name] = (asciified_name, updated_pids)
            except KeyError:
                indexable_name_pids_dict[indexable_name] = (asciified_name, name_pids_dict[name])

        surname = split_name_parts(name)[0]
        asciified_surname = translate_to_ascii(surname)[0]
        indexable_surname = create_indexable_name(asciified_surname)
        if indexable_surname:
            try:
                asciified_surname, pids = indexable_name_pids_dict[indexable_surname]
                updated_pids = pids | name_pids_dict[name]
                indexable_name_pids_dict[indexable_surname] = (asciified_surname, updated_pids)
            except KeyError:
                indexable_name_pids_dict[indexable_surname] = (asciified_surname, name_pids_dict[name])

    indexable_names_list = indexable_name_pids_dict.keys()

    # If an exception/error occurs in any of the threads it is not detectable
    # so inter-thread communication is necessary to make it visible.
    q = Queue()
    threads = list()
    threads.append(Thread(target=create_dense_index, args=(indexable_name_pids_dict, indexable_names_list, q)))
    threads.append(Thread(target=create_inverted_lists, args=(indexable_names_list, q)))

    for t in threads:
        t.start()

    for t in threads:
        all_ok, error = q.get(block=True)
        if not all_ok:
            raise error
        q.task_done()

    for t in threads:
        t.join()


def solve_T_occurence_problem(query_string):
    '''
    It solves a 'T-occurence problem' which is defined as follows: find the string ids
    that apper at least T times on the inverted lists of the query string qgrams. If the
    result dataset is bigger than a threshold it tries to limit it further.

    @param query_string:
    @type query_string: str

    @return: T_occurence_problem answers
    @rtype: list
    '''
    query_string_qgrams = get_qgrams_from_string(query_string, QGRAM_LEN)
    query_string_qgrams_set = set(query_string_qgrams)
    if not query_string_qgrams_set:
        return None

    inverted_lists = get_inverted_lists(query_string_qgrams_set)
    if not inverted_lists:
        return None

    inverted_lists = sorted(inverted_lists, key=itemgetter(1), reverse=True)
    T = int(MATCHING_QGRAMS_PERCENTAGE * len(inverted_lists))
    nameids = intbitset(deserialize(inverted_lists[0][0]))

    for i in range(1, T):
        inverted_list = intbitset(deserialize(inverted_lists[i][0]))
        nameids &= inverted_list

    for i in range(T, len(inverted_lists)):
        if len(nameids) < MAX_T_OCCURANCE_RESULT_LIST_CARDINALITY:
            break
        inverted_list = intbitset(deserialize(inverted_lists[i][0]))
        nameids_temp = inverted_list & nameids
        if len(nameids_temp) > MIN_T_OCCURANCE_RESULT_LIST_CARDINALITY:
            nameids = nameids_temp
        else:
            break

    return nameids


def calculate_name_score1(query_string, nameids):
    '''
    docstring

    @param query_string:
    @type query_string:
    @param nameids:
    @type nameids:

    @return:
    @rtype:
    '''
    name_personids_list = get_authors_data_from_indexable_name_ids(nameids)
    query_last_name = split_name_parts(query_string)[0]
    query_last_name_len = len(query_last_name)
    name_score_list = list()

    for name, personids in name_personids_list:
        current_last_name = split_name_parts(name)[0]
        current_last_name_len = len(current_last_name)
        if abs(query_last_name_len - current_last_name_len) == 0:
            dist = distance(query_last_name, current_last_name)
            limit = min([query_last_name_len, current_last_name_len])
            name_score = sum([1/float(2**(i+1)) for i in range(limit) if query_last_name[i] == current_last_name[i]])/(dist + 1)
            if name_score > 0.5:
                name_score_list.append((name, name_score, deserialize(personids)))

    return name_score_list

def calculate_name_score(query_string, nameids):
    '''
    docstring

    @param query_string:
    @type query_string:
    @param nameids:
    @type nameids:

    @return:
    @rtype:
    '''
    name_personids_list = get_authors_data_from_indexable_name_ids(nameids)
    query_last_name = split_name_parts(query_string)[0]
    query_last_name_len = len(query_last_name)
    name_score_list = list()

    for name, personids in name_personids_list:
        current_last_name = split_name_parts(name)[0]
        current_last_name_len = len(current_last_name)
        if abs(query_last_name_len - current_last_name_len) == 0:
            dist = distance(query_last_name, current_last_name)
            limit = min([query_last_name_len, current_last_name_len])
            name_score = sum([1/float(2**(i+1)) for i in range(limit) if query_last_name[i] == current_last_name[i]])/(dist + 1)
            if name_score > 0.5:
                name_score_list.append((name, name_score, deserialize(personids)))

    return name_score_list


def calculate_pid_score(names_score_list):
    '''
    docstring

    @param names_score_list:
    @type names_score_list:

    @return:
    @rtype:
    '''
    max_appearances = 1
    pid_metrics_dict = dict()

    for name, name_score, personids in names_score_list:
        for pid in personids:
            try:
                appearances = pid_metrics_dict[pid][2]+1
                pid_metrics_dict[pid][2] = appearances
                if appearances > max_appearances:
                    max_appearances = appearances
            except KeyError:
                pid_metrics_dict[pid] = [name, name_score, 1]

    pids_score_list = list()

    for pid in pid_metrics_dict.keys():
        name, name_score, appearances = pid_metrics_dict[pid]
        final_score = NAME_SCORE_COEFFICIENT*name_score + (1-NAME_SCORE_COEFFICIENT)*(appearances/float(max_appearances))
        pids_score_list.append((pid, name, final_score))

    return pids_score_list


def find_personids_by_name1(query_string):
    '''
    It finds a collection of personids who own a signature that is similar to the given query string.
    Its approach is by solving a 'T-occurance problem' and then it applies some filters to the candidate
    answers so it can remove the false positives. In the end it sorts the result set based on the score
    they obtained.

    @param query_string:
    @type query_string: str

    @return: personids which own a signature similar to the query string
    @rtype: list
    '''
    search_engine_is_functioning = search_engine_is_operating()
    if not search_engine_is_functioning:
        return list()

    asciified_query_string = translate_to_ascii(query_string)[0]
    indexable_query_string = create_indexable_name(asciified_query_string)
    if not indexable_query_string:
        return list()

    #query_string_surname = split_name_parts(query_string)[0]
    #asciified_query_string_surname = translate_to_ascii(query_string_surname)[0]
    #indexable_query_string_surname = create_indexable_name(asciified_query_string_surname)

    #if not indexable_query_string and not indexable_query_string_surname:
    #    return list()

    s1 = solve_T_occurence_problem(indexable_query_string)

    if not s1:
        s1 = intbitset()

    nameids = solve_T_occurence_problem(indexable_query_string)

    #s2 = solve_T_occurence_problem(indexable_query_string_surname)
    #if not s2:
    #    s2 = intbitset()

    #nameids = s1 | s2
    if not nameids:
        return list()

    name_score_list = calculate_name_score(asciified_query_string, nameids)

    return name_score_list
    #name_ranking_list = sorted(name_score_list, key=itemgetter(1), reverse=True)

    #pid_score_list = calculate_pid_score(name_ranking_list)
    #pids_ranking_list = sorted(pid_score_list, key=itemgetter(2), reverse=True)

    #ranked_pid_name_list = [pid for pid, name, final_score in pids_ranking_list]

    #return ranked_pid_name_list


def find_personids_by_name(query_string):
    query_string_surname = split_name_parts(query_string)[0]

    name_score_list = set(find_personids_by_name1(query_string) + find_personids_by_name1(query_string_surname))
    name_ranking_list = sorted(name_score_list, key=itemgetter(1), reverse=True)

    pid_score_list = calculate_pid_score(name_ranking_list)
    pids_ranking_list = sorted(pid_score_list, key=itemgetter(2), reverse=True)

    ranked_pid_name_list = [pid for pid, name, final_score in pids_ranking_list]

    return ranked_pid_name_list



