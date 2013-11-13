# -*- coding: utf-8 -*-
##
## Every db-related function of module webmessage
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

""" Migration from local clear password [v0.92.1] to local encrypted
 password_migration_kit
Usage: python password_migration_kit.py
This utility will encrypt all the local passwords stored in the database.
The encryption is not optional with the current Invenio code if local accounts
are used.
A backup copy of the user table will be created before the migration just in
case something goes wrong.
"""

__revision__ = "$Id$"

from invenio.legacy.dbquery import run_sql
from invenio.utils.text import wrap_text_in_a_box
import sys

def migrate_passwords():
    print wrap_text_in_a_box(title="Password migration kit (for Invenio prior to v0.92.1)", style='conclusion')
    print "Checking your installation..."
    if __check_update_possibility():
        print "Tables are OK."
    else:
        print "No need to update."
        sys.exit(1)
    admin_pwd = __get_admin_pwd()
    print "There are %i passwords to migrate (including guest users)" % __count_current_passwords()
    print "========================================================="
    print "Creating backup...",
    sys.stdout.flush()
    if __creating_backup():
        print "OK"
    else:
        __print_error()
    print "Migrating all Null password to ''...",
    sys.stdout.flush()
    if __migrate_passwords_from_null_to_empty_quotes():
        print "OK"
    else:
        __print_error(True)
    print "Changing the column type from string to blob...",
    sys.stdout.flush()
    if __migrate_column_from_string_to_blob():
        print "OK"
    else:
        __print_error(True)
    print "Encrypting passwords...",
    sys.stdout.flush()
    if __encrypt_password():
        print "OK"
    else:
        __print_error(True)
    print "Checking that admin could enter...",
    sys.stdout.flush()
    if __check_admin(admin_pwd):
        print "OK"
    else:
        __print_error(True)
    print "Removing backup...",
    sys.stdout.flush()
    if __removing_backup():
        print "OK"
    else:
        __print_error()
    print "========================================================="
    print "Migration to encrypted local passwords has been successful."

def __check_update_possibility():
    res = run_sql("SHOW COLUMNS FROM user LIKE 'password'");
    if res:
        return res[0][1] not in ('tinyblob', 'blob')
    print "User table is broken or Invenio Database is not functional."

def __count_current_passwords():
    query = "SELECT count(*) FROM user"
    return run_sql(query)[0][0]

def __get_admin_pwd():
    query = "SELECT password FROM user WHERE nickname='admin'"
    return run_sql(query)[0][0]

def __migrate_passwords_from_null_to_empty_quotes():
    query = "UPDATE user SET password='' WHERE password IS NULL"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    return True

def __migrate_column_from_string_to_blob():
    query = "ALTER TABLE user CHANGE password password BLOB NOT NULL"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    return True

def __encrypt_password():
    query = "UPDATE user SET password=AES_ENCRYPT(email,password)"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
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
        print 'The query "%s" produced: %s' % (query, msg)
        return False

def __creating_backup():
    query = "CREATE TABLE user_backup (PRIMARY KEY id (id)) SELECT id, email, password, note, settings, nickname, last_login FROM user"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    return True

def __removing_backup():
    query = "DROP TABLE user_backup"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    return True

def __restoring_from_backup():
    query = "UPDATE user SET password=''"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    query = "ALTER TABLE user CHANGE password password varchar(20) NULL default NULL"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    query = "UPDATE user,user_backup SET user.password=user_backup.password WHERE user.id=user_backup.id AND user.nickname=user_backup.nickname"
    try:
        run_sql(query)
    except Exception, msg:
        print 'The query "%s" produced: %s' % (query, msg)
        return False
    return True

def __print_error(restore_backup=False):
    print wrap_text_in_a_box("The kit encountered errors in migrating passwords. Please contact The Invenio developers in order to get support providing all the printed messages.")
    if restore_backup:
        if __restoring_from_backup():
            print wrap_text_in_a_box("Passwords were restored from the backup, but you still need to migrate them in order to use this version of Invenio.")
        else:
            print wrap_text_in_a_box("The kit was't unable to restore passwords from the backup")
    sys.exit(1)

if __name__ == '__main__':
    migrate_passwords()
