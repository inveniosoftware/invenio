# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.utils.xmlDict import XmlDictConfig, ElementTree
import urllib2
from werkzeug.contrib.cache import RedisCache
from invenio.ext.cache import cache


class SherpaRomeoSearch(object):
    """
    SHERPA/RoMEO API wrapper class to search Publishers and Journals
    Queries the SHERPA/RoMEO API and parses the xml returned.

    The search functions return the associated names.
    (search_issn returns journal)

    It uses Redis to cache all xml from queries and create a small Journal
    and Publisher db.

    For more detailed results the SherpaRomeoSearch.parser API must be used
    that gives access to conditions, issn and single items on exact matches


    @seealso: http://www.sherpa.ac.uk/romeo/api.html
    """

    def __init__(self):
        self.parser = SherpaRomeoXMLParser()
        self.error = False
        self.error_message = ""

    def search_publisher(self, query):
        """
        Search for Publishers
        query: the query to be made

        returns a list with publisher names
        """

        # Search first for exact matches in cache
        cached_publisher = cache.get("publisher:" + query.lower())
        if cached_publisher is not None:
            self.parser.set_single_item(publisher=cached_publisher,)
            return cached_publisher['name']

        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?pub=" + cleanquery
        self.parser.parse_url(url)
        self.error = self.parser.error
        self.error_message = self.parser.error_message
        if not self.error:
            return self.parser.get_publishers(attribute='name')

    def search_journal(self, query, query_type='contains'):
        """
        Search for Journals
        query: the query to be made
        query_type: it must be 'contains'(default), 'exact' or 'start'

        returns a list with the specific journal titles or empty list
        """

        if query_type is 'exact':
            # Search first for exact matches in cache
            cached_journal = cache.get("journal:" + query.lower())
            if cached_journal is not None:
                self.parser.set_single_item(journal=cached_journal)
                return cached_journal['jtitle']

        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?jtitle=" + cleanquery + "&qtype=" + query_type
        self.parser.parse_url(url)
        self.error = self.parser.error
        self.error_message = self.parser.error_message
        if not self.error:
            return self.parser.get_journals(attribute='jtitle')

    def search_issn(self, issn):
        """ Search for Journals based on ISSN """

        url = "http://www.sherpa.ac.uk/romeo/api29.php?issn=" + issn
        self.parser.parse_url(url)
        self.error = self.parser.error
        self.error_message = self.parser.error_message
        if not self.error:
            return self.parser.get_journals()

    def get_num_hits(self):
        return int(self.parser.xml['header']['numhits'])


class SherpaRomeoXMLParser(object):

    def __init__(self):
        self.parsed = False
        self.single_item = False
        self.error = False
        self.error_message = ""

    def parse_url(self, url):
        self.url = url
        #example
        #url = 'http://www.sherpa.ac.uk/romeo/api29.php?jtitle=Annals%20of%20Physics'

        found_journal = url.find("jtitle=")
        found_publisher = url.find("pub=")
        if found_journal != -1:
            self.search_type = "journal_search"
            self.query = url[found_journal + 7:(len(url) - 15)]
        elif found_publisher != -1:
            self.search_type = "publisher_search"
            found_publisher = url.find("pub=")
            self.query = url[found_publisher + 4:len(url)]
        else:
            self.search_type = "issn_search"
            found_publisher = url.find("issn=")
            self.query = url[found_publisher + 4:len(url)]

        cached_xml = cache.get(self.search_type + ":" + self.query.lower())
        if cached_xml is None:
            try:
                self.data = urllib2.urlopen(url).read()
            except urllib2.HTTPError:
                self.error = True
                return
            try:
                root = ElementTree.XML(self.data)
            except SyntaxError:
                self.error = True
                return
            self.xml = XmlDictConfig(root)
            outcome = self.xml['header']['outcome']
            if outcome != 'failed' and outcome != 'notFound':
                cache.set(self.search_type + ":" + self.query.lower(), self.xml,
                        999999999999)
        else:
            self.xml = cached_xml
            #self.data = cached_xml
            #root = ElementTree.XML(self.data)
            #self.xml = XmlDictConfig(root)

        if self.xml['header']['outcome'] == 'failed':
            self.error = True
            self.error_message = self.xml['header']['message']
        self.parsed = True
        self._cache_parsed_xml()

    def _cache_parsed_xml(self):
        """ Caches every Journal and Publisher found in the xml """
        if not self.parsed:
            return

        outcome = self.xml['header']['outcome'] is 'notFound'
        if outcome is 'notFound' or outcome is 'failed':
            return

        if self.xml['header']['outcome'] == 'singleJournal' \
            or self.xml['header']['outcome'] == 'uniqueZetoc':
            journal = self.xml['journals']['journal']
            cache.set("journal:" + journal['jtitle'].lower(), journal, 999999999999)

            if self.xml['header']['outcome'] != 'uniqueZetoc':
                # if the publisher has been indexed by RoMEO
                publisher = self.xml['publishers']['publisher']

                # Associate a Journal with a Publisher key in cache
                cache.set("journal-publisher:" + journal['jtitle'].lower(),
                                  "publisher:" + publisher['name'].lower(), 999999999999)
        elif self.xml['journals'] is not None:
            for journal in self.xml['journals']['journal']:
                cache.set("journal:" + journal['jtitle'].lower(), journal, 999999999999)

        if self.xml['header']['numhits'] == '1' \
            and self.xml['header']['outcome'] != 'uniqueZetoc':
            publisher = self.xml['publishers']['publisher']
            cache.set("publisher:" + publisher['name'].lower(), publisher, 999999999999)
        elif self.xml['publishers'] is not None:
            for publisher in self.xml['publishers']['publisher']:
                cache.set("publisher:" + publisher['name'].lower(), publisher,
                        None)

    def set_single_item(self, journal=None, publisher=None):
        """
        Used to initialize the parser with items retrieved from cache

        Note: if both a journal and a publisher are defined
              the publisher is associated with the journal
        """
        self.xml = dict()
        self.xml['header'] = dict()
        self.xml['header']['outcome'] = ''
        if journal is not None:
            self.xml['journals'] = dict()
            self.xml['journals']['journal'] = journal
            self.xml['header']['numhits'] = '1'
            self.parsed = True
            self.single_item = True
            if publisher is not None:
                # Associate a Journal with a Publisher key in cache
                self.xml['header']['outcome'] = 'singleJournal'
                cache.set("journal-publisher:" + journal['jtitle'].lower(),
                                  "publisher:" + publisher['name'].lower(), 999999999999)
        elif publisher is not None:
            self.xml['header']['outcome'] = 'publisherFound'
            self.xml['header']['numhits'] = '1'
            self.xml['publishers'] = dict()
            self.xml['publishers']['publisher'] = publisher
            self.single_item = True
            self.parsed = True

    def get_single_item(self):
        """Returns a single item retrieved from cache."""
        if self.single_item:
            return self.xml
        else:
            return None

    def get_journals(self, attribute=None):
        """Returns a list of journals.

        If an attribute is defined, returns only this attribute from
        every journal.
        """
        if self.xml['header']['outcome'] == 'notFound' \
           or self.xml['header']['outcome'] == 'failed':
            return []

        if self.xml['header']['outcome'] == 'singleJournal' \
         or self.xml['header']['outcome'] == 'uniqueZetoc' \
         or (self.single_item and self.xml['journals']['journal'] is not None):
            if attribute is None:
                return [self.xml['journals']['journal']]
            elif self.xml['journals']['journal'][attribute] is not None:
                return [self.xml['journals']['journal'][attribute]]
            else:
                return []

        journals = list()
        for j in self.xml['journals']['journal']:
            if attribute is None:
                journals.append(j)
            else:
                journals.append(j[attribute])

        return journals

    def get_publishers(self, attribute=None, journal=None,):
        """ Returns a list of the publishers if a publisher search was made or
        an empty list.

        If a journal is defined, it returns the associated publisher
        for this Journal or None. A journal definition makes the functions
        to query again if the publisher isn't found in the xml or cache.
        Note: If you define a journal, you must have searched for it first.

        If an attribute is defined, returns only this attribute from
        every publisher
        """

        if self.xml['header']['outcome'] == 'notFound' \
           or self.xml['header']['outcome'] == 'failed':
            return None

        if self.xml['header']['outcome'] == 'singleJournal':
            return self.xml['publishers']['publisher']

        if self.xml['header']['outcome'] == 'uniqueZetoc':
            # the Publisher has not yet been indexed by RoMEO
            return None

        if journal is not None:
            #  search the cache for matches
            publisher_key = cache.get("journal-publisher:" + journal.lower())
            if publisher_key is not None:
                return cache.get(publisher_key)

            # Query again sherpa romeo db to get the publisher
            s = SherpaRomeoSearch()
            issn = self.get_journals(attribute='issn')[0]
            if issn is not None:
                s.search_issn(issn)
                return s.parser.get_publishers()
            else:
                return None

        publishers = list()
        if self.xml['header']['outcome'] == 'publisherFound':
            if self.xml['header']['numhits'] == '1':
                p = self.xml['publishers']['publisher']
                if attribute is None:
                    publishers.append(p)
                else:
                    if p[attribute] is None:
                        return []
                    publishers.append(p[attribute])
            else:
                for p in self.xml['publishers']['publisher']:
                    if attribute is None:
                        publishers.append(p)
                    else:
                        publishers.append(p[attribute])
        return publishers

    def get_issn(self):
        """Returns the issn if the search returns a single Journal."""

        if 'issn' in self.xml:
            return self.xml['issn']

        if self.xml['header']['outcome'] == 'notFound' \
           or self.xml['header']['outcome'] == 'failed':
            return None

        if self.xml['header']['outcome'] == 'singleJournal'\
            or self.xml['header']['outcome'] == 'uniqueZetoc':
            return self.xml['journals']['journal']['issn']
        else:
            return None
            issns = dict()
            for j in self.xml['journals']['journal']:
                issns[j['jtitle']] = j['issn']

            return issns

