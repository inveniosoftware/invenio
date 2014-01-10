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

from invenio.legacy.dbquery import run_sql
from invenio.modules.indexer.tokenizers.BibIndexEmptyTokenizer import BibIndexEmptyTokenizer
from invenio.config import \
    CFG_CERN_SITE, \
    CFG_INSPIRE_SITE


if CFG_CERN_SITE:
    CFG_JOURNAL_TAG = '773__%'
    CFG_JOURNAL_PUBINFO_STANDARD_FORM = "773__p 773__v (773__y) 773__c"
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = r'^\w.*\s\w.*\s\(\d+\)\s\w.*$'
elif CFG_INSPIRE_SITE:
    CFG_JOURNAL_TAG = '773__%'
    CFG_JOURNAL_PUBINFO_STANDARD_FORM = "773__p,773__v,773__c"
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = r'^\w.*,\w.*,\w.*$'
else:
    CFG_JOURNAL_TAG = '909C4%'
    CFG_JOURNAL_PUBINFO_STANDARD_FORM = "909C4p 909C4v (909C4y) 909C4c"
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = r'^\w.*\s\w.*\s\(\d+\)\s\w.*$'



class BibIndexJournalTokenizer(BibIndexEmptyTokenizer):
    """
        Tokenizer for journal index. It returns joined title/volume/year/page as a word from journal tag.
        (In fact it's an aggregator.)
    """

    def __init__(self, stemming_language = None, remove_stopwords = False, remove_html_markup = False, remove_latex_markup = False):
        self.tag = CFG_JOURNAL_TAG
        self.journal_pubinfo_standard_form = CFG_JOURNAL_PUBINFO_STANDARD_FORM
        self.journal_pubinfo_standard_form_regexp_check = CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK


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
        for row in res:
            nb_instance, subfield, value = row
            if subfield.endswith("c"):
                # delete pageend if value is pagestart-pageend
                # FIXME: pages may not be in 'c' subfield
                value = value.split('-', 1)[0]
            if dpubinfos.has_key(nb_instance):
                dpubinfos[nb_instance][subfield] = value
            else:
                dpubinfos[nb_instance] = {subfield: value}

        # construct standard format:
        lwords = []
        for dpubinfo in dpubinfos.values():
            # index all journal subfields separately
            for tag, val in dpubinfo.items():
                lwords.append(val)
            # index journal standard format:
            pubinfo = self.journal_pubinfo_standard_form
            for tag, val in dpubinfo.items():
                pubinfo = pubinfo.replace(tag, val)
            if self.tag[:-1] in pubinfo:
                # some subfield was missing, do nothing
                pass
            else:
                lwords.append(pubinfo)

        # return list of words and pubinfos:
        return lwords

    def get_tokenizing_function(self, wordtable_type):
        return self.tokenize
