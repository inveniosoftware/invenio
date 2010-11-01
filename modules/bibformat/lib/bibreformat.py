## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

"""Call BibFormat engine and create HTML brief (and other) formats for
   bibliographic records.  Upload formats via BibUpload."""

__revision__ = "$Id$"

import sys

try:
    from invenio.dbquery import run_sql
    from invenio.config import \
         CFG_SITE_URL,\
         CFG_TMPDIR,\
         CFG_BINDIR

    from invenio.intbitset import intbitset
    from invenio.search_engine import perform_request_search, search_pattern
    from invenio.search_engine import print_record
    from invenio.bibformat import format_record
    from invenio.bibformat_config import CFG_BIBFORMAT_USE_OLD_BIBFORMAT
    from invenio.bibtask import task_init, write_message, task_set_option, \
            task_get_option, task_update_progress, task_has_option, \
            task_low_level_submission, task_sleep_now_if_required, \
            task_get_task_param
    import os
    import time
    import zlib
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)

### run the bibreformat task bibsched scheduled
###

def bibreformat_task(fmt, sql, sql_queries, cds_query, process_format, process, recids):
    """
    BibReformat main task
    """
    t1 = os.times()[4]


### Query the database
###
    task_update_progress('Fetching records to process')
    if process_format: # '-without' parameter
        write_message("Querying database for records without cache...")
        without_format = without_fmt(sql)

    recIDs = recids

    if cds_query['field']      != "" or  \
       cds_query['collection'] != "" or  \
       cds_query['pattern']    != "":

        write_message("Querying database (CDS query)...")

        if cds_query['collection'] == "":
            # use search_pattern() whenever possible, as it can search
            # even in private collections
            res = search_pattern(p=cds_query['pattern'],
                                 f=cds_query['field'],
                                 m=cds_query['matching'])
        else:
            # use perform_request_search when '-c' argument has been
            # defined, as it is not supported by search_pattern()
            res = intbitset(perform_request_search(req=None, of='id',
                                         c=cds_query['collection'],
                                         p=cds_query['pattern'],
                                         f=cds_query['field']))

        recIDs |= res

    for sql_query in sql_queries:
        write_message("Querying database (%s) ..." % sql_query, verbose=2)
        recIDs |= intbitset(run_sql(sql_query))

### list of corresponding record IDs was retrieved
### now format the selected records

    if process_format:
        write_message("Records to be processed: %d" % (len(recIDs) \
                                               + len(without_format)))
        write_message("Out of it records without existing cache: %d" % len(without_format))
    else:
        write_message("Records to be processed: %d" % (len(recIDs)))

### Initialize main loop

    total_rec   = 0     # Total number of records
    tbibformat  = 0     # time taken up by external call
    tbibupload  = 0     # time taken up by external call


### Iterate over all records prepared in lists I (option)
    if process:
        if CFG_BIBFORMAT_USE_OLD_BIBFORMAT: # FIXME: remove this
                                            # when migration from php to
                                            # python bibformat is done
            (total_rec_1, tbibformat_1, tbibupload_1) = iterate_over_old(recIDs,
                                                                         fmt)
        else:
            (total_rec_1, tbibformat_1, tbibupload_1) = iterate_over_new(recIDs,
                                                                         fmt)
        total_rec += total_rec_1
        tbibformat += tbibformat_1
        tbibupload += tbibupload_1

### Iterate over all records prepared in list II (no_format)
    if process_format and process:
        if CFG_BIBFORMAT_USE_OLD_BIBFORMAT: # FIXME: remove this
                                            # when migration from php to
                                            # python bibformat is done
            (total_rec_2, tbibformat_2, tbibupload_2) = iterate_over_old(without_format,
                                                                         fmt)
        else:
            (total_rec_2, tbibformat_2, tbibupload_2) = iterate_over_new(without_format,
                                                                         fmt)
        total_rec += total_rec_2
        tbibformat += tbibformat_2
        tbibupload += tbibupload_2

### Final statistics

    t2 = os.times()[4]

    elapsed = t2 - t1
    message = "total records processed: %d" % total_rec
    write_message(message)

    message = "total processing time: %2f sec" % elapsed
    write_message(message)

    message = "Time spent on external call (os.system):"
    write_message(message)

    message = " bibformat: %2f sec" % tbibformat
    write_message(message)

    message = " bibupload: %2f sec" % tbibupload
    write_message(message)


### Identify recIDs of records with missing format
###

def without_fmt(sql):
    "List of record IDs to be reformated, not having the specified format yet"

    rec_ids_with_cache = []
    all_rec_ids = []

    q1 = sql['q1']
    q2 = sql['q2']

    ## get complete recID list
    all_rec_ids = intbitset(run_sql(q1))

    ## get complete recID list of formatted records
    rec_ids_with_cache = intbitset(run_sql(q2))

    return all_rec_ids - rec_ids_with_cache


### Bibreformat all selected records (using new python bibformat)
### (see iterate_over_old further down)

def iterate_over_new(list, fmt):
    "Iterate over list of IDs"
    global total_rec

    formatted_records = ''      # (string-)List of formatted record of an iteration
    tbibformat  = 0     # time taken up by external call
    tbibupload  = 0     # time taken up by external call
    start_date = task_get_task_param('task_starting_time') # Time at which the record was formatted

    tot = len(list)
    count = 0
    for recID in list:
        t1 = os.times()[4]
        start_date = time.strftime('%Y-%m-%d %H:%M:%S')
        formatted_record = zlib.compress(format_record(recID, fmt, on_the_fly=True))
        if run_sql('SELECT id FROM bibfmt WHERE id_bibrec=%s AND format=%s', (recID, fmt)):
            run_sql('UPDATE bibfmt SET last_updated=%s, value=%s WHERE id_bibrec=%s AND format=%s', (start_date, formatted_record, recID, fmt))
        else:
            run_sql('INSERT INTO bibfmt(id_bibrec, format, last_updated, value) VALUES(%s, %s, %s, %s)', (recID, fmt, start_date, formatted_record))
        t2 = os.times()[4]
        tbibformat += (t2 - t1)
        count += 1
        if (count % 100) == 0:
            write_message("   ... formatted %s records out of %s" % (count, tot))
            task_update_progress('Formatted %s out of %s' % (count, tot))
            task_sleep_now_if_required(can_stop_too=True)
    if (tot % 100) != 0:
        write_message("   ... formatted %s records out of %s" % (count, tot))
    return (tot, tbibformat, tbibupload)

def iterate_over_old(list, fmt):
    "Iterate over list of IDs"

    n_rec       = 0
    n_max       = 10000
    xml_content = ''        # hold the contents
    tbibformat  = 0     # time taken up by external call
    tbibupload  = 0     # time taken up by external call
    total_rec      = 0          # Number of formatted records

    for record in list:

        n_rec = n_rec + 1
        total_rec = total_rec + 1

        message = "Processing record: %d" % (record)
        write_message(message, verbose=9)

        query = "id=%d&of=xm" % (record)

        count = 0

        contents = print_record(record, 'xm')

        while (contents == "") and (count < 10):
            contents = print_record(record, 'xm')
            count = count + 1
            time.sleep(10)
        if count == 10:
            sys.stderr.write("Failed to download %s from %s after 10 attempts... terminating" % (query, CFG_SITE_URL))
            sys.exit(0)

        xml_content = xml_content + contents

        if xml_content:

            if n_rec >= n_max:

                finalfilename = "%s/rec_fmt_%s.xml" % (CFG_TMPDIR, time.strftime('%Y%m%d_%H%M%S'))
                filename = "%s/bibreformat.xml" % CFG_TMPDIR
                filehandle = open(filename ,"w")
                filehandle.write(xml_content)
                filehandle.close()

### bibformat external call
###
                task_sleep_now_if_required(can_stop_too=True)
                t11 = os.times()[4]
                message = "START bibformat external call"
                write_message(message, verbose=9)
                command = "%s/bibformat otype='%s' < %s/bibreformat.xml > %s 2> %s/bibreformat.err" % (CFG_BINDIR, fmt.upper(), CFG_TMPDIR, finalfilename, CFG_TMPDIR)
                os.system(command)

                t22 = os.times()[4]
                message = "END bibformat external call (time elapsed:%2f)" % (t22-t11)
                write_message(message, verbose=9)
                task_sleep_now_if_required(can_stop_too=True)
                tbibformat = tbibformat + (t22 - t11)


### bibupload external call
###

                t11 = os.times()[4]
                message = "START bibupload external call"
                write_message(message, verbose=9)

                task_id = task_low_level_submission('bibupload', 'bibreformat', '-f', finalfilename)
                write_message("Task #%s submitted" % task_id)

                t22 = os.times()[4]
                message = "END bibupload external call (time elapsed:%2f)" % (t22-t11)
                write_message(message, verbose=9)

                tbibupload = tbibupload + (t22- t11)

                n_rec = 0
                xml_content = ''

### Process the last re-formated chunk
###

    if n_rec > 0:

        write_message("Processing last record set (%d)" % n_rec, verbose=9)

        finalfilename = "%s/rec_fmt_%s.xml" % (CFG_TMPDIR, time.strftime('%Y%m%d_%H%M%S'))
        filename = "%s/bibreformat.xml" % CFG_TMPDIR
        filehandle = open(filename ,"w")
        filehandle.write(xml_content)
        filehandle.close()

### bibformat external call
###

        t11 = os.times()[4]
        message = "START bibformat external call"
        write_message(message, verbose=9)

        command = "%s/bibformat otype='%s' < %s/bibreformat.xml > %s 2> %s/bibreformat.err" % (CFG_BINDIR, fmt.upper(), CFG_TMPDIR, finalfilename, CFG_TMPDIR)
        os.system(command)

        t22 = os.times()[4]
        message = "END bibformat external call (time elapsed:%2f)" % (t22 - t11)
        write_message(message, verbose=9)

        tbibformat = tbibformat + (t22 - t11)

### bibupload external call
###

        t11 = os.times()[4]
        message = "START bibupload external call"
        write_message(message, verbose=9)

        task_id = task_low_level_submission('bibupload', 'bibreformat', '-f', finalfilename)
        write_message("Task #%s submitted" % task_id)

        t22 = os.times()[4]
        message = "END bibupload external call (time elapsed:%2f)" % (t22 - t11)
        write_message(message, verbose=9)

        tbibupload = tbibupload + (t22 - t11)

    return (total_rec, tbibformat, tbibupload)

def task_run_core():
    """Runs the task by fetching arguments from the BibSched task queue.  This is what BibSched will be invoking via daemon call."""

    ## initialize parameters

    fmt = task_get_option('format')
    sql = {
        "all" : "select br.id from bibrec as br, bibfmt as bf where bf.id_bibrec=br.id and bf.format ='%s'" % fmt,
        "last": "select br.id from bibrec as br, bibfmt as bf where bf.id_bibrec=br.id and bf.format='%s' and bf.last_updated < br.modification_date" % fmt,
        "q1"  : "select br.id from bibrec as br",
        "q2"  : "select br.id from bibrec as br, bibfmt as bf where bf.id_bibrec=br.id and bf.format ='%s'" % fmt
    }
    sql_queries = []
    cds_query = {}
    if task_has_option("all"):
        sql_queries.append(sql['all'])
    if task_has_option("last"):
        sql_queries.append(sql['last'])
    if task_has_option("collection"):
        cds_query['collection'] = task_get_option('collection')
    else:
        cds_query['collection'] = ""

    if task_has_option("field"):
        cds_query['field']      = task_get_option('field')
    else:
        cds_query['field']      = ""

    if task_has_option("pattern"):
        cds_query['pattern']      = task_get_option('pattern')
    else:
        cds_query['pattern']      = ""

    if task_has_option("matching"):
        cds_query['matching']      = task_get_option('matching')
    else:
        cds_query['matching']      = ""

    recids = intbitset()
    if task_has_option("recids"):
        for recid in task_get_option('recids').split(','):
            if ":" in recid:
                start = int(recid.split(':')[0])
                end = int(recid.split(':')[1])
                recids += range(start, end)
            else:
                recids.add(int(recid))

### sql commands to be executed during the script run
###

    bibreformat_task(fmt, sql, sql_queries, cds_query, task_has_option('without'), not task_has_option('noprocess'), recids)

    return True

def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibformat',
            authorization_msg="BibReformat Task Submission",
            description="""
BibReformat formats the records and saves the produced outputs for
later retrieval.

BibReformat is usually run periodically via BibSched in order to (1)
format new records in the database and to (2) reformat records for
which the meta data has been modified.

BibReformat has to be run manually when (3) format config files have
been modified, in order to see the changes in the web interface.

Although it is not necessary to run BibReformat to display formatted
records in the web interface, BibReformat allows to improve serving
speed by precreating the outputs. It is suggested to run
BibReformat for 'HB' output.

Option -m cannot be used at the same time as option -c.
Option -c prevents from finding records in private collections.

Examples:
  bibreformat                    Format all new or modified records (in HB).
  bibreformat -o HD              Format all new or modified records in HD.

  bibreformat -a                 Force reformatting all records (in HB).
  bibreformat -c 'Photos'        Force reformatting all records in 'Photos' collection (in HB).
  bibreformat -c 'Photos' -o HD  Force reformatting all records in 'Photos' collection in HD.

  bibreformat -i 15              Force reformatting record 15 (in HB).
  bibreformat -i 15:20           Force reformatting records 15 to 20 (in HB).
  bibreformat -i 15,16,17        Force reformatting records 15, 16 and 17 (in HB).

  bibreformat -n                 Show how many records are to be (re)formatted.
  bibreformat -n -c 'Articles'   Show how many records are to be (re)formatted in 'Articles' collection.

  bibreformat -oHB -s1h          Format all new and modified records every hour, in HB.
""", help_specific_usage="""  -o,  --format         \t Specify output format (default HB)
  -n,  --noprocess      \t Count records to be formatted (no processing done)
Reformatting options:
  -a,  --all            \t Force reformatting all records
  -c,  --collection     \t Force reformatting records by collection
  -f,  --field          \t Force reformatting records by field
  -p,  --pattern        \t Force reformatting records by pattern
  -i,  --id             \t Force reformatting records by record id(s)
Pattern options:
  -m,  --matching       \t Specify if pattern is exact (e), regular expression (r),
                        \t partial (p), any of the words (o) or all of the words (a)
""",
            version=__revision__,
            specific_params=("ac:f:p:lo:nm:i:",
                ["all",
                 "collection=",
                 "matching=",
                 "field=",
                 "pattern=",
                 "format=",
                 "noprocess",
                 "id="]),
            task_submit_check_options_fnc=task_submit_check_options,
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)

def task_submit_check_options():
    """Last checks and updating on the options..."""
    if not (task_has_option('all') or task_has_option('collection') \
            or task_has_option('field') or task_has_option('pattern') \
            or task_has_option('matching') or task_has_option('recids')):
        task_set_option('without', 1)
        task_set_option('last', 1)
    return True

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Elaborate specific CLI parameters of BibReformat."""
    if key in ("-a", "--all"):
        task_set_option("all", 1)
        task_set_option("without", 1)
    elif key in ("-c", "--collection"):
        task_set_option("collection", value)
    elif key in ("-n", "--noprocess"):
        task_set_option("noprocess", 1)
    elif key in ("-f", "--field"):
        task_set_option("field", value)
    elif key in ("-p","--pattern"):
        task_set_option("pattern", value)
    elif key in ("-m", "--matching"):
        task_set_option("matching", value)
    elif key in ("-o","--format"):
        task_set_option("format", value)
    elif key in ("-i","--id"):
        task_set_option("recids", value)
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
