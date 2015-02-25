# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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
        field_map = {"title": "title"}
        record = bwo.get_data()
        extracted_titles = []
        if hasattr(record, "get") and "title" in record:
            if isinstance(record["title"], str):
                extracted_titles = [record["title"]]
            else:
                extracted_titles.append(record["title"][field_map["title"]])
        return ", ".join(extracted_titles) or "No title found"

    @staticmethod
    def get_description(bwo):
        """Get the description (identifiers and categories) from the object data."""
        from invenio.modules.records.api import Record
        from flask import render_template, current_app

        record = bwo.get_data()
        final_identifiers = {}
        try:
            identifiers = Record(record.dumps()).persistent_identifiers
            for values in identifiers.values():
                final_identifiers.extend([i.get("value") for i in values])
        except Exception:
            current_app.logger.exception("Could not get identifiers")
            if hasattr(record, "get"):
                final_identifiers = [
                    record.get("system_control_number", {}).get("value", 'No ids')
                ]
            else:
                final_identifiers = []

        categories = []
        if hasattr(record, "get"):
            if 'subject' in record:
                lookup = ["subject", "term"]
            elif "subject_term" in record:
                lookup = ["subject_term", "term"]
            else:
                lookup = None
            if lookup:
                primary, secondary = lookup
                category_list = record.get(primary, [])
                if isinstance(category_list, dict):
                    category_list = [category_list]
                categories = [subject[secondary] for subject in category_list]

        return render_template('workflows/styles/harvesting_record.html',
                               categories=categories,
                               identifiers=final_identifiers)

    @staticmethod
    def formatter(bwo, **kwargs):
        """Nicely format the record."""
        from pprint import pformat
        from invenio.modules.records.api import Record

        data = bwo.get_data()
        if not data:
            return ''

        formatter = kwargs.get("formatter", None)
        of = kwargs.get("of", None)
        if formatter:
            # A separate formatter is supplied
            return formatter(data)

        if isinstance(data, collections.Mapping):
            # Dicts are cool on its own, but maybe its SmartJson (record)
            try:
                data = Record(data.dumps()).legacy_export_as_marc()
            except (TypeError, KeyError):
                pass

        if isinstance(data, string_types):
            # We can try formatter!
            # If already XML, format_record does not like it.
            if of and of != 'xm':
                try:
                    from invenio.modules.formatter import format_record
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
        return formatted_data
