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
Check the kwalitee of the CDS Invenio Python code.

Q: What is kwalitee?
A: <http://qa.perl.org/phalanx/kwalitee.html>

Usage: python kwalitee.py <topsrcdir | file1.py file2.py ...>
Examples:
    $ python kwalitee.py ~/src/cds-invenio/
    $ python kwalitee.py ../../websearch/lib/*.py
"""

import os
import sre
import sys
import time

# pylint: disable-msg=C0301
# pylint: disable-msg=C0103

__revision__ = "$Id$"

verbose = 0

def get_list_of_python_code_files(modulesdir, modulename):
    """Return list of Python source code files for MODULENAME in MODULESDIR,
       excluding test files.
    """
    out = []
    # firstly, find out *.py files:
    (dummy, pipe, dummy)= os.popen3("find %s/%s/ -name '*.py'" % (modulesdir, modulename))
    out.extend([filename.strip() for filename in pipe.readlines()])
    pipe.close()
    # secondly, find out *.py.wml files:
    (dummy, pipe, dummy) = os.popen3("find %s/%s/ -name '*.py.wml'" % (modulesdir, modulename))
    out.extend([filename.strip() for filename in pipe.readlines()])
    pipe.close()
    # thirdly, find out bin/*.in files:
    (dummy, pipe, dummy) = os.popen3("find %s/%s/bin/ -name '*.in'" % (modulesdir, modulename))
    out.extend([filename.strip() for filename in pipe.readlines()])
    pipe.close()
    # last, remove Makefile, test files, z_ files:
    # pylint: disable-msg=W0141
    out = filter(lambda x: not x.endswith("Makefile.in"), out)
    out = filter(lambda x: not x.endswith("_tests.py"), out)
    out = filter(lambda x: x.find("/z_") == -1, out)
    # return list:
    return out

def wash_list_of_python_files_for_pylinting(filenames):
    """Remove away some Python files that are not suitable for
       pylinting, e.g. known wrong test files or empty init files.
    """
    # pylint: disable-msg=W0141
    # take only .py files for pylinting:
    filenames = filter(lambda x: x.endswith(".py"),
                                 filenames)
    # remove empty __init__.py files (FIXME: we may check for file size here
    # in case we shall have non-empty __init__.py files one day)    
    filenames = filter(lambda x: not x.endswith("__init__.py"),
                                 filenames)
    # take out unloadable bibformat test files:
    filenames = filter(lambda x: not x.endswith("bfe_test_4.py"),
                                 filenames)
    # take out test unloadable file:
    filenames = filter(lambda x: not x.endswith("test3.py"),
                                 filenames)
    return filenames

def get_list_of_python_unit_test_files(modulesdir, modulename):
    """Return list of Python unit test files for MODULENAME in MODULESDIR."""
    out = []
    (dummy, pipe, dummy) = os.popen3("find %s/%s/ -name '*_tests.py'" % (modulesdir, modulename))
    out.extend([filename.strip() for filename in pipe.readlines()])
    pipe.close()
    # pylint: disable-msg=W0141
    out = filter(lambda x: not x.endswith("_regression_tests.py"), out)
    return out

def get_list_of_python_regression_test_files(modulesdir, modulename):
    """Return list of Python unit test files for MODULENAME in MODULESDIR."""
    out = []
    (dummy, pipe, dummy) = os.popen3("find %s/%s/ -name '*_regression_tests.py'" % (modulesdir, modulename))
    out.extend([filename.strip() for filename in pipe.readlines()])
    pipe.close()
    return out

def get_nb_lines_in_file(filename):
    """Return number of lines in FILENAME."""
    return len(open(filename).readlines())

def get_nb_test_cases_in_file(filename):
    """Return number of test cases in FILENAME."""
    (dummy, pipe, dummy) = os.popen3("grep ' def test' %s" % filename)
    return len(pipe.readlines())

def get_pylint_score(filename):
    """Run pylint and return the code score for FILENAME.  If score
       cannot be detected, print an error and return -999999999.
    """
    (dummy, pipe, dummy) = os.popen3("pylint %s" % filename)
    pylint_output = pipe.read()
    pylint_score = -999999999
    pylint_score_matched = sre.search(r'Your code has been rated at ([0-9\.\-]+)\/10', pylint_output)
    if pylint_score_matched:
        pylint_score = pylint_score_matched.group(1)
    else:
        print "ERROR: cannot detect pylint score for %s" % filename
    if verbose >= 9:
        print "get_pylint_score(%s) = %s" % (filename, pylint_score)
    return float(pylint_score)

def get_nb_pychecker_warnings(filename):
    """Run pychecker for FILENAME and return the number of warnings.
       Do not return warnings from imported files, only warnings found
       inside FILENAME.
    """
    nb_warnings_found = 0
    filename_to_watch_for = sre.sub(r'^[\.\/]+', '', filename) # pychecker strips leading ../.. stuff
    (dummy, pipe, dummy) = os.popen3("pychecker %s" % filename)
    pychecker_output_lines = pipe.readlines()
    for line in pychecker_output_lines:
        if line.find(filename_to_watch_for + ":") > -1:            
            nb_warnings_found += 1            
    if verbose >= 9:
        print "get_nb_pychecker_warnings(%s) = %s" % (filename, nb_warnings_found)
    return nb_warnings_found    

def calculate_module_kwalitee(modulesdir, modulename):
    """Run kwalitee tests for MODULENAME in MODULESDIR
       and return tuple (modulename, nb_loc, nb_unit_tests, nb_regression_tests,
       nb_pychecker_warnings, avg_pylint_score).       
    """
    files_code = get_list_of_python_code_files(modulesdir, modulename)
    files_unit = get_list_of_python_unit_test_files(modulesdir, modulename)
    files_regression = get_list_of_python_regression_test_files(modulesdir, modulename)
    # 1 - calculate LOC:
    nb_loc = 0
    for filename in files_code:
        nb_loc += get_nb_lines_in_file(filename)
    # 2 - calculate # unit tests:
    nb_unit_tests = 0
    for filename in files_unit:
        nb_unit_tests += get_nb_test_cases_in_file(filename)
    # 3 - calculate # regression tests:
    nb_regression_tests = 0
    for filename in files_regression:
        nb_regression_tests += get_nb_test_cases_in_file(filename)
    # 4 - calculate pylint score:
    avg_pylint_score = 0.0
    files_for_pylinting = files_code + files_unit + files_regression
    files_for_pylinting = wash_list_of_python_files_for_pylinting(files_for_pylinting)
    for filename in files_for_pylinting:
        avg_pylint_score += get_pylint_score(filename)
    # pylint: disable-msg=W0704
    try:
        avg_pylint_score /= len(files_for_pylinting)
    except ZeroDivisionError:
        pass
    # 5 - calculate number of pychecker warnings:
    nb_pychecker_warnings = 0
    for filename in files_for_pylinting:
        nb_pychecker_warnings += get_nb_pychecker_warnings(filename)
    # 6 - return tuple:
    return [modulename, nb_loc, nb_unit_tests, nb_regression_tests, nb_pychecker_warnings, avg_pylint_score]

def get_invenio_modulenames(dirname="."):
    """Return the list of all CDS Invenio source modules
       (directories).
    """
    modulenames = os.listdir(dirname)
    # remove CVS:
    # pylint: disable-msg=W0141
    modulenames = filter(lambda x: not x=="CVS", modulenames)
    # remove non-directories:
    modulenames = filter(lambda x: os.path.isdir(dirname + "/" + x),
                         modulenames)
    # remove webhelp, not in Python:
    modulenames = filter(lambda x: not x=="webhelp", modulenames)
    # remove webstat, not in Python:
    modulenames = filter(lambda x: not x=="webstat", modulenames)
    # sort alphabetically:
    modulenames.sort()
    return modulenames

def generate_kwalitee_stats_for_all_modules(modulesdir):
    """Run kwalitee estimation for each CDS Invenio module and print
       the results on stdout.
    """
    # init kwalitee measurement structure:
    kwalitee = {}
    kwalitee['TOTAL'] = ['TOTAL', 0, 0, 0, 0, 0]
    # detect CDS Invenio modules:
    modulenames = get_invenio_modulenames(modulesdir)
    if "websearch" not in modulenames:
        print "Cannot find CDS Invenio modules in %s." % modulesdir
        print "Usage: python kwalitee.py [modulesdir]."
        sys.exit(1)
    # print header
    print "="*80
    print "CDS Invenio Python Code Kwalitee Check %41s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print "="*80
    print ""
    print "%(modulename)13s %(nb_loc)8s %(nb_unit)6s %(nb_regression)6s %(nb_tests_per_1k_loc)8s %(nb_pychecker_warnings)12s %(avg_pylint_score)11s" % \
          { 'modulename': 'Module',
            'nb_loc': '#LOC',
            'nb_unit': '#UnitT',
            'nb_regression': '#RegrT',
            'nb_tests_per_1k_loc': '#T/1kLOC',
            'nb_pychecker_warnings': '#PyChk/1kSRC',
            'avg_pylint_score': 'PyLintScore'}
    print " ", "-"*11, "-"*8, "-"*6, "-"*6, "-"*8, "-"*12, "-"*11
    for modulename in modulenames:
        # calculate kwalitee for this modulename:
        kwalitee[modulename] = calculate_module_kwalitee(modulesdir, modulename)
        # add it to global results:
        kwalitee['TOTAL'][1] += kwalitee[modulename][1]
        kwalitee['TOTAL'][2] += kwalitee[modulename][2]
        kwalitee['TOTAL'][3] += kwalitee[modulename][3]
        kwalitee['TOTAL'][4] += kwalitee[modulename][4]
        kwalitee['TOTAL'][5] += kwalitee[modulename][5]
        # print results for this modulename:
        print "%(modulename)13s %(nb_loc)8d %(nb_unit)6d %(nb_regression)6d %(nb_tests_per_1k_loc)8.2f %(nb_pychecker_warnings)12.3f %(avg_pylint_score)8.2f/10" % \
              { 'modulename': kwalitee[modulename][0],
                'nb_loc': kwalitee[modulename][1],
                'nb_unit': kwalitee[modulename][2],
                'nb_regression': kwalitee[modulename][3],
                'nb_tests_per_1k_loc': kwalitee[modulename][1] != 0 and \
                     (kwalitee[modulename][2] + kwalitee[modulename][3] + 0.0) / kwalitee[modulename][1] * 1000.0 or \
                     0,
                'nb_pychecker_warnings': kwalitee[modulename][1] != 0 and \
                     (kwalitee[modulename][4] + 0.0 ) / kwalitee[modulename][1] * 1000.0 or \
                     0,
                'avg_pylint_score': kwalitee[modulename][5],
              }
    # print totals:
    print " ", "-"*11, "-"*8, "-"*6, "-"*6, "-"*8, "-"*12, "-"*11
    print "%(modulename)13s %(nb_loc)8d %(nb_unit)6d %(nb_regression)6d %(nb_tests_per_1k_loc)8.2f %(nb_pychecker_warnings)12.3f %(avg_pylint_score)8.2f/10" % \
              { 'modulename': kwalitee['TOTAL'][0],
                'nb_loc': kwalitee['TOTAL'][1],
                'nb_unit': kwalitee['TOTAL'][2],
                'nb_regression': kwalitee['TOTAL'][3],
                'nb_tests_per_1k_loc': kwalitee['TOTAL'][1] != 0 and \
                     (kwalitee['TOTAL'][2] + kwalitee['TOTAL'][3] + 0.0) / kwalitee['TOTAL'][1]*1000.0 or \
                     0,
                'nb_pychecker_warnings': kwalitee['TOTAL'][1] != 0 and \
                     (kwalitee['TOTAL'][4] + 0.0 ) / kwalitee['TOTAL'][1] * 1000.0 or \
                     0,
                'avg_pylint_score': kwalitee['TOTAL'][5] / (len(kwalitee.keys()) - 1)
              }
    # print legend:
    print """
Legend:
  #LOC = number of lines of code (excl. test files, incl. comments/blanks)
  #UnitT = number of unit test cases  
  #RegrT = number of regression test cases
  #T/1kLOC = number of tests per 1k lines of code [desirable state: > 10]
  #PyChk/1kSRC = number of PyChecker warnings per 1k sources [desirable: 0]
  PyLintScore = average PyLint score [desirable state: > 9.0]
  """
    return

def generate_kwalitee_stats_for_some_files(filenames):
    """Run kwalitee checks on FILENAMES and print results."""
    # init kwalitee measurement structure:
    kwalitee = {}
    kwalitee['TOTAL'] = [0, 0, 0]
    # print header:
    print "%(filename)50s %(nb_loc)8s %(nb_pychecker_warnings)6s %(avg_pylint_score)11s" % {
        'filename': 'File',
        'nb_loc': '#LOC',
        'nb_pychecker_warnings': '#PyChk',
        'avg_pylint_score': 'PyLintScore',
        }
    print " ", "-"*48, "-"*8, "-"*6, "-"*11
    files_for_pylinting = wash_list_of_python_files_for_pylinting(filenames)
    for filename in files_for_pylinting:
        # calculate the kwalitee of the files:
        kwalitee[filename] = [0, 0, 0]
        kwalitee[filename][0] = get_nb_lines_in_file(filename) 
        kwalitee[filename][1] = get_nb_pychecker_warnings(filename)
        kwalitee[filename][2] = get_pylint_score(filename) 
        # add it to the total results:
        kwalitee['TOTAL'][0] += kwalitee[filename][0] 
        kwalitee['TOTAL'][1] += kwalitee[filename][1]
        kwalitee['TOTAL'][2] += kwalitee[filename][2]
        # print results for this filename:
        print "%(filename)50s %(nb_loc)8d %(nb_pychecker_warnings)6d %(avg_pylint_score)8.2f/10" % {
            'filename': filename,
            'nb_loc': kwalitee[filename][0],
            'nb_pychecker_warnings': kwalitee[filename][1],
            'avg_pylint_score': kwalitee[filename][2],
            }        
    # print totals:
    print " ", "-"*48, "-"*8, "-"*6, "-"*11
    print "%(filename)50s %(nb_loc)8d %(nb_pychecker_warnings)6d %(avg_pylint_score)8.2f/10" % {
        'filename': 'TOTAL',
        'nb_loc': kwalitee['TOTAL'][0],
        'nb_pychecker_warnings': kwalitee['TOTAL'][1],
        'avg_pylint_score': kwalitee['TOTAL'][2] / (len(kwalitee.keys()) - 1),
        }
    # print legend:
    print """
Legend:
  #LOC = number of lines of code (incl. comments/blanks)
  #PyChk = number of PyChecker warnings [desirable state: 0]
  PyLintScore = PyLint score [desirable state: > 9.0]
  """
    return

def usage():
    """Print usage info."""
    print """\
Usage: python kwalitee.py <topsrcdir | file1.py file2.py ...>
Description: check the kwalitee of the CDS Invenio Python code.
Examples:
    $ python kwalitee.py ~/src/cds-invenio/
    $ python kwalitee.py ../../websearch/lib/*.py"""
    return

def main():
    """Analyze CLI options and invoke appropriate actions."""
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    first_argument = sys.argv[1]
    if first_argument.startswith("-h") or first_argument.startswith("--help"):
        usage()
        sys.exit(0)
    elif os.path.isdir(first_argument):
        modulesdir = first_argument + "/modules"
        if os.path.isdir(modulesdir):
            generate_kwalitee_stats_for_all_modules(modulesdir)
        else:
            print "ERROR: %s does not seem to be CDS Invenio top source directory." % first_argument
            usage()
            sys.exit(0)
    elif os.path.isfile(first_argument):
        generate_kwalitee_stats_for_some_files(sys.argv[1:])            
    else:
        print "ERROR: don't know what to do with %s." % first_argument
        usage()
        sys.exit(1)
    return
    
if __name__ == "__main__":
    main()
