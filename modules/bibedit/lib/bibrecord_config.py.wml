## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

#include "configbis.wml"

### CONFIGURATION OPTIONS FOR BIBRECORD LIBRARY

#0: Parse Warning
"""Configuration for module bibrecord"""

cfg_marc21_dtd = "<ETCDIR>/bibedit/MARC21slim.dtd"

cfg_bibrecord_warning_msgs = {
    0: '' ,
    1: 'WARNING: tag missing for field(s)\nValue stored with tag \'000\'',
    2: 'WARNING: bad range for tags (tag must be in range 001-999)\nValue stored with tag \'000\'',
    3: 'WARNING: Missing atributte \'code\' for subfield\nValue stored with code \'\'',
    4: 'WARNING: Missing attributte \'ind1\'\n Value stored with ind1 = \'\'',
    5: 'WARNING: Missing attributte \'ind2\'\n Value stored with ind2 = \'\'',
    6: 'Import Error\n',
    7: 'WARNING: value expected of type string.',
    8: 'WARNING: empty datafield',
    98:'WARNING: problems importing cdsware',
    99: 'Document not well formed'
    } # Dictionary of warning messages

cfg_bibrecord_default_verbose_level=0 #Verbose level to be used in the creation of records
cfg_bibrecord_default_correct=0 #Correct (0/1) to be used in the creation of records
cfg_bibrecord_parsers_available = [0,1,2] #parsers available
                                          # 0 - minidom; 1-is4suite; 2-pyRXP
