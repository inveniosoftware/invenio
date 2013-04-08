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
"""Functions shared by websubmit_functions"""

__revision__ = "$Id$"

import os
import cgi

from invenio.config import \
     CFG_PATH_CONVERT, \
     CFG_PATH_GUNZIP, \
     CFG_PATH_GZIP, \
     CFG_SITE_LANG
from invenio.bibdocfile import decompose_file
from invenio.websubmit_file_converter import convert_file, InvenioWebSubmitFileConverterError
from invenio.websubmit_config import InvenioWebSubmitFunctionError
from invenio.dbquery import run_sql
from invenio.bibsched import server_pid
from invenio.messages import gettext_set_language

def createRelatedFormats(fullpath, overwrite=True):
    """Given a fullpath, this function extracts the file's extension and
    finds in which additional format the file can be converted and converts it.
    @param fullpath: (string) complete path to file
    @param overwrite: (bool) overwrite already existing formats
    Return a list of the paths to the converted files
    """
    createdpaths = []
    basedir, filename, extension = decompose_file(fullpath)
    extension = extension.lower()
    if extension == ".pdf":
        if overwrite or \
               not os.path.exists("%s/%s.ps" % (basedir, filename)):
            # Create PostScript
            try:
                convert_file(fullpath, "%s/%s.ps" % (basedir, filename))
                createdpaths.append("%s/%s.ps" % (basedir, filename))
            except InvenioWebSubmitFileConverterError:
                pass
        if overwrite or \
               not os.path.exists("%s/%s.ps.gz" % (basedir, filename)):
            if os.path.exists("%s/%s.ps" % (basedir, filename)):
                os.system("%s %s/%s.ps" % (CFG_PATH_GZIP, basedir, filename))
                createdpaths.append("%s/%s.ps.gz" % (basedir, filename))
    if extension == ".ps":
        if overwrite or \
               not os.path.exists("%s/%s.pdf" % (basedir, filename)):
            # Create PDF
            try:
                convert_file(fullpath, "%s/%s.pdf" % (basedir, filename))
                createdpaths.append("%s/%s.pdf" % (basedir, filename))
            except InvenioWebSubmitFileConverterError:
                pass
    if extension == ".ps.gz":
        if overwrite or \
               not os.path.exists("%s/%s.ps" % (basedir, filename)):
            #gunzip file
            os.system("%s %s" % (CFG_PATH_GUNZIP, fullpath))
        if overwrite or \
               not os.path.exists("%s/%s.pdf" % (basedir, filename)):
            # Create PDF
            try:
                convert_file("%s/%s.ps" % (basedir, filename), "%s/%s.pdf" % (basedir, filename))
                createdpaths.append("%s/%s.pdf" % (basedir, filename))
            except InvenioWebSubmitFileConverterError:
                pass
        #gzip file
        if not os.path.exists("%s/%s.ps.gz" % (basedir, filename)):
            os.system("%s %s/%s.ps" % (CFG_PATH_GZIP, basedir, filename))
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
    filename1 =filename.strip()
    try:
        of=open(filename1,'w')
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
        msg = _("The task queue is currently running in automatic mode, and there are currently %s tasks waiting to be executed. Your record should be available within a few minutes and searchable within an hour or thereabouts.\n") % (len(res))
    else:
        msg = _("Because of a human intervention or a temporary problem, the task queue is currently set to the manual mode. Your submission is well registered but may take longer than usual before it is fully integrated and searchable.\n")

    return pre + msg

def txt2html(msg):
    """Transform newlines into paragraphs."""
    rows = msg.split('\n')
    rows = [cgi.escape(row) for row in rows]
    rows = "<p>" + "</p><p>".join(rows) + "</p>"
    return rows
