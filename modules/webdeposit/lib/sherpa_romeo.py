# This Python file uses the following encoding: utf-8
from xmlDict import *
import urllib2
from werkzeug.contrib.cache import RedisCache


class SherpaRomeoSearch:

    def searchPublisher(self, query):
        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?pub=" + cleanquery
        self.parser = SherpaRomeoXMLParser()
        self.parser.parseURL(url)
        return self.parser.getPublishers()

    def searchTitle(self, query):
        cleanquery = query.replace(" ", "+")
        url = "http://www.sherpa.ac.uk/romeo/api29.php?jtitle=" + cleanquery + "&qtype=contains"
        self.parser = SherpaRomeoXMLParser()
        self.parser.parseURL(url)
        return self.parser.getTitles()


class SherpaRomeoXMLParser:

    def __init__(self):
        self.parsed = False


    def parseURL(self, url):
        print url
        self.url = url
        #example
        #url = 'http://www.sherpa.ac.uk/romeo/api29.php?jtitle=Annals%20of%20Physics'

        foundTitle = url.find("jtitle=")
        if foundTitle != -1:
            self.type = "title"
            self.query = url[foundTitle + 7:(len(url) - 15)]
        else:
            self.type = "pub"
            foundPublisher = url.find("pub=")
            if foundPublisher != -1:
                self.query = url[foundTitle + 4:len(url)]

        cache = RedisCache("localhost", default_timeout=9000)
        cachedXML = cache.get(self.type + ":" + self.query)
        if not cachedXML:
            print self.type + ":" + self.query + " is not cached!"
            self.data = urllib2.urlopen(url).read()
            root = ElementTree.XML(self.data)
            self.xml = XmlDictConfig(root)
            cache.set(self.type + ":" + self.query, self.data)
        else:
            self.data = cachedXML
            root = ElementTree.XML(self.data)
            self.xml = XmlDictConfig(root)

        self.parsed = True

    def getTitles(self):
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

    def getPublishers(self):
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


    def getConditions(self):
        #returns a publisher=>conditions dictionary
        if self.xml['header']['outcome'] == 'notFound' \
            or self.xml['header']['outcome'] == 'failed'\
            or self.xml['header']['outcome'] == 'uniqueZetoc' :
            return {}
        conditions = dict()

        if self.xml['header']['outcome'] == 'singleJournal':
            return self.xml['publishers']['publisher']['conditions']['condition']

        try:
            pubs = self.xml['publishers']['publisher']
        except TypeError:
            #there are no publishers
            #maybe the query returned multiple results
            url = "http://www.sherpa.ac.uk/romeo/api29.php?issn=" + self.getISSN()
            data = urllib2.urlopen(url).read()
            root = ElementTree.XML(data)
            xml = XmlDictConfig(root)
            return xml['publishers']['publisher']['conditions']['condition']

        for p in pubs:
            try:
                conditions[p['name']] = p['conditions']['condition']
            except TypeError:
                #there are no conditions
                #maybe the query returned multiple results
                if self.getISSN() is None:
                    continue;
                url = "http://www.sherpa.ac.uk/romeo/api29.php?issn=" + self.getISSN()
                print url
                data = urllib2.urlopen(url).read()
                root = ElementTree.XML(data)
                xml = XmlDictConfig(root)
                return xml['publishers']['publisher']['conditions']['condition']

        return conditions

    def getISSN(self):
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

