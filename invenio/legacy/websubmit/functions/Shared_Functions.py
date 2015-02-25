# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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
"""Functions shared by websubmit_functions"""

from __future__ import print_function

__revision__ = "$Id$"

import os
import cgi
import glob
import sys
from logging import DEBUG
from six import iteritems

from invenio.config import \
     CFG_PATH_CONVERT, \
     CFG_SITE_LANG, \
     CFG_BIBDOCFILE_FILEDIR
from invenio.legacy.bibdocfile.api import decompose_file, decompose_file_with_version
from invenio.ext.logging import register_exception
from invenio.legacy.websubmit.file_converter import convert_file, InvenioWebSubmitFileConverterError, get_missing_formats, get_file_converter_logger
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.cli import server_pid
from invenio.base.i18n import gettext_set_language
from invenio.legacy.search_engine import get_record
from invenio.legacy.bibrecord import record_get_field_values, record_get_field_value

def createRelatedFormats(fullpath, overwrite=True, debug=False, consider_version=False):
    """Given a fullpath, this function extracts the file's extension and
    finds in which additional format the file can be converted and converts it.
    @param fullpath: (string) complete path to file
    @param overwrite: (bool) overwrite already existing formats
    @param consider_version: (bool) if True, consider the version info
                             in C{fullpath} to find missing format
                             for that specific version, if C{fullpath}
                             contains version info
    Return a list of the paths to the converted files
    """
    file_converter_logger = get_file_converter_logger()
    old_logging_level = file_converter_logger.getEffectiveLevel()
    if debug:
        file_converter_logger.setLevel(DEBUG)
    try:
        createdpaths = []
        if consider_version:
            try:
                basedir, filename, extension, version = decompose_file_with_version(fullpath)
            except:
                basedir, filename, extension = decompose_file(fullpath)
                version = 0
        else:
            basedir, filename, extension = decompose_file(fullpath)
            version = 0
        extension = extension.lower()
        if debug:
            print("basedir: %s, filename: %s, extension: %s" % (basedir, filename, extension), file=sys.stderr)

        if overwrite:
            missing_formats = get_missing_formats([fullpath])
        else:
            if version:
                filelist = glob.glob(os.path.join(basedir, '%s*;%s' % (filename, version)))
            else:
                filelist = glob.glob(os.path.join(basedir, '%s*' % filename))
            if debug:
                print("filelist: %s" % filelist, file=sys.stderr)
            missing_formats = get_missing_formats(filelist)
        if debug:
            print("missing_formats: %s" % missing_formats, file=sys.stderr)
        for path, formats in iteritems(missing_formats):
            if debug:
                print("... path: %s, formats: %s" % (path, formats), file=sys.stderr)
            for aformat in formats:
                if debug:
                    print("...... aformat: %s" % aformat, file=sys.stderr)
                newpath = os.path.join(basedir, filename + aformat)
                if debug:
                    print("...... newpath: %s" % newpath, file=sys.stderr)
                try:
                    if CFG_BIBDOCFILE_FILEDIR in basedir:
                        # We should create the new files in a temporary location, not
                        # directly inside the BibDoc directory.
                        newpath = convert_file(path, output_format=aformat)
                    else:
                        convert_file(path, newpath)
                    createdpaths.append(newpath)
                except InvenioWebSubmitFileConverterError as msg:
                    if debug:
                        print("...... Exception: %s" % msg, file=sys.stderr)
                    register_exception(alert_admin=True)
    finally:
        if debug:
            file_converter_logger.setLevel(old_logging_level)
    return createdpaths

def createIcon(fullpath, iconsize):
    """Given a fullpath, this function extracts the file's extension and
    if the format is compatible it converts it to icon.
    @param fullpath: (string) complete path to file
    Return the iconpath if successful otherwise None
    """
    basedir = os.path.dirname(fullpath)
    filename = os.path.basename(fullpath)
    filename, extension = os.path.splitext(filename)
    if extension == filename:
        extension == ""
    iconpath = "%s/icon-%s.gif" % (basedir, filename)
    if os.path.exists(fullpath) and extension.lower() in ['.pdf', '.gif', '.jpg', '.jpeg', '.ps']:
        os.system("%s -scale %s %s %s" % (CFG_PATH_CONVERT, iconsize, fullpath, iconpath))
    if os.path.exists(iconpath):
        return iconpath
    else:
        return None

def get_dictionary_from_string(dict_string):
    """Given a string version of a "dictionary", split the string into a
       python dictionary.
       For example, given the following string:
         {'TITLE' : 'EX_TITLE', 'AUTHOR' : 'EX_AUTHOR', 'REPORTNUMBER' : 'EX_RN'}
       A dictionary in the following format will be returned:
         {
            'TITLE'        : 'EX_TITLE',
            'AUTHOR'       : 'EX_AUTHOR',
            'REPORTNUMBER' : 'EX_RN',
         }
       @param dict_string: (string) - the string version of the dictionary.
       @return: (dictionary) - the dictionary build from the string.
    """
    try:
        # Evaluate the dictionary string in an empty local/global
        # namespaces. An empty '__builtins__' variable is still
        # provided, otherwise Python will add the real one for us,
        # which would access to undesirable functions, such as
        # 'file()', 'open()', 'exec()', etc.
        evaluated_dict = eval(dict_string, {"__builtins__": {}}, {})
    except:
        evaluated_dict = {}

    # Check that returned value is a dict. Do not check with
    # isinstance() as we do not even want to match subclasses of dict.
    if type(evaluated_dict) is dict:
        return evaluated_dict
    else:
        return {}

def ParamFromFile(afile):
    """ Pipe a multi-line file into a single parameter"""
    parameter = ''
    afile = afile.strip()
    if afile == '': return parameter
    try:
        fp = open(afile, "r")
        lines = fp.readlines()
        for line in lines:
            parameter = parameter + line
        fp.close()
    except IOError:
        pass
    return parameter

def write_file(filename, filedata):
    """Open FILENAME and write FILEDATA to it."""
    filename1 = filename.strip()
    try:
        of = open(filename1,'w')
    except IOError:
        raise InvenioWebSubmitFunctionError('Cannot open ' + filename1 + ' to write')
    of.write(filedata)
    of.close()
    return ""

def get_nice_bibsched_related_message(curdir, ln=CFG_SITE_LANG):
    """
    @return: a message suitable to display to the user, explaining the current
        status of the system.
    @rtype: string
    """
    bibupload_id = ParamFromFile(os.path.join(curdir, 'bibupload_id'))
    if not bibupload_id:
        ## No BibUpload scheduled? Then we don't care about bibsched
        return ""
    ## Let's get an estimate about how many processes are waiting in the queue.
    ## Our bibupload might be somewhere in it, but it's not really so important
    ## WRT informing the user.
    _ = gettext_set_language(ln)
    res = run_sql("SELECT id,proc,runtime,status,priority FROM schTASK WHERE (status='WAITING' AND runtime<=NOW()) OR status='SLEEPING'")
    pre = _("Note that your submission has been inserted into the bibliographic task queue and is waiting for execution.\n")
    if server_pid():
        ## BibSched is up and running
        msg = _("The task queue is currently running in automatic mode, and there are currently %(x_num)s tasks waiting to be executed. Your record should be available within a few minutes and searchable within an hour or thereabouts.\n", x_num=(len(res)))
    else:
        msg = _("Because of a human intervention or a temporary problem, the task queue is currently set to the manual mode. Your submission is well registered but may take longer than usual before it is fully integrated and searchable.\n")

    return pre + msg

def txt2html(msg):
    """Transform newlines into paragraphs."""
    rows = msg.split('\n')
    rows = [cgi.escape(row) for row in rows]
    rows = "<p>" + "</p><p>".join(rows) + "</p>"
    return rows

def get_all_values_in_curdir(curdir):
    """
    Return a dictionary with all the content of curdir.

    @param curdir: the path to the current directory.
    @type curdir: string
    @return: the content
    @rtype: dict
    """
    ret = {}
    for filename in os.listdir(curdir):
        if not filename.startswith('.') and os.path.isfile(os.path.join(curdir, filename)):
            ret[filename] = open(os.path.join(curdir, filename)).read().strip()
    return ret

def get_current_record(curdir, system_number_file='SN'):
    """
    Return the current record (in case it's being modified).

    @param curdir: the path to the current directory.
    @type curdir: string
    @param system_number_file: is the name of the file on disk in curdir, that
        is supposed to contain the record id.
    @type system_number_file: string
    @return: the record
    @rtype: as in L{get_record}
    """
    if os.path.exists(os.path.join(curdir, system_number_file)):
        recid = open(os.path.join(curdir, system_number_file)).read().strip()
        if recid:
            recid = int(recid)
            return get_record(recid)
    return {}

def retrieve_field_values(curdir, field_name, separator=None, system_number_file='SN', tag=None):
    """
    This is a handy function to retrieve values either from the current
    submission directory, when a form has been just submitted, or from
    an existing record (e.g. during MBI action).

    @param curdir: is the current submission directory.
    @type curdir: string
    @param field_name: is the form field name that might exists on disk.
    @type field_name: string
    @param separator: is an optional separator. If it exists, it will be used
        to retrieve multiple values contained in the field.
    @type separator: string
    @param system_number_file: is the name of the file on disk in curdir, that
        is supposed to contain the record id.
    @type system_number_file: string
    @param tag: is the full MARC tag (tag+ind1+ind2+code) that should
        contain values. If not specified, only values in curdir will
        be retrieved.
    @type tag: 6-chars
    @return: the field value(s).
    @rtype: list of strings.

    @note: if field_name exists in curdir it will take precedence over
        retrieving the values from the record.
    """
    field_file = os.path.join(curdir, field_name)
    if os.path.exists(field_file):
        field_value = open(field_file).read()
        if separator is not None:
            return [value.strip() for value in field_value.split(separator) if value.strip()]
        else:
            return [field_value.strip()]
    elif tag is not None:
        system_number_file = os.path.join(curdir, system_number_file)
        if os.path.exists(system_number_file):
            recid = int(open(system_number_file).read().strip())
            record = get_record(recid)
            if separator:
                return record_get_field_values(record, tag[:3], tag[3], tag[4], tag[5])
            else:
                return [record_get_field_value(record, tag[:3], tag[3], tag[4], tag[5])]
    return []
