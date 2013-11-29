## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""BibMatch Configuration."""
import logging
import logging.handlers
from invenio.config import CFG_TMPDIR

def get_logger(logname, logfile):
    """
    Intializes and returns a logging object used in BibMatch.
    """
    logger = logging.getLogger(logname)
    logger.setLevel(logging.INFO)
    log_handler = logging.handlers.RotatingFileHandler(logfile, 'a', 10*1024*1024, 100)
    log_formatter = logging.Formatter("%(asctime)s -- [%(levelname)s] %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    return logger

CFG_LOGFILE = "%s/bibmatch.log" % (CFG_TMPDIR,)
try:
    CFG_BIBMATCH_LOGGER = get_logger("bibmatch_info", CFG_LOGFILE)
except IOError:
    CFG_LOGFILE = "/tmp/bibmatch.log"
    CFG_BIBMATCH_LOGGER = get_logger("bibmatch_info", CFG_LOGFILE)
## CFG_BIBMATCH_VALIDATION_MATCHING_MODES - list of supported comparison modes
## during record validation.
CFG_BIBMATCH_VALIDATION_MATCHING_MODES = ['title', 'author', 'identifier', 'date', 'normal']

## CFG_BIBMATCH_VALIDATION_RESULT_MODES - list of supported result modes
## during record validation.
CFG_BIBMATCH_VALIDATION_RESULT_MODES = ['normal', 'final', 'joker', 'fuzzy']

## CFG_BIBMATCH_VALIDATION_COMPARISON_MODES - list of supported parsing modes
## during record validation.
CFG_BIBMATCH_VALIDATION_COMPARISON_MODES = ['strict', 'normal', 'lazy', 'ignored']
