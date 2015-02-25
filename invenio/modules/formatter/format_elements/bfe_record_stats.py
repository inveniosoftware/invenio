# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints record statistics
"""
__revision__ = "$Id$"

from invenio.legacy.dbquery import run_sql

def format_element(bfo, display='day_distinct_ip_nb_views'):
    '''
    Prints record statistics

    @param display: the type of statistics displayed. Can be 'total_nb_view', 'day_nb_views', 'total_distinct_ip_nb_views', 'day_distincts_ip_nb_views', 'total_distinct_ip_per_day_nb_views'
    '''

    if display == 'total_nb_views':
        return run_sql("""SELECT COUNT(client_host) FROM rnkPAGEVIEWS
                           WHERE id_bibrec=%s""",
                       (bfo.recID,))[0][0]
    elif display == 'day_nb_views':
        return run_sql("""SELECT COUNT(client_host) FROM rnkPAGEVIEWS
                           WHERE id_bibrec=%s AND DATE(view_time)=CURDATE()""",
                       (bfo.recID,))[0][0]
    elif display == 'total_distinct_ip_nb_views':
        return run_sql("""SELECT COUNT(DISTINCT client_host) FROM rnkPAGEVIEWS
                           WHERE id_bibrec=%s""",
                       (bfo.recID,))[0][0]
    elif display == 'day_distinct_ip_nb_views':
        return run_sql("""SELECT COUNT(DISTINCT client_host) FROM rnkPAGEVIEWS
                           WHERE id_bibrec=%s AND DATE(view_time)=CURDATE()""",
                       (bfo.recID,))[0][0]
    elif display == 'total_distinct_ip_per_day_nb_views':
        # Count the number of distinct IP addresses for every day Then
        # sum up. Similar to total_distinct_users_nb_views but assume
        # that several different users can be behind a single IP
        # (which could change every day)
        res = run_sql("""SELECT COUNT(DISTINCT client_host)
                           FROM rnkPAGEVIEWS
                          WHERE id_bibrec=%s GROUP BY DATE(view_time)""",
                      (bfo.recID,))
        return sum([row[0] for row in res])

