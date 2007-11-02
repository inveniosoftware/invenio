# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibUpload Engine configuration.
"""

__revision__ = "$Id$"

from invenio.config import tmpdir

CFG_BIBUPLOAD_CONTROLFIELD_TAGS = ['001', '002', '003', '004',
                                   '005', '006', '007', '008']

CFG_BIBUPLOAD_SPECIAL_TAGS = ['FMT', 'FFT']

CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS = ('/tmp', '/home', '/afs', tmpdir)

CFG_BIBUPLOAD_REFERENCE_TAG = '999'

CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG = '970__a' # useful for matching when
                                            # our records come from an
                                            # external digital library
                                            # system

CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG = '035__a' # useful for matching when
                                            # we harvest stuff via OAI
                                            # that we do not want to
                                            # reexport via Invenio
                                            # OAI; so records may have
                                            # only the source OAI ID
                                            # stored in this tag (kind
                                            # of like external system
                                            # number too)

CFG_BIBUPLOAD_STRONG_TAGS = ['964'] # The list of tags that are strong
                                    # enough to resist the replace
                                    # mode.  Useful for tags that
                                    # might be created from an
                                    # external non-metadata-like
                                    # source, e.g. the information
                                    # about the number of copies left.
