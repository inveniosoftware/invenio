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

lispimagedir = $(libdir)/lisp/cdsware
lispimage_DATA = webstat.clisp.mem webstat.cmucl.core webstat.sbcl.core

FILESLISP   = $(wildcard $(srcdir)/*.lisp)
EXTRA_DIST = $(FILESLISP:$(srcdir)/%=%)
CLEANFILES = $(lispimage_DATA) *~ *.tmp *.pyc *.fas *.fasl *.lib *.x86f *.mem *.core

webstat.clisp.mem: $(FILESLISP)
	if [ -x "${CLISP}" ]; then \
	    clisp -q -x "(progn (load \"load.lisp\")(saveinitmem \"webstat.clisp.mem\"))"; \
        else \
            echo "Warning: cannot find CLISP, hoping you have CMUCL or SBCL instead."; \
        fi

webstat.cmucl.core: $(FILESLISP)
	if [ -x "${CMUCL}" ]; then \
	    lisp -quiet -batch -eval "(progn (load \"load.lisp\")(ext:save-lisp \"webstat.cmucl.core\"))"; \
        else \
            echo "Warning: cannot find CMUCL, hoping you have CLISP or SBCL instead."; \
        fi

webstat.sbcl.core: $(FILESLISP)
	if [ -x "${SBCL}" ]; then \
	    sbcl --noinform --disable-debugger --eval "(progn (load \"load.lisp\")(sb-ext:save-lisp-and-die \"webstat.sbcl.core\"))"; \
        else \
            echo "Warning: cannot find SBCL, hoping you have CLISP or CMUCL instead."; \
        fi


