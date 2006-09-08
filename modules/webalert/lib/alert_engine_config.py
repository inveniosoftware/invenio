## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

__revision__ = "$Id$"

# how many records at most do we send in an outgoing alert emails?
cfg_webalert_max_num_of_records_in_alert_email = 20

# number of chars per line in outgoing alert emails?
cfg_webalert_max_num_of_chars_per_line_in_alert_email = 72

# when sending alert emails fails, how many times we retry?
cfg_webalert_send_email_number_of_tries = 3

# when sending alert emails fails, what is the sleeptime between
# tries? (in seconds)
cfg_webalert_send_email_sleeptime_between_tries = 300 

# are we debugging?
## 0 = production, nothing on the console, email sent
## 1 = messages on the console, email sent
## 2 = messages on the console, no email sent
## 3 = many messages on the console, no email sent
## 4 = many messages on the console, email sent to supportemail
cfg_webalert_debug_level = 0

