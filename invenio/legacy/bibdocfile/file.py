# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

raise ImportError, """file.py module of Invenio has been superseeded by bibdocfile.py.
In order to port your code to the new bibdocfile note that:
    * the methods have been renamed from camelCode to underscore_standard
    * addFilesNewVersion and addFilesNewFormat are now singular:
        i.e. add_file_new_version and add_file_new_format. You will have
        to call them each time for every single file.
    * docnames are used everywhere in place of docids
    """
