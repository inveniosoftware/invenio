# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Display the duration of a media file
"""

__revision__ = "$Id$"

import re

re_duration = re.compile('(\s|\A)(((?P<hours>\d{1,2}):)?(?P<minutes>\d{1,2}):(?P<seconds>\d\d))(\s|\Z)')

def format_element(bfo, input_units="m", output_format="%(H)02i:%(M)02i:%(S)02i"):
    """
    Display the duration of a media file (300__a).

    @param input_units: if field 300__a is digit, expect it to be:
                           - s: seconds
                           - m: minutes
                           - h: hours
                        If field 300__a is not digit, expect it to contain some variant of HH:MM:SS
    @param output_format: how to display the duration. A basic Pythonic string replacement is
                          done on the input string. You can use the following keys:
                            - H: The number of hours
                            - M: The number of minutes
                            - S: The number of seconds
                            - H: The total number of hours
                            - M: The total number of minutes
                            - S: The total number of seconds
    """
    # Get the duration
    duration_in_seconds = None
    duration = bfo.field('300__a')
    try:
        int_duration = int(float(duration))
        if input_units == 's':
            duration_in_seconds = int_duration
        elif input_units == 'm':
            duration_in_seconds = int_duration * 60
        elif input_units == 'h':
            duration_in_seconds = int_duration * 3600
    except Exception as e:
        pass

    if duration_in_seconds is None:
        # Try to find something like HH:MM:SS
        match_obj = re_duration.match(duration)
        if match_obj:
            seconds = int(match_obj.group('seconds'))
            minutes = int(match_obj.group('minutes'))
            hours = match_obj.group('hours')
            if not hours:
                hours = 0
            else:
                hours = int(hours)
            duration_in_seconds = seconds + (60 * minutes) + (360 * hours)

    # Output the duration
    if duration_in_seconds:
        return output_format % {'H': duration_in_seconds / 3600,
                                'M': (duration_in_seconds / 60) % 60,
                                'S': duration_in_seconds % 60,
                                'h': duration_in_seconds / 3600.0, # Absolute nb of hours
                                'm': duration_in_seconds / 60.0, # Absolute nb of minutes
                                's': duration_in_seconds #Absolute nb of seconds
                                }
