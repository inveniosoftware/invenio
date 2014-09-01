# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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

""" Test for messages restful API."""


from __future__ import print_function
#for the the utc-iso date-time format
from datetime import datetime
from dateutil.tz import tzutc
from invenio.ext.restful.utils import APITestCase
from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite
db = lazy_import('invenio.ext.sqlalchemy.db')


class TestMessagesRestfulAPI(APITestCase):

    """This class tests the restful api for the messages."""

    def setUp(self):
        """Run before each test."""
        from invenio.modules.accounts.models import User

        self.user_a = User(email='user_a@example.com', _password='iamusera',
                           nickname='user_a')
        self.user_b = User(email='user_b@example.com', _password='iamuserb',
                           nickname='user_b')
        try:
            db.session.add(self.user_a)
            db.session.add(self.user_b)
            db.session.commit()
        except Exception:
            db.session.rollback()

        self.create_oauth_token(self.user_a.id, scopes=[""])
        self.create_oauth_token(self.user_b.id, scopes=[""])

    def tearDown(self):
        """Run after every test."""
        from invenio.modules.accounts.models import User

        self.remove_oauth_token()
        User.query.filter(User.nickname.in_([
            self.user_a.nickname,
            self.user_b.nickname,
        ])).delete(synchronize_session=False)
        db.session.commit()

    def test_405_methods_messages_list_resource(self):
        """Test methods that return 405."""
        methods_messages_list_resource = [self.head, self.options, self.patch]
        for m in methods_messages_list_resource:
            m(
                'messageslistresource',
                user_id=self.user_a.id,
                code=405,
            )

    def test_create_message_pass(self):
        """Create a message successfully."""
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        # user_a creates and sends a message to user_b
        message_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat()
        )
        answer = self.post(
            'messageslistresource',
            data=message_data,
            user_id=self.user_a.id,
            code=201,
        )
        print("Inside test_create_message_pass")
        print(answer.json)
        try:
            #delete the message that was created
            m_id = int(answer.json['id'])
            um = UserMsgMESSAGE.query.filter(
                UserMsgMESSAGE.id_user_to == self.user_b.id,
                UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()
        except Exception as e:
            print(e.args)

    def test_create_message_fail(self):
        """Fail to create a message."""
        message_data = dict(
            users_nicknames_to="user_b",
            groups_names_to=1,
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat(),
        )
        answer = self.post(
            'messageslistresource',
            data=message_data,
            user_id=self.user_a.id,
            code=400,
        )
        print(answer.json)

    def test_get_messages_paginated(self):
        #create some messages for user_b
        for i in range(12):
            # create message data dictionary
            m_data = dict(
                users_nicknames_to="user_b",
                groups_names_to="",
                subject="A subject",
                body="This is a message from user_a to user_b",
                sent_date=datetime.now(tzutc()).isoformat(),
            )
            # send the message
            self.post(
                'messageslistresource',
                data=m_data,
                user_id=self.user_a.id,
                code=201,
            )

        # per_page is set to default value 5
        page1 = self.get(
            'messageslistresource',
            urlargs=dict(page=1,),
            user_id=self.user_b.id,
        )
        # test correctness of first page
        self.assertEqual(len(page1.json), 5)
        endpoint = '/api/messages/?'
        link_template = '<{}per_page={}&page={}>; rel="{}"'
        first_link = link_template.format(endpoint, 5, 1, "first")
        next_link = link_template.format(endpoint, 5, 2, "next")
        last_link = link_template.format(endpoint, 5, 3, "last")
        expected_links_string = "{0},{1},{2}".format(
            first_link, next_link, last_link
        )
        self.assertEqual(page1.headers['Link'], expected_links_string)

        page3 = self.get(
            'messageslistresource',
            urlargs=dict(page=3,),
            user_id=self.user_b.id,
        )
        # test correctness of third(last) page
        self.assertEqual(len(page3.json), 2)
        endpoint = '/api/messages/?'
        link_template = '<{}per_page={}&page={}>; rel="{}"'
        first_link = link_template.format(endpoint, 5, 1, "first")
        prev_link = link_template.format(endpoint, 5, 2, "prev")
        last_link = link_template.format(endpoint, 5, 3, "last")
        expected_links_string = "{0},{1},{2}".format(
            first_link, prev_link, last_link
        )
        self.assertEqual(page3.headers['Link'], expected_links_string)

        # test non existent page
        non_existent = self.get(
            'messageslistresource',
            urlargs=dict(page=-2,),
            user_id=self.user_b.id,
        )
        self.assertEqual(non_existent.status_code, 400)

        # delete all the messages
        self.delete(
            'messageslistresource',
            user_id=self.user_b.id,
            code=204,
        )

    def test_delete_all_messages(self):
        """Delete all messages of a user."""
        #first create and send two messages from user_a to user_b
        m1_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat(),
        )
        self.post(
            'messageslistresource',
            data=m1_data,
            user_id=self.user_a.id,
            code=201,
        )

        m2_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="second message from user_a to user_b",
            body="this is the second message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat(),
        )
        self.post(
            'messageslistresource',
            data=m2_data,
            user_id=self.user_a.id,
            code=201,
        )
        self.delete(
            'messageslistresource',
            user_id=self.user_b.id,
            code=204,
        )

    def test_get_message(self):
        """Get a message from a user's inbox."""
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        #create and send a message from user_a to user_b
        message_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat(),
        )
        answer_post = self.post(
            'messageslistresource',
            data=message_data,
            user_id=self.user_a.id,
            code=201,
        )
        #get the message of user_b with the specified message id
        get_answer = self.get(
            'messageresource',
            urlargs=dict(message_id=int(answer_post.json['id'])),
            user_id=self.user_b.id,
        )

        print("Inside test_get_message")
        print(get_answer.json)
        try:
            #delete the message that was created
            m_id = int(get_answer.json['id'])
            um = UserMsgMESSAGE.query.filter(
                UserMsgMESSAGE.id_user_to == self.user_b.id,
                UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()
        except Exception as e:
            print(e.args)

    def test_delete_message(self):
        """Delete a message from a user's inbox."""
        #first create and send a message from user_a to user_b
        m1_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat(),
        )
        answer_post = self.post(
            'messageslistresource',
            data=m1_data,
            user_id=self.user_a.id,
            code=201,
        )
        self.delete(
            'messageresource',
            urlargs=dict(message_id=int(answer_post.json['id'])),
            user_id=self.user_b.id,
            code=204,
        )

    def test_reply_to_sender(self):
        """ Reply back to sender."""
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        #send a message from user_a to user_b
        m_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now(tzutc()).isoformat(),
        )
        answer_post = self.post(
            'messageslistresource',
            data=m_data,
            user_id=self.user_a.id,
            code=201,
        )

        #user_b replies to message
        data_to_reply = dict(
            reply_body="this is a reply to the message of user_a"
        )
        answer_put = self.put(
            'messageresource',
            urlargs=dict(message_id=int(answer_post.json['id'])),
            data=data_to_reply,
            user_id=self.user_b.id,
            code=201,
        )
        print("Inside test_reply_to_sender")
        print(answer_put.json)

        #delete what has been created
        try:
            m_id = int(answer_post.json['id'])
            um = UserMsgMESSAGE.query.filter(
                UserMsgMESSAGE.id_user_to == self.user_b.id,
                UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()

            m_id = int(answer_put.json['id'])
            um = UserMsgMESSAGE.query.filter(
                UserMsgMESSAGE.id_user_to == self.user_a.id,
                UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()
        except Exception as e:
            print(e.args)

TEST_SUITE = make_test_suite(TestMessagesRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
