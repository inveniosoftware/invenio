## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
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

pylibdir=$(libdir)/python/cdsware

pylib_DATA = access_control_engine.py access_control_config.py access_control_admin.py webaccessadmin_lib.py external_authentication.py

EXTRA_DIST = access_control_engine.py access_control_config.py.wml access_control_admin.py webaccessadmin_lib.py external_authentication.py

CLEANFILES = *~ *.tmp *.pyc

access_control_config.py: access_control_config.py.wml $(top_srcdir)/config/config.wml $(top_builddir)/config/configbis.wml
	$(WML) -o $@ $<
