# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Loads recommendations and optionally formats and filters them."""

import json

from invenio.bibfield import get_record
from invenio.config import CFG_BASE_URL, \
    CFG_RECOMMENDER_PREFIX, \
    CFG_SITE_RECORD
from invenio.recommender_initializer import get_redis_connection
from invenio.webuser import collect_user_info


def get_recommended_records(recid):
    """
    Record recommendations.

    @param recid: Record id for the recommendation.
    @return: List of recommended records and a version ([234, 34, 2], 5)
    """
    redis_connector = get_redis_connection()

    if not redis_connector:
        return [], 0

    # Get recommendation
    key = "{0}{1}".format(CFG_RECOMMENDER_PREFIX, recid)
    recommendations = redis_connector.get(key)
    if not recommendations:
        # No recommendations available.
        return [], 0

    recommendations = json.loads(recommendations)

    records = recommendations.get('records', [])
    recommender_version = recommendations.get('version', 0)

    return records, recommender_version


def get_recommended_records_with_metadata(recid, maximum=3):
    """
    Record recommendations with metadata as title, authors and url.

    @param recid: Record id for the recommendation.
    @param maximum: Maximum recommendations to return.
    @return: List of recommended records [{
                                          'number': ,
                                          'record_url': ,
                                          'record_title': ,
                                          'record_authors': ,
                                          }, ]
    """
    records, recommender_version = get_recommended_records(recid)
    return _format_recommendation(records, recid, recommender_version,
                                  user_id=0, maximum=maximum)


def _format_recommendation(recommended_records, recid_source,
                           recommender_version, user_id=0,
                           maximum=3):
    """
    Load the record information for each record in a list.

    @param recommended_records: List of records [1234 ,344 ,342]
    @param recid_source: Record id where the recommendations are displayed.
    @param recommender_version: Recommender version (for custom events).
    @param user_id: User ID checks if the user has access to the recommended
                    records, user id 0 shows only public records.
    @param maximum: Maximum recommendations to return.
    @return: List of recommended records [{
                                          'number': ,
                                          'record_url': ,
                                          'record_title': ,
                                          'record_authors': ,
                                          }, ]
    """
    from invenio.webstat import get_url_customevent
    from invenio.search_engine import check_user_can_view_record, \
        record_public_p

    check_same_title = []
    suggestions = []
    rec_count = 1
    for recid in recommended_records:
        try:
            if user_id > 0:
                # check if user can view record
                user_info = collect_user_info(user_id)
                if check_user_can_view_record(user_info, recid)[0] > 0:
                    # Not authorized
                    continue
            else:
                # check if record is public
                if not record_public_p(recid):
                    continue

            # get record information
            record = get_record(recid)
            title = record.get('title.title')

            # Check for no title or similar title
            if not title or title in check_same_title:
                continue
            else:
                check_same_title.append(title)

            rec_authors = filter(None, record.get('authors.full_name', [])) \
                or filter(None, record.get('corporate_name.name', []))
            authors = "; ".join(rec_authors)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue

        record_url = "{0}/{1}/{2}".format(CFG_BASE_URL, CFG_SITE_RECORD,
                                       str(recid))
        url = get_url_customevent(record_url,
                                  "recommended_record",
                                  [str(recid_source), str(recid),
                                   str(rec_count), str(user_id),
                                   str(recommender_version)])
        suggestions.append({
                           'number': rec_count,
                           'record_url': url,
                           'record_title': title.strip(),
                           'record_authors': authors.strip(),
                           })
        if rec_count >= maximum:
            break
        rec_count += 1

    return suggestions
