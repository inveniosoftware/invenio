# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Restful pagination."""

from flask import request, url_for
from invenio.utils.pagination import Pagination as InvenioPagination
from .errors import InvalidPageError


class RestfulPaginationMixIn(object):

    """Provide implementaion methods :meth:`link_header` and :meth:`links`."""

    def link_header(self, **kwargs):
        """Return tuple that can be used in response header."""
        links = self.links(**kwargs)
        keys = ("first", "prev", "next", "last")
        links_string = ",".join([links[key] for key in keys if key in links])
        return ('Link', links_string)

    def links(self, endpoint=None, args=None):
        """Generate links for the headers.

        :param endpoint: the URL endpoint
        :param args: the arguments of request
        :param count: the total number of items
        """
        if not endpoint:
            endpoint = request.endpoint
        if not args:
            args = request.args

        links = {}
        link_template = '<{}>; rel="{}"'

        # arguments to stick to the URL
        url_args = {}
        # url_args['page'] will be updated for every link
        url_args['page'] = 1
        url_args['per_page'] = self.per_page

        # generate link for rel first
        links['first'] = link_template.format(
            url_for(endpoint, **url_args), "first"
        )

        # generate link for prev if it exists
        if self.has_prev:
            url_args['page'] = self.page - 1
            links['prev'] = link_template.format(
                url_for(endpoint, **url_args), "prev"
            )

        # generate link for next if it exists
        if self.has_next:
            url_args['page'] = self.page + 1
            links['next'] = link_template.format(
                url_for(endpoint, **url_args), "next"
            )

        # generate link for last
        url_args['page'] = self.pages
        links['last'] = link_template.format(
            url_for(endpoint, **url_args), "last"
        )
        return links


class SQLAlchemyPaginationHelper(object):

    """Wrap SQLAlchemy query `paginate` method."""

    def __init__(self, query, page, per_page):
        """Initialize pagination property.

        :param query: query object from SQLAlchemy
        """
        self.query = query
        self.page = page
        self.per_page = per_page
        self.pagination = self.query.paginate(self.page, self.per_page, False)


class RestfulSQLAlchemyPagination(SQLAlchemyPaginationHelper,
                                  RestfulPaginationMixIn):

    """Implement Restful pagination for SQLAlchemy model."""

    @property
    def items(self):
        """Return found items."""
        return self.pagination.items

    @property
    def pages(self):
        """Return number of pages."""
        return self.pagination.pages

    @property
    def has_next(self):
        """Return `True` if has next page otherwise return `False`."""
        return self.pagination.has_next

    @property
    def has_prev(self):
        """Return `True` if has previous page otherwise return `False`."""
        return self.pagination.has_prev


class RestfulPagination(InvenioPagination, RestfulPaginationMixIn):

    """Implement Restful pagination for list of data."""

    def __init__(self, page, per_page, total_count, validate=True):
        super(RestfulPagination, self).__init__(page, per_page, total_count)
        if validate:
            self.validate()

    def validate(self):
        """Validate the range of page and per_page."""
        if self.per_page < 0:
            error_msg = (
                "Invalid per_page argument ('{0}'). Number of items "
                "per pages must be positive integer.".format(self.per_page)
            )
            raise InvalidPageError(error_msg)
        if self.page < 0 or self.page > self.pages:
            error_msg = "Invalid page number ('{0}').".format(self.page)
            raise InvalidPageError(error_msg)

    def slice(self, items):
        """Return items on current page."""
        return items[(self.page - 1) * self.per_page:self.page * self.per_page]
