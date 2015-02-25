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

from invenio.config import \
     CFG_SITE_NAME

   ## Description:   function Print_Success_MBI
   ##                This function displays a message telling the user the
   ##             modification has been taken into account
   ## Author:         T.Baron
   ## PARAMETERS:    -

def Print_Success_MBI(parameters, curdir, form, user_info=None):
    """
    This function simply displays a text on the screen, telling the
    user the modification went fine. To be used in the Modify Record
    (MBI) action.
    """
    global rn
    t="<b>Modification completed!</b><br /><br />"
    t+="These modifications on document %s will be processed as quickly as possible and made <br />available on the %s Server</b>" % (rn, CFG_SITE_NAME)
    return t

