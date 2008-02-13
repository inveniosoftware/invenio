# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibDocAdmin CLI administration tool
"""

__revision__ = "$Id$"

from optparse import OptionParser, OptionGroup
from invenio.bibdocfile import BibRecDocs, BibDoc

def _xml_mksubfield(key, subfield, fft):
    return fft.has_key(key) and '\t\t<subfield code="a">%s</subfield>\n' % fft[key] or ''

def _xml_fft_creator(fft):
    """Transform an fft dictionary (made by keys url, docname, format,
    new_docname, icon, comment, description, restriction, doctype, into an xml
    string."""
    out = '\t<datafield tag ="FFT" ind1=" " ind2=" ">\n'
    out += _xml_mksubfield('url', 'a', fft)
    out += _xml_mksubfield('docname', 'n', fft)
    out += _xml_mksubfield('format', 'f', fft)
    out += _xml_mksubfield('newdocname', 'm', fft)
    out += _xml_mksubfield('doctype', 't', fft)
    out += _xml_mksubfield('description', 'd', fft)
    out += _xml_mksubfield('comment', 'c', fft)
    out += _xml_mksubfield('restriction', 'r', fft)
    out += _xml_mksubfield('icon', 'x', fft)
    out += '\t</datafield>'
    return out

def ffts_to_xmls(ffts):
    """Transform a dictionary: recid -> ffts where ffts is a list of fft dictionary
    into xml.
    """
    out = ''
    for recid, ffts in ffts.iteritems():
        out += '<record>\n'
        out += '\t<controlfield tag="001">%i</controlfield>\n' % recid
        for fft in ffts:
            out += _xml_fft_creator(fft)
        out += '</record>\n'
    return out

def get_recids(pattern, collection, recid):
    """Return a list of recids corresponding to the given query."""
        return perform_request_search(cc=collection, p=pattern, recid=recid)

def get_usage():
    """Return a nicely formatted string for printing the help of bibdocadmin"""
    return """usage: %prog <query> <action> [options]
  <query>: --pattern <pattern>, --collection <collection>, --recid <recid>,
           --doctype <doctype>, --docid <docid>, --docname <docname>,
           --revision <revision>, --format <format>, --url <url>
 <action>: --get-info, --get-stats, --get-usage, --get-log, --get-docnames
           --get-docids, --get-recids, --get-doctypes, --get-revisions,
           --get-last-revisions, --get-formats, --get-comments,
           --get-descriptions, --get-restrictions, --get-icons
           --delete, --undelete, --purge, --expunge
           --check-md5, --update-md5
           --set-doctype, --set-docname, --set-comment, --set-description,
           --set-restriction, --set-icon
           --append --revise
[options]: --with-stamp-template <template>, --with-stamp-parameters <parameters>,
           --verbose <level>, --force, --interactive, --with-icon-size <size>,
           --with-related-formats
With <query> you select the range of record/docnames/single files to work on.
Note that some actions e.g. delete, append, revise etc. works at the docname
level, while others like --set-comment, --set-description, at single file level
and other can be applied in an iterative way to many records in a single run.
"""

_actions = ['get-info', 'get-stats', 'get-usage', 'get-log', 'get-docnames'
            'get-docids', 'get-recids', 'get-doctypes', 'get-revisions',
            'get-last-revisions', 'get-formats', 'get-comments',
            'get-descriptions', 'get-restrictions', 'get-icons',
            'delete', 'undelete', 'purge', 'expunge',
            'check-md5', 'update-md5',
            'set-doctype', 'set-docname', 'set-comment', 'set-description',
            'set-restriction', 'set-icon',
            'append', 'revise']

def prepare_option_parser():
    """Parse the command line options."""
    parser = OptionParser(usage="usage: %prog <query> <action> [options]", version=__revision__)
    query_options = OptionGroup(parser, 'Query parameters')
    query_options.add_option('-p', '--pattern', dest='pattern')
    query_options.add_option('-c', '--collection', dest='collection')
    query_options.add_option('-r', '--recid', type='int', dest='recid')
    query_options.add_option('-d', '--docname', dest='docname')
    query_options.add_option('-u', '--url', dest='url')
    query_options.add_option('--docid', type='int', dest='docid')
    query_options.add_option('--revision', dest='revision', default='last')
    query_options.add_option('-f', '--format', action='store', type='string', dest='format')
    parser.add_option_group(query_options)
    action_options = OptionGroup(parser, 'Action parameters')
    for action in _actions:
        action_options.add_option('--%s' % action, action='store_const', const=action, dest='action')
    parser.add_option_group(action_options)


