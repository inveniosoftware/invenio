# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012 CERN.
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

"""WebLinkback - Database Layer"""

from invenio.legacy.dbquery import run_sql
from invenio.legacy.weblinkback.config import CFG_WEBLINKBACK_STATUS, \
                                       CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME, \
                                       CFG_WEBLINKBACK_DEFAULT_USER, \
                                       CFG_WEBLINKBACK_PAGE_TITLE_STATUS
from invenio.utils.text import xml_entities_to_utf8


def get_all_linkbacks(recid=None, status=None, order=CFG_WEBLINKBACK_ORDER_BY_INSERTION_TIME["ASC"], linkback_type=None):
    """
    Get all linkbacks
    @param recid: of one record, of all if None
    @param status: with a certain status, of all if None
    @param order: order by insertion time either "ASC" or "DESC"
    @param linkback_type: of a certain type, of all if None
    @return [(linkback_id,
              origin_url,
              recid,
              additional_properties,
              linkback_type,
              linkback_status,
              insert_time)]
              in order by id
    """

    header_sql = """SELECT id,
                            origin_url,
                            id_bibrec,
                            additional_properties,
                            type,
                            status,
                            insert_time
                     FROM lnkENTRY"""
    conditions = []
    order_sql = "ORDER by id %s" % order

    params = []

    def add_condition(column, value):
        if value:
            if not conditions:
                conditions.append('WHERE %s=%%s' % column)
            else:
                conditions.append('AND %s=%%s' % column)
            params.append(value)

    add_condition('id_bibrec', recid)
    add_condition('status', status)
    add_condition('type', linkback_type)

    return run_sql(header_sql + ' ' + ' '.join(conditions) + ' ' + order_sql, tuple(params))


def approve_linkback(linkbackid, user_info):
    """
    Approve linkback
    @param linkbackid: linkback id
    @param user_info: user info
    """
    update_linkback_status(linkbackid, CFG_WEBLINKBACK_STATUS['APPROVED'], user_info)


def reject_linkback(linkbackid, user_info):
    """
    Reject linkback
    @param linkbackid: linkback id
    @param user_info: user info
    """
    update_linkback_status(linkbackid, CFG_WEBLINKBACK_STATUS['REJECTED'], user_info)


def update_linkback_status(linkbackid, new_status, user_info = None):
    """
    Update status of a linkback
    @param linkbackid: linkback id
    @param new_status: new status
    @param user_info: user info
    """

    if user_info == None:
        user_info = {}
        user_info['uid'] = CFG_WEBLINKBACK_DEFAULT_USER

    run_sql("""UPDATE lnkENTRY
                  SET status=%s
                  WHERE id=%s
            """, (new_status, linkbackid))

    logid = run_sql("""INSERT INTO lnkLOG (id_user, action, log_time)
                          VALUES
                          (%s, %s, NOW());
                       SELECT LAST_INSERT_ID();
                    """, (user_info['uid'], new_status))

    run_sql("""INSERT INTO lnkENTRYLOG (id_lnkENTRY , id_lnkLOG)
                  VALUES
                  (%s, %s);
            """, (linkbackid, logid))


def create_linkback(origin_url, recid, additional_properties, linkback_type, user_info):
    """
    Create linkback
    @param origin_url: origin URL,
    @param recid: recid
    @param additional_properties: additional properties
    @param linkback_type: linkback type
    @param user_info: user info
    @return id of the created linkback
    """
    linkbackid = run_sql("""INSERT INTO lnkENTRY (origin_url, id_bibrec, additional_properties, type, status, insert_time)
                               VALUES
                               (%s, %s, %s, %s, %s, NOW());
                            SELECT LAST_INSERT_ID();
                         """, (origin_url, recid, str(additional_properties), linkback_type, CFG_WEBLINKBACK_STATUS['PENDING']))

    logid = run_sql("""INSERT INTO lnkLOG (id_user, action, log_time)
                          VALUES
                          (%s, %s, NOW());
                       SELECT LAST_INSERT_ID();
                    """, (user_info['uid'], CFG_WEBLINKBACK_STATUS['INSERTED']))

    run_sql("""INSERT INTO lnkENTRYLOG (id_lnkENTRY, id_lnkLOG)
                  VALUES
                  (%s, %s);
            """, (linkbackid, logid))

    # add url title entry if necessary
    if len(run_sql("""SELECT url
                      FROM lnkENTRYURLTITLE
                      WHERE url=%s
                   """, (origin_url, ))) == 0:
        manual_set_title = 0
        title = ""
        if additional_properties != "" and 'title' in additional_properties.keys():
            manual_set_title = 1
            title = additional_properties['title']

        run_sql("""INSERT INTO lnkENTRYURLTITLE (url, title, manual_set)
                      VALUES
                      (%s, %s, %s)
                """, (origin_url, title, manual_set_title))

    return linkbackid


def get_approved_latest_added_linkbacks(count):
    """
    Get approved latest added linkbacks
    @param count: count of the linkbacks
    @return [(linkback_id,
              origin_url,
              recid,
              additional_properties,
              type,
              status,
              insert_time)]
              in descending order by insert_time
    """
    return run_sql("""SELECT id,
                             origin_url,
                             id_bibrec,
                             additional_properties,
                             type,
                             status,
                             insert_time
                      FROM lnkENTRY
                      WHERE status=%s
                      ORDER BY insert_time DESC
                      LIMIT %s
                   """, (CFG_WEBLINKBACK_STATUS['APPROVED'], count))


def get_url_list(list_type):
    """
    @param list_type: of CFG_WEBLINKBACK_LIST_TYPE
    @return (url0, ..., urln) in ascending order by url
    """
    result = run_sql("""SELECT url
                        FROM lnkADMINURL
                        WHERE list=%s
                        ORDER by url ASC
                     """, (list_type, ))
    return tuple(url[0] for (url) in result)


def get_urls():
    """
    Get all URLs and the corresponding listType
    @return ((url, CFG_WEBLINKBACK_LIST_TYPE), ..., (url, CFG_WEBLINKBACK_LIST_TYPE)) in ascending order by url
    """
    return run_sql("""SELECT url, list
                      FROM lnkADMINURL
                      ORDER by url ASC
                   """)


def url_exists(url, list_type=None):
    """
    Check if url exists
    @param url
    @param list_type: specific list of CFG_WEBLINKBACK_LIST_TYPE, all if None
    @return True or False
    """
    header_sql = """SELECT url
                FROM lnkADMINURL
                WHERE url=%s
                """
    optional_sql = " AND list=%s"

    result = None
    if list_type:
        result = run_sql(header_sql + optional_sql, (url, list_type))
    else:
        result = run_sql(header_sql, (url, ))

    if result != ():
        return True
    else:
        return False


def add_url_to_list(url, list_type, user_info):
    """
    Add a URL to a list
    @param url: unique URL string for all lists
    @param list_type: of CFG_WEBLINKBACK_LIST_TYPE
    @param user_info: user info
    @return id of the created url
    """
    urlid = run_sql("""INSERT INTO lnkADMINURL (url, list)
                          VALUES
                          (%s, %s);
                       SELECT LAST_INSERT_ID();
                    """, (url, list_type))
    logid = run_sql("""INSERT INTO lnkLOG (id_user, action, log_time)
                          VALUES
                          (%s, %s, NOW());
                       SELECT LAST_INSERT_ID();
                    """, (user_info['uid'], CFG_WEBLINKBACK_STATUS['INSERTED']))
    run_sql("""INSERT INTO lnkADMINURLLOG (id_lnkADMINURL, id_lnkLOG)
                  VALUES
                  (%s, %s);
            """, (urlid, logid))
    return urlid


def remove_url(url):
    """
    Remove a URL from list
    @param url: unique URL string for all lists
    """
    # get ids
    urlid = run_sql("""SELECT id
                       FROM lnkADMINURL
                       WHERE url=%s
                    """, (url, ))[0][0]
    logids = run_sql("""SELECT log.id
                        FROM lnkLOG log
                        JOIN lnkADMINURLLOG url_log
                          ON log.id=url_log.id_lnkLOG
                        WHERE url_log.id_lnkADMINURL=%s
                    """, (urlid, ))
    # delete url and url log
    run_sql("""DELETE FROM lnkADMINURL
               WHERE id=%s;
               DELETE FROM lnkADMINURLLOG
               WHERE id_lnkADMINURL=%s
            """, (urlid, urlid))
    # delete log
    for logid in logids:
        run_sql("""DELETE FROM lnkLOG
                   WHERE id=%s
                """, (logid[0], ))


def get_urls_and_titles(title_status=None):
    """
    Get URLs and their corresponding title
    @param old_new: of CFG_WEBLINKBACK_PAGE_TITLE_STATUS or None
    @return ((url, title, manual_set),...), all rows of the table if None
    """

    top_query = """SELECT url, title, manual_set, broken_count
                      FROM lnkENTRYURLTITLE
                   WHERE
                """

    where_sql = ""

    if title_status == CFG_WEBLINKBACK_PAGE_TITLE_STATUS['NEW']:
        where_sql = " title='' AND manual_set=0 AND"
    elif title_status == CFG_WEBLINKBACK_PAGE_TITLE_STATUS['OLD']:
        where_sql = " title<>'' AND manual_set=0 AND"
    elif title_status == CFG_WEBLINKBACK_PAGE_TITLE_STATUS['MANUALLY_SET']:
        where_sql = " manual_set=1 AND"

    where_sql += " broken=0"

    return run_sql(top_query + where_sql)


def update_url_title(url, title):
    """
    Update the corresponding title of a URL
    @param url: URL
    @param title: new title
    """
    run_sql("""UPDATE lnkENTRYURLTITLE
                  SET title=%s,
                      manual_set=0,
                      broken_count=0,
                      broken=0
                  WHERE url=%s
            """, (title, url))


def remove_url_title(url):
    """
    Remove URL title
    @param url: URL
    """
    run_sql("""DELETE FROM lnkENTRYURLTITLE
               WHERE url=%s
            """, (url, ))


def set_url_broken(url):
    """
    Set URL broken
    @param url: URL
    """
    linkbackids = run_sql("""SELECT id
                             FROM lnkENTRY
                             WHERE origin_url=%s
                          """, (url, ))
    run_sql("""UPDATE lnkENTRYURLTITLE
                  SET title=%s,
                      broken=1
                  WHERE url=%s
            """, (CFG_WEBLINKBACK_STATUS['BROKEN'], url))
    # update all linkbacks
    for linkbackid in linkbackids:
        update_linkback_status(linkbackid[0], CFG_WEBLINKBACK_STATUS['BROKEN'])


def get_url_title(url):
    """
    Get URL title or URL if title does not exist (empty string)
    @param url: URL
    @return title or URL if titles does not exist (empty string)
    """
    title = run_sql("""SELECT title
                       FROM lnkENTRYURLTITLE
                       WHERE url=%s and title<>"" and broken=0
                    """, (url, ))

    res = url
    if len(title) != 0:
        res = title[0][0]

    return xml_entities_to_utf8(res)


def increment_broken_count(url):
    """
    Increment broken count a URL
    @param url: URL
    """
    run_sql("""UPDATE lnkENTRYURLTITLE
                  SET broken_count=broken_count+1
                  WHERE url=%s
            """, (url, ))


def remove_linkback(linkbackid):
    """
    Remove a linkback database
    @param linkbackid: unique URL string for all lists
    """
    # get ids
    logids = run_sql("""SELECT log.id
                        FROM lnkLOG log
                        JOIN lnkENTRYLOG entry_log
                          ON log.id=entry_log.id_lnkLOG
                        WHERE entry_log.id_lnkENTRY=%s
                    """, (linkbackid, ))
    # delete linkback entry and entry log
    run_sql("""DELETE FROM lnkENTRY
               WHERE id=%s;
               DELETE FROM lnkENTRYLOG
               WHERE id_lnkENTRY=%s
            """, (linkbackid, linkbackid))
    # delete log
    for logid in logids:
        run_sql("""DELETE FROM lnkLOG
                   WHERE id=%s
                """, (logid[0], ))
