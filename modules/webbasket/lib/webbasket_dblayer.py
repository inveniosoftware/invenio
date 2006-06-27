# -*- coding: utf-8 -*-
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

""" Database related functions for webbasket module """

from zlib import decompress
from time import localtime

from invenio.dbquery import run_sql, escape_string
from invenio.webbasket_config import cfg_webbasket_share_levels, \
                                     cfg_webbasket_actions, \
                                     cfg_webbasket_share_levels_ordered
from invenio.dateutils import convert_datestruct_to_datetext

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
#
########################## General functions ##################################

def count_baskets(uid):
    """Return (nb personal baskets, nb group baskets, nb external
    baskets) tuple for given user"""
    query1 = "SELECT COUNT(id) FROM bskBASKET WHERE id_owner=%i"
    res1 = run_sql(query1 % int(uid))
    personal = __wash_count(res1)
    query2 = """SELECT count(ugbsk.id_bskbasket) 
                FROM usergroup_bskBASKET ugbsk LEFT JOIN user_usergroup uug 
                                               ON ugbsk.id_usergroup=uug.id_usergroup
                WHERE uug.id_user=%i
                GROUP BY ugbsk.id_usergroup"""
    res2 = run_sql(query2 % int(uid))
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
    query %= sep.join(map(lambda x: 'id=%i'% int(x), bskids))
    res = run_sql(query)
    if len(res)==1 and int(res[0][0])==uid:
        return 1
    else:
        return 0

def get_max_user_rights_on_basket(uid, bskid):
    """Return the max rights a user has on this basket"""
    query_owner = "SELECT count(id_owner) FROM bskBASKET WHERE id_owner=%i and id=%i"
    params_owner = (int(uid), int(bskid))
    res = run_sql(query_owner % params_owner)
    if res and res[0][0]:
        # if this user is owner of this baskets he can do anything he wants.
        return cfg_webbasket_share_levels['MANAGE']
    # not owner => group member ?
    query_group_baskets = """
    SELECT share_level
    FROM user_usergroup AS ug LEFT JOIN usergroup_bskBASKET AS ub
                              ON ug.id_usergroup=ub.id_usergroup
    WHERE ug.id_user=%i AND ub.id_bskBASKET=%i AND NOT(ub.share_level='NO')
    """
    max_rights_index = None
    params_group_baskets = (uid, bskid)
    res = run_sql(query_group_baskets % params_group_baskets)
    if res:
        group_rights = res[0][0]
        try:
            max_rights_index = cfg_webbasket_share_levels_ordered.index(group_rights)
        except ValueError:
            return None
    # public basket ?
    query_public_baskets = """
    SELECT share_level
    FROM usergroup_bskBASKET
    WHERE id_usergroup=0 AND id_bskBASKET=%i
    """
    res = run_sql(query_public_baskets % bskid)
    if res:
        public_rights = res[0][0]
        try:
            index = cfg_webbasket_share_levels_ordered.index(public_rights)
            if index > max_rights_index:
                return cfg_webbasket_share_levels_ordered[index]
            else:
                return cfg_webbasket_share_levels_ordered[max_rights_index]
        except ValueError:
            return None
            
            
########################### Personal baskets ##################################


def get_personal_baskets_infos(uid, topic):
    """
    Get useful infos (see below) for every personal basket of a given user in a given topic
    share level is assumed to be MA (MAnage) for a personal basket! 
    @param uid: user id (int)
    @param topic: topic of the basket
    @return a tuple of (id,
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
                             ubsk.id_user=%i AND
                             bsk.id_owner=%i)
                         LEFT JOIN bskREC rec
                         ON (bsk.id=rec.id_bskBASKET)
                                               
    WHERE  ubsk.topic='%s'
                      
    GROUP BY bsk.id
    """
    uid = int(uid)
    topic = escape_string(topic)
    res = run_sql(query%(uid, uid, topic))
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
    WHERE bsk.id_owner=%i
    ORDER BY ubsk.topic
    """
    params = (uid)
    return run_sql(query % params)

def get_basket_name(bskid):
    """return the name of a given basket"""
    query = 'SELECT name FROM bskBASKET where id=%i'
    res = run_sql(query % int(bskid))
    if res:
        return res[0][0]
    else:
        return ''

def get_personal_topics_infos(uid):
    """
    Get the list of every topic user has defined,
    and the number of baskets in each topic
    @param uid: user id (int)
    @return a list of tuples (topic name, nb of baskets)
    """
    query = """SELECT topic, count(b.id)
               FROM   user_bskBASKET ub JOIN bskBASKET b
                                        ON ub.id_bskBASKET=b.id AND
                                           b.id_owner=ub.id_user
               WHERE  ub.id_user=%i
               GROUP BY topic
               ORDER BY topic"""
    uid = int(uid)
    res = run_sql(query% uid)
    return res

def rename_basket(bskid, new_name):
    """Rename basket to new_name"""
    query = "UPDATE bskBASKET SET name='%s' WHERE id=%i"
    run_sql(query % (escape_string(new_name), int(bskid)))

def rename_topic(uid, old_topic, new_topic):
    """Rename topic to new_topic """
    query = "UPDATE user_bskBASKET SET topic='%s' WHERE id_user=%i AND topic='%s'"
    params = (escape_string(new_topic), int(uid), escape_string(old_topic))
    res = run_sql(query % params)
    return res
    
def move_baskets_to_topic(uid, bskids, new_topic):
    """Move given baskets to another topic"""
    if not(type(bskids) is list or type(bskids is tuple)):
        bskids = [bskids]
    query = "UPDATE user_bskBASKET SET topic='%s' WHERE id_user=%i AND (%s)"
    sep = ' OR '
    where_clause = sep.join(map(lambda x: 'id_bskBASKET=%i' % int(x), bskids))
    query %= (escape_string(new_topic), int(uid), where_clause)
    res = run_sql(query)
    return res

def delete_basket(bskid):
    """Delete given basket. """
    bskid = int(bskid)
    query1 = "DELETE FROM bskBASKET WHERE id=%i"
    res = run_sql(query1 % bskid)
    query2 = "DELETE FROM bskREC WHERE id_bskBASKET=%i"
    run_sql(query2 % bskid)
    query3 = "DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET=%i"
    run_sql(query3 % bskid)
    query4 = "DELETE FROM user_bskBASKET WHERE id_bskBASKET=%i"
    run_sql(query4 % bskid)
    query5 = "DELETE FROM usergroup_bskBASKET WHERE id_bskBASKET=%i"
    run_sql(query5 % bskid)
    query6 = "DELETE FROM user_query_basket WHERE id_basket=%i"
    run_sql(query6 % bskid)
    #delete group, external and alerts
    return int(res)

def create_basket(uid, basket_name, topic):
    """Create new basket for given user in given topic"""
    now = convert_datestruct_to_datetext(localtime())
    query1 = """INSERT INTO bskBASKET (id_owner, name, date_modification)
                VALUES                (%i, '%s', '%s')"""
    params1 = (uid, escape_string(basket_name), now)
    res = run_sql(query1 % params1)
    id_bsk = int(res)
    query2 = """INSERT INTO user_bskBASKET (id_user, id_bskBASKET, topic)
                VALUES                     (%i, %i, '%s')"""
    params2 = (uid, id_bsk, escape_string(topic))
    run_sql(query2 % params2)
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
    SELECT DATE_FORMAT(record.creation_date, '%%Y-%%m-%%d %%H:%%i:%%s'),
           DATE_FORMAT(record.modification_date, '%%Y-%%m-%%d %%H:%%i:%%s'),
           DATE_FORMAT(bskREC.date_added, '%%Y-%%m-%%d %%H:%%i:%%s'),
           user.nickname,
           count(cmt.id_bibrec_or_bskEXTREC),
           DATE_FORMAT(max(cmt.date_creation), '%%Y-%%m-%%d %%H:%%i:%%s'),
           fmt.value
           
    FROM bskREC LEFT JOIN user
                ON bskREC.id_user_who_added_item=user.id
                LEFT JOIN bskRECORDCOMMENT cmt 
                ON bskREC.id_bibrec_or_bskEXTREC=cmt.id_bibrec_or_bskEXTREC
                LEFT JOIN %(rec_table)s record
                ON (%(sign)sbskREC.id_bibrec_or_bskEXTREC=record.id)
                LEFT JOIN %(format_table)s fmt
                ON (record.id=fmt.%(id_field)s)
                
    WHERE bskREC.id_bskBASKET=%(bskid)i AND
          bskREC.id_bibrec_or_bskEXTREC=%(recid)s AND
          fmt.format='%(format)s'
                    
    GROUP BY bskREC.id_bibrec_or_bskEXTREC
    """
    params = {'rec_table': rec_table,
              'format_table': format_table,
              'sign': sign,
              'bskid': int(bskid),
              'recid': int(recid),
              'format': escape_string(format),
              'id_field': id_field}
    res = run_sql(query%params)
    if res:
        return __decompress_last(res[0])
    return ()

def share_basket_with_group(bskid, group_id,
                            share_level=cfg_webbasket_share_levels['READITM']):
    """ Share basket bskid with group group_id with given share_level
    @param share_level:  see cfg_webbasket_share_levels in webbasket_config
    """
    now = convert_datestruct_to_datetext(localtime())
    query = """REPLACE INTO usergroup_bskBASKET
                       (id_usergroup, id_bskBASKET, date_shared, share_level)
               VALUES (%i,%i,'%s','%s')"""
    run_sql(query % (int(group_id), int(bskid), now, escape_string(str(share_level))))

def update_rights(bskid, group_rights):
    """update rights (permissions) for groups.
    @param bskid: basket id
    @param group_rights: dictionary of {group id: new rights}
    """
    now = convert_datestruct_to_datetext(localtime())
    query1 = """REPLACE INTO usergroup_bskBASKET
                       (id_usergroup, id_bskBASKET, date_shared, share_level)
                VALUES %s"""
    values = []
    for (group_id, share_level) in group_rights.items():
        values.append("(%i,%i,'%s','%s')" % (int(group_id), int(bskid), now, str(share_level)))
    sep = ','
    values = sep.join(values)
    run_sql(query1 % values)
    query2 = """DELETE FROM usergroup_bskBASKET WHERE share_level='NO'"""
    run_sql(query2)
    
def move_item(bskid, recid, direction):
    """Change score of an item in a basket"""
    query1 = """SELECT id_bibrec_or_bskEXTREC,
                       score
                FROM bskREC
                WHERE id_bskBASKET=%i
                ORDER BY score, date_added"""
    items = run_sql(query1 % bskid)
    (recids, scores) = zip(*items)
    (recids, scores) = (list(recids), list(scores))
    if len(recids) and recid in recids:
        current_index = recids.index(recid)
        if direction == cfg_webbasket_actions['UP']:
            switch_index = 0
            if current_index != 0:
                switch_index = current_index -1
        else:
            switch_index = len(recids) - 1
            if current_index != len(recids)-1:
                switch_index = current_index + 1                
        query2 = """UPDATE bskREC
                    SET score=%i
                    WHERE id_bskBASKET=%i AND id_bibrec_or_bskEXTREC=%i"""
        res1 = run_sql(query2 % (scores[switch_index], bskid, recids[current_index]))
        res2 = run_sql(query2 % (scores[current_index], bskid, recids[switch_index]))
        if res1 and res2:
            now = convert_datestruct_to_datetext(localtime())
            query3 = "UPDATE bskBASKET SET date_modification='%s' WHERE id=%i"
            params3 = (now, bskid)
            run_sql(query3 % params3)

def delete_item(bskid, recid):
    """Remove item recid from basket bskid"""
    query1 = "DELETE from bskREC WHERE id_bskBASKET=%i AND id_bibrec_or_bskEXTREC=%i"
    params1 = (int(bskid), int(recid))
    res = run_sql(query1 % params1)
    if res:
        now = convert_datestruct_to_datetext(localtime())
        query2 = "UPDATE bskBASKET SET date_modification='%s' WHERE id=%i"
        params2 = (now, bskid)
        run_sql(query2 % params2)
    return res

def add_to_basket(uid, recids=[], bskids=[]):
    """Add items recids to every basket in bskids list."""
    if len(recids) and len(bskids):       
        query1 = """SELECT   id_bskBASKET,
                             max(score)
                    FROM     bskREC
                    WHERE    %s
                    GROUP BY id_bskBASKET"""
        sep_or = ' OR '
        bskids = filter(lambda x: int(x) >= 0, bskids) 
        query1 %= sep_or.join(map(lambda x: 'id_bskBASKET=' + str(x), bskids))
        bsks = dict.fromkeys(bskids, 0)
        bsks.update(dict(run_sql(query1)))
        query2 = """INSERT IGNORE
                    INTO   bskREC
                           (id_bibrec_or_bskEXTREC,
                            id_bskBASKET,
                            id_user_who_added_item,
                            date_added,
                            score)
                    VALUES """
        now = convert_datestruct_to_datetext(localtime())
        records = []
        for (bskid, max_score) in bsks.items():
            i = 1
            for recid in recids:
                record =  "(%i, %i, %i, '%s', %i)"
                record %= (int(recid), int(bskid), int(uid), now, int(max_score) + i) 
                records.append(record)
                i += 1
        sep_comma = ','
        run_sql(query2 + sep_comma.join(records))
        query3 = """UPDATE bskBASKET
                    SET    date_modification='%s'
                    WHERE """ % now
        query3 += sep_or.join(map(lambda x: 'id=' + str(x), bskids))
        run_sql(query3)
        return len(bskids)
    return 0       

def get_basket_content(bskid, format='hb'):
    """Get all records for a given basket."""
    query = """
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
                        extern.format='%(format)s')
                    LEFT JOIN bibfmt intern
                    ON (rec.id_bibrec_or_bskEXTREC=intern.id_bibrec AND
                        intern.format='%(format)s')

    WHERE rec.id_bskBASKET=%(id)i
          
    GROUP BY rec.id_bibrec_or_bskEXTREC

    ORDER BY rec.score
    """
    params = {'format': escape_string(format),
              'id': int(bskid)}
    res = run_sql(query% params)
    if res:
        query2 = "UPDATE bskBASKET SET nb_views=nb_views+1 WHERE id=%i"
        run_sql(query2 % int(bskid))
        return res
    return ()

############################ Group baskets ####################################


def get_group_baskets_infos(gid):
    """
    get useful infos (see below) for every basket of a group
    @param gid: group id (int)
    @return a tuple of (id,
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
    WHERE ub.id_usergroup=%i AND NOT(ub.share_level='NO')

    GROUP BY bsk.id
    """
    gid = int(gid)
    res = run_sql(query%gid)
    if res:
        return res
    return ()

def get_all_group_baskets_names(uid,
                                min_rights=cfg_webbasket_share_levels['ADDCMT']):
    """ for a given user returns every group baskets in which he can <min_rights>
    return a list of tuples: (bskid, bsk_name, group_name)
    """
    uid = int(uid)
    try:
        min_rights_num = cfg_webbasket_share_levels_ordered.index(min_rights)
    except ValueError:
        return ()
    groups = get_groups_user_member_of(uid)
    if groups:
        where_clause = '('
        for (group_id, group_name) in groups[:-1]:
            where_clause += 'ugbsk.id_usergroup=%i OR ' % int(group_id)
        where_clause += 'ugbsk.id_usergroup=%i)' % int(groups[-1][0])
        where_clause += ' AND (' 
        for right in cfg_webbasket_share_levels_ordered[min_rights_num:-1]:
            where_clause += "ugbsk.share_level = '%s' OR " % right
        where_clause += "ugbsk.share_level = '%s')" % cfg_webbasket_share_levels_ordered[-1]
        query = """
        SELECT bsk.id,
               bsk.name,
               ug.name
        FROM usergroup ug JOIN usergroup_bskBASKET ugbsk
                          ON ug.id=ugbsk.id_usergroup
                          JOIN bskBASKET bsk
                          ON bsk.id=ugbsk.id_bskBASKET
        WHERE %s AND NOT(ugbsk.share_level='NO')
        ORDER BY ug.name"""
        return run_sql(query % where_clause)
    return ()

def is_shared_to(bskids):
    """For each bskid in bskids get id of group.
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
        for bskid in bskids[:-1]:
            query += "b.id=%i OR "% int(bskid)
        query += "b.id=%i "% int(bskids[-1])
    query += "GROUP BY b.id"
    res = run_sql(query)
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
                         ON (bsk.id=ubsk.id_bskBASKET AND ubsk.id_user=%i)
                         LEFT JOIN bskREC rec
                         ON (bsk.id=rec.id_bskBASKET)
                         LEFT JOIN usergroup_bskBASKET ugbsk
                         ON (ugbsk.id_bskBASKET=bsk.id AND ugbsk.id_usergroup=0)
                      
    WHERE  bsk.id_owner!=%i
                                 
    GROUP BY bsk.id
    """
    uid = int(uid)
    params = (uid, uid)
    res = run_sql(query%params)
    if res:
        return res
    return ()
    
def count_external_baskets(uid):
    """return number of external baskets user has subscribed to"""
    query = """
    SELECT count(ubsk.id_bskBASKET)
    FROM   user_bskBASKET ubsk LEFT JOIN bskBASKET bsk
                               ON (bsk.id=ubsk.id_bskBASKET AND ubsk.id_user=%i)
    WHERE  bsk.id_owner!=%i
    """
    return __wash_count(run_sql(query % (int(uid), int(uid))))

def get_all_external_baskets_names(uid,
                                   min_rights=cfg_webbasket_share_levels['ADDCMT']):
    
    """ for a given user returns every basket which he has subscribed to and in which
    he can <min_rights>
    return a list of tuples: (bskid, bsk_name)
    """
    uid = int(uid)
    try:
        min_rights_num = cfg_webbasket_share_levels_ordered.index(min_rights)
    except ValueError:
        return ()
    where_clause = ' AND ('
    for right in cfg_webbasket_share_levels_ordered[min_rights_num:-1]:
        where_clause += "ugbsk.share_level = '%s' OR " % right
    where_clause += "ugbsk.share_level = '%s')" % cfg_webbasket_share_levels_ordered[-1]
    query = """
    SELECT bsk.id,
           bsk.name
    FROM bskBASKET bsk JOIN usergroup_bskBASKET ugbsk
                       ON bsk.id=ugbsk.id_bskBASKET
                       JOIN user_bskBASKET ubsk
                       ON ubsk.id_bskBASKET=bsk.id
    WHERE ugbsk.id_usergroup=0 AND
          ubsk.id_user=%i AND
          NOT(bsk.id_owner=%i) AND
          NOT(ugbsk.share_level='NO')
          %s
    """
    params = (uid, uid, where_clause)
    return run_sql(query % params)


############################ Public access ####################################

def get_public_basket_infos(bskid):
    """return (id, name, date modification, nb of views, id of owner, nickname of owner, rights for public access) 
    for a given basket"""
    basket = ()
    query1 = """SELECT bsk.id,
                       bsk.name,
                       DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                       bsk.nb_views,
                       bsk.id_owner,
                       user.nickname
                FROM bskBASKET bsk LEFT JOIN user
                                   ON bsk.id_owner=user.id
                WHERE bsk.id=%i"""
    res1 = run_sql(query1 % int(bskid))
    if len(res1):
        basket = list(res1[0])
        query2 = """SELECT share_level
                    FROM usergroup_bskBASKET
                    WHERE id_usergroup=0 and id_bskBASKET=%i"""
        res2 = run_sql(query2 % int(bskid))
        if res2:
            basket.append(res2[0][0])
        else:
            basket.append(None)
    return basket
    
def get_basket_general_infos(bskid):
    """return information about a basket, suited for public access.
    @return a (id, name, date of modification, nb of views, nb of records, id of owner) tuple
    """
    query = """SELECT bsk.id,
                      bsk.name,
                      DATE_FORMAT(bsk.date_modification, '%%Y-%%m-%%d %%H:%%i:%%s'),
                      bsk.nb_views,
                      count(rec.id_bibrec_or_bskEXTREC),
                      bsk.id_owner

    FROM   bskBASKET bsk LEFT JOIN bskREC rec
                         ON bsk.id=rec.id_bskBASKET
    WHERE bsk.id=%i

    GROUP BY bsk.id"""
    res = run_sql(query % int(bskid))
    if res:
        query2 = "UPDATE bskBASKET SET nb_views=nb_views+1 WHERE id=%i"
        run_sql(query2 % int(bskid))
        return res
    return ()

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
    if order==2:
        query += 'ORDER BY bsk.nb_views'
    elif order==3:
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
    query += "LIMIT %i,%i" % (inf_limit, max_number)

    return run_sql(query)
    
def is_public(bskid):
    """return 1 if basket is public, 0 else."""
    query = "SELECT count(id_usergroup) FROM usergroup_bskBASKET WHERE id_bskBASKET=%i AND id_usergroup=0"
    return __wash_count(run_sql(query % int(bskid)))
    
def subscribe(uid, bskid):
    """user uid subscribes to basket bskid"""
    query1 = "SELECT count(id_user) FROM user_bskBASKET WHERE id_user=%i AND id_bskBASKET=%i"
    if not(__wash_count(run_sql(query1 % (int(uid), int(bskid))))):
        query2 = "INSERT INTO user_bskBASKET (id_user, id_bskBASKET) VALUES (%i,%i)"
        run_sql(query2 % (int(uid), int(bskid)))
        
def unsubscribe(uid, bskid):
    """unsubscribe from basket"""
    query = "DELETE FROM user_bskBASKET WHERE id_user=%i AND id_bskBASKET=%i"
    run_sql(query % (int(uid), int(bskid)))
    
def count_subscribers(uid, bskid):
    """ Return a (number of users, number of groups, number of alerts) tuple """
    query_groups = """SELECT count(id_usergroup)
                      FROM usergroup_bskBASKET
                      WHERE id_bskBASKET=%i and NOT(share_level='NO')
                      GROUP BY id_bskBASKET"""
    nb_groups = __wash_count(run_sql(query_groups % bskid))
    query_users = """SELECT count(id_user)
                     FROM user_bskBASKET
                     WHERE id_bskBASKET=%i AND id_user!=%i
                     GROUP BY id_bskBASKET"""
    nb_users = __wash_count(run_sql(query_users % (bskid, uid)))
    query_alerts = """SELECT count(id_query)
                      FROM user_query_basket
                      WHERE id_basket=%i
                      GROUP BY id_basket"""
    nb_alerts = __wash_count(run_sql(query_alerts % bskid))
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
               WHERE ugb.id_bskBASKET=%i 
               ORDER BY ugb.id_usergroup"""
    return run_sql(query % int(bskid))
        
        
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
                      
    WHERE  bskcmt.id_bskBASKET=%i AND
           bskcmt.id_bibrec_or_bskEXTREC=%i

    ORDER BY bskcmt.date_creation
    """
    bskid = int(bskid)
    recid = int(recid)
    res = run_sql(query % (bskid, recid))
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
                      
    WHERE  bskcmt.id=%i
    """
    cmtid = int(cmtid)
    res = run_sql(query % cmtid)
    if res:
        return res[0]
    return out
    
def save_comment(uid, bskid, recid, title, body):
    """Save a given comment in table bskRECORDCOMMENT"""
    date = convert_datestruct_to_datetext(localtime())
    query = """
    INSERT INTO bskRECORDCOMMENT
           (id_user,
            id_bskBASKET,
            id_bibrec_or_bskEXTREC,
            title,
            body,
            date_creation)
    VALUES (%i, %i
    , %i, '%s', '%s', '%s')"""
    params = (uid, bskid, recid, escape_string(title), escape_string(body), date)
    res = run_sql(query % params)
    if res:
        return int(res)
    return 0

def delete_comment(bskid, recid, cmtid):
    """Delete a comment on an item of a basket"""
    query = """DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET=%i AND id_bibrec_or_bskEXTREC=%i AND id=%i"""
    run_sql(query % (int(bskid), int(recid), int(cmtid)))

########################## Usergroup functions ################################

def get_group_infos(uid):
    """Get for each group a user is member of its uid, name and number of baskets."""
    query = """SELECT g.id,
                      g.name,
                      count(ugb.id_bskBASKET)
               FROM usergroup g LEFT JOIN user_usergroup ug,
                                          usergroup_bskBASKET ugb
                                ON (g.id=ug.id_usergroup
                                            AND
                                    g.id=ugb.id_usergroup)
               WHERE ug.id_user=%i AND NOT(ugb.share_level='NO')
               GROUP BY g.id
               ORDER BY g.name"""
    uid = int(uid)
    res = run_sql(query% uid)
    return res  

def count_groups_user_member_of(uid):
    """Return number of groups user has joined."""
    query = 'SELECT count(id_usergroup) FROM user_usergroup WHERE id_user=%i'
    return __wash_count(run_sql(query % int(uid)))

def get_groups_user_member_of(uid):
    """
    Get uids and names of groups user is member of.
    @param uid: user id (int)
    @return a tuple of (group_id, group_name) tuples
    """
    query = """
    SELECT g.id,
           g.name
    FROM usergroup g JOIN user_usergroup ug
                   ON (g.id=ug.id_usergroup)
    WHERE ug.id_user=%i
    ORDER BY g.name
    """
    params = int(uid)
    res = run_sql(query%params)
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
