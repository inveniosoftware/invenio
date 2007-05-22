# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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
oaiharvest implementation.  See oaiharvest executable for entry point.
"""

__revision__ = "$Id$"

import marshal
import getopt
import getpass
import string
import os
import re
import sys
import time
import signal
import traceback
import calendar
import shutil

from invenio.config import \
     bibconvert, \
     bibupload, \
     bindir, \
     tmpdir, \
     version
from invenio.bibindex_engine_config import *
from invenio.dbquery import run_sql, escape_string
from invenio.access_control_engine import acc_authorize_action

options = {} # global variable to hold task options

## precompile some often-used regexp for speed reasons:
re_subfields = re.compile('\$\$\w');
re_html = re.compile("(?s)<[^>]*>|&#?\w+;")
re_datetime_shift = re.compile("([-\+]{0,1})([\d]+)([dhms])")

tmpHARVESTpath = tmpdir + '/oaiharvest'

def write_message(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr)."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
        try:
            stream.write("%s\n" % msg)
        except UnicodeEncodeError:
            stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    return

def usage(code, msg=''):
    "Prints usage for this module."
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    usagetext = """ Usage: oaiharvest [options]
     Examples:
      oaiharvest -r arxiv -s 24h
      oaiharvest -r pubmed -d 2005-05-05:2005-05-10 -t 10m

 Specific options:
 -r, --repository=REPOS_ONE,"REPOS TWO"     name of the OAI repositories to be harvested (default=all)
 -d, --dates=yyyy-mm-dd:yyyy-mm-dd          harvest repositories between specified dates (overrides repositories' last updated timestamps)

 Scheduling options:
 -u,  --user=USER          user name to store task, password needed
 -s,  --sleeptime=SLEEP    time after which to repeat tasks (no)
                           e.g.: 1s, 30m, 24h, 7d
 -t,  --time=TIME          moment for the task to be active (now)
                           e.g.: +15s, 5m, 3h , 2002-10-27 13:57:26

 General options:
 -h,  --help               print this help and exit
 -V,  --version            print version and exit
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)
    """
    sys.stderr.write(usagetext)
    sys.exit(code)

def authenticate(user, header="oaiharvest Task Submission", action="runoaiharvest"):
    """Authenticate the user against the user database.
       Check for its password, if it exists.
       Check for action access rights.
       Return user name upon authorization success,
       do system exit upon authorization failure.
       """
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

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = re_datetime_shift.match(var)
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

def get_nb_records_in_file(filename):
    """
    Return number of record in FILENAME that is either harvested or converted file.
    Useful for statistics.
    """
    try:
        nb = open(filename, 'r').read().count("</record>")
    except IOError:
        nb = 0 # file not exists and such
    except:
        nb = -1
    return nb

def task_run(row):
    """Run the harvesting task.  The row argument is the Bibharvest task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    global options

    reposlist = []
    datelist = []
    dateflag = 0

    # read from SQL row:
    task_id = row[0]
    task_proc = row[1]
    options = marshal.loads(row[6])
    task_status = row[7]

    # sanity check:
    if task_proc != "oaiharvest":
        write_message("The task #%d does not seem to be a oaiharvest task." % task_id, sys.stderr)
        return 0
    if task_status != "WAITING":
        write_message("The task #%d is %s.  I expected WAITING." % (task_id, task_status), sys.stderr)
        return 0

    # we can run the task now:
    if options["verbose"]:
        write_message("Task #%d started." % task_id)
    task_starting_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    task_update_status("RUNNING")

    # install signal handlers
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)

    ### go ahead: build up the reposlist
    if options["repository"] is not None:
        ### user requests harvesting from selected repositories
        write_message("harvesting from selected repositories")
        for reposname in options["repository"]:
            row = get_row_from_reposname(reposname)
            if row==[]:
                write_message("source name " + reposname + " is not valid")
                continue
            else:
                reposlist.append(get_row_from_reposname(reposname))
    else:
        ### user requests harvesting from all repositories
        write_message("harvesting from all repositories in the database")
        reposlist = get_all_rows_from_db()

    ### go ahead: check if user requested from-until harvesting
    if options["dates"]:
        ### for each repos simply perform a from-until date harvesting... no need to update anything
        dateflag = 1
        for element in options["dates"]:
            datelist.append(element)

    error_happened_p = False
    for repos in reposlist:
        postmode = str(repos[0][9])
        setspecs = str(repos[0][10])
        harvested_files = []

        if postmode == "h" or postmode == "h-c" or \
               postmode == "h-u" or postmode == "h-c-u" or \
               postmode == "h-c-f-u":
            harvestpath = tmpdir + "/oaiharvest" + str(os.getpid())
            harvest_dir, harvest_filename = os.path.split(harvestpath)

            if dateflag == 1:
                res = call_bibharvest(prefix=repos[0][2],
                                      baseurl=repos[0][1],
                                      harvestpath=harvestpath,
                                      fro=str(datelist[0]),
                                      until=str(datelist[1]),
                                      setspecs=setspecs)
                if res[0] == 1 :
                    write_message("source " + str(repos[0][6]) + \
                                  " was harvested from " + str(datelist[0]) \
                                  + " to " + str(datelist[1]))
                    harvested_files = res[1]
                else:
                    write_message("an error occurred while harvesting from source " + \
                                  str(repos[0][6]) + " for the dates chosen")
                    error_happened_p = True
                    continue

            elif dateflag != 1 and repos[0][7] is None and repos[0][8] != 0:
                write_message("source " + str(repos[0][6]) + \
                              " was never harvested before - harvesting whole repository")
                res = call_bibharvest(prefix=repos[0][2],
                                      baseurl=repos[0][1],
                                      harvestpath=harvestpath,
                                      setspecs=setspecs)
                if res[0] == 1 :
                    update_lastrun(repos[0][0])
                    harvested_files = res[1]
                else :
                    write_message("an error occurred while harvesting from source " + str(repos[0][6]))
                    error_happened_p = True
                    continue

            elif dateflag != 1 and repos[0][8] != 0:
                ### check that update is actually needed, i.e. lastrun+frequency>today
                timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                lastrundate = re.sub(r'\.[0-9]+$', '', str(repos[0][7]))        # remove trailing .00
                timeinsec = int(repos[0][8])*60*60
                updatedue = add_timestamp_and_timelag(lastrundate, timeinsec)
                proceed = compare_timestamps_with_tolerance(updatedue, timenow)
                if proceed == 0 or proceed == -1 : #update needed!
                    write_message("source " + str(repos[0][6]) + " is going to be updated")
                    fromdate = str(repos[0][7])
                    fromdate = fromdate.split()[0] # get rid of time of the day for the moment
                    res = call_bibharvest(prefix=repos[0][2],
                                          baseurl=repos[0][1],
                                          harvestpath=harvestpath,
                                          fro=fromdate,
                                          setspecs=setspecs)
                    if res[0] == 1 :
                        update_lastrun(repos[0][0])
                        harvested_files = res[1]
                    else :
                        write_message("an error occurred while harvesting from source " + str(repos[0][6]))
                        error_happened_p = True
                        continue
                else:
                    write_message("source " + str(repos[0][6]) + " does not need updating")
                    continue

            elif dateflag != 1 and repos[0][8] == 0:
                write_message("source " + str(repos[0][6]) +
                              " has frequency set to 'Never' so it will not be updated")
                continue

            # print stats:
            for harvested_file in harvested_files:
                write_message("File %s contains %i records." % \
                              (harvested_file,
                               get_nb_records_in_file(harvested_file)))

        if postmode == "h-u":
            res = 0
            for harvested_file in harvested_files:
                res += call_bibupload(harvested_file)
                if res == 0:
                    write_message("material harvested from source " + str(repos[0][6]) +
                                  " was successfully uploaded")
                else:
                    write_message("an error occurred while uploading harvest from " + str(repos[0][6]))
                    error_happened_p = True
                    continue

        if postmode == "h-c" or postmode == "h-c-u" or postmode == "h-c-f-u":
            convert_dir = tmpdir
            convertpath = convert_dir + os.sep +"bibconvertrun" + str(os.getpid())
            converted_files = []
            i = 0
            for harvested_file in harvested_files:
                converted_file = convertpath+".%07d" % i
                converted_files.append(converted_file)
                res = call_bibconvert(config=str(repos[0][5]),
                                      harvestpath=harvested_file,
                                      convertpath=converted_file)
                i += 1

                if res == 0:
                    write_message("material harvested from source " + str(repos[0][6]) +
                                  " was successfully converted")
                else:
                    write_message("an error occurred while converting from " + str(repos[0][6]))
                    error_happened_p = True
                    continue

            # print stats:
            for converted_file in converted_files:
                write_message("File %s contains %i records." % \
                              (converted_file,
                               get_nb_records_in_file(converted_file)))

        if postmode == "h-c-u":
            res = 0
            for converted_file in converted_files:
                res += call_bibupload(converted_file)
            if res == 0:
                write_message("material harvested from source " + str(repos[0][6]) +
                              " was successfully uploaded")
            else:
                write_message("an error occurred while uploading harvest from " + str(repos[0][6]))
                error_happened_p = True
                continue

        elif postmode == "h-c-f-u":
            # first call bibfilter:
            res = 0
            for converted_file in converted_files:
                res += call_bibfilter(str(repos[0][11]), converted_file)
            if res == 0:
                write_message("material harvested from source " + str(repos[0][6]) +
                              " was successfully bibfiltered")
            else:
                write_message("an error occurred while uploading harvest from " + str(repos[0][6]))
                error_happened_p = True
                continue
            # print stats:
            for converted_file in converted_files:
                write_message("File %s contains %i records." % \
                              (converted_file + ".insert.xml",
                               get_nb_records_in_file(converted_file + ".insert.xml")))
                write_message("File %s contains %i records." % \
                              (converted_file + ".correct.xml",
                               get_nb_records_in_file(converted_file + ".correct.xml")))
            # only then call upload:
            for converted_file in converted_files:
                res += call_bibupload(converted_file + ".insert.xml", "-i")
                res += call_bibupload(converted_file + ".correct.xml", "-c")
            if res == 0:
                write_message("material harvested from source " + str(repos[0][6]) +
                              " was successfully uploaded")
            else:
                write_message("an error occurred while uploading harvest from " + str(repos[0][6]))
                error_happened_p = True
                continue

        elif postmode not in ["h", "h-c", "h-u", "h-c-u", "h-c-f-u"]: ### this should not happen
            write_message("invalid postprocess mode: " + postmode + " skipping repository")
            error_happened_p = True
            continue

    if error_happened_p:
        task_update_status("DONE WITH ERRORS")
    else:
        task_update_status("DONE")
    if options["verbose"]:
        write_message("Task #%d finished." % task_id)
    return 1


def add_timestamp_and_timelag(timestamp,
                              timelag):
    """ Adds a time lag in seconds to a given date (timestamp). Returns the resulting date. """
    # remove any trailing .00 in timestamp:
    timestamp = re.sub(r'\.[0-9]+$', '', timestamp)
    # first convert timestamp to Unix epoch seconds:
    timestamp_seconds = calendar.timegm(time.strptime(timestamp, "%Y-%m-%d %H:%M:%S"))
    # now add them:
    result_seconds = timestamp_seconds + timelag
    result = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(result_seconds))
    return result

def update_lastrun(index):
    """ A method that updates the lastrun of a repository successfully harvested """
    try:
        today = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = 'UPDATE oaiHARVEST SET lastrun="%s" WHERE id=%s' % (today, index)
        res = run_sql(sql)
        return 1
    except StandardError, e:
        return (0,e)

def call_bibharvest(prefix, baseurl, harvestpath, fro="", until="", setspecs=""):
    """ A method that calls bibharvest and writes harvested output to disk """
    try:
        command = '%s/bibharvest -o %s -v ListRecords -p %s ' % (bindir,
                                                                 harvestpath,
                                                                 prefix)

        if fro != "":
            command += '-f %s ' % fro
        if until!="":
            command += '-u %s ' % until
        if setspecs!="":
            command += '-s "%s" ' % setspecs
        command += baseurl

	print "Start harvesting"
	#print command
        ret = os.system(command)
	#print "Harvesting finished, merging files"
	harvest_dir, harvest_filename = os.path.split(harvestpath)
	#print "get files"
	files = os.listdir(harvest_dir)
	#print "sort file"
	files.sort()
        harvested_files = [harvest_dir + os.sep + filename for \
                           filename in files \
                           if filename.startswith(harvest_filename)]
	#print "open dest file"
	## hf = file(harvestpath, 'w')
## 	for f in files:
## 	    if f.startswith(filename)
## 	        print "processing file %s"%f
## 	        rf = file(os.path.join(harvestdir, f), 'r')
## 	        hf.write(rf.read())
## 		hf.write("\n")
## 	        rf.close()
## 	        #os.remove(os.path.join(harvestdir, f))
## 	hf.close()
## 	print "Files merged"
        return (1, harvested_files)
    except StandardError, e:
        print e
        return (0,e)

def call_bibconvert(config, harvestpath, convertpath):
    """ A method that reads from a file and converts according to a BibConvert Configuration file. Converted output is returned """
    command = """%s/bibconvert -c %s < %s > %s """ % (bindir, config, harvestpath, convertpath)
    stdout = os.popen(command)
    return 0

def call_bibupload(marcxmlfile, mode="-r -i"):
    """Call bibupload in insert mode on MARCXMLFILE."""
    if os.path.exists(marcxmlfile):
        command = '%s/bibupload %s %s ' % (bindir, mode, marcxmlfile)
        return os.system(command)
    else:
        write_message("marcxmlfile %s does not exist" % marcxmlfile)
        return 1

def call_bibfilter(bibfilterprogram, marcxmlfile):
    """
    Call bibfilter program BIBFILTERPROGRAM on MARCXMLFILE that is a
    MARCXML file usually obtained after harvest and convert steps.

    The bibfilter should produce two files called MARCXMLFILE.insert.xml
    and MARCXMLFILE.correct.xml, the first file containing parts of
    MARCXML to be uploaded in insert mode and the second file part of
    MARCXML to be uploaded in correct mode.

    Return 0 if everything went okay, 1 otherwise.
    """
    if bibfilterprogram:
        if not os.path.isfile(bibfilterprogram):
            write_message("bibfilterprogram %s is not a file" % bibfilterprogram)
            return 1
        elif not os.path.isfile(marcxmlfile):
            write_message("marcxmlfile %s is not a file" % marcxmlfile)
            return 1
        else:
            return os.system('%s %s' % (bibfilterprogram, marcxmlfile))
            return 0
    else:
        try:
            write_message("no bibfilterprogram defined, copying %s only" % marcxmlfile)
            shutil.copy(marcxmlfile, marcxmlfile + ".insert.xml")
            return 0
        except:
            write_message("cannot copy %s into %s.insert.xml" % marcxmlfile)
            return 1

def get_row_from_reposname(reposname):
    """ Returns all information about a row (OAI source) from the source name """
    try:
        sql = """SELECT id, baseurl, metadataprefix, arguments,
                        comment, bibconvertcfgfile, name, lastrun,
                        frequency, postprocess, setspecs,
                        bibfilterprogram
                   FROM oaiHARVEST WHERE name=%s"""
        res = run_sql(sql, (reposname,))
        reposdata = []
        for element in res:
            reposdata.append(element)
        return reposdata
    except StandardError, e:
        return (0,e)

def get_all_rows_from_db():
    """ This method retrieves the full database of repositories and returns a list containing (in exact order):
    | id | baseurl | metadataprefix | arguments | comment | bibconvertcfgfile | name   | lastrun | frequency | postprocess | setspecs | bibfilterprogram
    """
    try:
        reposlist = []
        sql = """SELECT id FROM oaiHARVEST"""
        idlist = run_sql(sql)
        for index in idlist:
            sql = """SELECT id, baseurl, metadataprefix, arguments,
                            comment, bibconvertcfgfile, name, lastrun,
                            frequency, postprocess, setspecs,
                            bibfilterprogram
                     FROM oaiHARVEST WHERE id=%s""" % index

            reposelements = run_sql(sql)
            repos = []
            for element in reposelements:
                repos.append(element)
            reposlist.append(repos)
        return reposlist
    except StandardError, e:
        return (0,e)

def compare_timestamps_with_tolerance(timestamp1,
                                      timestamp2,
                                      tolerance=0):
    """Compare two timestamps TIMESTAMP1 and TIMESTAMP2, of the form
       '2005-03-31 17:37:26'. Optionally receives a TOLERANCE argument
       (in seconds).  Return -1 if TIMESTAMP1 is less than TIMESTAMP2
       minus TOLERANCE, 0 if they are equal within TOLERANCE limit,
       and 1 if TIMESTAMP1 is greater than TIMESTAMP2 plus TOLERANCE.
    """
    # remove any trailing .00 in timestamps:
    timestamp1 = re.sub(r'\.[0-9]+$', '', timestamp1)
    timestamp2 = re.sub(r'\.[0-9]+$', '', timestamp2)
    # first convert timestamps to Unix epoch seconds:
    timestamp1_seconds = calendar.timegm(time.strptime(timestamp1, "%Y-%m-%d %H:%M:%S"))
    timestamp2_seconds = calendar.timegm(time.strptime(timestamp2, "%Y-%m-%d %H:%M:%S"))
    # now compare them:
    if timestamp1_seconds < timestamp2_seconds - tolerance:
        return -1
    elif timestamp1_seconds > timestamp2_seconds + tolerance:
        return 1
    else:
        return 0

def command_line():
    global options
    long_flags =["repository=", "dates="
                 "user=","sleeptime=","time=",
                 "help", "version", "verbose="]
    short_flags ="r:d:u:s:t:hVv:l"
    format_string = "%Y-%m-%d %H:%M:%S"
    repositories = None
    dates = None
    sleeptime = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], short_flags, long_flags)
    except getopt.GetoptError, err:
        write_message(err, sys.stderr)
        usage(1)
    if args:
        usage(1)

    options={"sleeptime":0, "verbose":1, "repository":0, "dates":0}
    sched_time = time.strftime(format_string)

    user = ""
    # Check for key options

    try:
        for opt in opts:
            if opt == ("-h","")  or opt == ("--help",""):
                usage(1)
            elif opt == ("-V","")  or opt == ("--version",""):
                print __revision__
                sys.exit(1)
            elif opt[0] in ["--verbose", "-v"]:
                options["verbose"] = int(opt[1])
            elif opt[0] in [ "-r", "--repository" ]:
                repositories = opt[1]
            elif opt[0] in [ "-d", "--dates" ]:
                dates = opt[1]
            elif opt[0] in [ "-u", "--user"]:
                user = opt[1]
            elif opt[0] in [ "-s", "--sleeptime" ]:
                get_datetime(opt[1])    # see if it is a valid shift
                sleeptime= opt[1]
            elif opt[0] in [ "-t", "--time" ]:
                sched_time= get_datetime(opt[1])
            else: usage(1)
    except StandardError, e:
        write_message(e, sys.stderr)
        sys.exit(1)

    options["repository"] = get_repository_names(repositories)
    if dates is not None:
        options["dates"]=get_dates(dates)
    if dates is not None and options["dates"] is None:
        write_message("Date format not valid. Quitting task...")
        sys.exit(1)

    user = authenticate(user)

    if options["verbose"] >= 9:
        print ""
        write_message("storing task options %s\n" % options)

    ## sanity check: remove eventual "task" option:
    if options.has_key("task"):
        del options["task"]

    new_task_id = run_sql("""INSERT INTO schTASK (proc,user,runtime,sleeptime,arguments,status)
                             VALUES ('oaiharvest',%s,%s,%s,%s,'WAITING')""",
                      (user, sched_time, sleeptime, marshal.dumps(options)))

    ## update task number:
    options["task"] = new_task_id
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(options), new_task_id))

    print "Task #%d was successfully scheduled for execution." % new_task_id
    return

def get_dates(dates):
    """ A method to validate and process the dates input by the user at the command line """
    twodates = []
    if dates:
        datestring = string.split(dates, ":")
        if len(datestring)==2:
            for date in datestring:
                ### perform some checks on the date format
                datechunks = string.split(date, "-")
                if len(datechunks)==3:
                    try:
                        if int(datechunks[0]) and int(datechunks[1]) and int(datechunks[2]):
                            twodates.append(date)
                    except StandardError:
                        write_message("Dates have invalid format, not 'yyyy-mm-dd:yyyy-mm-dd'")
                        twodates=None
                        return twodates
                else:
                    write_message("Dates have invalid format, not 'yyyy-mm-dd:yyyy-mm-dd'")
                    twodates=None
                    return twodates
            ## final check.. date1 must me smaller than date2
            date1 = str(twodates[0]) + " 01:00:00"
            date2 = str(twodates[1]) + " 01:00:00"
            if compare_timestamps_with_tolerance(date1, date2)!=-1:
                write_message("First date must be before second date.")
                twodates=None
                return twodates
        else:
            write_message("Dates have invalid format, not 'yyyy-mm-dd:yyyy-mm-dd'")
            twodates=None
    else:
        twodates=None
    return twodates


def get_repository_names(repositories):
    """ A method to validate and process the repository names input by the user at the command line """
    repository_names = []
    if repositories:
        names = string.split(repositories, ",")
        for name in names:
            ### take into account both single word names and multiple word names (which get wrapped around "" or '')
            quote = "'"
            doublequote = '"'
            if name.find(quote)==0 and name.find(quote)==len(name):
                name = name.split(quote)[1]
            if name.find(doublequote)==0 and name.find(doublequote)==len(name):
                name = name.split(doublequote)[1]
            repository_names.append(name)
    else:
        repository_names=None
    return repository_names

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
    pass
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
    global options
    if options["verbose"] >= 9:
        write_message("Updating task progress to %s." % msg)
    return run_sql("UPDATE schTASK SET progress=%s where id=%s", (msg, options["task"]))

def task_update_status(val):
    """Updates state information in the BibSched task table."""
    global options
    if options["verbose"] >= 9:
        write_message("Updating task status to %s." % val)
    return run_sql("UPDATE schTASK SET status=%s where id=%s", (val, options["task"]))

def main():
    """Reads arguments and either runs the task, or starts user-interface (command line)."""
    if len(sys.argv) == 2:
        try:
            task_id = int(sys.argv[1])
        except StandardError:
            command_line()
            sys.exit()

        res = run_sql("SELECT * FROM schTASK WHERE id='%d'" % (task_id), None, 1)
        if not res:
            write_message("Selected task not found.", sys.stderr)
            sys.exit(1)
        try:
            if not task_run(res[0]):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except StandardError, e:
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            if options["verbose"] >= 9:
                traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.")
            task_update_status("ERROR")
    else:
        command_line()

