## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

# pylint: disable=C0301

"""Plotextractor configuration."""

__revision__ = "$Id$"

## CFG_PLOTEXTRACTOR_ARXIV_BASE -- for acquiring source tarballs for plot
## extraction, where should we look?  If nothing is set, we'll just go
## to arXiv, but this can be a filesystem location, too
CFG_PLOTEXTRACTOR_ARXIV_BASE = 'http://arxiv.org/' # home!

## CFG_PLOTEXTRACTOR_ARXIV_E_PRINT -- for acquiring source tarballs for plot
## extraction, subfolder where the tarballs sit
CFG_PLOTEXTRACTOR_ARXIV_E_PRINT = 'e-print/'

## CFG_PLOTEXTRACTOR_ARXIV_PDF -- for acquiring source tarballs for plot
## extraction, subfolder where the pdf sit
CFG_PLOTEXTRACTOR_ARXIV_PDF = 'pdf/'

## CFG_PLOTEXTRACTOR_DESY_BASE --
CFG_PLOTEXTRACTOR_DESY_BASE = 'http://www-library.desy.de/preparch/desy/'

## CFG_PLOTEXTRACTOR_DESY_PIECE --
CFG_PLOTEXTRACTOR_DESY_PIECE = '/desy'

## CFG_PLOTEXTRACTOR_CONTEXT_LIMIT -- when extracting context of plots from
## TeX sources, this is the limitation of characters in each direction to extract
## context from. Default 750.
CFG_PLOTEXTRACTOR_CONTEXT_EXTRACT_LIMIT = 750

## CFG_PLOTEXTRACTOR_DISALLOWED_TEX -- when extracting context of plots from TeX
## sources, this is the list of TeX tags that will trigger 'end of context'.
CFG_PLOTEXTRACTOR_DISALLOWED_TEX = ['begin', 'end', 'section', 'includegraphics',
                                    'caption', 'acknowledgements']

## CFG_PLOTEXTRACTOR_CONTEXT_WORD_LIMIT -- when extracting context of plots from
## TeX sources, this is the limitation of words in each direction. Default 75.
CFG_PLOTEXTRACTOR_CONTEXT_WORD_LIMIT = 75

## CFG_PLOTEXTRACTOR_CONTEXT_SENTENCE_LIMIT -- when extracting context of plots from
## TeX sources, this is the limitation of sentences in each direction. Default 2.
CFG_PLOTEXTRACTOR_CONTEXT_SENTENCE_LIMIT = 2
