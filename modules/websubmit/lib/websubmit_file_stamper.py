# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""This is the main body of stamp_file. This tool is used to create a stamped
   version of a PDF file.

   Python API: please see perform_request_stamping().

   CLI API:
    $ python ./websubmit_file_stamper.py -t foo.text
                                         -r BAR,baq
"""

__revision__ = "$Id$"


import getopt, sys, re, os, time, shutil
from invenio.config import CFG_PATH_DISTILLER

## from invenio.config import tmpdir
tmpdir = "/home/invenio/var/tmp"
## from invenio.config import etcdir
etcdir = "/home/invenio/etc"

CFG_WEBSUBMIT_LATEX_TEMPLATES_DIR = "%s/websubmit/latex" % etcdir
CFG_PATH_PDFTK = "pdftk"
CFG_PDF_TO_PS = "/usr/bin/pdf2ps"
CFG_PATH_GFILE = "/usr/bin/file"




class InvenioStampFileError(Exception):
    """This exception should be raised when an error is encoutered that
       prevents a file from being stamped.
       When caught, this exception should be used to stop processing with a
       failure signal.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - a string to write to the log.
        """
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)



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
    ## splitting, this one splits on any colon (:) that is not escaped by a
    ## backslash.
    final_dictionary = {}
    for key_value_string in key_vals:
        ## Split the pair apart, based on ":":
        key_value_pair = re.split(r'(?<!\\):', key_value_string)
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


def copy_template_files_to_stampdir(path_workingdir, tpl_name):
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
       @param tpl_name: (string) - the name of the LaTeX template to copy
        to the working dir.
    """
    ## Get the "base name" of the latex template:
    (template_path, template_name) = os.path.split(tpl_name)
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
                raise InvenioStampFileError(msg)
        else:
            ## Unable to read the template file:
            msg = """Error: Unable to copy LaTeX file [%s/%s] to """ \
                  """working directory for stamping [%s]. (File not """ \
                  """readable.)""" \
                  % (template_path, template_name, path_workingdir)
            raise InvenioStampFileError(msg)
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
                raise InvenioStampFileError(msg)
        elif os.access("%s/%s" % (CFG_WEBSUBMIT_LATEX_TEMPLATES_DIR, \
                                  template_name), os.F_OK):
            ## The template has been found in WebSubmit's latex templates
            ## directory. Copy it locally to the stamping working directory:
            try:
                shutil.copyfile("%s/%s" % (CFG_WEBSUBMIT_LATEX_TEMPLATES_DIR, \
                                           template_name), \
                                "%s/%s" % (path_workingdir, template_name))
            except IOError:
                ## Unable to copy the LaTeX template file to the
                ## working stamping directory:
                msg = """Error: Unable to copy LaTeX file [%s/%s] to """ \
                      """working directory for stamping [%s].""" \
                      % (CFG_WEBSUBMIT_LATEX_TEMPLATES_DIR, \
                         template_name, path_workingdir)
                raise InvenioStampFileError(msg)
            else:
                ## Now that the template has been found, set the "template
                ## path" to the WebSubmit latex templates directory:
                template_path = CFG_WEBSUBMIT_LATEX_TEMPLATES_DIR
        else:
            ## Unable to locate the latex template.
            msg = """Error: Unable to locate LaTeX file [%s].""" % template_name
            raise InvenioStampFileError(msg)

    ## Now that the LaTeX template file has been copied locally, extract
    ## the names of graphics files to be included in the resulting
    ## document and attempt to copy them to the working "stamp" directory:
    cmd_findgraphics = \
       """grep includegraphic %s/%s | """ \
       """sed -n 's/^[^{]*{\\([^}]\\{1,\\}\\)}.*$/\\1/p'""" \
       % (path_workingdir, template_name)

    fh_findgraphics = os.popen(cmd_findgraphics, "r")
    graphic_names = fh_findgraphics.readlines()
    findgraphics_errcode = fh_findgraphics.close()

    if findgraphics_errcode is not None:
        ## There was an error involving the grep/sed command.
        ## Unable to extract the details of any graphics to
        ## be included:
        msg = """Unable to stamp file. There was """ \
              """a problem when trying to obtain details of images """ \
              """included by the LaTeX template."""
        raise InvenioStampFileError(msg)

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
                        raise InvenioStampFileError(msg)
                else:
                    msg = """Unable to locate an image [%s/%s] included""" \
                          """ by the LaTeX template file [%s].""" \
                          % (graphic_path, graphic_name, template_name)
                    raise InvenioStampFileError(msg)
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
                            raise InvenioStampFileError(msg)
                    else:
                        msg = """Unable to locate an image [%s] included""" \
                              """ by the LaTeX template file [%s].""" \
                              % (graphic_name, template_name)
                        raise InvenioStampFileError(msg)
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
                            raise InvenioStampFileError(msg)
                    else:
                        msg = """Unable to locate an image [%s] included""" \
                              """ by the LaTeX template file [%s].""" \
                              % (graphic_name, template_name)
                        raise InvenioStampFileError(msg)
    ## Return the basename of the template so that it can be used to create
    ## the PDF stamp file:
    return template_name


def create_final_latex_template(working_dirname, \
                                template_name, \
                                tpl_replacements):
    """In the working directory, create a copy of the the orginal
       latex template with all the possible xxx--xxx in the template
       replaced with the values identified by the keywords in the
       tpl_replacements dictionary.
       @param working_dirname: (string) the working directory used for the
        creation of the PDF stamp file.
       @latex_template: (string) name of the latex template before it has
        been parsed for replacements.
       @tpl_replacements: (dict) dictionnary whose keys are the string to
        replace in latex_template and values are the replacement content
       @return name of the final latex template (after replacements)
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
                       % (working_dirname, template_name), "r")
        ## Open a file to contain the "parsed" latex template:
        fpwrite = open("%s/create%s" \
                       % (working_dirname, template_name), "w")
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
                    replacement_term = tpl_replacements[search_term]
                    ## Is the replacement term of the form date(XXXX)? If yes,
                    ## take it literally and generate a pythonic date with it:
                    if replacement_term.find("date(") == 0 \
                           and replacement_term[-1] == ")":
                        ## Take the date format string, use it to
                        ## generate today's date
                        date_format = replacement_term[5:-1].strip('\'"')
                        try:
                            replacement = time.strftime(date_format, time.localtime())
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
                except KeyError:
                    ## This search-term was not in the list of replacements
                    ## to be made. It should be replaced with an empty string
                    ## in the template:
                    line = line[0:replacement_marker.start()] + \
                           line[replacement_marker.end():]
            ## Write the modified line to the new template:
            fpwrite.write(line)
            fpwrite.flush()
        ## Close up the template files and unlink the original:
        fpread.close()
        fpwrite.close()
#        os.unlink("%s/%s" % (working_dirname, template_name))
    except IOError:
        msg = "Unable to read LaTeX template [%s/%s]. Cannot Stamp File" \
              % (working_dirname, template_name)
        raise InvenioStampFileError(msg)

    ## Return the name of the LaTeX template to be used:
    return "create%s" % template_name


def create_pdf_stamp(path_workingdir, tpl_replacements, latex_template):
    """Retrieve the LaTeX (and associated) files and use them to create a
       PDF "Stamp" file that can be merged with the main file.
       The PDF stamp is created in a temporary working directory.
       @param path_workingdir: (string) the path to the working directory
        that should be used for creating the PDF stamp file.
       @param tpl_replacements: (dictionary) - key-value pairs of strings
        to be sought and replaced within the latex template.
       @param latex_template: (string) - the name of the latex template
        to be used for the creation of the stamp.
       @return: (string) - the name of the PDF stamp file.
    """
    ## Copy the LaTeX (and helper) files should be copied into the working dir:
    template_name = copy_template_files_to_stampdir(path_workingdir, \
                                                    latex_template)

    ## Now that the latex template and its helper files have been retrieved,
    ## the Stamp PDF can be created.
    final_template = create_final_latex_template(path_workingdir, \
                                                 template_name, \
                                                 tpl_replacements)

    ## Now, build the Stamp PDF from the LaTeX template:
    cmd_latex = """cd %(workingdir)s; /usr/bin/pdflatex """ \
                """-interaction=batchmode """ \
                """%(workingdir)s/%(latex-template)s > /dev/null 2>&1""" \
                % { 'workingdir'         : path_workingdir,
                    'latex-template'     : final_template,
                  }
    ## Log the latex command
    os.system("""echo '%s' > latex_cmd""" % cmd_latex)
    ## Run the latex command
    error_latex = os.system(cmd_latex)
    
    if error_latex != 0:
        ## there was a problem creating the PDF from the LaTeX template
        msg = """Error: Unable to create stamp file for document"""
        raise InvenioStampFileError(msg)

    ## Return the name of the PDF stamp file:
    pdf_stamp_name = "%s.pdf" % os.path.splitext(final_template)[0]
    return pdf_stamp_name


def merge_stamp_with_subject_file(stamping_mode,
                                  working_dir,
                                  stamp_file,
                                  subject_file,
                                  output_file):
    ## Stamping is performed on PDF files. We therefore need to test for the
    ## type of the subject file before attempting to stamp it:
    ##
    ## Initialize a variable to hold the "file type" of the subject file:
    subject_filetype = ""

    ## Using the file command, test for the file-type of "subject_file":
    gfile_cmd = "%(gfile)s %(working-dir)s/%(file-to-stamp)s 2> /dev/null" \
                % { 'gfile'         : CFG_PATH_GFILE,
                    'working-dir'   : working_dir,
                    'file-to-stamp' : subject_file,
                  }
    ## Execute the file command:
    fh_gfilepipe = os.popen(gfile_cmd, "r")
    ## Read the results string output by gfile:
    output_gfile = fh_gfilepipe.read()
    ## Close the pipe and capture its error code:
    errcode_gfile = fh_gfilepipe.close()

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
        ## part of it.  This should be the "extension".
        tmp_file_extension = subject_file.split(".")[-1]
        if tmp_file_extension.lower() == "pdf":
            subject_filetype = "pdf"
        elif tmp_file_extension.lower() == "ps":
            subject_filetype = "ps"

    if subject_filetype not in ("ps", "pdf"):
        ## unable to process file.
        msg = """Error: Input file [%s] is not PDF or PS. - unable to """ \
              """perform stamping.""" % subject_file
        raise InvenioStampFileError(msg)

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
        distill_cmd = """%(distiller)s %(working-dir)s/%(ps-file)s """ \
                      """%(working-dir)s/%(pdf-file)s 2>/dev/null""" % \
                      { 'distiller' : CFG_PATH_DISTILLER, \
                        'working-dir' : working_dir,
                        'ps-file' : subject_file,
                        'pdf-file' : created_pdfname,
                      }
        ## Distill the PS into a PDF:
        fh_distill = os.popen(distill_cmd, "r")
        errcode_distill = fh_distill.close()

        ## Test to see whether the PS was distilled into a PDF without error:
        if errcode_distill is not None or \
           not os.access("%s/%s" % (working_dir, created_pdfname), os.F_OK):
            ## The PDF file was not correctly created in the working directory.
            ## Unable to continue with the stamping process.
            msg = "Error: Unable to correctly convert PostScript file [%s] to" \
                  " PDF. Cannot stamp file." % subject_file
            raise InvenioStampFileError(msg)
        
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

    if stamping_mode == 'cover-page':
        ## The stamp to be applied to the document is in fact a "cover page".
        ## This means that the entire PDF "stamp" that was created from the
        ## LaTeX template is to be appended to the subject file as the first
        ## page (i.e. a cover-page).

        ## Build the stamping command:
        stamp_cmd = """%(pdftk)s %(working-dir)s/%(cover-page)s """ \
                    """%(working-dir)s/%(file-to-stamp)s """ \
                    """cat output %(working-dir)s/%(stamped-file)s """ \
                    """2>/dev/null"""% \
                      { 'pdftk'         : CFG_PATH_PDFTK,
                        'working-dir'   : working_dir,
                        'cover-page'    : stamp_file,
                        'file-to-stamp' : subject_file,
                        'stamped-file'  : output_file,
                      }
        ## Execute the stamping command:
        fh_stamp = os.popen(stamp_cmd, "r")
        errcode_stamping = fh_stamp.close()

        ## Was the PDF merged with the coverpage without error?
        if errcode_stamping is not None:
            ## There was a problem:
            msg = "Error: Could not merge cover page [%s] with stamp file " \
                  "[%s]. Stamping failed." % (stamp_file, subject_file)
            raise InvenioStampFileError(msg)            
    elif stamping_mode == 'stamp':
        ## The stamp to be applied to the document is a simple stamp
        ## that is to be merged with the FIRST PAGE of the full-text
        ## PDF document.

        ## First create a backgroung using the stamp file on
        ## every page of the original file.
        ## The name of a temporary file with a stamp on every page:
        output_file_bg = "background-%s" % output_file

        ## The following command is used to apply the stamp as a background
        ## mark to every page of the subject file:
        stamp_cmd_stamp_allpages = \
                 "%(pdftk)s %(working-dir)s/%(file-to-stamp)s background " \
                 "%(working-dir)s/%(stamp-file)s output " \
                 "%(working-dir)s/%(stamped-file-all-pages)s 2>/dev/null" \
                 % { 'pdftk'                  : CFG_PATH_PDFTK,
                     'working-dir'            : working_dir,
                     'stamp-file'             : stamp_file,
                     'file-to-stamp'          : subject_file,
                     'stamped-file-all-pages' : output_file_bg,
                   }
        fh_stampall = os.popen(stamp_cmd_stamp_allpages, "r")
        errcode_stampall = fh_stampall.close()
        if errcode_stampall is not None or \
               not os.access("%s/%s" % (working_dir, output_file_bg), os.F_OK):
            ## There was a problem adding the stamp.
            msg = "Error: Could not apply stamp [%s] to the subject file " \
                  "[%s]. Stamping failed." % (stamp_file, subject_file)
            raise InvenioStampFileError(msg)
        ## Now take the first page from the file that was stamped, and merge
        ## that with the 2nd page onwards of the original PDF subject file.
        ## This will give a PDF file that is stamped on the first page:
        ## selected the first page of the stamped document and
        ## concatenate with the original one without the first page 
        ## -NB: pdftk doesn't allow to redirect the output to an input
        ## file so here we need to create a temporary document
        ## -If the original document contains only one page the
        ## temporary document is not created
        stamp_cmd_keep_stamp_only_on_first_page = \
                 "%(pdftk)s A=%(working-dir)s/%(stamped-file-all-pages)s  " \
                 "B=%(working-dir)s/%(original-file)s cat A1 B2-end output " \
                 "%(working-dir)s/%(stamped-file)s 2>/dev/null" \
                 % { 'pdftk' : CFG_PATH_PDFTK,
                     'working-dir' : working_dir,
                     'stamped-file-all-pages' : output_file_bg,
                     'original-file' : subject_file,
                     'stamped-file'  : output_file,
                   }
        fh_keep_stamp_only_on_first_page = \
                       os.popen(stamp_cmd_keep_stamp_only_on_first_page, "r")
        fh_keep_stamp_only_on_first_page.close()
        ## NOTE: We don't check for an error in the command's execution because
        ## if the original file only had one page, trying to concatenate it with
        ## the stamped version, from page 2 onwards will cause an error.
        ##
        ## So, was a final version of stamped_file created?
        if not os.access("%s/%s" % (working_dir, output_file), os.F_OK):
            ## The fact that there is no final version of the file tells us
            ## that the PDF was probably only 1 page long. We therefore
            ## rename the version that was stamped on "all" pages to the
            ## output_file filename:
            try:
                shutil.move("%s/%s" % (working_dir, output_file_bg),  \
                            "%s/%s" % (working_dir, output_file))
            except IOError:
                ## Oops - unable to rename the file to the final file.
                ## Stamping has failed.
                msg = "Error: Could not rename temporary stamped file [%s] to" \
                      " final stamped file [%s]. Stamping failed." \
                      % (output_file_bg, output_file)
                raise InvenioStampFileError(msg)
    else:
        ## Unexpcted stamping mode.
        msg = """Error: Unexpected stamping mode [%s] - cannot stamp file.""" \
              % stamping_mode
        raise InvenioStampFileError(msg)

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
        cmd_pdf2ps = "%s %s/%s %s/%s 2>/dev/null" % (CFG_PDF_TO_PS,
                                                     working_dir,
                                                     output_file,
                                                     working_dir,
                                                     stamped_psname)
        fh_pdf2ps = os.popen(cmd_pdf2ps, "r")
        errcode_pdf2ps = fh_pdf2ps.close()
        ## Check to see that the command executed OK:
        if errcode_pdf2ps is None and \
           os.access("%s/%s" % (working_dir, stamped_psname), os.F_OK):
            ## No problem converting the PDF to PS.
            output_file = stamped_psname
    ## Return the name of the "stamped" file:
    return output_file




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
    msg = """  Usage: stampfile [options] input-file.pdf [output-file.pdf]

  stampfile is used to add a "stamp" to a PDF file.
  A LaTeX template is used to create the stamp and this stamp is then
  concatenated with the original PDF file.
  The stamp can take the form of either a separate "cover page" that is
  appended to the document; or a "mark" that is applied somewhere on the
  document's first page.

  Options:
   -h, --help             print this help
   -V, --version          print version information
   -v, --verbose          verbosity level (##NOT IMPLEMENTED##)
   -t, --latex-template   The path to the LaTeX template that should be used
                          for the stamping.
   -m, --stamp-mode       The stamping mode. Must be either "cover-page" or
                          "stamp".  Will default to "cover-page".
   -r, --tpl-replacements A quoted string of quoted key-value pairs. The "key"
                          components will be sought in the template file and
                          replaced with the "value" strings. Pairs should be
                          separated by commas and should a comma be present in
                          value, it must be escaped (e.g. \\,).
                          Note: the entire string should be enclosed within
                          single quotes.

  Example: stampfile --latex-template=/home/foo/cern-stamp.tex \\
            --stamp-mode=stamp \\
            --tpl_replacements='"REPORTNUMBER":"DEMOTEST-ARTICLE-2008-001","DATE":"20 January 2008"' \\
            testfile.pdf

  The resulting stamped file will be written to a file called
  testfile-STAMPED.pdf.

"""
    sys.stderr.write(wmsg + msg)
    sys.exit(err_code)


## def get_names_of_stamping_subject_files(filenames):
##     """From a list of filenames, extract the path to the "input file" (that
##        which is to be stamped), and the output file (the name that the
##        stamped file is to be given.)
##        @param filenames: (list) - contains the paths/names of the files to
##         be worked with.
##        @return: tuple - the path to the input file and the name of the output
##         file (None if no output file was provided.)
##     """
##     ## Take the names of the input and output files:
##     try:
##         ## Get the name of the input file (that which is to be stamped):
##         path_infile = filenames[0]
##     except IndexError:
##         ## Oops, no input file name provided.
##         msg = """Error: unable to determine the name of the file to be stamped."""
##         raise InvenioStampFileError(msg)
##     ## If the name of an output file was specified, remove any leading path and 
##     try:
##         ## Get the name of the output file:
##         path_outfile = filenames[1]
##     except IndexError:
##         ## No output filename given.
##         name_outfile = None
##     else:
##         ## We only want to have the name of the output file, not a path to it.
##         (path_outfile, name_outfile) = os.path.split(path_outfile)
##         if name_outfile == "":
##             ## out_filepath was a pat, not a filename:
##             name_outfile = None

##     ## Return the names of the input and output files:
##     return (path_infile, name_outfile)

def copy_stampingfile_to_working_directory(path_workingdir, infile):
    (dummy, name_infile) = os.path.split(infile)
    if name_infile == "":
        ## Error: infile is just a path.
        msg = """Error: unable to determine the name of the file to be """ \
              """stamped."""
        raise InvenioStampFileError(msg)

    ## Test to see whether the stamping subject file is a real file and
    ## is readable:
    if os.access("%s" % infile, os.R_OK):
        ## File is readable. Copy it locally to the working directory:
        try:
            shutil.copyfile("%s" % infile, \
                            "%s/%s" % (path_workingdir, name_infile))
        except IOError:
            ## Unable to copy the stamping subject file to the
            ## working directory:
            msg = """Error: Unable to copy stamping file [%s] to """ \
                  """working directory for stamping [%s].""" \
                  % (infile, path_workingdir)
            raise InvenioStampFileError(msg)
    else:
        ## Unable to read the template file:
        msg = """Error: Unable to copy stamping file [%s] to """ \
              """working directory [%s]. (File not readable.)""" \
              % (infile, path_workingdir)
        raise InvenioStampFileError(msg)

    ## Now that the stamping file has been successfully copied to the working
    ## directory, return its base name:
    return name_infile

def create_working_directory(working_dirname):
    """Create the stamping "working directory" from a given directory name
       and return its full path.
       The working directory will be created in ~invenio/var/tmp or failing
       this, /tmp. If it cannot be created in either of these locations,
       an exception (InvenioStampFileError) will be raised.
       @param working_dirname: (string) - the name to be given to the
        working directory used in this stamping session.
       @return: (string) - the full path to the working directory.
       @Exceptions raised: InvenioStampFileError.
    """
    ## Create the temporary directory in which to place the LaTeX template
    ## and its helper files.
    ## Try first in ~invenio/var/tmp:
    path_workingdir = None
    try:
        os.mkdir("%s/%s" % (tmpdir, working_dirname))
    except OSError:
        ## Unable to create the temporary directory in ~invenio/var/tmp
        pass
    else:
        ## record the full path to the working directory:
        path_workingdir = "%s/%s" % (tmpdir, working_dirname)

    ## Now if it wasn't possible to create the working directory in
    ## ~invenio/var/tmp, try to create it in /tmp:
    if path_workingdir is None:
        try:
            os.mkdir("/tmp/%s" % working_dirname)
        except OSError:
            ## Unable to create the temporary directory in /tmp
            pass
        else:
            ## record the full path to the working directory:
            path_workingdir = "/tmp/%s" % working_dirname

    ## If it wasn't possible to create the temporary directory in /tmp,
    ## fail and exit.
    if path_workingdir is None:
        msg = """Error: Unable to create working directory [%] in either [%s] """ \
              """or [/tmp]. Cannot stamp file.""" % (working_dirname, tmpdir)
        raise InvenioStampFileError(msg)

    ## return the path to the working-directory:
    return path_workingdir




def get_cli_options():
    """Get the various arguments and options from the command line and populate
       a dictionary of cli_options.
       @return: (dictionary) of input options and flags, set as
        appropriate. The input options (dictionary keys) are:
         latex_template: The path to the latex template to be used for stamping;
         input_file: The file to be stamped;
         output_file: The name of the "stamped" file that is to be created;
         stamping_mode: either "cover-page" or "stamp" - effectively the
          type of stamp to be applied to the document;
         tpl_replacements: a set of key-value items, effectively search strings
          to be replaced in the latex template, and the values with which they
          should be replaced. This allows the stamp to contain custom strings;
         verbosity: an integer representing verbosity level;
    """
    ## dictionary of important values relating to cli call of program:
    options = { 'latex_template'   : "",
                'input_file'       : "",
                'output_file'      : "",
                'stamping_mode'    : "cover-page",
                'tpl_replacements' : "",
                'verbosity'        : 0,
              }

    ## Get the options and arguments provided by the user via the CLI:
    try:
        myoptions, myargs = getopt.getopt(sys.argv[1:], "hVv:t:m:r:o:", \
                                          ["help",
                                           "version",
                                           "verbose=",
                                           "latex-template=",
                                           "stamp-mode=",
                                           "latex-template-vars=",
                                           "output-file="])
    except getopt.GetoptError, err:
        ## Invalid option provided - usage message
        usage(wmsg="Error: %(msg)s." % { 'msg' : str(err) })

    ## Get the input file from the arguments list (it should be the
    ## first argument):
    if len(myargs) > 0:
        options["input_file"] = myargs[0]

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
        elif opt[0] in ("-v", "--verbose"):
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
            options["output_file"] = opt[1]
        elif opt[0] in ("-t", "--latex-template"):
            ## Get the path to the latex template:
            options["latex_template"] = opt[1]
        elif opt[0] in ("-m", "--stamp-mode"):
            ## Get the stamping mode to be used:
            if str(opt[1].lower()) in ("cover-page", "stamp"):
                ## if the user supplied the string cover-page or stamp,
                ## accept it.
                options["stamping_mode"] = str(opt[1]).lower()
            else:
                ## An illegal value was supplied for stamp-mode. Print the usage
                ## message and quit.
                usage()
        elif opt[0] in ("-r", "--tpl-replacements"):
            ## The user has provided a string of replacement strings that
            ## should be substituted for their values in the latex template.
            options["tpl_replacements"] = opt[1]

    ## Return the input options:
    return options


def perform_request_stamping(latex_template="",
                             input_file="",
                             output_file="",
                             tpl_replacements="",
                             stamping_mode="cover-page",
                             verbosity=0):
    """
    """
    ## SANITY CHECKS:
    ## Do we have an input file to work on?
    if input_file in (None, ""):
        ## No input file - stop the stamping:
        msg = "Error: unable to determine the name of the file to be stamped."
        raise InvenioStampFileError(msg)
    ## Do we have a LaTeX file for creation of the stamp?
    if latex_template in (None, ""):
        ## No latex stamp file - stop the stamping:
        msg = "Error: unable to determine the name of the LaTeX template " \
              "file to be used for stamp creation."
        raise InvenioStampFileError(msg)

    ## Get the output file:
    (path_outfile, name_outfile) = os.path.split(output_file)
    if name_outfile != "":
        ## Take just the basename component of outfile:
        output_file = name_outfile

    ## From the PID and the current timestamp, create the name of a temporary
    ## directory in which to store the latex/PDF files for stamping.
    current_time = time.strftime("%Y%m%d%H%M%S")
    my_pid = "%s" % os.getpid()
    current_timestamp = "%f" % time.time()
    working_dirname = "%s_stampfile_%s_%s" % (current_time,
                                              my_pid,
                                              current_timestamp)

    ## From the string passed via the "--tpl-replacements" option, get a
    ## dictionary of keywords/values to be replaced in the stamping template:
    replacements = get_dictionary_from_string(tpl_replacements)

    ## Create the working directory and get the full path to it:
    path_workingdir = create_working_directory(working_dirname)

    ## Copy the file to be stamped into the working directory:
    basename_infile = \
            copy_stampingfile_to_working_directory(path_workingdir, input_file)

    ## Now import the LaTeX (and associated) files into a temporary directory
    ## and use them to create the "stamp" PDF:
    pdf_stamp_name = \
            create_pdf_stamp(path_workingdir, replacements, latex_template)

    ## Everything is now ready to merge the "stamping subject" file with the
    ## PDF "stamp" file that has been created:
    name_stamped_file = merge_stamp_with_subject_file(stamping_mode, \
                                                      path_workingdir, \
                                                      pdf_stamp_name, \
                                                      basename_infile, \
                                                      output_file)

    ## Return a tuple containing the working directory and the name of the
    ## stamped file to the caller:
    return (path_workingdir, name_stamped_file)
    


def main():
    """Main function.
    """
    ## Get CLI options and arguments:
    input_options = get_cli_options()

    ## Stamp the file and obtain the working directory in which the stamped file
    ## is situated and the name of the stamped file:
    try:
        (working_dir, stamped_file) = \
           perform_request_stamping(latex_template=\
                                     input_options["latex_template"],
                                    input_file=\
                                     input_options["input_file"],
                                    output_file=\
                                     input_options["output_file"],
                                    tpl_replacements=\
                                     input_options["tpl_replacements"],
                                    stamping_mode=\
                                     input_options["stamping_mode"],
                                    verbosity=\
                                     input_options["verbosity"])
    except InvenioStampFileError, err:
        ## Oops. Something went wrong:
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
            msg = "It was not possible to copy the stamped file to the current " \
                  "working directory.\nYou can find it here: [%s/%s].\n" \
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


## Start proceedings for CLI calls:
if __name__ == "__main__":
    main()
