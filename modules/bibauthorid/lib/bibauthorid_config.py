# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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


# Current version of the framework
VERSION = '0.1.11'

# make sure current directory is importable
FILE_PATH = osp.dirname(osp.abspath(__file__))

# Permission definitions as in actions defined in roles
CMP_ADMIN_ROLE = "CMPadmin"
CMP_USER_ROLE = "CMPusers"
CMP_VIEW_PID_UNIVERSE = 'cmp_view_pid_universe'
CMP_CHANGE_OWN_DATA = 'cmp_change_own_data'
CMP_CHANGE_OTHERS_DATA = 'cmp_change_others_data'
CMP_CLAIM_OWN_PAPERS = 'cmp_claim_own_papers'
CMP_CLAIM_OTHERS_PAPERS = 'cmp_claim_others_papers'

if FILE_PATH not in sys.path:
    sys.path.insert(0, FILE_PATH)

# Max number of threads to parallelize sql queryes in table_utils updates
PERSONID_SQL_MAX_THREADS = 4

# Threshold for connecting a paper to a person: BCTKD are the papers from the 
# backtracked RAs found searching back for the papers already connected to the 
# persons, NEW is for the newly found one
PERSONID_MIN_P_FROM_BCTKD_RA = 0.5
PERSONID_MIN_P_FROM_NEW_RA = 0.5

# Minimum threshold for the compatibility list of persons to an RA: if no RA 
# is more compatible that that it will create a new person
PERSONID_MAX_COMP_LIST_MIN_TRSH = 0.5

#Create_new_person flags thresholds
PERSONID_CNP_FLAG_1 = 0.75
PERSONID_CNP_FLAG_MINUS1 = 0.5

# update_personid_from_algorithm  person_paper_list for get_person_ra call 
# minimum flag
PERSONID_UPFA_PPLMF = -1


#Tables Utils debug output
TABLES_UTILS_DEBUG = True

# Is the authorid algorithm allowed to attach a virtual author to multiple
# real authors in the last run of the orphan processing?
ATTACH_VA_TO_MULTIPLE_RAS = False
# Log Level for the message output.
# Log Levels are defined in the Python logging system
# 0 - 50 (log everything - log exceptions)
LOG_LEVEL = 25

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

## STANDALONE defines if the algorithm is run within the environment of
## Invenio/Inspire or if it is used individually (e.g. Grid usage)
STANDALONE = False

try:
    import dbquery
except ImportError, err:
    STANDALONE = True
    LOGGER.warning('Bibauthorid is running in standalone mode.\n'
                   '-> Access to the database is not supported.')
