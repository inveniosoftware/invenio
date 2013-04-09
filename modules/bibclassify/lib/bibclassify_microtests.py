# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Module for running microtests on how well the extraction works -
this module is STANDALONE safe"""

import ConfigParser
import glob
import traceback
import codecs

from invenio import bibclassify_config as bconfig
from invenio import bibclassify_engine as engine
log = bconfig.get_logger("bibclassify.microtest")


def run(glob_patterns,
        verbose=20,
        plevel = 1
        ):
    """Execute microtests"""

    if verbose is not None:
        log.setLevel(int(verbose))

    results = {}
    for pattern in glob_patterns:
        log.info("Looking for microtests: %s" % pattern)
        for cfgfile in glob.glob(pattern):
            log.debug("processing: %s" % (cfgfile))

            try:
                test_cases = load_microtest_definition(cfgfile)
                run_microtest_suite(test_cases, results=results, plevel=plevel)
            except Exception, msg:
                log.error('Error running microtest: %s' % cfgfile)
                log.error(msg)
                log.error(traceback.format_exc())

    summarize_results(results, plevel)


def run_microtest_suite(test_cases, results={}, plevel=1):
    """Runs all tests from the test_case
    @var test_cases: microtest definitions
    @keyword results: dict, where results are cummulated
    @keyword plevel: int [0..1], performance level, results
        below the plevel are considered unsuccessful
    @return: nothing
    """

    config = {}
    if 'config' in test_cases:
        config = test_cases['config']
        del(test_cases['config'])
    if 'taxonomy' not in config:
        config['taxonomy'] = ['HEP']

    for test_name in sorted(test_cases.keys()):
        test = test_cases[test_name]
        try:
            log.debug('section: %s' % test_name)
            phrase = test['phrase'][0]
            (skw, ckw, akw, acr) = engine.get_keywords_from_text(test['phrase'], config['taxonomy'][0], output_mode="raw")

            details = analyze_results(test, (skw, ckw) )
            if details["plevel"] < plevel:
                log.error("\n" + format_test_case(test))
                log.error("results\n" + format_details(details))
            else:
                log.info("Success for section: %s" % (test_name))
                log.info("\n" + format_test_case(test))
                if plevel != 1:
                    log.info("results\n" + format_details(details))

            results.setdefault(test_name, [])
            results[test_name].append(details)

        except Exception, msg:
            log.error('Operational error executing section: %s' % test_name)
            #log.error(msg)
            log.error(traceback.format_exc())


def summarize_results(results, plevel):
    total = 0
    success = 0
    for k,v in results.items():
        total += len(v)
        success += len(filter(lambda x: x["plevel"] >= plevel, v))
    log.info("Total number of micro-tests run: %s" % total)
    log.info("Success/failure: %d/%d" % (success, total-success))

def format_details(details):
    plevel = details["plevel"]
    details["plevel"] = [plevel]
    out = format_test_case(details)
    details["plevel"] = plevel
    return out

def format_test_case(test_case):

    padding = 13

    keys = ["phrase", "expected", "unwanted"]
    out = ["" for x in range(len(keys))]
    out2 = []

    for key in test_case.keys():
        phrase = "\n".join(map(lambda x: (" " * (padding + 1) ) + str(x), test_case[key]))
        if key in keys:
            out[keys.index(key)] = "%s=%s" % (key.rjust(padding-1), phrase[padding:])
        else:
            out2.append("%s=%s" % (key.rjust(padding-1), phrase[padding:]))

    if filter(len, out) and filter(len, out2):
        return "%s\n%s" % ("\n".join(filter(len, out)), "\n".join(out2))
    else:
        return "%s%s" % ("\n".join(filter(len, out)), "\n".join(out2))



def analyze_results(test_case, results):

    skw = results[0]
    ckw = results[1]

    details = {"correct" : [], "incorrect": [],
               "plevel" : 0}

    responses_total = len(skw) + len(ckw)
    expected_total = len(test_case["expected"])
    correct_responses = 0
    incorrect_responses = 0

    for result_set in (skw, ckw):
        for r in result_set:
            try:
                val = r[0].output()
            except:
                val = r.output()
            if r in test_case["expected"]:
                correct_responses += 1
                details["correct"].append(val)
            else:
                incorrect_responses += 1
                details["incorrect"].append(val)

    details["plevel"] = ((responses_total + expected_total) - incorrect_responses) / (responses_total + expected_total)

    return details

def load_microtest_definition(cfgfile, **kwargs):
    """Loads data from the microtest definition file
    {
     section-1:
        phrase: [ some-string]
        expected: [some, string]
        unwanted: [some-string]
     section-2:
        .....
    }
    """
    config = {}
    cfg = ConfigParser.ConfigParser()
    fo = codecs.open(cfgfile, 'r', 'utf-8')
    cfg.readfp(fo, filename=cfgfile)
    for s in cfg.sections():
        if s in config:
            log.error('two sections with the same name')
        config[s] = {}
        for k, v in cfg.items(s):
            if "\n" in v:
                v = filter(len, v.splitlines())
            else:
                v = [v.strip()]
            if k not in config[s]:
                config[s][k] = []
            config[s][k] += v
    fo.close()
    return config

if __name__ == "__main__":
    import os, sys
    test_paths = []
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        test_paths.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       "bibclassify/microtest*.cfg")))
        test_paths.append(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       "../../../etc/bibclassify/microtest*.cfg")))
        run(test_paths)
    elif (len(sys.argv) > 1):
        for p in sys.argv[1:]:
            if p[0] == os.path.sep: # absolute path
                test_paths.append(p)
            else: # try to detect if we shall prepend rootdir
                first = p.split(os.path.sep)[0]
                if os.path.exists(first): #probably relative path
                    test_paths.append(p)
                elif (os.path.join(bconfig.CFG_PREFIX, first)): #relative to root
                    test_paths.append(os.path.join(bconfig.CFG_PREFIX, p))
                    log.warning('Resolving relative path %s -> %s' % (p, test_paths[-1]))
                else:
                    raise Exception ('Please check the glob pattern: %s\n\
                            it seems to be a relative path, but not relative to the script, nor to the invenio rootdir' % p)
        run(test_paths)
    else:
        print 'Usage: %s glob_pattern [glob_pattern...]\nExample: %s %s/etc/bibclassify/microtest*.cfg' % (sys.argv[0],
                                                                         sys.argv[0],
                                                                         bconfig.CFG_PREFIX,
                                                                         )
