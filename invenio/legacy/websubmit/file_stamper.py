# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011 CERN.
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

from __future__ import print_function

"""This is websubmit_file_stamper.py
   This tool is used to create a stamped version of a PDF file.

   + Python API:
      Please see stamp_file().

   + CLI API:
    $ python ~invenio/lib/python/invenio/websubmit_file_stamper.py \\
              --latex-template=demo-stamp-left.tex \\
              --latex-template-var='REPORTNUMBER=TEST-THESIS-2008-019' \\
              --latex-template-var='DATE=27/02/2008' \\
              --stamp='first' \\
              --layer='background' \\
              --output-file=testfile_stamped.pdf \\
              testfile.pdf
"""

__revision__ = "$Id$"


import getopt, sys, re, os, time, shutil, tempfile

from six import iteritems

from invenio.config import \
	CFG_PATH_PS2PDF, \
	CFG_PATH_GFILE,\
	CFG_PATH_PDFLATEX
from invenio.ext.logging import register_exception
from invenio.config import CFG_TMPDIR
from invenio.config import CFG_ETCDIR

CFG_WEBSUBMIT_FILE_STAMPER_TEMPLATES_DIR = \
        pkg_resources.resource_filename('invenio.legacy.websubmit', 'file_stamper_templates')
from invenio.config import CFG_PATH_PDFTK
from invenio.utils.shell import escape_shell_arg
from invenio.legacy.websubmit.config import InvenioWebSubmitFileStamperError


# ***** Functions related to the creation of the PDF Stamp file: *****
re_latex_includegraphics = re.compile('\\includegraphics\[.*?\]\{(?P<image>.*?)\}')
def copy_template_files_to_stampdir(path_workingdir, latex_template):
    """In order to stamp a PDF fulltext file, LaTeX is used to create a
       "stamp" page that is then merged with the fulltext PDF.
       The stamp page is created in a temporary stamp "working directory".
       This means that the LaTeX file and its image files must be copied
       locally into this working directory. This function handles
       copying them into the working directory.

       Note: Copying of the LaTeX template and its included image files is
             fairly naive and assumes that it is a very basic LaTeX file
             consisting of a main file and any included graphics.
             No other included file items will be copied.

             Also note that the order of searching for the LaTeX file and
             its associated graphics is as follows:
               + If the templatename provided has a path attached to it,
                 look here first;
               + If there is no path, look in the current dir.
               + If there is no template in the current dir, look in
                 ~invenio/etc/websubmit/latex
               + Images included within the LaTeX file are sought in the
                 same way. Full path is used if provided; if not, current
                 dir and failing that ~invenio/etc/websubmit/latex.

       @param path_workingdir: (string) - the working directory into which the
        latex templates should be copied.
       @param latex_template: (string) - the name of the LaTeX template to copy
        to the working dir.
    """
    ## Get the "base name" of the latex template:
    (template_path, template_name) = os.path.split(latex_template)
    if template_path != "":
        ## A full path to the template was provided. We look for it there.
        ## Test to see whether the template is a real file and is readable:
        if os.access("%s/%s" % (template_path, template_name), os.R_OK):
            ## Template is readable. Copy it locally to the working directory:
            try:
                shutil.copyfile("%s/%s" % (template_path, template_name), \
                                "%s/%s" % (path_workingdir, template_name))
            except IOError:
                ## Unable to copy the LaTeX template file to the
                ## working directory:
                msg = """Error: Unable to copy LaTeX file [%s/%s] to """ \
                      """working directory for stamping [%s].""" \
                      % (template_path, template_name, path_workingdir)
                raise InvenioWebSubmitFileStamperError(msg)
        else:
            ## Unable to read the template file:
            msg = """Error: Unable to copy LaTeX file [%s/%s] to """ \
                  """working directory for stamping [%s]. (File not """ \
                  """readable.)""" \
                  % (template_path, template_name, path_workingdir)
            raise InvenioWebSubmitFileStamperError(msg)
    else:
        ## There is no path to the template file.
        ## Look for it first in the current working directory, then in
        ## ~invenio/websubmit/latex;
        ## If not found in either, give up.
        if os.access("%s" % (template_name), os.F_OK):
            ## Template has been found in the current working directory.
            ## Copy it locally to the stamping working directory:
            try:
                shutil.copyfile("%s" % (template_name), \
                                "%s/%s" % (path_workingdir, template_name))
            except IOError:
                ## Unable to copy the LaTeX template file to the
                ## working stamping directory:
                msg = """Error: Unable to copy LaTeX file [%s] to """ \
                      """working directory for stamping [%s].""" \
                      % (template_name, path_workingdir)
                raise InvenioWebSubmitFileStamperError(msg)
        elif os.access("%s/%s" % (CFG_WEBSUBMIT_FILE_STAMPER_TEMPLATES_DIR, \
                                  template_name), os.F_OK):
            ## The template has been found in WebSubmit's latex templates
            ## directory. Copy it locally to the stamping working directory:
            try:
                shutil.copyfile("%s/%s" \
                                % (CFG_WEBSUBMIT_FILE_STAMPER_TEMPLATES_DIR, \
                                   template_name), \
                                "%s/%s" % (path_workingdir, template_name))
            except IOError:
                ## Unable to copy the LaTeX template file to the
                ## working stamping directory:
                msg = """Error: Unable to copy LaTeX file [%s/%s] to """ \
                      """working directory for stamping [%s].""" \
                      % (CFG_WEBSUBMIT_FILE_STAMPER_TEMPLATES_DIR, \
                         template_name, path_workingdir)
                raise InvenioWebSubmitFileStamperError(msg)
            else:
                ## Now that the template has been found, set the "template
                ## path" to the WebSubmit latex templates directory:
                template_path = CFG_WEBSUBMIT_FILE_STAMPER_TEMPLATES_DIR
        else:
            ## Unable to locate the latex template.
            msg = """Error: Unable to locate LaTeX file [%s].""" % template_name
            raise InvenioWebSubmitFileStamperError(msg)

    ## Now that the LaTeX template file has been copied locally, extract
    ## the names of graphics files to be included in the resulting
    ## document and attempt to copy them to the working "stamp" directory:
    template_desc = file(os.path.join(path_workingdir, template_name))
    template_code = template_desc.read()
    template_desc.close()
    graphic_names = [match_obj.group('image') for match_obj in \
                     re_latex_includegraphics.finditer(template_code)]

    ## Copy each include-graphic extracted from the template
    ## into the working stamp directory:
    for graphic in graphic_names:
        ## Remove any leading/trailing whitespace:
        graphic = graphic.strip()
        ## Get the path and "base name" of the included graphic:
        (graphic_path, graphic_name) = os.path.split(graphic)

        ## If there is a graphic_name to work with, try copy the file:
        if graphic_name != "":
            if graphic_path != "":
                ## The graphic is included from an absolute path:
                if os.access("%s/%s" % (graphic_path, graphic_name), os.F_OK):
                    try:
                        shutil.copyfile("%s/%s" % (graphic_path, \
                                                   graphic_name), \
                                        "%s/%s" % (path_workingdir, \
                                                   graphic_name))
                    except IOError:
                        ## Unable to copy the LaTeX template file to
                        ## the current directory
                        msg = """Unable to stamp file. There was """ \
                              """a problem when trying to copy an image """ \
                              """[%s/%s] included by the LaTeX template""" \
                              """ [%s].""" \
                              % (graphic_path, graphic_name, template_name)
                        raise InvenioWebSubmitFileStamperError(msg)
                else:
                    msg = """Unable to locate an image [%s/%s] included""" \
                          """ by the LaTeX template file [%s].""" \
                          % (graphic_path, graphic_name, template_name)
                    raise InvenioWebSubmitFileStamperError(msg)
            else:
                ## The graphic is included from a relative path. Try to obtain
                ## it from the same directory that the latex template file was
                ## taken from:
                if template_path != "":
                    ## Since template path is not empty, try to get the images
                    ## from that location:
                    if os.access("%s/%s" % (template_path, graphic_name), \
                                 os.F_OK):
                        try:
                            shutil.copyfile("%s/%s" % (template_path, \
                                                       graphic_name), \
                                            "%s/%s" % (path_workingdir, \
                                                       graphic_name))
                        except IOError:
                            ## Unable to copy the LaTeX template file to
                            ## the current directory
                            msg = """Unable to stamp file. There was """ \
                                  """a problem when trying to copy images """ \
                                  """included by the LaTeX template."""
                            raise InvenioWebSubmitFileStamperError(msg)
                    else:
                        msg = """Unable to locate an image [%s] included""" \
                              """ by the LaTeX template file [%s].""" \
                              % (graphic_name, template_name)
                        raise InvenioWebSubmitFileStamperError(msg)
                else:
                    ## There is no template path. Try to get the images from
                    ## current dir:
                    if os.access("%s" % graphic_name, os.F_OK):
                        try:
                            shutil.copyfile("%s" % graphic_name, \
                                            "%s/%s" % (path_workingdir, \
                                                       graphic_name))
                        except IOError:
                            ## Unable to copy the LaTeX template file to
                            ## the current directory
                            msg = """Unable to stamp file. There was """ \
                                  """a problem when trying to copy images """ \
                                  """included by the LaTeX template."""
                            raise InvenioWebSubmitFileStamperError(msg)
                    else:
                        msg = """Unable to locate an image [%s] included""" \
                              """ by the LaTeX template file [%s].""" \
                              % (graphic_name, template_name)
                        raise InvenioWebSubmitFileStamperError(msg)
    ## Return the basename of the template so that it can be used to create
    ## the PDF stamp file:
    return template_name


def create_final_latex_template(working_dirname, \
                                latex_template, \
                                latex_template_var):
    """In the working directory, create a copy of the the orginal
       latex template with all the possible xxx--xxx in the template
       replaced with the values identified by the keywords in the
       latex_template_var dictionary.
       @param working_dirname: (string) the working directory used for the
        creation of the PDF stamp file.
       @latex_template: (string) name of the latex template before it has
        been parsed for replacements.
       @latex_template_var: (dict) dictionnary whose keys are the string to
        replace in latex_template and values are the replacement content
       @return: name of the final latex template (after replacements)
    """
    ## Regexp used for finding a substitution line in the original template:
    re_replacement = re.compile("""XXX-(.+?)-XXX""")

    ## Now, read-in the local copy of the template and parse it line-by-line,
    ## replacing any ocurrences of "XXX-SEARCHWORD-XXX" with either:
    ##
    ## (a) The value from the "replacements" dictionary;
    ## (b) Nothing if there was no search-term in the dictionary;
    try:
        ## Open the original latex template for reading:
        fpread  = open("%s/%s" \
                       % (working_dirname, latex_template), "r")
        ## Open a file to contain the "parsed" latex template:
        fpwrite = open("%s/create%s" \
                       % (working_dirname, latex_template), "w")
        for line in fpread.readlines():
            ## For each line in the template file, test for
            ## substitution-markers:
            replacement_markers = re_replacement.finditer(line)
            ## For each replacement-pattern detected in this line, process it:
            for replacement_marker in replacement_markers:
                ## Found a match:
                search_term = replacement_marker.group(1)
                try:
                    ## Get the replacement-term for this match
                    ## from the dictionary
                    replacement_term = latex_template_var[search_term]
                except KeyError:
                    ## This search-term was not in the list of replacements
                    ## to be made. It should be replaced with an empty string
                    ## in the template:
                    line = line[0:replacement_marker.start()] + \
                           line[replacement_marker.end():]
                else:
                    ## Is the replacement term of the form date(XXXX)? If yes,
                    ## take it literally and generate a pythonic date with it:
                    if replacement_term.find("date(") == 0 \
                           and replacement_term[-1] == ")":
                        ## Take the date format string, use it to
                        ## generate today's date
                        date_format = replacement_term[5:-1].strip('\'"')
                        try:
                            replacement = time.strftime(date_format, \
                                                        time.localtime())
                        except TypeError:
                            ## Bad date format
                            replacement = ""
                    elif replacement_term.find("include(") == 0 \
                             and replacement_term[-1] == ")":
                        ## Replacement term is a directive to include a file
                        ## in the LaTeX template:
                        replacement = replacement_term[8:-1].strip('\'"')
                    else:
                        ## Take replacement_term as a literal string
                        ## to be inserted into the template at this point.
                        replacement = replacement_term

                    ## Now substitute replacement into the line of the template:
                    line = line[0:replacement_marker.start()] + replacement \
                           + line[replacement_marker.end():]

            ## Write the modified line to the new template:
            fpwrite.write(line)
            fpwrite.flush()
        ## Close up the template files and unlink the original:
        fpread.close()
        fpwrite.close()
    except IOError:
        msg = "Unable to read LaTeX template [%s/%s]. Cannot Stamp File" \
              % (working_dirname, latex_template)
        raise InvenioWebSubmitFileStamperError(msg)

    ## Return the name of the LaTeX template to be used:
    return "create%s" % latex_template


def escape_latex_meta_characters(text):
    """The following are LaTeX meta characters that must be escaped with a
       backslash:
        # $ % & _ { }
       This function therefore takes a string as input and does a simple
       replace of these characters with escaped versions.
       @param text: (string) - the string to be escaped.
       @return: (string) - the string in which the LaTeX meta characters
        have been escaped.
    """
    text = text.replace('#', '\#')
    text = text.replace('$', '\$')
    text = text.replace('%', '\%')
    text = text.replace('&', '\&')
    text = text.replace('_', '\_')
    text = text.replace('{', '\{')
    text = text.replace('}', '\}')
    return text


def escape_latex_template_vars(template_vars, strict=False):
    """Take a dictionary of LaTeX template variables/values and escape LaTeX
       meta characters in some of them, or all of them depending upon whether
       a call is made in strict mode (if strict is set, ALL values are
       escaped.)
       Operating in non-strict mode, the rules for escaping are as follows:
        * If the string does not contain $ { or }, it must be escaped.
        * If the string contains $, then there must be an even number of
          these. If the count is even, do not escape. Else, escape.
        * If the string contains { or }, it must be balanced with a
          counterpart. That's to say that the count of "{" must match the
          count of "}". If it does, do not escape. Else, escape.
       @param template_vars: (dictionary) - the LaTeX template variables and
        their values.
       @param strict: (boolean) - a flag indicating whether or not to
        operate in strict mode. Strict mode means that all values are
        escaped regardless of whether or not they are considered to be
        "good" LaTeX.
       @return: (dictionary) - the LaTeX template variables with their
        values escaped.
    """
    ## Make a copy of the LaTeX template variables so as not to corrupt
    ## the original:
    working_template_vars = template_vars.copy()
    ##
    ## For each of the variables, escape LaTeX meta characteras in the
    ## value according to the strict flag:
    varnames = working_template_vars.keys()
    for varname in varnames:
        escape_value = False
        varval = working_template_vars[varname]
        ## We don't want to escape values that are date or include directives
        ## so unfortunately, this if is needed here:
        if (varval.find("date(") == 0 or varval.find("include(") == 0) and \
           varval[-1] == ")":
            ## This is a date or include directive:
            continue

        ## Count the number of "$", "{" and "}" in it. If any are present,
        ## they should be balanced. If so, we will assume that they are
        ## wanted and that the LaTeX in the string is good.
        ## If, however, they are not balanced, we will assume that they are
        ## not valid LaTeX commands and that the string should be escaped.
        ## If they are not present at all, we assume that the string should
        ## be escaped.
        if "$" in varval and varval.count("$") % 2 != 0:
            ## $ is present, but not in an even number. This string must
            ## be escaped:
            escape_value = True
        elif "{" in varval or "}" in varval:
            ## "{" and/or "}" is in the value string. Count each of them.
            ## If they are not matched one to one, consider the string to be
            ## in need of escaping:
            if varval.count("{") != varval.count("}"):
                escape_value = True
        elif "$" not in varval and "{" not in varval and "}" not in varval:
            ## Since none of $ { } are in the string, it should be escaped
            ## to be safe:
            escape_value = True
        ##
        if strict:
            ## If operating in strict mode, escape everything whatever the
            ## results of the above tests:
            escape_value = True

        ## If the value is to be escaped, go ahead and do so:
        if escape_value:
            escaped_varval = escape_latex_meta_characters(varval)
            working_template_vars[varname] = escaped_varval
    ## Return the "escaped" LaTeX template variables:
    return working_template_vars


def create_pdf_stamp(path_workingdir, latex_template, latex_template_var):
    """Retrieve the LaTeX (and associated) files and use them to create a
       PDF "Stamp" file that can be merged with the main file.
       The PDF stamp is created in a temporary working directory.
       @param path_workingdir: (string) the path to the working directory
        that should be used for creating the PDF stamp file.
       @param latex_template: (string) - the name of the latex template
        to be used for the creation of the stamp.
       @param latex_template_var: (dictionary) - key-value pairs of strings
        to be sought and replaced within the latex template.
       @return: (string) - the name of the PDF stamp file.
    """
    ## Copy the LaTeX (and helper) files should be copied into the working dir:
    template_name = copy_template_files_to_stampdir(path_workingdir, \
                                                    latex_template)
    ##
    ####
    ## Make a first attempt at the template PDF creation, escaping the variables
    ## in non-strict mode:
    escaped_latex_template_var = escape_latex_template_vars(latex_template_var)
    ## Now that the latex template and its helper files have been retrieved,
    ## the Stamp PDF can be created.
    final_template = create_final_latex_template(path_workingdir, \
                                                 template_name, \
                                                 escaped_latex_template_var)
    ##
    ## The name that will be givem to the PDF stamp file:
    pdf_stamp_name = "%s.pdf" % os.path.splitext(final_template)[0]
    ## Now, build the Stamp PDF from the LaTeX template:
    cmd_latex = """cd %(workingdir)s; %(path_pdflatex)s """ \
                """-interaction=batchmode """ \
                """%(template-path)s > /dev/null 2>&1""" \
                % { 'template-path' : escape_shell_arg("%s/%s" \
                                          % (path_workingdir, final_template)),
                    'workingdir'    : path_workingdir,
                    'path_pdflatex' : CFG_PATH_PDFLATEX,
                  }
    ## Log the latex command
    os.system("""echo %s > %s""" % (escape_shell_arg(cmd_latex), \
                                    escape_shell_arg("%s/latex_cmd_first_try" \
                                                     % path_workingdir)))
    ## Run the latex command
    errcode_latex = os.system("%s" % cmd_latex)

    ## Was the PDF stamp file successfully created without error?
    if errcode_latex:
        ## No it wasn't. Perhaps there was a problem with some of the variable
        ## values that we substituted into the template?
        ## To be certain, try to create the PDF one more time - this time
        ## escaping all of the variable values.
        ##
        ## Unlink the PDF file if one was created on the previous attempt:
        if os.access("%s/%s" % (path_workingdir, pdf_stamp_name), os.F_OK):
            try:
                os.unlink("%s/%s" % (path_workingdir, pdf_stamp_name))
            except OSError:
                ## Unable to unlink the PDF file.
                err_msg = "Unable to unlink the PDF stamp file [%s]. " \
                          "Stamping has failed." \
                          % pdf_stamp_name
                register_exception(prefix=err_msg)
                raise InvenioWebSubmitFileStamperError(err_msg)
        ##
        ## Unlink the LaTeX template file that was created with the previously
        ## escaped variables:
        if os.access("%s/%s" % (path_workingdir, final_template), os.F_OK):
            try:
                os.unlink("%s/%s" % (path_workingdir, final_template))
            except OSError:
                ## Unable to unlink the LaTeX file.
                err_msg = "Unable to unlink the LaTeX stamp template file " \
                          "[%s]. Stamping has failed." \
                          % final_template
                register_exception(prefix=err_msg)
                raise InvenioWebSubmitFileStamperError(err_msg)
        ##
        ####
        ## Make another attempt at the template PDF creation, this time escaping
        ## the variables in strict mode:
        escaped_latex_template_var = \
                     escape_latex_template_vars(latex_template_var, strict=True)
        ## Now that the latex template and its helper files have been retrieved,
        ## the Stamp PDF can be created.
        final_template = create_final_latex_template(path_workingdir, \
                                                     template_name, \
                                                     escaped_latex_template_var)
        ##
        ## The name that will be givem to the PDF stamp file:
        pdf_stamp_name = "%s.pdf" % os.path.splitext(final_template)[0]
        ## Now, build the Stamp PDF from the LaTeX template:
        cmd_latex = """cd %(workingdir)s; %(path_pdflatex)s """ \
                    """-interaction=batchmode """ \
                    """%(template-path)s > /dev/null 2>&1""" \
                    % { 'template-path' : escape_shell_arg("%s/%s" \
                                          % (path_workingdir, final_template)),
                        'workingdir'    : path_workingdir,
                        'path_pdflatex' : CFG_PATH_PDFLATEX,
                      }
        ## Log the latex command
        os.system("""echo %s > %s""" \
                  % (escape_shell_arg(cmd_latex), \
                     escape_shell_arg("%s/latex_cmd_second_try" \
                                      % path_workingdir)))
        ## Run the latex command
        errcode_latex = os.system("%s" % cmd_latex)

    ## Was the PDF stamp file successfully created?
    if errcode_latex or \
         not  os.access("%s/%s" % (path_workingdir, pdf_stamp_name), os.F_OK):
        ## It was not possible to create the PDF stamp file. Fail.
        msg = """Error: Unable to create a PDF stamp file."""
        raise InvenioWebSubmitFileStamperError(msg)

    ## Return the name of the PDF stamp file:
    return pdf_stamp_name


# ***** Functions related to the actual stamping of the file: *****

def apply_stamp_cover_page(path_workingdir, \
                           stamp_file_name, \
                           subject_file, \
                           output_file):
    """Carry out the stamping:
       This function adds a cover-page to the file.
       @param path_workingdir: (string) - the path to the working directory
        that contains all of the files needed for the stamping process to be
        carried out.
       @param stamp_file_name: (string) - the name of the PDF stamp file (i.e.
        the cover-page itself).
       @param subject_file: (string) - the name of the file to be stamped.
       @param output_file: (string) - the name of the final "stamped" file (i.e.
        that with the cover page added) that will be written in the working
        directory after the function has ended.
    """
    ## Build the stamping command:
    cmd_add_cover_page = \
                """%(pdftk)s %(cover-page-path)s """ \
                """%(file-to-stamp-path)s """ \
                """cat output %(stamped-file-path)s """ \
                """2>/dev/null"""% \
                  { 'pdftk'              : CFG_PATH_PDFTK,
                    'cover-page-path'    : escape_shell_arg("%s/%s" \
                                                % (path_workingdir, \
                                                   stamp_file_name)),
                    'file-to-stamp-path' : escape_shell_arg("%s/%s" \
                                                % (path_workingdir, \
                                                   subject_file)),
                    'stamped-file-path'  : escape_shell_arg("%s/%s" \
                                                % (path_workingdir, \
                                                   output_file)),
                  }
    ## Execute the stamping command:
    errcode_add_cover_page = os.system(cmd_add_cover_page)

    ## Was the PDF merged with the coverpage without error?
    if errcode_add_cover_page:
        ## There was a problem:
        msg = "Error: Unable to stamp file [%s/%s]. There was an error when " \
              "trying to add the cover page [%s/%s] to the file. Stamping " \
              "has failed." \
              % (path_workingdir, \
                 subject_file, \
                 path_workingdir, \
                 stamp_file_name)
        raise InvenioWebSubmitFileStamperError(msg)


def apply_stamp_first_page(path_workingdir, \
                           stamp_file_name, \
                           subject_file, \
                           output_file, \
                           stamp_layer):
    """Carry out the stamping:
       This function adds a stamp to the first page of the file.
       @param path_workingdir: (string) - the path to the working directory
        that contains all of the files needed for the stamping process to be
        carried out.
       @param stamp_file_name: (string) - the name of the PDF stamp file (i.e.
        the stamp itself).
       @param subject_file: (string) - the name of the file to be stamped.
       @param output_file: (string) - the name of the final "stamped" file that
        will be written in the working directory after the function has ended.
       @param stamp_layer: (string) - the layer to consider when stamping

    """
    ## Since only the first page of the subject file is to be stamped,
    ## it's safest to separate this into its own temporary file, stamp
    ## it, then re-merge it with the remaining pages of the original
    ## document.  In this way, the PDF to be stamped will probably be
    ## simpler (pages with complex figures and tables will probably be
    ## avoided) and the process will hopefully have a smaller chance of
    ## failure.
    ##
    ## First of all, separate the first page of the subject file into a
    ## temporary document:
    ##
    ## Name to be given to the first page of the document:
    output_file_first_page = "p1-%s" % output_file
    ## Name to be given to the first page of the document once it has
    ## been stamped:
    stamped_output_file_first_page = "stamped-%s" % output_file_first_page

    ## Perform the separation:
    cmd_get_first_page = \
             "%(pdftk)s A=%(file-to-stamp-path)s " \
             "cat A1 output %(first-page-path)s " \
             "2>/dev/null" \
             % { 'pdftk'         : CFG_PATH_PDFTK,
                 'file-to-stamp-path' : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, subject_file)),
                 'first-page-path'    : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               output_file_first_page)),
               }
    errcode_get_first_page = os.system(cmd_get_first_page)
    ## Check that the separation was successful:
    if errcode_get_first_page or \
           not os.access("%s/%s" % (path_workingdir, \
                                    output_file_first_page), os.F_OK):
        ## Separation was unsuccessful. Fail.
        msg = "Error: Unable to stamp file [%s/%s] - it wasn't possible to " \
              "separate the first page from the rest of the document. " \
              "Stamping has failed." \
              % (path_workingdir, subject_file)
        raise InvenioWebSubmitFileStamperError(msg)

    ## Now stamp the first page:
    cmd_stamp_first_page = \
             "%(pdftk)s %(first-page-path)s %(stamp_layer)s " \
             "%(stamp-file-path)s output " \
             "%(stamped-first-page-path)s 2>/dev/null" \
             % { 'pdftk'                   : CFG_PATH_PDFTK,
                 'first-page-path'         : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               output_file_first_page)),
                 'stamp-file-path'         : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               stamp_file_name)),
                 'stamped-first-page-path' : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               stamped_output_file_first_page)),
                 'stamp_layer'             : stamp_layer == 'foreground' and 'stamp' or 'background'
               }
    errcode_stamp_first_page = os.system(cmd_stamp_first_page)
    ## Check that the first page was stamped successfully:
    if errcode_stamp_first_page or \
           not os.access("%s/%s" % (path_workingdir, \
                                    stamped_output_file_first_page), os.F_OK):
        ## Unable to stamp the first page. Fail.
        msg = "Error: Unable to stamp the file [%s/%s] - it was not possible " \
              "to add the stamp to the first page. Stamping has failed." \
              % (path_workingdir, subject_file)
        raise InvenioWebSubmitFileStamperError(msg)

    ## Now that the first page has been stamped successfully, merge it with
    ## the remaining pages of the original file:
    cmd_merge_stamped_and_original_files = \
             "%(pdftk)s A=%(stamped-first-page-path)s  " \
             "B=%(original-file-path)s cat A1 B2-end output " \
             "%(stamped-file-path)s 2>/dev/null" \
             % { 'pdftk'              : CFG_PATH_PDFTK,
                 'stamped-first-page-path' : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               stamped_output_file_first_page)),
                 'original-file-path'      : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               subject_file)),
                 'stamped-file-path'       : escape_shell_arg("%s/%s" % \
                                              (path_workingdir, \
                                               output_file)),
               }
    errcode_merge_stamped_and_original_files = \
                   os.system(cmd_merge_stamped_and_original_files)
    ## Check to see whether the command exited with an error:
    if errcode_merge_stamped_and_original_files:
        ## There was an error when trying to merge the stamped first-page
        ## with pages 2 onwards of the original file. One possible
        ## explanation for this could be that the original file only had
        ## one page (in which case trying to reference pages 2-end would
        ## cause an error because they don't exist.
        ##
        ## Try to get the number of pages in the original PDF. If it only
        ## has 1 page, the stamped first page file can become the final
        ## stamped PDF. If it has more than 1 page, there really was an
        ## error when merging the stamped first page with the rest of the
        ## pages and stamping can be considered to have failed.
        cmd_find_number_pages = \
           """%(pdftk)s %(original-file-path)s dump_data | """ \
           """grep NumberOfPages | """ \
           """sed -n 's/^NumberOfPages: \\([0-9]\\{1,\\}\\)$/\\1/p'""" \
             % { 'pdftk'              : CFG_PATH_PDFTK,
                 'original-file-path' : escape_shell_arg("%s/%s" % \
                                                        (path_workingdir, \
                                                         subject_file)),
               }
        fh_find_number_pages = os.popen(cmd_find_number_pages, "r")
        match_number_pages = fh_find_number_pages.read()
        errcode_find_number_pages = fh_find_number_pages.close()

        if errcode_find_number_pages is not None:
            ## There was an error while checking for the number of pages.
            ## Fail.
            msg = "Error: Unable to stamp file [%s/%s]. There was an error " \
                  "when attempting to merge the file containing the " \
                  "first page of the stamped file with the remaining " \
                  "pages of the original file and when an attempt was " \
                  "made to count the number of pages in the file, an " \
                  "error was also encountered. Stamping has failed." \
                  % (path_workingdir, subject_file)
            raise InvenioWebSubmitFileStamperError(msg)
        else:
            try:
                number_pages_in_subject_file = int(match_number_pages)
            except ValueError:
                ## Unable to get the number of pages in the original file.
                ## Fail.
                msg = "Error: Unable to stamp file [%s/%s]. There was an " \
                      "error when attempting to merge the file containing the" \
                      " first page of the stamped file with the remaining " \
                      "pages of the original file and when an attempt was " \
                      "made to count the number of pages in the file, an " \
                      "error was also encountered. Stamping has failed." \
                      % (path_workingdir, subject_file)
                raise InvenioWebSubmitFileStamperError(msg)
            else:
                ## Do we have just one page?
                if number_pages_in_subject_file == 1:
                    ## There was only one page in the subject file.
                    ## copy the version that was stamped on the first page to
                    ## the output_file filename:
                    try:
                        shutil.copyfile("%s/%s" \
                                         % (path_workingdir, \
                                         stamped_output_file_first_page), \
                                        "%s/%s" \
                                         % (path_workingdir, output_file))
                    except IOError:
                        ## Unable to copy the file that was stamped on page 1
                        ## Stamping has failed.
                        msg = "Error: It was not possible to copy the " \
                              "temporary file that was stamped on the " \
                              "first page [%s/%s] to the final stamped " \
                              "file [%s/%s]. Stamping has failed." \
                              % (path_workingdir, \
                                 stamped_output_file_first_page, \
                                 path_workingdir, \
                                 output_file)
                        raise InvenioWebSubmitFileStamperError(msg)
                else:
                    ## Despite the fact that there was NOT only one page
                    ## in the original file, there was an error when trying
                    ## to merge it with the file that was stamped on the
                    ## first page. Fail.
                    msg = "Error: Unable to stamp file [%s/%s]. There " \
                          "was an error when attempting to merge the " \
                          "file containing the first page of the " \
                          "stamped file with the remaining pages of the " \
                          "original file. Stamping has failed." \
                          % (path_workingdir, subject_file)
                    raise InvenioWebSubmitFileStamperError(msg)
    elif not os.access("%s/%s" % (path_workingdir, output_file), os.F_OK):
        ## A final version of the stamped file was NOT created even though
        ## no error signal was encountered during the merging process.
        ## Fail.
        msg = "Error: Unable to stamp file [%s/%s]. When attempting to " \
              "merge the file containing the first page of the stamped " \
              "file with the remaining pages of the original file, no " \
              "final file was created.  Stamping has failed." \
              % (path_workingdir, subject_file)
        raise InvenioWebSubmitFileStamperError(msg)


def apply_stamp_all_pages(path_workingdir, \
                          stamp_file_name, \
                          subject_file, \
                          output_file, \
                          stamp_layer):
    """Carry out the stamping:
       This function adds a stamp to all pages of the file.
       @param path_workingdir: (string) - the path to the working directory
        that contains all of the files needed for the stamping process to be
        carried out.
       @param stamp_file_name: (string) - the name of the PDF stamp file (i.e.
        the stamp itself).
       @param subject_file: (string) - the name of the file to be stamped.
       @param output_file: (string) - the name of the final "stamped" file that
        will be written in the working directory after the function has ended.
       @param stamp_layer: (string) - the layer to consider when stamping
    """
    cmd_stamp_all_pages = \
             "%(pdftk)s %(file-to-stamp-path)s %(stamp_layer)s " \
             "%(stamp-file-path)s output " \
             "%(stamped-file-all-pages-path)s 2>/dev/null" \
             % { 'pdftk'                       : CFG_PATH_PDFTK,
                 'file-to-stamp-path'          : escape_shell_arg("%s/%s" % \
                                                  (path_workingdir, \
                                                   subject_file)),
                 'stamp-file-path'             : escape_shell_arg("%s/%s" % \
                                                  (path_workingdir, \
                                                   stamp_file_name)),
                 'stamped-file-all-pages-path' : escape_shell_arg("%s/%s" % \
                                                  (path_workingdir, \
                                                   output_file)),
                 'stamp_layer'             : stamp_layer == 'foreground' and 'stamp' or 'background'

               }
    errcode_stamp_all_pages = os.system(cmd_stamp_all_pages)
    if errcode_stamp_all_pages or \
           not os.access("%s/%s" % (path_workingdir, output_file), os.F_OK):
        ## There was a problem stamping the document. Fail.
        msg = "Error: Unable to stamp file [%s/%s]. Stamping has failed." \
              % (path_workingdir, subject_file)
        raise InvenioWebSubmitFileStamperError(msg)


def apply_stamp_to_file(path_workingdir,
                        stamp_type,
                        stamp_file_name,
                        subject_file,
                        output_file,
                        stamp_layer,
                        skip_metadata):
    """Given a stamp-file, the details of the type of stamp to apply, and the
       details of the file to be stamped, coordinate the process of having
       that stamp applied to the file.
       @param path_workingdir: (string) - the path to the working directory
        that contains all of the files needed for the stamping process to be
        carried out.
       @param stamp_type: (string) - the type of stamp to be applied to the
        file.
       @param stamp_file_name: (string) - the name of the PDF stamp file (i.e.
        the stamp itself).
       @param subject_file: (string) - the name of the file to be stamped.
       @param output_file: (string) - the name of the final "stamped" file that
        will be written in the working directory after the function has ended.
       @param stamp_layer: (string) - the layer to consider when stamping the file.
       @return: (string) - the name of the stamped file that has been created.
        It will be found in the stamping working directory.
    """
    ## Stamping is performed on PDF files. We therefore need to test for the
    ## type of the subject file before attempting to stamp it:
    ##
    ## Initialize a variable to hold the "file type" of the subject file:
    subject_filetype = ""

    ## Using the file command, test for the file-type of "subject_file":
    cmd_gfile = "%(gfile)s %(file-to-stamp-path)s 2> /dev/null" \
                % { 'gfile'              : CFG_PATH_GFILE,
                    'file-to-stamp-path' : escape_shell_arg("%s/%s" % \
                                                           (path_workingdir, \
                                                            subject_file)),
                  }
    ## Execute the file command:
    fh_gfile = os.popen(cmd_gfile, "r")
    ## Read the results string output by gfile:
    output_gfile = fh_gfile.read()
    ## Close the pipe and capture its error code:
    errcode_gfile = fh_gfile.close()

    ## If a result was obtained from gfile, scan it for an acceptable file-type:
    if errcode_gfile is None and output_gfile != "":
        output_gfile = output_gfile.lower()
        if "pdf document" in output_gfile:
            ## This is a PDF file.
            subject_filetype = "pdf"
        elif "postscript" in output_gfile:
            ## This is a PostScript file.
            subject_filetype = "ps"

    ## Unable to determine the file type using gfile.
    ## Try to determine the file type by examining its extension:
    if subject_filetype == "":
        ## split the name of the file to be stamped on "." and take the last
        ## part of it.  This should be the "extension", once cleaned from
        ## the possible "version" suffix (for eg. ';2' in "foo.pdf;2")
        tmp_file_extension = subject_file.split(".")[-1]
        tmp_file_extension = tmp_file_extension.split(';')[0]
        if tmp_file_extension.lower() == "pdf":
            subject_filetype = "pdf"
        elif tmp_file_extension.lower() == "ps":
            subject_filetype = "ps"

    if subject_filetype not in ("ps", "pdf"):
        ## unable to process file.
        msg = """Error: Input file [%s] is not PDF or PS. - unable to """ \
              """perform stamping.""" % subject_file
        raise InvenioWebSubmitFileStamperError(msg)

    if subject_filetype == "ps":
        ## Convert the subject file from PostScript to PDF:
        if subject_file[-3:].lower() == ".ps":
            ## The name of the file to be stamped has a PostScript extension.
            ## Strip it and give the name of the PDF file to be created a
            ## PDF extension:
            created_pdfname = "%s.pdf" % subject_file[:-3]
        elif len(subject_file.split(".")) > 1:
            ## The file name has an extension - strip it and add a PDF
            ## extension:
            raw_name = subject_file[:subject_file.rfind(".")]
            if raw_name != "":
                created_pdfname = "%s.pdf" % raw_name
            else:
                ## It would appear that the file had no extension and that its
                ## name started with a period. Just use the original name with
                ## a .pdf suffix:
                created_pdfname = "%s.pdf" % subject_file
        else:
            ## No extension - use the original name with a .pdf suffix:
            created_pdfname = "%s.pdf" % subject_file

        ## Build the distilling command:
        cmd_distill = """%(distiller)s %(ps-file-path)s """ \
                      """%(pdf-file-path)s 2>/dev/null""" % \
                      { 'distiller'     : CFG_PATH_PS2PDF,
                        'ps-file-path'  : escape_shell_arg("%s/%s" % \
                                                          (path_workingdir, \
                                                           subject_file)),
                        'pdf-file-path' : escape_shell_arg("%s/%s" % \
                                                          (path_workingdir, \
                                                           created_pdfname)),
                      }
        ## Distill the PS into a PDF:
        errcode_distill = os.system(cmd_distill)

        ## Test to see whether the PS was distilled into a PDF without error:
        if errcode_distill or \
           not os.access("%s/%s" % (path_workingdir, created_pdfname), os.F_OK):
            ## The PDF file was not correctly created in the working directory.
            ## Unable to continue with the stamping process.
            msg = "Error: Unable to correctly convert PostScript file [%s] to" \
                  " PDF. Cannot stamp file." % subject_file
            raise InvenioWebSubmitFileStamperError(msg)

        ## Now assign the name of the created PDF file to subject_file:
        subject_file = created_pdfname

    ## Treat the name of "output_file":
    if output_file in (None, ""):
        ## there is no value for outputfile. outfile should be given the same
        ## name as subject_file, but with "stamped-" appended to the front.
        ## E.g.: subject_file: test.pdf; outfile: stamped-test.pdf
        output_file = "stamped-%s" % subject_file
    else:
        ## If output_file has an extension, strip it and add a PDF extension:
        if len(output_file.split(".")) > 1:
            ## The file name has an extension - strip it and add a PDF
            ## extension:
            raw_name = output_file[:output_file.rfind(".")]
            if raw_name != "":
                output_file = "%s.pdf" % raw_name
            else:
                ## It would appear that the file had no extension and that its
                ## name started with a period. Just use the original name with
                ## a .pdf suffix:
                output_file = "%s.pdf" % output_file
        else:
            ## No extension - use the original name with a .pdf suffix:
            output_file = "%s.pdf" % output_file

    if not skip_metadata:
        ## Get the PDF file metadata
        # Metadata file name
        metadata_file = "metadata"
        # Get metadata command
        cmd_get_metadata = \
            "%(pdftk)s %(file-to-stamp-path)s dump_data output \
             %(metadata-file-path)s 2>/dev/null" % \
             { 'pdftk'              : CFG_PATH_PDFTK,
               'file-to-stamp-path' : escape_shell_arg("%s/%s" % \
                                                           (path_workingdir,
                                                            subject_file)),
               'metadata-file-path' : escape_shell_arg("%s/%s" % \
                                                           (path_workingdir,
                                                            metadata_file)), }
        # Get metadata errors
        err_get_metadata = os.system(cmd_get_metadata) or not \
                           os.access("%s/%s" % (path_workingdir, metadata_file),
                                     os.F_OK)

    if stamp_type == 'coverpage':
        ## The stamp to be applied to the document is in fact a "cover page".
        ## This means that the entire PDF "stamp" that was created from the
        ## LaTeX template is to be appended to the subject file as the first
        ## page (i.e. a cover-page).
        apply_stamp_cover_page(path_workingdir, \
                               stamp_file_name, \
                               subject_file, \
                               output_file)
    elif stamp_type == "first":
        apply_stamp_first_page(path_workingdir, \
                               stamp_file_name, \
                               subject_file, \
                               output_file, \
                               stamp_layer)
    elif stamp_type == 'all':
        ## The stamp to be applied to the document is a simple that that should
        ## be applied to ALL pages of the document (i.e. merged onto each page.)
        apply_stamp_all_pages(path_workingdir, \
                              stamp_file_name, \
                              subject_file, \
                              output_file, \
                              stamp_layer)
    else:
        ## Unexpcted stamping mode.
        msg = """Error: Unexpected stamping mode [%s]. Stamping has failed.""" \
              % stamp_type
        raise InvenioWebSubmitFileStamperError(msg)

    if not skip_metadata:
        ## Set the PDF file metadata
        # Were we able to get the metadata correctly in the first place?
        if not err_get_metadata:
            # Output file -with-metadata- name
            with_metadata_output_file = "with-metadata-" + output_file
            # Set metadata command
            cmd_set_metadata = \
                "%(pdftk)s %(stamped-file-path)s update_info \
                 %(metadata-file-path)s output \
                 %(with-metadata-stamped-file-path)s 2>/dev/null" % \
                 { 'pdftk'              : CFG_PATH_PDFTK,
                   'stamped-file-path'  : escape_shell_arg("%s/%s" % \
                                                            (path_workingdir,
                                                             output_file)),
                   'metadata-file-path' : escape_shell_arg("%s/%s" % \
                                                            (path_workingdir,
                                                             metadata_file)),
                   'with-metadata-stamped-file-path' : \
                        escape_shell_arg("%s/%s" % \
                                          (path_workingdir,
                                           with_metadata_output_file)), }
            # Set metadata errors
            err_set_metadata = os.system(cmd_set_metadata) or not \
                               os.access("%s/%s" % (path_workingdir,
                                                   with_metadata_output_file),
                                         os.F_OK)
            # Were we able to set the metadata correctly in the output file?
            if not err_set_metadata:
                without_metadata_output_file = "without-metadata-" + output_file
                try:
                    os.rename("%s/%s" % (path_workingdir, output_file),
                              "%s/%s" % (path_workingdir,
                                         without_metadata_output_file))
                except:
                    pass
                else:
                    try:
                        os.rename("%s/%s" % (path_workingdir,
                                             with_metadata_output_file),
                                  "%s/%s" % (path_workingdir, output_file))
                    except:
                        try:
                            os.rename("%s/%s" % (path_workingdir,
                                                 without_metadata_output_file),
                                      "%s/%s" % (path_workingdir, output_file))
                        except:
                            msg = "Error: Encoutered problems when renaming " + \
                                  "the output files after copying the PDF " + \
                                  "metadata"
                            raise InvenioWebSubmitFileStamperError(msg)

    ## Finally, if the original subject file was a PS, convert the stamped
    ## PDF back to PS:
    if subject_filetype == "ps":
        if output_file[-4:].lower() == ".pdf":
            ## The name of the file to be stamped has a PDF extension.
            ## Strip it and give the name of the PDF file to be created a
            ## PDF extension:
            stamped_psname = "%s.ps" % output_file[:-4]
        elif len(output_file.split(".")) > 1:
            ## The file name has an extension - strip it and add a PDF
            ## extension:
            raw_name = output_file[:output_file.rfind(".")]
            if raw_name != "":
                stamped_psname = "%s.ps" % raw_name
            else:
                ## It would appear that the file had no extension and that its
                ## name started with a period. Just use the original name with
                ## a .pdf suffix:
                stamped_psname = "%s.ps" % output_file
        else:
            ## No extension - use the original name with a .pdf suffix:
            stamped_psname = "%s.ps" % output_file

        ## Build the conversion command:
        cmd_pdf2ps = "%s %s %s 2>/dev/null" % (CFG_PATH_PDF2PS,
                                               escape_shell_arg("%s/%s" % \
                                                     (path_workingdir, \
                                                      output_file)),
                                               escape_shell_arg("%s/%s" % \
                                                     (path_workingdir, \
                                                      stamped_psname)))
        errcode_pdf2ps = os.system(cmd_pdf2ps)
        ## Check to see that the command executed OK:
        if not errcode_pdf2ps and \
           os.access("%s/%s" % (path_workingdir, stamped_psname), os.F_OK):
            ## No problem converting the PDF to PS.
            output_file = stamped_psname
    ## Return the name of the "stamped" file:
    return output_file


def copy_subject_file_to_working_directory(path_workingdir, input_file):
    """Attempt to copy the subject file (that which is to be stamped) to the
       current working directory, returning the name of the subject file if
       successful.
       @param path_workingdir: (string) - the path to the working directory
        for the current stamping session.
       @param input_file: (string) - the path to the subject file (that which
        is to be stamped).
       @return: (string) - the name of the subject file, which has been copied
        to the current working directory.
       @Exceptions raised: (InvenioWebSubmitFileStamperError) - upon failure
        to successfully copy the subject file to the working directory.
    """
    ## Divide the input filename into path and basename:
    (dummy, name_input_file) = os.path.split(input_file)
    if name_input_file == "":
        ## The input file is just a path - not a valid filename. Fail.
        msg = """Error: unable to determine the name of the file to be """ \
              """stamped."""
        raise InvenioWebSubmitFileStamperError(msg)

    ## Test to see whether the stamping subject file is a real file and
    ## is readable:
    if os.access("%s" % input_file, os.R_OK):
        ## File is readable. Copy it locally to the working directory:
        try:
            shutil.copyfile("%s" % input_file, \
                            "%s/%s" % (path_workingdir, name_input_file))
        except IOError:
            ## Unable to copy the stamping subject file to the
            ## working directory. Fail.
            msg = """Error: Unable to copy stamping file [%s] to """ \
                  """working directory for stamping [%s].""" \
                  % (input_file, path_workingdir)
            raise InvenioWebSubmitFileStamperError(msg)
    else:
        ## Unable to read the subject file. Fail.
        msg = """Error: Unable to copy stamping file [%s] to """ \
              """working directory [%s]. (File not readable.)""" \
              % (input_file, path_workingdir)
        raise InvenioWebSubmitFileStamperError(msg)

    ## Now that the stamping file has been successfully copied to the working
    ## directory, return its base name:
    return name_input_file

def create_working_directory():
    """Create a "working directory" in which the files related to the stamping
       process can be stored, and return the full path to it.
       The working directory will be created in ~invenio/var/tmp.
       If it cannot be created there, an exception
       (InvenioWebSubmitFileStamperError) will be raised.
       The working directory will have the prefix
       "websubmit_file_stamper_", and could be given a name something like:
                 - websubmit_file_stamper_Tzs3St
       @return: (string) - the full path to the working directory.
       @Exceptions raised: InvenioWebSubmitFileStamperError.
    """
    ## Create the temporary directory in which to place the LaTeX template
    ## and its helper files in ~invenio/var/tmp:
    path_workingdir = None
    try:
        path_workingdir = tempfile.mkdtemp(prefix="websubmit_file_stamper_", \
                                           dir="%s" % CFG_TMPDIR)
    except OSError as err:
        ## Unable to create the temporary directory in ~invenio/var/tmp
        msg = "Error: Unable to create a temporary working directory in " \
              "which to carry out the stamping process. An attempt was made " \
              "to create the directory in [%s]; the error encountered was " \
              "<%s>. Stamping has failed." % (CFG_TMPDIR, str(err))
        raise InvenioWebSubmitFileStamperError(msg)
    ## return the path to the working-directory:
    return path_workingdir


# ***** Functions Specific to CLI calling of the program: *****

def usage(wmsg="", err_code=0):
    """Print a "usage" message (along with an optional additional warning/error
       message) to stderr and exit with a given error code.
       @param wmsg: (string) - some kind of warning message for the user.
       @param err_code: (integer) - an error code to be passed to sys.exit,
        which is called after the usage message has been printed.
       @return: None.
    """
    ## Wash the warning message:
    if wmsg != "":
        wmsg = wmsg.strip() + "\n"

    ## The usage message:
    msg = """  Usage:
                 python ~invenio/lib/python/invenio/websubmit_file_stamper.py \\
                           [options] input-file.pdf

  websubmit_file_stamper.py  is used to add a "stamp" to a PDF file.
  A LaTeX template is used to create the stamp and this stamp is then
  concatenated with the original PDF file.
  The stamp can take the form of either a separate "cover page" that is
  appended to the document; or a "mark" that is applied somewhere either
  on the document's first page or on all of its pages.

  Options:
   -h, --help                Print this help.
   -V, --version             Print version information.
   -v, --verbose=LEVEL       Verbose level (0=min, 1=default, 9=max).
                              [NOT IMPLEMENTED]
   -t, --latex-template=PATH
                             Path to the LaTeX template file that should be used
                             for the creation of the PDF stamp. (Note, if it's
                             just a basename, it will be sought first in the
                             current working directory, and then in the invenio
                             file-stamper templates directory; If there is a
                             qualifying path to the template name, it will be
                             sought only in that location);
   -c, --latex-template-var='VARNAME=VALUE'
                             A variable that should be replaced in the LaTeX
                             template file with its corresponding value. Of the
                             following format:
                                 VARNAME=VALUE
                             This option is repeatable - one for each template
                             variable;
   -s, --stamp=STAMP-TYPE
                             The type of stamp to be applied to the subject
                             file. Must be one of 3 values:
                              + "first" - stamp only the first page;
                              + "all"   - stamp all pages;
                              + "coverpage" - add a cover page to the
                                document;
                             The default value is "first";
   -l, --layer=LAYER
                             The position of the stamp. Should be one of:
                              + "background" (invisible if original file has
                                a white -not transparent- background layer)
                              + "foreground" (on top of the stamped file.
                                If the stamp does not have a transparent
                                background, will hide all of the document
                                layers)
                             The default value is "background"
   -o, --output-file=XYZ
                             The optional name to be given to the finished
                             (stamped) file IN THE WORKING DIRECTORY
                             (Specify a file name, including
                             extension, not a path). If this is
                             omitted, the stamped file will be given
                             the same name as the input file, but will
                             be prefixed by"stamped-";
   --skip-metadata
                             Do not copy the PDF metadata of the input file
                             to the output (stamped) file.
                             If not specified, the PDF metadata will be
                             copied by default.

  Example:
    python ~invenio/lib/python/invenio/websubmit_file_stamper.py \\
              --latex-template=demo-stamp-left.tex \\
              --latex-template-var='REPORTNUMBER=TEST-THESIS-2008-019' \\
              --latex-template-var='DATE=27/02/2008' \\
              --stamp='first' \\
              --layer='background' \\
              --output-file=testfile_stamped.pdf \\
              testfile.pdf
"""
    sys.stderr.write(wmsg + msg)
    sys.exit(err_code)


def get_cli_options():
    """From the options and arguments supplied by the user via the CLI,
       build a dictionary of options to drive websubmit-file-stamper.
       For reference, the CLI options available to the user are as follows:

         -h, --help                 -> Display help/usage message and exit;
         -V, --version              -> Display version information and exit;
         -v, --verbose=             -> Set verbosity level (0=min, 1=default,
                                       9=max).
         -t, --latex-template=      -> Path to the LaTeX template file that
                                       should be used for the creation of the
                                       PDF stamp. (Note, if it's just a
                                       basename, it will be sought first in the
                                       current working directory, and then in
                                       the invenio file-stamper templates
                                       directory; If there is a qualifying
                                       path to the template name, it will be
                                       sought only in that location);
         -c, --latex-template-var=  -> A variable that should be
                                       replaced in the LaTeX template file
                                       with its corresponding value. Of the
                                       following format:
                                           varname=value
                                       This option is repeatable - one for each
                                       template variable;
         -s, --stamp=                  The type of stamp to be applied to the
                                       subject file. Must be one of 3 values:
                                        + "first" - stamp only the first page;
                                        + "all"   - stamp all pages;
                                        + "coverpage" - add a cover page to the
                                          document;
                                       The default value is "first";
         -l, --layer=               -> The position of the stamp. Should be one
                                       of:
                                        + "background" (invisible if original
                                          file has a white -not transparent-
                                          background layer)
                                        + "foreground" (on top of the stamped
                                          file. If the stamp does not have a
                                          transparent background, will hide all
                                          of the document layers).
                                        The default value is "background"
         -o, --output-file=         -> The optional name to be given to the
                                       finished (stamped) file IN THE
                                       WORKING DIRECTORY (Specify a
                                       name, not a path). If this is
                                       omitted, the stamped file will
                                       be given the same name as the
                                       input file, but will be
                                       prefixed by"stamped-";
         --skip-metadata            -> Do not copy the PDF metadata of the
                                       input file to the output (stamped)
                                       file. If not specified, the metadata
                                       will be copied by default.

       @return: (dictionary) of input options and flags, set as
        appropriate. The dictionary has the following structure:
           + latex-template: (string) - the path to the LaTeX template to be
              used for the creation of the stamp itself;
           + latex-template-var: (dictionary) - This dictionary contains
              variables that should be sought in the LaTeX template file, and
              the values that should be substituted in their place. E.g.:
                    { "TITLE" : "An Introduction to Invenio" }
           + input-file: (string) - the path to the input file (i.e. that
              which is to be stamped;
           + output-file: (string) - the name of the stamped file that should
              be created by the program. This is optional - if not provided,
              a default name will be applied to a file instead;
           + stamp: (string) - the type of stamp that is to be applied to the
              input file. It must take one of 3 values:
                    - "first": Stamp only the first page of the document;
                    - "all": Apply the stamp to all pages of the document;
                    - "coverpage": Add a "cover page" to the document;
           + layer: (string) - the position of the stamp in the layers of the
              file. Will be one of the following values:
                    - "background": stamp applied to the background layer;
                    - "foreground": stamp applied to the foreground layer;
           + verbosity: (integer) - the verbosity level under which the program
              is to run;
           + skip-metadata: (boolean) - whether to skip copying the metadata
              or not;
        So, an example of the returned dictionary would be something like:
              { 'latex-template'      : "demo-stamp-left.tex",
                'latex-template-var'  : { "REPORTNUMBER" : "TEST-2008-001",
                                          "DATE"         : "15/02/2008",
                                        },
                'input-file'          : "test-doc.pdf",
                'output-file'         : "",
                'stamp'               : "first",
                'layer'               : "background",
                'verbosity'           : 0,
                'skip-metadata'       : False,
              }
    """
    ## dictionary of important values relating to cli call of program:
    options = { 'latex-template'     : "",
                'latex-template-var' : {},
                'input-file'         : "",
                'output-file'        : "",
                'stamp'              : "first",
                'layer'              : "background",
                'verbosity'          : 0,
                'skip-metadata'      : False,
              }

    ## Get the options and arguments provided by the user via the CLI:
    try:
        myoptions, myargs = getopt.getopt(sys.argv[1:], "hVv:t:c:s:l:o:", \
                                          ["help",
                                           "version",
                                           "verbosity=",
                                           "latex-template=",
                                           "latex-template-var=",
                                           "stamp=",
                                           "layer=",
                                           "output-file=",
                                           "skip-metadata"])
    except getopt.GetoptError as err:
        ## Invalid option provided - usage message
        usage(wmsg="Error: %(msg)s." % { 'msg' : str(err) })

    ## Get the input file from the arguments list (it should be the
    ## first argument):
    if len(myargs) > 0:
        options["input-file"] = myargs[0]

    ## Extract the details of the options:
    for opt in myoptions:
        if opt[0] in ("-V","--version"):
            ## version message and exit
            sys.stdout.write("%s\n" % __revision__)
            sys.stdout.flush()
            sys.exit(0)
        elif opt[0] in ("-h","--help"):
            ## help message and exit
            usage()
        elif opt[0] in ("-v", "--verbosity"):
            ## Get verbosity level:
            if not opt[1].isdigit():
                options['verbosity'] = 0
            elif int(opt[1]) not in xrange(0, 10):
                options['verbosity'] = 0
            else:
                options['verbosity'] = int(opt[1])
        elif opt[0] in ("-o", "--output-file"):
            ## Get the name of the "output file" that is to be created after
            ## stamping (i.e. the "stamped file"):
            options["output-file"] = opt[1]
            if '/' in options["output-file"]:
                # probably user specified a file path, which is not
                # supported
                print("Warning: you seem to have specifed a path for option '--output-file'.")
                print("Only a file name can be specified. Stamping might fail.")
        elif opt[0] in ("-t", "--latex-template"):
            ## Get the path to the latex template to be used for the creation
            ## of the stamp file:
            options["latex-template"] = opt[1]
        elif opt[0] in ("-m", "--stamp"):
            ## The type of stamp that is to be applied to the document:
            ## Options are coverpage, first, all:
            if str(opt[1].lower()) in ("coverpage", "first", "all"):
                ## Valid stamp type, accept it;
                options["stamp"] = str(opt[1]).lower()
            else:
                ## Invalid stamp type. Print usage message and quit.
                usage(wmsg="Chosen stamp type '%s' is not valid" % opt[1])
        elif opt[0] in ("-l", "--layer"):
            ## The layer to consider for the stamp
            if str(opt[1].lower()) in ("background", "foreground"):
                ## Valid layer type, accept it;
                options["layer"] = str(opt[1]).lower()
            else:
                ## Invalid layer type. Print usage message and quit.
                usage(wmsg="Chosen layer type '%s' is not valid" % opt[1])
        elif opt[0] in ("-c", "--latex-template-var"):
            ## This is a variable to be replaced in the LaTeX template.
            ## It should take the following form:
            ##    varname=value
            ## We can therefore split it on the first "=" sign - anything to
            ## left will be considered to be the name of the variable to search
            ## for; anything to the right will be considered as the value that
            ## should replace the variable in the LaTeX template.
            ## Note: If the user supplies the same variable name more than once,
            ## the latter occurrence will be kept and the previous value will be
            ## overwritten.
            ## Note also that if the variable string does not take the
            ## expected format a=b, it will be ignored.
            ##
            ## Get the complete string:
            varstring = str(opt[1])
            ## Split into 2 string based on the first "=":
            split_varstring = varstring.split("=", 1)
            if len(split_varstring) == 2:
                ## Split based on equals sign was successful:
                if split_varstring[0] != "":
                    ## The variable name was not empty - keep it:
                    options["latex-template-var"]["%s" % split_varstring[0]] = \
                        "%s" % split_varstring[1]
        elif opt[0] in ("--skip-metadata"):
            options["skip-metadata"] = True

    ## Return the input options:
    return options


def stamp_file(options):
    """The driver for the stamping process. This is effectively the function
       that is responsible for coordinating the stamping of a file.
       @param options: (dictionary) - a dictionary of options that are required
        by the function in order to carry out the stamping process.

        The dictionary must have the following structure:
           + latex-template: (string) - the path to the LaTeX template to be
              used for the creation of the stamp itself;
           + latex-template-var: (dictionary) - This dictionary contains
              variables that should be sought in the LaTeX template file, and
              the values that should be substituted in their place. E.g.:
                    { "TITLE" : "An Introduction to Invenio" }
           + input-file: (string) - the path to the input file (i.e. that
              which is to be stamped;
           + output-file: (string) - the name of the stamped file that
              should be created by the program IN THE WORKING
              DIRECTORY (Specify a name, not a path).
              This is optional - if not provided, a default name will
              be applied to a file instead;
           + stamp: (string) - the type of stamp that is to be applied to the
              input file. It must take one of 3 values:
                    - "first": Stamp only the first page of the document;
                    - "all": Apply the stamp to all pages of the document;
                    - "coverpage": Add a "cover page" to the document;
           + layer: (string) - the layer to consider to stamp the file. Can be
              one of the following values:
                    - "background": stamp the background layer;
                    - "foreground": stamp the foreground layer;
           + verbosity: (integer) - the verbosity level under which the program
              is to run;
           + skip-metadata: (boolean) - whether to skip copying the metadata
              or not;
        So, an example of the returned dictionary would be something like:
              { 'latex-template'      : "demo-stamp-left.tex",
                'latex-template-var'  : { "REPORTNUMBER" : "TEST-2008-001",
                                          "DATE"         : "15/02/2008",
                                        },
                'input-file'          : "test-doc.pdf",
                'output-file'         : "",
                'stamp'               : "first",
                'layer'               : "background"
                'verbosity'           : 0,
                'skip-metadata'       : False,
              }

       @return: (tuple) - consisting of two strings:
          1. the path to the working directory in which all stamping-related
              files are stored;
          2. The name of the "stamped" file;
       @Exceptions raised: (InvenioWebSubmitFileStamperError) exceptions may
        be raised or propagated by this function when the stamping process
        fails for one reason or another.
    """
    ## SANITY CHECKS:
    ## Does the options dictionary contain all mandatory keys?
    ##
    ## A list of the names of the expected options:
    mandatory_option_names = ["latex-template", \
                              "latex-template-var", \
                              "input-file", \
                              "output-file"]
    optional_option_names_and_defaults = {"layer"         : "background",
                                          "verbosity"     : 0,
                                          "stamp"         : "first",
                                          "skip-metadata" : False}

    ## Are we missing some mandatory parameters?
    received_option_names = options.keys()
    for mandatory_option_name in mandatory_option_names:
        if not mandatory_option_name in received_option_names:
            msg = """Error: Mandatory parameter %s is missing""" % mandatory_option_name
            raise InvenioWebSubmitFileStamperError(msg)

    ## Are we getting some unknown option?
    for received_option_name in received_option_names:
        if not received_option_name in mandatory_option_names and \
           not received_option_name in optional_option_names_and_defaults.keys():
            ## Error: the dictionary of options had an illegal structure:
            msg = """Error: Option %s is not a recognized parameter""" % received_option_name
            raise InvenioWebSubmitFileStamperError(msg)

    ## Set default options when not specified
    for opt, value in iteritems(optional_option_names_and_defaults):
        if opt not in options:
            options[opt] = value

    ## Do we have an input file to work on?
    if options["input-file"] in (None, ""):
        ## No input file - stop the stamping:
        msg = "Error: unable to determine the name of the file to be stamped."
        raise InvenioWebSubmitFileStamperError(msg)

    ## Do we have a LaTeX file for creation of the stamp?
    if options["latex-template"] in (None, ""):
        ## No latex stamp file - stop the stamping:
        msg = "Error: unable to determine the name of the LaTeX template " \
              "file to be used for stamp creation."
        raise InvenioWebSubmitFileStamperError(msg)

    ## OK - begin the document stamping process:
    ##
    ## Get the output file:
    (dummy, name_outfile) = os.path.split(options["output-file"])
    if name_outfile != "":
        ## Take just the basename component of outfile:
        options["output-file"] = name_outfile

    ## Create a working directory (in which to store the various files used and
    ## created during the stamping process) and get the full path to it:
    path_workingdir = create_working_directory()

    ## Copy the file to be stamped into the working directory:
    basename_input_file = \
            copy_subject_file_to_working_directory(path_workingdir, \
                                                   options["input-file"])

    ## Now import the LaTeX (and associated) files into a temporary directory
    ## and use them to create the "stamp" PDF:
    pdf_stamp_name = create_pdf_stamp(path_workingdir, \
                                      options["latex-template"], \
                                      options["latex-template-var"])

    ## Everything is now ready to merge the "stamping subject" file with the
    ## PDF "stamp" file that has been created:
    name_stamped_file = apply_stamp_to_file(path_workingdir, \
                                            options["stamp"], \
                                            pdf_stamp_name, \
                                            basename_input_file, \
                                            options["output-file"], \
                                            options["layer"], \
                                            options["skip-metadata"])

    ## Return a tuple containing the working directory and the name of the
    ## stamped file to the caller:
    return (path_workingdir, name_stamped_file)



def stamp_file_cli():
    """The function responsible for triggering the stamping process when called
       via the CLI.
       This function will effectively get the CLI options, then pass them to
       function that is responsible for coordinating the stamping process
       itself.
       Once stamping has been completed, an attempt will be made to copy the
       stamped file to the current working directory.
    """
    ## Get CLI options and arguments:
    input_options = get_cli_options()

    ## Stamp the file and obtain the working directory in which the stamped file
    ## is situated and the name of the stamped file:
    try:
        (working_dir, stamped_file) = stamp_file(input_options)
    except InvenioWebSubmitFileStamperError as err:
        ## Something went wrong:
        sys.stderr.write("Stamping failed: [%s]\n" % str(err))
        sys.stderr.flush()
        sys.exit(1)

    if not os.access("./%s" % stamped_file, os.F_OK):
        ## Copy the stamped file into the current directory:
        try:
            shutil.copyfile("%s/%s" % (working_dir, stamped_file), \
                            "./%s" % stamped_file)
        except IOError:
            ## Report that it wasn't possible to copy the stamped file locally
            ## and offer the user a path to it:
            msg = "It was not possible to copy the stamped file to the " \
                  "current working directory.\nYou can find it here: " \
                  "[%s/%s].\n" \
                  % (working_dir, stamped_file)
            sys.stderr.write(msg)
            sys.stderr.flush()
    else:
        ## A file exists in curdir with the same name as the final stamped file.
        ## just print out a message stating this fact, along with the path to
        ## the stamped file in the temporary working directory:
        msg = "The stamped file [%s] has not been copied to the current " \
              "working directory because a file with this name already " \
              "existed there.\nYou can find the stamped file here: " \
              "[%s/%s].\n" % (stamped_file, working_dir, stamped_file)
        sys.stderr.write(msg)
        sys.stderr.flush()


# Start proceedings for CLI calls:
if __name__ == "__main__":
    stamp_file_cli()
