# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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

"""Invenio Obelix Search Engine Client Tests"""

from random import random
import json

from time import sleep, time
from collections import deque

from invenio.testutils import InvenioTestCase
from invenio.testutils import make_test_suite, run_test_suite

from invenio.search_engine_obelix import ObelixSearchEngine, ObelixSearchEngineSettings, \
    ObelixSearchEngineLogger, rank_records_obelix


class RedisMock(object):
    """ Redis mock used for testing Obelix """

    def __init__(self, store=None):
        if store:
            self.store = store
            self.store_timeout = {}
        else:
            self.store = {}
            self.store_timeout = {}

    def get(self, key):
        """
        Get value on key
        :param key:
        :return:
        """
        try:
            if key in self.store_timeout:
                if time() > self.store_timeout[key]:
                    return None

            return self.store[key]
        except KeyError:
            return None

    def set(self, key, value, timeout=None):
        """
        Sets value on key
        :param key:
        :param value:
        :param timeout:
        :return:
        """
        self.store[key] = value

        if timeout:
            self.store_timeout[key] = time() + timeout

        return self.store[key]

    def lpush(self, key, value):
        """
        Left push value to the *queue* key
        :param key:
        :param value:
        :return:
        """
        if key not in self.store:
            self.store[key] = deque()

        self.store[key].appendleft(value)

    def rpush(self, key, value):
        """
        Right push value to the *queue* key

        :param key:
        :param value:
        :return:
        """
        if key not in self.store:
            self.store[key] = deque()

        self.store[key].append(value)

    def rpop(self, key):
        """
        :param key: Right pop value from the *queue* key
        :return:
        """
        try:
            return self.store[key].pop()
        except (KeyError, IndexError):
            return None

    def lpop(self, key):
        """
        :param key: Left pop value from the *queue* key
        :return:
        """
        try:
            return self.store[key].popleft()
        except (KeyError, IndexError):
            return None


class TestRedisMock(InvenioTestCase):
    """Tests for the Redis Mock"""

    def setUp(self):
        """
        Set up the self.redis object
        :return:
        """
        self.redis = RedisMock()

    def test_set_and_get(self):
        """
        test_set_and_get
        :return:
        """
        self.redis.set("key", "value")
        self.assertEqual(self.redis.get("key"), "value")

    def test_set_and_get_timeout_timed_out(self):
        """
        test_set_and_get_timeout_timed_out
        :return:
        """
        self.redis.set("key", "value", 0.1)
        sleep(0.2)
        self.assertEqual(self.redis.get("key"), None)

    def test_set_and_get_timeout_not_timed_out(self):
        """
        test_set_and_get_timeout_not_timed_out
        :return:
        """
        self.redis.set("key", "value", 0.5)
        sleep(0.2)
        self.assertEqual(self.redis.get("key"), "value")

    def test_single_lpush_and_lpop(self):
        """
        test_single_lpush_and_lpop
        :return:
        """
        self.redis.lpush("key", "value")
        self.assertEqual(self.redis.lpop("key"), "value")
        self.assertEqual(self.redis.lpop("key"), None)

    def test_single_lpush_and_rpop(self):
        """
        test_single_lpush_and_rpop
        :return:
        """
        self.redis.lpush("key", "value")
        self.assertEqual(self.redis.rpop("key"), "value")
        self.assertEqual(self.redis.rpop("key"), None)

    def test_single_rpush_and_lpop(self):
        """
        test_single_rpush_and_lpop
        :return:
        """
        self.redis.rpush("key", "value")
        self.assertEqual(self.redis.lpop("key"), "value")
        self.assertEqual(self.redis.lpop("key"), None)

    def test_single_rpush_and_rpop(self):
        """
        test_single_rpush_and_rpop
        :return:
        """
        self.redis.rpush("key", "value")
        self.assertEqual(self.redis.rpop("key"), "value")
        self.assertEqual(self.redis.rpop("key"), None)

    def test_two_rpush_and_lpop(self):
        """
        test_two_rpush_and_lpop
        :return:
        """
        self.redis.rpush("key", "value1")
        self.redis.rpush("key", "value2")

        self.assertEqual(self.redis.lpop("key"), "value1")
        self.assertEqual(self.redis.lpop("key"), "value2")
        self.assertEqual(self.redis.lpop("key"), None)

    def test_two_rpush_and_rpop(self):
        """
        test_two_rpush_and_rpop
        :return:
        """
        self.redis.rpush("key", "value1")
        self.redis.rpush("key", "value2")

        self.assertEqual(self.redis.rpop("key"), "value2")
        self.assertEqual(self.redis.rpop("key"), "value1")
        self.assertEqual(self.redis.rpop("key"), None)

    def test_two_lpush_and_lpop(self):
        """
        test_two_lpush_and_lpop
        :return:
        """
        self.redis.lpush("key", "value1")
        self.redis.lpush("key", "value2")

        self.assertEqual(self.redis.lpop("key"), "value2")
        self.assertEqual(self.redis.lpop("key"), "value1")
        self.assertEqual(self.redis.lpop("key"), None)

    def test_two_lpush_and_rpop(self):
        """
        test_two_lpush_and_rpop
        :return:
        """
        self.redis.lpush("key", "value1")
        self.redis.lpush("key", "value2")

        self.assertEqual(self.redis.rpop("key"), "value1")
        self.assertEqual(self.redis.rpop("key"), "value2")
        self.assertEqual(self.redis.rpop("key"), None)


class TestObelixRecommendations(InvenioTestCase):
    """Test for the Obelix Recommendations"""

    def setUp(self):
        self.uid = 1
        self.hitset = range(1, 30)

        self.redis = RedisMock()
        self.search_engine = ObelixSearchEngine(self.uid,
                                                self.hitset,
                                                redis=self.redis)

        self.redis.set("obelix::settings",
                       json.dumps(self.search_engine.settings.dump()))

    def test_settings_set(self):
        self.assertEqual(json.loads(self.redis.get("obelix::settings")),
                         self.search_engine.settings.dump())

    def test_redis_key_generation_only_one_argument(self):
        self.assertEqual("obelix::user",
                         self.search_engine.settings.redis_key("user"))

    def test_redis_key_generation_two_arguments(self):
        self.assertEqual("obelix::user::1",
                         self.search_engine.settings.redis_key("user", "1"))

    def test_redis_key_generation_three_arguments(self):
        self.assertEqual("obelix::user::1::2",
                         self.search_engine.settings.redis_key("user", "1", "2"))

    def test_redis_key_generation_int(self):
        self.assertEqual("obelix::1", self.search_engine.settings.redis_key(1))

    def test_get_orignal_hitset(self):
        self.assertEqual(self.hitset, self.search_engine._get_hitset)

    def test_get_recommendations_empty(self):
        recommendations = json.dumps({})

        self.redis.set("obelix::recommendations::1", recommendations)
        self.assertEqual(json.loads(recommendations),
                         self.search_engine.recommendations)

    def test_get_recommendations_two_recommendations(self):
        recommendations = {10: 0.2, 11: 0.1}
        recommendations_json = json.dumps(recommendations)
        self.redis.set("obelix::recommendations::1", recommendations_json)
        self.search_engine = ObelixSearchEngine(self.uid, self.hitset, redis=self.redis)
        self.assertEqual(recommendations, self.search_engine.recommendations)

    def test_rank_hitset_by_order(self):
        self.assertEqual(self.hitset, self.search_engine.ranked_records_by_order)

    def test_rank_scores_by_order_equaly_long_as_list_of_records(self):
        self.assertEqual(len(self.hitset), len(self.search_engine.ranked_scores_by_order))

    def test_settings_read_default(self):
        settings = ObelixSearchEngineSettings(redis=self.redis)
        self.assertEqual(settings.recommendations_impact, 0.5)

    def test_settings_read_redis(self):
        settings = {'redis_prefix': "obelix::",
                    'recommendations_impact': 0.8,
                    'score_lower_limit': 0.2,
                    'score_min_limit': 10,
                    'score_min_multiply': 4,
                    'score_one_result': 1,
                    'method_switch_limit': 30,
                    'redis_timeout_search_result': 10}

        self.redis.set("obelix::settings", json.dumps(settings))

        settings = ObelixSearchEngineSettings(redis=self.redis)
        self.assertEqual(settings.recommendations_impact, 0.8)

    def test_sort_records_by_score(self):
        self.assertEqual(self.hitset, self.search_engine.ranked_records_by_order)

    def test_get_score_for_recid(self):
        recommendations = {1: 0.9, 2: 0.5}

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))
        search_engine = ObelixSearchEngine(self.uid, self.hitset, redis=self.redis)

        recid1_score = search_engine._get_score(1, 0)
        recid2_score = search_engine._get_score(2, 1)
        self.assertGreater(recid1_score, recid2_score)

    def test_build_no_recommendations(self):
        self.assertEqual({}, self.search_engine.recommendations)

    def test_build_recommendations(self):
        recommendations = {1: 0.9, 2: 0.5}
        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))
        search_engine = ObelixSearchEngine(self.uid, self.hitset, redis=self.redis)
        self.assertEqual(recommendations, search_engine.recommendations)

    def test_log_search(self):
        user_info = {'uid': 1, 'remote_ip': "127.0.0.1", "uri": "testuri"}
        record_ids = [[1, 88], [1, 2]]
        results_final_colls_scores = [[0.3, 0.5], [0.5, 0.2]]
        cols_in_result_ordered = ["Thesis", "Another"]
        seconds_to_rank_and_print = 2

        jrec, rg, rm, cc = 0, 10, "recommendations", "obelix"

        ObelixSearchEngineLogger(self.redis).search_result(user_info, record_ids, record_ids,
                                                           results_final_colls_scores,
                                                           cols_in_result_ordered,
                                                           seconds_to_rank_and_print,
                                                           jrec, rg, rm, cc)

        logged = self.redis.get("obelix::last-search-result::1")
        self.assertEqual(record_ids, json.loads(logged)['record_ids'])

    def test_log_search_analytics(self):
        user_info = {'uid': 1, 'remote_ip': "127.0.0.1", "uri": "testuri"}
        record_ids = [[1, 88], [1, 2]]
        results_final_colls_scores = [[0.3, 0.5], [0.5, 0.2]]
        cols_in_result_ordered = ["Thesis", "Another"]
        seconds_to_rank_and_print = 2

        jrec, rg, rm, cc = 0, 10, "recommendations", "obelix"

        ObelixSearchEngineLogger(self.redis).search_result(user_info, record_ids, record_ids,
                                                           results_final_colls_scores,
                                                           cols_in_result_ordered,
                                                           seconds_to_rank_and_print,
                                                           jrec, rg, rm, cc)

        logged = json.loads(self.redis.lpop("obelix::statistics-search-result"))

        self.assertEqual(str(user_info['uid']), logged['uid'])
        self.assertEqual(user_info['remote_ip'], logged['remote_ip'])

    def test_log_page_view(self):
        user_info = {'uid': 1, 'remote_ip': "127.0.0.1", "uri": "testuri"}
        record_ids = [[1, 88], [1, 2]]
        results_final_colls_scores = [[0.3, 0.5], [0.5, 0.2]]
        cols_in_result_ordered = ["Thesis", "Another"]
        seconds_to_rank_and_print = 2

        jrec, rg, rm, cc = 0, 10, "recommendations", "obelix"

        ObelixSearchEngineLogger(self.redis).search_result(user_info, record_ids, record_ids,
                                                           results_final_colls_scores,
                                                           cols_in_result_ordered,
                                                           seconds_to_rank_and_print,
                                                           jrec, rg, rm, cc)

        ObelixSearchEngineLogger(self.redis).page_view(user_info, 1)

        logged = json.loads(self.redis.lpop("obelix::statistics-page-view"))
        self.assertEqual(logged['uid'], '1')

        logged = json.loads(self.redis.lpop("obelix::logentries"))
        self.assertEqual(logged['type'], "events.pageviews")
        self.assertEqual(logged['user'], '1')

    def test__rank_records_by_order_scores_sorted_largest_first(self):
        self.search_engine = ObelixSearchEngine(1, [1, 2, 3, 4, 5, 6, 7, 8, 9],
                                                self.redis)

        sorted_by_value = sorted(self.search_engine.ranked_scores_by_order, reverse=True)
        self.assertEqual(sorted_by_value, self.search_engine.ranked_scores_by_order)

    def test_rank_records_obelix(self):
        user_info = {'uid': 1, 'remote_ip': "127.0.0.1", "uri": "testuri"}
        hitset = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        records, scores = rank_records_obelix(user_info, hitset, rg=10, jrec=0)
        self.assertEqual(hitset, records)

    def test_return_size_ofrank_records_obelix(self):
        user_info = {'uid': 1, 'remote_ip': "127.0.0.1", "uri": "testuri"}
        hitset = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

        records, scores = rank_records_obelix(user_info, hitset, rg=10, jrec=0)
        self.assertEqual(hitset[0:10], records)

    def testrank_records_obelix_using_ip_as_userid(self):
        user_info = {'uid': 1, 'remote_ip': "127.0.0.1", "uri": "testuri"}
        hitset = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        uid = user_info['remote_ip']

        ranker = ObelixSearchEngine(uid, hitset)
        records, scores = ranker.rank()
        self.assertEqual(hitset, records)

        ObelixSearchEngineLogger(self.redis).page_view(user_info, uid)

    def test_ranked_scores_by_order_only_one_result(self):
        hitset = [1]

        ranker = ObelixSearchEngine('1', hitset)
        records, scores = ranker.rank()

        self.assertEquals(records, [1])

    def test_different_users_get_different_results_with_different_recommendations(self):
        hitset = [1, 2, 3, 4, 5]

        self.redis.set("obelix::recommendations::1", json.dumps({1: 0.9, 2: 0.5}))
        self.redis.set("obelix::recommendations::2", json.dumps({5: 0.9, 1: 0.1}))

        s1 = ObelixSearchEngine("1", hitset, redis=self.redis)
        s2 = ObelixSearchEngine("2", hitset, redis=self.redis)

        s1_records, s1_scores = s1.rank()
        s2_records, s2_scores = s2.rank()

        self.assertNotEquals(s1_records, s2_records)
        self.assertNotEquals(s1_scores, s2_scores)

    def test_different_users_get_same_results_with_same_recommendations(self):
        hitset = [1, 2, 3, 4, 5]

        self.redis.set("obelix::recommendations::1", json.dumps({1: 0.9, 2: 0.5}))
        self.redis.set("obelix::recommendations::2", json.dumps({1: 0.9, 2: 0.5}))

        s1 = ObelixSearchEngine("1", hitset, redis=self.redis)
        s2 = ObelixSearchEngine("2", hitset, redis=self.redis)

        s1_records, s1_scores = s1.rank()
        s2_records, s2_scores = s2.rank()

        self.assertEquals(s1_records, s2_records)
        self.assertEquals(s1_scores, s2_scores)

    def test_large_data_set_of_records(self):
        records_to_test = range(0, 50000)

        s1 = ObelixSearchEngine("1", records_to_test, redis=self.redis)
        jrec, rg = 0, 10

        self.assertEquals(records_to_test[jrec:jrec + rg], s1.rank()[0][jrec:jrec + rg])

    def test_large_data_set_of_records_and_recommendations(self):
        records_to_test = range(0, 5000)
        recommendations = {}

        for recid in records_to_test:
            recommendations[recid] = random()

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))

        s1 = ObelixSearchEngine("1", records_to_test, redis=self.redis)

        self.assertNotEquals(records_to_test[0:100], s1.rank()[0][0:100])
        self.assertNotEquals(records_to_test[0:3], s1.rank()[0][0:3])

    def test_xlarge_data_set_of_records_and_a_few_recommendations(self):
        records_to_test = range(0, 1000000)
        recommendations = {}

        for recid in records_to_test[0:1000]:
            recommendations[recid] = random()

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))

        s1 = ObelixSearchEngine("1", records_to_test, redis=self.redis)

        self.assertNotEquals(records_to_test[0:100], s1.rank()[0][0:100])
        self.assertNotEquals(records_to_test[0:3], s1.rank()[0][0:3])

    def test_large_dataset_find_hidden_treasure(self):
        records_to_test = range(0, 1000000)

        recommendations = {1: 0.9, 90000: 1.0, 430: 0.8}

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))

        s1 = ObelixSearchEngine("1", records_to_test, redis=self.redis)
        s1records, s2scores = s1.rank()

        for key, val in recommendations.iteritems():
            self.assertTrue(key in s1records)

    def test_large_dataset_hidden_treasure_lost_without_recommendations(self):

        user_info = {'uid': '1', 'remote_ip': '127.0.0.1', 'uri': 'testuri'}

        records_to_test = range(0, 100000)
        recommendations = {90000: 1.0, 430: 0.8}

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))

        settings = ObelixSearchEngineSettings(redis=self.redis)
        settings.recommendations_impact = 0

        records, scores = rank_records_obelix(user_info,
                                               records_to_test,
                                               rg=10, jrec=0,
                                               settings=settings)

        for key, val in recommendations.iteritems():
            self.assertFalse(key in records)

    def test_large_dataset_hidden_treasure_lost_with_full_recommendations(self):

        user_info = {'uid': '1', 'remote_ip': '127.0.0.1', 'uri': 'testuri'}

        records_to_test = range(0, 100000)
        records_to_test.reverse()
        recommendations = {100: 1.0, 200: 0.8}

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))

        settings = ObelixSearchEngineSettings(redis=self.redis)
        settings.recommendations_impact = 0.9

        records, scores = rank_records_obelix(user_info,
                                               records_to_test,
                                               rg=10, jrec=0,
                                               settings=settings)

        for key, val in recommendations.iteritems():
            self.assertTrue(key in records)

    def test_set_recommendation_impact_via_redis(self):

        user_info = {'uid': '1', 'remote_ip': '127.0.0.1', 'uri': 'testuri'}

        records_to_test = range(0, 100000)
        recommendations = {90000: 1.0, 4300: 0.3}

        self.redis.set("obelix::recommendations::1", json.dumps(recommendations))

        settings = ObelixSearchEngineSettings(redis=self.redis)
        settings_json = settings.dump()

        settings_json['recommendations_impact'] = 1
        self.redis.set("obelix::settings", json.dumps(settings_json))

        records, scores = rank_records_obelix(user_info,
                                               records_to_test,
                                               rg=10, jrec=0,
                                               settings=settings)

        for key, val in recommendations.iteritems():
            self.assertTrue(key in records)

        settings_json['recommendations_impact'] = 0.1
        self.redis.set("obelix::settings", json.dumps(settings_json))

        records, scores = rank_records_obelix(user_info,
                                               records_to_test,
                                               rg=10, jrec=0,
                                               settings=settings)
        for key, val in recommendations.iteritems():
            self.assertFalse(key in records)

    def test_result_no_changes_when_user_is_zero(self):
        user_info = {'uid': '', 'remote_ip': '127.0.0.1', 'uri': 'testuri'}

        settings = ObelixSearchEngineSettings(redis=self.redis)

        self.assertEqual(self.hitset[0:10], rank_records_obelix(user_info,
                                                                 self.hitset, rg=10, jrec=0,
                                                                 settings=settings)[0])

    def test_result_no_changes_when_user_is_zero_jrec_set(self):
        user_info = {'uid': '', 'remote_ip': '127.0.0.1', 'uri': 'testuri'}

        settings = ObelixSearchEngineSettings(redis=self.redis)

        self.assertEqual(self.hitset[4:14], rank_records_obelix(user_info,
                                                                 self.hitset, rg=10, jrec=5,
                                                                 settings=settings)[0])


TEST_SUITE = make_test_suite(TestRedisMock,
                             TestObelixRecommendations)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
