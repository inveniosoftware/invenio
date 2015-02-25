# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

from __future__ import print_function

""" Migration from webbasket [v0.7.1] to [v0.9.0]
Usage: python webbasket_migration_kit.py
This utility will copy records and baskets from CDSware 0.7.1 to Invenio 0.9
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

from invenio.base.globals import cfg
from invenio.legacy.dbquery import run_sql, real_escape_string
import sys


def migrate_v071_baskets():
    default_topic_name = ''
    default_share_level = ''
    print("Basket migration kit (for CDSware prior to v0.7.1 -> v0.90)")
    print("===============================")
    print("Checking your installation...")
    if __check_update_possibility():
        print("Tables are OK, please answer the next two questions in order to migrate your existing baskets")
    else:
        sys.exit(1)
    print("There are %i baskets to migrate" % __count_current_baskets())
    print("===============================")
    print("In new WebBasket module, baskets are stored in topics.")
    print('Name of default topic [Default topic]: ', end=' ')
    default_topic_name = raw_input() or "Default topic"
    def choose_share_level():
        print("===============================")
        print("Public baskets now have share levels. Please choose between:")
        print("  0: current public baskets should not be public anymore")
        print("  1: people can view content [default]")
        print("  2: people can view content and comments")
        print("  3: people can add comments")
        print("  4: people can add records to baskets")
        print('Share level for current public baskets [1]: ', end=' ')
        return raw_input() or '1'
    choosed = 0
    while not(choosed):
        default_share_level = choose_share_level()
        try:
            default_share_level = int(default_share_level)
            if default_share_level in range(0, 5):
                choosed = 1
            else:
                choosed = 0
        except:
            choosed = 0
    share_levels = [None,
                    cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM'],
                    cfg['CFG_WEBBASKET_SHARE_LEVELS']['READCMT'],
                    cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDCMT'],
                    cfg['CFG_WEBBASKET_SHARE_LEVELS']['ADDITM']]
    default_share_level = share_levels[default_share_level]
    print("===============================")
    print("Checking database consistency...")
    problem = 0
    owners_list = __check_every_basket_has_one_owner()
    if len(owners_list):
        print("  -----------------------------")
        print("  Warning! There are baskets without owners.")
        print("  The following basket ids exist in table 'basket' but not in 'user_basket'")
        for (bskid, junk) in owners_list:
            print("    " + str(bskid))
        print("  -----------------------------")
        problem = 1
    else:
        print("  Baskets' ownership: OK")
    baskets_list = __check_baskets_exist()
    if len(baskets_list):
        print("  -----------------------------")
        print("  Warning! Users own unexisting baskets")
        print("  The following basket ids exist in table 'user_basket' but not in 'basket'")
        for (bskid, junk) in baskets_list:
            print("    " + str(bskid))
        problem = 1
        print("  -----------------------------")
    else:
        print("  Baskets' existence: OK")
    baskets_list = __check_basket_is_owned_by_only_one_user()
    if len(baskets_list):
        print("  -----------------------------")
        print("  Warning! Some baskets are owned by more than one user")
        print("  The following basket ids are mentioned several times in table 'user_basket'")
        for (bskid, junk) in baskets_list:
            print("    " + str(bskid) + " (%i records)" % __count_records(bskid))
        problem = 1
        print("  -----------------------------")
    else:
        print("  Multiple owners: OK")
    if problem:
        print("Problems have been detected. Please fix them before continuing.")
        print("Tables you should look at: basket, user_basket, basket_record, user_query_basket")
        sys.exit(1)
    print("===============================")
    print("Copying baskets...")
    nb_baskets = "N/A"
    try:
        nb_baskets = __import_baskets(default_topic_name, default_share_level)
    except:
        print("There was an error while importing baskets.")
        print("Table bskBASKET was perhaps not empty?")
        print("Migration cancelled")
        sys.exit(1)
    print("%s baskets haven been imported." % str(nb_baskets))
    print("===============================")
    print("Copying records... (time for a coffee break!)")
    nb_records = "N/A"
    try:
        nb_records = __import_records()
    except:
        print("There was an error while importing records.")
        print("Table bskREC was perhaps not empty?")
        print("Migration cancelled")
        sys.exit(1)
    print("%s records haven been imported." % str(nb_records))
    print("===============================")
    print("Updating auto-increment values.")
    try:
        __set_auto_increment_value()
    except:
        print("There was an error:")
        print("Could not set new auto-increment value to table 'bskBASKET'")
        sys.exit(1)
    def choose_delete():
        print("===============================")
        print("Would you like to remove old tables (type y or n)? [n]")
        return raw_input() or 'n'
    choosed = 0
    while not(choosed):
        delete = choose_delete()
        try:
            delete = str(delete)[0]
            if delete in ('y','n'):
                choosed = 1
            else:
                choosed = 0
        except:
            choosed = 0
    if delete == 'y':
        try:
            __drop_baskets()
        except:
            print("There was an error while deleting old tables")
            sys.exit(1)
        print("Old baskets have been erased")
    print("===============================")
    print("Migration to new basket system has been successful.")

def __check_update_possibility():
    """"""
    res = run_sql("SHOW TABLES LIKE '%basket%'");
    def v071filter(element):
        if element[0] in ['user_basket', 'basket', 'basket_record']:
            return 1
        return 0
    if len(filter(v071filter, res)) != 3:
        print("Tables 'basket', 'user_basket' and 'basket_record' do not seem to exist.")
        print("Migration is not necessary")
        return 0
    res = run_sql("SHOW TABLES LIKE '%bsk%'")
    def v090filter(element):
        if element[0] in ['user_bskBASKET', 'bskREC', 'bskBASKET', 'usergroup_bskBASKET']:
            return 1
        return 0
    if len(filter(v090filter, res)) != 4:
        print("Tables 'bskBASKET', 'user_bskBASKET', 'usergroup_bskBASKET and 'bskREC' do not seem to exist.")
        print("Please run make create-tables in a shell")
        return 0
    query1 = "SELECT count(*) from bskBASKET"
    new_bsk_nb = run_sql(query1)[0][0]
    if new_bsk_nb:
        print("Table bskBASKET does not seem to be empty. Migration has already been done")
        return 0
    query2 = "SELECT count(*) from bskREC"
    new_rec_nb = run_sql(query2)[0][0]
    if new_rec_nb:
        print("Table bskREC does not seem to be empty. Migration has already been done")
        return 0
    query3 = "SELECT count(*) from user_bskBASKET"
    new_ubsk_nb = run_sql(query3)[0][0]
    if new_ubsk_nb:
        print("Table user_bskBASKET does not seem to be empty. Migration has already been done")
        return 0
    query4 = "SELECT count(*) from usergroup_bskBASKET"
    new_ugbsk_nb = run_sql(query4)[0][0]
    if new_ugbsk_nb:
        print("Table usergroup_bskBASKET does not seem to be empty. Migration has already been done")
        return 0
    return 1

def __count_current_baskets():
    query = "SELECT count(*) FROM basket"
    return run_sql(query)[0][0]

def __check_basket_is_owned_by_only_one_user():
    """"""
    query = "SELECT id_basket, count(id_basket) FROM user_basket GROUP BY id_basket"
    res = run_sql(query)
    return filter(lambda x: x[1]>1, res)

def __check_every_basket_has_one_owner():
    """"""
    query = "SELECT bsk.id, ubsk.id_user FROM basket bsk LEFT JOIN user_basket ubsk ON bsk.id=ubsk.id_basket"
    res = run_sql(query)
    return filter(lambda x: x[1] is None, res)

def __check_baskets_exist():
    """"""
    query = "SELECT distinct ubsk.id_basket, bsk.id FROM user_basket ubsk LEFT JOIN basket bsk ON bsk.id=ubsk.id_basket"
    res = run_sql(query)
    return filter(lambda x: x[1] is None, res)


def __update_baskets(default_topic_name="Imported baskets",
                     default_share_level=cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM'],
                     drop_old_tables=0):
    """"""
    __import_baskets(default_topic_name, default_share_level)
    __import_records()
    __set_auto_increment_value()
    if drop_old_tables:
        __drop_baskets()

def __import_baskets(default_topic_name="Imported baskets",
                     default_share_level=cfg['CFG_WEBBASKET_SHARE_LEVELS']['READITM']):
    """"""
    query1 = """SELECT bsk.id,
                       bsk.name,
                       bsk.public,
                       ubsk.id_user,
                       DATE_FORMAT(ubsk.date_modification, '%Y-%m-%d %H:%i:%s')
                FROM basket bsk JOIN user_basket ubsk ON bsk.id=ubsk.id_basket"""
    baskets = run_sql(query1)
    if len(baskets):
        def basket_updater(basket):
            """"""
            (bskid, name, is_public, id_owner, date_modification) = basket
            try:
                int(bskid)
                int(id_owner)
            except:
                print("#####################")
                print("id basket:")
                print(bskid)
                print("id user")
                print(id_owner)
                print("#########################")

            return "(%i,'%s',%i,'%s')" % (int(bskid),
                                          real_escape_string(name),
                                          int(id_owner),
                                          real_escape_string(date_modification))
        values = reduce(lambda x, y: x + ',' + y, map(basket_updater, baskets))
        query2 = "INSERT INTO bskBASKET (id, name, id_owner, date_modification) VALUES %s"
        run_sql(query2 % values)
        def user_updater(basket):
            """"""
            (bskid, name, is_public, id_owner, date_modification) = basket
            return "(%i,%i,'%s')" % (int(bskid),
                                     int(id_owner),
                                     default_topic_name)
        values = reduce(lambda x, y: x + ',' + y, map(user_updater, baskets))
        query3 = "INSERT INTO user_bskBASKET (id_bskBASKET, id_user, topic) VALUES %s"
        run_sql(query3 % values)
        shared_baskets = filter(lambda x: x[2]!='n', baskets)
        def usergroup_updater(basket):
            """"""
            (bskid, name, is_public, id_owner, date_modification) = basket
            return "(0, %i,'%s','%s')" % (int(bskid),
                                          date_modification,
                                          default_share_level)
        values = reduce(lambda x, y: x + ',' + y, map(usergroup_updater, shared_baskets))
        query4 = "INSERT INTO usergroup_bskBASKET (id_usergroup, id_bskBASKET, date_shared, share_level) VALUES %s"
        if default_share_level:
            run_sql(query4 % values)
    return len(baskets)

def __count_records(bskid):
    query1 = "SELECT count(id_record) FROM basket_record WHERE id_basket=%i GROUP BY id_basket"
    return run_sql(query1 % int(bskid))[0][0]

def __import_records():
    """"""
    query1 = """SELECT bsk.id,
                       ubsk.id_user,
                       rec.id_record,
                       rec.nb_order,
                       DATE_FORMAT(ubsk.date_modification, '%Y-%m-%d %H:%i:%s')
                FROM basket bsk, user_basket ubsk, basket_record rec
                WHERE bsk.id=ubsk.id_basket AND bsk.id=rec.id_basket
                ORDER BY bsk.id"""
    records = run_sql(query1)
    def records_updater(record):
        (bskid, id_owner, id_record, order, date_modification) = record
        return "(%i,%i,%i,%i,'%s')" % (int(id_record), int(bskid), int(id_owner),
                                       int(order), real_escape_string(date_modification))

    query2 = """INSERT INTO bskREC (id_bibrec_or_bskEXTREC, id_bskBASKET,
                  id_user_who_added_item, score, date_added)
                VALUES %s"""
    iterator = 0
    while iterator < len(records):
        temp_val = reduce(lambda x, y: x + ',' + y, map(records_updater, records[iterator:iterator+10000]))
        run_sql(query2 % temp_val)
        if iterator + 10000 <= len(records):
            last_rec = iterator + 10000
        else:
            last_rec = len(records)
        print("  Inserting records %i-%i out of %i" % (iterator, last_rec, len(records)  ))
        iterator = iterator + 10000
    return len(records)

def __set_auto_increment_value():
    """"""
    query1 = "SELECT MAX(id) FROM basket"
    value = int(run_sql(query1)[0][0])
    query2 = "ALTER TABLE bskBASKET AUTO_INCREMENT=%i"
    run_sql(query2 % (value + 1))

def __drop_baskets():
    """"""
    query1 = "DROP TABLE basket"
    run_sql(query1)
    query2 = "DROP TABLE user_basket"
    run_sql(query2)
    query3 = "DROP TABLE basket_record"
    run_sql(query3)

if __name__ == '__main__':
    migrate_v071_baskets()
