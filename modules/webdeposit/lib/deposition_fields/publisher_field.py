# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from wtforms import TextField
from invenio.webdeposit_field import WebDepositField
from invenio.sherpa_romeo import SherpaRomeoSearch
from invenio.webdeposit_workflow_utils import JsonCookerMixinBuilder

__all__ = ['PublisherField']


class PublisherField(TextField, WebDepositField, JsonCookerMixinBuilder('publisher')):

    def __init__(self, **kwargs):
        self._icon_html = '<i class="icon-certificate"></i>'
        super(PublisherField, self).__init__(**kwargs)

    def pre_validate(self, form=None):
        value = self.data
        if value == "" or value.isspace():
            return dict(error=0, error_message='')
        s = SherpaRomeoSearch()
        s.search_publisher(value)
        if s.error:
            return dict(info=1, info_message=s.error_message)

        conditions = s.parser.get_publishers(attribute='conditions')[0]
        if conditions is not []:
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
                return dict(error=0, error_message='', info=1, info_message=info_html)

        return dict(error=0, error_message='')

    def autocomplete(self):
        value = self.data
        sherpa_romeo = SherpaRomeoSearch()
        return sherpa_romeo.search_publisher(value)
