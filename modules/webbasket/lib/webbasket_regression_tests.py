# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""WebBasket Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import mechanize

from invenio.config import weburl
from invenio.testutils import make_test_suite, warn_user_about_tests_and_run, \
                              test_web_page_content, make_url, make_surl, merge_error_messages

class WebBasketWebPagesAvailabilityTest(unittest.TestCase):
    """Check WebBasket web pages whether they are up or not."""

    def test_your_baskets_pages_availability(self):
        """webbasket - availability of Your Baskets pages""" 

        baseurl = weburl + '/yourbaskets/'

        _exports = ['', 'display', 'display_item', 'write_comment',
                    'save_comment', 'delete_comment', 'add', 'delete',
                    'modify', 'edit', 'create_basket', 'display_public',
                    'list_public_baskets', 'unsubscribe', 'subscribe']
        
        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

class WebBasketRecordsAdditionTest(unittest.TestCase):
    """Test addition of records to webbasket"""
    
    def _login(self, browser, user, password):
        """Log the user in an existing browser using his password"""
        
        browser.open(make_surl('/youraccount/login'))
        browser.select_form(nr=0)
        browser['p_un'] = user
        browser['p_pw'] = password
        browser.submit() 

    def _perform_search(self, browser, search_criteria):
        """Perform search in an existing browser using the specified criteria. 
        Calling the method is equal of typing the criteria in the search box 
        and pressing the 'search' button."""       
            
        # open the search page that in our case is the default page
        browser.open(make_url('/'))
        
        # perform search
        browser.select_form(name = 'search')
        browser['p'] = search_criteria
        browser.submit(name = 'action_search')
        
    def _select_records_for_adding_to_basket(self, browser, records):
        """Calling this method is is equal of selecting records from 
        the search results and pressing 'ADD TO BASKET' button """    
        
        # select the proper form containing the check boxes for marking the records 
        browser.select_form(nr = 2)
        
        # select the records
        control = browser.find_control('recid')
        
        for current_record in records:
            control.items[current_record].selected = True
        
        # press 'ADD TO BASKET' button
        browser.submit();        
        
    def _create_new_basket_and_add_records(self, browser, basket_name, topic_name):
        browser.select_form(name = 'add_to_basket')
        browser['new_basket_name'] = basket_name
        browser['new_topic_name'] = topic_name
        browser.submit()
        
    def _check_basket_content(self, browser, expected_texts):
        browser.open(make_surl('/yourbaskets/display?ln=en'))
        url_body = browser.response().read()
        
        for current_expected_text in expected_texts:
            if current_expected_text not in url_body:
                self.fail('Expects to find ' + current_expected_text + ' in the basket')
                
    def _add_records_to_basket_and_check_content(self, browser):
        """add records to basket and check content of baskets page for 
        expexted strings """
        
        self._perform_search(browser, 'ellis')
        self._select_records_for_adding_to_basket(browser, [0, 6])        
        self._create_new_basket_and_add_records(browser, 'Test Basket', 'Test Topic')

        expected_texts = ['Test Topic', 'Test Basket', '2 records',
                          'Thermal conductivity of dense quark matter and cooling of stars', 
                          'The total cross section for the production of heavy quarks in hadronic collisions']
        self._check_basket_content(browser, expected_texts)
        
    def test_records_addition_as_guest_user(self):
        """webbasket - addition of records as guest"""
        
        browser = mechanize.Browser()
        self._add_records_to_basket_and_check_content(browser)
                    
    def test_records_addition_as_registered_user(self):
        """webbasket - addition of records as registered user"""
        
        browser = mechanize.Browser()
        self._login(browser, 'jekyll', 'j123ekyll')
        # FIXME: remove the comment and add method to clean the baskets after the test
        # self._add_records_to_basket_and_check_content(browser)

test_suite = make_test_suite(WebBasketWebPagesAvailabilityTest, WebBasketRecordsAdditionTest)

if __name__ == "__main__":
    warn_user_about_tests_and_run(test_suite)
