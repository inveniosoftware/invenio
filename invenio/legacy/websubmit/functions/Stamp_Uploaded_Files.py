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

"""Stamp_Uploaded_Files: A WebSubmit Function whose job is to stamp given
    files that were uploaded during a submission.
"""
__revision__ = "$Id$"

from invenio.ext.logging import register_exception
from invenio import websubmit_file_stamper
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionWarning, \
     InvenioWebSubmitFunctionError, InvenioWebSubmitFileStamperError
import os.path, shutil, re

def Stamp_Uploaded_Files(parameters, curdir, form, user_info=None):
    """
    Stamp certain files that have been uploaded during a submission.

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

         + files_to_be_stamped: (string) - The directories in which files
            should be stamped: This is a comma-separated list of directory
            names. E.g.:
               DEMOTHESIS_MAIN,DEMOTHESIS_ADDITIONAL

            (If you use Create_Upload_Files_Interface function, you
            should know that uploaded files goes under a subdirectory
            'updated/' of the /files/ folder in submission directory:
            in this case you have to specify this component in the
            parameter. For eg:
            updated/DEMOTHESIS_MAIN,updated/DEMOTHESIS_ADDITIONAL)

         + stamp: (string) - the type of stamp to be applied to the files.
            should be one of:
              + first (only the first page is stamped);
              + all (all pages are stamped);
              + coverpage (a separate cover-page is added to the file as a
                 first page);

         + layer: (string) - the position of the stamp. Should be one of:
              + background (invisible if original file has a white -
                            not transparent- background layer)
              + foreground (on top of the stamped file. If the stamp
                            does not have a transparent background,
                            will hide all of the document layers)

         + switch_file: (string) - when this value is set, specifies
            the name of a file that will swith on/off the
            stamping. The 'switch_file' must contain the names defined
            in 'files_to_be_stamped' (comma-separated values). Stamp
            will be applied only to files referenced in the
            switch_file. No stamp is applied if the switch_file is
            missing from the submission directory.
            However if the no switch_file is defined in this variable
            (parameter is left empty), stamps are applied according
            the variable 'files_to_be_stamped'.
            Useful for eg. if you want to let your users control the
            stamping with a checkbox on your submission page.

    If all goes according to plan, for each directory in which files are to
    be stamped, the original, unstamped files should be found in a
    directory 'files_before_stamping/DIRNAME', and the stamped versions
    should be found under 'files/DIRNAME'. E.g., for DEMOTHESIS_Main:
         - Unstamped: files_before_stamping/DEMOTHESIS_Main
         - Stamped:   files/DEMOTHESIS_Main
    """
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
    ## A dictionary of arguments to be passed to visit_for_stamping:
    visit_for_stamping_arguments = { 'curdir' : curdir,
                                     'file_stamper_options' : \
                                                file_stamper_options,
                                     'user_info' : user_info
                                   }

    ## Start by getting the parameter-values from WebSubmit:
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
    ## The directories in which files should be stamped:
    ## This is a comma-separated list of directory names. E.g.:
    ## DEMOTHESIS_MAIN,DEMOTHESIS_ADDITIONAL
    stamp_content_of = "%s" % ((type(parameters['files_to_be_stamped']) \
                                is str and parameters['files_to_be_stamped']) \
                               or "")
    ## Now split the list (of directories in which to stamp files) on commas:
    if stamp_content_of.strip() != "":
        stamping_locations = stamp_content_of.split(",")
    else:
        stamping_locations = []

    ## Check if stamping is enabled
    switch_file = parameters.get('switch_file', '')
    if switch_file:
        # Good, a "switch file" was specified. Check if it exists, and
        # it its value is not empty.
        switch_file_content = ''
        try:
            fd = file(os.path.join(curdir, switch_file))
            switch_file_content = fd.read().split(',')
            fd.close()
        except:
            switch_file_content = ''
        if not switch_file_content:
            # File does not exist, or is emtpy. Silently abort
            # stamping.
            return ""
        else:
            stamping_locations = [location for location in stamping_locations \
                                  if location in switch_file_content]

    if len(stamping_locations) == 0:
        ## If there are no items to be stamped, don't continue:
        return ""

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
                            err_msg = "Error in Stamp_Uploaded_Files: The " \
                                      "function attempted to read a LaTex " \
                                      "template variable value from the " \
                                      "following file in the current " \
                                      "submission's working directory: " \
                                      "[%s]. However, an unexpected error " \
                                      "was encountered when doing so. " \
                                      "Please inform the administrator." \
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
                    err_msg = "Error in Stamp_Uploaded_Files: The function " \
                              "was configured to read a LaTeX template " \
                              "variable from a file with the following " \
                              "instruction: [%s --> %s]. The filename, " \
                              "however, was not considered valid. Please " \
                              "report this to the administrator." \
                              % (varname, varvalue)
                    raise InvenioWebSubmitFunctionError(err_msg)

    ## Put the 'fixed' values into the file_stamper_options dictionary:
    file_stamper_options['latex-template'] = latex_template
    file_stamper_options['latex-template-var'] = latex_template_vars
    file_stamper_options['stamp'] = stamp
    file_stamper_options['layer'] = layer

    for stampdir in stamping_locations:
        ## Create the full path to the stamp directory - it is considered
        ## to be under 'curdir' - the working directory for the current
        ## submission:
        path_to_stampdir = "%s/files/%s" % (curdir, stampdir.strip())
        ## Call os.path.walk, passing it the path to the directory to be
        ## walked, the visit_for_stamping function (which will call the
        ## file-stamper for each file within that directory), and the
        ## dictionary of options to be passed to the file-stamper:
        try:
            os.path.walk(path_to_stampdir, \
                         visit_for_stamping, \
                         visit_for_stamping_arguments)
        except InvenioWebSubmitFunctionWarning:
            ## Unable to stamp the files in stampdir. Register the exception
            ## and continue to try to stamp the files in the other stampdirs:
            ## FIXME - The original exception was registered in 'visit'.
            ## Perhaps we should just send the message contained in this
            ## warning to the admin?
            register_exception(req=user_info['req'])
            continue
        except InvenioWebSubmitFunctionError as err:
            ## Unexpected error in stamping. The admin should be contacted
            ## because it has resulted in an unstable situation with the
            ## files. They are no longer in a well-defined state - some may
            ## have been lost and manual intervention by the admin is needed.
            ## FIXME - should this be reported here, or since we propagate it
            ## up to websubmit_engine anyway, should we let it register it?
            register_exception(req=user_info['req'])
            raise err
    return ""



def visit_for_stamping(visit_for_stamping_arguments, dirname, filenames):
    """Visitor function called by os.path.walk.
       This function takes a directory and a list of files in that directory
       and for each file, calls the websubmit_file_stamper on it.
       When a file is stamped, the original is moved away into a directory
       of unstamped files and the new, stamped version is moved into its
       place.
       @param visit_for_stamping_arguments: (dictionary) of arguments needed
        by this function. Must contain 'curdir', 'user_info' and
        'file_stamper_options' members.
       @param dirname: (string) - the path to the directory in which the
        files are to be stamped.
       @param filenames: (list) - the names of each file in dirname. An
        attempt will be made to stamp each of these files.
       @Exceptions Raised:
         + InvenioWebSubmitFunctionWarning;
         + InvenioWebSubmitFunctionError;
    """
    ## Get the dictionary of options to pass to the stamper:
    file_stamper_options = visit_for_stamping_arguments['file_stamper_options']

    ## Create a directory to store original files before stamping:
    dirname_files_pre_stamping = dirname.replace("/files/", \
                                                 "/files_before_stamping/", 1)
    if not os.path.exists(dirname_files_pre_stamping):
        try:
            os.makedirs(dirname_files_pre_stamping)
        except OSError as err:
            ## Unable to make a directory in which to store the unstamped
            ## files.
            ## Register the exception:
            exception_prefix = "Unable to stamp files in [%s]. Couldn't " \
                               "create directory in which to store the " \
                               "original, unstamped files." \
                               % dirname
            register_exception(prefix=exception_prefix)
            ## Since we can't make a directory for the unstamped files,
            ## we can't continue to stamp them.
            ## Skip the stamping of the contents of this directory by raising
            ## a warning:
            msg = "Warning: A problem occurred when stamping files in [%s]. " \
                  "Unable to create directory to store the original, " \
                  "unstamped files. Got this error: [%s]. This means the " \
                  "files in this directory were not stamped." \
                  % (dirname, str(err))
            raise InvenioWebSubmitFunctionWarning(msg)


    ## Loop through each file in the directory and attempt to stamp it:
    for file_to_stamp in filenames:
        ## Get the path to the file to be stamped and put it into the
        ## dictionary of options that will be passed to stamp_file:
        path_to_subject_file = "%s/%s" % (dirname, file_to_stamp)
        file_stamper_options['input-file'] = path_to_subject_file

        ## Just before attempting to stamp the file, log the dictionary of
        ## options (file_stamper_options) that will be passed to websubmit-
        ## file-stamper:
        try:
            fh_log = open("%s/websubmit_file_stamper-calls-options.log" \
                          % visit_for_stamping_arguments['curdir'], "a+")
            fh_log.write("%s\n" % file_stamper_options)
            fh_log.flush()
            fh_log.close()
        except IOError:
            ## Unable to log the file stamper options.
            exception_prefix = "Unable to write websubmit_file_stamper " \
                               "options to log file " \
                               "%s/websubmit_file_stamper-calls-options.log" \
                               % visit_for_stamping_arguments['curdir']
            register_exception(prefix=exception_prefix)

        try:
            ## Try to stamp the file:
            (stamped_file_path_only, stamped_file_name) = \
                    websubmit_file_stamper.stamp_file(file_stamper_options)
        except InvenioWebSubmitFileStamperError:
            ## It wasn't possible to stamp this file.
            ## Register the exception along with an informational message:
            exception_prefix = "A problem occurred when stamping [%s]. The " \
                               "stamping of this file was unsuccessful." \
                               % path_to_subject_file
            register_exception(prefix=exception_prefix)
            ## Skip this file, moving on to the next:
            continue
        else:
            ## Stamping was successful.
            path_to_stamped_file = "%s/%s" % (stamped_file_path_only, \
                                              stamped_file_name)
            ## Move the unstamped file from the "files" directory into the
            ## "files_before_stamping" directory:
            try:
                shutil.move(path_to_subject_file, "%s/%s" \
                            % (dirname_files_pre_stamping, file_to_stamp))
            except IOError:
                ## Couldn't move the original file away from the "files"
                ## directory. Log the problem and continue on to the next
                ## file:
                exception_prefix = "A problem occurred when stamping [%s]. " \
                                   "The file was sucessfully stamped, and " \
                                   "can be found here: [%s]. Unfortunately " \
                                   "though, it could not be copied back to " \
                                   "the current submission's working " \
                                   "directory because the unstamped version " \
                                   "could not be moved out of the way (tried " \
                                   "to move it from here [%s] to here: " \
                                   "[%s/%s]). The stamping of this file was " \
                                   "unsuccessful." \
                                   % (path_to_subject_file, \
                                      path_to_stamped_file, \
                                      path_to_subject_file, \
                                      dirname_files_pre_stamping, \
                                      file_to_stamp)
                register_exception(prefix=exception_prefix)
                continue
            else:
                ## The original file has been moved into the files before
                ## stamping directory. Now try to copy the stamped file into
                ## the files directory:
                try:
                    shutil.copy(path_to_stamped_file, "%s/%s" \
                                % (dirname, file_to_stamp))
                except IOError:
                    ## Even though the original, unstamped file was moved away
                    ## from the files directory, the stamped-version couldn't
                    ## be moved into its place. Register the exception:
                    exception_prefix = "A problem occurred when stamping " \
                                       "[%s]. The file was sucessfully " \
                                       "stamped, and can be found here: " \
                                       "[%s]. Unfortunately though, it " \
                                       "could not be copied back to the " \
                                       "current submission's working " \
                                       "directory." % (path_to_subject_file, \
                                                       path_to_stamped_file)
                    register_exception(prefix=exception_prefix)

                    ## Because it wasn't possible to move the stamped file
                    ## into the files directory, attempt to move the original,
                    ## unstamped file back into the files directory:
                    try:
                        shutil.move("%s/%s" % (dirname_files_pre_stamping, \
                                               file_to_stamp), \
                                    path_to_stamped_file)
                    except IOError as err:
                        ## It wasn't possible even to move the original file
                        ## back to the files directory. Register the
                        ## exception and stop the stamping process - it isn't
                        ## safe to continue:
                        exeption_prefix = "A problem occurred when stamping " \
                                          "[%s]. The file was sucessfully " \
                                           "stamped, and can be found here: " \
                                           "[%s]. Unfortunately though, it " \
                                           "could not be copied back to the " \
                                           "current submission's working " \
                                           "directory. Additionionally, the " \
                                           "original, unstamped file " \
                                           "could not be moved back to the " \
                                           "files directory, from the files-" \
                                           "before-stamping directory. It " \
                                           "can now be found here: [%s/%s]. " \
                                           "Stamping cannot continue and " \
                                           "manual intervention is necessary " \
                                           "because the file cannot be " \
                                           "attached to the record." \
                                           % (path_to_subject_file, \
                                              path_to_stamped_file, \
                                              dirname_files_pre_stamping, \
                                              file_to_stamp)
                        register_exception(prefix=exeption_prefix)
                        ## Raise an InvenioWebSubmitFunctionError, stopping
                        ## further stamping, etc:
                        raise InvenioWebSubmitFunctionError(exception_prefix)


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
