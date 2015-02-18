# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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

"""Every db-related function of module webmessage"""

__revision__ = "$Id$"

from time import localtime, mktime
from invenio.legacy.dbquery import run_sql
from invenio.modules.messages.config import \
    CFG_WEBMESSAGE_STATUS_CODE, \
    CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA, \
    CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES, \
    CFG_WEBMESSAGE_DAYS_BEFORE_DELETE_ORPHANS
from invenio.utils.date import datetext_default, \
                              convert_datestruct_to_datetext
from invenio.legacy.websession.websession_config import CFG_WEBSESSION_USERGROUP_STATUS

from sqlalchemy.exc import OperationalError


def check_user_owns_message(uid, msgid):
    """
    Checks whether a user owns a message
    @param uid:   user id
    @param msgid: message id
    @return: 1 if the user owns the message, else 0
    """
    query  = """SELECT count(*)
                FROM   user_msgMESSAGE
                WHERE id_user_to=%s AND
                      id_msgMESSAGE=%s"""
    params = (uid, msgid)
    res = run_sql(query, params)
    return int(res[0][0])

def get_message(uid, msgid):
    """
    get a message with its status
    @param uid: user id
    @param msgid: message id
    @return: a (message_id,
               id_user_from,
               nickname_user_from,
               sent_to_user_nicks,
               sent_to_group_names,
               subject,
               body,
               sent_date,
               received_date,
               status)
     formed tuple or 0 (ZERO) if none found
    """
    query = """SELECT m.id,
                      m.id_user_from,
                      u.nickname,
                      m.sent_to_user_nicks,
                      m.sent_to_group_names,
                      m.subject,
                      m.body,
                      DATE_FORMAT(m.sent_date, '%%Y-%%m-%%d %%H:%%i:%%s'),
                      DATE_FORMAT(m.received_date, '%%Y-%%m-%%d %%H:%%i:%%s'),
                      um.status
               FROM   msgMESSAGE m,
                      user_msgMESSAGE um,
                      user u
               WHERE  m.id=%s AND
                      um.id_msgMESSAGE=%s AND
                      um.id_user_to=%s AND
                      u.id=m.id_user_from"""
    params = (msgid, msgid, uid)
    res = run_sql(query, params)
    if res:
        return res[0]
    else:
        return 0

def set_message_status(uid, msgid, new_status):
    """
    Change the status of a message (e.g. from "new" to "read").
    the status is a single character string, specified in constant
    CFG_WEBMESSAGE_STATUS_CODE in file webmessage_config.py
    examples:
        N: New message
        R: alreay Read message
        M: reminder
    @param uid:        user ID
    @param msgid:      Message ID
    @param new_status: new status. Should be a single character
    @return: 1 if succes, 0 if not
    """

    return int(run_sql("""UPDATE user_msgMESSAGE
                             SET    status=%s
                           WHERE  id_user_to=%s AND
                                  id_msgMESSAGE=%s""",
                       (new_status, uid, msgid)))

def get_nb_new_messages_for_user(uid):
    """ Get number of new mails for a given user
    @param uid: user id (int)
    @return: number of new mails as int.
    """
    update_user_inbox_for_reminders(uid)
    new_status = CFG_WEBMESSAGE_STATUS_CODE['NEW']
    res = run_sql("""SELECT count(id_msgMESSAGE)
                       FROM user_msgMESSAGE
                      WHERE id_user_to=%s AND
                       BINARY status=%s""",
                  (uid, new_status))
    if res:
        return res[0][0]
    return 0

def get_nb_readable_messages_for_user(uid):
    """ Get number of mails of a fiven user. Reminders are not counted
    @param uid: user id (int)
    @return: number of messages (int)
    """
    reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
    query = """SELECT count(id_msgMESSAGE)
               FROM user_msgMESSAGE
               WHERE id_user_to=%s AND
                     BINARY status!=%s"""
    params = (uid, reminder_status)
    res = run_sql(query, params)
    if res:
        return res[0][0]
    return 0


def get_all_messages_for_user(uid):
    """
    Get all messages for a user's inbox, without the eventual
    non-expired reminders.

    @param uid: user id
    @return: [(message_id,
              id_user_from,
              nickname_user_from,
              message_subject,
              message_sent_date,
              message_status)]
    """
    update_user_inbox_for_reminders(uid)
    reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
    return run_sql("""SELECT  m.id,
                       m.id_user_from,
                       u.nickname,
                       m.subject,
                       DATE_FORMAT(m.sent_date, '%%Y-%%m-%%d %%H:%%i:%%s'),
                       um.status
                FROM   user_msgMESSAGE um,
                       msgMESSAGE m,
                       user u
                WHERE  um.id_user_to = %s AND
                       !(BINARY um.status=%s) AND
                       um.id_msgMESSAGE=m.id AND
                       u.id=m.id_user_from
                ORDER BY m.sent_date DESC
                """, (uid, reminder_status))

def count_nb_messages(uid):
    """
    @param uid: user id
    @return: integer of number of messages a user has, 0 if none
    """
    uid = int(uid)
    query = """SELECT count(id_user_to)
               FROM   user_msgMESSAGE
               WHERE  id_user_to=%s
            """
    res = run_sql(query, (uid, ))
    if res:
        return int(res[0][0])
    else:
        return 0

def delete_message_from_user_inbox(uid, msg_id):
    """
    Delete message from users inbox
    If this message was does not exist in any other user's inbox,
    delete it permanently from the database
    @param uid: user id
    @param msg_id: message id
    @return: integer 1 if delete was successful, integer 0 else
    """
    query1 = """DELETE FROM user_msgMESSAGE
                WHERE id_user_to=%s AND
                      id_msgMESSAGE=%s"""
    params1 = (uid, msg_id)
    res1 = run_sql(query1, params1)
    check_if_need_to_delete_message_permanently([msg_id])
    return int(res1)

def check_if_need_to_delete_message_permanently(msg_ids):
    """
    Checks if a list of messages exist in anyone's inbox, if not,
    delete them permanently
    @param msg_id: sequence of message ids
    @return: number of deleted messages
    """
    if not((type(msg_ids) is list) or (type(msg_ids) is tuple)):
        msg_ids = [msg_ids]
    query1 = """SELECT count(id_msgMESSAGE)
                FROM user_msgMESSAGE
                WHERE id_msgMESSAGE=%s"""
    messages_to_delete = []
    for msg_id in msg_ids:
        nb_users = int(run_sql(query1, (msg_id,))[0][0])
        if nb_users == 0:
            messages_to_delete.append(int(msg_id))

    if len(messages_to_delete) > 0:
        query2 = """DELETE FROM msgMESSAGE
                    WHERE"""
        params2 = []
        for msg_id in messages_to_delete[0:-1]:
            query2 += " id=%s OR"
            params2.append(msg_id)
        query2 += " id=%s"
        params2.append(messages_to_delete[-1])

        run_sql(query2, tuple(params2))
    return len(messages_to_delete)

def delete_all_messages(uid):
    """
    Delete all messages of a user (except reminders)
    @param uid: user id
    @return: the number of messages deleted
    """
    reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
    query1 = """SELECT id_msgMESSAGE
               FROM user_msgMESSAGE
               WHERE id_user_to=%s AND
                     NOT(BINARY status like %s)"""
    params = (uid, reminder_status)
    msg_ids = map(get_element, run_sql(query1, params))

    query2 = """DELETE FROM user_msgMESSAGE
                WHERE id_user_to=%s AND
                NOT(BINARY status like %s)"""
    nb_messages = int(run_sql(query2, params))
    check_if_need_to_delete_message_permanently(msg_ids)
    return nb_messages

def get_uids_from_nicks(nicks):
    """
    Get the association uid/nickname of given nicknames
    @param nicks: list or sequence of strings, each string being a nickname
    @return: a dictionary {nickname: uid}
    """
    # FIXME: test case
    if not((type(nicks) is list) or (type(nicks) is tuple)):
        nicks = [nicks]
    users = {}
    query = "SELECT nickname, id FROM user WHERE BINARY nickname IN ("
    query_params = ()
    if len(nicks)> 0:
        for nick in nicks:
            users[nick] = None
        users_keys = users.keys()
        for nick in users_keys[0:-1]:
            query += "%s,"
            query_params += (nick,)
        query += "%s)"
        query_params += (users_keys[-1],)
        res = run_sql(query, query_params)
        def enter_dict(couple):
            """ takes a a tuple and enters it into dict users """
            users[couple[0]] = int(couple[1])
        map(enter_dict, res)
    return users

def get_nicks_from_uids(uids):
    """
    Get the association uid/nickname of given uids
    @param uids: list or sequence of uids
    @return: a dictionary {uid: nickname} where empty value is possible
    """
    if not((type(uids) is list) or (type(uids) is tuple)):
        uids = [uids]
    users = {}
    query = "SELECT id, nickname FROM user WHERE id in("
    query_params = []
    if len(uids) > 0:
        for uid in uids:
            users[uid] = None
        for uid in users.keys()[0:-1]:
            query += "%s,"
            query_params.append(uid)
        query += "%s)"
        query_params.append(users.keys()[-1])
        res = run_sql(query, tuple(query_params))
        for (user_id, nickname) in res:
            users[int(user_id)] = nickname
    return users

def get_uids_from_emails(emails):
    """
    Get the association uid/nickname of given nicknames
    @param nicks: list or sequence of strings, each string being a nickname
    @return: a dictionary {nickname: uid}
    """
    # FIXME: test case
    if not((type(emails) is list) or (type(emails) is tuple)):
        emails = [emails]
    users = {}
    query = "SELECT email, id FROM user WHERE BINARY email IN ("
    query_params = ()
    if len(emails)> 0:
        for mail in emails:
            users[mail] = None
        users_keys = users.keys()
        for mail in users_keys[0:-1]:
            query += "%s,"
            query_params += (mail,)
        query += "%s)"
        query_params += (users_keys[-1],)
        res = run_sql(query, query_params)
        def enter_dict(couple):
            """ takes a a tuple and enters it into dict users """
            users[couple[0]] = int(couple[1])
        map(enter_dict, res)
    return users


def get_gids_from_groupnames(groupnames):
    """
    Get the gids of given groupnames
    @param groupnames: list or sequence of strings, each string being a groupname
    @return: a dictionary {groupname: gid}
    """
    # FIXME: test case
    if not((type(groupnames) is list) or (type(groupnames) is tuple)):
        groupnames = [groupnames]
    groups = {}
    query = "SELECT name, id FROM usergroup WHERE BINARY name IN ("
    query_params = ()
    if len(groupnames) > 0:
        for groupname in groupnames:
            groups[groupname] = None
            groups_keys = groups.keys()
        for groupname in groups_keys[0:-1]:
            query += "%s,"
            query_params += (groupname,)
        query += "%s)"
        query_params += (groups_keys[-1],)
        res = run_sql(query, query_params)
        def enter_dict(couple):
            """ enter a tuple into dictionary groups """
            groups[couple[0]] = int(couple[1])
        map(enter_dict, res)
    return groups

def get_uids_members_of_groups(gids):
    """
    Get the distinct ids of users members of given groups.
    @param groupnames: list or sequence of group ids
    @return: a list of uids.
    """
    if not((type(gids) is list) or (type(gids) is tuple)):
        gids = [gids]
    query = """SELECT DISTINCT id_user
               FROM user_usergroup
               WHERE user_status!=%s AND (
            """
    query_params = [CFG_WEBSESSION_USERGROUP_STATUS['PENDING']]
    if len(gids) > 0:
        for gid in gids[0:-1]:
            query += " id_usergroup=%s OR"
            query_params.append(gid)
        query += " id_usergroup=%s)"
        query_params.append(gids[-1])
        return map(get_element, run_sql(query, tuple(query_params)))
    return []

def user_exists(uid):
    """ checks if a user exists in the system, given his uid. return 0 or 1"""
    query = "SELECT count(id) FROM user WHERE id=%s GROUP BY id"
    res = run_sql(query, (uid, ))
    if res:
        return int(res[0][0])
    return 0

def create_message(uid_from,
                   users_to_str="",
                   groups_to_str="",
                   msg_subject="",
                   msg_body="",
                   msg_send_on_date=datetext_default):
    """
    Creates a message in the msgMESSAGE table. Does NOT send the message.
    This function is like a datagramPacket...
    @param uid_from: uid of the sender (int)
    @param users_to_str: a string, with nicknames separated by semicolons (';')
    @param groups_to_str: a string with groupnames separated by semicolons
    @param msg_subject: string containing the subject of the message
    @param msg_body: string containing the body of the message
    @param msg_send_on_date: date on which message must be sent. Has to be a
                             datetex format (i.e. YYYY-mm-dd HH:MM:SS)
    @return: id of the created message
    """
    now = convert_datestruct_to_datetext(localtime())
    msg_id = run_sql("""INSERT INTO msgMESSAGE(id_user_from,
                                      sent_to_user_nicks,
                                      sent_to_group_names,
                                      subject,
                                      body,
                                      sent_date,
                                      received_date)
             VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                     (uid_from,
                      users_to_str,
                      groups_to_str,
                      msg_subject,
                      msg_body,
                      now,
                      msg_send_on_date))
    return int(msg_id)

def send_message(uids_to, msgid, status=CFG_WEBMESSAGE_STATUS_CODE['NEW']):
    """
    Send message to uids
    @param uids: sequence of user ids
    @param msg_id: id of message
    @param status: status of the message. (single char, see webmessage_config.py).
    @return: a list of users having their mailbox full
    """
    if not((type(uids_to) is list) or (type(uids_to) is tuple)):
        uids_to = [uids_to]
    user_problem = []
    if len(uids_to) > 0:
        users_quotas = check_quota(CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES - 1)
        query = """INSERT INTO user_msgMESSAGE (id_user_to, id_msgMESSAGE,
                    status) VALUES """
        fixed_value = ",%s,%s)"
        query_params = []
        def not_users_quotas_has_key(key):
            """ not(is key in users over  quota?)"""
            return not(key in users_quotas)
        user_ids_to = filter(not_users_quotas_has_key, uids_to)
        user_problem = filter(users_quotas.has_key, uids_to)
        if len(user_ids_to) > 0:
            for uid_to in user_ids_to[0:-1]:
                query += "(%%s%s," % fixed_value
                query_params += [uid_to, msgid, status]
            query += "(%%s%s" % fixed_value
            query_params += [user_ids_to[-1], msgid, status]
            run_sql(query, tuple(query_params))
    return user_problem


def check_quota(nb_messages):
    """
    @param nb_messages: max number of messages a user can have
    @return: a dictionary of users over-quota
    """
    from invenio.legacy.webuser import collect_user_info
    from invenio.modules.access.control import acc_is_user_in_role, acc_get_role_id
    no_quota_role_ids = [acc_get_role_id(role) for role in CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA]
    res = {}
    for uid, n in run_sql("SELECT id_user_to, COUNT(id_user_to) FROM user_msgMESSAGE GROUP BY id_user_to HAVING COUNT(id_user_to) > %s", (nb_messages, )):
        user_info = collect_user_info(uid)
        for role_id in no_quota_role_ids:
            if acc_is_user_in_role(user_info, role_id):
                break
        else:
            res[uid] = n
    return res

def update_user_inbox_for_reminders(uid):
    """
    Updates user's inbox with any reminders that should have arrived
    @param uid: user id
    @return: integer number of new expired reminders
    """
    now =  convert_datestruct_to_datetext(localtime())
    reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
    new_status = CFG_WEBMESSAGE_STATUS_CODE['NEW']
    query1 = """SELECT m.id
                FROM   msgMESSAGE m,
                       user_msgMESSAGE um
                WHERE  um.id_user_to=%s AND
                       um.id_msgMESSAGE=m.id AND
                       m.received_date<=%s AND
                       um.status like binary %s
                """
    params1 = (uid, now, reminder_status)
    res_ids = run_sql(query1, params1)
    out = len(res_ids)
    if (out>0):
        query2 = """UPDATE user_msgMESSAGE
                    SET    status=%s
                    WHERE  id_user_to=%s AND ("""
        query_params = [new_status, uid]
        for msg_id in res_ids[0:-1]:
            query2 += "id_msgMESSAGE=%s OR "
            query_params.append(msg_id[0])
        query2 += "id_msgMESSAGE=%s)"
        query_params.append(res_ids[-1][0])
        run_sql(query2, tuple(query_params))
    return out

def get_nicknames_like(pattern):
    """get nicknames like pattern"""
    if pattern:
        try:
            res = run_sql("SELECT nickname FROM user WHERE nickname RLIKE %s", (pattern,))
        except OperationalError:
            res = ()
        return res
    return ()

def get_groupnames_like(uid, pattern):
    """Get groupnames like pattern. Will return only groups that user is allowed to see
    """
    groups = {}
    if pattern:
        # For this use case external groups are like invisible one
        query1 = "SELECT id, name FROM usergroup WHERE name RLIKE %s AND join_policy like 'V%%' AND join_policy<>'VE'"
        try:
            res = run_sql(query1, (pattern,))
        except OperationalError:
            res = ()
        # The line belows inserts into groups dictionary every tuple the database returned,
        # assuming field0=key and field1=value
        map(lambda x: groups.setdefault(x[0], x[1]), res)
        query2 = """SELECT g.id, g.name
                    FROM usergroup g, user_usergroup ug
                    WHERE g.id=ug.id_usergroup AND ug.id_user=%s AND g.name RLIKE %s"""
        try:
            res = run_sql(query2, (uid, pattern))
        except OperationalError:
            res = ()
        map(lambda x: groups.setdefault(x[0], x[1]), res)
    return groups

def get_element(sql_res):
    """convert mySQL output
    @param x: a tuple like this: (6789L,)
    @return: integer conversion of the number in tuple
    """
    return int(sql_res[0])

def clean_messages():
    """ Cleans msgMESSAGE table"""
    current_time = localtime()
    seconds = mktime(current_time)
    seconds -= CFG_WEBMESSAGE_DAYS_BEFORE_DELETE_ORPHANS * 86400
    sql_date = convert_datestruct_to_datetext(localtime(seconds))
    deleted_items = 0
    #find id and email from every user who has got an email
    query1 = """SELECT distinct(umsg.id_user_to),
                       user.email
                FROM user_msgMESSAGE umsg
                LEFT JOIN user ON
                     umsg.id_user_to=user.id"""
    res1 = run_sql(query1)
    # if there is no email, user has disappeared
    users_deleted = map(lambda u: int(u[0]), filter(lambda x: x[1] is None, res1))
    # find ids from messages in user's inbox
    query2 = """SELECT distinct(umsg.id_msgMESSAGE),
                       msg.id
                FROM user_msgMESSAGE umsg
                LEFT JOIN msgMESSAGE msg ON
                     umsg.id_msgMESSAGE=msg.id"""
    res2 = run_sql(query2)
    # if there is no id, message was deleted from table msgMESSAGE...
    messages_deleted = map(lambda u: int(u[0]), filter(lambda x: x[1] is None, res2))
    def tuplize(el1, el2):
        return str(el1) + ',' + str(el2)
    if len(users_deleted) or len(messages_deleted):
        # Suppress every referential error from user_msgMESSAGE
        query3 = "DELETE FROM user_msgMESSAGE WHERE "
        query_params = []
        if len(users_deleted):
            query3 += "id_user_to IN (%s)"
            query_params.append(reduce(tuplize, users_deleted))
            if len(messages_deleted):
                query3 += ' OR '
        if len(messages_deleted):
            query3 += "id_msgMESSAGE IN (%s)"
            query_params.append(reduce(tuplize, messages_deleted))
        deleted_items = int(run_sql(query3, tuple(query_params)))
    # find every message that is nobody's inbox
    query4 = """SELECT msg.id
                FROM msgMESSAGE msg
                     LEFT JOIN user_msgMESSAGE umsg
                               ON msg.id=umsg.id_msgMESSAGE
                WHERE msg.sent_date<%s
                GROUP BY umsg.id_msgMESSAGE
                HAVING count(umsg.id_msgMESSAGE)=0
                """
    res4 = map(lambda x: x[0], run_sql(query4, (sql_date, )))
    if len(res4):
        # delete these messages
        query5 = "DELETE FROM msgMESSAGE WHERE "
        query5 += "id IN (%s)"
        deleted_items += int(run_sql(query5, (reduce(tuplize, res4), )))
    return deleted_items

