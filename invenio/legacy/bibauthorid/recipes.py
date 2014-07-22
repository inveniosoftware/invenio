# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2014 CERN.
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

'''
    BibAuthorID recipes

    This file has examples how to use the backend of BibAuthorID.
'''

def initial_disambiguation():
    from invenio.legacy.bibauthorid.tortoise import tortoise_from_scratch
    from invenio.legacy.bibauthorid.personid_maintenance import duplicated_tortoise_results_exist
    tortoise_from_scratch()
    assert duplicated_tortoise_results_exist()


# This is a super safe call to tortoise.
# For the moment tortoise is in experimental phase so
# it is mandatory.
def safe_disambiguation_iteration():
    from invenio.legacy.bibauthorid.tortoise import tortoise
    from invenio.legacy.bibauthorid.rabbit import rabbit
    from invenio.legacy.bibauthorid.personid_maintenance import check_author_paper_associations \
                                                 , duplicated_tortoise_results_exist \
                                                 , repair_author_paper_associations
    if not check_author_paper_associations():
        rabbit([])
        repair_author_paper_associations()
        rabbit([])

    assert check_author_paper_associations()
    tortoise()
    assert duplicated_tortoise_results_exist()


def safe_merger():
    from invenio.legacy.bibauthorid.merge import merge_static
    from invenio.legacy.bibauthorid.rabbit import rabbit
    from invenio.legacy.bibauthorid.personid_maintenance import check_author_paper_associations \
                                                 , duplicated_tortoise_results_exist \
                                                 , merger_errors_exist \
                                                 , repair_author_paper_associations \
                                                 , back_up_author_paper_associations \
                                                 , compare_personids

    assert duplicated_tortoise_results_exist()
    if not check_author_paper_associations():
        rabbit([])
        repair_author_paper_associations()
        rabbit([])

    assert check_author_paper_associations()
    back_up_author_paper_associations()
    merge_static()
    assert check_author_paper_associations()
    assert merger_errors_exist()
    compare_personids("/tmp/merge_diff")


def test_accuracy():
    from invenio.legacy.bibauthorid.tortoise import tortoise
    from invenio.legacy.bibauthorid.rabbit import rabbit
    from invenio.legacy.bibauthorid.personid_maintenance import check_author_paper_associations \
                                                 , duplicated_tortoise_results_exist \
                                                 , repair_author_paper_associations
    from invenio.legacy.bibauthorid.merge import matched_claims

    if not check_author_paper_associations():
        rabbit([])
        repair_author_paper_associations()
        rabbit([])

    assert check_author_paper_associations()
    tortoise(pure=True)
    assert duplicated_tortoise_results_exist()

    return matched_claims()
