# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013 CERN.
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

'''
Forward to ArXiv.org source code
'''

from __future__ import unicode_literals

from invenio.modules.formatter.api import get_tag_from_name

#Maximal time to keep the stored XML Service doucment before reloading it in sec
CFG_BIBSWORD_SERVICEDOCUMENT_UPDATE_TIME = 3600

#Default submission status
CFG_SUBMISSION_STATUS_SUBMITTED = "submitted"
CFG_SUBMISSION_STATUS_PUBLISHED = "published"
CFG_SUBMISSION_STATUS_ONHOLD = "onhold"
CFG_SUBMISSION_STATUS_REMOVED = "removed"

CFG_SUBMIT_ARXIV_INFO_MESSAGE = "Submitted from Invenio to arXiv by %s, on %s, as %s"
CFG_DOCTYPE_UPLOAD_COLLECTION = 'PUSHED_TO_ARXIV'


# report number:
marc_tag_main_report_number = get_tag_from_name('primary report number')
if marc_tag_main_report_number:
    CFG_MARC_REPORT_NUMBER = marc_tag_main_report_number
else:
    CFG_MARC_REPORT_NUMBER = '037__a'

# title:
marc_tag_title = get_tag_from_name('title')
if marc_tag_title:
    CFG_MARC_TITLE = marc_tag_title
else:
    CFG_MARC_TITLE = '245__a'

# author name:
marc_tag_author = get_tag_from_name('first author name')
if marc_tag_author:
    CFG_MARC_AUTHOR_NAME = marc_tag_author
else:
    CFG_MARC_AUTHOR_NAME = '100__a'

# author affiliation
marc_tag_author_affiliation = get_tag_from_name('first author affiliation')
if marc_tag_author_affiliation:
    CFG_MARC_AUTHOR_AFFILIATION = marc_tag_author_affiliation
else:
    CFG_MARC_AUTHOR_AFFILIATION = '100__u'

# contributor name:
marc_tag_contributor_name = get_tag_from_name('additional author name')
if marc_tag_contributor_name:
    CFG_MARC_CONTRIBUTOR_NAME = marc_tag_contributor_name
else:
    CFG_MARC_CONTRIBUTOR_NAME = '700__a'

# contributor affiliation:
marc_tag_contributor_affiliation = get_tag_from_name('additional author affiliation')
if marc_tag_contributor_affiliation:
    CFG_MARC_CONTRIBUTOR_AFFILIATION = marc_tag_contributor_affiliation
else:
    CFG_MARC_CONTRIBUTOR_AFFILIATION = '700__u'

# abstract:
marc_tag_abstract = get_tag_from_name('main abstract')
if marc_tag_abstract:
    CFG_MARC_ABSTRACT = marc_tag_abstract
else:
    CFG_MARC_ABSTRACT = '520__a'

# additional report number
marc_tag_additional_report_number = get_tag_from_name('additional report number')
if marc_tag_additional_report_number:
    CFG_MARC_ADDITIONAL_REPORT_NUMBER = marc_tag_additional_report_number
else:
    CFG_MARC_ADDITIONAL_REPORT_NUMBER = '088__a'

# doi
marc_tag_doi = get_tag_from_name('doi')
if marc_tag_doi:
    CFG_MARC_DOI = marc_tag_doi
else:
    CFG_MARC_DOI = '909C4a'

# journal code
marc_tag_journal_ref_code = get_tag_from_name('journal code')
if marc_tag_journal_ref_code:
    CFG_MARC_JOURNAL_REF_CODE = marc_tag_journal_ref_code
else:
    CFG_MARC_JOURNAL_REF_CODE = '909C4c'

# journal reference title
marc_tag_journal_ref_title = get_tag_from_name('journal title')
if marc_tag_journal_ref_title:
    CFG_MARC_JOURNAL_REF_TITLE = marc_tag_journal_ref_title
else:
    CFG_MARC_JOURNAL_REF_TITLE = '909C4p'

# journal reference page
marc_tag_journal_ref_page = get_tag_from_name('journal page')
if marc_tag_journal_ref_page:
    CFG_MARC_JOURNAL_REF_PAGE = marc_tag_journal_ref_page
else:
    CFG_MARC_JOURNAL_REF_PAGE = '909C4v'

# journal reference year
marc_tag_journal_ref_year = get_tag_from_name('journal year')
if marc_tag_journal_ref_year:
    CFG_MARC_JOURNAL_REF_YEAR = marc_tag_journal_ref_year
else:
    CFG_MARC_JOURNAL_REF_YEAR = '909C4y'

# comment
marc_tag_comment = get_tag_from_name('comment')
if marc_tag_comment:
    CFG_MARC_COMMENT = marc_tag_comment
else:
    CFG_MARC_COMMENT = '500__a'

# internal note field
marc_tag_internal_note = get_tag_from_name('internal notes')
if marc_tag_internal_note:
    CFG_MARC_RECORD_SUBMIT_INFO = marc_tag_internal_note
else:
    CFG_MARC_RECORD_SUBMIT_INFO = '595__a'
