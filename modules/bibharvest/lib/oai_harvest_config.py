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

"""OAI Harvest Configuration."""

__revision__ = "$Id$"

## CFG_OAI_POSSIBLE_POSTMODES -- list of possible modes available for
## OAI harvest post-processing
CFG_OAI_POSSIBLE_POSTMODES = [\
         ["h", "harvest only (h)"], \
         ["h-c", "harvest and convert (h-c)"], \
         ["h-u", "harvest and upload (h-u)"], \
         ["h-c-u", "harvest, convert and upload (h-c-u)"], \
         ["h-c-f-u", "harvest, convert, filter, upload (h-c-f-u)"], \
         ["h-c-e-u", "harvest, convert, extract, upload (h-c-e-u)"], \
         ["h-c-e-f-u", "harvest, convert, extract, filter, upload (h-c-e-f-u)"]]
