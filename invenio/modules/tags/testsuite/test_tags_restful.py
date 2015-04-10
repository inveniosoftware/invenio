# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Test tags REST API."""

from __future__ import print_function
from collections import OrderedDict
from datetime import datetime
from dateutil.tz import tzutc
from invenio.base.wrappers import lazy_import
from invenio.testsuite import make_test_suite, run_test_suite
from invenio.ext.restful.utils import APITestCase
from invenio.ext.restful import validation_errors


db = lazy_import('invenio.ext.sqlalchemy.db')


class TestTagsRestfulAPI(APITestCase):

    """Test REST API of tags."""

    def setUp(self):
        """Run before each test."""
        from invenio.modules.accounts.models import User

        self.user_a = User(email='user_a@example.com', nickname='user_a')
        self.user_a.password = "iamusera"

        try:
            db.session.add(self.user_a)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        self.create_oauth_token(self.user_a.id, scopes=[""])

    def tearDown(self):
        """Run after every test."""
        from invenio.modules.accounts.models import User

        self.remove_oauth_token()
        User.query.filter(User.nickname.in_([
            self.user_a.nickname,
        ])).delete(synchronize_session=False)
        db.session.commit()

    def test_405_methods_tagslistresource(self):
        """Test methods that return 405."""
        methods_405_tagslistresource = [self.patch, self.options,
                                        self.put, self.head]
        for m in methods_405_tagslistresource:
            m(
                'taglistresource',
                user_id=self.user_a.id,
                is_json=False,
                code=405,
            )

    def test_create_tag_fail(self):
        """Fail to create a tag."""
        data = dict(
            name=56,
        )
        answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=400,
        )
        ordered_json_answer = OrderedDict(
            sorted(answer.json.items(), key=lambda t: t[0])
        )
        expected_result = dict(
            status=400,
            message='Validation error for tag creation',
            errors=[
                dict(
                    code=validation_errors['INCORRECT_TYPE']['error_code'],
                    message=(
                        validation_errors['INCORRECT_TYPE']['error_mesg'] +
                        ": " + "'" + data.keys()[0] +
                        "' " + "must be of string type"
                    ),
                    field=data.keys()[0],
                )
            ]
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_json_answer, ordered_expected_result)

    def test_create_tag_pass(self):
        """Successfully create a tag."""
        from invenio.modules.tags.models import WtgTAG
        data = dict(
            name='HighEnergyPhysics',
        )
        answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        ordered_json_answer = OrderedDict(
            sorted(answer.json.items(), key=lambda t: t[0])
        )
        #query the created tag
        retrieved_tag = WtgTAG.query.filter(
            WtgTAG.name == data[data.keys()[0]]).first()
        expected_result = dict(
            id=retrieved_tag.id,
            name=retrieved_tag.name,
            id_user=self.user_a.id,
            group_name='',
            group_access_rights='View',
            show_in_description=True
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_json_answer, ordered_expected_result)
        db.session.delete(retrieved_tag)
        db.session.commit()

    def test_get_tag(self):
        """Retrieve a tag."""
        from invenio.modules.tags.models import WtgTAG
        # first create a tag
        data = dict(
            name='Physics',
        )

        post_answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        # retrieve the tag
        tag_name = post_answer.json['name']

        get_answer = self.get(
            'tagresource',
            urlargs=dict(tag_name=tag_name),
            user_id=self.user_a.id,
        )
        ordered_json_get_answer = OrderedDict(
            sorted(get_answer.json.items(), key=lambda t: t[0])
        )
        retrieved_tag = WtgTAG.query.filter(
            WtgTAG.name == data[data.keys()[0]]).first()
        expected_result = dict(
            id=retrieved_tag.id,
            name=retrieved_tag.name,
            id_user=self.user_a.id,
            group_name='',
            group_access_rights='View',
            show_in_description=True
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_json_get_answer, ordered_expected_result)
        db.session.delete(retrieved_tag)
        db.session.commit()

    def test_update_tag_fail(self):
        """Fail to update a tag."""
        from invenio.modules.tags.models import WtgTAG
        # first create a tag
        data = dict(
            name='Physics',
        )

        post_answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        # update the tag
        to_update = dict(
            show_in_description="true",
            rights=5,
        )
        ordered_to_update = OrderedDict(sorted(
            to_update.items(), key=lambda x: x[0]
        ))

        update_answer = self.patch(
            'tagresource',
            urlargs=dict(tag_name=post_answer.json['name']),
            user_id=self.user_a.id,
            data=ordered_to_update,
        )
        ordered_json_update_answer = OrderedDict(
            sorted(update_answer.json.items(), key=lambda t: t[0])
        )
        expected_result = dict(
            status=400,
            message='Validation for tag update failed',
            errors=[
                dict(
                    code=validation_errors['INCORRECT_TYPE']['error_code'],
                    message=(
                        validation_errors['INCORRECT_TYPE']['error_mesg'] +
                        ": " + "'" + ordered_to_update.keys()[1] + "' "
                        + "must be of boolean type"
                    ),
                    field=ordered_to_update.keys()[1],
                ),
                dict(
                    code=(validation_errors['VALUE_OUT_OF_BOUNDS']
                          ['error_code']),
                    message=(
                        validation_errors['VALUE_OUT_OF_BOUNDS']
                        ['error_mesg'] + " : " + "unallowed value "
                        + str(ordered_to_update[ordered_to_update.keys()[0]])
                    ),
                    field=ordered_to_update.keys()[0],
                )
            ]
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_json_update_answer, ordered_expected_result)
        tag = WtgTAG.query.filter(WtgTAG.id == post_answer.json['id']).first()
        db.session.delete(tag)
        db.session.commit()

    def test_update_tag_pass(self):
        """Update a tag successfully."""
        from invenio.modules.tags.models import WtgTAG
        # first create a tag
        data = dict(
            name='Physics',
        )

        post_answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        # update the tag
        to_update = dict(
            show_in_description=False,
            rights=30,
        )
        ordered_to_update = OrderedDict(sorted(
            to_update.items(), key=lambda x: x[0]
        ))
        update_answer = self.patch(
            'tagresource',
            urlargs=dict(tag_name=post_answer.json['name']),
            user_id=self.user_a.id,
            data=ordered_to_update,
        )
        ordered_json_update_answer = OrderedDict(
            sorted(update_answer.json.items(), key=lambda t: t[0])
        )
        retrieved_tag = WtgTAG.query.filter(
            WtgTAG.name == data[data.keys()[0]]).first()
        expected_result = dict(
            id=retrieved_tag.id,
            name=data[data.keys()[0]],
            id_user=self.user_a.id,
            group_name='',
            group_access_rights='view,add,remove',
            show_in_description=ordered_to_update[ordered_to_update.keys()[1]]
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_json_update_answer, ordered_expected_result)
        db.session.delete(retrieved_tag)
        db.session.commit()

    def test_delete_tag_fail(self):
        """Fail to delete a tag."""
        from invenio.modules.tags.models import WtgTAG
        # try to delete a tag that does not exist
        try_delete = self.delete(
            'tagresource',
            urlargs=dict(tag_name="Physics"),
            user_id=self.user_a.id,
        )
        ordered_try_delete = OrderedDict(
            sorted(try_delete.json.items(), key=lambda t: t[0])
        )
        expected_result = dict(
            status=404,
            message="Tag 'Physics' to be deleted could not be found",
        )
        ordered_expected_result = OrderedDict(sorted(
            expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_try_delete, ordered_expected_result)
        # create a tag
        data = dict(
            name='Physics',
        )

        post_answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        # try to delete the above tag
        try_delete2 = self.delete(
            'tagresource',
            urlargs=dict(tag_name=post_answer.json['name']),
            user_id=0,
        )
        ordered_try_delete2 = OrderedDict(
            sorted(try_delete2.json.items(), key=lambda t: t[0])
        )
        expected_result = dict(
            status=401,
            message="Unauthorized",
        )
        ordered_expected_result = OrderedDict(sorted(
            expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_try_delete2, ordered_expected_result)
        tag = WtgTAG.query.filter(WtgTAG.id == post_answer.json['id']).first()
        db.session.delete(tag)
        db.session.commit()

    def test_delete_tag_pass(self):
        """Successfully delete a tag."""
        # create a tag
        data = dict(
            name='Physics',
        )

        post_answer = self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        # delete the tag
        self.delete(
            'tagresource',
            urlargs=dict(tag_name=post_answer.json['name']),
            user_id=self.user_a.id,
            code=204,
        )

    def test_get_tags(self):
        """Retrieve all user's tags."""
        # create some tags
        tag_list = [
            "HighEnergyPhysics",
            "ParticlePhysics",
            "Higgs",
            "QuantumMechanics",
            "ROOT"
        ]
        # add the created tags to a list
        created_tags = []
        for tag in tag_list:
            data = dict(
                name=tag,
            )
            answer = self.post(
                'taglistresource',
                user_id=self.user_a.id,
                data=data,
                code=201,
            )
            created_tags.append(answer.json)
        # sort list of tags according to the tag name
        created_tags.sort(key=lambda t: t['name'])
        # order the attributes of a tag
        ordered_created_tags = []
        for tag in created_tags:
            ordered_tag = OrderedDict(
                sorted(tag.items(), key=lambda t: t[0])
            )
            ordered_created_tags.append(ordered_tag)

        # retrieve the tags of the user
        get_answer = self.get(
            'taglistresource',
            user_id=self.user_a.id,
        )
        ordered_received_tags = []
        for entry in get_answer.json:
            ordered_received_tag = OrderedDict(
                sorted(entry.items(), key=lambda t: t[0])
            )
            ordered_received_tags.append(ordered_received_tag)
        self.assertEqual(ordered_created_tags, ordered_received_tags)
        # delete what has been created
        self.delete(
            'taglistresource',
            user_id=self.user_a.id,
            code=204
        )

    def test_delete_tags(self):
        """Delete all user's tags."""
        # create some tags
        tag_list = [
            "HighEnergyPhysics",
            "ParticlePhysics",
            "Higgs",
            "QuantumMechanics",
            "ROOT"
        ]
        for tag in tag_list:
            data = dict(
                name=tag,
            )
            self.post(
                'taglistresource',
                user_id=self.user_a.id,
                data=data,
                code=201,
            )
        # delete the created tags
        self.delete(
            'taglistresource',
            user_id=self.user_a.id,
            code=204
        )

    def test_attach_tags_to_record_fail(self):
        """Fail to attach a tag to a record."""
        tag_data = dict(
            tags=["Physics", "ROOT"]
        )
        answer = self.post(
            'recordlisttagresource',
            user_id=self.user_a.id,
            data=tag_data,
            urlargs=dict(record_id=0),
        )
        ordered_json_answer = OrderedDict(
            sorted(answer.json.items(), key=lambda t: t[0])
        )
        expected_result = dict(
            status=404,
            message="Tag error: Record with id=0 does not exist",
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_json_answer, ordered_expected_result)

    def test_attach_tags_to_record_pass(self):
        """Successfully attach tags to a record."""
        from invenio.modules.records.models import Record
        # first create a record
        test_record = Record(
            creation_date=datetime.now(),
            modification_date=datetime.now()
        )
        test_record_info = dict(
            name="test_record"
        )
        test_record.additional_info = test_record_info
        db.session.add(test_record)
        db.session.commit()
        # attach tags to the record
        tag_data = dict(
            tags=["ROOT", "PHYSICS"]
        )
        answer = self.post(
            'recordlisttagresource',
            user_id=self.user_a.id,
            data=tag_data,
            urlargs=dict(record_id=test_record.id),
        )
        # answer.json is a list of TagRepresentation objects
        ordered_created_tags = []
        for tag_representation in answer.json:
            ordered_tag_repr = OrderedDict(
                sorted(tag_representation.items(), key=lambda t: t[0])
            )
            ordered_created_tags.append(ordered_tag_repr)
        #now query DB
        get_answer = self.get(
            'recordlisttagresource',
            user_id=self.user_a.id,
            urlargs=dict(record_id=test_record.id),
        )
        ordered_retrieved_tags = []
        for retrieved_tag_repr in get_answer.json:
            ordered_retrieved_tag_repr = OrderedDict(
                sorted(retrieved_tag_repr.items(), key=lambda t: t[0])
            )
            ordered_retrieved_tags.append(ordered_retrieved_tag_repr)

        self.assertEqual(ordered_created_tags, ordered_retrieved_tags)
        self.delete(
            'taglistresource',
            user_id=self.user_a.id,
            code=204
        )
        # delete the created record
        db.session.delete(test_record)
        db.session.commit()

    def test_detach_tags_from_record_fails(self):
        """Fail to detach tag from record."""
        from invenio.modules.records.models import Record
        # first create a record
        test_record = Record(
            creation_date=datetime.now(),
            modification_date=datetime.now()
        )
        db.session.add(test_record)
        db.session.commit()
        # create a tag
        data = dict(
            name='HighEnergyPhysics',
        )
        self.post(
            'taglistresource',
            user_id=self.user_a.id,
            data=data,
            code=201,
        )
        # try to detach tag that is not attached to record
        detach_answer = self.delete(
            'recordtagresource',
            urlargs=dict(
                record_id=test_record.id,
                tag_name=data[data.keys()[0]]
            ),
            user_id=self.user_a.id,
        )
        ordered_detach_answer = OrderedDict(
            sorted(detach_answer.json.items(), key=lambda t: t[0])
        )
        expected_result = dict(
            message=(
                "Tag '{0} is not attached to record with id={1}".
                format(data[data.keys()[0]], test_record.id)
            ),
            status=400
        )
        ordered_expected_result = OrderedDict(
            sorted(expected_result.items(), key=lambda t: t[0])
        )
        self.assertEqual(ordered_detach_answer, ordered_expected_result)
        # delete tag
        self.delete(
            'taglistresource',
            user_id=self.user_a.id,
            code=204
        )
        # delete record
        db.session.delete(test_record)
        db.session.commit()

    def test_detach_tags_from_record_pass(self):
        """Successfully detach tag from record."""
        from invenio.modules.records.models import Record
        # first create a record
        test_record = Record(
            creation_date=datetime.now(),
            modification_date=datetime.now()
        )
        db.session.add(test_record)
        db.session.commit()
        # create some tags
        tags_list = [
            "HighEnergyPhysics",
            "Higgs",
            "ROOT"
        ]
        # attach the tags to the record
        tags_data = dict(
            tags=tags_list,
        )
        self.post(
            'recordlisttagresource',
            user_id=self.user_a.id,
            data=tags_data,
            urlargs=dict(record_id=test_record.id),
        )
        # detach tags from record and delete them
        self.delete(
            'taglistresource',
            user_id=self.user_a.id,
            code=204
        )
        # delete record
        db.session.delete(test_record)
        db.session.commit()


TEST_SUITE = make_test_suite(TestTagsRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
