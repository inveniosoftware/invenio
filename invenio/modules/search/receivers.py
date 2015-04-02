# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Define custom action handlers."""

import os

from flask import flash, g, current_app
from logging import Formatter, getLogger, FileHandler
from six import iteritems
from werkzeug.local import LocalProxy


def get_logger():
    """Get search logger."""
    logger = getattr(g, 'search_logger', None)
    if logger is None:
        handler = FileHandler(
            os.path.join(current_app.config['CFG_LOGDIR'], 'search.log'),
            delay=True
        )
        logger = getLogger('invenio.search')
        formatter = Formatter('{asctime}#{action}#{p}#{f}#{colls}#{total}',
                              datefmt='%Y%m%d%H%M%S', style='{')

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        g.search_logger = logger
    return logger

logger = LocalProxy(get_logger)


def websearch_before_browse_handler(collection, **kwargs):
    """Flash message before browsing handler is called."""
    # keys = ['p', 'p1', 'p2', 'p3', 'f', 'f1', 'f2', 'f3', 'rm', 'cc', 'ln',
    #         'jrec', 'rg', 'aas', 'action']
    # kwargs = dict(filter(lambda (k, v): k in keys, iteritems(kwargs)))
    # if kwargs.get('action', '') == 'browse':
    # if msg and len(msg) > 0:
    #     flash(_("Did you mean to browse in %{x_index_name} index?",
    #             url), 'websearch-after-search-form')


def after_search(app, **kwargs):
    """Log user query after search."""
    from .models import UserQuery
    UserQuery.log()
    logger.info(extra=kwargs)


def after_insert_user_query():
    """Flash message after user query is logged."""
    #  of = request.values.get('of', 'hb')
    #  if of.startswith("h") and (em == '' or EM_REPOSITORY["alert"] in em):
    #      if not of in ['hcs', 'hcs2']:
    #          # display alert/RSS teaser for non-summary formats:
    #          display_email_alert_part = True
    #          if current_user:
    #              if current_user['email'] == 'guest':
    #                  if CFG_ACCESS_CONTROL_LEVEL_ACCOUNTS > 4:
    #                      display_email_alert_part = False
    #              else:
    #                  if not current_user['precached_usealerts']:
    #                      display_email_alert_part = False
    #          from flask import flash
    #          flash(websearch_templates.tmpl_alert_rss_teaser_box_for_query(
    #               id_query,
    #               ln=ln,
    #               display_email_alert_part=display_email_alert_part),
    #               'search-results-after')
    pass
