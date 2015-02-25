# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2014 CERN.
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

"""Tests for Authors Models."""
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class AuthorModelsTestCase(InvenioTestCase):

    """Base class for author model tests."""

    def setUp(self):
        """Basic setup for tests."""
        self.import_context()
        self._dummy_record = self.Record()
        self.db.session.add(self._dummy_record)
        self.db.session.commit()

        self._user = self.User(password='test')
        self._publications = [self.Publication(id_bibrec=self._dummy_record.id)
                              for _ in range(0, 3)]
        self._authors = [self.Author() for _ in range(0, 3)]

        map(self._publications[0].authors.append, self._authors[0:2])
        map(self._publications[1].authors.append, self._authors[1:3])
        self._publications[2].authors.append(self._authors[0])
        self._publications[0].references.append(self._publications[1])

        self.db.session.add(self._user)
        map(self.db.session.add, self._authors)
        map(self.db.session.add, self._publications)
        self.db.session.commit()

    def tearDown(self):
        """Basic teardown for tests."""
        for author in self._authors:
            author.delete()

        for publication in self._publications:
            publication.delete()

        self.db.session.delete(self._dummy_record)
        self.db.session.delete(self._user)
        self.db.session.commit()

    def import_context(self):
        """Import the Invenio classes here to make sure the testing
           context is valid."""
        from invenio.ext.sqlalchemy import db
        from invenio.modules.authors import models
        from invenio.modules.accounts.models import User
        from invenio.modules.records.models import Record
        from invenio.modules.authors.errors import SignatureExistsError

        self.db = db
        self.Author = models.Author
        self.Publication = models.Publication
        self.Signature = models.Signature
        self.User = User
        self.SignatureExistsError = SignatureExistsError
        self.Record = Record


class AuthorsModelsBasicTestCase(AuthorModelsTestCase):

    """Basic models tests."""

    def test_publication_has_author(self):
        """Publications should have authors assigned automatically."""
        pub_authors = self._publications[0].authors

        self.assertEqual(set(pub_authors), {self._authors[0],
                                            self._authors[1]})

    def test_author_has_publication(self):
        """Authors should have publications assigned automatically."""
        author_pubs = self._authors[0].publications

        self.assertEqual(set(author_pubs),
                         {self._publications[0], self._publications[2]})

        author_pubs = self._authors[1].publications

        self.assertEqual(set(author_pubs),
                         {self._publications[0], self._publications[1]})

    def test_references_and_citations(self):
        """The references of a paper should be the citations of the
           referenced paper."""
        self.assertEqual(self._publications[0].references,
                         [self._publications[1]])

        self.assertEqual(self._publications[1].citations,
                         [self._publications[0]])

    def test_coauthors(self):
        """Test for author.coauthors."""
        self.assertEqual(tuple(self._authors[0].coauthors),
                         (self._authors[1],))

    def test_author_citations(self):
        """Test for author.citations."""
        self.assertEqual(tuple(self._authors[2].citations),
                         (self._publications[0],))

    def test_author_user_one_to_one_relationship(self):
        """The author should be connected to one user only.
           The access of the author associated to the user should
           be possible."""
        self._authors[0].user = self._user
        self.db.session.add(self._authors[0])
        self.db.session.commit()
        self.assertEqual(self._authors[0].user, self._user)
        self.assertEqual(self._user.author, self._authors[0])

        self._authors[1].user = self._user
        self.db.session.add(self._authors[1])
        self.db.session.commit()
        self.assertFalse(self._authors[0].user)
        self.assertEqual(self._authors[1].user, self._user)
        self.assertEqual(self._user.author, self._authors[1])


class TestAuthorsModelsCleanup(AuthorModelsTestCase):

    """Models tests testing the deletion of models and side-effects."""

    def setUp(self):
        """Additional setup for claiming tests."""
        self.import_context()
        self._dummy_record = self.Record()
        self.db.session.add(self._dummy_record)
        self.db.session.commit()

        self._publications = [self.Publication(id_bibrec=self._dummy_record.id)
                              for _ in range(0, 3)]
        self._author = self.Author()
        self._user = self.User(password='test')
        self._author.user = self._user

        map(self._author.publications.append, self._publications)
        self.db.session.add(self._author)
        map(self.db.session.add, self._publications)
        self.db.session.add(self._user)
        self.db.session.commit()

    def tearDown(self):
        """Additional teardown for claiming tests."""
        try:
            self._author.delete()
        except AttributeError:
            pass
        for publication in self._publications:
            try:
                publication.delete()
            except AttributeError:
                pass
        self.db.session.delete(self._dummy_record)
        self.db.session.delete(self._user)
        self.db.session.commit()

    def test_author_deletion(self):
        """When an author is deleted, the respective signatures should
           have NULL as author. The publications should be there"""
        sigs = self.Signature.query.filter(
            self.Signature.author == self._author).all()
        self._author.delete()

        self.assertEqual([None] * 3, [sig.author for sig in sigs])
        self.assertTrue(self._user)

    def test_publication_deletion(self):
        """When a publication is deleted the respective signatures should be
           deleted"""
        self._publications[0].delete()
        deleted_pub = self._publications[0]

        self.assertFalse(self.Signature.query.filter(
            self.Signature.publication == deleted_pub).all())

    def test_signature_deletion(self):
        """When a signature is deleted, neither the publication or
           the author should be deleted. However, the link between
           the publication and the author should disappear."""
        pub1 = self._publications[0]
        sign1 = self.Signature.query.filter(
            self.Signature.publication == pub1).all()[0]
        self.db.session.delete(sign1)
        self.db.session.commit()

        author = self._author
        publication = self._publications[0]

        self.assertTrue(author)
        self.assertTrue(publication)
        self.assertEqual(set(author.publications), set(self._publications[1:]))

    def test_user_deletion(self):
        """When a user gets deleted, the author should stay intact."""
        self.db.session.delete(self._user)
        self.assertTrue(self._author)


class TestAuthorsModelsClaims(AuthorModelsTestCase):

    """Tests for the claiming operations of signatures"""

    def setUp(self):
        """Additional setup for claiming tests."""
        super(TestAuthorsModelsClaims, self).setUp()
        pub_2 = self._publications[1]
        self._authors[0].publications.append(pub_2)
        self.db.session.add(self._authors[0])
        self.db.session.commit()

    def tearDown(self):
        """Additional teardown for claiming tests."""
        self.db.session.commit()
        super(TestAuthorsModelsClaims, self).tearDown()

    def _get_signature(self, author, publication):
        """Get signature for author and publication.

        Fails test if no or many signatures are found.
        """
        sig_query = self.Signature.query.filter(
            self.db.and_(self.Signature.author == author,
                         self.Signature.publication == publication))
        try:
            sig = sig_query.one()
        except NoResultFound:
            self.fail('No signature found for author: %s and publication %s' %
                      (author, publication))
        except MultipleResultsFound:
            self.fail("""Multiple signatures found for author: %s and
            publication %s. In the context of the test this is wrong.""" %
                      (author, publication))
        return sig

    def test_signature_claim(self):
        """When a signature is claimed, the attribution status is set
           to 'verified' and the user claiming becomes the curator."""
        sig = self._get_signature(self._authors[0],
                                  self._publications[1])
        sig_id = sig.id
        sig.claim(self._user)
        self.assertEqual(sig.author, self.Signature.query.get(sig_id).author)
        self.assertEqual(self._user,
                         self.Signature.query.get(sig_id).curator)
        self.assertEqual(self.Signature.query.get(sig_id).attribution,
                         'verified')

    def test_signature_disclaim(self):
        """When a signature is disclaimed, the attribution status
           is set to verified and the user disclaiming becomes the
           curator."""
        sig = self._get_signature(self._authors[0],
                                  self._publications[1])
        sig_id = sig.id
        pubs_before = len(sig.author.publications)
        sig.disclaim(self._user)
        self.assertEqual(pubs_before, len(sig.author.publications) + 1)
        self.assertEqual(sig.author, self.Signature.query.get(sig_id).author)
        self.assertEqual(self._user,
                         self.Signature.query.get(sig_id).curator)
        self.assertEqual(self.Signature.query.get(sig_id).attribution,
                         'rejected')
        self.assertFalse(self._publications[1]
                         in self._authors[0].publications)
        self.assertFalse(self._authors[0] in self._publications[1].authors)

    def test_signature_move(self):
        """No attribution should be altered.
           Only the author and the curator should be modified."""
        sig = self._get_signature(self._authors[0],
                                  self._publications[1])
        sig_len_before = self.db.session.query(self.Signature).count()
        sig.move(self._authors[1])
        sig_len_after = self.db.session.query(self.Signature).count()

        self.assertFalse(self._publications[1]
                         in self._authors[0].publications)

        self.assertTrue(self._publications[1]
                        in self._authors[1].publications)

        self.assertEqual(sig_len_before, sig_len_after)

    def test_signature_reassignment(self):
        """A new signature should be created.
           The old signature should have an attribution of 'rejected'
           and the new signature should have an attribution of 'verified'."""
        sig = self._get_signature(self._authors[0], self._publications[2])
        sig_len_before = self.db.session.query(self.Signature).count()
        self.Signature.reassign(self._authors[2], self._user, sig)
        sig_len_after = self.db.session.query(self.Signature).count()
        self.assertEqual(sig_len_before + 1, sig_len_after)
        self.assertEqual(sig.attribution, 'rejected')
        one_sig = self.Signature.query.filter_by(
            publication=self._publications[2], author=self._authors[2]).one()
        self.assertTrue(one_sig)
        self.assertEqual(one_sig.attribution, 'verified')

    def test_signature_reassignment_already_assigned(self):
        """A Signature cannot be reassigned to an author who already
           owns this signature. A SignatureExistsError should be
           raised."""
        sig = self._get_signature(self._authors[0], self._publications[1])
        try:
            with self.assertRaises(self.SignatureExistsError):
                self.Signature.reassign(self._authors[0], self._user, sig)
        except AssertionError:
            self.fail("""SignatureExistsError was not raised,
                when trying to associate a second signature to
                the same pair of self.Author and Publications""")


TEST_SUITE = make_test_suite(AuthorsModelsBasicTestCase,
                             TestAuthorsModelsCleanup,
                             TestAuthorsModelsClaims)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
