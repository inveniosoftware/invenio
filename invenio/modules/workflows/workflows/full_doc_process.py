# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111 1307, USA.

""" Generic record process in harvesting."""
import collections
from six import string_types

from ..tasks.marcxml_tasks import (convert_record_with_repository,
                                   convert_record_to_bibfield,
                                   quick_match_record, upload_step,
                                   approve_record)
from ..tasks.workflows_tasks import log_info
from ..tasks.logic_tasks import workflow_if, workflow_else
from invenio.modules.workflows.utils import WorkflowBase


class full_doc_process(WorkflowBase):

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
                    final_identifiers = [record.get("system_number_external", {}).get("value", 'No ids')]
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

        from invenio.modules.formatter.engine import format_record

        data = bwo.get_data()
        if not data:
            return ''
        print kwargs
        formatter = kwargs.get("formatter", None)
        format = kwargs.get("format", None)
        if formatter:
            # A seperate formatter is supplied
            return formatter(data)
        from invenio.modules.records.api import Record
        if isinstance(data, collections.Mapping):
            # Dicts are cool on its own, but maybe its SmartJson (record)
            try:
                data = Record(data.dumps()).legacy_export_as_marc()
            except (TypeError, KeyError):
                # Maybe not, submission?
                return data

        if isinstance(data, string_types):
            # Its a string type, lets try to convert
            if format:
                # We can try formatter!
                # If already XML, format_record does not like it.
                if format != 'xm':
                    try:
                        return format_record(recID=None,
                                             of=format,
                                             xml_record=data)
                    except TypeError:
                        # Wrong kind of type
                        pass
                else:
                    # So, XML then
                    from xml.dom.minidom import parseString

                    try:
                        pretty_data = parseString(data)
                        return pretty_data.toprettyxml()
                    except TypeError:
                        # Probably not proper XML string then
                        return "Data cannot be parsed: %s" % (data,)
                    except Exception:
                        # Some other parsing error
                        pass

            # Just return raw string
            return data
        if isinstance(data, set):
            return list(data)
        # Not any of the above types. How juicy!
        return data

    object_type = "harvesting process"

    workflow = [
        convert_record_with_repository("oaiarxiv2marcxml.xsl"),
        convert_record_to_bibfield,
        workflow_if(quick_match_record, True),
        [
            approve_record,
            upload_step,
        ],
        workflow_else,
        [
            log_info("Record already into database"),
        ],
    ]
