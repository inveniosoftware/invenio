# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from invenio.xmlDict import XmlDictConfig, ElementTree
import urllib2
from werkzeug.contrib.cache import RedisCache


class SherpaRomeoSearch(object):

    def search_publisher(self, query):
        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?pub=" + cleanquery
        self.parser = SherpaRomeoXMLParser()
        self.parser.parse_url(url)
        return self.parser.get_publishers()

    def search_journal(self, query):
        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?jtitle=" + cleanquery + "&qtype=contains"
        self.parser = SherpaRomeoXMLParser()
        self.parser.parse_url(url)
        return self.parser.get_journals()

    def search_journal_exact(self, query):
        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?jtitle=" + cleanquery + "&qtype=exact"
        self.parser = SherpaRomeoXMLParser()
        self.parser.parse_url(url)
        return self.parser.get_journals()


class SherpaRomeoXMLParser(object):

    def __init__(self):
        self.parsed = False


    def parse_url(self, url):
        print url
        self.url = url
        #example
        #url = 'http://www.sherpa.ac.uk/romeo/api29.php?jtitle=Annals%20of%20Physics'

        found_title = url.find("jtitle=")
        if found_title != -1:
            self.type = "title"
            self.query = url[found_title + 7:(len(url) - 15)]
        else:
            self.type = "pub"
            found_publisher = url.find("pub=")
            if found_publisher != -1:
                self.query = url[found_title + 4:len(url)]

        cache = RedisCache("localhost", default_timeout=9000)
        cached_xml = cache.get(self.type + ":" + self.query)
        if not cached_xml:
            print self.type + ":" + self.query + " is not cached!"
            self.data = urllib2.urlopen(url).read()
            root = ElementTree.XML(self.data)
            self.xml = XmlDictConfig(root)
            cache.set(self.type + ":" + self.query, self.data)
        else:
            self.data = cached_xml
            root = ElementTree.XML(self.data)
            self.xml = XmlDictConfig(root)

        self.parsed = True

    def get_journals(self):
        titles = list()
        if self.xml['header']['outcome'] == 'notFound' \
           or self.xml['header']['outcome'] == 'failed':
            return []

        print self.xml['header']['outcome']

        if self.xml['header']['outcome'] == 'singleJournal' \
            or self.xml['header']['outcome'] == 'uniqueZetoc' :
            return [self.xml['journals']['journal']['jtitle']]

        titles = list()
        for j in self.xml['journals']['journal']:
            titles.append(j['jtitle'])

        return titles

    def get_publishers(self):
        if self.xml['header']['outcome'] == 'notFound' \
           or self.xml['header']['outcome'] == 'failed':
            return []
        #returns a list of publishers' names
        publishers = list()
        try:
            pubs = self.xml['publishers']['publisher']
            publishers.append(pubs['name'])
        except TypeError:
            #there are no publishers
            #the query returned multiple results
            for p in self.xml['publishers']['publisher']:
                publishers.append(p['name'])

        return publishers

    def get_conditions(self):
        if self.xml['header']['outcome'] == 'notFound' \
            or self.xml['header']['outcome'] == 'failed'\
            or self.xml['header']['outcome'] == 'uniqueZetoc' :
            return {}
        elif self.xml['header']['outcome'] == 'singleJournal':
            try:
                return self.xml['publishers']['publisher']['conditions']['condition']
            except TypeError:
                pass
        elif self.xml['header']['outcome'] == 'publisherFound':
            return self.xml['publishers']['publisher']['conditions']['condition']

        #there are no publishers
        #maybe the query returned multiple results
        url = "http://www.sherpa.ac.uk/romeo/api29.php?issn=" + self.get_issn()
        data = urllib2.urlopen(url).read()
        root = ElementTree.XML(data)
        xml = XmlDictConfig(root)
        try:
            return xml['publishers']['publisher']['conditions']['condition']
        except TypeError:
            return None



    def get_issn(self):
        if self.xml['header']['outcome'] == 'notFound' \
           or self.xml['header']['outcome'] == 'failed':
            return []
        if self.xml['header']['outcome'] == 'singleJournal'\
            or self.xml['header']['outcome'] == 'uniqueZetoc' :
            return self.xml['journals']['journal']['issn']
        else:
            issns = dict()
            for j in self.xml['journals']['journal']:
                if j['jtitle'].replace(" ", "+").lower() == self.query.lower():
                    return j['issn']
                issns[j['jtitle']] = j['issn']

            return issns

