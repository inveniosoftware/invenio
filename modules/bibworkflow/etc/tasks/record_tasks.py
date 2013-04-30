## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

"""
BibWorkflow
"""

from invenio.bibconvert_xslt_engine import convert
#from invenio.bibholdingpen.widgets import checking_widget


def convert_record(stylesheet):
    def _convert_record(obj, eng):
        """Test"""
        eng.log.info("Engine: test engine logging")
        eng.log.info(obj.data['record'])
        eng.log.info(type(obj.data['record']))
        eng.log.info(stylesheet)
        newtext = convert(obj.data['record'], stylesheet)
        obj.log.info("Object: test object logging")
        obj.data['record'] = newtext

    _convert_record.__title__ = "Record convertion"
    _convert_record.__description__ = "This task converts a record."

    return _convert_record


def check_record(obj, eng):
    obj.log.info("We need to check it")
    #obj.widget = checking_widget()
    raise HaltProcessing


def print_record(obj, eng):
    print obj.data['record']

print_record.__title__ = "Print Record"
print_record.__description__ = "prints the records"
