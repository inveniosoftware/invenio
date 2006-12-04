# -*- coding: utf-8 -*-

## $Id$
## Ranking of records using different parameters and methods.

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

__revision__ = "$Id$"

from marshal import loads,dumps
from zlib import compress,decompress
from string import split,translate,lower,upper
import getopt
import getpass
import string
import os
import sre
import sys
import time
import Numeric
import urllib
import signal
import tempfile
import unicodedata
import traceback
import cStringIO
import re
import copy
import types
import ConfigParser

from invenio.config import \
     CFG_MAX_RECID, \
     cdslang, \
     etcdir, \
     version
from invenio.search_engine import perform_request_search, strip_accents
from invenio.search_engine import HitSet, get_index_id, create_basic_search_units
from invenio.bibrank_citation_indexer import get_citation_weight
from invenio.bibrank_downloads_indexer import *
from invenio.dbquery import run_sql, escape_string

options = {}
def citation_exec(rank_method_code, name, config):
    """Creating the rank method data for citation"""
    dict = get_citation_weight(rank_method_code, config)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if dict: intoDB(dict, date, rank_method_code)
    else: print "no need to update the indexes for citations"
def single_tag_rank_method_exec(rank_method_code, name, config):
    """Creating the rank method data"""
    startCreate = time.time()
    rnkset = {}
    rnkset_old = fromDB(rank_method_code)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    rnkset_new = single_tag_rank(config)
    rnkset = union_dicts(rnkset_old, rnkset_new)
    intoDB(rnkset, date, rank_method_code)
def download_weight_filtering_user(row,run):
    return bibrank_engine(row,run)
def download_weight_total(row,run):
    return bibrank_engine(row,run)
def file_similarity_by_times_downloaded(row,run):
    return bibrank_engine(row,run)
def download_weight_filtering_user_exec (rank_method_code, name, config):
    """Ranking by number of downloads per User.
    Only one full Text Download is taken in account for one specific userIP address"""
    time1 = time.time()
    dic = fromDB(rank_method_code)
    last_updated = get_lastupdated(rank_method_code)
    keys = new_downloads_to_index(last_updated)
    filter_downloads_per_hour(keys,last_updated)
    dic = get_download_weight_filtering_user(dic, keys)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    intoDB(dic, date, rank_method_code)
    time2 = time.time()
    return {"time":time2-time1}
def download_weight_total_exec(rank_method_code, name, config):
    """rankink by total number of downloads without check the user ip
    if users downloads 3 time the same full text document it has to be count as 3 downloads"""
    time1 = time.time()
    dic = fromDB(rank_method_code)
    last_updated = get_lastupdated(rank_method_code)
    keys = new_downloads_to_index(last_updated)
    filter_downloads_per_hour(keys,last_updated)
    dic = get_download_weight_total(dic, keys)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    intoDB(dic, date, rank_method_code)
    time2 = time.time()
    return {"time":time2-time1}
def file_similarity_by_times_downloaded_exec(rank_method_code, name, config):
    """update dictionnary {recid:[(recid,nb page similarity),()..]}"""
    time1 = time.time()
    dic = fromDB(rank_method_code)
    last_updated = get_lastupdated(rank_method_code)
    keys = new_downloads_to_index(last_updated)
    filter_downloads_per_hour(keys,last_updated)
    dic = get_file_similarity_by_times_downloaded(dic, keys)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    intoDB(dic, date, rank_method_code)
    time2 = time.time()
    return {"time":time2-time1}
def single_tag_rank_method_exec(rank_method_code, name, config):
    """Creating the rank method data"""
    startCreate = time.time()
    rnkset = {}
    rnkset_old = fromDB(rank_method_code)
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    rnkset_new = single_tag_rank(config)
    rnkset = union_dicts(rnkset_old, rnkset_new)
    intoDB(rnkset, date, rank_method_code)

def single_tag_rank(config):
    """Connect the given tag with the data from the kb file given"""
    if options["verbose"] >= 9:
        write_message("Loading knowledgebase file")
    kb_data = {}
    records = []

    write_message("Reading knowledgebase file: %s" % config.get(config.get("rank_method", "function"), "kb_src"))
    input = open(config.get(config.get("rank_method", "function"), "kb_src"), 'r')
    data = input.readlines()
    for line in data:
        if not line[0:1] == "#":
            kb_data[string.strip((string.split(string.strip(line),"---"))[0])] = (string.split(string.strip(line), "---"))[1]
    write_message("Number of lines read from knowledgebase file: %s" % len(kb_data))

    tag = config.get(config.get("rank_method", "function"),"tag")
    tags = split(config.get(config.get("rank_method", "function"), "check_mandatory_tags"),",")
    if tags == ['']:
	tags = ""
   
    records = []
    for (recids,recide) in options["recid_range"]:
        write_message("......Processing records #%s-%s" % (recids, recide))
        recs = run_sql("SELECT id_bibrec,value FROM bib%sx,bibrec_bib%sx WHERE tag='%s' AND id_bibxxx=id and id_bibrec >=%s and id_bibrec<=%s" % (tag[0:2], tag[0:2], tag, recids, recide))
        valid = HitSet(Numeric.ones(CFG_MAX_RECID + 1))
        for key in tags:
            newset = HitSet()
            newset.addlist(run_sql("SELECT id_bibrec FROM bib%sx,bibrec_bib%sx WHERE id_bibxxx=id AND tag='%s' AND id_bibxxx=id and id_bibrec >=%s and id_bibrec<=%s" % (tag[0:2], tag[0:2], key, recids, recide)))
            valid.intersect(newset)
        if tags:
            recs = filter(lambda x: valid.contains(x[0]), recs)
        records = records + list(recs)
        write_message("Number of records found with the necessary tags: %s" % len(records))

    records = filter(lambda x: options["validset"].contains(x[0]), records)
    rnkset = {}
    for key,value in records:
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
    res = run_sql("SELECT rnkMETHOD.last_updated FROM rnkMETHOD WHERE name='%s'" % rank_method_code)
    if res:
        return res[0][0]
    else:
        raise Exception("Is this the first run? Please do a complete update.")

def intoDB(dict, date, rank_method_code):
    """Insert the rank method data into the database"""
    id = run_sql("SELECT id from rnkMETHOD where name='%s'" % rank_method_code)
    del_rank_method_codeDATA(rank_method_code)
    run_sql("INSERT INTO rnkMETHODDATA(id_rnkMETHOD, relevance_data) VALUES ('%s','%s')" % (id[0][0], serialize_via_marshal(dict)))
    run_sql("UPDATE rnkMETHOD SET last_updated='%s' WHERE name='%s'" % (date, rank_method_code))

def fromDB(rank_method_code):
    """Get the data for a rank method"""
    id = run_sql("SELECT id from rnkMETHOD where name='%s'" % rank_method_code)
    res = run_sql("SELECT relevance_data FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s" % id[0][0])
    if res:
        return deserialize_via_marshal(res[0][0])
    else:
        return {}

def del_rank_method_codeDATA(rank_method_code):
    """Delete the data for a rank method"""
    id = run_sql("SELECT id from rnkMETHOD where name='%s'" % rank_method_code)
    res = run_sql("DELETE FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s" % id[0][0])

def del_recids(rank_method_code, range):
    """Delete some records from the rank method"""
    id = run_sql("SELECT id from rnkMETHOD where name='%s'" % rank_method_code)
    res = run_sql("SELECT relevance_data FROM rnkMETHODDATA WHERE id_rnkMETHOD=%s" % id[0][0])
    if res:
        rec_dict = deserialize_via_marshal(res[0][0])
        write_message("Old size: %s" % len(rec_dict))
        for (recids,recide) in range:
            for i in range(int(recids), int(recide)):
                if rec_dict.has_key(i):
                    del rec_dict[i]  
        write_message("New size: %s" % len(rec_dict))
        date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        intoDB(rec_dict, date, rank_method_code)
    else:
        print "Create before deleting!"
    
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
    max = ('',-999999)
    maxcount = 0
    min = ('',999999)
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
    for i in range(1,11):
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
 
def write_message(msg, stream = sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr). Useful for debugging stuff."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
        stream.write("%s\n" % msg)
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s. [must be sys.stdout or sys.stderr]\n" % stream)
    return

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    shift_re = sre.compile("([-\+]{0,1})([\d]+)([dhms])")
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = shift_re.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        date = time.localtime(date + sign * factor * value)
        date = time.strftime(format_string, date)
    else:
        date = time.strptime(var, format_string)
        date = time.strftime(format_string, date)
    return date

def task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_sleep(), got signal %s frame %s" % (sig, frame))
    write_message("sleeping...")
    task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal

def task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_wakeup(), got signal %s frame %s" % (sig, frame))
    write_message("continuing...")
    task_update_status("CONTINUING")

def task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_stop(), got signal %s frame %s" % (sig, frame))
    write_message("stopping...")
    task_update_status("STOPPING")
    errcode = 0
    try:
        task_sig_stop_commands()
        write_message("stopped")
        task_update_status("STOPPED")
    except StandardError, err:
        write_message("Error during stopping! %e" % err)
        task_update_status("STOPPINGFAILED")
        errcode = 1
    sys.exit(errcode)

def task_sig_stop_commands():
    """Do all the commands necessary to stop the task before quitting.
    Useful for task_sig_stop() handler.
    """
    write_message("stopping commands started")
    write_message("stopping commands ended")

def task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_suicide(), got signal %s frame %s" % (sig, frame))
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    task_update_status("SUICIDED")
    sys.exit(0)

def task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame)) 

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    query = "UPDATE schTASK SET progress='%s' where id=%d" % (escape_string(msg), options["task"])
    if options["verbose"]>= 9:
        write_message(query)
    run_sql(query)
    return

def task_update_status(val):
    """Updates state information in the BibSched task table."""
    query = "UPDATE schTASK SET status='%s' where id=%d" % (escape_string(val), options["task"])
    if options["verbose"]>= 9:
        write_message(query)
    run_sql(query)
    return

def split_ranges(parse_string):
    recIDs = []
    ranges = string.split(parse_string, ",")
    for range in ranges:
        tmp_recIDs = string.split(range, "-")
        
        if len(tmp_recIDs)==1:
            recIDs.append([int(tmp_recIDs[0]), int(tmp_recIDs[0])])
        else:
            if int(tmp_recIDs[0]) > int(tmp_recIDs[1]): # sanity check
                tmp = tmp_recIDs[0]
                tmp_recIDs[0] = tmp_recIDs[1]
                tmp_recIDs[1] = tmp
            recIDs.append([int(tmp_recIDs[0]), int(tmp_recIDs[1])])
    return recIDs

def bibrank_engine(row, run):
    """Run the indexing task. The row argument is the BibSched task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
   
    try:
        import psyco
        psyco.bind(single_tag_rank) 
        psyco.bind(single_tag_rank_method_exec)
        psyco.bind(serialize_via_numeric_array)
        psyco.bind(deserialize_via_numeric_array)
    except StandardError, e: 
        print "Psyco ERROR",e 

    startCreate = time.time()
    global options
    task_id = row[0]
    task_proc = row[1]
    options = loads(row[6])

    task_starting_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)

    sets = {}
    try:
        options["run"] = []
        options["run"].append(run)
        for rank_method_code in options["run"]:
            cfg_name = getName(rank_method_code)
            if options["verbose"] >= 0:
                write_message("Running rank method: %s." % cfg_name)

            file = etcdir + "/bibrank/" + rank_method_code + ".cfg"
            config = ConfigParser.ConfigParser()
            try:
                config.readfp(open(file))
            except StandardError, e:
                write_message("Cannot find configurationfile: %s" % file, sys.stderr)
                raise StandardError

            cfg_short = rank_method_code
            cfg_function = config.get("rank_method", "function") + "_exec"
            cfg_name = getName(cfg_short)
            options["validset"] = get_valid_range(rank_method_code)

            if options["collection"]:
                l_of_colls = string.split(options["collection"], ",")
                recIDs = perform_request_search(c=l_of_colls)
                recIDs_range = []
                for recID in recIDs:
                    recIDs_range.append([recID,recID])
                options["recid_range"] = recIDs_range
            elif options["id"]:
                options["recid_range"] = options["id"]
            elif options["modified"]:
                options["recid_range"] = add_recIDs_by_date(rank_method_code, options["modified"])
            elif options["last_updated"]:
                options["recid_range"] = add_recIDs_by_date(rank_method_code)
            else:
                if options["verbose"] > 1:
                    write_message("No records specified, updating all")
                min_id = run_sql("SELECT min(id) from bibrec")[0][0]
                max_id = run_sql("SELECT max(id) from bibrec")[0][0]
                options["recid_range"] = [[min_id, max_id]] 

            if options["quick"] == "no" and options["verbose"] >= 9:
                write_message("Recalculate parameter not used, parameter ignored.")

            if options["cmd"] == "del":
                del_recids(cfg_short, options["recid_range"])
            elif options["cmd"] == "add":
                func_object = globals().get(cfg_function)
                func_object(rank_method_code, cfg_name, config)
            elif options["cmd"] == "stat":
                rank_method_code_statistics(rank_method_code)
            elif options["cmd"] == "check":
                check_method(rank_method_code)
            elif options["cmd"] == "repair":
                pass
            else:
                write_message("Invalid command found processing %s" % rank_method_code, sys.stderr)
                raise StandardError
    except StandardError, e:
        write_message("\nException caught: %s" % e, sys.stderr)
        if options["verbose"] >= 9:      
            traceback.print_tb(sys.exc_info()[2])
        raise StandardError

    if options["verbose"]:
        showtime((time.time() - startCreate))
    return 1

def get_valid_range(rank_method_code):
    """Return a range of records"""
    if options["verbose"] >=9:
        write_message("Getting records from collections enabled for rank method.")

    res = run_sql("SELECT collection.name FROM collection,collection_rnkMETHOD,rnkMETHOD WHERE collection.id=id_collection and id_rnkMETHOD=rnkMETHOD.id and rnkMETHOD.name='%s'" %  rank_method_code)
    l_of_colls = []
    for coll in res:
        l_of_colls.append(coll[0])
    if len(l_of_colls) > 0:
        recIDs = perform_request_search(c=l_of_colls)
    else:
        recIDs = []
    valid = HitSet()
    valid.addlist(recIDs)
    return valid
   
def add_recIDs_by_date(rank_method_code, dates=""):
    """Return recID range from records modified between DATES[0] and DATES[1].
       If DATES is not set, then add records modified since the last run of
       the ranking method RANK_METHOD_CODE.
    """
    if not dates:
        try:
            dates = (get_lastupdated(rank_method_code),'')
        except Exception, e:
            dates = ("0000-00-00 00:00:00", '')
    query = """SELECT b.id FROM bibrec AS b WHERE b.modification_date >= '%s'""" % dates[0]
    if dates[1]:
        query += "and b.modification_date <= '%s'" % dates[1]
    query += "ORDER BY b.id ASC"""
    res = run_sql(query)        
    list = create_range_list(res)
    if not list:
        if options["verbose"]:
            write_message("No new records added since last time method was run")
    return list

def getName(rank_method_code, ln=cdslang, type='ln'):
    """Returns the name of the method if it exists"""

    try:
        rnkid = run_sql("SELECT id FROM rnkMETHOD where name='%s'" % rank_method_code)
        if rnkid:
            rnkid = str(rnkid[0][0])
            res = run_sql("SELECT value FROM rnkMETHODNAME where type='%s' and ln='%s' and id_rnkMETHOD=%s" % (type, ln, rnkid))
            if not res:
                res = run_sql("SELECT value FROM rnkMETHODNAME WHERE ln='%s' and id_rnkMETHOD=%s and type='%s'"  % (cdslang, rnkid, type))
            if not res: 
                return rank_method_code
            return res[0][0]
        else:
            raise Exception
    except Exception, e:
        write_message("Cannot run rank method, either given code for method is wrong, or it has not been added using the webinterface.")
        raise Exception

def create_range_list(res):
    """Creates a range list from a recID select query result contained
    in res. The result is expected to have ascending numerical order."""
    if not res:
        return []
    row = res[0]
    if not row:
        return []
    else:
        range_list = [[row[0],row[0]]]
    for row in res[1:]:
        id = row[0]
        if id == range_list[-1][1] + 1:
            range_list[-1][1] = id
        else:
            range_list.append([id,id])
    return range_list

def single_tag_rank_method(row, run):
    return bibrank_engine(row, run)

def serialize_via_numeric_array_dumps(arr):
    return Numeric.dumps(arr)
def serialize_via_numeric_array_compr(str):
    return compress(str)
def serialize_via_numeric_array_escape(str):
    return escape_string(str)
def serialize_via_numeric_array(arr):
    """Serialize Numeric array into a compressed string."""
    return serialize_via_numeric_array_escape(serialize_via_numeric_array_compr(serialize_via_numeric_array_dumps(arr)))
def deserialize_via_numeric_array(string):
    """Decompress and deserialize string into a Numeric array."""
    return Numeric.loads(decompress(string))
def serialize_via_marshal(obj):
    """Serialize Python object via marshal into a compressed string."""
    return escape_string(compress(dumps(obj)))
def deserialize_via_marshal(string):
    """Decompress and deserialize string into a Python object via marshal."""
    return loads(decompress(string))

def showtime(timeused):
    """Show time used for method"""
    if options["verbose"] >= 9:
        write_message("Time used: %d second(s)." % timeused)
def citation(row,run):
    return bibrank_engine(row, run)
