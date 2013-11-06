# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

import os
import sys
import shutil
import datetime

from pipes import quote
from flask import current_app
from invenio.ext.script import Manager, change_command_name, print_progress

manager = Manager(usage="Perform database operations")

# Shortcuts for manager options to keep code DRY.
option_yes_i_know = manager.option('--yes-i-know', action='store_true',
                                   dest='yes_i_know', help='use with care!')
option_default_data = manager.option('--no-data', action='store_false',
                                     dest='default_data',
                                     help='do not populate tables with default data')


@manager.option('-u', '--user', dest='user', default="root")
@manager.option('-p', '--password', dest='password', default="")
@option_yes_i_know
def init(user='root', password='', yes_i_know=False):
    """Initializes database and user."""
    from invenio.ext.sqlalchemy import db
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user

    ## Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box("""WARNING: You are going to destroy your database tables! Run first `inveniomanage database drop`."""))

    ## Step 1: drop database and recreate it
    if db.engine.name == 'mysql':
        #FIXME improve escaping
        args = dict((k, str(v).replace('$', '\$'))
                    for (k, v) in current_app.config.iteritems()
                    if k.startswith('CFG_DATABASE'))
        args = dict(zip(args, map(quote, args.values())))
        prefix = ('{cmd} -u {user} --password={password} '
                  '-h {CFG_DATABASE_HOST} -P {CFG_DATABASE_PORT} ')
        cmd_prefix = prefix.format(cmd='mysql', user=user, password=password,
                                   **args)
        cmd_admin_prefix = prefix.format(cmd='mysqladmin', user=user,
                                         password=password,
                                         **args)
        cmds = [
            cmd_prefix + '-e "DROP DATABASE IF EXISTS {CFG_DATABASE_NAME}"',
            (cmd_prefix + '-e "CREATE DATABASE IF NOT EXISTS '
             '{CFG_DATABASE_NAME} DEFAULT CHARACTER SET utf8 '
             'COLLATE utf8_general_ci"'),
            # Create user and grant access to database.
            (cmd_prefix + '-e "GRANT ALL PRIVILEGES ON '
             '{CFG_DATABASE_USER}.* TO {CFG_DATABASE_NAME}@localhost '
             'IDENTIFIED BY {CFG_DATABASE_PASS}"'),
            cmd_admin_prefix + 'flush-privileges'
        ]
        for cmd in cmds:
            cmd = cmd.format(**args)
            print cmd
            if os.system(cmd):
                print "ERROR: failed execution of", cmd
                sys.exit(1)
        print '>>> Database has been installed.'

@option_yes_i_know
def drop(yes_i_know=False):
    """Drops database tables"""

    print ">>> Going to drop tables and related data on filesystem ..."

    from sqlalchemy import event
    from invenio.utils.date import get_time_estimator
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user
    from invenio.webstat import destroy_customevents
    from invenio.legacy.inveniocfg import test_db_connection
    from invenio.base.utils import autodiscover_models
    from invenio.ext.sqlalchemy import db
    from invenio.bibdocfile import _make_base_dir

    ## Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box("""WARNING: You are going to destroy your database tables and related data on filesystem!"""))

    ## Step 1: test database connection
    test_db_connection()
    list(autodiscover_models())

    ## Step 2: disable foreign key checks
    if db.engine.name == 'mysql':
        db.engine.execute('SET FOREIGN_KEY_CHECKS=0;')

    ## Step 3: destroy associated data
    try:
        msg = destroy_customevents()
        if msg:
            print msg
    except:
        print "ERROR: Could not destroy customevents."

    ## FIXME: move to bibedit_model
    def bibdoc_before_drop(target, connection_dummy, **kw_dummy):
        print
        print ">>> Going to remove records data..."
        for (docid,) in db.session.query(target.c.id).all():
            directory = _make_base_dir(docid)
            if os.path.isdir(directory):
                print '    >>> Removing files for docid =', docid
                shutil.rmtree(directory)
        db.session.commit()
        print ">>> Data has been removed."

    from invenio.modules.record_editor.models import Bibdoc
    event.listen(Bibdoc.__table__, "before_drop", bibdoc_before_drop)

    tables = list(reversed(db.metadata.sorted_tables))
    N = len(tables)

    prefix = '>>> Dropping %d tables ...' % N

    e = get_time_estimator(N)
    dropped = 0

    for i, table in enumerate(tables):
        try:
            print_progress(1.0 * i / N, prefix=prefix,
                            suffix=str(datetime.timedelta(seconds=e()[0])))
            table.drop(bind=db.engine)
            dropped += 1
        except:
            print '\r', '>>> problem with dropping table', table

    print
    if dropped == N:
        print ">>> Tables dropped successfully."
    else:
        print "ERROR: not all tables were properly dropped."
        print ">>> Dropped", dropped, 'out of', N


@option_default_data
def create(default_data=True):
    """Creates database tables from sqlalchemy models"""

    print ">>> Going to create tables..."

    from sqlalchemy import event
    from invenio.utils.date import get_time_estimator
    from invenio.legacy.inveniocfg import test_db_connection
    from invenio.base.utils import autodiscover_models
    from invenio.ext.sqlalchemy import db
    try:
        test_db_connection()
    except:
        from invenio.errorlib import get_tracestack
        print get_tracestack()

    list(autodiscover_models())

    def cfv_after_create(target, connection, **kw):
        print
        print ">>> Modifing table structure..."
        from invenio.dbquery import run_sql
        run_sql('ALTER TABLE collection_field_fieldvalue DROP PRIMARY KEY')
        run_sql('ALTER TABLE collection_field_fieldvalue ADD INDEX id_collection(id_collection)')
        run_sql('ALTER TABLE collection_field_fieldvalue CHANGE id_fieldvalue id_fieldvalue mediumint(9) unsigned')
        #print run_sql('SHOW CREATE TABLE collection_field_fieldvalue')

    from invenio.modules.search.models import CollectionFieldFieldvalue
    event.listen(CollectionFieldFieldvalue.__table__, "after_create", cfv_after_create)

    tables = db.metadata.sorted_tables
    N = len(tables)

    prefix = '>>> Creating %d tables ...' % N

    e = get_time_estimator(N)
    created = 0

    for i, table in enumerate(tables):
        try:
            print_progress(1.0 * i / N, prefix=prefix,
                            suffix=str(datetime.timedelta(seconds=e()[0])))
            table.create(bind=db.engine)
            created += 1
        except:
            print '\r', '>>> problem with creating table', table

    print

    if created == N:
        print ">>> Tables created successfully."
    else:
        print "ERROR: not all tables were properly created."
        print ">>> Created", created, 'out of', N

    populate(default_data)


@option_yes_i_know
@option_default_data
def recreate(yes_i_know=False, default_data=True):
    """Recreates database tables (same as issuing 'drop' and then 'create')"""
    drop()
    create(default_data)


@manager.command
def uri():
    """Prints SQLAlchemy database uri."""
    from flask import current_app
    print current_app.config['SQLALCHEMY_DATABASE_URI']


def load_fixtures(packages=['invenio.modules.*'], truncate_tables_first=False):
    from invenio.base.utils import autodiscover_models, \
        import_module_from_packages
    from invenio.ext.sqlalchemy import db
    from fixture import SQLAlchemyFixture

    fixture_modules = list(import_module_from_packages('fixtures',
                                                       packages=packages))
    model_modules = list(autodiscover_models())
    fixtures = dict((f, getattr(ff, f)) for ff in fixture_modules
                    for f in dir(ff) if f[-4:] == 'Data')
    fixture_names = fixtures.keys()
    models = dict((m+'Data', getattr(mm, m)) for mm in model_modules
                  for m in dir(mm) if m+'Data' in fixture_names)

    dbfixture = SQLAlchemyFixture(env=models, engine=db.metadata.bind,
                                  session=db.session)
    data = dbfixture.data(*[f for (n, f) in fixtures.iteritems() if n in models])
    if len(models) != len(fixtures):
        print ">>> ERROR: There are", len(models), "tables and", len(fixtures), "fixtures."
        print ">>>", set(fixture_names) ^ set(models.keys())
    else:
        print ">>> There are", len(models), "tables to be loaded."

    if truncate_tables_first:
        print ">>> Going to truncate following tables:",
        print map(lambda t: t.__tablename__, models.values())
        db.session.execute("TRUNCATE %s" % ('collectionname', ))
        db.session.execute("TRUNCATE %s" % ('collection_externalcollection', ))
        for m in models.values():
            db.session.execute("TRUNCATE %s" % (m.__tablename__, ))
        db.session.commit()

    data.setup()
    db.session.commit()


@option_default_data
@manager.option('--truncate', action='store_true',
                dest='truncate_tables_first', help='use with care!')
def populate(default_data=True, truncate_tables_first=False):
    """Populate database with default data"""

    from invenio.config import CFG_PREFIX
    from invenio.base.scripts.config import get_conf

    if not default_data:
        print '>>> No data filled...'
        return

    print ">>> Going to fill tables..."

    load_fixtures(truncate_tables_first=truncate_tables_first)

    conf = get_conf()

    from invenio.legacy.inveniocfg import cli_cmd_reset_sitename, \
        cli_cmd_reset_siteadminemail, cli_cmd_reset_fieldnames

    cli_cmd_reset_sitename(conf)
    cli_cmd_reset_siteadminemail(conf)
    cli_cmd_reset_fieldnames(conf)

    for cmd in ["%s/bin/webaccessadmin -u admin -c -a" % CFG_PREFIX]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)

    from invenio.modules.upgrader.engine import InvenioUpgrader
    iu = InvenioUpgrader()
    map(iu.register_success, iu.get_upgrades())

    print ">>> Tables filled successfully."


def version():
    """ Get running version of database driver."""
    from invenio.ext.sqlalchemy import db
    try:
        return db.engine.dialect.dbapi.__version__
    except:
        import MySQLdb
        return MySQLdb.__version__


@manager.option('-v', '--verbose', action='store_true', dest='verbose',
                help='Display more details (driver version).')
@change_command_name
def driver_info(verbose=False):
    """ Get name of running database driver."""
    from invenio.ext.sqlalchemy import db
    try:
        return db.engine.dialect.dbapi.__name__ + (('==' + version())
                                                   if verbose else '')
    except:
        import MySQLdb
        return MySQLdb.__name__ + (('==' + version()) if verbose else '')


@manager.option('-l', '--line-format', dest='line_format', default="%s: %s")
@manager.option('-s', '--separator', dest='separator', default="\n")
@change_command_name
def mysql_info(separator=None, line_format=None):
    """
    Detect and print MySQL details useful for debugging problems on various OS.
    """

    from invenio.ext.sqlalchemy import db
    if db.engine.name != 'mysql':
        raise Exception('Database engine is not mysql.')

    from invenio.dbquery import run_sql
    out = []
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
            out.append((key, val))

    if separator is not None:
        if line_format is None:
            line_format = "%s: %s"
        return separator.join(map(lambda i: line_format % i, out))

    return dict(out)


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
