# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2014 CERN.
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
This implements a redirection for CERN HR Documents.

This implements a redirection for CERN HR Documents in the CERN Document
Server. It's useful as a reference on how goto plugins could be implemented.
"""

import time
import re

from invenio.legacy.search_engine import perform_request_search
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.bibdocfile.api import BibRecDocs, InvenioBibDocFileError


def make_cern_ssr_docname(lang, edition, modif=0):
    """Make cern ssh docname."""
    # FIXME the docs
    if modif:
        return "CERN_SRR_%(lang)s_ed%(edition)02d_modif%(modif)02d" % {
            'lang': lang,
            'edition': edition,
            'modif': modif
        }
    else:
        return "CERN_SRR_%(lang)s_ed%(edition)02d" % {
            'lang': lang,
            'edition': edition,
        }

_RE_REVISION = re.compile(r"rev(\d\d)")


def _get_revision(docname):
    """
    Return the revision in a docname.

    Return the revision in a docname. E.g.:
    CERN_Circ_Op_en_02_rev01_Implementation measures.pdf -> 1
    CERN_Circ_Op_en_02_rev02_Implementation measures.PDF -> 2
    """
    g = _RE_REVISION.search(docname)
    if g:
        return int(g.group(1))
    return 0


def _register_document(documents, docname, key):
    """
    Register in the documents mapping the docname to key.

    Register in the documents mapping the docname to key, but only if the
    docname has a revision higher of the docname already associated with a key.
    """
    if key in documents:
        if _get_revision(docname) > _get_revision(documents[key]):
            documents[key] = docname
    else:
        documents[key] = docname


def goto(type, document='', number=0, lang='en', modif=0):
    """Goto function."""
    # FIXME the docs
    today = time.strftime('%Y-%m-%d')
    if type == 'SRR':
        ## We would like a CERN Staff Rules and Regulations
        recids = perform_request_search(
            cc='Staff Rules and Regulations',
            f="925__a:1996-01-01->%s 925__b:%s->9999-99-99" % (today, today))
        recid = recids[-1]
        reportnumber = get_fieldvalues(recid, '037__a')[0]
        edition = int(reportnumber[-2:])  # e.g. CERN-STAFF-RULES-ED08
        return BibRecDocs(recid).get_bibdoc(
            make_cern_ssr_docname(lang,
                                  edition,
                                  modif)).get_file('.pdf').get_url()
    elif type == "OPER-CIRC":
        recids = perform_request_search(
            cc="Operational Circulars",
            p="reportnumber:\"CERN-OPER-CIRC-%s-*\"" % number, sf="925__a")
        recid = recids[-1]
        documents = {}
        bibrecdocs = BibRecDocs(recid)
        for docname in bibrecdocs.get_bibdoc_names():
            ldocname = docname.lower()
            if 'implementation' in ldocname:
                _register_document(documents, docname, 'implementation-en')
            elif 'application' in ldocname:
                _register_document(documents, docname, 'implementation-fr')
            elif 'archiving' in ldocname:
                _register_document(documents, docname, 'archiving-en')
            elif 'archivage' in ldocname:
                _register_document(documents, docname, 'archiving-fr')
            elif 'annexe' in ldocname or 'annexes_fr' in ldocname:
                _register_document(documents, docname, 'annex-fr')
            elif 'annexes_en' in ldocname or 'annex' in ldocname:
                _register_document(documents, docname, 'annex-en')
            elif '_en_' in ldocname \
                 or '_eng_' in ldocname or '_angl_' in ldocname:
                _register_document(documents, docname, 'en')
            elif '_fr_' in ldocname:
                _register_document(documents, docname, 'fr')
        try:
            return bibrecdocs.get_bibdoc(documents[document]) \
                .get_file('.pdf').get_url()
        except InvenioBibDocFileError:
            return bibrecdocs.get_bibdoc(documents[document]) \
                .get_file('.PDF').get_url()
    elif type == 'ADMIN-CIRC':
        recids = perform_request_search(
            cc="Administrative Circulars",
            p='reportnumber:"CERN-ADMIN-CIRC-%s-*"' % number,
            sf="925__a")
        recid = recids[-1]
        documents = {}
        bibrecdocs = BibRecDocs(recid)
        for docname in bibrecdocs.get_bibdoc_names():
            ldocname = docname.lower()
            if 'implementation' in ldocname:
                _register_document(documents, docname, 'implementation-en')
            elif 'application' in ldocname:
                _register_document(documents, docname, 'implementation-fr')
            elif 'archiving' in ldocname:
                _register_document(documents, docname, 'archiving-en')
            elif 'archivage' in ldocname:
                _register_document(documents, docname, 'archiving-fr')
            elif 'annexe' in ldocname or 'annexes_fr' in ldocname:
                _register_document(documents, docname, 'annex-fr')
            elif 'annexes_en' in ldocname or 'annex' in ldocname:
                _register_document(documents, docname, 'annex-en')
            elif '_en_' in ldocname or '_eng_' in ldocname \
                 or '_angl_' in ldocname:
                _register_document(documents, docname, 'en')
            elif '_fr_' in ldocname:
                _register_document(documents, docname, 'fr')
        try:
            return bibrecdocs.get_bibdoc(
                documents[document]).get_file('.pdf').get_url()
        except InvenioBibDocFileError:
            return bibrecdocs.get_bibdoc(
                documents[document]).get_file('.PDF').get_url()


def register_hr_redirections():
    """Run this only once."""
    from invenio.modules.redirector.api import register_redirection
    plugin = 'goto_plugin_cern_hr_documents'

    ## Staff rules and regulations
    for modif in range(1, 20):
        for lang in ('en', 'fr'):
            register_redirection('hr-srr-modif%02d-%s' % (modif, lang),
                                 plugin,
                                 parameters={'type': 'SRR',
                                             'lang': lang,
                                             'modif': modif})
    for lang in ('en', 'fr'):
        register_redirection('hr-srr-%s' % lang, plugin,
                             parameters={'type': 'SRR',
                                         'lang': lang,
                                         'modif': 0})

    ## Operational Circulars
    for number in range(1, 10):
        for lang in ('en', 'fr'):
            register_redirection('hr-oper-circ-%s-%s' % (number, lang),
                                 plugin, parameters={'type': 'OPER-CIRC',
                                                     'document': lang,
                                                     'number': number})
    for number, special_document in ((2, 'implementation'),
                                     (2, 'annex'), (3, 'archiving'),
                                     (3, 'annex')):
        for lang in ('en', 'fr'):
            register_redirection(
                'hr-circ-%s-%s-%s' % (number, special_document, lang),
                plugin,
                parameters={'type': 'OPER-CIRC',
                            'document': '%s-%s' % (special_document, lang),
                            'number': number})

    ## Administrative Circulars:
    for number in range(1, 32):
        for lang in ('en', 'fr'):
            register_redirection('hr-admin-circ-%s-%s' % (number, lang),
                                 plugin,
                                 parameters={'type': 'ADMIN-CIRC',
                                             'document': lang,
                                             'number': number})


if __name__ == "__main__":
    register_hr_redirections()
