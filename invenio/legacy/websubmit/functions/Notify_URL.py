# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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

import os

from invenio.legacy.bibsched.bibtask import \
     task_low_level_submission, \
     bibtask_allocate_sequenceid
from invenio.legacy.websubmit.functions.Shared_Functions import ParamFromFile

def Notify_URL(parameters, curdir, form, user_info=None):
    """
    Access a given URL, and possibly post some content.

    Could be used to notify that a record has been fully integrated.
    (the URL is only accessed once the BibTask created by this
    function runs in BibSched, not the when the function is run. The
    BibTask uses a task sequence ID to respect ordering of tasks)

    if URL is empty, skip the notification.

    @param parameters: (dictionary) - contains the following parameter
         strings used by this function:

         + url: (string) - the URL to be contacted by this function
                           (must start with http/https)
                           If value starts with "FILE:", will look for
                           the URL in a file on curdir with the given name.
                           for eg: "FILE:my_url"
                           (value retrieved when function is run)

         + data: (string) - (optional) the data to be posted at the
                            given URL.  if no value is given, the URL
                            will be accessed via GET.
                            If value starts with "FILE:", will look for
                            the data in a file on curdir with the given name.
                            for eg: "FILE:my_data"
                            (value retrieved when function is run)

         + content_type: (string) - (optional) the content-type to use
                                    to post data. Default is 'text/plain'.
                                    Ignored if not data is posted.

         + attempt_times: (int) - (optional) up to how many time shall
                                  we try to contact the URL in case we
                                  fail at contacting it?

         + attempt_sleeptime: (int) - (optional) how many seconds to
                                       sleep between each attempt?

         + admin_emails: (string) - (optional) list of emails (comma-separated
                                    values) to contact in case the URL
                                    cannot be accessed after all attempts.
                                    If value starts with "FILE:", will look for
                                    the emails in a file on curdir with the given name.
                                    for eg: "FILE:my_email"
                                    (value retrieved when function is run)

         + user: (string) - the user to be used to launch the task
                            (visible in BibSched).  If value starts
                            with"FILE:", will look for the emails in a file on
                            curdir with the given name.
                            for eg:"FILE:my_user"
                            (value retrieved when function is run)

    """

    other_bibtasklet_arguments = []
    sequence_id = bibtask_allocate_sequenceid(curdir)

    url               = parameters["url"]
    data              = parameters["data"]
    admin_emails      = parameters["admin_emails"]
    content_type      = parameters["content_type"]
    attempt_times     = parameters["attempt_times"]
    attempt_sleeptime = parameters["attempt_sleeptime"]
    user              = parameters["user"]

    # Maybe some params must be read from disk
    if url.startswith('FILE:'):
        url = ParamFromFile(os.path.join(curdir, url[5:]))
    if not url:
        return ""
    if data.startswith('FILE:'):
        data = ParamFromFile(os.path.join(curdir, data[5:]))
    if admin_emails.startswith('FILE:'):
        admin_emails = ParamFromFile(os.path.join(curdir, admin_emails[5:]))
    if user.startswith('FILE:'):
        user = ParamFromFile(os.path.join(curdir, user[5:]))

    if data:
        other_bibtasklet_arguments.extend(("-a", "data=%s" % data))
        other_bibtasklet_arguments.extend(("-a", "content_type=%s" % content_type))

    return task_low_level_submission(
        "bibtasklet", user, "-T", "bst_notify_url",
        "-I", str(sequence_id),
        "-a", "url=%s" % url,
        "-a", "attempt_times=%s" % attempt_times,
        "-a", "attempt_sleeptime=%s" % attempt_sleeptime,
        "-a", "admin_emails=%s" % admin_emails,
        *other_bibtasklet_arguments)
