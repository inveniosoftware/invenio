## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""BibEdit Configuration."""

__revision__ = "$Id$"

## When a user edits a record, this record is locked to prevent other
## users to edit it at the same time.  After how many seconds the
## locked record will be again free for other people to edit?
CFG_BIBEDIT_TIMEOUT = 3600 # 1 hour

## Beginning of the name of the temporary files:
CFG_BIBEDIT_TMPFILENAMEPREFIX = "bibedit_record"
