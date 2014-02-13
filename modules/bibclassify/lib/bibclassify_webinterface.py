# This file is part of Invenio.
# Copyright (C) 2008, 2009, 2010, 2011, 2013 CERN.
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

"""BibClassify's web interface.

This module is NOT standalone safe - this component is never expected
to run in a standalone mode, but always inside invenio."""


import os
from cgi import escape
from urllib import quote
import time
from invenio import bibupload

from invenio.messages import gettext_set_language
from invenio.bibdocfile import BibRecDocs
from invenio.webinterface_handler import WebInterfaceDirectory
from invenio.webpage import pageheaderonly, pagefooteronly
from invenio.search_engine import get_colID, \
    guess_primary_collection_of_a_record, create_navtrail_links, \
    perform_request_search, get_record, print_record
from invenio.websearchadminlib import get_detailed_page_tabs
from invenio.template import load
from invenio.webinterface_handler import wash_urlargd
from invenio.webuser import collect_user_info
from invenio import access_control_engine as acce
from invenio import dbquery
from invenio import bibtask
from invenio import bibrecord

from invenio import bibclassify_config as bconfig
from invenio import bibclassify_text_extractor
from invenio import bibclassify_engine
from invenio import bibclassify_ontology_reader as bor

log = bconfig.get_logger("bibclassify.webinterface")

template = load('bibclassify')


def main_page(req, recid, tabs, ln,
              webstyle_template,
              websearch_template):
    """Generates the main page for the keyword tab - http://url/record/[recid]/keywords
    @var req: request object
    @var recid: int docid
    @var tabs: list of tab links
    @var ln: language id
    @var webstyle_template: template object
    @var websearch_template: template object
    @return: nothing, writes using req object
    """

    form = req.form
    argd = wash_urlargd(form, {
        'generate': (str, 'no'),
        'sorting': (str, 'occurences'),
        'type': (str, 'tagcloud'),
        'numbering': (str, 'off'),
        'showall': (str, 'off'),
        })

    for k, v in argd.items():
        argd[k] = escape(v)

    req.write(webstyle_template.detailed_record_container_top(recid, tabs, ln))
    req.write(websearch_template.tmpl_record_plots(recID=recid, ln=ln))

    # Get the keywords from MARC (if any)
    success, keywords, marcrec = record_get_keywords(recid)

    if success:
        # check for the cached file and delete it (we don't need it anymore, data are in the DB)
        tmp_file = bibclassify_engine.get_tmp_file(recid)
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except Exception, msg:
                log.error('Error removing the cached file: %s' % tmp_file)
                log.error(msg)

    if argd['generate'] == "yes" or not success:
        # Give user possibility to generate them ONLY if not available already
        # we may have some keywords, but they are the old ones and we want to generate new
        new_found, new_keywords, marcrec = generate_keywords(req, recid, argd)
        if keywords and new_keywords:
            for key in keywords.keys():
                if key in new_keywords:
                    log.warning('The old "DESY" keyword will be overwritten by the newly extracted one: %s' % key)
        keywords.update(new_keywords)

    if keywords:
        # Output the keywords or the generate button or some message why kw not available
        write_keywords_body(keywords, req, recid, argd, marcrec=marcrec)

    if argd['sorting'] == 'related' and not keywords:
        req.write('You may want to run BibIndex.')

    req.write(webstyle_template.detailed_record_container_bottom(recid, tabs, ln))


def write_keywords_body(keywords, req, recid, argd, marcrec=None):
    """Writes the bibclassify keyword output into req object"""


    if not keywords:
        req.write(template.tmpl_page_no_keywords(req=req, **argd))
        return

    # test if more than half of the entries have weight (0,0) - ie. not weighted
    #if argd['type'] == 'tagcloud' and len(filter(lambda x: (0,0) in x[0], keywords.values())) > (len(keywords) * .5):
    #    argd['type'] = 'list'


    if argd['type'] == 'list':
        # Display keywords as a list.
        req.write(template.tmpl_page_list(keywords, req=req, **argd))
    elif argd['type'] == 'tagcloud':
        # Display keywords as a tag cloud.
        req.write(template.tmpl_page_tagcloud(keywords=keywords, req=req, **argd))
    elif argd['type'] == 'xml':
        if marcrec:
            marcxml = filter_marcrec(marcrec)
        else:
            marcxml = bibclassify_engine.build_marc(recid, keywords, {})
        req.write(template.tmpl_page_xml_output(keywords,
                                                marcxml,
                                                req=req, **argd))
    else:
        _ = gettext_set_language(argd['ln'])
        req.write(template.tmpl_page(top=_('Unknown type: %s')  % argd['type'], **argd))



def record_get_keywords(record, main_field=bconfig.CFG_MAIN_FIELD,
                                others=bconfig.CFG_OTHER_FIELDS):
    """Returns a dictionary of keywordToken objects from the marc
    record. Weight is set to (0,0) if no weight can be found.

    This will load keywords from the field 653 and 695__a (which are the
    old 'DESY' keywords)

    @var record: int or marc record, if int - marc record is loaded
        from the database. If you pass record instance, keywords are
        extracted from it
    @return: tuple (found, keywords, marcxml)
        found - int indicating how many main_field keywords were found
            the other fields are not counted
        keywords - standard dictionary of keywordToken objects
        marcrec - marc record object loaded with data
    """
    keywords = {}

    if isinstance(main_field, basestring):
        main_field = [main_field]
    if isinstance(others, basestring):
        others = [others]

    if isinstance(record, int):
        rec = get_record(record)
    else:
        rec = record

    found = 0
    for m_field in main_field:
        tag, ind1, ind2 = bibclassify_engine._parse_marc_code(m_field)
        for field in rec.get(tag, []):
            keyword = ''
            weight = 0
            type = ''

            for subfield in field[0]:
                if subfield[0] == 'a':
                    keyword = subfield[1]
                elif subfield[0] == 'n':
                    weight = int(subfield[1])
                elif subfield[0] == '9':
                    type = subfield[1]
            if keyword:
                found += 1
                keywords[bor.KeywordToken(keyword, type=type)] = [[(0,0) for x in range(weight)]]

    if others:
        for field_no in others:
            tag, ind1, ind2 = bibclassify_engine._parse_marc_code(field_no)
            type = 'f%s' % field_no
            for field in rec.get(tag, []):
                keyword = ''
                for subfield in field[0]:
                    if subfield[0] == 'a':
                        keyword = subfield[1]
                        keywords[bor.KeywordToken(keyword, type=type)] = [[(0,0)]]
                        break

    return found, keywords, rec

def generate_keywords(req, recid, argd):
    """Extracts keywords from the fulltexts (if found) for the
    given recid. It first checks whether the keywords are not already
    stored in the temp file (maybe from the previous run).
    @var req: req object
    @var recid: record id
    @var argd: arguments passed from web
    @keyword store_keywords: boolean, whether to save records in the file
    @return: standard dictionary of kw objects or {}
    """

    ln = argd['ln']
    _ = gettext_set_language(ln)
    keywords = {}

    # check the files were not already generated
    abs_path = bibclassify_engine.get_tmp_file(recid)
    if os.path.exists(abs_path):
        try:
            # Try to load the data from the tmp file
            recs = bibupload.xml_marc_to_records(bibupload.open_marc_file(abs_path))
            return record_get_keywords(recs[0])
        except:
            pass

    # check it is allowed (for this user) to generate pages
    (exit_stat, msg) = acce.acc_authorize_action(req, 'runbibclassify')
    if exit_stat != 0:
        log.info('Access denied: ' + msg)
        msg = _("The site settings do not allow automatic keyword extraction")
        req.write(template.tmpl_page_msg(msg=msg))
        return 0, keywords, None

    # register generation
    bibdocfiles = BibRecDocs(recid).list_latest_files()
    if bibdocfiles:
        # User arrived at a page, but no keywords are available
        inprogress, msg = _doc_already_submitted(recid)
        if argd['generate'] != 'yes':
            # Display a form and give them possibility to generate keywords
            if inprogress:
                req.write(template.tmpl_page_msg(msg='<div class="warningbox">%s</div>' % _(msg)))
            else:
                req.write(template.tmpl_page_generate_keywords(req=req, **argd))
            return 0, keywords, None
        else: # after user clicked on "generate" button
            if inprogress:
                req.write(template.tmpl_page_msg(msg='<div class="warningbox">%s</div>' % _(msg) ))
            else:
                schedule_extraction(recid, taxonomy=bconfig.CFG_EXTRACTION_TAXONOMY)
                req.write(template.tmpl_page_msg(msg='<div class="warningbox">%s</div>' %
                                                 _('We have registered your request, the automated'
                'keyword extraction will run after some time. Please return back in a while.')))

    else:
        req.write(template.tmpl_page_msg(msg='<div class="warningbox">%s</div>' %
                    _("Unfortunately, we don't have a PDF fulltext for this record in the storage, \
                    keywords cannot be generated using an automated process.")))

    return 0, keywords, None



def upload_keywords(filename, mode='correct', recids=None):
    """Stores the extracted keywords in the database
    @var filename: fullpath to the file with marc record
    @keyword mode: correct|replace|add|delete
        use correct to add fields if they are different
        replace all fields with fields from the file
        add - add (even duplicate) fields
        delete - delete fields which are inside the file
    @keyword recids: list of record ids, this arg comes from
        the bibclassify daemon and it is used when the recids
        contains one entry (recid) - ie. one individual document
        was processed. We use it to mark the job title so that
        it is possible to query database if the bibclassify
        was run over that document (in case of collections with
        many recids, we simply construct a general title)
    """
    if mode == 'correct':
        m = '-c'
    elif mode == 'replace':
        m = '-r'
    elif mode == 'add':
        m = '-a'
    elif mode == 'delete':
        m = '-d'
    else:
        raise Exception('Unknown mode')

    # let's use the user column to store the information, cause no better alternative in sight...
    user_title = 'bibclassify.upload'
    if recids and len(recids) == 1:
        user_title = 'extract:%d' % recids[0]
    bibtask.task_low_level_submission('bibupload',
                user_title, '-n', m, filename)


def schedule_extraction(recid, taxonomy):
    bibtask.task_low_level_submission('bibclassify',
                'extract:%s' % recid, '-k', taxonomy, '-i', '%s' % recid)

def _doc_already_submitted(recid):
    # check extraction was already registered
    sql = "SELECT COUNT(proc) FROM schTASK WHERE proc='bibclassify' AND user=%s\
        AND (status='WAITING' OR status='RUNNING')"
    if dbquery.run_sql(sql, ("extract:" + str(recid),))[0][0] > 0:
        return (True, "The automated keyword extraction \
                    for this document has been already scheduled. Please return back in a while.")

    # check the upload is inside the scheduled tasks
    sql = "SELECT COUNT(proc) FROM schTASK WHERE proc='bibupload' AND user=%s\
        AND (status='WAITING' OR status='RUNNING')"
    if dbquery.run_sql(sql, ("extract:" + str(recid),))[0][0] > 0:
        return (True, 'The document was already processed, '
                        'it will take a while for it to be ingested.')

    # or the task was run and is already archived
    sql = "SELECT COUNT(proc) FROM hstTASK WHERE proc='bibupload' AND user=%s"
    if dbquery.run_sql(sql, ("extract:" + str(recid),))[0][0] > 0:
        return (True, 'The document was already processed, '
                        'at this moment, the automated extraction is not available.')

    # or the task was already ran
    sql = "SELECT COUNT(proc) FROM schTASK WHERE proc='bibclassify' AND user=%s\
        AND (status='DONE')"
    if dbquery.run_sql(sql, ("extract:" + str(recid),))[0][0] > 0:
        return (True, 'The document was already processed, '
                        'but automated extraction identified no suitable keywords.')

    # or the extraction is in error stat
    sql = "SELECT COUNT(proc) FROM schTASK WHERE proc='bibclassify' AND user=%s\
        AND (status='ERROR')"
    if dbquery.run_sql(sql, ("extract:" + str(recid),))[0][0] > 0:
        return (True, 'The document was already scheduled, '
                        'but an error happened. This requires an'
                        'administrator\'s intervention. Unfortunately, '
                        'for the moment we cannot display any data.')
    return (False, None)



def filter_marcrec(marcrec, main_field=bconfig.CFG_MAIN_FIELD,
                   others=bconfig.CFG_OTHER_FIELDS):
    """Removes the unwanted fields and returns xml"""
    if isinstance(main_field, basestring):
        main_field = [main_field]
    if isinstance(others, basestring):
        others = [others]
    key_map = ['001']

    for field in main_field + others:
        tag, ind1, ind2 = bibclassify_engine._parse_marc_code(field)
        key_map.append(tag)

    return bibrecord.print_rec(marcrec, 1, tags=key_map)
