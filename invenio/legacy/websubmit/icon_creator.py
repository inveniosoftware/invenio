# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012 CERN.
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

"""This is websubmit_icon_creator.py
   This tool is used to create an icon of a picture file.

   + Python API:
      Please see create_icon().

   + CLI API:

#     $ python ~invenio/lib/python/invenio/websubmit_icon_creator.py \\
#               --icon-scale=200 \\
#               --icon-name=test-icon \\
#               --icon-file-format=jpg \\
#               test-image.jpg

#     $ python ~invenio/lib/python/invenio/websubmit_icon_creator.py \\
#               --icon-scale=200 \\
#               --icon-name=test-icon2 \\
#               --icon-file-format=gif \\
#               --multipage-icon \\
#               --multipage-icon-delay=50 \\
#               test-image2.pdf
"""

__revision__ = "$Id$"

import os.path, sys, getopt, shutil, tempfile, re
from invenio.config import \
     CFG_TMPDIR, \
     CFG_PATH_PS2PDF, \
     CFG_PATH_PDFTK, \
     CFG_PATH_CONVERT
from invenio.utils.shell import escape_shell_arg
from invenio.legacy.websubmit.config import InvenioWebSubmitIconCreatorError

CFG_ALLOWED_FILE_EXTENSIONS = ["pdf", "gif", "jpg", \
                               "jpeg", "ps", "png", "bmp", \
                               "eps", "epsi", "epsf", \
                               "tiff", "tif"]


# ***** Functions related to the icon creation process: *****

# Accepted format for the ImageMagick 'scale' parameter:
re_imagemagic_scale_parameter_format = re.compile(r'x?\d+(x\d*)?(^|!|>|<|@|%)?$')

def create_working_directory():
    """Create a "working directory" in which the files related to the icon-
       creation process can be stored, and return the full path to it.
       The working directory will be created in ~invenio/var/tmp.
       If it cannot be created there, an exception
       (InvenioWebSubmitIconCreatorError) will be raised.
       The working directory will have the prefix
       "websubmit_icon_creator_", and could be given a name something like:
                 - websubmit_icon_creator_Tzs3St
       @return: (string) - the full path to the working directory.
       @Exceptions raised: InvenioWebSubmitIconCreatorError.
    """
    ## Create the temporary directory in which to place the files related to
    ## icon creation in ~invenio/var/tmp:
    path_workingdir = None
    try:
        path_workingdir = tempfile.mkdtemp(prefix="websubmit_icon_creator_", \
                                           dir="%s" % CFG_TMPDIR)
    except OSError as err:
        ## Unable to create the temporary directory in ~invenio/var/tmp
        msg = "Error: Unable to create a temporary working directory in " \
              "which to carry out the icon creation process. An attempt was " \
              "made to create the directory in [%s]; the error encountered " \
              "was <%s>. Icon creation has failed." % (CFG_TMPDIR, str(err))
        raise InvenioWebSubmitIconCreatorError(msg)
    ## return the path to the working-directory:
    return path_workingdir


def copy_file_to_directory(source_file, destination_dir):
    """Attempt to copy an ordinary file from one location to a destination
       directory, returning the name of the copied file if successful.
       @param source_file: (string) - the name of the file to be copied
        to the destination directory.
       @param destination_dir: (string) - the path of the directory into
        which the source file is to be copied.
       @return: (string) - the name of the source file after it has been
        copied to the destination directory (i.e. no leading path information.)
       @Exceptions raised: (IOError) - upon failure to successfully copy the
        source file to the destination directory.
    """
    ## Divide the input filename into path and basename:
    (dummy, name_source_file) = os.path.split(source_file)
    if name_source_file == "":
        ## The source file is just a path - not a valid filename.
        msg = """Error: the name of the file to be copied was invalid."""
        raise IOError(msg)

    ## Test to see whether source file is a real file and is readable:
    if os.access("%s" % source_file, os.R_OK):
        ## File is readable. Copy it locally to the destination directory:
        try:
            shutil.copyfile("%s" % source_file, \
                            "%s/%s" % (destination_dir, name_source_file))
        except IOError:
            ## Unable to copy the source file to the destination directory.
            msg = """Error: Unable to copy source file [%s] to """ \
                  """the destination directory [%s].""" \
                  % (source_file, destination_dir)
            raise IOError(msg)
    else:
        ## Unable to read the source file.
        msg = """Error: Unable to copy source file [%s] to """ \
              """destination directory [%s]. (File not readable.)""" \
              % (source_file, destination_dir)
        raise IOError(msg)

    ## Now that the source file has been successfully copied to the destination
    ## directory, return its base name:
    return name_source_file


def build_icon(path_workingdir,
               source_filename,
               source_filetype,
               icon_name,
               icon_filetype,
               multipage_icon,
               multipage_icon_delay,
               icon_scale):
    """Whereas create_icon acts as the API for icon creation and therefore
       deals with argument washing, temporary working directory creation,
       etc, the build_icon function takes care of the actual creation of the
       icon file itself by calling various shell tools.
       To accomplish this, it relies upon the following parameters:
       @param path_workingdir: (string) - the path to the working directory
        in which all files related to the icon creation are stored.
       @param source_filename: (string) - the filename of the original image
        file.
       @param source_filetype: (string) - the file type of the original image
        file.
       @param icon_name: (string) - the name that is to be given to the icon.
       @param icon_filetype: (string) - the file type of the icon that is
        to be created.
       @param multipage_icon: (boolean) - a flag indicating whether or not
        an icon with multiple pages (i.e. an animated gif icon) should be
        created.
       @param multipage_icon_delay: (integer) - the delay to be used between
        frame changing for an icon with multiple pages (i.e. an animated gif.)
       @param icon_scale: (integer) - the scaling information for the created
        icon.
       @return: (string) - the name of the created icon file (which will have
        been created in the working directory "path_workingdir".)
       @Exceptions raised: (InvenioWebSubmitIconCreatorError) - raised when
        the icon creation process fails.
    """
    ##
    ## If the source file is a PS, convert it into a PDF:
    if source_filetype == "ps":
        ## Convert the subject file from PostScript to PDF:
        if source_filename[-3:].lower() == ".ps":
            ## The name of the file to be stamped has a PostScript extension.
            ## Strip it and give the name of the PDF file to be created a
            ## PDF extension:
            created_pdfname = "%s.pdf" % source_filename[:-3]
        elif len(source_filename.split(".")) > 1:
            ## The file name has an extension - strip it and add a PDF
            ## extension:
            raw_name = source_filename[:source_filename.rfind(".")]
            if raw_name != "":
                created_pdfname = "%s.pdf" % raw_name
            else:
                ## It would appear that the file had no extension and that its
                ## name started with a period. Just use the original name with
                ## a .pdf suffix:
                created_pdfname = "%s.pdf" % source_filename
        else:
            ## No extension - use the original name with a .pdf suffix:
            created_pdfname = "%s.pdf" % source_filename

        ## Build the distilling command:
        cmd_distill = """%(distiller)s %(ps-file-path)s """ \
                      """%(pdf-file-path)s 2>/dev/null""" % \
                      { 'distiller'     : CFG_PATH_PS2PDF,
                        'ps-file-path'  : escape_shell_arg("%s/%s" % \
                                                          (path_workingdir, \
                                                           source_filename)),
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
            ## Unable to continue.
            msg = "Error: Unable to correctly convert PostScript file [%s] to" \
                  " PDF. Cannot create icon." % source_filename
            raise InvenioWebSubmitIconCreatorError(msg)

        ## Now assign the name of the created PDF file to subject_file:
        source_filename = created_pdfname

    ##
    ## Treat the name of the icon:
    if icon_name in (None, ""):
        ## Since no name has been provided for the icon, give it the same name
        ## as the source file, but with the prefix "icon-":
        icon_name = "icon-%s" % source_filename
    ## Now if the icon name has an extension, strip it and add that of the
    ## icon file type:
    if len(icon_name.split(".")) > 1:
        ## The icon file name has an extension - strip it and add the icon
        ## file type extension:
        raw_name = icon_name[:icon_name.rfind(".")]
        if raw_name != "":
            icon_name = "%s.%s" % (raw_name, icon_filetype)
        else:
            ## It would appear that the file had no extension and that its
            ## name started with a period. Just use the original name with
            ## the icon file type's suffix:
            icon_name = "%s.%s" % (icon_name, icon_filetype)
    else:
        ## The icon name had no extension. Use the original name with the
        ## icon file type's suffix:
        icon_name = "%s.%s" % (icon_name, icon_filetype)

    ##
    ## If the source file type is PS or PDF, it may be necessary to separate
    ## the first page from the rest of the document and keep it for use as
    ## the icon. Do this if necessary:
    if source_filetype in ("ps", "pdf") and \
           (icon_filetype != "gif" or not multipage_icon):
        ## Either (a) the icon type isn't GIF (in which case it cannot
        ## be animated and must therefore be created _only_ from the
        ## document's first page; or (b) the icon type is GIF, but the
        ## icon is to be created from the first page of the document only.
        ## The first page of the PDF document must be separated and is to
        ## be used for icon creation:
        source_file_first_page = "p1-%s" % source_filename
        ## Perform the separation:
        cmd_get_first_page = \
             "%(pdftk)s A=%(source-file-path)s " \
             "cat A1 output %(first-page-path)s " \
             "2>/dev/null" \
             % { 'pdftk'            : CFG_PATH_PDFTK,
                 'source-file-path' : escape_shell_arg("%s/%s" % \
                                           (path_workingdir, source_filename)),
                 'first-page-path'  : escape_shell_arg("%s/%s" % \
                                           (path_workingdir, \
                                            source_file_first_page)),
               }
        errcode_get_first_page = os.system(cmd_get_first_page)
        ## Check that the separation was successful:
        if errcode_get_first_page or \
               not os.access("%s/%s" % (path_workingdir, \
                                        source_file_first_page), os.F_OK):
            ## Separation was unsuccessful.
            msg = "Error: Unable to create an icon for file [%s/%s] - it " \
                  "wasn't possible to separate the first page from the " \
                  "rest of the document (error code [%s].)" \
                  % (path_workingdir, source_filename, errcode_get_first_page)
            raise InvenioWebSubmitIconCreatorError(msg)
        else:
            ## Successfully extracted the first page. Treat it as the source
            ## file for icon creation from now on:
            source_filename = source_file_first_page

    ##
    ## Create the icon:
    ## If a delay is necessary for an animated gif icon, create the
    ## delay string:
    delay_info = ""
    if source_filetype in ("ps", "pdf") and \
           icon_filetype == "gif" and multipage_icon:
        ## Include delay information:
        delay_info = "-delay %s" % escape_shell_arg(str(multipage_icon_delay))

    ## Command for icon creation:
    cmd_create_icon = "%(convert)s -colorspace rgb -auto-orient -scale %(scale)s %(delay)s " \
                      "%(source-file-path)s %(icon-file-path)s 2>/dev/null" \
                      % { 'convert'          : CFG_PATH_CONVERT,
                          'scale'            : \
                                             escape_shell_arg(icon_scale),
                          'delay'            : delay_info,
                          'source-file-path' : \
                                      escape_shell_arg("%s/%s" \
                                                      % (path_workingdir, \
                                                         source_filename)),
                          'icon-file-path'   : \
                                      escape_shell_arg("%s/%s" \
                                                      % (path_workingdir, \
                                                         icon_name)),
                        }
    errcode_create_icon = os.system(cmd_create_icon)
    ## Check that the icon creation was successful:
    if errcode_create_icon or \
           not os.access("%s/%s" % (path_workingdir, icon_name), os.F_OK):
        ## Icon creation was unsuccessful.
        msg = "Error: Unable to create an icon for file [%s/%s] (error " \
              "code [%s].)" \
              % (path_workingdir, source_filename, errcode_create_icon)
        raise InvenioWebSubmitIconCreatorError(msg)

    ##
    ## The icon was successfully created. Return its name:
    return icon_name


def create_icon(options):
    """The driver for the icon creation process. This is effectively the
       function that is responsible for coordinating the icon creation.
       It is the API for the creation of an icon.
       @param options: (dictionary) - a dictionary of options that are required
        by the function in order to carry out the icon-creation process.

        The dictionary must have the following structure:
           + input-file: (string) - the path to the input file (i.e. that
              which is to be stamped;
           + icon-name: (string) - the name of the icon that is to be created
              by the program. This is optional - if not provided,
              a default name will be applied to the icon file instead;
           + multipage-icon: (boolean) - used only when the original file
              is a PDF or PS file. If False, the created icon will feature ONLY
              the first page of the PDF. If True, ALL pages of the PDF will
              be included in the created icon. Note: If the icon type is not
              gif, this flag will be forced as False.
           + multipage-icon-delay: (integer) - used only when the original
              file is a PDF or PS AND use-first-page-only is False AND
              the icon type is gif.
              This allows the user to specify the delay between "pages"
              of a multi-page (animated) icon.
           + icon-scale: ('geometry') - the scaling information to be used for the
              creation of the new icon. Type 'geometry' as defined in ImageMagick.
              (eg. 320 or 320x240 or 100> or 5%)
           + icon-file-format: (string) - the file format of the icon that is
              to be created. Legal values are:
              * pdf
              * gif
              * jpg
              * jpeg
              * ps
              * png
              * bmp
           + verbosity: (integer) - the verbosity level under which the program
              is to run;
        So, an example of the returned dictionary could be something like:
              { 'input-file'           : "demo-picture-file.jpg",
                'icon-name'            : "icon-demo-picture-file",
                'icon-file-format'     : "gif",
                'multipage-icon'       : True,
                'multipage-icon-delay' : 100,
                'icon-scale'           : 180,
                'verbosity'            : 0,
              }
       @return: (tuple) - consisting of two strings:
          1. the path to the working directory in which all files related to
              icon creation are stored;
          2. The name of the "icon" file;
       @Exceptions raised: (InvenioWebSubmitIconCreatorError)
        be raised or propagated by this function when the icon creation process
        fails for one reason or another.
    """
    ## SANITY CHECKS:
    ## Does the options dictionary contain all expected keys?
    ##
    ## A list of the names of the expected options:
    expected_option_names = ['input-file', \
                             'icon-name', \
                             'icon-file-format', \
                             'multipage-icon', \
                             'multipage-icon-delay', \
                             'icon-scale', \
                             'verbosity']
    expected_option_names.sort()
    ## A list of the option names that have been received:
    received_option_names = options.keys()
    received_option_names.sort()

    if expected_option_names != received_option_names:
        ## Error: he dictionary of options had an illegal structure:
        msg = """Error: Unexpected value received for "options" parameter."""
        raise InvenioWebSubmitIconCreatorError(msg)

    ## Do we have an input file to work on?
    if options["input-file"] in (None, ""):
        ## No input file - stop the icon creation:
        msg = "Error: unable to determine the name of the file from which " \
              "the icon is to be created."
        raise InvenioWebSubmitIconCreatorError(msg)
    else:
        ## Get the file type of the input file:
        tmp_file_extension = options["input-file"].split(".")[-1]
        ## allow also Invenio files that use the format: filename.ext;format;subformat;version
        tmp_file_extension = tmp_file_extension.split(';')[0]
        if tmp_file_extension.lower() not in CFG_ALLOWED_FILE_EXTENSIONS:
            ## Ilegal input file type.
            msg = "Error: icons can be only be created from %s files, " \
                  "not [%s]." % (str(CFG_ALLOWED_FILE_EXTENSIONS), \
                                 tmp_file_extension.lower())
            raise InvenioWebSubmitIconCreatorError(msg)
        else:
            subject_filetype = tmp_file_extension.lower()

    ## Wash the requested icon name:
    if type(options["icon-name"]) is not str:
        options["icon-name"] = ""
    else:
        (dummy, name_iconfile) = os.path.split(options["icon-name"])
        if name_iconfile != "":
            ## Take just the basename component of the icon file:
            options["icon-name"] = name_iconfile

    ## Do we have an icon file format?
    icon_format = options["icon-file-format"]
    if icon_format in (None, ""):
        ## gif by default:
        options["icon-file-format"] = "gif"
    elif str(icon_format).lower() not in CFG_ALLOWED_FILE_EXTENSIONS:
        ## gif if an invalid icon type was supplied:
        options["icon-file-format"] = "gif"
    else:
        ## Use the provided icon type:
        options["icon-file-format"] = icon_format.lower()

    ## Wash the use-first-page-only flag according to the type of the
    ## requested icon:
    if options["icon-file-format"] != "gif":
        ## Since the request icon isn't a gif file, it can't be animated
        ## and should be created from the first "page" of the original file:
        options["multipage-icon"] = False
    else:
        ## The requested icon is a gif. Verify that the multipage-icon
        ## flag is a boolean value. If not, set it to False by default:
        if type(options["multipage-icon"]) is not bool:
            ## Non-boolean value: default to False:
            options["multipage-icon"] = False

    ## Wash the delay time for frames in an animated gif icon:
    if type(options["multipage-icon-delay"]) is not int:
        ## Invalid value - set it to default:
        options["multipage-icon-delay"] = 100
    elif options["multipage-icon-delay"] < 0:
        ## Can't have negative delays:
        options["multipage-icon-delay"] = 100

    ## Wash the icon scaling information:
    if not re_imagemagic_scale_parameter_format.match(options["icon-scale"]):
        ## Ivalid value - set it to default:
        options["icon-scale"] = "180"

    ## OK. Begin the icon creation process:
    ##
    ## Create a working directory for the icon creation process and get the
    ## full path to it:
    path_workingdir = create_working_directory()

    ## Copy the file from which the icon is to be created into the
    ## working directory:
    try:
        basename_source_file = \
                copy_file_to_directory(options["input-file"], path_workingdir)
    except IOError as err:
        ## Unable to copy the source file to the working directory.
        msg = "Icon creation failed: unable to copy the source image file " \
              "to the working directory. Got this error: [%s]" % str(err)
        raise InvenioWebSubmitIconCreatorError(msg)

    ## Create the icon and get its name:
    icon_name = build_icon(path_workingdir, \
                           basename_source_file, \
                           subject_filetype, \
                           options["icon-name"], \
                           options["icon-file-format"], \
                           options["multipage-icon"], \
                           options["multipage-icon-delay"], \
                           options["icon-scale"])
    ## Return a tuple containing the working directory and the name of the
    ## icon file to the caller:
    return (path_workingdir, icon_name)



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
                 python ~invenio/lib/python/invenio/websubmit_icon_creator.py \\
                           [options] input-file.jpg

  websubmit_icon_creator.py is used to create an icon for an image.

  Options:
   -h, --help                      Print this help.
   -V, --version                   Print version information.
   -v, --verbose=LEVEL             Verbose level (0=min, 1=default, 9=max).
                                    [NOT IMPLEMENTED]
   -s, --icon-scale
                                   Scaling information for the icon that is to
                                   be created. Must be an integer. Defaults to
                                   180.
   -m, --multipage-icon
                                   A flag to indicate that the icon should
                                   consist of multiple pages. Will only be
                                   respected if the requested icon type is GIF
                                   and the input file is a PS or PDF consisting
                                   of several pages.
   -d, --multipage-icon-delay=VAL
                                   If the icon consists of several pages and is
                                   an animated GIF, a delay between frames can
                                   be specified. Must be an integer. Defaults
                                   to 100.
   -f, --icon-file-format=FORMAT
                                   The file format of the icon to be created.
                                   Must be one of:
                                       [pdf, gif, jpg, jpeg, ps, png, bmp]
                                   Defaults to gif.
   -o, --icon-name=XYZ
                                   The optional name to be given to the created
                                   icon file. If this is omitted, the icon file
                                   will be given the same name as the input
                                   file, but will be prefixed by "icon-";

  Examples:
    python ~invenio/lib/python/invenio/websubmit_icon_creator.py \\
              --icon-scale=200 \\
              --icon-name=test-icon \\
              --icon-file-format=jpg \\
              test-image.jpg

    python ~invenio/lib/python/invenio/websubmit_icon_creator.py \\
              --icon-scale=200 \\
              --icon-name=test-icon2 \\
              --icon-file-format=gif \\
              --multipage-icon \\
              --multipage-icon-delay=50 \\
              test-image2.pdf
"""
    sys.stderr.write(wmsg + msg)
    sys.exit(err_code)


def get_cli_options():
    """From the options and arguments supplied by the user via the CLI,
       build a dictionary of options to drive websubmit-icon-creator.
       For reference, the CLI options available to the user are as follows:

         -h, --help                  -> Display help/usage message and exit;
         -V, --version               -> Display version information and exit;
         -v, --verbose=              -> Set verbosity level (0=min, 1=default,
                                        9=max).
         -s, --icon-scale            -> Scaling information for the icon that
                                        is to be created. Must be of
                                        type 'geometry', as understood
                                        by ImageMagick (Eg. 320 or
                                        320x240 or 100>). Defaults to
                                        180.
         -m, --multipage-icon        -> A flag to indicate that the icon should
                                        consist of multiple pages. Will only be
                                        respected if the requested icon type is
                                        GIF and the input file is a PS or PDF
                                        consisting of several pages.
         -d, --multipage-icon-delay= -> If the icon consists of several pages
                                        and is an animated GIF, a delay between
                                        frames can be specified. Must be an
                                        integer. Defaults to 100.
         -f, --icon-file-format=     -> The file format of the icon to be
                                        created. Must be one of:
                                         [pdf, gif, jpg, jpeg, ps, png, bmp]
                                        Defaults to gif.
         -o, --icon-name=            -> The optional name to be given to the
                                        created icon file. If this is omitted,
                                        the icon file will be given the same
                                        name as the input file, but will be
                                        prefixed by "icon-";

       @return: (dictionary) of input options and flags, set as
        appropriate. The dictionary has the following structure:
           + input-file: (string) - the path to the input file (i.e. that
              which is to be stamped;
           + icon-name: (string) - the name of the icon that is to be created
              by the program. This is optional - if not provided,
              a default name will be applied to the icon file instead;
           + multipage-icon: (boolean) - used only when the original file
              is a PDF or PS file. If False, the created icon will feature ONLY
              the first page of the PDF. If True, ALL pages of the PDF will
              be included in the created icon. Note: If the icon type is not
              gif, this flag will be forced as False.
           + multipage-icon-delay: (integer) - used only when the original
              file is a PDF or PS AND use-first-page-only is False AND
              the icon type is gif.
              This allows the user to specify the delay between "pages"
              of a multi-page (animated) icon.
           + icon-scale: (integer) - the scaling information to be used for the
              creation of the new icon.
           + icon-file-format: (string) - the file format of the icon that is
              to be created. Legal values are:
                  [pdf, gif, jpg, jpeg, ps, png, bmp]
           + verbosity: (integer) - the verbosity level under which the program
              is to run;
        So, an example of the returned dictionary could be something like:
              { 'input-file'           : "demo-picture-file.jpg",
                'icon-name'            : "icon-demo-picture-file",
                'icon-file-format'     : "gif",
                'multipage-icon'       : True,
                'multipage-icon-delay' : 100,
                'icon-scale'           : 180,
                'verbosity'            : 0,
              }
    """
    ## dictionary of important values relating to cli call of program:
    options = { 'input-file'           : "",
                'icon-name'            : "",
                'icon-file-format'     : "",
                'multipage-icon'       : False,
                'multipage-icon-delay' : 100,
                'icon-scale'           : 180,
                'verbosity'            : 0,
              }
    ## Get the options and arguments provided by the user via the CLI:
    try:
        myoptions, myargs = getopt.getopt(sys.argv[1:], "hVv:s:md:f:o:", \
                                          ["help",
                                           "version",
                                           "verbosity=",
                                           "icon-scale=",
                                           "multipage-icon",
                                           "multipage-icon-delay=",
                                           "icon-file-format=",
                                           "icon-name="])
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
        elif opt[0] in ("-o", "--icon-name"):
            ## Get the name of the icon that is to be created:
            options["icon-name"] = opt[1]
        elif opt[0] in ("-f", "--icon-file-format"):
            ## The file format of the icon file:
            if str(opt[1]).lower() not in CFG_ALLOWED_FILE_EXTENSIONS:
                ## Illegal file format requested for icon:
                usage()
            else:
                ## gif if an invalid icon type was supplied:
                options["icon-file-format"] = str(opt[1]).lower()
        elif opt[0] in ("-m","--multipage-icon"):
            ## The user would like a multipage (animated) icon:
            options['multipage-icon'] = True
        elif opt[0] in ("-d", "--multipage-icon-delay"):
            ## The delay to be used in the case of a multipage (animated) icon:
            try:
                frame_delay = int(opt[1])
            except ValueError:
                ## Invalid value for delay supplied. Usage message.
                usage()
            else:
                if frame_delay >= 0:
                    options['multipage-icon-delay'] = frame_delay
        elif opt[0] in ("-s", "--icon-scale"):
            ## The scaling information for the icon:
            if re_imagemagic_scale_parameter_format.match(opt[1]):
                options['icon-scale'] = opt[1]
            else:
                usage()
    ##
    ## Done. Return the dictionary of options:
    return options


def create_icon_cli():
    """The function responsible for triggering the icon creation process when
       called via the CLI.
       This function will effectively get the CLI options, then pass them to
       function that is responsible for coordinating the icon creation process
       itself.
       Once stamping has been completed, an attempt will be made to copy the
       icon file to the current working directory. If this can't be done, the
       path to the icon will be printed to stdout instead.
    """
    ## Get CLI options and arguments:
    input_options = get_cli_options()

    ## Create the icon file and obtain the name of the working directory in
    ## which the icon file is situated and the name of the icon file:
    try:
        (working_dir, icon_file) = create_icon(input_options)
    except InvenioWebSubmitIconCreatorError as err:
        ## Something went wrong:
        sys.stderr.write("Icon creation failed: [%s]\n" % str(err))
        sys.stderr.flush()
        sys.exit(1)

    if not os.access("./%s" % icon_file, os.F_OK):
        ## Copy the icon file into the current directory:
        try:
            shutil.copyfile("%s/%s" % (working_dir, icon_file), \
                            "./%s" % icon_file)
        except IOError:
            ## Report that it wasn't possible to copy the icon file locally
            ## and offer the user a path to it:
            msg = "It was not possible to copy the icon file to the " \
                  "current working directory.\nYou can find it here: " \
                  "[%s/%s].\n" \
                  % (working_dir, icon_file)
            sys.stderr.write(msg)
            sys.stderr.flush()
    else:
        ## A file exists in curdir with the same name as the final icon file.
        ## Just print out a message stating this fact, along with the path to
        ## the icon file in the temporary working directory:
        msg = "The icon file [%s] has not been copied to the current " \
              "working directory because a file with this name already " \
              "existed there.\nYou can find the icon file here: " \
              "[%s/%s].\n" % (icon_file, working_dir, icon_file)
        sys.stderr.write(msg)
        sys.stderr.flush()



# Start proceedings for CLI calls:
if __name__ == "__main__":
    create_icon_cli()
