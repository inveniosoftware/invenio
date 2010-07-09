# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibExport plugin implementing 'sitemap' exporting method.

The main function is run_export_method(jobname) defined at the end.
This is what BibExport daemon calls for all the export jobs that use
this exporting method.
"""

from datetime import datetime
from urllib import quote
from ConfigParser import ConfigParser
import os

from invenio.search_engine import get_collection_reclist
from invenio.dbquery import run_sql
from invenio.config import CFG_SITE_URL, CFG_WEBDIR, CFG_ETCDIR
from invenio.intbitset import intbitset
from invenio.websearch_webcoll import Collection
from invenio.messages import language_list_long
from invenio.bibtask import write_message, task_update_progress
       

DEFAULT_TIMEZONE = '+01:00'

DEFAULT_PRIORITY_HOME = 1
DEFAULT_CHANGEFREQ_HOME = 'hourly'

DEFAULT_PRIORITY_RECORDS = 0.8
DEFAULT_CHANGEFREQ_RECORDS = 'weekly'

DEFAULT_PRIORITY_COMMENTS = 0.4
DEFAULT_CHANGEFREQ_COMMENTS = 'weekly'

DEFAULT_PRIORITY_REVIEWS = 0.6
DEFAULT_CHANGEFREQ_REVIEWS = 'weekly'

DEFAULT_PRIORITY_FULLTEXTS = 0.9
DEFAULT_CHANGEFREQ_FULLTEXTS = 'weekly'

DEFAULT_PRIORITY_COLLECTIONS = 0.3
DEFAULT_CHANGEFREQ_COLLECTIONS = 'hourly'

MAX_RECORDS = 50000
MAX_SIZE = 10000000

def get_all_public_records(collections):
    """ Get all records which exist (i.e. not suppressed ones) and are in
    accessible collection.
    returns list of (recid, last_modification) tuples
    """
    recids = intbitset()
    for collection in collections:
        recids += get_collection_reclist(collection)
    query = 'SELECT id, modification_date FROM bibrec'
    res = run_sql(query)
    return [(recid, lastmod) for (recid, lastmod) in res if recid in recids]

def get_all_public_collections(base_collections):
    """  Return a list of (collection.name, last_modification) tuples for all
    collections and subcollections of base_collections
    """
    def get_collection_last_modification(collection):
        """ last modification = modification date fo latest added record """
        last_mod = None
        query_last_mod = "SELECT modification_date FROM bibrec WHERE id=%s"
        try:
            latest_recid = collection.reclist.tolist()[-1]
        except IndexError:
            # this collection is empty
            return last_mod
        res = run_sql(query_last_mod, (latest_recid,))

        if res and res[0][0]:
            last_mod = res[0][0]
        return last_mod

    output = []
    for coll_name in base_collections:
        mother_collection = Collection(coll_name)
        if not mother_collection.restricted_p():
            last_mod = get_collection_last_modification(mother_collection)
            output.append((coll_name, last_mod))
            for descendant in mother_collection.get_descendants(type='r'):
                if not descendant.restricted_p():
                    last_mod = get_collection_last_modification(descendant)
                    output.append((descendant.name, last_mod))
            for descendant in mother_collection.get_descendants(type='v'):
                if not descendant.restricted_p():
                    last_mod = get_collection_last_modification(descendant)
                    output.append((descendant.name, last_mod))
    return output

def filter_fulltexts(recids, fulltext_type=None):
    """ returns list of records having a fulltext of type x"""
    recids = dict(recids)
    if fulltext_type:
        query = """SELECT id_bibrec, max(modification_date)
                   FROM bibrec_bibdoc
                   LEFT JOIN bibdoc ON bibrec_bibdoc.id_bibdoc=bibdoc.id
                   WHERE type=%s
                   GROUP BY id_bibrec"""
        res = run_sql(query, (fulltext_type,))
    else:
        query = """SELECT id_bibrec, max(modification_date)
                   FROM bibrec_bibdoc
                   LEFT JOIN bibdoc ON bibrec_bibdoc.id_bibdoc=bibdoc.id
                   GROUP BY id_bibrec"""
        res = run_sql(query)
    return [(recid, lastmod) for (recid, lastmod) in res if recid in recids]


def filter_comments(recids):
    """ Retrieve recids having a comment. return (recid, last_review_date)"""
    recids = dict(recids)
    query = """SELECT id_bibrec, max(date_creation)
               FROM cmtRECORDCOMMENT
               WHERE star_score=0
               GROUP BY id_bibrec"""
    res = run_sql(query)
    return [(recid, lastmod) for (recid, lastmod) in res if recid in recids]


def filter_reviews(recids):
    """ Retrieve recids having a review. return (recid, last_review_date)"""
    recids = dict(recids)
    query = """SELECT id_bibrec, max(date_creation)
               FROM cmtRECORDCOMMENT
               WHERE star_score>0
               GROUP BY id_bibrec"""
    res = run_sql(query)
    return [(recid, lastmod) for (recid, lastmod) in res if recid in recids]



SITEMAP_HEADER = \
'<?xml version="1.0" encoding="UTF-8"?>\n' \
'<urlset\n' \
'  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n' \
'  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n' \
'  http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"\n' \
'  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

SITEMAP_FOOTER = '\n</urlset>\n'

class SitemapWriter(object):
    """ Writer for sitemaps"""

    def __init__(self, name):
        """ Constructor.
        name: path to the sitemap file to be created
        """
        self.header = SITEMAP_HEADER
        self.footer = SITEMAP_FOOTER
        self.name = name
        self.filedescriptor = open(self.name, 'w')
        self.num_urls = 0
        self.file_size = 0
        self.buffer = []
        self.filedescriptor.write(self.header)
        self.file_size += len(self.footer)

    def add_url(self, url, lastmod=datetime(1900, 1, 1), changefreq="",
            priority=""):
        """ create a new url node. Returns the number of url nodes in sitemap"""
        self.num_urls += 1
        url_node = u"""
  <url>
    <loc>%s</loc>%s
  </url>"""
        optional = ''
        if lastmod:
            optional += u"""
    <lastmod>%s</lastmod>""" % lastmod.strftime('%Y-%m-%dT%H:%M:%S' + \
                                                DEFAULT_TIMEZONE)
        if changefreq:
            optional += u"""
    <changefreq>%s</changefreq>""" % changefreq
        if priority:
            optional += u"""
    <priority>%s</priority>""" % priority
        url_node %= (url, optional)
        self.file_size += len(url_node)
        self.buffer.append(url_node)
        return self.num_urls

    def get_size(self):
        """ File size. Should ot be > 10MB """
        return self.file_size + len(self.footer)

    def get_number_of_urls(self):
        """ Number of urls in the sitemap. Should not be > 50'000"""
        return self.num_urls

    def get_name(self):
        """ Returns the filename """
        return self.name

    def close(self):
        """ Writes the whole sitemap """
        self.filedescriptor.write(''.join(self.buffer) + self.footer)
        self.filedescriptor.close()

SITEMAP_INDEX_HEADER = \
'<?xml version="1.0" encoding="UTF-8"?>\n' \
'<sitemapindex\n' \
'  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n' \
'  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n' \
'  http://www.sitemaps.org/schemas/sitemap/0.9/siteindex.xsd"\n' \
'  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

SITEMAP_INDEX_FOOTER = '\n</sitemapindex>\n'

class SitemapIndexWriter(SitemapWriter):
    """class for writing Sitemap Index files."""

    def __init__(self, name):
        """ Constructor.
        name: path to the sitemap index file to be created
        """
        self.header = SITEMAP_INDEX_HEADER
        self.footer = SITEMAP_INDEX_FOOTER
        self.name = name
        self.filedescriptor = open(self.name, 'w')
        self.num_urls = 0
        self.file_size = 0
        self.buffer = []
        self.filedescriptor.write(self.header)
        self.file_size += len(self.footer)

    def add_url(self, url, lastmod=datetime(1900, 1, 1)):
        """ create a new url node. Returns the number of url nodes in sitemap"""
        self.num_urls += 1
        url_node = u"""
  <sitemap>
    <loc>%s</loc>%s
  </sitemap>"""
        optional = ''
        if lastmod:
            optional += u"""
    <lastmod>%s</lastmod>""" % lastmod.strftime('%Y-%m-%dT%H:%M:%S' +\
                                                DEFAULT_TIMEZONE)
        url_node %= (url, optional)
        self.file_size += len(url_node)
        self.buffer.append(url_node)
        return self.num_urls



def generate_sitemaps(collection_names, fulltext_filter=''):
    """
    Generate sitemaps themselves. Return list of generated sitemaps files
    """
    sitemap_id = 1
    writer = SitemapWriter(CFG_WEBDIR + '/sitemap-%s.xml' % sitemap_id)
    sitemaps = [writer.get_name()]
    nb_urls = 0
    for [lang, lang_name] in language_list_long():
        writer.add_url(CFG_SITE_URL + '/?ln=%s' % lang,
                       lastmod=datetime.today(),
                       changefreq=DEFAULT_CHANGEFREQ_HOME,
                       priority=DEFAULT_PRIORITY_HOME)
        nb_urls += 1

    recids = get_all_public_records(collection_names)
    task_update_progress("Generating urls for %s records" % len(recids))
    #task_sleep_now_if_required(can_stop_too=True)
    for (recid, lastmod) in recids:
        if nb_urls <= MAX_RECORDS and nb_urls % 100 == 0:
            #print nb_urls
            #print writer.get_size()
            if writer.get_size() > MAX_SIZE or nb_urls == MAX_RECORDS:
                writer.close()
                sitemap_id += 1
                writer = SitemapWriter(CFG_WEBDIR + '/sitemap-%s.xml' % sitemap_id)
                sitemaps.append(writer.get_name())
        nb_urls = writer.add_url(CFG_SITE_URL + '/record/%s' % recid,
                                 lastmod = lastmod,
                                 changefreq = DEFAULT_CHANGEFREQ_RECORDS,
                                 priority = DEFAULT_PRIORITY_RECORDS)
        #task_sleep_now_if_required(can_stop_too=False)
    task_update_progress("Generating urls for collections")
    for (collection, lastmod) in get_all_public_collections(collection_names):
        for [lang, lang_name] in language_list_long():
            if nb_urls <= MAX_RECORDS and nb_urls % 100 == 0:
                #print nb_urls
                #print writer.get_size()
                if writer.get_size() > MAX_SIZE or nb_urls == MAX_RECORDS:
                    writer.close()
                    sitemap_id += 1
                    writer = SitemapWriter('%s/sitemap-%s.xml' % (CFG_WEBDIR,
                                                                  sitemap_id))
                    sitemaps.append(writer.get_name())
            nb_urls = writer.add_url(
                       '%s/collection/%s?ln=%s' % (CFG_SITE_URL, quote(collection), lang),
                       lastmod = lastmod,
                       changefreq = DEFAULT_CHANGEFREQ_COLLECTIONS,
                       priority = DEFAULT_PRIORITY_COLLECTIONS)
            #task_sleep_now_if_required(can_stop_too=False)
    task_update_progress("Generating urls for fulltexts")
    for  (recid, lastmod) in filter_fulltexts(recids, fulltext_filter):
        if nb_urls <= MAX_RECORDS and nb_urls % 100 == 0:
            #print nb_urls
            #print writer.get_size()
            if writer.get_size() > MAX_SIZE or nb_urls == MAX_RECORDS:
                writer.close()
                sitemap_id += 1
                writer = SitemapWriter(CFG_WEBDIR + '/sitemap-%s.xml' % sitemap_id)
                sitemaps.append(writer.get_name())
        nb_urls = writer.add_url(CFG_SITE_URL + '/record/%s/files' % recid,
                                 lastmod = lastmod,
                                 changefreq = DEFAULT_CHANGEFREQ_FULLTEXTS,
                                 priority = DEFAULT_PRIORITY_FULLTEXTS)
        #task_sleep_now_if_required(can_stop_too=False)

    task_update_progress("Generating urls for comments")
    for  (recid, lastmod) in filter_comments(recids):
        if nb_urls <= MAX_RECORDS and nb_urls % 100 == 0:
            #print nb_urls
            #print writer.get_size()
            if writer.get_size() > MAX_SIZE or nb_urls == MAX_RECORDS:
                writer.close()
                sitemap_id += 1
                writer = SitemapWriter(CFG_WEBDIR + '/sitemap-%s.xml' % sitemap_id)
                sitemaps.append(writer.get_name())
        nb_urls = writer.add_url(CFG_SITE_URL + '/record/%s/comments' % recid,
                                 lastmod = lastmod,
                                 changefreq = DEFAULT_CHANGEFREQ_COMMENTS,
                                 priority = DEFAULT_PRIORITY_COMMENTS)
        #task_sleep_now_if_required(can_stop_too=False)
    task_update_progress("Generating urls for reviews")
    for  (recid, lastmod) in filter_reviews(recids):
        if nb_urls <= MAX_RECORDS and nb_urls % 100 == 0:
            #print nb_urls
            #print writer.get_size()
            if writer.get_size() > MAX_SIZE or nb_urls == MAX_RECORDS:
                writer.close()
                sitemap_id += 1
                writer = SitemapWriter(CFG_WEBDIR + '/sitemap-%s.xml' % sitemap_id)
                sitemaps.append(writer.get_name())
        nb_urls = writer.add_url(CFG_SITE_URL + '/record/%s/reviews' % recid,
                                 lastmod = lastmod,
                                 changefreq = DEFAULT_CHANGEFREQ_REVIEWS,
                                 priority = DEFAULT_PRIORITY_REVIEWS)
        #task_sleep_now_if_required(can_stop_too=False)
    try:
        writer.close()
    except:
        pass
    return sitemaps

def generate_sitemaps_index(collection_list, fulltext_filter=None):
    """main function. Generates the sitemap index and the sitemaps
    collection_list: list of collection names to add in sitemap
    fulltext_filter: if provided the parser will intergrate only give fulltext
                     types
    """
    sitemaps = generate_sitemaps(collection_list, fulltext_filter)
    writer = SitemapIndexWriter(CFG_WEBDIR + '/sitemap-index.xml')

    task_update_progress("Generating sitemap index for %s sitemap files" % \
                        len(sitemaps))
    #task_sleep_now_if_required(can_stop_too=False)
    for sitemap in sitemaps:
        writer.add_url(CFG_SITE_URL + '/%s' % sitemap.split('/')[-1],
                       lastmod=datetime.today())
    writer.close()

def run_export_method(jobname):
    """Main function, reading params and running the task."""
    write_message("bibexport_sitemap: job %s started." % jobname)

    collections = get_config_parameter(jobname = "sitemap", parameter_name = "collection", is_parameter_collection = True)
    fulltext_type = get_config_parameter(jobname = "sitemap", parameter_name = "fulltext_status")

    generate_sitemaps_index(collections, fulltext_type)

    write_message("bibexport_sitemap: job %s finished." % jobname)

def get_config_parameter(jobname, parameter_name, is_parameter_collection = False):
    """Detect export method of JOBNAME.  Basically, parse JOBNAME.cfg
       and return export_method.  Return None if problem found."""
    jobconfig = ConfigParser()
    jobconffile = CFG_ETCDIR + os.sep + 'bibexport' + os.sep + jobname + '.cfg'

    if not os.path.exists(jobconffile):
        write_message("ERROR: cannot find config file %s." % jobconffile)
        return None

    jobconfig.read(jobconffile)

    if is_parameter_collection:
        all_items = jobconfig.items(section = 'export_job')

        parameters = []

        for item_name, item_value in all_items:
            if item_name.startswith(parameter_name):
                parameters.append(item_value)

        return parameters
    else:
        parameter = jobconfig.get('export_job', parameter_name)
        return parameter
