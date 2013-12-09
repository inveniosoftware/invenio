# -*- coding:utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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
"""BibIndexJournalTokenizer: useful for journal index.
   Agregates info about journal in a specific way given by its variable
   journal_pubinfo_standard_form.
   Behaves in the same way for all index table types:
   - Words
   - Pairs
   - Phrases
"""

from invenio.dbquery import run_sql
from invenio.bibindex_tokenizers.BibIndexMultiFieldTokenizer import BibIndexMultiFieldTokenizer
from invenio.config import \
    CFG_CERN_SITE, \
    CFG_INSPIRE_SITE
from invenio.bibindex_engine_utils import get_values_recursively
from invenio.bibfield import get_record

if CFG_CERN_SITE:
    CFG_JOURNAL_TAG = '773__%'
    CFG_JOURNAL_PUBINFO_STANDARD_FORM = "773__p 773__v (773__y) 773__c"
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = r'^\w.*\s\w.*\s\(\d+\)\s\w.*$'
    CFG_JOURNAL_PUBINFO_JOURNAL_VOLUME_FORM = "773__p 773__v"
elif CFG_INSPIRE_SITE:
    CFG_JOURNAL_TAG = '773__%'
    CFG_JOURNAL_PUBINFO_STANDARD_FORM = "773__p,773__v,773__c"
    CFG_JOURNAL_PUBINFO_JOURNAL_VOLUME_FORM = "773__p,773__v"
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = r'^\w.*,\w.*,\w.*$'
else:
    CFG_JOURNAL_TAG = '909C4%'
    CFG_JOURNAL_PUBINFO_STANDARD_FORM = "909C4p 909C4v (909C4y) 909C4c"
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = r'^\w.*\s\w.*\s\(\d+\)\s\w.*$'
    CFG_JOURNAL_PUBINFO_JOURNAL_VOLUME_FORM = "909C4p 909C4v"



class BibIndexJournalTokenizer(BibIndexMultiFieldTokenizer):
    """
        Tokenizer for journal index.
        Returns joined title/volume/year/page as a word from journal tag.

        Tokenizer works on multiple tags.
        For more information on tokenizers working on per-record basis
        take a look on BibIndexJournalTokenizer base class.
    """

    def __init__(self, stemming_language = None, remove_stopwords = False, remove_html_markup = False, remove_latex_markup = False):
        self.tag = CFG_JOURNAL_TAG
        self.nonmarc_tag = 'journal_info'
        self.journal_pubinfo_standard_form = CFG_JOURNAL_PUBINFO_STANDARD_FORM
        self.journal_pubinfo_standard_form_regexp_check = CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK
        self.journal_pubinfo_journal_volume_form = CFG_JOURNAL_PUBINFO_JOURNAL_VOLUME_FORM


    def tokenize(self, recID):
        """
        Special procedure to extract words from journal tags.  Joins
        title/volume/year/page into a standard form that is also used for
        citations.
        """
        # get all journal tags/subfields:
        bibXXx = "bib" + self.tag[0] + self.tag[1] + "x"
        bibrec_bibXXx = "bibrec_" + bibXXx
        query = """SELECT bb.field_number,b.tag,b.value FROM %s AS b, %s AS bb
                    WHERE bb.id_bibrec=%%s
                      AND bb.id_bibxxx=b.id AND tag LIKE %%s""" % (bibXXx, bibrec_bibXXx)
        res = run_sql(query, (recID, self.tag))
        # construct journal pubinfo:
        dpubinfos = {}
        for nb_instance, subfield, value in res:
            dpubinfos.setdefault(nb_instance, {})[subfield] = value

        def replace_tags(tags_values, pubinfo):
            for tag, val in tags_values.items():
                    pubinfo = pubinfo.replace(tag, val)
            if self.tag[:-1] in pubinfo:
                # some subfield was missing, do nothing
                return None
            else:
                return pubinfo


        # construct standard format:
        lwords = []
        for dpubinfo in dpubinfos.values():
            # index all journal subfields separately
            for tag, val in dpubinfo.items():
                lwords.append(val)

            # Store journal and volume for searches without a page
            # Store J.Phys.,B50
            word = replace_tags(dpubinfo, self.journal_pubinfo_journal_volume_form)
            if word is not None:
                lwords.append(word)
            # Store full info for searches with all info
            # Store J.Phys.,B50,16-24
            word = replace_tags(dpubinfo, self.journal_pubinfo_standard_form)
            if word is not None:
                lwords.append(word)
            # Store info without ending page for searches without ending page
            # Replace page range with just the starting page
            # 777__c = '16-24' becomes 777__c = '16'
            # Store J.Phys.,B50,16
            for tag in dpubinfo.keys():
                if tag.endswith('c'):
                    dpubinfo[tag] = dpubinfo[tag].split('-')[0]
            word = replace_tags(dpubinfo, self.journal_pubinfo_standard_form)
            if word is not None:
                lwords.append(word)

        # return list of words and pubinfos:
        return lwords

    def tokenize_via_recjson(self, recID):
        """
        Tokenizes for journal info.
        Uses bibfield.
        """
        phrases = []
        rec = get_record(recID)
        recjson_field = rec.get(self.nonmarc_tag)
        get_values_recursively(recjson_field, phrases)
        final = []
        append = final.append
        for phrase in phrases:
            info = phrase.split("-", 1)
            append(info[0])
        return final

    def tokenize_for_words(self, recID):
        return self.tokenize(recID)

    def tokenize_for_pairs(self, recID):
        return self.tokenize(recID)

    def tokenize_for_phrases(self, recID):
        return self.tokenize(recID)

    def get_tokenizing_function(self, wordtable_type):
        return self.tokenize

    def get_nonmarc_tokenizing_function(self, table_type):
        return self.tokenize_via_recjson
