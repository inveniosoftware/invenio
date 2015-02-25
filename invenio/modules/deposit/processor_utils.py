# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

# from wtforms.validators import ValidationError, StopValidation, Regexp
from werkzeug import MultiDict
from invenio.utils.datacite import DataciteMetadata
from invenio.utils.sherpa_romeo import SherpaRomeoSearch
from invenio.modules.records.api import get_record
from invenio.utils import persistentid as pidutils

#
# General purpose processors
#


def replace_field_data(field_name, getter=None):
    """Return a processor.

    This will replace the given field names value with the value from the field
    where the processor is installed.
    """
    def _inner(form, field, submit=False, fields=None):
        getattr(form, field_name).data = getter(field) if getter else \
            field.data
    return _inner


def set_flag(flag_name):
    """Return processor which will set a given flag on a field."""
    def _inner(form, field, submit=False, fields=None):
        setattr(field.flags, flag_name, True)
    return _inner


#
# PID processors
#
class PidSchemeDetection(object):

    """Detect persistent identifier scheme and store it in another field."""

    def __init__(self, set_field=None):
        self.set_field = set_field

    def __call__(self, form, field, submit=False, fields=None):
        if field.data:
            schemes = pidutils.detect_identifier_schemes(field.data)
            if schemes:
                getattr(form, self.set_field).data = schemes[0]
            else:
                getattr(form, self.set_field).data = ''


class PidNormalize(object):

    """Normalize a persistent identifier."""

    def __init__(self, scheme_field=None, scheme=None):
        self.scheme_field = scheme_field
        self.scheme = scheme

    def __call__(self, form, field, submit=False, fields=None):
        scheme = None
        if self.scheme_field:
            scheme = getattr(form, self.scheme_field).data
        elif self.scheme:
            scheme = self.scheme
        else:
            schemes = pidutils.detect_identifier_schemes(field.data)
            if schemes:
                scheme = schemes[0]
        if scheme:
            if field.data:
                field.data = pidutils.normalize_pid(field.data, scheme=scheme)


#
# DOI-related processors
#

def datacite_dict_mapper(datacite, form, mapping):
    """Map DataCite metadata to form fields based on a mapping."""
    for func_name, field_name in mapping.items():
        setattr(form, field_name, getattr(datacite, func_name)())


class DataCiteLookup(object):

    """Lookup DOI metadata in DataCite.

    But only if DOI is not locally administered.
    """

    def __init__(self, display_info=False, mapping=None,
                 mapping_func=None, exclude_prefix='10.5072'):
        self.display_info = display_info
        self.mapping = mapping or dict(
            get_publisher='publisher',
            get_titles='title',
            get_dates='date',
            get_description='abstract',
        )
        self.mapping_func = mapping_func or datacite_dict_mapper
        self.prefix = exclude_prefix

    def __call__(self, form, field, submit=False, fields=None):
        if not field.errors and field.data \
           and not field.data.startswith(self.prefix + '/'):
            try:
                datacite = DataciteMetadata(field.data)
                if datacite.error:
                    if self.display_info:
                        field.add_message(
                            "DOI metadata could not be retrieved.",
                            state='info'
                        )
                    return
                if self.mapping_func:
                    self.mapping_func(datacite, form, self.mapping)
                    if self.display_info:
                        field.add_message(
                            "DOI metadata successfully imported from "
                            "DataCite.", state='info')
            except Exception:
                # Ignore errors
                pass


datacite_lookup = DataCiteLookup


def sherpa_romeo_issn_process(form, field, submit=False):
    value = field.data or ''
    if value == "" or value.isspace():
        return dict(error=0, error_message='')
    s = SherpaRomeoSearch()
    s.search_issn(value)
    if s.error:
        field.add_message(s.error_message, state='info')
        return

    if s.get_num_hits() == 1:
        journal = s.parser.get_journals(attribute='jtitle')
        journal = journal[0]
        publisher = s.parser.get_publishers(journal=journal)
        if publisher is not None and publisher != []:
            if hasattr(form, 'journal'):
                form.journal.data = journal

            if hasattr(form, 'publisher'):
                form.publisher.data = publisher['name']
            return
        else:
            if hasattr(form, 'journal'):
                form.journal.data = journal
            return

    field.add_message("Couldn't find Journal.", state='info')


def sherpa_romeo_publisher_process(form, field, submit=False, fields=None):
    value = field.data or ''
    if value == "" or value.isspace():
        return
    s = SherpaRomeoSearch()
    s.search_publisher(value)
    if s.error:
        field.add_message(s.error_message, state='info')

    conditions = s.parser.get_publishers(attribute='conditions')
    if conditions is not None and s.get_num_hits() == 1:
        conditions = conditions[0]
    else:
        conditions = []
    if conditions != []:
        conditions_html = "<u>Conditions</u><br><ol>"
        if isinstance(conditions['condition'], str):
            conditions_html += "<li>" + conditions['condition'] + "</li>"
        else:
            for condition in conditions['condition']:
                conditions_html += "<li>" + condition + "</li>"

        copyright_links = s.parser.get_publishers(attribute='copyrightlinks')
        if copyright_links is not None and copyright_links != []:
            copyright_links = copyright_links[0]
        else:
            copyright_links = None

        if isinstance(copyright_links, list):
            copyright_links_html = ""
            for copyright_link in copyright_links['copyrightlink']:
                copyright_links_html += (
                    '<a href="' + copyright_link['copyrightlinkurl'] +
                    '">' + copyright_link['copyrightlinktext'] + "</a><br>")
        elif isinstance(copyright_links, dict):
            if isinstance(copyright_links['copyrightlink'], list):
                for copyright_link in copyright_links['copyrightlink']:
                    copyright_links_html = (
                        '<a href="' + copyright_link['copyrightlinkurl'] +
                        '">' + copyright_link['copyrightlinktext'] +
                        "</a><br>")
            else:
                copyright_link = copyright_links['copyrightlink']
                copyright_links_html = (
                    '<a href="' + copyright_link['copyrightlinkurl'] +
                    '">' + copyright_link['copyrightlinktext'] + "</a><br>")

        home_url = s.parser.get_publishers(attribute='homeurl')
        if home_url is not None and home_url != []:
            home_url = home_url[0]
            home_url = '<a href="' + home_url + '">' + home_url + "</a>"
        else:
            home_url = None

        info_html = ""
        if home_url is not None:
            info_html += "<p>" + home_url + "</p>"

        if conditions is not None:
            info_html += "<p>" + conditions_html + "</p>"

        if copyright_links is not None:
            info_html += "<p>" + copyright_links_html + "</p>"

        if info_html != "":
            field.add_message(info_html, state='info')


def sherpa_romeo_journal_process(form, field, submit=False, fields=None):
    value = field.data or ''
    if value == "" or value.isspace():
        return

    s = SherpaRomeoSearch()
    s.search_journal(value, 'exact')
    if s.error:
        field.add_message(s.error_message, state='info')
        return

    if s.get_num_hits() == 1:
        issn = s.parser.get_journals(attribute='issn')
        if issn != [] and issn is not None:
            issn = issn[0]
            publisher = s.parser.get_publishers(journal=value)
            if publisher is not None and publisher != []:
                if hasattr(form, 'issn'):
                    form.issn.data = issn

                if hasattr(form, 'publisher'):
                    form.publisher.data = publisher['name']
                    form.publisher.post_process(form)
                return

            field.add_message("Journal's Publisher not found", state='info')
            if hasattr(form, 'issn'):
                form.issn.data = issn
            if hasattr(form, 'publisher'):
                form.publisher.data = publisher
                form.publisher.post_process(form)
        else:
            field.add_message("Couldn't find ISSN.", state='info')


def record_id_process(form, field, submit=False):
    value = field.data or ''
    if value == "" or value.isspace():
        return

    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    if is_number(field.data):
        json_reader = get_record(value)
    else:
        field.add_message("Record id must be a number!", state='error')
        return

    if json_reader is not None:
        webdeposit_json = form.uncook_json(json_reader, {}, value)
        #FIXME: update current json, past self, what do you mean?? :S

        field.add_message('<a href="/record/"' + value +
                          '>Record</a> was loaded successfully',
                          state='info')

        form.process(MultiDict(webdeposit_json))
    else:
        field.add_message("Record doesn't exist", state='info')
