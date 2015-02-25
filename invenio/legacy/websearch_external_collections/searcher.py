# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Invenio external search Engines."""

__revision__ = "$Id$"

import sys
import urllib

import cgi

from six import iteritems

from invenio.config import CFG_SITE_LANG
from .config import CFG_EXTERNAL_COLLECTIONS, CFG_EXTERNAL_COLLECTION_MAXRESULTS
from .parser import CDSIndicoCollectionResutsParser, \
    GoogleExternalCollectionResultsParser, \
    KISSExternalCollectionResultsParser, GoogleScholarExternalCollectionResultsParser, \
    GoogleBooksExternalCollectionResultsParser, KISSBooksExternalCollectionResultsParser, \
    SPIRESExternalCollectionResultsParser, SCIRUSExternalCollectionResultsParser, \
    CiteSeerExternalCollectionResultsParser, ScienceCinemaXMLExternalCollectionResultsParser

def format_basic(basic):
    """Format a basic query"""
    if basic[3] == "w":
        return basic[1]
    else:
        return '"' + basic[1] + '"'

def only_field(basic_search_units, fieldname):
    """Check if in the basic search units, there is only on field representated."""
    for search_unit in basic_search_units:
        if search_unit[2] != fieldname:
            return False
    return True

class ExternalSearchEngine(object):
    """Global class for interfaces to external search engines."""

    lang_translator = None

    def __init__(self, configuration):
        self.search_url = ""
        self.user_search_url = None
        self.combiner = " "
        self.name = None
        self.parser_params = None
        self.parser = None
        self.fetch_format = ""
        self.record_url = None
        self.selected_by_default = False
        for (name, value) in iteritems(configuration):
            setattr(self, name, value)
        if self.parser_params:
            setattr(self, 'parser', self.parser_params['parser'](self.parser_params))
            if 'fetch_format' in self.parser_params.keys():
                self.fetch_format = self.parser_params['fetch_format']

    def build_units(self, basic_search_units):
        """ Build the research units for basic_search_units provided"""
        units = []
        for search_unit in basic_search_units:
            unit = self.build_search_unit_unit(search_unit)
            if unit is not None:
                units.append(unit)
        return units

    def build_search_unit_unit(self, basic):
        """Build a search string from a search unit. This is the base
        version that just keep keywords with "+". """
        if basic[0] == "+":
            return basic[1]
        return None

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """
        Build a search URL for a specific set of search_units.

        This is the URL accessed by the engine to retrieve the records
        to embed on the results page. Use C{self.search_url} as base
        URL when L{search_url} is not set.

        @see: L{build_user_search_url}
        """

        units = self.build_units(basic_search_units)
        if len(units) == 0:
            return None
        request = self.combine_units(units)
        url_request = urllib.quote(request)

        return self.search_url + url_request

    def build_user_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """
        Build a user search URL for a specific set of search_units.

        This is the URL that users can follow to retrieve the full set
        of results on the remote search engine. It can return a
        different URL from L{build_search_url} when it retrieves for
        eg. XML results, while this function would link to an HTML
        page. Use L{self.user_search_url} as base URL.

        Returns C{None} when the URL returned by L{build_search_url}
        should be used instead.

        @see: L{build_search_url}
        """
        if self.user_search_url is None:
            return None

        units = self.build_units(basic_search_units)
        if len(units) == 0:
            return None
        request = self.combine_units(units)
        url_request = urllib.quote(request)

        return self.user_search_url + url_request

    def combine_units(self, units):
        """Combine the units to make a boolean AND query."""
        return self.combiner.join(units)

    def __repr__(self):
        return 'ec:' + self.name

class SortedFieldsSearchEngine(ExternalSearchEngine):
    """Class for search engines that used separate query box for fields."""

    def __init__(self, configuration):
        self.fields = []
        self.fields_content = {}
        self.search_url = ""
        self.converter = {}
        super(SortedFieldsSearchEngine, self).__init__(configuration)

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build a search URL. Reuse the search pattern found in req only with Invenio-based search engines"""
        self.clear_fields()
        self.fill_fields(basic_search_units)

    def clear_fields(self):
        """Clear fields to be able to build a new URL."""
        self.fields_content = {}
        for field_name in self.fields:
            self.fields_content[field_name] = []
        self.fields_content["default"] = []

    def fill_fields(self, basic_search_units):
        """Fill fields with the apropriate research terms."""
        for search_unit in basic_search_units:
            self.add_search_unit(search_unit)

    def add_search_unit(self, search_unit):
        """Add a search unit to fields to search."""

        if search_unit[0] == "-":
            return

        search = format_basic(search_unit)
        field_name = search_unit[2]
        if field_name in self.fields:
            self.fields_content[field_name].append(search)
        else:
            self.fields_content["default"].append(search)

# CERN

class CDSIndicoSearchEngine(ExternalSearchEngine):
    """Global class for CDS Search Engines."""

    index_translator = {'title' : 'title', 'author': 'author', 'fulltext': 'fulltext', 'abstract': 'abstract', 'affiliation': 'affiliation', 'keyword': 'keyword'}
    lang_translator = {
        'ca': 'ca', 'cs': 'cs', 'de': 'de', 'el': 'el', 'en': 'en', 'es': 'es',
        'fr': 'fr', 'it': 'it', 'ja': 'ja', 'no': 'no', 'pl': 'pl', 'pt': 'pt',
        'ru': 'ru', 'sk': 'sk', 'sv': 'sv', 'uk': 'uk', 'default' : 'en'}

    def __init__(self, configuration):
        super(CDSIndicoSearchEngine, self).__init__(configuration)
        self.base_url = 'http://indico.cern.ch/'
        #self.search_url = 'http://indicosearchpublic.cern.ch/search?cc=INDICOPUBLIC&p='
        self.search_url = 'http://indico.cern.ch/search.py?p='
        self.parser = CDSIndicoCollectionResutsParser()

    def build_search_unit_unit(self, basic):
        """Build a search string from a search unit.
        This will also translate index name using the index_translator
        dictionary."""
        operator = basic[0]
        pattern = basic[1]
        index = basic[2]
        search_type = basic[3]

        if index in self.index_translator:
            index = self.index_translator[index]
        else:
            index = None

        if index:
            return operator + index + ':"' + pattern + '"'
        else:
            if search_type == 'w':
                return operator + pattern
            else:
                return operator + '"' + pattern + '"'

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build an URL for a specific set of search_units."""

        url = super(CDSIndicoSearchEngine, self).build_search_url(basic_search_units, None, lang)
        if not url:
            return None

        if lang in self.lang_translator:
            dest_lang = self.lang_translator[lang]
        else:
            dest_lang = self.lang_translator['default']

        return url + '&ln=' + dest_lang + '&rg=' + str(CFG_EXTERNAL_COLLECTION_MAXRESULTS)

class CERNEDMSSearchEngine(SortedFieldsSearchEngine):
    """CERN EDMS"""

    def __init__(self, configuration):
        super(CERNEDMSSearchEngine, self).__init__(configuration)
        self.base_url = "http://edms.cern.ch/cedar/plsql/fullsearch.doc_search"
        self.search_url = "http://edms.cern.ch/cedar/plsql/fullsearch.doc_search?p_search_type=ADVANCED&"
        self.search_url_simple = "http://edms.cern.ch/cedar/plsql/fullsearch.doc_search?p_search_type=BASE&p_free_text="
        self.fields = ["author", "keyword", "abstract", "title", "reportnumber"]

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build an URL for CERN EDMS."""
        super(CERNEDMSSearchEngine, self).build_search_url(basic_search_units)
        if len(self.fields_content["default"]) > 0:
            free_text = self.bind_fields(["author", "keyword", "abstract", "title", "reportnumber", "default"])
            return self.search_url_simple + free_text
        else:
            authors = self.bind_fields(["author"])
            title = self.bind_fields(["title", "abstract", "keyword"])
            reportnumber = self.bind_fields(["reportnumber"])
            url_parts = []
            if authors != '':
                url_parts.append('p_author=' + authors)
            if title != "":
                url_parts.append('p_title=' + title)
            if reportnumber != "":
                url_parts.append('p_document_id=' + reportnumber)
            if len(url_parts) == 0:
                return None
            return self.search_url + "&".join(url_parts)

    def bind_fields(self, fieldname_list):
        """Combine some fields together."""
        result = []
        for key in fieldname_list:
            content = self.fields_content[key]
            if len(content) > 0:
                result.append(" ".join(content))
        return urllib.quote(" ".join(result))

class CERNAgendaSearchEngine(ExternalSearchEngine):
    """CERN Agenda"""

    def __init__(self, configuration):
        super(CERNAgendaSearchEngine, self).__init__(configuration)
        self.base_url = "http://agenda.cern.ch"
        self.search_url_author = "http://agenda.cern.ch/search.php?field=speaker&search=Search&keywords="
        self.search_url_title = "http://agenda.cern.ch/search.php?field=title&search=Search&keywords="

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build an url for searching on CERN Agenda. This will only work if there is only author
        or title tags."""
        if only_field(basic_search_units, "author"):
            self.search_url = self.search_url_author
        elif only_field(basic_search_units, "title"):
            self.search_url = self.search_url_title
        else:
            return None
        return super(CERNAgendaSearchEngine, self).build_search_url(basic_search_units)

# Google

class GoogleSearchEngine(ExternalSearchEngine):
    """Search engine class for Google """

    def __init__(self, configuration):
        super(GoogleSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.google.com"
        self.search_url = "http://www.google.com/search?q="
        self.parser = GoogleExternalCollectionResultsParser()

    def build_search_unit_unit(self, search_unit):
        """Build a part of the google query."""
        return self.build_search_unit_unit_google(search_unit, "")

    def build_search_unit_unit_google(self, search_unit, author_tag):
        """Parse a unit and return it in a google query form."""
        sign = search_unit[0].replace("+", "")
        if search_unit[2] == "author":
            if search_unit[1].find(",") >= 0 and search_unit[3] != "p":
                (lastname, firstname) = search_unit[1].split(",", 1)
                return sign + author_tag + '"%s %s" OR ' % (lastname, firstname) + \
                    sign + author_tag + '"%s %s"' % (firstname, lastname)
            else:
                return sign + author_tag + search_unit[1]
        if search_unit[3] == "w":
            return sign + search_unit[1]
        else:
            return sign + '"' + search_unit[1] + '"'

class GoogleBooksSearchEngine(GoogleSearchEngine):
    """Interface for searching on Google Books."""

    def __init__(self, configuration):
        super(GoogleBooksSearchEngine, self).__init__(configuration)
        self.base_url = "http://books.google.com"
        self.search_url = "http://books.google.com/books?q="
        self.parser = GoogleBooksExternalCollectionResultsParser()

class GoogleScholarSearchEngine(GoogleSearchEngine):
    """Interface for searching on Google Scholar."""

    def __init__(self, configuration):
        super(GoogleScholarSearchEngine, self).__init__(configuration)
        self.base_url = 'http://scholar.google.com'
        self.search_url = 'http://scholar.google.com/scholar?q='
        self.parser = GoogleScholarExternalCollectionResultsParser()

    def build_search_unit_unit(self, search_unit):
        """Build a unit for Google Scholar. Is different from Google one's
        because there is an author tag for authors."""
        return self.build_search_unit_unit_google(search_unit, "author:")

# Kiss

class KissSearchEngine(SortedFieldsSearchEngine):
    """Search interface for KEK Information Service System.
       Not to be used directly but with Kiss*SearchEngine. """

    def __init__(self, configuration):
        super(KissSearchEngine, self).__init__(configuration)
        self.converter = { "author": "AU=", "year": "YR=",
             "title": "TI=", "reportnumber": "RP=" }
        self.fields = self.converter.keys()
        self.parser = KISSExternalCollectionResultsParser()

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build an URL for a search."""
        super(KissSearchEngine, self).build_search_url(basic_search_units)
        url_parts = []
        for key in self.fields:
            if len(self.fields_content[key]) > 0:
                field_request = " and ".join(self.fields_content[key])
                url_part = self.converter[key] + urllib.quote(field_request)
                url_parts.append(url_part)
        if len(url_parts) == 0:
            return None
        return self.search_url + "&".join(url_parts)

    def add_search_unit(self, search_unit):
        """Add a search unit to fields to search."""
        if search_unit[0] == "+":
            search = search_unit[1]
            field_name = search_unit[2]
            if field_name == "author":
                self.add_author(search, search_unit[3])
            elif field_name == "year" or field_name == "reportnumber":
                self.fields_content[field_name].append(search)
            else:
                self.fields_content["title"].append("'" + search + "'")

    def add_author(self, author_name, unit_type):
        """Handle an author unit. """
        if author_name.find(",") >= 0 and unit_type != "p":
            (lastname, firstname) = author_name.split(",", 1)
            if firstname:
                self.fields_content["author"].append("'%s, %c'" % (lastname, firstname[0]))
            else:
                self.fields_content["author"].append("'%s'" % (lastname))
        else:
            self.fields_content["author"].append("'" + author_name + "'")

class KissForPreprintsSearchEngine(KissSearchEngine):
    """Interface for seaching on Kiss for Preprints"""

    def __init__(self, configuration):
        super(KissForPreprintsSearchEngine, self).__init__(configuration)
        self.base_url = "http://www-lib.kek.jp/KISS/kiss_prepri.html"
        self.search_url = "http://www-lib.kek.jp/cgi-bin/kiss_prepri.v8?"

class KissForBooksAndJournalsSearchEngine(KissSearchEngine):
    """Interface for seaching on Kiss for Books and Journals"""

    def __init__(self, configuration):
        super(KissForBooksAndJournalsSearchEngine, self).__init__(configuration)
        self.base_url = "http://www-lib.kek.jp/KISS/kiss_book.html"
        self.search_url = "http://www-lib.kek.jp/cgi-bin/kiss_book.v8?DSP=1&"
        self.parser = KISSBooksExternalCollectionResultsParser()

# Scirus

class ScirusSearchEngine(ExternalSearchEngine):
    """Interface for the Scirus search engine."""

    def __init__(self, configuration):
        super(ScirusSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.scirus.com/srsapp/"
        self.search_url = "http://www.scirus.com/srsapp/search?q="
        self.parser = SCIRUSExternalCollectionResultsParser()

    def build_search_unit_unit(self, search_unit):
        """Build a unit for a search unit"""
        sign = search_unit[0].replace("+", "")
        search = self.normalize_unit(search_unit)
        if search_unit[2] == "author":
            return sign + "au:" + search
        if search_unit[2] == "title":
            return sign + "ti:" + search
        if search_unit[2] == "keyword":
            return sign + "keyword:" + search
        if search_unit[3] == "w":
            return sign + search

    def normalize_unit(self, search_unit):
        """ Add double quote if needed. """
        if search_unit[3] == "a":
            return '"' + search_unit[1] + '"'
        else:
            return search_unit[1]

# Spires

class SPIRESSearchEngine(ExternalSearchEngine):
    """Interface for the Spires Search engine."""

    def __init__(self, configuration):
        super(SPIRESSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.slac.stanford.edu/spires/hep/"
        self.search_url = "http://www.slac.stanford.edu/spires/find/hep/?rawcmd=find+"
        self.combiner = " and "
        self.parser = SPIRESExternalCollectionResultsParser()

    def build_search_unit_unit(self, basic):
        """Build a search string from a search unit. This is the base
        version that just keep keywords with "+". """
        word = format_basic(basic)
        if basic[0] == "-":
            sign = "not "
        else:
            sign = ""
        if basic[2] == "author":
            return sign + "a " + word
        if basic[2] == "title":
            return sign + "t " + word
        if basic[2] == "keyword":
            return sign + "k " + word
        if basic[2] == "reportnumber":
            return sign + "r " + word
        if basic[0] == "+":
            return "a " + word + " or t " + word + " or k " + word
        else:
            return "not a " + word + " and not t " + word + " and not k " + word

class SPIRESBooksSearchEngine(SPIRESSearchEngine):
    """SPIRES Books"""

    def __init__(self, configuration):
        super(SPIRESBooksSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.slac.stanford.edu/library/catalog/"
        self.search_url = "http://www.slac.stanford.edu/spires/find/books/?rawcmd=find+"
        self.parser = None

class SPIRESJournalsSearchEngine(SPIRESSearchEngine):
    """SPIRES Journals"""

    def __init__(self, configuration):
        super(SPIRESJournalsSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.slac.stanford.edu/spires/find/tserials/"
        self.search_url = "http://www.slac.stanford.edu/spires/find/tserials/?rawcmd=find+"

# Misc

class AmazonSearchEngine(ExternalSearchEngine):
    """Interface for searching books on Amazon."""

    def __init__(self, configuration):
        super(AmazonSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.amazon.com"
        self.search_url_general = "http://www.amazon.com/exec/obidos/external-search/?tag=cern&keyword="
        self.search_url_author = "http://www.amazon.com/exec/obidos/external-search/?tag=cern&field-author="

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build an URL for Amazon"""
        if only_field(basic_search_units, "author"):
            self.search_url = self.search_url_author
        else:
            self.search_url = self.search_url_general
        return super(AmazonSearchEngine, self).build_search_url(basic_search_units)

class CiteseerSearchEngine(ExternalSearchEngine):
    """Interface for searching on CiteSeer."""

    def __init__(self, configuration):
        super(CiteseerSearchEngine, self).__init__(configuration)
        self.base_url = "http://citeseer.ist.psu.edu"
        self.search_url = "http://citeseer.ist.psu.edu/cs?q="
        self.parser = CiteSeerExternalCollectionResultsParser()

class INSPECSearchEngine(ExternalSearchEngine):
    """INSPEC"""

    def __init__(self, configuration):
        super(INSPECSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.datastarweb.com/cern/"
        self.search_url = "http://www.datastarweb.com/cern/?dblabel=inzz&query="
        self.combiner = " AND "

    def build_search_unit_unit(self, basic):
        """Build a search string from a search unit. This is the base
        version that just keep keywords with "+". """
        word = format_basic(basic)
        if basic[0] == "-":
            return None
        if basic[2] == "author":
            return word + ".au."
        if basic[2] == "title":
            return word + ".ti."
        if basic[2] == "abstract":
            return word + ".ab."
        if basic[2] == "year":
            return word + ".yr."
        return word + ".ti. OR " + word + ".ab."

class NEBISSearchEngine(ExternalSearchEngine):
    """NEBIS"""

    def __init__(self, configuration):
        super(NEBISSearchEngine, self).__init__(configuration)
        self.base_url = "http://opac.nebis.ch"
        self.search_url_general = "http://opac.nebis.ch/F/?func=find-b&find_code=WRD&REQUEST="
        self.search_url_author = "http://opac.nebis.ch/F/?func=find-b&find_code=WAU&REQUEST="
        self.search_url_title = "http://opac.nebis.ch/F/?func=find-b&find_code=WTI&REQUEST="

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build an URL for NEBIS"""
        if only_field(basic_search_units, "author"):
            self.search_url = self.search_url_author
        elif only_field(basic_search_units, "title"):
            self.search_url = self.search_url_title
        else:
            self.search_url = self.search_url_general
        return super(NEBISSearchEngine, self).build_search_url(basic_search_units)

# Invenio based

class InvenioSearchEngine(ExternalSearchEngine):
    """Generic search engine class for Invenio based sites"""

    def __init__(self, configuration):
        super(InvenioSearchEngine, self).__init__(configuration)

    def build_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build a URL for an Invenio based site"""

        if req_args:
            search_url_params = ""
            if type(req_args) is list:
                # req_args is by definition a string. It is a list
                # only when we manually pass it as a list of recids.
                conjunction = " or "
                search_url_recids = conjunction.join(['recid:%s'] * len(req_args))
                params = tuple(req_args)
                search_url_recids %= params
                # TODO: "rg" here should be the naximum limit of items to be
                # added to a basket at once. Create a static variable for that.
                req_args = "p=" + search_url_recids + "&rg=" + str(100)
            req_args_dict = cgi.parse_qs(req_args)
            if 'p' in req_args_dict:
                search_url_params += urllib.quote(req_args_dict['p'][0])
            if 'f' in req_args_dict:
                search_url_params += '&f=' + req_args_dict['f'][0]
            if 'jrec' in req_args_dict:
                search_url_params += '&jrec=' + req_args_dict['jrec'][0]
            if 'rg' in req_args_dict:
                search_url_params += '&rg=' + req_args_dict['rg'][0]
            else:
                search_url_params += '&rg=' + str(limit)
            if 'd1d' in req_args_dict:
                search_url_params += '&d1d=' + req_args_dict['d1d'][0]
            if 'd1m' in req_args_dict:
                search_url_params += '&d1m=' + req_args_dict['d1m'][0]
            if 'd1y' in req_args_dict:
                search_url_params += '&d1y=' + req_args_dict['d1y'][0]
            if 'd2d' in req_args_dict:
                search_url_params += '&d2d=' + req_args_dict['d2d'][0]
            if 'd2m' in req_args_dict:
                search_url_params += '&d2m=' + req_args_dict['d2m'][0]
            if 'd2y' in req_args_dict:
                search_url_params += '&d2y=' + req_args_dict['d2y'][0]
            if 'ap' in req_args_dict:
                search_url_params += '&ap=' + req_args_dict['ap'][0]
            if 'sf' in req_args_dict:
                search_url_params += '&sf=' + req_args_dict['sf'][0]
            if 'so' in req_args_dict:
                search_url_params += '&so=' + req_args_dict['so'][0]
            if not '&userurl=true' in req_args:
                search_url_params += '&of=' + self.fetch_format
            return self.search_url + search_url_params
        else:
            units = self.build_units(basic_search_units)
            if len(units) == 0:
                return None
            request = self.combine_units(units)
            url_request = urllib.quote(request)
            return self.search_url + url_request + '&rg=' + str(limit) + '&of=' + self.fetch_format

    def build_user_search_url(self, basic_search_units, req_args=None, lang=CFG_SITE_LANG, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS):
        """Build a user search URL for a specific set of search_units."""
        if type(req_args) is str:
            req_args += '&userurl=true'
        return self.build_search_url(basic_search_units, req_args, lang, limit)

    def build_search_unit_unit(self, basic):
        """Build a search string from a search unit. Reconstructs original user query"""

        # TO DO: correct & improve the print out
        # adding the semicolon in case a specific field is chosen
        if basic[2] != "": basic[2] = basic[2] + ":"
        # adding the single quotes in case a multi word values is searched for
        if basic[3] == "a": basic[1] = "'" + basic[1] + "'"
        return basic[0] + " " + basic[2] + basic[1]

    def build_record_urls(self, recids):
        """Given a list of records this function returns a dictionary with
        recid:external_url key:value pairs"""

        if type(recids) is not list:
            recids = [recids]
        recids_urls = []
        for recid in recids:
            recids_urls.append((recid, self.record_url + recid))
        return recids_urls

# ScienceCinema

class ScienceCinemaSearchEngine(ExternalSearchEngine):
    """ScienceCinema"""

    def __init__(self, configuration):
        super(ScienceCinemaSearchEngine, self).__init__(configuration)
        self.base_url = "http://www.osti.gov/sciencecinema"
        self.search_url = "http://www.osti.gov/sciencecinema/searchxml?audio="
        self.user_search_url = "http://www.osti.gov/sciencecinema/basicsearch.jsp?act=Search&searchFor="
        self.parser = ScienceCinemaXMLExternalCollectionResultsParser()

external_collections_dictionary = {}

def build_external_collections_dictionary():
    """Build the dictionary of the external collections."""
    for (name, configuration) in iteritems(CFG_EXTERNAL_COLLECTIONS):
        engine_name = configuration.pop('engine', 'External') + 'SearchEngine'
        configuration['name'] = name
        if engine_name in globals():
            external_collections_dictionary[name] = globals()[engine_name](configuration)
        else:
            sys.stderr.write("Error : not found " + engine_name + "\n")

build_external_collections_dictionary()
