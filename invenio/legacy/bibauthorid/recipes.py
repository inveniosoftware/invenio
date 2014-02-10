# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011, 2012 CERN.
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
    from invenio.legacy.bibauthorid.personid_maintenance import check_results
    tortoise_from_scratch()
    assert check_results()


# This is a super safe call to tortoise.
# For the moment tortoise is in experimental phase so
# it is mandatory.
def safe_disambiguation_iteration():
    from invenio.legacy.bibauthorid.tortoise import tortoise
    from invenio.legacy.bibauthorid.rabbit import rabbit
    from invenio.legacy.bibauthorid.personid_maintenance import check_personid_papers \
                                                 , check_results \
                                                 , repair_personid

    if not check_personid_papers():
        rabbit([])
        repair_personid()
        rabbit([])

    assert check_personid_papers()
    tortoise()
    assert check_results()


def safe_merger():
    from invenio.legacy.bibauthorid.merge import merge_static
    from invenio.legacy.bibauthorid.rabbit import rabbit
    from invenio.legacy.bibauthorid.personid_maintenance import check_personid_papers \
                                                 , check_results \
                                                 , check_merger \
                                                 , repair_personid \
                                                 , copy_personids \
                                                 , compare_personids

    assert check_results()
    if not check_personid_papers():
        rabbit([])
        repair_personid()
        rabbit([])

    assert check_personid_papers()
    copy_personids()
    merge_static()
    assert check_personid_papers()
    assert check_merger()
    compare_personids("/tmp/merge_diff")


def test_accuracy():
    from invenio.legacy.bibauthorid.tortoise import tortoise
    from invenio.legacy.bibauthorid.rabbit import rabbit
    from invenio.legacy.bibauthorid.personid_maintenance import check_personid_papers \
                                                 , check_results \
                                                 , repair_personid
    from invenio.legacy.bibauthorid.merge import matched_claims

    if not check_personid_papers():
        rabbit([])
        repair_personid()
        rabbit([])

    assert check_personid_papers()
    tortoise(pure=True)
    assert check_results()

    return matched_claims()

