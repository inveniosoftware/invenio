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

"""Authors data models."""

from sqlalchemy.orm.exc import MultipleResultsFound

from invenio.ext.sqlalchemy import db, utils
from invenio.modules.accounts.models import User
from invenio.modules.records.models import Record
from invenio.modules.records.api import get_record

from .errors import SignatureExistsError

# The 'authors_citation' table is an association table of publications.
# An 'authors_publication' cites an other 'authors_publication'.
Citation = db.Table('authors_citation', db.metadata,
                    db.Column('citer', db.Integer(15, unsigned=True),
                              db.ForeignKey('authors_publication.id')),
                    db.Column('cited', db.Integer(15, unsigned=True),
                              db.ForeignKey('authors_publication.id')))


class Publication(db.Model):

    """Model representing a publication entity.

    Each publication is associated to an Invenio bibrec (record),
    may have authors and may contain references to other publications.
    Finally, each publication may have citations by other publications.
    """

    __tablename__ = 'authors_publication'

    # When deleting a number of signatures, it should not be expected
    # by the mapper that the same number of publications should be
    # deleted, as many signatures can be associated with a publication.
    # This disables the default behaviour of the mapper to show a
    # warning.
    __mapper_args__ = {'confirm_deleted_rows': False}

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True, nullable=False)
    """Id of the publication (required)."""

    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Record.id), nullable=False)
    """Id of the associated Invenio bibrec (required)."""

    authors = db.relationship('Author', secondary='authors_signature',
                              secondaryjoin="""and_(
                                  Signature.id_author == Author.id,
                                  Signature.attribution.in_(
                                      ('unknown', 'verified')))""")
    """Authors of the publication."""

    references = db.relationship('Publication', secondary='authors_citation',
                                 primaryjoin=Citation.c.cited == id,
                                 secondaryjoin=Citation.c.citer == id,
                                 backref='citations')
    """Publications that this publication cites.
           Other direction: publications that cite this publication."""

    @property
    def record(self):
        """Get the Invenio record in JSON format.

        :return: an instance of a record in JSON format
        """
        return get_record(self.id_bibrec)

    def __repr__(self):
        """Return a printable representation of a Publication."""
        return 'Publication(id=%s)' % self.id

    @utils.session_manager
    def delete(self):
        """Delete a publication and the associated signatures.

        Note: This is the mandatory way to delete a publication when
        using database engines that do not support 'ON DELETE' clauses
        (e.g. MyISAM of MySQL).
        """
        sigs = Signature.query.filter(Signature.publication == self).all()
        for s in sigs:
            db.session.delete(s)

        db.session.delete(self)


class Author(db.Model):

    """Model representing an author entity.

    Each author may be associated to an Invenio author bibrec (record),
    an Invenio user and may have publications. Moreover,
    an author may have fellow coauthors and citations (based on his
    publications).
    """

    __tablename__ = 'authors_author'

    # When deleting a number of signatures, it should not be expected
    # by the mapper that the same number of authors should be deleted,
    # as many signatures can be associated with a publication. This
    # disables the default behaviour of the mapper to show a warning.
    __mapper_args__ = {'confirm_deleted_rows': False}

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True, nullable=False)
    """Id of the author (required)."""

    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                          db.ForeignKey(Record.id))
    """Id of the associated Invenio author bibrec."""

    id_user = db.Column(db.Integer(15, unsigned=True), db.ForeignKey(User.id))
    """Id of the associated Invenio user."""

    user = db.relationship('User', backref=db.backref("author", uselist=False))
    """Invenio user associated with this author."""
    publications = db.relationship('Publication',
                                   secondary='authors_signature',
                                   secondaryjoin="""and_(
                                    Signature.id_publication == Publication.id,
                                    Signature.attribution.in_(
                                     ('unknown', 'verified')))""")
    """Publications of the author."""

    @property
    def record(self):
        """Get the Invenio author record in JSON format.

        :return: an instance of an author record in JSON format
        """
        return get_record(self.id_bibrec)

    @property
    def coauthors(self):
        """Get the the authors co-writing this author's publications.

        :return: Author objects
        """
        return (coauthor for publication in self.publications
                for coauthor in publication.authors if coauthor != self)

    @property
    def citations(self):
        """Get the citations of this author's publications.

        :return: Publication objects
        """
        return (citation for publication in self.publications
                for citation in publication.citations)

    def __repr__(self):
        """Return a printable representation of an Author."""
        return 'Author(id=%s)' % self.id

    @utils.session_manager
    def delete(self):
        """Delete an author and modify the associated signatures.

        When deleting an author, the author field in the associated
        signatures should be set to None.

        Note: This is the mandatory way to delete a publication when
        using database engines that do not support 'ON DELETE' clauses
        (e.g. MyISAM of MySQL).
        """
        for s in Signature.query.filter(Signature.author == self).all():
            s.author = None
            db.session.add(s)
        db.session.commit()

        db.session.delete(self)


class Signature(db.Model):

    """Represents a signature of an author on a publication.

    A signature is the event when an author "signs" a publication.
    For example, "author A has written publication P" is a valid
    signature.

    Each signature has a unique id, an author and a publication.
    Additionally, each signature is associated to a curator and a JSON
    field representing raw metadata from the corresponding publication.

    Finally, each signature has an attribution field which represents
    a certainty level: a signature may be either attributed
    automatically (default), verified by a curator or rejected by a
    curator.
    """

    __tablename__ = 'authors_signature'
    __mapper_args__ = {'confirm_deleted_rows': False}

    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                   autoincrement=True, nullable=False)
    """Id of the signature (required)."""

    id_author = db.Column(db.Integer(15, unsigned=True),
                          db.ForeignKey(Author.id, ondelete="SET NULL"))
    """Id of the associated author."""

    id_publication = db.Column(db.Integer(15, unsigned=True),
                               db.ForeignKey(Publication.id), nullable=False)
    """Id of the associated publication."""

    id_curator = db.Column(db.Integer(15, unsigned=True),
                           db.ForeignKey(User.id))
    """Id of the last curator (User) of this signature."""

    raw_metadata = db.Column(db.JSON, default=None)
    """Raw metadata of the record in JSON format."""

    attribution = db.Column(db.Enum('unknown', 'rejected', 'verified',
                                    name='authors_attribution'),
                            default='unknown')
    """Attribution may be "unknown" (default), "verified", "rejected."""

    author = db.relationship('Author', backref='signatures')
    """Author who signs."""

    publication = db.relationship('Publication', backref='signatures')
    """Publication signed."""

    curator = db.relationship('User')
    """User who last curated this signature
           (disambiguation algorithm if None)"""

    def __repr__(self):
        """Return a printable representation of a Signature."""
        return 'Signature(id=%s)' % self.id

    @utils.session_manager
    def claim(self, curator):
        """Claim that the signature is a true event.

        :param curator: the User who verifies the truth
        """
        self.curator = curator
        self.attribution = 'verified'
        db.session.add(self)

    @utils.session_manager
    def disclaim(self, curator):
        """Disclaim that the signature is a true event.

        :param curator: the User who verifies the falseness
        """
        self.curator = curator
        self.attribution = 'rejected'
        db.session.add(self)

    @utils.session_manager
    def move(self, author, curator=None):
        """Modify the author in the signature.

        The attribution of the signature is not altered.

        :param author: the Author to move the signature to
        :param curator: the User who performs the move (optional)
        """
        self.curator = curator
        self.author = author
        db.session.add(self)

    @staticmethod
    @utils.session_manager
    def reassign(author, curator, signature):
        """Reassign a signature to a different author.

        The current author of a signature rejects the signature. Then,
        a new signature is created and claimed for the given author.

        :param author: the Author to reassign the signature to
        :param curator: the User who performs the reassignment
        :param signature: the signature to reassign

        :raise SignatureExistsError: the given author already has
                                     the given signature.
        """
        try:
            sig = Signature.query.filter_by(publication=signature.publication,
                                            author=author).scalar()
            if sig:
                raise SignatureExistsError(
                    "Cannot reassign signature {signature} to author {author} "
                    "for publication {signature.publication}. The author "
                    "already has a signature for this publication."
                    .format(signature=signature, author=author))
            signature.disclaim(curator)
            new_signature = Signature(publication=signature.publication,
                                      author=author)
            new_signature.claim(curator)
        except MultipleResultsFound as e:
            # This should not happen.
            raise e


__all__ = ('Publication', 'Author', 'Signature', 'Citation')
