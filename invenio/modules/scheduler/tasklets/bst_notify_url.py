# -*- coding: utf-8 -*-
#
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

"""
Invenio Tasklet.

Notify a URL, and post data if wanted.
"""
import urlparse
import urllib2
import time

from invenio.config import \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_NAME
from invenio.legacy.bibsched.bibtask import write_message, \
     task_sleep_now_if_required
from invenio.ext.email import send_email

def bst_notify_url(url, data=None,
                   content_type='text/plain',
                   attempt_times=1,
                   attempt_sleeptime=10,
                   admin_emails=None):
    """
    Access given URL, and post given data if specified.

    @param url: the URL to access
    @type url: string
    @param data: the data to be posted to the given URL
    @type data: string
    @param data: the content-type header to use to post data
    @type data: string
    @param attempt_times: number of tries
    @type attempt_times: int
    @param attempt_sleeptime: seconds in between tries
    @type attempt_sleeptime: int
    @param admin_emails: a comma-separated list of emails to notify in case of failure
    @type admin_emails: string or list (as accepted by mailutils.send_email)

    If accessing fails, try to send it ATTEMPT_TIMES, and wait for
    ATTEMPT_SLEEPTIME seconds in between tries. When the maximum
    number of attempts is reached, send an email notification to the
    recipients specified in ADMIN_EMAILS.
    """
    attempt_times = int(attempt_times)
    attempt_sleeptime = int(attempt_sleeptime)
    remaining_attempts = attempt_times

    success_p = False
    reason_failure = ""

    write_message("Going to notify URL: %(url)s" %  {'url': url})

    while not success_p and remaining_attempts > 0:
        ## <scheme>://<netloc>/<path>?<query>#<fragment>
        scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
        ## See: http://stackoverflow.com/questions/111945/is-there-any-way-to-do-http-put-in-python
        if scheme == 'http':
            opener = urllib2.build_opener(urllib2.HTTPHandler)
        elif scheme == 'https':
            opener = urllib2.build_opener(urllib2.HTTPSHandler)
        else:
            raise ValueError("Scheme not handled %s for url %s" % (scheme, url))
        request = urllib2.Request(url, data=data)
        if data:
            request.add_header('Content-Type', content_type)
            request.get_method = lambda: 'POST'
        try:
            opener.open(request)
            success_p = True
        except urllib2.URLError as e:
            success_p = False
            reason_failure = repr(e)
        if not success_p:
            remaining_attempts -= 1
            if remaining_attempts > 0: # sleep only if we shall retry again
                task_sleep_now_if_required(can_stop_too=True)
                time.sleep(attempt_sleeptime)

        # Report about success/failure
        if success_p:
            write_message("URL successfully notified")
        else:
            write_message("Failed at notifying URL. Reason:\n%(reason_failure)s" % \
                          {'reason_failure': reason_failure})

    if not success_p and admin_emails:
        # We could not access the specified URL. Send an email to the
        # specified contacts.
        write_message("Notifying by email %(admin_emails)s" % \
                      {'admin_emails': str(admin_emails)})
        subject = "%(CFG_SITE_NAME)s could not contact %(url)s" % \
                  {'CFG_SITE_NAME': CFG_SITE_NAME,
                   'url': url}
        content = """\n%(CFG_SITE_NAME)s unsuccessfully tried to contact %(url)s.

Number of attempts: %(attempt_times)i. No further attempts will be made.

""" % \
                  {'CFG_SITE_NAME': CFG_SITE_NAME,
                   'url': url,
                   'attempt_times': attempt_times}
        if data:
            max_data_length = 10000
            content += "The following data should have been posted:\n%(data)s%(extension)s" % \
                      {'data': data[:max_data_length],
                       'extension': len(data) > max_data_length and ' [...]' or ''}
        # Send email. If sending fails, we will stop the queue
        return send_email(fromaddr=CFG_SITE_ADMIN_EMAIL,
                          toaddr=admin_emails,
                          subject=subject,
                          content=content)

    # We do not really want to stop the queue now, even in case of
    # failure as an email would have been sent if necessary.
    return 1
