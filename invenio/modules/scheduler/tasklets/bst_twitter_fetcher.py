#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""
Twitter fetcher

In order to schedule fetching tweets you can type at the command line:

$ sudo -u www-data /opt/invenio/bin/bibtasklet -T bst_twitter_fetcher -uadmin -s5m -a "query=YOURQUERY"

"""

# Here we import the Twitter APIs
import twitter
import re
import os
import sys
import tempfile
import time
import sys

# Here are some good Invenio APIs

from invenio.config import CFG_TMPDIR

# BibRecord -> to create MARCXML records
from invenio.legacy.bibrecord import record_add_field, record_xml_output

# BibTask -> to manipulate Bibliographic Tasks
from invenio.legacy.bibsched.bibtask import task_low_level_submission, write_message, task_update_progress

# BibDocFile to manipulate documents
from invenio.legacy.bibdocfile.api import check_valid_url

# WebSearch to search for previous tweets
from invenio.legacy.search_engine import perform_request_search, get_fieldvalues

_TWITTER_API = twitter.Api()

def get_tweets(query):
    """
    This is how simple it is to fetch tweets :-)
    """
    ## We shall skip tweets that already in the system.
    previous_tweets = perform_request_search(p='980__a:"TWEET" 980__b:"%s"' % query, sf='970__a', so='a')
    if previous_tweets:
        ## A bit of an algorithm to retrieve the last Tweet ID that was stored
        ## in our records
        since_id = int(get_fieldvalues(previous_tweets[0], '970__a')[0])
    else:
        since_id = 0
    final_results = []
    results = list(_TWITTER_API.Search(query, rpp=100, since_id=since_id).results)
    final_results.extend(results)
    page = 1
    while len(results) == 100: ## We stop if there are less than 100 results per page
        page += 1
        results = list(_TWITTER_API.Search(query, rpp=100, since_id=since_id, page=page).results)
        final_results.extend(results)
    return final_results

_RE_GET_HTTP = re.compile("(https?://.+?)(\s|$)")
_RE_TAGS = re.compile("([#@]\w+)")
def tweet_to_record(tweet, query):
    """
    Transform a tweet into a record.
    @note: you may want to highly customize this.
    """
    rec = {}
    ## Let's normalize the body of the tweet.
    text = tweet.text.encode('UTF-8')
    text = text.replace('&gt;', '>')
    text = text.replace('&lt;', '<')
    text = text.replace('&quot;', "'")
    text = text.replace('&amp;', '&')

    ## Let's add the creation date
    try:
        creation_date = time.strptime(tweet.created_at, '%a, %d %b %Y %H:%M:%S +0000')
    except ValueError:
        creation_date = time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
    record_add_field(rec, '260__c', time.strftime('%Y-%m-%dZ%H:%M:%ST', creation_date))

    ## Let's add the Tweet ID
    record_add_field(rec, '970', subfields=[('a', str(tweet.id))])

    ## Let's add the body of the tweet as an abstract
    record_add_field(rec, '520', subfields=[('a', text)])

    ## Let's re-add the body of the tweet as a title.
    record_add_field(rec, '245', subfields=[('a', text)])

    ## Let's fetch information about the user
    try:
        user = _TWITTER_API.GetUser(tweet.from_user)

        ## Let's add the user name as author of the tweet
        record_add_field(rec, '100', subfields=[('a', str(user.name.encode('UTF-8')))])

        ## Let's fetch the icon of the user profile, and let's upload it as
        ## an image (and an icon of itself)
        record_add_field(rec, 'FFT', subfields=[('a', user.profile.image_url.encode('UTF-8')), ('x', user.profile.image_url.encode('UTF-8'))])
    except Exception as err:
        write_message("WARNING: issue when fetching the user: %s" % err, stream=sys.stderr)
    if hasattr(tweet, 'iso_language_code'):
            ## Let's add the language of the Tweet if available (also this depends)
        ## on the kind of Twitter API call we used
        record_add_field(rec, '045', subfields=[('a', tweet.iso_language_code.encode('UTF-8'))])

    ## Let's tag this record as a TWEET so that later we can build a collection
    ## out of these records.
    record_add_field(rec, '980', subfields=[('a', 'TWEET'), ('b', query)])

    ## Some smart manipulations: let's parse out URLs and tags from the body
    ## of the Tweet.
    for url in _RE_GET_HTTP.findall(text):
        url = url[0]
        record_add_field(rec, '856', '4', subfields=[('u', url)])

    for tag in _RE_TAGS.findall(text):
        ## And here we add the keywords.
        record_add_field(rec, '653', '1', subfields=[('a', tag), ('9', 'TWITTER')])

    ## Finally we shall serialize everything to MARCXML
    return record_xml_output(rec)

def bst_twitter_fetcher(query):
    """
    Fetch the tweets related to the user and upload them into Invenio.
    @param user: the user
    """
    ## We prepare a temporary MARCXML file to upload.
    fd, name = tempfile.mkstemp(suffix='.xml', prefix='tweets', dir=CFG_TMPDIR)
    tweets = get_tweets(query)
    if tweets:
        os.write(fd, """<collection>\n""")
        for i, tweet in enumerate(tweets):
            ## For every tweet we transform it to MARCXML and we dump it in the file.
            task_update_progress('DONE: tweet %s out %s' % (i, len(tweets)))
            os.write(fd, tweet_to_record(tweet, query))

        os.write(fd, """</collection\n>""")
        os.close(fd)

        ## Invenio magic: we schedule an upload of the created MARCXML to be inserted
        ## ASAP in the system.
        task_low_level_submission('bibupload', 'admin', '-i', '-r', name, '-P5')
        write_message("Uploaded file %s with %s new tweets about %s" % (name, len(tweets), query))
    else:
        write_message("No new tweets about %s" % query)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        bst_twitter_fetcher(sys.argv[1])
    else:
        print("USAGE: %s TWITTER_QUERY" % sys.argv[0])
        sys.exit(1)
