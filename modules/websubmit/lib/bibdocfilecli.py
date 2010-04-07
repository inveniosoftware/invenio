# -*- coding: utf-8 -*-
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

import sys
import os
import time
import fnmatch
from optparse import OptionParser, OptionGroup
from tempfile import mkstemp

from invenio.config import CFG_TMPDIR
from invenio.bibdocfile import BibRecDocs, BibDoc, InvenioWebSubmitFileError, \
    nice_size, check_valid_url, clean_url, get_docname_from_url, \
    get_format_from_url, KEEP_OLD_VALUE
from invenio.intbitset import intbitset
from invenio.search_engine import perform_request_search, search_unit
from invenio.textutils import wrap_text_in_a_box, wait_for_user
from invenio.dbquery import run_sql
from invenio.bibtask import task_low_level_submission
from invenio.textutils import encode_for_xml
from invenio.websubmit_file_converter import can_perform_ocr

def _xml_mksubfield(key, subfield, fft):
    return fft.get(key, None) and '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(fft[key])) or ''

def _xml_mksubfields(key, subfield, fft):
    ret = ""
    for value in fft.get(key, []):
        ret += '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(value))
    return ret

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
    out += _xml_mksubfield('comment', 'z', fft)
    out += _xml_mksubfield('restriction', 'r', fft)
    out += _xml_mksubfield('icon', 'x', fft)
    out += _xml_mksubfields('options', 'o', fft)
    out += '\t</datafield>\n'
    return out

def ffts_to_xml(ffts_dict):
    """Transform a dictionary: recid -> ffts where ffts is a list of fft dictionary
    into xml.
    """
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
    return out

_actions = [('get-info', 'print all the informations about the record/bibdoc/file structure'),
            #'get-stats',
            ('get-disk-usage', 'print statistics about usage disk usage'),
            ('get-docnames', 'print the document docnames'),
            #'get-docids',
            #'get-recids',
            #'get-doctypes',
            #'get-revisions',
            #'get-last-revisions',
            #'get-formats',
            #'get-comments',
            #'get-descriptions',
            #'get-restrictions',
            #'get-icons',
            ('get-history', 'print the document history'),
            ('delete', 'delete the specified docname'),
            ('undelete', 'undelete the specified docname'),
            ('list-available-flags', 'list the available flags that can be used when revising/appending a file'),
            #'purge',
            #'expunge',
            ('check-md5', 'check md5 checksum validity of files'),
            ('check-format', 'check if any format-related inconsistences exists'),
            ('check-duplicate-docnames', 'check for duplicate docnames associated with the same record'),
            ('update-md5', 'update md5 checksum of files'),
            ('fix-all', 'fix inconsistences in filesystem vs database vs MARC'),
            ('fix-marc', 'synchronize MARC after filesystem/database'),
            ('fix-format', 'fix format related inconsistences'),
            ('fix-duplicate-docnames', 'fix duplicate docnames associated with the same record'),
            ('textify', 'extract the text, to allow for indexing'),
            ('textify-with-ocr', 'extract the text to allow for indexing (and using OCR if possible)')]


_actions_with_parameter = {
    #'set-doctype' : 'doctype',
    #'set-docname' : 'docname',
    #'set-comment' : 'comment',
    #'set-description' : 'description',
    #'set-restriction' : 'restriction',
    'append' : ('append_path', 'specify the URL/path of the file that will appended to the bibdoc'),
    'revise' : ('revise_path', 'specify the URL/path of the file that will revise the bibdoc'),
    'revise_hide_previous' : ('revise_hide_path', 'specify the URL/path of the file that will revise the bibdoc, previous revisions will be hidden'),
    'merge-into' : ('into_docname', 'merge the docname speficied --docname into_docname'),
}

class OptionParserSpecial(OptionParser):
    def format_help(self, *args, **kwargs):
        result = OptionParser.format_help(self, *args, **kwargs)
        if hasattr(self, 'trailing_text'):
            return "%s\n%s\n" % (result, self.trailing_text)
        else:
            return result

def prepare_option_parser():
    """Parse the command line options."""
    parser = OptionParserSpecial(usage="usage: %prog <query> <action> [options]",
    #epilog="""With <query> you select the range of record/docnames/single files to work on. Note that some actions e.g. delete, append, revise etc. works at the docname level, while others like --set-comment, --set-description, at single file level and other can be applied in an iterative way to many records in a single run. Note that specifing docid(2) takes precedence over recid(2) which in turns takes precedence over pattern/collection search.""",
        version=__revision__)
    parser.trailing_text = """
Examples:
    $ bibdocfile --append foo.tar.gz --recid=1
    $ bibdocfile --revise http://foo.com?search=123 --docname='sam'
            --format=pdf --recid=3 --new-docname='pippo'
    $ bibdocfile --delete *sam --all
    $ bibdocfile --undelete -c "Test Collection"
    """
    parser.trailing_text += wrap_text_in_a_box("""
The bibdocfile command line tool is in a state of high developement. Please
do not rely on the command line parameters to remain compatible for the next
release. You should in particular be aware that if you need to build scripts
on top of the bibdocfile command line interfaces, you will probably need to
revise them with the next release of CDS Invenio.""", 'WARNING')
    query_options = OptionGroup(parser, 'Query parameters')
    query_options.add_option('-a', '--all', action='store_true', dest='all', help='Select all the records')
    query_options.add_option('--show-deleted', action='store_true', dest='show_deleted', help='Show deleted docname, too')
    query_options.add_option('-p', '--pattern', dest='pattern', help='select by specifying the search pattern')
    query_options.add_option('-c', '--collection', dest='collection', help='select by collection')
    query_options.add_option('-r', '--recid', type='int', dest='recid', help='select the recid (or the first recid in a range)')
    query_options.add_option('--recid2', type='int', dest='recid2', help='select the end of the range')
    query_options.add_option('-d', '--docid', type='int', dest='docid', help='select by docid (or the first docid in a range)')
    query_options.add_option('--docid2', type='int', dest='docid2', help='select the end of the range')
    query_options.add_option('--docname', dest='docname', help='specify the docname to work on')
    query_options.add_option('--new-docname', dest='newdocname', help='specify the desired new docname for revising')
    query_options.add_option('--doctype', dest='doctype', help='specify the new doctype')
    query_options.add_option('--format', dest='format', help='specify the format')
    query_options.add_option('--icon', dest='icon', help='specify the URL/path for an icon')
    query_options.add_option('--description', dest='description', help='specify a description')
    query_options.add_option('--comment', dest='comment', help='specify a comment')
    query_options.add_option('--restriction', dest='restriction', help='specify a restriction tag')
    query_options.add_option('--force', dest='force', help='force an action even when it\'s not necessary e.g. textify on an already textified bibdoc.', action='store_true', default=False)

    parser.add_option_group(query_options)
    action_options = OptionGroup(parser, 'Actions')
    for (action, help) in _actions:
        action_options.add_option('--%s' % action, action='store_const', const=action, dest='action', help=help)
    parser.add_option_group(action_options)
    action_with_parameters = OptionGroup(parser, 'Actions with parameter')
    for action, (dest, help) in _actions_with_parameter.iteritems():
        action_with_parameters.add_option('--%s' % action, dest=dest, help=help)
    parser.add_option_group(action_with_parameters)
    parser.add_option('-v', '--verbose', type='int', dest='verbose', default=1)
    parser.add_option('--yes-i-know', action='store_true', dest='yes-i-know')
    parser.add_option('-H', '--human-readable', dest='human_readable', action='store_true', default=False, help='print sizes in human readable format (e.g., 1KB 234MB 2GB)')
    return parser

def get_recids_from_query(pattern, collection, recid, recid2, docid, docid2):
    """Return the proper set of recids corresponding to the given
    parameters."""
    if docid:
        ret = intbitset()
        if not docid2:
            docid2 = docid
        for adocid in xrange(docid, docid2 + 1):
            try:
                bibdoc = BibDoc(adocid)
                if bibdoc and bibdoc.get_recid():
                    ret.add(bibdoc.get_recid())
            except (InvenioWebSubmitFileError, TypeError):
                pass
        return ret
    elif recid:
        if not recid2:
            recid2 = recid
        recid_range = intbitset(xrange(recid, recid2 + 1))
        recid_set = intbitset(run_sql('select id from bibrec'))
        recid_set &= recid_range
        return recid_set
    elif pattern or collection:
        return intbitset(perform_request_search(cc=collection or "", p=pattern or ""))
    else:
        print >> sys.stderr, "ERROR: no record specified."
        sys.exit(1)

def get_docids_from_query(recid_set, docname, docid, docid2, show_deleted=False):
    """Given a set of recid and an optional range of docids
    return a corresponding docids set. The range of docids
    takes precedence over the recid_set."""
    if docname:
        ret = intbitset()
        for recid in recid_set:
            bibrec = BibRecDocs(recid, deleted_too=show_deleted)
            for bibdoc in bibrec.list_bibdocs():
                if fnmatch.fnmatch(bibdoc.get_docname(), docname):
                    ret.add(bibdoc.get_id())
        return ret
    elif docid:
        ret = intbitset()
        if not docid2:
            docid2 = docid
        for adocid in xrange(docid, docid2 + 1):
            try:
                bibdoc = BibDoc(adocid)
                if bibdoc:
                    ret.add(adocid)
            except (InvenioWebSubmitFileError, TypeError):
                pass
        return ret
    else:
        ret = intbitset()
        for recid in recid_set:
            bibrec = BibRecDocs(recid, deleted_too=show_deleted)
            for bibdoc in bibrec.list_bibdocs():
                ret.add(bibdoc.get_id())
                icon = bibdoc.get_icon()
                if icon:
                    ret.add(icon.get_id())
        return ret

def print_info(recid, docid, info):
    """Nicely print info about a recid, docid pair."""
    print '%i:%i:%s' % (recid, docid, info)

def bibupload_ffts(ffts, append=False):
    """Given an ffts dictionary it creates the xml and submit it."""
    xml = ffts_to_xml(ffts)
    if xml:
        print xml
        tmp_file_fd, tmp_file_name = mkstemp(suffix='.xml', prefix="bibdocfile_%s" % time.strftime("%Y-%m-%d_%H:%M:%S"), dir=CFG_TMPDIR)
        os.write(tmp_file_fd, xml)
        os.close(tmp_file_fd)
        os.chmod(tmp_file_name, 0644)
        if append:
            wait_for_user("This will be appended via BibUpload")
            task = task_low_level_submission('bibupload', 'bibdocfile', '-a', tmp_file_name)
            print "BibUpload append submitted with id %s" % task
        else:
            wait_for_user("This will be corrected via BibUpload")
            task = task_low_level_submission('bibupload', 'bibdocfile', '-c', tmp_file_name)
            print "BibUpload correct submitted with id %s" % task
    else:
        print "WARNING: no MARC to upload."
    return True

def cli_append(recid=None, docid=None, docname=None, doctype=None, url=None, format=None, icon=None, description=None, comment=None, restriction=None):
    """Create a bibupload FFT task submission for appending a format."""
    if docid is not None:
        bibdoc = BibDoc(docid)
        if recid is not None and recid != bibdoc.get_recid():
            print >> sys.stderr, "ERROR: Provided recid %i is not linked with provided docid %i" % (recid, docid)
            return False
        if docname is not None and docname != bibdoc.get_docname():
            print >> sys.stderr, "ERROR: Provided docid %i is not named as the provided docname %s" % (docid, docname)
            return False
        recid = bibdoc.get_recid()
        docname = bibdoc.get_docname()
    elif recid is None:
        print >> sys.stderr, "ERROR: Not enough information to identify the record and desired document"
        return False
    try:
        url = clean_url(url)
        check_valid_url(url)
    except StandardError, e:
        print >> sys.stderr, "ERROR: Not a valid url has been specified: %s" % e
        return False
    if docname is None:
        docname = get_docname_from_url(url)
    if not docname:
        print >> sys.stderr, "ERROR: Not enough information to decide a docname!"
        return False
    if format is None:
        format = get_format_from_url(url)
    if not format:
        print >> sys.stderr, "ERROR: Not enough information to decide a format!"
        return False
    if icon is not None and icon != KEEP_OLD_VALUE:
        try:
            icon = clean_url(icon)
            check_valid_url(url)
        except StandardError, e:
            print >> sys.stderr, "ERROR: Not a valid url has been specified for the icon: %s" % e
            return False
    if doctype is None:
        doctype = 'Main'

    fft = {
        'url' : url,
        'docname' : docname,
        'format' :format,
        'icon' : icon,
        'comment' : comment,
        'description' : description,
        'restriction' : restriction,
        'doctype' : doctype
    }
    ffts = {recid : [fft]}
    return bibupload_ffts(ffts, append=True)

def cli_revise(recid=None, docid=None, docname=None, new_docname=None, doctype=None, url=None, format=None, icon=None, description=None, comment=None, restriction=None, hide_previous=False):
    """Create a bibupload FFT task submission for appending a format."""
    if docid is not None:
        bibdoc = BibDoc(docid)
        if recid is not None and recid != bibdoc.get_recid():
            print >> sys.stderr, "ERROR: Provided recid %i is not linked with provided docid %i" % (recid, docid)
            return False
        if docname is not None and docname != bibdoc.get_docname():
            print >> sys.stderr, "ERROR: Provided docid %i is not named as the provided docname %s" % (docid, docname)
            return False
        recid = bibdoc.get_recid()
        docname = bibdoc.get_docname()
    elif recid is None:
        print >> sys.stderr, "ERROR: Not enough information to identify the record and desired document"
        return False
    if url is not None:
        try:
            url = clean_url(url)
            check_valid_url(url)
        except StandardError, e:
            print >> sys.stderr, "ERROR: Not a valid url has been specified: %s" % e
            return False
    if docname is None and url is not None:
        docname = get_docname_from_url(url)
    if not docname:
        print >> sys.stderr, "ERROR: Not enough information to decide a docname!"
        return False
    if docname not in BibRecDocs(recid).get_bibdoc_names():
        print >> sys.stderr, "ERROR: docname %s is not connected with recid %s!" % (docname, recid)
        return False
    if format is None and url is not None:
        format = get_format_from_url(url)
    if not format:
        print >> sys.stderr, "ERROR: Not enough information to decide a format!"
        return False
    if icon is not None and icon != KEEP_OLD_VALUE:
        try:
            icon = clean_url(icon)
            check_valid_url(url)
        except StandardError, e:
            print >> sys.stderr, "ERROR: Not a valid url has been specified for the icon: %s" % e
            return False
    if doctype is None:
        doctype = 'Main'

    fft = {
        'url' : url,
        'docname' : docname,
        'newdocname' : new_docname,
        'format' :format,
        'icon' : icon,
        'comment' : comment,
        'description' : description,
        'restriction' : restriction,
        'doctype' : doctype
    }
    if hide_previous:
        fft['options'] = 'PERFORM_HIDE_PREVIOUS'
    ffts = {recid : [fft]}
    return bibupload_ffts(ffts, append=False)

def cli_get_history(docid_set):
    """Print the history of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        history = bibdoc.get_history()
        for row in history:
            print_info(bibdoc.get_recid(), docid, row)

def cli_textify(docid_set, perform_ocr=False, force=False):
    """Extract text to let indexing on fulltext be possible."""
    if perform_ocr:
        if not can_perform_ocr():
            print >> sys.stderr, "WARNING: OCR requested but OCR is not possible"
            perform_ocr = False
    if perform_ocr:
        additional = ' using OCR (this might take some time)'
    else:
        additional = ''
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        print 'Extracting text for docid %s%s...' % (docid, additional),
        sys.stdout.flush()
        if force or not bibdoc.has_text(require_up_to_date=True):
            try:
                bibdoc.extract_text(perform_ocr=perform_ocr)
                print "DONE"
            except InvenioWebSubmitFileError, e:
                print >> sys.stderr, "WARNING: %s" % e
        else:
            print "not needed"

def cli_fix_all(recid_set):
    """Fix all the records of a recid_set."""
    ffts = {}
    for recid in recid_set:
        ffts[recid] = []
        for docname in BibRecDocs(recid).get_bibdoc_names():
            ffts[recid].append({'docname' : docname, 'doctype' : 'FIX-ALL'})
    return bibupload_ffts(ffts, append=False)

def cli_fix_marc(recid_set):
    """Fix all the records of a recid_set."""
    ffts = {}
    for recid in recid_set:
        ffts[recid] = []
        for docname in BibRecDocs(recid).get_bibdoc_names():
            ffts[recid].append({'docname' : docname, 'doctype' : 'FIX-MARC'})
    return bibupload_ffts(ffts, append=False)

def cli_check_format(recid_set):
    """Check if any format-related inconsistences exists."""
    count = 0
    duplicate = False
    for recid in recid_set:
        bibrecdocs = BibRecDocs(recid)
        if not bibrecdocs.check_duplicate_docnames():
            print >> sys.stderr, "recid %s has duplicate docnames!"
            broken = True
            duplicate = True
        else:
            broken = False
        for docname in bibrecdocs.get_bibdoc_names():
            if not bibrecdocs.check_format(docname):
                print >> sys.stderr, "recid %s with docname %s need format fixing" % (recid, docname)
                broken = True
        if broken:
            count += 1
    if count:
        result = "%d out of %d records need their formats to be fixed." % (count, len(recid_set))
    else:
        result = "All records appear to be correct with respect to formats."
    if duplicate:
        result += " Note however that at least one record appear to have duplicate docnames. You should better fix this situation by using --fix-duplicate-docnames."
    print wrap_text_in_a_box(result, style="conclusion")
    return not(duplicate or count)

def cli_check_duplicate_docnames(recid_set):
    """Check if some record is connected with bibdoc having the same docnames."""
    count = 0
    for recid in recid_set:
        bibrecdocs = BibRecDocs(recid)
        if bibrecdocs.check_duplicate_docnames():
            count += 1
            print sys.stderr, "recid %s has duplicate docnames!"
    if count:
        result = "%d out of %d records have duplicate docnames." % (count, len(recid_set))
        return False
    else:
        result = "All records appear to be correct with respect to duplicate docnames."
        return True

def cli_fix_format(recid_set):
    """Fix format-related inconsistences."""
    fixed = intbitset()
    for recid in recid_set:
        bibrecdocs = BibRecDocs(recid)
        for docname in bibrecdocs.get_bibdoc_names():
            if not bibrecdocs.check_format(docname):
                if bibrecdocs.fix_format(docname, skip_check=True):
                    print >> sys.stderr, "%i has been fixed for docname %s" % (recid, docname)
                else:
                    print >> sys.stderr, "%i has been fixed for docname %s. However note that a new bibdoc might have been created." % (recid, docname)
                fixed.add(recid)
    if fixed:
        print "Now we need to synchronize MARC to reflect current changes."
        cli_fix_marc(fixed)
    print wrap_text_in_a_box("%i out of %i record needed to be fixed." % (len(recid_set), len(fixed)), style="conclusion")
    return not fixed

def cli_fix_duplicate_docnames(recid_set):
    """Fix duplicate docnames."""
    fixed = intbitset()
    for recid in recid_set:
        bibrecdocs = BibRecDocs(recid)
        if not bibrecdocs.check_duplicate_docnames():
            bibrecdocs.fix_duplicate_docnames(skip_check=True)
            print >> sys.stderr, "%i has been fixed for duplicate docnames." % recid
            fixed.add(recid)
    if fixed:
        print "Now we need to synchronize MARC to reflect current changes."
        cli_fix_marc(fixed)
    print wrap_text_in_a_box("%i out of %i record needed to be fixed." % (len(recid_set), len(fixed)), style="conclusion")
    return not fixed

def cli_delete(docid_set):
    """Delete the given docid_set."""
    ffts = {}
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        if not bibdoc.icon_p():
            ## Icons are indirectly deleted with the relative bibdoc.
            docname = bibdoc.get_docname()
            recid = bibdoc.get_recid()
            ffts[recid] = [{'docname' : docname, 'doctype' : 'DELETE'}]
    if ffts:
        return bibupload_ffts(ffts, append=False)
    else:
        print >> sys.stderr, 'ERROR: nothing to delete'
    return False

def cli_undelete(recid_set, docname, status):
    """Delete the given docname"""
    fix_marc = intbitset()
    count = 0
    if not docname.startswith('DELETED-'):
        docname = 'DELETED-*-' + docname
    for recid in recid_set:
        bibrecdocs = BibRecDocs(recid, deleted_too=True)
        for bibdoc in bibrecdocs.list_bibdocs():
            if bibdoc.get_status() == 'DELETED' and fnmatch.fnmatch(bibdoc.get_docname(), docname):
                bibdoc.undelete(status)
                fix_marc.add(recid)
                count += 1
    cli_fix_marc(fix_marc)
    print wrap_text_in_a_box("%s bibdoc successfuly undeleted with status '%s'" % (count, status), style="conclusion")

def cli_merge_into(recid, docname, into_docname):
    """Merge docname into_docname for the given recid."""
    bibrecdocs = BibRecDocs(recid)
    docnames = bibrecdocs.get_bibdoc_names()
    if docname in docnames and into_docname in docnames:
        try:
            bibrecdocs.merge_bibdocs(into_docname, docname)
        except InvenioWebSubmitFileError, e:
            print >> sys.stderr, e
        else:
            cli_fix_marc(intbitset((recid)))
    else:
        print >> sys.stderr, 'ERROR: Either %s or %s is not a valid docname for recid %s' % (docname, into_docname, recid)

def cli_get_info(recid_set, show_deleted=False, human_readable=False):
    """Print all the info of a recid_set."""
    for recid in recid_set:
        print BibRecDocs(recid, deleted_too=show_deleted, human_readable=human_readable)

def cli_get_docnames(docid_set):
    """Print all the docnames of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        print_info(bibdoc.get_recid(), docid, bibdoc.get_docname())

def cli_get_disk_usage(docid_set, human_readable=False):
    """Print the space usage of a docid_set."""
    total_size = 0
    total_latest_size = 0
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        size = bibdoc.get_total_size()
        total_size += size
        latest_size = bibdoc.get_total_size_latest_version()
        total_latest_size += latest_size
        if human_readable:
            print_info(bibdoc.get_recid(), docid, 'size=%s' % nice_size(size))
            print_info(bibdoc.get_recid(), docid, 'latest version size=%s' % nice_size(latest_size))
        else:
            print_info(bibdoc.get_recid(), docid, 'size=%s' % size)
            print_info(bibdoc.get_recid(), docid, 'latest version size=%s' % latest_size)
    if human_readable:
        print wrap_text_in_a_box('total size: %s\n\nlatest version total size: %s'
            % (nice_size(total_size), nice_size(total_latest_size)),
            style='conclusion')
    else:
        print wrap_text_in_a_box('total size: %s\n\nlatest version total size: %s'
            % (total_size, total_latest_size),
            style='conclusion')


def cli_check_md5(docid_set):
    """Check the md5 sums of a docid_set."""
    failures = 0
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        if bibdoc.md5s.check():
            print_info(bibdoc.get_recid(), docid, 'checksum OK')
        else:
            for afile in bibdoc.list_all_files():
                if not afile.check():
                    failures += 1
                    print_info(bibdoc.get_recid(), docid, '%s failing checksum!' % afile.get_full_path())
    if failures:
        print wrap_text_in_a_box('%i files failing' % failures , style='conclusion')
    else:
        print wrap_text_in_a_box('All files are correct', style='conclusion')

def cli_update_md5(docid_set):
    """Update the md5 sums of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        if bibdoc.md5s.check():
            print_info(bibdoc.get_recid(), docid, 'checksum OK')
        else:
            for afile in bibdoc.list_all_files():
                if not afile.check():
                    print_info(bibdoc.get_recid(), docid, '%s failing checksum!' % afile.get_full_path())
            wait_for_user('Updating the md5s of this document can hide real problems.')
            bibdoc.md5s.update(only_new=False)

def cli_assert_recid(options):
    """Check for recid to be correctly set."""
    try:
        assert(int(options.recid) > 0)
        return True
    except:
        print >> sys.stderr, 'ERROR: recid not correctly set: "%s"' % options.recid
        return False

def cli_assert_docname(options):
    """Check for recid to be correctly set."""
    try:
        assert(options.docname)
        return True
    except:
        print >> sys.stderr, 'ERROR: docname not correctly set: "%s"' % options.docname
        return False

def get_all_recids():
    """Return all the existing recids."""
    return intbitset(run_sql('select id from bibrec')) - search_unit(p='DELETED', f='collection', m='e')

def cli_list_available_flags():
    """
    Return the available flags that can be associated with a docname.
    """
    print "Available flags:", ', '.join(CFG_BIBDOCFILE_AVAILABLE_FLAGS)

def cli_list_available_flags():
    """
    Return the available flags that can be associated with a docname.
    """
    print "Available flags:", ', '.join(CFG_BIBDOCFILE_AVAILABLE_FLAGS)

def main():
    parser = prepare_option_parser()
    (options, args) = parser.parse_args()
    if options.all:
        recid_set = get_all_recids()
    else:
        recid_set = get_recids_from_query(options.pattern, options.collection, options.recid, options.recid2, options.docid, options.docid2)
    docid_set = get_docids_from_query(recid_set, options.docname, options.docid, options.docid2, options.show_deleted is True or options.action == 'undelete')
    try:
        if options.action == 'get-history':
            cli_get_history(docid_set)
        elif options.action == 'get-info':
            cli_get_info(recid_set, options.show_deleted is True, options.human_readable)
        elif options.action == 'get-docnames':
            cli_get_docnames(docid_set)
        elif options.action == 'get-disk-usage':
            cli_get_disk_usage(docid_set, options.human_readable)
        elif options.action == 'check-md5':
            cli_check_md5(docid_set)
        elif options.action == 'update-md5':
            cli_update_md5(docid_set)
        elif options.action == 'fix-all':
            cli_fix_all(recid_set)
        elif options.action == 'fix-marc':
            cli_fix_marc(recid_set)
        elif options.action == 'delete':
            cli_delete(docid_set)
        elif options.action == 'fix-duplicate-docnames':
            cli_fix_duplicate_docnames(recid_set)
        elif options.action == 'fix-format':
            cli_fix_format(recid_set)
        elif options.action == 'check-duplicate-docnames':
            cli_check_duplicate_docnames(recid_set)
        elif options.action == 'check-format':
            cli_check_format(recid_set)
        elif options.action == 'list-available-flags':
            cli_list_available_flags()
        elif options.action == 'undelete':
            cli_undelete(recid_set, options.docname or '*', options.restriction or '')
        elif options.action == 'textify':
            cli_textify(docid_set, force=options.force)
        elif options.action == 'textify-with-ocr':
            cli_textify(docid_set, perform_ocr=True, force=options.force)
        elif options.append_path:
            if cli_assert_recid(options):
                res = cli_append(options.recid, options.docid, options.docname, options.doctype, options.append_path, options.format, options.icon, options.description, options.comment, options.restriction)
                if not res:
                    sys.exit(1)
        elif options.revise_path:
            if cli_assert_recid(options):
                res = cli_revise(options.recid, options.docid, options.docname,
                options.newdocname, options.doctype, options.revise_path, options.format,
                options.icon, options.description, options.comment, options.restriction)
                if not res:
                    sys.exit(1)
        elif options.revise_hide_path:
            if cli_assert_recid(options):
                res = cli_revise(options.recid, options.docid, options.docname,
                options.newdocname, options.doctype, options.revise_path, options.format,
                options.icon, options.description, options.comment, options.restriction, True)
                if not res:
                    sys.exit(1)
        elif options.into_docname:
            if options.recid and options.docname:
                cli_merge_into(options.recid, options.docname, options.into_docname)
            else:
                print >> sys.stderr, "ERROR: You have to specify both the recid and a docname for using --merge-into"
        else:
            print >> sys.stderr, "ERROR: Action %s is not valid" % options.action
            sys.exit(1)
    except InvenioWebSubmitFileError, e:
        print >> sys.stderr, 'ERROR: Exception caught: %s' % e
        sys.exit(1)

if __name__ == '__main__':
    main()
