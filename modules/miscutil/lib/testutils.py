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

"""
Helper functions for building test suites.
"""

import unittest, sys

from urllib import urlencode

from invenio.config import weburl

def warn_user_about_tests():
    """ Put a standard warning about running tests that might modify
    user data"""
    
    # Provide a command line option to avoid having to type the
    # confirmation every time during development.
    if '--yes-i-know' in sys.argv:
        return

    print """\
----------------------------------------------------------------------

ATTENTION:

  this suite needs the application to be in 'demo' mode, which WILL
  ERASE YOUR DATA PERMANENTLY.

  To set it in demo mode, run:

    $ make drop-tables
    $ make create-tables
    $ make create-demo-site
    $ make load-demo-records
  
----------------------------------------------------------------------
    """

    # readline provides a nicer input support to the user, but is
    # sometimes unavailable.
    try:
        import readline
    except ImportError:
        pass

    answer = raw_input('Please confirm by typing "yes I know": ')
    if answer != 'yes I know':
        print "Test aborted by user."
        raise SystemExit(0)

    return

def warn_user_about_tests_and_run(testsuite):
    """ Convenience function to embed in test suites """
    warn_user_about_tests()
    unittest.TextTestRunner(verbosity=2).run(testsuite)
    

def make_suite(*test_cases):
    """ Build up a test suite given separate test cases"""
    
    return unittest.TestSuite([unittest.makeSuite(case, 'test')
                               for case in test_cases])

def make_url(path, **kargs):
    """ Helper to generate an absolute invenio URL with query
    arguments"""
    
    url = weburl + path
    
    if kargs:
        url += '?' + urlencode(kargs, doseq=True)

    return url

