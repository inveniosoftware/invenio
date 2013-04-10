# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from invenio.dataciteutils import DataciteMetadata
from invenio.sherpa_romeo import SherpaRomeoSearch


def datacite_doi_validate(field):
    value = field.data
    if value == "" or value.isspace():
        return dict()
    datacite = DataciteMetadata(value)
    if datacite.error:
        return dict(info=1, info_message="Couldn't retrieve doi metadata")

    return dict(fields=dict(publisher=datacite.get_publisher(),
                            title=datacite.get_titles(),
                            date=datacite.get_dates(),
                            abstract=datacite.get_description()),
                success=1,
                success_message='Datacite.org metadata imported successfully')


def sherpa_romeo_issn_validate(field):
    value = field.data
    if value == "" or value.isspace():
        return dict(error=0, error_message='')
    s = SherpaRomeoSearch()
    s.search_issn(value)
    if s.error:
        return dict(error=1, error_message=s.error_message)

    if s.get_num_hits() == 1:
        journal = s.parser.get_journals(attribute='jtitle')
        journal = journal[0]
        publisher = s.parser.get_publishers(journal=journal)
        if publisher is not None and publisher != []:
            return dict(error=0, error_message='',
                        fields=dict(journal=journal,
                                    publisher=publisher['name']))
        else:
            return dict(error=0, error_message='',
                        fields=dict(journal=journal))

    return dict(info=1, info_message="Couldn't find Journal")


def sherpa_romeo_publisher_validate(field):
    value = field.data
    if value == "" or value.isspace():
        return dict(error=0, error_message='')
    s = SherpaRomeoSearch()
    s.search_publisher(value)
    if s.error:
        return dict(info=1, info_message=s.error_message)

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
            for copyright in copyright_links['copyrightlink']:
                copyright_links_html += '<a href="' + copyright['copyrightlinkurl'] + \
                                        '">' + copyright['copyrightlinktext'] + "</a><br>"
        elif isinstance(copyright_links, dict):
            if isinstance(copyright_links['copyrightlink'], list):
                for copyright in copyright_links['copyrightlink']:
                    copyright_links_html = '<a href="' + copyright['copyrightlinkurl'] + \
                                           '">' + copyright['copyrightlinktext'] + "</a><br>"
            else:
                copyright = copyright_links['copyrightlink']
                copyright_links_html = '<a href="' + copyright['copyrightlinkurl'] + \
                                       '">' + copyright['copyrightlinktext'] + "</a><br>"

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
            return dict(error=0, error_message='',
                        info=1, info_message=info_html)
    return dict(error=0, error_message='')


def sherpa_romeo_journal_validate(field):
    value = field.data
    if value == "" or value.isspace():
        return dict(error=0, error_message='')

    s = SherpaRomeoSearch()
    s.search_journal(value, 'exact')
    if s.error:
        return dict(info=1, info_message=s.error_message)

    if s.get_num_hits() == 1:
        issn = s.parser.get_journals(attribute='issn')
        if issn != [] and issn is not None:
            issn = issn[0]
            publisher = s.parser.get_publishers(journal=value)
            if publisher is not None and publisher != []:
                return dict(error=0, error_message='',
                            fields=dict(issn=issn,
                                        publisher=publisher['name']))
            return dict(error=0, error_message='',
                        info=1, info_message="Journal's Publisher not found",
                        fields=dict(publisher="", issn=issn))
        else:
            return dict(info=1, info_message="Couldn't find ISSN")
    return dict(error=0, error_message='')


def number_validate(field, error_message='It must be a number!'):
    value = field.data
    if value == "" or value.isspace():
        return dict(error=0, error_message='')

    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    if not is_number(value):
        try:
            field.errors.append(error_message)
        except AttributeError:
            field.errors = list(field.process_errors)
            field.errors.append(error_message)
        return dict(error=1,
                    error_message=error_message)
    else:
        return dict(error=0, error_message='')
