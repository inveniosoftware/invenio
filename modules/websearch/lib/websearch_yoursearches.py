## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""User searches personal features."""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL
from invenio.dbquery import run_sql
from invenio.webaccount import warning_guest_user
from invenio.webalert import get_textual_query_info_from_urlargs
from invenio.messages import gettext_set_language
from invenio.webuser import isGuestUser

import invenio.template
websearch_templates = invenio.template.load('websearch')

def perform_request_yoursearches_display(uid,
                                         ln=CFG_SITE_LANG):
    """
    Display the user's search history.
    @param uid: the user id
    @type uid: integer
    @return: A list of searches queries in formatted html.
    """
    
    # load the right language
    _ = gettext_set_language(ln)

    # firstly, calculate the number of total and distinct queries
    nb_queries_total = 0
    nb_queries_distinct = 0
    query_nb_queries = """ SELECT  COUNT(*),
                                   COUNT(DISTINCT(id_query))
                           FROM    user_query
                           WHERE   id_user=%s"""
    params_nb_queries = (uid,)
    res_nb_queries = run_sql(query_nb_queries, params_nb_queries)
    nb_queries_total = res_nb_queries[0][0]
    nb_queries_distinct = res_nb_queries[0][1]

    # secondly, calculate the search queries
    query = """ SELECT      DISTINCT(q.id),
                            q.urlargs,
                            DATE_FORMAT(MAX(uq.date),'%%Y-%%m-%%d %%H:%%i:%%s')
                FROM        query q,
                            user_query uq
                WHERE       uq.id_user=%s
                    AND     uq.id_query=q.id
                GROUP BY    uq.id_query
                ORDER BY    q.id DESC"""
    params = (uid,)
    result = run_sql(query, params)

    search_queries = []
    if result:
        for search_query in result:
            search_query_id = search_query[0]
            search_query_args = search_query[1]
            search_query_lastrun = search_query[2] or _("unknown")
            search_queries.append({'id' : search_query_id,
                                   'args' : search_query_args,
                                   'textargs' : get_textual_query_info_from_urlargs(search_query_args, ln=ln),
                                   'lastrun' : search_query_lastrun})

    return websearch_templates.tmpl_yoursearches_display(
        ln = ln,
        nb_queries_total = nb_queries_total,
        nb_queries_distinct = nb_queries_distinct,
        search_queries = search_queries,
        guest = isGuestUser(uid),
        guesttxt = warning_guest_user(type="searches", ln=ln))

def account_list_searches(uid,
                          ln=CFG_SITE_LANG):
    """
    Display a short summary of the searches the user has performed.
    @param uid: The user id
    @type uid: int
    @return: A short summary of the user searches.
    """

    # load the right language
    _ = gettext_set_language(ln)
    
    query = """ SELECT  COUNT(uq.id_query)
                FROM    user_query uq
                WHERE   uq.id_user=%s"""
    params = (uid,)
    result = run_sql(query, params, 1)
    if result:
        nb_queries_total = result[0][0]
    else:
        nb_queries_total = 0

    out = _("You have made %(x_nb)s queries. A %(x_url_open)sdetailed list%(x_url_close)s is available with a possibility to (a) view search results and (b) subscribe to an automatic email alerting service for these queries.") % \
        {'x_nb': nb_queries_total,
         'x_url_open': '<a href="%s/yoursearches/display?ln=%s">' % (CFG_SITE_URL, ln),
         'x_url_close': '</a>'}

    return out