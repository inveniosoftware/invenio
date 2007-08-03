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

__revision__ = "$Id$"

from distutils.core import setup
from distutils.extension import Extension
from Pyrex.Distutils import build_ext
#from Cython.Distutils import build_ext

setup(
    name = 'intbitset',
    version = '0.1',
    description = 'Fast BitSet C extension to hold unsigned integer',
    author = 'CDS',
    author_email = 'cds.support@cern.ch',
    url = 'http://cdsware.cern.ch',
    ext_modules=[
        Extension("invenio.intbitset", ["intbitset.pyx", "intbitset_impl.c"], extra_compile_args=['-O3']),
    ],
    cmdclass = {'build_ext': build_ext},
)
