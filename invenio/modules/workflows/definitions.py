# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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


"""Contains basic workflow types for use in workflow definitions."""


import collections
from six import string_types


class WorkflowMissing(object):

    """Placeholder workflow definition."""

    workflow = [lambda obj, eng: None]


class WorkflowBase(object):

    """Base class for workflow definition.

    Interface to define which functions should be imperatively implemented.
    All workflows should inherit from this class.
    """

    @staticmethod
    def get_title(bwo, **kwargs):
        """Return the value to put in the title column of HoldingPen."""
        return "No title"

    @staticmethod
    def get_description(bwo, **kwargs):
        """Return the value to put in the title  column of HoldingPen."""
        return "No description"

    @staticmethod
    def formatter(obj, **kwargs):
        """Format the object."""
        return "No data"


class RecordWorkflow(WorkflowBase):

    """Workflow to be used where BibWorkflowObject is a Record instance."""

    workflow = []

    @staticmethod
    def get_title(bwo):
        """Get the title."""
        extracted_title = []
        record = bwo.get_data()
        if hasattr(record, "get") and "title" in record:
            if isinstance(record["title"], str):
                extracted_title = [record["title"]]
            else:
                for a_title in record["title"]:
                    extracted_title.append(record["title"][a_title])
        else:
            extracted_title = [" No title"]
        title_final = ""
        for i in extracted_title:
            title_final += "{0} ".format(i)
        return title_final

    @staticmethod
    def get_description(bwo):
        """Get the description column part."""
        message = None
        try:
            record = bwo.get_data()
            from invenio.modules.records.api import Record

            try:
                identifiers = Record(record.dumps()).persistent_identifiers
                final_identifiers = []
                for i in identifiers:
                    final_identifiers.append(i['value'])
            except Exception as e:
                if hasattr(record, "get"):
                    final_identifiers = [record.get("system_control_number", {}).get("value", 'No ids')]
                else:
                    final_identifiers = [' No ids']

            categories = [" No categories"]
            if hasattr(record, "get"):
                if 'subject' in record:
                    lookup = ["subject", "term"]
                elif "subject_term":
                    lookup = ["subject_term", "term"]
                else:
                    lookup = None
                categories = []
                if lookup:
                    primary, secondary = lookup
                    category_list = record.get(primary, [])
                    if isinstance(category_list, dict):
                        category_list = [category_list]
                    for subject in category_list:
                        category = subject[secondary]
                        if len(subject) == 2:
                            if subject.keys()[1] == secondary:
                                source_list = subject[subject.keys()[0]]
                            else:
                                source_list = subject[subject.keys()[1]]
                        else:
                            try:
                                source_list = subject['source']
                            except KeyError:
                                source_list = ""
                        categories.append(category + "(" + source_list + ")")
        except Exception as e:
            categories = None
            final_identifiers = None
            from invenio.modules.workflows.models import ObjectVersion

            if bwo.version == ObjectVersion.INITIAL:
                message = categories = "The process has not started!!!"
            else:
                message = categories = "The process CRASHED!!! \n {0}".format(str(e.message))

        from flask import render_template
        return render_template('workflows/styles/harvesting_record.html',
                               categories=categories,
                               identifiers=final_identifiers,
                               message=message)

    @staticmethod
    def formatter(bwo, **kwargs):
        """Nicely format the record."""
        from flask import Markup
        from pprint import pformat

        data = bwo.get_data()
        if not data:
            return ''

        formatter = kwargs.get("formatter", None)
        of = kwargs.get("of", None)
        if formatter:
            # A separate formatter is supplied
            return formatter(data)

        from invenio.modules.records.api import Record
        if isinstance(data, collections.Mapping):
            # Dicts are cool on its own, but maybe its SmartJson (record)
            try:
                data = Record(data.dumps()).legacy_export_as_marc()
            except (TypeError, KeyError):
                pass

        if isinstance(data, string_types):
            # We can try formatter!
            # If already XML, format_record does not like it.
            if of != 'xm':
                try:
                    from invenio.modules.formatter.engine import format_record
                    formatted_data = format_record(
                        recID=None,
                        of=of,
                        xml_record=data
                    )
                except TypeError:
                    # Wrong kind of type
                    pass
            else:
                # So, XML then
                from xml.dom.minidom import parseString

                try:
                    unpretty_data = parseString(data)
                    formatted_data = unpretty_data.toprettyxml()
                except TypeError:
                    # Probably not proper XML string then
                    return "Data cannot be parsed: %s" % (data,)
                except Exception:
                    # Just return raw string
                    pass

        if not formatted_data:
            formatted_data = data

        if isinstance(formatted_data, dict):
            formatted_data = pformat(formatted_data)
        elif of == "xm":
            formatted_data = Markup.escape(formatted_data)
        elif of == 'xo':
            formatted_data = Markup.escape(formatted_data[0])
