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


def convert_record(stylesheet="oaiarxiv2marcxml.xsl"):
    def _convert_record(obj, eng):
        """
        Will convert the object data, if XML, using the given stylesheet
        """
        from invenio.bibconvert_xslt_engine import convert

        obj.extra_data["last_task_name"] = 'convert_record'
        eng.log_info("Starting conversion using %s stylesheet" %
                     (stylesheet,))
        eng.log_info("Type of data: %s" % (obj.data_type,))
        if obj.data_type == "text/xml":
            try:
                obj.data['data'] = convert(obj.data['data'], stylesheet)
            except:
                obj.extra_data["error_msg"] = 'Could not convert record'
                eng.log_error("Error: %s" % (obj.extra_data["error_msg"],))
                raise
        else:
            eng.halt("Data type not valid text/xml")

    _convert_record.__title__ = "Record conversion"
    _convert_record.__description__ = "This task converts a XML record."
    return _convert_record


def download_fulltext(obj, eng):
    """
    Will download the fulltext document
    """
    from invenio.bibdocfile import download_url

    obj.extra_data["last_task_name"] = 'download_fulltext'
    try:
        eng.log_info("Starting download of %s" % (obj.data['url']))
        url = download_url(obj.data['url'])
        obj.extra_data['tasks_results']['fulltext_url'] = url
    except KeyError:
        # Log the error
        obj.extra_data["error_msg"] = 'Record does not include url'
        eng.log.error("Error: %s" % (obj.extra_data["error_msg"],))

download_fulltext.__title__ = "Record conversion"
download_fulltext.__description__ = "This task downloads fulltext."


def match_record(obj, eng):
    """
    Will try to find matches in stored records
    """
    from invenio.bibrecord import create_record
    from invenio.bibmatch_engine import match_records

    obj.extra_data["last_task_name"] = 'match_record'
    rec = create_record(obj.data['data'])
    matches = match_records(records=[rec],
                            qrystrs=[("title", "[245__a]")])
    obj.extra_data['tasks_results']['match_record'] = matches
    if matches[2] or matches[3]:
        # we have ambiguous or fuzzy results
        # render holding pen corresponding template
        eng.halt("Match resolution needed")
    elif matches[0]:
        eng.log_info("Matching: new record")
    else:
        results = matches[1][0][1]
        eng.log_info("Matching: existing record %s" % (results,))

match_record.__title__ = "Record matching"
match_record.__description__ = "This task matches a XML record."


def print_record(obj, eng):
    eng.log_info(obj.data['data'])

print_record.__title__ = "Print Record"
print_record.__description__ = "Prints the record data to engine log"


def upload_record(mode="ir"):
    def _upload_record(obj, eng):
        from invenio.bibtask import task_low_level_submission

        eng.log_info("Saving data to temporary file for upload")
        filename = obj.save_to_file()
        params = ["-%s" % (mode,), filename]
        task_id = task_low_level_submission("bibupload", "bibworkflow",
                                            *tuple(params))
        eng.log_info("Submitted task #%s" % (task_id,))

    _upload_record.__title__ = "Upload Record"
    _upload_record.__description__ = "Uploads the record using BibUpload"
    return _upload_record
