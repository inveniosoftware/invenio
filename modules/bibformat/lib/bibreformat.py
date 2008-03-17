## -*- mode: python; coding: utf-8; -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

    from invenio.search_engine import perform_request_search, search_pattern
    from invenio.search_engine import print_record, encode_for_xml
    from invenio.bibformat import format_record
    from invenio.bibformat_utils import encode_for_xml
    from invenio.bibformat_config import CFG_BIBFORMAT_USE_OLD_BIBFORMAT
    from invenio.bibtask import task_init, write_message, task_set_option, \
            task_get_option, task_update_progress, task_has_option
    import sys
    import os
    import time
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)

sql_queries    = []                           # holds SQL queries to be executed
cds_query      = {}                           # holds CDS query parameters (fields, collection, pattern)
process_format = 0                            # flag, process records without created format
process        = 1                            # flag, process records (unless count only)
fmt            = "hb"                         # default format to be processed


### run the bibreformat task bibsched scheduled
###

def bibreformat_task(sql, sql_queries, cds_query, process_format):
    """
    BibReformat main task
    """
    global process, fmt

    t1 = os.times()[4]


### Query the database
###
    task_update_progress('Fetching records to process')
    if process_format: # '-without' parameter
        write_message("Querying database for records without cache...")
        without_format = without_fmt(sql)

    recIDs = []

    if cds_query['field']      != "" or  \
       cds_query['collection'] != "" or  \
       cds_query['pattern']    != "":

        write_message("Querying database (CDS query)...")

        if cds_query['collection'] == "":
            # use search_pattern() whenever possible, as it can search
            # even in private collections
            res = search_pattern(p=cds_query['pattern'],
                                 f=cds_query['field'],
                                 m=cds_query['matching']).tolist()
        else:
            # use perform_request_search when '-c' argument has been
            # defined, as it is not supported by search_pattern()
            res = perform_request_search(req=None, of='id',
                                         c=cds_query['collection'],
                                         p=cds_query['pattern'],
                                         f=cds_query['field'])


        for item in res:
            recIDs.append(item)

    for sql_query in sql_queries:
        write_message("Querying database (SQL query) ...")
        res = run_sql(sql_query)
        for item in res:
            recIDs.append(item[0])

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


### Result set operations
###

def lhdiff(l1, l2):
    "Does list difference via intermediate hash."
    d = {}
    ld = []
    for e in l2:
        d[e] = 1
    for e in l1:
        if not d.has_key(e):
            ld.append(e)
    return ld


### Result set operations
###

def ldiff(l1, l2):
    "Returns l1 - l2."

    ld = []
    for e in l1:
        if not e in l2:
            ld.append(e)
    return ld

### Identify recIDs of records with missing format
###

def without_fmt(sql):
    "List of record IDs to be reformated, not having the specified format yet"

    rec_ids_with_cache = []
    all_rec_ids = []

    q1 = sql['q1']
    q2 = sql['q2']

    ## get complete recID list
    all_rec_ids = [x[0] for x in run_sql(q1)]

    ## get complete recID list of formatted records
    rec_ids_with_cache = [x[0] for x in run_sql(q2)]

    return lhdiff(all_rec_ids, rec_ids_with_cache)


### Bibreformat all selected records (using new python bibformat)
### (see iterate_over_old further down)

def iterate_over_new(list, fmt):
    "Iterate over list of IDs"
    global total_rec

    n_it_rec       = 0          # Number of records for current iteration
    n_it_max       = 10000      # Number of max records in one iteration
    total_rec      = 0          # Number of formatted records
    formatted_records = ''      # (string-)List of formatted record of an iteration
    tbibformat  = 0     # time taken up by external call
    tbibupload  = 0     # time taken up by external call
    start_date = "1970-01-01 01:01:01" # Time at which the record was formatted

    for recID in list:
        total_rec += 1
        n_it_rec += 1
        task_update_progress('Formatting %s out of %s' %(total_rec, len(list)))

        message = "Processing record %d with format %s (New BibFormat)" % (recID, fmt)
        write_message(message, verbose=9)

        ### bibformat external call
        ###
        t1 = os.times()[4]
        start_date = time.strftime('%Y-%m-%d %H:%M:%S')
        formatted_record = format_record(recID, fmt, on_the_fly=True)
        t2 = os.times()[4]
        tbibformat = tbibformat + (t2 - t1)

        # Encapsulate record in xml tags that bibupload understands
        prologue = '''
    <record>
       <controlfield tag="001">%s</controlfield>
          <datafield tag="FMT" ind1=" " ind2=" ">
             <subfield code="f">%s</subfield>
             <subfield code="d">%s</subfield>
             <subfield code="g">''' % (recID, fmt, start_date)
        epilogue = '''
          </subfield>
       </datafield>
    </record>'''

        if formatted_record != '':
            # Skip this record if its value is empty.
            formatted_records += prologue + encode_for_xml(formatted_record) + epilogue

        # every n_it_max record, upload all formatted records.
        # also upload if recID is last one
        if (n_it_rec > n_it_max or total_rec == len(list)) and \
               formatted_records != '':

            #Save formatted records to disk for bibupload
            finalfilename = "%s/rec_fmt_%s.xml" % (CFG_TMPDIR, time.strftime('%Y%m%d_%H%M%S'))
            filehandle = open(finalfilename, "w")
            filehandle.write("<collection>" + \
                             formatted_records + \
                             "</collection>")
            filehandle.close()

            ### bibupload external call
            ###
            t1 = os.times()[4]
            message = "START bibupload external call"
            write_message(message, verbose=9)

            command = "%s/bibupload -f %s" % (CFG_BINDIR, finalfilename)
            os.system(command)

            t2 = os.times()[4]
            tbibupload = tbibupload + (t2 - t1)
            message = "END bibupload external call (time elapsed:%2f)" % (t2-t1)
            write_message(message, verbose=9)

            #Reset iteration state
            n_it_rec = 0
            formatted_records = ''

    return (total_rec, tbibformat, tbibupload)

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

                t11 = os.times()[4]
                message = "START bibformat external call"
                write_message(message, verbose=9)

                command = "%s/bibformat otype='%s' < %s/bibreformat.xml > %s 2> %s/bibreformat.err" % (CFG_BINDIR, fmt.upper(), CFG_TMPDIR, finalfilename, CFG_TMPDIR)
                os.system(command)

                t22 = os.times()[4]
                message = "END bibformat external call (time elapsed:%2f)" % (t22-t11)
                write_message(message, verbose=9)

                tbibformat = tbibformat + (t22 - t11)


### bibupload external call
###

                t11 = os.times()[4]
                message = "START bibupload external call"
                write_message(message, verbose=9)

                command = "%s/bibupload -f %s" % (CFG_BINDIR, finalfilename)
                os.system(command)

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

        command = "%s/bibupload -f %s" % (CFG_BINDIR, finalfilename)
        os.system(command)

        t22 = os.times()[4]
        message = "END bibupload external call (time elapsed:%2f)" % (t22 - t11)
        write_message(message, verbose=9)

        tbibupload = tbibupload + (t22 - t11)

    return (total_rec, tbibformat, tbibupload)

def task_run_core():
    """Runs the task by fetching arguments from the BibSched task queue.  This is what BibSched will be invoking via daemon call."""

    global process, fmt, process_format
    ## initialize parameters


    fmt = task_get_option('format')

    sql = {

        "all" : "select br.id from bibrec as br, bibfmt as bf where bf.id_bibrec=br.id and bf.format ='%s'" % fmt,
        "last": "select br.id from bibrec as br, bibfmt as bf where bf.id_bibrec=br.id and bf.format='%s' and bf.last_updated < br.modification_date" % fmt,
        "q1"  : "select br.id from bibrec as br",
        "q2"  : "select br.id from bibrec as br, bibfmt as bf where bf.id_bibrec=br.id and bf.format ='%s'" % fmt
    }

    if task_has_option("all"):
        sql_queries.append(sql['all'])
    if task_has_option("without"):
        process_format = 1

    if task_has_option("noprocess"):
        process = 0

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

### sql commands to be executed during the script run
###

    bibreformat_task(sql, sql_queries, cds_query, process_format)

    return True

def main():
    """Main that construct all the bibtask."""
    task_set_option('format', 'hb')
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
Pattern options:
  -m,  --matching       \t Specify if pattern is exact (e), regular expression (r),
                        \t partial (p), any of the words (o) or all of the words (a)
""",
            version=__revision__,
            specific_params=("ac:f:p:lo:nm:",
                ["all",
                "collection=",
                "matching=",
                "field=",
                "pattern=",
                "format=",
                "noprocess"]),
            task_submit_check_options_fnc=task_submit_check_options,
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)

def task_submit_check_options():
    """Last checks and updating on the options..."""
    if not (task_has_option('all') or task_has_option('collection') \
            or task_has_option('field') or task_has_option('pattern') \
            or task_has_option('matching')):
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
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
