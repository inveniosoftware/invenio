# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

""" Test unit for the miscutil/errorlib module. """

__revision__ = "$Id$"

from invenio.errorlib import get_emergency_recipients
from invenio.testutils import make_test_suite, run_test_suite

import unittest
import datetime

class TestGetEmergencyRecipients(unittest.TestCase):

    def test_get_emergency_recipients(self):
        """errorlib - test return of proper set of recipients"""

        now = datetime.datetime.today()
        tomorrow = now + datetime.timedelta(days=1)
        diff_day = now + datetime.timedelta(days=4)
        later = now.replace(hour=(now.hour + 1) % 24)
        earlier = now.replace(hour=(now.hour - 1) % 24)
        constraint_now = "%s %s-%s" % (
                                    now.strftime("%a"),
                                    earlier.strftime("%H:00"),
                                    later.strftime("%H:00"),
                                    )
        constraint_tomorrow = "%s %s-%s" % (
                                    tomorrow.strftime("%a"),
                                    earlier.strftime("%H:00"),
                                    later.strftime("%H:00"),
                                    )
        constraint_time = "%s-%s" % (
                                    earlier.strftime("%H:00"),
                                    later.strftime("%H:00"),
                                    )
        minute = (now.minute - 3) % 60
        # hour and earlier can change when minute is modified
        if minute > now.minute:
            hour = (now.hour - 1) % 24
            earlier = now.replace(hour=(now.hour - 2) % 24)
        else:
            hour = now.hour
        constraint_near_miss = "%s-%s" % (
                                    earlier.strftime("%H:00"),
                                    now.replace(minute=minute, hour=hour) \
                                        .strftime("%H:%M")
                                    )
        constraint_day = "%s" % now.strftime("%A")
        constraint_diff_day = "%s" % diff_day.strftime("%A")
        test_config = {
                       constraint_now:      'now@example.com',
                       constraint_tomorrow: 'tomorrow@example.com',
                       constraint_time:     'time@example.com',
                       constraint_day:      'day@example.com,day@foobar.com',
                       constraint_diff_day: 'diff_day@example.com',
                       constraint_near_miss:'near_miss@example.com',
                       '*':                 'fallback@example.com',
                       }
        result = get_emergency_recipients(recipient_cfg=test_config)
        expected = ['now@example.com', 'time@example.com',
                    'day@example.com,day@foobar.com', 'fallback@example.com']
        self.assertEqual(set(result), set(expected))

TEST_SUITE = make_test_suite(TestGetEmergencyRecipients,)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
