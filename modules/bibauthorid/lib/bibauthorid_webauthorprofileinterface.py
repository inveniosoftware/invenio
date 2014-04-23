# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

from invenio.bibauthorid_config import CLAIMPAPER_ADMIN_ROLE  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_config import CLAIMPAPER_USER_ROLE  # emitting #pylint: disable-msg=W0611

# import invenio.bibauthorid_webapi as webapi
# import invenio.bibauthorid_config as bconfig

from invenio.bibauthorid_frontinterface import get_bibrefrec_name_string  # emitting #pylint: disable-msg=W0611

from invenio.bibauthorid_webapi import search_person_ids_by_name  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import get_papers_by_person_id  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_names_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_existing_authors  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_authors_by_name  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_frontinterface import get_confirmed_papers_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_title_of_paper  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_orcid_id_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_arxiv_papers_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_existing_authors  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import get_person_redirect_link  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import author_has_papers  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import is_valid_canonical_id  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import is_valid_bibref  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import get_person_id_from_paper  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import get_person_id_from_canonical_id  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_webapi import get_hepnames  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_names_count_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_canonical_name_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_coauthors_of_author  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import remove_empty_authors  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_dbinterface import get_papers_of_author
from invenio.bibauthorid_dbinterface import get_pid_to_canonical_name_map
from invenio.bibauthorid_dbinterface import get_names_to_records_of_author

from invenio.bibauthorid_name_utils import create_normalized_name  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_name_utils import split_name_parts  # emitting #pylint: disable-msg=W0611
# from invenio.bibauthorid_config import CLAIMPAPER_CLAIM_OTHERS_PAPERS
from invenio.bibauthorid_config import AID_ENABLED  # emitting #pylint: disable-msg=W0611
from invenio.bibauthorid_config import AID_ON_AUTHORPAGES  # emitting #pylint: disable-msg=W0611

from invenio import bibauthorid_searchinterface as pt  # emitting #pylint: disable-msg=W0611


def gathered_names_by_personid(pid):
    return [p[0] for p in get_names_count_of_author(pid)]
