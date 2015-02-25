# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011 CERN.
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

"""Stamp_Replace_Single_File_Approval: A function to allow a single file
   that is already attached to a record to be stamped at approval time.
"""
__revision__ = "$Id$"


from invenio.legacy.bibdocfile.api import BibRecDocs, InvenioBibDocFileError
from invenio.ext.logging import register_exception
from invenio import websubmit_file_stamper
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionWarning, \
     InvenioWebSubmitFunctionError, InvenioWebSubmitFileStamperError
import os.path
import re
import cgi
import time


def Stamp_Replace_Single_File_Approval(parameters, \
                                       curdir, \
                                       form, \
                                       user_info=None):
    """
    This function is intended to be called when a document has been
    approved and needs to be stamped.
    The function should be used when there is ONLY ONE file to be
    stamped after approval (for example, the "main file").
    The name of the file to be stamped should be known and should be stored
    in a file in the submission's working directory (without the extension).
    Generally, this will work our fine as the main file is named after the
    report number of the document, this will be stored in the report number
    file.

    @param parameters: (dictionary) - must contain:

         + latex_template: (string) - the name of the LaTeX template that
            should be used for the creation of the stamp.

         + latex_template_vars: (string) - a string-ified dictionary
            of variables to be replaced in the LaTeX template and the
            values (or names of files in curdir containing the values)
            with which to replace them. Use prefix 'FILE:' to specify
            that the stamped value must be read from a file in
            submission directory instead of being a fixed value to
            stamp.
            E.G.:
               { 'TITLE' : 'FILE:DEMOTHESIS_TITLE',
                 'DATE'  : 'FILE:DEMOTHESIS_DATE'
               }

         + file_to_be_stamped: (string) - this is the name of a file in the
            submission's working directory that contains the name of the
            bibdocfile that is to be stamped.

         + new_file_name: (string) - this is the name of a file in the
            submission's working directory that contains the name that is to
            be given to the file after it has been stamped. If empty, or if
            that file doesn't exist, the file will not be renamed after
            stamping.

         + switch_file: (string) - when this value is set, specifies
            the name of a file that will swith on/off the
            stamping. The stamp will be applied if the file exists in
            the submission directory and is not empty. If the file
            cannot be found or is empty, the stamp is not applied.
            Useful for eg. if you want to let your users control the
            stamping with a checkbox on your submission page.
            Leave this parameter empty to always stamp by default.

         + stamp: (string) - the type of stamp to be applied to the file.
            should be one of:
              + first (only the first page is stamped);
              + all (all pages are stamped);
              + coverpage (a separate cover-page is added to the file as a
                 first page);

         + layer: (string) - the position of the stamp. Should be one of:
              + background (invisible if original file has a white
                -not transparent- background layer)
              + foreground (on top of the stamped file.  If the stamp
                does not have a transparent background, will hide all
                of the document layers)
           The default value is 'background'.
    """
    ############
    ## Definition of important variables:
    ############
    ## The file stamper needs to be called with a dictionary of options of
    ## the following format:
    ##  { 'latex-template'      : "", ## TEMPLATE_NAME
    ##    'latex-template-var'  : {}, ## TEMPLATE VARIABLES
    ##    'input-file'          : "", ## INPUT FILE
    ##    'output-file'         : "", ## OUTPUT FILE
    ##    'stamp'               : "", ## STAMP TYPE
    ##    'layer'               : "", ## LAYER TO STAMP
    ##    'verbosity'           : 0,  ## VERBOSITY (we don't care about it)
    ##  }
    file_stamper_options = { 'latex-template'      : "",
                             'latex-template-var'  : { },
                             'input-file'          : "",
                             'output-file'         : "",
                             'stamp'               : "",
                             'layer'               : "",
                             'verbosity'           : 0,
                           }

    ## Check if stamping is enabled
    switch_file = parameters.get('switch_file', '')
    if switch_file:
        # Good, a "switch file" was specified. Check if it exists, and
        # it its value is not empty.
        if not _read_in_file(os.path.join(curdir, switch_file)):
            # File does not exist, or is emtpy. Silently abort
            # stamping.
            return ""

    ## Submission access number:
    access = _read_in_file("%s/access" % curdir)
    ## record ID for the current submission. It is found in the special file
    ## "SN" (sysno) in curdir:
    recid = _read_in_file("%s/SN" % curdir)
    try:
        recid = int(recid)
    except ValueError:
        ## No record ID. Cannot continue.
        err_msg = "Error in Stamp_Replace_Single_File_Approval: " \
                  "Cannot recover record ID from the submission's working " \
                  "directory. Stamping cannot be carried out. The " \
                  "submission ID is [%s]." % cgi.escape(access)
        register_exception(prefix=err_msg)
        raise InvenioWebSubmitFunctionError(err_msg)
    ############
    ## Resolution of function parameters:
    ############
    ## The name of the LaTeX template to be used for stamp creation:
    latex_template = "%s" % ((type(parameters['latex_template']) is str \
                              and parameters['latex_template']) or "")
    ## A string containing the variables/values that should be substituted
    ## in the final (working) LaTeX template:
    latex_template_vars_string = "%s" % \
                       ((type(parameters['latex_template_vars']) is str \
                         and parameters['latex_template_vars']) or "")
    ## The type of stamp to be applied to the file(s):
    stamp = "%s" % ((type(parameters['stamp']) is str and \
                     parameters['stamp'].lower()) or "")
    ## The layer to use for stamping:
    try:
        layer = parameters['layer']
    except KeyError:
        layer = "background"
    if not layer in ('background', 'foreground'):
        layer = "background"
    ## Get the name of the file to be stamped from the file indicated in
    ## the file_to_be_stamped parameter:
    try:
        file_to_stamp_file = parameters['file_to_be_stamped']
    except KeyError:
        file_to_stamp_file = ""
    else:
        if file_to_stamp_file is None:
            file_to_stamp_file = ""
    ## Get the "basename" for the file to be stamped (it's mandatory that it
    ## be in curdir):
    file_to_stamp_file = os.path.basename(file_to_stamp_file).strip()
    name_file_to_stamp = _read_in_file("%s/%s" % (curdir, file_to_stamp_file))
    name_file_to_stamp.replace("\n", "").replace("\r", "")
    ##
    ## Get the name to be given to the file after it has been stamped (if there
    ## is one.) Once more, it will be found in a file in curdir:
    try:
        new_file_name_file = parameters['new_file_name']
    except KeyError:
        new_file_name_file = ""
    else:
        if new_file_name_file is None:
            new_file_name_file = ""
    ## Get the "basename" for the file containing the new file name. (It's
    ## mandatory that it be in curdir):
    new_file_name_file = os.path.basename(new_file_name_file).strip()
    new_file_name = _read_in_file("%s/%s" % (curdir, new_file_name_file))

    ############
    ## Begin:
    ############
    ##
    ## If no name for the file to stamp, warning.
    if name_file_to_stamp == "":
        wrn_msg = "Warning in Stamp_Replace_Single_File_Approval: " \
                  "It was not possible to recover a valid name for the " \
                  "file to be stamped. Stamping could not, therefore, be " \
                  "carried out. The submission ID is [%s]." \
                  % access
        raise InvenioWebSubmitFunctionWarning(wrn_msg)
    ##
    ## The file to be stamped is a bibdoc. We will only stamp it (a) if it
    ## exists; and (b) if it is a PDF file. So, get the path (in the bibdocs
    ## tree) to the file to be stamped:
    ##
    ## First get the object representing the bibdocs belonging to this record:
    bibrecdocs = BibRecDocs(recid)
    try:
        bibdoc_file_to_stamp = bibrecdocs.get_bibdoc("%s" % name_file_to_stamp)
    except InvenioBibDocFileError:
        ## Couldn't get a bibdoc object for this filename. Probably the file
        ## that we wanted to stamp wasn't attached to this record.
        wrn_msg = "Warning in Stamp_Replace_Single_File_Approval: " \
                  "It was not possible to recover a bibdoc object for the " \
                  "filename [%s] when trying to stamp the main file. " \
                  "Stamping could not be carried out. The submission ID is " \
                  "[%s] and the record ID is [%s]." \
                  % (name_file_to_stamp, access, recid)
        register_exception(prefix=wrn_msg)
        raise InvenioWebSubmitFunctionWarning(wrn_msg)
    ## Get the BibDocFile object for the PDF version of the bibdoc to be
    ## stamped:
    try:
        bibdocfile_file_to_stamp = bibdoc_file_to_stamp.get_file("pdf")
    except InvenioBibDocFileError:
        ## This bibdoc doesn't have a physical file with the extension ".pdf"
        ## (take note of the lower-case extension - the bibdocfile library
        ## is case-sensitive with respect to filenames.  Log that there was
        ## no "pdf" and check for a file with extension "PDF":
        wrn_msg = "Warning in Stamp_Replace_Single_File_Approval: " \
                  "It wasn't possible to recover a PDF BibDocFile object " \
                  "for the file with the name [%s], using the extension " \
                  "[pdf] - note the lower case - the bibdocfile library " \
                  "relies upon the case of an extension. The submission ID " \
                  "is [%s] and the record ID is [%s]. Going to try " \
                  "looking for a file with a [PDF] extension before giving " \
                  "up . . . " \
                  % (name_file_to_stamp, access, recid)
        register_exception(prefix=wrn_msg)
        try:
            bibdocfile_file_to_stamp = bibdoc_file_to_stamp.get_file("PDF")
        except InvenioBibDocFileError:
            wrn_msg = "Warning in Stamp_Replace_Single_File_Approval: " \
                      "It wasn't possible to recover a PDF " \
                      "BibDocFile object for the file with the name [%s], " \
                      "using the extension [PDF] - note the upper case. " \
                      "Had previously tried searching for [pdf] - now " \
                      "giving up. Stamping could not be carried out. " \
                      "The submission ID is [%s] and the record ID is [%s]." \
                      % (name_file_to_stamp, access, recid)
            register_exception(prefix=wrn_msg)
            raise InvenioWebSubmitFunctionWarning(wrn_msg)
    ############
    ## Go ahead and prepare the details for the LaTeX stamp template and its
    ## variables:
    ############
    ## Strip the LaTeX filename into the basename (All templates should be
    ## in the template repository):
    latex_template = os.path.basename(latex_template)

    ## Convert the string of latex template variables into a dictionary
    ## of search-term/replacement-term pairs:
    latex_template_vars = get_dictionary_from_string(latex_template_vars_string)
    ## For each of the latex variables, check in `CURDIR' for a file with that
    ## name. If found, use it's contents as the template-variable's value.
    ## If not, just use the raw value string already held by the template
    ## variable:
    latex_template_varnames = latex_template_vars.keys()
    for varname in latex_template_varnames:
        ## Get this variable's value:
        varvalue = latex_template_vars[varname].strip()
        if not ((varvalue.find("date(") == 0 and varvalue[-1] == ")") or \
                (varvalue.find("include(") == 0 and varvalue[-1] == ")")) \
                and varvalue != "":
            ## We don't want to interfere with date() or include() directives,
            ## so we only do this if the variable value didn't contain them:
            ##
            ## Is this variable value the name of a file in the current
            ## submission's working directory, from which a literal value for
            ## use in the template should be extracted? If yes, it will
            ## begin with "FILE:". If no, we leave the value exactly as it is.
            if varvalue.upper().find("FILE:") == 0:
                ## The value to be used is to be taken from a file. Clean the
                ## file name and if it's OK, extract that value from the file.
                ##
                seekvalue_fname = varvalue[5:].strip()
                seekvalue_fname = os.path.basename(seekvalue_fname).strip()
                if seekvalue_fname != "":
                    ## Attempt to extract the value from the file:
                    if os.access("%s/%s" % (curdir, seekvalue_fname), \
                                 os.R_OK|os.F_OK):
                        ## The file exists. Extract its value:
                        try:
                            repl_file_val = \
                              open("%s/%s" \
                                   % (curdir, seekvalue_fname), "r").readlines()
                        except IOError:
                            ## The file was unreadable.
                            err_msg = "Error in Stamp_Replace_Single_File_" \
                                      "Approval: The function attempted to " \
                                      "read a LaTex template variable " \
                                      "value from the following file in the " \
                                      "current submission's working " \
                                      "directory: [%s]. However, an " \
                                      "unexpected error was encountered " \
                                      "when doing so. Please inform the " \
                                      "administrator." \
                                      % seekvalue_fname
                            register_exception(req=user_info['req'])
                            raise InvenioWebSubmitFunctionError(err_msg)
                        else:
                            final_varval = ""
                            for line in repl_file_val:
                                final_varval += line
                            final_varval = final_varval.rstrip()
                            ## Replace the variable value with that which has
                            ## been read from the file:
                            latex_template_vars[varname] = final_varval
                    else:
                        ## The file didn't actually exist in the current
                        ## submission's working directory. Use an empty
                        ## value:
                        latex_template_vars[varname] = ""
                else:
                    ## The filename was not valid.
                    err_msg = "Error in Stamp_Replace_Single_File_Approval: " \
                              "The function was configured to read a LaTeX " \
                              "template variable from a file with the " \
                              "following instruction: [%s --> %s]. The " \
                              "filename, however, was not considered valid. " \
                              "Please report this to the administrator." \
                              % (varname, varvalue)
                    raise InvenioWebSubmitFunctionError(err_msg)

    ## Put the 'fixed' values into the file_stamper_options dictionary:
    file_stamper_options['latex-template'] = latex_template
    file_stamper_options['latex-template-var'] = latex_template_vars
    file_stamper_options['stamp'] = stamp
    file_stamper_options['layer'] = layer

    ## Put the input file and output file into the file_stamper_options
    ## dictionary:
    file_stamper_options['input-file'] = bibdocfile_file_to_stamp.fullpath
    file_stamper_options['output-file'] = bibdocfile_file_to_stamp.get_full_name()
    ##
    ## Before attempting to stamp the file, log the dictionary of arguments
    ## that will be passed to websubmit_file_stamper:
    try:
        fh_log = open("%s/websubmit_file_stamper-calls-options.log" \
                      % curdir, "a+")
        fh_log.write("%s\n" % file_stamper_options)
        fh_log.flush()
        fh_log.close()
    except IOError:
        ## Unable to log the file stamper options.
        exception_prefix = "Unable to write websubmit_file_stamper " \
                           "options to log file " \
                           "%s/websubmit_file_stamper-calls-options.log" \
                           % curdir
        register_exception(prefix=exception_prefix)

    try:
        ## Try to stamp the file:
        (stamped_file_path_only, stamped_file_name) = \
                websubmit_file_stamper.stamp_file(file_stamper_options)
    except InvenioWebSubmitFileStamperError:
        ## It wasn't possible to stamp this file.
        ## Register the exception along with an informational message:
        wrn_msg = "Warning in Stamp_Replace_Single_File_Approval: " \
                  "There was a problem stamping the file with the name [%s] " \
                  "and the fullpath [%s]. The file has not been stamped. " \
                  "The submission ID is [%s] and the record ID is [%s]." \
                  % (name_file_to_stamp, \
                     file_stamper_options['input-file'], \
                     access, \
                     recid)
        register_exception(prefix=wrn_msg)
        raise InvenioWebSubmitFunctionWarning(wrn_msg)
    else:
        ## Stamping was successful. The BibDocFile must now be revised with
        ## the latest (stamped) version of the file:
        file_comment = "Stamped by WebSubmit: %s" \
                       % time.strftime("%d/%m/%Y", time.localtime())
        try:
            dummy = \
                  bibrecdocs.add_new_version("%s/%s" \
                                             % (stamped_file_path_only, \
                                                stamped_file_name), \
                                                name_file_to_stamp, \
                                                comment=file_comment, \
                                                flags=('STAMPED', ))
        except InvenioBibDocFileError:
            ## Unable to revise the file with the newly stamped version.
            wrn_msg = "Warning in Stamp_Replace_Single_File_Approval: " \
                      "After having stamped the file with the name [%s] " \
                      "and the fullpath [%s], it wasn't possible to revise " \
                      "that file with the newly stamped version. Stamping " \
                      "was unsuccessful. The submission ID is [%s] and the " \
                      "record ID is [%s]." \
                      % (name_file_to_stamp, \
                         file_stamper_options['input-file'], \
                         access, \
                         recid)
            register_exception(prefix=wrn_msg)
            raise InvenioWebSubmitFunctionWarning(wrn_msg)
        else:
            ## File revised. If the file should be renamed after stamping,
            ## do so.
            if new_file_name != "":
                try:
                    bibrecdocs.change_name(newname = new_file_name, docid = bibdoc_file_to_stamp.id)
                except (IOError, InvenioBibDocFileError):
                    ## Unable to change the name
                    wrn_msg = "Warning in Stamp_Replace_Single_File_Approval" \
                              ": After having stamped and revised the file " \
                              "with the name [%s] and the fullpath [%s], it " \
                              "wasn't possible to rename it to [%s]. The " \
                              "submission ID is [%s] and the record ID is " \
                              "[%s]." \
                              % (name_file_to_stamp, \
                                 file_stamper_options['input-file'], \
                                 new_file_name, \
                                 access, \
                                 recid)
    ## Finished.
    return ""


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
    ## First, strip off the leading and trailing spaces and braces:
    dict_string = dict_string.strip(" {}")

    ## Next, split the string on commas (,) that have not been escaped
    ## So, the following string: """'hello' : 'world', 'click' : 'here'"""
    ## will be split into the following list:
    ##   ["'hello' : 'world'", " 'click' : 'here'"]
    ##
    ## However, the string """'hello\, world' : '!', 'click' : 'here'"""
    ## will be split into: ["'hello\, world' : '!'", " 'click' : 'here'"]
    ## I.e. the comma that was escaped in the string has been kept.
    ##
    ## So basically, split on unescaped parameters at first:
    key_vals = re.split(r'(?<!\\),', dict_string)

    ## Now we should have a list of "key" : "value" terms. For each of them,
    ## check it is OK. If not in the format "Key" : "Value" (quotes are
    ## optional), discard it. As with the comma separator in the previous
    ## splitting, this one splits on the first colon (:) ONLY.
    final_dictionary = {}
    for key_value_string in key_vals:
        ## Split the pair apart, based on the first ":":
        key_value_pair = key_value_string.split(":", 1)
        ## check that the length of the new list is 2:
        if len(key_value_pair) != 2:
            ## There was a problem with the splitting - pass this pair
            continue
        ## The split was made.
        ## strip white-space, single-quotes and double-quotes from around the
        ## key and value pairs:
        key_term   = key_value_pair[0].strip(" '\"")
        value_term = key_value_pair[1].strip(" '\"")

        ## Is the left-side (key) term empty?
        if len(key_term) == 0:
            continue

        ## Now, add the search-replace pair to the dictionary of
        ## search-replace terms:
        final_dictionary[key_term] = value_term
    return final_dictionary


def _read_in_file(filepath):
    """Read the contents of a file into a string in memory.
       @param filepath: (string) - the path to the file to be read in.
       @return: (string) - the contents of the file.
    """
    if filepath != ""  and \
           os.path.exists("%s" % filepath):
        try:
            fh_filepath = open("%s" % filepath, "r")
            file_contents = fh_filepath.read()
            fh_filepath.close()
        except IOError:
            register_exception()
            file_contents = ""
    else:
        file_contents = ""
    return file_contents
