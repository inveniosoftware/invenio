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

"""Allocate an ALEPH system number (SYS) for a record."""

__revision__ = "$Id$"

import os.path
from random import randint, seed
from os import getpid, unlink, access, rename, R_OK, W_OK
from os.path import getmtime
from shutil import copyfile
from time import strftime, localtime, mktime, sleep
import time

from invenio.config import \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_NAME, \
     CFG_WEBSUBMIT_COUNTERSDIR, \
     CFG_SITE_SUPPORT_EMAIL
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError
from invenio.ext.email import send_email

CFG_WARNING_MAX_SYS_APPROACHING = 2000
CFG_MAX_AGE_LOCKFILE = 300 ## (300 seconds is the maximum age that we allow for a lockfile)
CFG_LEGAL_ALEPH_DATABASES = ["CER", "IEX", "MAN", "MMD"]

def Allocate_ALEPH_SYS(parameters, curdir, form, user_info=None):
    """
       Get the next available ALEPH SYS from the counter file, and allocate it as the
       SYS for this record. Increment the counterby one.
       ALEPH SYS allocation works in "slots" of free numbers. For example,
       000425201 -> 000634452 for a given database may be available.
       This means that it is necessary to care about not over-stepping the maximum
       boundary. To this end, two counters (for each ALEPH Database) must be present:
          - last_SYS_<DATABASE>      (this contains the last SYS allocated for
            a database)
          - maximum_SYS_<DATABASE>   (this contains the MAXIMUM SYS allowed for a
            database)
       So, for example, for the CER database, there would be:
          - last_SYS_CER
          - maximum_SYS_CER
       When the maximum SYS has been reached, all further attempts to obtain ALEPH SYSs
       will fail, as this function will fail with an error.  To prevent this from coming
       as a surprise, however, when "last_SYS_<DATABASE>" gets somewhere near to the value
       stored in "maximum_SYS_<DATABASE>", a mail will be sent to the Admin with every
       SYS allocated, warning them that only N numbers remain free for the XY database.
       The number until MAX SYS which determines this period of warning emails is
       determined by a variable "warn_admin_at_N_sys_remaining".  It is set to 2000 by
       default, but can be changed.
       When the system allocates a new sys and there are 2000 or less free SYS remaining,
       the warning mails to ADMIN will be sent.

       @param alephdatabase: (string) the name of the ALEPH database for which a SYS is to be
        allocated.  E.g. "CER".  The he absence of this will cause the function to fail.
        Also, the absence of either of the 2 counter files "last_SYS_${database}" and
        "maximum_SYS_${database}" will cause the function to fail.
    """
    mailfrom_addr = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)
    database = parameters['alephdatabase'].strip()
    counter_lastsys = "last_SYS_%s" % database
    counter_maxsys = "maximum_SYS_%s" % database

    ## ensure that "database" param is not empty, and exists in the list of legal DBs
    if database == "" or database not in CFG_LEGAL_ALEPH_DATABASES:
        ## error with supplied database
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, an invalid database name was"""\
              """ supplied: [%s]. It was therefore not possible to allocate the SYS.""" % database
        raise InvenioWebSubmitFunctionError(msg)

    ## before trying to make a lockfile, test if one exists and whether it is older than "CFG_MAX_AGE_LOCKFILE" seconds
    ## if so, raise an error and warn the admin:
    counter_lockfile = "last_SYS_%s.lock" % database
    try:
        lockfile_modtime = getmtime("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lockfile))
        time_now = mktime(localtime())
        time_since_last_lockfile_mod = time_now - lockfile_modtime
        if time_since_last_lockfile_mod > CFG_MAX_AGE_LOCKFILE:
            ## lockfile is old - warn admin and stop
            admin_msg = """ERROR: When trying to allocate an ALEPH SYS for a record in the [%s] DB, it was not possible """\
                        """to create a lockfile. An attempt was made at [%s], but a lockfile already existed with a """\
                        """last modification time of [%s]. It was therefore not possible to allocate the SYS.""" \
                        % (database, strftime("%d/%m/%Y %H:%M:%S", localtime(time_now)),
                           strftime("%d/%m/%Y %H:%M:%S", localtime(lockfile_modtime)))
            send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - OLD ALEPH SYS LOCKFILE ENCOUNTERED!", content=admin_msg)
            user_msg = """ERROR: When trying to allocate an ALEPH SYS for a record in the [%s] DB, it was not possible""" \
                       """ to create a lockfile. It was therefore not possible to allocate the SYS.""" \
                       % database
            raise InvenioWebSubmitFunctionError(user_msg)
    except OSError:
        ## no lockfile
        pass

    ## before any counter operations, create a lockfile:
    got_lock = _create_SYS_counter_lockfile(database)

    if got_lock == 0:
        ## unable to create lockfile!
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record in the [%s] DB, it was not possible"""\
              """ to create a lockfile within 60 seconds. It was therefore not possible to allocate the SYS.""" % database
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT CREATE LOCKFILE!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)

    ## test that counter files exist for "database":
    rw_count_lastsys_ok = access("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys), R_OK|W_OK)
    rw_count_maxsys_ok = access("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_maxsys), R_OK|W_OK)

    if not rw_count_lastsys_ok or not rw_count_maxsys_ok:
        ## cannot access the ALEPH counter files - critical error
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, either [%s] or [%s] (or both) was not"""\
              """ accessible. It was therefore not possible to allocate the SYS.""" % (counter_lastsys, counter_maxsys)
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT ACCESS ALEPH SYS COUNTER(S)!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)


    ## read last-sys and max-sys:
    try:
        fp = open("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys), "r")
        fileval_lastsys = fp.read()
        fp.close()
        fp = open("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_maxsys), "r")
        fileval_maxsys = fp.read()
        fp.close()
    except IOError:
        ## could not read one or both of the files
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, either [%s] or [%s] (or both) could not"""\
              """ be read. It was therefore not possible to allocate the SYS.""" % (counter_lastsys, counter_maxsys)
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT ACCESS ALEPH SYS COUNTER(S)!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)


    ## for the values from both files, clean any whitespace from beginning or end of file text and cast the result to an integer:
    try:
        lastsys = int(fileval_lastsys.strip())
        maxsys = int(fileval_maxsys.strip())
    except ValueError:
        ## the value in one or both of the files did not cast to an int!
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, either [%s] or [%s] (or both) contained invalid"""\
              """ (non-integer) values. It was therefore not possible to allocate the SYS.""" % (counter_lastsys, counter_maxsys)
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - ALEPH SYS COUNTER(S) CONTAINS INVALID DATA!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)


    ## check that "fileval_lastsys" is less than "fileval_maxsys". If yes, proceed - else fail and mail ADMIN
    if not (lastsys < maxsys):
        ## MAX SYS EXCEEDED
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, the value of [%s -> %d] is not less than the """\
              """value of [%s -> %d]. It was therefore not possible to allocate the SYS. A new SYS range must be allocated!"""\
              % (counter_lastsys, lastsys, counter_maxsys, maxsys)
        ## mail admin:
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - MAXIMUM ALEPH SYS COUNTER VALUE EXCEEDED!", content=msg)
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        raise InvenioWebSubmitFunctionError(msg)


    if maxsys - lastsys < CFG_WARNING_MAX_SYS_APPROACHING:
        ## WARN admin that MAX ALEPH SYS for this DB is approaching:
        _warn_admin_counterlimit_approaching(db=database, lastsys=lastsys, maxsys=maxsys)


    ## increment the value of the last SYS
    lastsys += 1

    ## cast sys to a string and pad the value on the left with leading zeros to 9 characters:
    cursys = "%09d%s" % (lastsys, database[0:3].upper().strip())

    ## now write out the new value of lastsys to the relevant counter file:
    ## make temporary file then move it later
    tmpfname = "%s_%s_%s" % (counter_lastsys, strftime("%Y%m%d%H%M%S", localtime()), getpid())

    ## open temp counter file for writing:
    try:
        fp = open("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, tmpfname), "w")
        fp.write("%d" % (lastsys,))
        fp.flush()
        fp.close()
    except IOError:
        ## could not write to temp file
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, could not write out new value for last SYS used """\
              """to a temporary file [%s]. It was therefore not possible to allocate a SYS for the record ([%s] was not """\
              """incremented.)""" % ("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, tmpfname), counter_lastsys)
        ## remove the "lock file"
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT CREATE TEMPORARY ALEPH SYS COUNTER FILE!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)

    ## copy old counter file to backup version:
    try:
        copyfile("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys), "%s/%s.bk" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys))
    except IOError:
        ## unable to make backup of counter file:
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, could not write out new value for last SYS used."""\
              """ Couldn't make a back-up copy of the SYS counter file [%s].""" % ("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys),)
        ## remove the "lock file"
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT WRITE BACK-UP ALEPH SYS COUNTER!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)

    ## rename temp counter file to final counter file:
    try:
        rename("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, tmpfname), "%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys))
    except OSError:
        ## couldnt rename the tmp file to final file name
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, could not write out new value for last SYS used."""\
              """ Created the temporary last SYS counter file [%s], but couldn't then rename it to the final counter file [%s]."""\
              """ It was therefore not possible to allocate a SYS for the record ([%s] was not incremented.)"""\
              % ("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, tmpfname), "%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lastsys), counter_lastsys)
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT WRITE ALEPH SYS COUNTER FILE!", content=msg)
        raise InvenioWebSubmitFunctionError(msg)


    ## now that counter has been successfully incremented, write cursys out to the file "SNa500":
    try:
        fp = open("%s/SNa500" % curdir, "w")
        fp.write("%s" % cursys)
        fp.flush()
        fp.close()
    except IOError:
        ## unable to write out the SYS!
        msg = """ERROR: When trying to allocate an ALEPH SYS for a record, could not write out new SYS to file [%s/SNa500]."""\
              """ It was therefore not possible to allocate the SYS ([%s] was not incremented.)"""\
              % (curdir, counter_lastsys)
        lockfile_removed = _unlink_SYS_counter_lockfile(database)
        if lockfile_removed == 0:
            ## couldn't remove lockfile - mail ADMIN
            _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        raise InvenioWebSubmitFunctionError(msg)

    ## finally, unlink the lock file:
    lockfile_removed = _unlink_SYS_counter_lockfile(database)
    if lockfile_removed == 0:
        ## couldn't remove lockfile - mail ADMIN
        msg = """ERROR: After allocating an ALEPH SYS for a record, it was not possible to remove the lock file [last_SYS_%s.lock] after the """\
              """SYS was allocated.""" % ("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, database),)
        _mail_admin_because_lockfile_not_removeable(lockfilename="last_SYS_%s" % database, extramsg="\n\n"+msg)
        raise InvenioWebSubmitFunctionError(msg)

    return ""


def _warn_admin_counterlimit_approaching(db, lastsys, maxsys):
    mailfrom_addr = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)
    mailtxt = """WARNING: The maxmimum ALEPH SYS value for the [%s] database is approaching!\n"""\
              """The last SYS allocated was [%d]; The maximum SYS allowed is [%d].\n\n"""\
              """You should be thinking about allocating a new range of SYS now!\n"""\
              % (db, lastsys, maxsys)
    send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit WARNING - MAXIMUM SYS IN [%s] APPROACHING!" % db,
                           content=mailtxt)


def _mail_admin_because_lockfile_not_removeable(lockfilename, extramsg=""):
    mailfrom_addr = '%s Submission Engine <%s>' % (CFG_SITE_NAME, CFG_SITE_SUPPORT_EMAIL)
    mailtxt = """ERROR: When trying to allocate an ALEPH SYS for a record, it was not possible to remove the lockfile [%s]!"""\
              """ This means that all attempted new submissions to that database will be blocked and fail, as it is not"""\
              """ possible to allocate them a SYS in ALEPH. Please investigate and remove the lockfile ASAP.\n\n"""\
              % (lockfilename,)
    mailtxt += extramsg
    send_email(fromaddr=mailfrom_addr, toaddr=CFG_SITE_ADMIN_EMAIL, subject="WebSubmit ERROR - CANNOT REMOVE ALEPH SYS LOCKFILE!", content=mailtxt)


def _create_SYS_counter_lockfile(database):
    """Write a lock-file for "last_SYS_%(database)s" to the "CFG_WEBSUBMIT_COUNTERSDIR" directory, thus ensuring that only one process will
       access the counter at any one time.
       If the lockfile doesn't already exist, it will be created in the CFG_WEBSUBMIT_COUNTERSDIR directory with the name
       "last_SYS_%(database)s.lock" (e.g. "last_SYS_CER.lock".)  If the lockfile does exist, the process will sleep for 1 second
       and then try again.  In all, it will try 60 times to create a lockfile before giving up.
       When a lockfile is created, it will contain a string of the format "processPID->YYYYMMDDhhmmss->random int, between 1-1000000"
       (E.g. something like this: "856->20060705120533->324".)
       When the lockfile has been written, it will be re-read and the string inside of it compared with the string that was written.
       If they match, then it shall be assumed that this is the lockfile owned by this process. If they do not match, then it shall
       be assumed that at the time of lockfile creation, another process also created its own lockfile, and this one belongs to the
       other process. In such a case, this process will sleep for one second and then try again.
       @param database: (string) the name of the database whose counter file has been locked. This
        is used to determine the name of the lockfile.
       @return: (integer) an error flag - 0 (ZERO) or 1 (ONE). 0 means lockfile could not be created;
        1 means that it was successfully created.
    """
    seed()
    counter_lockfile = "last_SYS_%s.lock" % database
    lockfile_text = """%s->%.7f->%d""" % (getpid(), time.time(), randint(0,1000000))
    got_lock = 0

    ## get lock on counter:
    for i in range(0, 60):
        if os.path.exists("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lockfile)):
            ## lock file exists - sleep 1 second and try again
            sleep(1)
            continue
        else:
            ## lock file doesn't exist - make it
            try:
                fp = open("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lockfile), "w")
                fp.write("%s" % (lockfile_text,))
                fp.flush()
                fp.close()
                ## open and read the contents of the lock file back to ensure that it *really* belongs to this process:
                fp = open("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lockfile), "r")
                read_lockfile_contents = fp.readline()
                fp.close()
                if read_lockfile_contents.strip() != lockfile_text:
                    ## this is not our lockfile, or it has been corrupted
                    ## probably another process has written its own lockfile in the mean time
                    sleep(1)
                    continue
                else:
                    got_lock = 1
                    break
            except IOError:
                ## could not create - pass and go on to next iteration
                got_lock = 0
                sleep(1)
    return got_lock

def _unlink_SYS_counter_lockfile(database):
    """Remove the lockfile that was created for this session of SYS allocation.
       @param database: (string) the name of the database whose counter file has been locked. This
        is used to determine the name of the lockfile.
       @return: (integer) an error flag - 0 (ZERO) or 1 (ONE). 0 means lockfile could not be removed;
        1 means that it was successfully removed.
    """
    counter_lockfile = "last_SYS_%s.lock" % (database,)
    unlinked_lockfile = 0
    try:
        unlink("%s/%s" % (CFG_WEBSUBMIT_COUNTERSDIR, counter_lockfile))
        unlinked_lockfile = 1
    except OSError:
        ## unable to remove lockfile:
        pass
    return unlinked_lockfile
