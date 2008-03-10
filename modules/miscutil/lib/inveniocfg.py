# -*- coding: utf-8 -*-
##
## $Id$
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
Invenio configuration and administration CLI tool.

Usage: inveniocfg [options]

General options:
   -h, --help               print this help
   -V, --version            print version number

Options to finish your installation:
   --create-apache-conf     create Apache configuration files
   --create-tables          create DB tables for Invenio
   --drop-tables            drop DB tables of Invenio

Options to set up and test a demo site:
   --create-demo-site       create demo site
   --load-demo-records      load demo records
   --remove-demo-records    remove demo records, keeping demo site
   --drop-demo-site         drop demo site configurations too
   --run-unit-tests         run unit test suite (need DB connectivity)
   --run-regression-tests   run regression test suite (need demo site)

Options to update config files in situ:
   --update-all             perform all the update options
   --update-config-py       update config.py file from invenio.conf file
   --update-dbquery-py      update dbquery.py with DB credentials from invenio.conf
   --update-dbexec          update dbexec with DB credentials from invenio.conf
   --update-bibconvert-tpl  update bibconvert templates with CFG_SITE_URL from invenio.conf

Options to update DB tables:
   --reset-all              perform all the reset options
   --reset-sitename         reset tables to take account of new CFG_SITE_NAME*
   --reset-adminemail       reset tables to take account of new ADMINEMAIL
   --reset-fieldnames       reset tables to take account of new I18N names from PO files

Options to help the work:
   --list                   print names and values of all options from conf files
   --get <some-opt>         get value of a given option from conf files
   --conf-dir </some/path>  path to directory where invenio*.conf files are [optional]
"""

__revision__ = "$Id$"

from ConfigParser import ConfigParser
import os
import re
import shutil
import sys

def print_usage():
    """Print help."""
    print __doc__

def print_version():
    """Print version information."""
    print __revision__

def convert_conf_option(option_name, option_value):
    """
    Convert conf option into Python config.py line, converting
    values to ints or strings as appropriate.
    """

    ## 1) convert option name to uppercase:
    option_name = option_name.upper()

    ## also, adjust some conf names due to backwards compatibility:
    option_name_replace_data = {'CFG_SITE_URL': 'weburl',
                                'CFG_SITE_SECURE_URL': 'sweburl',
                                'CFG_SITE_NAME': 'cdsname',
                                'CFG_SITE_NAME_INTL': 'cdsnameintl',
                                'CFG_SITE_LANG': 'cdslang',
                                'CFG_SITE_LANGS': 'cdslangs',
                                'CFG_SITE_SUPPORT_EMAIL': 'supportemail',
                                'CFG_SITE_ADMIN_EMAIL': 'adminemail',
                                }
    if option_name_replace_data.has_key(option_name):
        option_name = option_name_replace_data[option_name]

    ## 2) convert option value to int or string:
    try:
        option_value = int(option_value)
    except ValueError:
        option_value = '"' + option_value + '"'

    ## 3a) special cases: regexps
    if option_name in ['CFG_BIBINDEX_CHARS_ALPHANUMERIC_SEPARATORS',
                       'CFG_BIBINDEX_CHARS_PUNCTUATION']:
        option_value = 'r"[' + option_value[1:-1] + ']"'

    ## 3b) special cases: True, False, None
    if option_value in ['"True"', '"False"', '"None"']:
        option_value = option_value[1:-1]

    ## 3c) special cases: dicts or lists
    if option_name in ['CFG_WEBSEARCH_FIELDS_CONVERT',
                       'CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS']:
        option_value = option_value[1:-1]

    ## 3d) special cases: cdslangs
    if option_name == 'cdslangs':
        out = "["
        for lang in option_value[1:-1].split(","):
            out += "'%s', " % lang
        out += "]"
        option_value = out

    ## 3e) special cases: multiline
    if option_name == 'CFG_OAI_IDENTIFY_DESCRIPTION':
        # make triple quotes
        option_value = '""' + option_value + '""'

    ## 3f) ignore some options:
    if option_name == 'cdsnameintl':
        # treated elsewhere
        return

    ## 4) finally, return output line:
    return '%s = %s' % (option_name, option_value)

def cli_cmd_update_config_py(conf):
    """
    Update new config.py from conf options, keeping previous
    config.py in a backup copy.
    """
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
    fdesc.write("cdsnameintl = {}\n")
    for lang in conf.get("Invenio", "CFG_SITE_LANGS").split(","):
        fdesc.write("cdsnameintl['%s'] = \"%s\"\n" % (lang, conf.get("Invenio",
                                                                   "CFG_SITE_NAME_INTL_" + lang)))
    ## special treatment for legacy WebSubmit options: (FIXME: phase them out)
    fdesc.write("accessurl = '%s/search'\n" % conf.get("Invenio", "CFG_SITE_URL"))
    fdesc.write("urlpath = '%s'\n" % conf.get("Invenio", "CFG_SITE_URL"))
    fdesc.write("images = '%s/img'\n" % conf.get("Invenio", "CFG_SITE_URL"))
    fdesc.write("htdocsurl = '%s'\n" % conf.get("Invenio", "CFG_SITE_URL"))
    ## process all the options normally:
    for section in conf.sections():
        for option in conf.options(section):
            if not option.startswith('CFG_DATABASE_'):
                # put all options except for db credentials into config.py
                line_out = convert_conf_option(option, conf.get(section, option))
                if line_out:
                    fdesc.write(line_out + "\n")
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
    dbquerypyfile = conf.get("Invenio", "CFG_PYLIBDIR") + \
                    os.sep + 'invenio' + os.sep + 'dbquery.py'
    ## backup current dbquery.py file:
    if os.path.exists(dbquerypyfile):
        shutil.copy(dbquerypyfile, dbquerypyfile + '.OLD')
    ## replace db parameters:
    out = ''
    for line in open(dbquerypyfile, 'r').readlines():
        match = re.search(r'^CFG_DATABASE_(HOST|NAME|USER|PASS)(\s*=\s*)\'.*\'$', line)
        if match:
            dbparam = 'CFG_DATABASE_' + match.group(1)
            out += "%s%s'%s'\n" % (dbparam, match.group(2),
                                   conf.get('Invenio', dbparam))
        else:
            out += line
    fdesc = open(dbquerypyfile, 'w')
    fdesc.write(out)
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
        match = re.search(r'^CFG_DATABASE_(HOST|NAME|USER|PASS)(\s*=\s*)\'.*\'$', line)
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
    http://.../record/ lines, replacing URL with CDSWEB taken from
    conf file.  Note: this edits tpl files in situ, taking a
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
                match = re.search(r'^(.*)http://.*?/record/(.*)$', line)
                if match:
                    out += "%s%s/record/%s\n" % (match.group(1),
                                                 conf.get("Invenio", 'CFG_SITE_URL'),
                                                 match.group(2))
                else:
                    out += line
            fdesc = open(tplfile, 'w')
            fdesc.write(out)
            fdesc.close()
    print ">>> bibconvert templates updated successfully."

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
        run_sql("""INSERT INTO collection (id, name, dbquery, reclist, restricted) VALUES
                                          (1,%s,NULL,NULL,NULL)""", (sitename,))
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

def cli_cmd_reset_adminemail(conf):
    """
    Reset user-related tables with new ADMINEMAIL read from conf files.
    """
    print ">>> Going to reset ADMINEMAIL..."
    from invenio.dbquery import run_sql
    adminemail = conf.get("Invenio", "CFG_SITE_ADMIN_EMAIL")
    run_sql("DELETE FROM user WHERE id=1")
    run_sql("""INSERT INTO user (id, email, password, note, nickname) VALUES
                        (1, %s, AES_ENCRYPT(email, ''), 1, 'admin')""",
            (adminemail,))
    print "You may want to restart Apache now."
    print ">>> ADMINEMAIL reset successfully."

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
                            "experiment": _("experiment"),
                            "record ID": _("record ID"),}
        ## update I18N names for every language:
        for (field_id, field_name) in field_id_name_list:
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
                                 "citation": _("times cited"),}
        for (rankmethod_id, rankmethod_name) in rankmethod_id_name_list:
            try:
                run_sql("""INSERT INTO rnkMETHODNAME (id_rnkMETHOD,ln,type,value) VALUES
                            (%s,%s,%s,%s)""", (rankmethod_id, lang, 'ln',
                                               rankmethod_name_names[rankmethod_name]))
            except IntegrityError:
                run_sql("""UPDATE rnkMETHODNAME SET value=%s
                            WHERE id_rnkMETHOD=%s AND ln=%s AND type=%s""",
                        (rankmethod_name_names[rankmethod_name], rankmethod_id, lang, 'ln',))

    print ">>> I18N field names reset successfully."

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
        from invenio.dbquery import CFG_DATABASE_HOST, CFG_DATABASE_NAME, \
             CFG_DATABASE_USER, CFG_DATABASE_PASS
        print wrap_text_in_a_box("""\
DATABASE CONNECTIVITY ERROR %(errno)d: %(errmsg)s.\n

Perhaps you need to set up database and connection rights?
If yes, then please login as MySQL admin user and run the
following commands now:


 $ mysql -h %(dbhost)s -u root -p mysql
   mysql> CREATE DATABASE %(dbname)s DEFAULT CHARACTER SET utf8;
   mysql> GRANT ALL PRIVILEGES ON %(dbname)s.* TO %(dbuser)s@%(webhost)s IDENTIFIED BY '%(dbpass)s';
   mysql> QUIT


The values printed above were detected from your configuration.
If they are not right, then please edit your invenio.conf file
and rerun 'inveniocfg --update-all' first.


If the problem is of different nature, then please inspect
the above error message and fix the problem before continuing.""" % \
                                 {'errno': err.args[0],
                                  'errmsg': err.args[1],
                                  'dbname': CFG_DATABASE_NAME,
                                  'dbhost': CFG_DATABASE_HOST,
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
        beta_in_utf8 = "β" # Greek beta in UTF-8 is 0xCEB2
        run_sql("CREATE TEMPORARY TABLE test__invenio__utf8 (x char(1), y varbinary(2)) DEFAULT CHARACTER SET utf8")
        run_sql("INSERT INTO test__invenio__utf8 (x, y) VALUES (%s, %s)", (beta_in_utf8, beta_in_utf8))
        res = run_sql("SELECT x,y,HEX(x),HEX(y),LENGTH(x),LENGTH(y),CHAR_LENGTH(x),CHAR_LENGTH(y) FROM test__invenio__utf8")
        assert res[0] == ('\xce\xb2', '\xce\xb2', 'CEB2', 'CEB2', 2L, 2L, 1L, 2L)
        run_sql("DROP TEMPORARY TABLE test__invenio__utf8")
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
    cli_cmd_reset_adminemail(conf)
    cli_cmd_reset_fieldnames(conf)
    for cmd in ["%s/bin/webaccessadmin -u admin -c -a" % CFG_PREFIX]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)
    print ">>> Tables created and filled successfully."

def cli_cmd_drop_tables(conf):
    """Drop Invenio DB tables.  Useful for the uninstallation process."""
    print ">>> Going to drop tables..."
    from invenio.config import CFG_PREFIX
    from invenio.textutils import wrap_text_in_a_box, wait_for_user
    if '--yes-i-know' not in sys.argv:
        wait_for_user(wrap_text_in_a_box("""\
WARNING: You are going to destroy your database tables!\n

Press Ctrl-C if you want to abort this action.\n
Press ENTER to proceed with this action."""))
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
    for cmd in ["%s/bin/dbexec < %s/lib/sql/invenio/democfgdata.sql" % (CFG_PREFIX, CFG_PREFIX),
                "%s/bin/webaccessadmin -u admin -c -r -D" % CFG_PREFIX,
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 1" % CFG_PREFIX,]:
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
    for cmd in ["%s/bin/bibupload -i %s/var/tmp/demobibdata.xml" % (CFG_PREFIX, CFG_PREFIX),
                "%s/bin/bibupload 1" % CFG_PREFIX,
                "%s/bin/bibindex -u admin" % CFG_PREFIX,
                "%s/bin/bibindex 2" % CFG_PREFIX,
                "%s/bin/bibreformat -u admin -o HB" % CFG_PREFIX,
                "%s/bin/bibreformat 3" % CFG_PREFIX,
                "%s/bin/bibupload 4" % CFG_PREFIX,
                "%s/bin/webcoll -u admin" % CFG_PREFIX,
                "%s/bin/webcoll 5" % CFG_PREFIX,
                "%s/bin/bibrank -u admin" % CFG_PREFIX,
                "%s/bin/bibrank 6" % CFG_PREFIX,]:
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
    if '--yes-i-know' not in sys.argv:
        wait_for_user(wrap_text_in_a_box("""\
WARNING: You are going to destroy your records and documents!\n

Press Ctrl-C if you want to abort this action.\n
Press ENTER to proceed with this action."""))
    if os.path.exists(CFG_PREFIX + os.sep + 'var' + os.sep + 'data' + os.sep + 'files'):
        shutil.rmtree(CFG_PREFIX + os.sep + 'var' + os.sep + 'data' + os.sep + 'files')
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
    if '--yes-i-know' not in sys.argv:
        wait_for_user(wrap_text_in_a_box("""\
WARNING: You are going to destroy your site and documents!\n

Press Ctrl-C if you want to abort this action.\n
Press ENTER to proceed with this action."""))
    cli_cmd_drop_tables(conf)
    cli_cmd_create_tables(conf)
    cli_cmd_remove_demo_records(conf)
    print ">>> Demo site dropped successfully."

def cli_cmd_run_unit_tests(conf):
    """Run unit tests, usually on the working demo site."""
    from invenio.config import CFG_PREFIX
    os.system("%s/bin/testsuite" % CFG_PREFIX)

def cli_cmd_run_regression_tests(conf):
    """Run regression tests, usually on the working demo site."""
    from invenio.config import CFG_PREFIX
    if '--yes-i-know' in sys.argv:
        os.system("%s/bin/regressiontestsuite --yes-i-know" % CFG_PREFIX)
    else:
        os.system("%s/bin/regressiontestsuite" % CFG_PREFIX)

def cli_cmd_create_apache_conf(conf):
    """
    Create Apache conf files for this site, keeping previous
    files in a backup copy.
    """
    print ">>> Going to create Apache conf files..."
    from invenio.textutils import wrap_text_in_a_box
    apache_conf_dir = conf.get("Invenio", 'CFG_ETCDIR') + \
                      os.sep + 'apache'
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
NameVirtualHost *:80
<Files *.pyc>
   deny from all
</Files>
<Files *~>
   deny from all
</Files>
<VirtualHost *:80>
        ServerName %(servername)s
        ServerAlias %(serveralias)s
        ServerAdmin %(serveradmin)s
        DocumentRoot %(webdir)s
        <Directory %(webdir)s>
           Options FollowSymLinks MultiViews
           AllowOverride None
           Order allow,deny
           allow from all
        </Directory>
        ErrorLog %(logdir)s/apache.err
        LogLevel warn
        CustomLog %(logdir)s/apache.log combined
        DirectoryIndex index.en.html index.html
        <LocationMatch "^(/+$|/index|/collection|/record|/author|/search|/browse|/youraccount|/youralerts|/yourbaskets|/yourmessages|/yourgroups|/submit|/getfile|/comments|/error|/oai2d|/rss|/help|/journal|/openurl)">
           SetHandler python-program
           PythonHandler invenio.webinterface_layout
           PythonDebug On
        </LocationMatch>
        <Directory %(webdir)s>
           AddHandler python-program .py
           PythonHandler mod_python.publisher
           PythonDebug On
        </Directory>
</VirtualHost>
""" % {'servername': conf.get('Invenio', 'CFG_SITE_URL').replace("http://", ""),
       'serveralias': conf.get('Invenio', 'CFG_SITE_URL').replace("http://", "").split('.')[0],
       'serveradmin': conf.get('Invenio', 'CFG_SITE_ADMIN_EMAIL'),
       'webdir': conf.get('Invenio', 'CFG_WEBDIR'),
       'logdir': conf.get('Invenio', 'CFG_LOGDIR'),
       }
    apache_vhost_ssl_body = """\
ServerSignature Off
ServerTokens Prod
NameVirtualHost *:443
#SSLCertificateFile /etc/apache2/ssl/apache.pem
SSLCertificateFile /etc/apache2/ssl/server.crt
SSLCertificateKeyFile /etc/apache2/ssl/server.key
<Files *.pyc>
   deny from all
</Files>
<Files *~>
   deny from all
</Files>
<VirtualHost *:443>
        ServerName %(servername)s
        ServerAlias %(serveralias)s
        ServerAdmin %(serveradmin)s
        SSLEngine on
        DocumentRoot %(webdir)s
        <Directory %(webdir)s>
           Options FollowSymLinks MultiViews
           AllowOverride None
           Order allow,deny
           allow from all
        </Directory>
        ErrorLog %(logdir)s/apache-ssl.err
        LogLevel warn
        CustomLog %(logdir)s/apache-ssl.log combined
        DirectoryIndex index.en.html index.html
        <LocationMatch "^(/+$|/index|/collection|/record|/search|/browse|/youraccount|/youralerts|/yourbaskets|/yourmessages|/yourgroups|/submit|/getfile|/comments|/error|/oai2d|/rss|/help|/journal|/openurl)">
           SetHandler python-program
           PythonHandler invenio.webinterface_layout
           PythonDebug On
        </LocationMatch>
        <Directory %(webdir)s>
           AddHandler python-program .py
           PythonHandler mod_python.publisher
           PythonDebug On
        </Directory>
</VirtualHost>
""" % {'servername': conf.get('Invenio', 'CFG_SITE_URL_SECURE').replace("http://", ""),
       'serveralias': conf.get('Invenio', 'CFG_SITE_URL_SECURE').replace("http://", "").split('.')[0],
       'serveradmin': conf.get('Invenio', 'CFG_SITE_ADMIN_EMAIL'),
       'webdir': conf.get('Invenio', 'CFG_WEBDIR'),
       'logdir': conf.get('Invenio', 'CFG_LOGDIR'),
       }
    # write HTTP vhost snippet:
    if os.path.exists(apache_vhost_file):
        shutil.copy(apache_vhost_file,
                    apache_vhost_file + '.OLD')
    fdesc = open(apache_vhost_file, 'w')
    fdesc.write(apache_vhost_body)
    fdesc.close()
    print "Created file", apache_vhost_file
    # write HTTPS vhost snippet:
    if conf.get('Invenio', 'CFG_SITE_URL_SECURE') != \
       conf.get('Invenio', 'CFG_SITE_URL'):
        if os.path.exists(apache_vhost_ssl_file):
            shutil.copy(apache_vhost_ssl_file,
                        apache_vhost_ssl_file + '.OLD')
        fdesc = open(apache_vhost_ssl_file, 'w')
        fdesc.write(apache_vhost_ssl_body)
        fdesc.close()
        print "Created file", apache_vhost_ssl_file

    print ""
    print wrap_text_in_a_box("""\
Apache virtual host configurations for your site have been
created. You can check created files and put the following
include statements in your httpd.conf:\n

Include %s
Include %s
    """ % (apache_vhost_file, apache_vhost_ssl_file))
    print ">>> Apache conf files created."

def cli_cmd_get(conf, varname):
    """
    Return value of VARNAME read from CONF files.  Useful for
    third-party programs to access values of conf options such as
    CFG_PREFIX.  Return None if VARNAME is not found.
    """
    # do not pay attention to upper/lower case:
    varname = varname.lower()
    # do not pay attention to section names yet:
    all_options = {}
    for section in conf.sections():
        for option in conf.options(section):
            all_options[option] = conf.get(section, option)
    return  all_options.get(varname, None)

def cli_cmd_list(conf):
    """
    Print a list of all conf options and values from CONF.
    """
    for section in conf.sections():
        for option in conf.options(section):
            print option, '=', conf.get(section, option)

def main():
    """Main entry point."""
    conf = ConfigParser()
    if '--help' in sys.argv or \
       '-h' in sys.argv:
        print_usage()
    elif '--version' in sys.argv or \
         '-V' in sys.argv:
        print_version()
    else:
        confdir = None
        if '--conf-dir' in sys.argv:
            try:
                confdir = sys.argv[sys.argv.index('--conf-dir') + 1]
            except IndexError:
                pass # missing --conf-dir argument value
            if not os.path.exists(confdir):
                print "ERROR: bad or missing --conf-dir option value."
                sys.exit(1)
        else:
            ## try to detect path to conf dir (relative to this bin dir):
            confdir = re.sub(r'/bin$', '/etc', sys.path[0])
        ## read conf files:
        for conffile in [confdir + os.sep + 'invenio.conf',
                         confdir + os.sep + 'invenio-autotools.conf',
                         confdir + os.sep + 'invenio-local.conf',]:
            if os.path.exists(conffile):
                conf.read(conffile)
            else:
                print "ERROR: Badly guessed conf file location", conffile
                print "(Please use --conf-dir option.)"
                sys.exit(1)
        ## decide what to do:
        done = False
        for opt_idx in range(0, len(sys.argv)):
            opt = sys.argv[opt_idx]
            if opt == '--conf-dir':
                # already treated before, so skip silently:
                pass
            elif opt == '--get':
                try:
                    varname = sys.argv[opt_idx + 1]
                except IndexError:
                    print "ERROR: bad or missing --get option value."
                    sys.exit(1)
                if varname.startswith('-'):
                    print "ERROR: bad or missing --get option value."
                    sys.exit(1)
                varvalue = cli_cmd_get(conf, varname)
                if varvalue is not None:
                    print varvalue
                else:
                    sys.exit(1)
                done = True
            elif opt == '--list':
                cli_cmd_list(conf)
                done = True
            elif opt == '--create-tables':
                cli_cmd_create_tables(conf)
                done = True
            elif opt == '--drop-tables':
                cli_cmd_drop_tables(conf)
                done = True
            elif opt == '--create-demo-site':
                cli_cmd_create_demo_site(conf)
                done = True
            elif opt == '--load-demo-records':
                cli_cmd_load_demo_records(conf)
                done = True
            elif opt == '--remove-demo-records':
                cli_cmd_remove_demo_records(conf)
                done = True
            elif opt == '--drop-demo-site':
                cli_cmd_drop_demo_site(conf)
                done = True
            elif opt == '--run-unit-tests':
                cli_cmd_run_unit_tests(conf)
                done = True
            elif opt == '--run-regression-tests':
                cli_cmd_run_regression_tests(conf)
                done = True
            elif opt == '--update-all':
                cli_cmd_update_config_py(conf)
                cli_cmd_update_dbquery_py(conf)
                cli_cmd_update_dbexec(conf)
                cli_cmd_update_bibconvert_tpl(conf)
                done = True
            elif opt == '--update-config-py':
                cli_cmd_update_config_py(conf)
                done = True
            elif opt == '--update-dbquery-py':
                cli_cmd_update_dbquery_py(conf)
                done = True
            elif opt == '--update-dbexec':
                cli_cmd_update_dbexec(conf)
                done = True
            elif opt == '--update-bibconvert-tpl':
                cli_cmd_update_bibconvert_tpl(conf)
                done = True
            elif opt == '--reset-all':
                cli_cmd_reset_sitename(conf)
                cli_cmd_reset_adminemail(conf)
                cli_cmd_reset_fieldnames(conf)
                done = True
            elif opt == '--reset-sitename':
                cli_cmd_reset_sitename(conf)
                done = True
            elif opt == '--reset-adminemail':
                cli_cmd_reset_adminemail(conf)
                done = True
            elif opt == '--reset-fieldnames':
                cli_cmd_reset_fieldnames(conf)
                done = True
            elif opt == '--create-apache-conf':
                cli_cmd_create_apache_conf(conf)
                done = True
            elif opt.startswith("-") and opt != '--yes-i-know':
                print "ERROR: unknown option", opt
                sys.exit(1)
        if not done:
            print """ERROR: Please specify a command.  Please see '--help'."""
            sys.exit(1)

if __name__ == '__main__':
    main()
