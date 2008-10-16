# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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
Bibclassify keyword extractor command line entry point.
"""

__revision__ = "$Id$"

import getopt
import os
import sys
import time

try:
    from bibclassifylib import get_regular_expressions, \
        get_keywords_from_text, check_taxonomy
    from bibclassify_text_extractor import text_lines_from_local_file, \
        text_lines_from_url, is_pdf
    from bibclassify_config import CFG_BIBCLASSIFY_USER_AGENT
except ImportError, err:
    print >> sys.stderr, "Error: %s" % err
    sys.exit(1)

# Retrieve the custom configuration if it exists.
try:
    from bibclassify_config_local import *
except ImportError:
    # No local configuration was found.
    pass

_OPTIONS = {}

def display_help():
    """Prints the help message for this module."""
    print >> sys.stdout, """Usage: bibclassify [OPTION]... [FILE/URL]...
  or:  bibclassify [OPTION]... [DIRECTORY]...
Searches keywords in FILEs and/or files in DIRECTORY(ies). If a directory is
specified, BibClassify will generate keywords for all PDF documents contained
in the directory.

  -h, --help                display this help and exit
  -V, --version             output version information and exit
  -v, --verbose LEVEL       sets the verbose to LEVEL (=0)
  -k, --skos-taxonomy FILE  sets the FILE to read the RDF/SKOS taxonomy from
  -K, --vocabulary FILE     sets the FILE to read the controlled vocabulary
                              from
  -o, --output-mode TYPE    changes the output format to TYPE (text, marcxml or
                              html) (=text)
  -s, --spires              outputs keywords in the SPIRES format
  -n, --keywords-number INT sets the number of keywords displayed (=20), use 0
                              to set no limit
  -m, --matching-mode TYPE  changes the search mode to TYPE (full or partial)
                              (=full)
  --detect-author-keywords  detect keywords that are explicitely written in the
                              document
  --check-taxonomy          checks the taxonomy and reports warnings and errors
  --rebuild-cache           ignores the existing cache and regenerates it
  --no-cache                don't cache the taxonomy

Backward compatibility (using these options is discouraged):
  -q                        equivalent to -s
  -f FILE URL               sets the file to read the keywords from

Example:
    $ bibclassify -k HEP.rdf http://arxiv.org/pdf/0808.1825
    $ bibclassify -k HEP.rdf article.pdf
    $ bibclassify -k HEP.rdf directory/"""
    sys.exit(0)

def main():
    """Main function """
    read_options(sys.argv[1:])

    # taxonomy check
    if _OPTIONS["check_taxonomy"]:
        print >> sys.stdout, ("Checking taxonomy file %s" %
            _OPTIONS["taxonomy"])
        check_taxonomy(_OPTIONS["taxonomy"])
    # End of taxonomy check.

    # Initialize cache
    get_regular_expressions(taxonomy=_OPTIONS["taxonomy"],
        vocabulary=_OPTIONS["vocabulary"],
        rebuild=_OPTIONS["rebuild_cache"], no_cache=_OPTIONS["no_cache"])

    # Get the fulltext for each source.
    sources = {}
    for entry in _OPTIONS["text_files"]:
        text_lines = None
        if os.path.isdir(entry):
            for filename in os.listdir(entry):
                if (os.path.isfile(entry + filename) and
                    is_pdf(entry + filename)):
                    text_lines = text_lines_from_local_file(entry + filename)
                    sources[filename] = text_lines
        elif os.path.isfile(entry):
            text_lines = text_lines_from_local_file(entry)
            sources[os.path.basename(entry)] = text_lines
        else:
            # Treat as a URL.
            text_lines = text_lines_from_url(entry,
                user_agent=CFG_BIBCLASSIFY_USER_AGENT)
            sources[entry.split("/")[-1]] = text_lines

    # For each identified source, check the keywords and output them.
    for source, text_lines in sources.iteritems():
        if _OPTIONS["output_mode"] == "text":
            print >> sys.stdout, "Input file: " + source
        print >> sys.stdout, get_keywords_from_text(text_lines,
            output_mode=_OPTIONS["output_mode"],
            output_limit=_OPTIONS["output_limit"],
            spires=_OPTIONS["spires"],
            match_mode=_OPTIONS["match_mode"],
            with_author_keywords=_OPTIONS["with_author_keywords"])

def read_options(options_string):
    """Reads the options, test if the specified values are consistent and
    populates the options dictionary."""
    global _OPTIONS
    _OPTIONS = {
        "check_taxonomy": False,
        "spires": False,
        "output_limit": 20,
        "text_files": [],
        "taxonomy": "",
        "vocabulary": "",
        "output_mode": "text",
        "verbose": 0,
        "match_mode": "full",
        "output_prefix": None,
        "rebuild_cache": False,
        "no_cache": False,
        "with_author_keywords": False,
    }

    output_modes = ("html", "text", "marcxml")
    modes = ("full", "partial")

    try:
        long_flags = ["taxonomy=", "output-mode=", "verbose=", "spires",
                      "keywords-number=", "matching-mode=", "help", "version",
                      "file", "rebuild-cache", "no-limit", "no-cache",
                      "check-taxonomy", "detect-author-keywords",
                      "vocabulary="]
        short_flags = "f:k:t:o:n:m:v:sqhV"
        opts, args = getopt.gnu_getopt(options_string, short_flags, long_flags)
    except getopt.GetoptError, err1:
        print >> sys.stderr, "Options problem: %s" % err1
        usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            display_help()
        elif opt in ("-V", "--version"):
            try:
                from invenio.config import CFG_VERSION
                print >> sys.stdout, ("CDS Invenio/%s bibclassify/%s" %
                    (CFG_VERSION, CFG_VERSION))
            except ImportError:
                print >> sys.stdout, "CDS Invenio bibclassify/standalone"
            sys.exit(1)
        elif opt in ("-v", "--verbose"):
            _OPTIONS["verbose"] = arg
        elif opt in ("-k", "--taxonomy"):
            if os.access(arg, os.R_OK):
                _OPTIONS["taxonomy"] = arg
            else:
                try:
                    from invenio.config import CFG_ETCDIR
                except ImportError:
                    # bibclassifylib takes care of error messages.
                    _OPTIONS["taxonomy"] = arg
                else:
                    _OPTIONS["taxonomy"] = CFG_ETCDIR + os.sep + \
                        'bibclassify' + os.sep + arg
        elif opt in ("-o", "--output-mode"):
            _OPTIONS["output_mode"] = arg.lower()
        elif opt in ("-m", "--matching-mode"):
            _OPTIONS["match_mode"] = arg.lower()
        # -q for backward compatibility
        elif opt in ("-s", "--spires", "-q"):
            _OPTIONS["spires"] = True
        elif opt in ("-n", "--nkeywords"):
            _OPTIONS["output_limit"] = arg
        elif opt == "--rebuild-cache":
            _OPTIONS["rebuild_cache"] = True
        elif opt == "--no-cache":
            _OPTIONS["no_cache"] = True
        elif opt == "--write-to-file":
            _OPTIONS["output_prefix"] = arg
        # -f for compatibility reasons
        elif opt in ("-f", "--file"):
            _OPTIONS["text_files"].append(arg)
        elif opt == "--check-taxonomy":
            _OPTIONS["check_taxonomy"] = True
        elif opt == "--detect-author-keywords":
            _OPTIONS["with_author_keywords"] = True
        elif opt in("-t", "--vocabulary"):
            if os.access(arg, os.R_OK):
                _OPTIONS["vocabulary"] = arg
            else:
                try:
                    from invenio.config import CFG_ETCDIR
                except ImportError:
                    # bibclassifylib takes care of error messages.
                    _OPTIONS["vocabulary"] = arg
                else:
                    _OPTIONS["vocabulary"] = CFG_ETCDIR + os.sep + \
                        'bibclassify' + os.sep + arg

    if not opts and not args:
        display_help()

    _OPTIONS["text_files"] += args

    # Test if the options are consistent.
    if not args:
        if not _OPTIONS["check_taxonomy"] and not _OPTIONS["text_files"]:
            print >> sys.stderr, "ERROR: please specify a file or directory."
            usage()
    if not (_OPTIONS["taxonomy"] or _OPTIONS["vocabulary"]):
        print >> sys.stderr, "ERROR: please specify a taxonomy file (-k)."
        usage()
    if _OPTIONS["output_mode"] not in output_modes:
        print >> sys.stderr, ("ERROR: output (-o) should be TEXT, MARCXML or "
            "HTML.")
        usage()
    if _OPTIONS["match_mode"] not in modes:
        print >> sys.stderr, "ERROR: mode (-m) should be FULL or PARTIAL."
        usage()
    if _OPTIONS["taxonomy"] and _OPTIONS["vocabulary"]:
        print >> sys.stderr, ("ERROR: bibclassify doesn't support both a "
            "taxonomy file and a vocabulary file.")
        usage()
    try:
        _OPTIONS["output_limit"] = int(_OPTIONS["output_limit"])
        if _OPTIONS["output_limit"] < 0:
            print >> sys.stderr, ("ERROR: output limit must be a positive "
                "integer.")
    except ValueError:
        print >> sys.stderr, ("ERROR: output limit must be a positive "
            "integer.")
        usage()

def usage():
    """Displays usage (single line) and exit."""
    # TODO: write usage
    display_help()
    sys.exit(1)

def version():
    """Display BibClassify version and exit."""
    # TODO
    display_help()
    sys.exit(0)

def write_message(msg, stream=sys.stdout, verbose=1):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).
    Useful for debugging stuff. Copied from bibtask.py."""
    if msg and _OPTIONS["verbose"] >= verbose:
        if stream == sys.stdout or stream == sys.stderr:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ",
                                       time.localtime()))
            try:
                stream.write("%s\n" % msg)
            except UnicodeEncodeError:
                stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
                stream.flush()
        else:
            sys.stderr.write("Unknown stream %s. [must be sys.stdout or "
                             "sys.stderr]\n" % stream)

if __name__ == '__main__':
    main()

