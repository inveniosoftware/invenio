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
"""BibIndexCanonicalAuthorTokenizer: tokenizer that extracts author
canonical ids from parent records.
"""

from invenio.bibindex_tokenizers.BibIndexMultiFieldTokenizer import (
    BibIndexMultiFieldTokenizer
)
from invenio.bibindex_engine_utils import get_author_canonical_ids_for_recid
from invenio.intbitset import intbitset


class BibIndexCanonicalAuthorTokenizer(BibIndexMultiFieldTokenizer):

    """Tokenizer that extracts author canonical ids from parent records.
    """

    def get_tokenizing_function(self, wordtable_type):
        return self.tokenize

    def tokenize(self, recID):
        return get_author_canonical_ids_for_recid(recID)

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
        super_class = super(BibIndexCanonicalAuthorTokenizer, cls)
        recids |= super_class.get_modified_recids(
            date_range,
            index_name
        )
        # Record whose canonical author id changed
        recids |= get_modified_recids_bibauthorid(date_range)
        return recids


def get_modified_recids_bibauthorid(dates):
    """ Finds records that were modified between dates due to bibauthorid.

    @param dates: the dates between whom this function will look for
        modified records. If the end_date is None this function will look
        for modified records after start_date
    @type dates: tuple (start_date, end_date)
    @return: the modified recids
    @type return: intbitset
    """
    from invenio.bibauthorid_personid_maintenance import (
        get_recids_affected_since
    )
    return intbitset(get_recids_affected_since(dates[0]))
