## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

pylibdir = $(libdir)/python/invenio

pylib_DATA = webstat.py \
			 webstat_config.py \
             webstat_templates.py \
             webstat_engine.py \
             webstatadmin.py \
             webstat_regression_tests.py

lispimagedir = $(libdir)/lisp/invenio
lispimage_DATA = webstat.clisp.mem webstat.cmucl.core webstat.sbcl.core

FILESLISP   = load.lisp \
              webstatlib.lisp
EXTRA_DIST = $(pylib_DATA) $(FILESLISP)
CLEANFILES = $(lispimage_DATA) *~ *.tmp *.pyc *.fas *.fasl *.lib *.x86f *.mem *.core

webstat.clisp.mem: $(FILESLISP)
	if [ -x "${CLISP}" ]; then \
             (cwd=`pwd`; cd $(srcdir) && \
             ${CLISP} -q -x "(progn (load \"load.lisp\")(saveinitmem \"$${cwd}/webstat.clisp.mem\"))"); \
        else \
            echo "Warning: cannot find CLISP, hoping you have CMUCL or SBCL instead."; \
            touch webstat.clisp.mem; \
        fi

webstat.cmucl.core: $(FILESLISP)
	if [ -x "${CMUCL}" ]; then \
            (cwd=`pwd`; cd $(srcdir) && \
             ${CMUCL} -quiet -batch -eval "(progn (load \"load.lisp\")(ext:save-lisp \"$${cwd}/webstat.cmucl.core\"))"); \
        else \
            echo "Warning: cannot find CMUCL, hoping you have CLISP or SBCL instead."; \
            touch webstat.cmucl.core; \
        fi

webstat.sbcl.core: $(FILESLISP)
	if [ -x "${SBCL}" ]; then \
           (cwd=`pwd`; cd $(srcdir) && \
            ${SBCL} --noinform --eval "(progn (load \"load.lisp\")(sb-ext:save-lisp-and-die \"$${cwd}/webstat.sbcl.core\"))"); \
        else \
            echo "Warning: cannot find SBCL, hoping you have CLISP or CMUCL instead."; \
            touch webstat.sbcl.core; \
        fi
