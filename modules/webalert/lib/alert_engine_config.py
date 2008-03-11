## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

"""CDS Invenio Alert Engine config parameters."""

__revision__ = \
    "$Id$"

# how many records at most do we send in an outgoing alert emails?
CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL = 20

# number of chars per line in outgoing alert emails?
CFG_WEBALERT_MAX_NUM_OF_CHARS_PER_LINE_IN_ALERT_EMAIL = 72

# when sending alert emails fails, how many times we retry?
CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES = 3

# when sending alert emails fails, what is the sleeptime between
# tries? (in seconds)
CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES = 300

# are we debugging?
## 0 = production, nothing on the console, email sent
## 1 = messages on the console, email sent
## 2 = messages on the console, no email sent
## 3 = many messages on the console, no email sent
## 4 = many messages on the console, email sent to CFG_SITE_SUPPORT_EMAIL
CFG_WEBALERT_DEBUG_LEVEL = 0

