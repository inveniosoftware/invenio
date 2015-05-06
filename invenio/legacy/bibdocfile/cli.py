# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2012, 2014, 2015 CERN.
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

from __future__ import print_function

"""
BibDocAdmin CLI administration tool
"""

__revision__ = "$Id$"

import sys
import re
import os
import time
import fnmatch
from datetime import datetime
from logging import getLogger, debug, DEBUG
from optparse import OptionParser, OptionGroup, OptionValueError
from six import iteritems

from invenio.base.factory import with_app_context

from invenio.ext.logging import register_exception
from invenio.config import CFG_SITE_URL, CFG_BIBDOCFILE_FILEDIR, \
    CFG_SITE_RECORD, CFG_TMPSHAREDDIR
from invenio.legacy.bibdocfile.api import BibRecDocs, BibDoc, InvenioBibDocFileError, \
    nice_size, check_valid_url, clean_url, get_docname_from_url, \
    guess_format_from_url, KEEP_OLD_VALUE, decompose_bibdocfile_fullpath, \
    bibdocfile_url_to_bibdoc, decompose_bibdocfile_url, \
    CFG_BIBDOCFILE_AVAILABLE_FLAGS

from intbitset import intbitset
from invenio.legacy.search_engine import perform_request_search
from invenio.utils.text import wrap_text_in_a_box, wait_for_user
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.bibtask import task_low_level_submission
from invenio.utils.text import encode_for_xml
from invenio.legacy.websubmit.file_converter import can_perform_ocr
from invenio.utils.shell import retry_mkstemp

def _xml_mksubfield(key, subfield, fft):
    return fft.get(key, None) is not None and '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(str(fft[key]))) or ''

def _xml_mksubfields(key, subfield, fft):
    ret = ""
    for value in fft.get(key, []):
        ret += '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(str(value)))
    return ret

def _xml_fft_creator(fft):
    """Transform an fft dictionary (made by keys url, docname, format,
    new_docname, comment, description, restriction, doctype, into an xml
    string."""
    debug('Input FFT structure: %s' % fft)
    out = '\t<datafield tag ="FFT" ind1=" " ind2=" ">\n'
    out += _xml_mksubfield('url', 'a', fft)
    out += _xml_mksubfield('docname', 'n', fft)
    out += _xml_mksubfield('format', 'f', fft)
    out += _xml_mksubfield('new_docname', 'm', fft)
    out += _xml_mksubfield('doctype', 't', fft)
    out += _xml_mksubfield('description', 'd', fft)
    out += _xml_mksubfield('comment', 'z', fft)
    out += _xml_mksubfield('restriction', 'r', fft)
    out += _xml_mksubfields('options', 'o', fft)
    out += _xml_mksubfield('version', 'v', fft)
    out += '\t</datafield>\n'
    debug('FFT created: %s' % out)
    return out

def ffts_to_xml(ffts_dict):
    """Transform a dictionary: recid -> ffts where ffts is a list of fft dictionary
    into xml.
    """
    debug('Input FFTs dictionary: %s' % ffts_dict)
    out = ''
    recids = ffts_dict.keys()
    recids.sort()
    for recid in recids:
        ffts = ffts_dict[recid]
        if ffts:
            out += '<record>\n'
            out += '\t<controlfield tag="001">%i</controlfield>\n' % recid
            for fft in ffts:
                out += _xml_fft_creator(fft)
            out += '</record>\n'
    debug('MARC to Upload: %s' % out)
    return out

_shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
def _parse_datetime(var):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    if not var:
        return None
    date = time.time()
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = _shift_re.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        return datetime.fromtimestamp(date + sign * factor * value)
    else:
        return datetime(*(time.strptime(var, "%Y-%m-%d %H:%M:%S")[0:6]))
        # The code above is Python 2.4 compatible. The following is the 2.5
        # version.
        # return datetime.strptime(var, "%Y-%m-%d %H:%M:%S")

def _parse_date_range(var):
    """Returns the two dates contained as a low,high tuple"""
    limits = var.split(",")
    if len(limits)==1:
        low = _parse_datetime(limits[0])
        return low, None
    if len(limits)==2:
        low = _parse_datetime(limits[0])
        high = _parse_datetime(limits[1])
        return low, high
    return None, None

def cli_quick_match_all_recids(options):
    """Return an quickly an approximate but (by excess) list of good recids."""
    url = getattr(options, 'url', None)
    if url:
        return intbitset([decompose_bibdocfile_url(url)[0]])
    path = getattr(options, 'path', None)
    if path:
        docid = decompose_bibdocfile_fullpath(path)["doc_id"]
        bd = BibDoc(docid)
        ids = []
        for rec_link in bd.bibrec_links:
            ids.append(rec_link["recid"])
        return intbitset(ids)
    docids = getattr(options, 'docids', None)
    if docids:
        ids = []
        for docid in docids:
            bd = BibDoc(docid)
            for rec_link in bd.bibrec_links:
                ids.append(rec_link["recid"])
        return intbitset(ids)



    collection = getattr(options, 'collection', None)
    pattern = getattr(options, 'pattern', None)
    recids = getattr(options, 'recids', None)
    md_rec = getattr(options, 'md_rec', None)
    cd_rec = getattr(options, 'cd_rec', None)
    tmp_date_query = []
    tmp_date_params = []
    if recids is None:
        debug('Initially considering all the recids')
        recids = intbitset(run_sql('SELECT id FROM bibrec'))
        if not recids:
            print('WARNING: No record in the database', file=sys.stderr)
    if md_rec[0] is not None:
        tmp_date_query.append('modification_date>=%s')
        tmp_date_params.append(md_rec[0])
    if md_rec[1] is not None:
        tmp_date_query.append('modification_date<=%s')
        tmp_date_params.append(md_rec[1])
    if cd_rec[0] is not None:
        tmp_date_query.append('creation_date>=%s')
        tmp_date_params.append(cd_rec[0])
    if cd_rec[1] is not None:
        tmp_date_query.append('creation_date<=%s')
        tmp_date_params.append(cd_rec[1])
    if tmp_date_query:
        tmp_date_query = ' AND '.join(tmp_date_query)
        tmp_date_params = tuple(tmp_date_params)
        query = 'SELECT id FROM bibrec WHERE %s' % tmp_date_query
        debug('Query: %s, param: %s' % (query, tmp_date_params))
        recids &= intbitset(run_sql(query % tmp_date_query, tmp_date_params))
        debug('After applying dates we obtain recids: %s' % recids)
        if not recids:
            print('WARNING: Time constraints for records are too strict', file=sys.stderr)
    if collection or pattern:
        recids &= intbitset(perform_request_search(cc=collection or '', p=pattern or ''))
        debug('After applyings pattern and collection we obtain recids: %s' % recids)
    debug('Quick recids: %s' % recids)
    return recids

def cli_quick_match_all_docids(options, recids=None):
    """Return an quickly an approximate but (by excess) list of good docids."""
    url = getattr(options, 'url', None)
    if url:
        return intbitset([bibdocfile_url_to_bibdoc(url).get_id()])
    path = getattr(options, 'path', None)
    if path:
        docid = decompose_bibdocfile_fullpath(path)["doc_id"]
        bd = BibDoc(docid)
        ids = []
        for rec_link in bd.bibrec_links:
            ids.append(rec_link["recid"])
        return intbitset(ids)

    deleted_docs = getattr(options, 'deleted_docs', None)
    action_undelete = getattr(options, 'action', None) == 'undelete'
    docids = getattr(options, 'docids', None)
    md_doc = getattr(options, 'md_doc', None)
    cd_doc = getattr(options, 'cd_doc', None)
    if docids is None:
        debug('Initially considering all the docids')
        if recids is None:
            recids = cli_quick_match_all_recids(options)
        docids = intbitset()
        for id_bibrec, id_bibdoc in run_sql('SELECT id_bibrec, id_bibdoc FROM bibrec_bibdoc'):
            if id_bibrec in recids:
                docids.add(id_bibdoc)
    else:
        debug('Initially considering this docids: %s' % docids)
    tmp_query = []
    tmp_params = []
    if deleted_docs is None and action_undelete:
        deleted_docs = 'only'
    if deleted_docs == 'no':
        tmp_query.append("status<>'DELETED'")
    elif deleted_docs == 'only':
        tmp_query.append("status='DELETED'")
    if md_doc[0] is not None:
        tmp_query.append('modification_date>=%s')
        tmp_params.append(md_doc[0])
    if md_doc[1] is not None:
        tmp_query.append('modification_date<=%s')
        tmp_params.append(md_doc[1])
    if cd_doc[0] is not None:
        tmp_query.append('creation_date>=%s')
        tmp_params.append(cd_doc[0])
    if cd_doc[1] is not None:
        tmp_query.append('creation_date<=%s')
        tmp_params.append(cd_doc[1])
    if tmp_query:
        tmp_query = ' AND '.join(tmp_query)
        tmp_params = tuple(tmp_params)
        query = 'SELECT id FROM bibdoc WHERE %s' % tmp_query
        debug('Query: %s, param: %s' % (query, tmp_params))
        docids &= intbitset(run_sql(query, tmp_params))
        debug('After applying dates we obtain docids: %s' % docids)
    return docids

def cli_slow_match_single_recid(options, recid, docids=None):
    """Apply all the given queries in order to assert wethever a recid
    match or not.
    if with_docids is True, the recid is matched if it has at least one docid that is matched"""
    debug('cli_slow_match_single_recid checking: %s' % recid)
    deleted_docs = getattr(options, 'deleted_docs', None)
    deleted_recs = getattr(options, 'deleted_recs', None)
    empty_recs = getattr(options, 'empty_recs', None)
    docname = cli2docname(options)
    bibrecdocs = BibRecDocs(recid, deleted_too=(deleted_docs != 'no'))
    if bibrecdocs.deleted_p() and (deleted_recs == 'no'):
        return False
    elif not bibrecdocs.deleted_p() and (deleted_recs != 'only'):
        if docids:
            for bibdoc in bibrecdocs.list_bibdocs():
                if bibdoc.get_id() in docids:
                    break
            else:
                return False
        if docname:
            for other_docname in bibrecdocs.get_bibdoc_names():
                if docname and fnmatch.fnmatchcase(other_docname, docname):
                    break
            else:
                return False
        if bibrecdocs.empty_p() and (empty_recs != 'no'):
            return True
        elif not bibrecdocs.empty_p() and (empty_recs != 'only'):
            return True
    return False

def cli_slow_match_single_docid(options, docid, recids=None):
    """Apply all the given queries in order to assert wethever a recid
    match or not."""

    debug('cli_slow_match_single_docid checking: %s' % docid)
    empty_docs = getattr(options, 'empty_docs', None)
    docname = cli2docname(options)
    if recids is None:
        recids = cli_quick_match_all_recids(options)
    bibdoc = BibDoc.create_instance(docid)
    dn = None
    if bibdoc.bibrec_links:
        dn = bibdoc.bibrec_links[0]["docname"]
    if docname and not fnmatch.fnmatchcase(dn, docname):
        debug('docname %s does not match the pattern %s' % (repr(dn), repr(docname)))
        return False

#    elif bibdoc.get_recid() and bibdoc.get_recid() not in recids:
#        debug('recid %s is not in pattern %s' % (repr(bibdoc.get_recid()), repr(recids)))
#        return False

    elif empty_docs == 'no' and bibdoc.empty_p():
        debug('bibdoc is empty')
        return False
    elif empty_docs == 'only' and not bibdoc.empty_p():
        debug('bibdoc is not empty')
        return False
    else:
        return True

def cli2recid(options, recids=None, docids=None):
    """Given the command line options return a recid."""
    recids = list(cli_recids_iterator(options, recids=recids, docids=docids))
    if len(recids) == 1:
        return recids[0]
    if recids:
        raise StandardError, "More than one recid has been matched: %s" % recids
    else:
        raise StandardError, "No recids matched"

def cli2docid(options, recids=None, docids=None):
    """Given the command line options return a docid."""
    docids = list(cli_docids_iterator(options, recids=recids, docids=docids))
    if len(docids) == 1:
        return docids[0]
    if docids:
        raise StandardError, "More than one docid has been matched: %s" % docids
    else:
        raise StandardError, "No docids matched"

def cli2flags(options):
    """
    Transform a comma separated list of flags into a list of valid flags.
    """
    flags = getattr(options, 'flags', None)
    if flags:
        flags = [flag.strip().upper() for flag in flags.split(',')]
        for flag in flags:
            if flag not in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
                raise StandardError("%s is not among the valid flags: %s" % (flag, ', '.join(CFG_BIBDOCFILE_AVAILABLE_FLAGS)))
        return flags
    return []

def cli2description(options):
    """Return a good value for the description."""
    description = getattr(options, 'set_description', None)
    if description is None:
        description = KEEP_OLD_VALUE
    return description

def cli2restriction(options):
    """Return a good value for the restriction."""
    restriction = getattr(options, 'set_restriction', None)
    if restriction is None:
        restriction = KEEP_OLD_VALUE
    return restriction

def cli2comment(options):
    """Return a good value for the comment."""
    comment = getattr(options, 'set_comment', None)
    if comment is None:
        comment = KEEP_OLD_VALUE
    return comment

def cli2doctype(options):
    """Return a good value for the doctype."""
    doctype = getattr(options, 'set_doctype', None)
    if not doctype:
        return 'Main'
    return doctype

def cli2docname(options, url=None):
    """Given the command line options and optional precalculated docid
    returns the corresponding docname."""
    docname = getattr(options, 'docname', None)
    if docname is not None:
        return docname
    if url is not None:
        return get_docname_from_url(url)
    else:
        return None

def cli2format(options, url=None):
    """Given the command line options returns the corresponding format."""
    docformat = getattr(options, 'format', None)
    if docformat is not None:
        return docformat
    elif url is not None:
        ## FIXME: to deploy once conversion-tools branch is merged
        #return guess_format_from_url(url)
        return guess_format_from_url(url)
    else:
        raise OptionValueError("Not enough information to retrieve a valid format")

def cli_recids_iterator(options, recids=None, docids=None):
    """Slow iterator over all the matched recids.
    if with_docids is True, the recid must be attached to at least a matched docid"""
    debug('cli_recids_iterator')
    if recids is None:
        recids = cli_quick_match_all_recids(options)
    debug('working on recids: %s, docids: %s' % (recids, docids))
    for recid in recids:
        if cli_slow_match_single_recid(options, recid, docids):
            yield recid
    raise StopIteration

def cli_docids_iterator(options, recids=None, docids=None):
    """Slow iterator over all the matched docids."""
    if recids is None:
        recids = cli_quick_match_all_recids(options)
    if docids is None:
        docids = cli_quick_match_all_docids(options, recids)
    for docid in docids:
        if cli_slow_match_single_docid(options, docid, recids):
            yield docid
    raise StopIteration

def cli_get_stats(dummy):
    """Print per every collection some stats"""
    def print_table(title, table):
        if table:
            print("=" * 20, title, "=" * 20)
            for row in table:
                print("\t".join(str(elem) for elem in row))

    from invenio.modules.collections.cache import get_collection_reclist
    for collection, in run_sql("SELECT name FROM collection ORDER BY name"):
        print("-" * 79)
        print("Statistic for: %s " % collection)
        reclist = get_collection_reclist(collection)
        if reclist:
            sqlreclist = "(" + ','.join(str(elem) for elem in reclist) + ')'
            print_table("Formats", run_sql("SELECT COUNT(format) as c, format FROM bibrec_bibdoc AS bb JOIN bibdocfsinfo AS fs ON bb.id_bibdoc=fs.id_bibdoc WHERE id_bibrec in %s AND last_version=true GROUP BY format ORDER BY c DESC" % sqlreclist)) # kwalitee: disable=sql
            print_table("Mimetypes", run_sql("SELECT COUNT(mime) as c, mime FROM bibrec_bibdoc AS bb JOIN bibdocfsinfo AS fs ON bb.id_bibdoc=fs.id_bibdoc WHERE id_bibrec in %s AND last_version=true GROUP BY mime ORDER BY c DESC" % sqlreclist)) # kwalitee: disable=sql
            print_table("Sizes", run_sql("SELECT SUM(filesize) AS c FROM bibrec_bibdoc AS bb JOIN bibdocfsinfo AS fs ON bb.id_bibdoc=fs.id_bibdoc WHERE id_bibrec in %s AND last_version=true" % sqlreclist)) # kwalitee: disable=sql

class OptionParserSpecial(OptionParser):
    def format_help(self, *args, **kwargs):
        result = OptionParser.format_help(self, *args, **kwargs)
        if hasattr(self, 'trailing_text'):
            return "%s\n%s\n" % (result, self.trailing_text)
        else:
            return result

def prepare_option_parser():
    """Parse the command line options."""

    def _ids_ranges_callback(option, opt, value, parser):
        """Callback for optparse to parse a set of ids ranges in the form
        nnn1-nnn2,mmm1-mmm2... returning the corresponding intbitset.
        """
        try:
            debug('option: %s, opt: %s, value: %s, parser: %s' % (option, opt, value, parser))
            debug('Parsing range: %s' % value)
            value = ranges2ids(value)
            setattr(parser.values, option.dest, value)
        except Exception as e:
            raise OptionValueError("It's impossible to parse the range '%s' for option %s: %s" % (value, opt, e))

    def _date_range_callback(option, opt, value, parser):
        """Callback for optparse to parse a range of dates in the form
        [date1],[date2]. Both date1 and date2 could be optional.
        the date can be expressed absolutely ("%Y-%m-%d %H:%M:%S")
        or relatively (([-\+]{0,1})([\d]+)([dhms])) to the current time."""
        try:
            value = _parse_date_range(value)
            setattr(parser.values, option.dest, value)
        except Exception as e:
            raise OptionValueError("It's impossible to parse the range '%s' for option %s: %s" % (value, opt, e))

    parser = OptionParserSpecial(usage="usage: %prog [options]",
    #epilog="""With <query> you select the range of record/docnames/single files to work on. Note that some actions e.g. delete, append, revise etc. works at the docname level, while others like --set-comment, --set-description, at single file level and other can be applied in an iterative way to many records in a single run. Note that specifing docid(2) takes precedence over recid(2) which in turns takes precedence over pattern/collection search.""",
        version=__revision__)
    parser.trailing_text = """
Examples:
    $ bibdocfile --append foo.tar.gz --recid=1
    $ bibdocfile --revise http://foo.com?search=123 --with-docname='sam'
            --format=pdf --recid=3 --set-docname='pippo' # revise for record 3
                    # the document sam, renaming it to pippo.
    $ bibdocfile --delete --with-docname="*sam" --all # delete all documents
                                                      # starting ending
                                                      # with "sam"
    $ bibdocfile --undelete -c "Test Collection" # undelete documents for
                                                 # the collection
    $ bibdocfile --get-info --recids=1-4,6-8 # obtain informations
    $ bibdocfile -r 1 --with-docname=foo --set-docname=bar # Rename a document
    $ bibdocfile -r 1 --set-restriction "firerole: deny until '2011-01-01'
    allow any" # set an embargo to all the documents attached to record 1
        # (note the ^M or \\n before 'allow any')
        # See also $r subfield in <%(site)s/help/admin/bibupload-admin-guide#3.6>
        # and Firerole in <%(site)s/help/admin/webaccess-admin-guide#6>
    $ bibdocfile --append x.pdf --recid=1 --with-flags='PDF/A,OCRED' # append
        # to record 1 the file x.pdf specifying the PDF/A and OCRED flags
    """ % {'site': CFG_SITE_URL}
    query_options = OptionGroup(parser, 'Query options')

    query_options.add_option('-r', '--recids', action="callback", callback=_ids_ranges_callback, type='string', dest='recids', help='matches records by recids, e.g.: --recids=1-3,5-7')
    query_options.add_option('-d', '--docids', action="callback", callback=_ids_ranges_callback, type='string', dest='docids', help='matches documents by docids, e.g.: --docids=1-3,5-7')
    query_options.add_option('-a', '--all', action='store_true', dest='all', help='Select all the records')
    query_options.add_option("--with-deleted-recs", choices=['yes', 'no', 'only'], type="choice", dest="deleted_recs", help="'Yes' to also match deleted records, 'no' to exclude them, 'only' to match only deleted ones", metavar="yes/no/only", default='no')
    query_options.add_option("--with-deleted-docs", choices=['yes', 'no', 'only'], type="choice", dest="deleted_docs", help="'Yes' to also match deleted documents, 'no' to exclude them, 'only' to match only deleted ones (e.g. for undeletion)", metavar="yes/no/only", default='no')
    query_options.add_option("--with-empty-recs", choices=['yes', 'no', 'only'], type="choice", dest="empty_recs", help="'Yes' to also match records without attached documents, 'no' to exclude them, 'only' to consider only such records (e.g. for statistics)", metavar="yes/no/only", default='no')
    query_options.add_option("--with-empty-docs", choices=['yes', 'no', 'only'], type="choice", dest="empty_docs", help="'Yes' to also match documents without attached files, 'no' to exclude them, 'only' to consider only such documents (e.g. for sanity checking)", metavar="yes/no/only", default='no')
    query_options.add_option("--with-record-modification-date", action="callback", callback=_date_range_callback, dest="md_rec", nargs=1, type="string", default=(None, None), help="matches records modified date1 and date2; dates can be expressed relatively, e.g.:\"-5m,2030-2-23 04:40\" # matches records modified since 5 minutes ago until the 2030...", metavar="date1,date2")
    query_options.add_option("--with-record-creation-date", action="callback", callback=_date_range_callback, dest="cd_rec", nargs=1, type="string", default=(None, None), help="matches records created between date1 and date2; dates can be expressed relatively", metavar="date1,date2")
    query_options.add_option("--with-document-modification-date", action="callback", callback=_date_range_callback, dest="md_doc", nargs=1, type="string", default=(None, None), help="matches documents modified between date1 and date2; dates can be expressed relatively", metavar="date1,date2")
    query_options.add_option("--with-document-creation-date", action="callback", callback=_date_range_callback, dest="cd_doc", nargs=1, type="string", default=(None, None), help="matches documents created between date1 and date2; dates can be expressed relatively", metavar="date1,date2")
    query_options.add_option("--url", dest="url", help='matches the document referred by the URL, e.g. "%s/%s/1/files/foobar.pdf?version=2"' % (CFG_SITE_URL, CFG_SITE_RECORD))
    query_options.add_option("--path", dest="path", help='matches the document referred by the internal filesystem path, e.g. %s/g0/1/foobar.pdf\\;1' % CFG_BIBDOCFILE_FILEDIR)
    query_options.add_option("--with-docname", dest="docname", help='matches documents with the given docname (accept wildcards)')
    query_options.add_option("--with-doctype", dest="doctype", help='matches documents with the given doctype')
    query_options.add_option('-p', '--pattern', dest='pattern', help='matches records by pattern')
    query_options.add_option('-c', '--collection', dest='collection', help='matches records by collection')
    query_options.add_option('--force', dest='force', help='force an action even when it\'s not necessary e.g. textify on an already textified bibdoc.', action='store_true', default=False)
    parser.add_option_group(query_options)

    getting_information_options = OptionGroup(parser, 'Actions for getting information')
    getting_information_options.add_option('--get-info', dest='action', action='store_const', const='get-info', help='print all the informations about the matched record/documents')
    getting_information_options.add_option('--get-disk-usage', dest='action', action='store_const', const='get-disk-usage', help='print disk usage statistics of the matched documents')
    getting_information_options.add_option('--get-history', dest='action', action='store_const', const='get-history', help='print the matched documents history')
    getting_information_options.add_option('--get-stats', dest='action', action='store_const', const='get-stats', help='print some statistics of file properties grouped by collections')
    parser.add_option_group(getting_information_options)

    setting_information_options = OptionGroup(parser, 'Actions for setting information')
    setting_information_options.add_option('--set-doctype', dest='set_doctype', help='specify the new doctype', metavar='doctype')
    setting_information_options.add_option('--set-description', dest='set_description', help='specify a description', metavar='description')
    setting_information_options.add_option('--set-comment', dest='set_comment', help='specify a comment', metavar='comment')
    setting_information_options.add_option('--set-restriction', dest='set_restriction', help='specify a restriction tag', metavar='restriction')
    setting_information_options.add_option('--set-docname', dest='new_docname', help='specifies a new docname for renaming', metavar='docname')
    setting_information_options.add_option("--unset-comment", action="store_const", const='', dest="set_comment", help="remove any comment")
    setting_information_options.add_option("--unset-descriptions", action="store_const", const='', dest="set_description", help="remove any description")
    setting_information_options.add_option("--unset-restrictions", action="store_const", const='', dest="set_restriction", help="remove any restriction")
    setting_information_options.add_option("--hide", dest="action", action='store_const', const='hide', help="hides matched documents and revisions")
    setting_information_options.add_option("--unhide", dest="action", action='store_const', const='unhide', help="hides matched documents and revisions")
    parser.add_option_group(setting_information_options)

    revising_options = OptionGroup(parser, 'Action for revising content')
    revising_options.add_option("--append", dest='append_path', help='specify the URL/path of the file that will appended to the bibdoc (implies --with-empty-recs=yes)', metavar='PATH/URL')
    revising_options.add_option("--revise", dest='revise_path', help='specify the URL/path of the file that will revise the bibdoc', metavar='PATH/URL')
    revising_options.add_option("--revert", dest='action', action='store_const', const='revert', help='reverts a document to the specified version')
    revising_options.add_option("--delete", action='store_const', const='delete', dest='action', help='soft-delete the matched documents')
    revising_options.add_option("--hard-delete", action='store_const', const='hard-delete', dest='action', help='hard-delete the single matched document with a specific format and a specific revision (this operation is not revertible)')
    revising_options.add_option("--undelete", action='store_const', const='undelete', dest='action', help='undelete previosuly soft-deleted documents')
    revising_options.add_option("--purge", action='store_const', const='purge', dest='action', help='purge (i.e. hard-delete any format of any version prior to the latest version of) the matched documents')
    revising_options.add_option("--expunge", action='store_const', const='expunge', dest='action', help='expunge (i.e. hard-delete any version and formats of) the matched documents')
    revising_options.add_option("--with-version", dest="version", help="specifies the version(s) to be used with hide, unhide, e.g.: 1-2,3 or ALL. Specifies the version to be used with hard-delete and revert, e.g. 2")
    revising_options.add_option("--with-format", dest="format", help='to specify a format when appending/revising/deleting/reverting a document, e.g. "pdf"', metavar='FORMAT')
    revising_options.add_option("--with-hide-previous", dest='hide_previous', action='store_true', help='when revising, hides previous versions', default=False)
    revising_options.add_option("--with-flags", dest='flags', help='comma-separated optional list of flags used when appending/revising a document. Valid flags are: %s' % ', '.join(CFG_BIBDOCFILE_AVAILABLE_FLAGS), default=None)
    parser.add_option_group(revising_options)

    housekeeping_options = OptionGroup(parser, 'Actions for housekeeping')
    housekeeping_options.add_option("--check-md5", action='store_const', const='check-md5', dest='action', help='check md5 checksum validity of files')
    housekeeping_options.add_option("--check-format", action='store_const', const='check-format', dest='action', help='check if any format-related inconsistences exists')
    housekeeping_options.add_option("--check-duplicate-docnames", action='store_const', const='check-duplicate-docnames', dest='action', help='check for duplicate docnames associated with the same record')
    housekeeping_options.add_option("--update-md5", action='store_const', const='update-md5', dest='action', help='update md5 checksum of files')
    housekeeping_options.add_option("--fix-all", action='store_const', const='fix-all', dest='action', help='fix inconsistences in filesystem vs database vs MARC')
    housekeeping_options.add_option("--fix-marc", action='store_const', const='fix-marc', dest='action', help='synchronize MARC after filesystem/database')
    housekeeping_options.add_option("--fix-format", action='store_const', const='fix-format', dest='action', help='fix format related inconsistences')
    housekeeping_options.add_option("--fix-duplicate-docnames", action='store_const', const='fix-duplicate-docnames', dest='action', help='fix duplicate docnames associated with the same record')
    housekeeping_options.add_option("--fix-bibdocfsinfo-cache", action='store_const', const='fix-bibdocfsinfo-cache', dest='action', help='fix bibdocfsinfo cache related inconsistences')
    parser.add_option_group(housekeeping_options)

    experimental_options = OptionGroup(parser, 'Experimental options (do not expect to find them in the next release)')
    experimental_options.add_option('--textify', dest='action', action='store_const', const='textify', help='extract text from matched documents and store it for later indexing')
    experimental_options.add_option('--with-ocr', dest='perform_ocr', action='store_true', default=False, help='when used with --textify, wether to perform OCR')
    parser.add_option_group(experimental_options)

    parser.add_option('-D', '--debug', action='store_true', dest='debug', default=False)
    parser.add_option('-H', '--human-readable', dest='human_readable', action='store_true', default=False, help='print sizes in human readable format (e.g., 1KB 234MB 2GB)')
    parser.add_option('--yes-i-know', action='store_true', dest='yes-i-know', help='use with care!')
    return parser

def print_info(docid, info):
    """Nicely print info about a docid."""
    print('%i:%s' % (docid, info))

def bibupload_ffts(ffts, append=False, do_debug=False, interactive=True):
    """Given an ffts dictionary it creates the xml and submit it."""
    xml = ffts_to_xml(ffts)
    if xml:
        if interactive:
            print(xml)
        tmp_file_fd, tmp_file_name = retry_mkstemp(suffix='.xml',
                                                   prefix="bibdocfile_%s" % time.strftime("%Y-%m-%d_%H:%M:%S"),
                                                   directory=CFG_TMPSHAREDDIR)
        os.write(tmp_file_fd, xml)
        os.close(tmp_file_fd)
        os.chmod(tmp_file_name, 0o644)
        if append:
            if interactive:
                wait_for_user("This will be appended via BibUpload")
            if do_debug:
                task = task_low_level_submission('bibupload', 'bibdocfile', '-a', tmp_file_name, '-N', 'FFT', '-S2', '-v9')
            else:
                task = task_low_level_submission('bibupload', 'bibdocfile', '-a', tmp_file_name, '-N', 'FFT', '-S2')
            if interactive:
                print("BibUpload append submitted with id %s" % task)
        else:
            if interactive:
                wait_for_user("This will be corrected via BibUpload")
            if do_debug:
                task = task_low_level_submission('bibupload', 'bibdocfile', '-c', tmp_file_name, '-N', 'FFT', '-S2', '-v9')
            else:
                task = task_low_level_submission('bibupload', 'bibdocfile', '-c', tmp_file_name, '-N', 'FFT', '-S2')
            if interactive:
                print("BibUpload correct submitted with id %s" % task)
    elif interactive:
        print("WARNING: no MARC to upload.", file=sys.stderr)
    return True

def ranges2ids(parse_string):
    """Parse a string and return the intbitset of the corresponding ids."""
    ids = intbitset()
    ranges = parse_string.split(",")
    for arange in ranges:
        tmp_ids = arange.split("-")
        if len(tmp_ids)==1:
            ids.add(int(tmp_ids[0]))
        else:
            if int(tmp_ids[0]) > int(tmp_ids[1]): # sanity check
                tmp = tmp_ids[0]
                tmp_ids[0] = tmp_ids[1]
                tmp_ids[1] = tmp
            ids += xrange(int(tmp_ids[0]), int(tmp_ids[1]) + 1)
    return ids

def cli_append(options, append_path):
    """Create a bibupload FFT task submission for appending a format."""
    recid = cli2recid(options)
    comment = cli2comment(options)
    description = cli2description(options)
    restriction = cli2restriction(options)
    doctype = cli2doctype(options)
    docname = cli2docname(options, url=append_path)
    flags = cli2flags(options)
    if not docname:
        raise OptionValueError, 'Not enough information to retrieve a valid docname'
    docformat = cli2format(options, append_path)
    url = clean_url(append_path)
    check_valid_url(url)
    bibrecdocs = BibRecDocs(recid)
    if bibrecdocs.has_docname_p(docname) and bibrecdocs.get_bibdoc(docname).format_already_exists_p(docformat):
        new_docname = bibrecdocs.propose_unique_docname(docname)
        wait_for_user("WARNING: a document with name %s and format %s already exists for recid %s. A new document with name %s will be created instead." % (repr(docname), repr(docformat), repr(recid), repr(new_docname)))
        docname = new_docname
    ffts = {recid: [{
        'docname' : docname,
        'comment' : comment,
        'description' : description,
        'restriction' : restriction,
        'doctype' : doctype,
        'format' : docformat,
        'url' : url,
        'options': flags
    }]}
    return bibupload_ffts(ffts, append=True)

def cli_revise(options, revise_path):
    """Create aq bibupload FFT task submission for appending a format."""
    recid = cli2recid(options)
    comment = cli2comment(options)
    description = cli2description(options)
    restriction = cli2restriction(options)
    docname = cli2docname(options, url=revise_path)
    hide_previous = getattr(options, 'hide_previous', None)
    flags = cli2flags(options)
    if hide_previous and 'PERFORM_HIDE_PREVIOUS' not in flags:
        flags.append('PERFORM_HIDE_PREVIOUS')
    if not docname:
        raise OptionValueError, 'Not enough information to retrieve a valid docname'
    docformat = cli2format(options, revise_path)
    doctype = cli2doctype(options)
    url = clean_url(revise_path)
    new_docname = getattr(options, 'new_docname', None)
    check_valid_url(url)
    ffts = {recid : [{
        'docname' : docname,
        'new_docname' : new_docname,
        'comment' : comment,
        'description' : description,
        'restriction' : restriction,
        'doctype' : doctype,
        'format' : docformat,
        'url' : url,
        'options' : flags
    }]}
    return bibupload_ffts(ffts)

def cli_set_batch(options):
    """Change in batch the doctype, description, comment and restriction."""
    ffts = {}
    doctype = getattr(options, 'set_doctype', None)
    description = cli2description(options)
    comment = cli2comment(options)
    restriction = cli2restriction(options)
    with_format = getattr(options, 'format', None)
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        recid = None
        docname = None
        if bibdoc.bibrec_links:
            # pick a sample recid from those to which a BibDoc is attached
            recid = bibdoc.bibrec_links[0]["recid"]
            docname = bibdoc.bibrec_links[0]["docname"]

        fft = []
        if description is not None or comment is not None:
            for bibdocfile in bibdoc.list_latest_files():
                docformat = bibdocfile.get_format()
                if not with_format or with_format == format:
                    fft.append({
                        'docname': docname,
                        'restriction': restriction,
                        'comment': comment,
                        'description': description,
                        'format': docformat,
                        'doctype': doctype
                    })
        else:
            fft.append({
                'docname': docname,
                'restriction': restriction,
                'doctype': doctype,
            })
        ffts[recid] = fft
    return bibupload_ffts(ffts, append=False)

def cli_textify(options):
    """Extract text to let indexing on fulltext be possible."""
    force = getattr(options, 'force', None)
    perform_ocr = getattr(options, 'perform_ocr', None)
    if perform_ocr:
        if not can_perform_ocr():
            print("WARNING: OCR requested but OCR is not possible", file=sys.stderr)
            perform_ocr = False
    if perform_ocr:
        additional = ' using OCR (this might take some time)'
    else:
        additional = ''
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        print('Extracting text for docid %s%s...' % (docid, additional), end=' ')
        sys.stdout.flush()
        #pylint: disable=E1103
        if force or (hasattr(bibdoc, "has_text") and not bibdoc.has_text(require_up_to_date=True)):
            try:
                #pylint: disable=E1103
                bibdoc.extract_text(perform_ocr=perform_ocr)
                print("DONE")
            except InvenioBibDocFileError as e:
                print("WARNING: %s" % e, file=sys.stderr)
        else:
            print("not needed")

def cli_rename(options):
    """Rename a docname within a recid."""
    new_docname = getattr(options, 'new_docname', None)
    docid = cli2docid(options)
    bibdoc = BibDoc.create_instance(docid)
    docname = None
    if bibdoc.bibrec_links:
        docname = bibdoc.bibrec_links[0]["docname"]

    recid = cli2recid(options) # now we read the recid from options
    ffts = {recid : [{'docname' : docname, 'new_docname' : new_docname}]}
    return bibupload_ffts(ffts, append=False)

def cli_fix_bibdocfsinfo_cache(options):
    """Rebuild the bibdocfsinfo table according to what is available on filesystem"""
    to_be_fixed = intbitset()
    for docid in intbitset(run_sql("SELECT id FROM bibdoc")):
        print("Fixing bibdocfsinfo table for docid %s..." % docid, end=' ')
        sys.stdout.flush()
        try:
            bibdoc = BibDoc(docid)
        except InvenioBibDocFileError as err:
            print(err)
            continue
        try:
            bibdoc._sync_to_db()
        except Exception as err:
            if bibdoc.bibrec_links:
                recid = bibdoc.bibrec_links[0]["recid"]
                if recid:
                    to_be_fixed.add(recid)
                print("ERROR: %s, scheduling a fix for recid %s" % (err, recid))
            else:
                print("ERROR %s" % (err, ))
        print("DONE")
    if to_be_fixed:
        cli_fix_format(options, recids=to_be_fixed)
    print("You can now add CFG_BIBDOCFILE_ENABLE_BIBDOCFSINFO_CACHE=1 to your invenio-local.conf file.")

def cli_fix_all(options):
    """Fix all the records of a recid_set."""
    ffts = {}
    for recid in cli_recids_iterator(options):
        ffts[recid] = []
        for docname in BibRecDocs(recid).get_bibdoc_names():
            ffts[recid].append({'docname' : docname, 'doctype' : 'FIX-ALL'})
    return bibupload_ffts(ffts, append=False)

def cli_fix_marc(options, explicit_recid_set=None, interactive=True):
    """Fix all the records of a recid_set."""
    ffts = {}
    if explicit_recid_set is not None:
        for recid in explicit_recid_set:
            ffts[recid] = [{'doctype' : 'FIX-MARC'}]
    else:
        for recid in cli_recids_iterator(options):
            ffts[recid] = [{'doctype' : 'FIX-MARC'}]
    return bibupload_ffts(ffts, append=False, interactive=interactive)

def cli_check_format(options):
    """Check if any format-related inconsistences exists."""
    count = 0
    tot = 0
    duplicate = False
    for recid in cli_recids_iterator(options):
        tot += 1
        bibrecdocs = BibRecDocs(recid)
        if not bibrecdocs.check_duplicate_docnames():
            print("recid %s has duplicate docnames!" % recid, file=sys.stderr)
            broken = True
            duplicate = True
        else:
            broken = False
        for docname in bibrecdocs.get_bibdoc_names():
            if not bibrecdocs.check_format(docname):
                print("recid %s with docname %s need format fixing" % (recid, docname), file=sys.stderr)
                broken = True
        if broken:
            count += 1
    if count:
        result = "%d out of %d records need their formats to be fixed." % (count, tot)
    else:
        result = "All records appear to be correct with respect to formats."
    if duplicate:
        result += " Note however that at least one record appear to have duplicate docnames. You should better fix this situation by using --fix-duplicate-docnames."
    print(wrap_text_in_a_box(result, style="conclusion"))
    return not(duplicate or count)

def cli_check_duplicate_docnames(options):
    """Check if some record is connected with bibdoc having the same docnames."""
    count = 0
    tot = 0
    for recid in cli_recids_iterator(options):
        tot += 1
        bibrecdocs = BibRecDocs(recid)
        if not bibrecdocs.check_duplicate_docnames():
            count += 1
            print("recid %s has duplicate docnames!" % recid, file=sys.stderr)
    if count:
        print("%d out of %d records have duplicate docnames." % (count, tot))
        return False
    else:
        print("All records appear to be correct with respect to duplicate docnames.")
        return True

def cli_fix_format(options, recids=None):
    """Fix format-related inconsistences."""
    fixed = intbitset()
    tot = 0
    if not recids:
        recids = cli_recids_iterator(options)
    for recid in recids:
        tot += 1
        bibrecdocs = BibRecDocs(recid)
        for docname in bibrecdocs.get_bibdoc_names():
            if not bibrecdocs.check_format(docname):
                if bibrecdocs.fix_format(docname, skip_check=True):
                    print("%i has been fixed for docname %s" % (recid, docname), file=sys.stderr)
                else:
                    print("%i has been fixed for docname %s. However note that a new bibdoc might have been created." % (recid, docname), file=sys.stderr)
                fixed.add(recid)
    if fixed:
        print("Now we need to synchronize MARC to reflect current changes.")
        cli_fix_marc(options, explicit_recid_set=fixed)

    print(wrap_text_in_a_box("%i out of %i record needed to be fixed." % (tot, len(fixed)), style="conclusion"))
    return not fixed

def cli_fix_duplicate_docnames(options):
    """Fix duplicate docnames."""
    fixed = intbitset()
    tot = 0
    for recid in cli_recids_iterator(options):
        tot += 1
        bibrecdocs = BibRecDocs(recid)
        if not bibrecdocs.check_duplicate_docnames():
            bibrecdocs.fix_duplicate_docnames(skip_check=True)
            print("%i has been fixed for duplicate docnames." % recid, file=sys.stderr)
            fixed.add(recid)
    if fixed:
        print("Now we need to synchronize MARC to reflect current changes.")
        cli_fix_marc(options, explicit_recid_set=fixed)
    print(wrap_text_in_a_box("%i out of %i record needed to be fixed." % (len(fixed), tot), style="conclusion"))
    return not fixed

def cli_delete(options):
    """Delete the given docid_set."""
    ffts = {}
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        docname = None
        recid = None
        # retrieve the 1st recid
        if bibdoc.bibrec_links:
            recid = bibdoc.bibrec_links[0]["recid"]
            docname = bibdoc.bibrec_links[0]["docname"]
            ffts.setdefault(recid, []).append(
                {'docname' : docname,
                 'doctype' : 'DELETE'}
            )
    return bibupload_ffts(ffts)

def cli_delete_file(options):
    """Delete the given file irreversibely."""
    docid = cli2docid(options)
    recid = cli2recid(options, docids=intbitset([docid]))
    docformat = cli2format(options)
    bdr = BibRecDocs(recid)
    docname = bdr.get_docname(docid)
    version = getattr(options, 'version', None)
    try:
        version_int = int(version)
        if 0 >= version_int:
            raise ValueError
    except:
        raise OptionValueError, 'when hard-deleting, version should be valid positive integer, not %s' % version
    ffts = {recid : [{'docname' : docname, 'version' : version, 'format' : docformat, 'doctype' : 'DELETE-FILE'}]}
    return bibupload_ffts(ffts)

def cli_revert(options):
    """Revert a bibdoc to a given version."""
    docid = cli2docid(options)
    recid = cli2recid(options, docids=intbitset([docid]))
    bdr = BibRecDocs(recid)
    docname = bdr.get_docname(docid)
    version = getattr(options, 'version', None)
    try:
        version_int = int(version)
        if 0 >= version_int:
            raise ValueError
    except:
        raise OptionValueError, 'when reverting, version should be valid positive integer, not %s' % version
    ffts = {recid : [{'docname' : docname, 'version' : version, 'doctype' : 'REVERT'}]}
    return bibupload_ffts(ffts)

def cli_undelete(options):
    """Delete the given docname"""
    docname = cli2docname(options)
    restriction = getattr(options, 'restriction', None)
    count = 0
    if not docname:
        docname = 'DELETED-*-*'
    if not docname.startswith('DELETED-'):
        docname = 'DELETED-*-' + docname
    to_be_undeleted = intbitset()
    fix_marc = intbitset()
    setattr(options, 'deleted_docs', 'only')
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        dnold = None
        if bibdoc.bibrec_links:
            dnold = bibdoc.bibrec_links[0]["docname"]
        if bibdoc.get_status() == 'DELETED' and fnmatch.fnmatch(dnold, docname):
            to_be_undeleted.add(docid)
            # get the 1st recid to which the document is attached
            recid = None
            if bibdoc.bibrec_links:
                recid = bibdoc.bibrec_links[0]["recid"]
            fix_marc.add(recid)
            count += 1
            print('%s (docid %s from recid %s) will be undeleted to restriction: %s' % (dnold, docid, recid, restriction))
    wait_for_user("I'll proceed with the undeletion")
    for docid in to_be_undeleted:
        bibdoc = BibDoc.create_instance(docid)
        bibdoc.undelete(restriction)
    cli_fix_marc(options, explicit_recid_set=fix_marc)
    print(wrap_text_in_a_box("%s bibdoc successfuly undeleted with status '%s'" % (count, restriction), style="conclusion"))

def cli_get_info(options):
    """Print all the info of the matched docids or recids."""
    debug('Getting info!')
    human_readable = bool(getattr(options, 'human_readable', None))
    debug('human_readable: %s' % human_readable)
    deleted_docs = getattr(options, 'deleted_docs', None) in ('yes', 'only')
    debug('deleted_docs: %s' % deleted_docs)
    if getattr(options, 'docids', None):
        for docid in cli_docids_iterator(options):
            sys.stdout.write(str(BibDoc.create_instance(docid, human_readable=human_readable)))
    else:
        for recid in cli_recids_iterator(options):
            sys.stdout.write(str(BibRecDocs(recid, deleted_too=deleted_docs, human_readable=human_readable)))

def cli_purge(options):
    """Purge the matched docids."""
    ffts = {}
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        recid = None
        docname = None
        if bibdoc.bibrec_links:
            recid = bibdoc.bibrec_links[0]["recid"]
            docname = bibdoc.bibrec_links[0]["docname"]

        if recid:
            if recid not in ffts:
                ffts[recid] = []
            ffts[recid].append({
                'docname' : docname,
                'doctype' : 'PURGE',
            })
    return bibupload_ffts(ffts)

def cli_expunge(options):
    """Expunge the matched docids."""
    ffts = {}
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        recid = None
        docname = None
        if bibdoc.bibrec_links:
            #TODO: If we have a syntax for manipulating completely standalone objects,
            # this has to be modified
            recid = bibdoc.bibrec_links[0]["recid"]
            docname = bibdoc.bibrec_links[0]["docname"]

        if recid:
            if recid not in ffts:
                ffts[recid] = []
            ffts[recid].append({
                'docname' : docname,
                'doctype' : 'EXPUNGE',
            })
    return bibupload_ffts(ffts)

def cli_get_history(options):
    """Print the history of a docid_set."""
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        history = bibdoc.get_history()
        for row in history:

            print_info(docid, row)

def cli_get_disk_usage(options):
    """Print the space usage of a docid_set."""
    human_readable = getattr(options, 'human_readable', None)
    total_size = 0
    total_latest_size = 0
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        size = bibdoc.get_total_size()
        total_size += size
        latest_size = bibdoc.get_total_size_latest_version()
        total_latest_size += latest_size
        if human_readable:
            print_info(docid, 'size=%s' % nice_size(size))
            print_info(docid, 'latest version size=%s' % nice_size(latest_size))
        else:
            print_info(docid, 'size=%s' % size)
            print_info( docid, 'latest version size=%s' % latest_size)
    if human_readable:
        print(wrap_text_in_a_box('total size: %s\n\nlatest version total size: %s'
            % (nice_size(total_size), nice_size(total_latest_size)),
            style='conclusion'))
    else:
        print(wrap_text_in_a_box('total size: %s\n\nlatest version total size: %s'
            % (total_size, total_latest_size),
            style='conclusion'))

def cli_check_md5(options):
    """Check the md5 sums of a docid_set."""
    failures = 0
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        if bibdoc.md5s.check():
            print_info(docid, 'checksum OK')
        else:
            for afile in bibdoc.list_all_files():
                if not afile.check():
                    failures += 1
                    print_info(docid, '%s failing checksum!' % afile.get_full_path())
    if failures:
        print(wrap_text_in_a_box('%i files failing' % failures , style='conclusion'))
    else:
        print(wrap_text_in_a_box('All files are correct', style='conclusion'))

def cli_update_md5(options):
    """Update the md5 sums of a docid_set."""
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        if bibdoc.md5s.check():
            print_info(docid, 'checksum OK')
        else:
            for afile in bibdoc.list_all_files():
                if not afile.check():
                    print_info(docid, '%s failing checksum!' % afile.get_full_path())
            wait_for_user('Updating the md5s of this document can hide real problems.')
            bibdoc.md5s.update(only_new=False)
            bibdoc._sync_to_db()


def cli_hide(options):
    """Hide the matched versions of documents."""
    documents_to_be_hidden = {}
    to_be_fixed = intbitset()
    versions = getattr(options, 'version', 'all')
    if versions != 'all':
        try:
            versions = ranges2ids(versions)
        except:
            raise OptionValueError, 'You should specify correct versions. Not %s' % versions
    else:
        versions = intbitset(trailing_bits=True)
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        recid = None
        if bibdoc.bibrec_links:
            recid = bibdoc.bibrec_links[0]["recid"]
        if recid:
            for bibdocfile in bibdoc.list_all_files():
                this_version = bibdocfile.get_version()
                this_format = bibdocfile.get_format()
                if this_version in versions:
                    if docid not in documents_to_be_hidden:
                        documents_to_be_hidden[docid] = []
                    documents_to_be_hidden[docid].append((this_version, this_format))
                    to_be_fixed.add(recid)
                    print('%s (docid: %s, recid: %s) will be hidden' % (bibdocfile.get_full_name(), docid, recid))
    wait_for_user('Proceeding to hide the matched documents...')
    for docid, documents in iteritems(documents_to_be_hidden):
        bibdoc = BibDoc.create_instance(docid)
        for version, docformat in documents:
            bibdoc.set_flag('HIDDEN', docformat, version)
    return cli_fix_marc(options, to_be_fixed)

def cli_unhide(options):
    """Unhide the matched versions of documents."""
    documents_to_be_unhidden = {}
    to_be_fixed = intbitset()
    versions = getattr(options, 'version', 'all')
    if versions != 'all':
        try:
            versions = ranges2ids(versions)
        except:
            raise OptionValueError, 'You should specify correct versions. Not %s' % versions
    else:
        versions = intbitset(trailing_bits=True)
    for docid in cli_docids_iterator(options):
        bibdoc = BibDoc.create_instance(docid)
        recid = None
        if bibdoc.bibrec_links:
            recid = bibdoc.bibrec_links[0]["recid"]
        if recid:
            for bibdocfile in bibdoc.list_all_files():
                this_version = bibdocfile.get_version()
                this_format = bibdocfile.get_format()
                if this_version in versions:
                    if docid not in documents_to_be_unhidden:
                        documents_to_be_unhidden[docid] = []
                    documents_to_be_unhidden[docid].append((this_version, this_format))
                    to_be_fixed.add(recid)
                    print('%s (docid: %s, recid: %s) will be unhidden' % (bibdocfile.get_full_name(), docid, recid))
    wait_for_user('Proceeding to unhide the matched documents...')
    for docid, documents in iteritems(documents_to_be_unhidden):
        bibdoc = BibDoc.create_instance(docid)
        for version, docformat in documents:
            bibdoc.unset_flag('HIDDEN', docformat, version)
    return cli_fix_marc(options, to_be_fixed)


@with_app_context()
def main():
    parser = prepare_option_parser()
    (options, args) = parser.parse_args()
    if getattr(options, 'debug', None):
        getLogger().setLevel(DEBUG)
        debug('test')
    debug('options: %s, args: %s' % (options, args))
    try:
        if not getattr(options, 'action', None) and \
                not getattr(options, 'append_path', None) and \
                not getattr(options, 'revise_path', None):
            if getattr(options, 'set_doctype', None) is not None or \
                    getattr(options, 'set_comment', None) is not None or \
                    getattr(options, 'set_description', None) is not None or \
                    getattr(options, 'set_restriction', None) is not None:
                cli_set_batch(options)
            elif getattr(options, 'new_docname', None):
                cli_rename(options)
            else:
                print("ERROR: no action specified", file=sys.stderr)
                sys.exit(1)
        elif getattr(options, 'append_path', None):
            options.empty_recs = 'yes'
            options.empty_docs = 'yes'
            cli_append(options, getattr(options, 'append_path', None))
        elif getattr(options, 'revise_path', None):
            cli_revise(options, getattr(options, 'revise_path', None))
        elif options.action == 'textify':
            cli_textify(options)
        elif getattr(options, 'action', None) == 'get-history':
            cli_get_history(options)
        elif getattr(options, 'action', None) == 'get-info':
            cli_get_info(options)
        elif getattr(options, 'action', None) == 'get-disk-usage':
            cli_get_disk_usage(options)
        elif getattr(options, 'action', None) == 'check-md5':
            cli_check_md5(options)
        elif getattr(options, 'action', None) == 'update-md5':
            cli_update_md5(options)
        elif getattr(options, 'action', None) == 'fix-all':
            cli_fix_all(options)
        elif getattr(options, 'action', None) == 'fix-marc':
            cli_fix_marc(options)
        elif getattr(options, 'action', None) == 'delete':
            cli_delete(options)
        elif getattr(options, 'action', None) == 'hard-delete':
            cli_delete_file(options)
        elif getattr(options, 'action', None) == 'fix-duplicate-docnames':
            cli_fix_duplicate_docnames(options)
        elif getattr(options, 'action', None) == 'fix-format':
            cli_fix_format(options)
        elif getattr(options, 'action', None) == 'check-duplicate-docnames':
            cli_check_duplicate_docnames(options)
        elif getattr(options, 'action', None) == 'check-format':
            cli_check_format(options)
        elif getattr(options, 'action', None) == 'undelete':
            cli_undelete(options)
        elif getattr(options, 'action', None) == 'purge':
            cli_purge(options)
        elif getattr(options, 'action', None) == 'expunge':
            cli_expunge(options)
        elif getattr(options, 'action', None) == 'revert':
            cli_revert(options)
        elif getattr(options, 'action', None) == 'hide':
            cli_hide(options)
        elif getattr(options, 'action', None) == 'unhide':
            cli_unhide(options)
        elif getattr(options, 'action', None) == 'fix-bibdocfsinfo-cache':
            options.empty_docs = 'yes'
            cli_fix_bibdocfsinfo_cache(options)
        elif getattr(options, 'action', None) == 'get-stats':
            cli_get_stats(options)
        else:
            print("ERROR: Action %s is not valid" % getattr(options, 'action', None), file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        register_exception()
        print('ERROR: %s' % e, file=sys.stderr)
        sys.exit(1)
