## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

"""
Code kwalitee checking tools for Invenio Python code.

Q: What is kwalitee?
A: <http://qa.perl.org/phalanx/kwalitee.html>

Usage: python kwalitee.py [options] <topsrcdir | file1.py file2.py ...>

General options::
   -h, --help               print this help
   -V, --version            print version number
   -q, --quiet              be quiet, print only warnings

Check options::
   --stats                  generate kwalitee summary stats
   --check-all              perform all checks listed below
   --check-some             perform some (important) checks only [default]
   --check-errors           check Python errors
   --check-variables        check Python variables
   --check-indentation      check Python code indentation
   --check-whitespace       check trailing whitespace
   --check-docstrings       check Python doctrings compliance
   --check-pep8             check PEP8 compliance
   --check-sql              check SQL queries
   --check-eval             check Python eval calls
   --check-html-options     check <option> missing 'value' attribute

Examples::
   $ python kwalitee.py --stats ~/private/src/invenio/
   $ python kwalitee.py --stats ../../websearch/lib/*.py
   $ python kwalitee.py --check-some ../../websearch/lib/
   $ python kwalitee.py --check-all ../../websearch/lib/search_engine.py
"""

import os
import re
import sys
import time
import subprocess

__revision__ = "$Id$" #: revision number

QUIET_MODE = False #: are we running in quiet mode? (will be set from CLI)


try:
    from pylint.__pkginfo__ import version as PYLINT_VERSION
except ImportError:
    PYLINT_VERSION = '0.0.0' #: cannot detect pylint version; pretend old


def get_list_of_python_code_files(modulesdir, modulename):
    """Return list of Python source code files for MODULENAME in MODULESDIR,
       excluding test files.
    """
    out = []
    # firstly, find out *.py files:
    out.extend(get_python_filenames_from_pathnames(["%s/%s/" % \
                                                   (modulesdir, modulename)]))
    # secondly, find out bin/*.in files:
    out.extend(get_python_filenames_from_pathnames(["%s/%s/" % \
                                                   (modulesdir, modulename)],
                                                   extension='.in'))
    # last, remove Makefile, test files, z_ files:
    out = [x for x in out if not x.endswith("Makefile.in")]
    out = [x for x in out if not x.endswith("dbexec.in")]
    out = [x for x in out if not x.endswith("_tests.py")]
    out = [x for x in out if x.find("/z_") == -1]
    # return list:
    return out


def wash_list_of_python_files_for_pylinting(filenames):
    """Remove away some Python files that are not suitable for
       pylinting, e.g. known wrong test files or empty init files.
    """
    # take only .py files for pylinting:
    filenames = [x for x in filenames if x.endswith(".py")]
    # remove empty __init__.py files (FIXME: we may check for file size here
    # in case we shall have non-empty __init__.py files one day)
    filenames = [x for x in filenames if not x.endswith("__init__.py")]
    # take out unloadable bibformat test files:
    filenames = [x for x in filenames if not x.endswith("bfe_test_4.py")]
    # take out test unloadable file:
    filenames = [x for x in filenames if not x.endswith("test3.py")]
    # take out test no docstring file:
    filenames = [x for x in filenames if not x.endswith("test_5.py")]
    return filenames


def get_list_of_python_unit_test_files(modulesdir, modulename):
    """Return list of Python unit test files for MODULENAME in MODULESDIR."""
    out = []
    for filename in get_python_filenames_from_pathnames(["%s/%s/" % \
                                                        (modulesdir,
                                                         modulename)]):
        if filename.endswith('_tests.py') and \
           not filename.endswith('_regression_tests.py'):
            out.append(filename)
    return out


def get_list_of_python_regression_test_files(modulesdir, modulename):
    """Return list of Python unit test files for MODULENAME in MODULESDIR."""
    out = []
    for filename in get_python_filenames_from_pathnames(["%s/%s/" % \
                                                        (modulesdir,
                                                         modulename)]):
        if filename.endswith('_regression_tests.py'):
            out.append(filename)
    return out


def get_list_of_web_test_files(modulesdir, modulename):
    """Return list of HTML Selenese web test files for MODULENAME
    in MODULESDIR."""
    out = []
    process = subprocess.Popen(['find', '%s/%s/' % (modulesdir, modulename),
                                '-name', 'test_*.html'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process_output, process_error = process.communicate()
    if process_error:
        print "[ERROR]", process_error
    for test_file in process_output.split('\n'): # pylint: disable=E1103
        if test_file:
            out.append(test_file)
    return out


def get_nb_lines_in_file(filename):
    """Return number of lines in FILENAME."""
    return len(open(filename).readlines())


def get_nb_test_cases_in_file(filename):
    """Return number of test cases in FILENAME."""
    process = subprocess.Popen(['grep', ' def test', filename],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process_output, process_error = process.communicate()
    if process_error:
        print "[ERROR]", process_error
    return process_output.count('\n')


def get_pylint_results(filename):
    """
    Run pylint and return the tuple of (nb_missing_docstrings, score,
    nb_msg_convention, nb_msg_refactor, nb_msg_warning, nb_msg_error,
    nb_msg_fatal) for FILENAME.  If score cannot be detected, print an
    error and return (-999999999, -999999999, 0, 0, 0, 0, 0).
    """
    process = subprocess.Popen(['pylint',
                                PYLINT_VERSION.startswith('0') and \
                                  '--output-format=parseable' or \
                                  '--msg-template={path}:{line}:' +
                                  ' [{msg_id}({symbol}), {obj}] {msg}',
                                '--rcfile=/dev/null',
                                filename],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    pylint_output, pylint_error = process.communicate()
    if pylint_error:
        print "[ERROR]", pylint_error

    # detect number of missing docstrings:
    nb_missing_docstrings = pylint_output.count("] Missing docstring")

    # detect pylint score:
    pylint_score = -999999999
    pylint_score_matched = re.search(r'Your code has been rated at ' \
                                     '([0-9\.\-]+)\/10', pylint_output)
    if pylint_score_matched:
        pylint_score = pylint_score_matched.group(1)
    else:
        print "ERROR: cannot detect pylint score for %s" % filename

    # detect pylint messages
    nb_msg_convention = pylint_output.count(": [C")
    nb_msg_refactor = pylint_output.count(": [R")
    nb_msg_warning = pylint_output.count(": [W")
    nb_msg_error = pylint_output.count(": [E")
    nb_msg_fatal = pylint_output.count(": [F")

    # return results:
    return (nb_missing_docstrings, float(pylint_score),
            nb_msg_convention, nb_msg_refactor, nb_msg_warning,
            nb_msg_error, nb_msg_fatal)


def get_nb_pychecker_warnings(filename):
    """Run pychecker for FILENAME and return the number of warnings.
       Do not return warnings from imported files, only warnings found
       inside FILENAME.
    """
    nb_warnings_found = 0
    filename_to_watch_for = os.path.basename(filename) # pychecker strips
                                                       # leading path
    process = subprocess.Popen(['pychecker', '-Q', '--limit=10000', filename],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    pychecker_output, dummy_pychecker_error = process.communicate()
    #if dummy_pychecker_error:
    #    print "[ERROR]", dummy_pychecker_error
    for line in pychecker_output.split('\n'): # pylint: disable=E1103
        if line.find(filename_to_watch_for + ":") > -1:
            nb_warnings_found += 1
    return nb_warnings_found


def calculate_module_kwalitee(modulesdir, modulename):
    """Run kwalitee tests for MODULENAME in MODULESDIR and return
       kwalitee dict with keys modulename, nb_loc, nb_unit_tests,
       nb_regression_tests, nb_web_tests, nb_pychecker_warnings,
       nb_missing_docstrings, avg_pylint_score.
    """
    files_code = get_list_of_python_code_files(modulesdir, modulename)
    files_unitt = get_list_of_python_unit_test_files(modulesdir, modulename)
    files_regressiont = get_list_of_python_regression_test_files(modulesdir,
                                                                modulename)
    files_webt = get_list_of_web_test_files(modulesdir, modulename)
    # 1 - calculate LOC:
    nb_loc = 0
    for filename in files_code:
        nb_loc += get_nb_lines_in_file(filename)
    # 2 - calculate # unit tests:
    nb_unit_tests = 0
    for filename in files_unitt:
        nb_unit_tests += get_nb_test_cases_in_file(filename)
    # 3 - calculate # regression tests:
    nb_regression_tests = 0
    for filename in files_regressiont:
        nb_regression_tests += get_nb_test_cases_in_file(filename)
    # 4 - calculate # regression tests:
    nb_web_tests = len(files_webt)
    # 5 - calculate pylint results and score:
    total_nb_missing_docstrings = 0
    total_pylint_score = 0.0
    total_nb_msg_convention = 0
    total_nb_msg_refactor = 0
    total_nb_msg_warning = 0
    total_nb_msg_error = 0
    total_nb_msg_fatal = 0
    files_for_pylinting = files_code + files_unitt + files_regressiont
    files_for_pylinting = \
         wash_list_of_python_files_for_pylinting(files_for_pylinting)
    for filename in files_for_pylinting:
        (filename_nb_missing_docstrings, filename_pylint_score,
         filename_nb_msg_convention, filename_nb_msg_refactor,
         filename_nb_msg_warning, filename_nb_msg_error,
         filename_nb_msg_fatal) = get_pylint_results(filename)
        total_nb_missing_docstrings += filename_nb_missing_docstrings
        total_pylint_score += filename_pylint_score
        total_nb_msg_convention += filename_nb_msg_convention
        total_nb_msg_refactor += filename_nb_msg_refactor
        total_nb_msg_warning += filename_nb_msg_warning
        total_nb_msg_error += filename_nb_msg_error
        total_nb_msg_fatal += filename_nb_msg_fatal
    try:
        avg_pylint_score = total_pylint_score / len(files_for_pylinting)
    except ZeroDivisionError:
        avg_pylint_score = 0.0
    # 5 - calculate number of pychecker warnings:
    nb_pychecker_warnings = 0
    for filename in files_for_pylinting:
        nb_pychecker_warnings += get_nb_pychecker_warnings(filename)
    # 6 - return kwalitee dict:
    return {'modulename': modulename,
            'nb_loc': nb_loc,
            'nb_unit_tests': nb_unit_tests,
            'nb_regression_tests': nb_regression_tests,
            'nb_web_tests': nb_web_tests,
            'nb_missing_docstrings': total_nb_missing_docstrings,
            'nb_pychecker_warnings': nb_pychecker_warnings,
            'avg_pylint_score': avg_pylint_score,
            'nb_msg_convention': total_nb_msg_convention,
            'nb_msg_refactor': total_nb_msg_refactor,
            'nb_msg_warning': total_nb_msg_warning,
            'nb_msg_error': total_nb_msg_error,
            'nb_msg_fatal': total_nb_msg_fatal,
            }


def get_invenio_modulenames(dirname="."):
    """Return the list of all Invenio source modules
       (directories).
    """
    modulenames = os.listdir(dirname)
    # remove CVS:
    modulenames = [x for x in modulenames if not x == "CVS"]
    # remove non-directories:
    modulenames = [x for x in modulenames if os.path.isdir(dirname + "/" + x)]
    # remove webhelp, not in Python:
    modulenames = [x for x in modulenames if not x == "webhelp"]
    # sort alphabetically:
    modulenames.sort()
    return modulenames


def shorten_module_name(modulename, maxlen=13):
    """Return MODULENAME shortened to maximum length of MAXLEN characters.
       Useful for pretty-printing module names in aligned tables.
    """
    return modulename[:maxlen]


def generate_kwalitee_stats_for_all_modules(modulesdir):
    """Run kwalitee estimation for each Invenio module and print
       the results on stdout.
    """
    # init kwalitee measurement structure:
    kwalitee = {}
    kwalitee['TOTAL'] = {'modulename': 'TOTAL',
                         'nb_loc': 0,
                         'nb_unit_tests': 0,
                         'nb_regression_tests': 0,
                         'nb_web_tests': 0,
                         'nb_missing_docstrings': 0,
                         'nb_pychecker_warnings': 0,
                         'avg_pylint_score': 0,
                         'nb_msg_convention': 0,
                         'nb_msg_refactor': 0,
                         'nb_msg_warning': 0,
                         'nb_msg_error': 0,
                         'nb_msg_fatal': 0,
                         }
    # detect Invenio modules:
    modulenames = get_invenio_modulenames(modulesdir)
    if "websearch" not in modulenames:
        print "Cannot find Invenio modules in %s." % modulesdir
        print_usage()
        sys.exit(1)
    # print header
    print "="*112
    print "Invenio Python Code Kwalitee Check %73s" % \
          time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print "="*112
    print ""
    print "%(modulename)13s %(nb_loc)8s %(nb_unitt)6s %(nb_regressiont)6s " \
          "%(nb_webt)6s %(nb_tests_per_1k_loc)8s %(nb_missing_docstrings)8s " \
          "%(nb_pychecker_warnings)12s %(avg_pylint_score)11s " \
          "%(pylint_details)s" % \
             {'modulename': 'Module',
              'nb_loc': '#LOC',
              'nb_unitt': '#UnitT',
              'nb_regressiont': '#RegrT',
              'nb_webt': '#WebT',
              'nb_tests_per_1k_loc': '#T/1kLOC',
              'nb_missing_docstrings': '#MissDoc',
              'nb_pychecker_warnings': '#PyChk/1kSRC',
              'avg_pylint_score': 'PyLintScore',
              'pylint_details': 'PyLintDetails'}
    print " ", "-"*11, "-"*8, "-"*6, "-"*6, "-"*6, "-"*8, "-"*8, "-"*12, \
          "-"*11, "-"*25
    for modulename in modulenames:
        # calculate kwalitee for this modulename:
        kwalitee[modulename] = calculate_module_kwalitee(modulesdir,
                                                         modulename)
        # add it to global results:
        kwalitee['TOTAL']['nb_loc'] += kwalitee[modulename]['nb_loc']
        kwalitee['TOTAL']['nb_unit_tests'] += \
               kwalitee[modulename]['nb_unit_tests']
        kwalitee['TOTAL']['nb_regression_tests'] += \
               kwalitee[modulename]['nb_regression_tests']
        kwalitee['TOTAL']['nb_web_tests'] += \
               kwalitee[modulename]['nb_web_tests']
        kwalitee['TOTAL']['nb_pychecker_warnings'] += \
               kwalitee[modulename]['nb_pychecker_warnings']
        kwalitee['TOTAL']['nb_missing_docstrings'] += \
               kwalitee[modulename]['nb_missing_docstrings']
        kwalitee['TOTAL']['avg_pylint_score'] += \
               kwalitee[modulename]['avg_pylint_score']
        kwalitee['TOTAL']['nb_msg_convention'] += \
               kwalitee[modulename]['nb_msg_convention']
        kwalitee['TOTAL']['nb_msg_refactor'] += \
               kwalitee[modulename]['nb_msg_refactor']
        kwalitee['TOTAL']['nb_msg_warning'] += \
               kwalitee[modulename]['nb_msg_warning']
        kwalitee['TOTAL']['nb_msg_error'] += \
               kwalitee[modulename]['nb_msg_error']
        kwalitee['TOTAL']['nb_msg_fatal'] += \
               kwalitee[modulename]['nb_msg_fatal']
        # print results for this modulename:
        print "%(modulename)13s %(nb_loc)8d %(nb_unitt)6d " \
              "%(nb_regressiont)6d %(nb_webt)6d %(nb_tests_per_1k_loc)8.2f " \
              "%(nb_missing_docstrings)8d %(nb_pychecker_warnings)12.3f " \
              "%(avg_pylint_score)8.2f/10 %(pylint_details)s" % \
              {'modulename': \
                     shorten_module_name(kwalitee[modulename]['modulename']),
               'nb_loc': kwalitee[modulename]['nb_loc'],
               'nb_unitt': kwalitee[modulename]['nb_unit_tests'],
               'nb_regressiont': kwalitee[modulename]['nb_regression_tests'],
               'nb_webt': kwalitee[modulename]['nb_web_tests'],
               'nb_tests_per_1k_loc': kwalitee[modulename]['nb_loc'] != 0 and \
                     (kwalitee[modulename]['nb_unit_tests'] + \
                      kwalitee[modulename]['nb_regression_tests'] + \
                      kwalitee[modulename]['nb_web_tests'] + 0.0) / \
                     kwalitee[modulename]['nb_loc'] * 1000.0 or 0,
               'nb_missing_docstrings': \
                     kwalitee[modulename]['nb_missing_docstrings'],
               'nb_pychecker_warnings': \
                     kwalitee[modulename]['nb_loc'] != 0 and \
                     (kwalitee[modulename]['nb_pychecker_warnings'] + 0.0) / \
                      kwalitee[modulename]['nb_loc'] * 1000.0 or 0,
               'avg_pylint_score': kwalitee[modulename]['avg_pylint_score'],
               'pylint_details': "%3dF %3dE %3dW %3dR %3dC" % \
                      (kwalitee[modulename]['nb_msg_fatal'],
                       kwalitee[modulename]['nb_msg_error'],
                       kwalitee[modulename]['nb_msg_warning'],
                       kwalitee[modulename]['nb_msg_refactor'],
                       kwalitee[modulename]['nb_msg_convention'])}
    # print totals:
    print " ", "-"*11, "-"*8, "-"*6, "-"*6, "-"*6, "-"*8, "-"*8, "-"*12, \
          "-"*11, "-"*25
    print "%(modulename)13s %(nb_loc)8d %(nb_unitt)6d %(nb_regressiont)6d " \
          "%(nb_webt)6d %(nb_tests_per_1k_loc)8.2f " \
          "%(nb_missing_docstrings)8d %(nb_pychecker_warnings)12.3f " \
          "%(avg_pylint_score)8.2f/10 %(pylint_details)s" % \
              {'modulename': kwalitee['TOTAL']['modulename'],
               'nb_loc': kwalitee['TOTAL']['nb_loc'],
               'nb_unitt': kwalitee['TOTAL']['nb_unit_tests'],
               'nb_regressiont': kwalitee['TOTAL']['nb_regression_tests'],
               'nb_webt': kwalitee['TOTAL']['nb_web_tests'],
               'nb_tests_per_1k_loc': kwalitee['TOTAL']['nb_loc'] != 0 and \
                    (kwalitee['TOTAL']['nb_unit_tests'] + \
                     kwalitee['TOTAL']['nb_regression_tests'] + \
                     kwalitee['TOTAL']['nb_web_tests'] + 0.0) / \
                    kwalitee['TOTAL']['nb_loc']*1000.0 or 0,
               'nb_missing_docstrings': \
                    kwalitee['TOTAL']['nb_missing_docstrings'],
               'nb_pychecker_warnings': kwalitee['TOTAL']['nb_loc'] != 0 and \
                    (kwalitee['TOTAL']['nb_pychecker_warnings'] + 0.0) / \
                        kwalitee['TOTAL']['nb_loc'] * 1000.0 or 0,
               'avg_pylint_score': kwalitee['TOTAL']['avg_pylint_score'] / \
                        (len(kwalitee.keys()) - 1),
               'pylint_details': "%3dF %3dE %3dW %3dR %3dC" % \
                        (kwalitee['TOTAL']['nb_msg_fatal'],
                         kwalitee['TOTAL']['nb_msg_error'],
                         kwalitee['TOTAL']['nb_msg_warning'],
                         kwalitee['TOTAL']['nb_msg_refactor'],
                         kwalitee['TOTAL']['nb_msg_convention'])}
    # print legend:
    print """
Legend:
  #LOC = number of lines of code (excl. test files, incl. comments/blanks)
  #UnitT = number of unit test cases
  #RegrT = number of regression test cases
  #WebT = number of web test cases
  #T/1kLOC = number of tests per 1k lines of code [desirable: > 10]
  #MissDoc = number of missing docstrings [desirable: 0]
  #PyChk/1kSRC = number of PyChecker warnings per 1k sources [desirable: 0]
  PyLintScore = average PyLint score [desirable: > 9.00]
  PyLintDetails = number of PyLint messages (Fatal, Error, Warning, Refactor,
                                             Convention)
  """
    return


def generate_kwalitee_stats_for_some_files(filenames):
    """Run kwalitee checks on FILENAMES and print results."""
    # init kwalitee measurement structure:
    kwalitee = {}
    kwalitee['TOTAL'] = {'nb_loc': 0,
                         'nb_missing_docstrings': 0,
                         'nb_pychecker_warnings': 0,
                         'avg_pylint_score': 0,
                         'nb_msg_convention': 0,
                         'nb_msg_refactor': 0,
                         'nb_msg_warning': 0,
                         'nb_msg_error': 0,
                         'nb_msg_fatal': 0,
                         }
    # print header:
    print "%(filename)50s %(nb_loc)8s %(nb_missing_docstrings)8s " \
          "%(nb_pychecker_warnings)6s %(avg_pylint_score)11s " \
          "%(pylint_details)s" % {
              'filename': 'File',
              'nb_loc': '#LOC',
              'nb_missing_docstrings': '#MissDoc',
              'nb_pychecker_warnings': '#PyChk',
              'avg_pylint_score': 'PyLintScore',
              'pylint_details': 'PyLintDetails'}
    print " ", "-"*48, "-"*8, "-"*8, "-"*6, "-"*11, "-"*25
    files_for_pylinting = wash_list_of_python_files_for_pylinting(filenames)
    for filename in files_for_pylinting:
        # calculate the kwalitee of the files:
        kwalitee[filename] = {'nb_loc': 0,
                              'nb_missing_docstrings': 0,
                              'nb_pychecker_warnings': 0,
                              'avg_pylint_score': 0,
                              'nb_msg_convention': 0,
                              'nb_msg_refactor': 0,
                              'nb_msg_warning': 0,
                              'nb_msg_error': 0,
                              'nb_msg_fatal': 0,
                              }
        kwalitee[filename]['nb_loc'] = get_nb_lines_in_file(filename)
        kwalitee[filename]['nb_pychecker_warnings'] = \
                 get_nb_pychecker_warnings(filename)
        (kwalitee[filename]['nb_missing_docstrings'],
         kwalitee[filename]['avg_pylint_score'],
         kwalitee[filename]['nb_msg_convention'],
         kwalitee[filename]['nb_msg_refactor'],
         kwalitee[filename]['nb_msg_warning'],
         kwalitee[filename]['nb_msg_error'],
         kwalitee[filename]['nb_msg_fatal']) = get_pylint_results(filename)
        # add it to the total results:
        kwalitee['TOTAL']['nb_loc'] += kwalitee[filename]['nb_loc']
        kwalitee['TOTAL']['nb_pychecker_warnings'] += \
                 kwalitee[filename]['nb_pychecker_warnings']
        kwalitee['TOTAL']['nb_missing_docstrings'] += \
                 kwalitee[filename]['nb_missing_docstrings']
        kwalitee['TOTAL']['avg_pylint_score'] += \
                 kwalitee[filename]['avg_pylint_score']
        kwalitee['TOTAL']['nb_msg_convention'] += \
                 kwalitee[filename]['nb_msg_convention']
        kwalitee['TOTAL']['nb_msg_refactor'] += \
                 kwalitee[filename]['nb_msg_refactor']
        kwalitee['TOTAL']['nb_msg_warning'] += \
                  kwalitee[filename]['nb_msg_warning']
        kwalitee['TOTAL']['nb_msg_error'] += kwalitee[filename]['nb_msg_error']
        kwalitee['TOTAL']['nb_msg_fatal'] += kwalitee[filename]['nb_msg_fatal']
        # print results for this filename:
        print "%(filename)50s %(nb_loc)8d %(nb_missing_docstrings)8d " \
              "%(nb_pychecker_warnings)6d %(avg_pylint_score)8.2f/10 " \
              "%(pylint_details)s" % {
            'filename': filename,
            'nb_loc': kwalitee[filename]['nb_loc'],
            'nb_missing_docstrings': \
                  kwalitee[filename]['nb_missing_docstrings'],
            'nb_pychecker_warnings': \
                  kwalitee[filename]['nb_pychecker_warnings'],
            'avg_pylint_score': kwalitee[filename]['avg_pylint_score'],
            'pylint_details': "%3dF %3dE %3dW %3dR %3dC" % \
                  (kwalitee[filename]['nb_msg_fatal'],
                   kwalitee[filename]['nb_msg_error'],
                   kwalitee[filename]['nb_msg_warning'],
                   kwalitee[filename]['nb_msg_refactor'],
                   kwalitee[filename]['nb_msg_convention'])}
    # print totals:
    print " ", "-"*48, "-"*8, "-"*8, "-"*6, "-"*11, "-"*25
    print "%(filename)50s %(nb_loc)8d %(nb_missing_docstrings)8d " \
          "%(nb_pychecker_warnings)6d %(avg_pylint_score)8.2f/10 " \
          "%(pylint_details)s" % {
        'filename': 'TOTAL',
        'nb_loc': kwalitee['TOTAL']['nb_loc'],
        'nb_missing_docstrings': kwalitee['TOTAL']['nb_missing_docstrings'],
        'nb_pychecker_warnings': kwalitee['TOTAL']['nb_pychecker_warnings'],
        'avg_pylint_score': kwalitee['TOTAL']['avg_pylint_score'] / \
                            (len(kwalitee.keys()) - 1),
        'pylint_details': "%3dF %3dE %3dW %3dR %3dC" % \
              (kwalitee['TOTAL']['nb_msg_fatal'],
               kwalitee['TOTAL']['nb_msg_error'],
               kwalitee['TOTAL']['nb_msg_warning'],
               kwalitee['TOTAL']['nb_msg_refactor'],
               kwalitee['TOTAL']['nb_msg_convention'])}
    # print legend:
    print """
Legend:
  #LOC = number of lines of code (incl. comments/blanks)
  #MissDoc = number of missing docstrings [desirable: 0]
  #PyChk = number of PyChecker warnings [desirable: 0]
  PyLintScore = PyLint score [desirable: > 9.00]
  PyLintDetails = number of PyLint messages (Fatal, Error, Warning, Refactor,
                                             Convention)
  """
    return


def get_python_filenames_from_pathnames(pathnames, extension='.py'):
    """Get recursively all Python filenames from given pathnames.
    Input: list of pathnames (a pathname is a file or a directory).
    Output: list of Python files.
    """
    if not isinstance(pathnames, list):
        # sanity check in case people pass one pathname without list
        pathnames = [pathnames]
    out = set([])
    for pathname in pathnames:
        if os.path.isdir(pathname):
            # we have directory, so recursively searching list of files:
            for rootdir, dummy_subdirs, files in os.walk(pathname):
                for afile in files:
                    if afile.endswith(extension):
                        out.add(os.path.join(rootdir, afile))
        else:
            # we have file:
            if pathname.endswith(extension):
                out.add(pathname)
    out = list(out)
    out.sort()
    return out


def print_heading(phrase, prefix='', suffix='', stream='INFO'):
    """Print heading phrase in a special style."""
    if QUIET_MODE:
        return
    print prefix + '[' + stream + '] ' + phrase + suffix


def print_usage():
    """Print usage info."""
    print __doc__


def print_version():
    """Print version info."""
    print __revision__


def cmd_check_all(filenames):
    """Run all checks on filenames."""
    errors_found_p = False
    if cmd_check_errors(filenames):
        errors_found_p = True
    if cmd_check_variables(filenames):
        errors_found_p = True
    if cmd_check_indentation(filenames):
        errors_found_p = True
    if cmd_check_whitespace(filenames):
        errors_found_p = True
    if cmd_check_docstrings(filenames):
        errors_found_p = True
    if cmd_check_pep8(filenames):
        errors_found_p = True
    if cmd_check_eval(filenames): # kwalitee: disable=eval
        errors_found_p = True
    if cmd_check_sql(filenames):
        errors_found_p = True
    if cmd_check_html_options(filenames):
        errors_found_p = True
    return errors_found_p


def cmd_check_some(filenames):
    """Run some (important) checks on filenames."""
    errors_found_p = False
    if cmd_check_errors(filenames):
        errors_found_p = True
    if cmd_check_variables(filenames):
        errors_found_p = True
    if cmd_check_indentation(filenames):
        errors_found_p = True
    if cmd_check_eval(filenames): # kwalitee: disable=eval
        errors_found_p = True
    if cmd_check_sql(filenames):
        errors_found_p = True
    if cmd_check_html_options(filenames):
        errors_found_p = True
    return errors_found_p


def cmd_check_errors(filenames):
    """Run pylint error check on filenames."""
    errors_found_p = False
    print_heading('Checking Python errors...')
    for filename in filenames:
        out = ''
        process = subprocess.Popen(['pylint', '--rcfile=/dev/null',
                                    PYLINT_VERSION.startswith('0') and \
                                      '--output-format=parseable' or \
                                      '--msg-template={path}:{line}:' +
                                      ' [{msg_id}({symbol}), {obj}] {msg}',
                                    '--errors-only', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        if err:
            errors_found_p = True
            print "[ERROR]", err
        if out:
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_variables(filenames):
    """Run pylint variable check on filenames."""
    errors_found_p = False
    print_heading('Checking Python variables...')
    for filename in filenames:
        out = ''
        process = subprocess.Popen(['pylint', '--rcfile=/dev/null',
                                    PYLINT_VERSION.startswith('0') and \
                                      '--output-format=parseable' or \
                                      '--msg-template={path}:{line}:' +
                                      ' [{msg_id}({symbol}), {obj}] {msg}',
                                    '--reports=n', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        pylint_output, pylint_error = process.communicate()
        if pylint_error:
            errors_found_p = True
            print "[ERROR]", pylint_error
        for line in pylint_output.split('\n'): # pylint: disable=E1103
            if '; [F' in line or ': [E' in line or ': [W' in line:
                if 'variable' in line or \
                   'name' in line or \
                   'global' in line or \
                   'Unused' in line or \
                   'Redefining' in line:
                    out += line + '\n'
        if out:
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_indentation(filenames):
    """Run pylint indendation check on filenames."""
    errors_found_p = False
    print_heading('Checking Python indentation...')
    for filename in filenames:
        out = ''
        process = subprocess.Popen(['pylint', '--rcfile=/dev/null',
                                    PYLINT_VERSION.startswith('0') and \
                                      '--output-format=parseable' or \
                                      '--msg-template={path}:{line}:' +
                                      ' [{msg_id}({symbol}), {obj}] {msg}',
                                    '--reports=n', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process_output, process_error = process.communicate()
        if process_error:
            errors_found_p = True
            print "[ERROR]", process_error
        for line in process_output.split('\n'): # pylint: disable=E1103
            if 'indent' in line:
                out += line + '\n'
        if out:
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_whitespace(filenames):
    """Run trailing whitespace check on filenames."""
    errors_found_p = False
    print_heading('Checking trailing whitespace...')
    for filename in filenames:
        out = ''
        process = subprocess.Popen(['grep', '-Hni', ' $', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process_output, process_error = process.communicate()
        if process_error:
            errors_found_p = True
            print "[ERROR]", process_error
        for line in process_output.split('\n'): # pylint: disable=E1103
            if line:
                out += line + '\n'
        if out:
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_html_options(filenames):
    """
    Check cases where an C{<option>} element has been used without its
    C{value} attribute, in filenames.

    It is better to avoid missing C{value} attribute in C{<option>}
    elements as some browsers/plugins might automatically translate
    the label of the option, which I{could} then become the
    (unexpected) value of the option.

    @note: the check is very simple, and will miss cases such as
    C{<option class="">}
    """
    errors_found_p = False
    print_heading('Checking <option> without \'value\' attribute...')
    for filename in filenames:
        if filename.endswith('kwalitee.py'):
            # Skip this file with false positives
            continue
        out = ''
        process = subprocess.Popen(['grep', '-Hni', '<option\s*>', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process_output, process_error = process.communicate()
        if process_error:
            errors_found_p = True
            print "[ERROR]", process_error
        for line in process_output.split('\n'): # pylint: disable=E1103
            if line:
                out += line + '\n'
        if out:
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_docstrings(filenames):
    """Run epydoc doctrings check on filenames."""
    errors_found_p = False
    print_heading('Checking Python docstrings compliance...')
    for filename in filenames:
        out = ''
        process = subprocess.Popen(['epydoc', '-v', '--simple-term',
                                    '--check', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process_output, process_error = process.communicate()
        if process_error:
            errors_found_p = True
            print "[ERROR]", process_error
        for line in process_output.split('\n'): # pylint: disable=E1103
            if line.startswith('  [......'):
                pass
            elif line.endswith('.__package__'):
                # epydoc does not treat __package__ properly, so let's
                # discard these types of findings
                pass
            else:
                out += line + '\n'
        if out and out.strip() != 'Warning: Undocumented:':
            # something other than sole __package__ was found
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_pep8(filenames):
    """Run PEP8 compliance check on filenames."""
    errors_found_p = False
    print_heading('Checking PEP8 compliance...')
    path_to_pep8 = sys.argv[0].replace('kwalitee.py', 'pep8.py')
    for filename in filenames:
        out = ''
        process = subprocess.Popen(['python', path_to_pep8, '--repeat',
                                    '--statistics', filename],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
        if err:
            errors_found_p = True
            print "[ERROR]", err
        if out:
            errors_found_p = True
            print out
    return errors_found_p


def cmd_check_sql(filenames):
    """Run SQL query compliance check on filenames."""
    errors_found_p = False
    print_heading('Checking SQL queries...')
    for filename in filenames:
        out = ''
        for grepargs in ('SELECT \* FROM',
                         'INSERT INTO ([[:alnum:]]|_)+[[:space:]]*VALUES',
                         'INSERT INTO ([[:alnum:]]|_)+[[:space:]]*$$',
                         "run_sql.*'%[dfis]'",
                         'run_sql.*"%[dfis]"',
                         'run_sql.* % '): # kwalitee: disable=sql
            process = subprocess.Popen(['grep', '-HEni', grepargs, filename],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process_output, process_error = process.communicate()
            if process_error:
                errors_found_p = True
                print "[ERROR]", process_error
            for line in process_output.split('\n'): # pylint: disable=E1103
                if line and not line.endswith('# kwalitee: disable=sql'):
                    out += line + '\n'
        if out:
            errors_found_p = True
            print out.strip()
    return errors_found_p


def cmd_check_eval(filenames): # kwalitee: disable=eval
    """Run `eval' and `execfile' check on filenames."""
    errors_found_p = False
    print_heading('Checking Python eval calls...')
    for filename in filenames:
        out = ''
        for grepargs in ('eval\(',
                         'execfile\('):
            process = subprocess.Popen(['grep', '-HEni', grepargs, filename],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process_output, process_error = process.communicate()
            if process_error:
                errors_found_p = True
                print "[ERROR]", process_error
            for line in process_output.split('\n'): # pylint: disable=E1103
                if line and not line.endswith('# kwalitee: disable=eval'):
                    out += line + '\n'
        if out:
            errors_found_p = True
            print out.strip()
    return errors_found_p


def cmd_stats(filenames):
    """Run overall kwalite stats on file/dir."""
    if len(filenames) == 1 and os.path.isdir(filenames[0]):
        modulesdir = filenames[0] + "/modules"
        if os.path.isdir(modulesdir):
            generate_kwalitee_stats_for_all_modules(modulesdir)
        else:
            print "ERROR: %s does not seem to be Invenio top source " \
                  "directory." % filenames[0]
            print_usage()
            sys.exit(0)
    else:
        # os.path.isfile(cmd_arg) and cmd_arg.endswith(".py"):
        generate_kwalitee_stats_for_some_files(filenames)


def main():
    """Analyze CLI options and invoke appropriate actions."""
    global QUIET_MODE # pylint: disable=W0603
    # check options:
    if '--help' in sys.argv or \
       '-h' in sys.argv:
        print_usage()
    elif '--version' in sys.argv or \
         '-V' in sys.argv:
        print_version()
    else:
        # detect what to run:
        cmd_option = None
        cmd_pathnames = None
        for opt_idx in range(1, len(sys.argv)):
            opt = sys.argv[opt_idx]
            if opt in ('--stats', '--check-all', '--check-some',
                       '--check-errors', '--check-variables',
                       '--check-indentation', '--check-whitespace',
                       '--check-docstrings', '--check-pep8',
                       '--check-html-options', '--check-sql',
                       '--check-eval'):
                cmd_option = opt[2:].replace('-', '_')
            elif opt in ('-q', '--quiet'):
                QUIET_MODE = True
            elif not opt.startswith('--'):
                cmd_pathnames = sys.argv[opt_idx:]
                break
        if not cmd_option:
            # by default, we are checking only `most important' stuff
            cmd_option = 'check_some'
        if not cmd_pathnames:
            print "ERROR: Please specify directory/file; see '--help'."
            sys.exit(1)
        # run it:
        if cmd_option == 'stats':
            eval('cmd_' + cmd_option)(cmd_pathnames) # kwalitee: disable=eval
        else:
            # detect Python files to process:
            cmd_filenames = get_python_filenames_from_pathnames(cmd_pathnames)
            if not cmd_filenames:
                # Hmm, maybe people passed invenio.webfoo_bar, so
                # let's try to continue.  Most checks will work, some
                # will not (e.g. PEP8).  FIXME: clean this
                # double-entry stuff, display verbose warnings in
                # respective tests, and after cleaning advertize it in
                # the --help page.
                cmd_filenames = cmd_pathnames
            errors_found_p = \
              eval('cmd_' + cmd_option)(cmd_filenames) # kwalitee: disable=eval
            if errors_found_p:
                print_heading('Kwalitee problems found.  Please fix.',
                              stream='ERROR')
                sys.exit(1)
        print_heading('Done.')
    return

if __name__ == "__main__":
    main()
