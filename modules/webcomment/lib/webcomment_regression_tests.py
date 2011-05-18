# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

"""WebComment Regression Test Suite."""

__revision__ = "$Id$"

import unittest
import shutil
from mechanize import Browser, LinkNotFoundError, HTTPError

from invenio.config import \
     CFG_SITE_URL, \
     CFG_WEBDIR, \
     CFG_TMPDIR, \
     CFG_SITE_RECORD
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages
from invenio.dbquery import run_sql
from invenio.webcomment import query_add_comment_or_remark


def prepare_attachments():
    """
    We copy necessary files to temporary directory. Every time we will
    attach files to a comment, these files get moved, so this function
    must be called again.
    """
    shutil.copy(CFG_WEBDIR + '/img/journal_water_dog.gif', CFG_TMPDIR)
    shutil.copy(CFG_WEBDIR + '/img/invenio.css', CFG_TMPDIR)


class WebCommentWebPagesAvailabilityTest(unittest.TestCase):
    """Check WebComment web pages whether they are up or not."""

    def test_your_baskets_pages_availability(self):
        """webcomment - availability of comments pages"""

        baseurl = CFG_SITE_URL + '/%s/10/comments/' % CFG_SITE_RECORD

        _exports = ['', 'display', 'add', 'vote', 'report']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            error_messages.extend(test_web_page_content(url))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_webcomment_admin_interface_availability(self):
        """webcomment - availability of WebComment Admin interface pages"""

        baseurl = CFG_SITE_URL + '/admin/webcomment/webcommentadmin.py/'

        _exports = ['', 'comments', 'delete', 'users']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            # first try as guest:
            error_messages.extend(test_web_page_content(url,
                                                        username='guest',
                                                        expected_text=
                                                        'Authorization failure'))
            # then try as admin:
            error_messages.extend(test_web_page_content(url,
                                                        username='admin'))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_webcomment_admin_guide_availability(self):
        """webcomment - availability of WebComment Admin Guide"""
        self.assertEqual([],
                         test_web_page_content(CFG_SITE_URL + '/help/admin/webcomment-admin-guide',
                                               expected_text="WebComment Admin Guide"))
        return

    def test_webcomment_mini_review_availability(self):
        """webcomment - availability of mini-review panel on detailed record page"""
        url = CFG_SITE_URL + '/%s/12' % CFG_SITE_RECORD
        error_messages = test_web_page_content(url,
                                               expected_text="(Not yet reviewed)")


class WebCommentRestrictionsTest(unittest.TestCase):
    """Check WebComment restrictions"""

    def setUp(self):
        """Insert some comments in some records"""

        # Comments have access restrictions when:
        # - the comment is in a restricted collection ('viewrestrcoll' action)
        # - the comment is in a restricted discussion page ('viewcomment' action)
        # - the comment itself is restricted ('viewrestrcomment'
        #   action), either because of the markup of the record, or
        #   because it is a reply to a restricted comment.

        self.public_record = 5
        self.public_record_restr_comment = 6
        self.restr_record = 42
        self.restr_record_restr_comment = 41
        self.restricted_discussion = 76

        self.romeo_uid = 5
        self.jekyll_uid = 2
        self.attached_files = {'file1': CFG_TMPDIR + '/journal_water_dog.gif',
                               'file2': CFG_TMPDIR + '/invenio.css'}

        # Load content of texual file2
        prepare_attachments()
        fp = file(self.attached_files['file2'])
        self.attached_file2_content = fp.read()
        fp.close()

        # Insert a public comment in a public record (public collection)
        self.msg1 = "A test comment 1"
        self.public_comid = query_add_comment_or_remark(reviews=0, recID=self.public_record,
                                                        uid=self.romeo_uid, msg=self.msg1,
                                                        editor_type='textarea',
                                                        attached_files=self.attached_files)

        # Insert a public comment in a restricted record (restricted collection)
        self.msg2 = "A test comment 2"
        prepare_attachments()
        self.restr_comid_1 = \
                           query_add_comment_or_remark(reviews=0, recID=self.restr_record,
                                                       uid=self.jekyll_uid, msg=self.msg2,
                                                       editor_type='textarea',
                                                       attached_files=self.attached_files)

        # Insert a restricted comment in a public collection
        self.msg3 = "A test comment 3"
        prepare_attachments()
        self.restr_comid_2 = \
                           query_add_comment_or_remark(reviews=0, recID=self.public_record_restr_comment,
                                                       uid=self.jekyll_uid, msg=self.msg3,
                                                       editor_type='textarea',
                                                       attached_files=self.attached_files)

        # Insert a restricted comment, in a restricted collection
        self.msg5 = "A test comment 5"
        prepare_attachments()
        self.restr_comid_4 = \
                           query_add_comment_or_remark(reviews=0, recID=self.restr_record_restr_comment,
                                                       uid=self.romeo_uid, msg=self.msg5,
                                                       editor_type='textarea',
                                                       attached_files=self.attached_files)

        # Insert a public comment in a restricted discussion
        self.msg6 = "A test comment 6"
        prepare_attachments()
        self.restr_comid_5 = \
                           query_add_comment_or_remark(reviews=0, recID=self.restricted_discussion,
                                                       uid=self.romeo_uid, msg=self.msg6,
                                                       editor_type='textarea',
                                                       attached_files=self.attached_files)
        self.restr_comid_3 = None

    def tearDown(self):
        """Remove inserted comments"""
        run_sql("""DELETE FROM cmtRECORDCOMMENT WHERE id=%s""", (self.public_comid,))
        run_sql("""DELETE FROM cmtRECORDCOMMENT WHERE id=%s""", (self.restr_comid_1,))
        run_sql("""DELETE FROM cmtRECORDCOMMENT WHERE id=%s""", (self.restr_comid_2,))
        if self.restr_comid_3:
            run_sql("""DELETE FROM cmtRECORDCOMMENT WHERE id=%s""", (self.restr_comid_3,))
        run_sql("""DELETE FROM cmtRECORDCOMMENT WHERE id=%s""", (self.restr_comid_4,))
        run_sql("""DELETE FROM cmtRECORDCOMMENT WHERE id=%s""", (self.restr_comid_5,))
        pass

    def test_access_public_record_public_discussion_public_comment(self):
        """webcomment - accessing "public" comment in a "public" discussion of a restricted record"""
        # Guest user should not be able to access it
        self.assertNotEqual([],
                         test_web_page_content("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record),
                                               expected_text=self.msg2))

        # Accessing a non existing file for a restricted comment should also ask to login
        self.assertEqual([],
                         test_web_page_content("%s/%s/%i/comments/attachments/get/%i/not_existing_file" % \
                                               (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record, self.restr_comid_1),
                                               expected_text='You can use your nickname or your email address to login'))

        # Check accessing file of a restricted comment
        self.assertEqual([],
                         test_web_page_content("%s/%s/%i/comments/attachments/get/%i/file2" % \
                                               (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record, self.restr_comid_1),
                                               expected_text='You can use your nickname or your email address to login'))


    def test_access_restricted_record_public_discussion_public_comment(self):
        """webcomment - accessing "public" comment in a "public" discussion of a restricted record"""
        # Guest user should not be able to access it
        self.assertNotEqual([],
                         test_web_page_content("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record),
                                               expected_text=self.msg2))

        # Accessing a non existing file for a restricted comment should also ask to login
        self.assertEqual([],
                         test_web_page_content("%s/%s/%i/comments/attachments/get/%i/not_existing_file" % \
                                               (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record, self.restr_comid_1),
                                               expected_text='You can use your nickname or your email address to login'))

        # Check accessing file of a restricted comment
        self.assertEqual([],
                         test_web_page_content("%s/%s/%i/comments/attachments/get/%i/file2" % \
                                               (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record, self.restr_comid_1),
                                               expected_text='You can use your nickname or your email address to login'))

        # Juliet should not be able to access the comment
        br = Browser()
        br.open(CFG_SITE_URL + '/youraccount/login')
        br.select_form(nr=0)
        br['p_un'] = 'juliet'
        br['p_pw'] = 'j123uliet'
        br.submit()
        br.open("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record))
        response = br.response().read()
        if not self.msg2 in response:
            pass
        else:
            self.fail("Oops, this user should not have access to this comment")

        # Juliet should not be able to access the attached files
        br.open("%s/%s/%i/comments/attachments/get/%i/file2" % \
                     (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record, self.restr_comid_1))
        response = br.response().read()
        if "You are not authorized" in response:
            pass
        else:
            self.fail("Oops, this user should not have access to this comment attachment")

        # Jekyll should be able to access the comment
        br = Browser()
        br.open(CFG_SITE_URL + '/youraccount/login')
        br.select_form(nr=0)
        br['p_un'] = 'jekyll'
        br['p_pw'] = 'j123ekyll'
        br.submit()
        br.open("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record))
        response = br.response().read()
        if not self.msg2 in response:
            self.fail("Oops, this user should have access to this comment")

        # Jekyll should be able to access the attached files
        br.open("%s/%s/%i/comments/attachments/get/%i/file2" % \
                     (CFG_SITE_URL, CFG_SITE_RECORD, self.restr_record, self.restr_comid_1))
        response = br.response().read()
        self.assertEqual(self.attached_file2_content, response)

    def test_access_public_record_restricted_discussion_public_comment(self):
        """webcomment - accessing "public" comment in a restricted discussion of a public record"""
        # Guest user should not be able to access it
        self.assertNotEqual([],
                         test_web_page_content("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion),
                                               expected_text=self.msg2))

        # Accessing a non existing file for a restricted comment should also ask to login
        self.assertEqual([],
                         test_web_page_content("%s/%s/%i/comments/attachments/get/%i/not_existing_file" % \
                                               (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion, self.restr_comid_5),
                                               expected_text='You can use your nickname or your email address to login'))

        # Check accessing file of a restricted comment
        self.assertEqual([],
                         test_web_page_content("%s/%s/%i/comments/attachments/get/%i/file2" % \
                                               (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion, self.restr_comid_5),
                                               expected_text='You can use your nickname or your email address to login'))

        # Juliet should not be able to access the comment
        br = Browser()
        br.open(CFG_SITE_URL + '/youraccount/login')
        br.select_form(nr=0)
        br['p_un'] = 'juliet'
        br['p_pw'] = 'j123uliet'
        br.submit()
        br.open("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion))
        response = br.response().read()
        if not self.msg6 in response:
            pass
        else:
            self.fail("Oops, this user should not have access to this comment")

        # Juliet should not be able to access the attached files
        br.open("%s/%s/%i/comments/attachments/get/%i/file2" % \
                     (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion, self.restr_comid_5))
        response = br.response().read()
        if "You are not authorized" in response:
            pass
        else:
            self.fail("Oops, this user should not have access to this comment attachment")

        # Romeo should be able to access the comment
        br = Browser()
        br.open(CFG_SITE_URL + '/youraccount/login')
        br.select_form(nr=0)
        br['p_un'] = 'romeo'
        br['p_pw'] = 'r123omeo'
        br.submit()
        br.open("%s/%s/%i/comments/" % (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion))
        response = br.response().read()
        if not self.msg6 in response:
            self.fail("Oops, this user should have access to this comment")

        # Romeo should be able to access the attached files
        br.open("%s/%s/%i/comments/attachments/get/%i/file2" % \
                     (CFG_SITE_URL, CFG_SITE_RECORD, self.restricted_discussion, self.restr_comid_5))
        response = br.response().read()
        self.assertEqual(self.attached_file2_content, response)

    def test_comment_replies_inherit_restrictions(self):
        """webcomment - a reply to a comment inherits restrictions"""
        # In this test we reply to a restricted comment, and check if
        # the restriction is inherited. However, in order to make sure
        # that the comment restriction is inherited, and not the
        # record restriction, we temporary change the restriction of
        # the parent.
        self.public_record_restr_comment
        original_restriction = run_sql("SELECT restriction FROM cmtRECORDCOMMENT WHERE id=%s",
                                       (self.restr_comid_2,))[0][0]
        restriction_to_inherit = 'juliet_only'
        run_sql("UPDATE cmtRECORDCOMMENT SET restriction=%s WHERE id=%s",
                (restriction_to_inherit, self.restr_comid_2))

        # Reply to a restricted comment
        self.msg4 = "A test comment 4"
        prepare_attachments()
        self.restr_comid_3 = \
                           query_add_comment_or_remark(reviews=0, recID=self.public_record_restr_comment,
                                                       uid=self.jekyll_uid, msg=self.msg4,
                                                       editor_type='textarea',
                                                       attached_files=self.attached_files,
                                                       reply_to=self.restr_comid_2)

        inherited_restriction = run_sql("SELECT restriction FROM cmtRECORDCOMMENT WHERE id=%s",
                                        (self.restr_comid_3,))[0][0]

        self.assertEqual(restriction_to_inherit, inherited_restriction)

        # Restore original restriction
        run_sql("UPDATE cmtRECORDCOMMENT SET restriction=%s WHERE id=%s",
                (original_restriction, self.restr_comid_2))

TEST_SUITE = make_test_suite(WebCommentWebPagesAvailabilityTest,
                             WebCommentRestrictionsTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)
