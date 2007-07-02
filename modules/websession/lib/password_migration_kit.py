# -*- coding: utf-8 -*-
## $Id$
##
## Every db-related function of module webmessage
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

""" Migration from webbasket [v0.7.1] to [v0.9.0]
Usage: python webbasket_migration_kit.py
This utility will copy records and baskets from CDSware 0.7.1 to CDS Invenio 0.9
It will check for database consistency before copying. Inconsistencies can be:
    - Baskets that do not belong to a user
    - Users that posses baskets that do not exist
    - Baskets that belong to more than one user
This utility won't erase old baskets unless you choose to do it.
It needs new tables (bsk*) to be created before. The new tables should be empty before migration (old basket IDs are also copied and could, therefore, cause
duplicates entries).

Main function: migrate_v071_baskets()
"""

__revision__ = "$Id$"

from invenio.dbquery import run_sql, escape_string
from invenio.webbasket_config import CFG_WEBBASKET_SHARE_LEVELS

import sys


def migrate_passwords():
    print "Password migration kit (for CDS Invenio prior to v0.92.1)"
    print "==============================="
    print "Checking your installation..."
    if __check_update_possibility():
        print "Tables are OK."
    else:
        print "No need to update."
        sys.exit(1)
    admin_pwd = __get_admin_pwd()
    print "There are %i passwords to migrate (including guest users)" % __count_current_passwords()
    print "==============================="
    print "Creating backup...",
    if __creating_backup():
        print " Ok"
    else:
        __print_error()
    print "Migrating all Null password to ''...",
    if __migrate_passwords_from_null_to_empty_quotes():
        print " Ok"
    else:
        __print_error(True)
    print "Changing the column type from string to blob...",
    if __migrate_column_from_string_to_blob():
        print " Ok"
    else:
        __print_error(True)
    print "Encrypting passwords...",
    if __encrypt_password():
        print " Ok"
    else:
        __print_error(True)
    print "Checking that admin could enter...",
    if __check_admin(admin_pwd):
        print " Ok"
    else:
        __print_error(True)
    print "Removing backup...",
    if __removing_backup():
        print " Ok"
    else:
        __print_error()
    print "==============================="
    print "Migration to encrypted local password has been successful."

def __check_update_possibility():
    """"""
    res = run_sql("SHOW COLUMNS FROM user LIKE 'password'");
    if res:
        return res[0][1] in ('tinyblob', 'blob')
    print "User table is broken or CDS Invenio Database is not functional."

def __count_current_passwords():
    query = "SELECT count(*) FROM user"
    return run_sql(query)[0][0]

def __get_admin_pwd():
    query = "SELECT password FROM user WHERE nickname='admin'"
    return run_sql(query)[0][0]

def __migrate_passwords_from_null_to_empty_quotes():
    query = "UPDATE user SET password='' WHERE password=NULL"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    return True

def __migrate_column_from_string_to_blob():
    query = "ALTER TABLE user CHANGE password password BLOB NOT NULL"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    return True

def __encrypt_password():
    query = "UPDATE user SET password=AES_ENCRYPT(email,password)"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    return True

def __check_admin(admin_pwd):
    query = "SELECT nickname FROM user WHERE nickname='admin' AND password=AES_ENCRYPT(email, %s)"
    try:
        if run_sql(query, (admin_pwd, ))[0][0] == 'admin':
            return True
        else:
            return False
    except Exception, msg:
        print msg
        return False

def __creating_backup():
    query = "CREATE TABLE user_backup (PRIMARY KEY id (id)) SELECT * FROM user"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    return True

def __removing_backup():
    query = "DROP TABLE user_backup"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    return True

def __restoring_from_backup():
    query = "UPDATE user SET password=''"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    query = "ALTER TABLE user CHANGE password password varchar(20) NULL default NULL"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    query = "UPDATE user,user_backup SET user.password=user_backup.password WHERE user.id=user_backup.id AND user.nickname=user_backup.nickname"
    try:
        run_sql(query)
    except Exception, msg:
        print msg
        return False
    return True

def __print_error(restore_backup=False):
    print "The kit encountered errors in migrating password. Please contact"
    print "The CDS Invenio developers in order to get support providing all"
    print "the printed messages."
    if restore_backup:
        if __restoring_from_backup():
            print "Passwords were restored from the backup, but you still need to"
            print "migrate them in order to use this version of CDS Invenio."
        else:
            print "The kit was't unable to restore passwords from the backup"
    sys.exit(1)


if __name__ == '__main__':
    migrate_passwords()
