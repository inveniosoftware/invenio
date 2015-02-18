# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014, 2015 CERN.
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

"""Implementation of different ranking methods based on
the citation graph:
- citation count/ time decayed citation count
- pagerank / pagerank with external citations
- time decayed pagerank
"""

# pylint: disable=E0611

import ConfigParser
from math import exp
import datetime
import time
import re
import sys
try:
    from numpy import array, ones, zeros, int32, float32, sqrt, dot
    import_numpy = 1
except ImportError:
    import_numpy = 0

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622


from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.bibtask import write_message
from invenio.modules.ranker.registry import configuration
from invenio.utils.serializers import serialize_via_marshal


def get_citations_from_file(filename):
    """gets the citation data (who cites who) from a file and returns
    - a dictionary of type x:{x1,x2..},
            where x is cited by x1,x2..
    - a dictionary of type a:{b},
             where recid 'a' is asociated with an index 'b' """
    cit = {}
    dict_of_ids = {}
    count = 0
    try:
        citation_file = open(filename, "r")
    except StandardError:
        write_message("Cannot find file: %s" % filename, sys.stderr)
        raise StandardError
    for line in citation_file:
        tokens = line.strip().split()
        recid_cites = int(tokens[0])
        recid_cited = int(tokens[1])
        if recid_cited not in cit:
            cit[recid_cited] = []
        #without this, duplicates might be introduced
        if recid_cites not in cit[recid_cited] and recid_cites != recid_cited:
            cit[recid_cited].append(recid_cites)
        if recid_cites not in dict_of_ids:
            dict_of_ids[recid_cites] = count
            count += 1
        if recid_cited not in dict_of_ids:
            dict_of_ids[recid_cited] = count
            count += 1
    citation_file.close()
    write_message("Citation data collected from file: %s" %filename, verbose=2)
    write_message("Ids and recids corespondace: %s" \
        %str(dict_of_ids), verbose=9)
    write_message("Citations: %s" % str(cit), verbose=9)
    return cit, dict_of_ids


def get_citations_from_db():
    """gets the citation data (who cites who) from the rnkCITATIONDATA table,
    and returns:
    -a dictionary of type x:{x1,x2..}, where x is cited by x1,x2..
    -a dict of type a:{b} where recid 'a' is asociated with an index 'b'"""
    dict_of_ids = {}

    cit = {}
    rows = run_sql("SELECT citer, citee FROM rnkCITATIONDICT")
    for citer, citee in rows:
        cit.setdefault(citee, set()).add(citer)

    count = 0
    for item in cit:
        if item in cit[item]:
            cit[item].remove(item)
        if item not in dict_of_ids:
            dict_of_ids[item] = count
            count += 1
        for value in cit[item]:
            if value not in dict_of_ids:
                dict_of_ids[value] = count
                count += 1

    write_message("Citation data collected", verbose=2)
    write_message("Ids and recids correspondence: %s" \
                                                 % str(dict_of_ids), verbose=9)
    write_message("Citations: %s" % str(cit), verbose=9)

    return cit, dict_of_ids


def construct_ref_array(cit, dict_of_ids, len_):
    """returns an array with the number of references that each recid has """
    ref = array((), int32)
    ref = zeros(len_, int32)
    for key in cit:
        for value in cit[key]:
            ref[dict_of_ids[value]] += 1
    write_message("Number of references: %s" %str(ref), verbose=9)
    write_message("Finished computing total number \
of references for each paper.", verbose=5)
    return ref


def get_external_links_from_file(filename, ref, dict_of_ids):
    """returns a dictionary containing the number of
    external links for each recid
    external link=citation that is not in our database """
    ext_links = {}
    #format: ext_links[dict_of_ids[recid]]=number of total external links
    try:
        external_file = open(filename, "r")
    except StandardError:
        write_message("Cannot find file: %s" % filename, sys.stderr)
        raise StandardError
    for line in external_file:
        tokens = line.strip().split()
        recid = int(tokens[0])
        nr_of_external = int(tokens[1])
        ext_links[dict_of_ids[recid]] = nr_of_external - ref[dict_of_ids[recid]]
        if ext_links[dict_of_ids[recid]] < 0:
            ext_links[dict_of_ids[recid]] = 0
    external_file.close()
    write_message("External link information extracted", verbose=2)
    return ext_links


def get_external_links_from_db_old(ref, dict_of_ids, reference_indicator):
    """returns a dictionary containing the number of
    external links for each recid
    external link=citation that is not in our database """
    ext_links = {}
    reference_tag_regex = reference_indicator + "[a-z]"
    for recid in dict_of_ids:
        query = "select COUNT(DISTINCT field_number) from bibrec_bib99x \
                where id_bibrec='%s' and id_bibxxx in \
                (select id from bib99x where tag RLIKE '%s');" \
                    % (str(recid), reference_tag_regex)
        result_set = run_sql(query)
        if result_set:
            total_links = int(result_set[0][0])
            internal_links = ref[dict_of_ids[recid]]
            ext_links[dict_of_ids[recid]] = total_links - internal_links
            if ext_links[dict_of_ids[recid]] < 0:
                ext_links[dict_of_ids[recid]] = 0
        else:
            ext_links[dict_of_ids[recid]] = 0
    write_message("External link information extracted", verbose=2)
    write_message("External links: %s" % str(ext_links), verbose=9)
    return ext_links


def get_external_links_from_db(ref, dict_of_ids, reference_indicator):
    """returns a dictionary containing the number of
    external links for each recid
    external link=citation that is not in our database """
    ext_links = {}
    dict_all_ref = {}
    for recid in dict_of_ids:
        dict_all_ref[recid] = 0
        ext_links[dict_of_ids[recid]] = 0
    reference_db_id = reference_indicator[0:2]
    reference_tag_regex = reference_indicator + "[a-z]"
    tag_list = run_sql("select id from bib" + reference_db_id + \
                         "x where tag RLIKE %s", (reference_tag_regex, ))
    tag_set = set()
    for tag in tag_list:
        tag_set.add(tag[0])
    ref_list = run_sql("select id_bibrec, id_bibxxx, field_number from \
                       bibrec_bib" + reference_db_id + "x group by \
                       id_bibrec, field_number")
    for item in ref_list:
        recid = int(item[0])
        id_bib = int(item[1])
        if recid in dict_of_ids and id_bib in tag_set:
            dict_all_ref[recid] += 1
    for recid in dict_of_ids:
        total_links = dict_all_ref[recid]
        internal_links = ref[dict_of_ids[recid]]
        ext_links[dict_of_ids[recid]] = total_links - internal_links
        if ext_links[dict_of_ids[recid]] < 0:
            ext_links[dict_of_ids[recid]] = 0
    write_message("External link information extracted", verbose=2)
    write_message("External links: %s" % str(ext_links), verbose=9)
    return ext_links


def avg_ext_links_with_0(ext_links):
    """returns the average number of external links per paper
    including in the counting the papers with 0 external links"""
    total = 0.0
    for item in ext_links:
        total += ext_links[item]
    avg_ext = total/len(ext_links)
    write_message("The average number of external links per paper (including \
papers with 0 external links) is: %s" % str(avg_ext), verbose=3)
    return avg_ext


def avg_ext_links_without_0(ext_links):
    """returns the average number of external links per paper
    excluding in the counting the papers with 0 external links"""
    count = 0.0
    total = 0.0
    for item in ext_links:
        if ext_links[item] != 0:
            count += 1
            total += ext_links[item]
    avg_ext = total/count
    write_message("The average number of external links per paper (excluding \
papers with 0 external links) is: %s" % str(avg_ext), verbose=3)
    return avg_ext


def leaves(ref):
    """returns the number of papers that do not cite any other paper"""
    nr_of_leaves = 0
    for i in ref:
        if i == 0:
            nr_of_leaves += 1
    write_message("The number of papers that do not cite \
any other papers: %s" % str(leaves), verbose=3)
    return nr_of_leaves


def get_dates_from_file(filename, dict_of_ids):
    """Returns the year of the publication for each paper.
    In case the year is not in the db, the year of the submission is taken"""
    dates = {}
    # the format is: dates[dict_of_ids[recid]] = year
    try:
        dates_file = open(filename, "r")
    except StandardError:
        write_message("Cannot find file: %s" % filename, sys.stderr)
        raise StandardError
    for line in dates_file:
        tokens = line.strip().split()
        recid = int(tokens[0])
        year = int(tokens[1])
        dates[dict_of_ids[recid]] = year
    dates_file.close()
    write_message("Dates extracted", verbose=2)
    write_message("Dates dictionary %s" % str(dates), verbose=9)
    return dates


def get_dates_from_db(dict_of_ids, publication_year_tag, creation_date_tag):
    """Returns the year of the publication for each paper.
    In case the year is not in the db, the year of the submission is taken"""
    current_year = int(datetime.datetime.now().strftime("%Y"))
    publication_year_db_id = publication_year_tag[0:2]
    creation_date_db_id = creation_date_tag[0:2]
    total = 0
    count = 0
    dict_of_dates = {}
    for recid in dict_of_ids:
        dict_of_dates[recid] = 0
    date_list = run_sql("select id, tag, value from bib" + \
                        publication_year_db_id + "x where tag=%s", \
                        (publication_year_tag, ))
    date_dict = {}
    for item in date_list:
        date_dict[int(item[0])] = item[2]
    pattern = re.compile('.*(\d{4}).*')
    date_list = run_sql("select id_bibrec, id_bibxxx, field_number \
                        from bibrec_bib" + publication_year_db_id +"x")
    for item in date_list:
        recid = int(item[0])
        id_ = int(item[1])
        if id_ in date_dict and recid in dict_of_dates:
            reg = pattern.match(date_dict[id_])
            if reg:
                date = int(reg.group(1))
                if date > 1000 and date <= current_year:
                    dict_of_dates[recid] = date
                    total += date
                    count += 1
    not_covered = []
    for recid in dict_of_dates:
        if dict_of_dates[recid] == 0:
            not_covered.append(recid)
    date_list = run_sql("select id, tag, value from bib" + \
                        creation_date_db_id + "x where tag=%s", \
                        (creation_date_tag, ))
    date_dict = {}
    for item in date_list:
        date_dict[int(item[0])] = item[2]
    date_list = run_sql("select id_bibrec, id_bibxxx, field_number \
                        from bibrec_bib" + creation_date_db_id + "x")
    for item in date_list:
        recid = int(item[0])
        id_ = int(item[1])
        if id_ in date_dict and recid in not_covered:
            date = int(str(date_dict[id_])[0:4])
            if date > 1000 and date <= current_year:
                dict_of_dates[recid] = date
                total += date
                count += 1
    dates = {}
    med = total/count
    for recid in dict_of_dates:
        if dict_of_dates[recid] == 0:
            dates[dict_of_ids[recid]] = med
        else:
            dates[dict_of_ids[recid]] = dict_of_dates[recid]
    write_message("Dates extracted", verbose=2)
    write_message("Dates dictionary %s" % str(dates), verbose=9)
    return dates


def construct_sparse_matrix(cit, ref, dict_of_ids, len_, damping_factor):
    """returns several structures needed in the calculation
    of the PAGERANK method using this structures, we don't need
    to keep the full matrix in the memory"""
    sparse = {}
    for item in cit:
        for value in cit[item]:
            sparse[(dict_of_ids[item], dict_of_ids[value])] = \
                    damping_factor * 1.0/ref[dict_of_ids[value]]
    semi_sparse = []
    for j in range(len_):
        if ref[j] == 0:
            semi_sparse.append(j)
    semi_sparse_coeficient = damping_factor/len_
    #zero_coeficient = (1-damping_factor)/len_
    write_message("Sparse information calculated", verbose=3)
    return sparse, semi_sparse, semi_sparse_coeficient


def construct_sparse_matrix_ext(cit, ref, ext_links, dict_of_ids, alpha, beta):
    """if x doesn't cite anyone: cites everyone : 1/len_ -- should be used!
    returns several structures needed in the calculation
    of the PAGERANK_EXT method"""
    len_ = len(dict_of_ids)
    sparse = {}
    semi_sparse = {}
    sparse[0, 0] = 1.0 - alpha
    for j in range(len_):
        sparse[j+1, 0] = alpha/(len_)
        if j not in ext_links:
            sparse[0, j+1] = beta/(len_ + beta)
        else:
            if ext_links[j] == 0:
                sparse[0, j+1] = beta/(len_ + beta)
            else:
                aux = beta * ext_links[j]
                if ref[j] == 0:
                    sparse[0, j+1] = aux/(aux + len_)
                else:
                    sparse[0, j+1] = aux/(aux + ref[j])
        if ref[j] == 0:
            semi_sparse[j+1] = (1.0 - sparse[0, j + 1])/len_
    for item in cit:
        for value in cit[item]:
            sparse[(dict_of_ids[item] + 1, dict_of_ids[value] + 1)] = \
               (1.0 - sparse[0, dict_of_ids[value] + 1])/ref[dict_of_ids[value]]
    #for i in range(len_ + 1):
    #    a = ""
    #    for j in range (len_ + 1):
    #        if (i,j) in sparse:
    #            a += str(sparse[(i,j)]) + "\t"
    #        else:
    #            a += "0\t"
    #    print a
    #print semi_sparse
    write_message("Sparse information calculated", verbose=3)
    return sparse, semi_sparse


def construct_sparse_matrix_time(cit, ref, dict_of_ids, \
         damping_factor, date_coef):
    """returns several structures needed in the calculation of the PAGERANK_time
    method using this structures,
    we don't need to keep the full matrix in the memory"""
    len_ = len(dict_of_ids)
    sparse = {}
    for item in cit:
        for value in cit[item]:
            sparse[(dict_of_ids[item], dict_of_ids[value])] = damping_factor * \
                    date_coef[dict_of_ids[value]]/ref[dict_of_ids[value]]
    semi_sparse = []
    for j in range(len_):
        if ref[j] == 0:
            semi_sparse.append(j)
    semi_sparse_coeficient = damping_factor/len_
    #zero_coeficient = (1-damping_factor)/len_
    write_message("Sparse information calculated", verbose=3)
    return sparse, semi_sparse, semi_sparse_coeficient


def statistics_on_sparse(sparse):
    """returns the number of papers that cite themselves"""
    count_diag = 0
    for (i, j) in sparse.keys():
        if i == j:
            count_diag += 1
    write_message("The number of papers that cite themselves: %s" % \
        str(count_diag), verbose=3)
    return count_diag


def pagerank(conv_threshold, check_point, len_, sparse, \
            semi_sparse, semi_sparse_coef):
    """the core function of the PAGERANK method
    returns an array with the ranks coresponding to each recid"""
    weights_old = ones((len_), float32) # initial weights
    weights_new = array((), float32)
    converged = False
    nr_of_check_points = 0
    difference = len_
    while not converged:
        nr_of_check_points += 1
        for step in (range(check_point)):
            weights_new = zeros((len_), float32)
            for (i, j) in sparse.keys():
                weights_new[i] += sparse[(i, j)]*weights_old[j]
            semi_total = 0.0
            for j in semi_sparse:
                semi_total += weights_old[j]
            weights_new = weights_new + semi_sparse_coef * semi_total + \
                            (1.0/len_ - semi_sparse_coef) * sum(weights_old)
            if step == check_point - 1:
                diff = weights_new - weights_old
                difference = sqrt(dot(diff, diff))/len_
                write_message("Finished step: %s, %s " \
                        %(str(check_point*(nr_of_check_points-1) + step), \
                            str(difference)), verbose=5)
            weights_old = weights_new.copy()
            converged = (difference < conv_threshold)
    write_message("PageRank calculated for all recids finnished in %s steps. \
The threshold was %s" % (str(nr_of_check_points), str(difference)),\
             verbose=2)
    return weights_old


def pagerank_ext(conv_threshold, check_point, len_, sparse, semi_sparse):
    """the core function of the PAGERANK_EXT method
    returns an array with the ranks coresponding to each recid"""
    weights_old = array((), float32)
    weights_old = ones((len_), float32)
    weights_new = array((), float32)
    converged = False
    nr_of_check_points = 0
    difference = len_
    while not converged:
        nr_of_check_points += 1
        for step in (range(check_point)):
            weights_new = zeros((len_), float32)
            for (i, j) in sparse.keys():
                weights_new[i] += sparse[(i, j)]*weights_old[j]
            total_sum = 0.0
            for j in semi_sparse:
                total_sum += semi_sparse[j]*weights_old[j]
            weights_new[1:len_] = weights_new[1:len_] + total_sum
            if step == check_point - 1:
                diff = weights_new - weights_old
                difference = sqrt(dot(diff, diff))/len_
                write_message("Finished step: %s, %s " \
                    % (str(check_point*(nr_of_check_points-1) + step), \
                        str(difference)), verbose=5)
            weights_old = weights_new.copy()
            converged = (difference < conv_threshold)
    write_message("PageRank calculated for all recids finnished in %s steps. \
The threshold was %s" % (str(nr_of_check_points), \
            str(difference)), verbose=2)
    #return weights_old[1:len_]/(len_ - weights_old[0])
    return weights_old[1:len_]


def pagerank_time(conv_threshold, check_point, len_, \
        sparse, semi_sparse, semi_sparse_coeficient, date_coef):
    """the core function of the PAGERANK_TIME method: pageRank + time decay
    returns an array with the ranks coresponding to each recid"""
    weights_old = array((), float32)
    weights_old = ones((len_), float32) # initial weights
    weights_new = array((), float32)
    converged = False
    nr_of_check_points = 0
    difference = len_
    while not converged:
        nr_of_check_points += 1
        for step in (range(check_point)):
            weights_new = zeros((len_), float32)
            for (i, j) in sparse.keys():
                weights_new[i] += sparse[(i, j)]*weights_old[j]
            semi_total = 0.0
            for j in semi_sparse:
                semi_total += weights_old[j]*date_coef[j]
            zero_total = 0.0
            for i in range(len_):
                zero_total += weights_old[i]*date_coef[i]
            #dates = array(date_coef.keys())
            #zero_total = dot(weights_old, dates)
            weights_new = weights_new + semi_sparse_coeficient * semi_total + \
                    (1.0/len_ - semi_sparse_coeficient) * zero_total
            if step == check_point - 1:
                diff = weights_new - weights_old
                difference = sqrt(dot(diff, diff))/len_
                write_message("Finished step: %s, %s " \
                    % (str(check_point*(nr_of_check_points-1) + step), \
                    str(difference)), verbose=5)
            weights_old = weights_new.copy()
            converged = (difference < conv_threshold)
    write_message("PageRank calculated for all recids finnished in %s steps.\
The threshold was %s" % (str(nr_of_check_points), \
        str(difference)), verbose=2)
    return weights_old


def citation_rank_time(cit, dict_of_ids, date_coef, dates, decimals):
    """returns a dictionary recid:weight based on the total number of
    citations as function of time"""
    dict_of_ranks = {}
    for key in dict_of_ids:
        if key in cit:
            dict_of_ranks[key] = 0
            for recid in cit[key]:
                dict_of_ranks[key] += date_coef[dict_of_ids[recid]]
            dict_of_ranks[key] = round(dict_of_ranks[key], decimals) \
+ dates[dict_of_ids[key]]* pow(10, 0-4-decimals)
        else:
            dict_of_ranks[key] = dates[dict_of_ids[key]]* pow(10, 0-4-decimals)
    write_message("Citation rank calculated", verbose=2)
    return dict_of_ranks


def get_ranks(weights, dict_of_ids, mult, dates, decimals):
    """returns a dictionary recid:value, where value is the weight of the
    recid paper; the second order is the reverse time order,
    from recent to past"""
    dict_of_ranks = {}
    for item in dict_of_ids:
        dict_of_ranks[item] = round(weights[dict_of_ids[item]]* mult, decimals)\
          + dates[dict_of_ids[item]]* pow(10, 0-4-decimals)
        #dict_of_ranks[item] = weights[dict_of_ids[item]]
    return dict_of_ranks


def sort_weights(dict_of_ranks):
    """sorts the recids based on weights(first order)
    and on dates(second order)"""
    ranks_by_citations = sorted(dict_of_ranks.keys(), lambda x, y: \
cmp(dict_of_ranks[y], dict_of_ranks[x]))
    return ranks_by_citations


def normalize_weights(dict_of_ranks):
    """the weights should be normalized to 100, so they woun't be
    different from the weights from other ranking methods"""
    max_weight = 0.0
    for recid in dict_of_ranks:
        weight = dict_of_ranks[recid]
        if weight > max_weight:
            max_weight = weight
    for recid in dict_of_ranks:
        dict_of_ranks[recid] = round(dict_of_ranks[recid] * 100.0/max_weight, 3)


def write_first_ranks_to_file(ranks_by_citations, dict_of_ranks, \
        nr_of_ranks, filename):
    """Writes the first n results of the ranking method into a file"""
    try:
        ranks_file = open(filename, "w")
    except StandardError:
        write_message("Problems with file: %s" % filename, sys.stderr)
        raise StandardError
    for i in range(nr_of_ranks):
        ranks_file.write(str(i+1) + "\t" + str(ranks_by_citations[i]) + \
            "\t" + str(dict_of_ranks[ranks_by_citations[i]]) + "\n")
    ranks_file.close()
    write_message("The first %s pairs recid:rank in the ranking order \
are written into this file: %s" % (nr_of_ranks, filename), verbose=2)


def del_rank_method_data(rank_method_code):
    """Delete the data for a rank method from rnkMETHODDATA table"""
    id_ = run_sql("SELECT id from rnkMETHOD where name=%s", (rank_method_code, ))
    run_sql("DELETE FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s", (id_[0][0], ))


def into_db(dict_of_ranks, rank_method_code):
    """Writes into the rnkMETHODDATA table the ranking results"""
    method_id = run_sql("SELECT id from rnkMETHOD where name=%s", \
        (rank_method_code, ))
    del_rank_method_data(rank_method_code)
    serialized_data = serialize_via_marshal(dict_of_ranks)
    method_id_str = str(method_id[0][0])
    run_sql("INSERT INTO rnkMETHODDATA(id_rnkMETHOD, relevance_data) \
        VALUES(%s, %s) ", (method_id_str, serialized_data, ))
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    run_sql("UPDATE rnkMETHOD SET last_updated=%s WHERE name=%s", \
        (date, rank_method_code))
    write_message("Finished writing the ranks into rnkMETHOD table", verbose=5)


def run_pagerank(cit, dict_of_ids, len_, ref, damping_factor, \
            conv_threshold, check_point, dates):
    """returns the final form of the ranks when using pagerank method"""
    write_message("Running the PageRank method", verbose=5)
    sparse, semi_sparse, semi_sparse_coeficient = \
        construct_sparse_matrix(cit, ref, dict_of_ids, len_, damping_factor)
    weights = pagerank(conv_threshold, check_point, len_, \
                    sparse, semi_sparse, semi_sparse_coeficient)
    dict_of_ranks = get_ranks(weights, dict_of_ids, 1, dates, 2)
    return dict_of_ranks


def run_pagerank_ext(cit, dict_of_ids, ref, ext_links, \
                        conv_threshold, check_point, alpha, beta, dates):
    """returns the final form of the ranks when using pagerank_ext method"""
    write_message("Running the PageRank with external links method", verbose=5)
    len_ = len(dict_of_ids)
    sparse, semi_sparse = construct_sparse_matrix_ext(cit, ref, \
        ext_links, dict_of_ids, alpha, beta)
    weights = pagerank_ext(conv_threshold, check_point, \
        len_ + 1, sparse, semi_sparse)
    dict_of_ranks = get_ranks(weights, dict_of_ids, 1, dates, 2)
    return dict_of_ranks


def run_pagerank_time(cit, dict_of_ids, len_, ref, damping_factor, \
                        conv_threshold, check_point, date_coef, dates):
    """returns the final form of the ranks when using
    pagerank + time decay method"""
    write_message("Running the PageRank_time method", verbose=5)
    sparse, semi_sparse, semi_sparse_coeficient = \
        construct_sparse_matrix_time(cit, ref, dict_of_ids, \
            damping_factor, date_coef)
    weights = pagerank_time(conv_threshold, check_point, len_, \
        sparse, semi_sparse, semi_sparse_coeficient, date_coef)
    dict_of_ranks = get_ranks(weights, dict_of_ids, 100000, dates, 2)
    return dict_of_ranks


def run_citation_rank_time(cit, dict_of_ids, date_coef, dates):
    """returns the final form of the ranks when using citation count
    as function of time method"""
    write_message("Running the citation rank with time decay method", verbose=5)
    dict_of_ranks = citation_rank_time(cit, dict_of_ids, date_coef, dates, 2)
    return dict_of_ranks


def spearman_rank_correlation_coef(rank1, rank2, len_):
    """rank1 and rank2 are arrays containing the recids in the ranking order
    returns the corelation coeficient (-1 <= c <= 1) between 2 rankings
    the closec c is to 1, the more correlated are the two ranking methods"""
    total = 0
    for i in range(len_):
        rank_value = rank2.index(rank1[i])
        total += (i - rank_value)*(i - rank_value)
    return 1 - (6.0 * total) / (len_*(len_*len_ - 1))


def remove_loops(cit, dates, dict_of_ids):
    """when using time decay, new papers that are part of a loop
    are accumulating a lot of fake weight"""
    new_cit = {}
    for recid in cit:
        new_cit[recid] = []
        for cited_by in cit[recid]:
            if dates[dict_of_ids[cited_by]] >= dates[dict_of_ids[recid]]:
                if cited_by in cit:
                    if recid not in cit[cited_by]:
                        new_cit[recid].append(cited_by)
                    else:
                        write_message("Loop removed: %s <-> %s" \
                            %(cited_by, recid), verbose=9)
                else:
                    new_cit[recid].append(cited_by)
            else:
                write_message("Loop removed: %s <-> %s" \
                        %(cited_by, recid), verbose=9)
    write_message("Simple loops removed", verbose=5)
    return new_cit


def calculate_time_weights(len_, time_decay, dates):
    """calculates the time coeficients for each paper"""
    current_year = int(datetime.datetime.now().strftime("%Y"))
    date_coef = {}
    for j in range(len_):
        date_coef[j] = exp(time_decay*(dates[j] - current_year))
    write_message("Time weights calculated", verbose=5)
    write_message("Time weights: %s" % str(date_coef), verbose=9)
    return date_coef


def get_dates(function, config, dict_of_ids):
    """returns a dictionary containing the year of
    publishing for each paper"""
    try:
        file_for_dates = config.get(function, "file_with_dates")
        dates = get_dates_from_file(file_for_dates, dict_of_ids)
    except (ConfigParser.NoOptionError, StandardError) as err:
        write_message("If you want to read the dates from file set up the \
'file_for_dates' variable in the config file [%s]" %err, verbose=3)
    try:
        publication_year_tag = config.get(function, "publication_year_tag")
        dummy = int(publication_year_tag[0:3])
    except (ConfigParser.NoOptionError, StandardError):
        write_message("You need to set up correctly the publication_year_tag \
                      in the cfg file", sys.stderr)
        raise Exception
    try:
        creation_date_tag = config.get(function, "creation_date_tag")
        dummy = int(creation_date_tag[0:3])
    except (ConfigParser.NoOptionError, StandardError):
        write_message("You need to set up correctly the creation_date_tag \
                      in the cfg file", sys.stderr)
        raise Exception
    dates = get_dates_from_db(dict_of_ids, publication_year_tag, \
                              creation_date_tag)
    return dates


def citerank(rank_method_code):
    """new ranking method based on the citation graph"""
    write_message("Running rank method: %s" % rank_method_code, verbose=0)
    if not import_numpy:
        write_message('The numpy package could not be imported. \
This package is compulsory for running the citerank methods.')
        return
    try:
        file_ = configuration.get(rank_method_code + '.cfg', '')
        config = ConfigParser.ConfigParser()
        config.readfp(open(file_))
    except StandardError:
        write_message("Cannot find configuration file: %s" % file_, sys.stderr)
        raise StandardError
    # the file for citations needs to have the following format:
    #each line needs to be x[tab]y, where x cites y; x,y are recids
    function = config.get("rank_method", "function")
    try:
        file_for_citations = config.get(function, "file_with_citations")
        cit, dict_of_ids = get_citations_from_file(file_for_citations)
    except (ConfigParser.NoOptionError, StandardError) as err:
        write_message("If you want to read the citation data from file set up \
the file_for_citations parameter in the config file [%s]" %err, verbose=2)
        cit, dict_of_ids = get_citations_from_db()
    len_ = len(dict_of_ids.keys())
    write_message("Number of nodes(papers) to rank : %s" % str(len_), verbose=3)
    if len_ == 0:
        write_message("No citation data found, nothing to be done.")
        return
    try:
        method = config.get(function, "citerank_method")
    except ConfigParser.NoOptionError as err:
        write_message("Exception: %s " %err, sys.stderr)
        raise Exception
    write_message("Running %s method." % method, verbose=2)
    dates = get_dates(function, config, dict_of_ids)
    if method == "citation_time":
        try:
            time_decay = float(config.get(function, "time_decay"))
        except (ConfigParser.NoOptionError, ValueError) as err:
            write_message("Exception: %s" % err, sys.stderr)
            raise Exception
        date_coef = calculate_time_weights(len_, time_decay, dates)
        #cit = remove_loops(cit, dates, dict_of_ids)
        dict_of_ranks = \
            run_citation_rank_time(cit, dict_of_ids, date_coef, dates)
    else:
        try:
            conv_threshold = float(config.get(function, "conv_threshold"))
            check_point = int(config.get(function, "check_point"))
            damping_factor = float(config.get(function, "damping_factor"))
            write_message("Parameters: d = %s, conv_threshold = %s, \
check_point = %s" %(str(damping_factor), \
str(conv_threshold), str(check_point)), verbose=5)
        except (ConfigParser.NoOptionError, StandardError) as err:
            write_message("Exception: %s" % err, sys.stderr)
            raise Exception
        if method == "pagerank_classic":
            ref = construct_ref_array(cit, dict_of_ids, len_)
            use_ext_cit = ""
            try:
                use_ext_cit = config.get(function, "use_external_citations")
                write_message("Pagerank will use external citations: %s" \
                   %str(use_ext_cit), verbose=5)
            except (ConfigParser.NoOptionError, StandardError) as err:
                write_message("%s" % err, verbose=2)
            if use_ext_cit == "yes":
                try:
                    ext_citation_file = config.get(function, "ext_citation_file")
                    ext_links = get_external_links_from_file(ext_citation_file,
                                                             ref, dict_of_ids)
                except (ConfigParser.NoOptionError, StandardError):
                    write_message("If you want to read the external citation \
data from file set up the ext_citation_file parameter in the config. file", \
verbose=3)
                    try:
                        reference_tag = config.get(function, "ext_reference_tag")
                        dummy = int(reference_tag[0:3])
                    except (ConfigParser.NoOptionError, StandardError):
                        write_message("You need to set up correctly the \
reference_tag in the cfg file", sys.stderr)
                        raise Exception
                    ext_links = get_external_links_from_db(ref, \
                            dict_of_ids, reference_tag)
                    avg = avg_ext_links_with_0(ext_links)
                    if avg < 1:
                        write_message("This method can't be ran. There is not \
enough information about the external citation. Hint: check the reference tag", \
sys.stderr)
                        raise Exception
                    avg_ext_links_without_0(ext_links)
                try:
                    alpha = float(config.get(function, "ext_alpha"))
                    beta = float(config.get(function, "ext_beta"))
                except (ConfigParser.NoOptionError, StandardError) as err:
                    write_message("Exception: %s" % err, sys.stderr)
                    raise Exception
                dict_of_ranks = run_pagerank_ext(cit, dict_of_ids, ref, \
                ext_links, conv_threshold, check_point, alpha, beta, dates)
            else:
                dict_of_ranks = run_pagerank(cit, dict_of_ids, len_, ref, \
                    damping_factor, conv_threshold, check_point, dates)
        elif method == "pagerank_time":
            try:
                time_decay = float(config.get(function, "time_decay"))
                write_message("Parameter: time_decay = %s" \
                              %str(time_decay), verbose=5)
            except (ConfigParser.NoOptionError, StandardError) as err:
                write_message("Exception: %s" % err, sys.stderr)
                raise Exception
            date_coef = calculate_time_weights(len_, time_decay, dates)
            cit = remove_loops(cit, dates, dict_of_ids)
            ref = construct_ref_array(cit, dict_of_ids, len_)
            dict_of_ranks = run_pagerank_time(cit, dict_of_ids, len_, ref, \
             damping_factor, conv_threshold, check_point, date_coef, dates)
        else:
            write_message("Error: Unknown ranking method. \
Please check the ranking_method parameter in the config. file.", sys.stderr)
            raise Exception
    try:
        filename_ranks = config.get(function, "output_ranks_to_filename")
        max_ranks = config.get(function, "output_rank_limit")
        if not max_ranks.isdigit():
            max_ranks = len_
        else:
            max_ranks = int(max_ranks)
            if max_ranks > len_:
                max_ranks = len_
        ranks = sort_weights(dict_of_ranks)
        write_message("Ranks: %s" % str(ranks), verbose=9)
        write_first_ranks_to_file(ranks, dict_of_ranks, \
                max_ranks, filename_ranks)
    except (ConfigParser.NoOptionError, StandardError):
        write_message("If you want the ranks to be printed in a file you have \
to set output_ranks_to_filename and output_rank_limit \
parameters in the configuration file", verbose=3)
    normalize_weights(dict_of_ranks)
    into_db(dict_of_ranks, rank_method_code)
