## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2010, 2011, 2012 CERN.
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

"""Call BibFormat engine and create HTML brief (and other) formats cache for
   bibliographic records."""

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
    from invenio.bibrank_citation_searcher import get_cited_by
    from invenio.bibrank_citation_indexer import get_bibrankmethod_lastupdate
    from invenio.bibformat import format_record
    from invenio.bibformat_config import CFG_BIBFORMAT_USE_OLD_BIBFORMAT
    from invenio.shellutils import split_cli_ids_arg
    from invenio.bibtask import task_init, write_message, task_set_option, \
            task_get_option, task_update_progress, task_has_option, \
            task_low_level_submission, task_sleep_now_if_required, \
            task_get_task_param
    import os
    import time
    import zlib
    from datetime import datetime
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)


def fetch_last_updated(format):
    select_sql = "SELECT last_updated FROM format WHERE code = %s"
    row = run_sql(select_sql, (format.lower(), ))

    # Fallback in case we receive None instead of a valid date
    last_date = row[0][0] or datetime(year=1900, month=1, day=1)

    return last_date


def store_last_updated(format, update_date):
    sql = "UPDATE format SET last_updated = %s " \
           "WHERE code = %s AND (last_updated < %s or last_updated IS NULL)"
    iso_date = update_date.strftime("%Y-%m-%d %H:%M:%S")
    run_sql(sql, (iso_date, format.lower(), iso_date))


### run the bibreformat task bibsched scheduled
###

def bibreformat_task(fmt, sql, sql_queries, cds_query, process_format, process, recids):
    """
    BibReformat main task

    @param fmt: output format to use
    @param sql: dictionary with pre-created sql queries for various cases (for selecting records). Some of these queries will be picked depending on the case
    @param sql_queries: a list of sql queries to be executed to select records to reformat.
    @param cds_query: a search query to be executed to select records to reformat
    @param process_format:
    @param process:
    @param recids: a list of record IDs to reformat
    @return: None
    """
    write_message("Processing format %s" % fmt)

    t1 = os.times()[4]

    start_date = datetime.now()

### Query the database
###
    task_update_progress('Fetching records to process')
    if process_format:  # '-without' parameter
        write_message("Querying database for records without cache...")
        without_format = without_fmt(sql)

    recIDs = intbitset(recids)

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

    if fmt == "HDREF" and recIDs:
        # HDREF represents the references tab
        # the tab needs to be recomputed not only when the record changes
        # but also when one of the citations changes
        latest_bibrank_run = get_bibrankmethod_lastupdate('citation')
        start_date = latest_bibrank_run
        sql = """SELECT id, modification_date FROM bibrec
                 WHERE id in (%s)""" % ','.join(str(r) for r in recIDs)

        def check_date(mod_date):
            return mod_date < latest_bibrank_run
        recIDs = intbitset([recid for recid, mod_date in run_sql(sql) \
                                                    if check_date(mod_date)])
        for r in recIDs:
            recIDs |= intbitset(get_cited_by(r))

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

### Store last run time
    if task_has_option("last"):
        write_message("storing run date to %s" % start_date)
        store_last_updated(fmt, start_date)

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

def check_validity_input_formats(input_formats):
    """
    Checks the validity of every input format.
    @param input_formats: list of given formats
    @type input_formats: list
    @return: if there is any invalid input format it returns this value
    @rtype: string
    """
    from invenio.search_engine import get_available_output_formats
    valid_formats = get_available_output_formats()

    # let's to extract the values of the available formats
    format_values = []
    for aformat in valid_formats:
        format_values.append(aformat['value'])

    invalid_format = ''
    for aformat in input_formats:
        if aformat.lower() not in format_values:
            invalid_format = aformat.lower()
            break
    return invalid_format

### Identify recIDs of records with missing format
###

def without_fmt(queries, chunk_size=2000):
    """
    List of record IDs to be reformated, not having the specified format yet

    @param sql: a dictionary with sql queries to pick from
    @return: a list of record ID without pre-created format cache
    """
    sql = queries['missing']
    recids = intbitset()
    max_id = run_sql("SELECT max(id) FROM bibrec")[0][0]
    for start in xrange(1, max_id + 1, chunk_size):
        end = start + chunk_size
        recids += intbitset(run_sql(sql, (start, end)))
    return recids


### Bibreformat all selected records (using new python bibformat)
### (see iterate_over_old further down)

def iterate_over_new(list, fmt):
    """
    Iterate over list of IDs

    @param list: the list of record IDs to format
    @param fmt: the output format to use
    @return: tuple (total number of records, time taken to format, time taken to insert)
    """
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
        run_sql('REPLACE LOW_PRIORITY INTO bibfmt (id_bibrec, format, last_updated, value) VALUES (%s, %s, %s, %s)',
                (recID, fmt, start_date, formatted_record))
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
    """
    Iterate over list of IDs

    @param list: the list of record IDs to format
    @param fmt: the output format to use
    @return: tuple (total number of records, time taken to format, time taken to insert)
    """

    n_rec       = 0
    n_max       = 10000
    xml_content = ''        # hold the contents
    tbibformat  = 0         # time taken up by external call
    tbibupload  = 0         # time taken up by external call
    total_rec   = 0         # Number of formatted records

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
        filehandle = open(filename, "w")
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
    if task_get_option('format'):
        fmts = task_get_option('format')
    else:
        fmts = 'HB'  # default value if no format option given
    for fmt in fmts.split(','):
        last_updated = fetch_last_updated(fmt)
        write_message("last stored run date is %s" % last_updated)

        sql = {
            "all" : """SELECT br.id FROM bibrec AS br, bibfmt AS bf
                       WHERE bf.id_bibrec = br.id AND bf.format = '%s'""" % fmt,
            "last": """SELECT br.id FROM bibrec AS br
                       INNER JOIN bibfmt AS bf ON bf.id_bibrec = br.id
                       WHERE br.modification_date >= '%(last_updated)s'
                       AND bf.format='%(format)s'
                       AND bf.last_updated < br.modification_date""" \
                            % {'format': fmt,
                               'last_updated': last_updated.strftime('%Y-%m-%d %H:%M:%S')},
            "missing"  : """SELECT br.id
                            FROM bibrec as br
                            LEFT JOIN bibfmt as bf
                            ON bf.id_bibrec = br.id AND bf.format ='%s'
                            WHERE bf.id_bibrec IS NULL
                            AND br.id BETWEEN %%s AND %%s
                         """ % fmt,
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

        if task_has_option("recids"):
            recids = list(split_cli_ids_arg(task_get_option('recids')))
        else:
            recids = []

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
  bibreformat -o HD,HB           Format all new or modified records in HD and HB.

  bibreformat -a                 Force reformatting all records (in HB).
  bibreformat -c 'Photos'        Force reformatting all records in 'Photos' collection (in HB).
  bibreformat -c 'Photos' -o HD  Force reformatting all records in 'Photos' collection in HD.

  bibreformat -i 15              Force reformatting record 15 (in HB).
  bibreformat -i 15:20           Force reformatting records 15 to 20 (in HB).
  bibreformat -i 15,16,17        Force reformatting records 15, 16 and 17 (in HB).

  bibreformat -n                 Show how many records are to be (re)formatted.
  bibreformat -n -c 'Articles'   Show how many records are to be (re)formatted in 'Articles' collection.

  bibreformat -oHB -s1h          Format all new and modified records every hour, in HB.
""", help_specific_usage="""  -o,  --formats         \t Specify output format/s (default HB)
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
    """
    Elaborate specific CLI parameters of BibReformat.

    @param key: a parameter key to check
    @param value: a value associated to parameter X{Key}
    @return: True for known X{Key} else False.
    """
    if key in ("-a", "--all"):
        task_set_option("all", 1)
        task_set_option("without", 1)
    elif key in ("-c", "--collection"):
        task_set_option("collection", value)
    elif key in ("-n", "--noprocess"):
        task_set_option("noprocess", 1)
    elif key in ("-f", "--field"):
        task_set_option("field", value)
    elif key in ("-p", "--pattern"):
        task_set_option("pattern", value)
    elif key in ("-m", "--matching"):
        task_set_option("matching", value)
    elif key in ("-o", "--format"):
        input_formats = value.split(',')
        ## check the validity of the given output formats
        invalid_format = check_validity_input_formats(input_formats)
        if invalid_format:
            try:
                raise Exception('Invalid output format.')
            except Exception:
                from invenio.errorlib import register_exception
                register_exception(prefix="The given output format '%s' is not available or is invalid. Please try again" % invalid_format, alert_admin=True)
                return
        else:  # every given format is available
            task_set_option("format", value)
    elif key in ("-i", "--id"):
        task_set_option("recids", value)
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
