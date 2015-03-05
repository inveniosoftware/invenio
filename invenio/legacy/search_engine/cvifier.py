# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011 CERN.
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
Search engine CVifier, generating CVs for record collections in LaTeX, html, and plaintext formats.
The main API is cvify_records().
"""

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

from invenio.config import CFG_SITE_SUPPORT_EMAIL
import invenio.legacy.template
websearch_templates = invenio.legacy.template.load('websearch')

def cvify_records(recids, of, req=None, so='d'):
    """
       Write a CV for records RECIDS in the format OF in language LN.
       REQ is the Apache/mod_python request object.
    """
    #FIXME use Jinja2 template
    from invenio.modules.formatter import print_records

    # intbitsets don't support indexing, so we need a list from our hitset first
    recids = [hit for hit in recids]
    if so == 'd':
        recids.reverse()
    if of.startswith('h'):
        if of == 'hcv':
            format_records(recids, of=of,
                           record_prefix=lambda count: '%d) ' % (count+1),
                           req=req)
        elif of == 'htcv':
            format_records(recids, of=of,
                           record_prefix=lambda count: '%d) ' % (count+1),
                           req=req)

    elif of == 'tlcv':
        HEADER = r'''
\documentclass{article}
%%To use pdflatex, uncomment these lines, as well as the \href lines
%%in each entry
%%\usepackage[pdftex,
%%       colorlinks=true,
%%       urlcolor=blue,       %% \href{...}{...} external (URL)
%%       filecolor=green,     %% \href{...} local file
%%       linkcolor=red,       %% \ref{...} and \pageref{...}
%%       pdftitle={Papers by AUTHOR},
%%       pdfauthor={Your Name},
%%       pdfsubject={Just a test},
%%       pdfkeywords={test testing testable},
%%       pagebackref,
%%       pdfpagemode=None,
%%        bookmarksopen=true]{hyperref}
%%usepackage{arial}
%%\renewcommand{\familydefault}{\sfdefault} %% San serif
\renewcommand{\labelenumii}{\arabic{enumi}.\arabic{enumii}}

\pagestyle{empty}
\oddsidemargin 0.0in
\textwidth 6.5in
\topmargin -0.75in
\textheight 9.5in

\begin{document}
\title{Papers by AUTHOR}
\author{}
\date{}
\maketitle
\begin{enumerate}

%%%%   LIST OF PAPERS
%%%%   Please comment out anything between here and the
%%%%   first \item
%%%%   Please send any updates or corrections to the list to
%%%%   %(email)s
''' % { 'email' : CFG_SITE_SUPPORT_EMAIL, }
        FOOTER = r'''
\end{enumerate}
\end{document}
'''
        format_records(recids, of=of,
                       prologue=HEADER,
                       epilogue=FOOTER,
                       req=req)

    return ''
