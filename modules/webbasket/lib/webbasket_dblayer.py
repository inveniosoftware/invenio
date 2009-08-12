# -*- coding: utf-8 -*-
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

""" Database related functions for webbasket module """

__revision__ = "$Id$"

from zlib import decompress
from zlib import compress
from time import localtime

from invenio.dbquery import run_sql
from invenio.webbasket_config import CFG_WEBBASKET_SHARE_LEVELS, \
                                     CFG_WEBBASKET_ACTIONS, \
                                     CFG_WEBBASKET_SHARE_LEVELS_ORDERED
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.websession_config import CFG_WEBSESSION_USERGROUP_STATUS

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
#    - get_personal_baskets_infos
#    - get_all_personal_baskets_names
#    - get_basket_name
#    - get_personal_topics_infos
#    - rename_basket
#    - rename_topic
#    - move_baskets_to_topic
#    - delete_basket
#    - create_basket
#
# 3. Actions on baskets
#    - get_basket_record
#    - share_basket_with_group
#    - update_rights
#    - move_item
#    - delete_item
#    - add_to_basket
#    - get_basket_content
#    - get_external_records_by_collection
#    - store_external_records
#    - store_external_urls
#    - store_external_source
#
# 4. Group baskets
#    - get_group_basket_infos
#    - (*) get_all_group_baskets_names
#    - is_shared_to
#
# 5. External baskets (baskets user has subscribed to)
#    - get_external_baskets_infos
#    - count_external_baskets
#    - get_all_external_baskets_names
#
# 6. Public baskets (interface to subscribe to baskets)
#    - get_public_basket_infos
#    - get_basket_general_infos
#    - count_public_baskets
#    - get_public_baskets_list
#    - subscribe
#    - unsubscribe
#    - count_subscribers
#    - (*) get_groups_subscribing_to_basket
#
# 7. Commenting
#    - get_comments
#    - get_comment
#    - save_comment
#    - delete_comment
#
# 8. Usergroup functions
#    - (*) get_group_infos
#    - count_groups_user_member_of
#    - (*) get_groups_user_member_of
#
# 9. Useful functions
#    - __wash_count
#    - __decompress_last
#    - create_pseudo_record
#
########################## General functions ##################################

def count_baskets(uid):
    """Return (nb personal baskets, nb group baskets, nb external
    baskets) tuple for given user"""
    query1 = "SELECT COUNT(id) FROM bskBASKET WHERE id_owner=%s"
    res1 = run_sql(query1, (int(uid),))
    personal = __wash_count(res1)
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
        return CFG_WEBBASKET_SHARE_LEVELS['MANAGE']
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
            group_index = CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(res[0][0])
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
            public_index = CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(res[0][0])
        except:
            return None
    if group_index or public_index:
        if group_index > public_index:
            return CFG_WEBBASKET_SHARE_LEVELS_ORDERED[group_index]
        else:
            return CFG_WEBBASKET_SHARE_LEVELS_ORDERED[public_index]
    return None

########################### Personal baskets ##################################


def get_personal_baskets_infos(uid, topic):
    """
    Get useful infos (see below) for every personal basket of a given user in a given topic
    share level is assumed to be MA (MAnage) for a personal basket!
    @param uid: user id (int)
    @param topic: topic of the basket
    @return: a tuple of (id,
                       name,
                       share_level,
                       date_modification
                       nb_views) tuples
    """
    query = """
    SELECT bsk.id,
           bsk.name,
           DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
           bsk.nb_views,
           count(rec.id_bibrec_or_bskEXTREC),
           DATE_FORMAT(max(rec.date_added), '%%Y-%%m-%%d %%H:%%i:%%s')

    FROM   bskBASKET bsk JOIN user_bskBASKET ubsk
                         ON (bsk.id=ubsk.id_bskBASKET AND
                             ubsk.id_user=%s AND
                             bsk.id_owner=%s)
                         LEFT JOIN bskREC rec
                         ON (bsk.id=rec.id_bskBASKET)

    WHERE  ubsk.topic=%s

    GROUP BY bsk.id
    """
    res = run_sql(query, (uid, uid, topic))
    if res:
        return res
    return ()

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
    """Delete given basket. """
    bskid = int(bskid)
    query1 = "DELETE FROM bskBASKET WHERE id=%s"
    res = run_sql(query1, (bskid,))
    query2A = "SELECT id_bibrec_or_bskEXTREC FROM bskREC WHERE id_bskBASKET=%s"
    ids = run_sql(query2A, (bskid,))
    external_ids = [-id[0] for id in ids if id[0]<0]
    if external_ids:
        query2B = "DELETE FROM bskEXTREC WHERE %s"
        query2C = "DELETE FROM bskEXTFMT WHERE %s"
        sep_or = ' OR '
        query2B %= sep_or.join(['id=%s'] * len(external_ids))
        query2C %= sep_or.join(['id_bskEXTREC=%s'] * len(external_ids))
        params2BC = tuple(external_ids)
        run_sql(query2B, params2BC)
        run_sql(query2C, params2BC)
    query2D = "DELETE FROM bskREC WHERE id_bskBASKET=%s"
    run_sql(query2D, (bskid,))
    query3 = "DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET=%s"
    run_sql(query3, (bskid,))
    query4 = "DELETE FROM user_bskBASKET WHERE id_bskBASKET=%s"
    run_sql(query4, (bskid,))
    query5 = "DELETE FROM usergroup_bskBASKET WHERE id_bskBASKET=%s"
    run_sql(query5, (bskid,))
    query6 = "DELETE FROM user_query_basket WHERE id_basket=%s"
    run_sql(query6, (bskid,))
    #delete group, external and alerts
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

def share_basket_with_group(bskid, group_id,
                            share_level=CFG_WEBBASKET_SHARE_LEVELS['READITM']):
    """ Share basket bskid with group group_id with given share_level
    @param share_level:  see CFG_WEBBASKET_SHARE_LEVELS in webbasket_config
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
        if direction == CFG_WEBBASKET_ACTIONS['UP']:
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

def delete_item(bskid, recid):
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
    query1 = "DELETE from bskREC WHERE id_bskBASKET=%s AND id_bibrec_or_bskEXTREC=%s"
    params1 = (int(bskid), int(recid))
    res = run_sql(query1, params1)
    if res:
        now = convert_datestruct_to_datetext(localtime())
        query2 = "UPDATE bskBASKET SET date_modification=%s WHERE id=%s"
        params2 = (now, int(bskid))
        run_sql(query2, params2)
    return res

def add_to_basket(uid, recids=[], colid=0, bskids=[], es_title="", es_desc="", es_url=""):
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
            query2A = """INSERT
                        INTO bskEXTREC
                            (external_id,
                            collection_id,
                            creation_date,
                            modification_date)
                        VALUES """
            now = convert_datestruct_to_datetext(localtime())
            records = ["(%s, %s, %s, %s)"] * len(recids)
            query2A += ', '.join(records)
            params = ()
            for recid in recids:
                params += (int(recid), colid, now, now)
            res = run_sql(query2A, params)
            recids = range(-res,-(res+len(recids)),-1)
        elif colid < 0:
            # the query for external sources. Not yet implemented.
            # a url should be passed to this function and set as
            # the fourth element of the params tuple
            query2B = """INSERT
                        INTO bskEXTREC
                            (collection_id,
                            original_url,
                            creation_date,
                            modification_date)
                        VALUES (%s, %s, %s, %s)"""
            now = convert_datestruct_to_datetext(localtime())
            params = (colid, es_url, now, now)
            res = run_sql(query2B, params)
            recids = [-res]
            store_external_source(res, es_title, es_desc, es_url, 'hb')

        query2 = """INSERT IGNORE
                    INTO   bskREC
                           (id_bibrec_or_bskEXTREC,
                            id_bskBASKET,
                            id_user_who_added_item,
                            date_added,
                            score)
                    VALUES """
        if colid == 0:
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

def get_basket_content(bskid, format='hb'):
    """Get all records for a given basket."""
    res = run_sql("""
    SELECT rec.id_bibrec_or_bskEXTREC,
           count(cmt.id_bibrec_or_bskEXTREC),
           DATE_FORMAT(max(cmt.date_creation), '%%Y-%%m-%%d %%H:%%i:%%s'),
           extern.value as ext_val,
           intern.value as int_val,
           rec.score

    FROM bskREC rec LEFT JOIN bskRECORDCOMMENT cmt
                    ON (rec.id_bibrec_or_bskEXTREC=cmt.id_bibrec_or_bskEXTREC AND
                        rec.id_bskBASKET=cmt.id_bskBASKET)
                    LEFT JOIN bskEXTFMT extern
                    ON (-rec.id_bibrec_or_bskEXTREC=extern.id_bskEXTREC AND
                        extern.format=%s)
                    LEFT JOIN bibfmt intern
                    ON (rec.id_bibrec_or_bskEXTREC=intern.id_bibrec AND
                        intern.format=%s)

    WHERE rec.id_bskBASKET=%s

    GROUP BY rec.id_bibrec_or_bskEXTREC

    ORDER BY rec.score
    """, (format, format, int(bskid)))
    if res:
        query2 = "UPDATE bskBASKET SET nb_views=nb_views+1 WHERE id=%s"
        run_sql(query2, (int(bskid),))
        return res
    return ()

def get_external_records_by_collection(recids):
    """Get the selected recids, both local and external, grouped by collection."""

    if len(recids):
        query = """SELECT GROUP_CONCAT(id),
                    GROUP_CONCAT(external_id),
                    collection_id
                    FROM bskEXTREC
                    WHERE %s
                    GROUP BY collection_id"""
    
        recids = [-recid for recid in recids]
        sep_or = ' OR '
        query %= sep_or.join(['id=%s'] * len(recids))
        params = tuple(recids)
        res = run_sql(query,params)
        return res
    else:
        return 0

def store_external_records(records, of="hb"):
    """Store formatted external records to the database."""

    if len(records):
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

def store_external_urls(urls):
    """Store original urls for external records to the database."""

    for url in urls.iteritems():
        query = """UPDATE
                    bskEXTREC
                    SET original_url=%s
                    WHERE id=%s"""
        params = (url[1], url[0])
        run_sql(query,params)

def store_external_source(es_id, es_title, es_desc, es_url, of="hb"):
    """Store formatted external sources to the database."""

    if es_id and es_title and es_desc:
        query = """INSERT
                    INTO bskEXTFMT
                        (id_bskEXTREC,
                        format,
                        last_updated,
                        value)
                    VALUES (%s, %s, %s, %s)"""
        now = convert_datestruct_to_datetext(localtime())
        params = (es_id, of, now, compress(create_pseudo_record(es_title, es_desc, es_url, of)))
        run_sql(query,params)

def get_external_colid_url(recid):
    """Get the original url for an external record."""

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


def get_group_baskets_infos(gid):
    """
    get useful infos (see below) for every basket of a group
    @param gid: group id (int)
    @return: a tuple of (id,
                        name,
                        topic,
                        rigths,
                        date_shared,
                        date_modification,
                        nb_views) tuples
    """
    if gid == 0:
        return ()
    query = """
    SELECT bsk.id,
           bsk.name,
           DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
           bsk.nb_views,
           count(rec.id_bibrec_or_bskEXTREC),
           DATE_FORMAT(max(rec.date_added), '%%Y-%%m-%%d %%H:%%i:%%s'),
           ub.share_level,
           bsk.id_owner

    FROM   bskBASKET bsk JOIN usergroup_bskBASKET ub
                         ON bsk.id=ub.id_bskBASKET
                         LEFT JOIN bskREC rec
                         ON bsk.id=rec.id_bskBASKET
    WHERE ub.id_usergroup=%s AND NOT(ub.share_level='NO')

    GROUP BY bsk.id
    """
    gid = int(gid)
    res = run_sql(query, (gid,))
    if res:
        return res
    return ()

def get_all_group_baskets_names(uid,
                                min_rights=CFG_WEBBASKET_SHARE_LEVELS['ADDCMT']):
    """ for a given user returns every group baskets in which he can <min_rights>
    return a list of tuples: (bskid, bsk_name, group_name)
    """
    uid = int(uid)
    try:
        min_rights_num = CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(min_rights)
    except ValueError:
        return ()
    groups = get_groups_user_member_of(uid)
    if groups:
        where_clause = '('
        where_clause += " OR ".join(["ugbsk.id_usergroup=%s"] * len(groups))
        where_clause += ') AND ('
        where_clause += " OR ".join(["ugbsk.share_level=%s"] * len(CFG_WEBBASKET_SHARE_LEVELS_ORDERED[min_rights_num:]))
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
        params = tuple([group_id for group_id, group_name in groups])
        params += tuple(CFG_WEBBASKET_SHARE_LEVELS_ORDERED[min_rights_num:])
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

def count_external_baskets(uid):
    """return number of external baskets user has subscribed to"""
    query = """
    SELECT count(ubsk.id_bskBASKET)
    FROM   user_bskBASKET ubsk LEFT JOIN bskBASKET bsk
                               ON (bsk.id=ubsk.id_bskBASKET AND ubsk.id_user=%s)
    WHERE  bsk.id_owner!=%s
    """
    return __wash_count(run_sql(query, (int(uid), int(uid))))

def get_all_external_baskets_names(uid,
                                   min_rights=CFG_WEBBASKET_SHARE_LEVELS['ADDCMT']):

    """ for a given user returns every basket which he has subscribed to and in which
    he can <min_rights>
    return a list of tuples: (bskid, bsk_name)
    """
    uid = int(uid)
    try:
        min_rights_num = CFG_WEBBASKET_SHARE_LEVELS_ORDERED.index(min_rights)
    except ValueError:
        return ()
    where_clause = ' AND ('
    for right in CFG_WEBBASKET_SHARE_LEVELS_ORDERED[min_rights_num:-1]:
        where_clause += "ugbsk.share_level = '%s' OR " % right
    where_clause += "ugbsk.share_level = '%s')" % CFG_WEBBASKET_SHARE_LEVELS_ORDERED[-1]
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
    """return number of public baskets"""
    query = """SELECT count(id_bskBASKET)
               FROM usergroup_bskBASKET
               WHERE id_usergroup=0"""
    return __wash_count(run_sql(query))

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

def is_public(bskid):
    """return 1 if basket is public, 0 else."""
    query = "SELECT count(id_usergroup) FROM usergroup_bskBASKET WHERE id_bskBASKET=%s AND id_usergroup=0"
    return __wash_count(run_sql(query, (int(bskid),)))

def subscribe(uid, bskid):
    """user uid subscribes to basket bskid"""
    query1 = "SELECT count(id_user) FROM user_bskBASKET WHERE id_user=%s AND id_bskBASKET=%s"
    if not(__wash_count(run_sql(query1, (int(uid), int(bskid))))):
        query2 = "INSERT INTO user_bskBASKET (id_user, id_bskBASKET) VALUES (%s,%s)"
        run_sql(query2, (int(uid), int(bskid)))

def unsubscribe(uid, bskid):
    """unsubscribe from basket"""
    query = "DELETE FROM user_bskBASKET WHERE id_user=%s AND id_bskBASKET=%s"
    run_sql(query, (int(uid), int(bskid)))

def count_subscribers(uid, bskid):
    """ Return a (number of users, number of groups, number of alerts) tuple """
    uid = int(uid)
    bskid = int(bskid)
    query_groups = """SELECT count(id_usergroup)
                      FROM usergroup_bskBASKET
                      WHERE id_bskBASKET=%s and NOT(share_level='NO')
                      GROUP BY id_bskBASKET"""
    nb_groups = __wash_count(run_sql(query_groups, (bskid,)))
    query_users = """SELECT count(id_user)
                     FROM user_bskBASKET
                     WHERE id_bskBASKET=%s AND id_user!=%s
                     GROUP BY id_bskBASKET"""
    nb_users = __wash_count(run_sql(query_users, (bskid, uid)))
    query_alerts = """SELECT count(id_query)
                      FROM user_query_basket
                      WHERE id_basket=%s
                      GROUP BY id_basket"""
    nb_alerts = __wash_count(run_sql(query_alerts, (bskid,)))
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


############################ Comments ########################################

def get_comments(bskid, recid):
    """Return all comments for record recid in basket bskid."""
    out = ()
    query = """
    SELECT user.id,
           user.nickname,
           bskcmt.title,
           bskcmt.body,
           DATE_FORMAT(bskcmt.date_creation, '%%Y-%%m-%%d %%H:%%i:%%s'),
           bskcmt.priority,
           bskcmt.id

    FROM   bskRECORDCOMMENT bskcmt LEFT JOIN user
                                   ON (bskcmt.id_user=user.id)

    WHERE  bskcmt.id_bskBASKET=%s AND
           bskcmt.id_bibrec_or_bskEXTREC=%s

    ORDER BY bskcmt.date_creation
    """
    bskid = int(bskid)
    recid = int(recid)
    res = run_sql(query, (bskid, recid))
    if res:
        return res
    return out

def get_comment(cmtid):
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

def save_comment(uid, bskid, recid, title, body):
    """Save a given comment in table bskRECORDCOMMENT"""
    date = convert_datestruct_to_datetext(localtime())
    res = run_sql("""INSERT INTO bskRECORDCOMMENT (id_user, id_bskBASKET,
                       id_bibrec_or_bskEXTREC, title, body, date_creation)
                     VALUES (%s, %s, %s, %s, %s, %s)""",
                  (int(uid), int(bskid), int(recid), title, body, date))
    if res:
        return int(res)
    return 0

def delete_comment(bskid, recid, cmtid):
    """Delete a comment on an item of a basket"""
    query = """DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET=%s AND id_bibrec_or_bskEXTREC=%s AND id=%s"""
    run_sql(query, (int(bskid), int(recid), int(cmtid)))

########################## Usergroup functions ################################

def get_group_infos(uid):
    """Get for each group a user is member of its uid, name and number of baskets."""
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
    """Return number of groups user has joined."""
    query = "SELECT count(id_usergroup) FROM user_usergroup WHERE id_user=%s AND user_status!=%s"
    params = (int(uid), CFG_WEBSESSION_USERGROUP_STATUS['PENDING'])
    return __wash_count(run_sql(query, params))

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

########################## helpful functions ##################################

def __wash_count(res):
    """If query is like SELECT count(x) FROM y, return a washed version"""
    if res:
        return int(res[0][0])
    else:
        return 0

def __decompress_last(item):
    """private function, used to shorten code"""
    item = list(item)
    item[-1] = decompress(item[-1])
    return item

def create_pseudo_record(es_title, es_desc, es_url, of="hb"):
    """Return a pseudo record representation given a title and a description."""

    if of == 'hb':
        record = """
<strong>%s</strong>
<br />
<small>%s
<br />
<strong>URL:</strong> <a class="note" target="_blank" href="%s">%s</a>
</small>
""" % (es_title, es_desc, es_url, prettify_url(es_url))
        return record
    if of == 'xm':
        pass

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
