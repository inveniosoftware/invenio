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
BibClassify command-line interface.

This modules provides a CLI for BibClassify. It reads the options and calls
the method output_keywords_for_sources from bibclassify_engine.
"""

import getopt
import sys

STANDALONE = False

try:
    from invenio.bibclassify_engine import output_keywords_for_sources
    from invenio.bibclassify_utils import write_message, set_verbose_level
    from invenio.bibclassify_daemon import bibclassify_daemon
    from invenio.bibclassify_ontology_reader import check_taxonomy
except ImportError, err:
    from bibclassify_engine import output_keywords_for_sources
    from bibclassify_utils import write_message, set_verbose_level
    from bibclassify_ontology_reader import check_taxonomy
    write_message("WARNING: Running in standalone mode.", stream=sys.stderr,
        verbose = 2)
    STANDALONE = True

# Retrieve the custom configuration if it exists.
try:
    from bibclassify_config_local import *
except ImportError:
    # No local configuration was found.
    pass

def get_recids_list(recids_string):
    """Returns a list of recIDs."""
    recids = {}
    elements = recids_string.split(",")
    for element in elements:
        bounds = element.split("-")
        bounds_nb = len(bounds)
        if bounds_nb == 1:
            # Single record.
            recids[int(element)] = None
        elif bounds_nb == 2:
            # Range
            min_bound = int(bounds[0])
            max_bound = int(bounds[1])
            if min_bound > max_bound:
                min_bound, max_bound = max_bound, min_bound
            elif min_bound == max_bound:
                recids[min_bound] = None
            else:
                for i in range(int(bounds[0]), int(bounds[1]) + 1):
                    recids[i] = None
        else:
            # FIXME change type of exception
            raise ValueError("Format error in recids ranges.")

    return recids.keys()

def main():
    """Main function """
    arguments = sys.argv
    for index, argument in enumerate(arguments):
        if 'bibclassify' in argument:
            break
    arguments = arguments[index+1:]

    run_as_daemon = False

    # Check if running in standalone or daemon mode.
    if not arguments:
        run_as_daemon = True
    elif len(arguments) == 1 and arguments[0].isdigit():
        # Running the task with its PID number (bibsched style).
        run_as_daemon = True

    specific_daemon_options = ('-i', '--recid', '-c', '--collection', '-f')
    for option in specific_daemon_options:
        for arg in arguments:
            if arg.startswith(option):
                run_as_daemon = True

    if run_as_daemon:
        bibclassify_daemon()
    else:
        options = _read_options(arguments)

        if options['check_taxonomy']:
            check_taxonomy(options['taxonomy'])

        output_keywords_for_sources(options["text_files"],
            options["taxonomy"],
            rebuild_cache=options["rebuild_cache"],
            no_cache=options["no_cache"],
            output_mode=options["output_mode"],
            output_limit=options["output_limit"],
            spires=options["spires"],
            match_mode=options["match_mode"],
            with_author_keywords=options["with_author_keywords"],
            extract_acronyms=options["extract_acronyms"],
            only_core_tags=options["only_core_tags"])

def _display_help():
    """Prints the help message for this module."""
    print """Usage: bibclassify [OPTION]... [FILE/URL]...
       bibclassify [OPTION]... [DIRECTORY]...
Searches keywords in FILEs and/or files in DIRECTORY(ies). If a directory is
specified, BibClassify will generate keywords for all PDF documents contained
in the directory.  Can also run in a daemon mode, in which case the files to
be run are looked for from the database (=records modified since the last run).

General options:
  -h, --help                display this help and exit
  -V, --version             output version information and exit
  -v, --verbose=LEVEL       sets the verbose to LEVEL (=0)
  -k, --taxonomy=NAME       sets the taxonomy NAME. It can be a simple
                            controlled vocabulary or a descriptive RDF/SKOS
                            and can be located in a local file or URL.

Standalone file mode options:
  -o, --output-mode=TYPE    changes the output format to TYPE (text, marcxml or
                            html) (=text)
  -s, --spires              outputs keywords in the SPIRES format
  -n, --keywords-number=INT sets the number of keywords displayed (=20), use 0
                            to set no limit
  -m, --matching-mode=TYPE  changes the search mode to TYPE (full or partial)
                            (=full)
  --detect-author-keywords  detect keywords that are explicitely written in the
                            document
   --extract-acronyms       outputs a list of acronyms and expansions found in
                            the document.
   --acronyms-file=FILE     if specified, the acronyms will be added to the
                            content of that file
Daemon mode options:
  -i, --recid=RECID         extract keywords for a record and store into DB
                            (=all necessary ones for pre-defined taxonomies)
  -c, --collection=COLL     extract keywords for a collection and store into DB
                            (=all necessary ones for pre-defined taxonomies)

Taxonomy management options:
  --check-taxonomy          checks the taxonomy and reports warnings and errors
  --rebuild-cache           ignores the existing cache and regenerates it
  --no-cache                don't cache the taxonomy

Backward compatibility options (discouraged):
  -q                        equivalent to -s
  -f FILE URL               sets the file to read the keywords from

Examples (standalone file mode):
    $ bibclassify -k HEP.rdf http://arxiv.org/pdf/0808.1825
    $ bibclassify -k HEP.rdf article.pdf
    $ bibclassify -k HEP.rdf directory/

Examples (daemon mode):
    $ bibclassify -u admin -s 24h -L 23:00-05:00
    $ bibclassify -u admin -i 1234
    $ bibclassify -u admin -c Preprints
"""
    sys.exit(1)

def _display_version():
    """Display BibClassify version and exit."""
    try:
        from invenio.config import CFG_VERSION
        print "\nCDS Invenio/%s bibclassify/%s\n" % (CFG_VERSION, CFG_VERSION)
    except ImportError:
        print "CDS Invenio bibclassify/standalone"
    sys.exit(1)

def _read_options(options_string):
    """Reads the options, test if the specified values are consistent and
    populates the options dictionary."""
    options = {
        "check_taxonomy": False,
        "spires": False,
        "output_limit": 20,
        "text_files": [],
        "taxonomy": "",
        "output_mode": "text",
        "match_mode": "full",
        "output_prefix": None,
        "rebuild_cache": False,
        "no_cache": False,
        "with_author_keywords": False,
        "extract_acronyms": False,
        "acronyms_file": "",
        "only_core_tags": False,
    }

    try:
        short_flags = "m:f:k:o:n:m:v:sqhV"
        long_flags = ["taxonomy=", "output-mode=", "verbose=", "spires",
            "keywords-number=", "matching-mode=", "help", "version", "file",
            "rebuild-cache", "no-limit", "no-cache", "check-taxonomy",
            "detect-author-keywords", "id:", "collection:", "modified:",
            "extract-acronyms", "acronyms-file=", "only-core-tags"]
        opts, args = getopt.gnu_getopt(options_string, short_flags, long_flags)
    except getopt.GetoptError, err1:
        print >> sys.stderr, "Options problem: %s" % err1
        _display_help()

    # 2 dictionaries containing the option linked to its destination in the
    # options dictionary.
    with_argument = {
        "-k": "taxonomy",
        "--taxonomy": "taxonomy",
        "-o": "output_mode",
        "--output-mode": "output_mode",
        "-m": "match_mode",
        "--matching-mode": "match_mode",
        "-n": "output_limit",
        "--keywords-number": "output_limit",
        "--acronyms-file": "acronyms_file",
    }

    without_argument = {
        "-s": "spires",
        "--spires": "spires",
        "-q": "spires",
        "--rebuild-cache": "rebuild_cache",
        "--no-cache": "no_cache",
        "--check-taxonomy": "check_taxonomy",
        "--detect-author-keywords": "with_author_keywords",
        "--extract-acronyms": "acronyms",
        "--only-core-tags": "only_core_tags",
    }

    for option, argument in opts:
        if option in ("-h", "--help"):
            _display_help()
        elif option in ("-V", "--version"):
            _display_version()
        elif option in ("-v", "--verbose"):
            set_verbose_level(argument)
        elif option in ("-f", "--file"):
            options["text_files"].append(argument)
        elif option in with_argument:
            options[with_argument[option]] = argument
        elif option in without_argument:
            options[without_argument[option]] = True
        else:
            # This shouldn't happen as gnu_getopt should already handle
            # that case.
            write_message("ERROR: option unrecognized -- %s" % option,
                stream=sys.stderr, verbose=1)

    # Collect the text inputs.
    options["text_files"] = args

    # Test if the options are consistent.
    # No file input. Checking the taxonomy or using old-style text
    # input?
    if not args:
        if not options["check_taxonomy"] and not options["text_files"]:
            write_message("ERROR: please specify a file or directory.",
                stream=sys.stderr, verbose=0)
            sys.exit(0)
    # No taxonomy input.
    elif not options["taxonomy"]:
        write_message("ERROR: please specify a taxonomy file.",
            stream=sys.stderr, verbose=0)
        sys.exit(0)
    # Output mode is correct?
    elif options["output_mode"]:
        options["output_mode"] = options["output_mode"].lower() # sanity
        if options["output_mode"] not in ("text", "marcxml", "html"):
            write_message("ERROR: output (-o) should be TEXT, MARCXML or HTML.",
                          stream=sys.stderr, verbose=0)
            sys.exit(0)
    # Match mode is correct?
    elif options["match_mode"]:
        options["match_mode"] = options["match_mode"].lower() # sanity
        if options["match_mode"] not in ("full", "partial"):
            write_message("ERROR: mode (-m) should be FULL or PARTIAL.",
                          stream=sys.stderr, verbose=0)
            sys.exit(0)
    # Output limit is correct?
    try:
        options["output_limit"] = int(options["output_limit"])
        if options["output_limit"] < 0:
            write_message("ERROR: output limit must be a positive integer.",
                stream=sys.stderr, verbose=0)
            sys.exit(0)
    except ValueError:
        write_message("ERROR: output limit must be a positive integer.",
            stream=sys.stderr, verbose=0)
        sys.exit(0)

    return options

if __name__ == '__main__':
    main()
