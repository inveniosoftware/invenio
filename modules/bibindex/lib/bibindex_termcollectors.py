# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
BibIndex termcollectors.
"""

import fnmatch

from invenio.bibindex_engine_utils import list_union, \
    UnknownTokenizer, \
    get_values_recursively
from invenio.bibindex_engine_config import CFG_BIBINDEX_TOKENIZER_TYPE
from invenio.dbquery import run_sql
from invenio.bibdocfile import BibRecDocs
from invenio.search_engine_utils import get_fieldvalues

from invenio.bibauthority_engine import get_index_strings_by_control_no
from invenio.bibauthority_config import \
    CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC
from invenio.bibfield import get_record


class TermCollector(object):

    """
    Objects of this class take care of collecting phrases from
    records metadata and tokenizing them in order to get
    termslists which can be store in databse.

    They collect terms from MARC tags ONLY.
    Please don't use it for other standards, of course
    you can, but it won't work. Use NonmarcTermCollector instead.
    """

    def __init__(self, tokenizer,
                 tokenizer_type,
                 table_type,
                 tags,
                 recIDs_range):
        self.table_type = table_type
        self.tokenizer = tokenizer
        self.tokenizer_type = tokenizer_type
        self.tokenizing_function = \
            self.tokenizer.get_tokenizing_function(table_type)
        self.tags = tags
        self.special_tags = {}
        self.first_recID = recIDs_range[0]
        self.last_recID = recIDs_range[1]

        if self.tokenizer_type not in CFG_BIBINDEX_TOKENIZER_TYPE.values():
            raise UnknownTokenizer("Tokenizer has not been recognized: %s"
                                   % self.tokenizer.__class__.__name__)

    def set_special_tags(self, special_tags):
        """
        Adds special tags for further use.
        """
        self.special_tags = special_tags

    def collect(self, recIDs, termslist={}):
        """
        Finds terms and tokenizes them in order to obtain termslist.
        @param recIDs: records to index in form: [rid1, rid2, rid3 ...]
        @param termslist: dictionary for results
        """
        collector = getattr(self, "_collect_" + self.tokenizer_type)
        return collector(recIDs, termslist)

    def _collect_recjson(self, recIDs, termslist):
        """
        Collects terms from recjson with use of bibfield.
        Used together with recjson tokenizer.
        """
        tokenizing_function = self.tokenizing_function
        for recID in recIDs:
            record = get_record(recID)
            if record:
                new_words = tokenizing_function(record)
                if not recID in termslist:
                    termslist[recID] = []
                termslist[recID] = list_union(new_words, termslist[recID])
        return termslist

    def _collect_multifield(self, recIDs, termslist):
        """
        Calculates terms from many fields or tags.
        Used together with multifield tokenizer
        """
        tokenizing_function = self.tokenizing_function
        for recID in recIDs:
            new_words = tokenizing_function(recID)
            if not recID in termslist:
                termslist[recID] = []
            termslist[recID] = list_union(new_words, termslist[recID])
        return termslist

    def _collect_string(self, recIDs, termslist):
        """
        Collects terms from specific tags or fields.
        Used together with string tokenizer.
        """
        for tag in self.tags:
            tokenizing_function = self.special_tags.get(
                tag, self.tokenizing_function)
            phrases = self._get_phrases_for_tokenizing(tag, recIDs)
            for recID, phrase in phrases:
                if recID in recIDs:
                    if not recID in termslist:
                        termslist[recID] = []
                    new_words = tokenizing_function(phrase)
                    termslist[recID] = list_union(new_words, termslist[recID])
        return termslist

    def _get_phrases_for_tokenizing(self, tag, recIDs):
        """
        Gets phrases for later tokenization
        for a range of records and specific tag.
        @param tag: MARC tag
        @param recIDs: list of specific recIDs (not range)
        """
        if len(recIDs) == 0:
            return ()
        bibXXx = "bib" + tag[0] + tag[1] + "x"
        bibrec_bibXXx = "bibrec_" + bibXXx
        query = """SELECT bb.id_bibrec,b.value FROM %s AS b, %s AS bb
                   WHERE bb.id_bibrec BETWEEN %%s AND %%s
                   AND bb.id_bibxxx=b.id AND tag LIKE %%s""" % (bibXXx, bibrec_bibXXx)
        phrases = run_sql(query, (self.first_recID, self.last_recID, tag))
        if tag == '8564_u':
            # FIXME: Quick hack to be sure that hidden files are
            # actually indexed.
            phrases = set(phrases)
            for recID in recIDs:
                for bibdocfile in BibRecDocs(recID).list_latest_files():
                    phrases.add((recID, bibdocfile.get_url()))
        # authority records
        pattern = tag.replace('%', '*')
        matches = fnmatch.filter(
            CFG_BIBAUTHORITY_CONTROLLED_FIELDS_BIBLIOGRAPHIC.keys(), pattern)
        if not len(matches):
            return phrases
        phrases = set(phrases)
        for tag_match in matches:
            authority_tag = tag_match[0:3] + "__0"
            for recID in recIDs:
                control_nos = get_fieldvalues(recID, authority_tag)
                for control_no in control_nos:
                    new_strings = get_index_strings_by_control_no(control_no)
                    for string_value in new_strings:
                        phrases.add((recID, string_value))
        return phrases


class NonmarcTermCollector(TermCollector):

    """
        TermCollector for standards other than MARC.
        Uses bibfield's records and fields.
    """

    def __init__(self, tokenizer,
                 tokenizer_type,
                 table_type,
                 tags,
                 recIDs_range):
        super(NonmarcTermCollector, self).__init__(tokenizer,
                                                   tokenizer_type,
                                                   table_type,
                                                   tags,
                                                   recIDs_range)
        self.tokenizing_function = \
            self.tokenizer.get_nonmarc_tokenizing_function(table_type)

    def _collect_string(self, recIDs, termslist):
        """
        Collects terms from specific tags or fields.
        Used together with string tokenizer.
        """
        tags = self.tags
        for recID in recIDs:
            rec = get_record(recID)
            new_words = []
            extend = new_words.extend
            for tag in tags:
                tokenizing_function = self.special_tags.get(
                    tag, self.tokenizing_function)
                phrases = []
                recjson_field = rec.get(tag)
                get_values_recursively(recjson_field, phrases)
                for phrase in phrases:
                    extend(tokenizing_function(phrase))
            if recID not in termslist and new_words:
                termslist[recID] = []
            if new_words:
                termslist[recID] = list_union(new_words, termslist[recID])
        return termslist
