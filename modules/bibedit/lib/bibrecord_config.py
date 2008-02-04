## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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

### CONFIGURATION OPTIONS FOR BIBRECORD LIBRARY

"""bibrecord configuration"""

__revision__ = "$Id$"

from invenio.config import etcdir

# location of the MARC21 DTD file:
CFG_MARC21_DTD = "%s/bibedit/MARC21slim.dtd" % etcdir

# pylint: disable-msg=C0301

# internal dictionary of warning messages:
CFG_BIBRECORD_WARNING_MSGS = {
    0: '' ,
    1: 'WARNING: tag missing for field(s)\nValue stored with tag \'000\'',
    2: 'WARNING: bad range for tags (tag must be in range 001-999)\nValue stored with tag \'000\'',
    3: 'WARNING: Missing atributte \'code\' for subfield\nValue stored with code \'\'',
    4: 'WARNING: Missing attributte \'ind1\'\n Value stored with ind1 = \'\'',
    5: 'WARNING: Missing attributte \'ind2\'\n Value stored with ind2 = \'\'',
    6: 'Import Error\n',
    7: 'WARNING: value expected of type string.',
    8: 'WARNING: empty datafield',
    98:'WARNING: problems importing invenio',
    99: 'Document not well formed'
    } 

# verbose level to be used when creating records from XML: (0=least, ..., 9=most)
CFG_BIBRECORD_DEFAULT_VERBOSE_LEVEL = 0

# correction level to be used when creating records from XML: (0=no, 1=yes)
CFG_BIBRECORD_DEFAULT_CORRECT = 0

# XML parsers available: (0=minidom, 1=4suite, 2=PyRXP)
CFG_BIBRECORD_PARSERS_AVAILABLE = [0, 1, 2]                                           
