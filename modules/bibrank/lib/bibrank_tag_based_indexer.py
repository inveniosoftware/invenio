# -*- coding: utf-8 -*-
## Ranking of records using different parameters and methods.

## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012 CERN.
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



import os
import sys
import time
import ConfigParser

from invenio.config import \
     CFG_SITE_LANG, \
     CFG_ETCDIR, \
     CFG_PREFIX
from invenio.search_engine import perform_request_search
from invenio.bibrank_citation_indexer import get_citation_weight, print_missing, get_cit_dict, insert_into_cit_db
from invenio.bibrank_downloads_indexer import *
from invenio.dbquery import run_sql, serialize_via_marshal, deserialize_via_marshal, \
     wash_table_column_name, get_table_update_time
from invenio.errorlib import register_exception
from invenio.bibtask import task_get_option, write_message, task_sleep_now_if_required
from invenio.bibindex_engine import create_range_list
from invenio.intbitset import intbitset

options = {}

def remove_auto_cites(dic):
    """Remove auto-cites and dedupe."""
    for key in dic.keys():
        new_list = dic.fromkeys(dic[key]).keys()
        try:
            new_list.remove(key)
        except ValueError:
            pass
        dic[key] = new_list
    return dic

def citation_repair_exec():
    """Repair citation ranking method"""
    ## repair citations
    for rowname in ["citationdict","reversedict"]:
        ## get dic
        dic = get_cit_dict(rowname)
        ## repair
        write_message("Repairing %s" % rowname)
        dic = remove_auto_cites(dic)
        ## store healthy citation dic
        insert_into_cit_db(dic, rowname)
    return

def download_weight_filtering_user_repair_exec ():
    """Repair download weight filtering user ranking method"""
    write_message("Repairing for this ranking method is not defined. Skipping.")
    return

def download_weight_total_repair_exec():
    """Repair download weight total ranking method"""
    write_message("Repairing for this ranking method is not defined. Skipping.")
    return

def file_similarity_by_times_downloaded_repair_exec():
    """Repair file similarity by times downloaded ranking method"""
    write_message("Repairing for this ranking method is not defined. Skipping.")
    return

def single_tag_rank_method_repair_exec():
    """Repair single tag ranking method"""
    write_message("Repairing for this ranking method is not defined. Skipping.")
    return

def citation_exec(rank_method_code, name, config):
    """Rank method for citation analysis"""
    #first check if this is a specific task
    begin_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if task_get_option("cmd") == "print-missing":
        num = task_get_option("num")
        print_missing(num)
    else:
        dict = get_citation_weight(rank_method_code, config)
        if dict:
            if task_get_option("id") or task_get_option("collection") or \
               task_get_option("modified"):
                # user have asked to citation-index specific records
                # only, so we should not update citation indexer's
                # last run time stamp information
                begin_date = None
            intoDB(dict, begin_date, rank_method_code)
        else:
            write_message("No need to update the indexes for citations.")

def download_weight_filtering_user(run):
    return bibrank_engine(run)

def download_weight_total(run):
    return bibrank_engine(run)

def file_similarity_by_times_downloaded(run):
    return bibrank_engine(run)

def download_weight_filtering_user_exec (rank_method_code, name, config):
    """Ranking by number of downloads per User.
    Only one full Text Download is taken in account for one
    specific userIP address"""
    begin_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    time1 = time.time()
    dic = fromDB(rank_method_code)
    last_updated = get_lastupdated(rank_method_code)
    keys = new_downloads_to_index(last_updated)
    filter_downloads_per_hour(keys, last_updated)
    dic = get_download_weight_filtering_user(dic, keys)
    intoDB(dic, begin_date, rank_method_code)
    time2 = time.time()
    return {"time":time2-time1}

def download_weight_total_exec(rank_method_code, name, config):
    """rankink by total number of downloads without check the user ip
    if users downloads 3 time the same full text document it has to be count as 3 downloads"""
    begin_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    time1 = time.time()
    dic = fromDB(rank_method_code)
    last_updated = get_lastupdated(rank_method_code)
    keys = new_downloads_to_index(last_updated)
    filter_downloads_per_hour(keys, last_updated)
    dic = get_download_weight_total(dic, keys)
    intoDB(dic, begin_date, rank_method_code)
    time2 = time.time()
    return {"time":time2-time1}

def file_similarity_by_times_downloaded_exec(rank_method_code, name, config):
    """update dictionnary {recid:[(recid, nb page similarity), ()..]}"""
    begin_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    time1 = time.time()
    dic = fromDB(rank_method_code)
    last_updated = get_lastupdated(rank_method_code)
    keys = new_downloads_to_index(last_updated)
    filter_downloads_per_hour(keys, last_updated)
    dic = get_file_similarity_by_times_downloaded(dic, keys)
    intoDB(dic, begin_date, rank_method_code)
    time2 = time.time()
    return {"time":time2-time1}

def single_tag_rank_method_exec(rank_method_code, name, config):
    """Creating the rank method data"""
    begin_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    rnkset = {}
    rnkset_old = fromDB(rank_method_code)
    rnkset_new = single_tag_rank(config)
    rnkset = union_dicts(rnkset_old, rnkset_new)
    intoDB(rnkset, begin_date, rank_method_code)

def single_tag_rank(config):
    """Connect the given tag with the data from the kb file given"""
    write_message("Loading knowledgebase file", verbose=9)
    kb_data = {}
    records = []

    write_message("Reading knowledgebase file: %s" % \
                   config.get(config.get("rank_method", "function"), "kb_src"))
    input = open(config.get(config.get("rank_method", "function"), "kb_src"), 'r')
    data = input.readlines()
    for line in data:
        if not line[0:1] == "#":
            kb_data[string.strip((string.split(string.strip(line), "---"))[0])] = (string.split(string.strip(line), "---"))[1]
    write_message("Number of lines read from knowledgebase file: %s" % len(kb_data))

    tag = config.get(config.get("rank_method", "function"), "tag")
    tags = config.get(config.get("rank_method", "function"), "check_mandatory_tags").split(", ")
    if tags == ['']:
        tags = ""

    records = []
    for (recids, recide) in options["recid_range"]:
        task_sleep_now_if_required(can_stop_too=True)
        write_message("......Processing records #%s-%s" % (recids, recide))
        recs = run_sql("SELECT id_bibrec, value FROM bib%sx, bibrec_bib%sx WHERE tag=%%s AND id_bibxxx=id and id_bibrec >=%%s and id_bibrec<=%%s" % (tag[0:2], tag[0:2]), (tag, recids, recide))
        valid = intbitset(trailing_bits=1)
        valid.discard(0)
        for key in tags:
            newset = intbitset()
            newset += [recid[0] for recid in (run_sql("SELECT id_bibrec FROM bib%sx, bibrec_bib%sx WHERE id_bibxxx=id AND tag=%%s AND id_bibxxx=id and id_bibrec >=%%s and id_bibrec<=%%s" % (tag[0:2], tag[0:2]), (key, recids, recide)))]
            valid.intersection_update(newset)
        if tags:
            recs = filter(lambda x: x[0] in valid, recs)
        records = records + list(recs)
        write_message("Number of records found with the necessary tags: %s" % len(records))

    records = filter(lambda x: x[0] in options["validset"], records)
    rnkset = {}
    for key, value in records:
        if kb_data.has_key(value):
            if not rnkset.has_key(key):
                rnkset[key] = float(kb_data[value])
            else:
                if kb_data.has_key(rnkset[key]) and float(kb_data[value]) > float((rnkset[key])[1]):
                    rnkset[key] = float(kb_data[value])
        else:
            rnkset[key] = 0

    write_message("Number of records available in rank method: %s" % len(rnkset))
    return rnkset

def get_lastupdated(rank_method_code):
    """Get the last time the rank method was updated"""
    res = run_sql("SELECT rnkMETHOD.last_updated FROM rnkMETHOD WHERE name=%s", (rank_method_code, ))
    if res:
        return res[0][0]
    else:
        raise Exception("Is this the first run? Please do a complete update.")

def intoDB(dict, date, rank_method_code):
    """Insert the rank method data into the database"""
    mid = run_sql("SELECT id from rnkMETHOD where name=%s", (rank_method_code, ))
    del_rank_method_codeDATA(rank_method_code)
    serdata = serialize_via_marshal(dict);
    midstr = str(mid[0][0]);
    run_sql("INSERT INTO rnkMETHODDATA(id_rnkMETHOD, relevance_data) VALUES (%s,%s)", (midstr, serdata,))
    if date:
        run_sql("UPDATE rnkMETHOD SET last_updated=%s WHERE name=%s", (date, rank_method_code))

    # FIXME: the following is a workaround for the citation indexer
    # memory troubles, when Apache WSGI daemon processes may end up
    # doubling the memory after citation dictionary is updated;
    # therefore let us restart the WSGI daemon application after the
    # citation indexer finished, which relieves this problem.  The
    # restart is done via touching invenio.wsgi file.  The proper fix
    # for this problem would be strict separation between citation
    # indexer updating dicts and citation searcher loading dicts.
    if rank_method_code == 'citation':
        os.system('touch ' + os.path.join(CFG_PREFIX, 'var', 'www-wsgi',
                                          'invenio.wsgi'))

def fromDB(rank_method_code):
    """Get the data for a rank method"""
    id = run_sql("SELECT id from rnkMETHOD where name=%s", (rank_method_code, ))
    res = run_sql("SELECT relevance_data FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s", (id[0][0], ))
    if res:
        return deserialize_via_marshal(res[0][0])
    else:
        return {}

def del_rank_method_codeDATA(rank_method_code):
    """Delete the data for a rank method"""
    id = run_sql("SELECT id from rnkMETHOD where name=%s", (rank_method_code, ))
    run_sql("DELETE FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s", (id[0][0], ))

def del_recids(rank_method_code, range_rec):
    """Delete some records from the rank method"""
    id = run_sql("SELECT id from rnkMETHOD where name=%s", (rank_method_code, ))
    res = run_sql("SELECT relevance_data FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s", (id[0][0], ))
    if res:
        rec_dict = deserialize_via_marshal(res[0][0])
        write_message("Old size: %s" % len(rec_dict))
        for (recids, recide) in range_rec:
            for i in range(int(recids), int(recide)):
                if rec_dict.has_key(i):
                    del rec_dict[i]
        write_message("New size: %s" % len(rec_dict))
        intoDB(rec_dict, begin_date, rank_method_code)
    else:
        write_message("Create before deleting!")

def union_dicts(dict1, dict2):
    "Returns union of the two dicts."
    union_dict = {}
    for (key, value) in dict1.iteritems():
        union_dict[key] = value
    for (key, value) in dict2.iteritems():
        union_dict[key] = value
    return union_dict

def rank_method_code_statistics(rank_method_code):
    """Print statistics"""

    method = fromDB(rank_method_code)
    max = ('', -999999)
    maxcount = 0
    min = ('', 999999)
    mincount = 0

    for (recID, value) in method.iteritems():
        if value < min and value > 0:
            min = value
        if value > max:
            max = value

    for (recID, value) in method.iteritems():
        if value == min:
            mincount += 1
        if value == max:
            maxcount += 1

    write_message("Showing statistic for selected method")
    write_message("Method name: %s" % getName(rank_method_code))
    write_message("Short name: %s" % rank_method_code)
    write_message("Last run: %s" % get_lastupdated(rank_method_code))
    write_message("Number of records: %s" % len(method))
    write_message("Lowest value: %s - Number of records: %s" % (min, mincount))
    write_message("Highest value: %s - Number of records: %s" % (max, maxcount))
    write_message("Divided into 10 sets:")
    for i in range(1, 11):
        setcount = 0
        distinct_values = {}
        lower = -1.0 + ((float(max + 1) / 10)) * (i - 1)
        upper = -1.0 + ((float(max + 1) / 10)) * i
        for (recID, value) in method.iteritems():
            if value >= lower and value <= upper:
                setcount += 1
                distinct_values[value] = 1
        write_message("Set %s (%s-%s) %s Distinct values: %s" % (i, lower, upper, len(distinct_values), setcount))

def check_method(rank_method_code):
    write_message("Checking rank method...")
    if len(fromDB(rank_method_code)) == 0:
        write_message("Rank method not yet executed, please run it to create the necessary data.")
    else:
        if len(add_recIDs_by_date(rank_method_code)) > 0:
            write_message("Records modified, update recommended")
        else:
            write_message("No records modified, update not necessary")

def bibrank_engine(run):
    """Run the indexing task.
    Return 1 in case of success and 0 in case of failure.
    """

    try:
        import psyco
        psyco.bind(single_tag_rank)
        psyco.bind(single_tag_rank_method_exec)
        psyco.bind(serialize_via_marshal)
        psyco.bind(deserialize_via_marshal)
    except StandardError, e:
        pass

    startCreate = time.time()
    try:
        options["run"] = []
        options["run"].append(run)
        for rank_method_code in options["run"]:
            task_sleep_now_if_required(can_stop_too=True)
            cfg_name = getName(rank_method_code)
            write_message("Running rank method: %s." % cfg_name)

            file = CFG_ETCDIR + "/bibrank/" + rank_method_code + ".cfg"
            config = ConfigParser.ConfigParser()
            try:
                config.readfp(open(file))
            except StandardError, e:
                write_message("Cannot find configurationfile: %s" % file, sys.stderr)
                raise StandardError

            cfg_short = rank_method_code
            cfg_function = config.get("rank_method", "function") + "_exec"
            cfg_repair_function = config.get("rank_method", "function") + "_repair_exec"
            cfg_name = getName(cfg_short)
            options["validset"] = get_valid_range(rank_method_code)

            if task_get_option("collection"):
                l_of_colls = string.split(task_get_option("collection"), ", ")
                recIDs = perform_request_search(c=l_of_colls)
                recIDs_range = []
                for recID in recIDs:
                    recIDs_range.append([recID, recID])
                options["recid_range"] = recIDs_range
            elif task_get_option("id"):
                options["recid_range"] = task_get_option("id")
            elif task_get_option("modified"):
                options["recid_range"] = add_recIDs_by_date(rank_method_code, task_get_option("modified"))
            elif task_get_option("last_updated"):
                options["recid_range"] = add_recIDs_by_date(rank_method_code)
            else:
                write_message("No records specified, updating all", verbose=2)
                min_id = run_sql("SELECT min(id) from bibrec")[0][0]
                max_id = run_sql("SELECT max(id) from bibrec")[0][0]
                options["recid_range"] = [[min_id, max_id]]

            if task_get_option("quick") == "no":
                write_message("Recalculate parameter not used, parameter ignored.", verbose=9)

            if task_get_option("cmd") == "del":
                del_recids(cfg_short, options["recid_range"])
            elif task_get_option("cmd") == "add":
                func_object = globals().get(cfg_function)
                func_object(rank_method_code, cfg_name, config)
            elif task_get_option("cmd") == "stat":
                rank_method_code_statistics(rank_method_code)
            elif task_get_option("cmd") == "check":
                check_method(rank_method_code)
            elif task_get_option("cmd") == "print-missing":
                func_object = globals().get(cfg_function)
                func_object(rank_method_code, cfg_name, config)
            elif task_get_option("cmd") == "repair":
                func_object = globals().get(cfg_repair_function)
                func_object()
            else:
                write_message("Invalid command found processing %s" % rank_method_code, sys.stderr)
                raise StandardError
    except StandardError, e:
        write_message("\nException caught: %s" % e, sys.stderr)
        register_exception()
        raise StandardError

    if task_get_option("verbose"):
        showtime((time.time() - startCreate))
    return 1

def get_valid_range(rank_method_code):
    """Return a range of records"""
    write_message("Getting records from collections enabled for rank method.", verbose=9)

    res = run_sql("SELECT collection.name FROM collection, collection_rnkMETHOD, rnkMETHOD WHERE collection.id=id_collection and id_rnkMETHOD=rnkMETHOD.id and rnkMETHOD.name=%s",  (rank_method_code, ))
    l_of_colls = []
    for coll in res:
        l_of_colls.append(coll[0])
    if len(l_of_colls) > 0:
        recIDs = perform_request_search(c=l_of_colls)
    else:
        recIDs = []
    valid = intbitset()
    valid += recIDs
    return valid

def add_recIDs_by_date(rank_method_code, dates=""):
    """Return recID range from records modified between DATES[0] and DATES[1].
       If DATES is not set, then add records modified since the last run of
       the ranking method RANK_METHOD_CODE.
    """
    if not dates:
        try:
            dates = (get_lastupdated(rank_method_code), '')
        except Exception:
            dates = ("0000-00-00 00:00:00", '')
    if dates[0] is None:
        dates = ("0000-00-00 00:00:00", '')
    query = """SELECT b.id FROM bibrec AS b WHERE b.modification_date >= %s"""
    if dates[1]:
        query += " and b.modification_date <= %s"
    query += " ORDER BY b.id ASC"""
    if dates[1]:
        res = run_sql(query, (dates[0], dates[1]))
    else:
        res = run_sql(query, (dates[0], ))
    alist = create_range_list([row[0] for row in res])
    if not alist:
        write_message("No new records added since last time method was run")
    return alist

def getName(rank_method_code, ln=CFG_SITE_LANG, type='ln'):
    """Returns the name of the method if it exists"""

    try:
        rnkid = run_sql("SELECT id FROM rnkMETHOD where name=%s", (rank_method_code, ))
        if rnkid:
            rnkid = str(rnkid[0][0])
            res = run_sql("SELECT value FROM rnkMETHODNAME where type=%s and ln=%s and id_rnkMETHOD=%s", (type, ln, rnkid))
            if not res:
                res = run_sql("SELECT value FROM rnkMETHODNAME WHERE ln=%s and id_rnkMETHOD=%s and type=%s", (CFG_SITE_LANG, rnkid, type))
            if not res:
                return rank_method_code
            return res[0][0]
        else:
            raise Exception
    except Exception:
        write_message("Cannot run rank method, either given code for method is wrong, or it has not been added using the webinterface.")
        raise Exception

def single_tag_rank_method(run):
    return bibrank_engine(run)

def showtime(timeused):
    """Show time used for method"""
    write_message("Time used: %d second(s)." % timeused, verbose=9)

def citation(run):
    return bibrank_engine(run)


# Hack to put index based sorting here, but this is very similar to tag
#based method and should re-use a lot of this code, so better to have here
#than separate
#

def index_term_count_exec(rank_method_code, name, config):
    """Creating the rank method data"""
    write_message("Recreating index weighting data")
    begin_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # we must recalculate these every time for all records, since the
    # weighting of a record is determined by the index entries of _other_
    # records

    rnkset = calculate_index_term_count(config)
    intoDB(rnkset, begin_date, rank_method_code)

def calculate_index_term_count(config):
    """Calculate the weight of a record set based on number of enries of a
    tag from the record in another index...useful for authority files"""

    records = []

    if config.has_section("index_term_count"):
        index = config.get("index_term_count","index_table_name")
        tag = config.get("index_term_count","index_term_value_from_tag")
        # check against possible SQL injection:
        dummy = get_table_update_time(index)
        tag = wash_table_column_name(tag)
    else:
        raise Exception("Config file " + config + " does not have index_term_count section")
        return()

    task_sleep_now_if_required(can_stop_too=True)
    write_message("......Processing all records")
    query = "SELECT id_bibrec, value FROM bib%sx, bibrec_bib%sx WHERE tag=%%s AND id_bibxxx=id" % \
            (tag[0:2], tag[0:2]) # we checked that tag is safe
    records = list(run_sql(query, (tag,)))
    write_message("Number of records found with the necessary tags: %s" % len(records))


    rnkset = {}
    for key, value in records:
        hits = 0
        if len(value):
            query = "SELECT hitlist from %s where term = %%s" % index # we checked that index is a table
            row = run_sql(query, (value,))
            if row and row[0] and row[0][0]:
                #has to be prepared for corrupted data!
                try:
                    hits = len(intbitset(row[0][0]))
                except:
                    hits = 0
        rnkset[key] = hits
    write_message("Number of records available in rank method: %s" % len(rnkset))
    return rnkset


def index_term_count(run):
    return bibrank_engine(run)
