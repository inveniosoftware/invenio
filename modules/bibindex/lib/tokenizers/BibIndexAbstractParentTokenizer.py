# -*- coding:utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
""" BibIndexAbstractParentTokenizer: retrieves records using the recid in the
'parent_tag' of the original record, then uses the wrapped 'parent_tokenizer'
to get the tokens from the parent records.
"""

from invenio.bibindex_tokenizers.BibIndexMultiFieldTokenizer import (
    BibIndexMultiFieldTokenizer
)
from invenio.bibindex_tokenizers.BibIndexDefaultTokenizer import (
    BibIndexDefaultTokenizer
)
from invenio.bibindex_engine_utils import (
    get_fieldvalues,
    create_range_list,
    unroll_range_list
)
from invenio.bibindex_termcollectors import TermCollector
from invenio.intbitset import intbitset


class BibIndexAbstractParentTokenizer(BibIndexMultiFieldTokenizer):

    """ Tokenizer that retrieves records using the recid in the 'parent_tag'
    of the original record, then uses the wrapped 'parent_tokenizer' to
    take the tokens from the parent records.

    It uses the parent_tokenizer and the tags associated to the index
    to decide which records need to be indexed.

    This is an abstract class, the extending class must set the
    'implemented' return value to True.

    Description of some variables:
    * parent_tag: it is the tag containing the recids of the
      parent records
    * parent_tokenizer: it is the wrapped tokenizer used to take tokens
      from the parent records
    * self.parent_special_tags and self.parent_tags: parameters passed to
      the TermCollector when getting tokens from the parent records.
      Thes are usually setted by the extending class.

    For some examples of how to extend this class see
    BibIndexParentAuthorTokenizer and BibIndexParentCanonicalAuthorTokenizer
    """

    parent_tokenizer = BibIndexDefaultTokenizer
    parent_tag = "786__w"

    def __init__(self, stemming_language=None,
                 remove_stopwords=False, remove_html_markup=False,
                 remove_latex_markup=False):
        from invenio.bibindex_engine import detect_tokenizer_type
        self.parent_tokenizer = self.parent_tokenizer(
            stemming_language,
            remove_stopwords,
            remove_html_markup,
            remove_latex_markup
        )
        self.parent_tokenizer_type = \
            detect_tokenizer_type(self.parent_tokenizer)

        self.parent_special_tags = {}
        self.parent_tags = []

    def get_parent_recids(self, recID):
        parent_ids = []

        parent_ids += [int(val) for val in get_fieldvalues(
            recID,
            self.parent_tag,
            repetitive_values=False
        )]

        return parent_ids

    def tokenize_parents_range(self, parents_range, table_type):
        wlist = {}
        collector = TermCollector(self.parent_tokenizer,
                                  self.parent_tokenizer_type,
                                  table_type,
                                  self.parent_tags,
                                  parents_range)
        collector.set_special_tags(self.parent_special_tags)
        wlist = collector.collect(unroll_range_list([parents_range]), wlist)
        # Remove duplicates
        return list(set(
            [item for sublist in wlist.values() for item in sublist]
        ))

    def tokenize_parents(self, parent_recids, table_type):
        tokens = []
        parents_range_list = create_range_list(sorted(parent_recids))

        for parents_range in parents_range_list:
            tokens += self.tokenize_parents_range(parents_range, table_type)

        # Remove duplicates
        return list(set(tokens))

    def tokenize(self, recID, table_type):
        return self.tokenize_parents(
            self.get_parent_recids(recID),
            table_type
        )

    def get_tokenizing_function(self, table_type):
        def tokenizing_function(recID):
            return self.tokenize(recID, table_type)
        return tokenizing_function

    @property
    def implemented(self):
        False

    @classmethod
    def get_modified_recids(cls, date_range, index_name):
        """ Returns all the records that need to be reindexed using this
        tokenizer **due to an action happened in the specified date range**.
        Assumes that the tokenizer is used for the index index_name.

        If a record needs to be updated due to a modification happened to
        another record, use get_dependent_recids() insthead of this method.

        @param date_range: the dates between whom this function will look for
            modified records. If the end_date is None this function will look
            for modified records after start_date
        @type date_range: tuple (start_date, end_date)
        @param index_name: the name of the index
        @type index_name: string
        @return: the modified records
        @type return: intbitset
        """
        recids = intbitset()
        # Modified records coming from the super class
        recids |= super(BibIndexAbstractParentTokenizer, cls).get_modified_recids(
            date_range,
            index_name
        )
        # Modified parent records
        parent_tokenizer = cls.parent_tokenizer
        recids |= parent_tokenizer.get_modified_recids(
            date_range,
            index_name
        )
        return recids

    @classmethod
    def get_dependent_recids(cls, modified_recids, index_name):
        """ Returns all the records that need to be reindexed using this
        tokenizer **due to a modification happened to the records in
        modified_recids**.
        Assumes that the tokenizer is used for the index index_name.

        If a record needs to be updated due to an action that did not affect
        another record, use get_modified_recids() insthead of this method.

        @param modified_recids: the ids of the modified records
        @type modified_recids: intbitset
        @param index_name: the name of the index
        @type index_name: string
        @return: the dependent records
        @type return: intbitset
        """
        recids = intbitset()
        # Enrich with records dependant from modified records
        super_class = super(BibIndexAbstractParentTokenizer, cls)
        recids |= super_class.get_dependent_recids(
            modified_recids,
            index_name
        )
        # Get records dependent from parent records
        dependent_from_parent = cls.parent_tokenizer.get_dependent_recids(
            modified_recids,
            index_name
        )
        # Get records referring to dependent_from_parent records
        recids |= get_recids_by_field_values(
            cls.parent_tag,
            dependent_from_parent
        )
        return recids


def get_recids_by_field_values(field, field_values):
    """ Find records whose 'field' value is contained in 'field_values'.

    @param field: the field we are looking at
    @type field: string
    @param field_values: the values we are looking for
    @type field_values: an iterable (e.g. list or intbitset)
    @return: the resulting records
    @type return: intbitset
    """
    from invenio.search_engine import perform_request_search
    result_recids = intbitset()

    for value in field_values:
        result_recids |= intbitset(
            perform_request_search(p=str(value), f=field)
        )

    return result_recids
