# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2014 CERN.
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

"""Render Bar chart from csv file."""

import csv

from chardet.universaldetector import UniversalDetector
from flask import current_app, render_template, request

from invenio.ext.cache import cache


@cache.memoize(timeout=172800)
def validate_csv(f):
    """Return dialect information about given csv file."""
    with open(f.fullpath, 'rU') as csvfile:
        is_valid = False
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
        except Exception as e:
            current_app.logger.debug(
                'File %s is not valid CSV: %s' % (f.name+f.superformat, e))
            return {
                'delimiter': '',
                'encoding': '',
                'is_valid': is_valid
            }
        u = UniversalDetector()
        dialect.strict = True
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        try:
            for row in reader:
                u.feed(dialect.delimiter.join(row))
            is_valid = True
        except csv.Error as e:
            current_app.logger.debug(
                'File %s is not valid CSV: %s' % (f.name+f.superformat, e))
        finally:
            u.close()
    return {
        'delimiter': dialect.delimiter,
        'encoding': u.result['encoding'],
        'is_valid': is_valid
        }


def can_preview(f):
    """Determine if the given file can be previewed."""
    if f.superformat == '.csv':
        return validate_csv(f)['is_valid']
    else:
        return False


def preview(f):
    """Render appropiate template with embed flag."""
    file_info = validate_csv(f)

    return render_template("previewer/csv_bar.html", f=f,
                           delimiter=file_info['delimiter'],
                           encoding=file_info['encoding'],
                           embed=request.args.get('embed', type=bool))
