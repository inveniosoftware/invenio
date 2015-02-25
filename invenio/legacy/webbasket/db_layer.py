# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

""" Database related functions for webbasket module """

__revision__ = "$Id$"

from zlib import decompress
from zlib import compress
from six import iteritems
from time import localtime

from invenio.base.globals import cfg
from invenio.utils.text import encode_for_xml

from invenio.legacy.dbquery import run_sql
from invenio.modules.comments.api import get_reply_order_cache_data
from invenio.config import CFG_SITE_URL
from invenio.utils.date import convert_datestruct_to_datetext
from invenio.legacy.websession.websession_config import CFG_WEBSESSION_USERGROUP_STATUS
from invenio.legacy.search_engine import get_fieldvalues

########################### Table of contents ################################
#
# NB. functions preceeded by a star use usergroup table
#
# 1. General functions
#    - count_baskets
#    - check_user_owns_basket
#    - get_max_user_rights_on_basket
#
# 2. Personal baskets
#    - get_personal_baskets_info_for_topic
#    - get_all_personal_basket_ids_and_names_by_topic
#    - get_all_personal_baskets_names
#    - get_basket_name
#    - is_personal_basket_valid
#    - is_topic_valid
#    - get_basket_topic
#    - get_personal_topics_infos
#    - rename_basket
#    - rename_topic
#    - move_baskets_to_topic
#    - delete_basket
#    - create_basket
#
# 3. Actions on baskets
#    - get_basket_record
#    - get_basket_content
#    - get_basket_item
#    - get_basket_item_title_and_URL
#    - share_basket_with_group
#    - update_rights
#    - move_item
#    - delete_item
#    - add_to_basket
#    - get_external_records_by_collection
#    - store_external_records
#    - store_external_urls
#    - store_external_source
#    - get_external_colid_and_url
#
# 4. Group baskets
#    - get_group_basket_infos
#    - get_group_name
#    - get_all_group_basket_ids_and_names_by_group
#    - (*) get_all_group_baskets_names
#    - is_shared_to
#
# 5. External baskets (baskets user has subscribed to)
#    - get_external_baskets_infos
#    - get_external_basket_info
#    - get_all_external_basket_ids_and_names
#    - count_external_baskets
#    - get_all_external_baskets_names
#
# 6. Public baskets (interface to subscribe to baskets)
#    - get_public_basket_infos
#    - get_public_basket_info
#    - get_basket_general_infos
#    - get_basket_owner_id
#    - count_public_baskets
#    - get_public_baskets_list
#    - is_basket_public
#    - subscribe
#    - unsubscribe
#    - is_user_subscribed_to_basket
#    - count_subscribers
#    - (*) get_groups_subscribing_to_basket
#    - get_rights_on_public_basket
#
# 7. Annotating
#    - get_notes
#    - get_note
#    - save_note
#    - delete_note
#    - note_belongs_to_item_in_basket_p
#
# 8. Usergroup functions
#    - (*) get_group_infos
#    - count_groups_user_member_of
#    - (*) get_groups_user_member_of
#
# 9. auxilliary functions
#    - __wash_sql_count
#    - __decompress_last
#    - create_pseudo_record
#    - prettify_url

########################## General functions ##################################

def count_baskets(uid):
    """Return (nb personal baskets, nb group baskets, nb external
    baskets) tuple for given user"""
    query1 = "SELECT COUNT(id) FROM bskBASKET WHERE id_owner=%s"
    res1 = run_sql(query1, (int(uid),))
    personal = __wash_sql_count(res1)
    query2 = """SELECT count(ugbsk.id_bskbasket)
                FROM usergroup_bskBASKET ugbsk LEFT JOIN user_usergroup uug
                                               ON ugbsk.id_usergroup=uug.id_usergroup
                WHERE uug.id_user=%s AND uug.user_status!=%s
                GROUP BY ugbsk.id_usergroup"""
    params = (int(uid), CFG_WEBSESSION_USERGROUP_STATUS['PENDING'])
    res2 = run_sql(query2, params)
    if len(res2):
        groups = reduce(lambda x, y: x + y, map(lambda x: x[0], res2))
    else:
        groups = 0
    external = count_external_baskets(uid)
    return (personal, groups, external)

def check_user_owns_baskets(uid, bskids):
    """ Return 1 if user is owner of every basket in list bskids"""
    if not((type(bskids) is list) or (type(bskids) is tuple)):
        bskids = [bskids]
    query = """SELECT id_owner FROM bskBASKET WHERE %s GROUP BY id_owner"""
    sep = ' OR '
    query %= sep.join(['id=%s'] * len(bskids))
    res = run_sql(query, tuple(bskids))
    if len(res)==1 and int(res[0][0])==uid:
        return 1
    else:
        return 0

def get_max_user_rights_on_basket(uid, bskid):
    """Return the max rights a user has on this basket"""
    query_owner = "SELECT count(id_owner) FROM bskBASKET WHERE id_owner=%s and id=%s"
    params_owner = (int(uid), int(bskid))
    res = run_sql(query_owner, params_owner)
    if res and res[0][0]:
        # if this user is owner of this baskets he can do anything he wants.
        return cfg['CFG_WEBBASKET_SHARE_LEVELS']['MANAGE']
    # not owner => group member ?
    query_group_baskets = """
    SELECT share_level
    FROM user_usergroup AS ug LEFT JOIN usergroup_bskBASKET AS ub
                              ON ug.id_usergroup=ub.id_usergroup
    WHERE ug.id_user=%s AND ub.id_bskBASKET=%s AND NOT(ub.share_level='NO') AND ug.user_status!=%s
    """
    params_group_baskets = (int(uid), int(bskid), CFG_WEBSESSION_USERGROUP_STATUS['PENDING'])
    res = run_sql(query_group_baskets, params_group_baskets)
    group_index = None
    if res:
        try:
            group_index = cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(res[0][0])
        except:
            return None
    # public basket ?
    query_public_baskets = """
    SELECT share_level
    FROM usergroup_bskBASKET
    WHERE id_usergroup=0 AND id_bskBASKET=%s
    """
    public_index = None
    res = run_sql(query_public_baskets, (int(bskid),))
    if res:
        try:
            public_index = cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(res[0][0])
        except:
            return None
    if group_index or public_index:
        if group_index > public_index:
            return cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'][group_index]
        else:
            return cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'][public_index]
    return None

########################### Personal baskets ##################################

def get_personal_baskets_info_for_topic(uid, topic):
    """Return information about every basket that belongs to the given user and topic."""

    query = """ SELECT      bsk.id,
                            bsk.name,
                            DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                            bsk.nb_views,
                            count(rec.id_bibrec_or_bskEXTREC),
                            DATE_FORMAT(max(rec.date_added), '%%Y-%%m-%%d %%H:%%i:%%s')
                FROM        user_bskBASKET AS ubsk
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=ubsk.id_bskBASKET
                    AND     bsk.id_owner=%s
                LEFT JOIN   bskREC AS rec
                    ON      rec.id_bskBASKET=bsk.id
                WHERE       ubsk.id_user=%s
                AND         ubsk.topic=%s
                GROUP BY    bsk.id
                ORDER BY    bsk.name"""

    params = (uid, uid, topic)

    res = run_sql(query, params)

    return res

def get_all_user_personal_basket_ids_by_topic(uid):
    """For a given user return all their personal basket ids grouped by topic."""

    query = """ SELECT      ubsk.topic,
                            GROUP_CONCAT(bsk.id)
                FROM        user_bskBASKET AS ubsk
                JOIN        bskBASKET AS bsk
                ON          ubsk.id_bskBASKET=bsk.id
                AND         ubsk.id_user=bsk.id_owner
                WHERE       bsk.id_owner=%s
                GROUP BY    ubsk.topic
                ORDER BY    ubsk.topic"""
    params = (uid,)
    res = run_sql(query, params)

    return res

def get_all_personal_baskets_names(uid):
    """ for a given user, returns every basket he is owner of
    returns list of tuples: (bskid, bsk_name, topic)
    """
    query = """
    SELECT bsk.id,
           bsk.name,
           ubsk.topic
    FROM user_bskBASKET ubsk JOIN bskBASKET bsk
                             ON ubsk.id_bskBASKET=bsk.id
                             AND ubsk.id_user=bsk.id_owner
    WHERE bsk.id_owner=%s
    ORDER BY ubsk.topic
    """
    params = (int(uid),)
    return run_sql(query, params)

def get_basket_name(bskid):
    """return the name of a given basket"""
    query = 'SELECT name FROM bskBASKET where id=%s'
    res = run_sql(query, (int(bskid), ))
    if res:
        return res[0][0]
    else:
        return ''

def is_personal_basket_valid(uid, bskid):
    """Check if the basked (bskid) belongs to user (uid) and is valid."""

    query = """ SELECT  id
                FROM    bskBASKET
                WHERE   id=%s
                AND     id_owner=%s"""
    params = (bskid, uid)
    res = run_sql(query, params)

    return res

def is_topic_valid(uid, topic):
    """Check if the topic defined by user (uid) exists."""

    query = """ SELECT  distinct(topic)
                FROM    user_bskBASKET
                WHERE   topic=%s
                AND     id_user=%s"""
    params = (topic, uid)
    res = run_sql(query, params)

    return res

def get_basket_topic(uid, bskid):
    """Return the name of the topic this basket (bskid) belongs to."""

    query = """ SELECT  topic
                FROM    user_bskBASKET
                WHERE   id_bskBASKET=%s
                AND     id_user=%s"""
    params = (bskid,uid)
    res = run_sql(query, params)

    return res

def get_personal_topics_infos(uid):
    """
    Get the list of every topic user has defined,
    and the number of baskets in each topic
    @param uid: user id (int)
    @return: a list of tuples (topic name, nb of baskets)
    """
    query = """SELECT topic, count(b.id)
               FROM   user_bskBASKET ub JOIN bskBASKET b
                                        ON ub.id_bskBASKET=b.id AND
                                           b.id_owner=ub.id_user
               WHERE  ub.id_user=%s
               GROUP BY topic
               ORDER BY topic"""
    uid = int(uid)
    res = run_sql(query, (uid,))
    return res

def get_basket_ids_and_names(bskids, limit=0):
    """For the given basket ids, return their ids and names,
    ordered by basket name.
    If 'limit' is greater than 0, limit the number of results returned."""

    if not((type(bskids) is list) or (type(bskids) is tuple)):
        bskids = [bskids]

    query = """ SELECT      bsk.id,
                            bsk.name
                FROM        bskBASKET AS bsk
                WHERE       %s
                ORDER BY    bsk.name
                %s"""
    sep = ' OR '
    query %= (sep.join(['id=%s'] * len(bskids)), limit and 'LIMIT %i' % limit or '')

    params = tuple(bskids)

    res = run_sql(query, params)

    return res

def rename_basket(bskid, new_name):
    """Rename basket to new_name"""
    run_sql("UPDATE bskBASKET SET name=%s WHERE id=%s", (new_name, bskid))

def rename_topic(uid, old_topic, new_topic):
    """Rename topic to new_topic """
    res = run_sql("UPDATE user_bskBASKET SET topic=%s WHERE id_user=%s AND topic=%s",
                  (new_topic, uid, old_topic))
    return res

def move_baskets_to_topic(uid, bskids, new_topic):
    """Move given baskets to another topic"""
    if not((type(bskids) is list) or (type(bskids) is tuple)):
        bskids = [bskids]
    query = "UPDATE user_bskBASKET SET topic=%s WHERE id_user=%s AND ("
    query += ' OR '.join(['id_bskBASKET=%s'] * len(bskids))
    query += ")"
    params = (new_topic, uid) + tuple(bskids)
    res = run_sql(query, params)
    return res

def delete_basket(bskid):
    """Delete given basket."""

    # TODO: check if any alerts are automaticly adding items to the given basket.
    bskid = int(bskid)

    query1 = "DELETE FROM bskBASKET WHERE id=%s"
    res = run_sql(query1, (bskid,))

    query2A = "SELECT id_bibrec_or_bskEXTREC FROM bskREC WHERE id_bskBASKET=%s"
    local_and_external_ids = run_sql(query2A, (bskid,))
    external_ids = [local_and_external_id[0] for local_and_external_id in \
                    local_and_external_ids if local_and_external_id[0]<0]
    for external_id in external_ids:
        delete_item(bskid=bskid, recid=external_id, update_date_modification=False)

    query2B = "DELETE FROM bskREC WHERE id_bskBASKET=%s"
    run_sql(query2B, (bskid,))

    query3 = "DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET=%s"
    run_sql(query3, (bskid,))

    query4 = "DELETE FROM user_bskBASKET WHERE id_bskBASKET=%s"
    run_sql(query4, (bskid,))

    query5 = "DELETE FROM usergroup_bskBASKET WHERE id_bskBASKET=%s"
    run_sql(query5, (bskid,))

    query6 = "DELETE FROM user_query_basket WHERE id_basket=%s"
    run_sql(query6, (bskid,))

    return int(res)

def create_basket(uid, basket_name, topic):
    """Create new basket for given user in given topic"""
    now = convert_datestruct_to_datetext(localtime())
    id_bsk = run_sql("""INSERT INTO bskBASKET (id_owner, name, date_modification)
                        VALUES                (%s, %s, %s)""",
                     (uid, basket_name, now))
    run_sql("""INSERT INTO user_bskBASKET (id_user, id_bskBASKET, topic)
               VALUES                     (%s, %s, %s)""",
            (uid, id_bsk, topic))
    return id_bsk

def get_all_items_in_user_personal_baskets(uid,
                                           topic="",
                                           format='hb'):
    """For the specified user, return all the items in their personal baskets,
    grouped by basket if local or as a list if external.
    If topic is set, return only that topic's items."""

    if topic:
        topic_clause = """AND     ubsk.topic=%s"""
        params_local = (uid, uid, topic)
        params_external = (uid, uid, topic, format)
    else:
        topic_clause = ""
        params_local = (uid, uid)
        params_external = (uid, uid, format)

    query_local = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            ubsk.topic,
                            GROUP_CONCAT(rec.id_bibrec_or_bskEXTREC)
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                    AND     bsk.id_owner=%%s
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ubsk.id_user=%%s
                    %s
                WHERE       rec.id_bibrec_or_bskEXTREC > 0
                GROUP BY    rec.id_bskBASKET""" % (topic_clause,)

    res_local = run_sql(query_local, params_local)

    query_external = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            ubsk.topic,
                            rec.id_bibrec_or_bskEXTREC,
                            ext.value
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                    AND     bsk.id_owner=%%s
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ubsk.id_user=%%s
                    %s
                JOIN        bskEXTFMT AS ext
                    ON      ext.id_bskEXTREC=-rec.id_bibrec_or_bskEXTREC
                    AND     ext.format=%%s
                WHERE       rec.id_bibrec_or_bskEXTREC < 0
                ORDER BY    rec.id_bskBASKET""" % (topic_clause,)

    res_external = run_sql(query_external, params_external)

    return (res_local, res_external)

def get_all_items_in_user_personal_baskets_by_matching_notes(uid,
                                                             topic="",
                                                             p=""):
    """For the specified user, return all the items in their personal baskets
    matching their notes' titles and bodies, grouped by basket.
    If topic is set, return only that topic's items."""

    p = p and '%' + p + '%' or '%'

    if topic:
        topic_clause = """AND     ubsk.topic=%s"""
        params = (uid, uid, topic, p, p)
    else:
        topic_clause = ""
        params = (uid, uid, p, p)

    query = """ SELECT      notes.id_bskBASKET,
                            bsk.name,
                            ubsk.topic,
                            GROUP_CONCAT(DISTINCT(notes.id_bibrec_or_bskEXTREC))
                FROM        bskRECORDCOMMENT AS notes
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=notes.id_bskBASKET
                    AND     bsk.id_owner=%%s
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=notes.id_bskBASKET
                    AND     ubsk.id_user=%%s
                    %s
                WHERE       notes.title like %%s
                OR          notes.body like %%s
                GROUP BY    notes.id_bskBASKET""" % (topic_clause,)

    res = run_sql(query, params)

    return res

def get_all_user_topics(uid):
    """Return a list of the user's topics."""

    query = """ SELECT      ubsk.topic
                FROM        bskBASKET AS bsk
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=bsk.id
                    AND     ubsk.id_user=bsk.id_owner
                WHERE       bsk.id_owner=%s
                GROUP BY    ubsk.topic"""
    params = (uid,)
    res = run_sql(query, params)
    return res

########################## Actions on baskets #################################

def get_basket_record(bskid, recid, format='hb'):
    """get record recid in basket bskid
    """
    if recid < 0:
        rec_table = 'bskEXTREC'
        format_table = 'bskEXTFMT'
        id_field = 'id_bskEXTREC'
        sign = '-'
    else:
        rec_table = 'bibrec'
        format_table = 'bibfmt'
        id_field = 'id_bibrec'
        sign = ''
    query = """
    SELECT DATE_FORMAT(record.creation_date, '%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s'),
           DATE_FORMAT(record.modification_date, '%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s'),
           DATE_FORMAT(bskREC.date_added, '%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s'),
           user.nickname,
           count(cmt.id_bibrec_or_bskEXTREC),
           DATE_FORMAT(max(cmt.date_creation), '%%%%Y-%%%%m-%%%%d %%%%H:%%%%i:%%%%s'),
           fmt.value

    FROM bskREC LEFT JOIN user
                ON bskREC.id_user_who_added_item=user.id
                LEFT JOIN bskRECORDCOMMENT cmt
                ON bskREC.id_bibrec_or_bskEXTREC=cmt.id_bibrec_or_bskEXTREC
                LEFT JOIN %(rec_table)s record
                ON (%(sign)sbskREC.id_bibrec_or_bskEXTREC=record.id)
                LEFT JOIN %(format_table)s fmt
                ON (record.id=fmt.%(id_field)s)

    WHERE bskREC.id_bskBASKET=%%s AND
          bskREC.id_bibrec_or_bskEXTREC=%%s AND
          fmt.format=%%s

    GROUP BY bskREC.id_bibrec_or_bskEXTREC
    """ % {'rec_table': rec_table,
           'sign': sign,
           'format_table': format_table,
           'id_field':id_field}
    params = (int(bskid), int(recid), format)
    res = run_sql(query, params)
    if res:
        return __decompress_last(res[0])
    return ()

def get_basket_content(bskid, format='hb'):
    """Get all records for a given basket."""

    query = """ SELECT      rec.id_bibrec_or_bskEXTREC,
                            extrec.collection_id,
                            count(cmt.id_bibrec_or_bskEXTREC),
                            DATE_FORMAT(max(cmt.date_creation), '%%Y-%%m-%%d %%H:%%i:%%s'),
                            extern.value as ext_val,
                            intern.value as int_val,
                            rec.score

                FROM        bskREC AS rec

                LEFT JOIN   bskRECORDCOMMENT AS cmt
                    ON     (rec.id_bibrec_or_bskEXTREC=cmt.id_bibrec_or_bskEXTREC
                    AND     rec.id_bskBASKET=cmt.id_bskBASKET)

                LEFT JOIN   bskEXTFMT AS extern
                    ON     (-rec.id_bibrec_or_bskEXTREC=extern.id_bskEXTREC
                    AND     extern.format=%s)

                LEFT JOIN   bibfmt AS intern
                    ON     (rec.id_bibrec_or_bskEXTREC=intern.id_bibrec
                    AND     intern.format=%s)

                LEFT JOIN   bskEXTREC AS extrec
                    ON      extrec.id=-rec.id_bibrec_or_bskEXTREC

                WHERE       rec.id_bskBASKET=%s

                GROUP BY    rec.id_bibrec_or_bskEXTREC

                ORDER BY    rec.score"""

    params = (format, format, int(bskid))

    res = run_sql(query, params)

    if res:
        query2 = "UPDATE bskBASKET SET nb_views=nb_views+1 WHERE id=%s"
        run_sql(query2, (int(bskid),))
        return res
    return ()

def get_basket_item(bskid, recid, format='hb'):
    """Get item (recid) for a given basket."""

    query = """ SELECT      rec.id_bibrec_or_bskEXTREC,
                            extrec.collection_id,
                            count(cmt.id_bibrec_or_bskEXTREC),
                            DATE_FORMAT(max(cmt.date_creation), '%%Y-%%m-%%d %%H:%%i:%%s'),
                            extern.value as ext_val,
                            intern.value as int_val,
                            rec.score
                FROM        bskREC rec
                LEFT JOIN   bskRECORDCOMMENT cmt
                ON          (rec.id_bibrec_or_bskEXTREC=cmt.id_bibrec_or_bskEXTREC
                             AND
                             rec.id_bskBASKET=cmt.id_bskBASKET)
                LEFT JOIN   bskEXTFMT extern
                ON          (-rec.id_bibrec_or_bskEXTREC=extern.id_bskEXTREC
                             AND
                             extern.format=%s)
                LEFT JOIN   bibfmt intern
                ON          (rec.id_bibrec_or_bskEXTREC=intern.id_bibrec
                             AND
                             intern.format=%s)
                LEFT JOIN   bskEXTREC AS extrec
                    ON      extrec.id=-rec.id_bibrec_or_bskEXTREC
                WHERE       rec.id_bskBASKET=%s
                AND         rec.id_bibrec_or_bskEXTREC=%s
                GROUP BY    rec.id_bibrec_or_bskEXTREC
                ORDER BY    rec.score"""
    params = (format, format, bskid, recid)
    res = run_sql(query, params)
    if res:
        queryU = """UPDATE bskBASKET SET nb_views=nb_views+1 WHERE id=%s"""
        paramsU = (bskid,)
        run_sql(queryU, paramsU)
        score = res[0][6]
        query_previous = """SELECT      id_bibrec_or_bskEXTREC
                            FROM        bskREC
                            WHERE       id_bskBASKET=%s
                            AND         score<%s
                            ORDER BY    score   DESC
                            LIMIT 1"""
        params_previous = (bskid, score)
        res_previous = run_sql(query_previous, params_previous)
        query_next = """SELECT      id_bibrec_or_bskEXTREC
                        FROM        bskREC
                        WHERE       id_bskBASKET=%s
                        AND         score>%s
                        ORDER BY    score   ASC
                        LIMIT 1"""
        params_next = (bskid, score)
        res_next = run_sql(query_next, params_next)
        query_index = """   SELECT      COUNT(id_bibrec_or_bskEXTREC)
                            FROM        bskREC
                            WHERE       id_bskBASKET=%s
                            AND         score<=%s
                            ORDER BY    score"""
        params_index = (bskid, score)
        res_index = run_sql(query_index, params_index)
        res_index = __wash_sql_count(res_index)
        return (res[0], res_previous and res_previous[0][0] or 0, res_next and res_next[0][0] or 0, res_index)
    else:
        return ()

def get_basket_item_title_and_URL(recid):
    """
    Retrieves the title and URL for the specified item in the specified basket.

    @param bskid: The basked id
    @type bskid: int

    @param recid: The record (item) id
    @type recid: int

    @return: A tuple containing the title as a sting and the URL as a string.
    """

    if recid > 0:
        # This is a local record, we can easily retrieve the title using the
        # search engine's get_fieldvalues function and the MARC field and tag.
        title_list = get_fieldvalues(recid, '245___')
        # Check if the main title is always the first element in the list
        if title_list:
            title = title_list[0]
        else:
            title = ""
        url = '%s/record/%i' % (CFG_SITE_URL, recid)
    elif recid < 0:
        # This is an external record or item, use
        title = "This is an external record or item."
        url = '%s' % (CFG_SITE_URL,)

        query = """ SELECT  rec.collection_id,
                            rec.original_url,
                            fmt.value
                    FROM    bskEXTREC as rec,
                            bskEXTFMT as fmt
                    WHERE   rec.id=%s
                        AND fmt.id_bskEXTREC=%s
                        AND fmt.format='hb'"""
        params = (-recid, -recid)
        result = run_sql(query, params)
        if result:
            item = __decompress_last(result[0])
            collection = item[0]
            url = item[1]
            hb = item[2]
            if collection == 0:
                # This is an external item
                title = hb.split('\n',1)[0]
            elif collection > 0:
                # This is an external record from a hosted collection
                title = hb.split('</strong>',1)[0].split('<strong>')[-1]

    return (title, url)

def share_basket_with_group(bskid, group_id,
                            share_level=cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM']):
    """ Share basket bskid with group group_id with given share_level
    @param share_level:  see cfg['CFG_WEBBASKET_SHARE_LEVELS ']in webbasket_config
    """
    now = convert_datestruct_to_datetext(localtime())
    run_sql("""REPLACE INTO usergroup_bskBASKET
                 (id_usergroup, id_bskBASKET, date_shared, share_level)
               VALUES (%s,%s,%s,%s)""",
            (group_id, bskid, now, str(share_level)))

def update_rights(bskid, group_rights):
    """update rights (permissions) for groups.
    @param bskid: basket id
    @param group_rights: dictionary of {group id: new rights}
    """
    now = convert_datestruct_to_datetext(localtime())
    query1 = """REPLACE INTO usergroup_bskBASKET
                       (id_usergroup, id_bskBASKET, date_shared, share_level)
                VALUES """ + \
                ', '.join(["(%s, %s, %s, %s)"] * len(group_rights.items()))

    params = ()
    for (group_id, share_level) in group_rights.items():
        params += (int(group_id), int(bskid), now, str(share_level))

    run_sql(query1, params)
    query2 = """DELETE FROM usergroup_bskBASKET WHERE share_level='NO'"""
    run_sql(query2)

def move_item(bskid, recid, direction):
    """Change score of an item in a basket"""
    bskid = int(bskid)
    query1 = """SELECT id_bibrec_or_bskEXTREC,
                       score
                FROM bskREC
                WHERE id_bskBASKET=%s
                ORDER BY score, date_added"""
    items = run_sql(query1, (bskid,))
    (recids, scores) = zip(*items)
    (recids, scores) = (list(recids), list(scores))
    if len(recids) and recid in recids:
        current_index = recids.index(recid)
        if direction == cfg['CFG_WEBBASKET_ACTIONS']['UP']:
            switch_index = 0
            if current_index != 0:
                switch_index = current_index -1
        else:
            switch_index = len(recids) - 1
            if current_index != len(recids)-1:
                switch_index = current_index + 1
        query2 = """UPDATE bskREC
                    SET score=%s
                    WHERE id_bskBASKET=%s AND id_bibrec_or_bskEXTREC=%s"""
        res1 = run_sql(query2, (scores[switch_index], bskid, recids[current_index]))
        res2 = run_sql(query2, (scores[current_index], bskid, recids[switch_index]))
        if res1 and res2:
            now = convert_datestruct_to_datetext(localtime())
            query3 = "UPDATE bskBASKET SET date_modification=%s WHERE id=%s"
            params3 = (now, int(bskid))
            run_sql(query3, params3)

def delete_item(bskid, recid, update_date_modification=True):
    """Remove item recid from basket bskid"""

    if recid < 0:
        query0A = "select count(id_bskBASKET) from bskREC where id_bibrec_or_bskEXTREC=%s" % (int(recid))
        ncopies = run_sql(query0A)
        if ncopies and ncopies[0][0]<=1:
            # uncomment the following 5 lines and comment the following 2 to delete cached records
            # only for external sources and not for external records
            #query0B = "SELECT collection_id FROM bskEXTREC WHERE id=%s" % (-int(recid))
            #colid = run_sql(query0B)
            #if colid and colid[0][0]==0:
                #query0C = "DELETE from bskEXTFMT WHERE id_bskEXTREC=%s" % (-int(recid))
                #run_sql(query0C)
            # the following two lines delete cached external records. We could keep them if we find
            # a way to reuse them in case the external records are added again in the future.
            query0D = "DELETE from bskEXTFMT WHERE id_bskEXTREC=%s" % (-int(recid))
            run_sql(query0D)
            query0E = "DELETE from bskEXTREC WHERE id=%s" % (-int(recid))
            run_sql(query0E)
    query_notes = "DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET=%s AND id_bibrec_or_bskEXTREC=%s"
    run_sql(query_notes, (bskid, recid,))
    query1 = "DELETE from bskREC WHERE id_bskBASKET=%s AND id_bibrec_or_bskEXTREC=%s"
    params1 = (int(bskid), int(recid))
    res = run_sql(query1, params1)
    if update_date_modification and res:
        now = convert_datestruct_to_datetext(localtime())
        query2 = "UPDATE bskBASKET SET date_modification=%s WHERE id=%s"
        params2 = (now, int(bskid))
        run_sql(query2, params2)
    return res

def add_to_basket(uid,
                  recids=[],
                  colid=0,
                  bskid=0,
                  es_title="",
                  es_desc="",
                  es_url=""):
    """Add items (recids) basket (bskid)."""
    if (recids or (colid == -1 and es_title and es_desc and es_url)) and bskid > 0:
        query_max_score = """   SELECT   MAX(score)
                                FROM     bskREC
                                WHERE    id_bskBASKET=%s"""
        params_max_score = (bskid,)
        res_max_score = run_sql(query_max_score, params_max_score)
        max_score = __wash_sql_count(res_max_score)
        if not max_score:
            # max_score == None actually means that the basket doesn't exist.
            # Maybe we should return 0 and inform the admin?
            max_score = 1

        if colid > 0:
            query_existing = """    SELECT  id,
                                            external_id
                                    FROM    bskEXTREC
                                    WHERE   %s
                                    AND     collection_id=%s"""
            sep_or = ' OR '
            query_existing %= (sep_or.join(['external_id=%s'] * len(recids)), colid)
            params_existing = tuple(recids)
            res_existing = run_sql(query_existing, params_existing)
            existing_recids = [int(external_ids_couple[1]) for external_ids_couple in res_existing]
            existing_ids = [int(ids[0]) for ids in res_existing]
            new_recids = [recid for recid in recids if int(recid) not in existing_recids]
            # sets approach
            #existing_recids = [ids[1] for ids in res_existing]
            #new_recids = list(set(recids)-set(existing_recids))
            if new_recids:
                query_new = """ INSERT INTO bskEXTREC (external_id,
                                                       collection_id,
                                                       creation_date,
                                                       modification_date)
                                VALUES """
                now = convert_datestruct_to_datetext(localtime())
                records = ["(%s, %s, %s, %s)"] * len(new_recids)
                query_new += ', '.join(records)
                params_new = ()
                for new_recid in new_recids:
                    params_new += (int(new_recid), colid, now, now)
                res_new = run_sql(query_new, params_new)
                recids = [-int(recid) for recid in existing_ids]
                recids.extend(range(-res_new,-(res_new+len(new_recids)),-1))
            else:
                recids = [-int(recid) for recid in existing_ids]
        elif colid < 0:
            query_external = """INSERT INTO bskEXTREC (collection_id,
                                                       original_url,
                                                       creation_date,
                                                       modification_date)
                                VALUES      (%s, %s, %s, %s)"""
            now = convert_datestruct_to_datetext(localtime())
            params_external = (colid, es_url, now, now)
            res_external = run_sql(query_external, params_external)
            recids = [-res_external]
            store_external_source(res_external, es_title, es_desc, es_url, 'xm')
            store_external_source(res_external, es_title, es_desc, es_url, 'hb')

        query_insert = """  INSERT IGNORE INTO  bskREC
                                                (id_bibrec_or_bskEXTREC,
                                                 id_bskBASKET,
                                                 id_user_who_added_item,
                                                 date_added,
                                                 score)
                            VALUES """
        if colid == 0 or (colid > 0 and not new_recids):
            now = convert_datestruct_to_datetext(localtime())
        records = ["(%s, %s, %s, %s, %s)"] * len(recids)
        query_insert += ', '.join(records)
        params_insert = ()
        i = 1
        for recid in recids:
            params_insert += (recid, bskid, uid, now, max_score + i)
            i += 1
        run_sql(query_insert, params_insert)

        query_update = """  UPDATE  bskBASKET
                            SET     date_modification=%s
                            WHERE   id=%s"""
        params_update = (now, bskid)
        run_sql(query_update, params_update)
        return recids
    return 0


def move_to_basket(uid,
                   recids=None,
                   old_bskid=0,
                   new_bskid=0,
                   update_date_modification=True):
    """ Move items (recids) from basket (old_bskid) to basket (new_bskid) """
    if (recids is not None) and len(recids) > 0:

        moved_recids = []

        for recid in recids:
            # Prevent duplication of items
            query = """ SELECT  '1'
                        FROM    bskREC
                        WHERE   id_bskBASKET=%s
                                AND
                                id_bibrec_or_bskEXTREC=%s
                    """
            params = (int(new_bskid), int(recid))

            res = run_sql(query, params)

            if len(res) == 0:
                # Change the item's pointer to basket
                query = """ UPDATE  bskREC
                            SET     id_bskBASKET=%s,
                                    id_user_who_added_item=%s
                            WHERE   id_bskBASKET=%s
                                    AND id_bibrec_or_bskEXTREC=%s
                        """

                params = (int(new_bskid), int(uid), int(old_bskid), int(recid))
                res = run_sql(query, params)

                moved_recids.append(int(recid))

        # Update 'modification date'
        if len(moved_recids) > 0 and update_date_modification:
            now = convert_datestruct_to_datetext(localtime())
            query = "UPDATE bskBASKET SET date_modification=%s WHERE id=%s"

            params = (now, int(old_bskid))
            run_sql(query, params)

            params = (now, int(new_bskid))
            run_sql(query, params)

    return moved_recids


def add_to_many_baskets(uid, recids=[], colid=0, bskids=[], es_title="", es_desc="", es_url=""):
    """Add items recids to every basket in bskids list."""
    if (len(recids) or colid == -1) and len(bskids):
        query1 = """SELECT   id_bskBASKET,
                             max(score)
                    FROM     bskREC
                    WHERE    %s
                    GROUP BY id_bskBASKET"""
        bskids = [bskid for bskid in bskids if int(bskid) >= 0]
        sep_or = ' OR '
        query1 %= sep_or.join(['id_bskBASKET=%s'] * len(bskids))
        bsks = dict.fromkeys(bskids, 0)
        params = tuple(bskids)
        bsks.update(dict(run_sql(query1, params)))

        if colid > 0:
            query2A = """SELECT id,
                                external_id
                         FROM   bskEXTREC
                         WHERE  %s
                         AND    collection_id=%s"""
            query2A %= (sep_or.join(['external_id=%s'] * len(recids)), colid)
            params2A = tuple(recids)
            res2A = run_sql(query2A, params2A)
            existing_recids = [int(external_ids_couple[1]) for external_ids_couple in res2A]
            existing_ids = [int(ids[0]) for ids in res2A]
            new_recids = [recid for recid in recids if int(recid) not in existing_recids]
            # sets approach
            #existing_recids = [ids[1] for ids in res2A]
            #new_recids = list(set(recids)-set(existing_recids))
            if new_recids:
                query2B = """INSERT
                             INTO   bskEXTREC
                                   (external_id,
                                    collection_id,
                                    creation_date,
                                    modification_date)
                             VALUES """
                now = convert_datestruct_to_datetext(localtime())
                records = ["(%s, %s, %s, %s)"] * len(new_recids)
                query2B += ', '.join(records)
                params2B = ()
                for new_recid in new_recids:
                    params2B += (int(new_recid), colid, now, now)
                res = run_sql(query2B, params2B)
                recids = [-int(recid) for recid in existing_ids]
                recids.extend(range(-res,-(res+len(new_recids)),-1))
            else:
                recids = [-int(recid) for recid in existing_ids]
        elif colid < 0:
            query2C = """INSERT
                        INTO bskEXTREC
                            (collection_id,
                            original_url,
                            creation_date,
                            modification_date)
                        VALUES (%s, %s, %s, %s)"""
            now = convert_datestruct_to_datetext(localtime())
            params = (colid, es_url, now, now)
            res = run_sql(query2C, params)
            recids = [-res]
            store_external_source(res, es_title, es_desc, es_url, 'xm')
            store_external_source(res, es_title, es_desc, es_url, 'hb')

        query2 = """INSERT IGNORE
                    INTO   bskREC
                           (id_bibrec_or_bskEXTREC,
                            id_bskBASKET,
                            id_user_who_added_item,
                            date_added,
                            score)
                    VALUES """
        if colid == 0 or (colid > 0 and not new_recids):
            now = convert_datestruct_to_datetext(localtime())
        records = ["(%s, %s, %s, %s, %s)"] * (len(recids) * len(bsks.items()))
        query2 += ', '.join(records)
        params = ()
        for (bskid, max_score) in bsks.items():
            i = 1
            for recid in recids:
                params += (int(recid), int(bskid), int(uid), now, int(max_score) + i)
                i += 1
        run_sql(query2, params)

        query3 = """UPDATE bskBASKET
                    SET    date_modification=%s
                    WHERE """
        query3 += sep_or.join(["id=%s"] * len(bskids))
        params = (now,) + tuple(bskids)
        run_sql(query3, params)
        return len(bskids)
    return 0

def get_external_records_by_collection(recids):
    """Get the selected recids, both local and external, grouped by collection."""

    if recids:
        query = """ SELECT      GROUP_CONCAT(id),
                                GROUP_CONCAT(external_id),
                                collection_id
                    FROM        bskEXTREC
                    WHERE       %s
                    GROUP BY    collection_id"""

        recids = [-recid for recid in recids]
        sep_or = ' OR '
        query %= sep_or.join(['id=%s'] * len(recids))
        params = tuple(recids)
        res = run_sql(query,params)
        return res
    return 0

def get_external_records(recids, of="hb"):
    """Get formatted external records from the database."""

    if recids:
        query = """ SELECT  rec.collection_id,
                            fmt.id_bskEXTREC,
                            fmt.value
                    FROM    bskEXTFMT AS fmt
                    JOIN    bskEXTREC AS rec
                        ON  rec.id=fmt.id_bskEXTREC
                    WHERE   format=%%s
                    AND     ( %s )"""
        recids = [-recid for recid in recids]
        sep_or = ' OR '
        query %= sep_or.join(['id_bskEXTREC=%s'] * len(recids))
        params = [of]
        params.extend(recids)
        params = tuple(params)
        res = run_sql(query,params)
        return res
    return ()

def store_external_records(records, of="hb"):
    """Store formatted external records to the database."""

    if records:
        query = """INSERT
                    INTO bskEXTFMT
                        (id_bskEXTREC,
                        format,
                        last_updated,
                        value)
                    VALUES """
        now = convert_datestruct_to_datetext(localtime())
        formatted_records = ["(%s, %s, %s, %s)"] * len(records)
        query += ', '.join(formatted_records)
        params = ()
        for record in records:
            params += (record[0], of, now, compress(record[1]))
        run_sql(query,params)

def store_external_urls(ids_urls):
    """Store original urls for external records to the database."""

    #for id_url in iteritems(ids_urls):
    for id_url in ids_urls:
        query = """UPDATE
                    bskEXTREC
                    SET original_url=%s
                    WHERE id=%s"""
        params = (id_url[1], id_url[0])
        run_sql(query,params)

def store_external_source(es_id, es_title, es_desc, es_url, of="hb"):
    """Store formatted external sources to the database."""

    if es_id and es_title and es_desc:
        query = """INSERT INTO  bskEXTFMT
                                (id_bskEXTREC,
                                 format,
                                 last_updated,
                                 value)
                    VALUES      (%s, %s, %s, %s)"""
        now = convert_datestruct_to_datetext(localtime())
        value = create_pseudo_record(es_title, es_desc, es_url, of)
        params = (es_id, of, now, compress(value))
        run_sql(query,params)

def get_external_colid_and_url(recid):
    """Get the collection id and original url for an external record."""

    if recid:
        query = """SELECT
                    collection_id,
                    original_url
                    FROM bskEXTREC
                    WHERE id=%s"""
        params = (-recid,)
        res = run_sql(query,params)
        if res:
            return res
        else:
            return 0

############################ Group baskets ####################################

def get_group_baskets_info_for_group(grpid):
    """Return information about every basket that belongs to the given group,
    provided the user is its manager or a member of it."""

    if not grpid:
        return ()

    query = """ SELECT      bsk.id,
                            bsk.name,
                            DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                            bsk.nb_views,
                            COUNT(rec.id_bibrec_or_bskEXTREC),
                            DATE_FORMAT(max(rec.date_added), '%%Y-%%m-%%d %%H:%%i:%%s'),
                            ugbsk.share_level,
                            bsk.id_owner
                FROM        usergroup_bskBASKET AS ugbsk
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=ugbsk.id_bskBASKET
                LEFT JOIN   bskREC AS rec
                    ON      rec.id_bskBASKET=bsk.id
                WHERE       ugbsk.id_usergroup=%s
                AND         ugbsk.share_level!='NO'
                GROUP BY    bsk.id
                ORDER BY    bsk.name"""

    params = (grpid,)

    res = run_sql(query, params)

    return res

def get_group_name(gid):
    """Given its id return the group's name."""

    query = """ SELECT  name
                FROM    usergroup
                WHERE   id=%s"""
    params = (gid,)
    res = run_sql(query, params)

    return res

def get_all_user_group_basket_ids_by_group(uid):
    """For a given user return all their group basket ids grouped by group."""

    query = """ SELECT      ug.id,
                            ug.name,
                            GROUP_CONCAT(ugbsk.id_bskBASKET)
                FROM        usergroup AS ug
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_usergroup=ug.id
                JOIN        bskBASKET AS bsk
                    ON      ugbsk.id_bskBASKET=bsk.id
                JOIN        user_usergroup AS uug
                    ON      ug.id=uug.id_usergroup
                    AND     uug.id_user=%s
                GROUP BY    ug.name
                ORDER BY    ug.name"""
    params = (uid,)
    res = run_sql(query, params)

    return res

def get_all_user_group_basket_ids_by_group_with_add_rights(uid):
    """For a given user return all their group basket ids grouped by group.
    Return only the basket ids to which it is allowed to add records."""

    query = """ SELECT      ug.name,
                            GROUP_CONCAT(ugbsk.id_bskBASKET)
                FROM        usergroup AS ug
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_usergroup=ug.id
                    AND     ugbsk.share_level!='NO'
                    AND     ugbsk.share_level!='RI'
                    AND     ugbsk.share_level!='RC'
                    AND     ugbsk.share_level!='AC'
                JOIN        bskBASKET AS bsk
                    ON      ugbsk.id_bskBASKET=bsk.id
                JOIN        user_usergroup AS uug
                    ON      ug.id=uug.id_usergroup
                    AND     uug.id_user=%s
                GROUP BY    ug.name
                ORDER BY    ug.name"""
    params = (uid,)
    res = run_sql(query, params)

    return res

def get_all_group_baskets_names(uid,
                                min_rights=cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT']):
    """For a given user returns every group baskets in which he can <min_rights>
    return a list of tuples: (bskid, bsk_name, group_name)."""

    # TODO: This function is no longer used. Delete if necessary.
    uid = int(uid)
    try:
        min_rights_num = cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(min_rights)
    except ValueError:
        return ()
    groups = get_groups_user_member_of(uid)
    if groups:
        where_clause = '('
        where_clause += " OR ".join(["ugbsk.id_usergroup=%s"] * len(groups))
        where_clause += ') AND ('
        where_clause += " OR ".join(["ugbsk.share_level=%s"] * len(cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'][min_rights_num:]))
        where_clause += ")"
        query = """
        SELECT bsk.id,
               bsk.name,
               ug.name
        FROM usergroup ug JOIN usergroup_bskBASKET ugbsk
                          ON ug.id=ugbsk.id_usergroup
                          JOIN bskBASKET bsk
                          ON bsk.id=ugbsk.id_bskBASKET
        WHERE %s AND NOT(ugbsk.share_level='NO')
        ORDER BY ug.name""" % where_clause
        params = tuple([group_id for (group_id, dummy) in groups])
        params += tuple(cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'][min_rights_num:])
        return run_sql(query, params)
    return ()

def is_shared_to(bskids):
    """For each bskid in bskids get id of one of its group. Used to
    make distinction between private basket (no group), 'world' basket
    (0) or group basket (any int > 0)
    """
    if not((type(bskids) == list) or (type(bskids) == tuple)):
        bskids = [bskids]
    query = """SELECT b.id,
                      min(u.id_usergroup)
               FROM
                      bskBASKET b LEFT JOIN usergroup_bskBASKET u
                      ON (b.id=u.id_bskBASKET) """
    if len(bskids) != 0:
        query += " WHERE "
        query += " OR ".join(['b.id=%s'] * len(bskids))
    query += " GROUP BY b.id"
    params = tuple(bskids)
    res = run_sql(query, params)
    if res:
        return res
    return ()

def get_basket_share_level(bskid):
    """Get the minimum share level of the basket (bskid).
    Returns:
        None for personal baskets
        positive integet for group baskets
        0 for public baskets
    Will return 0 if the basket is both group and publicly shared."""

    query = """ SELECT      MIN(ugbsk.id_usergroup)
                FROM        bskBASKET AS bsk
                LEFT JOIN   usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=bsk.id
                WHERE       bsk.id=%s
                GROUP BY    bsk.id"""

    params = (bskid,)

    res = run_sql(query, params)

    return res

def get_all_items_in_user_group_baskets(uid,
                                        group=0,
                                        format='hb'):
    """For the specified user, return all the items in their group baskets,
    grouped by basket if local or as a list if external.
    If group is set, return only that group's items."""

    if group:
        group_clause = """AND     ugbsk.id_usergroup=%s"""
        params_local = (group, uid)
        params_external = (group, uid, format)
    else:
        group_clause = ""
        params_local = (uid,)
        params_external = (uid, format)

    query_local = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            uug.id_usergroup,
                            ug.name,
                            ugbsk.share_level,
                            GROUP_CONCAT(rec.id_bibrec_or_bskEXTREC)
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=rec.id_bskBASKET
                    %s
                JOIN        user_usergroup AS uug
                    ON      uug.id_usergroup=ugbsk.id_usergroup
                    AND     uug.id_user=%%s
                JOIN        usergroup AS ug
                    ON      ug.id=uug.id_usergroup
                WHERE       rec.id_bibrec_or_bskEXTREC > 0
                GROUP BY    rec.id_bskBASKET""" % (group_clause,)

    res_local = run_sql(query_local, params_local)

    query_external = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            uug.id_usergroup,
                            ug.name,
                            ugbsk.share_level,
                            rec.id_bibrec_or_bskEXTREC,
                            ext.value
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=rec.id_bskBASKET
                    %s
                JOIN        user_usergroup AS uug
                    ON      uug.id_usergroup=ugbsk.id_usergroup
                    AND     uug.id_user=%%s
                JOIN        usergroup AS ug
                    ON      ug.id=uug.id_usergroup
                JOIN        bskEXTFMT AS ext
                    ON      ext.id_bskEXTREC=-rec.id_bibrec_or_bskEXTREC
                    AND     ext.format=%%s
                WHERE       rec.id_bibrec_or_bskEXTREC < 0
                ORDER BY    rec.id_bskBASKET""" % (group_clause,)

    res_external = run_sql(query_external, params_external)

    return (res_local, res_external)

def get_all_items_in_user_group_baskets_by_matching_notes(uid,
                                                          group=0,
                                                          p=""):
    """For the specified user, return all the items in group personal baskets
    matching their notes' titles and bodies, grouped by basket.
    If topic is set, return only that topic's items."""

    p = p and '%' + p + '%' or '%'

    if group:
        group_clause = """AND     ugbsk.id_usergroup=%s"""
        params = (group, uid, p, p)
    else:
        group_clause = ""
        params = (uid, p, p)

    query = """ SELECT      notes.id_bskBASKET,
                            bsk.name,
                            uug.id_usergroup,
                            ug.name,
                            ugbsk.share_level,
                            GROUP_CONCAT(DISTINCT(notes.id_bibrec_or_bskEXTREC))
                FROM        bskRECORDCOMMENT AS notes
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=notes.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=notes.id_bskBASKET
                    AND     ugbsk.share_level IS NOT NULL
                    AND     ugbsk.share_level!='NO'
                    AND     ugbsk.share_level!='RI'
                    %s
                JOIN        user_usergroup AS uug
                    ON      uug.id_usergroup=ugbsk.id_usergroup
                    AND     uug.id_user=%%s
                JOIN        usergroup AS ug
                    ON      ug.id=uug.id_usergroup
                WHERE       notes.title like %%s
                OR          notes.body like %%s
                GROUP BY    notes.id_bskBASKET""" % (group_clause,)

    res = run_sql(query, params)

    return res

def is_group_basket_valid(uid, bskid):
    """Check if the basked (bskid) belongs to one of the groups the user (uid)
    is a member of and is valid."""

    query = """ SELECT  id
                FROM    bskBASKET AS bsk
                JOIN    usergroup_bskBASKET AS ugbsk
                    ON  ugbsk.id_bskBASKET=bsk.id
                JOIN    user_usergroup AS uug
                    ON  uug.id_usergroup=ugbsk.id_usergroup
                    AND uug.id_user=%s
                WHERE   id=%s"""
    params = (uid, bskid)
    res = run_sql(query, params)

    return res

def is_group_valid(uid, group):
    """Check if the group exists and the user is a member or manager."""

    query = """ SELECT  id_usergroup
                FROM    user_usergroup
                WHERE   id_usergroup=%s
                AND     id_user=%s"""
    params = (group, uid)
    res = run_sql(query, params)

    return res

def get_all_user_groups(uid):
    """Return a list of the groups the user is a member of or manages."""

    query = """ SELECT      ug.id,
                            ug.name
                FROM        user_usergroup AS uug
                JOIN        usergroup AS ug
                    ON      ug.id=uug.id_usergroup
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_usergroup=uug.id_usergroup
                WHERE       uug.id_user=%s
                GROUP BY    uug.id_usergroup"""
    params = (uid,)
    res = run_sql(query, params)
    return res

########################## External baskets ###################################

def get_external_baskets_infos(uid):
    """Get general informations about every external basket user uid has subscribed to."""
    query = """
    SELECT bsk.id,
           bsk.name,
           DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
           bsk.nb_views,
           count(rec.id_bibrec_or_bskEXTREC),
           DATE_FORMAT(max(rec.date_added), '%%Y-%%m-%%d %%H:%%i:%%s'),
           ugbsk.share_level
    FROM   bskBASKET bsk JOIN user_bskBASKET ubsk
                         ON (bsk.id=ubsk.id_bskBASKET AND ubsk.id_user=%s)
                         LEFT JOIN bskREC rec
                         ON (bsk.id=rec.id_bskBASKET)
                         LEFT JOIN usergroup_bskBASKET ugbsk
                         ON (ugbsk.id_bskBASKET=bsk.id AND ugbsk.id_usergroup=0)

    WHERE  bsk.id_owner!=%s

    GROUP BY bsk.id
    """
    uid = int(uid)
    params = (uid, uid)
    res = run_sql(query, params)
    if res:
        return res
    return ()

def get_external_basket_info(bskid):
    """"""

    query = """ SELECT      bsk.id,
                            bsk.name,
                            DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                            bsk.nb_views,
                            count(rec.id_bibrec_or_bskEXTREC),
                            DATE_FORMAT(max(rec.date_added), '%%Y-%%m-%%d %%H:%%i:%%s'),
                            ugbsk.share_level
                FROM        bskBASKET AS bsk
                LEFT JOIN   bskREC AS rec
                ON          bsk.id=rec.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                ON          bsk.id=ugbsk.id_bskBASKET
                AND         ugbsk.id_usergroup=0
                WHERE       id=%s"""
    params = (bskid,)
    res = run_sql(query, params)

    return res

def get_all_external_basket_ids_and_names(uid):
    """For a given user return all their external baskets
    (in tuples: (id, name, number_of_records))."""

    query = """ SELECT      bsk.id,
                            bsk.name,
                            count(rec.id_bibrec_or_bskEXTREC),
                            ugbsk.id_usergroup
                FROM        user_bskBASKET AS ubsk
                JOIN        bskBASKET AS bsk
                    ON      ubsk.id_bskBASKET=bsk.id
                    AND     ubsk.id_user!=bsk.id_owner
                LEFT JOIN   bskREC AS rec
                    ON      ubsk.id_bskBASKET=rec.id_bskBASKET
                LEFT JOIN   usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_usergroup=0
                    AND     ugbsk.id_bskBASKET=bsk.id
                WHERE       ubsk.id_user=%s
                GROUP BY    bsk.id
                ORDER BY    bsk.name"""
    params = (uid,)
    res = run_sql(query, params)

    return res

def count_external_baskets(uid):
    """Returns the number of external baskets the user is subscribed to."""

    query = """ SELECT      COUNT(ubsk.id_bskBASKET)
                FROM        user_bskBASKET ubsk
                LEFT JOIN   bskBASKET bsk
                    ON      (bsk.id=ubsk.id_bskBASKET AND ubsk.id_user=%s)
                WHERE       bsk.id_owner!=%s"""

    params = (int(uid), int(uid))

    res = run_sql(query, params)

    return __wash_sql_count(res)

def get_all_external_baskets_names(uid,
                                   min_rights=cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT']):

    """ for a given user returns every basket which he has subscribed to and in which
    he can <min_rights>
    return a list of tuples: (bskid, bsk_name)
    """
    uid = int(uid)
    try:
        min_rights_num = cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'].index(min_rights)
    except ValueError:
        return ()
    where_clause = ' AND ('
    for right in cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'][min_rights_num:-1]:
        where_clause += "ugbsk.share_level = '%s' OR " % right
    where_clause += "ugbsk.share_level = '%s')" % cfg['CFG_WEBBASKET_SHARE_LEVELS_ORDERED'][-1]
    query = """
    SELECT bsk.id,
           bsk.name
    FROM bskBASKET bsk JOIN usergroup_bskBASKET ugbsk
                       ON bsk.id=ugbsk.id_bskBASKET
                       JOIN user_bskBASKET ubsk
                       ON ubsk.id_bskBASKET=bsk.id
    WHERE ugbsk.id_usergroup=0 AND
          ubsk.id_user=%s AND
          NOT(bsk.id_owner=%s) AND
          NOT(ugbsk.share_level='NO')
    """ + where_clause

    params = (uid, uid)
    return run_sql(query, params)

def get_all_items_in_user_public_baskets(uid,
                                        format='hb'):
    """For the specified user, return all the items in the public baskets they
    are subscribed to, grouped by basket if local or as a list if external."""

    query_local = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            ugbsk.share_level,
                            GROUP_CONCAT(rec.id_bibrec_or_bskEXTREC)
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                    AND     bsk.id_owner!=%s
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ubsk.id_user=%s
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ugbsk.id_usergroup=0
                WHERE       rec.id_bibrec_or_bskEXTREC > 0
                GROUP BY    rec.id_bskBASKET"""

    params_local = (uid, uid)

    res_local = run_sql(query_local, params_local)

    query_external = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            ugbsk.share_level,
                            rec.id_bibrec_or_bskEXTREC,
                            ext.value
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                    AND     bsk.id_owner!=%s
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ubsk.id_user=%s
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ugbsk.id_usergroup=0
                JOIN        bskEXTFMT AS ext
                    ON      ext.id_bskEXTREC=-rec.id_bibrec_or_bskEXTREC
                    AND     ext.format=%s
                WHERE       rec.id_bibrec_or_bskEXTREC < 0
                ORDER BY    rec.id_bskBASKET"""

    params_external = (uid, uid, format)

    res_external = run_sql(query_external, params_external)

    return (res_local, res_external)

def get_all_items_in_user_public_baskets_by_matching_notes(uid,
                                                           p=""):
    """For the specified user, return all the items in the public baskets they
    are subscribed to, matching their notes' titles and bodies,
    grouped by basket"""

    p = p and '%' + p + '%' or '%'

    query = """ SELECT      notes.id_bskBASKET,
                            bsk.name,
                            ugbsk.share_level,
                            GROUP_CONCAT(DISTINCT(notes.id_bibrec_or_bskEXTREC))
                FROM        bskRECORDCOMMENT AS notes
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=notes.id_bskBASKET
                    AND     bsk.id_owner!=%s
                JOIN        user_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=notes.id_bskBASKET
                    AND     ubsk.id_user=%s
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=notes.id_bskBASKET
                    AND     ugbsk.id_usergroup=0
                    AND     ugbsk.share_level IS NOT NULL
                    AND     ugbsk.share_level!='NO'
                    AND     ugbsk.share_level!='RI'
                WHERE       notes.title like %s
                OR          notes.body like %s
                GROUP BY    notes.id_bskBASKET"""

    params = (uid, uid, p, p)

    res = run_sql(query, params)

    return res

def get_all_items_in_all_public_baskets(format='hb'):
    """Return all the items in all the public baskets,
    grouped by basket if local or as a list if external."""

    query_local = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            ugbsk.share_level,
                            GROUP_CONCAT(rec.id_bibrec_or_bskEXTREC)
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ugbsk.id_usergroup=0
                WHERE       rec.id_bibrec_or_bskEXTREC > 0
                GROUP BY    rec.id_bskBASKET"""

    res_local = run_sql(query_local)

    query_external = """
                SELECT      rec.id_bskBASKET,
                            bsk.name,
                            ugbsk.share_level,
                            rec.id_bibrec_or_bskEXTREC,
                            ext.value
                FROM        bskREC AS rec
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=rec.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=rec.id_bskBASKET
                    AND     ugbsk.id_usergroup=0
                JOIN        bskEXTFMT AS ext
                    ON      ext.id_bskEXTREC=-rec.id_bibrec_or_bskEXTREC
                    AND     ext.format=%s
                WHERE       rec.id_bibrec_or_bskEXTREC < 0
                ORDER BY    rec.id_bskBASKET"""

    params_external = (format,)

    res_external = run_sql(query_external, params_external)

    return (res_local, res_external)

def get_all_items_in_all_public_baskets_by_matching_notes(p=""):
    """Return all the items in all the public baskets matching
    their notes' titles and bodies, grouped by basket"""

    p = p and '%' + p + '%' or '%'

    query = """ SELECT      notes.id_bskBASKET,
                            bsk.name,
                            ugbsk.share_level,
                            GROUP_CONCAT(DISTINCT(notes.id_bibrec_or_bskEXTREC))
                FROM        bskRECORDCOMMENT AS notes
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=notes.id_bskBASKET
                JOIN        usergroup_bskBASKET AS ugbsk
                    ON      ugbsk.id_bskBASKET=notes.id_bskBASKET
                    AND     ugbsk.id_usergroup=0
                    AND     ugbsk.share_level IS NOT NULL
                    AND     ugbsk.share_level!='NO'
                    AND     ugbsk.share_level!='RI'
                WHERE       notes.title like %s
                OR          notes.body like %s
                GROUP BY    notes.id_bskBASKET"""

    params = (p, p)

    res = run_sql(query, params)

    return res

############################ Public access ####################################

def get_public_basket_infos(bskid):
    """return (id, name, date modification, nb of views, id of owner, nickname of owner, rights for public access)
    for a given basket"""
    basket = []
    query1 = """SELECT bsk.id,
                       bsk.name,
                       DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                       bsk.nb_views,
                       bsk.id_owner,
                       user.nickname
                FROM bskBASKET bsk LEFT JOIN user
                                   ON bsk.id_owner=user.id
                WHERE bsk.id=%s"""
    res1 = run_sql(query1, (int(bskid),))
    if len(res1):
        basket = list(res1[0])
        query2 = """SELECT share_level
                    FROM usergroup_bskBASKET
                    WHERE id_usergroup=0 and id_bskBASKET=%s"""
        res2 = run_sql(query2, (int(bskid),))
        if res2:
            basket.append(res2[0][0])
        else:
            basket.append(None)
    return basket

def get_public_basket_info(bskid):
    """Return information about a given public basket."""

    query = """ SELECT      bsk.id,
                            bsk.name,
                            bsk.id_owner,
                            DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                            bsk.nb_views,
                            COUNT(rec.id_bibrec_or_bskEXTREC),
                            GROUP_CONCAT(rec.id_bibrec_or_bskEXTREC),
                            ubsk.share_level
                FROM        bskBASKET AS bsk
                LEFT JOIN   bskREC AS rec
                    ON      rec.id_bskBASKET=bsk.id
                JOIN        usergroup_bskBASKET AS ubsk
                    ON      ubsk.id_bskBASKET=bsk.id
                    AND     ubsk.id_usergroup=0
                WHERE       bsk.id=%s
                GROUP BY    bsk.id;"""

    params = (bskid,)

    res = run_sql(query, params)

    return res

def get_basket_general_infos(bskid):
    """return information about a basket, suited for public access.
    @return: a (id, name, date of modification, nb of views, nb of records, id of owner) tuple
    """
    query = """SELECT bsk.id,
                      bsk.name,
                      DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                      bsk.nb_views,
                      count(rec.id_bibrec_or_bskEXTREC),
                      bsk.id_owner

    FROM   bskBASKET bsk LEFT JOIN bskREC rec
                         ON bsk.id=rec.id_bskBASKET
    WHERE bsk.id=%s

    GROUP BY bsk.id"""
    res = run_sql(query, (int(bskid),))
    if res:
        query2 = "UPDATE bskBASKET SET nb_views=nb_views+1 WHERE id=%s"
        run_sql(query2, (int(bskid),))
        return res[0]
    return ()

def get_basket_owner_id(bskid):
    """Return the uid of the owner."""
    query = """SELECT id_owner
                 FROM bskBASKET
                WHERE id=%s"""
    res = run_sql(query, (bskid, ))
    if res:
        return res[0][0]
    return -1

def count_public_baskets():
    """Returns the number of public baskets."""

    query = """ SELECT  COUNT(id_bskBASKET)
                FROM    usergroup_bskBASKET
                WHERE   id_usergroup=0"""

    res = run_sql(query)

    return __wash_sql_count(res)

def get_public_baskets_list(inf_limit, max_number, order=1, asc=1):
    """Return list of public baskets
    @param inf_limit: limit to baskets from number x
    @param max_number: number of baskets to return
    @order: 1: order by name of basket, 2: number of views, 3: owner
    @return:
    [(basket id, basket name, nb of views, uid of owner, nickname of owner)]"""

    query = """SELECT bsk.id,
                      bsk.name,
                      bsk.nb_views,
                      u.id,
                      u.nickname
               FROM   bskBASKET bsk LEFT JOIN usergroup_bskBASKET ugbsk
                                    on bsk.id=ugbsk.id_bskBASKET
                                    LEFT JOIN user u
                                    on bsk.id_owner=u.id
               WHERE ugbsk.id_usergroup=0
    """
    if order == 2:
        query += 'ORDER BY bsk.nb_views'
    elif order == 3:
        query += 'ORDER BY u.nickname'
        if asc:
            query += ' ASC'
        else:
            query += ' DESC'
        query += ', u.id'
    else:
        query += 'ORDER BY bsk.name'
    if asc:
        query += ' ASC '
    else:
        query += ' DESC '
    query += "LIMIT %s,%s"

    return run_sql(query, (inf_limit, max_number))

def count_all_public_baskets():
    """Return the number of all the public baskets."""

    query = """ SELECT  count(id_bskBASKET)
                FROM    usergroup_bskBASKET
                WHERE   id_usergroup=0"""

    res = run_sql(query)

    return __wash_sql_count(res)

def get_list_public_baskets(page, max_number, sort='name', asc=1):
    """Return list of public baskets
    @param page: limit to baskets from number x
    @param max_number: maximum number of baskets to return
    @sort: 1: order by name of basket, 2: number of views, 3: owner
    @return:
    [(basket id, basket name, nb of views, uid of owner, nickname of owner)]"""

    query = """ SELECT      bsk.id,
                            bsk.name,
                            bsk.id_owner,
                            u.nickname,
                            DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                            COUNT(rec.id_bibrec_or_bskEXTREC) AS items,
                            bsk.nb_views
                FROM        usergroup_bskBASKET AS ugbsk
                JOIN        bskBASKET AS bsk
                    ON      bsk.id=ugbsk.id_bskBASKET
                LEFT JOIN   bskREC AS rec
                    ON      rec.id_bskBASKET=bsk.id
                LEFT JOIN   user AS u
                    ON      u.id=bsk.id_owner
                WHERE       ugbsk.id_usergroup=0
                GROUP BY    bsk.id"""

    if sort == 'name':
        query += """
                ORDER BY bsk.name"""
    elif sort == 'owner':
        query += """
                ORDER BY u.nickname"""
    elif sort == 'views':
        query += """
                ORDER BY bsk.nb_views"""
    elif sort == 'date':
        query += """
                ORDER BY bsk.date_modification"""
    elif sort == 'items':
        query += """
                ORDER BY items"""
    else:
        query += """
                ORDER BY bsk.name"""
    if asc:
        query += """ ASC"""
        if sort == """owner""":
            query += """, u.id"""
    else:
        query += """ DESC"""
        if sort == """owner""":
            query += """, u.id"""

    query += """
                LIMIT %s, %s"""

    page = max(0, page)

    res = run_sql(query, (page, max_number))

    return res

def is_basket_public(bskid):
    """Check if the given basket is public.
    Returns ((0,),) if False, ((1,),) if True."""

    query = """ SELECT  COUNT(*)
                FROM    usergroup_bskBASKET
                WHERE   id_usergroup=0
                AND     id_bskBASKET=%s"""

    params = (bskid,)

    res = run_sql(query, params)

    return __wash_sql_count(res)

def subscribe(uid, bskid):
    """Subscribe the given user to the given basket."""

    query1 = """SELECT  COUNT(*)
                FROM    user_bskBASKET
                WHERE   id_user=%s
                AND     id_bskBASKET=%s"""

    params1 = (uid, bskid)

    res1 = run_sql(query1, params1)

    if res1[0][0]:
        # The user is either the owner of the basket or is already subscribed.
        return False
    else:
        query2 = """INSERT INTO user_bskBASKET (id_user, id_bskBASKET)
                                   VALUES      (%s, %s)"""

        params2 = (uid, bskid)

        run_sql(query2, params2)

        return True

def unsubscribe(uid, bskid):
    """Unsubscribe the given user from the given basket."""

    query1 = """SELECT  COUNT(*)
                FROM    bskBASKET
                WHERE   id_owner=%s
                AND     id=%s"""

    params1 = (uid, bskid)

    res1 = run_sql(query1, params1)

    if res1[0][0]:
        # The user is the owner of the basket.
        return False
    else:
        query2 = """DELETE FROM user_bskBASKET
                    WHERE       id_user=%s
                    AND         id_bskBASKET=%s"""

        params2 = (uid, bskid)

        res2 = run_sql(query2, params2)

        if res2:
            return True
        else:
            return False

def is_user_subscribed_to_basket(uid, bskid):
    """Return ((1,),) if the user is subscribed to the given basket
    or ((0,),) if the user is not subscribed or is the owner of the basket."""

    query = """ SELECT  COUNT(ubsk.id_bskBASKET)
                FROM    user_bskBASKET AS ubsk
                JOIN    bskBASKET AS bsk
                    ON  bsk.id=ubsk.id_bskBASKET
                    AND bsk.id_owner!=ubsk.id_user
                WHERE   ubsk.id_user=%s
                AND     ubsk.id_bskBASKET=%s"""

    params = (uid, bskid)

    res = run_sql(query, params)

    return __wash_sql_count(res)

def count_subscribers(uid, bskid):
    """Returns a (number of users, number of groups, number of alerts) tuple
    for the given user (uid) and basket (bskid)."""

    uid = int(uid)
    bskid = int(bskid)

    query_groups = """  SELECT      count(id_usergroup)
                        FROM        usergroup_bskBASKET
                        WHERE       id_bskBASKET=%s
                        AND         NOT(share_level='NO')
                        GROUP BY    id_bskBASKET"""
    params_groups = (bskid,)
    res_groups = run_sql(query_groups, params_groups)
    nb_groups = __wash_sql_count(res_groups)

    query_users = """   SELECT      count(id_user)
                        FROM        user_bskBASKET
                        WHERE       id_bskBASKET=%s
                        AND         id_user!=%s
                        GROUP BY    id_bskBASKET"""
    params_users = (bskid, uid)
    res_users = run_sql(query_users, params_users)
    nb_users = __wash_sql_count(res_users)

    query_alerts = """  SELECT      count(id_query)
                        FROM        user_query_basket
                        WHERE       id_basket=%s
                        GROUP BY    id_basket"""
    params_alerts = (bskid,)
    res_alerts = run_sql(query_alerts, params_alerts)
    nb_alerts = __wash_sql_count(res_alerts)
    return (nb_users, nb_groups, nb_alerts)

def get_groups_subscribing_to_basket(bskid):
    """ get list of (group id, group name, rights) tuples for a given basket
    Please note that group 0 is used to mean everybody.
    """
    query = """SELECT ugb.id_usergroup,
                      ug.name,
                      ugb.share_level
               FROM usergroup_bskBASKET ugb LEFT JOIN usergroup ug
                                            ON ugb.id_usergroup=ug.id
               WHERE ugb.id_bskBASKET=%s
               ORDER BY ugb.id_usergroup"""
    return run_sql(query, (int(bskid),))

def get_rights_on_public_basket(bskid):
    """"""

    query = """ SELECT  share_level
                FROM    usergroup_bskBASKET
                WHERE   id_usergroup=0
                AND     id_bskBASKET=%s"""

    params = (bskid,)

    res = run_sql(query, params)

    return res

def count_public_basket_subscribers(bskid):
    """Return the number of users subscribed to the given public basket."""

    query = """ SELECT  COUNT(ubsk.id_user)
                FROM    user_bskBASKET AS ubsk
                JOIN    bskBASKET AS bsk
                    ON  bsk.id=ubsk.id_bskBASKET
                    AND bsk.id_owner!=ubsk.id_user
                WHERE   ubsk.id_bskBASKET=%s"""

    params = (bskid,)

    res = run_sql(query, params)

    return __wash_sql_count(res)

################################ Notes ########################################

def get_notes(bskid, recid):
    """Return all comments for record recid in basket bskid."""

    query = """
    SELECT user.id,
           user.nickname,
           bskcmt.title,
           bskcmt.body,
           DATE_FORMAT(bskcmt.date_creation, '%%Y-%%m-%%d %%H:%%i:%%s'),
           bskcmt.priority,
           bskcmt.id,
           bskcmt.in_reply_to_id_bskRECORDCOMMENT

    FROM   bskRECORDCOMMENT bskcmt LEFT JOIN user
                                   ON (bskcmt.id_user=user.id)

    WHERE  bskcmt.id_bskBASKET=%s AND
           bskcmt.id_bibrec_or_bskEXTREC=%s

    ORDER BY bskcmt.reply_order_cached_data
    """
    bskid = int(bskid)
    recid = int(recid)
    res = run_sql(query, (bskid, recid))
    if res:
        return res
    else:
        return ()

def get_note(cmtid):
    """Return comment cmtid as a (author's nickname, author's uid, title, body, date of creation, priority) tuple"""
    out = ()
    query = """
    SELECT user.nickname,
           user.id,
           bskcmt.title,
           bskcmt.body,
           DATE_FORMAT(bskcmt.date_creation, '%%Y-%%m-%%d %%H:%%i:%%s'),
           bskcmt.priority

    FROM   bskRECORDCOMMENT bskcmt LEFT JOIN user
                                   ON (bskcmt.id_user=user.id)

    WHERE  bskcmt.id=%s
    """
    cmtid = int(cmtid)
    res = run_sql(query, (cmtid,))
    if res:
        return res[0]
    return out

def save_note(uid, bskid, recid, title, body, date_creation=None, reply_to=None):
    """Save then given note (title, body) on the given item in the given basket.
    @param date_creation: date in which the note was created
    @type date_creation: None or String, e.g: '2011-07-04 14:20:57'

    Note: convert_datestruct_to_datetext((2005, 11, 16, 15, 11, 44, 2, 320, 0)) -> '2005-11-16 15:11:44'
    """
    if reply_to and cfg['CFG_WEBBASKET_MAX_COMMENT_THREAD_DEPTH']>= 0:
        # Check that we have not reached max depth
        note_ancestors = get_note_ancestors(reply_to)
        if len(note_ancestors) >= cfg['CFG_WEBBASKET_MAX_COMMENT_THREAD_DEPTH']:
            if cfg['CFG_WEBBASKET_MAX_COMMENT_THREAD_DEPTH']== 0:
                reply_to = None
            else:
                reply_to = note_ancestors[cfg['CFG_WEBBASKET_MAX_COMMENT_THREAD_DEPTH']- 1]

    if not date_creation:
        date = convert_datestruct_to_datetext(localtime())
    else: #the date comes with the proper format
        date = date_creation

    res = run_sql("""INSERT INTO bskRECORDCOMMENT (id_user, id_bskBASKET,
                       id_bibrec_or_bskEXTREC, title, body, date_creation, in_reply_to_id_bskRECORDCOMMENT)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                  (int(uid), int(bskid), int(recid), title, body, date, reply_to or 0))
    if res:
        new_comid = int(res)
        parent_reply_order = run_sql("""SELECT reply_order_cached_data from bskRECORDCOMMENT where id=%s""", (reply_to,))
        if not parent_reply_order or parent_reply_order[0][0] is None:
            parent_reply_order = ''
        else:
            parent_reply_order = parent_reply_order[0][0]
        run_sql("""UPDATE bskRECORDCOMMENT SET reply_order_cached_data=%s WHERE id=%s""",
                (parent_reply_order + get_reply_order_cache_data(new_comid), new_comid))
        return int(res)
    return 0

def delete_note(bskid, recid, cmtid):
    """Delete a comment on an item of a basket"""

    query = """ DELETE
                FROM    bskRECORDCOMMENT
                WHERE   id_bskBASKET=%s
                AND     id_bibrec_or_bskEXTREC=%s
                AND     id=%s"""

    params = (int(bskid), int(recid), int(cmtid))

    run_sql(query, params)

def get_note_ancestors(cmtid, depth=None):
    """
    Returns the list of ancestors of the given note, ordered from
    oldest to newest ("top-down": direct parent of cmtid is at last position),
    up to given depth

    @param cmtid: the ID of the note for which we want to retrieve ancestors
    @type cmtid: int
    @param depth: the maximum of levels up from the given note we
                  want to retrieve ancestors. None for no limit, 1 for
                  direct parent only, etc.
    @type depth: int
    @return the list of ancestors
    @rtype: list
    """
    if depth == 0:
        return []

    res = run_sql("SELECT in_reply_to_id_bskRECORDCOMMENT FROM bskRECORDCOMMENT WHERE id=%s", (cmtid,))
    if res:
        parent_cmtid = res[0][0]
        if parent_cmtid == 0:
            return []
        parent_ancestors = []
        if depth:
            depth -= 1
        parent_ancestors = get_note_ancestors(parent_cmtid, depth)
        parent_ancestors.append(parent_cmtid)
        return parent_ancestors
    else:
        return []

def note_belongs_to_item_in_basket_p(cmtid, recid, bskid):
    """Returns 1 (True) if the given note (cmtid) belongs to the given item
    (recid) and the given basket (bskid) or 0 (False)."""

    query = """ SELECT  COUNT(*)
                FROM    bskRECORDCOMMENT
                WHERE   id=%s
                AND     id_bibrec_or_bskEXTREC=%s
                AND     id_bskBASKET=%s"""

    params = (cmtid, recid, bskid)

    res = run_sql(query, params)

    return __wash_sql_count(res)

def get_number_of_notes_per_record_in_basket(bskid, recids):
    """Returns the number of comments per record
    for all the given records in the given basket"""

    # We need to convert the list of recids into a string of commma separated
    # numbers (recids), instead of a tuple, to cover the case where we have
    # single element lists of recids. Example:
    # [1] --> '1' instaed of [1] --> (1,)
    # Single element tuples would cause the query to fail due to the syntax.
    query = """ SELECT      rec.id_bibrec_or_bskEXTREC,
                            COUNT(cmt.id_bibrec_or_bskEXTREC)
                FROM        bskREC as rec
                LEFT JOIN   bskRECORDCOMMENT as cmt
                    ON      cmt.id_bibrec_or_bskEXTREC = rec.id_bibrec_or_bskEXTREC
                WHERE       rec.id_bskBASKET=%%s
                    AND     rec.id_bibrec_or_bskEXTREC IN (%s)
                GROUP BY    id_bibrec_or_bskEXTREC
                ORDER BY    rec.score""" % (str(map(int, recids))[1:-1],)

    params = (bskid,)

    result = run_sql(query, params)

    return result

########################## Usergroup functions ################################

def get_group_infos(uid):
    """For each group the user with uid is a member of return the id, name and number of baskets."""
    query = """SELECT g.id,
                      g.name,
                      count(ugb.id_bskBASKET)
               FROM usergroup g LEFT JOIN (user_usergroup ug,
                                           usergroup_bskBASKET ugb)
                                ON (g.id=ug.id_usergroup
                                            AND
                                    g.id=ugb.id_usergroup)
               WHERE ug.id_user=%s AND NOT(ugb.share_level='NO') AND ug.user_status!=%s
               GROUP BY g.id
               ORDER BY g.name"""
    params = (int(uid), CFG_WEBSESSION_USERGROUP_STATUS['PENDING'])
    res = run_sql(query, params)
    return res

def count_groups_user_member_of(uid):
    """Returns the number of groups the user has joined."""

    query = """ SELECT  COUNT(id_usergroup)
                FROM    user_usergroup
                WHERE   id_user=%s
                AND     user_status!=%s"""

    params = (int(uid), CFG_WEBSESSION_USERGROUP_STATUS['PENDING'])

    res = run_sql(query, params)

    return __wash_sql_count(res)

def get_groups_user_member_of(uid):
    """
    Get uids and names of groups user is member of.
    @param uid: user id (int)
    @return: a tuple of (group_id, group_name) tuples
    """
    query = """
    SELECT g.id,
           g.name
    FROM usergroup g JOIN user_usergroup ug
                   ON (g.id=ug.id_usergroup)
    WHERE ug.id_user=%s and ug.user_status!=%s
    ORDER BY g.name
    """
    params = (int(uid), CFG_WEBSESSION_USERGROUP_STATUS['PENDING'])
    res = run_sql(query, params)
    if res:
        return res
    return ()

########################## auxilliary functions ###############################

def __wash_sql_count(res):
    """Wash the result of SQL COUNT function and return only an integer."""
    if res:
        return res[0][0]
    return 0

def __decompress_last(item):
    """private function, used to shorten code"""
    item = list(item)
    item[-1] = decompress(item[-1])
    return item

def create_pseudo_record(es_title, es_desc, es_url, of="hb"):
    """Return a pseudo record representation given a title and a description."""

    if of == 'hb':
        record = '\n'.join([es_title, es_desc, es_url])
    if of == 'xm':
# In case we want to use the controlfield,
# the -es_id must be used.
#<controlfield tag="001">%s</controlfield>
        record = """<record>
  <datafield tag="245" ind1=" " ind2=" ">
    <subfield code="a">%s</subfield>
  </datafield>
  <datafield tag="520" ind1=" " ind2=" ">
    <subfield code="a">%s</subfield>
  </datafield>
  <datafield tag="856" ind1="4" ind2=" ">
    <subfield code="u">%s</subfield>
  </datafield>
</record>""" % (encode_for_xml(es_title), encode_for_xml(es_desc), encode_for_xml(es_url))
    return record

def prettify_url(url, char_limit=50, nb_dots=3):
    """If the url has more characters than char_limit return a shortened version of it
    keeping the beginning and ending and replacing the rest with dots."""

    if len(url) > char_limit:
        # let's set a minimum character limit
        if char_limit < 5:
            char_limit = 5
        # let's set a maximum number of dots in relation to the character limit
        if nb_dots > char_limit/4:
            nb_dots = char_limit/5
        nb_char_url = char_limit - nb_dots
        nb_char_end = nb_char_url/4
        nb_char_beg = nb_char_url - nb_char_end
        return url[:nb_char_beg] + '.'*nb_dots + url[-nb_char_end:]
    else:
        return url
