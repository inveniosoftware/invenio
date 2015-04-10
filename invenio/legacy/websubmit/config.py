# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio Submission Web Interface config file."""

from __future__ import unicode_literals

__revision__ = "$Id$"

import re

# test:
test = "FALSE"

# CC all action confirmation mails to administrator? (0 == NO; 1 == YES)
CFG_WEBSUBMIT_COPY_MAILS_TO_ADMIN = 0

# During submission, warn user if she is going to leave the
# submission by following some link on the page?
# Does not work with Opera and Konqueror.
# This requires all submission functions to set Javascript variable
# 'user_must_confirm_before_leaving_page' to 'false' before
# programmatically submitting a form , or else users will be asked
# confirmation after each submission step.
# (0 == NO; 1 == YES)
CFG_WEBSUBMIT_CHECK_USER_LEAVES_SUBMISSION = 0

# List of keywords/format parameters that should not write by default
# corresponding files in submission directory (`curdir').  Some other
# filenames not included here are reserved too, such as those
# containing non-alphanumeric chars (excepted underscores '_'), for
# eg all names containing a dot ('bibdocactions.log',
# 'performed_actions.log', etc.)
CFG_RESERVED_SUBMISSION_FILENAMES = ['SuE',
                                     'files',
                                     'lastuploadedfile',
                                     'curdir',
                                     'function_log',
                                     'SN',
                                     'ln']

# Prefix for video uploads, Garbage Collector
CFG_WEBSUBMIT_TMP_VIDEO_PREFIX = "video_upload_"

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
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)


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
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)


class InvenioWebSubmitFunctionWarning(Exception):
    """This exception should be raised by a WebSubmit function
       when unexpected behaviour is encountered during the execution
       of the function. The unexpected behaviour should not have been
       so serious that execution had to be halted, but since the
       function was unable to perform its task, the event must be
       logged.
       Logging of the exception will be performed by WebSubmit.

       Extends: Exception.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - a string to write to the log.
        """
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)


class InvenioWebSubmitFileStamperError(Exception):
    """This exception should be raised by websubmit_file_stamper when an
       error is encoutered that prevents a file from being stamped.
       When caught, this exception should be used to stop processing with a
       failure signal.

       Extends: Exception.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - a string to write to the log.
        """
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)


class InvenioWebSubmitIconCreatorError(Exception):
    """This exception should be raised by websubmit_icon_creator when an
       error is encoutered that prevents an icon from being created.
       When caught, this exception should be used to stop processing with a
       failure signal.

       Extends: Exception.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - a string to write to the log.
        """
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)

class InvenioWebSubmitFileMetadataRuntimeError(Exception):
    """This exception should be raised by websubmit_file_metadata plugins when an
       error is encoutered that prevents a extracting/updating a file.
       When caught, this exception should be used to stop processing with a
       failure signal.

       Extends: Exception.
    """
    def __init__(self, value):
        """Set the internal "value" attribute to that of the passed "value"
           parameter.
           @param value: (string) - a string to write to the log.
        """
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        """Return oneself as a string (actually, return the contents of
           self.value).
           @return: (string)
        """
        return str(self.value)
