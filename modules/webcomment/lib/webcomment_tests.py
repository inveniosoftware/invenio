import webcomment
import unittest

class TestWashQueryParameters(unittest.TestCase):
    """Test for washing of search query parameters."""

    def test_wash_url_argument(self):
        """search engine - washing of URL arguments"""
        self.assertEqual(1, search_engine.wash_url_argument(['1'],'int'))
        self.assertEqual("1", search_engine.wash_url_argument(['1'],'str'))
        self.assertEqual(['1'], search_engine.wash_url_argument(['1'],'list'))
        self.assertEqual(0, search_engine.wash_url_argument('ellis','int'))
        self.assertEqual("ellis", search_engine.wash_url_argument('ellis','str'))
        self.assertEqual(["ellis"], search_engine.wash_url_argument('ellis','list'))
        self.assertEqual(0, search_engine.wash_url_argument(['ellis'],'int'))
        self.assertEqual("ellis", search_engine.wash_url_argument(['ellis'],'str'))
        self.assertEqual(["ellis"], search_engine.wash_url_argument(['ellis'],'list'))

    def test_wash_pattern(self):
        """search engine - washing of query patterns"""
        self.assertEqual("Ellis, J", search_engine.wash_pattern('Ellis, J'))
        self.assertEqual("ell", search_engine.wash_pattern('ell*'))
        
def create_test_suite():
    """Return test suite for the search engine."""
    return unittest.TestSuite((unittest.makeSuite(TestWashQueryParameters,'test'),
                               unittest.makeSuite(TestStripAccents,'test'),
                               unittest.makeSuite(TestQueryParser,'test')))

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(create_test_suite())
