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

from invenio.config import CFG_SITE_LANG, CFG_SITE_SECURE_URL
from invenio.dbquery import run_sql
from invenio.webaccount import warning_guest_user
from invenio.messages import gettext_set_language
from invenio.webuser import isGuestUser
from urllib import quote, quote_plus, unquote_plus
from invenio.webalert import count_user_alerts_for_given_query

import invenio.template
websearch_templates = invenio.template.load('websearch')

CFG_WEBSEARCH_YOURSEARCHES_MAX_NUMBER_OF_DISPLAYED_SEARCHES = 20

def perform_request_yoursearches_display(uid,
                                         page=1,
                                         step=CFG_WEBSEARCH_YOURSEARCHES_MAX_NUMBER_OF_DISPLAYED_SEARCHES,
                                         p='',
                                         ln=CFG_SITE_LANG):
    """
    Display the user's search history.

    @param uid: the user id
    @type uid: integer

    @param page: 
    @type page: integer

    @param step: 
    @type step: integer

    @param p: 
    @type p: strgin

    @param ln: 
    @type ln: string

    @return: A list of searches queries in formatted html.
    """
    
    # Load the right language
    _ = gettext_set_language(ln)

    search_clause = ""
    if p:
        p_stripped = p.strip()
        p_stripped_args = p.split()
        sql_p_stripped_args = ['\'%%' + quote(p_stripped_arg) + '%%\'' for p_stripped_arg in p_stripped_args]
        for sql_p_stripped_arg in sql_p_stripped_args:
            search_clause += """ AND q.urlargs LIKE %s""" % (sql_p_stripped_arg,)

    # Calculate the number of total and distinct queries
    nb_queries_total = 0
    nb_queries_distinct = 0
    query_nb_queries = """  SELECT  COUNT(uq.id_query),
                                    COUNT(DISTINCT(uq.id_query))
                            FROM    user_query AS uq,
                                    query q
                            WHERE   uq.id_user=%%s
                                AND q.id=uq.id_query
                                %s""" % (search_clause,)
    params_nb_queries = (uid,)
    res_nb_queries = run_sql(query_nb_queries, params_nb_queries)
    nb_queries_total = res_nb_queries[0][0]
    nb_queries_distinct = res_nb_queries[0][1]

    # The real page starts counting from 0, i.e. minus 1 from the human page
    real_page = page - 1
    # The step needs to be a positive integer
    if (step <= 0):
        step = CFG_WEBSEARCH_YOURSEARCHES_MAX_NUMBER_OF_DISPLAYED_SEARCHES
    # The maximum real page is the integer division of the total number of
    # searches and the searches displayed per page
    max_real_page = (nb_queries_distinct / step) - (not (nb_queries_distinct % step) and 1 or 0)
    # Check if the selected real page exceeds the maximum real page and reset
    # if needed
    if (real_page >= max_real_page):
        #if ((nb_queries_distinct % step) != 0):
        #    real_page = max_real_page
        #else:
        #    real_page = max_real_page - 1
        real_page = max_real_page
        page = real_page + 1
    elif (real_page < 0):
        real_page = 0
        page = 1
    # Calculate the start value for the SQL LIMIT constraint
    limit_start = real_page * step
    # Calculate the display of the paging navigation arrows for the template
    paging_navigation = (real_page >= 2,
                         real_page >= 1,
                         real_page <= (max_real_page - 1),
                         (real_page <= (max_real_page - 2)) and (max_real_page + 1))
    

    # Calculate the user search queries
    query = """ SELECT      DISTINCT(q.id),
                            q.urlargs,
                            DATE_FORMAT(MAX(uq.date),'%s')
                FROM        query q,
                            user_query uq
                WHERE       uq.id_user=%%s
                    AND     uq.id_query=q.id
                    %s
                GROUP BY    uq.id_query
                ORDER BY    MAX(uq.date) DESC
                LIMIT       %%s,%%s""" % ('%%Y-%%m-%%d %%H:%%i:%%s', search_clause,)
    params = (uid, limit_start, step)
    result = run_sql(query, params)

    search_queries = []
    if result:
        for search_query in result:
            search_query_id = search_query[0]
            search_query_args = search_query[1]
            search_query_lastrun = search_query[2] or _("unknown")
            search_queries.append({'id' : search_query_id,
                                   'args' : search_query_args,
                                   'lastrun' : search_query_lastrun,
                                   'user_alerts' : count_user_alerts_for_given_query(uid, search_query_id)})

    return websearch_templates.tmpl_yoursearches_display(
        nb_queries_total = nb_queries_total,
        nb_queries_distinct = nb_queries_distinct,
        search_queries = search_queries,
        page=page,
        step=step,
        paging_navigation=paging_navigation,
        p=p,
        guest = isGuestUser(uid),
        guesttxt = warning_guest_user(type="searches", ln=ln),
        ln = ln)

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
         'x_url_open': '<a href="%s/yoursearches/display?ln=%s">' % (CFG_SITE_SECURE_URL, ln),
         'x_url_close': '</a>'}

    return out
