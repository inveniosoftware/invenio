# -*- coding: utf-8 -*-
##
## $Id$
##
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

"""
BibUpload: Receive MARC XML file and update the appropriate database
tables according to options.

    Usage: bibupload [options] input.xml
    Examples:  
      $ bibupload -i input.xml

    Options:
     -a, --append            new fields are appended to the existing record
     -c, --correct           fields are replaced by the new ones in the existing record
     -f, --format            takes only the FMT fields into account. Does not update
     -i, --insert            insert the new record in the database
     -r, --replace           the existing record is entirely replaced by the new one
     -z, --reference         update references (update only 999 fields)
     -s, --stage=STAGE       stage to start from in the algorithm (0: always done; 1: FMT tags;
                             2: FFT tags; 3: BibFmt; 4: Metadata update; 5: time update)
     -n,  --notimechange     do not change record last modification date when updating

    Scheduling options:
     -u, --user=USER         user name to store task, password needed
    
    General options:
     -h, --help              print this help and exit
     -v, --verbose=LEVEL     verbose level (from 0 to 9, default 1)
     -V  --version           print the script version    
"""
 
__revision__ = "$Id$"

import os
import sys
import getopt
import getpass
import signal
import string
import marshal
import time
import traceback
from zlib import compress
import MySQLdb
import re

from invenio.config import CFG_OAI_ID_FIELD
from invenio.bibupload_config import * 
from invenio.access_control_engine import acc_authorize_action
from invenio.dbquery import run_sql, \
                            Error
from invenio.bibrecord import create_records, \
                              create_record, \
                              record_add_field, \
                              record_delete_field, \
                              record_xml_output, \
                              record_get_field_instances, \
                              record_get_field_values, \
                              field_get_subfield_values
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.bibformat import format_record
from invenio.config import filedir, \
                           filedirsize, \
                           htdocsurl

# Global variables
options = {}
options['mode'] = None
options['verbose'] = 1 
options['tag'] = None
options['file_path'] = None
options['notimechange'] = 0
options['stage_to_start_from'] = 1

#Statistic variables
stat = {}
stat['nb_records_to_upload'] = 0
stat['nb_records_updated'] = 0
stat['nb_records_inserted'] = 0
stat['nb_errors'] = 0
stat['exectime'] = time.localtime()

### bibsched task related functions:

def write_message(msg, stream=sys.stdout, verbose=1):
    """Write message and flush output stream (may be sys.stdout or
    sys.stderr).  Useful for debugging stuff.  Do not print anything
    if the global verbose option is lower than VERBOSE.
    """
    if stream == sys.stdout or stream == sys.stderr:
        if options['verbose'] >= verbose:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ",
                                       time.localtime()))
            stream.write("%s\n" % msg)
            stream.flush()
    else:
        sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    return

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
    write_message("flushing cache or whatever...")
    time.sleep(3)
    write_message("closing tables or whatever...")
    time.sleep(1)
    write_message("stopped")
    task_update_status("STOPPED")
    sys.exit(0)
    
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

def authenticate(user, header="BibUpload Task Submission", action="runbibupload"):
    """Authenticate the user against the user database.
       Check for its password, if it exists.
       Check for action access rights.
       Return user name upon authorization success,
       do system exit upon authorization failure.
       """

    # FIXME: for the time being do not authenticate but always let the
    # tasks in, because of automated inserts.  Maybe we shall design
    # an internal user here that will always be let in.
    return user

    print header
    print "=" * len(header)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        user = string.strip(string.lower(sys.stdin.readline()))
    else:
        print >> sys.stdout, "\rUsername:", user        
    ## first check user pw:
    res = run_sql("select id,password from user where email=%s", (user,), 1) + \
          run_sql("select id,password from user where nickname=%s", (user,), 1)
    if not res:
        print "Sorry, %s does not exist." % user
        sys.exit(1)        
    else:
        (uid_db, password_db) = res[0]
        if password_db:
            password_entered = getpass.getpass()
            if password_db == password_entered:
                pass
            else:
                print "Sorry, wrong credentials for %s." % user
                sys.exit(1)
        ## secondly check authorization for the action:
        (auth_code, auth_message) = acc_authorize_action(uid_db, action)
        if auth_code != 0:
            print auth_message
            sys.exit(1)
    return user

def task_submit():
    """Submits task to the BibSched task queue.
       This is what people will be invoking via command line.
    """
    global options
    ## sanity check: remove eventual "task" option:
    if options.has_key("task"):
        del options["task"]
    ## authenticate user:
    user = authenticate(options.get("user", ""))
    ## submit task:
    if options["verbose"] >= 9:
        print ""
        write_message("storing task options %s\n" % options)
    task_id = run_sql("""INSERT INTO schTASK (id,proc,user,runtime,sleeptime,status,arguments)
                         VALUES (NULL,'bibupload',%s,%s,%s,'WAITING',%s)""",
                      (user, options["runtime"], options["sleeptime"], marshal.dumps(options)))
    ## update task number: 
    options["task"] = task_id
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(options), task_id))
    write_message("Task #%d submitted." % task_id)    
    return task_id

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    global options
    if options["verbose"] >= 9:
        write_message("Updating task progress to %s." % msg)
    return run_sql("UPDATE schTASK SET progress=%s WHERE id=%s", (msg, options["task"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    global options
    if options["verbose"] >= 9:
        write_message("Updating task status to %s." % val)
    return run_sql("UPDATE schTASK SET status=%s WHERE id=%s", (val, options["task"]))    

def task_read_status(task_id):
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s", (task_id,), 1)
    try:
        out = res[0][0]
    except:
        out = 'UNKNOWN'
    return out

def task_get_options(task_id):
    """Returns options for the task 'task_id' read from the BibSched task queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc='bibupload'", (task_id,))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: BibUpload task %d does not seem to exist." % \
                      task_id, sys.stderr)
        sys.exit(1)
    return out

def task_run(task_id):
    """Runs the task by fetching arguments from the BibSched task
       queue.  This is what BibSched will be invoking via daemon call.

       Return 1 in case of success and 0 in case of failure.
    """
    
    global options, stat
    options = task_get_options(task_id) # get options from BibSched task table
    ## check task id:
    if not options.has_key("task"):
        write_message("Error: The task #%d does not seem to be a BibUpload task." % task_id, sys.stderr)
        return 0
    ## check task status:
    task_status = task_read_status(task_id)
    if task_status != "WAITING":
        write_message("Error: The task #%d is %s.  I expected WAITING." % \
                      (task_id, task_status), sys.stderr)
        return 0
    ## we can run the task now:
    if options["verbose"]:
        write_message("Task #%d started." % task_id)
    task_update_status("RUNNING")
    ## initialize signal handler:
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)

    ## run the task:
    error = 0
    write_message("Input file '%s', input mode '%s'." % (options['file_path'], options['mode']))
    write_message("STAGE 0:", verbose=2)
    
    if options['file_path'] is not None: 
        recs = xml_marc_to_records(open_marc_file(options['file_path']))
        stat['nb_records_to_upload'] = len(recs)
        write_message("   -Open XML marc: DONE", verbose=2)
        if recs is not None:
            # We proceed each record by record
            for record in recs:
                error = bibupload(record)
                if error[0] == 1:
                    if record:                        
                        sys.stderr.write("\n"+record_xml_output(record)+"\n\n")
                    else:
                        sys.stderr.write("\nRecord could not have been parsed.\n\n")
                    stat['nb_errors'] += 1
                task_update_progress("Done %d out of %d." % \
                                     (stat['nb_records_inserted'] + \
                                      stat['nb_records_updated'],
                                      stat['nb_records_to_upload']))
        else:
            write_message("   Error bibupload failed: No record found",
                          verbose=1, stream=sys.stderr)
    
    if options['verbose'] >= 1:
        # Print out the statistics
        print_out_bibupload_statistics()
    
    # Check if they were errors
    if stat['nb_errors'] >= 1:
        task_update_status("DONE WITH ERRORS")
    else:
        ## we are done:
        task_update_status("DONE") 
    if options["verbose"]:
        write_message("Task #%d finished." % task_id)
    return 1

### bibupload engine functions:

def parse_command():
    """Analyze the command line and retrieve arguments (xml file,
       mode, etc) into global options variable.

       Return 0 in case everything went well, 1 in case of errors, 2
       in case only help or version number were asked for.
    """
    # FIXME: add treatment of `time'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ircazs:fu:hv:Vn",
                 [
                   "insert",
                   "replace",
                   "correct",
                   "append",
                   "reference",
                   "stage=",
                   "format",
                   "user=",
                   "help",
                   "verbose=",
                   "version",
                   "notimechange",
                 ])
    except getopt.GetoptError,erro:
        usage()
        write_message("Stage 0 error: %s" % erro, verbose=1, stream=sys.stderr)
        return 1

    # set the proper mode depending on the argument value
    for opt, opt_value in opts:
        # Verbose mode option
        if opt in ["-v", "--verbose"]:
            try:
                options['verbose'] = int(opt_value)
            except ValueError:
                write_message("Failed: enter a valid number for verbose mode (between 0 and 9).", verbose=1, stream=sys.stderr)
                return 1

        # stage mode option
        if opt in ["-s", "--stage"]:
            try:
                options['stage_to_start_from'] = int(opt_value)
            except ValueError:
                write_message("Failed: enter a valid number for the stage to start from(>0).", verbose=1, stream=sys.stderr)
                return 1

        # No time change option
        if opt in ["-n", "--notimechange"]:    
            options['notimechange'] = 1

        # Insert mode option
        if opt in ["-i", "--insert"]:
            if options['mode'] == 'replace':
                # if also replace found, then set to replace_or_insert
                options['mode'] = 'replace_or_insert'
            else:
                options['mode'] = 'insert'
            options['file_path'] = os.path.abspath(args[0])

        # Replace mode option
        if opt in ["-r", "--replace"]:
            if options['mode'] == 'insert':
                # if also insert found, then set to replace_or_insert
                options['mode'] = 'replace_or_insert'
            else:
                options['mode'] = 'replace'
            options['file_path'] = os.path.abspath(args[0])
                
        # Correct mode option
        if opt in ["-c", "--correct"]:
            options['mode'] = 'correct'
            options['file_path'] = os.path.abspath(args[0])

        # Append mode option
        if opt in ["-a", "--append"]:
            options['mode'] = 'append'
            options['file_path'] = os.path.abspath(args[0])

        # Reference mode option
        if opt in ["-z", "--reference"]:
            options['mode'] = 'reference'
            options['file_path'] = os.path.abspath(args[0])

        # Format mode option
        if opt in ["-f", "--format"]:
            options['mode'] = 'format'
            options['file_path'] = os.path.abspath(args[0])
        
        # Detection of user
        if opt in ["-u", "--user"]:    
            options['user'] = opt_value

        # Help mode option
        if opt in ["-h", "--help"]:    
            usage()
            return 2

        # Version mode option
        if opt in ["-V", "--version"]:
            write_message(__revision__, verbose=1)
            return 2

    if options['mode'] is None:
        write_message("Please specify at least one update/insert mode!")
        return 1

    if options['file_path'] is None:
        write_message("Missing filename! -h for help.")
        return 1
    return 0
    
def bibupload(record):
    """Main function: process a record and fit it in the tables
       bibfmt, bibrec, bibrec_bibxxx, bibxxx with proper record
       metadata.

       Return (error_code, recID) of the processed record.
    """
    error = None
    # If there are special tags to proceed check if it exists in the record
    if options['tag'] is not None and not(record.has_key(options['tag'])):
        write_message("    Failed: Tag not found, enter a valid tag to update.", verbose=1, stream=sys.stderr)
        return (1, -1)
    
    # Extraction of the Record Id from 001, SYSNO or OAIID tags:
    rec_id = retrieve_rec_id(record)
    if rec_id == -1:
        return (1, -1)
    elif rec_id > 0:
        write_message("   -Retrieve record ID (found %s): DONE." % rec_id, verbose=2)
        if not record.has_key('001'):
            # Found record ID by means of SYSNO or OAIID, and the
            # input MARCXML buffer does not have this 001 tag, so we
            # should add it now:
            error = record_add_field(record, '001', '', '', rec_id, [], 0)
            if error is None:
                write_message("   Failed: " \
                                             "Error during adding the 001 controlfield "  \
                                             "to the record", verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            else:
                error = None
            write_message("   -Added tag 001: DONE.", verbose=2)
    write_message("   -Check if the xml marc file is already in the database: DONE" , verbose=2)
    
    # Reference mode check if there are reference tag 
    if options['mode'] == 'reference':
        error = extract_tag_from_record(record, CFG_BIBUPLOAD_REFERENCE_TAG)
        if error is None:
            write_message("   Failed: No reference tags has been found...", verbose=1, stream=sys.stderr)
            return (1, -1)
        else:
            error = None
            write_message("   -Check if reference tags exist: DONE", verbose=2)
     
    if options['mode'] == 'insert' or \
       (options['mode'] == 'replace_or_insert' and rec_id is None):
        insert_mode_p = True
        # Insert the record into the bibrec databases to have a recordId
        rec_id = create_new_record()
        write_message("   -Creation of a new record id (%d): DONE" % rec_id, verbose=2)
        
        # we add the record Id control field to the record
        error = record_add_field(record, '001', '', '', rec_id, [], 0)
        if error is None:
            write_message("   Failed: " \
                                         "Error during adding the 001 controlfield "  \
                                         "to the record", verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        else:
            error = None

    elif options['mode'] != 'insert' and options['mode'] != 'format' and options['stage_to_start_from'] != 5:
        insert_mode_p = False
        # Update Mode
        # Retrieve the old record to update
        rec_old = create_record(format_record(int(rec_id), 'xm'), 2)[0]
        if rec_old is None:
            write_message("   Failed during the creation of the old record!", verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        else:
            write_message("   -Retrieve the old record to update: DONE", verbose=2)
        
        # Delete tags to correct in the record
        if options['mode'] == 'correct' or options['mode'] == 'reference':
            delete_tags_to_correct(record, rec_old)
            write_message("   -Delete the old tags to correct in the old record: DONE", verbose=2)
        
        # Append new tag to the old record and update the new record with the old_record modified
        if options['mode'] == 'append' or options['mode'] == 'correct' or options['mode'] == 'reference':
            record = append_new_tag_to_old_record(record, rec_old)
            write_message("   -Append new tags to the old record: DONE", verbose=2)

        # now we clear all the rows from bibrec_bibxxx from the old
        # record (they will be populated later (if needed) during
        # stage 4 below):
        delete_bibrec_bibxxx(rec_old, rec_id)
        write_message("   -Clean bibrec_bibxxx: DONE", verbose=2)
    write_message("   -Stage COMPLETED", verbose=2)

    # Have a look if we have FMT tags
    write_message("Stage 1: Start (Insert of FMT tags if exist).", verbose=2)
    if options['stage_to_start_from'] <= 1 and  extract_tag_from_record(record, 'FMT') is not None:
        record = insert_fmt_tags(record, rec_id)
        if record is None:
            write_message("   Stage 1 failed: Error while inserting FMT tags", verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        elif record == 0:
            # Mode format finished
            stat['nb_records_updated'] += 1
            return (0, int(rec_id))
        write_message("   -Stage COMPLETED", verbose=2)
    else:
        write_message("   -Stage NOT NEEDED", verbose=2)
   
    # Have a look if we have FFT tags 
    write_message("Stage 2: Start (Process FFT tags if exist).", verbose=2)
    if options['stage_to_start_from'] <= 2 and  extract_tag_from_record(record, 'FFT') is not None:
        
        if insert_mode_p or options['mode'] == 'append':
            record = insert_fft_tags(record, rec_id)
        else:
            record = update_fft_tag(record, rec_id)
        write_message("   -Stage COMPLETED", verbose=2)
    else:
        write_message("   -Stage NOT NEEDED", verbose=2)
    
    # Update of the BibFmt
    write_message("Stage 3: Start (Update bibfmt).", verbose=2)
    if options['stage_to_start_from'] <= 3:
        # format the single record as xml
        rec_xml_new = record_xml_output(record)
        # Update bibfmt with the format xm of this record
        if options['mode'] != 'format': 
            error = update_bibfmt_format(rec_id, rec_xml_new, 'xm')
        if error == 1:
            write_message("   Failed: error during update_bibfmt_format", verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        write_message("   -Stage COMPLETED", verbose=2)
    
    # Update the database MetaData
    write_message("Stage 4: Start (Update the database with the metadata).", verbose=2)
    if options['stage_to_start_from'] <= 4:
        if options['mode'] == 'insert' or \
           options['mode'] == 'replace' or \
           options['mode'] == 'replace_or_insert' or \
           options['mode'] == 'append' or \
           options['mode'] == 'correct' or \
           options['mode'] == 'reference':
            update_database_with_metadata(record, rec_id)
        else:
            write_message("   -Stage NOT NEEDED in mode %s" % options['mode'], verbose=2)
        write_message("   -Stage COMPLETED", verbose=2)
    else:
        write_message("   -Stage NOT NEEDED", verbose=2)
    
    # Finally we update the bibrec table with the current date
    write_message("Stage 5: Start (Update bibrec table with current date).", verbose=2)
    if options['stage_to_start_from'] <= 5 and \
       options['notimechange'] == 0 and \
       not insert_mode_p:
        now = convert_datestruct_to_datetext(time.localtime())
        write_message("   -Retrieved current localtime: DONE", verbose=2)
        update_bibrec_modif_date(now, rec_id)
        write_message("   -Stage COMPLETED", verbose=2)
    else:
        write_message("   -Stage NOT NEEDED", verbose=2)

    # Increase statistics
    if insert_mode_p:
        stat['nb_records_inserted'] += 1
    else:
        stat['nb_records_updated'] += 1
    
    # Upload of this record finish
    write_message("Record "+str(rec_id)+" DONE", verbose=1)
    return (0, int(rec_id))

def usage():
    """Print help"""
    print """Receive MARC XML file and update appropriate database tables according to options.

    Usage: bibupload [options] input.xml
    Examples:  
      $ bibupload -i input.xml

    Options:
     -a, --append            new fields are appended to the existing record
     -c, --correct           fields are replaced by the new ones in the existing record
     -f, --format            takes only the FMT fields into account. Does not update
     -i, --insert            insert the new record in the database
     -r, --replace           the existing record is entirely replaced by the new one
     -z, --reference         update references (update only 999 fields)
     -s, --stage=STAGE       stage to start from in the algorithm (0: always done; 1: FMT tags;
                             2: FFT tags; 3: BibFmt; 4: Metadata update; 5: time update)
     -n,  --notimechange     do not change record last modification date when updating

    Scheduling options:
     -u, --user=USER         user name to store task, password needed
    
    General options:
     -h, --help              print this help and exit
     -v, --verbose=LEVEL     verbose level (from 0 to 9, default 1)
     -V  --version           print the script version    
    """    
    
def print_out_bibupload_statistics():
    """Print the statistics of the process"""
    out = "Task stats: %(nb_input)d input records, %(nb_updated)d updated, " \
          "%(nb_inserted)d inserted, %(nb_errors)d errors.  Time %(nb_sec).2f sec." % { \
              'nb_input': stat['nb_records_to_upload'],
              'nb_updated': stat['nb_records_updated'],
              'nb_inserted': stat['nb_records_inserted'],
              'nb_errors': stat['nb_errors'],
              'nb_sec': time.time() - time.mktime(stat['exectime']) }
    write_message(out)    
    
def open_marc_file(path):
    """Open a file and return the data"""
    try:
        # open the file containing the marc document
        marc_file = open(path,'r')
        marc = marc_file.read()
        marc_file.close()
    except IOError, erro:
        write_message("Error: %s" % erro, verbose=1, stream=sys.stderr)
        write_message("Exiting.", sys.stderr)
        task_update_status("ERROR")                                   
        sys.exit(1)
    return marc

def xml_marc_to_records(xml_marc):
    """create the records"""
    # Creation of the records from the xml Marc in argument
    recs = create_records(xml_marc, 1, 1)
    if recs == []:
        write_message("Error: Cannot parse MARCXML file.", verbose=1, stream=sys.stderr)
        write_message("Exiting.", sys.stderr)
        task_update_status("ERROR")                                   
        sys.exit(1)        
    elif recs[0][0] is None:
        write_message("Error: MARCXML file has wrong format: %s" % recs, verbose=1, stream=sys.stderr)
        write_message("Exiting.", sys.stderr)
        task_update_status("ERROR")                                   
        sys.exit(1)
    else:
        recs = map((lambda x:x[0]), recs)
        return recs
    
def find_record_format(rec_id, format):
    """Look whether record REC_ID is formatted in FORMAT,
       i.e. whether FORMAT exists in the bibfmt table for this record.
    
       Return the number of times it is formatted: 0 if not, 1 if yes,
       2 if found more than once (should never occur).
    """
    out = 0
    query = """SELECT COUNT(id) FROM bibfmt WHERE id_bibrec=%s AND format=%s"""
    params = (rec_id, format)
    res = []
    try:
        res = run_sql(query, params)
        out = res[0][0]
    except Error, error:
        write_message("   Error during find_record_format() : %s " % error, verbose=1, stream=sys.stderr) 
    return out

def find_record_bibfmt(marc):
    """ receives the xmlmarc containing a record and returns the id in bibrec if the record exists in bibfmt"""
    # compress the marc value
    pickled_marc =  MySQLdb.escape_string(compress(marc))
    query = """SELECT id_bibrec FROM bibfmt WHERE value = %s"""
    # format for marc xml is xm
    params = (pickled_marc,)
    try:
        res = run_sql(query, params)
    except Error, error:
        write_message("   Error during find_record_bibfmt function : %s " % error, verbose=1, stream=sys.stderr) 
    if len(res):
        return res
    else:
        return None

def find_record_from_recid(rec_id):
    """
    Try to find record in the database from the REC_ID number.
    Return record ID if found, None otherwise.
    """
    try:
        res = run_sql("SELECT id FROM bibrec WHERE id=%s",
                      (rec_id,))
    except Error, error:
        write_message("   Error during find_record_bibrec() : %s " % error,
                      verbose=1, stream=sys.stderr) 
    if res:
        return res[0][0]
    else:
        return None
        
def find_record_from_sysno(sysno):
    """
    Try to find record in the database from the external SYSNO number.
    Return record ID if found, None otherwise.
    """
    bibxxx = 'bib'+CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    try:
        res = run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
                                                 %(bibxxx)s AS b
                         WHERE b.tag=%%s AND b.value=%%s AND bb.id_bibxxx=b.id""" % \
                      {'bibxxx': bibxxx,
                       'bibrec_bibxxx': bibrec_bibxxx},
                      (CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, sysno,))
    except Error, error:
        write_message("   Error during find_record_from_sysno(): %s " % error,
                      verbose=1, stream=sys.stderr)     
    if res:
        return res[0][0]
    else:
        return None

def find_record_from_oaiid(oaiid):
    """
    Try to find record in the database from the OAI ID number.
    Return record ID if found, None otherwise.
    """
    bibxxx = 'bib'+CFG_OAI_ID_FIELD[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    try:
        res = run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
                                                 %(bibxxx)s AS b
                         WHERE b.tag=%%s AND b.value=%%s AND bb.id_bibxxx=b.id""" % \
                      {'bibxxx': bibxxx,
                       'bibrec_bibxxx': bibrec_bibxxx},
                      (CFG_OAI_ID_FIELD, oaiid,))
    except Error, error:
        write_message("   Error during find_record_from_oaiid(): %s " % error,
                      verbose=1, stream=sys.stderr)     
    if res:
        return res[0][0]
    else:
        return None

def extract_tag_from_record(record, tag_number):
    """ Extract the tag_number for record."""
    # first step verify if the record is not already in the database
    if record:
        return record.get(tag_number, None)
    return None
            
def retrieve_rec_id(record):
    """Retrieve the record Id from a record by using tag 001 or SYSNO or OAI ID tag."""

    rec_id = None
    
    # 1st step: we look for the tag 001
    tag_001 = extract_tag_from_record(record, '001')
    if tag_001 is not None:
        # We extract the record ID from the tag
        rec_id = tag_001[0][3]        
        # if we are in insert mode => error
        if options['mode'] == 'insert':
            write_message("   Failed : Error tag 001 found in the xml" \
                          " submitted, you should use the option replace," \
                          " correct or append to replace an existing" \
                          " record. (-h for help)",
                          verbose=1, stream=sys.stderr)
            return -1            
        else:
            # we found the rec id and we are not in insert mode => continue
            # we try to match rec_id against the database:
            if find_record_from_recid(rec_id) is not None:
                # okay, 001 corresponds to some known record
                return rec_id
            else:
                # The record doesn't exist yet. We shall have try to check
                # the SYSNO or OAI id later.                
                write_message("   -Tag 001 value not found in database.",
                              verbose=9)
                rec_id = None
    else:
        write_message("   -Tag 001 not found in the xml marc file.", verbose=9)

    if rec_id is None:
        # 2nd step we look for the SYSNO or OAIID
        sysnos = record_get_field_values(record,
                                         CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
                                         CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] != "_" and \
                                         CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] or "",
                                         CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] != "_" and \
                                         CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] or "",
                                         CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6])
        if sysnos:
            sysno = sysnos[0] # there should be only one external SYSNO
            write_message("   -Checking if SYSNO " + sysno + \
                          " exists in the database", verbose=9)
            # try to find the corresponding rec id from the database
            rec_id = find_record_from_sysno(sysno)
            if rec_id is not None:
                # rec_id found
                pass
            else:
                # The record doesn't exist yet. We will try to check
                # OAI id later.                
                write_message("   -Tag SYSNO value not found in database.",
                              verbose=9)
                rec_id = None
        else:
            write_message("   -Tag SYSNO not found in the xml marc file.", verbose=9)

    if rec_id is None:
        # 3rd step we look for the OAI ID
        oaiidvalues = record_get_field_values(record,
                                              CFG_OAI_ID_FIELD[0:3],
                                              CFG_OAI_ID_FIELD[3:4] != "_" and \
                                              CFG_OAI_ID_FIELD[3:4] or "",
                                              CFG_OAI_ID_FIELD[4:5] != "_" and \
                                              CFG_OAI_ID_FIELD[4:5] or "",
                                              CFG_OAI_ID_FIELD[5:6])
        if oaiidvalues:
            oaiid = oaiidvalues[0] # there should be only one OAI ID
            write_message("   -Check if the OAI ID " + oaiid + \
                          " exist in the database", verbose=9)
            
            # try to find the corresponding rec id from the database
            rec_id = find_record_from_oaiid(oaiid)
            if rec_id is not None:
                # rec_id found
                pass
            else:
                write_message("   -Tag OAI ID value not found in database.",
                              verbose=9)
                rec_id = None
        else:
            write_message("   -Tag SYSNO not found in the xml marc file.", verbose=9)

    # Now we should have detected rec_id from SYSNO or OAIID
    # tags.  (None otherwise.)  
    if rec_id:
        if options['mode'] == 'insert':
            write_message("   Failed : Record found in the database," \
                          " you should use the option replace," \
                          " correct or append to replace an existing" \
                          " record. (-h for help)",
                          verbose=1, stream=sys.stderr)
            return -1
    else:
        if options['mode'] != 'insert' and \
           options['mode'] != 'replace_or_insert':
            write_message("   Failed : Record not found in the database."\
                          " Please insert the file before updating it."\
                          " (-h for help)", verbose=1, stream=sys.stderr)
            return -1

    return rec_id

### Insert functions

def create_new_record():
    """Create new record in the database"""
    now = convert_datestruct_to_datetext(time.localtime())
    query = """INSERT INTO bibrec (creation_date, modification_date)
                VALUES (%s, %s)"""
    params = (now, now)
    try:
        rec_id = run_sql(query, params)
        return rec_id
    except Error, error:
        write_message("   Error during the creation_new_record function : %s " % error, verbose=1, stream=sys.stderr) 
    return None
    
def insert_bibfmt(id_bibrec, marc, format):
    """Insert the format in the table bibfmt"""
    # compress the marc value
    #pickled_marc =  MySQLdb.escape_string(compress(marc))
    pickled_marc =  compress(marc)
    # get the current time
    now = convert_datestruct_to_datetext(time.localtime())
    query = """INSERT INTO  bibfmt (id_bibrec, format, last_updated, value) VALUES (%s, %s, %s, %s)"""
    try:
        row_id  = run_sql(query, (id_bibrec, format, now, pickled_marc))
        return row_id
    except Error, error:
        write_message("   Error during the insert_bibfmt function : %s " % error, verbose=1, stream=sys.stderr) 
    return None

def insert_record_bibxxx(tag, value):
    """Insert the record into bibxxx"""
    # determine into which table one should insert the record
    table_name = 'bib'+tag[0:2]+'x'

    # check if the tag, value combination exists in the table
    query = """SELECT id FROM %s """ % table_name
    query += """ WHERE tag=%s AND value=%s"""
    params = (tag, value)
    try:
        res = run_sql(query, params)
    except Error, error:
        write_message("   Error during the insert_record_bibxxx function : %s " % error, verbose=1, stream=sys.stderr) 
    
    if len(res):
        # get the id of the row, if it exists
        row_id = res[0][0]
        return (table_name, row_id)
    else:
        # necessary to insert the tag, value into bibxxx table
        query = """INSERT INTO %s """ % table_name
        query += """ (tag, value) values (%s , %s)""" 
        params = (tag, value)
        try:
            row_id = run_sql(query, params)
        except Error, error:
            write_message("   Error during the insert_record_bibxxx function : %s " % error, verbose=1, stream=sys.stderr) 
        
        return (table_name, row_id)

def insert_record_bibrec_bibxxx(table_name, id_bibxxx, field_number, id_bibrec):
    """Insert the record into bibrec_bibxxx"""
    # determine into which table one should insert the record
    full_table_name = 'bibrec_'+ table_name

    # insert the proper row into the table
    query = """INSERT INTO %s """ % full_table_name
    query += """(id_bibrec,id_bibxxx, field_number) values (%s , %s, %s)"""
    params = (id_bibrec, id_bibxxx, field_number)
    try:
        res = run_sql(query, params)
    except Error, error:
        write_message("   Error during the insert_record_bibrec_bibxxx function 2nd query : %s " % error, verbose=1, stream=sys.stderr) 
    return res
    
def insert_fft_tags(record, rec_id):
    """Process and insert FFT tags"""
    tuple_list = None
    tuple_list = extract_tag_from_record(record, 'FFT')
    # If there is a FFT TAG :)
    if tuple_list is not None:
        for single_tuple in tuple_list:
            # Get the inside of the FFT file
            docpath = single_tuple[0][0][1]
            docname = re.sub("\..*", "", os.path.basename(docpath))
            extension = re.sub("^[^\.]*.", "", os.path.basename(docpath)).lower()
            # Create a new docId
            try:
                bib_doc_id = run_sql("insert into bibdoc (docname,creation_date,modification_date) values(%s,NOW(),NOW())", (docname,))
                write_message("   -Insert of the file %s into bibdoc : DONE" % docname, verbose=2)
            except Error, error:
                write_message("   Error during the insert_fft_tags function : %s " % error, verbose=1, stream=sys.stderr) 
            
            if bib_doc_id is not None:
                # we link the document to the record if a rec_id was specified
                if rec_id != "":
                    
                    # FIXME doc_type : main or additional, fron where the information come from?
                    doc_type = ""
                    try:
                        res = run_sql("insert into bibrec_bibdoc values(%s,%s,%s)", (rec_id, bib_doc_id, doc_type))
                        if res is None:
                            write_message("   Failed during creation of link between doc Id and rec Id).", verbose=1, stream=sys.stderr)
                        else:
                            write_message("   -Insert of the link bibrec bibdoc for %s : DONE" % docname, verbose=2)
                    except Error, error:
                        write_message("   Error during the insert_fft_tags function : %s " % error, verbose=1, stream=sys.stderr) 
            else:
                write_message("   Failed during creation of the new doc Id.", verbose=1, stream=sys.stderr)
            # Move the file to the correct place
            # Variables from the config file
            archivepath = filedir
            archivesize = filedirsize
            url_path = None

            group = "g"+str(int(int(bib_doc_id)/archivesize))
            basedir = "%s/%s/%s" % (archivepath, group, bib_doc_id)
            # we create the corresponding storage directory
            if not os.path.exists(basedir):
                try:
                    os.makedirs(basedir)
                    write_message("   -Create a new directory %s : DONE" % basedir, verbose=2)
                except OSError, error:
                    write_message("   Error making the directory : %s " % error, verbose=1, stream=sys.stderr) 
                    
            # and save the father record id if it exists
            if rec_id != "":
                try:
                    filep = open("%s/.recid" % basedir, "w")
                    filep.write(str(bib_doc_id))
                    filep.close()
                except IOError, error:
                    write_message("   Error writing the file : %s " % error, verbose=1, stream=sys.stderr) 
                # Move the file to the good directory
                try:
                    os.system("mv %s %s" % (docpath, basedir))
                    write_message("   -Move the file %s : DONE" % docname, verbose=2)
                except OSError, error:
                    write_message("   Error moving the file : %s " % error, verbose=1, stream=sys.stderr) 
                
                # Create the Url Path
                url_path = htdocsurl+"/record/"+str(rec_id)+"/files/"+docname+"."+extension
             
                # add tag 856 to the xml marc to proceed
                subfield_list = [('u', url_path), ('z', 'Access to Fulltext')] 
                newfield_number = record_add_field(record, "856", "4", "", "", subfield_list)
                if newfield_number is None:
                    write_message("   Error when adding the field"+ single_tuple, verbose=1, stream=sys.stderr)
                else:
                    write_message("   -Add the new tag 856 to the record for %s : DONE" % docname, verbose=2)
                
            # Delete FFT tag :)
            record_delete_field(record, 'FFT', '', '')
            write_message("   -Delete FFT tag from source : DONE", verbose=2)
    return record

def insert_fmt_tags(record, rec_id):
    """Process and insert FMT tags"""

    fmt_fields = record_get_field_instances(record, 'FMT')
    if fmt_fields:
        for fmt_field in fmt_fields:
            # Get the f, g subfields of the FMT tag
            try:
                f_value = field_get_subfield_values(fmt_field, "f")[0]
            except IndexError:
                f_value = ""
            try:
                g_value = field_get_subfield_values(fmt_field, "g")[0]            
            except IndexError:
                g_value = ""
            # Update the format
            res = update_bibfmt_format(rec_id, g_value, f_value)
            if res == 1:
                write_message("   Failed: Error during update_bibfmt", verbose=1, stream=sys.stderr)
                
        # If we are in format mode, we only care about the FMT tag
        if options['mode'] == 'format':
            return 0
        # We delete the FMT Tag of the record
        record_delete_field(record, 'FMT')
        write_message("   -Delete field FMT from record : DONE", verbose=2)
        return record

    elif options['mode'] == 'format':
        write_message("   Failed: Format updated failed : No tag FMT found", verbose=1, stream=sys.stderr)
        return None
    else:
        return record

    
### Update functions
    
def update_bibrec_modif_date(now, bibrec_id):
    """Update the date of the record in bibrec table """    
    query = """UPDATE bibrec SET modification_date=%s WHERE id=%s"""
    params = (now, bibrec_id)
    try:
        run_sql(query, params)
        write_message("   -Update record modification date : DONE" , verbose=2)
    except Error, error:
        write_message("   Error during update_bibrec_modif_date function : %s" % error,
                      verbose=1, stream=sys.stderr)

def update_bibfmt_format(id_bibrec, format_value, format_name):
    """Update the format in the table bibfmt"""

    # We check if the format is already in bibFmt
    nb_found = find_record_format(id_bibrec, format_name)
    
    if nb_found == 1:
        # Update the format
        # get the current time
        now = convert_datestruct_to_datetext(time.localtime())
        # compress the format_value value
        pickled_format_value =  compress(format_value)
        
        query = """UPDATE bibfmt SET last_updated=%s, value=%s WHERE id_bibrec=%s AND format=%s""" 
        params = (now, pickled_format_value, id_bibrec, format_name)
        try:
            row_id  = run_sql(query, params)
            if row_id is None:
                write_message("   Failed: Error during update_bibfmt_format function", verbose=1, stream=sys.stderr)
                return 1
            else:
                write_message("   -Update the format %s in bibfmt : DONE" % format_name , verbose=2)
                return 0
        except Error, error:
            write_message("   Error during the update_bibfmt_format function : %s " % error, verbose=1, stream=sys.stderr)     
       
    elif nb_found > 1:
        write_message("   Failed: Same format %s found several time in bibfmt for the same record." % format_name, verbose=1, stream=sys.stderr)
        return 1
    else:
        # Insert the format information in BibFMT
        res = insert_bibfmt(id_bibrec, format_value, format_name)
        if res is None:
            write_message("   Failed: Error during insert_bibfmt", verbose=1, stream=sys.stderr)
            return 1
        else:
            write_message("   -Insert the format %s in bibfmt : DONE" % format_name , verbose=2)
            return 0
    
def update_database_with_metadata(record, rec_id):
    """Update the database tables with the record and the record id given in parameter"""
    for tag in record.keys():
        # check if tag is not a special one:
        if tag not in CFG_BIBUPLOAD_SPECIAL_TAGS:
            # for each tag there is a list of tuples representing datafields
            tuple_list = record[tag]
            # this list should contain the elements of a full tag [tag, ind1, ind2, subfield_code]
            tag_list = []
            tag_list.append(tag)
            for single_tuple in tuple_list:
                # these are the contents of a single tuple
                subfield_list = single_tuple[0]
                ind1 = single_tuple[1]
                ind2 = single_tuple[2]
                # append the ind's to the full tag
                if ind1 == '' or ind1 == ' ':
                    tag_list.append('_')
                else:
                    tag_list.append(ind1)
                if ind2 == '' or ind2 == ' ':
                    tag_list.append('_')
                else:
                    tag_list.append(ind2)
                datafield_number = single_tuple[4]
                
                if tag in CFG_BIBUPLOAD_SPECIAL_TAGS:
                    # nothing to do for special tags (FFT, FMT)
                    pass
                elif tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS and tag != "001":
                    value = single_tuple[3]
                    # get the full tag
                    full_tag = ''.join(tag_list)
                    
                    # update the tables
                    write_message("   insertion of the tag "+full_tag+" with the value "+value, verbose=9)
                    # insert the tag and value into into bibxxx
                    (table_name, bibxxx_row_id) = insert_record_bibxxx(full_tag, value)
                    #print 'tname, bibrow', table_name, bibxxx_row_id;
                    if table_name is None or bibxxx_row_id is None:
                        write_message("   Failed : during insert_record_bibxxx", verbose=1, stream=sys.stderr)
                    # connect bibxxx and bibrec with the table bibrec_bibxxx
                    res = insert_record_bibrec_bibxxx(table_name, bibxxx_row_id, datafield_number, rec_id)
                    if res is None:
                        write_message("   Failed : during insert_record_bibrec_bibxxx", verbose=1, stream=sys.stderr)
                else:
                    # get the tag and value from the content of each subfield
                    for subfield in subfield_list:
                        subtag = subfield[0]
                        value = subfield[1]
                        tag_list.append(subtag)
                        # get the full tag
                        full_tag = ''.join(tag_list)
                        # update the tables
                        write_message("   insertion of the tag "+full_tag+" with the value "+value, verbose=9)
                        # insert the tag and value into into bibxxx
                        (table_name, bibxxx_row_id) = insert_record_bibxxx(full_tag, value)
                        if table_name is None or bibxxx_row_id is None:
                            write_message("   Failed : during insert_record_bibxxx", verbose=1, stream=sys.stderr)
                        # connect bibxxx and bibrec with the table bibrec_bibxxx
                        res = insert_record_bibrec_bibxxx(table_name, bibxxx_row_id, datafield_number, rec_id)
                        if res is None:
                            write_message("   Failed : during insert_record_bibrec_bibxxx", verbose=1, stream=sys.stderr)
                        # remove the subtag from the list
                        tag_list.pop()
                tag_list.pop()
                tag_list.pop()
            tag_list.pop()
    write_message("   -Update the database with metadata : DONE", verbose=2)

def append_new_tag_to_old_record(record, rec_old):
    """Append new tags to a old record"""
    if options['tag'] is not None:
        tag = options['tag']
        if tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
            if tag == '001':
                pass
            else:
                # if it is a controlfield,just access the value
                for single_tuple in record[tag]:
                    controlfield_value = single_tuple[3]
                    # add the field to the old record
                    newfield_number = record_add_field(rec_old, tag, "", "", controlfield_value)
                    if newfield_number is None:
                        write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
        else:
            # For each tag there is a list of tuples representing datafields
            for single_tuple in record[tag]: 
                # We retrieve the information of the tag
                subfield_list = single_tuple[0]
                ind1 = single_tuple[1]
                ind2 = single_tuple[2]
                # We add the datafield to the old record
                if options['verbose'] == 9:
                    print "      Adding tag: ", tag, " ind1=", ind1, " ind2=", ind2, " code=", subfield_list
                newfield_number = record_add_field(rec_old, tag, ind1, ind2, "", subfield_list)
                if newfield_number is None:
                    write_message("Error when adding the field"+tag, verbose=1, stream=sys.stderr)
    else:
        # Go through each tag in the appended record
        for tag in record.keys():
            # Reference mode append only reference tag
            if options['mode'] == 'reference':
                if tag == CFG_BIBUPLOAD_REFERENCE_TAG:
                    for single_tuple in record[tag]: 
                        # We retrieve the information of the tag
                        subfield_list = single_tuple[0]
                        ind1 = single_tuple[1]
                        ind2 = single_tuple[2]
                        # We add the datafield to the old record
                        if options['verbose'] == 9:
                            print "      Adding tag: ", tag, " ind1=", ind1, " ind2=", ind2, " code=", subfield_list
                        newfield_number = record_add_field(rec_old, tag, ind1, ind2, "", subfield_list)
                        if newfield_number is None:
                            write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
            else:
                if tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
                    if tag == '001':
                        pass
                    else:
                        # if it is a controlfield,just access the value
                        for single_tuple in record[tag]:
                            controlfield_value = single_tuple[3]
                            # add the field to the old record
                            newfield_number = record_add_field(rec_old, tag, "", "", controlfield_value)
                            if newfield_number is None:
                                write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
                else:
                    # For each tag there is a list of tuples representing datafields
                    for single_tuple in record[tag]: 
                        # We retrieve the information of the tag
                        subfield_list = single_tuple[0]
                        ind1 = single_tuple[1]
                        ind2 = single_tuple[2]
                        # We add the datafield to the old record
                        if options['verbose'] == 9:
                            print "      Adding tag: ", tag, " ind1=", ind1, " ind2=", ind2, " code=", subfield_list
                        newfield_number = record_add_field(rec_old, tag, ind1, ind2, "", subfield_list)
                        if newfield_number is None:
                            write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
    return rec_old

def update_fft_tag(record, rec_id):
    """Process and Update FFT tags"""
    
    # FIXME: SELECT THE BIBDOC ID TO DELETE AND FIRST INSERT THE NEW
    # FFT TAGS BEFORE DELETING THE OLD ONE
    
    # We delete the bibdoc corresponding to this record
    delete_bibdoc(rec_id)
    
    # We delete the links between bibrec and bibdoc
    delete_bibrec_bibdoc(rec_id)
    
    # We delete the tag 856 from the record
    record_delete_field(record, '856', '4')

    # We add the new fft tags
    record = insert_fft_tags(record, rec_id)
    
    return record
    
    
### Delete functions

def delete_tags_to_correct(record, rec_old):
    """
    Delete tags from REC_OLD which are also existing in RECORD.  When
    deleting, pay attention not only to tags, but also to indicators,
    so that fields with the same tags but different indicators are not
    deleted.
    """
    # browse through all the tags from the MARCXML file:
    for tag in record.keys():
        # do we have to delete only a special tag or any tag?
        if options['tag'] is None or options['tag'] == tag:
            # check if the tag exists in the old record too:
            if rec_old.has_key(tag) and tag != '001':
                # the tag does exist, so delete all record's tag+ind1+ind2 combinations from rec_old
                for dummy_sf_vals, ind1, ind2, dummy_cf, dummy_field_number in record[tag]:
                    write_message("      Delete tag: " + tag + " ind1=" + ind1 + " ind2=" + ind2, verbose=9)
                    record_delete_field(rec_old, tag, ind1, ind2)

def delete_bibrec_bibxxx(record, id_bibrec):
    """Delete the database record from the table bibxxx given in parameters"""
    # we clear all the rows from bibrec_bibxxx from the old record 
    for tag in record.keys():
        if tag not in CFG_BIBUPLOAD_SPECIAL_TAGS:        
            # for each name construct the bibrec_bibxxx table name
            table_name = 'bibrec_bib'+tag[0:2]+'x'
            # delete all the records with proper id_bibrec
            query = """DELETE FROM `%s` where id_bibrec = %s"""
            params = (table_name, id_bibrec)
            try:
                run_sql(query % params)
            except Error, error:
                write_message("   Error during the delete_bibrec_bibxxx function : %s " % error, verbose=1, stream=sys.stderr) 

def wipe_out_record_from_all_tables(recid):
    """
    Wipe out completely the record and all its traces of RECID from
    the database (bibrec, bibrec_bibxxx, bibxxx, bibfmt).  Useful for
    the time being for test cases.
    """
    # delete from bibrec:
    run_sql("DELETE FROM bibrec WHERE id=%s", (recid,))
    # delete from bibrec_bibxxx:
    for i in range(0,10):
        for j in range(0, 10):
            run_sql("DELETE FROM %(bibrec_bibxxx)s WHERE id_bibrec=%%s" % \
                    {'bibrec_bibxxx': "bibrec_bib%i%ix" % (i, j)},
                    (recid,))
    # delete all unused bibxxx values:
    for i in range(0,10):
        for j in range(0, 10):
            run_sql("DELETE %(bibxxx)s FROM %(bibxxx)s " \
                    " LEFT JOIN %(bibrec_bibxxx)s " \
                    " ON %(bibxxx)s.id=%(bibrec_bibxxx)s.id_bibxxx " \
                    " WHERE %(bibrec_bibxxx)s.id_bibrec IS NULL" % \
                    {'bibxxx': "bib%i%ix" % (i, j),
                     'bibrec_bibxxx': "bibrec_bib%i%ix" % (i, j)})
    # delete from bibfmt:
    run_sql("DELETE FROM bibfmt WHERE id_bibrec=%s", (recid,))
    # delete from bibrec_bibdoc:
    run_sql("DELETE FROM bibrec_bibdoc WHERE id_bibrec=%s", (recid,))
    return

def delete_bibdoc(id_bibrec):
    """Delete document from bibdoc which correspond to the bibrec id given in parameter"""
    query = """UPDATE bibdoc SET status='deleted' WHERE id IN (SELECT id_bibdoc FROM bibrec_bibdoc WHERE id_bibrec=%s)"""
    params = (id_bibrec,)
    try:
        run_sql(query, params)
    except Error, error:
        write_message("   Error during the delete_bibdoc function : %s " % error, verbose=1, stream=sys.stderr) 

def delete_bibrec_bibdoc(id_bibrec):
    """Delete the bibrec record from the table bibrec_bibdoc given in parameter"""
    # delete all the records with proper id_bibrec
    query = """DELETE FROM bibrec_bibdoc WHERE id_bibrec=%s"""
    params = (id_bibrec,)
    try:
        run_sql(query, params)
    except Error, error:
        write_message("   Error during the delete_bibrec_bibdoc function : %s " % error, verbose=1, stream=sys.stderr) 

def main():
    """main entry point for bibupload"""
    global options
    ## parse command line:
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        ## A - run the task
        task_id = int(sys.argv[1])
        try:
            if not task_run(task_id):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except StandardError, erro:
            write_message("Unexpected error occurred: %s." % erro, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")                                   
    else:
        ## B - submit the task
        # set default values:
        options["runtime"] = time.strftime("%Y-%m-%d %H:%M:%S") 
        options["sleeptime"] = ""
        # set user-defined options:
        error = parse_command()
        if error == 0:
            task_submit()
        else:
            sys.exit(1)
    return

if __name__ == "__main__":
    main()
