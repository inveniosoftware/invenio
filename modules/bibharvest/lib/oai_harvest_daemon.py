# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
     CFG_TMPDIR, \
     CFG_ETCDIR, \
     CFG_INSPIRE_SITE, \
     CFG_CERN_SITE, \
     CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT, \
     CFG_SITE_URL, \
     CFG_OAI_FAILED_HARVESTING_STOP_QUEUE, \
     CFG_OAI_FAILED_HARVESTING_EMAILS_ADMIN
from invenio.oai_harvest_config import InvenioOAIHarvestWarning
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
from invenio.bibrecord import record_extract_oai_id, create_records, \
                              create_record, record_add_fields, \
                              record_delete_fields, record_xml_output, \
                              record_get_field_instances, \
                              record_modify_subfield, \
                              record_has_field, field_xml_output
from invenio import oai_harvest_getter
from invenio.errorlib import register_exception
from invenio.plotextractor_getter import harvest_single, make_single_directory
from invenio.plotextractor_converter import untar
from invenio.plotextractor import process_single, get_defaults
from invenio.shellutils import run_shell_command, Timeout
from invenio.textutils import translate_latex2unicode
from invenio.bibedit_utils import record_find_matching_fields
from invenio.bibcatalog import bibcatalog_system

## precompile some often-used regexp for speed reasons:
REGEXP_OAI_ID = re.compile("<identifier.*?>(.*?)<\/identifier>", re.DOTALL)
REGEXP_RECORD = re.compile("<record.*?>(.*?)</record>", re.DOTALL)
REGEXP_REFS = re.compile("<record.*?>.*?<controlfield .*?>.*?</controlfield>(.*?)</record>", re.DOTALL)
REGEXP_AUTHLIST = re.compile("<collaborationauthorlist.*?</collaborationauthorlist>", re.DOTALL)
CFG_OAI_AUTHORLIST_POSTMODE_STYLESHEET = "%s/bibconvert/config/%s" % (CFG_ETCDIR, "authorlist2marcxml.xsl")

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
    filepath_prefix = "%s/oaiharvest_%s" % (CFG_TMPDIR, str(task_get_task_param("task_id")))
    ### go ahead: build up the reposlist
    if task_get_option("repository") is not None:
        ### user requests harvesting from selected repositories
        write_message("harvesting from selected repositories")
        for reposname in task_get_option("repository"):
            row = get_row_from_reposname(reposname)
            if row == []:
                write_message("source name %s is not valid" % (reposname,))
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

    error_happened_p = 0 # 0: no error, 1: "recoverable" error (don't stop queue), 2: error (admin intervention needed)

    j = 0
    for repos in reposlist:
        j += 1
        task_sleep_now_if_required()

        # Extract values from database row (in exact order):
        #  | id | baseurl | metadataprefix | arguments | comment
        #  | bibconvertcfgfile | name   | lastrun | frequency
        #  | postprocess | setspecs | bibfilterprogram
        baseurl = str(repos[0][1])
        metadataprefix = str(repos[0][2])
        bibconvert_cfgfile = str(repos[0][5])
        reponame = str(repos[0][6])
        lastrun = repos[0][7]
        frequency = repos[0][8]
        postmode = repos[0][9]
        setspecs = str(repos[0][10])
        bibfilterprogram = str(repos[0][11])

        write_message("running in postmode %s" % (postmode,))
        downloaded_material_dict = {}
        harvested_files_list = []
        # Harvest phase
        harvestpath = "%s_%d_%s_" % (filepath_prefix, j, time.strftime("%Y%m%d%H%M%S"))
        if dateflag == 1:
            task_update_progress("Harvesting %s from %s to %s (%i/%i)" % \
                                 (reponame, \
                                  str(datelist[0]),
                                  str(datelist[1]),
                                  j, \
                                  len(reposlist)))
            exit_code, file_list = oai_harvest_get(prefix=metadataprefix,
                                                   baseurl=baseurl,
                                                   harvestpath=harvestpath,
                                                   fro=str(datelist[0]),
                                                   until=str(datelist[1]),
                                                   setspecs=setspecs)
            if exit_code == 1 :
                write_message("source %s was harvested from %s to %s" % \
                              (reponame, str(datelist[0]), str(datelist[1])))
                harvested_files_list = file_list
            else:
                write_message("an error occurred while harvesting from source %s for the dates chosen:\n%s\n" % \
                              (reponame, file_list))
                if error_happened_p < 1:
                    error_happened_p = 1
                continue

        elif dateflag != 1 and lastrun is None and frequency != 0:
            write_message("source %s was never harvested before - harvesting whole repository" % \
                          (reponame,))
            task_update_progress("Harvesting %s (%i/%i)" % \
                                 (reponame,
                                  j, \
                                  len(reposlist)))
            exit_code, file_list = oai_harvest_get(prefix=metadataprefix,
                                                   baseurl=baseurl,
                                                   harvestpath=harvestpath,
                                                   setspecs=setspecs)
            if exit_code == 1 :
                update_lastrun(repos[0][0])
                harvested_files_list = file_list
            else :
                write_message("an error occurred while harvesting from source %s:\n%s\n" % \
                              (reponame, file_list))
                if error_happened_p < 1:
                    error_happened_p = 1
                continue

        elif dateflag != 1 and frequency != 0:
            ### check that update is actually needed,
            ### i.e. lastrun+frequency>today
            timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            lastrundate = re.sub(r'\.[0-9]+$', '',
                str(lastrun)) # remove trailing .00
            timeinsec = int(frequency) * 60 * 60
            updatedue = add_timestamp_and_timelag(lastrundate, timeinsec)
            proceed = compare_timestamps_with_tolerance(updatedue, timenow)
            if proceed == 0 or proceed == -1 : #update needed!
                write_message("source %s is going to be updated" % (reponame,))
                fromdate = str(lastrun)
                fromdate = fromdate.split()[0] # get rid of time of the day for the moment
                task_update_progress("Harvesting %s (%i/%i)" % \
                                     (reponame,
                                     j, \
                                     len(reposlist)))
                exit_code, file_list = oai_harvest_get(prefix=metadataprefix,
                                                       baseurl=baseurl,
                                                       harvestpath=harvestpath,
                                                       fro=fromdate,
                                                       setspecs=setspecs)
                if exit_code == 1 :
                    update_lastrun(repos[0][0])
                    harvested_files_list = file_list
                else :
                    write_message("an error occurred while harvesting from source %s:\n%s\n" % \
                                  (reponame, file_list))
                    if error_happened_p < 1:
                        error_happened_p = 1
                    continue
            else:
                write_message("source %s does not need updating" % (reponame,))
                continue

        elif dateflag != 1 and frequency == 0:
            write_message("source %s has frequency set to 'Never' so it will not be updated" % \
                          (reponame,))
            continue

        # Harvesting done, now convert/extract/filter/upload as requested
        if len(harvested_files_list) < 1:
            write_message("No records harvested for %s" % (reponame,))
            continue

        # Retrieve all OAI IDs and set active list
        harvested_identifier_list = collect_identifiers(harvested_files_list)
        active_files_list = harvested_files_list
        if len(active_files_list) != len(harvested_identifier_list):
            # Harvested files and its identifiers are 'out of sync', abort harvest
            write_message("Harvested files miss identifiers for %s" % (reponame,))
            continue
        write_message("post-harvest processes started")
        # Convert phase
        if 'c' in postmode:
            updated_files_list = []
            i = 0
            write_message("conversion step started")
            for active_file in active_files_list:
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Converting material harvested from %s (%i/%i)" % \
                                     (reponame, \
                                      i, \
                                      len(active_files_list)))
                updated_file = "%s.converted" % (active_file.split('.')[0],)
                updated_files_list.append(updated_file)
                (exitcode, err_msg) = call_bibconvert(config=bibconvert_cfgfile,
                                                      harvestpath=active_file,
                                                      convertpath=updated_file)
                if exitcode == 0:
                    write_message("harvested file %s was successfully converted" % \
                                  (active_file,))
                else:
                    write_message("an error occurred while converting %s:\n%s" % \
                                  (active_file, err_msg))
                    error_happened_p = 2
                    continue
            # print stats:
            for updated_file in updated_files_list:
                write_message("File %s contains %i records." % \
                              (updated_file,
                               get_nb_records_in_file(updated_file)))
            active_files_list = updated_files_list
            write_message("conversion step ended")
        # plotextract phase
        if 'p' in postmode:
            write_message("plotextraction step started")
            # Download tarball for each harvested/converted record, then run plotextrator.
            # Update converted xml files with generated xml or add it for upload
            updated_files_list = []
            i = 0
            for active_file in active_files_list:
                identifiers = harvested_identifier_list[i]
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Extracting plots from harvested material from %s (%i/%i)" % \
                                     (reponame, i, len(active_files_list)))
                updated_file = "%s.plotextracted" % (active_file.split('.')[0],)
                updated_files_list.append(updated_file)
                (exitcode, err_msg) = call_plotextractor(active_file,
                                                         updated_file,
                                                         identifiers,
                                                         downloaded_material_dict)
                if exitcode == 0:
                    if err_msg != "":
                        write_message("plots from %s was extracted, but with some errors:\n%s" % \
                                  (active_file, err_msg))
                    else:
                        write_message("plots from %s was successfully extracted" % \
                                      (active_file,))
                else:
                    write_message("an error occurred while extracting plots from %s:\n%s" % \
                                  (active_file, err_msg))
                    error_happened_p = 2
                    continue
            # print stats:
            for updated_file in updated_files_list:
                write_message("File %s contains %i records." % \
                              (updated_file,
                               get_nb_records_in_file(updated_file)))
            active_files_list = updated_files_list
            write_message("plotextraction step ended")
        # refextract phase
        if 'r' in postmode:
            updated_files_list = []
            i = 0
            write_message("refextraction step started")
            for active_file in active_files_list:
                identifiers = harvested_identifier_list[i]
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Extracting references from material harvested from %s (%i/%i)" % \
                                     (reponame, i, len(active_files_list)))
                updated_file = "%s.refextracted" % (active_file.split('.')[0],)
                updated_files_list.append(updated_file)
                (exitcode, err_msg) = call_refextract(active_file,
                                                      updated_file,
                                                      identifiers,
                                                      downloaded_material_dict)
                if exitcode == 0:
                    if err_msg != "":
                        write_message("references from %s was extracted, but with some errors:\n%s" % \
                                      (active_file, err_msg))
                    else:
                        write_message("references from %s was successfully extracted" % \
                                      (active_file,))
                else:
                    write_message("an error occurred while extracting references from %s:\n%s" % \
                                  (active_file, err_msg))
                    error_happened_p = 2
                    continue
            # print stats:
            for updated_file in updated_files_list:
                write_message("File %s contains %i records." % \
                              (updated_file,
                               get_nb_records_in_file(updated_file)))
            active_files_list = updated_files_list
            write_message("refextraction step ended")
        # authorlist phase
        if 'a' in postmode:
            write_message("authorlist extraction step started")
            # Initialize BibCatalog connection as default user, if possible
            if bibcatalog_system is not None:
                bibcatalog_response = bibcatalog_system.check_system()
            else:
                bibcatalog_response = "No ticket system configured"
            if bibcatalog_response != "":
                write_message("BibCatalog error: %s\n" % (bibcatalog_response,))
            updated_files_list = []
            i = 0
            for active_file in active_files_list:
                identifiers = harvested_identifier_list[i]
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Extracting any authorlists from material harvested from %s (%i/%i)" % \
                                     (reponame, i, len(active_files_list)))
                updated_file = "%s.authextracted" % (active_file.split('.')[0],)
                updated_files_list.append(updated_file)
                (exitcode, err_msg) = call_authorlist_extract(active_file,
                                                              updated_file,
                                                              identifiers,
                                                              downloaded_material_dict)
                if exitcode == 0:
                    if err_msg != "":
                        write_message("authorlists from %s was extracted, but with some errors:\n%s" % \
                                      (active_file, err_msg))
                    else:
                        write_message("any authorlists from %s was successfully extracted" % \
                                      (active_file,))
                else:
                    write_message("an error occurred while extracting authorlists from %s:\n%s" % \
                                  (active_file, err_msg))
                    error_happened_p = 2
                    continue
            # print stats:
            for updated_file in updated_files_list:
                write_message("File %s contains %i records." % \
                              (updated_file,
                               get_nb_records_in_file(updated_file)))
            active_files_list = updated_files_list
            write_message("authorlist extraction step ended")
        # fulltext phase
        if 't' in postmode:
            write_message("full-text attachment step started")
            # Attaching fulltext
            updated_files_list = []
            i = 0
            for active_file in active_files_list:
                identifiers = harvested_identifier_list[i]
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Attaching fulltext to records harvested from %s (%i/%i)" % \
                                     (reponame, i, len(active_files_list)))
                updated_file = "%s.fulltext" % (active_file.split('.')[0],)
                updated_files_list.append(updated_file)
                (exitcode, err_msg) = call_fulltext(active_file,
                                                    updated_file,
                                                    identifiers,
                                                    downloaded_material_dict)
                if exitcode == 0:
                    write_message("fulltext from %s was successfully attached" % \
                                  (active_file,))
                else:
                    write_message("an error occurred while attaching fulltext to %s:\n%s" % \
                                  (active_file, err_msg))
                    error_happened_p = 2
                    continue
            # print stats:
            for updated_file in updated_files_list:
                write_message("File %s contains %i records." % \
                              (updated_file,
                               get_nb_records_in_file(updated_file)))
            active_files_list = updated_files_list
            write_message("full-text attachment step ended")
        # Filter-phase
        if 'f' in postmode:
            write_message("filtering step started")
            # first call bibfilter:
            res = 0
            i = 0
            for active_file in active_files_list:
                i += 1
                task_sleep_now_if_required()
                task_update_progress("Filtering material harvested from %s (%i/%i)" % \
                                     (reponame, \
                                      i, \
                                      len(active_files_list)))
                (exitcode, err_msg) = call_bibfilter(bibfilterprogram, active_file)

                if exitcode == 0:
                    write_message("%s was successfully bibfiltered" % \
                                  (active_file,))
                else:
                    write_message("an error occurred while bibfiltering %s:\n%s" % \
                                  (active_file, err_msg))
                    error_happened_p = 2
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
            write_message("filtering step ended")
        # Upload files
        if "u" in postmode:
            write_message("upload step started")
            if 'f' in postmode:
                # upload filtered files
                uploaded = False
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
                                              ["-i"], oai_src_id=repos[0][0])
                        uploaded = True
                    task_sleep_now_if_required()
                    if get_nb_records_in_file(active_file + ".correct.xml") > 0:
                        task_update_progress("Uploading corrections for records harvested from %s (%i/%i)" % \
                                             (reponame, \
                                              i, \
                                              len(active_files_list)))
                        res += call_bibupload(active_file + ".correct.xml", \
                                              ["-c"], oai_src_id=repos[0][0])
                        uploaded = True
                    if get_nb_records_in_file(active_file + ".append.xml") > 0:
                        task_update_progress("Uploading additions for records harvested from %s (%i/%i)" % \
                                             (reponame, \
                                              i, \
                                              len(active_files_list)))
                        res += call_bibupload(active_file + ".append.xml", \
                                              ["-a"], oai_src_id=repos[0][0])
                        uploaded = True
                    if get_nb_records_in_file(active_file + ".holdingpen.xml") > 0:
                        task_update_progress("Uploading records harvested from %s to holding pen (%i/%i)" % \
                                             (reponame, \
                                              i, \
                                              len(active_files_list)))
                        res += call_bibupload(active_file + ".holdingpen.xml", \
                                              ["-o"], oai_src_id=repos[0][0])
                        uploaded = True
                if len(active_files_list) > 0:
                    if res == 0:
                        if uploaded:
                            write_message("material harvested from source %s was successfully uploaded" % \
                                          (reponame,))
                        else:
                            write_message("nothing to upload")
                    else:
                        write_message("an error occurred while uploading harvest from %s" % (reponame,))
                        error_happened_p = 2
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
                        res += call_bibupload(active_file, oai_src_id=repos[0][0])
                        uploaded = True
                    if res == 0:
                        if uploaded:
                            write_message("material harvested from source %s was successfully uploaded" % \
                                          (reponame,))
                        else:
                            write_message("nothing to upload")
                    else:
                        write_message("an error occurred while uploading harvest from %s" % (reponame,))
                        error_happened_p = 2
                        continue
            write_message("upload step ended")

            if CFG_INSPIRE_SITE:
                # Launch BibIndex,Webcoll update task to show uploaded content quickly
                task_low_level_submission("bibindex", "oai", *tuple(['-w', 'reportnumber,collection', '-P', '6']))
                task_low_level_submission("webcoll", "oai", *tuple(['-c', 'HEP', '-P', '6']))
        write_message("post-harvest processes ended")
    if error_happened_p:
        if CFG_OAI_FAILED_HARVESTING_STOP_QUEUE == 0 or \
           not task_get_task_param("sleeptime") or \
           error_happened_p > 1:
            # Admin want BibSched to stop, or the task is not set to
            # run at a later date: we must stop the queue.
            write_message("An error occurred. Task is configured to stop")
            return False
        else:
            # An error happened, but it can be recovered at next run
            # (task is re-scheduled) and admin set BibSched to
            # continue even after failure.
            write_message("An error occurred, but task is configured to continue")
            if CFG_OAI_FAILED_HARVESTING_EMAILS_ADMIN:
                try:
                    raise InvenioOAIHarvestWarning("OAIHarvest (task #%s) failed at fully harvesting source(s) %s. BibSched has NOT been stopped, and OAIHarvest will try to recover at next run" % (task_get_task_param("task_id"), ", ".join([repo[0][6] for repo in reposlist]),))
                except InvenioOAIHarvestWarning, e:
                    register_exception(stream='warning', alert_admin=True)
            return True
    else:
        return True

def collect_identifiers(harvested_file_list):
    """Collects all OAI PMH identifiers from each file in the list
    and adds them to a list of identifiers per file.

    @param harvested_file_list: list of filepaths to harvested files

    @return list of lists, containing each files' identifier list"""
    result = []
    for harvested_file in harvested_file_list:
        try:
            fd_active = open(harvested_file)
        except IOError:
            write_message("Error opening harvested file '%s'. Skipping.." % (harvested_file,))
            continue
        data = fd_active.read()
        fd_active.close()
        result.append(REGEXP_OAI_ID.findall(data))
    return result

def remove_duplicates(harvested_file_list):
    """
    Go through a list of harvested files and remove any duplicate records.
    """
    harvested_identifiers = []
    for harvested_file in harvested_file_list:
        # Firstly, rename original file to temporary name
        try:
            os.rename(harvested_file, "%s~" % (harvested_file,))
        except OSError:
            write_message("Error renaming harvested file '%s'. Skipping.." % (harvested_file,))
            continue
        # Secondly, open files for writing and reading
        try:
            updated_harvested_file = open(harvested_file, 'w')
            original_harvested_file = open("%s~" % (harvested_file,))
        except IOError:
            write_message("Error opening harvested file '%s'. Skipping.." % (harvested_file,))
            continue
        data = original_harvested_file.read()
        original_harvested_file.close()

        # Get and write OAI-PMH XML header data to updated file
        header_index_end = data.find("<ListRecords>") + len("<ListRecords>")
        updated_harvested_file.write("%s\n" % (data[:header_index_end],))

        # By checking the OAI ID we write all records not written previously (in any file)
        harvested_records = REGEXP_RECORD.findall(data)
        for record in harvested_records:
            oai_identifier = REGEXP_OAI_ID.search(record)
            if oai_identifier != None and oai_identifier.group(1) not in harvested_identifiers:
                updated_harvested_file.write("<record>%s</record>\n" % (record,))
                harvested_identifiers.append(oai_identifier.group(1))
        updated_harvested_file.write("</ListRecords>\n</OAI-PMH>\n")
        updated_harvested_file.close()

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
                    fro=None, until=None, setspecs=None,
                    user=None, password=None, cert_file=None,
                    key_file=None, method="POST"):
    """
    Retrieve OAI records from given repository, with given arguments
    """
    try:
        (addressing_scheme, network_location, path, dummy1, \
         dummy2, dummy3) = urlparse.urlparse(baseurl)
        secure = (addressing_scheme == "https")

        http_param_dict = {'verb': "ListRecords",
                           'metadataPrefix': prefix}
        if fro:
            http_param_dict['from'] = fro
        if until:
            http_param_dict['until'] = until
        sets = None
        if setspecs:
            sets = [oai_set.strip() for oai_set in setspecs.split(' ')]

        harvested_files = oai_harvest_getter.harvest(network_location, path, http_param_dict, method, harvestpath,
                                   sets, secure, user, password, cert_file, key_file)
        remove_duplicates(harvested_files)
        return (1, harvested_files)
    except (StandardError, oai_harvest_getter.InvenioOAIRequestError), e:
        return (0, e)

def call_bibconvert(config, harvestpath, convertpath):
    """ Call BibConvert to convert file given at 'harvestpath' with
    conversion template 'config', and save the result in file at
    'convertpath'.

    Returns status exit code of the conversion, as well as error
    messages, if any
    """
    exitcode, dummy, cmd_stderr = \
        run_shell_command(cmd="%s/bibconvert -c %s < %s", \
                          args=(CFG_BINDIR, config, harvestpath), filename_out=convertpath)
    return (exitcode, cmd_stderr)

def call_plotextractor(active_file, extracted_file, harvested_identifier_list, \
                       downloaded_files):
    """
    Function that generates proper MARCXML containing harvested plots for
    each record.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file where the final results will be saved
    @param harvested_identifier_list: list of OAI identifiers for this active_file
    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.

    @return: exitcode and any error messages as: (exitcode, err_msg)
    """
    all_err_msg = []
    exitcode = 0
    # Read in active file
    recs_fd = open(active_file, 'r')
    records = recs_fd.read()
    recs_fd.close()

    # Find all record
    record_xmls = REGEXP_RECORD.findall(records)
    updated_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    updated_xml.append('<collection>')
    i = 0
    for record_xml in record_xmls:
        current_exitcode = 0
        identifier = harvested_identifier_list[i]
        i += 1
        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        updated_xml.append("<record>")
        updated_xml.append(record_xml)
        if "tarball" not in downloaded_files[identifier]:
            current_exitcode, err_msg, tarball, dummy = \
                        plotextractor_harvest(identifier, active_file, selection=["tarball"])
            if current_exitcode != 0:
                exitcode = current_exitcode
                all_err_msg.append(err_msg)
            else:
                downloaded_files[identifier]["tarball"] = tarball
        if current_exitcode == 0:
            plotextracted_xml_path = process_single(downloaded_files[identifier]["tarball"])
            if plotextracted_xml_path != None:
                # We store the path to the directory the tarball contents live
                downloaded_files[identifier]["tarball-extracted"] = os.path.split(plotextracted_xml_path)[0]
                # Read and grab MARCXML from plotextractor run
                plotsxml_fd = open(plotextracted_xml_path, 'r')
                plotextracted_xml = plotsxml_fd.read()
                plotsxml_fd.close()
                re_list = REGEXP_RECORD.findall(plotextracted_xml)
                if re_list != []:
                    updated_xml.append(re_list[0])
        updated_xml.append("</record>")
    updated_xml.append('</collection>')
    # Write to file
    file_fd = open(extracted_file, 'w')
    file_fd.write("\n".join(updated_xml))
    file_fd.close()
    if len(all_err_msg) > 0:
        return exitcode, "\n".join(all_err_msg)
    return exitcode, ""

def call_refextract(active_file, extracted_file, harvested_identifier_list,
                    downloaded_files):
    """
    Function that calls refextractor to extract references and attach them to
    harvested records. It will download the fulltext-pdf for each identifier
    if necessary.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file where the final results will be saved
    @param harvested_identifier_list: list of OAI identifiers for this active_file
    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.

    @return: exitcode and any error messages as: (exitcode, all_err_msg)
    """
    all_err_msg = []
    exitcode = 0
    flag = ""
    if CFG_INSPIRE_SITE == 1:
        flag = "--inspire --kb-journal '%s/bibedit/refextract-journal-titles-INSPIRE.kb'" \
                % (CFG_ETCDIR,)
    # Read in active file
    recs_fd = open(active_file, 'r')
    records = recs_fd.read()
    recs_fd.close()

    # Find all record
    record_xmls = REGEXP_RECORD.findall(records)
    updated_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    updated_xml.append('<collection>')
    i = 0
    for record_xml in record_xmls:
        current_exitcode = 0
        identifier = harvested_identifier_list[i]
        i += 1
        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        updated_xml.append("<record>")
        updated_xml.append(record_xml)
        if "pdf" not in downloaded_files[identifier]:
            current_exitcode, err_msg, dummy, pdf = \
                        plotextractor_harvest(identifier, active_file, selection=["pdf"])
            if current_exitcode != 0:
                exitcode = current_exitcode
                all_err_msg.append(err_msg)
            else:
                downloaded_files[identifier]["pdf"] = pdf
        if current_exitcode == 0:
            current_exitcode, cmd_stdout, err_msg = run_shell_command(cmd="%s/refextract %s -f 1:'%s'" % \
                                                (CFG_BINDIR, flag, downloaded_files[identifier]["pdf"]))
            if err_msg != "" or current_exitcode != 0:
                exitcode = current_exitcode
                all_err_msg.append("Error extracting references from id: %s\nError:%s" % \
                         (identifier, err_msg))
            else:
                references_xml = REGEXP_REFS.search(cmd_stdout)
                if references_xml:
                    updated_xml.append(references_xml.group(1))
        updated_xml.append("</record>")
    updated_xml.append('</collection>')
    # Write to file
    file_fd = open(extracted_file, 'w')
    file_fd.write("\n".join(updated_xml))
    file_fd.close()
    if len(all_err_msg) > 0:
        return exitcode, "\n".join(all_err_msg)
    return exitcode, ""

def call_authorlist_extract(active_file, extracted_file, harvested_identifier_list,
                            downloaded_files):
    """
    Function that will look in harvested tarball for any authorlists. If found
    it will extract and convert the authors using a XSLT stylesheet.

    @param active_file: path to the currently processed file
    @type active_file: string

    @param extracted_file: path to the file where the final results will be saved
    @type extracted_file: string

    @param harvested_identifier_list: list of OAI identifiers for this active_file
    @type harvested_identifier_list: list

    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.
    @type downloaded_files: dict

    @return: exitcode and any error messages as: (exitcode, all_err_msg)
    @rtype: tuple
    """
    all_err_msg = []
    exitcode = 0

    # Read in active file
    recs_fd = open(active_file, 'r')
    records = recs_fd.read()
    recs_fd.close()

    # Find all records
    record_xmls = REGEXP_RECORD.findall(records)
    updated_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    updated_xml.append('<collection>')
    i = 0
    for record_xml in record_xmls:
        current_exitcode = 0
        identifier = harvested_identifier_list[i]
        i += 1
        # Grab BibRec instance of current record for later amending
        existing_record, status_code, dummy1 = create_record("<record>%s</record>" % (record_xml,))
        if status_code == 0:
            all_err_msg.append("Error parsing record, skipping authorlist extraction of: %s\n" % \
                               (identifier,))
            updated_xml.append("<record>%s</record>" % (record_xml,))
            continue
        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        if "tarball" not in downloaded_files[identifier]:
            current_exitcode, err_msg, tarball, dummy = \
                        plotextractor_harvest(identifier, active_file, selection=["tarball"])
            if current_exitcode != 0:
                exitcode = current_exitcode
                all_err_msg.append(err_msg)
            else:
                downloaded_files[identifier]["tarball"] = tarball
        if current_exitcode == 0:
            current_exitcode, err_msg, authorlist_xml_path = authorlist_extract(downloaded_files[identifier]["tarball"], \
                                                                       identifier, downloaded_files)
            if current_exitcode != 0:
                exitcode = current_exitcode
                all_err_msg.append("Error extracting authors from id: %s\nError:%s" % \
                         (identifier, err_msg))
            elif authorlist_xml_path is not None:
                ## Authorlist found
                # Read and create BibRec
                xml_fd = open(authorlist_xml_path, 'r')
                author_xml = xml_fd.read()
                xml_fd.close()
                authorlist_record = create_records(author_xml)
                if len(authorlist_record) == 1:
                    if authorlist_record[0][0] == None:
                        all_err_msg.append("Error parsing authorlist record for id: %s" % \
                             (identifier,))
                        continue
                    authorlist_record = authorlist_record[0][0]
                    # Convert any LaTeX symbols in authornames
                    translate_fieldvalues_from_latex(authorlist_record, '100', code='a')
                    translate_fieldvalues_from_latex(authorlist_record, '700', code='a')
                    # Look for any UNDEFINED fields in authorlist
                    key = "UNDEFINED"
                    matching_fields = record_find_matching_fields(key, authorlist_record, tag='100') \
                                      + record_find_matching_fields(key, authorlist_record, tag='700')
                    if len(matching_fields) > 0 and bibcatalog_system != None:
                        # UNDEFINED found. Create ticket in author queue
                        ticketid = create_authorlist_ticket(matching_fields, identifier)
                        if ticketid:
                            write_message("authorlist RT ticket %d submitted for %s" % (ticketid, identifier))
                        else:
                            all_err_msg.append("Error while submitting RT ticket for %s" % (identifier,))
                    # Replace 100,700 fields of original record with extracted fields
                    record_delete_fields(existing_record, '100')
                    record_delete_fields(existing_record, '700')
                    first_author = record_get_field_instances(authorlist_record, '100')
                    additional_authors = record_get_field_instances(authorlist_record, '700')
                    record_add_fields(existing_record, '100', first_author)
                    record_add_fields(existing_record, '700', additional_authors)
        updated_xml.append(record_xml_output(existing_record))
    updated_xml.append('</collection>')
    # Write to file
    file_fd = open(extracted_file, 'w')
    file_fd.write("\n".join(updated_xml))
    file_fd.close()

    if len(all_err_msg) > 0:
        return exitcode, all_err_msg
    return exitcode, ""

def call_fulltext(active_file, extracted_file, harvested_identifier_list,
                  downloaded_files):
    """
    Function that calls attach FFT tag for full-text pdf to harvested records.
    It will download the fulltext-pdf for each identifier if necessary.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file where the final results will be saved
    @param harvested_identifier_list: list of OAI identifiers for this active_file
    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.

    @return: exitcode and any error messages as: (exitcode, err_msg)
    """
    all_err_msg = []
    exitcode = 0
    # Read in active file
    recs_fd = open(active_file, 'r')
    records = recs_fd.read()
    recs_fd.close()

    # Set doctype FIXME: Remove when parameters are introduced to post-process steps
    if CFG_INSPIRE_SITE == 1:
        doctype = "arXiv"
    elif CFG_CERN_SITE == 1:
        doctype = ""
    else:
        doctype = ""

    # Find all records
    record_xmls = REGEXP_RECORD.findall(records)
    updated_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    updated_xml.append('<collection>')
    i = 0
    for record_xml in record_xmls:
        current_exitcode = 0
        identifier = harvested_identifier_list[i]
        i += 1
        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        updated_xml.append("<record>")
        updated_xml.append(record_xml)
        if "pdf" not in downloaded_files[identifier]:
            current_exitcode, err_msg, dummy, pdf = \
                        plotextractor_harvest(identifier, active_file, selection=["pdf"])
            if current_exitcode != 0:
                exitcode = current_exitcode
                all_err_msg.append(err_msg)
            else:
                downloaded_files[identifier]["pdf"] = pdf
        if current_exitcode == 0:
            fulltext_xml = """  <datafield tag="FFT" ind1=" " ind2=" ">
    <subfield code="a">%(url)s</subfield>
    <subfield code="t">%(doctype)s</subfield>
  </datafield>""" % {'url': downloaded_files[identifier]["pdf"],
                     'doctype': doctype}
            updated_xml.append(fulltext_xml)
        updated_xml.append("</record>")
    updated_xml.append('</collection>')
    # Write to file
    file_fd = open(extracted_file, 'w')
    file_fd.write("\n".join(updated_xml))
    file_fd.close()

    if len(all_err_msg) > 0:
        return exitcode, "\n".join(all_err_msg)
    return exitcode, ""


def authorlist_extract(tarball_path, identifier, downloaded_files):
    """
    Try to extract the tarball given, if not already extracted, and look for
    any XML files that could be authorlists. If any is found, use a XSLT stylesheet
    to transform the authorlist into MARCXML author-fields, and return the full path
    of resulting conversion.

    @param tarball_path: path to the tarball to check
    @type tarball_path: string

    @param identifier: OAI Identifier to the current record
    @type identifier: string

    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.
    @type downloaded_files: dict

    @return: path to converted authorlist together with exitcode and any error messages as:
             (exitcode, err_msg, authorlist_path)
    @rtype: tuple
    """
    all_err_msg = []
    exitcode = 0
    if "tarball-extracted" not in downloaded_files[identifier]:
        # tarball has not been extracted
        tar_dir, dummy = get_defaults(tarball=tarball_path, sdir=CFG_TMPDIR, refno_url="")
        try:
            dummy = untar(tarball_path, tar_dir)
        except Timeout:
            all_err_msg.append("Timeout during tarball extraction of %s" % (tarball_path,))
            exitcode = 1
            return  exitcode, "\n".join(all_err_msg), None
        downloaded_files[identifier]["tarball-extracted"] = tar_dir
    # tarball is now surely extracted, so we try to fetch all XML in the folder
    xml_files_list = find_matching_files(downloaded_files[identifier]["tarball-extracted"], \
                                         ["xml"])
    # Try to convert authorlist candidates, returning on first success
    for xml_file in xml_files_list:
        xml_file_fd = open(xml_file, "r")
        xml_content = xml_file_fd.read()
        xml_file_fd.close()
        match = REGEXP_AUTHLIST.findall(xml_content)
        if match != []:
            tempfile_fd, temp_authorlist_path = tempfile.mkstemp(suffix=".xml", prefix="authorlist_temp")
            os.write(tempfile_fd, match[0])
            os.close(tempfile_fd)
            # Generate file to store conversion results
            newfile_fd, authorlist_resultxml_path = tempfile.mkstemp(suffix=".xml", prefix="authorlist_MARCXML", \
                                                             dir=downloaded_files[identifier]["tarball-extracted"])
            os.close(newfile_fd)
            exitcode, cmd_stderr = call_bibconvert(config=CFG_OAI_AUTHORLIST_POSTMODE_STYLESHEET, \
                                                   harvestpath=temp_authorlist_path, \
                                                   convertpath=authorlist_resultxml_path)
            if cmd_stderr == "" and exitcode == 0:
                # Success!
                return 0, "", authorlist_resultxml_path
    # No valid authorlist found
    return 0, "", None

def plotextractor_harvest(identifier, active_file, selection=["pdf", "tarball"]):
    """
    Function that calls plotextractor library to download selected material,
    i.e. tarball or pdf, for passed identifier. Returns paths to respective files.

    @param identifier: OAI identifier of the record to harvest
    @param active_file: path to the currently processed file
    @param selection: list of materials to harvest

    @return: exitcode, errormessages and paths to harvested tarball and fulltexts
             (exitcode, err_msg, tarball, pdf)
    """
    all_err_msg = []
    exitcode = 0
    active_dir, active_name = os.path.split(active_file)
    # turn oaiharvest_23_1_20110214161632_converted -> oaiharvest_23_1_material
    # to let harvested material in same folder structure
    active_name = "_".join(active_name.split('_')[:-2]) + "_material"
    extract_path = make_single_directory(active_dir, active_name)
    tarball, pdf = harvest_single(identifier, extract_path, selection)
    time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)
    if tarball == None and "tarball" in selection:
        all_err_msg.append("Error harvesting tarball from id: %s %s" % \
                     (identifier, extract_path))
        exitcode = 1
    if pdf == None and "pdf" in selection:
        all_err_msg.append("Error harvesting full-text from id: %s %s" % \
                     (identifier, extract_path))
        exitcode = 1
    return exitcode, "\n".join(all_err_msg), tarball, pdf

def find_matching_files(basedir, filetypes):
    """
    This functions tries to find all files matching given filetypes by looking at
    all the files and filenames in the given directory, including subdirectories.

    @param basedir: full path to base directory to search in
    @type basedir: string

    @param filetypes: list of filetypes, extensions
    @type filetypes: list

    @return: exitcode and any error messages as: (exitcode, err_msg)
    @rtype: tuple
    """
    files_list = []
    for dirpath, dummy0, filenames in os.walk(basedir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            dummy1, cmd_out, dummy2 = run_shell_command('file %s', (full_path,))
            for filetype in filetypes:
                if cmd_out.lower().find(filetype) > -1:
                    files_list.append(full_path)
                elif filename.split('.')[-1].lower() == filetype:
                    files_list.append(full_path)
    return files_list

def translate_fieldvalues_from_latex(record, tag, code='', encoding='utf-8'):
    """
    Given a record and field tag, this function will modify the record by
    translating the subfield values of found fields from LaTeX to chosen
    encoding for all the subfields with given code (or all if no code is given).

    @param record: record to modify, in BibRec style structure
    @type record: dict

    @param tag: tag of fields to modify
    @type tag: string

    @param code: restrict the translation to a given subfield code
    @type code: string

    @param encoding: scharacter encoding for the new value. Defaults to UTF-8.
    @type encoding: string
    """
    field_list = record_get_field_instances(record, tag)
    for field in field_list:
        subfields = field[0]
        subfield_index = 0
        for subfield_code, subfield_value in subfields:
            if code == '' or subfield_code == code:
                newvalue = translate_latex2unicode(subfield_value).encode(encoding)
                record_modify_subfield(record, tag, subfield_code, newvalue, \
                                       subfield_index, field_position_global=field[4])
            subfield_index += 1

def create_authorlist_ticket(matching_fields, identifier):
    """
    This function will submit a ticket generated by UNDEFINED affiliations
    in extracted authors from collaboration authorlists.

    @param matching_fields: list of (tag, field_instances) for UNDEFINED nodes
    @type matching_fields: list

    @param identifier: OAI identifier of record
    @type identifier: string

    @return: return the ID of the created ticket, or None on failure
    @rtype: int or None
    """
    if bibcatalog_system is None:
        return None
    subject = "[OAI Harvest] UNDEFINED affiliations for record %s" % (identifier,)
    text = """
Harvested record with identifier %(ident)s has had its authorlist extracted and contains some UNDEFINED affiliations.

To see the record, go here: %(baseurl)s/search?p=%(ident)s

If the record is not there yet, try again later. It may take some time for it to load into the system.

List of unidentified fields:
%(fields)s
    """ % {
           'ident' : identifier,
           'baseurl' : CFG_SITE_URL,
           'fields' : "\n".join([field_xml_output(field, tag) for tag, field_instances in matching_fields \
                                for field in field_instances])
           }
    queue = "Authors"
    ticketid = bibcatalog_system.ticket_submit(subject=subject, queue=queue)
    if bibcatalog_system.ticket_comment(None, ticketid, text) == None:
        write_message("Error: commenting on ticket %s failed." % (str(ticketid),))
    return ticketid

def create_oaiharvest_log(task_id, oai_src_id, marcxmlfile):
    """
    Function which creates the harvesting logs
    @param task_id bibupload task id
    """
    file_fd = open(marcxmlfile, "r")
    xml_content = file_fd.read(-1)
    file_fd.close()
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

def call_bibupload(marcxmlfile, mode=None, oai_src_id= -1):
    """Call bibupload in insert mode on MARCXMLFILE."""
    if mode is None:
        mode = ["-r", "-i"]
    if os.path.exists(marcxmlfile):
        try:
            args = mode
            # Add custom name 'oai' with priority 6 and file to upload to arguments
            #FIXME: allow per-harvest arguments
            args.extend(["-N", "oai", "-P", "6", marcxmlfile])
            task_id = task_low_level_submission("bibupload", "oaiharvest", *tuple(args))
            create_oaiharvest_log(task_id, oai_src_id, marcxmlfile)
        except Exception, msg:
            write_message("An exception during submitting oaiharvest task occured : %s " % (str(msg)))
            return 1
        return 0
    else:
        write_message("marcxmlfile %s does not exist" % (marcxmlfile,))
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

    @return: exitcode and any error messages as: (exitcode, err_msg)
    """
    all_err_msg = []
    exitcode = 0
    if bibfilterprogram:
        if not os.path.isfile(bibfilterprogram):
            all_err_msg.append("bibfilterprogram %s is not a file" %
                (bibfilterprogram,))
            exitcode = 1
        elif not os.path.isfile(marcxmlfile):
            all_err_msg.append("marcxmlfile %s is not a file" % (marcxmlfile,))
            exitcode = 1
        else:
            exitcode, dummy, cmd_stderr = run_shell_command(cmd="%s '%s'", \
                                                             args=(bibfilterprogram, \
                                                                   marcxmlfile))
            if exitcode != 0 or cmd_stderr != "":
                all_err_msg.append("Error while running filtering script on %s\nError:%s" % \
                         (marcxmlfile, cmd_stderr))
    else:
        try:
            all_err_msg.append("no bibfilterprogram defined, copying %s only" %
                (marcxmlfile,))
            shutil.copy(marcxmlfile, marcxmlfile + ".insert.xml")
        except:
            all_err_msg.append("cannot copy %s into %s.insert.xml" % (marcxmlfile, marcxmlfile))
        exitcode = 1
    return exitcode, "\n".join(all_err_msg)

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

def usage(exitcode=0, msg=""):
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
                (addressing_scheme, network_location, path, dummy1, \
                 dummy2, dummy3) = urlparse.urlparse(base_url)
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
                    except KeyboardInterrupt, error:
                        sys.stderr.write("\n%s\n" % (error,))
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
    task_init(authorization_action='runoaiharvest',
              authorization_msg="oaiharvest Task Submission",
              description="""
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
            help_specific_usage='Manual single-shot harvesting mode:\n'
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
