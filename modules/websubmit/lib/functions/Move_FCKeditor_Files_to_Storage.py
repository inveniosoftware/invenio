## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
"""
WebSubmit function - Replaces the links that have been created by the
FCKeditor
"""
__revision__ = "$Id$"

import re
import os
import urllib
from invenio.bibdocfile import decompose_file
from invenio.config import \
     CFG_SITE_URL, \
     CFG_PREFIX

re_fckeditor_link = re.compile('"' + CFG_SITE_URL + \
                               r'/submit/getattachedfile/(?P<uid>\d+)/(?P<type>(image|file|media|flash))/(?P<filename>.*?)"')

def Move_FCKeditor_Files_to_Storage(parameters, curdir, form, user_info=None):
    """
    Moves the files uploaded via the FCKeditor that are linked to
    the given field. Replace these links with URLs 'local' to the
    record (recid/files/).

    When attaching a file, the editor post the file to a temporary
    drop box accessible via a URL for previews. We want to fetch
    these files (via FFT) to integrate them to the record, and change
    the links in the record to point to the integrated files.

    The function *MUST* be run BEFORE the record has been created
    (with Make_Record.py or Make_Modify_Record.py).

    You *HAVE* to include the created FFT field (output of this
    function) in your BibConvert template.

    Parameters:

    input_fields - *str* a comma separated list of file names that
                   should be processed by this element. Eg:
                   'ABSE,ABSF' in order to process values of the
                   English and French abstracts
    """
    input_filenames = [input_filename for input_filename in \
                       parameters['input_fields'].split(',') if \
                       os.path.exists(curdir + os.sep + input_filename)]

    processed_paths = []

    for input_filename in input_filenames:
        input_file = file(curdir + os.sep + input_filename)
        input_string = input_file.read()
        input_file.close()

        def translate_link(match_obj):
            """Replace FCKeditor link by 'local' record link. Also
            create the FFT for that link"""
            file_type = match_obj.group('type')
            file_name = match_obj.group('filename')
            uid = match_obj.group('uid')
            dummy, name, extension = decompose_file(file_name)
            new_url = build_url(sysno, name, file_type, extension)
            original_location = match_obj.group()[1:-1]
            icon_location = original_location
            # Prepare FFT that will fetch the file (+ the original
            # file in the case of images)
            if file_type == 'image':
                # Does original file exists, or do we just have the
                # icon? We expect the original file at a well defined
                # location
                possible_original_path = os.path.join(CFG_PREFIX,
                                                      'var', 'tmp',
                                                      'attachfile',
                                                      uid,
                                                      file_type,
                                                      'original',
                                                      file_name)
                if os.path.exists(possible_original_path):
                    icon_location = original_location
                    original_location = possible_original_path
                    new_url = build_url(sysno, name,
                                        file_type, extension, is_icon=True)

            docname = build_docname(name, file_type, extension)
            if original_location not in processed_paths:
                # Must create an FFT only if we have not yet processed
                # the file. This can happen if same image exists on
                # the same page (either in two different FCKeditor
                # instances, or twice in the HTML)
                processed_paths.append(original_location)
                write_fft(original_location,
                          docname,
                          icon_location,
                          doctype=file_type)
            return '"' + new_url + '"'

        output_string = re_fckeditor_link.sub(translate_link, input_string)
        output_file = file(curdir + os.sep + input_filename, 'w')
        output_file.write(output_string)
        output_file.close()

def build_url(sysno, name, file_type, extension, is_icon=False):
    """
    Build the local URL to the file with given parameters

    @param sysno: record ID
    @name name: base name of the file
    @param file_type: as chosen by FCKeditor: 'File', 'Image', 'Flash', 'Media'
    @param extension: file extension, including '.'
    """
    return CFG_SITE_URL + '/record/' + str(sysno) + \
           '/files/' + build_docname(name, file_type, extension) + \
           (is_icon and '?subformat=icon' or '')

def build_docname(name, file_type, extension):
    """
    Build the docname of the file.

    In order to ensure uniqueness of the docname, we have to prefix
    the filename with the filetype: FCKeditor takes care of filenames
    uniqueness for each diffrent filetype, but not that files in
    different filetypes will not have the same name
    """
    return name + '_' + file_type + extension

def write_fft(file_location, docname, icon_location=None, doctype="image"):
    """
    Append a new FFT for the record. Write the result to the FFT file on disk.

    May only be used for files attached with FCKeditor (i.e. URLs
    matching re_fckeditor_link)
    """
    if file_location.startswith(CFG_SITE_URL):
        # FCKeditor does not url-encode filenames, and FFT does not
        # like URLs that are not quoted. So do it now (but only for
        # file name, in URL context!)
        url_parts = file_location.split("/")
        try:
            file_location = "/".join(url_parts[:-1]) + \
                            '/' + urllib.quote(url_parts[-1])
        except:
            pass

    if icon_location.startswith(CFG_SITE_URL):
        # Ditto quote file name
        url_parts = icon_location.split("/")
        try:
            icon_location = "/".join(url_parts[:-1]) + \
                            '/' + urllib.quote(url_parts[-1])
        except:
            pass

    icon_subfield = ''
    if icon_location:
        icon_subfield = '<subfield code="x">%s</subfield>' % icon_location

    fft_file = file(os.path.join(curdir, 'FFT'), 'a')
    fft_file.write("""
    <datafield tag="FFT" ind1=" " ind2=" ">
        <subfield code="a">%(location)s</subfield>
        <subfield code="n">%(docname)s</subfield>
        <subfield code="t">%(doctype)s</subfield>
        %(icon_subfield)s
    </datafield>""" % {'location': file_location,
                       'icon_subfield': icon_subfield,
                       'doctype': doctype,
                       'docname': docname})
    fft_file.close()
