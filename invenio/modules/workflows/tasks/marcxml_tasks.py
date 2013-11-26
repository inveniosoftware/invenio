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


def add_metadata_to_extra_data(obj, eng):
    """
    Creates bibrecord from object data and
    populates extra_data with metadata
    """
    from invenio.legacy.bibrecord import create_record, record_get_field_value
    record = create_record(obj.data)

    obj.extra_data['redis_search']['category'] =\
        record_get_field_value(record[0], '037', code='c')
    obj.extra_data['redis_search']['title'] =\
        record_get_field_value(record[0], '245', code='a')
    obj.extra_data['redis_search']['source'] =\
        record_get_field_value(record[0], '035', code='9')

add_metadata_to_extra_data.__title__ = "Metadata Extraction"
add_metadata_to_extra_data.__description__ = "Populates object's extra_data with metadata"


def approve_record(obj, eng):
    """
    Will add the approval widget to the record
    """
    obj.extra_data["last_task_name"] = 'Record Approval'
    try:
        obj.extra_data['message'] = 'Record needs approval. Click on widget to resolve.'
        obj.extra_data['widget'] = 'approval_widget'
        eng.halt("Record needs approval")
    except KeyError:
        # Log the error
        obj.extra_data["error_msg"] = 'Could not assign widget'

approve_record.__title__ = "Record Approval"
approve_record.__description__ = "This task assigns the approval widget to a record."


def convert_record(stylesheet="oaiarxiv2marcxml.xsl"):
    def _convert_record(obj, eng):
        """
        Will convert the object data, if XML, using the given stylesheet
        """
        from invenio.legacy.bibconvert.xslt_engine import convert

        obj.extra_data["last_task_name"] = 'Convert Record'
        try:
            obj.data = convert(obj.data, stylesheet)
        except:
            obj.extra_data["error_msg"] = 'Could not convert record'
            raise

    _convert_record.__title__ = "Convert Record"
    _convert_record.__description__ = "This task converts a XML record."
    return _convert_record


def download_fulltext(obj, eng):
    """
    Will download the fulltext document
    """
    from invenio.legacy.bibdocfile.api import download_url

    obj.extra_data["last_task_name"] = 'Download Fulltext'
    try:
        eng.log_info("Starting download of %s" % (obj.data['url']))
        url = download_url(obj.data['url'])
        obj.extra_data['tasks_results']['fulltext_url'] = url
    except KeyError:
        # Log the error
        obj.extra_data["error_msg"] = 'Record does not include url'
        eng.log.error("Error: %s" % (obj.extra_data["error_msg"],))

download_fulltext.__title__ = "Fulltext Download"
download_fulltext.__description__ = "This task downloads fulltext."


def match_record(obj, eng):
    """
    Will try to find matches in stored records
    """
    from invenio.legacy.bibrecord import create_record
    from invenio.legacy.bibmatch.engine import match_records

    obj.extra_data["last_task_name"] = 'Bibmatch Record'
    rec = create_record(obj.data)
    matches = match_records(records=[rec],
                            qrystrs=[("title", "[245__a]")])
    obj.extra_data['tasks_results']['match_record'] = matches
    if matches[2] or matches[3]:
        # we have ambiguous or fuzzy results
        # render holding pen corresponding template
        eng.halt("Match resolution needed")
    elif matches[0]:
        pass
    else:
        results = matches[1][0][1]
    obj.extra_data['widget'] = 'bibmatch_widget'

match_record.__title__ = "Bibmatch Record"
match_record.__description__ = "This task matches a XML record."


def print_record(obj, eng):
    eng.log_info(obj.get_data())

print_record.__title__ = "Print Record"
print_record.__description__ = "Prints the record data to engine log"


def upload_record(mode="ir"):
    def _upload_record(obj, eng):
        from invenio.legacy.bibsched.bibtask import task_low_level_submission

        obj.extra_data["last_task_name"] = 'Upload Record'

        eng.log_info("Saving data to temporary file for upload")
        filename = obj.save_to_file()
        params = ["-%s" % (mode,), filename]
        task_id = task_low_level_submission("bibupload", "bibworkflow",
                                            *tuple(params))
        eng.log_info("Submitted task #%s" % (task_id,))

    _upload_record.__title__ = "Upload Record"
    _upload_record.__description__ = "Uploads the record using BibUpload"
    return _upload_record
