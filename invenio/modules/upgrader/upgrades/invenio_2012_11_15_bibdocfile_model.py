# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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

"""Upgrade recipe."""

import logging

from invenio.legacy.dbquery import run_sql

from six.moves import cPickle

from sqlalchemy.exc import OperationalError


depends_on = ['invenio_release_1_1_0']

update_needed = True


def info():
    """Info."""
    return "Change of the underlying data model allowing extended " + \
        "BibDocs and MoreInfo"


def do_upgrade():
    """Implement your upgrades here."""
    logger = logging.getLogger('invenio_upgrader')
    if update_needed:
        _backup_tables(logger)
        _update_database_structure_pre(logger)
        recids = _retrieve_fulltext_recids()
        for recid in recids:
            if not _fix_recid(recid, logger):
                logger.info(
                    "ERROR: Failed fixing the record %s" % (str(recid)))
        _update_database_structure_post(logger)
    else:
        logger.info("Update executed but not needed. skipping")


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    res = run_sql("select count(*) from bibdoc")
    if res:
        return int(float(res[0][0]) / 40)
    return 0


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    # Example of raising errors:
    res = run_sql("show create table bibdoc")[0][1]
    global update_needed
    if "more_info" not in res:
        update_needed = False


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
    pass


# private methods

def _update_database_structure_pre(logger):
    """Pre update database structure.

    This function alters the already existing database by adding
    additional columns ... the step from before modification
    """
    logger.info("Adding missing columns to tables")
    try:
        run_sql(
            """ALTER TABLE bibdoc ADD COLUMN doctype varchar(255)
               AFTER more_info""")
    except Exception as e:
        logger.info("WARNING: Problem when altering table. "
                    "Is the database really in the state from before "
                    "the upgrade ? " + str(e))
    try:
        run_sql(
            """ALTER TABLE bibdoc CHANGE COLUMN docname docname varchar(250)
               COLLATE utf8_bin default NULL""")
    except Exception as e:
        logger.info("WARNING: Problem when altering table. "
                    "Is the database really in the state from before "
                    "the upgrade ? " + str(e))

    try:
        run_sql("""ALTER TABLE bibrec_bibdoc ADD COLUMN docname varchar(250)
                   COLLATE utf8_bin NOT NULL default 'file' AFTER id_bibdoc,
                   ADD KEY docname(docname)""")
    except Exception as e:
        logger.info("WARNING: Problem when altering table. "
                    "Is the database really in the state from before the "
                    "upgrade ? " + str(e))

    try:
        run_sql("""ALTER TABLE bibdoc_bibdoc CHANGE COLUMN id_bibdoc1
                   id_bibdoc1 mediumint(9) unsigned DEFAULT NULL""")
        run_sql("""ALTER TABLE bibdoc_bibdoc CHANGE COLUMN id_bibdoc2
                   id_bibdoc2 mediumint(9) unsigned DEFAULT NULL""")
        run_sql("""ALTER TABLE bibdoc_bibdoc ADD COLUMN id mediumint(9)
                   unsigned NOT NULL auto_increment FIRST,
                   ADD COLUMN version1 tinyint(4) unsigned AFTER id_bibdoc1,
                   ADD COLUMN format1 varchar(50) AFTER version1,
                   ADD COLUMN version2 tinyint(4) unsigned AFTER id_bibdoc2,
                   ADD COLUMN format2 varchar(50) AFTER version2,
                   CHANGE COLUMN type rel_type varchar(255)
                   AFTER format2, ADD KEY (id)""")
    except Exception as e:
        logger.info("WARNING: Problem when altering table. "
                    "Is the database really in the state from before "
                    "the upgrade ? " + str(e))

    run_sql("""CREATE TABLE IF NOT EXISTS bibdocmoreinfo (
        id_bibdoc mediumint(9) unsigned DEFAULT NULL,
        version tinyint(4) unsigned DEFAULT NULL,
        format VARCHAR(50) DEFAULT NULL,
        id_rel mediumint(9) unsigned DEFAULT NULL,
        namespace VARCHAR(25) DEFAULT NULL,
        data_key VARCHAR(25),
        data_value MEDIUMBLOB,
        KEY (id_bibdoc, version, format, id_rel, namespace, data_key)
    ) ENGINE=MyISAM;""")


def _update_database_structure_post(logger):
    """The function alters the already existing database by removing columns.

    the step after the modification
    """
    logger.info("Removing unnecessary columns from tables")
    run_sql("ALTER TABLE bibdoc DROP COLUMN more_info")


def _backup_tables(logger):
    """Backup tables.

    This function create a backup of bibrec_bibdoc, bibdoc and bibdoc_bibdoc
    tables. Returns False in case dropping of previous table is needed.
    """
    logger.info("droping old backup tables")
    run_sql('DROP TABLE IF EXISTS bibrec_bibdoc_backup_newdatamodel')
    run_sql('DROP TABLE IF EXISTS bibdoc_backup_newdatamodel')
    run_sql('DROP TABLE IF EXISTS bibdoc_bibdoc_backup_newdatamodel')

    try:
        run_sql("""CREATE TABLE bibrec_bibdoc_backup_newdatamodel
                   SELECT * FROM bibrec_bibdoc""")
        run_sql("""CREATE TABLE bibdoc_backup_newdatamodel
                   SELECT * FROM bibdoc""")
        run_sql("""CREATE TABLE bibdoc_bibdoc_backup_newdatamodel
                   SELECT * FROM bibdoc_bibdoc""")
    except OperationalError:
        logger.info("Problem when backing up tables")
        raise
    return True


def _retrieve_fulltext_recids():
    """Return fulltext recids.

    Returns the list of all the recid number linked with at least a fulltext
    file.
    """
    res = run_sql('SELECT DISTINCT id_bibrec FROM bibrec_bibdoc')
    return [int(x[0]) for x in res]


def _fix_recid(recid, logger):
    """Fix a given recid."""
    # logger.info("Upgrading record %s:" % recid)
    # 1) moving docname and type to the relation with bibrec
    bibrec_docs = run_sql("""select id_bibdoc, type from bibrec_bibdoc
                             where id_bibrec=%s""", (recid, ))
    are_equal = True

    for docid_str in bibrec_docs:
        docid = str(docid_str[0])
        doctype = str(docid_str[1])

        # logger.info("Upgrading document %s:" % (docid, ))
        res2 = run_sql(
            "select docname, more_info from bibdoc where id=%s", (docid,))
        if not res2:
            logger.error(("Error when migrating document %s attached to the "
                          "record %s: can not retrieve from the bibdoc table ")
                         % (docid, recid))
        else:
            docname = str(res2[0][0])
            run_sql("""update bibrec_bibdoc set docname=%%s where id_bibrec=%s
                       and id_bibdoc=%s""" % (str(recid), docid), (docname, ))
            run_sql("update bibdoc set doctype=%%s where id=%s"
                    % (docid,), (doctype, ))

        # 2) moving moreinfo to the new moreinfo structures (default namespace)
        if res2[0][1]:
            minfo = cPickle.loads(res2[0][1])
            # 2a migrating descriptions->version->format
            new_value = cPickle.dumps(minfo.get('descriptions', {}))
            run_sql("""INSERT INTO bibdocmoreinfo
                       (id_bibdoc, namespace, data_key, data_value)
                       VALUES (%s, %s, %s, %s)""",
                    (str(docid), "", "descriptions", new_value))
            # 2b migrating comments->version->format
            new_value = cPickle.dumps(minfo.get('comments', {}))
            run_sql("""INSERT INTO bibdocmoreinfo
                       (id_bibdoc, namespace, data_key, data_value)
                       VALUES (%s, %s, %s, %s)""",
                    (str(docid), "", "comments", new_value))
            # 2c migrating flags->flagname->version->format
            new_value = cPickle.dumps(minfo.get('flags', {}))
            run_sql("""INSERT INTO bibdocmoreinfo
                       (id_bibdoc, namespace, data_key, data_value)
                       VALUES (%s, %s, %s, %s)""",
                    (str(docid), "", "flags", new_value))

            # 3) Verify the correctness of moreinfo transformations
            try:
                descriptions = cPickle.loads(run_sql(
                    """SELECT data_value FROM bibdocmoreinfo
                       WHERE id_bibdoc=%s AND namespace=%s AND data_key=%s""",
                    (str(docid), '', 'descriptions'))[0][0])
                for version in minfo.get('descriptions', {}):
                    for docformat in minfo['descriptions'][version]:
                        v1 = descriptions[version][docformat]
                        v2 = minfo['descriptions'][version][docformat]
                        if v1 != v2:
                            are_equal = False
                            logger.info(("ERROR: Document %s: Expected "
                                        "description %s and got %s")
                                        % (str(docid), str(v2), str(v1)))
            except Exception as e:
                logger.info(("ERROR: Document %s: Problem with retrieving "
                            "descriptions: %s  MoreInfo: %s Descriptions: %s")
                            % (str(docid), str(e), str(minfo),
                               str(descriptions)))

            try:
                comments = cPickle.loads(run_sql(
                    """SELECT data_value FROM bibdocmoreinfo
                       WHERE id_bibdoc=%s AND namespace=%s AND data_key=%s""",
                    (str(docid), '', 'comments'))[0][0])
                for version in minfo.get('comments', {}):
                    for docformat in minfo['comments'][version]:

                        v1 = comments[version][docformat]
                        v2 = minfo['comments'][version][docformat]
                        if v1 != v2:
                            are_equal = False
                            logger.info(("ERROR: Document %s: Expected "
                                         "comment %s and got %s")
                                        % (str(docid), str(v2), str(v1)))
            except Exception as e:
                logger.info(("ERROR: Document %s: Problem with retrieving "
                             "comments: %s MoreInfo: %s  Comments: %s")
                            % (str(docid), str(e), str(minfo), str(comments)))

            try:
                flags = cPickle.loads(run_sql(
                    """SELECT data_value FROM bibdocmoreinfo
                       WHERE id_bibdoc=%s AND namespace=%s AND data_key=%s""",
                    (str(docid), '', 'flags'))[0][0])
                for flagname in minfo.get('flags', {}):
                    for version in minfo['flags'][flagname]:
                        for docformat in minfo['flags'][flagname][version]:
                            if minfo['flags'][flagname][version][docformat]:
                                are_equal = are_equal and \
                                    (docformat in flags[flagname][version])
                                if not (docformat in flags[flagname][version]):
                                    logger.info(("ERROR: Document %s: "
                                                 "Expected  %s")
                                                % (str(docid), str(minfo)))
            except Exception as e:
                logger.info(("ERROR: Document %s: Problem with retrieving "
                             "flags. %s MoreInfo: %s  flags: %s")
                            % (str(docid), str(e), str(minfo), str(flags)))

            if not are_equal:
                logger.info(("Failed to move MoreInfo structures from old "
                             "database to the new one docid: %s")
                            % (str(docid),))

    return are_equal
