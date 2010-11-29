# -*- coding: utf-8 -*-
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

"""
OAI Harvest daemon - harvest records from OAI repositories.

If started via CLI with --verb parameters, starts a manual single-shot
harvesting. Otherwise starts a BibSched task for periodical harvesting
of repositories defined in the OAI Harvest admin interface
"""

__revision__ = "$Id$"

import os
import sys
import getopt
import getpass
import re
import time
import calendar
import shutil
import tempfile
import urlparse

from invenio.config import \
     CFG_BINDIR, \
     CFG_TMPDIR
from invenio.oai_harvest_config import CFG_OAI_POSSIBLE_POSTMODES
from invenio.dbquery import run_sql
from invenio.bibtask import \
     task_get_task_param, \
     task_get_option, \
     task_set_option, \
     write_message, \
     task_init, \
     task_sleep_now_if_required, \
     task_update_progress, \
     task_low_level_submission
from invenio.bibrecord import record_extract_oai_id, create_records
from invenio import oai_harvest_getter
from invenio.plotextractor_getter import harvest_single, make_single_directory
from invenio.plotextractor import process_single

## precompile some often-used regexp for speed reasons:
re_subfields = re.compile('\$\$\w')
re_datetime_shift = re.compile("([-\+]{0, 1})([\d]+)([dhms])")
re_record = re.compile('<record>(.*?<datafield tag="035" ind1=" " ind2=" ">' + \
                           '<subfield code="9">arXiv<\/subfield>' + \
                           '<subfield code="z">(.*?)<\/subfield>' + \
                       '<\/datafield>.*?)<\/record>', re.DOTALL)

tmpHARVESTpath = CFG_TMPDIR + "/oaiharvest"

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
    """Run the harvesting task.  The row argument is the oaiharvest task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    reposlist = []
    datelist = []
    dateflag = 0
    possible_postmodes = [code for code, dummy in CFG_OAI_POSSIBLE_POSTMODES]
    filepath_prefix = tmpHARVESTpath + "_" + str(task_get_task_param("task_id"))
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
        reponame = str(repos[0][6])
        postmode = str(repos[0][9])
        setspecs = str(repos[0][10])
        harvested_files_list = []
        if postmode in possible_postmodes:
            # Harvest phase
            harvestpath = filepath_prefix + "_" + str(j) + "_" + \
                         time.strftime("%Y%m%d%H%M%S") + "_harvested"
            if dateflag == 1:
                task_update_progress("Harvesting %s from %s to %s (%i/%i)" % \
                                     (reponame, \
                                      str(datelist[0]),
                                      str(datelist[1]),
                                      j, \
                                      len(reposlist)))
                exit_code, file_list = oai_harvest_get(prefix = repos[0][2],
                                      baseurl = repos[0][1],
                                      harvestpath = harvestpath,
                                      fro = str(datelist[0]),
                                      until = str(datelist[1]),
                                      setspecs = setspecs)
                if exit_code == 1 :
                    write_message("source " + reponame + \
                                  " was harvested from " + str(datelist[0]) \
                                  + " to " + str(datelist[1]))
                    harvested_files_list = file_list
                else:
                    write_message("an error occurred while harvesting "
                        "from source " +
                        reponame + " for the dates chosen")
                    error_happened_p = True
                    continue

            elif dateflag != 1 and repos[0][7] is None and repos[0][8] != 0:
                write_message("source " + reponame + \
                              " was never harvested before - harvesting whole "
                              "repository")
                task_update_progress("Harvesting %s (%i/%i)" % \
                                     (reponame,
                                      j, \
                                      len(reposlist)))
                exit_code, file_list = oai_harvest_get(prefix = repos[0][2],
                                      baseurl = repos[0][1],
                                      harvestpath = harvestpath,
                                      setspecs = setspecs)
                if exit_code == 1 :
                    update_lastrun(repos[0][0])
                    harvested_files_list = file_list
                else :
                    write_message("an error occurred while harvesting from "
                        "source " + reponame)
                    error_happened_p = True
                    continue

            elif dateflag != 1 and repos[0][8] != 0:
                ### check that update is actually needed,
                ### i.e. lastrun+frequency>today
                timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                lastrundate = re.sub(r'\.[0-9]+$', '',
                    str(repos[0][7])) # remove trailing .00
                timeinsec = int(repos[0][8]) * 60 * 60
                updatedue = add_timestamp_and_timelag(lastrundate, timeinsec)
                proceed = compare_timestamps_with_tolerance(updatedue, timenow)
                if proceed == 0 or proceed == -1 : #update needed!
                    write_message("source " + reponame +
                        " is going to be updated")
                    fromdate = str(repos[0][7])
                    fromdate = fromdate.split()[0] # get rid of time
                                                   # of the day for the moment
                    task_update_progress("Harvesting %s (%i/%i)" % \
                                         (reponame,
                                         j, \
                                         len(reposlist)))
                    exit_code, file_list = oai_harvest_get(prefix = repos[0][2],
                                          baseurl = repos[0][1],
                                          harvestpath = harvestpath,
                                          fro = fromdate,
                                          setspecs = setspecs)
                    if exit_code == 1 :
                        update_lastrun(repos[0][0])
                        harvested_files_list = file_list
                    else :
                        write_message("an error occurred while harvesting "
                            "from source " + reponame)
                        error_happened_p = True
                        continue
                else:
                    write_message("source " + reponame +
                        " does not need updating")
                    continue

            elif dateflag != 1 and repos[0][8] == 0:
                write_message("source " + reponame + \
                    " has frequency set to 'Never' so it will not be updated")
                continue

            # Harvesting done, now convert/extract/filter/upload as requested
            if len(harvested_files_list) < 1:
                write_message("No records harvested for %s" % (reponame,))
                continue
            active_files_list = harvested_files_list
            # Convert phase
            if 'c' in postmode:
                converted_files_list = []
                i = 0
                for active_file in active_files_list:
                    i += 1
                    task_sleep_now_if_required()
                    task_update_progress("Converting material harvested from %s (%i/%i)" % \
                                         (reponame, \
                                          i, \
                                          len(active_files_list)))
                    converted_file = filepath_prefix + "_" + str(i) + "_" + \
                        time.strftime("%Y%m%d%H%M%S") + "_converted"
                    converted_files_list.append(converted_file)
                    (exitcode, err_msg) = call_bibconvert(config = str(repos[0][5]),
                                                          harvestpath = active_file,
                                                          convertpath = converted_file)
                    if exitcode == 0:
                        write_message("material harvested from source " +
                            reponame + " was successfully converted")
                    else:
                        write_message("an error occurred while converting from " +
                            reponame + ': \n' + err_msg)
                        error_happened_p = True
                        continue
                # print stats:
                for converted_file in converted_files_list:
                    write_message("File %s contains %i records." % \
                                  (converted_file,
                                   get_nb_records_in_file(converted_file)))
                active_files_list = converted_files_list

            if 'e' in postmode:
                # Download tarball for each harvested/converted record, then run plotextrator.
                # Update converted xml files with generated xml or add it for upload
                extracted_files_list = []
                i = 0
                for active_file in active_files_list:
                    i += 1
                    task_sleep_now_if_required()
                    task_update_progress("Extracting material harvested from %s (%i/%i)" % \
                                         (reponame, i, len(active_files_list)))
                    extracted_file = filepath_prefix + "_" + str(i) + "_" + \
                        time.strftime("%Y%m%d%H%M%S") + "_extracted"
                    extracted_files_list.append(extracted_file)
                    (exitcode, err_msg) = call_plotextractor(active_file,
                                                             extracted_file)
                    if exitcode == 0:
                        write_message("material harvested from source " +
                            reponame + " was successfully extracted")
                    else:
                        write_message("an error occurred while extracting from " +
                            reponame + ': \n' + err_msg)
                        error_happened_p = True
                        continue
                # print stats:
                for extracted_file in extracted_files_list:
                    write_message("File %s contains %i records." % \
                                  (extracted_file,
                                   get_nb_records_in_file(extracted_file)))
                active_files_list = extracted_files_list

            # Filter-phase
            if 'f' in postmode:
                # first call bibfilter:
                res = 0
                uploaded = False
                i = 0
                for active_file in active_files_list:
                    i += 1
                    task_sleep_now_if_required()
                    task_update_progress("Filtering material harvested from %s (%i/%i)" % \
                                         (reponame, \
                                          i, \
                                          len(active_files_list)))
                    res += call_bibfilter(str(repos[0][11]), active_file)
                if len(active_files_list) > 0:
                    if res == 0:
                        write_message("material harvested from source " +
                                      reponame + " was successfully bibfiltered")
                    else:
                        write_message("an error occurred while bibfiltering "
                                      "harvest from " + reponame)
                        error_happened_p = True
                        continue
                # print stats:
                for active_file in active_files_list:
                    write_message("File %s contains %i records." % \
                        (active_file + ".insert.xml",
                        get_nb_records_in_file(active_file + ".insert.xml")))
                    write_message("File %s contains %i records." % \
                        (active_file + ".correct.xml",
                        get_nb_records_in_file(active_file + ".correct.xml")))
                    write_message("File %s contains %i records." % \
                        (active_file + ".append.xml",
                        get_nb_records_in_file(active_file + ".append.xml")))
                    write_message("File %s contains %i records." % \
                        (active_file + ".holdingpen.xml",
                        get_nb_records_in_file(active_file + ".holdingpen.xml")))

            # Upload files
            if "u" in postmode:
                if 'f' in postmode:
                    # upload filtered files
                    i = 0
                    for active_file in active_files_list:
                        task_sleep_now_if_required()
                        i += 1
                        if get_nb_records_in_file(active_file + ".insert.xml") > 0:
                            task_update_progress("Uploading new records harvested from %s (%i/%i)" % \
                                                 (reponame, \
                                                  i, \
                                                  len(active_files_list)))
                            res += call_bibupload(active_file + ".insert.xml", \
                                                  ["-i"], oai_src_id = repos[0][0])
                            uploaded = True
                        task_sleep_now_if_required()
                        if get_nb_records_in_file(active_file + ".correct.xml") > 0:
                            task_update_progress("Uploading corrections for records harvested from %s (%i/%i)" % \
                                                 (reponame, \
                                                  i, \
                                                  len(active_files_list)))
                            res += call_bibupload(active_file + ".correct.xml", \
                                                  ["-c"], oai_src_id = repos[0][0])
                            uploaded = True
                        if get_nb_records_in_file(active_file + ".append.xml") > 0:
                            task_update_progress("Uploading additions for records harvested from %s (%i/%i)" % \
                                                 (reponame, \
                                                  i, \
                                                  len(active_files_list)))
                            res += call_bibupload(active_file + ".append.xml", \
                                                  ["-a"], oai_src_id = repos[0][0])
                            uploaded = True
                        if get_nb_records_in_file(active_file + ".holdingpen.xml") > 0:
                            task_update_progress("Uploading records harvested from %s to holding pen (%i/%i)" % \
                                                 (reponame, \
                                                  i, \
                                                  len(active_files_list)))
                            res += call_bibupload(active_file + ".holdingpen.xml", \
                                                  ["-o"], oai_src_id = repos[0][0])
                            uploaded = True
                    if len(active_files_list) > 0:
                        if res == 0:
                            if uploaded:
                                write_message("material harvested from source " +
                                              reponame + " was successfully uploaded")
                            else:
                                write_message("nothing to upload")
                        else:
                            write_message("an error occurred while uploading "
                                          "harvest from " + reponame)
                            error_happened_p = True
                            continue
                else:
                    # upload files normally
                    res = 0
                    i = 0
                    uploaded = False
                    for active_file in active_files_list:
                        i += 1
                        task_sleep_now_if_required()
                        if get_nb_records_in_file(active_file) > 0:
                            task_update_progress("Uploading records harvested from %s (%i/%i)" % \
                                                 (reponame, \
                                                  i, \
                                                  len(active_files_list)))
                            res += call_bibupload(active_file, oai_src_id = repos[0][0])
                            uploaded = True
                        if res == 0:
                            if uploaded:
                                write_message("material harvested from source " +
                                              reponame + " was successfully uploaded")
                            else:
                                write_message("nothing to upload")
                        else:
                            write_message("an error occurred while uploading "
                                          "harvest from " + reponame)
                            error_happened_p = True
                            continue

        else: ### this should not happen
            write_message("invalid postprocess mode: " + postmode +
                " skipping repository")
            error_happened_p = True
            continue

    if error_happened_p:
        return False
    else:
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

def oai_harvest_get(prefix, baseurl, harvestpath,
                    fro = None, until = None, setspecs = None,
                    user = None, password = None, cert_file = None,
                    key_file = None, method = "POST"):
    """
    Retrieve OAI records from given repository, with given arguments
    """
    try:
        (addressing_scheme, network_location, path, parameters, \
         query, fragment_identifier) = urlparse.urlparse(baseurl)
        secure = (addressing_scheme == "https")

        http_param_dict = {'verb': "ListRecords",
                           'metadataPrefix': prefix}
        if fro:
            http_param_dict['from'] = fro
        if until:
            http_param_dict['until'] = until
        sets = None
        if setspecs:
            sets = [set.strip() for set in setspecs.split(' ')]

        print "Start harvesting"
        oai_harvest_getter.harvest(network_location, path, http_param_dict, method, harvestpath,
                                   sets, secure, user, password, cert_file, key_file)

        harvest_dir, harvest_filename = os.path.split(harvestpath)
        files = os.listdir(harvest_dir)
        files.sort()
        harvested_files = [harvest_dir + os.sep + filename for \
                           filename in files \
                           if filename.startswith(harvest_filename)]

        return (1, harvested_files)
    except StandardError, e:
        print e
        return (0, e)

def call_bibconvert(config, harvestpath, convertpath):
    """ Call BibConvert to convert file given at 'harvestpath' with
    conversion template 'config', and save the result in file at
    'convertpath'.

    Returns status exit code of the conversion, as well as error
    messages, if any
    """
    cmd_err_fd, file_cmd_err = tempfile.mkstemp()
    command = "%s/bibconvert -c %s < %s > %s 2> %s" % \
              (CFG_BINDIR, config, harvestpath, convertpath, file_cmd_err)
    exitcode = os.system(command)
    cmd_err = ""
    if exitcode != 0:
        cmd_err_fo = open(file_cmd_err)
        cmd_err = cmd_err_fo.read()
        cmd_err_fo.close()
        os.remove(file_cmd_err)
    os.close(cmd_err_fd)
    return (exitcode, cmd_err)

def call_plotextractor(active_file, extracted_file):
    """
    Function that generates proper MARCXML containing harvested material
    such as plots and fulltext for each record.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file to be extracted in which the
                           final resulting MARCXML will be saved
    @return: exitcode and any error messages as: (exitcode, err_msg)
    """
    err_msg = ""
    exitcode = 0

    # Read in active file
    recs_fd = open(active_file, 'r')
    records = recs_fd.read()
    recs_fd.close()

    # Find all records mapped with identifier
    record_xmls = re_record.findall(records)
    updated_xml = '<?xml version="1.0" encoding="UTF-8"?><collection>'
    for record_xml, identifier in record_xmls:
        updated_xml += "<record>%s" % (record_xml,)
        exitcode, err_msg, extracted_fulltext_xml, plotextracted_xml = \
                    plotextractor_harvest(identifier, active_file)
        if plotextracted_xml != None:
            # Strip tags. Expecting:
            # <?xml version="1.0" encoding="UTF-8"?>
            # <collection><record>
            # ...
            # </record></collection>
            plotextracted_xml = plotextracted_xml[58:-22]
            updated_xml += plotextracted_xml
        if extracted_fulltext_xml != None:
            updated_xml += extracted_fulltext_xml
        updated_xml += "</record>"

    # Write to file
    file_fd = open(extracted_file, 'w')
    file_fd.write(updated_xml + '</collection>')
    file_fd.close()
    return exitcode, err_msg

def plotextractor_harvest(identifier, active_file):
    """
    Function that calls plotextractor library to download and extract tarball
    and fulltext pdf for each record.

    @param identifier: OAI identifier of the record to harvest
    @param active_file: path to the currently processed file

    @return: exitcode, errormessages and paths to generated MARCXML for plots and fulltext as a tuple
             (exitcode, err_msg, fulltext_xml, plotextracted_xml)
    """
    err_msg = ""
    exitcode = 0
    plotextracted_xml = None
    fulltext_xml = None
    active_dir, active_name = os.path.split(active_file)
    extract_path = make_single_directory(active_dir, active_name + \
                                          "_plotextraction")
    tarball, pdf = harvest_single(identifier, extract_path)
    if tarball != None:
        plotextracted_xml_path = process_single(tarball, clean = True)
        if plotextracted_xml_path != None:
            plotsxml_fd = open(plotextracted_xml_path, 'r')
            plotextracted_xml = plotsxml_fd.read()
            plotsxml_fd.close()
        else:
            err_msg += "Error extracting plots from id: %s %s\n" % \
                     (identifier, tarball)
            exitcode = 1
    else:
        err_msg += "Error harvesting plots from id: %s %s\n" % \
                     (identifier, extract_path)
        exitcode = 1

    if pdf != None:
        fulltext_xml = '<datafield tag="FFT" ind1=" " ind2=" ">' + \
                   '<subfield code="a">' + pdf + '</subfield>' + \
                   '<subfield code="t"></subfield>' + \
                   '</datafield>'
    else:
        err_msg += "Error harvesting fulltext from id: %s %s\n" % \
                     (identifier, extract_path)
        exitcode = 1
    return exitcode, err_msg, fulltext_xml, plotextracted_xml

def create_oaiharvest_log(task_id, oai_src_id, marcxmlfile):
    """
    Function which creates the harvesting logs
    @param task_id bibupload task id
    """
    file = open(marcxmlfile, "r")
    xml_content = file.read(-1)
    file.close()
    create_oaiharvest_log_str(task_id, oai_src_id, xml_content)

def create_oaiharvest_log_str(task_id, oai_src_id, xml_content):
    """
    Function which creates the harvesting logs
    @param task_id bibupload task id
    """
    try:
        records = create_records(xml_content)
        for record in records:
            oai_id = record_extract_oai_id(record[0])
            query = "INSERT INTO oaiHARVESTLOG (id_oaiHARVEST, oai_id, date_harvested, bibupload_task_id) VALUES (%s, %s, NOW(), %s)"
            run_sql(query, (str(oai_src_id), str(oai_id), str(task_id)))
    except Exception, msg:
        print "Logging exception : %s   " % (str(msg),)

def call_bibupload(marcxmlfile, mode = None, oai_src_id = -1):
    """Call bibupload in insert mode on MARCXMLFILE."""
    if mode is None:
        mode = ["-r", "-i"]
    if os.path.exists(marcxmlfile):
        try:
            args = mode
            args.append(marcxmlfile)
            task_id = task_low_level_submission("bibupload", "oaiharvest", *tuple(args))
            create_oaiharvest_log(task_id, oai_src_id, marcxmlfile)
        except Exception, msg:
            write_message("An exception during submitting oaiharvest task occured : %s " % (str(msg)))
            return 1
        return 0
    else:
        write_message("marcxmlfile %s does not exist" % marcxmlfile)
        return 1

def call_bibfilter(bibfilterprogram, marcxmlfile):
    """
    Call bibfilter program BIBFILTERPROGRAM on MARCXMLFILE, which is usually
    run before uploading records.

    The bibfilter should produce up to four files called MARCXMLFILE.insert.xml,
    MARCXMLFILE.correct.xml, MARCXMLFILE.append.xml and MARCXMLFILE.holdingpen.xml.
    The first file contains parts of MARCXML to be uploaded in insert mode,
    the second file is uploaded in correct mode, third in append mode and the last file
    contains MARCXML to be uploaded into the holding pen.

    @param bibfilterprogram: path to bibfilter script to run
    @param marcxmlfile: base-marcxmlfilename

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
        res = run_sql(sql, (reposname,))
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
                                      tolerance = 0):
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
        return - 1
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
        if len(datestring) == 2:
            for date in datestring:
                ### perform some checks on the date format
                datechunks = date.split("-")
                if len(datechunks) == 3:
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
            if compare_timestamps_with_tolerance(date1, date2) != -1:
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
        names = repositories.split(",")
        for name in names:
            ### take into account both single word names and multiple word
            ### names (which get wrapped around "" or '')
            name = name.strip()
            if name.startswith("'"):
                name = name.strip("'")
            elif name.startswith('"'):
                name = name.strip('"')
            repository_names.append(name)
    else:
        repository_names = None
    return repository_names

def usage(exitcode = 0, msg = ""):
    "Print out info. Only used when run in 'manual' harvesting mode"
    sys.stderr.write("*Manual single-shot harvesting mode*\n")
    if msg:
        sys.stderr.write(msg + "\n")
    sys.exit(exitcode)

def main():
    """Starts the tool.

    If the command line arguments are those of the 'manual' mode, then
    starts a manual one-time harvesting. Else trigger a BibSched task
    for automated harvesting based on the OAIHarvest admin settings.
    """

    # Let's try to parse the arguments as used in manual harvesting:
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:v:m:p:i:s:f:u:r:x:c:k:w:l:",
                                   ["output=",
                                    "verb=",
                                    "method=",
                                    "metadataPrefix=",
                                    "identifier=",
                                    "set=",
                                    "from=",
                                    "until=",
                                    "resumptionToken=",
                                    "certificate=",
                                    "key=",
                                    "user=",
                                    "password="]
                                   )
        # So everything went smoothly: start harvesting in manual mode
        if len([opt for opt, opt_value in opts if opt in ['-v', '--verb']]) > 0:
            # verb parameter is given
            http_param_dict = {}
            method = "POST"
            output = ""
            user = None
            password = None
            cert_file = None
            key_file = None
            sets = []

            # get options and arguments
            for opt, opt_value in opts:
                if   opt in ["-v", "--verb"]:
                    http_param_dict['verb'] = opt_value
                elif opt in ["-m", '--method']:
                    if opt_value == "GET" or opt_value == "POST":
                        method = opt_value
                elif opt in ["-p", "--metadataPrefix"]:
                    http_param_dict['metadataPrefix'] = opt_value
                elif opt in ["-i", "--identifier"]:
                    http_param_dict['identifier'] = opt_value
                elif opt in ["-s", "--set"]:
                    sets = opt_value.split()
                elif opt in ["-f", "--from"]:
                    http_param_dict['from'] = opt_value
                elif opt in ["-u", "--until"]:
                    http_param_dict['until'] = opt_value
                elif opt in ["-r", "--resumptionToken"]:
                    http_param_dict['resumptionToken'] = opt_value
                elif opt in ["-o", "--output"]:
                    output = opt_value
                elif opt in ["-c", "--certificate"]:
                    cert_file = opt_value
                elif opt in ["-k", "--key"]:
                    key_file = opt_value
                elif opt in ["-l", "--user"]:
                    user = opt_value
                elif opt in ["-w", "--password"]:
                    password = opt_value
                elif opt in ["-V", "--version"]:
                    print __revision__
                    sys.exit(0)
                else:
                    usage(1, "Option %s is not allowed" % opt)

            if len(args) > 0:
                base_url = args[-1]
                if not base_url.lower().startswith('http'):
                    base_url = 'http://' + base_url
                (addressing_scheme, network_location, path, parameters, \
                 query, fragment_identifier) = urlparse.urlparse(base_url)
                secure = (addressing_scheme == "https")

                if (cert_file and not key_file) or \
                   (key_file and not cert_file):
                    # Both are needed if one specified
                    usage(1, "You must specify both certificate and key files")

                if password and not user:
                    # User must be specified when password is given
                    usage(1, "You must specify a username")
                elif user and not password:
                    if not secure:
                        sys.stderr.write("*WARNING* Your password will be sent in clear!\n")
                    try:
                        password = getpass.getpass()
                    except KeyboardInterrupt, e:
                        sys.stderr.write("\n")
                        sys.exit(0)

                oai_harvest_getter.harvest(network_location, path,
                                           http_param_dict, method,
                                           output, sets, secure, user,
                                           password, cert_file,
                                           key_file)

                sys.stderr.write("Harvesting completed at: %s\n\n" %
                    time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
                return
            else:
                usage(1, "You must specify the URL to harvest")
        else:
            # verb is not given. We will continue with periodic
            # harvesting. But first check if URL parameter is given:
            # if it is, then warn directly now
            if len(args) > 1 or \
               (len(args) == 1 and not args[0].isdigit()):
                usage(1, "You must specify the --verb parameter")
    except getopt.error, e:
        # So could it be that we are using different arguments? Try to
        # start the BibSched task (automated harvesting) and see if it
        # validates
        pass

    # BibSched mode - periodical harvesting
    # Note that the 'help' is common to both manual and automated
    # mode.
    task_set_option("repository", None)
    task_set_option("dates", None)
    task_init(authorization_action = 'runoaiharvest',
              authorization_msg = "oaiharvest Task Submission",
              description = """
Harvest records from OAI sources.
Manual vs automatic harvesting:
   - Manual harvesting retrieves records from the specified URL,
     with the specified OAI arguments. Harvested records are displayed
     on the standard output or saved to a file, but are not integrated
     into the repository. This mode is useful to 'play' with OAI
     repositories or to build special harvesting scripts.
   - Automatic harvesting relies on the settings defined in the OAI
     Harvest admin interface to periodically retrieve the repositories
     and sets to harvest. It also take care of harvesting only new or
     modified records. Records harvested using this mode are converted
     and integrated into the repository, according to the settings
     defined in the OAI Harvest admin interface.

Examples:
Manual (single-shot) harvesting mode:
   Save to /tmp/z.xml records from CDS added/modified between 2004-04-01
   and 2004-04-02, in MARCXML:
     $ oaiharvest -vListRecords -f2004-04-01 -u2004-04-02 -pmarcxml -o/tmp/z.xml http://cdsweb.cern.ch/oai2d
Automatic (periodical) harvesting mode:
   Schedule daily harvesting of all repositories defined in OAIHarvest admin:
     $ oaiharvest -s 24h
   Schedule daily harvesting of repository 'arxiv', defined in OAIHarvest admin:
     $ oaiharvest -r arxiv -s 24h
   Harvest in 10 minutes from 'pubmed' repository records added/modified
   between 2005-05-05 and 2005-05-10:
     $ oaiharvest -r pubmed -d 2005-05-05:2005-05-10 -t 10m
""",
            help_specific_usage = 'Manual single-shot harvesting mode:\n'
              '  -o, --output         specify output file\n'
              '  -v, --verb           OAI verb to be executed\n'
              '  -m, --method         http method (default POST)\n'
              '  -p, --metadataPrefix metadata format\n'
              '  -i, --identifier     OAI identifier\n'
              '  -s, --set            OAI set(s). Whitespace-separated list\n'
              '  -r, --resuptionToken Resume previous harvest\n'
              '  -f, --from           from date (datestamp)\n'
              '  -u, --until          until date (datestamp)\n'
              '  -c, --certificate    path to public certificate (in case of certificate-based harvesting)\n'
              '  -k, --key            path to private key (in case of certificate-based harvesting)\n'
              '  -l, --user           username (in case of password-protected harvesting)\n'
              '  -w, --password       password (in case of password-protected harvesting)\n'
              'Automatic periodical harvesting mode:\n'
              '  -r, --repository="repo A"[,"repo B"] \t which repositories to harvest (default=all)\n'
              '  -d, --dates=yyyy-mm-dd:yyyy-mm-dd \t reharvest given dates only\n',
            version = __revision__,
            specific_params = ("r:d:", ["repository=", "dates=", ]),
            task_submit_elaborate_specific_parameter_fnc =
                task_submit_elaborate_specific_parameter,
            task_run_fnc = task_run_core)

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
