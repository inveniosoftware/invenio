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

from invenio.dbquery import run_sql
ELASTICSEARCH_ENABLED = False

try:
    from elasticsearch import Elasticsearch
    from invenio.config import \
        CFG_ELASTICSEARCH_LOGGING, \
        CFG_ELASTICSEARCH_SEARCH_HOST, \
        CFG_ELASTICSEARCH_INDEX_PREFIX

    # if we were able to import all modules and ES logging is enabled, then use
    # elasticsearch instead of normal db queries
    if CFG_ELASTICSEARCH_LOGGING:
        ELASTICSEARCH_ENABLED = True
except ImportError:
    pass
    # elasticsearch not supported


def format_element(bfo, display='day_distinct_ip_nb_views'):
    '''
    Prints record statistics

    @param display: the type of statistics displayed. Can be 'total_nb_view', 'day_nb_views', 'total_distinct_ip_nb_views', 'day_distincts_ip_nb_views', 'total_distinct_ip_per_day_nb_views'
    '''
    if ELASTICSEARCH_ENABLED:
        page_views = 0
        ES_INDEX = CFG_ELASTICSEARCH_INDEX_PREFIX + "*"
        recID = bfo.recID
        query = ""

        es = Elasticsearch(CFG_ELASTICSEARCH_SEARCH_HOST)
        if display == 'total_nb_views':
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "id_bibrec": recID
                                }
                            },
                            {
                                "match": {
                                    "_type": "events.pageviews"
                                }
                            }
                        ]
                    }
                }
            }
            results = es.count(index=ES_INDEX, body=query)
            if results:
                page_views = results.get('count', 0)
        elif display == 'day_nb_views':
            query = {
                "query": {
                    "filtered": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "id_bibrec": recID
                                        }
                                    },
                                    {
                                        "match": {
                                            "_type": "events.pageviews"
                                        }
                                    }
                                ]
                            }
                        },
                        "filter": {
                            "range": {
                                "@timestamp": {
                                    "gt": "now-1d"
                                }
                            }
                        }
                    }
                }
            }
            results = es.count(index=ES_INDEX, body=query)
            if results:
                page_views = results.get('count', 0)
        elif display == 'total_distinct_ip_nb_views':
            search_type = "count"
            # TODO this search query with aggregation is slow, maybe there is a way to make it faster ?
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "id_bibrec": recID
                                }
                            },
                            {
                                "match": {
                                    "_type": "events.pageviews"
                                }
                            }
                        ]
                    }
                },
                "aggregations": {
                    "distinct_ips": {
                        "cardinality": {
                            "field": "client_host"
                        }
                    }
                }
            }
            results = es.search(index=ES_INDEX, body=query, search_type=search_type)
            if results:
                page_views = results.get('aggregations', {}).get('distinct_ips', {}).get('value', 0)
        elif display == 'day_distinct_ip_nb_views':
            search_type = "count"
            # TODO aggregation is slow, maybe there is a way to make a faster query
            query = {
                "query": {
                    "filtered": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "id_bibrec": recID
                                        }
                                    },
                                    {
                                        "match": {
                                            "_type": "events.pageviews"
                                        }
                                    }
                                ]
                            }
                        },
                        "filter": {
                            "range": {
                                "@timestamp": {
                                    "gt": "now-1d"
                                }
                            }
                        }
                    }
                },
                "aggregations": {
                    "distinct_ips": {
                        "cardinality": {
                            "field": "client_host"
                        }
                    }
                }
            }
            results = es.search(index=ES_INDEX, body=query, search_type=search_type)
            if results:
                page_views = results.get('aggregations', {}).get('distinct_ips', {}).get('value', 0)
        elif display == 'total_distinct_ip_per_day_nb_views':
            search_type = "count"
            # TODO aggregation is slow, maybe there is a way to make a faster query
            query = {
                "query": {
                    "filtered": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "id_bibrec": recID
                                        }
                                    },
                                    {
                                        "match": {
                                            "_type": "events.pageviews"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                },
                "aggregations": {
                    "daily_stats": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "interval": "day"
                        },
                        "aggregations": {
                            "distinct_ips": {
                                "cardinality": {
                                    "field": "client_host"
                                }
                            }
                        }
                    }
                }
            }
            results = es.search(index=ES_INDEX, body=query, search_type=search_type)
            if results:
                buckets = results.get("aggregations", {}).get("daily_stats", {}).get("buckets", {})
                page_views = sum([int(bucket.get("distinct_ips", {}).get('value', '0')) for bucket in buckets])
        return page_views
    else:

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

