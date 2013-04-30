## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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
import sys
from invenio.bibconvert_xslt_engine import convert
from invenio.invenio_connector import InvenioConnector
from invenio.bibdocfile import download_url
from invenio.bibmatch_engine import match_record as bibmatch_record


def convert_record(stylesheet="oaiarxiv2marcxml.xsl"):
    def _convert_record(obj, eng):
        """
        Will convert the object data, if XML, using the given stylesheet
        """
        obj.db_obj.last_task_name = 'convert_record'
        # Some check against MIME type perhaps?
        #if obj.type not in ("text/xml", "text/html"):
        #    print 'Not in text/xml or html'
            # raise HaltProcessing("Not valid object data type for XSLT processing."
            #                      "Type is %s" % (obj.type,))
        # Now for the conversion
        try:
            obj.data['data'] = convert(obj.data['data'], stylesheet)
            print 'Converted record'
        except:
            obj.error_msg = 'Could not convert record'
        print obj.db_obj.last_task_name
    return _convert_record


def download_fulltext():
    def _download_fulltext(obj, eng):
        """
        Will download the fulltext document
        """
        try:
            print obj.data.viewkeys()
            obj.db_obj.last_task_name = 'download_fulltext'
            url = download_url(obj.data['url'])
            print 'Downloaded URL'
            return url
        except KeyError:
            print 'DownloadFullTextTypeError'
            obj.db_obj.error_msg = 'Record does not include url'
            print obj.db_obj.error_msg
            # Log the error
    return _download_fulltext


def match_record():
    def _match_record(obj, eng):
        """
        Will try to find matches in stored records
        """
        obj.db_obj.last_task_name = 'match_record'
        try:

            from invenio.bibrecord import create_record
            rec = create_record(obj.db_obj.data['data'])
            print rec[0]
            print type(rec[0])
            cds = InvenioConnector("http://inspirehep.net")
            matches = bibmatch_record(obj.db_obj.id, rec[0], cds, [("title", "[245__a]")])
            if matches[1] or matches[2]:
                print 'Found Some'
                # we have ambiguous or fuzzy results
                # render holding pen corresponding template
            print matches
            obj.db_obj.extra_data['tasks_results']['match_record'] = matches
            print obj.db_obj.extra_data
            return matches
        except:
            print sys.exc_info()[0]
            print 'Error in bibmatch'
            obj.db_obj.error_msg = 'Could not run bibmatch'
    return _match_record


def filter_record():
    pass


def upload_record(obj):
    pass
    # return bibupload(obj, ? ? )
