# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""WebTag Regression Tests"""

from invenio.base.wrappers import lazy_import
from invenio.testsuite import \
    InvenioTestCase, \
    make_test_suite, \
    run_test_suite
from mechanize import Browser

from invenio.config import CFG_SITE_SECURE_URL

cfg = lazy_import('invenio.webtag_config')
webtag_model = lazy_import('invenio.webtag_model')
db = lazy_import('invenio.sqlalchemyutils:db')


class WebTagDeletionTest(InvenioTestCase):
    """Check if deleting w WtgTAG clears all associations"""
    def test_record_association_deletion(self):
        """webtag - are WtgTAGRecord rows deleted when WtgTAG is deleted?"""

        # (1) Create a new tag
        new_tag = webtag_model.WtgTAG()
        new_tag.id_user = 1
        new_tag.name = 'test record association deletion'
        db.session.add(new_tag)
        db.session.commit()
        db.session.refresh(new_tag)

        new_tag_id = new_tag.id

        # (2) Create the associations
        for recid in range(1, 5):
            new_association = webtag_model.WtgTAGRecord()
            new_association.tag = new_tag
            new_association.id_bibrec = recid
            db.session.add(new_association)

        db.session.commit()

        # (3) Delete the tag
        db.session.delete(new_tag)
        db.session.commit()

        # (4) Are there any associations left?
        associations_left = webtag_model.WtgTAGRecord.query\
            .filter_by(id_tag=new_tag_id)\
            .count()

        self.assertEqual(0, associations_left)


class WebTagUserSettingsTest(InvenioTestCase):
    """Check if the preferences for WebTag are editable and properly saved"""

    def login(self, username, password):
        browser = Browser()
        browser.open(CFG_SITE_SECURE_URL + "/youraccount/login/")
        browser.select_form(nr=0)
        browser['nickname'] = username
        browser['password'] = password

        try:
            browser.submit()
        except Exception, e:
            self.fail("Cannot login with nickname={name} password={pw}."\
                .format(name=username, pw=password))

        return browser

    def test_preferences_edition(self):
        browser = self.login('admin', '')

        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit/WebTagSettings")
        browser.select_form(nr=0)
        browser['display_tags_private'] = '0'
        browser.submit()

        browser.open(CFG_SITE_SECURE_URL + "/youraccount/edit/WebTagSettings")
        browser.select_form(nr=0)

        if browser['display_tags_private'] != '0':
            self.fail("Setting 'display_tags_private' saved as False, but is still True")

        browser['display_tags_private'] = '1'
        browser.submit()


# Running tests
TEST_SUITE = make_test_suite(
    WebTagDeletionTest,
    WebTagUserSettingsTest
)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
