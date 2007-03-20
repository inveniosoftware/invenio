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

"""CDS Invenio Submission Web Interface config file."""

__revision__ = "$Id$"

## test:
test = "FALSE"

## CC all action confirmation mails to administrator? (0 == NO; 1 == YES)
CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN = 0

## known compressed file extensions: 
CFG_COMPRESSED_FILE_EXTENSIONS = ["z", "gz", "tar", "tgz", "tar",
                                  "tar.gz", "zip", "rar", "arj",
                                  "arc", "pak", "lha", "lhz", "sit",
                                  "sea", "sitx", "cpt", "hqx", "uu",
                                  "uue", "bz", "bz2", "bzip", "tbz",
                                  "tbz2", "tar.bz", "tar.bz2"]
                                
CFG_KNOWN_FILE_EXTENSIONS = ["lis",
			     "sxi",
   		 	     "zip",
			     "kpr",
                             "xls",
                             "mov",
			     "avi",
			     "ppt",
			     "prn",
			     "pdf",
			     "tif",
			     "doc",
			     "dot",
			     "ps.gz",
			     "ps.Z",
			     "ps",
			     "eps",
			     "pps",
			     "gif",
			     "jpeg",
			     "jpg",
			     "JPG",
			     "html",
			     "htm",
			     "Download.link",
			     "link",
			     "tex",
			     "txt",
			     "ef.tif",
			     "e.tif",
			     "f.tif",
			     "ef.pdf",
			     "e.pdf",
			     "f.pdf",
			     "ef.ps.gz",
			     "e.ps.gz",
			     "f.ps.gz",
			     "ef.ps",
			     "e.ps",
			     "f.ps",
			     "e.xls",
			     "f.xls",
			     "ef.doc",
			     "e.doc",
			     "f.doc",
			     "ef.html",
			     "e.html",
			     "f.html",
			     "hpg",
			     "mpp",
			     "h",
			     "rtf",
			     "tar",
			     "tar.gz",
			     "tgz",
			     "msg",
			     "llb",
			     "ogg",
			     "mp3",
			     "wav",
			     "mpg"]


class InvenioWebSubmitFunctionError(Exception):
    """This exception should only ever be raised by WebSubmit functions.
       It will be caught and handled by the WebSubmit core itself.
       It is used to signal to WebSubmit core that one of the functions
       encountered a FATAL ERROR situation that should all further execution
       of the submission.
       The exception will carry an error message in its "value" string. This
       message will probably be displayed on the user's browser in an Invenio
       "error" box, and may be logged for the admin to examine.

       Again: If this exception is raised by a WebSubmit function, an error
              message will displayed and the submission ends in failure.

       Extends: Exception.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - an error string to display to the user.
        """
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return repr(self.value)


class InvenioWebSubmitFunctionStop(Exception):
    """This exception should only ever be raised by WebSubmit functions.
       It will be caught and handled by the WebSubmit core itself.
       It is used to signal to WebSubmit core that one of the functions
       encountered a situation that should prevent the functions that follow
       it from being executed, and that WebSubmit core should display some sort
       of message to the user. This message will be stored in the "value"
       attribute of the object.

       ***
       NOTE: In the current WebSubmit, this "value" is ususally a JavaScript
             string that redirects the user's browser back to the Web form
             phase of the submission. The use of JavaScript, however is going
             to be removed in the future, so the mechanism may change.
       ***

       Extends: Exception.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - a string to display to the user.
        """
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return repr(self.value)


class InvenioWebSubmitFunctionWarning(Exception):
    """This exception should be raised by a WebSubmit function
       when unexpected behaviour is encountered during the execution
       of the function. The unexpected behaviour should not have been
       so serious that execution had to be halted, but since the
       function was unable to perform its task, the event must be
       logged.
       Logging of the exception will be performed by WebSubmit.
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
        return repr(self.value)
