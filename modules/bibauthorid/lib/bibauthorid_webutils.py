# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

import locale

# Set locale rules at definition time for formatting.
locale.setlocale(locale.LC_ALL, '')


def group_format_number(number):
    """Formats a floating or integer number into number groups by locale.

    Example:
        >>> group_format_number(123456)
        '123,456'

        Note that floats are rounded to a precision of 1:
        >>> group_format_number(1234.56)
        '1,234.6'

    """
    if isinstance(number, int) or long:
        return locale.format("%d", number, grouping=True)
    elif isinstance(number, float):
        return locale.format("%-.1f", number, grouping=True)
    else:
        raise TypeError("Only group formatting of ints and floats are supported.")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
