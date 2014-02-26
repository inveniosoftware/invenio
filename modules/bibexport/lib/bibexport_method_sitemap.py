# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011, 2014 CERN.
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
import gzip
import time

from invenio.bibdocfile import BibRecDocs
from invenio.search_engine import get_collection_reclist, get_all_restricted_recids
from invenio.dbquery import run_sql
from invenio.config import CFG_SITE_URL, CFG_WEBDIR, CFG_ETCDIR, \
    CFG_SITE_RECORD, CFG_SITE_LANGS, CFG_TMPSHAREDDIR
from invenio.intbitset import intbitset
from invenio.websearch_webcoll import Collection
from invenio.bibtask import write_message, task_update_progress, task_sleep_now_if_required
from invenio.textutils import encode_for_xml
from invenio.urlutils import get_canonical_and_alternates_urls


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

_CFG_FORCE_RECRAWLING_TIMESTAMP_PATH = os.path.join(CFG_TMPSHAREDDIR, "bibexport_sitemap_force_recrawling_timestamp.txt")

def get_minimum_timestamp():
    """
    Return the minimum timestamp to be used when exporting.
    """
    if os.path.exists(_CFG_FORCE_RECRAWLING_TIMESTAMP_PATH):
        return datetime.fromtimestamp(os.path.getmtime(_CFG_FORCE_RECRAWLING_TIMESTAMP_PATH))
    else:
        return datetime(1970, 1, 1)

def get_all_public_records(collections):
    """ Get all records which exist (i.e. not suppressed ones) and are in
    accessible collection.
    returns list of (recid, last_modification) tuples
    """
    all_restricted_recids = get_all_restricted_recids()
    recids = intbitset()
    minimum_timestamp = get_minimum_timestamp()
    for collection in collections:
        recids += get_collection_reclist(collection)
    recids = recids.difference(all_restricted_recids)
    query = 'SELECT id, modification_date FROM bibrec'
    res = run_sql(query)
    return [(recid, max(lastmod, minimum_timestamp)) for (recid, lastmod) in res if recid in recids]

def get_all_public_collections(base_collections):
    """  Return a list of (collection.name, last_modification) tuples for all
    collections and subcollections of base_collections
    """
    minimum_timestamp = get_minimum_timestamp()
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
        return max(minimum_timestamp, last_mod)

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

def filter_fulltexts(recids):
    """ returns list of records having a fulltext of type fulltext_type.
    If fulltext_type is empty, return all records having a fulltext"""
    recids = dict(recids)
    minimum_timestamp = get_minimum_timestamp()
    query = """SELECT id_bibrec, max(modification_date)
                FROM bibrec_bibdoc
                LEFT JOIN bibdoc ON bibrec_bibdoc.id_bibdoc=bibdoc.id
                GROUP BY id_bibrec"""
    res = run_sql(query)
    return [(recid, max(lastmod, minimum_timestamp)) for (recid, lastmod) in res if recid in recids and BibRecDocs(recid).list_latest_files(list_hidden=False)]


def filter_comments(recids):
    """ Retrieve recids having a comment. return (recid, last_review_date)"""
    minimum_timestamp = get_minimum_timestamp()
    recids = dict(recids)
    query = """SELECT id_bibrec, max(date_creation)
               FROM cmtRECORDCOMMENT
               WHERE star_score=0
               GROUP BY id_bibrec"""
    res = run_sql(query)
    return [(recid, max(minimum_timestamp, lastmod)) for (recid, lastmod) in res if recid in recids]


def filter_reviews(recids):
    """ Retrieve recids having a review. return (recid, last_review_date)"""
    minimum_timestamp = get_minimum_timestamp()
    recids = dict(recids)
    query = """SELECT id_bibrec, max(date_creation)
               FROM cmtRECORDCOMMENT
               WHERE star_score>0
               GROUP BY id_bibrec"""
    res = run_sql(query)
    return [(recid, max(lastmod, minimum_timestamp)) for (recid, lastmod) in res if recid in recids]


SITEMAP_HEADER = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xhtml="http://www.w3.org/1999/xhtml"
  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
  http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

SITEMAP_FOOTER = '\n</urlset>\n'

class SitemapWriter(object):
    """ Writer for sitemaps"""

    def __init__(self, sitemap_id, base_dir=None, name=None):
        """ Constructor.
        name: path to the sitemap file to be created
        """
        self.header = SITEMAP_HEADER
        self.footer = SITEMAP_FOOTER
        self.sitemap_id = sitemap_id
        if name:
            sitemap_name = name
        else:
            sitemap_name = 'sitemap'
        if base_dir:
            self.name = os.path.join(base_dir, sitemap_name + '-%02d.xml.gz' % sitemap_id)
        else:
            self.name = os.path.join(CFG_WEBDIR, sitemap_name + '-%02d.xml.gz' % sitemap_id)
        self.filedescriptor = gzip.open(self.name + '.part', 'w')
        self.num_urls = 0
        self.file_size = 0
        self.filedescriptor.write(self.header)
        self.file_size += len(self.footer)

    def add_url(self, url, lastmod=datetime(1900, 1, 1), changefreq="", priority="", alternate=False):
        """ create a new url node. Returns the number of url nodes in sitemap"""
        self.num_urls += 1
        canonical_url, alternate_urls = get_canonical_and_alternates_urls(url, drop_ln=not alternate)
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
        if alternate:
            for ln, alternate_url in alternate_urls.iteritems():
                ln = ln.replace('_', '-') ## zh_CN -> zh-CN
                optional += u"""
    <xhtml:link rel="alternate" hreflang="%s" href="%s" />""" % (ln, encode_for_xml(alternate_url, quote=True))
        url_node %= (encode_for_xml(canonical_url), optional)
        self.file_size += len(url_node)
        self.filedescriptor.write(url_node)
        return self.num_urls

    def get_size(self):
        """ File size. Should not be > 10MB """
        return self.file_size + len(self.footer)

    def get_number_of_urls(self):
        """ Number of urls in the sitemap. Should not be > 50'000"""
        return self.num_urls

    def get_name(self):
        """ Returns the filename """
        return self.name

    def get_sitemap_url(self):
        """ Returns the sitemap URL"""
        return self.name.replace(CFG_WEBDIR, CFG_SITE_URL, 1)

    def __del__(self):
        """ Writes the whole sitemap """
        self.filedescriptor.write(self.footer)
        self.filedescriptor.close()
        os.rename(self.name + '.part', self.name)

SITEMAP_INDEX_HEADER = \
'<?xml version="1.0" encoding="UTF-8"?>\n' \
'<sitemapindex\n' \
'  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n' \
'  xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n' \
'  http://www.sitemaps.org/schemas/sitemap/0.9/siteindex.xsd"\n' \
'  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

SITEMAP_INDEX_FOOTER = '\n</sitemapindex>\n'

class SitemapIndexWriter(object):
    """class for writing Sitemap Index files."""

    def __init__(self, name):
        """ Constructor.
        name: path to the sitemap index file to be created
        """
        self.header = SITEMAP_INDEX_HEADER
        self.footer = SITEMAP_INDEX_FOOTER
        self.name = name
        self.filedescriptor = gzip.open(self.name + '.part', 'w')
        self.num_urls = 0
        self.file_size = 0
        self.filedescriptor.write(self.header)
        self.file_size += len(self.footer)

    def add_url(self, url):
        """ create a new url node. Returns the number of url nodes in sitemap"""
        self.num_urls += 1
        url_node = u"""
  <sitemap>
    <loc>%s</loc>%s
  </sitemap>"""
        optional = u"""
    <lastmod>%s</lastmod>""" % time.strftime('%Y-%m-%dT%H:%M:%S' +\
                                            DEFAULT_TIMEZONE)
        url_node %= (url, optional)
        self.file_size += len(url_node)
        self.filedescriptor.write(url_node)
        return self.num_urls

    def __del__(self):
        """ Writes the whole sitemap """
        self.filedescriptor.write(self.footer)
        self.filedescriptor.close()
        os.rename(self.name + '.part', self.name)

def generate_sitemaps(sitemap_index_writer, collection_names, export_fulltext=True):
    """
    Generate sitemaps themselves. Return list of generated sitemaps files
    """
    sitemap_id = 1
    writer = SitemapWriter(sitemap_id)
    sitemap_index_writer.add_url(writer.get_sitemap_url())
    nb_urls = 0
    for lang in CFG_SITE_LANGS:
        writer.add_url(CFG_SITE_URL + '/?ln=%s' % lang,
                       lastmod=datetime.today(),
                       changefreq=DEFAULT_CHANGEFREQ_HOME,
                       priority=DEFAULT_PRIORITY_HOME,
                       alternate=True)
        nb_urls += 1
    write_message("... Getting all public records...")
    recids = get_all_public_records(collection_names)
    write_message("... Generating urls for %s records..." % len(recids))
    task_sleep_now_if_required(can_stop_too=True)
    for i, (recid, lastmod) in enumerate(recids):
        if nb_urls % 100 == 0 and (writer.get_size() >= MAX_SIZE or nb_urls >= MAX_RECORDS):
            sitemap_id += 1
            writer = SitemapWriter(sitemap_id)
            sitemap_index_writer.add_url(writer.get_sitemap_url())
        nb_urls = writer.add_url(CFG_SITE_URL + '/%s/%s' % (CFG_SITE_RECORD, recid),
                                lastmod = lastmod,
                                changefreq = DEFAULT_CHANGEFREQ_RECORDS,
                                priority = DEFAULT_PRIORITY_RECORDS)
        if i % 100 == 0:
            task_update_progress("Sitemap for recid %s/%s" % (i + 1, len(recids)))
            task_sleep_now_if_required(can_stop_too=True)
    write_message("... Generating urls for collections...")
    collections = get_all_public_collections(collection_names)
    for i, (collection, lastmod) in enumerate(collections):
        for lang in CFG_SITE_LANGS:
            if nb_urls % 100 == 0 and (writer.get_size() >= MAX_SIZE or nb_urls >= MAX_RECORDS):
                sitemap_id += 1
                writer = SitemapWriter(sitemap_id)
                sitemap_index_writer.add_url(writer.get_sitemap_url())
            nb_urls = writer.add_url('%s/collection/%s?ln=%s' % (CFG_SITE_URL, quote(collection), lang),
                        lastmod = lastmod,
                        changefreq = DEFAULT_CHANGEFREQ_COLLECTIONS,
                        priority = DEFAULT_PRIORITY_COLLECTIONS,
                        alternate=True)
        if i % 100 == 0:
            task_update_progress("Sitemap for collection %s/%s" % (i + 1, len(collections)))
            task_sleep_now_if_required(can_stop_too=True)
    if export_fulltext:
        write_message("... Generating urls for fulltexts...")
        recids = filter_fulltexts(recids)
        for i, (recid, lastmod) in enumerate(recids):
            if nb_urls % 100 == 0 and (writer.get_size() >= MAX_SIZE or nb_urls >= MAX_RECORDS):
                sitemap_id += 1
                writer = SitemapWriter(sitemap_id)
                sitemap_index_writer.add_url(writer.get_sitemap_url())
            nb_urls = writer.add_url(CFG_SITE_URL + '/%s/%s/files' % (CFG_SITE_RECORD, recid),
                                    lastmod = lastmod,
                                    changefreq = DEFAULT_CHANGEFREQ_FULLTEXTS,
                                    priority = DEFAULT_PRIORITY_FULLTEXTS)
            if i % 100 == 0:
                task_update_progress("Sitemap for files page %s/%s" % (i, len(recids)))
                task_sleep_now_if_required(can_stop_too=True)

    write_message("... Generating urls for comments...")
    recids = filter_comments(recids)
    for i, (recid, lastmod) in enumerate(recids):
        if nb_urls % 100 == 0 and (writer.get_size() >= MAX_SIZE or nb_urls >= MAX_RECORDS):
            sitemap_id += 1
            writer = SitemapWriter(sitemap_id)
            sitemap_index_writer.add_url(writer.get_sitemap_url())
        nb_urls = writer.add_url(CFG_SITE_URL + '/%s/%s/comments' % (CFG_SITE_RECORD, recid),
                                 lastmod = lastmod,
                                 changefreq = DEFAULT_CHANGEFREQ_COMMENTS,
                                 priority = DEFAULT_PRIORITY_COMMENTS)
        if i % 100 == 0:
            task_update_progress("Sitemap for comments page %s/%s" % (i, len(recids)))
            task_sleep_now_if_required(can_stop_too=True)
    write_message("... Generating urls for reviews")
    recids = filter_reviews(recids)
    for i, (recid, lastmod) in enumerate(recids):
        if nb_urls % 100 == 0 and (writer.get_size() >= MAX_SIZE or nb_urls >= MAX_RECORDS):
            sitemap_id += 1
            write_message("")
            writer = SitemapWriter(sitemap_id)
            sitemap_index_writer.add_url(writer.get_sitemap_url())
        nb_urls = writer.add_url(CFG_SITE_URL + '/%s/%s/reviews' % (CFG_SITE_RECORD, recid),
                                 lastmod = lastmod,
                                 changefreq = DEFAULT_CHANGEFREQ_REVIEWS,
                                 priority = DEFAULT_PRIORITY_REVIEWS)
        if i % 100 == 0:
            task_update_progress("Sitemap for reviews page %s/%s" % (i, len(recids)))
            task_sleep_now_if_required(can_stop_too=True)

def generate_sitemaps_index(collection_list, export_fulltext=True):
    """main function. Generates the sitemap index and the sitemaps
    collection_list: list of collection names to add in sitemap
    fulltext_filter: if provided the parser will intergrate only give fulltext
                     types
    """
    write_message("Generating all sitemaps...")
    sitemap_index_writer = SitemapIndexWriter(CFG_WEBDIR + '/sitemap-index.xml.gz')
    generate_sitemaps(sitemap_index_writer, collection_list, export_fulltext=export_fulltext)


def run_export_method(jobname):
    """Main function, reading params and running the task."""
    write_message("bibexport_sitemap: job %s started." % jobname)

    collections = get_config_parameter(jobname=jobname, parameter_name="collection", is_parameter_collection=True)
    export_fulltext = bool(int(get_config_parameter(jobname=jobname, parameter_name="export_fulltext")))

    generate_sitemaps_index(collections, export_fulltext)

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
        all_items = jobconfig.items(section='export_job')

        parameters = []

        for item_name, item_value in all_items:
            if item_name.startswith(parameter_name):
                parameters.append(item_value)

        return parameters
    else:
        parameter = jobconfig.get('export_job', parameter_name)
        return parameter
