# -*- coding: utf-8 -*-
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

"""
oaiharvest implementation.  See oaiharvest executable for entry point.
"""

__revision__ = "$Id$"

import os
import re
import time
import calendar
import shutil

from invenio.config import \
     CFG_BINDIR, \
     CFG_TMPDIR
from invenio.dbquery import run_sql
from invenio.bibtask import \
     task_get_option, \
     task_set_option, \
     write_message, \
     task_update_status, \
     task_init, \
     task_sleep_now_if_required, \
     task_update_progress

## precompile some often-used regexp for speed reasons:
re_subfields = re.compile('\$\$\w')
re_html = re.compile("(?s)<[^>]*>|&#?\w+;")
re_datetime_shift = re.compile("([-\+]{0, 1})([\d]+)([dhms])")

tmpHARVESTpath = CFG_TMPDIR + '/oaiharvest'

def get_nb_records_in_file(filename):
    """
    Return number of record in FILENAME that is either harvested or converted
    file. Useful for statistics.
    """
    try:
        nb = open(filename, 'r').read().count("</record>")
    except IOError:
        nb = 0 # file not exists and such
    except:
        nb = -1
    return nb

def task_run_core():
    """Run the harvesting task.  The row argument is the Bibharvest task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    reposlist = []
    datelist = []
    dateflag = 0

    ### go ahead: build up the reposlist
    if task_get_option("repository") is not None:
        ### user requests harvesting from selected repositories
        write_message("harvesting from selected repositories")
        for reposname in task_get_option("repository"):
            row = get_row_from_reposname(reposname)
            if row == []:
                write_message("source name " + reposname + " is not valid")
                continue
            else:
                reposlist.append(get_row_from_reposname(reposname))
    else:
        ### user requests harvesting from all repositories
        write_message("harvesting from all repositories in the database")
        reposlist = get_all_rows_from_db()

    ### go ahead: check if user requested from-until harvesting
    if task_get_option("dates"):
        ### for each repos simply perform a from-until date harvesting...
        ### no need to update anything
        dateflag = 1
        for element in task_get_option("dates"):
            datelist.append(element)

    error_happened_p = False
    j = 0
    for repos in reposlist:
        j += 1
        task_sleep_now_if_required()
        postmode = str(repos[0][9])
        setspecs = str(repos[0][10])
        harvested_files = []

        if postmode == "h" or postmode == "h-c" or \
               postmode == "h-u" or postmode == "h-c-u" or \
               postmode == "h-c-f-u":
            harvestpath = CFG_TMPDIR + "/oaiharvest" + str(os.getpid())

            if dateflag == 1:
                task_update_progress("Harvesting %s from %s to %s (%i/%i)" % \
                                     (str(repos[0][6]),\
                                      str(datelist[0]),
                                      str(datelist[1]),
                                      j, \
                                      len(reposlist)))
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
                    write_message("an error occurred while harvesting "
                        "from source " +
                        str(repos[0][6]) + " for the dates chosen")
                    error_happened_p = True
                    continue

            elif dateflag != 1 and repos[0][7] is None and repos[0][8] != 0:
                write_message("source " + str(repos[0][6]) + \
                              " was never harvested before - harvesting whole "
                              "repository")
                task_update_progress("Harvesting %s (%i/%i)" % \
                                     (str(repos[0][6]),
                                      j, \
                                      len(reposlist)))
                res = call_bibharvest(prefix=repos[0][2],
                                      baseurl=repos[0][1],
                                      harvestpath=harvestpath,
                                      setspecs=setspecs)
                if res[0] == 1 :
                    update_lastrun(repos[0][0])
                    harvested_files = res[1]
                else :
                    write_message("an error occurred while harvesting from "
                        "source " + str(repos[0][6]))
                    error_happened_p = True
                    continue

            elif dateflag != 1 and repos[0][8] != 0:
                ### check that update is actually needed,
                ### i.e. lastrun+frequency>today
                timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                lastrundate = re.sub(r'\.[0-9]+$', '',
                    str(repos[0][7])) # remove trailing .00
                timeinsec = int(repos[0][8])*60*60
                updatedue = add_timestamp_and_timelag(lastrundate, timeinsec)
                proceed = compare_timestamps_with_tolerance(updatedue, timenow)
                if proceed == 0 or proceed == -1 : #update needed!
                    write_message("source " + str(repos[0][6]) +
                        " is going to be updated")
                    fromdate = str(repos[0][7])
                    fromdate = fromdate.split()[0] # get rid of time
                                                   # of the day for the moment
                    task_update_progress("Harvesting %s (%i/%i)" % \
                                         (str(repos[0][6]),
                                         j, \
                                         len(reposlist)))
                    res = call_bibharvest(prefix=repos[0][2],
                                          baseurl=repos[0][1],
                                          harvestpath=harvestpath,
                                          fro=fromdate,
                                          setspecs=setspecs)
                    if res[0] == 1 :
                        update_lastrun(repos[0][0])
                        harvested_files = res[1]
                    else :
                        write_message("an error occurred while harvesting "
                            "from source " + str(repos[0][6]))
                        error_happened_p = True
                        continue
                else:
                    write_message("source " + str(repos[0][6]) +
                        " does not need updating")
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
            i = 0
            for harvested_file in harvested_files:
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Uploading records harvested from %s (%i/%i)" % \
                                     (str(repos[0][6]),\
                                      i, \
                                      len(harvested_files)))
                res += call_bibupload(harvested_file)
                if res == 0:
                    write_message("material harvested from source " +
                        str(repos[0][6]) + " was successfully uploaded")
                else:
                    write_message("an error occurred while uploading "
                        "harvest from " + str(repos[0][6]))
                    error_happened_p = True
                    continue

        if postmode == "h-c" or postmode == "h-c-u" or postmode == "h-c-f-u":
            convert_dir = CFG_TMPDIR
            convertpath = convert_dir + os.sep +"bibconvertrun" + \
                str(os.getpid())
            converted_files = []
            i = 0
            for harvested_file in harvested_files:
                i += 1
                task_sleep_now_if_required()
                converted_file = convertpath+".%07d" % i
                converted_files.append(converted_file)
                task_update_progress("Converting material harvested from %s (%i/%i)" % \
                                     (str(repos[0][6]), \
                                      i, \
                                      len(harvested_files)))
                res = call_bibconvert(config=str(repos[0][5]),
                                      harvestpath=harvested_file,
                                      convertpath=converted_file)

                if res == 0:
                    write_message("material harvested from source " +
                        str(repos[0][6]) + " was successfully converted")
                else:
                    write_message("an error occurred while converting from " +
                        str(repos[0][6]))
                    error_happened_p = True
                    continue

            # print stats:
            for converted_file in converted_files:
                write_message("File %s contains %i records." % \
                              (converted_file,
                               get_nb_records_in_file(converted_file)))

        if postmode == "h-c-u":
            res = 0
            i = 0
            uploaded = False
            for converted_file in converted_files:
                i += 1
                task_sleep_now_if_required()
                if get_nb_records_in_file(converted_file) > 0:
                    task_update_progress("Uploading records harvested from %s (%i/%i)" % \
                                         (str(repos[0][6]),\
                                          i, \
                                          len(converted_files)))
                    res += call_bibupload(converted_file)
                    uploaded = True
            if len(converted_files) > 0:
                if res == 0:
                    if uploaded:
                        write_message("material harvested from source " +
                                      str(repos[0][6]) + " was successfully uploaded")
                    else:
                        write_message("nothing to upload")
                else:
                    write_message("an error occurred while uploading "
                                  "harvest from " + str(repos[0][6]))
                    error_happened_p = True
                    continue

        elif postmode == "h-c-f-u":
            # first call bibfilter:
            res = 0
            uploaded = False
            i = 0
            for converted_file in converted_files:
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Filtering material harvested from %s (%i/%i)" % \
                                     (str(repos[0][6]), \
                                      i,\
                                      len(converted_files)))
                res += call_bibfilter(str(repos[0][11]), converted_file)
            if len(converted_files) > 0:
                if res == 0:
                    write_message("material harvested from source " +
                                  str(repos[0][6]) + " was successfully bibfiltered")
                else:
                    write_message("an error occurred while bibfiltering "
                                  "harvest from " + str(repos[0][6]))
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
            i = 0
            for converted_file in converted_files:
                task_sleep_now_if_required()
                i += 1
                if get_nb_records_in_file(converted_file + ".insert.xml") > 0:
                    task_update_progress("Uploading new records harvested from %s (%i/%i)" % \
                                         (str(repos[0][6]),\
                                          i, \
                                          len(converted_files)))
                    res += call_bibupload(converted_file + ".insert.xml", "-i")
                    uploaded = True
                task_sleep_now_if_required()
                if get_nb_records_in_file(converted_file + ".correct.xml") > 0:
                    task_update_progress("Uploading corrections for records harvested from %s (%i/%i)" % \
                                         (str(repos[0][6]),\
                                          i, \
                                          len(converted_files)))
                    res += call_bibupload(converted_file + ".correct.xml", "-c")
                    uploaded = True
            if len(converted_files) > 0:
                if res == 0:
                    if uploaded:
                        write_message("material harvested from source " +
                                      str(repos[0][6]) + " was successfully uploaded")
                    else:
                        write_message("nothing to upload")
                else:
                    write_message("an error occurred while uploading "
                                  "harvest from " + str(repos[0][6]))
                    error_happened_p = True
                    continue

        elif postmode not in ["h", "h-c", "h-u",
                "h-c-u", "h-c-f-u"]: ### this should not happen
            write_message("invalid postprocess mode: " + postmode +
                " skipping repository")
            error_happened_p = True
            continue

    if error_happened_p:
        task_update_status("DONE WITH ERRORS")
    else:
        task_update_status("DONE")
    return True


def add_timestamp_and_timelag(timestamp,
                              timelag):
    """ Adds a time lag in seconds to a given date (timestamp).
        Returns the resulting date. """
    # remove any trailing .00 in timestamp:
    timestamp = re.sub(r'\.[0-9]+$', '', timestamp)
    # first convert timestamp to Unix epoch seconds:
    timestamp_seconds = calendar.timegm(time.strptime(timestamp,
        "%Y-%m-%d %H:%M:%S"))
    # now add them:
    result_seconds = timestamp_seconds + timelag
    result = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(result_seconds))
    return result

def update_lastrun(index):
    """ A method that updates the lastrun of a repository
        successfully harvested """
    try:
        today = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sql = 'UPDATE oaiHARVEST SET lastrun=%s WHERE id=%s'
        run_sql(sql, (today, index))
        return 1
    except StandardError, e:
        return (0, e)

def call_bibharvest(prefix, baseurl, harvestpath,
            fro="", until="", setspecs=""):
    """ A method that calls bibharvest and writes harvested output to disk """
    try:
        command = '%s/bibharvest -o %s -v ListRecords -p %s ' % (CFG_BINDIR,
                                                                 harvestpath,
                                                                 prefix)

        if fro != "":
            command += '-f %s ' % fro
        if until != "":
            command += '-u %s ' % until
        if setspecs != "":
            command += '-s "%s" ' % setspecs
        command += baseurl

        print "Start harvesting"
        #print command
        os.system(command)
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
##         for f in files:
##             if f.startswith(filename)
##                 print "processing file %s"%f
##                 rf = file(os.path.join(harvestdir, f), 'r')
##                 hf.write(rf.read())
##                 hf.write("\n")
##                 rf.close()
##                 #os.remove(os.path.join(harvestdir, f))
##         hf.close()
##         print "Files merged"
        return (1, harvested_files)
    except StandardError, e:
        print e
        return (0, e)

def call_bibconvert(config, harvestpath, convertpath):
    """ A method that reads from a file and converts according to a BibConvert
        Configuration file. Converted output is returned """
    command = """%s/bibconvert -c %s < %s > %s """ % (CFG_BINDIR, config,
        harvestpath, convertpath)
    os.popen(command)
    return 0

def call_bibupload(marcxmlfile, mode="-r -i"):
    """Call bibupload in insert mode on MARCXMLFILE."""
    if os.path.exists(marcxmlfile):
        command = '%s/bibupload %s %s ' % (CFG_BINDIR, mode, marcxmlfile)
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
            write_message("bibfilterprogram %s is not a file" %
                bibfilterprogram)
            return 1
        elif not os.path.isfile(marcxmlfile):
            write_message("marcxmlfile %s is not a file" % marcxmlfile)
            return 1
        else:
            return os.system('%s %s' % (bibfilterprogram, marcxmlfile))
    else:
        try:
            write_message("no bibfilterprogram defined, copying %s only" %
                marcxmlfile)
            shutil.copy(marcxmlfile, marcxmlfile + ".insert.xml")
            return 0
        except:
            write_message("cannot copy %s into %s.insert.xml" % marcxmlfile)
            return 1

def get_row_from_reposname(reposname):
    """ Returns all information about a row (OAI source)
        from the source name """
    try:
        sql = """SELECT id, baseurl, metadataprefix, arguments,
                        comment, bibconvertcfgfile, name, lastrun,
                        frequency, postprocess, setspecs,
                        bibfilterprogram
                   FROM oaiHARVEST WHERE name=%s"""
        res = run_sql(sql, (reposname, ))
        reposdata = []
        for element in res:
            reposdata.append(element)
        return reposdata
    except StandardError, e:
        return (0, e)

def get_all_rows_from_db():
    """ This method retrieves the full database of repositories and returns
        a list containing (in exact order):
        | id | baseurl | metadataprefix | arguments | comment
        | bibconvertcfgfile | name   | lastrun | frequency
        | postprocess | setspecs | bibfilterprogram
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
        return (0, e)

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
    timestamp1_seconds = calendar.timegm(time.strptime(timestamp1,
        "%Y-%m-%d %H:%M:%S"))
    timestamp2_seconds = calendar.timegm(time.strptime(timestamp2,
        "%Y-%m-%d %H:%M:%S"))
    # now compare them:
    if timestamp1_seconds < timestamp2_seconds - tolerance:
        return -1
    elif timestamp1_seconds > timestamp2_seconds + tolerance:
        return 1
    else:
        return 0

def get_dates(dates):
    """ A method to validate and process the dates input by the user
        at the command line """
    twodates = []
    if dates:
        datestring = dates.split(":")
        if len(datestring)==2:
            for date in datestring:
                ### perform some checks on the date format
                datechunks = date.split("-")
                if len(datechunks)==3:
                    try:
                        if int(datechunks[0]) and int(datechunks[1]) and \
                                int(datechunks[2]):
                            twodates.append(date)
                    except StandardError:
                        write_message("Dates have invalid format, not "
                            "'yyyy-mm-dd:yyyy-mm-dd'")
                        twodates = None
                        return twodates
                else:
                    write_message("Dates have invalid format, not "
                        "'yyyy-mm-dd:yyyy-mm-dd'")
                    twodates = None
                    return twodates
            ## final check.. date1 must me smaller than date2
            date1 = str(twodates[0]) + " 01:00:00"
            date2 = str(twodates[1]) + " 01:00:00"
            if compare_timestamps_with_tolerance(date1, date2)!=-1:
                write_message("First date must be before second date.")
                twodates = None
                return twodates
        else:
            write_message("Dates have invalid format, not "
                "'yyyy-mm-dd:yyyy-mm-dd'")
            twodates = None
    else:
        twodates = None
    return twodates


def get_repository_names(repositories):
    """ A method to validate and process the repository names input by the
        user at the command line """
    repository_names = []
    if repositories:
        names = repositories.split(", ")
        for name in names:
            ### take into account both single word names and multiple word
            ### names (which get wrapped around "" or '')
            quote = "'"
            doublequote = '"'
            if name.find(quote)==0 and name.find(quote)==len(name):
                name = name.split(quote)[1]
            if name.find(doublequote)==0 and name.find(doublequote)==len(name):
                name = name.split(doublequote)[1]
            repository_names.append(name)
    else:
        repository_names = None
    return repository_names

def main():
    """Main that construct all the bibtask."""
    task_set_option("repository", None)
    task_set_option("dates", None)
    task_init(authorization_action='runoaiharvest',
            authorization_msg="oaiharvest Task Submission",
            description="""Examples:
    oaiharvest -r arxiv -s 24h
    oaiharvest -r pubmed -d 2005-05-05:2005-05-10 -t 10m\n""",
            help_specific_usage='  -r, --repository=REPOS_ONE, "REPOS TWO"     '
                'name of the OAI repositories to be harvested (default=all)\n'
                '  -d, --dates=yyyy-mm-dd:yyyy-mm-dd          '
                'harvest repositories between specified dates '
                '(overrides repositories\' last updated timestamps)\n',
            version=__revision__,
            specific_params=("r:d:", ["repository=", "dates=", ]),
            task_submit_elaborate_specific_parameter_fnc=
                task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Elaborate specific cli parameters for oaiharvest."""
    if key in ("-r", "--repository"):
        task_set_option('repository', get_repository_names(value))
    elif key in ("-d", "--dates"):
        task_set_option('dates', get_dates(value))
        if value is not None and task_get_option("dates") is None:
            raise StandardError, "Date format not valid."
    else:
        return False
    return True


### okay, here we go:
if __name__ == '__main__':
    main()
