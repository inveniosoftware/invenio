# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
'''
bibauthorid_general_utils
    Bibauthorid utilities used by many parts of the framework
'''

from invenio import bibauthorid_config as bconfig
from invenio.config import CFG_BASE_URL
from datetime import datetime
import sys
import os
from math import floor
from invenio.crossrefutils import get_marcxml_for_doi, CrossrefError
try:
    import elementtree.ElementTree as ET
except ImportError:
    from xml.etree import ElementTree as ET
from urllib import urlopen
from urllib2 import HTTPError
from collections import deque

import multiprocessing as mp
from multiprocessing import Queue
from Queue import Empty

import time
import re
import random
from collections import Hashable
from functools import partial

import os
PID = os.getpid

pidfiles = dict()

# Constants for classification
DOI_ID = "doi"
ARXIV_ID = "arxivid"

ORCID_ID = "orcid"
INSPIRE_ID = "inspire"

orcid_regex = re.compile(r"((?:https?://)?(?:www.)?orcid.org/)?((?:\d{4}-){3}\d{3}[\dX]$)", re.IGNORECASE)
inspire_regex = re.compile(r"(INSPIRE-)(\d+)$", re.IGNORECASE)

arxiv_new_regex = re.compile(r"(arXiv:)?(\d{4})\.(\d{4,6})(v\d+)?$", re.IGNORECASE)
arxiv_old_regex = re.compile(
    r"(arXiv:)?((?:[a-zA-Z]|[a-zA-Z]-[a-zA-Z])+)(\.[a-zA-Z]{2})?/(\d{7})(v\d+)?$",
    re.IGNORECASE)
doi_regex = re.compile(r"((?:https?://)?(?:dx.)?doi.org/)?(10\.(\d+)(/|\.)\S.*)$", re.IGNORECASE)


class memoized(object):

    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    Keeps at most cache_limit elements. Deletes half of caches in case of overflow.
    '''

    def __init__(self, func, cache_limit=1000000):

        self.func = func
        self.cache = {}

        if cache_limit:
            self.cache_limit = cache_limit
        else:
            cache_limit = False

    def __call__(self, *args, **kwargs):
        if kwargs:
            return self.func(*args, **kwargs)
        try:
            key = hash(args)
        except TypeError:
            return self.func(*args)
        if key in self.cache:
            return self.cache[key]
        else:
            value = self.func(*args)
            self.cache[key] = value
            if self.cache_limit and len(self.cache) > self.cache_limit:
                keys = self.cache.keys()
                random.shuffle(keys)
                to_delete = keys[0:self.cache_limit / 2]
                map(self.cache.pop, to_delete)
            return value

    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return partial(self.__call__, obj)


def get_doi_url(doi):
    """
    Provides a HTTP DX DOI resolvable url given a DOI.

    @param doi: DOI string
    @return: Resolvable DOI URL
    """
    return "http://dx.doi.org/%s" % doi


def get_arxiv_url(arxiv):
    """
    Provides a HTTP arXiv resolvable url given an arXiv ID.

    @param arxiv: arXiv string
    @return: Resolvable arXiv URL
    """
    return "http://arxiv.org/abs/%s" % arxiv


def get_inspire_record_url(recid):
    """
    Provides a resolvable url given an inspire recid.

    @param recid: internal record id
    @return: Resolvable inspire record URL
    """
    return "%s/record/%s" % (CFG_BASE_URL, recid)


def get_orcid_from_string(identifier, uri=False):
    """
    Extracts the ORCID from various string inputs and validates the format.

    This function returns an ORCID that can be used with other functions
    handling ORCIDs based on the string representation of a valid ORCID.

    Passing True to the uri key will ensure that the function returns a
    valid ORCID with the http://orcid.org prefix as per the specification.

    @param identifier: Target string to extract from.
    @param uri: True to return an ORCID URI, None defaults to return the ORCID.
    @return: ORCID without prefix or None if no ORCID is found.
    """
    result = orcid_regex.match(identifier.strip())
    if result is None:
        return None
    elif uri:
        return "http://orcid.org/" + result.group(2)
    else:
        return result.group(2)


def calculate_orcid_checksum_digit(orcid):
    """
    Calculates the ORCID Checksum on the 'digit' component of an ORCID.

    @param orcid: ORCID String representation in the format of dddd-dddd-dddd-dddC
    @return: String representation of 'C' the checksum digit in range 0-9 and X
    """
    clean_orcid = orcid[:-1].replace("-", "")
    assert len(clean_orcid) == 15

    total = 0
    for char in clean_orcid:
        total = (total + int(char)) * 2

    remainder = total % 11
    result = (12 - remainder) % 11

    if result == 10:
        return "X"
    else:
        return str(result)


def is_orcid_checksum_matching(orcid):
    """
    Compares the validity of a supplied ORCID using the checksum.

    @param orcid: ORCID String representation in the format of dddd-dddd-dddd-dddC
    @return: Boolean of whether the ORCID is valid based on the checksum
    """
    assert len(orcid) == 19
    caps_orcid = orcid.upper()

    return calculate_orcid_checksum_digit(orcid) == caps_orcid[-1:]


def is_valid_orcid(identifier):
    """
    Complete validation of an ORCID through format and its checksum.

    @param identifier: The string of an identifier to check.
    @return: Boolean representing the statement.
    """
    orcid = get_orcid_from_string(identifier)

    if orcid is None:
        return False
    else:
        return is_orcid_checksum_matching(orcid)


def is_inspire_id(identifier):
    """
    Checks if a given ID matches the format of an INSPIRE ID.

    @param identifier: The string of an identifier to check.
    @return: Boolean representing the statement.
    """
    result = inspire_regex.match(identifier.strip())
    return result is not None


def is_orcid_or_inspire_id(identifier):
    """
    Checks if a given ID is a ORCID or INSPIRE ID.

    @param identifier: The string of an identifier to check.
    @return: ORCID_ID or INSPIRE_ID constant or None if neither.
    """
    if is_valid_orcid(identifier):
        return ORCID_ID
    elif is_inspire_id(identifier):
        return INSPIRE_ID
    else:
        return None


def is_arxiv_id_new(identifier):
    """
    Checks if a given ID matches the format of a new arXiv ID.

    examples: arXiv:1234.1234, arXiv:1234.1234v2
    @param identifier: The string of an identifier to check.
    @return: Boolean representing the statement.
    """
    result = arxiv_new_regex.match(identifier.strip())
    return result is not None


def is_arxiv_id_old(identifier):
    """
    Checks if a given ID matches the format of an old arXiv ID.

    examples: arXiv:hep-th/9901001, arXiv:hep-th/9901001v1
    @param identifier: The string of an identifier to check.
    @return: Boolean representing the statement.
    """
    result = arxiv_old_regex.match(identifier.strip())
    return result is not None


def is_arxiv_id(identifier):
    """
    Checks if a given ID matches the format of any arXiv ID scheme.

    examples: arXiv:hep-th/9901001, arXiv:1234.1234
    @param identifier: The string of an identifier to check.
    @return: Boolean representing the statement.
    """
    return is_arxiv_id_new(identifier) or is_arxiv_id_old(identifier)


def is_doi(identifier):
    """
    Checks if a given ID matches the format of a DOI.

    examples: 10.1016/S0735-1097(98)00347-7, 10.1007/978-3-642-28108-2_19
    @param identifier: The string of an identifier to check.
    @return: Boolean representing the statement.
    """
    result = doi_regex.match(identifier.strip())
    return result is not None


def get_doi(identifier):
    """
    Extracts doi from a given ID that matches the format of a DOI.

    examples: 10.1016/S0735-1097(98)00347-7, 10.1007/978-3-642-28108-2_19
    @param identifier: The string of an identifier to check.
    @return: doi: None or a string representing the doi.
    """
    result = doi_regex.match(identifier.strip())
    if result is not None:
        return result.group(2)
    else:
        return None


def is_arxiv_id_or_doi(identifier):
    """
    Checks if a given ID is a arXiv ID or DOI.

    @param identifier: The string of an identifier to check.
    @return: ARXIV_ID or DOI_ID constant or None if neither.
    """
    if is_arxiv_id(identifier):
        return ARXIV_ID
    elif is_doi(identifier):
        return DOI_ID
    else:
        return None


def get_title_of_doi(doi):
    try:
        xml = get_marcxml_for_doi(doi)
    except CrossrefError:
        return doi

    root = ET.fromstring(xml)

    for datafield in root.findall('datafield'):
        tag = datafield.get('tag')

        if tag == '245':
            title = datafield.find('subfield').text
            return title

    return doi


def get_xml_referer_of_arxiv_pubid(arxiv_pubid):
    arxiv_id = None

    if is_arxiv_id_new(arxiv_pubid):
        result = arxiv_new_regex.match(arxiv_pubid)
        arxiv_id = arxiv_pubid[len(result.group(1)):]
    elif is_arxiv_id_old(arxiv_pubid):
        arxiv_id = arxiv_pubid

    if arxiv_id is None:
        return None

    # TODO: the below url should be configurable
    referer = 'http://export.arxiv.org/oai2?verb=GetRecord&identifier=oai:arXiv.org:%s&metadataPrefix=oai_dc' % arxiv_id

    return referer


def get_title_of_arxiv_pubid(arxiv_pubid):
    def get_title_from_arxiv_xml(tree, tags):
        try:
            tag = tags.popleft()
        except IndexError:
            return tree.text

        for descendant in tree:
            if descendant.tag.endswith(tag):
                return get_title_from_arxiv_xml(descendant, tags)

        return None

    xml_referer = get_xml_referer_of_arxiv_pubid(arxiv_pubid)
    if xml_referer is None:
        return arxiv_pubid

    try:
        fxml = urlopen(xml_referer)
        xml = fxml.read()
        fxml.close()
        root = ET.fromstring(xml)
    except HTTPError:
        return arxiv_pubid

    title = get_title_from_arxiv_xml(root, deque(['GetRecord', 'record', 'metadata', 'dc', 'title']))

    if title:
        return title

    return arxiv_pubid


def proc_f(function, results_q, return_result, args, kwargs):
    identity = os.getpid()
    retdict = {'id': identity, 'exception': None, 'result': None}
    try:
        retval = function(*args, **kwargs)
        if return_result:
            retdict['result'] = retval
    except Exception as e:
        retdict['exception'] = e
    finally:
        results_q.put(retdict)


def schedule_workers(
    function,
    args,
    max_processes=mp.cpu_count(),
    with_kwargs=False,
    return_results=False,
        raise_exceptions=True):
    '''
    This function should be used as a scheduler for multithreaded jobs.
    It is necessary to specify whether there are keyword arguments used (with_kwargs flag).


    @param function: function to call for each worker.
    @type function: func

    @param args: list of tuples where each tuple contains positional arguments.
    @type args: list or list tuple (if with_kwargs)

    @param max_processess:
        the maximum number of processes to spawn. By default,
        the number of cores.
    @type max_processes: int

    @param with_kwargs:
        Indicates whether kwargs are present. args must contain
        a list of 2-tuples where the first component represents
        positional args and the second represents kwargs.
    @type with_kwargs: bool

    #param rise_exceptions:
        If a process raises an exception, terminate everything and raise
    '''
    results_q = Queue()
    results = list()

    processes = dict()

    jobs = list(args)
    # jobs gets popped from the right....
    jobs.reverse()

    while jobs:
        if with_kwargs:
            args, kwargs = jobs.pop()
        else:
            args = jobs.pop()
            kwargs = dict()

        assigned = False
        while not assigned:
            if len(processes) <= max_processes:
                new_proc = mp.Process(target=proc_f, args=(function, results_q, return_results, args, kwargs))
                new_proc.start()
                processes[new_proc.pid] = new_proc
                assigned = True
                break
            else:
                retval = results_q.get()
                if retval['exception']:
                    if raise_exceptions:
                        for pid, proc in processes.iteritems():
                            proc.terminate()
                        raise retval['exception']
                else:
                    results.append(retval['result'])
                processes[retval['id']].join()
                processes[retval['id']].terminate()
                del processes[retval['id']]

    while len(processes) > 0:
        retval = results_q.get()
        if retval['exception']:
            if raise_exceptions:
                raise retval['exception']
        else:
            results.append(retval['result'])
        processes[retval['id']].join()
        processes[retval['id']].terminate()
        del processes[retval['id']]

    return results


def swmap(f, args):
    return schedule_workers(f, args, return_results=True)


class defaultdict(dict):

    '''
    Implementation of defaultdict to supply missing collections library in python <= 2.4
    '''

    def __init__(self, default_factory, *args, **kwargs):
        super(defaultdict, self).__init__(*args, **kwargs)
        self.default_factory = default_factory

    def __missing__(self, key):
        try:
            self[key] = self.default_factory()
        except TypeError:
            raise KeyError("Missing key %s" % (key,))
        else:
            return self[key]

    def __getitem__(self, key):
        try:
            return super(defaultdict, self).__getitem__(key)
        except KeyError:
            return self.__missing__(key)


# python2.4 compatibility layer.
try:
    any([True])
except:
    def any(x):
        for element in x:
            if element:
                return True
        return False
bai_any = any

try:
    all([True])
except:
    def all(x):
        for element in x:
            if not element:
                return False
        return True
bai_all = all
# end of python2.4 compatibility. Please remove this horror as soon as all systems will have
# been ported to python2.6+


def print_tortoise_memory_log(summary, fp):
    stry = "PID:\t%s\tPEAK:\t%s,%s\tEST:\t%s\tBIBS:\t%s\n" % (
        summary['pid'],
        summary['peak1'],
        summary['peak2'],
        summary['est'],
        summary['bibs'])
    fp.write(stry)


def parse_tortoise_memory_log(memfile_path):
    f = open(memfile_path)
    lines = f.readlines()
    f.close()

    def line_2_dict(line):
        line = line.split('\t')
        ret = {'mem1': int(line[3].split(",")[0]),
                 'mem2': int(line[3].split(",")[1]),
                 'est': float(line[5]),
                 'bibs': int(line[7])
               }
        return ret

    return map(line_2_dict, lines)


eps = 1e-6


def is_eq(v1, v2):
    return v1 + eps > v2 and v2 + eps > v1

# Sort files in place


class FileSort(object):

    def __init__(self, inFile, outFile=None, splitSize=20):
        """ split size (in MB) """
        self._inFile = inFile
        if outFile is None:
            self._outFile = inFile
        else:
            self._outFile = outFile

        self._splitSize = splitSize * 1000000
        self.setKeyExtractMethod()

        self.reverse = False

    def setKeyExtractMethod(self, keyExtractMethod=None):
        """ key extract from line for sort method:
            def f(line):
                return line[1:3], line[5:10]
        """
        if keyExtractMethod is None:
            self._getKey = lambda line: line
        else:
            self._getKey = keyExtractMethod

    def sort(self, reverse=False):
        self.reverse = reverse
        files = self._splitFile()

        if files is None:
            """ file size <= self._splitSize """
            self._sortFile(self._inFile, self._outFile)
            return

        for fn in files:
            self._sortFile(fn)

        self._mergeFiles(files)
        self._deleteFiles(files)

    def _sortFile(self, fileName, outFile=None):
        lines = open(fileName).readlines()
        get_key = self._getKey
        data = [(get_key(line), line) for line in lines if line != '']
        data.sort(reverse=self.reverse)
        lines = [line[1] for line in data]
        if outFile is not None:
            open(outFile, 'w').write(''.join(lines))
        else:
            open(fileName, 'w').write(''.join(lines))

    def _splitFile(self):
        totalSize = os.path.getsize(self._inFile)
        if totalSize <= self._splitSize:
            # do not split file, the file isn't so big.
            return None

        fileNames = []

        fn, e = os.path.splitext(self._inFile)
        f = open(self._inFile)
        try:
            i = size = 0
            lines = []
            for line in f:
                size += len(line)
                lines.append(line)
                if size >= self._splitSize:
                    i += 1
                    tmpFile = fn + '.%03d' % i
                    fileNames.append(tmpFile)
                    open(tmpFile, 'w').write(''.join(lines))
                    del lines[:]
                    size = 0

            if size > 0:
                tmpFile = fn + '.%03d' % (i + 1)
                fileNames.append(tmpFile)
                open(tmpFile, 'w').write(''.join(lines))

            return fileNames
        finally:
            f.close()

    def _mergeFiles(self, files):
        files = [open(f) for f in files]
        lines = []
        keys = []

        for f in files:
            l = f.readline()
            lines.append(l)
            keys.append(self._getKey(l))

        buff = []
        buffSize = self._splitSize / 2
        append = buff.append
        output = open(self._outFile, 'w')
        try:
            key = min(keys)
            index = keys.index(key)
            get_key = self._getKey
            while True:
                while key == min(keys):
                    append(lines[index])
                    if len(buff) > buffSize:
                        output.write(''.join(buff))
                        del buff[:]

                    line = files[index].readline()
                    if not line:
                        files[index].close()
                        del files[index]
                        del keys[index]
                        del lines[index]
                        break
                    key = get_key(line)
                    keys[index] = key
                    lines[index] = line

                if len(files) == 0:
                    break
                # key != min(keys), see for new index (file)
                key = min(keys)
                index = keys.index(key)

            if len(buff) > 0:
                output.write(''.join(buff))
        finally:
            output.close()

    def _deleteFiles(self, files):
        for fn in files:
            os.remove(fn)


def sortFileInPlace(inFileName, outFileName=None, getKeyMethod=None, reverse=False):
    fs = FileSort(inFileName, outFileName)
    if getKeyMethod is not None:
        fs.setKeyExtractMethod(getKeyMethod)

    fs.sort(reverse=reverse)
    fs = None


import inspect


def lineno():
    a = inspect.getframeinfo(inspect.getouterframes(inspect.currentframe())[2][0])
    return (a.filename, a.lineno)


def caller():
    a = inspect.stack()[3]
    return (a[1], a[2])


def monitored(func):

    with open('/tmp/logfile', 'w') as logfile:
        logfile.write('')

    def wrap(*args, **keywords):
        with open('/tmp/logfile', 'a') as logfile:
            start_time = time.time()
            r = func(*args, **keywords)
            end_time = time.time()
            file_name, line = lineno()
            file_name = file_name.split('/')[-1]
            call_name, call_line = caller()
            call_name = call_name.split('/')[-1]
            logfile.write(
                file_name + '\t' + str(
                    line) + '\t' + str(
                        end_time - start_time) + '\t' + str(
                            call_name) + '\t' + str(
                    call_line) + '\n')
            return r

    return wrap
