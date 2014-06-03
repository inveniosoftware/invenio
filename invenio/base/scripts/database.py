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

from invenio.scriptutils import Manager, change_command_name, print_progress

manager = Manager(usage="Perform database operations")

# Shortcuts for manager options to keep code DRY.
option_yes_i_know = manager.option('--yes-i-know', action='store_true',
                                   dest='yes_i_know', help='use with care!')
option_default_data = manager.option('--no-data', action='store_false',
                                     dest='default_data',
                                     help='do not populate tables with default data')




@option_yes_i_know
def drop(yes_i_know=False):
    """Drops database tables"""

    print ">>> Going to drop tables and related data on filesystem ..."

    from sqlalchemy import event
    from invenio.dateutils import get_time_estimator
    from invenio.textutils import wrap_text_in_a_box, wait_for_user
    from invenio.webstat import destroy_customevents
    from invenio.inveniocfg import test_db_connection
    from invenio.sqlalchemyutils import db, autodiscover_models
    from invenio.bibdocfile import _make_base_dir

    ## Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box("""WARNING: You are going to destroy your database tables and related data on filesystem!"""))

    ## Step 1: test database connection
    test_db_connection()
    autodiscover_models()

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

    from invenio.bibedit_model import Bibdoc
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
    from invenio.dateutils import get_time_estimator
    from invenio.inveniocfg import test_db_connection
    from invenio.sqlalchemyutils import db, autodiscover_models

    test_db_connection()
    autodiscover_models()

    def cfv_after_create(target, connection, **kw):
        print
        print ">>> Modifing table structure..."
        from invenio.dbquery import run_sql
        run_sql('ALTER TABLE collection_field_fieldvalue DROP PRIMARY KEY')
        run_sql('ALTER TABLE collection_field_fieldvalue ADD INDEX id_collection(id_collection)')
        run_sql('ALTER TABLE collection_field_fieldvalue CHANGE id_fieldvalue id_fieldvalue mediumint(9) unsigned')
        #print run_sql('SHOW CREATE TABLE collection_field_fieldvalue')

    from invenio.websearch_model import CollectionFieldFieldvalue
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


def load_fixtures(suffix='', truncate_tables_first=False):
    from invenio.sqlalchemyutils import db, autodiscover_models
    from fixture import SQLAlchemyFixture
    from invenio.importutils import autodiscover_modules

    if len(suffix) > 0:
        related_name_re = ".+_fixtures_%s\.py" % (suffix, )
    else:
        related_name_re = ".+_fixtures\.py"

    fixture_modules = autodiscover_modules(['invenio'],
                                           related_name_re=related_name_re)
    model_modules = autodiscover_models()
    fixtures = dict((f, getattr(ff, f)) for ff in fixture_modules
                    for f in dir(ff) if f[-4:] == 'Data')
    fixture_names = fixtures.keys()
    models = dict((m+'Data', getattr(mm, m)) for mm in model_modules
                  for m in dir(mm) if m+'Data' in fixture_names)

    dbfixture = SQLAlchemyFixture(env=models, engine=db.metadata.bind,
                                  session=db.session)
    data = dbfixture.data(*fixtures.values())

    if len(models) != len(fixtures):
        print ">>> ERROR: There are", len(models), "tables and", len(fixtures), "fixtures."
    else:
        print ">>> There are", len(models), "tables to be loaded."

    if truncate_tables_first:
        print ">>> Going to truncate following tables:",
        print map(lambda t: t.__name__, models.values())
        db.session.execute("TRUNCATE %s" % ('collectionname', ))
        db.session.execute("TRUNCATE %s" % ('collection_externalcollection', ))
        for m in models.values():
            db.session.execute("TRUNCATE %s" % (m.__tablename__, ))
        db.session.commit()

    data.setup()
    db.session.commit()


@option_default_data
def populate(default_data=True):
    """Populate database with default data"""

    from invenio.config import CFG_PREFIX
    from invenio.config_manager import get_conf

    if not default_data:
        print '>>> No data filled...'
        return

    print ">>> Going to fill tables..."

    load_fixtures()

    conf = get_conf()

    from invenio.inveniocfg import cli_cmd_reset_sitename, \
        cli_cmd_reset_siteadminemail, cli_cmd_reset_fieldnames

    cli_cmd_reset_sitename(conf)
    cli_cmd_reset_siteadminemail(conf)
    cli_cmd_reset_fieldnames(conf)

    for cmd in ["%s/bin/webaccessadmin -u admin -c -a" % CFG_PREFIX]:
        if os.system(cmd):
            print "ERROR: failed execution of", cmd
            sys.exit(1)

    from invenio.inveniocfg_upgrader import InvenioUpgrader
    iu = InvenioUpgrader()
    map(iu.register_success, iu.get_upgrades())

    print ">>> Tables filled successfully."


def version():
    """ Get running version of database driver."""
    from invenio.sqlalchemyutils import db
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
    from invenio.sqlalchemyutils import db
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

    from invenio.sqlalchemyutils import db
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
    from invenio.webinterface_handler_flask import create_invenio_flask_app
    app = create_invenio_flask_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
