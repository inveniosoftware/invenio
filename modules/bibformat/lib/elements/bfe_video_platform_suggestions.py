# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""BibFormat element
* Part of the video platform prototype
* Creates a list of video suggestions
* Based on word similarity ranking
* Must be done in a collection that holds video records with thumbnails, title and author
"""

from invenio.config import CFG_BASE_URL
from invenio.bibdocfile import BibRecDocs
from invenio.intbitset import intbitset
from invenio.search_engine import perform_request_search 
from invenio.bibrank_record_sorter import rank_records
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibencode_utils import timecode_to_seconds
import random

html_skeleton_suggestion = """
<!-- VIDEO SUGGESTION -->
<div class="video_suggestion_box">
    <div class="video_suggestion_thumbnail">
        <a href="%(video_record_url)s">
            <img src="%(video_thumb_url)s" alt="%(video_thumb_alt)s"/>
        </a>
        <div class="video_suggestion_duration">
            %(video_duration)s
        </div>
    </div>
    <div class="video_suggestion_title">
        %(video_title)s
    </div>
    <div class="video_suggestion_author">
        by %(video_authors)s
    </div>
</div>
"""

def format_element(bfo, collection="Videos", threshold="75", maximum="3", shuffle="True"):
    """ Creates video suggestions based on ranking algorithms
    
    @param collection: Collection to take the suggestions from
    @param threshold: Value between 0 and 100. Only records ranked higher than the value are presented.
    @param maximum: Maximum suggestions to show
    @param shuffle: True or False, should the suggestions be shuffled?
    """
    if threshold.isdigit():
        threshold = int(threshold)
    else:
        raise ValueError("The given threshold is not a digit")
    if maximum.isdigit():
        maximum = int(maximum)
    else:
        raise ValueError("The given maximum is not a digit")
    if shuffle == "True":
        shuffle = True
    else:
        shuffle = False;
    suggestions = []
    recid = bfo.control_field('001')
    similar_records = find_similar_videos(recid, collection, threshold, maximum, shuffle)
    for sim_recid in similar_records:
        thumbnail = get_video_thumbnail(sim_recid)
        title = get_video_title(sim_recid)
        authors = get_video_authors(sim_recid)
        url = get_video_record_url(sim_recid)
        duration = get_video_duration(sim_recid)
        suggestion = html_skeleton_suggestion % {
                    'video_record_url': url,
                    'video_thumb_url': thumbnail[0],
                    'video_thumb_alt': thumbnail[1],
                    'video_duration': duration,
                    'video_title': title,
                    'video_authors': authors,
                    }
        suggestions.append(suggestion)
    return "\n".join(suggestions)

def find_similar_videos(recid, collection="Videos", threshold=75, maximum=3, shuffle=True):
    """ Returns a list of similar video records
    """
    similar_records = []
    collection_recids = intbitset(perform_request_search(cc=collection))
    ranking = rank_records('wrd', 0, collection_recids, ['recid:' + str(recid)])
    ## ([6, 7], [81, 100], '(', ')', '')
    for list_pos, rank in enumerate(ranking[1]):
        if rank >= threshold:
            similar_records.append(ranking[0][list_pos])
    if shuffle:
        if maximum > len(similar_records):
            maximum = len(similar_records)
        return random.sample(similar_records, maximum)
    else:
        return similar_records[:maximum]

def get_video_thumbnail(recid):
    """ Returns the URL and ALT text for a video thumbnail of a given record
    """
    comments = get_fieldvalues(recid, '8564_z')
    descriptions =  get_fieldvalues(recid, '8564_y')
    urls = get_fieldvalues(recid, '8564_u')
    for pos, comment in enumerate(comments):
        if comment in ('SUGGESTIONTHUMB', 'BIGTHUMB', 'THUMB', 'SMALLTHUMB', 'POSTER'):
            return (urls[pos], descriptions[pos])
    return ("", "")

def get_video_title(recid):
    """ Return the Title of a video record
    """
    return get_fieldvalues(recid, '245__a')[0]

def get_video_authors(recid):
    """ Return the Authors of a video record
    """
    return ", ".join(get_fieldvalues(recid, '100__a'))

def get_video_record_url(recid):
    """ Return the URL of a video record
    """
    return CFG_BASE_URL + "/record/" + str(recid)

def get_video_duration(recid):
    """ Return the duration of a video
    """
    duration = get_fieldvalues(recid, '950__d')
    if duration:
        duration = duration[0]
        duration = timecode_to_seconds(duration)
        return human_readable_time(duration)
    else:
        return ""

def human_readable_time(seconds):
    """ Creates a human readable duration representation
    """
    for x in ['s','m','h']:
        if seconds < 60.0:
            return "%.0f %s" % (seconds, x)
        seconds /= seconds

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0