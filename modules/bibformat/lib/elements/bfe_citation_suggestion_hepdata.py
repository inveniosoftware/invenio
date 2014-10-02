# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
"""BibFormat element - Prints the citation suggestion
"""
__revision__ = "$Id$"

import re


def format_element(bfo):
    """
    Prints the citation suggestion. Only for Hepdata and Dataverse by now.
    Languages/repos will come.
    """

    publisher = bfo.field("520__9")
    return cite_as(bfo, publisher)


def cite_as(bfo, publisher):
    """
    HepData format example:
        Cite as: The ATLAS Collaboration (2013) HepData, doi: 10.1234/123456
    Dataverse format example:
        Cranmer, Kyle; Allanach, Ben; Lester, Christopher; Weber, Arne, "Replication data for:
        "Natural Priors, CMSSM Fits and LHC Weather Forecasts"", http://hdl.handle.net/1902.1/21804
    INSPIRE format example:
        Cite as: The ATLAS Collaboration (2013) INSPIRE, doi: 10.1234/123456
    """

    from invenio.bibformat_engine import BibFormatObject

    if publisher == "Dataverse":
        return dataverse_cite_as(bfo)

    colls = []
    for coll in bfo.fields("710__g"):
        if coll not in colls:
            colls.append(coll)

    parent_recid = int(bfo.field("786__w"))
    bfo_parent = BibFormatObject(parent_recid)
    year = get_year(bfo_parent)

    if publisher == 'HEPDATA':
        publisher = 'HepData'
    elif publisher == "INSPIRE":
        publisher == "INSPIRE-HEP"

    pid_type = bfo.field("0247_2")
    pid = bfo.field("0247_a")

    out = ''
    out += "<b>Cite as: </b>"
    if colls:
        out += str(colls[0])
    if year:
        out += ' ( ' + str(year) + ' ) '
    out += publisher + ', '

    if pid_type == 'DOI':
        out += '<a href="http://doi.org/' + pid + '" target="_blank" > http://doi.org/' + pid + '</a>'
    elif pid_type == 'HDL':
        out += '<a href="http://hdl.handle.net/' + pid + '" target="_blank" > http://hdl.handle.net/' + pid + '</a>'
    elif pid_type == '':
        out += '[no persistent identifier assigned]'

    return out


def dataverse_cite_as(bfo):
    """
    Dataverse format example:
        Cranmer, Kyle; Allanach, Ben; Lester, Christopher; Weber, Arne, "Replication data for: 
        "Natural Priors, CMSSM Fits and LHC Weather Forecasts"", http://hdl.handle.net/1902.1/21804
    """
    authors = ""
    for auth in bfo.fields("100__a"):
        authors += str(auth) + "; "
    out = ''
    out += ("<b>Cite as: </b>")
    out += authors[:-2] + ", "

    title = bfo.field("245__a")
    out += '"' + title + '", <br /> ' 

    pid_type = bfo.field("0247_2")
    pid = bfo.field("0247_a")

    if pid_type == 'HDL':
        out += '<a href="http://hdl.handle.net/' + pid + '" target="_blank" > http://hdl.handle.net/' + pid + '</a>'
    elif pid_type == '':
        out += '[no persistent identifier assigned]'

    return out


def get_year(bfo):
    """
    Returns a year of publication for the best available date. Returns None if none found.

    @param bfo: BibFormatObject for current record
    @type nfo: object

    @return: integer if the year is found, otherwise None.
    """
    from invenio.bibformat_elements.bfe_INSPIRE_arxiv import get_arxiv

    #true date
    date = bfo.field('269__c')
    if date:
        return date[:4]

    #arxiv date
    arxiv = get_arxiv(bfo,category="no")
    if arxiv:
        date = re.search('(\d+)',arxiv[0]).groups()[0]
        if len(date) >=4:
            year = date[0:2]
            if year > '90':
                year='19'+year
            else:
                year='20'+year
            return year

    #journal year
    date = bfo.field('773__y')
    if date:
        return date[:4]

    #date added
    date = bfo.field('961__x')
    if date:
        return date[:4]

    #book year
    date = bfo.field('260__c')
    if date:
        return date[:4]

    return None

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
