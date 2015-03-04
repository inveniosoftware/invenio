# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

from invenio.legacy.dbquery import run_sql
from operator import itemgetter
from itertools import groupby
from msgpack import packb as serialize

depends_on = ['invenio_release_1_1_0']

def info():
    return "Introduces aidPERSONIDDATA datablob column"

def do_upgrade():
    column_exists = run_sql("SHOW COLUMNS FROM `aidPERSONIDDATA` LIKE 'datablob'")
    if not column_exists:
        run_sql("""ALTER TABLE aidPERSONIDDATA
                   ADD COLUMN datablob LONGBLOB NULL DEFAULT NULL AFTER data;""")

    run_sql("""ALTER TABLE aidPERSONIDDATA MODIFY data VARCHAR( 256 ) NULL DEFAULT NULL""")

    pids_with_tickets = set(run_sql("""select personid
                                       from aidPERSONIDDATA
                                       where tag like %s""",
                                       ('rt_%',) ))
    pids_with_tickets = [pid[0] for pid in pids_with_tickets]

    for pid in pids_with_tickets:
        request_tickets = run_sql("""select tag, data, opt1
                                     from aidPERSONIDDATA
                                     where personid=%s
                                     and tag like 'rt_%%'""",
                                     (pid,) )
        request_tickets = sorted(request_tickets, key=itemgetter(2))
        request_tickets = groupby(request_tickets, key=itemgetter(2))
        request_tickets = [[[(i[0][3:], i[1]) for i in tinfo], tid] for tid, tinfo in request_tickets]

        new_request_tickets = list()
        for request_ticket_attributes, tid in request_tickets:
            new_request_ticket = {'tid': tid}
            operations = list()
            for tag, value in request_ticket_attributes:
                if tag == 'confirm':
                    operations.append(('assign', value))
                elif tag == 'repeal':
                    operations.append(('reject', value))
                else:
                    new_request_ticket[tag] = value

            new_request_ticket['operations'] = operations

            if new_request_ticket['operations']:
                new_request_tickets.append(new_request_ticket)

        new_request_tickets_num = len(new_request_tickets)
        new_request_tickets = serialize(new_request_tickets)

        run_sql("""insert into aidPERSONIDDATA
                   (personid, tag, datablob, opt1)
                   values (%s, %s, %s, %s)""",
                   (pid, 'request_tickets', new_request_tickets, new_request_tickets_num) )

    run_sql("""delete from aidPERSONIDDATA
               where tag like %s""",
               ('rt_%', ))

def estimate():
    return 1
