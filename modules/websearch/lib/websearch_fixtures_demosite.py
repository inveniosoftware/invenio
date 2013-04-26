# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

from invenio.config import CFG_SITE_NAME
from fixture import DataSet


class ExternalcollectionData(DataSet):

    class amazon:
        id = 1
        name = 'Amazon'

    class CERNEDMS:
        id = 2
        name = 'CERN EDMS'

    class CERNIndico:
        id = 3
        name = 'CERN Indico'

    class CERNIntranet:
        id = 4
        name = 'CERN Intranet'

    class citeSeer:
        id = 5
        name = 'CiteSeer'

    class googleBooks:
        id = 6
        name = 'Google Books'

    class googleScholar:
        id = 7
        name = 'Google Scholar'

    class googleWeb:
        id = 8
        name = 'Google Web'

    class IEC:
        id = 9
        name = 'IEC'

    class IHS:
        id = 10
        name = 'IHS'

    class INSPEC:
        id = 11
        name = 'INSPEC'

    class ISO:
        id = 12
        name = 'ISO'

    class KISSBooksJournals:
        id = 13
        name = 'KISS Books/Journals'

    class KISSPreprints:
        id = 14
        name = 'KISS Preprints'

    class NEBIS:
        id = 15
        name = 'NEBIS'

    class SLACLibraryCatalog:
        id = 16
        name = 'SLAC Library Catalog'

    class SPIRESHEP:
        id = 17
        name = 'SPIRES HEP'

    class scirus:
        id = 18
        name = 'Scirus'

    class atlantisInstituteBooks:
        id = 19
        name = 'Atlantis Institute Books'

    class atlantisInstituteArticles:
        id = 20
        name = 'Atlantis Institute Articles'


class CollectionDataDefault(DataSet):
    class siteCollection:
        id = 1
        name = CFG_SITE_NAME
        dbquery = None


class CollectionData(CollectionDataDefault):

    class siteCollection:
        id = 1
        name = CFG_SITE_NAME
        dbquery = None
        externalcollections_0 = [
            ExternalcollectionData.atlantisInstituteBooks,
            ExternalcollectionData.atlantisInstituteArticles
        ]
        externalcollections_1 = [
            ExternalcollectionData.amazon,
            ExternalcollectionData.CERNEDMS,
            ExternalcollectionData.CERNIndico,
            ExternalcollectionData.CERNIntranet,
            ExternalcollectionData.citeSeer,
            ExternalcollectionData.googleBooks,
            ExternalcollectionData.googleScholar,
            ExternalcollectionData.googleWeb,
            ExternalcollectionData.IEC,
            ExternalcollectionData.IHS,
            ExternalcollectionData.INSPEC,
            ExternalcollectionData.ISO,
            ExternalcollectionData.KISSBooksJournals,
            ExternalcollectionData.KISSPreprints,
            ExternalcollectionData.NEBIS,
            ExternalcollectionData.SLACLibraryCatalog,
            ExternalcollectionData.SPIRESHEP,
            ExternalcollectionData.scirus
        ]

    class preprints:
        id = 2
        name = 'Preprints'
        dbquery = 'collection:PREPRINT'
        names = {
            ('en', 'ln'): u'Preprints',
            ('fr', 'ln'): u'Prétirages',
            ('de', 'ln'): u'Preprints',
            ('es', 'ln'): u'Preprints',
            ('ca', 'ln'): u'Preprints',
            ('pl', 'ln'): u'Preprinty',
            ('pt', 'ln'): u'Preprints',
            ('it', 'ln'): u'Preprint',
            ('ru', 'ln'): u'Препринты',
            ('sk', 'ln'): u'Preprinty',
            ('cs', 'ln'): u'Preprinty',
            ('no', 'ln'): u'Førtrykk',
            ('sv', 'ln'): u'Preprints',
            ('el', 'ln'): u'Προδημοσιεύσεις',
            ('uk', 'ln'): u'Препринти',
            ('ja', 'ln'): u'プレプリント',
            ('bg', 'ln'): u'Препринти',
            ('hr', 'ln'): u'Preprinti',
            ('zh_CN', 'ln'): u'预印',
            ('zh_TW', 'ln'): u'預印',
            ('hu', 'ln'): u'Preprintek',
            ('af', 'ln'): u'Pre-drukke',
            ('gl', 'ln'): u'Preprints',
            ('ro', 'ln'): u'Preprinturi',
            ('rw', 'ln'): u'Preprints',
            ('ka', 'ln'): u'პრეპრინტები',
            ('lt', 'ln'): u'Rankraščiai',
            ('ar', 'ln'): u'مسودات'
        }
        externalcollections_0 = [
            ExternalcollectionData.atlantisInstituteBooks,
            ExternalcollectionData.atlantisInstituteArticles
        ]
        externalcollections_1 = [
            ExternalcollectionData.amazon,
            ExternalcollectionData.CERNEDMS,
            ExternalcollectionData.CERNIntranet,
            ExternalcollectionData.googleBooks,
            ExternalcollectionData.googleScholar,
            ExternalcollectionData.googleWeb,
            ExternalcollectionData.IEC,
            ExternalcollectionData.IHS,
            ExternalcollectionData.INSPEC,
            ExternalcollectionData.ISO,
            ExternalcollectionData.NEBIS,
            ExternalcollectionData.SLACLibraryCatalog
        ]
        externalcollections_2 = [
            ExternalcollectionData.CERNIndico,
            ExternalcollectionData.citeSeer,
            ExternalcollectionData.KISSBooksJournals,
            ExternalcollectionData.KISSPreprints,
            ExternalcollectionData.SPIRESHEP,
            ExternalcollectionData.scirus
        ]

    class books(siteCollection):
        id = 3
        name = 'Books'
        dbquery = 'collection:BOOK'

    class theses(siteCollection):
        id = 4
        name = 'Theses'
        dbquery = 'collection:THESIS'

    class reports(siteCollection):
        id = 5
        name = 'Reports'
        dbquery = 'collection:REPORT'

    class articles(preprints):
        id = 6
        name = 'Articles'
        dbquery = 'collection:ARTICLE'

    class pictures(siteCollection):
        id = 8
        name = 'Pictures'
        dbquery = 'collection:PICTURE'

    class CERNDivisions(siteCollection):
        id = 9
        name = 'CERN Divisions'
        dbquery = None

    class CERNExperiments(siteCollection):
        id = 10
        name = 'CERN Experiments'
        dbquery = None

    class theoreticalPhysics(siteCollection):
        id = 11
        name = 'Theoretical Physics'
        dbquery = None

    class experimentalPhysics(siteCollection):
        id = 12
        name = 'Experimental Physics'
        dbquery = None

    class ISOLDE(siteCollection):
        id = 13
        name = 'ISOLDE'
        dbquery = 'experiment:ISOLDE'

    class ALEPH(siteCollection):
        id = 14
        name = 'ALEPH'
        dbquery = 'experiment:ALEPH'

    class articlesPreprints(preprints):
        id = 15
        name = 'Articles & Preprints'
        dbquery = None

    class booksReports(siteCollection):
        id = 16
        name = 'Books & Reports'
        dbquery = None

    class multimediaArts(siteCollection):
        id = 17
        name = 'Multimedia & Arts'
        dbquery = None

    class poetry(siteCollection):
        id = 18
        name = 'Poetry'
        dbquery = 'collection:POETRY'

    class atlantisTimesNews:
        id = 19
        name = 'Atlantis Times News'
        dbquery = 'collection:ATLANTISTIMESNEWS'

    class atlantisTimesArts:
        id = 20
        name = 'Atlantis Times Arts'
        dbquery = 'collection:ATLANTISTIMESARTS'

    class atlantisTimesScience:
        id = 21
        name = 'Atlantis Times Science'
        dbquery = 'collection:ATLANTISTIMESSCIENCE'

    class atlantisTimes:
        id = 22
        name = 'Atlantis Times'
        dbquery = None

    class atlantisInstituteBooks:
        id = 23
        name = 'Atlantis Institute Books'
        dbquery = 'hostedcollection:'

    class atlantisInstituteArticles:
        id = 24
        name = 'Atlantis Institute Articles'
        dbquery = 'hostedcollection:'

    class atlantisTimesDrafts:
        id = 25
        name = 'Atlantis Times Drafts'
        dbquery = 'collection:ATLANTISTIMESSCIENCEDRAFT or collection:ATLANTISTIMESARTSDRAFT or collection:ATLANTISTIMESNEWSDRAFT'


class CollectionCollectionData(DataSet):

    class siteCollection_articlesPreprints:
        dad = CollectionData.siteCollection
        son = CollectionData.articlesPreprints
        score = 60
        type = 'r'

    class siteCollection_booksReports:
        dad = CollectionData.siteCollection
        son = CollectionData.booksReports
        score = 50
        type = 'r'

    class siteCollection_multimediaArts:
        dad = CollectionData.siteCollection
        son = CollectionData.multimediaArts
        score = 40
        type = 'r'

    class siteCollection_CERNDivisions:
        dad = CollectionData.siteCollection
        son = CollectionData.CERNDivisions
        score = 20
        type = 'v'

    class siteCollection_CERNExperiments:
        dad = CollectionData.siteCollection
        son = CollectionData.CERNExperiments
        score = 10
        type = 'v'

    class CERNExperiments_ISOLDE:
        dad = CollectionData.CERNExperiments
        son = CollectionData.ISOLDE
        score = 10
        type = 'r'

    class CERNExperiments_ALEPH:
        dad = CollectionData.CERNExperiments
        son = CollectionData.ALEPH
        score = 20
        type = 'r'

    class articlesPreprints_preprints:
        dad = CollectionData.articlesPreprints
        son = CollectionData.preprints
        score = 10
        type = 'r'

    class articlesPreprints_articles:
        dad = CollectionData.articlesPreprints
        son = CollectionData.articles
        score = 20
        type = 'r'

    class booksReports_books:
        dad = CollectionData.booksReports
        son = CollectionData.books
        score = 30
        type = 'r'

    class booksReports_theses:
        dad = CollectionData.booksReports
        son = CollectionData.theses
        score = 20
        type = 'r'

    class booksReports_reports:
        dad = CollectionData.booksReports
        son = CollectionData.reports
        score = 10
        type = 'r'

    class multimediaArts_pictures:
        dad = CollectionData.multimediaArts
        son = CollectionData.pictures
        score = 30
        type = 'r'

    class multimediaArts_poetry:
        dad = CollectionData.multimediaArts
        son = CollectionData.poetry
        score = 20
        type = 'r'

    class multimediaArts_atlantisTimes:
        dad = CollectionData.multimediaArts
        son = CollectionData.atlantisTimes
        score = 10
        type = 'r'

    class atlantisTimes_atlantisTimesNews:
        dad = CollectionData.atlantisTimes
        son = CollectionData.atlantisTimesNews
        score = 30
        type = 'r'

    class atlantisTimes_atlantisTimesArts:
        dad = CollectionData.atlantisTimes
        son = CollectionData.atlantisTimesArts
        score = 20
        type = 'r'

    class atlantisTimes_atlantisTimesScience:
        dad = CollectionData.atlantisTimes
        son = CollectionData.atlantisTimesScience
        score = 10
        type = 'r'

    class CERNDivisions_theoreticalPhysics:
        dad = CollectionData.CERNDivisions
        son = CollectionData.theoreticalPhysics
        score = 10
        type = 'r'

    class CERNDivisions_experimentalPhysics:
        dad = CollectionData.CERNDivisions
        son = CollectionData.experimentalPhysics
        score = 20
        type = 'r'
