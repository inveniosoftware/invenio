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

import sys
import os
import time
from optparse import OptionParser, OptionGroup
from tempfile import mkstemp

from invenio.config import CFG_TMPDIR
from invenio.bibdocfile import BibRecDocs, BibDoc, InvenioWebSubmitFileError, \
    nice_size, check_valid_url, clean_url, get_docname_from_url, \
    get_format_from_url, KEEP_OLD_VALUE
from invenio.intbitset import intbitset
from invenio.search_engine import perform_request_search
from invenio.textutils import wrap_text_in_a_box, wait_for_user
from invenio.dbquery import run_sql
from invenio.bibtask import task_low_level_submission
from invenio.bibrecord import encode_for_xml

def _xml_mksubfield(key, subfield, fft):
    return fft.get(key, None) and '\t\t<subfield code="%s">%s</subfield>\n' % (subfield, encode_for_xml(fft[key])) or ''

def _xml_fft_creator(fft):
    """Transform an fft dictionary (made by keys url, docname, format,
    new_docname, icon, comment, description, restriction, doctype, into an xml
    string."""
    out = '\t<datafield tag="FFT" ind1=" " ind2=" ">\n'
    out += _xml_mksubfield('url', 'a', fft)
    out += _xml_mksubfield('docname', 'n', fft)
    out += _xml_mksubfield('format', 'f', fft)
    out += _xml_mksubfield('newdocname', 'm', fft)
    out += _xml_mksubfield('doctype', 't', fft)
    out += _xml_mksubfield('description', 'd', fft)
    out += _xml_mksubfield('comment', 'c', fft)
    out += _xml_mksubfield('restriction', 'r', fft)
    out += _xml_mksubfield('icon', 'x', fft)
    out += '\t</datafield>\n'
    return out

def ffts_to_xml(ffts):
    """Transform a dictionary: recid -> ffts where ffts is a list of fft dictionary
    into xml.
    """
    out = ''
    for recid, ffts in ffts.iteritems():
        out += '<record>\n'
        out += '\t<controlfield tag="001">%i</controlfield>\n' % recid
        if ffts:
            for fft in ffts:
                out += _xml_fft_creator(fft)
        else:
            out += '<datafield tag="FFT" ind1=" " ind2=" "></datafield>\n'
        out += '</record>\n'
    return out

def get_usage():
    """Return a nicely formatted string for printing the help of bibdocadmin"""
    return """usage: %prog <query> <action> [options]
  <query>: --pattern <pattern>, --collection <collection>, --recid <recid>,
           --recid2 <recid>, --docid <docid>, --all
           --docid2 <docid>, --docname <docname>,
 <action>: --get-info, --get-stats, --get-usage, --get-docnames
           --get-docids, --get-recids, --get-doctypes, --get-revisions,
           --get-last-revisions, --get-formats, --get-comments,
           --get-descriptions, --get-restrictions, --get-icons,
           --get-history,
           --delete, --undelete, --purge, --expunge, --revert <revision>,
           --check-md5, --update-md5,
           --set-doctype <doctype>, --set-docname <docname>,
           --set-comment <comment>, --set-description <description>,
           --set-restriction <tag>, --set-icon <path>,
           --append <path>, --revise <path>,
[options]: --with-stamp-template <template>, --with-stamp-parameters <parameters>,
           --verbose <level>, --force, --interactive, --with-icon-size <size>,
           --with-related-formats
With <query> you select the range of record/docnames/single files to work on.
Note that some actions e.g. delete, append, revise etc. works at the docname
level, while others like --set-comment, --set-description, at single file level
and other can be applied in an iterative way to many records in a single run.

Note that specifying docid(2) takes precedence over recid(2) which in turns
takes precedence over pattern/collection search.
"""

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
            #'delete',
            #'undelete',
            #'purge',
            #'expunge',
            ('check-md5', 'check md5 checksum validity of files'),
            ('update-md5', 'update md5 checksum of files'),
            ('fix-all', 'fix inconsistences in filesystem vs database vs MARC'),
            ('fix-marc', 'synchronize MARC after filesystem/database')]

_actions_with_parameter = {
    #'set-doctype' : 'doctype',
    #'set-docname' : 'docname',
    #'set-comment' : 'comment',
    #'set-description' : 'description',
    #'set-restriction' : 'restriction',
    'append' : ('append_path', 'specify the URL/path of the file that will appended to the bibdoc'),
    'revise' : ('revise_path', 'specify the URL/path of the file that will revise the bibdoc')
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
    """
    parser.trailing_text += wrap_text_in_a_box("""
The bibdocfile command line tool is in a state of high developement. Please
do not rely on the command line parameters to remain compatible for the next
release. You should in particular be aware that if you need to build scripts
on top of the bibdocfile command line interfaces, you will probably need to
revise them with the next release of CDS Invenio.""", 'WARNING')
    query_options = OptionGroup(parser, 'Query parameters')
    query_options.add_option('-a', '--all', action='store_true', dest='all', help='Select all the records')
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
        return intbitset(perform_request_search(cc=collection, p=pattern))
    else:
        return intbitset(run_sql('select id from bibrec'))

def get_docids_from_query(recid_set, docid, docid2):
    """Given a set of recid and an optional range of docids
    return a corresponding docids set. The range of docids
    takes precedence over the recid_set."""
    if docid:
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
            bibrec = BibRecDocs(recid)
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
    print xml
    tmp_file = os.path.join(CFG_TMPDIR, "bibdocfile_%s" % time.strftime("%Y-%m-%d_%H:%M:%S"))
    open(tmp_file, 'w').write(xml)
    if append:
        wait_for_user("This will be appended via BibUpload")
        task = task_low_level_submission('bibupload', 'bibdocfile', '-a', tmp_file)
        print "BibUpload append submitted with id %s" % task
    else:
        wait_for_user("This will be corrected via BibUpload")
        task = task_low_level_submission('bibupload', 'bibdocfile', '-c', tmp_file)
        print "BibUpload correct submitted with id %s" % task
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

def cli_revise(recid=None, docid=None, docname=None, new_docname=None, doctype=None, url=None, format=None, icon=None, description=None, comment=None, restriction=None):
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
    ffts = {recid : [fft]}
    return bibupload_ffts(ffts, append=False)

def cli_get_history(docid_set):
    """Print the history of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        history = bibdoc.get_history()
        for row in history:
            print_info(bibdoc.get_recid(), docid, row)

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

def cli_get_info(recid_set):
    """Print all the info of a recid_set."""
    for recid in recid_set:
        print BibRecDocs(recid)

def cli_get_docnames(docid_set):
    """Print all the docnames of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        print_info(bibdoc.get_recid(), docid, bibdoc.get_docname())

def cli_get_disk_usage(docid_set):
    """Print the space usage of a docid_set."""
    total_size = 0
    total_latest_size = 0
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        size = bibdoc.get_total_size()
        total_size += size
        latest_size = bibdoc.get_total_size_latest_version()
        total_latest_size += latest_size
        print_info(bibdoc.get_recid(), docid, 'size %s, latest version size %s' % (nice_size(size), nice_size(total_latest_size)))
    print wrap_text_in_a_box('total size: %s\n\nlatest version total size: %s'
        % (nice_size(total_size), nice_size(total_latest_size)),
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

def get_all_recids():
    """Return all the existing recids."""
    return intbitset(run_sql('select id from bibrec'))

def main():
    parser = prepare_option_parser()
    (options, args) = parser.parse_args()
    if options.all:
        recid_set = get_all_recids()
    else:
        recid_set = get_recids_from_query(options.pattern, options.collection, options.recid, options.recid2, options.docid, options.docid2)
    docid_set = get_docids_from_query(recid_set, options.docid, options.docid2)
    if options.action == 'get-history':
        cli_get_history(docid_set)
    elif options.action == 'get-info':
        cli_get_info(recid_set)
    elif options.action == 'get-docnames':
        cli_get_docnames(docid_set)
    elif options.action == 'get-disk-usage':
        cli_get_disk_usage(docid_set)
    elif options.action == 'check-md5':
        cli_check_md5(docid_set)
    elif options.action == 'update-md5':
        cli_update_md5(docid_set)
    elif options.action == 'fix-all':
        cli_fix_all(recid_set)
    elif options.action == 'fix-marc':
        cli_fix_marc(recid_set)
    elif options.append_path:
        res = cli_append(options.recid, options.docid, options.docname, options.doctype, options.append_path, options.format, options.icon, options.description, options.comment, options.restriction)
        if not res:
            sys.exit(1)
    elif options.revise_path:
        res = cli_revise(options.recid, options.docid, options.docname,
        options.newdocname, options.doctype, options.revise_path, options.format,
        options.icon, options.description, options.comment, options.restriction)
        if not res:
            sys.exit(1)
    else:
        print >> sys.stderr, "Action %s is not valid" % options.action
        sys.exit(1)

if __name__=='__main__':
    main()
