#-*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012 CERN.
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

"""
Invenio 1.1.0 upgrade

DISCLAIMER: This upgrade is special, and should not be used as an example of an
upgrade. Read more below.

This upgrade is special and much more complex than future upgrade will normally
be. Since this is the first upgrade, the upgrade does not depend on other
upgrades. Furthermore the current state of the database is unknown and thus
the upgrade will try to guess the current state, as well as be quite tolerant
towards errors.

To create a new upgrade recipe just run:

  inveniocfg --upgrade-create-standard-recipe=invenio,~/src/invenio/modules/miscutil/lib/upgrades/
"""

import warnings
import logging
from invenio.legacy.dbquery import run_sql

DB_VERSION = None

depends_on = []

def info():
    return "Invenio 1.0.x to 1.1.0 upgrade"

def estimate():
    """ Return estimate of upgrade time in seconds """
    return 10

def do_upgrade():
    """ Perform upgrade """
    tables = _get_tables()
    session_tbl = _get_table_info('session')
    if (DB_VERSION == '1.0.0' or DB_VERSION == 'master') and \
            'session_expiry' not in session_tbl['indexes']:
        _run_sql_ignore("ALTER TABLE session ADD KEY session_expiry " \
                        "(session_expiry)")

    # Create tables
    _create_table(tables, "upgrade", """
        CREATE TABLE IF NOT EXISTS upgrade (
          upgrade varchar(255) NOT NULL,
          applied DATETIME NOT NULL,
          PRIMARY KEY (upgrade)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxWORD17F", """
        CREATE TABLE IF NOT EXISTS idxWORD17F (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term varchar(50) default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxWORD17R", """
        CREATE TABLE IF NOT EXISTS idxWORD17R (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxWORD18F", """
        CREATE TABLE IF NOT EXISTS idxWORD18F (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term varchar(50) default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxWORD18R", """
        CREATE TABLE IF NOT EXISTS idxWORD18R (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPAIR17F", """
        CREATE TABLE IF NOT EXISTS idxPAIR17F (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term varchar(100) default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPAIR17R", """
        CREATE TABLE IF NOT EXISTS idxPAIR17R (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPAIR18F", """
        CREATE TABLE IF NOT EXISTS idxPAIR18F (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term varchar(100) default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPAIR18R", """
        CREATE TABLE IF NOT EXISTS idxPAIR18R (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPHRASE17F", """
        CREATE TABLE IF NOT EXISTS idxPHRASE17F (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term text default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          KEY term (term(50))
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPHRASE17R", """
        CREATE TABLE IF NOT EXISTS idxPHRASE17R (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPHRASE18F", """
        CREATE TABLE IF NOT EXISTS idxPHRASE18F (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term text default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          KEY term (term(50))
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "idxPHRASE18R", """
        CREATE TABLE IF NOT EXISTS idxPHRASE18R (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "bibdocfsinfo", """
        CREATE TABLE IF NOT EXISTS bibdocfsinfo (
          id_bibdoc mediumint(9) unsigned NOT NULL,
          version tinyint(4) unsigned NOT NULL,
          format varchar(50) NOT NULL,
          last_version boolean NOT NULL,
          cd datetime NOT NULL,
          md datetime NOT NULL,
          checksum char(32) NOT NULL,
          filesize bigint(15) unsigned NOT NULL,
          mime varchar(100) NOT NULL,
          master_format varchar(50) NULL default NULL,
          PRIMARY KEY (id_bibdoc, version, format),
          KEY (last_version),
          KEY (format),
          KEY (cd),
          KEY (md),
          KEY (filesize),
          KEY (mime)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "userEXT", """
        CREATE TABLE IF NOT EXISTS userEXT (
          id varbinary(255) NOT NULL,
          method varchar(50) NOT NULL,
          id_user int(15) unsigned NOT NULL,
          PRIMARY KEY (id, method),
          UNIQUE KEY (id_user, method)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "cmtCOLLAPSED", """
        CREATE TABLE IF NOT EXISTS cmtCOLLAPSED (
          id_bibrec int(15) unsigned NOT NULL default '0',
          id_cmtRECORDCOMMENT int(15) unsigned NULL,
          id_user int(15) unsigned NOT NULL,
          PRIMARY KEY (id_user, id_bibrec, id_cmtRECORDCOMMENT)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "aidPERSONIDPAPERS", """
        CREATE TABLE IF NOT EXISTS `aidPERSONIDPAPERS` (
          `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
          `bibref_table` ENUM(  '100',  '700' ) NOT NULL ,
          `bibref_value` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
          `bibrec` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
          `name` VARCHAR( 256 ) NOT NULL ,
          `flag` SMALLINT( 2 ) NOT NULL DEFAULT  '0' ,
          `lcul` SMALLINT( 2 ) NOT NULL DEFAULT  '0' ,
          `last_updated` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ,
          INDEX `personid-b` (`personid`) ,
          INDEX `reftable-b` (`bibref_table`) ,
          INDEX `refvalue-b` (`bibref_value`) ,
          INDEX `rec-b` (`bibrec`) ,
          INDEX `name-b` (`name`) ,
          INDEX `pn-b` (`personid`, `name`) ,
          INDEX `timestamp-b` (`last_updated`) ,
          INDEX `flag-b` (`flag`) ,
          INDEX `ptvrf-b` (`personid`, `bibref_table`, `bibref_value`, `bibrec`, `flag`)
        ) ENGINE=MYISAM;
        """)

    _create_table(tables, "aidRESULTS", """
        CREATE TABLE IF NOT EXISTS `aidRESULTS` (
          `personid` VARCHAR( 256 ) NOT NULL ,
          `bibref_table` ENUM(  '100',  '700' ) NOT NULL ,
          `bibref_value` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
          `bibrec` MEDIUMINT( 8 ) UNSIGNED NOT NULL ,
          INDEX `personid-b` (`personid`) ,
          INDEX `reftable-b` (`bibref_table`) ,
          INDEX `refvalue-b` (`bibref_value`) ,
          INDEX `rec-b` (`bibrec`)
        ) ENGINE=MYISAM;
        """)

    _create_table(tables, "aidPERSONIDDATA", """
        CREATE TABLE IF NOT EXISTS `aidPERSONIDDATA` (
          `personid` BIGINT( 16 ) UNSIGNED NOT NULL ,
          `tag` VARCHAR( 64 ) NOT NULL ,
          `data` VARCHAR( 256 ) NOT NULL ,
          `opt1` MEDIUMINT( 8 ) NULL DEFAULT NULL ,
          `opt2` MEDIUMINT( 8 ) NULL DEFAULT NULL ,
          `opt3` VARCHAR( 256 ) NULL DEFAULT NULL ,
          INDEX `personid-b` (`personid`) ,
          INDEX `tag-b` (`tag`) ,
          INDEX `data-b` (`data`) ,
          INDEX `opt1` (`opt1`)
        ) ENGINE=MYISAM;
        """)

    _create_table(tables, "aidUSERINPUTLOG", """
        CREATE TABLE IF NOT EXISTS `aidUSERINPUTLOG` (
          `id` bigint(15) NOT NULL AUTO_INCREMENT,
          `transactionid` bigint(15) NOT NULL,
          `timestamp` datetime NOT NULL,
          `userid` int,
          `userinfo` varchar(255) NOT NULL,
          `personid` bigint(15) NOT NULL,
          `action` varchar(50) NOT NULL,
          `tag` varchar(50) NOT NULL,
          `value` varchar(200) NOT NULL,
          `comment` text,
          PRIMARY KEY (`id`),
          INDEX `transactionid-b` (`transactionid`),
          INDEX `timestamp-b` (`timestamp`),
          INDEX `userinfo-b` (`userinfo`),
          INDEX `userid-b` (`userid`),
          INDEX `personid-b` (`personid`),
          INDEX `action-b` (`action`),
          INDEX `tag-b` (`tag`),
          INDEX `value-b` (`value`)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "aidCACHE", """
        CREATE TABLE IF NOT EXISTS `aidCACHE` (
          `id` int(15) NOT NULL auto_increment,
          `object_name` varchar(120) NOT NULL,
          `object_key` varchar(120) NOT NULL,
          `object_value` text,
          `last_updated` datetime NOT NULL,
          PRIMARY KEY  (`id`),
          INDEX `name-b` (`object_name`),
          INDEX `key-b` (`object_key`),
          INDEX `last_updated-b` (`last_updated`)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "xtrJOB", """
        CREATE TABLE IF NOT EXISTS `xtrJOB` (
          `id` tinyint(4) NOT NULL AUTO_INCREMENT,
          `name` varchar(30) NOT NULL,
          `last_updated` datetime NOT NULL,
          PRIMARY KEY (`id`)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "bsrMETHOD", """
        CREATE TABLE IF NOT EXISTS bsrMETHOD (
          id mediumint(8) unsigned NOT NULL auto_increment,
          name varchar(20) NOT NULL,
          definition varchar(255) NOT NULL,
          washer varchar(255) NOT NULL,
          PRIMARY KEY (id),
          UNIQUE KEY (name)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "bsrMETHODNAME", """
        CREATE TABLE IF NOT EXISTS bsrMETHODNAME (
          id_bsrMETHOD mediumint(8) unsigned NOT NULL,
          ln char(5) NOT NULL default '',
          type char(3) NOT NULL default 'sn',
          value varchar(255) NOT NULL,
          PRIMARY KEY (id_bsrMETHOD, ln, type)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "bsrMETHODDATA", """
        CREATE TABLE IF NOT EXISTS bsrMETHODDATA (
          id_bsrMETHOD mediumint(8) unsigned NOT NULL,
          data_dict longblob,
          data_dict_ordered longblob,
          data_list_sorted longblob,
          last_updated datetime,
          PRIMARY KEY (id_bsrMETHOD)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "bsrMETHODDATABUCKET", """
        CREATE TABLE IF NOT EXISTS bsrMETHODDATABUCKET (
          id_bsrMETHOD mediumint(8) unsigned NOT NULL,
          bucket_no tinyint(2) NOT NULL,
          bucket_data longblob,
          bucket_last_value varchar(255),
          last_updated datetime,
          PRIMARY KEY (id_bsrMETHOD, bucket_no)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "collection_bsrMETHOD", """
        CREATE TABLE IF NOT EXISTS collection_bsrMETHOD (
          id_collection mediumint(9) unsigned NOT NULL,
          id_bsrMETHOD mediumint(9) unsigned NOT NULL,
          score tinyint(4) unsigned NOT NULL default '0',
          PRIMARY KEY (id_collection, id_bsrMETHOD)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "seqSTORE", """
        CREATE TABLE IF NOT EXISTS seqSTORE (
          id int(15) NOT NULL auto_increment,
          seq_name varchar(15),
          seq_value varchar(20),
          PRIMARY KEY (id),
          UNIQUE KEY seq_name_value (seq_name, seq_value)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "webapikey", """
        CREATE TABLE IF NOT EXISTS webapikey (
          id varchar(150) NOT NULL,
          secret varchar(150) NOT NULL,
          id_user int(15) NOT NULL,
          status varchar(25) NOT NULL default 'OK',
          description varchar(255) default NULL,
          PRIMARY KEY (id),
          KEY (id_user),
          KEY (status)
        ) ENGINE=MyISAM;
        """)

    _create_table(tables, "wapCACHE", """
        CREATE TABLE IF NOT EXISTS `wapCACHE` (
          `object_name` varchar(120) NOT NULL,
          `object_key` varchar(120) NOT NULL,
          `object_value` longtext,
          `object_status` varchar(120),
          `last_updated` datetime NOT NULL,
          PRIMARY KEY  (`object_name`,`object_key`),
          INDEX `last_updated-b` (`last_updated`),
          INDEX `status-b` (`object_status`)
        ) ENGINE=MyISAM;
        """)

    # Insert and alter table queries
    _run_sql_ignore("INSERT INTO sbmALLFUNCDESCR VALUES ('Set_Embargo','Set an embargo on all the documents of a given record.');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Set_Embargo','date_file');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Set_Embargo','date_format');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('User_is_Record_Owner_or_Curator','curator_role');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('User_is_Record_Owner_or_Curator','curator_flag');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Move_Photos_to_Storage','iconformat');")
    _run_sql_ignore("INSERT INTO format (name, code, description, content_type, visibility) VALUES ('Podcast', 'xp', 'Sample format suitable for multimedia feeds, such as podcasts', 'application/rss+xml', 0);")
    _run_sql_ignore("ALTER TABLE accMAILCOOKIE ADD INDEX expiration (expiration);")
    _run_sql_ignore("UPDATE sbmFUNDESC SET function='Move_CKEditor_Files_to_Storage' WHERE function='Move_FCKeditor_Files_to_Storage';")
    _run_sql_ignore("UPDATE sbmALLFUNCDESCR SET function='Move_CKEditor_Files_to_Storage', description='Transfer files attached to the record with the CKEditor' WHERE function='Move_FCKeditor_Files_to_Storage';")
    _run_sql_ignore("UPDATE sbmFUNCTIONS SET function='Move_CKEditor_Files_to_Storage' WHERE function='Move_FCKeditor_Files_to_Storage';")
    _run_sql_ignore("ALTER TABLE schTASK CHANGE proc proc varchar(255) NOT NULL;")
    _run_sql_ignore("ALTER TABLE schTASK ADD sequenceid int(8) NULL default NULL;")
    _run_sql_ignore("ALTER TABLE schTASK ADD INDEX sequenceid (sequenceid);")
    _run_sql_ignore("ALTER TABLE hstTASK CHANGE proc proc varchar(255) NOT NULL;")
    _run_sql_ignore("ALTER TABLE hstTASK ADD sequenceid int(8) NULL default NULL;")
    _run_sql_ignore("ALTER TABLE hstTASK ADD INDEX sequenceid (sequenceid);")
    _run_sql_ignore("ALTER TABLE session CHANGE session_object session_object longblob;")
    _run_sql_ignore("ALTER TABLE session CHANGE session_expiry session_expiry datetime NOT NULL default '0000-00-00 00:00:00';")
    _run_sql_ignore("ALTER TABLE oaiREPOSITORY CHANGE setSpec setSpec varchar(255) NOT NULL default 'GLOBAL_SET';")
    _run_sql_ignore("UPDATE oaiREPOSITORY SET setSpec='GLOBAL_SET' WHERE setSpec='';")
    _run_sql_ignore("ALTER TABLE user_query_basket ADD COLUMN alert_desc TEXT DEFAULT NULL AFTER alert_name;")
    _run_sql_ignore("INSERT INTO sbmALLFUNCDESCR VALUES ('Link_Records','Link two records toghether via MARC');")
    _run_sql_ignore("INSERT INTO sbmALLFUNCDESCR VALUES ('Video_Processing',NULL);")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Link_Records','edsrn');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Link_Records','edsrn2');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Link_Records','directRelationship');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Link_Records','reverseRelationship');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Link_Records','keep_original_edsrn2');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Video_Processing','aspect');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Video_Processing','batch_template');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Video_Processing','title');")
    _run_sql_ignore("INSERT INTO sbmALLFUNCDESCR VALUES ('Set_RN_From_Sysno', 'Set the value of global rn variable to the report number identified by sysno (recid)');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Set_RN_From_Sysno','edsrn');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Set_RN_From_Sysno','rep_tags');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Set_RN_From_Sysno','record_search_pattern');")
    _run_sql_ignore("UPDATE externalcollection SET name='INSPIRE' where name='SPIRES HEP';")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Report_Number_Generation','initialvalue');")
    _run_sql_ignore("INSERT INTO sbmALLFUNCDESCR VALUES ('Notify_URL','Access URL, possibly to post content');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','url');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','data');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','admin_emails');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','content_type');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','attempt_times');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','attempt_sleeptime');")
    _run_sql_ignore("INSERT INTO sbmFUNDESC VALUES ('Notify_URL','user');")
    _run_sql_ignore("ALTER TABLE bibfmt DROP COLUMN id;")
    _run_sql_ignore("ALTER TABLE bibfmt ADD PRIMARY KEY (id_bibrec, format);")
    _run_sql_ignore("ALTER TABLE bibfmt DROP KEY id_bibrec;")
    _run_sql_ignore("ALTER TABLE bibfmt ADD KEY last_updated (last_updated);")
    _run_sql_ignore("ALTER TABLE user_query_basket ADD COLUMN alert_recipient TEXT DEFAULT NULL AFTER alert_desc;")
    _run_sql_ignore("ALTER TABLE format ADD COLUMN last_updated datetime NOT NULL default '0000-00-00' AFTER visibility;")
    _run_sql_ignore("REPLACE INTO sbmFIELDDESC VALUES ('Upload_Files',NULL,'','R',NULL,NULL,NULL,NULL,NULL,'\"\"\"\r\nThis is an example of element that creates a file upload interface.\r\nClone it, customize it and integrate it into your submission. Then add function \r\n\\'Move_Uploaded_Files_to_Storage\\' to your submission functions list, in order for files \r\nuploaded with this interface to be attached to the record. More information in \r\nthe WebSubmit admin guide.\r\n\"\"\"\r\nfrom invenio.legacy.bibdocfile.managedocfiles import create_file_upload_interface\r\nfrom invenio.websubmit_functions.Shared_Functions import ParamFromFile\r\n\r\nindir = ParamFromFile(os.path.join(curdir, \\'indir\\'))\r\ndoctype = ParamFromFile(os.path.join(curdir, \\'doctype\\'))\r\naccess = ParamFromFile(os.path.join(curdir, \\'access\\'))\r\ntry:\r\n    sysno = int(ParamFromFile(os.path.join(curdir, \\'SN\\')).strip())\r\nexcept:\r\n    sysno = -1\r\nln = ParamFromFile(os.path.join(curdir, \\'ln\\'))\r\n\r\n\"\"\"\r\nRun the following to get the list of parameters of function \\'create_file_upload_interface\\':\r\necho -e \\'from invenio.legacy.bibdocfile.managedocfiles import create_file_upload_interface as f\\nprint f.__doc__\\' | python\r\n\"\"\"\r\ntext = create_file_upload_interface(recid=sysno,\r\n                                 print_outside_form_tag=False,\r\n                                 include_headers=True,\r\n                                 ln=ln,\r\n                                 doctypes_and_desc=[(\\'main\\',\\'Main document\\'),\r\n                                                    (\\'additional\\',\\'Figure, schema, etc.\\')],\r\n                                 can_revise_doctypes=[\\'*\\'],\r\n                                 can_describe_doctypes=[\\'main\\'],\r\n                                 can_delete_doctypes=[\\'additional\\'],\r\n                                 can_rename_doctypes=[\\'main\\'],\r\n                                 sbm_indir=indir, sbm_doctype=doctype, sbm_access=access)[1]\r\n','0000-00-00','0000-00-00',NULL,NULL,0);")

def pre_upgrade():
    """
    Run pre-upgrade check conditions to ensure the upgrade can be applied
    without problems.
    """
    logger = logging.getLogger('invenio_upgrader')

    global DB_VERSION  # Needed because we assign to it

    DB_VERSION = _invenio_schema_version_guesser()

    if DB_VERSION == 'unknown':
        raise RuntimeError("Your Invenio database schema version could not be"
            " determined. Please upgrade to Invenio v1.0.0 first.")

    if DB_VERSION == 'pre-0.99.0':
        raise RuntimeError("Upgrading from Invenio versions prior to 0.99 is"
            " not supported. Please upgrade to 0.99.0 first.")

    if DB_VERSION == '0.99.0':
        raise RuntimeError("It seems like you are running Invenio version "
            "0.99.0. Please run the upgrade in the following special way:\n"
            "make install\ninveniocfg --update-all\n"
            "make update-v0.99.0-tables\nmake update-v0.99.6-tables\n"
            "inveniocfg --upgrade\n\nNote: Most warnings printed during "
            "inveniocfg --upgrade can safely be ignored when upgrading from"
            " Invenio 0.99.0.")

    if DB_VERSION in ['0.99.x', '0.99.x-1.0.0']:
        raise RuntimeError("It seems like you are running Invenio version "
            "v0.99.1-v0.99.x. Please run the upgrade in the following special"
            " way:\nmake install\ninveniocfg --update-all\n"
            "make update-v0.99.6-tables\n"
            "inveniocfg --upgrade\n\nNote: Most warnings printed during "
            "inveniocfg --upgrade can safely be ignored when upgrading from"
            " Invenio v0.99.1-0.99.x.")

    if DB_VERSION == 'master':
        warnings.warn("Invenio database schema is on a development version"
            " between 1.0.x and 1.1.0")

        # Run import here, since we are on 1.0-1.1 we know the import will work
        from invenio.utils.text import wait_for_user
        try:
            wait_for_user("\nUPGRADING TO 1.1.0 FROM A DEVELOPMENT VERSION"
                          " WILL LEAD TO MANY WARNINGS! Please thoroughly"
                          " test the upgrade on non-production systems first,"
                          " and pay close attention to warnings.\n")
        except SystemExit:
            raise RuntimeError("Upgrade aborted by user.")
    else:
        logger.info("Invenio version v%s detected." % DB_VERSION)


# ==============
# Helper methods
# ==============

def _create_table(tables, tblname, ddl_stmt):
    """ Create table if it does not already exsits """
    if tblname not in tables:
        run_sql(ddl_stmt)
    else:
        res = run_sql('SHOW CREATE TABLE %s' % tblname)
        your_ddl = res[0][1]
        warnings.warn("Table '%s' already exists but was not supposed to."
               " Please manually compare the CREATE-statment used to create"
               " the table in your database:\n\n%s\n\n"
               "against the following CREATE-statement:\n%s\n"
               % (tblname, "\n".join([x.strip() for x in your_ddl.splitlines()])
                  , "\n".join([x.strip() for x in ddl_stmt.splitlines()])))


def _get_table_info(tblname):
    """ Retrieve fields and indexes in table. """
    try:
        tblinfo = {'fields': {}, 'indexes': {}}
        for f in run_sql("SHOW FIELDS FROM %s" % tblname):
            tblinfo['fields'][f[0]] = f[1:]
        for f in run_sql("SHOW INDEXES FROM %s" % tblname):
            tblinfo['indexes'][f[2]] = f
        return tblinfo
    except Exception:
        return {'fields': {}, 'indexes': {}}


def _get_tables():
    """ Retrieve list of tables in current database. """
    return [x[0] for x in run_sql("SHOW TABLES;")]


def _invenio_schema_version_guesser():
    """ Introspect database to guess Invenio schema version

    Note 1.0.1 did not have any database changes thus 1.0.0 and 1.0.1 schemas
    are identical.

    @return: One of the values pre-0.99.0, 0.99.0, 0.99.x, 0.99.x-1.0.0, 1.0.0,
        1.0.2, master, unknown
    """
    tables = [x[0] for x in run_sql("SHOW TABLES;")]

    invenio_version = {
        'pre-0.99.0': 0,
        '0.99.0': 0,
        '0.99.x': 0,
        '1.0.0': 0,
        '1.0.2': 0,
        '1.1.0': 0,
    }
    # 0.92.x indicators
    if 'oaiHARVEST' in tables:
        tblinfo = _get_table_info('oaiHARVEST')
        if 'bibfilterprogram' not in tblinfo['fields']:
            invenio_version['pre-0.99.0'] += 1

    if 'idxINDEX' in tables:
        tblinfo = _get_table_info('idxINDEX')
        if 'stemming_language' not in tblinfo['fields']:
            invenio_version['pre-0.99.0'] += 1

    if 'format' in tables:
        tblinfo = _get_table_info('format')
        if 'visibility' not in tblinfo['fields']:
            invenio_version['pre-0.99.0'] += 1

    # 0.99.0 indicators
    if 'bibdoc' in tables:
        tblinfo = _get_table_info('bibdoc')
        if 'more_info' not in tblinfo['fields']  and \
                'creation_date' in tblinfo['indexes']:
            invenio_version['0.99.0'] += 1

    if 'schTASK' in tables:
        tblinfo = _get_table_info('schTASK')
        if 'priority' not in tblinfo['fields']:
            invenio_version['0.99.0'] += 1

    if 'sbmAPPROVAL' in tables:
        tblinfo = _get_table_info('sbmAPPROVAL')
        if 'note' not in tblinfo['fields']:
            invenio_version['0.99.0'] += 1

    # 0.99.1-5 indicators
    if 'oaiARCHIVE' in tables and 'oaiREPOSITORY' not in tables:
        if 'sbmAPPROVAL' in tables:
            tblinfo = _get_table_info('sbmAPPROVAL')
            if 'note' in tblinfo['fields']:
                invenio_version['0.99.x'] += 1

    if 'bibdoc' in tables:
        tblinfo = _get_table_info('bibdoc')
        if 'text_extraction_date' not in tblinfo['fields'] \
                and 'more_info' in tblinfo['fields']:
            invenio_version['0.99.x'] += 1

    if 'collection' in tables:
        tblinfo = _get_table_info('collection')
        if 'restricted' in tblinfo['fields']:
            invenio_version['0.99.x'] += 1

    # 1.0.0 indicators
    if 'collection' in tables:
        tblinfo = _get_table_info('collection')
        if 'restricted' not in tblinfo['fields']:
            invenio_version['1.0.0'] += 1

    if 'oaiARCHIVE' not in tables and 'oaiREPOSITORY' in tables:
        invenio_version['1.0.0'] += 1

    if 'cmtRECORDCOMMENT' in tables:
        tblinfo = _get_table_info('cmtRECORDCOMMENT')
        if 'status' in tblinfo['fields']:
            invenio_version['1.0.0'] += 1

    # 1.0.2 indicators
    if 'session' in tables:
        tblinfo = _get_table_info('session')
        if 'session_expiry' in tblinfo['indexes']:
            invenio_version['1.0.2'] += 1

    # '1.1.0/master' indicators
    if 'accMAILCOOKIE' in tables:
        tblinfo = _get_table_info('accMAILCOOKIE')
        if 'expiration' in tblinfo['indexes']:
            invenio_version['1.1.0'] += 1

    if 'schTASK' in tables:
        tblinfo = _get_table_info('schTASK')
        if 'sequenceid' in tblinfo['fields']:
            invenio_version['1.1.0'] += 1

    if 'format' in tables:
        tblinfo = _get_table_info('format')
        if 'last_updated' in tblinfo['fields']:
            invenio_version['1.1.0'] += 1

    if invenio_version['pre-0.99.0'] > 1:
        return 'pre-0.99.0'

    if invenio_version['0.99.0'] >= 1:
        return '0.99.0'

    if invenio_version['0.99.x'] >= 1:
        if invenio_version['1.0.0'] == 0:
            return '0.99.x'
        else:
            return '0.99.x-1.0.0'

    if invenio_version['1.0.0'] >= 1:
        if invenio_version['1.1.0'] == 0:
            if invenio_version['1.0.2'] == 0:
                return '1.0.0'
            else:
                return '1.0.2'
        else:
            return 'master'
    return 'unknown'


def _run_sql_ignore(query, *args, **kwargs):
    """ Execute SQL query but ignore any errors. """
    try:
        run_sql(query, *args, **kwargs)
    except Exception as e:
        warnings.warn("Failed to execute query %s: %s" % (query, unicode(e)))
