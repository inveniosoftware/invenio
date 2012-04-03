## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
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

"""Applies a transformation function to a value"""

from time import strptime, strftime
from invenio.textutils import strip_accents

LEADING_ARTICLES = ['the', 'a', 'an', 'at', 'on', 'of']


class InvenioBibSortWasherNotImplementedError(Exception):
    """Exception raised when a washer method
    defined in the bibsort config file is not implemented"""
    pass


class BibSortWasher(object):
    """Implements all the washer methods"""

    def __init__(self, washer):
        self.washer = washer
        fnc_name = '_' + washer
        try:
            self.washer_fnc = self.__getattribute__(fnc_name)
        except AttributeError, err:
            raise InvenioBibSortWasherNotImplementedError(err)

    def get_washer(self):
        """Returns the washer name"""
        return self.washer

    def get_transformed_value(self, val):
        """Returns the value"""
        return self.washer_fnc(val)

    def _sort_alphanumerically_remove_leading_articles_strip_accents(self, val):
        """
        Convert:
        'The title' => 'title'
        'A title' => 'title'
        'Title' => 'title'
        """
        if not val:
            return ''
        val_tokens = str(val).split(" ", 1) #split in leading_word, phrase_without_leading_word
        if len(val_tokens) == 2 and val_tokens[0].lower() in LEADING_ARTICLES:
            return strip_accents(val_tokens[1].strip().lower())
        return strip_accents(val.lower())

    def _sort_alphanumerically_remove_leading_articles(self, val):
        """
        Convert:
        'The title' => 'title'
        'A title' => 'title'
        'Title' => 'title'
        """
        if not val:
            return ''
        val_tokens = str(val).split(" ", 1) #split in leading_word, phrase_without_leading_word
        if len(val_tokens) == 2 and val_tokens[0].lower() in LEADING_ARTICLES:
            return val_tokens[1].strip().lower()
        return val.lower()

    def _sort_case_insensitive_strip_accents(self, val):
        """Remove accents and convert to lower case"""
        if not val:
            return ''
        return strip_accents(str(val).lower())

    def _sort_case_insensitive(self, val):
        """Conversion to lower case"""
        if not val:
            return ''
        return str(val).lower()

    def _sort_dates(self, val):
        """
        Convert:
        '8 nov 2010' => '2010-11-08'
        'nov 2010' => '2010-11-01'
        '2010' => '2010-01-01'
        """
        datetext_format = "%Y-%m-%d"
        try:
            datestruct = strptime(val, datetext_format)
        except ValueError:
            try:
                datestruct = strptime(val, "%d %b %Y")
            except ValueError:
                try:
                    datestruct = strptime(val, "%b %Y")
                except ValueError:
                    try:
                        datestruct = strptime(val, "%Y")
                    except ValueError:
                        return val
        return strftime(datetext_format, datestruct)

    def _sort_numerically(self, val):
        """
        Convert:
        1245 => float(1245)
        """
        try:
            return float(val)
        except ValueError:
            return 0


def get_all_available_washers():
    """
    Returns all the available washer functions without the leading '_'
    """
    method_list = dir(BibSortWasher)
    return [method[1:] for method in method_list if method.startswith('_') and method.find('__') < 0]
