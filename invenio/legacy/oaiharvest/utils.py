# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
OAI Harvest utility functions.
"""

__revision__ = "$Id$"

import os
import re
import time
import urlparse
import calendar
from invenio.ext.logging import register_exception
from invenio.legacy.oaiharvest import getter

from invenio.config import (CFG_SITE_URL,
                            CFG_SITE_ADMIN_EMAIL,
                            )
from invenio.legacy.bibrecord import (record_get_field_instances,
                                      record_modify_subfield,
                                      field_xml_output
                                      )
from invenio.utils.shell import run_shell_command
from invenio.utils.text import translate_latex2unicode
from invenio.legacy.oaiharvest.dblayer import create_oaiharvest_log_str
from invenio.legacy.bibcatalog.api import BIBCATALOG_SYSTEM

from invenio.legacy.bibsched.bibtask import (write_message,
                                             task_low_level_submission)
from invenio.modules.workflows.models import BibWorkflowEngineLog


# precompile some often-used regexp for speed reasons:
REGEXP_OAI_ID = re.compile("<identifier.*?>(.*?)<\/identifier>", re.DOTALL)


def get_nb_records_in_file(filename):
    """
    Return number of record in FILENAME that is either harvested or converted
    file. Useful for statistics.
    :param filename:
    """
    try:
        nb = open(filename, 'r').read().count("</record>")
    except IOError:
        nb = 0  # file not exists and such
    return nb


def get_nb_records_in_string(string):
    """
    Return number of record in FILENAME that is either harvested or converted
    file. Useful for statistics.
    :param string:
    """
    nb = string.count("</record>")
    return nb


def create_oaiharvest_log(task_id, oai_src_id, marcxmlfile):
    """
    Function which creates the harvesting logs
    :param task_id: bibupload task id
    :param oai_src_id:
    :param marcxmlfile:
    """
    file_fd = open(marcxmlfile, "r")
    xml_content = file_fd.read(-1)
    file_fd.close()
    create_oaiharvest_log_str(task_id, oai_src_id, xml_content)


def collect_identifiers(harvested_file_list):
    """Collects all OAI PMH identifiers from each file in the list
    and adds them to a list of identifiers per file.

    :param harvested_file_list: list of filepaths to harvested files

    :return list of lists, containing each files' identifier list"""
    result = []
    for harvested_file in harvested_file_list:
        try:
            fd_active = open(harvested_file)
        except IOError as e:
            raise e
        data = fd_active.read()
        fd_active.close()
        result.append(REGEXP_OAI_ID.findall(data))
    return result


def find_matching_files(basedir, filetypes):
    """
    This functions tries to find all files matching given filetypes by
    looking at all the files and filenames in the given directory,
    including subdirectories.

    :param basedir: full path to base directory to search in
    :type basedir: string

    :param filetypes: list of filetypes, extensions
    :type filetypes: list

    :return: exitcode and any error messages as: (exitcode, err_msg)
    :rtype: tuple
    """
    files_list = []
    for dirpath, dummy0, filenames in os.walk(basedir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            dummy1, cmd_out, dummy2 = run_shell_command(
                'file %s', (full_path,)
            )
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

    :param record: record to modify, in BibRec style structure
    :type record: dict

    :param tag: tag of fields to modify
    :type tag: string

    :param code: restrict the translation to a given subfield code
    :type code: string

    :param encoding: scharacter encoding for the new value. Defaults to UTF-8.
    :type encoding: string
    """
    field_list = record_get_field_instances(record, tag)
    for field in field_list:
        subfields = field[0]
        subfield_index = 0
        for subfield_code, subfield_value in subfields:
            if code == '' or subfield_code == code:
                newvalue = translate_latex2unicode(
                    subfield_value
                ).encode(encoding)
                record_modify_subfield(record, tag, subfield_code, newvalue,
                                       subfield_index,
                                       field_position_global=field[4])
            subfield_index += 1


def compare_timestamps_with_tolerance(timestamp1,
                                      timestamp2,
                                      tolerance=0):
    """Compare two timestamps TIMESTAMP1 and TIMESTAMP2, of the form
       '2005-03-31 17:37:26'. Optionally receives a TOLERANCE argument
       (in seconds).  Return -1 if TIMESTAMP1 is less than TIMESTAMP2
       minus TOLERANCE, 0 if they are equal within TOLERANCE limit,
       and 1 if TIMESTAMP1 is greater than TIMESTAMP2 plus TOLERANCE.

        :param timestamp1:
        :param timestamp2:
        :param tolerance:
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


def generate_harvest_report(workflow, current_task_id=-1):
    """
    Returns an applicable subject-line + text to send via e-mail or add to
    a ticket about the harvesting results.

    :param workflow:
    :param current_task_id:
    :param manual_harvest:
    :param error_happened:
    """
    from invenio.modules.oaiharvester.models import OaiHARVEST

    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    extra_data_workflow = workflow.get_extra_data()
    list_source = ""
    if "task_specific_name" in extra_data_workflow["options"]:
        fullname = str(extra_data_workflow["options"]["repository"]) + extra_data_workflow["options"][
            "task_specific_name"]
    else:
        fullname = str(extra_data_workflow["options"]["repository"])
    try:
        for i in extra_data_workflow["options"]["repository"]:
            repository = OaiHARVEST.query.filter(OaiHARVEST.name == i).one()
            list_source += "\n" + str(repository.id) + "  " + str(repository.baseurl)
    except:
        list_source = "No information"

    try:

        if extra_data_workflow["options"]["identifiers"]:
            # One-shot manual harvest
            harvesting_prefix = "Manual harvest"
        else:
            # Automatic
            harvesting_prefix = "Periodical harvesting"
    except KeyError:
        harvesting_prefix = "Periodical harvesting"

    subject = "%s of '%s' finished %s" % (harvesting_prefix, fullname, current_time)

    if workflow.counter_error:
        subject += " with errors"

    text = """
The %(harvesting)s completed with %(number_errors)d errors at %(ctime)s.

Please forward this mail to administrators. <%(admin_mail)s>

Repositories which have been harvested are :
id   base url:
%(list_source)s
""" % {'ctime': current_time,
       'admin_mail': CFG_SITE_ADMIN_EMAIL,
       'harvesting': harvesting_prefix,
       'number_errors': workflow.counter_error,
       'list_source': list_source}

    try:

        text += """

List of OAI IDs harvested:
%(identifiers)s
""" % {'identifiers': str(extra_data_workflow["options"]["identifiers"])}
    except KeyError:

        text += """

No identifiers specified.
"""

    workflowlog = BibWorkflowEngineLog.query.filter(
        BibWorkflowEngineLog.id_object == workflow.uuid
    ).filter(BibWorkflowEngineLog.log_type > 10).all()

    logs = ""
    for log in workflowlog:
        logs += str(log) + '\n'
    text += """
Logs :

%(logs)s
""" % {'logs': logs}

    return subject, text


def harvest_step(obj, harvestpath):
    """
    Performs the entire harvesting step.
    Returns a tuple of (file_list, error_code)
    :param obj:
    :param harvestpath:
    """
    if obj.extra_data["options"]["identifiers"]:
        # Harvesting is done per identifier instead of server-updates
        return harvest_by_identifiers(obj, harvestpath)
    else:
        return harvest_by_dates(obj, harvestpath)


def harvest_by_identifiers(obj, harvestpath):
    """
    Harvest an OAI repository by identifiers.

    Given a repository "object" (dict from DB) and a list of OAI identifiers
    of records in the repository perform a OAI harvest using GetRecord
    for each.

    The records will be harvested into the specified filepath.
    :param obj:
    :param harvestpath:
    """
    harvested_files_list = []
    for oai_identifier in obj.extra_data["options"]["identifiers"]:
        harvested_files_list.extend(oai_harvest_get(prefix=obj.data["metadataprefix"],
                                                    baseurl=obj.data["baseurl"],
                                                    harvestpath=harvestpath,
                                                    verb="GetRecord",
                                                    identifier=oai_identifier))
    return harvested_files_list


def call_bibupload(marcxmlfile, mode=None, oai_src_id=-1, sequence_id=None):
    """
    Creates a bibupload task for the task scheduler in given mode
    on given file. Returns the generated task id and logs the event
    in oaiHARVESTLOGS, also adding any given oai source identifier.


    :param marcxmlfile: base-marcxmlfilename to upload
    :param mode: mode to upload in
    :param oai_src_id: id of current source config
    :param sequence_id: sequence-number, if relevant

    :return: task_id if successful, otherwise None.
    """
    if mode is None:
        mode = ["-r", "-i"]
    if os.path.exists(marcxmlfile):
        try:
            args = mode
            # Add job with priority 6 (above normal bibedit tasks)
            # and file to upload to arguments
            args.extend(["-P", "6", marcxmlfile])
            if sequence_id:
                args.extend(['-I', str(sequence_id)])
            task_id = task_low_level_submission("bibupload", "oaiharvest", *tuple(args))
            create_oaiharvest_log(task_id, oai_src_id, marcxmlfile)
        except Exception as msg:
            write_message("An exception during submitting oaiharvest task occured : %s " % (str(msg)))
            return None
        return task_id
    else:
        write_message("marcxmlfile %s does not exist" % (marcxmlfile,))
        return None


def harvest_by_dates(obj, harvestpath):
    """
    Harvest an OAI repository by dates.

    Given a repository "object" (dict from DB) and from/to dates,
    this function will perform an OAI harvest request for records
    updated between the given dates.

    If no dates are given, the repository is harvested from the beginning.

    If you set fromdate == last-run and todate == None, then the repository
    will be harvested since last time (most common type).

    The records will be harvested into the specified filepath.
    :param obj:
    :param harvestpath:
    """
    if obj.extra_data["options"]["dates"]:
        fromdate = str(obj.extra_data["options"]["dates"][0])
        todate = str(obj.extra_data["options"]["dates"][1])
    elif obj.data["lastrun"] is None or obj.data["lastrun"] == '':
        fromdate = None
        todate = None
        obj.extra_data["_should_last_run_be_update"] = True
    else:
        fromdate = str(obj.data["lastrun"]).split()[0]
        todate = None
        obj.extra_data["_should_last_run_be_update"] = True

    return oai_harvest_get(prefix=obj.data["metadataprefix"],
                           baseurl=obj.data["baseurl"],
                           harvestpath=harvestpath,
                           fro=fromdate,
                           until=todate,
                           setspecs=obj.data["setspecs"])


def oai_harvest_get(prefix, baseurl, harvestpath,
                    fro=None, until=None, setspecs=None,
                    user=None, password=None, cert_file=None,
                    key_file=None, method="POST", verb="ListRecords",
                    identifier=""):
    """
    Retrieve OAI records from given repository, with given arguments
    :param prefix:
    :param baseurl:
    :param harvestpath:
    :param fro:
    :param until:
    :param setspecs:
    :param user:
    :param password:
    :param cert_file:
    :param key_file:
    :param method:
    :param verb:
    :param identifier:
    """
    try:
        (addressing_scheme, network_location, path, dummy1,
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

        harvested_files = getter.harvest(network_location, path, http_param_dict, method, harvestpath,
                                         sets, secure, user, password, cert_file, key_file)
        return harvested_files
    except (StandardError, getter.InvenioOAIRequestError) as exce:
        register_exception()
        raise Exception("An error occurred while harvesting from %s: %s\n"
                        % (baseurl, str(exce)))


def create_authorlist_ticket(matching_fields, identifier, queue):
    """
    This function will submit a ticket generated by UNDEFINED affiliations
    in extracted authors from collaboration authorlists.

    :param matching_fields: list of (tag, field_instances) for UNDEFINED nodes
    :type matching_fields: list

    :param identifier: OAI identifier of record
    :type identifier: string

    :param queue: the RT queue to send a ticket to
    :type queue: string

    :return: return the ID of the created ticket, or None on failure
    :rtype: int or None
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
        'fields': "\n".join([field_xml_output(field, tag) for tag, field_instances in matching_fields
                             for field in field_instances])
    }
    return create_ticket(queue, subject, text)


def create_ticket(queue, subject, text=""):
    """
    This function will submit a ticket using the configured BibCatalog system.

    :param queue: the ticketing queue to send a ticket to
    :type queue: string

    :param subject: subject of the ticket
    :type subject: string

    :param text: the main text or body of the ticket. Optional.
    :type text: string

    :return: return the ID of the created ticket, or None on failure
    :rtype: int or None
    """
    # Initialize BibCatalog connection as default user, if possible
    if bibcatalog_system is not None:
        bibcatalog_response = bibcatalog_system.check_system()
    else:
        bibcatalog_response = "No ticket system configured"
    if bibcatalog_response != "":
        write_message("BibCatalog error: %s\n" % (bibcatalog_response,))
        return None

    ticketid = bibcatalog_system.ticket_submit(subject=subject, queue=queue)
    if text:
        comment = bibcatalog_system.ticket_comment(None, ticketid, text)
        if comment is None:
            write_message("Error: commenting on ticket %s failed." % (str(ticketid),))
    return ticketid
