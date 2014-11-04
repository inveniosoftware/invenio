# -*- coding: utf-8 -*-
#
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

"""OAI harvest utils."""

from lxml import etree


def record_extraction_from_file(path, oai_namespace="{http://www.openarchives.org/OAI/2.0/}"):
    """Given a harvested file return a list of every record incl. headers.

    :param path: is the path of the file harvested
    :type path: str

    :return: return a list of XML records as string
    :rtype: str
    """
    list_of_records = []
    with open(path) as xml_file:
        list_of_records = record_extraction_from_string(xml_file.read(), oai_namespace)
    return list_of_records


def record_extraction_from_string(xml_string, oai_namespace="{http://www.openarchives.org/OAI/2.0/}"):
    """Given a OAI-PMH XML return a list of every record incl. headers.

    :param xml_string: OAI-PMH XML
    :type xml_string: str

    :return: return a list of XML records as string
    :rtype: str
    """
    root = etree.fromstring(xml_string)
    headers = []
    headers.extend(root.findall(".//{0}responseDate".format(oai_namespace)))
    headers.extend(root.findall(".//{0}request".format(oai_namespace)))

    records = root.findall(".//{0}record".format(oai_namespace))

    list_of_records = []
    for record in records:
        wrapper = etree.Element("{0}OAI-PMH".format(oai_namespace))
        for header in headers:
            wrapper.append(header)
        wrapper.append(record)
        list_of_records.append(etree.tostring(wrapper))
    return list_of_records


def identifier_extraction_from_string(xml_string, oai_namespace="{http://www.openarchives.org/OAI/2.0/}"):
    """Given a OAI-PMH XML string return the OAI identifier.

    :param xml_string: OAI-PMH XML
    :type xml_string: str

    :return: OAI identifier
    :rtype: str
    """
    root = etree.fromstring(xml_string)
    node = root.find(".//{0}identifier".format(oai_namespace))
    if node is not None:
        return node.text
