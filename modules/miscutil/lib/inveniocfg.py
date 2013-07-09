# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
Invenio configuration and administration CLI tool.

Usage: inveniocfg [options]

General options:
   -h, --help               print this help
   -V, --version            print version number

Options to finish your installation:
   --create-apache-conf     create Apache configuration files
   --create-tables          create DB tables for Invenio
   --load-bibfield-conf     load the BibField configuration
   --load-webstat-conf      load the WebStat configuration
   --drop-tables            drop DB tables of Invenio
   --check-openoffice       check for correctly set up of openoffice temporary directory

Options to set up and test a demo site:
   --create-demo-site       create demo site
   --load-demo-records      load demo records
   --remove-demo-records    remove demo records, keeping demo site
   --drop-demo-site         drop demo site configurations too
   --run-unit-tests         run unit test suite (needs demo site)
   --run-regression-tests   run regression test suite (needs demo site)
   --run-web-tests          run web tests in a browser (needs demo site, Firefox, Selenium IDE)

Options to update config files in situ:
   --update-all             perform all the update options
   --update-config-py       update config.py file from invenio.conf file
   --update-dbquery-py      update dbquery.py with DB credentials from invenio.conf
   --update-dbexec          update dbexec with DB credentials from invenio.conf
   --update-bibconvert-tpl  update bibconvert templates with CFG_SITE_URL from invenio.conf
   --update-web-tests       update web test cases with CFG_SITE_URL from invenio.conf

Options to update DB tables:
   --reset-all              perform all the reset options
   --reset-sitename         reset tables to take account of new CFG_SITE_NAME*
   --reset-siteadminemail   reset tables to take account of new CFG_SITE_ADMIN_EMAIL
   --reset-fieldnames       reset tables to take account of new I18N names from PO files
   --reset-recstruct-cache  reset record structure cache according to CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE
   --reset-recjson-cache    reset record json cache according to CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE

Options to upgrade your installation:
    --upgrade                       apply all pending upgrades
    --upgrade-check                 run pre-upgrade checks for all pending upgrades
    --upgrade-show-pending          show pending upgrades ready to be applied
    --upgrade-show-applied          show history of applied upgrades
    --upgrade-create-standard-recipe create a new upgrade recipe (for developers)
    --upgrade-create-release-recipe create a new release upgrade recipe (for developers)

Options to help the work:
   --list                   print names and values of all options from conf files
   --get <some-opt>         get value of a given option from conf files
   --conf-dir </some/path>  path to directory where invenio*.conf files are [optional]
   --detect-system-details  print system details such as Apache/Python/MySQL versions
"""

__revision__ = "$Id$"

from ConfigParser import ConfigParser
from optparse import OptionParser, OptionGroup, IndentedHelpFormatter, Option, \
    OptionError
import os
import re
import shutil
import socket
import sys
import zlib


def print_usage():
    """Print help."""
    print __doc__


def get_version():
    """ Get running version of Invenio """
    from invenio.config import CFG_VERSION
    return CFG_VERSION


def print_version():
    """Print version information."""
    print get_version()


def convert_conf_option(option_name, option_value):
    """
    Convert conf option into Python config.py line, converting
    values to ints or strings as appropriate.
    """

    ## 1) convert option name to uppercase:
    option_name = option_name.upper()

    ## 1a) adjust renamed variables:
    if option_name in ['CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_DOCTYPES',
                          'CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_RESTRICTIONS',
                          'CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_MISC',
                          'CFG_WEBSUBMIT_FILESYSTEM_BIBDOC_GROUP_LIMIT',
                          'CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS',
                          'CFG_WEBSUBMIT_DESIRED_CONVERSIONS']:
        new_option_name = option_name.replace('WEBSUBMIT', 'BIBDOCFILE')
        print >> sys.stderr, ("""WARNING: %s has been renamed to %s.
Please, update your invenio-local.conf file accordingly.""" % (option_name, new_option_name))
        option_name = new_option_name


    ## 2) convert option value to int or string:
    if option_name in ['CFG_BIBUPLOAD_REFERENCE_TAG',
                       'CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG',
                       'CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG',
                       'CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG',
                       'CFG_BIBUPLOAD_STRONG_TAGS',
                       'CFG_BIBFORMAT_HIDDEN_TAGS']:
        # some options are supposed be string even when they look like
        # numeric
        option_value = '"' + option_value + '"'
    else:
        try:
            option_value = int(option_value)
        except ValueError:
            option_value = '"' + option_value + '"'

    ## 3a) special cases: chars regexps
    if option_name in ['CFG_BIBINDEX_CHARS_ALPHANUMERIC_SEPARATORS',
                       'CFG_BIBINDEX_CHARS_PUNCTUATION']:
        option_value = 'r"[' + option_value[1:-1] + ']"'

    ## 3abis) special cases: real regexps
    if option_name in ['CFG_BIBINDEX_PERFORM_OCR_ON_DOCNAMES',
                       'CFG_BATCHUPLOADER_WEB_ROBOT_AGENTS',
                       'CFG_BIBUPLOAD_INTERNAL_DOI_PATTERN']:
        option_value = 'r"' + option_value[1:-1] + '"'

    ## 3b) special cases: True, False, None
    if option_value in ['"True"', '"False"', '"None"']:
        option_value = option_value[1:-1]

    ## 3c) special cases: dicts and real pythonic lists
    if option_name in ['CFG_WEBSEARCH_FIELDS_CONVERT',
                       'CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS',
                       'CFG_WEBSEARCH_FULLTEXT_SNIPPETS',
                       'CFG_WEBSEARCH_FULLTEXT_SNIPPETS_CHARS',
                       'CFG_SITE_EMERGENCY_EMAIL_ADDRESSES',
                       'CFG_BIBMATCH_FUZZY_WORDLIMITS',
                       'CFG_BIBMATCH_QUERY_TEMPLATES',
                       'CFG_WEBSEARCH_SYNONYM_KBRS',
                       'CFG_BIBINDEX_SYNONYM_KBRS',
                       'CFG_WEBCOMMENT_EMAIL_REPLIES_TO',
                       'CFG_WEBCOMMENT_RESTRICTION_DATAFIELD',
                       'CFG_WEBCOMMENT_ROUND_DATAFIELD',
                       'CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS',
                       'CFG_BIBSCHED_NODE_TASKS',
                       'CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE',
                       'CFG_OAI_METADATA_FORMATS',
                       'CFG_BIBDOCFILE_DESIRED_CONVERSIONS',
                       'CFG_BIBDOCFILE_BEST_FORMATS_TO_EXTRACT_TEXT_FROM',
                       'CFG_WEB_API_KEY_ALLOWED_URL',
                       'CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_MISC',
                       'CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_DOCTYPES',
                       'CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_RESTRICTIONS',
                       'CFG_REFEXTRACT_KBS_OVERRIDE',
                       'CFG_OPENID_CONFIGURATIONS',
                       'CFG_OAUTH1_CONFIGURATIONS',
                       'CFG_OAUTH2_CONFIGURATIONS',
                       'CFG_BIBDOCFILE_ADDITIONAL_KNOWN_MIMETYPES',
                       'CFG_BIBDOCFILE_PREFERRED_MIMETYPES_MAPPING',
                       'CFG_BIBSCHED_NON_CONCURRENT_TASKS',
                       'CFG_REDIS_HOSTS',
                       'CFG_BIBSCHED_INCOMPATIBLE_TASKS',
                       'CFG_ICON_CREATION_FORMAT_MAPPINGS',
                       'CFG_BIBSCHED_INCOMPATIBLE_TASKS',
                       'CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_ICON_SIZE',
                       'CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_ICON_DOCTYPES',
                       'CFG_BIBEDIT_AUTOCOMPLETE']:
        try:
            option_value = option_value[1:-1]
            if option_name == "CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE" and option_value.strip().startswith("{"):
                print >> sys.stderr, ("""ERROR: CFG_BIBEDIT_EXTEND_RECORD_WITH_COLLECTION_TEMPLATE
now accepts only a list of tuples, not a dictionary. Check invenio.conf for an example.
Please, update your invenio-local.conf file accordingly.""")
                sys.exit(1)
        except TypeError:
            if option_name in ('CFG_WEBSEARCH_FULLTEXT_SNIPPETS',):
                print >> sys.stderr, """WARNING: CFG_WEBSEARCH_FULLTEXT_SNIPPETS
has changed syntax: it can be customised to display different snippets for
different document types.  See the corresponding documentation in invenio.conf.
You may want to customise your invenio-local.conf configuration accordingly."""
                option_value = """{'': %s}""" % option_value
            else:
                print >> sys.stderr, "ERROR: type error in %s value %s." % \
                      (option_name, option_value)
                sys.exit(1)

    ## 3cbis) very special cases: dicts with backward compatible string
    if option_name in ['CFG_BIBINDEX_SPLASH_PAGES']:
        if option_value.startswith('"{') and option_value.endswith('}"'):
            option_value = option_value[1:-1]
        else:
            option_value = """{%s: ".*"}""" % option_value

    ## 3d) special cases: comma-separated lists
    if option_name in ['CFG_SITE_LANGS',
                       'CFG_BIBDOCFILE_ADDITIONAL_KNOWN_FILE_EXTENSIONS',
                       'CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS',
                       'CFG_BIBUPLOAD_STRONG_TAGS',
                       'CFG_BIBFORMAT_HIDDEN_TAGS',
                       'CFG_BIBSCHED_GC_TASKS_TO_REMOVE',
                       'CFG_BIBSCHED_GC_TASKS_TO_ARCHIVE',
                       'CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS',
                       'CFG_BIBUPLOAD_CONTROLLED_PROVENANCE_TAGS',
                       'CFG_BIBUPLOAD_DELETE_FORMATS',
                       'CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES',
                       'CFG_WEBSTYLE_HTTP_STATUS_ALERT_LIST',
                       'CFG_WEBSEARCH_RSS_I18N_COLLECTIONS',
                       'CFG_BATCHUPLOADER_FILENAME_MATCHING_POLICY',
                       'CFG_BIBAUTHORID_EXTERNAL_CLAIMED_RECORDS_KEY',
                       'CFG_BIBCIRCULATION_ITEM_STATUS_OPTIONAL',
                       'CFG_PLOTEXTRACTOR_DISALLOWED_TEX',
                       'CFG_OAI_FRIENDS',
                       'CFG_WEBSTYLE_REVERSE_PROXY_IPS',
                       'CFG_BIBEDIT_AUTOCOMPLETE_INSTITUTIONS_FIELDS',
                       'CFG_BIBFORMAT_DISABLE_I18N_FOR_CACHED_FORMATS',
                       'CFG_BIBFORMAT_HIDDEN_FILE_FORMATS',
                       'CFG_BIBFIELD_MASTER_FORMATS',
                       'CFG_OPENID_PROVIDERS',
                       'CFG_OAUTH1_PROVIDERS',
                       'CFG_OAUTH2_PROVIDERS',
                       'CFG_BIBFORMAT_CACHED_FORMATS',
                       'CFG_BIBEDIT_ADD_TICKET_RT_QUEUES',
                       'CFG_BIBAUTHORID_ENABLED_REMOTE_LOGIN_SYSTEMS',
                       'CFG_WEBSEARCH_BLACKLISTED_FORMATS']:
        out = "["
        for elem in option_value[1:-1].split(","):
            if elem:
                elem = elem.strip()
                if option_name in ['CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES']:
                    # 3d1) integer values
                    out += "%i, " % int(elem)
                else:
                    # 3d2) string values
                    out += "'%s', " % elem
        out += "]"
        option_value = out

    ## 3e) special cases: multiline
    if option_name == 'CFG_OAI_IDENTIFY_DESCRIPTION':
        # make triple quotes
        option_value = '""' + option_value + '""'

    ## 3f) ignore some options:
    if option_name.startswith('CFG_SITE_NAME_INTL'):
        # treated elsewhere
        return

    ## 3g) special cases: float
    if option_name in ['CFG_BIBDOCFILE_MD5_CHECK_PROBABILITY',
                       'CFG_BIBMATCH_LOCAL_SLEEPTIME',
                       'CFG_BIBMATCH_REMOTE_SLEEPTIME',
                       'CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT',
                       'CFG_BIBMATCH_FUZZY_MATCH_VALIDATION_LIMIT']:
        option_value = float(option_value[1:-1])

    ## 3h) special cases: bibmatch validation list
    if option_name in ['CFG_BIBMATCH_MATCH_VALIDATION_RULESETS']:
        option_value = option_value[1:-1]

    ## 4a) dropped variables
    if option_name in ['CFG_BATCHUPLOADER_WEB_ROBOT_AGENT']:
        print >> sys.stderr, ("""ERROR: CFG_BATCHUPLOADER_WEB_ROBOT_AGENT has been dropped in favour of
CFG_BATCHUPLOADER_WEB_ROBOT_AGENTS.
Please, update your invenio-local.conf file accordingly.""")
        sys.exit(1)
        option_value = option_value[1:-1]
    elif option_name in ['CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_DOCTYPES',
                          'CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_RESTRICTIONS',
                          'CFG_WEBSUBMIT_DOCUMENT_FILE_MANAGER_MISC',
                          'CFG_WEBSUBMIT_FILESYSTEM_BIBDOC_GROUP_LIMIT',
                          'CFG_WEBSUBMIT_ADDITIONAL_KNOWN_FILE_EXTENSIONS',
                          'CFG_WEBSUBMIT_DESIRED_CONVERSIONS']:
        new_option_name = option_name.replace('WEBSUBMIT', 'BIBDOCFILE')
        print >> sys.stderr, ("""ERROR: %s has been renamed to %s.
Please, update your invenio-local.conf file accordingly.""" % (option_name, new_option_name))
        option_name = new_option_name



    ## 5) finally, return output line:
    return '%s = %s' % (option_name, option_value)

def cli_cmd_update_config_py(conf):
    """
    Update new config.py from conf options, keeping previous
    config.py in a backup copy.
    """
    ## NOTE: the following function exists also in urlutils.py
    ## However we can't import urlutils here, as it depends on config.py
    ## to already exist, while we are in the process of creating it.
    def get_relative_url(url):
        """
        Returns the relative URL from a URL. For example:

        'http://web.net' -> ''
        'http://web.net/' -> ''
        'http://web.net/1222' -> '/1222'
        'http://web.net/wsadas/asd' -> '/wsadas/asd'

        It will never return a trailing "/".

        @param url: A url to transform
        @type url: str

        @return: relative URL
        """
        # remove any protocol info before
        stripped_site_url = url.replace("://", "")
        baseurl = "/" + "/".join(stripped_site_url.split("/")[1:])

        # remove any trailing slash ("/")
        if baseurl[-1] == "/":
            return baseurl[:-1]
        else:
            return baseurl

    print ">>> Going to update config.py..."
    ## location where config.py is:
    configpyfile = conf.get("Invenio", "CFG_PYLIBDIR") + \
                   os.sep + 'invenio' + os.sep + 'config.py'
    ## backup current config.py file:
    if os.path.exists(configpyfile):
        shutil.copy(configpyfile, configpyfile + '.OLD')
    ## here we go:
    fdesc = open(configpyfile, 'w')
    ## generate preamble:
    fdesc.write("# -*- coding: utf-8 -*-\n")
    fdesc.write("# DO NOT EDIT THIS FILE!  IT WAS AUTOMATICALLY GENERATED\n")
    fdesc.write("# FROM INVENIO.CONF BY EXECUTING:\n")
    fdesc.write("# " + " ".join(sys.argv) + "\n")
    ## special treatment for CFG_SITE_NAME_INTL options:
    fdesc.write("CFG_SITE_NAME_INTL = {}\n")
    for lang in conf.get("Invenio", "CFG_SITE_LANGS").split(","):
        fdesc.write("CFG_SITE_NAME_INTL['%s'] = \"%s\"\n" % (lang, conf.get("Invenio",
                                                                            "CFG_SITE_NAME_INTL_" + lang)))
    ## special treatment for CFG_SITE_SECURE_URL that may be empty, in
    ## which case it should be put equal to CFG_SITE_URL:
    if not conf.get("Invenio", "CFG_SITE_SECURE_URL"):
        conf.set("Invenio", "CFG_SITE_SECURE_URL",
                 conf.get("Invenio", "CFG_SITE_URL"))
    ## Special treatment of base URL, adding CFG_BASE_URL
    base_url = get_relative_url(conf.get("Invenio", "CFG_SITE_URL"))
    fdesc.write("CFG_BASE_URL = \"%s\"\n" % (base_url,))
    ## process all the options normally:
    sections = conf.sections()
    sections.sort()
    for section in sections:
        options = conf.options(section)
        options.sort()
        for option in options:
            if not option.upper().startswith('CFG_DATABASE_'):
                # put all options except for db credentials into config.py
                line_out = convert_conf_option(option, conf.get(section, option))
                if line_out:
                    fdesc.write(line_out + "\n")
    ## FIXME: special treatment for experimental variables
    ## CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES and CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE
    ## (not offering them in invenio.conf since they will be refactored)
    fdesc.write("CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE = 0\n")
    fdesc.write("CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES = [0, 1,]\n")
    ## generate postamble:
    fdesc.write("")
    fdesc.write("# END OF GENERATED FILE")
    ## we are done:
    fdesc.close()
    print "You may want to restart Apache now."
    print ">>> config.py updated successfully."

def cli_cmd_update_dbquery_py(conf):
    """
    Update lib/dbquery.py file with DB parameters read from conf file.
    Note: this edits dbquery.py in situ, taking a backup first.
    Use only when you know what you are doing.
    """
    print ">>> Going to update dbquery.py..."
    ## location where dbquery.py is:
    dbqueryconfigpyfile = conf.get("Invenio", "CFG_PYLIBDIR") + \
                    os.sep + 'invenio' + os.sep + 'dbquery_config.py'
    ## backup current dbquery.py file:
    if os.path.exists(dbqueryconfigpyfile + 'c'):
        shutil.copy(dbqueryconfigpyfile + 'c', dbqueryconfigpyfile + 'c.OLD')

    out = ["%s = '%s'\n" % (item.upper(), value) \
                        for item, value in conf.items('Invenio') \
                        if item.upper().startswith('CFG_DATABASE_')]

    fdesc = open(dbqueryconfigpyfile, 'w')
    fdesc.write("# -*- coding: utf-8 -*-\n")
    fdesc.writelines(out)
    fdesc.close()

    print "You may want to restart Apache now."
    print ">>> dbquery.py updated successfully."

def cli_cmd_update_dbexec(conf):
    """
    Update bin/dbexec file with DB parameters read from conf file.
    Note: this edits dbexec in situ, taking a backup first.
    Use only when you know what you are doing.
    """
    print ">>> Going to update dbexec..."
    ## location where dbexec is:
    dbexecfile = conf.get("Invenio", "CFG_BINDIR") + \
                    os.sep + 'dbexec'
    ## backup current dbexec file:
    if os.path.exists(dbexecfile):
        shutil.copy(dbexecfile, dbexecfile + '.OLD')
    ## replace db parameters via sed:
    out = ''
    for line in open(dbexecfile, 'r').readlines():
        match = re.search(r'^CFG_DATABASE_(HOST|PORT|NAME|USER|PASS|SLAVE)(\s*=\s*)\'.*\'$', line)
        if match:
            dbparam = 'CFG_DATABASE_' + match.group(1)
            out += "%s%s'%s'\n" % (dbparam, match.group(2),
                                   conf.get("Invenio", dbparam))
        else:
            out += line
    fdesc = open(dbexecfile, 'w')
    fdesc.write(out)
    fdesc.close()
    print ">>> dbexec updated successfully."

def cli_cmd_update_bibconvert_tpl(conf):
    """
    Update bibconvert/config/*.tpl files looking for 856
    http://.../CFG_SITE_RECORD lines, replacing URL with CFG_SITE_URL taken
    from conf file.  Note: this edits tpl files in situ, taking a
    backup first.  Use only when you know what you are doing.
    """
    print ">>> Going to update bibconvert templates..."
    ## location where bibconvert/config/*.tpl are:
    tpldir = conf.get("Invenio", 'CFG_ETCDIR') + \
             os.sep + 'bibconvert' + os.sep + 'config'
    ## find all *.tpl files:
    for tplfilename in os.listdir(tpldir):
        if tplfilename.endswith(".tpl"):
            ## change tpl file:
            tplfile = tpldir + os.sep + tplfilename
            shutil.copy(tplfile, tplfile + '.OLD')
            out = ''
            for line in open(tplfile, 'r').readlines():
                match = re.search(r'^(.*)http://.*?/%s/(.*)$' % conf.get("Invenio", 'CFG_SITE_RECORD'), line)
                if match:
                    out += "%s%s/%s/%s\n" % (match.group(1),
                                                 conf.get("Invenio", 'CFG_SITE_URL'),
                                                 conf.get("Invenio", 'CFG_SITE_RECORD'),
                                                 match.group(2))
                else:
                    out += line
            fdesc = open(tplfile, 'w')
            fdesc.write(out)
            fdesc.close()
    print ">>> bibconvert templates updated successfully."

def cli_cmd_update_web_tests(conf):
    """
    Update web test cases lib/webtest/test_*.html looking for
    <td>http://.+?[</] strings and replacing them with CFG_SITE_URL
    taken from conf file.  Note: this edits test files in situ, taking
    a backup first.  Use only when you know what you are doing.
    """
    print ">>> Going to update web tests..."
    ## location where test_*.html files are:
    testdir = conf.get("Invenio", 'CFG_PREFIX') + os.sep + \
             'lib' + os.sep + 'webtest' + os.sep + 'invenio'
    ## find all test_*.html files:
    for testfilename in os.listdir(testdir):
        if testfilename.startswith("test_") and \
               testfilename.endswith(".html"):
            ## change test file:
            testfile = testdir + os.sep + testfilename
            shutil.copy(testfile, testfile + '.OLD')
            out = ''
            for line in open(testfile, 'r').readlines():
                match = re.search(r'^(.*<td>)http://.+?([</].*)$', line)
                if match:
                    out += "%s%s%s\n" % (match.group(1),
                                         conf.get("Invenio", 'CFG_SITE_URL'),
                                         match.group(2))
                else:
                    match = re.search(r'^(.*<td>)/opt/invenio(.*)$', line)
                    if match:
                        out += "%s%s%s\n" % (match.group(1),
                                            conf.get("Invenio", 'CFG_PREFIX'),
                                            match.group(2))
                    else:
                        out += line
            fdesc = open(testfile, 'w')
            fdesc.write(out)
            fdesc.close()
    print ">>> web tests updated successfully."

def cli_cmd_reset_sitename(conf):
    """
    Reset collection-related tables with new CFG_SITE_NAME and
    CFG_SITE_NAME_INTL* read from conf files.
    """
    print ">>> Going to reset CFG_SITE_NAME and CFG_SITE_NAME_INTL..."
    from invenio.dbquery import run_sql, IntegrityError
    # reset CFG_SITE_NAME:
    sitename = conf.get("Invenio", "CFG_SITE_NAME")
    try:
        run_sql("""INSERT INTO collection (id, name, dbquery, reclist) VALUES
                                          (1,%s,NULL,NULL)""", (sitename,))
    except IntegrityError:
        run_sql("""UPDATE collection SET name=%s WHERE id=1""", (sitename,))
    # reset CFG_SITE_NAME_INTL:
    for lang in conf.get("Invenio", "CFG_SITE_LANGS").split(","):
        sitename_lang = conf.get("Invenio", "CFG_SITE_NAME_INTL_" + lang)
        try:
            run_sql("""INSERT INTO collectionname (id_collection, ln, type, value) VALUES
                         (%s,%s,%s,%s)""", (1, lang, 'ln', sitename_lang))
        except IntegrityError:
            run_sql("""UPDATE collectionname SET value=%s
                        WHERE ln=%s AND id_collection=1 AND type='ln'""",
                    (sitename_lang, lang))
    print "You may want to restart Apache now."
    print ">>> CFG_SITE_NAME and CFG_SITE_NAME_INTL* reset successfully."

def cli_cmd_reset_recstruct_cache(conf):
    """If CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE is changed, this function
    will adapt the database to either store or not store the recstruct
    format."""
    from invenio.intbitset import intbitset
    from invenio.dbquery import run_sql, serialize_via_marshal
    from invenio.search_engine import get_record, print_record
    from invenio.bibsched import server_pid, pidfile
    enable_recstruct_cache = conf.get("Invenio", "CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE")
    enable_recstruct_cache = enable_recstruct_cache in ('True', '1')
    pid = server_pid(ping_the_process=False)
    if pid:
        print >> sys.stderr, "ERROR: bibsched seems to run with pid %d, according to %s." % (pid, pidfile)
        print >> sys.stderr, "       Please stop bibsched before running this procedure."
        sys.exit(1)
    if enable_recstruct_cache:
        print ">>> Searching records which need recstruct cache resetting; this may take a while..."
        all_recids = intbitset(run_sql("SELECT id FROM bibrec"))
        good_recids = intbitset(run_sql("SELECT bibrec.id FROM bibrec JOIN bibfmt ON bibrec.id = bibfmt.id_bibrec WHERE format='recstruct' AND modification_date < last_updated"))
        recids = all_recids - good_recids
        print ">>> Generating recstruct cache..."
        tot = len(recids)
        count = 0
        for recid in recids:
            try:
                value = serialize_via_marshal(get_record(recid))
            except zlib.error, err:
                print >> sys.stderr, "Looks like XM is corrupted for record %s. Let's recover it from bibxxx" % recid
                run_sql("DELETE FROM bibfmt WHERE id_bibrec=%s AND format='xm'", (recid, ))
                xm_value = zlib.compress(print_record(recid, 'xm'))
                run_sql("INSERT INTO bibfmt(id_bibrec, format, last_updated, value) VALUES(%s, 'xm', NOW(), %s)", (recid, xm_value))
                value = serialize_via_marshal(get_record(recid))

            run_sql("DELETE FROM bibfmt WHERE id_bibrec=%s AND format='recstruct'", (recid, ))
            run_sql("INSERT INTO bibfmt(id_bibrec, format, last_updated, value) VALUES(%s, 'recstruct', NOW(), %s)", (recid, value))
            count += 1
            if count % 1000 == 0:
                print "    ... done records %s/%s" % (count, tot)
        if count % 1000 != 0:
            print "    ... done records %s/%s" % (count, tot)
        print ">>> recstruct cache generated successfully."
    else:
        print ">>> Cleaning recstruct cache..."
        run_sql("DELETE FROM bibfmt WHERE format='recstruct'")

def cli_cmd_reset_recjson_cache(conf):
    """If CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE is changed, this function
    will adapt the database to either store or not store the recjson
    format."""
    try:
        import cPickle as pickle
    except:
        import pickle
    from invenio.intbitset import intbitset
    from invenio.dbquery import run_sql
    from invenio.bibfield import get_record
    from invenio.bibsched import server_pid, pidfile
    enable_recjson_cache = conf.get("Invenio", "CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE")
    enable_recjson_cache = enable_recjson_cache in ('True', '1')
    pid = server_pid(ping_the_process=False)
    if pid:
        print >> sys.stderr, "ERROR: bibsched seems to run with pid %d, according to %s." % (pid, pidfile)
        print >> sys.stderr, "       Please stop bibsched before running this procedure."
        sys.exit(1)
    if enable_recjson_cache:
        print ">>> Searching records which need recjson cache resetting; this may take a while..."
        all_recids = intbitset(run_sql("SELECT id FROM bibrec"))
        #TODO: prevent doing all records?
        recids = all_recids
        print ">>> Generating recjson cache..."
        tot = len(recids)
        count = 0
        cli_cmd_load_bibfield_config(conf)
        for recid in recids:
            run_sql("DELETE FROM bibfmt WHERE id_bibrec=%s AND format='recjson'", (recid,))
            #TODO: Update the cache or wait for the first access
            get_record(recid)
            count += 1
            if count % 1000 == 0:
                print "    ... done records %s/%s" % (count, tot)
        if count % 1000 != 0:
            print "    ... done records %s/%s" % (count, tot)
        print ">>> recjson cache generated successfully."

def cli_cmd_reset_siteadminemail(conf):
    """
    Reset user-related tables with new CFG_SITE_ADMIN_EMAIL read from conf files.
    """
    print ">>> Going to reset CFG_SITE_ADMIN_EMAIL..."
    from invenio.dbquery import run_sql
    siteadminemail = conf.get("Invenio", "CFG_SITE_ADMIN_EMAIL")
    run_sql("DELETE FROM user WHERE id=1")
    run_sql("""INSERT INTO user (id, email, password, note, nickname) VALUES
                        (1, %s, AES_ENCRYPT(email, ''), 1, 'admin')""",
            (siteadminemail,))
    print "You may want to restart Apache now."
    print ">>> CFG_SITE_ADMIN_EMAIL reset successfully."

def cli_cmd_reset_fieldnames(conf):
    """
    Reset I18N field names such as author, title, etc and other I18N
    ranking method names such as word similarity.  Their translations
    are taken from the PO files.
    """
    print ">>> Going to reset I18N field names..."
    from invenio.messages import gettext_set_language, language_list_long
    from invenio.dbquery import run_sql, IntegrityError

    ## get field id and name list:
    field_id_name_list = run_sql("SELECT id, name FROM field")
    ## get rankmethod id and name list:
    rankmethod_id_name_list = run_sql("SELECT id, name FROM rnkMETHOD")
    ## update names for every language:
    for lang, dummy in language_list_long():
        _ = gettext_set_language(lang)
        ## this list is put here in order for PO system to pick names
        ## suitable for translation
        field_name_names = {"any field": _("any field"),
                            "title": _("title"),
                            "author": _("author"),
                            "abstract": _("abstract"),
                            "keyword": _("keyword"),
                            "report number": _("report number"),
                            "subject": _("subject"),
                            "reference": _("reference"),
                            "fulltext": _("fulltext"),
                            "collection": _("collection"),
                            "division": _("division"),
                            "year": _("year"),
                            "journal": _("journal"),
                            "experiment": _("experiment"),
                            "record ID": _("record ID")}
        ## update I18N names for every language:
        for (field_id, field_name) in field_id_name_list:
            if field_name_names.has_key(field_name):
                try:
                    run_sql("""INSERT INTO fieldname (id_field,ln,type,value) VALUES
                                (%s,%s,%s,%s)""", (field_id, lang, 'ln',
                                                field_name_names[field_name]))
                except IntegrityError:
                    run_sql("""UPDATE fieldname SET value=%s
                                WHERE id_field=%s AND ln=%s AND type=%s""",
                            (field_name_names[field_name], field_id, lang, 'ln',))
        ## ditto for rank methods:
        rankmethod_name_names = {"wrd": _("word similarity"),
                                 "demo_jif": _("journal impact factor"),
                                 "citation": _("times cited"),
                                 "citerank_citation_t": _("time-decay cite count"),
                                 "citerank_pagerank_c": _("all-time-best cite rank"),
                                 "citerank_pagerank_t": _("time-decay cite rank"),}
        for (rankmethod_id, rankmethod_name) in rankmethod_id_name_list:
            if rankmethod_name_names.has_key(rankmethod_name):
                try:
                    run_sql("""INSERT INTO rnkMETHODNAME (id_rnkMETHOD,ln,type,value) VALUES
                                (%s,%s,%s,%s)""", (rankmethod_id, lang, 'ln',
                                                   rankmethod_name_names[rankmethod_name]))
                except IntegrityError:
                    run_sql("""UPDATE rnkMETHODNAME SET value=%s
                                WHERE id_rnkMETHOD=%s AND ln=%s AND type=%s""",
                            (rankmethod_name_names[rankmethod_name], rankmethod_id, lang, 'ln',))

    print ">>> I18N field names reset successfully."

def cli_check_openoffice(conf):
    """
    If OpenOffice.org integration is enabled, checks whether the system is
    properly configured.
    """
    from invenio.bibtask import check_running_process_user
    from invenio.websubmit_file_converter import can_unoconv, get_file_converter_logger
    logger = get_file_converter_logger()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    check_running_process_user()
    print ">>> Checking if Libre/OpenOffice.org is correctly integrated...",
    sys.stdout.flush()
    if can_unoconv(True):
        print "ok"
    else:
        sys.exit(1)

def test_db_connection():
    """
    Test DB connection, and if fails, advise user how to set it up.
    Useful to be called during table creation.
    """
    print "Testing DB connection...",
    from invenio.textutils import wrap_text_in_a_box
    from invenio.dbquery import run_sql, Error

    ## first, test connection to the DB server:
    try:
        run_sql("SHOW TABLES")
    except Error, err:
        from invenio.dbquery import CFG_DATABASE_HOST, CFG_DATABASE_PORT, \
             CFG_DATABASE_NAME, CFG_DATABASE_USER, CFG_DATABASE_PASS
        print wrap_text_in_a_box("""\
DATABASE CONNECTIVITY ERROR %(errno)d: %(errmsg)s.\n

Perhaps you need to set up database and connection rights?
If yes, then please login as MySQL admin user and run the
following commands now:


$ mysql -h %(dbhost)s -P %(dbport)s -u root -p mysql

mysql> CREATE DATABASE %(dbname)s DEFAULT CHARACTER SET utf8;

mysql> GRANT ALL PRIVILEGES ON %(dbname)s.*

       TO %(dbuser)s@%(webhost)s IDENTIFIED BY '%(dbpass)s';

mysql> QUIT


The values printed above were detected from your
configuration. If they are not right, then please edit your
invenio-local.conf file and rerun 'inveniocfg --update-all' first.


If the problem is of different nature, then please inspect
the above error message and fix the problem before continuing.""" % \
                                 {'errno': err.args[0],
                                  'errmsg': err.args[1],
                                  'dbname': CFG_DATABASE_NAME,
                                  'dbhost': CFG_DATABASE_HOST,
                                  'dbport': CFG_DATABASE_PORT,
                                  'dbuser': CFG_DATABASE_USER,
                                  'dbpass': CFG_DATABASE_PASS,
                                  'webhost': CFG_DATABASE_HOST == 'localhost' and 'localhost' or os.popen('hostname -f', 'r').read().strip(),
                                  })
        sys.exit(1)
    print "ok"

    ## second, test insert/select of a Unicode string to detect
    ## possible Python/MySQL/MySQLdb mis-setup:
    print "Testing Python/MySQL/MySQLdb UTF-8 chain...",
    try:
        try:
            beta_in_utf8 = "β" # Greek beta in UTF-8 is 0xCEB2
            run_sql("CREATE TABLE test__invenio__utf8 (x char(1), y varbinary(2)) DEFAULT CHARACTER SET utf8 ENGINE=MyISAM;")
            run_sql("INSERT INTO test__invenio__utf8 (x, y) VALUES (%s, %s)", (beta_in_utf8, beta_in_utf8))
            res = run_sql("SELECT x,y,HEX(x),HEX(y),LENGTH(x),LENGTH(y),CHAR_LENGTH(x),CHAR_LENGTH(y) FROM test__invenio__utf8")
            assert res[0] == ('\xce\xb2', '\xce\xb2', 'CEB2', 'CEB2', 2L, 2L, 1L, 2L)
            run_sql("DROP TABLE test__invenio__utf8")
        except Exception, err:
            print wrap_text_in_a_box("""\
DATABASE RELATED ERROR %s\n

A problem was detected with the UTF-8 treatment in the chain
between the Python application, the MySQLdb connector, and
the MySQL database. You may perhaps have installed older
versions of some prerequisite packages?\n

Please check the INSTALL file and please fix this problem
before continuing.""" % err)

            sys.exit(1)
    finally:
        run_sql("DROP TABLE IF EXISTS test__invenio__utf8")
    print "ok"

def cli_cmd_create_tables(conf):
    """Create and fill Invenio DB tables.  Useful for the installation process."""
    print ">>> Going to create and fill tables..."
    from invenio.config import CFG_PREFIX
    test_db_connection()
    for cmd in ["%s/bin/dbexec < %s/lib/sql/invenio/tabcreate.sql" % (CFG_PREFIX, CFG_PREFIX),
                "%s/bin/dbexec < %s/lib/sql/invenio/tabfill.sql" % (CFG_PREFIX, CFG_PREFIX)]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    cli_cmd_reset_sitename(conf)
    cli_cmd_reset_siteadminemail(conf)
    cli_cmd_reset_fieldnames(conf)
    for cmd in ["%s/bin/webaccessadmin -u admin -c -a" % CFG_PREFIX]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    print ">>> Tables created and filled successfully."

def cli_cmd_load_webstat_conf(conf):
    print ">>> Going to load WebStat config..."
    from invenio.config import CFG_PREFIX
    cmd = "%s/bin/webstatadmin --load-config" % CFG_PREFIX
    if os.system(cmd):
        print "ERROR: failed execution of", cmd
        sys.exit(1)
    print ">>> WebStat config load successfully."

def cli_cmd_load_bibfield_config(conf):
    print ">>> Going to load BibField config..."
    from invenio.bibfield_config_engine import BibFieldParser
    BibFieldParser.reparse()
    print ">>> BibField config load successfully."

def cli_cmd_drop_tables(conf):
    """Drop Invenio DB tables.  Useful for the uninstallation process."""
    print ">>> Going to drop tables..."
    from invenio.config import CFG_PREFIX
    from invenio.textutils import wrap_text_in_a_box, wait_for_user
    from invenio.webstat import destroy_customevents
    wait_for_user(wrap_text_in_a_box("""WARNING: You are going to destroy
your database tables!"""))
    msg = destroy_customevents()
    if msg:
        print msg
    cmd = "%s/bin/dbexec < %s/lib/sql/invenio/tabdrop.sql" % (CFG_PREFIX, CFG_PREFIX)
    if os.system(cmd):
        print "ERROR: failed execution of", cmd
        sys.exit(1)
    print ">>> Tables dropped successfully."

def cli_cmd_create_demo_site(conf):
    """Create demo site.  Useful for testing purposes."""
    print ">>> Going to create demo site..."
    from invenio.config import CFG_PREFIX
    from invenio.dbquery import run_sql
    run_sql("TRUNCATE schTASK")
    run_sql("TRUNCATE session")
    run_sql("DELETE FROM user WHERE email=''")
    for cmd in ["%s/bin/dbexec < %s/lib/sql/invenio/democfgdata.sql" % \
                   (CFG_PREFIX, CFG_PREFIX),]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    cli_cmd_reset_fieldnames(conf) # needed for I18N demo ranking method names
    for cmd in ["%s/bin/webaccessadmin -u admin -c -r -D" % CFG_PREFIX,
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 1" % CFG_PREFIX,
                "%s/bin/bibsort -u admin --load-config" % CFG_PREFIX,
                "%s/bin/bibsort 2" % CFG_PREFIX, ]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    print ">>> Demo site created successfully."

def cli_cmd_load_demo_records(conf):
    """Load demo records.  Useful for testing purposes."""
    from invenio.config import CFG_PREFIX
    from invenio.dbquery import run_sql
    print ">>> Going to load demo records..."
    run_sql("TRUNCATE schTASK")
    for cmd in ["%s/bin/bibupload -u admin -i %s/var/tmp/demobibdata.xml" % (CFG_PREFIX, CFG_PREFIX),
                "%s/bin/bibupload 1" % CFG_PREFIX,
                "%s/bin/bibdocfile --textify --with-ocr --recid 97" % CFG_PREFIX,
                "%s/bin/bibdocfile --textify --all" % CFG_PREFIX,
                "%s/bin/bibindex -u admin" % CFG_PREFIX,
                "%s/bin/bibindex 2" % CFG_PREFIX,
                "%s/bin/bibindex -u admin -w global" % CFG_PREFIX,
                "%s/bin/bibindex 3" % CFG_PREFIX,
                "%s/bin/bibreformat -u admin -o HB" % CFG_PREFIX,
                "%s/bin/bibreformat 4" % CFG_PREFIX,
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 5" % CFG_PREFIX,
                "%s/bin/bibrank -u admin" % CFG_PREFIX,
                "%s/bin/bibrank 6" % CFG_PREFIX,
                "%s/bin/bibsort -u admin -R" % CFG_PREFIX,
                "%s/bin/bibsort 7" % CFG_PREFIX,
                "%s/bin/oairepositoryupdater -u admin" % CFG_PREFIX,
                "%s/bin/oairepositoryupdater 8" % CFG_PREFIX,
                "%s/bin/bibupload 9" % CFG_PREFIX,]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    print ">>> Demo records loaded successfully."

def cli_cmd_remove_demo_records(conf):
    """Remove demo records.  Useful when you are finished testing."""
    print ">>> Going to remove demo records..."
    from invenio.config import CFG_PREFIX
    from invenio.dbquery import run_sql
    from invenio.textutils import wrap_text_in_a_box, wait_for_user
    wait_for_user(wrap_text_in_a_box("""WARNING: You are going to destroy
your records and documents!"""))
    if os.path.exists(CFG_PREFIX + os.sep + 'var' + os.sep + 'data'):
        shutil.rmtree(CFG_PREFIX + os.sep + 'var' + os.sep + 'data')
    run_sql("TRUNCATE schTASK")
    for cmd in ["%s/bin/dbexec < %s/lib/sql/invenio/tabbibclean.sql" % (CFG_PREFIX, CFG_PREFIX),
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 1" % CFG_PREFIX,]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    print ">>> Demo records removed successfully."

def cli_cmd_drop_demo_site(conf):
    """Drop demo site completely.  Useful when you are finished testing."""
    print ">>> Going to drop demo site..."
    from invenio.textutils import wrap_text_in_a_box, wait_for_user
    wait_for_user(wrap_text_in_a_box("""WARNING: You are going to destroy
your site and documents!"""))
    cli_cmd_drop_tables(conf)
    cli_cmd_create_tables(conf)
    cli_cmd_remove_demo_records(conf)
    print ">>> Demo site dropped successfully."

def cli_cmd_run_unit_tests(conf):
    """Run unit tests, usually on the working demo site."""
    from invenio.testutils import build_and_run_unit_test_suite
    if not build_and_run_unit_test_suite():
        sys.exit(1)

def cli_cmd_run_js_unit_tests(conf):
    """Run JavaScript unit tests, usually on the working demo site."""
    from invenio.testutils import build_and_run_js_unit_test_suite
    if not build_and_run_js_unit_test_suite():
        sys.exit(1)

def cli_cmd_run_regression_tests(conf):
    """Run regression tests, usually on the working demo site."""
    from invenio.testutils import build_and_run_regression_test_suite
    if not build_and_run_regression_test_suite():
        sys.exit(1)

def cli_cmd_run_web_tests(conf):
    """Run web tests in a browser. Requires Firefox with Selenium."""
    from invenio.testutils import build_and_run_web_test_suite
    if not build_and_run_web_test_suite():
        sys.exit(1)

def _detect_ip_address():
    """Detect IP address of this computer.  Useful for creating Apache
    vhost conf snippet on RHEL like machines.

    @return: IP address, or '*' if cannot detect
    @rtype: string
    @note: creates socket for real in order to detect real IP address,
        not the loopback one.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('invenio-software.org', 0))
        return s.getsockname()[0]
    except:
        return '*'

def cli_cmd_create_apache_conf(conf):
    """
    Create Apache conf files for this site, keeping previous
    files in a backup copy.
    """
    print ">>> Going to create Apache conf files..."
    from invenio.textutils import wrap_text_in_a_box
    from invenio.access_control_config import CFG_EXTERNAL_AUTH_USING_SSO
    apache_conf_dir = conf.get("Invenio", 'CFG_ETCDIR') + \
                      os.sep + 'apache'
    if guess_apache_24():
        directory_www_directive = """
        # Uncomment the following on Apache < 2.4
        # <Directory %(webdir)s>
        #    Options FollowSymLinks MultiViews
        #    AllowOverride None
        #    Order allow,deny
        #    Allow from all
        # </Directory>
        # Comment the following on Apache < 2.4
        <Directory %(webdir)s>
           Options FollowSymLinks MultiViews
           AllowOverride None
           Require all granted
        </Directory>""" % {'webdir': conf.get('Invenio', 'CFG_WEBDIR')}
        directory_wsgi_directive = """
        # Uncomment the following on Apache < 2.4
        # <Directory %(wsgidir)s>
        #    WSGIProcessGroup invenio
        #    WSGIApplicationGroup %%{GLOBAL}
        #    Options FollowSymLinks MultiViews
        #    AllowOverride None
        #    Order allow,deny
        #    Allow from all
        # </Directory>
        # Comment the following on Apache < 2.4
        <Directory %(wsgidir)s>
           WSGIProcessGroup invenio
           WSGIApplicationGroup %%{GLOBAL}
           Options FollowSymLinks MultiViews
           AllowOverride None
           Require all granted
        </Directory>""" % {'wsgidir': os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'www-wsgi')}
    else:
        directory_www_directive = """
        # Comment the following on Apache >= 2.4
        <Directory %(webdir)s>
           Options FollowSymLinks MultiViews
           AllowOverride None
           Order allow,deny
           Allow from all
        </Directory>
        # Uncomment the following on Apache >= 2.4
        # <Directory %(webdir)s>
        #    Options FollowSymLinks MultiViews
        #    AllowOverride None
        #    Require all granted
        # </Directory>""" % {'webdir': conf.get('Invenio', 'CFG_WEBDIR')}
        directory_wsgi_directive = """
        # Comment the following on Apache >= 2.4
        <Directory %(wsgidir)s>
           WSGIProcessGroup invenio
           WSGIApplicationGroup %%{GLOBAL}
           Options FollowSymLinks MultiViews
           AllowOverride None
           Order allow,deny
           Allow from all
        </Directory>
        # Uncomment the following on Apache >= 2.4
        # <Directory %(wsgidir)s>
        #    WSGIProcessGroup invenio
        #    WSGIApplicationGroup %%{GLOBAL}
        #    Options FollowSymLinks MultiViews
        #    AllowOverride None
        #    Require all granted
        # </Directory>""" % {'wsgidir': os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'www-wsgi')}

    ## Preparation of XSendFile directive
    xsendfile_directive_needed = int(conf.get("Invenio", 'CFG_BIBDOCFILE_USE_XSENDFILE')) != 0
    if xsendfile_directive_needed:
        xsendfile_directive = "XSendFile On\n"
    else:
        xsendfile_directive = "#XSendFile On\n"
    for path in (conf.get('Invenio', 'CFG_BIBDOCFILE_FILEDIR'), # BibDocFile
            conf.get('Invenio', 'CFG_WEBDIR'),
            conf.get('Invenio', 'CFG_WEBSUBMIT_STORAGEDIR'), # WebSubmit
            conf.get('Invenio', 'CFG_TMPDIR'),
            os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'tmp', 'attachfile'),
            os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'data', 'comments'),
            os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'data', 'baskets', 'comments'),
            os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'lib', 'webdoc', 'invenio', 'info'),
            '/tmp'): # BibExport
        if xsendfile_directive_needed:
            xsendfile_directive += '        XSendFilePath %s\n' % path
        else:
            xsendfile_directive += '        #XSendFilePath %s\n' % path
    xsendfile_directive = xsendfile_directive.strip()

    ## Preparation of deflate directive
    deflate_directive_needed = int(conf.get("Invenio", 'CFG_WEBSTYLE_HTTP_USE_COMPRESSION')) != 0
    if deflate_directive_needed:
        deflate_directive = r"""
        ## Configuration snippet taken from:
        ## <http://httpd.apache.org/docs/2.2/mod/mod_deflate.html>
        <IfModule mod_deflate.c>
            SetOutputFilter DEFLATE

            # Netscape 4.x has some problems...
            BrowserMatch ^Mozilla/4 gzip-only-text/html

            # Netscape 4.06-4.08 have some more problems
            BrowserMatch ^Mozilla/4\.0[678] no-gzip

            # MSIE masquerades as Netscape, but it is fine
            # BrowserMatch \bMSIE !no-gzip !gzip-only-text/html

            # NOTE: Due to a bug in mod_setenvif up to Apache 2.0.48
            # the above regex won't work. You can use the following
            # workaround to get the desired effect:
            BrowserMatch \bMSI[E] !no-gzip !gzip-only-text/html

            # Don't compress images
            SetEnvIfNoCase Request_URI \
                \.(?:gif|jpe?g|png)$ no-gzip dont-vary

            # Make sure proxies don't deliver the wrong content
            <IfModule mod_headers.c>
                Header append Vary User-Agent env=!dont-vary
            </IfModule>
        </IfModule>
        """
    else:
        deflate_directive = ""

    if CFG_EXTERNAL_AUTH_USING_SSO:
        shibboleth_directive = r"""
        <Location ~ "/youraccount/login|Shibboleth.sso/">
            SSLRequireSSL   # The modules only work using HTTPS
            AuthType shibboleth
            ShibRequireSession On
            ShibRequireAll On
            ShibExportAssertion Off
            require valid-user
        </Location>
        """
    else:
        shibboleth_directive = ""

    ## Apache vhost conf file is distro specific, so analyze needs:
    # Gentoo (and generic defaults):
    listen_directive_needed = True
    ssl_pem_directive_needed = False
    ssl_pem_path = '/etc/apache2/ssl/apache.pem'
    ssl_crt_path = '/etc/apache2/ssl/server.crt'
    ssl_key_path = '/etc/apache2/ssl/server.key'
    vhost_ip_address_needed = False
    wsgi_socket_directive_needed = False
    # Debian:
    if os.path.exists(os.path.sep + 'etc' + os.path.sep + 'debian_version'):
        listen_directive_needed = False
        ssl_pem_directive_needed = True
    # RHEL/SLC:
    if os.path.exists(os.path.sep + 'etc' + os.path.sep + 'redhat-release'):
        listen_directive_needed = False
        ssl_crt_path = '/etc/pki/tls/certs/localhost.crt'
        ssl_key_path = '/etc/pki/tls/private/localhost.key'
        vhost_ip_address_needed = True
        wsgi_socket_directive_needed = True
    # maybe we are using non-standard ports?
    vhost_site_url = conf.get('Invenio', 'CFG_SITE_URL').replace("http://", "")
    if vhost_site_url.startswith("https://"):
        ## The installation is configured to require HTTPS for any connection
        vhost_site_url = vhost_site_url.replace("https://", "")
    vhost_site_url_port = '80'
    vhost_site_secure_url = conf.get('Invenio', 'CFG_SITE_SECURE_URL').replace("https://", "")
    vhost_site_secure_url_port = '443'
    if ':' in vhost_site_url:
        vhost_site_url, vhost_site_url_port = vhost_site_url.split(':', 1)
    if ':' in vhost_site_secure_url:
        vhost_site_secure_url, vhost_site_secure_url_port = vhost_site_secure_url.split(':', 1)
    if vhost_site_url_port != '80' or vhost_site_secure_url_port != '443':
        listen_directive_needed = True
    ## OK, let's create Apache vhost files:
    if not os.path.exists(apache_conf_dir):
        os.mkdir(apache_conf_dir)
    apache_vhost_file = apache_conf_dir + os.sep + \
                            'invenio-apache-vhost.conf'
    apache_vhost_ssl_file = apache_conf_dir + os.sep + \
                             'invenio-apache-vhost-ssl.conf'
    apache_vhost_body = """\
AddDefaultCharset UTF-8
ServerSignature Off
ServerTokens Prod
NameVirtualHost %(vhost_ip_address)s:%(vhost_site_url_port)s
%(listen_directive)s
%(wsgi_socket_directive)s
WSGIRestrictStdout Off
<Files *.pyc>
   deny from all
</Files>
<Files *~>
   deny from all
</Files>
<VirtualHost %(vhost_ip_address)s:%(vhost_site_url_port)s>
        ServerName %(servername)s
        ServerAlias %(serveralias)s
        ServerAdmin %(serveradmin)s
        DocumentRoot %(webdir)s
        %(directory_www_directive)s
        ErrorLog %(logdir)s/apache.err
        LogLevel warn
        LogFormat "%%h %%l %%u %%t \\"%%r\\" %%>s %%b \\"%%{Referer}i\\" \\"%%{User-agent}i\\" %%D" combined_with_timing
        CustomLog %(logdir)s/apache.log combined_with_timing
        DirectoryIndex index.en.html index.html
        Alias /static/ %(webdir)s/static/
        Alias /img/ %(webdir)s/img/
        Alias /css/ %(webdir)s/css/
        Alias /js/ %(webdir)s/js/
        Alias /flash/ %(webdir)s/flash/
        Alias /export/ %(webdir)s/export/
        Alias /MathJax/ %(webdir)s/MathJax/
        Alias /jsCalendar/ %(webdir)s/jsCalendar/
        Alias /ckeditor/ %(webdir)s/ckeditor/
        Alias /mediaelement/ %(webdir)s/mediaelement/
        AliasMatch /sitemap-(.*) %(webdir)s/sitemap-$1
        Alias /robots.txt %(webdir)s/robots.txt
        Alias /favicon.ico %(webdir)s/favicon.ico
        WSGIDaemonProcess invenio processes=5 threads=1 display-name=%%{GROUP} inactivity-timeout=3600 maximum-requests=10000
        WSGIImportScript %(wsgidir)s/invenio.wsgi process-group=invenio application-group=%%{GLOBAL}
        WSGIScriptAlias / %(wsgidir)s/invenio.wsgi
        WSGIPassAuthorization On
        %(xsendfile_directive)s
        %(directory_wsgi_directive)s
        %(deflate_directive)s
</VirtualHost>
""" % {'vhost_site_url_port': vhost_site_url_port,
       'servername': vhost_site_url,
       'serveralias': vhost_site_url.split('.')[0],
       'serveradmin': conf.get('Invenio', 'CFG_SITE_ADMIN_EMAIL'),
       'webdir': conf.get('Invenio', 'CFG_WEBDIR'),
       'logdir': conf.get('Invenio', 'CFG_LOGDIR'),
       'wsgidir': os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'www-wsgi'),
       'vhost_ip_address': vhost_ip_address_needed and _detect_ip_address() or '*',
       'listen_directive': listen_directive_needed and 'Listen ' + vhost_site_url_port or \
                           '#Listen ' + vhost_site_url_port,
       'wsgi_socket_directive': (wsgi_socket_directive_needed and \
                                'WSGISocketPrefix ' or '#WSGISocketPrefix ') + \
              conf.get('Invenio', 'CFG_PREFIX') + os.sep + 'var' + os.sep + 'run',
       'xsendfile_directive': xsendfile_directive,
       'directory_www_directive': directory_www_directive,
       'directory_wsgi_directive': directory_wsgi_directive,
       'deflate_directive': deflate_directive,
       }
    apache_vhost_ssl_body = """\
ServerSignature Off
ServerTokens Prod
%(listen_directive)s
NameVirtualHost %(vhost_ip_address)s:%(vhost_site_secure_url_port)s
%(ssl_pem_directive)s
%(ssl_crt_directive)s
%(ssl_key_directive)s
WSGIRestrictStdout Off
<Files *.pyc>
   deny from all
</Files>
<Files *~>
   deny from all
</Files>
<VirtualHost %(vhost_ip_address)s:%(vhost_site_secure_url_port)s>
        ServerName %(servername)s
        ServerAlias %(serveralias)s
        ServerAdmin %(serveradmin)s
        SSLEngine on
        DocumentRoot %(webdir)s
        %(directory_www_directive)s
        ErrorLog %(logdir)s/apache-ssl.err
        LogLevel warn
        LogFormat "%%h %%l %%u %%t \\"%%r\\" %%>s %%b \\"%%{Referer}i\\" \\"%%{User-agent}i\\" %%D" combined_with_timing
        CustomLog %(logdir)s/apache-ssl.log combined_with_timing
        DirectoryIndex index.en.html index.html
        Alias /static/ %(webdir)s/static/
        Alias /img/ %(webdir)s/img/
        Alias /css/ %(webdir)s/css/
        Alias /js/ %(webdir)s/js/
        Alias /flash/ %(webdir)s/flash/
        Alias /export/ %(webdir)s/export/
        Alias /MathJax/ %(webdir)s/MathJax/
        Alias /jsCalendar/ %(webdir)s/jsCalendar/
        Alias /ckeditor/ %(webdir)s/ckeditor/
        Alias /mediaelement/ %(webdir)s/mediaelement/
        AliasMatch /sitemap-(.*) %(webdir)s/sitemap-$1
        Alias /robots.txt %(webdir)s/robots.txt
        Alias /favicon.ico %(webdir)s/favicon.ico
        RedirectMatch /sslredirect/(.*) http://$1
        WSGIScriptAlias / %(wsgidir)s/invenio.wsgi
        WSGIPassAuthorization On
        %(xsendfile_directive)s
        %(directory_wsgi_directive)s
        %(deflate_directive)s
        %(shibboleth_directive)s
</VirtualHost>
""" % {'vhost_site_secure_url_port': vhost_site_secure_url_port,
       'servername': vhost_site_secure_url,
       'serveralias': vhost_site_secure_url.split('.')[0],
       'serveradmin': conf.get('Invenio', 'CFG_SITE_ADMIN_EMAIL'),
       'webdir': conf.get('Invenio', 'CFG_WEBDIR'),
       'logdir': conf.get('Invenio', 'CFG_LOGDIR'),
       'wsgidir' : os.path.join(conf.get('Invenio', 'CFG_PREFIX'), 'var', 'www-wsgi'),
       'vhost_ip_address': vhost_ip_address_needed and _detect_ip_address() or '*',
       'listen_directive' : listen_directive_needed and 'Listen ' + vhost_site_secure_url_port or \
                            '#Listen ' + vhost_site_secure_url_port,
       'ssl_pem_directive': ssl_pem_directive_needed and \
                            'SSLCertificateFile %s' % ssl_pem_path or \
                            '#SSLCertificateFile %s' % ssl_pem_path,
       'ssl_crt_directive': ssl_pem_directive_needed and \
                            '#SSLCertificateFile %s' % ssl_crt_path or \
                            'SSLCertificateFile %s' % ssl_crt_path,
       'ssl_key_directive': ssl_pem_directive_needed and \
                            '#SSLCertificateKeyFile %s' % ssl_key_path or \
                            'SSLCertificateKeyFile %s' % ssl_key_path,
       'xsendfile_directive': xsendfile_directive,
       'directory_www_directive': directory_www_directive,
       'directory_wsgi_directive': directory_wsgi_directive,
       'deflate_directive': deflate_directive,
       'shibboleth_directive': shibboleth_directive,
       }
    # write HTTP vhost snippet:
    if os.path.exists(apache_vhost_file):
        shutil.copy(apache_vhost_file,
                    apache_vhost_file + '.OLD')
    fdesc = open(apache_vhost_file, 'w')
    fdesc.write(apache_vhost_body)
    fdesc.close()
    print
    print "Created file", apache_vhost_file
    # write HTTPS vhost snippet:
    vhost_ssl_created = False
    if conf.get('Invenio', 'CFG_SITE_SECURE_URL').startswith("https://"):
        if os.path.exists(apache_vhost_ssl_file):
            shutil.copy(apache_vhost_ssl_file,
                        apache_vhost_ssl_file + '.OLD')
        fdesc = open(apache_vhost_ssl_file, 'w')
        fdesc.write(apache_vhost_ssl_body)
        fdesc.close()
        vhost_ssl_created = True
        print "Created file", apache_vhost_ssl_file

    print wrap_text_in_a_box("""\
Apache virtual host configuration file(s) for your Invenio site
was(were) created.  Please check created file(s) and activate virtual
host(s).  For example, you can put the following include statements in
your httpd.conf:\n

Include %s

%s


Please see the INSTALL file for more details.
    """ % (apache_vhost_file, (vhost_ssl_created and 'Include ' or '#Include ') + apache_vhost_ssl_file))
    print ">>> Apache conf files created."

def cli_cmd_get(conf, varname):
    """
    Return value of VARNAME read from CONF files.  Useful for
    third-party programs to access values of conf options such as
    CFG_PREFIX.  Return None if VARNAME is not found.
    """
    try:
        if not varname:
            raise Exception("ERROR: Please specify a configuration variable.")
        varname = varname.lower()
        # do not pay attention to section names yet:
        all_options = {}
        for section in conf.sections():
            for option in conf.options(section):
                all_options[option] = conf.get(section, option)
        varvalue = all_options.get(varname, None)
        if varvalue is None:
            raise Exception()
        print varvalue
    except Exception, e:
        if e.message:
            print e.message
        sys.exit(1)

def cli_cmd_list(conf):
    """
    Print a list of all conf options and values from CONF.
    """
    sections = conf.sections()
    sections.sort()
    for section in sections:
        options = conf.options(section)
        options.sort()
        for option in options:
            print option.upper(), '=', conf.get(section, option)

def _grep_version_from_executable(path_to_exec, version_regexp):
    """
    Try to detect a program version by digging into its binary
    PATH_TO_EXEC and looking for VERSION_REGEXP.  Return program
    version as a string.  Return empty string if not succeeded.
    """
    from invenio.shellutils import run_shell_command
    exec_version = ""
    if os.path.exists(path_to_exec):
        dummy1, cmd2_out, dummy2 = run_shell_command("strings %s | grep %s",
                                                     (path_to_exec, version_regexp))
        if cmd2_out:
            for cmd2_out_line in cmd2_out.split("\n"):
                if len(cmd2_out_line) > len(exec_version):
                    # the longest the better
                    exec_version = cmd2_out_line
    return exec_version

_RE_APACHE_MAJOR_VERSION = re.compile(r"Apache/(\d+\.\d+)")
def guess_apache_24(apache_versions=None):
    """
    Returns True if it looks like the system is running Apache 2.4 or later.
    """
    if apache_versions is None:
        apache_versions = detect_apache_version()
    for apache_version in apache_versions:
        g = _RE_APACHE_MAJOR_VERSION.search(apache_version)
        if g:
            try:
                version = float(g.group(1))
            except ValueError:
                continue
            if version >= 2.4:
                return True
    return False


def detect_apache_version():
    """
    Try to detect Apache version by localizing httpd or apache
    executables and grepping inside binaries.  Return list of all
    found Apache versions and paths.  (For a given executable, the
    returned format is 'apache_version [apache_path]'.)  Return empty
    list if no success.
    """
    from invenio.shellutils import run_shell_command
    out = []
    dummy1, cmd_out, dummy2 = run_shell_command("locate bin/httpd bin/apache")
    for apache in cmd_out.split("\n"):
        apache_version = _grep_version_from_executable(apache, '^Apache\/')
        if apache_version:
            out.append("%s [%s]" % (apache_version, apache))
    return out

def cli_cmd_detect_system_details(conf):
    """
    Detect and print system details such as Apache/Python/MySQL
    versions etc.  Useful for debugging problems on various OS.
    """
    import MySQLdb
    print ">>> Going to detect system details..."
    print "* Hostname: " + socket.gethostname()
    print "* Invenio version: " + conf.get("Invenio", "CFG_VERSION")
    print "* Python version: " + sys.version.replace("\n", " ")
    print "* Apache version: " + ";\n                  ".join(detect_apache_version())
    print "* MySQLdb version: " + MySQLdb.__version__
    try:
        from invenio.dbquery import run_sql
        print "* MySQL version:"
        for key, val in run_sql("SHOW VARIABLES LIKE 'version%'") + \
                run_sql("SHOW VARIABLES LIKE 'charact%'") + \
                run_sql("SHOW VARIABLES LIKE 'collat%'"):
            if False:
                print "    - %s: %s" % (key, val)
            elif key in ['version',
                         'character_set_client',
                         'character_set_connection',
                         'character_set_database',
                         'character_set_results',
                         'character_set_server',
                         'character_set_system',
                         'collation_connection',
                         'collation_database',
                         'collation_server']:
                print "    - %s: %s" % (key, val)
    except ImportError:
        print "* ERROR: cannot import dbquery"
    print ">>> System details detected successfully."


def cli_cmd_upgrade(conf):
    """
    Command for applying upgrades
    """
    from invenio.inveniocfg_upgrader import cmd_upgrade
    cmd_upgrade(conf)

def cli_cmd_upgrade_check(conf):
    """
    Command for running pre-upgrade checks
    """
    from invenio.inveniocfg_upgrader import cmd_upgrade_check
    cmd_upgrade_check(conf)


def cli_cmd_upgrade_show_pending(conf):
    """
    Command for showing upgrades ready to be applied
    """
    from invenio.inveniocfg_upgrader import cmd_upgrade_show_pending
    cmd_upgrade_show_pending(conf)


def cli_cmd_upgrade_show_applied(conf):
    """
    Command for showing all upgrades already applied.
    """
    from invenio.inveniocfg_upgrader import cmd_upgrade_show_applied
    cmd_upgrade_show_applied(conf)


def cli_cmd_upgrade_create_release_recipe(conf, path):
    """
    Create a new release upgrade recipe (for developers).
    """
    from invenio.inveniocfg_upgrader import cmd_upgrade_create_release_recipe
    cmd_upgrade_create_release_recipe(conf, path)


def cli_cmd_upgrade_create_standard_recipe(conf, path, depends_on=None,
                                          release=False):
    """
    Create a new upgrade recipe (for developers).
    """
    from invenio.inveniocfg_upgrader import cmd_upgrade_create_standard_recipe
    cmd_upgrade_create_standard_recipe(conf, path, depends_on=depends_on,
                                       release=release)


def prepare_option_parser():
    """Parse the command line options."""

    class InvenioOption(Option):
        """
        Option class that implements the action 'store_append_const' which will

        1) append <const> to list in options.<dest>
        2) take a value and store in options.<const>

        Useful for e.g. appending a const to an actions list, while also taking
        an option value and storing it.

        This ensures that we can run actions in the order they are given on the
        command-line.

        Python 2.4 compatibility note: *append_const* action is not available in
        Python 2.4, so it is implemented here, together with the new action
        *store_append_const*.
        """
        ACTIONS = Option.ACTIONS + ("store_append_const", "append_const")
        STORE_ACTIONS = Option.STORE_ACTIONS + ("store_append_const", "append_const")
        TYPED_ACTIONS = Option.TYPED_ACTIONS + ("store_append_const", )
        ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("store_append_const", )
        CONST_ACTIONS = getattr(Option, 'CONST_ACTIONS', ()) + ("store_append_const", "append_const")

        def take_action(self, action, dest, opt, value, values, parser):
            if action == "store_append_const":
                # Combination of 'store' and 'append_const' actions
                values.ensure_value(dest, []).append(self.const)
                value_dest = self.const.replace('-', '_')
                setattr(values, value_dest, value)
            elif action == "append_const" and not hasattr(Option, 'CONST_ACTIONS'):
                values.ensure_value(dest, []).append(self.const)
            else:
                Option.take_action(self, action, dest, opt, value, values, parser)

        def _check_const(self):
            if self.action not in self.CONST_ACTIONS and self.const is not None:
                raise OptionError(
                    "'const' must not be supplied for action %r" % self.action,
                    self)

        CHECK_METHODS = [
            Option._check_action,
            Option._check_type,
            Option._check_choice,
            Option._check_dest,
            _check_const,
            Option._check_nargs,
            Option._check_callback,
        ]

    parser = OptionParser(option_class=InvenioOption, description="Invenio configuration and administration CLI tool", formatter=IndentedHelpFormatter(max_help_position=31))

    parser.add_option("-V", "--version", action="store_true", help="print version number")

    finish_options = OptionGroup(parser, "Options to finish your installation")
    finish_options.add_option("", "--create-apache-conf", dest='actions', const='create-apache-conf', action="append_const", help="create Apache configuration files")
    finish_options.add_option("", "--create-tables", dest='actions', const='create-tables', action="append_const", help="create DB tables for Invenio")
    finish_options.add_option("", "--load-bibfield-conf", dest='actions', const='load-bibfield-conf', action="append_const", help="load bibfield configuration file")
    finish_options.add_option("", "--load-webstat-conf", dest='actions', const='load-webstat-conf', action="append_const", help="load the WebStat configuration")
    finish_options.add_option("", "--drop-tables", dest='actions', const='drop-tables', action="append_const", help="drop DB tables of Invenio")
    finish_options.add_option("", "--check-openoffice", dest='actions', const='check-openoffice', action="append_const", help="check for correctly set up of openoffice temporary directory")
    parser.add_option_group(finish_options)

    demotest_options = OptionGroup(parser, "Options to set up and test a demo site")
    demotest_options.add_option("", "--create-demo-site", dest='actions', const='create-demo-site', action="append_const", help="create demo site")
    demotest_options.add_option("", "--load-demo-records", dest='actions', const='load-demo-records', action="append_const", help="load demo records")
    demotest_options.add_option("", "--remove-demo-records", dest='actions', const='remove-demo-records', action="append_const", help="remove demo records, keeping demo site")
    demotest_options.add_option("", "--drop-demo-site", dest='actions', const='drop-demo-site', action="append_const", help="drop demo site configurations too")
    demotest_options.add_option("", "--run-unit-tests", dest='actions', const='run-unit-tests', action="append_const", help="run unit test suite (needs demo site)")
    demotest_options.add_option("", "--run-js-unit-tests", dest='actions', const='run-js-unit-tests', action="append_const", help="run JS unit test suite (needs demo site)")
    demotest_options.add_option("", "--run-regression-tests", dest='actions', const='run-regression-tests', action="append_const", help="run regression test suite (needs demo site)")
    demotest_options.add_option("", "--run-web-tests", dest='actions', const='run-web-tests', action="append_const", help="run web tests in a browser (needs demo site, Firefox, Selenium IDE)")
    parser.add_option_group(demotest_options)

    config_options = OptionGroup(parser, "Options to update config files in situ")
    config_options.add_option("", "--update-all", dest='actions', const='update-all', action="append_const", help="perform all the update options")
    config_options.add_option("", "--update-config-py", dest='actions', const='update-config-py', action="append_const", help="update config.py file from invenio.conf file")
    config_options.add_option("", "--update-dbquery-py", dest='actions', const='update-dbquery-py', action="append_const", help="update dbquery.py with DB credentials from invenio.conf")
    config_options.add_option("", "--update-dbexec", dest='actions', const='update-dbexec', action="append_const", help="update dbexec with DB credentials from invenio.conf")
    config_options.add_option("", "--update-bibconvert-tpl", dest='actions', const='update-bibconvert-tpl', action="append_const", help="update bibconvert templates with CFG_SITE_URL from invenio.conf")
    config_options.add_option("", "--update-web-tests", dest='actions', const='update-web-tests', action="append_const", help="update web test cases with CFG_SITE_URL from invenio.conf")
    parser.add_option_group(config_options)

    reset_options = OptionGroup(parser, "Options to update DB tables")
    reset_options.add_option("", "--reset-all", dest='actions', const='reset-all', action="append_const", help="perform all the reset options")
    reset_options.add_option("", "--reset-sitename", dest='actions', const='reset-sitename', action="append_const", help="reset tables to take account of new CFG_SITE_NAME*")
    reset_options.add_option("", "--reset-siteadminemail", dest='actions', const='reset-siteadminemail', action="append_const", help="reset tables to take account of new CFG_SITE_ADMIN_EMAIL")
    reset_options.add_option("", "--reset-fieldnames", dest='actions', const='reset-fieldnames', action="append_const", help="reset tables to take account of new I18N names from PO files")
    reset_options.add_option("", "--reset-recstruct-cache", dest='actions', const='reset-recstruct-cache', action="append_const", help="reset record structure cache according to CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE")
    reset_options.add_option("", "--reset-recjson-cache", dest='actions', const='reset-recjson-cache', action="append_const", help="reset record json structure cache according to CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE")
    parser.add_option_group(reset_options)

    upgrade_options = OptionGroup(parser, "Options to upgrade your installation")
    upgrade_options.add_option("", "--upgrade", dest='actions', const='upgrade', action="append_const", help="apply all pending upgrades")
    upgrade_options.add_option("", "--upgrade-check", dest='actions', const='upgrade-check', action="append_const", help="run pre-upgrade checks for pending upgrades")
    upgrade_options.add_option("", "--upgrade-show-pending", dest='actions', const='upgrade-show-pending', action="append_const", help="show pending upgrades")
    upgrade_options.add_option("", "--upgrade-show-applied", dest='actions', const='upgrade-show-applied', action="append_const", help="show history of applied upgrades")
    upgrade_options.add_option("", "--upgrade-create-standard-recipe", dest='actions', metavar='REPOSITORY[,DIR]', const='upgrade-create-standard-recipe', action="store_append_const", help="create a new standard upgrade recipe (for developers)")
    upgrade_options.add_option("", "--upgrade-create-release-recipe", dest='actions', metavar='REPOSITORY[,DIR]', const='upgrade-create-release-recipe', action="store_append_const", help="create a new release upgrade recipe (for developers)")
    parser.add_option_group(upgrade_options)

    helper_options = OptionGroup(parser, "Options to help the work")
    helper_options.add_option("", "--list", dest='actions', const='list', action="append_const", help="print names and values of all options from conf files")
    helper_options.add_option("", "--get", dest='actions', const='get', action="store_append_const", metavar="OPTION", help="get value of a given option from conf files")
    helper_options.add_option("", "--conf-dir", action="store", metavar="PATH", help="path to directory where invenio*.conf files are [optional]")
    helper_options.add_option("", "--detect-system-details", dest='actions', const='detect-system-details', action="append_const", help="print system details such as Apache/Python/MySQL versions")
    parser.add_option_group(helper_options)

    parser.add_option('--yes-i-know', action='store_true', dest='yes-i-know', help='use with care!')
    parser.add_option('-x', '--stop', action='store_true', dest='stop_on_error', help='When running tests, stop at first error')

    return parser


def prepare_conf(options):
    """ Read configuration files """
    conf = ConfigParser()
    confdir = getattr(options, 'conf_dir', None)

    if confdir is None:
        ## try to detect path to conf dir (relative to this bin dir):
        confdir = re.sub(r'/bin$', '/etc', sys.path[0])

    if confdir and not os.path.exists(confdir):
        raise Exception("ERROR: bad --conf-dir option value - directory does not exists.")
        sys.exit(1)

    ## read conf files:
    for conffile in [confdir + os.sep + 'invenio.conf',
                     confdir + os.sep + 'invenio-autotools.conf',
                     confdir + os.sep + 'invenio-local.conf', ]:

        if os.path.exists(conffile):
            conf.read(conffile)
        else:
            if not conffile.endswith("invenio-local.conf"):
                # invenio-local.conf is optional, otherwise stop
                raise Exception("ERROR: Badly guessed conf file location %s (Please use --conf-dir option.)" % conffile)
    return conf


def main(*cmd_args):
    """Main entry point."""
    # Allow easier testing
    if not cmd_args:
        cmd_args = sys.argv[1:]

    # Parse arguments
    parser = prepare_option_parser()
    (options, dummy_args) = parser.parse_args(list(cmd_args))

    if getattr(options, 'stop_on_error', False):
        from invenio.testutils import wrap_failfast
        wrap_failfast()

    if getattr(options, 'version', False):
        print_version()
    else:
        # Read configuration
        try:
            conf = prepare_conf(options)
        except Exception, e:
            print e
            sys.exit(1)

        ## Decide what to do
        actions = getattr(options, 'actions', None)

        if not actions:
            print """ERROR: Please specify a command.  Please see '--help'."""
            sys.exit(1)

        for action in actions:
            if action == 'get':
                cli_cmd_get(conf, getattr(options, 'get', None))
            elif action == 'list':
                cli_cmd_list(conf)
            elif action == 'detect-system-details':
                cli_cmd_detect_system_details(conf)
            elif action == 'create-tables':
                cli_cmd_create_tables(conf)
            elif action == 'load-webstat-conf':
                cli_cmd_load_webstat_conf(conf)
            elif action == 'drop-tables':
                cli_cmd_drop_tables(conf)
            elif action == 'check-openoffice':
                cli_check_openoffice(conf)
            elif action == 'load-bibfield-conf':
                cli_cmd_load_bibfield_config(conf)
            elif action == 'create-demo-site':
                cli_cmd_create_demo_site(conf)
            elif action == 'load-demo-records':
                cli_cmd_load_demo_records(conf)
            elif action == 'remove-demo-records':
                cli_cmd_remove_demo_records(conf)
            elif action == 'drop-demo-site':
                cli_cmd_drop_demo_site(conf)
            elif action == 'run-unit-tests':
                cli_cmd_run_unit_tests(conf)
            elif action == 'run-js-unit-tests':
                cli_cmd_run_js_unit_tests(conf)
            elif action == 'run-regression-tests':
                cli_cmd_run_regression_tests(conf)
            elif action == 'run-web-tests':
                cli_cmd_run_web_tests(conf)
            elif action == 'update-all':
                cli_cmd_update_config_py(conf)
                cli_cmd_update_dbquery_py(conf)
                cli_cmd_update_dbexec(conf)
                cli_cmd_update_bibconvert_tpl(conf)
                cli_cmd_update_web_tests(conf)
            elif action == 'update-config-py':
                cli_cmd_update_config_py(conf)
            elif action == 'update-dbquery-py':
                cli_cmd_update_dbquery_py(conf)
            elif action == 'update-dbexec':
                cli_cmd_update_dbexec(conf)
            elif action == 'update-bibconvert-tpl':
                cli_cmd_update_bibconvert_tpl(conf)
            elif action == 'update-web-tests':
                cli_cmd_update_web_tests(conf)
            elif action == 'reset-all':
                cli_cmd_reset_sitename(conf)
                cli_cmd_reset_siteadminemail(conf)
                cli_cmd_reset_fieldnames(conf)
                cli_cmd_reset_recstruct_cache(conf)
            elif action == 'reset-sitename':
                cli_cmd_reset_sitename(conf)
            elif action == 'reset-siteadminemail':
                cli_cmd_reset_siteadminemail(conf)
            elif action == 'reset-fieldnames':
                cli_cmd_reset_fieldnames(conf)
            elif action == 'reset-recstruct-cache':
                cli_cmd_reset_recstruct_cache(conf)
            elif action == 'reset-recjson-cache':
                cli_cmd_reset_recjson_cache(conf)
            elif action == 'create-apache-conf':
                cli_cmd_create_apache_conf(conf)
            elif action == 'upgrade':
                cli_cmd_upgrade(conf)
            elif action == 'upgrade-check':
                cli_cmd_upgrade_check(conf)
            elif action == 'upgrade-show-pending':
                cli_cmd_upgrade_show_pending(conf)
            elif action == 'upgrade-show-applied':
                cli_cmd_upgrade_show_applied(conf)
            elif action == 'upgrade-create-standard-recipe':
                cli_cmd_upgrade_create_standard_recipe(conf, getattr(options, 'upgrade_create_standard_recipe', None))
            elif action == 'upgrade-create-release-recipe':
                cli_cmd_upgrade_create_release_recipe(conf, getattr(options, 'upgrade_create_release_recipe', None))
            else:
                print "ERROR: Unknown command", action
                sys.exit(1)

if __name__ == '__main__':
    main()
