## -*- mode: python; coding: utf-8; -*-
##
## $Id$
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

"""
Guest user sessions garbage collector.
"""

__revision__ = "$Id$"

import sys
try:
    from invenio.dbquery import run_sql
    from invenio.access_control_engine import acc_authorize_action
    from invenio.config import logdir, tmpdir
    import getopt
    import marshal
    import time
    import traceback
    import signal
    import re
    import getpass
    import os
except ImportError, e:
    print "Error: %s" % (e, )
    sys.exit(1)

# configure variables
CFG_MYSQL_ARGUMENTLIST_SIZE = 100
# After how many days to remove obsolete log/err files
CFG_MAX_ATIME_RM_LOG = 28
# After how many days to zip obsolete log/err files
CFG_MAX_ATIME_ZIP_LOG = 7
# After how many days to remove obsolete bibreformat fmt xml files
CFG_MAX_ATIME_RM_FMT = 28
# After how many days to zip obsolete bibreformat fmt xml files
CFG_MAX_ATIME_ZIP_FMT = 7
# After how many days to remove obsolete bibharvest fmt xml files
CFG_MAX_ATIME_RM_OAI = 28
# After how many days to zip obsolete bibharvest fmt xml files
CFG_MAX_ATIME_ZIP_OAI = 7

# will hold task options
options = {}

def gc_exec_command(command, verbose=1):
    """ Exec the command logging in appropriate way its output."""
    if verbose >= 9:
        write_message('  %s' % command)
    (dontcare, output, errors) = os.popen3(command)
    write_messages(errors.read())
    if verbose: write_messages(output.read())

def clean_filesystem(verbose=1):
    """ Clean the filesystem from obsolete files. """
    if verbose: write_message("""FILESYSTEM CLEANING STARTED""")
    if verbose: write_message("- deleting/gzipping bibsched empty/old err/log BibSched files")
    vstr = verbose > 1 and '-v' or ''
    gc_exec_command('find %s -name "bibsched_task_*" -size 0c -exec rm %s -f {} \;' \
            % (logdir, vstr), verbose)
    gc_exec_command('find %s -name "bibsched_task_*" -atime +%s -exec rm %s -f {} \;' \
            % (logdir, CFG_MAX_ATIME_RM_LOG, vstr), verbose)
    gc_exec_command('find %s -name "bibsched_task_*" -atime +%s -exec gzip %s -9 {} \;' \
            % (logdir, CFG_MAX_ATIME_ZIP_LOG, vstr), verbose)

    if verbose: write_message("- deleting/gzipping temporary empty/old BibReformat xml files")
    gc_exec_command('find %s -name "rec_fmt_*" -size 0c -exec rm %s -f {} \;' \
            % (tmpdir, vstr), verbose)
    gc_exec_command('find %s -name "rec_fmt_*" -atime +%s -exec rm %s -f {} \;' \
            % (tmpdir, CFG_MAX_ATIME_RM_FMT, vstr), verbose)
    gc_exec_command('find %s -name "rec_fmt_*" -atime +%s -exec gzip %s -9 {} \;' \
            % (tmpdir, CFG_MAX_ATIME_ZIP_FMT, vstr), verbose)

    if verbose: write_message("- deleting/gzipping temporary old BibHarvest xml files")
    gc_exec_command('find %s -name "bibharvestadmin.*" -exec rm %s -f {} \;' \
            % (tmpdir, vstr), verbose)
    gc_exec_command('find %s -name "bibconvertrun.*" -exec rm %s -f {} \;' \
            % (tmpdir, vstr), verbose)
    gc_exec_command('find %s -name "oaiharvest*" -atime +%s -exec gzip %s -9 {} \;' \
            % (tmpdir, CFG_MAX_ATIME_ZIP_OAI, vstr), verbose)
    gc_exec_command('find %s -name "oaiharvest*" -atime +%s -exec rm %s -f {} \;' \
            % (tmpdir, CFG_MAX_ATIME_RM_OAI, vstr), verbose)
    gc_exec_command('find %s -name "oai_archive*" -atime +%s -exec rm %s -f {} \;' \
            % (tmpdir, CFG_MAX_ATIME_RM_OAI, vstr), verbose)
    if verbose: write_message("""FILESYSTEM CLEANING FINISHED""")


def guest_user_garbage_collector(verbose=1):
    """Session Garbage Collector

    program flow/tasks:
    1: delete expired sessions
    1b:delete guest users without session
    2: delete queries not attached to any user
    3: delete baskets not attached to any user
    4: delete alerts not attached to any user

    verbose - level of program output.
              0 - nothing
              1 - default
              9 - max, debug"""

    # dictionary used to keep track of number of deleted entries
    delcount = {'session': 0,
                'user': 0,
                'user_query': 0,
                'query': 0,
                'bskBASKET': 0,
                'user_bskBASKET': 0,
                'bskREC': 0,
                'bskRECORDCOMMENT':0,
                'bskEXTREC':0,
                'bskEXTFMT':0,
                'user_query_basket': 0}

    if verbose: write_message("""GUEST USER SESSIONS GARBAGE COLLECTOR STARTED""")

    # 1 - DELETE EXPIRED SESSIONS
    if verbose: write_message("- deleting expired sessions")
    timelimit = time.time()
    if verbose >= 9: write_message("""  DELETE FROM session WHERE session_expiry < %d \n""" % (timelimit, ))
    delcount['session'] += run_sql("""DELETE FROM session WHERE session_expiry < %s """ % (timelimit, ))


    # 1b - DELETE GUEST USERS WITHOUT SESSION
    if verbose: write_message("- deleting guest users without session")

    # get uids
    if verbose >= 9: write_message("""  SELECT u.id\n  FROM user AS u LEFT JOIN session AS s\n  ON u.id = s.uid\n  WHERE s.uid IS NULL AND u.email = ''""")

    result = run_sql("""SELECT u.id
    FROM user AS u LEFT JOIN session AS s
    ON u.id = s.uid
    WHERE s.uid IS NULL AND u.email = ''""")
    if verbose >= 9: write_message(result)

    if result:
        # work on slices of result list in case of big result
        for i in range(0, len(result), CFG_MYSQL_ARGUMENTLIST_SIZE):
            # create string of uids
            uidstr = ''
            for (id_user, ) in result[i:i+CFG_MYSQL_ARGUMENTLIST_SIZE]:
                if uidstr: uidstr += ','
                uidstr += "%s" % (id_user, )

            # delete users
            if verbose >= 9: write_message("""  DELETE FROM user WHERE id IN (TRAVERSE LAST RESULT) AND email = '' \n""")
            delcount['user'] += run_sql("""DELETE FROM user WHERE id IN (%s) AND email = ''""" % (uidstr, ))


    # 2 - DELETE QUERIES NOT ATTACHED TO ANY USER

    # first step, delete from user_query
    if verbose: write_message("- deleting user_queries referencing non-existent users")

    # find user_queries referencing non-existent users
    if verbose >= 9: write_message("""  SELECT DISTINCT uq.id_user\n  FROM user_query AS uq LEFT JOIN user AS u\n  ON uq.id_user = u.id\n  WHERE u.id IS NULL""")
    result = run_sql("""SELECT DISTINCT uq.id_user
    FROM user_query AS uq LEFT JOIN user AS u
    ON uq.id_user = u.id
    WHERE u.id IS NULL""")
    if verbose >= 9: write_message(result)


    # delete in user_query one by one
    if verbose >= 9: write_message("""  DELETE FROM user_query WHERE id_user = 'TRAVERSE LAST RESULT' \n""")
    for (id_user, ) in result:
        delcount['user_query'] += run_sql("""DELETE FROM user_query WHERE id_user = %s""" % (id_user, ))

    # delete the actual queries
    if verbose: write_message("- deleting queries not attached to any user")

    # select queries that must be deleted
    if verbose >= 9: write_message("""  SELECT DISTINCT q.id\n  FROM query AS q LEFT JOIN user_query AS uq\n  ON uq.id_query = q.id\n  WHERE uq.id_query IS NULL AND\n  q.type <> 'p' """)
    result = run_sql("""SELECT DISTINCT q.id
                        FROM query AS q LEFT JOIN user_query AS uq
                        ON uq.id_query = q.id
                        WHERE uq.id_query IS NULL AND
                              q.type <> 'p'""")
    if verbose >= 9: write_message(result)

    # delete queries one by one
    if verbose >= 9: write_message("""  DELETE FROM query WHERE id = 'TRAVERSE LAST RESULT \n""")
    for (id_user, ) in result:
        delcount['query'] += run_sql("""DELETE FROM query WHERE id = %s""" % (id_user, ))


    # 3 - DELETE BASKETS NOT OWNED BY ANY USER
    if verbose: write_message("- deleting baskets not owned by any user")

    # select basket ids
    if verbose >= 9: write_message(""" SELECT ub.id_bskBASKET\n  FROM user_bskBASKET AS ub LEFT JOIN user AS u\n  ON u.id = ub.id_user\n  WHERE u.id IS NULL""")
    try:
        result = run_sql("""SELECT ub.id_bskBASKET
                              FROM user_bskBASKET AS ub LEFT JOIN user AS u
                                ON u.id = ub.id_user
                             WHERE u.id IS NULL""")
    except:
        result = []
    if verbose >= 9: write_message(result)

    # delete from user_basket and basket one by one
    if verbose >= 9:
        write_message("""  DELETE FROM user_bskBASKET WHERE id_bskBASKET = 'TRAVERSE LAST RESULT' """)
        write_message("""  DELETE FROM bskBASKET WHERE id = 'TRAVERSE LAST RESULT' """)
        write_message("""  DELETE FROM bskREC WHERE id_bskBASKET = 'TRAVERSE LAST RESULT'""")
        write_message("""  DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET = 'TRAVERSE LAST RESULT' \n""")
    for (id_basket, ) in result:
        delcount['user_bskBASKET'] += run_sql("""DELETE FROM user_bskBASKET WHERE id_bskBASKET = %s""" % (id_basket, ))
        delcount['bskBASKET'] += run_sql("""DELETE FROM bskBASKET WHERE id = %s""" % (id_basket, ))
        delcount['bskREC'] += run_sql("""DELETE FROM bskREC WHERE id_bskBASKET = %s""" % (id_basket, ))
        delcount['bskRECORDCOMMENT'] += run_sql("""DELETE FROM bskRECORDCOMMENT WHERE id_bskBASKET = %s""" % (id_basket, ))
    if verbose >= 9: write_message(""" SELECT DISTINCT ext.id, rec.id_bibrec_or_bskEXTREC FROM bskEXTREC AS ext \nLEFT JOIN bskREC AS rec ON ext.id=-rec.id_bibrec_or_bskEXTREC WHERE id_bibrec_or_bskEXTREC is NULL""")
    try:
        result = run_sql("""SELECT DISTINCT ext.id FROM bskEXTREC AS ext
                            LEFT JOIN bskREC AS rec ON ext.id=-rec.id_bibrec_or_bskEXTREC
                            WHERE id_bibrec_or_bskEXTREC is NULL""")
    except:
        result = []
    if verbose >= 9:
        write_message(result)
        write_message("""  DELETE FROM bskEXTREC WHERE id = 'TRAVERSE LAST RESULT' """)
        write_message("""  DELETE FROM bskEXTFMT WHERE id_bskEXTREC = 'TRAVERSE LAST RESULT' \n""")
    for (id_basket, ) in result:
        delcount['bskEXTREC'] += run_sql("""DELETE FROM bskEXTREC WHERE id=%s""" % (id_basket,))
        delcount['bskEXTFMT'] += run_sql("""DELETE FROM bskEXTFMT WHERE id_bskEXTREC=%s""" % (id_basket,))

    # 4 - DELETE ALERTS NOT OWNED BY ANY USER
    if verbose: write_message('- deleting alerts not owned by any user')

    # select user ids in uqb that reference non-existent users
    if verbose >= 9: write_message("""SELECT DISTINCT uqb.id_user FROM user_query_basket AS uqb LEFT JOIN user AS u ON uqb.id_user = u.id WHERE u.id IS NULL""")
    result = run_sql("""SELECT DISTINCT uqb.id_user FROM user_query_basket AS uqb LEFT JOIN user AS u ON uqb.id_user = u.id WHERE u.id IS NULL""")
    if verbose >= 9: write_message(result)

    # delete all these entries
    for (id_user, ) in result:
        if verbose >= 9: write_message("""DELETE FROM user_query_basket WHERE id_user = 'TRAVERSE LAST RESULT """)
        delcount['user_query_basket'] += run_sql("""DELETE FROM user_query_basket WHERE id_user = %s """ % (id_user, ))


    # print STATISTICS

    if verbose:
        write_message("""STATISTICS - DELETED DATA: """)
        write_message("""- %7s sessions.""" % (delcount['session'], ))
        write_message("""- %7s users.""" % (delcount['user'], ))
        write_message("""- %7s user_queries.""" % (delcount['user_query'], ))
        write_message("""- %7s queries.""" % (delcount['query'], ))
        write_message("""- %7s baskets.""" % (delcount['bskBASKET'], ))
        write_message("""- %7s user_baskets.""" % (delcount['user_bskBASKET'], ))
        write_message("""- %7s basket_records.""" % (delcount['bskREC'], ))
        write_message("""- %7s basket_external_records.""" % (delcount['bskEXTREC'], ))
        write_message("""- %7s basket_external_formats.""" % (delcount['bskEXTFMT'], ))
        write_message("""- %7s basket_comments.""" % (delcount['bskRECORDCOMMENT'], ))
        write_message("""- %7s user_query_baskets.""" % (delcount['user_query_basket'], ))
        write_message("""GUEST USER SESSIONS GARBAGE COLLECTOR FINISHED""")

    return


def test_insertdata():
    """insert testdata for the garbage collector.
    something will be deleted, other data kept.
    test_checkdata() checks if the remains are correct."""

    test_deletedata_nooutput()

    print 'insert into session 6'
    for (key, uid) in [('23A', 2000), ('24B', 2100), ('25C', 2200), ('26D', 2300)]:
        run_sql("""INSERT INTO session (session_key, session_expiry, uid) values ('%s', %d, %s) """ % (key, time.time(), uid))
    for (key, uid) in [('27E', 2400), ('28F', 2500)]:
        run_sql("""INSERT INTO session (session_key, session_expiry, uid) values ('%s', %d, %s) """ % (key, time.time()+20000, uid))

    print 'insert into user 6'
    for id in range(2000, 2600, 100):
        run_sql("""INSERT INTO user (id, email) values (%s, '') """ % (id, ))

    print 'insert into user_query 6'
    for (id_user, id_query) in [(2000, 155), (2100, 231), (2200, 155), (2300, 574), (2400, 155), (2500, 988)]:
        run_sql("""INSERT INTO user_query (id_user, id_query) values (%s, %s) """ % (id_user, id_query))

    print 'insert into query 4'
    for (id, urlargs) in [(155, 'p=cern'), (231, 'p=muon'), (574, 'p=physics'), (988, 'cc=Atlantis+Institute+of+Science&as=0&p=')]:
        run_sql("""INSERT INTO query (id, type, urlargs) values (%s, 'r', '%s') """ % (id, urlargs))

    print 'insert into basket 4'
    for (id, name) in [(6, 'general'), (7, 'physics'), (8, 'cern'), (9, 'diverse')]:
        run_sql("""INSERT INTO basket (id, name, public) values (%s, '%s', 'n')""" % (id, name))

    print 'insert into user_basket 4'
    for (id_user, id_basket) in [(2000, 6), (2200, 7), (2200, 8), (2500, 9)]:
        run_sql("""INSERT INTO user_basket (id_user, id_basket) values (%s, %s) """ % (id_user, id_basket))

    print 'insert into user_query_basket 2'
    for (id_user, id_query, id_basket) in [(2200, 155, 6), (2500, 988, 9)]:
        run_sql("""INSERT INTO user_query_basket (id_user, id_query, id_basket) values (%s, %s, %s) """ % (id_user, id_query, id_basket))

def test_deletedata():
    """deletes all the testdata inserted in the insert function.
    outputs how many entries are deleted"""

    print 'delete from session',
    print run_sql("DELETE FROM session WHERE uid IN (2000,2100,2200,2300,2400,2500) ")
    print 'delete from user',
    print run_sql("DELETE FROM user WHERE id IN (2000,2100,2200,2300,2400,2500) ")
    print 'delete from user_query',
    print run_sql("DELETE FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) OR id_query IN (155,231,574,988) ")
    print 'delete from query',
    print run_sql("DELETE FROM query WHERE id IN (155,231,574,988) ")
    print 'delete from basket',
    print run_sql("DELETE FROM basket WHERE id IN (6,7,8,9) ")
    print 'delete from user_basket',
    print run_sql("DELETE FROM user_basket WHERE id_basket IN (6,7,8,9) OR id_user IN (2000, 2200, 2500) ")
    print 'delete from user_query_basket',
    print run_sql("DELETE FROM user_query_basket WHERE id_user IN (2200, 2500) ")


def test_deletedata_nooutput():
    """same as test_deletedata without output."""

    run_sql("DELETE FROM session WHERE uid IN (2000,2100,2200,2300,2400,2500) ")
    run_sql("DELETE FROM user WHERE id IN (2000,2100,2200,2300,2400,2500) ")
    run_sql("DELETE FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) OR id_query IN (155,231,574,988) ")
    run_sql("DELETE FROM query WHERE id IN (155,231,574,988) ")
    run_sql("DELETE FROM basket WHERE id IN (6,7,8,9) ")
    run_sql("DELETE FROM user_basket WHERE id_basket IN (6,7,8,9) OR id_user IN (2000, 2200, 2500) ")
    run_sql("DELETE FROM user_query_basket WHERE id_user IN (2200, 2500) ")


def test_showdata():
    print '\nshow test data:'

    print '\n- select * from session:'
    for r in run_sql("SELECT * FROM session WHERE session_key IN ('23A','24B','25C','26D','27E','28F') "): print r

    print '\n- select * from user:'
    for r in run_sql("SELECT * FROM user WHERE email = '' AND id IN (2000,2100,2200,2300,2400,2500) "): print r

    print '\n- select * from user_query:'
    for r in run_sql("SELECT * FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) "): print r

    print '\n- select * from query:'
    for r in run_sql("SELECT * FROM query  WHERE id IN (155,231,574,988) "): print r

    print '\n- select * from basket:'
    for r in run_sql("SELECT * FROM basket WHERE id IN (6,7,8,9) "): print r

    print '\n- select * from user_basket:'
    for r in run_sql("SELECT * FROM user_basket WHERE id_basket IN (6,7,8,9)"): print r

    print '\n- select * from user_query_basket:'
    for r in run_sql("SELECT * FROM user_query_basket WHERE id_basket IN (6,7,8,9) "): print r


def test_checkdata():
    """checks wether the data in the database is correct after
    the garbage collector has run.
    test_insertdata must have been run followed by the gc for this to be true."""

    result = run_sql("SELECT DISTINCT session_key FROM session WHERE session_key IN ('23A','24B','25C','26D','27E','28F') ")
    if len(result) != 2: return 0
    for r in [('27E', ), ('28F', )]:
        if r not in result: return 0

    result = run_sql("SELECT id FROM user WHERE email = '' AND id IN (2000,2100,2200,2300,2400,2500) ")
    if len(result) != 2: return 0
    for r in [(2400, ), (2500, )]:
        if r not in result: return 0

    result = run_sql("SELECT DISTINCT id_user FROM user_query WHERE id_user IN (2000,2100,2200,2300,2400,2500) ")
    if len(result) != 2: return 0
    for r in [(2400, ), (2500, )]:
        if r not in result: return 0

    result = run_sql("SELECT id FROM query  WHERE id IN (155,231,574,988) ")
    if len(result) != 2: return 0
    for r in [(155, ), (988, )]:
        if r not in result: return 0

    result = run_sql("SELECT id FROM basket WHERE id IN (6,7,8,9) ")
    if len(result) != 1: return 0
    for r in [(9, )]:
        if r not in result: return 0

    result = run_sql("SELECT id_user, id_basket FROM user_basket WHERE id_basket IN (6,7,8,9)")
    if len(result) != 1: return 0
    for r in [(2500, 9)]:
        if r not in result: return 0

    result = run_sql("SELECT id_user, id_query, id_basket FROM user_query_basket WHERE id_basket IN (6,7,8,9) ")
    if len(result) != 1: return 0
    for r in [(2500, 988, 9)]:
        if r not in result: return 0

    return 1

def test_runtest_guest_user_garbage_collector():
    """a test to see if the garbage collector works correctly."""

    test_insertdata()
    test_showdata()
    guest_user_garbage_collector(verbose=9)
    test_showdata()
    if test_checkdata():
        print '\n\nGARBAGE COLLECTOR CLEANED UP THE CORRECT DATA \n\n'
    else:
        print '\n\nERROR ERROR ERROR - WRONG DATA CLEANED - ERROR ERROR ERROR \n\n'
    test_deletedata_nooutput()
    return

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = shift_re.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        date = time.localtime(date + sign * factor * value)
        date = time.strftime(format_string, date)
    else:
        date = time.strptime(var, format_string)
        date = time.strftime(format_string, date)
    return date

def get_current_time_timestamp():
    """Return timestamp corresponding to the current time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_sleep(), got signal %s frame %s" % (sig, frame))
    write_message("sleeping...")
    task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal

def task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_wakeup(), got signal %s frame %s" % (sig, frame))
    write_message("continuing...")
    task_update_status("CONTINUING")

def task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_stop(), got signal %s frame %s" % (sig, frame))
    write_message("stopping...")
    task_update_status("STOPPING")
    task_update_status("STOPPED")
    sys.exit(0)

def task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_suicide(), got signal %s frame %s" % (sig, frame))
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    task_update_status("SUICIDED")
    sys.exit(0)

def task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame))

def write_message(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).  Useful for debugging stuff."""
    if msg:
        if stream == sys.stdout or stream == sys.stderr:
            stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
            try:
                stream.write("%s\n" % msg)
            except UnicodeEncodeError:
                stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
            stream.flush()
        else:
            sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)

def write_messages(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).  Useful for debugging stuff."""
    for message in msg.split('\n'):
        write_message(message, stream)

def authenticate(user, header="SessionGC Guest User Garbage Collector Task Submission", action="runsessiongc"):
    """Authenticate the user against the user database.
       Check for its password, if it exists.
       Check for action access rights.
       Return user name upon authorization success,
       do system exit upon authorization failure.
       """
    print header
    print "=" * len(header)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        user = sys.stdin.readline().lower().strip()
    else:
        print >> sys.stdout, "\rUsername:", user
    ## first check user pw:
    res = run_sql("select id,password from user where email=%s", (user,), 1) + \
          run_sql("select id,password from user where nickname=%s", (user,), 1)
    if not res:
        print "Sorry, %s does not exist." % user
        sys.exit(1)
    else:
        (uid_db, password_db) = res[0]
        if password_db:
            password_entered = getpass.getpass()
            if password_db == password_entered:
                pass
            else:
                print "Sorry, wrong credentials for %s." % user
                sys.exit(1)
        ## secondly check authorization for the action:
        (auth_code, auth_message) = acc_authorize_action(uid_db, action)
        if auth_code != 0:
            print auth_message
            sys.exit(1)
    return user

def task_submit():
    """Submits task to the BibSched task queue.  This is what people will be invoking via command line."""
    global options
    ## sanity check: remove eventual "task" option:
    if options.has_key("task"):
        del options["task"]
    ## authenticate user:
    user = authenticate(options.get("user", ""))
    ## submit task:
    if options["verbose"] >= 9:
        print ""
        write_message("storing task options %s\n" % options)
    task_id = run_sql("""INSERT INTO schTASK (id,proc,user,runtime,sleeptime,status,arguments)
                         VALUES (NULL,'sessiongc',%s,%s,%s,'WAITING',%s)""",
                      (user, options["runtime"], options["sleeptime"], marshal.dumps(options)))
    ## update task number:
    options["task"] = task_id
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(options), task_id))
    write_message("Task #%d submitted." % task_id)
    return task_id

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    global options
    return run_sql("UPDATE schTASK SET progress=%s where id=%s", (msg, options["task"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    global options
    return run_sql("UPDATE schTASK SET status=%s where id=%s", (val, options["task"]))

def task_read_status(task_id):
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s", (task_id,), 1)
    try:
        out = res[0][0]
    except:
        out = 'UNKNOWN'
    return out

def task_get_options(id):
    """Returns options for the task 'id' read from the BibSched task queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc='sessiongc'", (id,))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: SessionGC task %d does not seem to exist." % id)
        sys.exit(1)
    return out

def task_run(task_id):
    """Run the sessiongc task by fetching arguments from the BibSched task queue.
       This is what BibSched will be invoking via daemon call.
       The task will update collection reclist cache and collection web pages for
       given collection. (default is all).
       Arguments described in usage() function.
       Return 1 in case of success and 0 in case of failure."""
    global options
    task_run_start_timestamp = get_current_time_timestamp()
    options = task_get_options(task_id) # get options from BibSched task table
    ## check task id:
    if not options.has_key("task"):
        write_message("Error: The task #%d does not seem to be a SessionGC task." % task_id)
        return 0
    ## check task status:
    task_status = task_read_status(task_id)
    if task_status != "WAITING":
        write_message("Error: The task #%d is %s.  I expected WAITING." % (task_id, task_status))
        return 0
    ## we can run the task now:
    if options["verbose"]:
        write_message("Task #%d started." % task_id)
    task_update_status("RUNNING")
    ## initialize signal handler:
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)
    # Running the garbace collector
    guest_user_garbage_collector(options["verbose"])
    if options["filesystem"]:
        clean_filesystem(options["verbose"])
    # We are done!
    task_update_progress("Done.")
    task_update_status("DONE")
    if options["verbose"]:
        write_message("Task #%d finished." % task_id)
    return 1

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    sys.stderr.write("Scheduling options:\n")
    sys.stderr.write("  -u, --user=USER \t User name to submit the task as, password needed.\n")
    sys.stderr.write("  -t, --runtime=TIME \t Time to execute the task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26\n")
    sys.stderr.write("  -s, --sleeptime=SLEEP \t Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.stderr.write("  -v, --verbose=LEVEL   \t Verbose level (from 0 to 9, default 1).\n")
    sys.stderr.write("  -f, --filesystem\t\t Clean up the filesystem.\n")
    sys.stderr.write("""Description: %s garbage collects all the guests users sessions\n""" % sys.argv[0])
    sys.exit(exitcode)

def main():
    """CLI to the session garbage collector."""

    ## parse command line:
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        ## A - run the task
        task_id = int(sys.argv[1])
        try:
            if not task_run(task_id):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except StandardError, e:
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")
    else:
        ## B - submit the task
        # set default values:
        options["runtime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        options["verbose"] = 1
        options["filesystem"] = False
        options["sleeptime"] = ""
        # set user-defined options:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hVv:u:s:t:f",
                                       ["help", "version", "verbose=", "user=",
                                        "sleeptime=", "runtime=", "filesystem"])
        except getopt.GetoptError, err:
            usage(1, err)
        try:
            for opt in opts:
                if opt[0] in ["-h", "--help"]:
                    usage(0)
                elif opt[0] in ["-V", "--version"]:
                    print __revision__
                    sys.exit(0)
                elif opt[0] in ["-u", "--user"]:
                    options["user"] = opt[1]
                elif opt[0] in ["-v", "--verbose"]:
                    options["verbose"] = int(opt[1])
                elif opt[0] in ["-s", "--sleeptime"]:
                    get_datetime(opt[1]) # see if it is a valid shift
                    options["sleeptime"] = opt[1]
                elif opt[0] in ["-t", "--runtime"]:
                    options["runtime"] = get_datetime(opt[1])
                elif opt[0] in ["-f", "--filesystem"]:
                    options["filesystem"] = True
                else:
                    usage(1)
        except StandardError, e:
            usage(e)
        task_submit()
    return

if __name__ == '__main__':
    main()
