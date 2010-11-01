# -*- coding: utf-8 -*-
##
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

""" Configuration file for miscutil module.
- Contains standard error messages for errorlib
  e.g. No error message given, etc.
"""

__revision__ = "$Id$"

# pylint: disable=C0301
CFG_MISCUTIL_ERROR_MESSAGES = \
{   'ERR_MISCUTIL_BAD_FILE_ARGUMENT_PASSED':  '_("Invalid argument %s was passed")',
    'ERR_MISCUTIL_WRITE_FAILED': '_("Unable to write to file %s")',
    'ERR_MISCUTIL_NO_ERROR_MESSAGE': '_("Trying to write a non error message to error log")',
    'ERR_MISCUTIL_NO_WARNING_MESSAGE': '_("Trying to write a non error message or non warning message to error log")',
    'ERR_MISCUTIL_TOO_MANY_ARGUMENT': '_("Unable to display error: Too many arguments given for error %s")',
    'ERR_MISCUTIL_TOO_FEW_ARGUMENT':'_("Unable to display error: Too few arguments given for error %s")',
    'ERR_MISCUTIL_IMPORT_ERROR': '_("An undefined error has occured (%s). \'%s\' does not exist")',
    'ERR_MISCUTIL_NO_DICT': '_("An undefined error has occured (%s). %s does not contain %s")',
    'ERR_MISCUTIL_NO_MESSAGE_IN_DICT': '_("An undefined error has occured. %s not defined in %s")',
    'ERR_MISCUTIL_UNDEFINED_ERROR': '_("An undefined error has occured (%s)")',
    'ERR_MISCUTIL_BAD_ARGUMENT_TYPE': '_("Unable to display error: Arguments do not match for error %s")',
    'ERR_MISCUTIL_DEBUG': 'Error nb %i',
    'ERR_MISCUTIL_NOT_ATTEMPTING_SEND_EMAIL' : '_("The system is not attempting to send an email from %s, to %s, with body %s")',
    'ERR_MISCUTIL_CONNECTION_SMTP': '_("Error in connecting to the SMPT server waiting %s seconds. Exception is %s, while sending email from %s to %s with body %s.")',
    'ERR_MISCUTIL_SENDING_EMAIL' : '_("Error in sending email from %s to %s with body %s")'
}
