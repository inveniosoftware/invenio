from invenio.bibauthorid_dbinterface import populate_partial_marc_caches
from invenio.bibauthorid_dbinterface import destroy_partial_marc_caches
from invenio.bibauthorid_dbinterface import _get_author_refs_from_marc_caches_of_paper
from invenio.bibauthorid_dbinterface import _get_author_refs_from_db_of_paper
from invenio.bibauthorid_dbinterface import _get_coauthor_refs_from_db_of_paper
from invenio.bibauthorid_dbinterface import _get_coauthor_refs_from_marc_caches_of_paper
from invenio.bibauthorid_dbinterface import _get_name_by_bibref_from_cache
from invenio.bibauthorid_dbinterface import _get_name_from_db_by_bibref
from invenio.bibauthorid_dbinterface import _get_grouped_records_using_marc_caches
from invenio.bibauthorid_dbinterface import _get_grouped_records_from_db
from invenio.bibauthorid_rabbit_regression_tests import BibAuthorIDRabbitTestCase
from invenio.bibauthorid_webapi import get_bibrefs_from_bibrecs
from invenio.bibauthorid_testutils import get_modified_marc_for_test
from invenio.bibauthorid_testutils import get_new_marc_for_test
from invenio.bibauthorid_testutils import get_bibrec_for_record

from invenio.testutils import make_test_suite
from invenio.testutils import run_test_suite


class Marc100700CacheTestCase(BibAuthorIDRabbitTestCase):  # TODO Refactor, create test utils.

    """Regression tests ensuring that the marc cache is working consistenly.
       It is ensured by comparing the result of the cache with the result of the db."""

    def setUp(self):
        super(Marc100700CacheTestCase, self).setUp()
        marc_xml_record = get_new_marc_for_test("Test", author_name=self.author_name,
                                                ext_id=None,
                                                co_authors_names=self.co_authors_names)
        self.bibrec_to_test = get_bibrec_for_record(marc_xml_record,
                                                    opt_mode='insert')
        self.bibrecs_to_clean = [self.bibrec_to_test]
        bibrefs = get_bibrefs_from_bibrecs([self.bibrec_to_test])
        for bibref in bibrefs:
            self.ref_table = bibref[1][0][0].split(":")[0]
            self.ref_value = bibref[1][0][0].split(":")[1]
        populate_partial_marc_caches([self.bibrec_to_test])

    def test_cache_author_refs(self):
        """This regression test ensures that the MARC_100_700_CACHE works for author_refs."""
        from_cache = _get_author_refs_from_marc_caches_of_paper(self.bibrec_to_test)
        from_db = _get_author_refs_from_db_of_paper(self.bibrec_to_test)
        self.assertEquals(from_cache, from_db)

    def test_cache_coauthor_refs(self):
        from_cache = sorted(_get_coauthor_refs_from_marc_caches_of_paper(self.bibrec_to_test))
        from_db = sorted(_get_coauthor_refs_from_db_of_paper(self.bibrec_to_test))
        self.assertEquals(from_cache, from_db)

    def test_cache_name_by_bibref(self):
            from_cache = _get_name_by_bibref_from_cache((self.ref_table, self.ref_value))
            from_db = _get_name_from_db_by_bibref((self.ref_table, self.ref_value))
            self.assertEquals(from_cache, from_db)

    def test_get_grouped_record(self):
            from_cache = _get_grouped_records_using_marc_caches((self.ref_table, self.ref_value, self.bibrec_to_test))
            from_db = _get_grouped_records_from_db((self.ref_table, self.ref_value, self.bibrec_to_test))
            self.assertEquals(from_cache, from_db)

    def tearDown(self):
        super(Marc100700CacheTestCase, self).tearDown()
        destroy_partial_marc_caches()


TEST_SUITE = make_test_suite(Marc100700CacheTestCase)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=False)
