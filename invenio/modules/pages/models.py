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

"""Contains page model."""

from invenio.ext.sqlalchemy import db
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime


class Page(db.Model):

    """Represents a page."""

    __tablename__ = 'pages'

    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    """Page identifier."""

    url = db.Column(db.String(100), unique=True, nullable=False)
    """Page url."""

    title = db.Column(db.String(200), nullable=True)
    """Page title."""

    content = db.Column(
        db.Text().with_variant(db.Text(length=2**32-2), 'mysql'),
        nullable=True)
    # Default is pages/templates/default.html

    description = db.Column(db.String(200), nullable=True)
    """Page description."""

    template_name = db.Column(db.String(70), nullable=True)
    """Page template name. Default is pages/templates/pages/default.html."""

    background_image = db.Column(db.String(100), nullable=True)
    """Page background image url."""

    icon = db.Column(db.String(100), nullable=True)
    """Page icon name."""

    created = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    """Page creation date."""

    last_modified = db.Column(db.DateTime(), nullable=False,
                              default=datetime.now, onupdate=datetime.now)
    """Page last modification date."""

    def is_list_of_pages(self):
        """Check if this Page represents PageList.
        :returns: True if Page represents some PageList, False in other case.
        """
        try:
            PageList.query.filter_by(page_id=self.id).one()
            return True
        except NoResultFound:
            return False

    def get_list_id(self):
        """Get id of a PageList this Page represents.
        :returns: PageList id or None.
        """
        if self.is_list_of_pages():
            try:
                pl = PageList.query.join(Page).filter_by(id=self.id).one()
                return pl.id
            except NoResultFound:
                return None
        else:
            return None

    def get_pages(self):
        """Get list of Pages which belong to the PageList this Page represents.
        :returns: a list of Pages.
        """
        if self.is_list_of_pages():
            return Page.query.join(
                PagePageList).filter_by(
                    list_id=self.get_list_id()).all()
        else:
            return []


class PageList(db.Model):
    """Represents a list of pages."""
    __tablename__ = 'pagesLIST'

    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    """Page list identifier."""

    page_id = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(Page.id), nullable=False)
    """Id of a page, which represents this list."""

    page = db.relationship(Page, backref="represents_list")
    """Relation to the page."""


class PagePageList(db.Model):
    """Represent associative table of page and pages list."""
    __tablename__ = 'pages_pagesLIST'

    id = db.Column(db.Integer(15, unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    """PagePageList identifier."""

    list_id = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(PageList.id), nullable=False)
    """Id of a list page belongs to."""

    page_id = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(Page.id), nullable=False)
    """Id of a page."""

    list = db.relationship(PageList, backref="pages")
    """Relation to the list."""

    page = db.relationship(Page, backref="part_of_lists")
    """Relation to the page."""


__all__ = ['Page', 'PageList', 'PagePageList']
