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
"""
bibauthorid_file_utils
    This function supplies methods to read and write the memory cache from
    and to files. to save space and ensure integrity of the files, the
    marshal-dumped content of the mem cache will be zipped in the files.
"""

import os
import sys

import bibauthorid_structs as dat
import bibauthorid_config as bconfig

from marshal import dumps, loads
from zlib import decompress, compress


def populate_structs_from_files(work_dir, results=False):
    '''
    Reads the content of the files in 'work_dir' and tries to load the
    contained data in the respective memory cache. These files are created
    by the daemon's -G or --prepare-grid function.

    The files to be read are:
        - authornames.dat
        - virtual_authors.dat
        - virtual_author_data.dat
        - virtual_author_clusters.dat
        - virtual_author_cluster_cache.dat
        - realauthors.dat
        - realauthor_data.dat
        - doclist.dat
        - records.dat
        - ids.dat
        - ra_va_cache.dat

    @param work_dir: the directory to read the files from
    @type work_dir: string
    @return: Returns True if the process finished without error. If it fails,
        the program will exit with system error code 1
    @rtype: boolean
    '''
    if work_dir.endswith("/"):
        work_dir = work_dir[:-1]

    bconfig.LOGGER.log(25, "Reading files from %s to mem cache" % (work_dir,))

    if not os.path.exists(work_dir):
        bconfig.LOGGER.critical("Job directory does not exist. Aborting.")
        raise IOError

    dat.reset_mem_cache(True)

    try:

        dfile = open("%s/authornames.dat" % (work_dir), "r")
        dat.AUTHOR_NAMES = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/virtual_authors.dat" % (work_dir), "r")
        dat.VIRTUALAUTHORS = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/virtual_author_data.dat" % (work_dir), "r")
        dat.VIRTUALAUTHOR_DATA = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/virtual_author_clusters.dat" % (work_dir), "r")
        dat.VIRTUALAUTHOR_CLUSTERS = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/virtual_author_cluster_cache.dat" % (work_dir), "r")
        dat.VIRTUALAUTHOR_CLUSTER_CACHE = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/realauthors.dat" % (work_dir), "r")
        dat.REALAUTHORS = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/realauthor_data.dat" % (work_dir), "r")
        dat.REALAUTHOR_DATA = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/doclist.dat" % (work_dir), "r")
        dat.DOC_LIST = loads(decompress(dfile.read()))
        dfile.close()

        if not results:
            dfile = open("%s/records.dat" % (work_dir), "r")
            dat.RELEVANT_RECORDS = loads(decompress(dfile.read()))
            dfile.close()

        dfile = open("%s/ids.dat" % (work_dir), "r")
        dat.ID_TRACKER = loads(decompress(dfile.read()))
        dfile.close()

        dfile = open("%s/ra_va_cache.dat" % (work_dir), "r")
        dat.RA_VA_CACHE = loads(decompress(dfile.read()))
        dfile.close()

    except IOError, message:
        bconfig.LOGGER.exception("IOError while trying to read from file %s."
                      % (message,))
        raise Exception()
    except ValueError:
        bconfig.LOGGER.exception("Failed to de-serialize code.")
        raise Exception()

    bconfig.LOGGER.log(25, "Done. All files read in mem cache")

    return True


def write_mem_cache_to_files(destination_dir, lnames=None, is_result=False):
    '''
    Reads every memory cache and writes its contents to the file in the
    specified directory.

    @param destination_dir: path to the final storage directory.
    @type destination_dir: string
    @param lnames: list of last names in human readable form
    @type lnames: list of strings
    '''
    bconfig.LOGGER.log(25, "Writing mem cache files to %s"
                       % (destination_dir,))

    if not os.path.exists(destination_dir):
        bconfig.LOGGER.error("Destination directory does not exist!")
        return False

    if destination_dir.endswith("/"):
        destination_dir = destination_dir[0:-1]

    if lnames:
        bconfig.LOGGER.log(25, "A total of %s recs will be stored."
                      % (len(dat.RELEVANT_RECORDS)))

        try:
            hr_name_file = open("%s/names.txt" % (destination_dir), 'w')
            hr_name_file.write(str(lnames))
            hr_name_file.close()
        except IOError, message:
            bconfig.LOGGER.exception("IOError while trying to write to file %s"
                      % (message,))

    try:
        dfile = open("%s/authornames.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.AUTHOR_NAMES)))
        dfile.close()

        dfile = open("%s/virtual_authors.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.VIRTUALAUTHORS)))
        dfile.close()

        dfile = open("%s/virtual_author_data.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.VIRTUALAUTHOR_DATA)))
        dfile.close()

        dfile = open("%s/virtual_author_clusters.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.VIRTUALAUTHOR_CLUSTERS)))
        dfile.close()

        dfile = open("%s/virtual_author_cluster_cache.dat"
                     % (destination_dir), "w")
        dfile.write(compress(dumps(dat.VIRTUALAUTHOR_CLUSTER_CACHE)))
        dfile.close()

        dfile = open("%s/realauthors.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.REALAUTHORS)))
        dfile.close()

        dfile = open("%s/realauthor_data.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.REALAUTHOR_DATA)))
        dfile.close()

        dfile = open("%s/doclist.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.DOC_LIST)))
        dfile.close()

        if not is_result:
            dfile = open("%s/records.dat" % (destination_dir), "w")
            dfile.write(compress(dumps(dat.RELEVANT_RECORDS)))
            dfile.close()

        dfile = open("%s/ids.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.ID_TRACKER)))
        dfile.close()

        dfile = open("%s/ra_va_cache.dat" % (destination_dir), "w")
        dfile.write(compress(dumps(dat.RA_VA_CACHE)))
        dfile.close()
    except IOError, message:
        bconfig.LOGGER.exception("IOError while trying to handle file %s."
                      % (message,))
        sys.exit(1)
    except ValueError:
        bconfig.LOGGER.exception("Failed to serialize code.")
        sys.exit(1)


def make_directory(path, force=False):
    '''
    Checks if a specified directory exists. If not, it will create one.
    If a directory exists, false shall be returned to indicate a potentially
    dangerous operation.

    @param path: path to the directory
    @type path: string
    '''
    if os.path.exists(path) and not force:
        bconfig.LOGGER.error("Directory already exists: %s" % (path,))
        return False
    else:
        os.mkdir(path)
        return True


def tail(filepath, read_size=1024):
    """
    This function returns the last line of a file.
    @param filepath: path to file
    @param read_size:  data is read in chunks of this size
        (optional, default=1024)
    @raise IOError: if file cannot be processed.
    """
    # U is to open it with Universal newline support
    filepointer = open(filepath, 'rU')
    offset = read_size
    filepointer.seek(0, 2)
    file_size = filepointer.tell()

    if file_size == 0:
        raise IOError

    while 1:
        if file_size < offset:
            offset = file_size

        filepointer.seek(-1 * offset, 2)
        read_str = filepointer.read(offset)

        if read_str[offset - 1] == '\n':
            read_str = read_str[0:-1]

        lines = read_str.split('\n')

        if len(lines) > 1:
            return lines[len(lines) - 1]

        if offset == file_size:
            return read_str

        offset += read_size
        filepointer.close()
