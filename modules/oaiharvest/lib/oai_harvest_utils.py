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
OAI Harvest utility functions.
"""

__revision__ = "$Id$"

import os
import re
import time
import calendar
import traceback

from invenio.config import CFG_ETCDIR, CFG_SITE_URL, \
                           CFG_SITE_ADMIN_EMAIL
from invenio.bibrecord import record_get_field_instances, \
                              record_modify_subfield
from invenio.shellutils import run_shell_command
from invenio.textutils import translate_latex2unicode
from invenio.bibtask import write_message

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
        nb = 0  # file not exists and such
    except:
        nb = -1
    return nb


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
    Usually happens when records are cross-listed across OAI sets.

    Saves a backup of original harvested file in: filename~
    """
    harvested_identifiers = []
    for harvested_file in harvested_file_list:
        # Firstly, rename original file to temporary name
        try:
            os.rename(harvested_file, "%s~" % (harvested_file,))
        except IOError:
            write_message("Error renaming harvested file '%s': %s" % \
                         (harvested_file, traceback.print_exc()))
            continue
        # Secondly, open files for writing and reading
        original_harvested_file = None
        try:
            try:
                original_harvested_file = open("%s~" % (harvested_file,))
                data = original_harvested_file.read()
            except IOError:
                write_message("Error opening harvested file '%s': %s" % \
                             (harvested_file, traceback.print_exc()))
                continue
        finally:
            if original_harvested_file:
                original_harvested_file.close()

        if '<ListRecords>' not in data:
            # We do not need to de-duplicate in non-ListRecords requests
            continue

        updated_file_content = []
        # Get and write OAI-PMH XML header data to updated file
        header_index_end = data.find("<ListRecords>") + len("<ListRecords>")
        updated_file_content.append("%s" % (data[:header_index_end],))

        # By checking the OAI ID we write all records not written previously (in any file)
        harvested_records = REGEXP_RECORD.findall(data)
        for record in harvested_records:
            oai_identifier = REGEXP_OAI_ID.search(record)
            if oai_identifier != None and oai_identifier.group(1) not in harvested_identifiers:
                updated_file_content.append("<record>%s</record>" % (record,))
                harvested_identifiers.append(oai_identifier.group(1))
        updated_file_content.append("</ListRecords>\n</OAI-PMH>")
        updated_harvested_file = None
        try:
            try:
                updated_harvested_file = open(harvested_file, 'w')
                updated_harvested_file.write("\n".join(updated_file_content))
            except IOError:
                write_message("Error saving updated harvest-file '%s': %s" % \
                             (harvested_file, traceback.print_exc()))
                continue
        finally:
            if updated_harvested_file:
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


def generate_harvest_report(repository, harvested_identifier_list, \
                            uploaded_task_ids=[], active_files_list=[], \
                            task_specific_name="", current_task_id=-1, \
                            manual_harvest=False, error_happened=False):
    """
    Returns an applicable subject-line + text to send via e-mail or add to
    a ticket about the harvesting results.
    """
    # Post-harvest reporting
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if task_specific_name:
        fullname = repository['name'] + task_specific_name
    else:
        fullname = repository['name']

    if manual_harvest:
        # One-shot manual harvest
        harvesting_prefix = "Manual harvest"
    else:
        # Automatic
        harvesting_prefix = "Periodical harvesting"

    subject = "%s of '%s' finished %s" % (harvesting_prefix, fullname, current_time)
    if error_happened:
        subject += " with errors"
        text = \
"""
%(harvesting)s completed *with errors* from source named '%(name)s' (%(sourceurl)s) at %(ctime)s.
In total %(total)d record(s) were harvested.

See harvest task log here for more information on the problems:
%(harvesttasklink)s

Please forward this mail to administrators. <%(admin_mail)s>

----------
Extra Info
----------

Harvest history for this source:
%(siteurl)s/admin/oaiharvest/oaiharvestadmin.py/viewhistory?ln=no&oai_src_id=%(oai_src_id)s

See state of uploaded records:
%(uploadtasklinks)s

List of OAI IDs harvested:
%(ids)s

Records ready to upload are located here:
%(files)s
""" \
        % {
            'harvesting': harvesting_prefix,
            'admin_mail': CFG_SITE_ADMIN_EMAIL,
            'name': fullname,
            'sourceurl': repository['baseurl'],
            'ctime': current_time,
            'total': sum([len(ids) for ids in harvested_identifier_list]),
            'files': '\n'.join(active_files_list),
            'ids': '\n'.join([oaiid for ids in harvested_identifier_list for oaiid in ids]),
            'siteurl': CFG_SITE_URL,
            'oai_src_id': repository['id'],
            'harvesttasklink': "%s/admin/oaiharvest/oaiharvestadmin.py/viewtasklogs?ln=no&task_id=%s" \
                               % (CFG_SITE_URL, current_task_id),
            'uploadtasklinks': '\n'.join(["%s/admin/oaiharvest/oaiharvestadmin.py/viewtasklogs?ln=no&task_id=%s" \
                                           % (CFG_SITE_URL, task_id) for task_id in uploaded_task_ids]) or "None",\
        }
    else:
        text = \
"""
%(harvesting)s completed successfully from source named '%(name)s' (%(sourceurl)s) at %(ctime)s.
In total %(total)d record(s) were harvested.

See harvest history here:
%(siteurl)s/admin/oaiharvest/oaiharvestadmin.py/viewhistory?ln=no&oai_src_id=%(oai_src_id)s

See state of uploaded records:
%(uploadtasklinks)s

List of OAI IDs harvested:
%(ids)s

Records ready to upload are located here:
%(files)s
""" \
            % {
                'harvesting': harvesting_prefix,
                'name': fullname,
                'sourceurl': repository['baseurl'],
                'ctime': current_time,
                'total': sum([len(ids) for ids in harvested_identifier_list]),
                'files': '\n'.join(active_files_list),
                'ids': '\n'.join([oaiid for ids in harvested_identifier_list for oaiid in ids]),
                'siteurl': CFG_SITE_URL,
                'oai_src_id': repository['id'],
                'uploadtasklinks': '\n'.join(["%s/admin/oaiharvest/oaiharvestadmin.py/viewtasklogs?ln=no&task_id=%s" \
                                               % (CFG_SITE_URL, task_id) for task_id in uploaded_task_ids]) or "None",\
            }
        if not manual_harvest:
            text += "Categories harvested from: \n%s\n" % (repository['setspecs'] or "None",)
    return subject, text
