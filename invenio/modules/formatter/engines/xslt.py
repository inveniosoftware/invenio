# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

"""
bibformat_xslt_engine - Wrapper for an XSLT engine.

Some functions are registered in order to be used in XSL code:
  - creation_date(recID)
  - modification_date(recID)

Used by: bibformat_engine.py
"""

from __future__ import print_function

import os

from flask import current_app
from lxml import etree

from invenio.modules.formatter.config import CFG_BIBFORMAT_TEMPLATES_PATH
from invenio.modules.formatter.api import (get_creation_date,
                                           get_modification_date)

CFG_BIBFORMAT_FUNCTION_NS = "http://cdsweb.cern.ch/bibformat/fn"
"""The namespace used for BibFormat function."""


def _get_creation_date(ctx, recID, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    Bridge between BibFormat and XSL stylesheets.

    Can be used in that way in XSL stylesheet (provided
    ``xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"`` has been declared):
    ``<xsl:value-of select="fn:creation_date(445)"/>`` where 445 is a recID

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value

    :param ctx: context as passed by lxml
    :param recID: record ID
    :param fmt: format of the returned date
    :return: creation date of X{recID}
    :rtype: str

    """
    try:
        if isinstance(recID, str):
            recID_int = int(recID)
        elif isinstance(recID, (int, long)):
            recID_int = recID
        elif isinstance(recID, list):
            recID = recID[0]
            if isinstance(recID, str):
                recID_int = int(recID)
            else:
                recID_int = int(recID.text)
        else:
            recID_int = int(recID.text)

        if isinstance(fmt, str):
            fmt_str = fmt
        elif isinstance(fmt, list):
            fmt = fmt[0]
            if isinstance(fmt, str):
                fmt_str = fmt
            else:
                fmt_str = fmt.text
        else:
            fmt_str = fmt.text

        return get_creation_date(recID_int, fmt_str)
    except Exception:
        current_app.logger.exception(
            "Error during formatting function evaluation"
        )
        return ''


def _get_modification_date(ctx, recID, fmt="%Y-%m-%dT%H:%M:%SZ"):
    """
    Bridge between BibFormat and XSL stylesheets.

    Can be used in that way in XSL stylesheet (provided
    ``xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"`` has been declared):
    ``<xsl:value-of select="fn:modification_date(445)"/>`` where 445 is a
    recID

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value

    :param ctx: context as passed by lxml
    :param recID: record ID
    :param fmt: format of the returned date
    :return: modification date of X{recID}
    :rtype: str

    """
    try:
        if isinstance(recID, str):
            recID_int = int(recID)
        elif isinstance(recID, (int, long)):
            recID_int = recID
        elif isinstance(recID, list):
            recID = recID[0]
            if isinstance(recID, str):
                recID_int = int(recID)
            else:
                recID_int = int(recID.text)
        else:
            recID_int = int(recID.text)

        if isinstance(fmt, str):
            fmt_str = fmt
        elif isinstance(fmt, list):
            fmt = fmt[0]
            if isinstance(fmt, str):
                fmt_str = fmt
            else:
                fmt_str = fmt.text
        else:
            fmt_str = fmt.text

        return get_modification_date(recID_int, fmt_str)
    except Exception:
        current_app.logger.exception(
            "Error during formatting function evaluation."
        )
        return ''


def _eval_bibformat(ctx, recID, template_code):
    """
    Bridge between BibFormat and XSL stylesheets.

    Can be used in that way in XSL stylesheet (provided
    ``xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"`` has been declared)::

        <xsl:value-of select="fn:eval_bibformat(marc:controlfield[@tag='001'],
                              '&lt;BFE_SERVER_INFO var=&quot;recurl&quot;>')"/>

    if recID is string, value is converted to int
    if recID is Node, first child node (text node) is taken as value
    template_code is evaluated as a format template piece of code. '<'
    and '"' need to be escaped with '&lt;' and '&quot;'

    :param ctx: context as passed by lxml
    :param recID: record ID
    :param template_code: the code calling a BFE_ as it would be used in
                          format template
    :return: the evaluated call to a format template (usually a call to a
             format element)
    :rtype: str

    """
    from invenio.modules.formatter.engine import format_with_format_template, \
        BibFormatObject
    try:
        if isinstance(recID, str):
            recID_int = int(recID)
        elif isinstance(recID, (int, long)):
            recID_int = recID
        elif isinstance(recID, list):
            recID = recID[0]
            if isinstance(recID, str):
                recID_int = int(recID)
            else:
                recID_int = int(recID.text)
        else:
            recID_int = int(recID.text)

        bfo = BibFormatObject(recID_int)
        out = format_with_format_template(None, bfo,
                                          verbose=0,
                                          format_template_code=template_code)
        return out[0]
    except Exception:
        current_app.logger.exception(
            "Error during formatting function evaluation."
        )
        return ''


def format(xmltext, template_filename=None, template_source=None):
    """
    Process an XML text according to a template, and returns the result.

    The template can be given either by name (or by path) or by source.
    If source is given, name is ignored.

    bibformat_xslt_engine will look for template_filename in standard
    directories for templates. If not found, template_filename will be assumed
    to be a path to a template. If none can be found, return None.

    :param xmltext: The string representation of the XML to process
    :param template_filename: The name of the template to use for the
                              processing
    :param template_source: The configuration describing the processing.
    :return: the transformed XML text.

    """
    # Retrieve template and read it
    if template_source:
        template = template_source
    elif template_filename:
        try:
            path_to_templates = (CFG_BIBFORMAT_TEMPLATES_PATH + os.sep +
                                 template_filename)
            if os.path.exists(path_to_templates):
                template = file(path_to_templates).read()
            elif os.path.exists(template_filename):
                template = file(template_filename).read()
            else:
                current_app.logger.error(
                    "{0} does not exist".format(template_filename)
                )
                return None
        except IOError:
            current_app.logger.exception(
                '{0} could not be read.'.format(template_filename),
            )
            return None
    else:
        current_app.logger.error('No templates were given.')
        return None

    # Some massaging of the input to avoid the default namespace issue
    # in XPath. More elegant solution might be found though.
    xmltext = xmltext.replace('xmlns="http://www.loc.gov/MARC21/slim"', '')

    # For older MARCXML records stored in bibfmt with empty indicators
    xmltext = xmltext.replace('ind1=""', 'ind1=" "')
    xmltext = xmltext.replace('ind2=""', 'ind2=" "')

    result = ""

    try:
        xml = etree.XML(xmltext)
    except etree.XMLSyntaxError:
        current_app.logger.exception('The XML code given is invalid.')
        return result
    except:
        current_app.logger.exception('Failed to process the XML code.')
        return result

    try:
        xsl = etree.XML(template)
    except etree.XMLSyntaxError:
        current_app.logger.exception('The XSL code given is invalid.')
        return result
    except:
        current_app.logger.exception('Failed to process the XSL code.')
        return result

    try:
        fns = etree.FunctionNamespace(CFG_BIBFORMAT_FUNCTION_NS)
        fns["creation_date"] = _get_creation_date
        fns["modification_date"] = _get_modification_date
        fns["eval_bibformat"] = _eval_bibformat
    except etree.NamespaceRegistryError:
        current_app.logger.exception(
            'Failed registering the XPath extension function.'
        )
        return result

    try:
        xslt = etree.XSLT(xsl)
    except etree.XSLTParseError:
        current_app.logger.exception('The XSL code given is invalid.')
        return result
    except:
        current_app.logger.exception('Failed to process the XSL code.')
        return result

    try:
        temporary_result = xslt(xml)
    except:
        current_app.logger.exception(
            'Failed to perform the XSL transformation.'
        )
        return result

    result = str(temporary_result)

    # Housekeeping
    del temporary_result
    del xslt
    del xsl
    del xml

    return result
