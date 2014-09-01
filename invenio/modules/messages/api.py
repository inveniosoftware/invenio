## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""API to interact with the database."""

from datetime import datetime
from flask import current_app
from invenio.ext.sqlalchemy import db
from invenio.ext.restful import pagination
from invenio.ext.restful.errors import InvalidPageError
from invenio.base.globals import cfg
from invenio.modules.accounts.models import User
from .models import MsgMESSAGE, UserMsgMESSAGE
from .util import (filter_messages_from_user_with_status,
                   filter_all_messages_from_user,
                   filter_user_message)
from .errors import (MessageNotFoundError, MessageNotDeletedError,
                     MessagesNotFetchedError, MessageNotCreatedError)


def check_user_owns_message(uid, msgid):
    """Check whether a user owns a message.

    :param uid: user identifier
    :param msgid: message identifier
    :returns: bool -- True if the user owns the message, else False
    """
    user_msg = UserMsgMESSAGE.query.filter_by(id_user_to=uid,
                                              id_msgMESSAGE=msgid).first()
    if user_msg is None:
        return False
    return True


def check_user_owns_message_and_count(uid, msgid):
    """Check whether a user owns a message

    :param uid:   user id
    :param msgid: message id
    :return: number of messages own by user
    """
    return db.session.query(db.func.count('*')).\
        select_from(UserMsgMESSAGE).\
        filter(filter_user_message(uid, msgid)).scalar()


def message_exists(msgid):
    """Check if a message with exists in the database.

    :param msgid: message identifier
    :returns: bool -- True if msgid exists else False
    """
    m = MsgMESSAGE.query.get(id=msgid)
    if m is None:
        return False
    return True


def get_message(msgid):
    """ Fetch a message from the table msgMESSAGE.

    :param msgid: the id of the message
    :returns: an object of type MsgMESSAGE
    """
    try:
        return MsgMESSAGE.query.filter(MsgMESSAGE.id == int(msgid)).one()
    except Exception:
        raise MessageNotFoundError(
            message="Message cannot be found",
            code=404
        )


def get_message_from_user_inbox(uid, msgid):
    """Get a message with its status and sender nickname.

    :param uid: user identifier
    :param msgid: message identifier
    :returns: exactly one message or raise an exception.
    """
    try:
        return UserMsgMESSAGE.query.options(
            db.joinedload_all(UserMsgMESSAGE.message, MsgMESSAGE.user_from)
        ).options(
            db.joinedload(UserMsgMESSAGE.user_to)
        ).filter(filter_user_message(uid, msgid)).one()
    except Exception:
        raise MessageNotFoundError(
            message="Message cannot be found",
            code=404
        )


def set_message_status(uid, msgid, new_status):
    """Change the status of a message (e.g. from "new" to "read").

    the status is a single character string, specified in constant
    CFG_WEBMESSAGE_STATUS_CODE in file webmessage_config.py
    examples:
        N: New message
        R: already Read message
        M: reminder
    :param uid:        user ID
    :param msgid:      Message ID
    :param new_status: new status. Should be a single character
    :returns: int -- 1 if success, 0 if not
    """
    return db.session.query(UserMsgMESSAGE).filter(
        filter_user_message(uid, msgid)
    ).update({UserMsgMESSAGE.status: new_status})


def update_user_inbox_for_reminders(uid):
    """Update user's inbox with any reminders that should have arrived.

    :param uid: user id
    :returns: int -- number of new expired reminders
    """
    reminder_status = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['REMINDER']
    new_status = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['NEW']
    expired_reminders = db.session.query(
        UserMsgMESSAGE.id_msgMESSAGE
    ).join(UserMsgMESSAGE.message).filter(db.and_(
        UserMsgMESSAGE.id_user_to == uid,
        UserMsgMESSAGE.status.like(reminder_status),
        MsgMESSAGE.received_date <= datetime.now())
    ).all()

    if len(expired_reminders):
        filter = db.and_(
            UserMsgMESSAGE.id_user_to == uid,
            UserMsgMESSAGE.id_msgMESSAGE.in_(
                [i for i, in expired_reminders]))

        res = UserMsgMESSAGE.query.filter(filter).\
            update({UserMsgMESSAGE.status: new_status},
                   synchronize_session='fetch')
        return res


def get_nb_new_messages_for_user(uid):
    """ Get the number of new mails for a given user.

    :param uid: user id (int)
    :return: number of new mails as int.
    """
    update_user_inbox_for_reminders(uid)
    new_status = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['NEW']
    return db.session.query(
        db.func.count(UserMsgMESSAGE.id_msgMESSAGE)
    ).select_from(UserMsgMESSAGE).filter(
        filter_messages_from_user_with_status(uid, new_status)).scalar()


def get_nb_readable_messages_for_user(uid):
    """ Get number of mails of a given user , reminders are not counted.

    :param uid: user id (int)
    :returns: int -- number of messages
    """
    return db.session.query(
        db.func.count(UserMsgMESSAGE.id_msgMESSAGE)
    ).select_from(UserMsgMESSAGE).filter(
        filter_all_messages_from_user(uid)).scalar()


def get_all_messages_for_user(uid):
    """Get all messages for a user's inbox.

    There are no expired reminders.

    :param uid: user identifier
    :returns: list -- a list of objects of type UserMsgMESSAGE
    """
    try:
        update_user_inbox_for_reminders(uid)
        reminder = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['REMINDER']
        return UserMsgMESSAGE.query.join(MsgMESSAGE).filter(
            MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
            UserMsgMESSAGE.id_user_to == int(uid),
            UserMsgMESSAGE.status != reminder
        ).order_by(MsgMESSAGE.received_date).all()
    except Exception:
        raise MessagesNotFetchedError(
            message="Could not fetch messages",
            code=400
        )


def get_page_of_messages_for_user(uid, page, per_page):
    """Get a list of user's messages according to the page.

    :param uid: user identifier
    :param page: requested page of messages
    :param per_page: the number of results per page
    Returns:
        a RestfulSQLAlchemyPagination object
    """
    if page < 0:
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    if per_page < 0:
        raise InvalidPageError(
            error_msg="Invalid per_page: {}".format(per_page),
            status_code=400
        )
    # query object
    update_user_inbox_for_reminders(uid)
    reminder = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['REMINDER']
    msgs_query = UserMsgMESSAGE.query.join(MsgMESSAGE).filter(
        MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
        UserMsgMESSAGE.id_user_to == int(uid),
        UserMsgMESSAGE.status != reminder
    ).order_by(MsgMESSAGE.id)
    p = pagination.RestfulSQLAlchemyPagination(
        query=msgs_query, page=page, per_page=per_page
    )
    if (page > p.pages):
        raise InvalidPageError(
            error_msg="Invalid page: {}".format(page),
            status_code=400
        )
    return p


def number_of_all_messages_in_inbox_of_user(uid):
    """Get the number of all messages of a user's inbox.

    :param uid: user id
    :returns: int -- number of messages of a user's inbox
    """
    return len(get_all_messages_for_user(uid))


def get_new_messages_for_user(uid):
    """Fetch all new messages.

    :param uid: the user id_user_from
    :returns: -- a list of objects of type UserMsgMESSAGE
    """
    try:
        update_user_inbox_for_reminders(uid)
        NEW = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['NEW']
        return UserMsgMESSAGE.query.join(MsgMESSAGE).filter(
            MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
            UserMsgMESSAGE.id_user_to == int(uid),
            UserMsgMESSAGE.status == NEW).order_by(
            MsgMESSAGE.received_date).all()
    except Exception:
        raise MessagesNotFetchedError(
            message="Could not fetch messages",
            code=400
        )


def number_of_new_messages_for_user(uid):
    """Count the new messages of a user.

    :param uid: the user id
    :returns: int -- the number of the new messages in a user's inbox
    """
    return len(get_new_messages_for_user(uid))


def get_the_read_messages_in_inbox_of_user(uid):
    """Fetch the messages that a user has read already.

    :param uid: the user id
    :returns: -- a list of objects of type UserMsgMESSAGE
    """
    try:
        update_user_inbox_for_reminders(uid)
        READ = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['READ']
        return UserMsgMESSAGE.query.join(MsgMESSAGE).filter(
            MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
            UserMsgMESSAGE.id_user_to == int(uid),
            UserMsgMESSAGE.status == READ).order_by(
            MsgMESSAGE.received_date).all()
    except Exception:
        raise MessagesNotFetchedError(
            message="Could not fetch the messages that are already read",
            code=400
        )


def number_of_read_messages_in_inbox_of_user(uid):
    """Count the read messages of a user.

    :param uid: the user id
    :returns: int -- the number of the new messages in a user's inbox
    """
    return len(get_the_read_messages_in_inbox_of_user(uid))


def count_nb_messages(uid):
    """Count the messages of a user.

    :param uid: user id
    :returns: int -- number of messages a user has, 0 if none
    """
    uid = int(uid)
    return db.session.query(
        db.func.count(UserMsgMESSAGE.id_user_to)
    ).select_from(UserMsgMESSAGE).filter(
        UserMsgMESSAGE.id_user_to == uid).scalar()


def delete_message_from_user_inbox(uid, msg_id):
    """Delete message from users inbox.

    If this message does not exist in any other user's inbox,
    delete it permanently from the database
    :param uid: user id
    :param msg_id: message id
    :returns: int 1 if delete was successful, 0 else
    """
    try:
        res = UserMsgMESSAGE.query.filter(
            filter_user_message(uid, msg_id)).\
            delete(synchronize_session=False)
        check_if_need_to_delete_message_permanently(msg_id)
        if res == 0:
            raise MessageNotDeletedError(
                message="Message could not be deleted",
                code=400
            )
        return res
    except Exception:
        raise MessageNotDeletedError(
            message="Message could not be deleted",
            code=400
        )


def check_if_need_to_delete_message_permanently(msg_ids):
    """Check if a list of messages exist in anyone's inbox.

    Delete them permanently if any user has them in inbox.

    :param msg_id: list of message identifiers
    :returns: int -- number of deleted messages
    """
    if not((type(msg_ids) is list) or (type(msg_ids) is tuple)):
        msg_ids = [msg_ids]

    msg_used = db.session.query(UserMsgMESSAGE.id_msgMESSAGE).filter(
        UserMsgMESSAGE.id_msgMESSAGE.in_(msg_ids)
    ).group_by(UserMsgMESSAGE.id_msgMESSAGE).having(
        db.func.count(UserMsgMESSAGE.id_user_to) > 0).subquery()

    return MsgMESSAGE.query.filter(db.and_(
        MsgMESSAGE.id.in_(msg_ids),
        db.not_(MsgMESSAGE.id.in_(msg_used))
    )).delete(synchronize_session=False)


def delete_all_messages(uid):
    """Delete all messages of a user (except reminders).

    :param uid: user id
    :returns: int -- the number of messages deleted
    """
    try:
        reminder_status = cfg["CFG_WEBMESSAGE_STATUS_CODE"]['REMINDER']
        msg_ids = map(lambda (x, ): x,
                      db.session.query(UserMsgMESSAGE.id_msgMESSAGE).
                      filter(db.and_(
                             UserMsgMESSAGE.id_user_to == uid,
                             UserMsgMESSAGE.status != reminder_status)).
                      all())
        nb_messages = UserMsgMESSAGE.query.filter(
            db.and_(
                UserMsgMESSAGE.id_user_to == uid,
                UserMsgMESSAGE.status != reminder_status
            )
        ).delete(synchronize_session=False)
        if len(msg_ids) > 0:
            check_if_need_to_delete_message_permanently(msg_ids)
        return nb_messages
    except Exception:
        raise MessageNotDeletedError(
            message="Error while deleting all messages",
            code=400
        )


def check_if_user_has_free_space(uid):
    """Check if a user has free space to his inbox.

    :param uid: user id
    :returns: bool -- True if the user has free space in inbox , else False
    """
    users_with_full_mailbox = check_quota(
        cfg["CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES"])
    if uid in users_with_full_mailbox:
        return False
    else:
        return True


def create_message(uid_from,
                   users_to_str="",
                   groups_to_str="",
                   msg_subject="",
                   msg_body="",
                   msg_send_on_date=None):
    """Create and send a message.

    :param uid_from: uid of the sender (int)
    :param users_to_str: a string, with nicknames separated by semicolons (';')
    :param groups_to_str: a string with groupnames separated by semicolons
    :param msg_subject: string containing the subject of the message
    :param msg_body: string containing the body of the message
    :param msg_send_on_date: date on which message must be sent. Has to be a
                             datetex format (i.e. YYYY-mm-dd HH:MM:SS)
    :returns: int -- id of the created message
    """
    if msg_send_on_date is None:
        msg_send_on_date = datetime.strptime(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "%Y-%m-%d %H:%M:%S")
    try:
        m = MsgMESSAGE(id_user_from=uid_from, sent_to_user_nicks=users_to_str,
                       sent_to_group_names=groups_to_str,
                       subject=msg_subject, body=msg_body,
                       sent_date=msg_send_on_date,
                       received_date=msg_send_on_date)
        return m.send()
    except Exception as e:
        current_app.logger.exception(e.args[0])
        raise MessageNotCreatedError(
            message="Message could not be created",
            code=400
        )


def reply_to_sender(msg_id, reply_body, uid):
    """Reply back to sender.

    :param msg_id: the id of the message to which a user wants to reply to
    :param reply_body: the body of the new message
    :param uid: the id of the user that replies back
    """
    m = get_message(msg_id)
    return m.reply_to_sender_only(reply_body=reply_body, user_id=uid)


def check_quota(nb_messages):
    """Check for quota.

    :param nb_messages: max number of messages a user can have
    :returns: a dictionary of users over-quota
    """
    from invenio.legacy.webuser import collect_user_info
    from invenio.modules.access.control import acc_is_user_in_role, \
        acc_get_role_id
    no_quota_role_ids = [acc_get_role_id(role)
                         for role in cfg["CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA"]
                         ]
    res = {}

    stmt = db.select(
        [UserMsgMESSAGE.id_user_to, db.func.count(UserMsgMESSAGE.id_user_to)]
    ).group_by(UserMsgMESSAGE.id_user_to).having(
        db.func.count(UserMsgMESSAGE.id_user_to) > nb_messages)

    db_results = db.engine.execute(stmt)

    for row in db_results:
        uid = row[0]
        nb_of_messages_to_uid = row[1]
        user_info = collect_user_info(uid)
        for role_id in no_quota_role_ids:
            if acc_is_user_in_role(user_info, role_id):
                break
        else:
            res[uid] = nb_of_messages_to_uid
    return res


def clean_messages():
    """ Clean MsgMESSAGE table."""
    msgids_to_delete = []

    all_messages_ids = db.session.query(MsgMESSAGE.id).all()
    all_users_messages_ids = db.session.query(
        UserMsgMESSAGE.id_msgMESSAGE).all()

    # case 1
    # find the ids of the messages that must be deleted
    for msgid in all_messages_ids:
        if msgid not in all_users_messages_ids:
            msgids_to_delete.append(msgid)

    # case 2
    messages_users_dictionary = {}  # dictionary in form {m_id: [uids]}
    #get the distinct message ids from UserMsgMESSAGE
    distinct_mids_in_user_messages = db.session.query(
        UserMsgMESSAGE.id_msgMESSAGE.distinct()
    ).order_by(UserMsgMESSAGE.id_msgMESSAGE).all()

    for mid in distinct_mids_in_user_messages:
        #get the user ids that have mid in their mailbox
        uids_with_mid = db.session.query(UserMsgMESSAGE.id_user_to).filter_by(
            id_msgMESSAGE=mid).order_by(UserMsgMESSAGE.id_user_to).all()
        messages_users_dictionary[mid] = uids_with_mid

    # for every (distinct) message id in the User_MsgMESSAGE table
    for mid in messages_users_dictionary:
        counter_uid_with_mid_not_in_users = 0
        # get the users that have received the message with mid
        for uid in messages_users_dictionary[mid]:
            if uid not in db.session.query(User.id).order_by(User.id).all():
                counter_uid_with_mid_not_in_users += 1
        # if none of the users that has receive the message with mid as id,
        # is not in the system anymore
        if counter_uid_with_mid_not_in_users == \
                len(messages_users_dictionary[mid]):
            msgids_to_delete.append()

    # delete all the messages that their ids belong to the list
    # 'message_to_delete'
    if len(msgids_to_delete) > 0:
        for msgid in msgids_to_delete:
            message_to_delete = MsgMESSAGE.query.filter_by(id=msgid).first()
            db.session.delete(message_to_delete)

        db.session.commit()
