# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Test knowledge REST API."""

from __future__ import print_function

from invenio.base.wrappers import lazy_import
from invenio.ext.restful.utils import APITestCase
from invenio.ext.sqlalchemy.utils import session_manager
from invenio.testsuite import make_test_suite, run_test_suite

db = lazy_import('invenio.ext.sqlalchemy.db')


class TestKnowledgeRestfulAPI(APITestCase):

    """Test REST API of mappings."""

    @session_manager
    def setUp(self):
        """Run before each test."""
        from invenio.modules.knowledge.models import KnwKB, KnwKBRVAL

        self.kb_a = KnwKB(name='example1', description='test description',
                          kbtype='w')
        db.session.add(self.kb_a)

        # add kbrval
        key = "testkey1"
        value = "testvalue1"
        self.kb_a.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval (with different key and same value)
        key = "testkey1_1"
        value = "testvalue1"
        self.kb_a.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval
        key = "testkey2"
        value = "testvalue2"
        self.kb_a.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval
        key = "testkey3"
        value = "testvalue3"
        self.kb_a.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval
        key = "testkey4"
        value = "testvalue4"
        self.kb_a.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        self.kb_b = KnwKB(name='example2', description='test description 2',
                          kbtype='w')
        db.session.add(self.kb_b)

        # add kbrval
        key = "testkey1b"
        value = "testvalue1b"
        self.kb_b.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval
        key = "testkey2b"
        value = "testvalue2b"
        self.kb_b.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval
        key = "testkey3b"
        value = "testvalue3b"
        self.kb_b.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

        # add kbrval
        key = "testkey4b"
        value = "testvalue4b"
        self.kb_b.kbrvals.set(KnwKBRVAL(m_key=key, m_value=value))

    @session_manager
    def tearDown(self):
        """Run after every test."""
        from invenio.modules.knowledge.models import KnwKB

        db.session.delete(KnwKB.query.filter_by(id=self.kb_a.id).one())
        db.session.delete(KnwKB.query.filter_by(id=self.kb_b.id).one())

    def test_get_knwkb_ok(self):
        """Test return a knowledge."""
        per_page = 2
        get_answer = self.get(
            'knwkbresource',
            urlargs={
                'slug': self.kb_a.slug,
                'page': 1,
                'per_page': per_page,
                'from': '2'
            },
            user_id=1
        )

        answer = get_answer.json

        assert answer['name'] == 'example1'
        assert answer['type'] == 'w'
        assert answer['description'] == 'test description'
        assert answer['mappings'][0]['from'] == 'testkey2'
        assert answer['mappings'][0]['to'] == 'testvalue2'
        assert len(answer['mappings']) == 1

    def test_get_knwkb_search_key_return_empty(self):
        """Test return a knowledge with search key that returns empty."""
        per_page = 4
        get_answer = self.get(
            'knwkbresource',
            urlargs={
                'slug': self.kb_b.slug,
                'page': 1,
                'per_page': per_page,
                'from': 'not_existing_mapping_from'
            },
            user_id=1
        )

        answer = get_answer.json

        assert len(answer['mappings']) == 0

    def test_get_knwkb_search_key(self):
        """Test return a knowledge with search key."""
        per_page = 4
        get_answer = self.get(
            'knwkbresource',
            urlargs={
                'slug': self.kb_b.slug,
                'page': 1,
                'per_page': per_page,
                'from': 'testkey1b'
            },
            user_id=1
        )

        answer = get_answer.json

        assert answer['name'] == 'example2'
        assert answer['type'] == 'w'
        assert answer['description'] == 'test description 2'
        assert answer['mappings'][0]['from'] == 'testkey1b'
        assert answer['mappings'][0]['to'] == 'testvalue1b'
        assert len(answer['mappings']) == 1

    def test_get_knwkb_not_exist(self):
        """Test return a knowledge that not exists."""
        slug = 'testsuite-slug-not-exists-123'
        get_answer = self.get(
            'knwkbresource',
            urlargs=dict(slug=slug),
            user_id=1,
        )

        answer = get_answer.json

        expected_result = dict(
            status=404,
        )

        assert answer['status'] == expected_result['status']

    def test_get_knwkb_mappings(self):
        """Test the return of list of mappings."""
        get_answer = self.get(
            'knwkbmappingsresource',
            urlargs=dict(
                slug=self.kb_a.slug,
                page=1,
                per_page=10,
                to="2"
            ),
            user_id=1,
        )

        answer = get_answer.json

        assert answer[0]['from'] == 'testkey2'
        assert answer[0]['to'] == 'testvalue2'

    def test_get_knwkb_mapping_to_unique_ok(self):
        """Test the return of unique "mappings to" list."""
        per_page = 4
        get_answer = self.get(
            'knwkbmappingstoresource',
            urlargs={
                'slug': self.kb_a.slug,
                'page': 1,
                'per_page': per_page,
                'unique': '1'
            },
            user_id=1
        )

        answer = get_answer.json

        assert isinstance(answer, list)
        assert 'testvalue1' in answer
        assert 'testvalue2' in answer
        assert 'testvalue3' in answer
        assert 'testvalue4' in answer
        assert len(answer) == 4

    def test_get_knwkb_mapping_to_ok(self):
        """Test the return of "mappings to" list."""
        per_page = 4
        get_answer = self.get(
            'knwkbmappingstoresource',
            urlargs={
                'slug': self.kb_a.slug,
                'page': 1,
                'per_page': per_page,
            },
            user_id=1
        )

        answer = get_answer.json

        assert isinstance(answer, list)
        assert 'testvalue1' in answer
        assert 'testvalue2' in answer
        assert 'testvalue3' in answer
        assert 'testvalue4' not in answer
        assert len(answer) == 4

    def test_not_allowed_url(self):
        """Check not allowed url."""
        paths = [
            'foo',
            'foo/bar',
            '123',
            'test/url/foo',
        ]

        for path in paths:
            self.get(
                'notimplementedknowledegeresource',
                urlargs={
                    'slug': self.kb_a.slug,
                    'foo': path,
                },
                user_id=1,
                code=405,
            )
            self.head(
                'notimplementedknowledegeresource',
                urlargs={
                    'slug': self.kb_a.slug,
                    'foo': path,
                },
                user_id=1,
                code=405,
            )
            self.options(
                'notimplementedknowledegeresource',
                urlargs={
                    'slug': self.kb_a.slug,
                    'foo': path,
                },
                user_id=1,
                code=405,
            )
            self.post(
                'notimplementedknowledegeresource',
                urlargs={
                    'slug': self.kb_a.slug,
                    'foo': path,
                },
                user_id=1,
                code=405,
            )
            self.put(
                'notimplementedknowledegeresource',
                urlargs={
                    'slug': self.kb_a.slug,
                    'foo': path,
                },
                user_id=1,
                code=405,
            )

TEST_SUITE = make_test_suite(TestKnowledgeRestfulAPI)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
