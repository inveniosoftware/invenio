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

"""
bibauthorid_config
    Part of the framework responsible for supplying configuration options used
    by different parts of the framework. Note, however, that it's best to
    declare any configuration options for the modules within themselves.
"""

# To refactor: Local variables should also start with CFG.

try:
    from invenio.access_control_config import SUPERADMINROLE
except ImportError:
    SUPERADMINROLE = "Superadmin"

GLOBAL_CONFIG = True

try:
    from invenio.config import CFG_BIBAUTHORID_PERSONID_SQL_MAX_THREADS, \
        CFG_BIBAUTHORID_MAX_PROCESSES, \
        CFG_BIBAUTHORID_EXTERNAL_CLAIMED_RECORDS_KEY, \
        CFG_BIBAUTHORID_ENABLED, \
        CFG_BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE, \
        CFG_INSPIRE_SITE, \
        CFG_ADS_SITE, \
        CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS, \
        CFG_SITE_NAME

except ImportError:
    GLOBAL_CONFIG = False

# Current version of the framework
VERSION = '1.1.2'

# Permission definitions as in actions defined in roles
CLAIMPAPER_ADMIN_ROLE = "claimpaperoperators"
CLAIMPAPER_USER_ROLE = "claimpaperusers"
CMP_ENABLED_ROLE = "paperclaimviewers"
CHP_ENABLED_ROLE = "paperattributionviewers"
AID_LINKS_ROLE = "paperattributionlinkviewers"

CLAIMPAPER_VIEW_PID_UNIVERSE = 'claimpaper_view_pid_universe'
CLAIMPAPER_CHANGE_OWN_DATA = 'claimpaper_change_own_data'
CLAIMPAPER_CHANGE_OTHERS_DATA = 'claimpaper_change_others_data'
CLAIMPAPER_CLAIM_OWN_PAPERS = 'claimpaper_claim_own_papers'
CLAIMPAPER_CLAIM_OTHERS_PAPERS = 'claimpaper_claim_others_papers'

# Number of persons in a search result for which the first five papers will be shown
PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT = 10

CMPROLESLCUL = {'guest': 0,
                CLAIMPAPER_USER_ROLE: 25,
                CLAIMPAPER_ADMIN_ROLE: 50,
                SUPERADMINROLE: 50}

# Number of persons that will be shown per page in search results.
PERSONS_PER_PAGE = 5
# Max amount of recent papers shown to the user
MAX_NUM_SHOW_PAPERS = 5

# BibAuthorId functionalities should always be enabled for Inspire.
if CFG_INSPIRE_SITE:
    CFG_BIBAUTHORID_ENABLED = True

# Globally enable AuthorID Interfaces.
#     If False: No guest, user or operator will have access to the system.
if GLOBAL_CONFIG:
    AID_ENABLED = CFG_BIBAUTHORID_ENABLED
else:
    AID_ENABLED = True

# Enable AuthorID information on the author pages.
if GLOBAL_CONFIG:
    AID_ON_AUTHORPAGES = CFG_BIBAUTHORID_ENABLED
else:
    AID_ON_AUTHORPAGES = True

# Limit the disambiguation to a specific collections. Leave empty for all
# Collections are to be defined as a list of strings
# Special for ADS: Focus on ASTRONOMY collection
if GLOBAL_CONFIG and CFG_ADS_SITE:
    LIMIT_TO_COLLECTIONS = ["ASTRONOMY"]
elif CFG_INSPIRE_SITE:
    LIMIT_TO_COLLECTIONS = ['HEP']
else:
    LIMIT_TO_COLLECTIONS = list()

# User info keys for externally claimed records
# e.g. for arXiv SSO: ["external_arxivids"]
if GLOBAL_CONFIG and CFG_BIBAUTHORID_EXTERNAL_CLAIMED_RECORDS_KEY:
    EXTERNAL_CLAIMED_RECORDS_KEY = CFG_BIBAUTHORID_EXTERNAL_CLAIMED_RECORDS_KEY
else:
    EXTERNAL_CLAIMED_RECORDS_KEY = []

# Lists all filters that are valid to filter the export by.
# An example is 'arxiv' to return only papers with a 037 entry named arxiv
VALID_EXPORT_FILTERS = ["arxiv"]

# Max number of threads to parallelize sql queryes in table_utils updates
if GLOBAL_CONFIG and CFG_BIBAUTHORID_PERSONID_SQL_MAX_THREADS:
    PERSONID_SQL_MAX_THREADS = CFG_BIBAUTHORID_PERSONID_SQL_MAX_THREADS
else:
    PERSONID_SQL_MAX_THREADS = 12

# Max number of processes spawned by the disambiguation algorithm
if GLOBAL_CONFIG and CFG_BIBAUTHORID_MAX_PROCESSES:
    BIBAUTHORID_MAX_PROCESSES = CFG_BIBAUTHORID_MAX_PROCESSES
else:
    BIBAUTHORID_MAX_PROCESSES = 12

WEDGE_THRESHOLD = 0.70


# Rabbit use or ignore external ids
RABBIT_USE_EXTERNAL_IDS = True

# Collect and use in rabbit external ids INSPIREID
COLLECT_EXTERNAL_ID_INSPIREID = CFG_INSPIRE_SITE
if CFG_INSPIRE_SITE:
    RABBIT_EXTERNAL_IDS_TO_USE = ['InspireID', 'OrcidID']
else:
    RABBIT_EXTERNAL_IDS_TO_USE = list()

# Threshold to the determine whether a person' records will be cached during the query.
EXT_ID_CACHE_THRESHOLD = 50

# Force rabbit to cache entire marc tables instead of querying db if dealing with more
# then threshold papers
RABBIT_USE_CACHED_GET_GROUPED_RECORDS = True
RABBIT_USE_CACHED_GET_GROUPED_RECORDS_THRESHOLD = 5000


# Cache the personid table for performing exact name searches?
RABBIT_USE_CACHED_PID = True

# Collect (external ids from and store them as person attributes) _only_ from manually claimed papers?
# If false, collects even from non claimed papers.
LIMIT_EXTERNAL_IDS_COLLECTION_TO_CLAIMED_PAPERS = True


# BibAuthorID debugging options

# This flag triggers the basic output.
DEBUG_OUTPUT = False

DEBUG_UPDATE_STATUS_THREAD_SAFE = False
DEBUG_LOG_TO_PIDFILE = False

# The following options trigger the output for parts of
# bibauthorid which normally generate too much output
DEBUG_NAME_COMPARISON_OUTPUT = False
DEBUG_METADATA_COMPARISON_OUTPUT = False
DEBUG_WEDGE_OUTPUT = False
DEBUG_PROCESS_PEAK_MEMORY = False

# Keep in mind that you might use an assert instead of this option.
# Use DEBUG_CHECKS to guard heavy computations in order to make
# their use explicit.
DEBUG_CHECKS = False

TORTOISE_FILES_PATH = '/opt/tortoise_cache/'

# force skip ui arxiv stub page (specific for inspire)
BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE = True

if GLOBAL_CONFIG and CFG_INSPIRE_SITE:
    BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE = CFG_BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE
else:
    BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE = True

# URL for the remote INSPIRE login that shall be shown on (arXiv stub page.)
BIBAUTHORID_CFG_INSPIRE_LOGIN = ""

if GLOBAL_CONFIG and CFG_INSPIRE_SITE:
    BIBAUTHORID_CFG_INSPIRE_LOGIN = 'https://arxiv.org/inspire_login'
# Shall we send from local:ly defined eMail address or from the users one
# when we send out a ticket? Default is True -> send with user's email
TICKET_SENDING_FROM_USER_EMAIL = True

# Regexp for the names separation
NAMES_SEPARATOR_CHARACTER_LIST = ",;.=\-\(\)"
SURNAMES_SEPARATOR_CHARACTER_LIST = ",;"

# create new profile required
CREATE_NEW_PERSON = -3

# Dict which lists which external identifiers  can be stored on a person profile page, and maps them
# with their representation in aidPERSONIDDATA
PERSONID_EXTERNAL_IDENTIFIER_MAP = {'Inspire': 'INSPIREID', 'Orcid': 'ORCID'}

# HepNames whitelist of identifiers displayed on user profiles.
# Identifiers should be in lowercase and the value represents the priority.
# Priority values are ordered: smallest first and largest last.
# {} signifies that all identifiers should be displayed.
# e.g. { "arxiv": 1 } signals arxiv identifiers with highest priority.
PROFILE_IDENTIFIER_WHITELIST = {
    "bai": 1,
    "inspire": 2,
    "orcid": 3,
    "googlescholar": 4,
    "arxiv": 5
}

# Used to define URL mappings for identifiers in lowercase
# Identifiers will be placed where {0} is found in the mapping.
# e.g. { "orcid": "https://orcid.org/{0}"}
PROFILE_IDENTIFIER_URL_MAPPING = {
    "bai": "http://inspirehep.net/author/profile/{0}",
    "orcid": "https://orcid.org/{0}"
}

NON_EMPTY_PERSON_TAGS = ['canonical_name']

QGRAM_LEN = 2
MATCHING_QGRAMS_PERCENTAGE = 0.8
MAX_T_OCCURANCE_RESULT_LIST_CARDINALITY = 35
MIN_T_OCCURANCE_RESULT_LIST_CARDINALITY = 10

# List that contains the existing remote systems that a user can logged in via them in Inspire
CFG_BIBAUTHORID_EXISTING_REMOTE_LOGIN_SYSTEMS = ['arXiv', 'orcid']

if GLOBAL_CONFIG and not set(CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS) <= set(CFG_BIBAUTHORID_EXISTING_REMOTE_LOGIN_SYSTEMS):
    raise Exception(
        "Wrong configuration!!! CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS must be a subset of %s" %
        str(CFG_BIBAUTHORID_EXISTING_REMOTE_LOGIN_SYSTEMS))

CFG_BIBAUTHORID_REMOTE_LOGIN_SYSTEMS_IDENTIFIERS = {'arxivid': '037', 'doi': 'doi'}
CFG_BIBAUTHORID_REMOTE_LOGIN_SYSTEMS_LINKS = {'arXiv': 'invalid', 'invalid': 'invalid'}
CFG_BIBAUTHORID_REMOTE_LOGIN_SYSTEMS_IDENTIFIER_TYPES = {'arXiv': 'arxivid', 'orcid': 'doi'}

# For Inspire,the value of CFG_SITE_NAME is extensively used for a different purpose.
# This keeps the configuration neutral of implementations.
BIBAUTHORID_CFG_SITE_NAME = ""

if GLOBAL_CONFIG and CFG_INSPIRE_SITE:
    BIBAUTHORID_CFG_SITE_NAME = "INSPIRE"
else:
    BIBAUTHORID_CFG_SITE_NAME = CFG_SITE_NAME
