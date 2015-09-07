# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Filter for assets."""

from __future__ import unicode_literals

from flask import current_app

from webassets.filter.cssrewrite.base import PatternRewriter, urltag_re


__all__ = (
    'CSSUrlFixer',
)


# Helper class as a workaround for the strange cleancss URL handling
class CSSUrlFixer(PatternRewriter):

    """Helper to fix `url(...)` entries in CSS files."""

    patterns = {
        'rewrite_url': urltag_re
    }

    def __init__(self, subpath):
        """Create new CSSUrlFixer.

        :param subpath: relative subpath to the site URL, where all resources
            are located.
        """
        self.subpath = subpath
        super(CSSUrlFixer, self).__init__()

    def rewrite_url(self, matches):
        """Rewrite found URL pattern."""
        # Get the regex matches; note how we maintain the exact
        # whitespace around the actual url; we'll indeed only
        # replace the url itself.
        text_before = matches.groups()[0]
        url = matches.groups()[1]
        text_after = matches.groups()[2]

        # Normalize the url: remove quotes
        quotes_used = ''
        if url[:1] in '"\'':
            quotes_used = url[:1]
            url = url[1:]
        if url[-1:] in '"\'':
            url = url[:-1]

        url = self.replace_url(url) or url

        result = 'url({before}{quotes}{url}{quotes}{after})'.format(
            before=text_before, quotes=quotes_used, url=url, after=text_after
        )
        return result

    def replace_url(self, url):
        """Replace given URL with a new one."""
        return "{}/{}/{}".format(
            current_app.config.get('CFG_SITE_URL'),
            self.subpath,
            url
        )
