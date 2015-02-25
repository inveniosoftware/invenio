# -*- mode: python; coding: utf-8; -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

from __future__ import print_function

"""
Usage: bibrankgkb %s [options]
     Examples:
       bibrankgkb --input=bibrankgkb.cfg --output=test.kb
       bibrankgkb -otest.kb -v9
       bibrankgkb -v9

 Generate options:
 -i,  --input=file          input file, default from /etc/bibrank/bibrankgkb.cfg
 -o,  --output=file         output file, will be placed in current folder
 General options:
 -h,  --help                print this help and exit
 -V,  --version             print version and exit
 -v,  --verbose=LEVEL       verbose level (from 0 to 9, default 1)
"""

__revision__ = "$Id$"

import getopt
import sys
import time
import re
import ConfigParser

from invenio.utils.url import make_invenio_opener
from invenio.config import CFG_ETCDIR
from invenio.legacy.dbquery import run_sql
from invenio.modules.ranker.registry import configuration

BIBRANK_OPENER = make_invenio_opener('BibRank')

opts_dict = {}
task_id = -1

def bibrankgkb(config):
    """Generates a .kb file based on input from the configuration file"""

    if opts_dict["verbose"] >= 1:
        write_message("Running: Generate Knowledgebase.")
    journals = {}
    journal_src = {}
    i = 0

    #Reading the configuration file
    while config.has_option("bibrankgkb","create_%s" % i):
        cfg = config.get("bibrankgkb", "create_%s" % i).split(",,")
        conv = {}
        temp = {}

        #Input source 1, either file, www or from db
        if cfg[0] == "file":
            conv = get_from_source(cfg[0], cfg[1])
            del cfg[0:2]
        elif cfg[0] == "www":
            j = 0
            urls = {}
            while config.has_option("bibrankgkb", cfg[1] % j):
                urls[j] = config.get("bibrankgkb", cfg[1] % j)
                j = j + 1
            conv = get_from_source(cfg[0], (urls, cfg[2]))
            del cfg[0:3]
        elif cfg[0] == "db":
            conv = get_from_source(cfg[0], (cfg[1], cfg[2]))
            del cfg[0:3]
        if not conv:
            del cfg[0:2]
        else:
            if opts_dict["verbose"] >= 9:
                write_message("Using last resource for converting values.")

        #Input source 2, either file, www or from db
        if cfg[0] == "file":
            temp = get_from_source(cfg[0], cfg[1])
        elif cfg[0] == "www":
            j = 0
            urls = {}
            while config.has_option("bibrankgkb", cfg[1] % j):
                urls[j] = config.get("bibrankgkb", cfg[1] % j)
                j = j + 1
            temp = get_from_source(cfg[0], (urls, cfg[2]))
        elif cfg[0] == "db":
            temp = get_from_source(cfg[0], (cfg[1], cfg[2]))
        i = i + 1

        #If a conversion file is given, the names will be converted to the correct convention
        if len(conv) != 0:
            if opts_dict["verbose"] >= 9:
                write_message("Converting between naming conventions given.")
            temp = convert(conv, temp)
        if len(journals) != 0:
            for element in temp.keys():
                if element not in journals:
                    journals[element] = temp[element]
        else:
            journals = temp

    #Writing output file
    if opts_dict["output"]:
        f = open(opts_dict["output"], 'w')
        f.write("#Created by %s\n" % __revision__)
        f.write("#Sources:\n")
        for key in journals.keys():
            f.write("%s---%s\n" % (key, journals[key]))
        f.close()
        if opts_dict["verbose"] >= 9:
            write_message("Output complete: %s" % opts_dict["output"])
            write_message("Number of hits: %s" % len(journals))

    if opts_dict["verbose"] >= 9:
        write_message("Result:")
        for key in journals.keys():
            write_message("%s---%s" % (key, journals[key]))
        write_message("Total nr of lines: %s" % len(journals))

def showtime(timeused):
    if opts_dict["verbose"] >= 9:
        write_message("Time used: %d second(s)." % timeused)

def get_from_source(type, data):
    """Read a source based on the input to the function"""

    datastruct = {}
    if type == "db":
        jvalue = run_sql(data[0])
        jname = dict(run_sql(data[1]))
        if opts_dict["verbose"] >= 9:
            write_message("Reading data from database using SQL statements:")
            write_message(jvalue)
            write_message(jname)
        for key, value in jvalue:
            if key in jname:
                key2 = jname[key].strip()
                datastruct[key2] = value
                #print "%s---%s" % (key2, value)
    elif type == "file":
        input = open(data, 'r')
        if opts_dict["verbose"] >= 9:
            write_message("Reading data from file: %s" % data)
        data = input.readlines()
        datastruct = {}
        for line in data:
            #print line
            if not line[0:1] == "#":
                key = line.strip().split("---")[0].split()
                value = line.strip().split("---")[1]
                datastruct[key] = value
                #print "%s---%s" % (key,value)
    elif type == "www":
        if opts_dict["verbose"] >= 9:
            write_message("Reading data from www using regexp: %s" % data[1])
            write_message("Reading data from url:")
        for link in data[0].keys():
            if opts_dict["verbose"] >= 9:
                write_message(data[0][link])
            page = BIBRANK_OPENER.open(data[0][link])
            input = page.read()
            #Using the regexp from config file
            reg = re.compile(data[1])
            iterator = re.finditer(reg, input)
            for match in iterator:
                if match.group("value"):
                    key = match.group("key").strip()
                    value = match.group("value").replace(",", ".")
                    datastruct[key] = value
                    if opts_dict["verbose"] == 9:
                        print("%s---%s" % (key, value))
    return datastruct

def convert(convstruct, journals):
    """Converting between names"""

    if len(convstruct) > 0 and len(journals) > 0:
        invconvstruct = dict(map(lambda x: (x[1], x[0]), convstruct.items()))
        tempjour = {}
        for name in journals.keys():
            if name in convstruct:
                tempjour[convstruct[name]] = journals[name]
            elif name in invconvstruct:
                tempjour[name] = journals[name]
        return tempjour
    else:
        return journals

def write_message(msg, stream = sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr). Useful for debugging stuff."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
        try:
            stream.write("%s\n" % msg)
        except UnicodeEncodeError:
            stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s. [must be sys.stdout or sys.stderr]\n" % stream)
    return

def usage(code, msg=''):
    "Prints usage for this module."
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)

    print(""" Usage: %s [options]
     Examples:
       %s --input=bibrankgkb.cfg --output=test.kb
       %s -otest.kb -v9
       %s -v9

 Generate options:
 -i,  --input=file          input file, default from bibrankgkb.cfg (see rankext/configuration)
 -o,  --output=file         output file, will be placed in current folder
 General options:
 -h,  --help                print this help and exit
 -V,  --version             print version and exit
 -v,  --verbose=LEVEL       verbose level (from 0 to 9, default 1)
    """ % ((sys.argv[0],) * 4), file=sys.stderr)

    sys.exit(code)

def command_line():
    global opts_dict
    long_flags = ["input=", "output=", "help", "version", "verbose="]
    short_flags = "i:o:hVv:"
    format_string = "%Y-%m-%d %H:%M:%S"
    sleeptime = ""
    try:
        opts, args = getopt.getopt(sys.argv[1:], short_flags, long_flags)
    except getopt.GetoptError as err:
        write_message(err, sys.stderr)
        usage(1)
    if args:
        usage(1)
    opts_dict = {"input": configuration.get('bibrankgkb.cfg', ''), "output":"", "verbose":1}
    sched_time = time.strftime(format_string)
    user = ""
    try:
        for opt in opts:
            if opt == ("-h","") or opt == ("--help",""):
                usage(1)
            elif opt == ("-V","") or opt == ("--version",""):
                print(__revision__)
                sys.exit(1)
            elif opt[0] in ["--input", "-i"]:
                opts_dict["input"] = configuration.get(opt[1], opt[1])
            elif opt[0] in ["--output", "-o"]:
                opts_dict["output"] = opt[1]
            elif opt[0] in ["--verbose", "-v"]:
                opts_dict["verbose"] = int(opt[1])
            else:
                usage(1)

        startCreate = time.time()
        config_file = opts_dict["input"]
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file))
        bibrankgkb(config)
        if opts_dict["verbose"] >= 9:
            showtime((time.time() - startCreate))
    except StandardError as e:
        write_message(e, sys.stderr)
        sys.exit(1)
    return

def main():
    command_line()

if __name__ == "__main__":
    main()
