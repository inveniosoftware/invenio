# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
bibauthorid_config
    Part of the framework responsible for supplying configuration options used
    by different parts of the framework. Note, however, that it's best to
    declare any configuration options for the modules within themselves.
"""

import logging.handlers
import sys
import os.path as osp

try:
    from invenio.access_control_config import SUPERADMINROLE
except ImportError:
    SUPERADMINROLE = "Superadmin"


GLOBAL_CONFIG = True

try:
    from invenio.config import CFG_BIBAUTHORID_PERSONID_SQL_MAX_THREADS, \
        CFG_BIBAUTHORID_MAX_PROCESSES, \
        CFG_BIBAUTHORID_PERSONID_MIN_P_FROM_BCTKD_RA, \
        CFG_BIBAUTHORID_PERSONID_MIN_P_FROM_NEW_RA, \
        CFG_BIBAUTHORID_PERSONID_MAX_COMP_LIST_MIN_TRSH, \
        CFG_BIBAUTHORID_PERSONID_MAX_COMP_LIST_MIN_TRSH_P_N, \
        CFG_BIBAUTHORID_EXTERNAL_CLAIMED_RECORDS_KEY, \
        CFG_BIBAUTHORID_ATTACH_VA_TO_MULTIPLE_RAS , \
        CFG_BIBAUTHORID_ENABLED, \
        CFG_BIBAUTHORID_ON_AUTHORPAGES, \
        CFG_BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE, \
        CFG_INSPIRE_SITE

except ImportError:
    GLOBAL_CONFIG = False


# Current version of the framework
VERSION = '1.1.1'

# make sure current directory is importable
FILE_PATH = osp.dirname(osp.abspath(__file__))

if FILE_PATH not in sys.path:
    sys.path.insert(0, FILE_PATH)

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

#Number of persons in a search result for which the first five papers will be shown
PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT = 10

CMPROLESLCUL = {'guest': 0,
                CLAIMPAPER_USER_ROLE: 25,
                CLAIMPAPER_ADMIN_ROLE: 50,
                SUPERADMINROLE: 50}

# Globally enable AuthorID Interfaces.
#     If False: No guest, user or operator will have access to the system.
if GLOBAL_CONFIG:
    AID_ENABLED = CFG_BIBAUTHORID_ENABLED
else:
    AID_ENABLED = True


# Enable AuthorID information on the author pages.
if GLOBAL_CONFIG:
    AID_ON_AUTHORPAGES = CFG_BIBAUTHORID_ON_AUTHORPAGES
else:
    AID_ON_AUTHORPAGES = True

# Limit the disambiguation to a specific collections. Leave empty for all
# Collections are to be defined as a list of strings
LIMIT_TO_COLLECTIONS = []

# Exclude documents that are visible in a collection mentioned here:
EXCLUDE_COLLECTIONS = ["HEPNAMES", "INST", "Deleted", "DELETED", "deleted"]

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

# Threshold for connecting a paper to a person: BCTKD are the papers from the
# backtracked RAs found searching back for the papers already connected to the
# persons, NEW is for the newly found one
if GLOBAL_CONFIG and CFG_BIBAUTHORID_PERSONID_MIN_P_FROM_BCTKD_RA:
    PERSONID_MIN_P_FROM_BCTKD_RA = CFG_BIBAUTHORID_PERSONID_MIN_P_FROM_BCTKD_RA
else:
    PERSONID_MIN_P_FROM_BCTKD_RA = 0.5

if GLOBAL_CONFIG and CFG_BIBAUTHORID_PERSONID_MIN_P_FROM_NEW_RA:
    PERSONID_MIN_P_FROM_NEW_RA = CFG_BIBAUTHORID_PERSONID_MIN_P_FROM_NEW_RA
else:
    PERSONID_MIN_P_FROM_NEW_RA = 0.5

# Minimum threshold for the compatibility list of persons to an RA: if no RA
# is more compatible that that it will create a new person
if GLOBAL_CONFIG and CFG_BIBAUTHORID_PERSONID_MAX_COMP_LIST_MIN_TRSH:
    PERSONID_MAX_COMP_LIST_MIN_TRSH = CFG_BIBAUTHORID_PERSONID_MAX_COMP_LIST_MIN_TRSH
else:
    PERSONID_MAX_COMP_LIST_MIN_TRSH = 0.5

if GLOBAL_CONFIG and CFG_BIBAUTHORID_PERSONID_MAX_COMP_LIST_MIN_TRSH_P_N:
    PERSONID_MAX_COMP_LIST_MIN_TRSH_P_N = CFG_BIBAUTHORID_PERSONID_MAX_COMP_LIST_MIN_TRSH_P_N
else:
    PERSONID_MAX_COMP_LIST_MIN_TRSH_P_N = 0.5

#personid fast assign papers minimum name threshold: names below will create new persons,
#names over will add the paper to the most compatible one
PERSONID_FAST_ASSIGN_PAPERS_MIN_NAME_TRSH = 0.8

#Create_new_person flags thresholds
PERSONID_CNP_FLAG_1 = 0.75
PERSONID_CNP_FLAG_MINUS1 = 0.5

# update_personid_from_algorithm  person_paper_list for get_person_ra call
# minimum flag
PERSONID_UPFA_PPLMF = -1


# Update/disambiguation process surname list creation method
# Can be either 'mysql' or 'regexp'.
# 'mysql' is inerently slow but accurate, 'regexp' is really really fast, but with potentially
#different results. 'mysql' left in for compatibility.
BIBAUTHORID_LIST_CREATION_METHOD = 'regexp'


#Tables Utils debug output
TABLES_UTILS_DEBUG = False
AUTHORNAMES_UTILS_DEBUG = False

# Is the authorid algorithm allowed to attach a virtual author to multiple
# real authors in the last run of the orphan processing?
if GLOBAL_CONFIG and CFG_BIBAUTHORID_ATTACH_VA_TO_MULTIPLE_RAS:
    ATTACH_VA_TO_MULTIPLE_RAS = CFG_BIBAUTHORID_ATTACH_VA_TO_MULTIPLE_RAS
else:
    ATTACH_VA_TO_MULTIPLE_RAS = False

# Shall we send from locally defined eMail address or from the users one
# when we send out a ticket? Default is True -> send with user's email
TICKET_SENDING_FROM_USER_EMAIL = True
# Log Level for the message output.
# Log Levels are defined in the Python logging system
# 0 - 50 (log everything - log exceptions)
LOG_LEVEL = 30

# Default logging file name
LOG_FILENAME = "job.log"

# tables_utils_config
TABLE_POPULATION_BUNCH_SIZE = 6000

# Max number of authors on a paper to be considered while creating jobs
MAX_AUTHORS_PER_DOCUMENT = 15

# Set limit_authors to true, if papers that are written by collaborations
# or by more than MAX_AUTHORS_PER_DOCUMENT authors shall be excluded
# The default is False.
LIMIT_AUTHORS_PER_DOCUMENT = False

# Regexp for the names separation
NAMES_SEPARATOR_CHARACTER_LIST = ",;.=\-\(\)"
SURNAMES_SEPARATOR_CHARACTER_LIST = ",;"

# Path where all the modules live and which prefix the have.
MODULE_PATH = ("%s/bibauthorid_comparison_functions/aid_cmp_*.py"
               % (FILE_PATH,))

## threshold for adding a va to more than one real authors for
## the add_new_virtualauthor function
REALAUTHOR_VA_ADD_THERSHOLD = 0.449

## parameters for the 'compute real author name' function
CONFIDENCE_THRESHOLD = 0.46
P_THRESHOLD = 0.46
INVERSE_THRESHOLD_DELTA = 0.1

## parameters for the comparison function chain
CONSIDERATION_THRESHOLD = 0.04

## Set up complex logging system:
## - Setup Default logger, which logs to console on critical events only
## - on init call, set up a three-way logging system:
## - 1. Log to console anything ERROR or higher.
## - 2. Log everything LOG_LEVEL or higher to memory and
## - 3. Flush to file in the specified path.

LOGGERS = []
HANDLERS = {}

## Default logger and handler
DEFAULT_HANDLER = logging.StreamHandler()
DEFAULT_LOG_FORMAT = logging.Formatter('%(levelname)-8s %(message)s')
DEFAULT_HANDLER.setFormatter(DEFAULT_LOG_FORMAT)
DEFAULT_HANDLER.setLevel(logging.CRITICAL)

## workaround for the classes to detect that LOGGER is actually an instance
## of type logging.
LOGGER = logging.getLogger("Dummy")
LOGGER.addHandler(DEFAULT_HANDLER)
LOGGER.setLevel(LOG_LEVEL)


## force skip ui arxiv stub page (specific for inspire)
BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE = True

if GLOBAL_CONFIG and CFG_INSPIRE_SITE:
    BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE = CFG_BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE
else:
    BIBAUTHORID_UI_SKIP_ARXIV_STUB_PAGE = True


## URL for the remote INSPIRE login that shall be shown on (arXiv stub page.)
BIBAUTHORID_CFG_INSPIRE_LOGIN = ""


if GLOBAL_CONFIG and CFG_INSPIRE_SITE:
    BIBAUTHORID_CFG_INSPIRE_LOGIN = 'https://arxiv.org/inspire_login'

if not LOGGERS:
    LOGGERS.append(logging.getLogger("Dummy"))
    LOGGERS[0].addHandler(DEFAULT_HANDLER)


def init_logger(logfile=None):
    '''
    Set up specific logger for 3-way logging.

    @param logfile: path to file which will be used for flushing the memory
        log cache.
    @type logfile: string
    '''

    if not logfile:
        return False

    logging.addLevelName(25, "LOG")

    HANDLERS['filelog'] = logging.FileHandler(logfile, mode="w")
    HANDLERS['memlog'] = logging.handlers.MemoryHandler(1000, logging.ERROR,
                                                        HANDLERS['filelog'])
    HANDLERS['console'] = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s -- %(levelname)-8s %(message)s",
                                  "%Y-%m-%d %H:%M:%S")
    HANDLERS['filelog'].setFormatter(formatter)
    HANDLERS['memlog'].setFormatter(formatter)
    HANDLERS['console'].setFormatter(formatter)

    HANDLERS['memlog'].setLevel(LOG_LEVEL)
    HANDLERS['console'].setLevel(logging.ERROR)

    if LOGGERS:
        LOGGERS[:] = []

    LOGGERS.append(logging.getLogger(""))
    LOGGERS[0].setLevel(LOG_LEVEL)
    LOGGERS[0].addHandler(HANDLERS['memlog'])
    LOGGERS[0].addHandler(HANDLERS['console'])


def stop_and_close_logger():
    '''
    Closes and detaches all handlers from the logging instances. Necessary to
    flush the latest contents of the memory handler to file.
    '''
    HANDLERS['memlog'].close()
    HANDLERS['filelog'].close()
    HANDLERS['console'].close()
    LOGGER.removeHandler(HANDLERS['memlog'])
    LOGGER.removeHandler(HANDLERS['console'])

## Logging 'device' used by the classes to write log messages
LOGGER = LOGGERS[0]



