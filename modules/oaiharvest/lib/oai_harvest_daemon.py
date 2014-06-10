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
import shutil
import tempfile
import urlparse
import random
import traceback

from invenio.config import \
     CFG_BINDIR, \
     CFG_TMPSHAREDDIR, \
     CFG_INSPIRE_SITE, \
     CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT, \
     CFG_SITE_URL, \
     CFG_OAI_FAILED_HARVESTING_STOP_QUEUE, \
     CFG_OAI_FAILED_HARVESTING_EMAILS_ADMIN, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_TMPDIR
from invenio.oai_harvest_config import InvenioOAIHarvestWarning
from invenio.dbquery import deserialize_via_marshal
from invenio.bibtask import \
     task_get_task_param, \
     task_get_option, \
     task_set_option, \
     write_message, \
     task_init, \
     task_sleep_now_if_required, \
     task_update_progress, \
     task_low_level_submission
from invenio.bibrecord import create_records, \
                              create_record, record_add_fields, \
                              record_delete_fields, record_xml_output, \
                              record_get_field_instances, \
                              field_xml_output
from invenio import oai_harvest_getter
from invenio.errorlib import register_exception
from invenio.plotextractor_getter import harvest_single, make_single_directory
from invenio.plotextractor_converter import untar
from invenio.plotextractor import process_single, get_defaults
from invenio.shellutils import run_shell_command, Timeout
from invenio.bibedit_utils import record_find_matching_fields
from invenio.bibcatalog import BIBCATALOG_SYSTEM
from invenio.oai_harvest_dblayer import get_oai_src_by_name, \
                                        get_all_oai_src, \
                                        update_lastrun, \
                                        create_oaiharvest_log_str
from invenio.oai_harvest_utils import get_nb_records_in_file, \
                                      collect_identifiers, \
                                      remove_duplicates, \
                                      add_timestamp_and_timelag, \
                                      find_matching_files, \
                                      translate_fieldvalues_from_latex, \
                                      compare_timestamps_with_tolerance, \
                                      generate_harvest_report, \
                                      record_collect_oai_identifiers
from invenio.webuser import email_valid_p
from invenio.mailutils import send_email

import invenio.template
oaiharvest_templates = invenio.template.load('oai_harvest')

## precompile some often-used regexp for speed reasons:
REGEXP_OAI_ID = re.compile("<identifier.*?>(.*?)<\/identifier>", re.DOTALL)
REGEXP_RECORD = re.compile("<record.*?>(.*?)</record>", re.DOTALL)
REGEXP_REFS = re.compile("<record.*?>.*?<controlfield .*?>.*?</controlfield>(.*?)</record>", re.DOTALL)
REGEXP_AUTHLIST = re.compile("<collaborationauthorlist.*?</collaborationauthorlist>", re.DOTALL)


def task_run_core():
    """Run the harvesting task.  The row argument is the oaiharvest task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    reposlist = []
    datelist = []
    identifiers = None
    filepath_prefix = "%s/oaiharvest_%s" % (CFG_TMPSHAREDDIR, str(task_get_task_param("task_id")))
    ### go ahead: build up the reposlist
    if task_get_option("repository") is not None:
        ### user requests harvesting from selected repositories
        write_message("harvesting from selected repositories")
        for reposname in task_get_option("repository"):
            row = get_oai_src_by_name(reposname)
            if row == [] or len(row) != 1:
                write_message("source name %s is not valid" % (reposname,))
                continue
            else:
                reposlist.append(row[0])
    else:
        ### user requests harvesting from all repositories
        write_message("harvesting from all repositories in the database")
        reposlist = get_all_oai_src()

    ### go ahead: check if user requested from-until harvesting
    if task_get_option("dates"):
        ### for each repos simply perform a from-until date harvesting...
        ### no need to update anything
        for element in task_get_option("dates"):
            datelist.append(element)

    if task_get_option("identifier"):
        identifiers = task_get_option("identifier")

    # 0: no error
    # 1: "recoverable" error (don't stop queue)
    # 2: error (admin intervention needed)
    error_happened_p = 0

    j = 0
    for repository in reposlist:
        j += 1
        current_progress = "(%i/%i)" % (j, len(reposlist))
        task_sleep_now_if_required()
        if repository['arguments']:
            repository['arguments'] = deserialize_via_marshal(repository['arguments'])

        write_message("running with post-processes: %s" % (repository["postprocess"],))

        downloaded_material_dict = {}

        # Harvest phase
        harvested_files_list = []
        harvestpath = "%s_%d_%s_" % (filepath_prefix, j, time.strftime("%Y%m%d%H%M%S"))
        harvest_start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        harvested_files_list, error_code = harvest_step(repository, harvestpath, identifiers, datelist, current_progress)
        if harvested_files_list == None or len(harvested_files_list) < 1:
            if error_code:
                error_happened_p = error_code
                write_message("Error while harvesting %s. Skipping." % (repository["name"],))
            else:
                write_message("No records harvested for %s" % (repository["name"],))
            continue

        # Retrieve all OAI IDs and set active list
        harvested_identifier_list = collect_identifiers(harvested_files_list)
        active_files_list = harvested_files_list
        if len(active_files_list) != len(harvested_identifier_list):
            # Harvested files and its identifiers are 'out of sync', abort harvest
            write_message("Harvested files miss identifiers for %s" % (repository["name"],))
            continue

        # Harvesting done, now convert/extract/filter/upload as requested
        write_message("post-harvest processes started")

        post_process_functions = []

        # Convert?
        if 'c' in repository["postprocess"]:
            post_process_functions.append(convert_step)

        # Fulltext?
        if 't' in repository["postprocess"]:
            post_process_functions.append(fulltext_step)

        # Plotextract?
        if 'p' in repository["postprocess"]:
            post_process_functions.append(plotextract_step)

        # Refextract?
        if 'r' in repository["postprocess"]:
            post_process_functions.append(refextract_step)

        # Authorlist?
        if 'a' in repository["postprocess"]:
            post_process_functions.append(authorlist_step)

        # Filter?
        if 'f' in repository["postprocess"]:
            post_process_functions.append(filter_step)

        # Upload?
        if 'u' in repository["postprocess"]:
            post_process_functions.append(upload_step)

        uploaded_task_ids = []

        # Run the post-process functions
        for fun in post_process_functions:
            active_files_list, error_code = fun(repository=repository, \
                                                active_files_list=active_files_list, \
                                                downloaded_material_dict=downloaded_material_dict, \
                                                uploaded_task_ids=uploaded_task_ids)
            if error_code:
                error_happened_p = error_code
                continue
            # print stats:
            for active_files in active_files_list:
                write_message("File %s contains %i records." % \
                              (active_files,
                               get_nb_records_in_file(active_files)))
        write_message("post-harvest processes ended")

        # We got this far. Now we can actually update the last_run
        if not datelist and not identifiers and repository["frequency"] != 0:
            update_lastrun(repository["id"],
                           runtime=harvest_start_time)

        # Generate reports
        ticket_queue = task_get_option("create-ticket-in")
        notification_email = task_get_option("notify-email-to")
        if ticket_queue or notification_email:
            subject, text = generate_harvest_report(repository, harvested_identifier_list, \
                                                    uploaded_task_ids, active_files_list, \
                                                    task_specific_name=task_get_task_param("task_specific_name") or "", \
                                                    current_task_id=task_get_task_param("task_id"), \
                                                    manual_harvest=bool(identifiers), \
                                                    error_happened=bool(error_happened_p))
            # Create ticket for finished harvest?
            if ticket_queue:
                ticketid = create_ticket(ticket_queue, subject=subject, text=text)
                if ticketid:
                    write_message("Ticket %s submitted." % (str(ticketid),))

            # Send e-mail for finished harvest?
            if notification_email:
                send_email(fromaddr=CFG_SITE_SUPPORT_EMAIL, \
                           toaddr=notification_email, \
                           subject=subject, \
                           content=text)

    # All records from all repositories harvested. Check for any errors.
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
                    raise InvenioOAIHarvestWarning("OAIHarvest (task #%s) failed at fully harvesting source(s) %s. BibSched has NOT been stopped, and OAIHarvest will try to recover at next run" % (task_get_task_param("task_id"), ", ".join([repo['name'] for repo in reposlist]),))
                except InvenioOAIHarvestWarning:
                    register_exception(stream='warning', alert_admin=True)
            return True
    else:
        return True


def harvest_by_identifiers(repository, identifiers, harvestpath):
    """
    Harvest an OAI repository by identifiers.

    Given a repository "object" (dict from DB) and a list of OAI identifiers
    of records in the repository perform a OAI harvest using GetRecord for each.

    The records will be harvested into the specified filepath.
    """
    harvested_files_list = []
    count = 0
    error_happened = 0
    for oai_identifier in identifiers:
        count += 1
        task_update_progress("Harvesting from %s (%i/%i)" % \
                             (repository["name"], \
                              count, \
                              len(identifiers)))
        try:
            harvested_files_list.extend(oai_harvest_get(prefix=repository["metadataprefix"],
                                                        baseurl=repository["baseurl"],
                                                        harvestpath=harvestpath,
                                                        verb="GetRecord",
                                                        identifier=oai_identifier))
        except StandardError:
            # exception already dealt with, just noting the error.
            error_happened = 1
            continue

        write_message("identifier %s was harvested from %s" % \
                      (oai_identifier, repository["name"]))
    return harvested_files_list, error_happened


def harvest_by_dates(repository, harvestpath, fromdate=None, todate=None, progress=""):
    """
    Harvest an OAI repository by dates.

    Given a repository "object" (dict from DB) and from/to dates, this function will
    perform an OAI harvest request for records updated between the given dates.

    If no dates are given, the repository is harvested from the beginning.

    If you set fromdate == last-run and todate == None, then the repository
    will be harvested since last time (most common type).

    The records will be harvested into the specified filepath.
    """
    if fromdate and todate:
        dates = "from %s to %s" % (fromdate, todate)
    elif fromdate:
        dates = "from %s" % (fromdate,)
    else:
        dates = ""

    task_update_progress("Harvesting %s %s %s" % \
                         (repository["name"], \
                          dates,
                          progress))
    try:
        file_list = oai_harvest_get(prefix=repository["metadataprefix"],
                                    baseurl=repository["baseurl"],
                                    harvestpath=harvestpath,
                                    fro=fromdate,
                                    until=todate,
                                    setspecs=repository["setspecs"])
    except StandardError:
        # exception already dealt with, just noting the error.
        return [], 1

    return file_list, 0


def harvest_step(repository, harvestpath, identifiers, dates, current_progress):
    """
    Performs the entire harvesting step.

    Returns a tuple of (file_list, error_code)
    """
    harvested_files_list = None
    if identifiers:
        # Harvesting is done per identifier instead of server-updates
        write_message("about to harvest %d identifiers: %s" % \
                     (len(identifiers), ",".join(identifiers[:20],)))
        harvested_files_list, error_code = harvest_by_identifiers(repository, identifiers, harvestpath)
        if error_code:
            return [], error_code
        write_message("all records harvested from %s" % \
                      (repository["name"],))

    elif dates:
        # Dates are given so we harvest "from" -> "to" dates
        write_message("about to harvest %s from %s to %s" % \
                     (repository['name'], str(dates[0]), str(dates[1])))
        harvested_files_list, error_code = harvest_by_dates(repository, \
                                                            harvestpath, \
                                                            str(dates[0]), \
                                                            str(dates[1]), \
                                                            current_progress)
        if error_code:
            return [], error_code
        write_message("source %s was successfully harvested" % \
                      (repository["name"],))

    elif not dates and repository["lastrun"] is None and repository["frequency"] != 0:
        # First time we harvest from this repository
        write_message("source %s was never harvested before - harvesting whole repository" % \
                      (repository["name"],))
        harvested_files_list, error_code = harvest_by_dates(repository, harvestpath, current_progress)
        if error_code:
            return [], error_code
        write_message("source %s was successfully harvested" % \
                      (repository["name"],))

    elif not dates and repository["frequency"] != 0:
        # Just a regular update from last time it ran

        ### check that update is actually needed,
        ### i.e. lastrun+frequency>today
        timenow = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        lastrundate = re.sub(r'\.[0-9]+$', '',
            str(repository["lastrun"]))  # remove trailing .00
        timeinsec = int(repository["frequency"]) * 60 * 60
        updatedue = add_timestamp_and_timelag(lastrundate, timeinsec)
        proceed = compare_timestamps_with_tolerance(updatedue, timenow)
        if proceed != 1:
            # update needed!
            write_message("source %s is going to be updated" % (repository["name"],))
            fromdate = str(repository["lastrun"])
            # get rid of time of the day for the moment
            fromdate = fromdate.split()[0]
            harvested_files_list, error_code = harvest_by_dates(repository, harvestpath, \
                                                                fromdate=fromdate, \
                                                                progress=current_progress)
            if error_code:
                return [], error_code
            write_message("source %s was successfully harvested" % \
                          (repository["name"],))
        else:
            write_message("source %s does not need updating" % (repository["name"],))
            return [], 0  # No actual error here.

    elif not dates and repository["frequency"] == 0:
        write_message("source %s has frequency set to 'Never' so it will not be updated" % \
                      (repository["name"],))
        return [], 0  # No actual error here.
    return harvested_files_list, 0


def convert_step(repository, active_files_list, *args, **kwargs):
    """
    Performs the conversion step.
    """
    updated_files_list = []
    i = 0
    final_exit_code = 0
    write_message("conversion step started")
    for active_file in active_files_list:
        i += 1
        task_sleep_now_if_required()
        task_update_progress("Converting material harvested from %s (%i/%i)" % \
                             (repository["name"], \
                              i, \
                              len(active_files_list)))
        updated_file = "%s.converted" % (os.path.splitext(active_file)[0],)
        updated_files_list.append(updated_file)
        (exitcode, err_msg) = call_bibconvert(config=repository["arguments"]['c_stylesheet'],
                                              harvestpath=active_file,
                                              convertpath=updated_file)
        if exitcode == 0:
            write_message("harvested file %s was successfully converted" % \
                          (active_file,))
        else:
            write_message("an error occurred while converting %s:\n%s" % \
                          (active_file, err_msg))
            final_exit_code = 1
            continue

    write_message("conversion step ended")
    return updated_files_list, final_exit_code


def plotextract_step(repository, active_files_list, downloaded_material_dict, *args, **kwargs):
    """
    Performs the plotextraction step.
    """
    write_message("plotextraction step started")
    if not repository["arguments"]['p_extraction-source']:
        # No plotextractor type chosen, exit with failure
        write_message("Error: No plotextractor source type chosen!")
        return [], 1

    final_exit_code = 0

    # Download tarball for each harvested/converted record, then run plotextrator.
    # Update converted xml files with generated xml or add it for upload
    updated_files_list = []
    i = 0
    for active_file in active_files_list:
        i += 1
        task_sleep_now_if_required()
        task_update_progress("Extracting plots from harvested material from %s (%i/%i)" % \
                             (repository["name"], i, len(active_files_list)))
        updated_file = "%s.plotextracted" % (os.path.splitext(active_file)[0],)
        updated_files_list.append(updated_file)
        (exitcode, err_msg) = call_plotextractor(active_file,
                                                 updated_file,
                                                 downloaded_material_dict,
                                                 repository["arguments"]['p_extraction-source'],
                                                 repository["id"])
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
            final_exit_code = 1
            continue

    return updated_files_list, final_exit_code


def refextract_step(repository, active_files_list, downloaded_material_dict, *args, **kwargs):
    """
    Performs the reference extraction step.
    """
    updated_files_list = []
    final_exit_code = 0
    i = 0
    write_message("refextraction step started")
    for active_file in active_files_list:
        i += 1
        task_sleep_now_if_required()
        task_update_progress("Extracting references from material harvested from %s (%i/%i)" % \
                             (repository["name"], i, len(active_files_list)))
        updated_file = "%s.refextracted" % (os.path.splitext(active_file)[0],)
        updated_files_list.append(updated_file)
        (exitcode, err_msg) = call_refextract(active_file,
                                              updated_file,
                                              downloaded_material_dict,
                                              repository["arguments"],
                                              repository["id"])
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
            final_exit_code = 1
            continue

    return updated_files_list, final_exit_code


def authorlist_step(repository, active_files_list, downloaded_material_dict, *args, **kwargs):
    """
    Performs the special authorlist extraction step (Mostly INSPIRE/CERN related).
    """
    write_message("authorlist extraction step started")
    updated_files_list = []
    final_exit_code = 0
    i = 0
    for active_file in active_files_list:
        i += 1
        task_sleep_now_if_required()
        task_update_progress("Extracting any authorlists from material harvested from %s (%i/%i)" % \
                             (repository["name"], i, len(active_files_list)))
        updated_file = "%s.authextracted" % (os.path.splitext(active_file)[0],)
        updated_files_list.append(updated_file)
        (exitcode, err_msg) = call_authorlist_extract(active_file,
                                                      updated_file,
                                                      downloaded_material_dict,
                                                      repository["arguments"].get('a_rt-queue', ""),
                                                      repository["arguments"].get('a_stylesheet', "authorlist2marcxml.xsl"),
                                                      repository["id"])
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
            final_exit_code = 1
            continue

    return updated_files_list, final_exit_code


def fulltext_step(repository, active_files_list, downloaded_material_dict, *args, **kwargs):
    """
    Performs the fulltext download step.
    """
    write_message("full-text attachment step started")
    updated_files_list = []
    final_exit_code = 0
    i = 0
    for active_file in active_files_list:
        i += 1
        task_sleep_now_if_required()
        task_update_progress("Attaching fulltext to records harvested from %s (%i/%i)" % \
                             (repository["name"], i, len(active_files_list)))
        updated_file = "%s.fulltext" % (os.path.splitext(active_file)[0],)
        updated_files_list.append(updated_file)
        (exitcode, err_msg) = call_fulltext(active_file,
                                            updated_file,
                                            downloaded_material_dict,
                                            repository["arguments"].get('t_doctype', ""),
                                            repository["id"])
        if exitcode == 0:
            write_message("fulltext from %s was successfully attached" % \
                          (active_file,))
        else:
            write_message("an error occurred while attaching fulltext to %s:\n%s" % \
                          (active_file, err_msg))
            final_exit_code = 1
            continue

    return updated_files_list, final_exit_code


def filter_step(repository, active_files_list, *args, **kwargs):
    """
    Perform filtering step
    """
    write_message("filtering step started")
    updated_files_list = []
    final_exit_code = 0
    i = 0
    for active_file in active_files_list:
        i += 1
        task_sleep_now_if_required()
        task_update_progress("Filtering material harvested from %s (%i/%i)" % \
                             (repository["name"], \
                              i, \
                              len(active_files_list)))
        (exitcode, err_msg) = call_bibfilter(repository["arguments"]['f_filter-file'], active_file)

        if exitcode == 0:
            write_message("%s was successfully bibfiltered" % \
                          (active_file,))
        else:
            write_message("an error occurred while bibfiltering %s:\n%s" % \
                          (active_file, err_msg))
            final_exit_code = 1
            continue

        if os.path.exists("%s.insert.xml" % (active_file,)):
            updated_files_list.append("%s.insert.xml" % (active_file,))
        if os.path.exists("%s.correct.xml" % (active_file,)):
            updated_files_list.append("%s.correct.xml" % (active_file,))
        if os.path.exists("%s.append.xml" % (active_file,)):
            updated_files_list.append("%s.append.xml" % (active_file,))
        if os.path.exists("%s.holdingpen.xml" % (active_file,)):
            updated_files_list.append("%s.holdingpen.xml" % (active_file,))

    write_message("filtering step ended")
    return updated_files_list, final_exit_code


def upload_step(repository, active_files_list, uploaded_task_ids=None, *args, **kwargs):
    """
    Perform the upload step.
    """
    write_message("upload step started")
    if 'f' in repository["postprocess"]:
        upload_modes = {'.insert.xml': '-i',
                        '.correct.xml': '-c',
                        '.append.xml': '-a',
                        '.holdingpen.xml': '-o'}
    else:
        upload_modes = {'': '-ir'}

    i = 0
    last_upload_task_id = -1
    final_exit_code = 0
    # Get a random sequence ID that will allow for the tasks to be
    # run in order, regardless if parallel task execution is activated
    sequence_id = random.randrange(1, 4294967296)
    for active_file in active_files_list:
        task_sleep_now_if_required()
        i += 1
        task_update_progress("Uploading records harvested from %s (%i/%i)" % \
                            (repository["name"], \
                             i, \
                             len(active_files_list)))
        # Now we launch BibUpload tasks for the final MARCXML files
        for suffix, mode in upload_modes.items():
            # We check for each upload-mode in question.
            if not suffix or active_file.endswith(suffix):
                last_upload_task_id = call_bibupload(active_file, \
                                                     [mode], \
                                                     repository["id"], \
                                                     sequence_id, \
                                                     repository["arguments"].get('u_name', ""), \
                                                     repository["arguments"].get('u_priority', 5))
                if not last_upload_task_id:
                    final_exit_code = 2
                    write_message("an error occurred while uploading %s from %s" % \
                                  (active_file, repository["name"]))
                    break
                uploaded_task_ids.append(last_upload_task_id)
        else:
            write_message("material harvested from source %s was successfully uploaded" % \
                          (repository["name"],))
    if len(active_files_list) == 0:
        write_message("nothing to upload")
    write_message("upload step ended")
    return active_files_list, final_exit_code


def oai_harvest_get(prefix, baseurl, harvestpath,
                    fro=None, until=None, setspecs=None,
                    user=None, password=None, cert_file=None,
                    key_file=None, method="POST", verb="ListRecords",
                    identifier=""):
    """
    Retrieve OAI records from given repository, with given arguments
    """
    try:
        (addressing_scheme, network_location, path, dummy1, \
         dummy2, dummy3) = urlparse.urlparse(baseurl)
        secure = (addressing_scheme == "https")

        http_param_dict = {'verb': verb,
                           'metadataPrefix': prefix}
        if identifier:
            http_param_dict['identifier'] = identifier
        if fro:
            http_param_dict['from'] = fro
        if until:
            http_param_dict['until'] = until
        sets = None
        if setspecs:
            sets = [oai_set.strip() for oai_set in setspecs.split(' ')]

        harvested_files = oai_harvest_getter.harvest(network_location, path, http_param_dict, method, harvestpath,
                                   sets, secure, user, password, cert_file, key_file)
        if verb == "ListRecords":
            remove_duplicates(harvested_files)
        return harvested_files
    except (StandardError, oai_harvest_getter.InvenioOAIRequestError), e:
        write_message("An error occurred while harvesting from %s: %s\n%s\n"
                      % (baseurl, str(e), traceback.print_exc()))
        register_exception()
        raise

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

def call_plotextractor(active_file, extracted_file,
                       downloaded_files, plotextractor_types, source_id):
    """
    Function that generates proper MARCXML containing harvested plots for
    each record.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file where the final results will be saved
    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.
    @param plotextractor_types: list of names of which plotextractor(s) to use (latex or pdf)
        (pdf is currently ignored).
    @param source_id: the repository identifier

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
    for record_xml in record_xmls:
        current_exitcode = 0

        id_list = record_collect_oai_identifiers("<record>" + record_xml + "</record>")
        # We bet on the first one.
        identifier = None
        for oai_id in id_list:
            if "oai" in oai_id.lower():
                identifier = oai_id
                break
        write_message("OAI identifier found in record: %s" % (identifier,), verbose=6)

        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        updated_xml.append("<record>")
        updated_xml.append(record_xml)
        if not oaiharvest_templates.tmpl_should_process_record_with_mode(record_xml, 'p', source_id):
            # We skip this record
            updated_xml.append("</record>")
            continue
        if 'latex' in plotextractor_types:
            # Run LaTeX plotextractor
            if "tarball" not in downloaded_files[identifier]:
                current_exitcode, err_msg, tarball, dummy = \
                            plotextractor_harvest(identifier, active_file, selection=["tarball"])
                if current_exitcode != 0:
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
                        # Add final FFT info from LaTeX plotextractor to record.
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

def call_refextract(active_file, extracted_file,
                    downloaded_files, arguments, source_id):
    """
    Function that calls refextractor to extract references and attach them to
    harvested records. It will download the fulltext-pdf for each identifier
    if necessary.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file where the final results will be saved
    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.
    @param arguments: dict of post-process arguments.
                      r_format, r_kb-journal-file, r_kb-rep-no-file
    @param source_id: the repository identifier
    @return: exitcode and any error messages as: (exitcode, all_err_msg)
    """
    all_err_msg = []
    exitcode = 0

    flags = []
    if arguments.get('r_format'):
        flags.append("--%s" % (arguments['r_format'],))
    elif CFG_INSPIRE_SITE:
        flags.append("--inspire")
    if arguments.get('r_kb-journal-file'):
        flags.append("--kb-journal '%s'" % (arguments['r_kb-journal-file'],))
    if arguments.get('r_kb-rep-no-file'):
        flags.append("--kb-report-number '%s'" % (arguments['r_kb-rep-no-file'],))

    flag = " ".join(flags)
    # Read in active file
    recs_fd = open(active_file, 'r')
    records = recs_fd.read()
    recs_fd.close()

    # Find all record
    record_xmls = REGEXP_RECORD.findall(records)
    updated_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    updated_xml.append('<collection>')
    for record_xml in record_xmls:
        current_exitcode = 0

        id_list = record_collect_oai_identifiers("<record>" + record_xml + "</record>")
        # We bet on the first one.
        identifier = None
        for oai_id in id_list:
            if "oai" in oai_id.lower():
                identifier = oai_id
                break
        write_message("OAI identifier found in record: %s" % (identifier,), verbose=6)

        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        updated_xml.append("<record>")
        updated_xml.append(record_xml)
        if not oaiharvest_templates.tmpl_should_process_record_with_mode(record_xml, 'p', source_id):
            # We skip this record
            updated_xml.append("</record>")
            continue
        if "pdf" not in downloaded_files[identifier]:
            current_exitcode, err_msg, dummy, pdf = \
                        plotextractor_harvest(identifier, active_file, selection=["pdf"])
            if current_exitcode != 0:
                all_err_msg.append(err_msg)
            else:
                downloaded_files[identifier]["pdf"] = pdf
        if current_exitcode == 0:
            current_exitcode, cmd_stdout, err_msg = run_shell_command(cmd="%s/refextract %s -f '%s'" % \
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

def call_authorlist_extract(active_file, extracted_file,
                            downloaded_files, queue, stylesheet, source_id):
    """
    Function that will look in harvested tarball for any authorlists. If found
    it will extract and convert the authors using a XSLT stylesheet.

    @param active_file: path to the currently processed file
    @type active_file: string

    @param extracted_file: path to the file where the final results will be saved
    @type extracted_file: string

    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.
    @type downloaded_files: dict

    @param queue: name of the RT queue
    @type queue: string

    @param source_id: the repository identifier
    @type source_id: integer

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
    for record_xml in record_xmls:
        current_exitcode = 0
        if not oaiharvest_templates.tmpl_should_process_record_with_mode(record_xml, 'p', source_id):
            # We skip this record
            updated_xml.append("<record>")
            updated_xml.append(record_xml)
            updated_xml.append("</record>")
            continue

        id_list = record_collect_oai_identifiers("<record>" + record_xml + "</record>")
        # We bet on the first one.
        identifier = None
        for oai_id in id_list:
            if "oai" in oai_id.lower():
                identifier = oai_id
                break
        write_message("OAI identifier found in record: %s" % (identifier,), verbose=6)

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
                all_err_msg.append(err_msg)
            else:
                downloaded_files[identifier]["tarball"] = tarball
        if current_exitcode == 0:
            current_exitcode, err_msg, authorlist_xml_path = authorlist_extract(downloaded_files[identifier]["tarball"], \
                                                                                identifier, downloaded_files, stylesheet)
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
                    if len(matching_fields) > 0:
                        # UNDEFINED found. Create ticket in author queue
                        ticketid = create_authorlist_ticket(matching_fields, \
                                                            identifier, queue)
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
        return exitcode, "\n".join(all_err_msg)
    return exitcode, ""

def call_fulltext(active_file, extracted_file,
                  downloaded_files, doctype, source_id):
    """
    Function that calls attach FFT tag for a downloaded file to harvested records.
    It will download the fulltext-pdf for each identifier if necessary.

    @param active_file: path to the currently processed file
    @param extracted_file: path to the file where the final results will be saved
    @param downloaded_files: dict of identifier -> dict mappings for downloaded material.
    @param doctype: doctype of downloaded file in BibDocFile
    @param source_id: the repository identifier

    @return: exitcode and any error messages as: (exitcode, err_msg)
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
    for record_xml in record_xmls:
        current_exitcode = 0

        id_list = record_collect_oai_identifiers("<record>" + record_xml + "</record>")
        # We bet on the first one.
        identifier = None
        for oai_id in id_list:
            if "oai" in oai_id.lower():
                identifier = oai_id
                break
        write_message("OAI identifier found in record: %s" % (identifier,), verbose=6)

        if identifier not in downloaded_files:
            downloaded_files[identifier] = {}
        updated_xml.append("<record>")
        updated_xml.append(record_xml)
        if not oaiharvest_templates.tmpl_should_process_record_with_mode(record_xml, 'p', source_id):
            # We skip this record
            updated_xml.append("</record>")
            continue
        if "pdf" not in downloaded_files[identifier]:
            current_exitcode, err_msg, dummy, pdf = \
                        plotextractor_harvest(identifier, active_file, selection=["pdf"])
            if current_exitcode != 0:
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


def authorlist_extract(tarball_path, identifier, downloaded_files, stylesheet):
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
        tar_dir, dummy = get_defaults(tarball=tarball_path, sdir=CFG_TMPSHAREDDIR, refno_url="")
        try:
            untar(tarball_path, tar_dir)
        except Timeout:
            all_err_msg.append("Timeout during tarball extraction of %s" % (tarball_path,))
            exitcode = 1
            return exitcode, "\n".join(all_err_msg), None
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
            tempfile_fd, temp_authorlist_path = tempfile.mkstemp(suffix=".xml", prefix="authorlist_temp", dir=CFG_TMPDIR)
            os.write(tempfile_fd, match[0])
            os.close(tempfile_fd)
            # Generate file to store conversion results
            newfile_fd, authorlist_resultxml_path = tempfile.mkstemp(suffix=".xml", prefix="authorlist_MARCXML", \
                                                             dir=downloaded_files[identifier]["tarball-extracted"])
            os.close(newfile_fd)
            exitcode, cmd_stderr = call_bibconvert(config=stylesheet, \
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


def create_authorlist_ticket(matching_fields, identifier, queue):
    """
    This function will submit a ticket generated by UNDEFINED affiliations
    in extracted authors from collaboration authorlists.

    @param matching_fields: list of (tag, field_instances) for UNDEFINED nodes
    @type matching_fields: list

    @param identifier: OAI identifier of record
    @type identifier: string

    @param queue: the RT queue to send a ticket to
    @type queue: string

    @return: return the ID of the created ticket, or None on failure
    @rtype: int or None
    """
    subject = "[OAI Harvest] UNDEFINED affiliations for record %s" % (identifier,)
    text = """
Harvested record with identifier %(ident)s has had its authorlist extracted and contains some UNDEFINED affiliations.

To see the record, go here: %(baseurl)s/search?p=%(ident)s

If the record is not there yet, try again later. It may take some time for it to load into the system.

List of unidentified fields:
%(fields)s
    """ % {
           'ident': identifier,
           'baseurl': CFG_SITE_URL,
           'fields': "\n".join([field_xml_output(field, tag) for tag, field_instances in matching_fields \
                                for field in field_instances])
           }
    return create_ticket(queue, subject, text)


def create_ticket(queue, subject, text=""):
    """
    This function will submit a ticket using the configured BibCatalog system.

    @param queue: the ticketing queue to send a ticket to
    @type queue: string

    @param subject: subject of the ticket
    @type subject: string

    @param text: the main text or body of the ticket. Optional.
    @type text: string

    @return: return the ID of the created ticket, or None on failure
    @rtype: int or None
    """
    # Initialize BibCatalog connection as default user, if possible
    if BIBCATALOG_SYSTEM is not None:
        bibcatalog_response = BIBCATALOG_SYSTEM.check_system()
    else:
        bibcatalog_response = "No ticket system configured"
    if bibcatalog_response != "":
        write_message("BibCatalog error: %s\n" % (bibcatalog_response,))
        return None

    try:
        ticketid = BIBCATALOG_SYSTEM.ticket_submit(subject=subject, queue=queue)
    except ValueError, e:
        write_message("Error creating ticket: %s" % (str(e),))
        return None
    if text:
        try:
            BIBCATALOG_SYSTEM.ticket_comment(None, ticketid, text)
        except ValueError, e:
            write_message("Error commenting on ticket %s: %s" % (str(ticketid), str(e)))
            return None
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


def call_bibupload(marcxmlfile, mode=None, oai_src_id= -1, sequence_id=None,
                   name="", priority=5):
    """
    Creates a bibupload task for the task scheduler in given mode
    on given file. Returns the generated task id and logs the event
    in oaiHARVESTLOGS, also adding any given oai source identifier.

    @param marcxmlfile: base-marcxmlfilename to upload
    @param mode: mode to upload in
    @param oai_src_id: id of current source config
    @param sequence_id: sequence-number, if relevant
    @param name: bibtask name, if relevant
    @param priority: bibtask priority, defaults to 5.

    @return: task_id if successful, otherwise None.
    """
    if mode is None:
        mode = ["-r", "-i"]
    if os.path.exists(marcxmlfile):
        try:
            args = mode
            if sequence_id:
                args.extend(['-I', str(sequence_id)])
            if name:
                args.extend(['-N', name])
            if priority:
                args.extend(['-P', str(priority)])
            args.append(marcxmlfile)
            task_id = task_low_level_submission("bibupload", "oaiharvest", *tuple(args))
            create_oaiharvest_log(task_id, oai_src_id, marcxmlfile)
        except Exception, msg:
            write_message("An exception during submitting oaiharvest task occured : %s " % (str(msg)))
            return None
        return task_id
    else:
        write_message("marcxmlfile %s does not exist" % (marcxmlfile,))
        return None


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


def get_identifier_names(identifier):
    if identifier:
        # Let's see if the user had a comma-separated list of OAI ids.
        stripped_idents = []
        for ident in identifier.split(","):
            if not ident.startswith("oai:arXiv.org"):
                if "oai:arxiv.org" in ident.lower():
                    ident = ident.replace("oai:arxiv.org", "oai:arXiv.org")
                elif "arXiv" in ident:
                    # New style arXiv ID
                    ident = ident.replace("arXiv", "oai:arXiv.org")
                elif "/" in ident:
                    # Old style arXiv ID?
                    ident = "%s%s" % ("oai:arXiv.org:", ident)
            stripped_idents.append(ident.strip())
        return stripped_idents


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
            if len([opt for opt, opt_value in opts if opt in ['-i', '--identifier']]) == 0 \
               and len(args) > 1 or \
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
    task_set_option("identifier", None)
    task_set_option("dates", None)
    task_set_option("upload-email", None)
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
   - Daemon mode (automatic harvesting) relies on the settings defined in the OAI
     Harvest admin interface to periodically or as a one-shot task retrieve the repositories
     and sets to harvest. It also take care of harvesting only new or
     modified records. Records harvested using this mode can be converted
     and integrated into the repository, according to the settings
     defined in the OAI Harvest admin interface.

Examples:
Manual (single-shot) harvesting mode:
   Save to /tmp/z.xml records from CDS added/modified between 2004-04-01
   and 2004-04-02, in MARCXML:
     $ oaiharvest -vListRecords -f2004-04-01 -u2004-04-02 -pmarcxml -o/tmp/z.xml http://cds.cern.ch/oai2d
Daemon (single-shot or periodical) harvesting mode:
   Schedule daily harvesting of all repositories defined in OAIHarvest admin:
     $ oaiharvest -s 24h
   Schedule daily harvesting of repository 'arxiv', defined in OAIHarvest admin:
     $ oaiharvest -r arxiv -s 24h
   Schedule single-shot harvesting of given oai id for repository 'arxiv', defined in OAIHarvest admin:
     $ oaiharvest -r arxiv -i oai:arXiv.org:1212.0748
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
              'Deamon mode (periodical or one-shot harvesting mode):\n'
              '  -r, --repository="repo A"[,"repo B"] \t which repositories to harvest (default=all)\n'
              '  -d, --dates=yyyy-mm-dd:yyyy-mm-dd \t reharvest given dates only\n'
              '  -i, --identifier     OAI identifier if wished to run in as a task.\n'
              '  --notify-email-to    Receive notifications on given email on successful upload and/or finished harvest.\n'
              '  --create-ticket-in   Provide desired ticketing queue to create a ticket in it on upload and/or finished harvest.\n'
              '                       Requires a configured ticketing system (BibCatalog).\n',
            version=__revision__,
            specific_params=("r:i:d:", ["repository=", "idenfifier=", "dates=", "notify-email-to=", "create-ticket-in="]),
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Elaborate specific cli parameters for oaiharvest."""
    if key in ("-r", "--repository"):
        task_set_option('repository', get_repository_names(value))
    elif key in ("-i", "--identifier"):
        task_set_option('identifier', get_identifier_names(value))
        if len(task_get_option("repository")) != 1:
            raise StandardError("Error: You can only specify one repository when defining identifiers.")
    elif key in ("-d", "--dates"):
        task_set_option('dates', get_dates(value))
        if value is not None and task_get_option("dates") is None:
            raise StandardError("Date format not valid.")
    elif key in ("--notify-email-to"):
        if email_valid_p(value):
            task_set_option('notify-email-to', value)
        else:
            raise StandardError("E-mail format not valid.")
    elif key in ("--create-ticket-in"):
        task_set_option('create-ticket-in', value)
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
