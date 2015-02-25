# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2012 CERN.
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
"""WebSubmit function - Batch photo uploader

To be used with WebSubmit element 'Upload_Photos' or one of its
derivatives in order to create a batch photos uploader.

Requirements:
=============
 JQuery:
  - jquery.min.js

 JQuery UI:
  - jquery-ui.min.js
  - UI "base" theme:
      - jquery.ui.slider.css
      - jquery.ui.core.css
      - jquery.ui.theme.css
      - images

 Uploadify 2.0.1 (JQuery plugin):
  - jquery.uploadify.min.js
  - sfwobject.js
  - uploadify.css
  - cancel.png
  - uploadify.swf, uploadify.allglyphs.swf and uploadify.fla
"""

import os
import time
import re
from urllib import quote
from cgi import escape
from six import iteritems

from invenio.legacy.bibdocfile.api import BibRecDocs, InvenioBibDocFileError
from invenio.config import CFG_BINDIR, CFG_SITE_URL
from invenio.legacy.dbquery import run_sql
from invenio.legacy.websubmit.icon_creator import create_icon, InvenioWebSubmitIconCreatorError
from invenio.legacy.bibdocfile.config import CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT

def Move_Photos_to_Storage(parameters, curdir, form, user_info=None):
    """
    The function moves files received from the submission's form
    through the PHOTO_MANAGER element and its asynchronous uploads at
    CFG_SITE_URL/submit/uploadfile.

    Parameters:
        @iconsize - Seperate multiple sizes with commas. The ImageMagick geometry inputs are supported.
              Use type 'geometry' as defined in ImageMagick.
              (eg. 320 or 320x240 or 100> or 5%)
              Example: "180>,700>" will create two icons, one with maximum dimension 180px, one 700px
        @iconformat - Allowed extensions (as defined in websubmit_icon_creator.py) are:
                "pdf", "gif", "jpg",
                "jpeg", "ps", "png", "bmp"
                "eps", "epsi", "epsf"

    The PHOTO_MANAGER elements builds the following file organization
    in the directory curdir::

                                     curdir/
                                        |
         ______________________________________________________________________
        |                                   |                                  |
      files/                         PHOTO_MANAGER_ICONS                     icons/
        |                            PHOTO_MANAGER_ORDER                       |
     (user id)/                      PHOTO_MANAGER_DELETE                  (user id)/
        |                            PHOTO_MANAGER_NEW                         |
     NewFile/                        PHOTO_MANAGER_DESCRIPTION_X           NewFile/
        |                                                                      |
        _______________________                                      _____________________
       |            |          |                                    |          |          |
     photo1.jpg  myPhoto.gif   ...                             photo1.jpg  myPhoto.gif   ...


    where the files are:
      - PHOTO_MANAGER_ORDER: ordered list of file IDs. One per line.

      - PHOTO_MANAGER_ICONS: mappings from file IDs to URL of the icons.
                             One per line. Separator: /

      - PHOTO_MANAGER_NEW: mapping from file ID to filename on disk. Only
                           applicable to files that have just been
                           uploaded (i.e. not bibdocfiles). One per
                           line. Separator: /

      - PHOTO_MANAGER_DELETE: list of files IDs that must be deleted. One
                               per line

      - PHOTO_MANAGER_DESCRIPTION_X, where X is file ID: contains photos
                                     descriptions (one per file)

    """
    global sysno

    icon_sizes = parameters.get('iconsize').split(',')
    icon_format = parameters.get('iconformat')
    if not icon_format:
        icon_format = 'gif'

    PHOTO_MANAGER_ICONS = read_param_file(curdir, 'PHOTO_MANAGER_ICONS', split_lines=True)
    photo_manager_icons_dict = dict([value.split('/', 1) \
                                     for value in PHOTO_MANAGER_ICONS \
                                     if '/' in value])
    PHOTO_MANAGER_ORDER = read_param_file(curdir, 'PHOTO_MANAGER_ORDER', split_lines=True)
    photo_manager_order_list = [value for value in PHOTO_MANAGER_ORDER if value.strip()]
    PHOTO_MANAGER_DELETE = read_param_file(curdir, 'PHOTO_MANAGER_DELETE', split_lines=True)
    photo_manager_delete_list = [value for value in PHOTO_MANAGER_DELETE if value.strip()]
    PHOTO_MANAGER_NEW = read_param_file(curdir, 'PHOTO_MANAGER_NEW', split_lines=True)
    photo_manager_new_dict = dict([value.split('/', 1) \
                               for value in PHOTO_MANAGER_NEW \
                               if '/' in value])

    ## Create an instance of BibRecDocs for the current recid(sysno)
    bibrecdocs = BibRecDocs(sysno)
    for photo_id in photo_manager_order_list:
        photo_description = read_param_file(curdir, 'PHOTO_MANAGER_DESCRIPTION_' + photo_id)
        # We must take different actions depending if we deal with a
        # file that already exists, or if it is a new file
        if photo_id in photo_manager_new_dict.keys():
            # New file
            if photo_id not in photo_manager_delete_list:
                filename = photo_manager_new_dict[photo_id]
                filepath = os.path.join(curdir, 'files', str(user_info['uid']),
                                        'NewFile', filename)
                icon_filename = os.path.splitext(filename)[0] + ".gif"
                fileiconpath = os.path.join(curdir, 'icons', str(user_info['uid']),
                                            'NewFile', icon_filename)

                # Add the file
                if os.path.exists(filepath):
                    _do_log(curdir, "Adding file %s" % filepath)
                    bibdoc = bibrecdocs.add_new_file(filepath, doctype="picture", never_fail=True)
                    has_added_default_icon_subformat_p = False
                    for icon_size in icon_sizes:
                        # Create icon if needed
                        try:
                            (icon_path, icon_name) = create_icon(
                                { 'input-file'           : filepath,
                                  'icon-name'            : icon_filename,
                                  'icon-file-format'     : icon_format,
                                  'multipage-icon'       : False,
                                  'multipage-icon-delay' : 100,
                                  'icon-scale'           : icon_size, # Resize only if width > 300
                                  'verbosity'            : 0,
                                  })
                            fileiconpath = os.path.join(icon_path, icon_name)
                        except InvenioWebSubmitIconCreatorError as e:
                            _do_log(curdir, "Icon could not be created to %s: %s" % (filepath, e))
                            pass
                        if os.path.exists(fileiconpath):
                            try:
                                if not has_added_default_icon_subformat_p:
                                    bibdoc.add_icon(fileiconpath)
                                    has_added_default_icon_subformat_p = True
                                    _do_log(curdir, "Added icon %s" % fileiconpath)
                                else:
                                    icon_suffix = icon_size.replace('>', '').replace('<', '').replace('^', '').replace('!', '')
                                    bibdoc.add_icon(fileiconpath, subformat=CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT + "-" + icon_suffix)
                                    _do_log(curdir, "Added icon %s" % fileiconpath)
                            except InvenioBibDocFileError as e:
                                # Most probably icon already existed.
                                pass

                    if photo_description and bibdoc:
                        for file_format in [bibdocfile.get_format() \
                                       for bibdocfile in bibdoc.list_latest_files()]:
                            bibdoc.set_comment(photo_description, file_format)
                            _do_log(curdir, "Added comment %s" % photo_description)
        else:
            # Existing file
            bibdocname = bibrecdocs.get_docname(int(photo_id))
            if photo_id in photo_manager_delete_list:
                # In principle we should not get here. but just in case...
                bibrecdocs.delete_bibdoc(bibdocname)
                _do_log(curdir, "Deleted  %s" % bibdocname)
            else:
                bibdoc = bibrecdocs.get_bibdoc(bibdocname)
                for file_format in [bibdocfile.get_format() \
                               for bibdocfile in bibdoc.list_latest_files()]:
                    bibdoc.set_comment(photo_description, file_format)
                    _do_log(curdir, "Added comment %s" % photo_description)

    # Now delete requeted files
    for photo_id in photo_manager_delete_list:
        try:
            bibdocname = bibrecdocs.get_docname(int(photo_id))
            bibrecdocs.delete_bibdoc(bibdocname)
            _do_log(curdir, "Deleted  %s" % bibdocname)
        except:
            # we tried to delete a photo that does not exist (maybe already deleted)
            pass

    # Update the MARC
    _do_log(curdir, "Asking bibdocfile to fix marc")
    bibdocfile_bin = os.path.join(CFG_BINDIR, 'bibdocfile --yes-i-know')
    os.system(bibdocfile_bin + " --fix-marc --recid=" + str(sysno))

    # Delete the HB BibFormat cache in the DB, so that the fulltext
    # links do not point to possible dead files
    run_sql("DELETE LOW_PRIORITY from bibfmt WHERE format='HB' AND id_bibrec=%s", (sysno,))

    return ""

def read_param_file(curdir, param, split_lines=False):
    "Helper function to access files in submission dir"
    param_value = ""
    path = os.path.join(curdir, param)
    try:
        if os.path.abspath(path).startswith(curdir):
            fd = file(path)
            if split_lines:
                param_value = [line.strip() for line in fd.readlines()]
            else:
                param_value = fd.read()
            fd.close()
    except Exception as e:
        _do_log(curdir, 'Could not read %s: %s' % (param, e))
        pass
    return param_value

def _do_log(log_dir, msg):
    """
    Log what we have done, in case something went wrong.
    Nice to compare with bibdocactions.log

    Should be removed when the development is over.
    """
    log_file = os.path.join(log_dir, 'performed_actions.log')
    file_desc = open(log_file, "a+")
    file_desc.write("%s --> %s\n" %(time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    file_desc.close()

def get_session_id(req, uid, user_info):
    """
    Returns by all means the current session id of the user.

    Raises ValueError if cannot be found
    """
    # Get the session id
    ## This can be later simplified once user_info object contain 'sid' key
    session_id = None
    try:
        try:
            from flask import session
            session_id = session.sid
        except AttributeError as e:
            # req was maybe not available (for eg. when this is run
            # through Create_Modify_Interface.py)
            session_id = user_info['session']
    except Exception as e:
        raise ValueError("Cannot retrieve user session")

    return session_id

def create_photos_manager_interface(sysno, session_id, uid,
                                    doctype, indir, curdir, access,
                                    can_delete_photos=True,
                                    can_reorder_photos=True,
                                    can_upload_photos=True,
                                    editor_width=None,
                                    editor_height=None,
                                    initial_slider_value=100,
                                    max_slider_value=200,
                                    min_slider_value=80):
    """
    Creates and returns the HTML of the photos manager interface for
    submissions.

    @param sysno: current record id
    @param session_id: user session_id (as retrieved by get_session_id(...) )
    @param uid: user id
    @param doctype: doctype of the submission
    @param indir: submission "indir"
    @param curdir: submission "curdir"
    @param access: submission "access"
    @param can_delete_photos: if users can delete photos
    @param can_reorder_photos: if users can reorder photos
    @param can_upload_photos: if users can upload photos
    @param editor_width: width (in pixels) of the editor
    @param editor_height: height (in pixels) of the editor
    @param initial_slider_value: initial value of the photo size slider
    @param max_slider_value: max value of the photo size slider
    @param min_slider_value: min value of the photo size slider
    """
    out = ''

    PHOTO_MANAGER_ICONS = read_param_file(curdir, 'PHOTO_MANAGER_ICONS', split_lines=True)
    photo_manager_icons_dict = dict([value.split('/', 1) for value in PHOTO_MANAGER_ICONS if '/' in value])
    PHOTO_MANAGER_ORDER = read_param_file(curdir, 'PHOTO_MANAGER_ORDER', split_lines=True)
    photo_manager_order_list = [value for value in PHOTO_MANAGER_ORDER if value.strip()]
    PHOTO_MANAGER_DELETE = read_param_file(curdir, 'PHOTO_MANAGER_DELETE', split_lines=True)
    photo_manager_delete_list = [value for value in PHOTO_MANAGER_DELETE if value.strip()]
    PHOTO_MANAGER_NEW = read_param_file(curdir, 'PHOTO_MANAGER_NEW', split_lines=True)
    photo_manager_new_dict = dict([value.split('/', 1) for value in PHOTO_MANAGER_NEW if '/' in value])
    photo_manager_descriptions_dict = {}

    # Compile a regular expression that can match the "default" icon,
    # and not larger version.
    CFG_BIBDOCFILE_ICON_SUBFORMAT_RE_DEFAULT = re.compile(CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT + '\Z')

    # Load the existing photos from the DB if we are displaying
    # this interface for the first time, and if a record exists
    if sysno and not PHOTO_MANAGER_ORDER:
        bibarchive = BibRecDocs(sysno)
        for doc in bibarchive.list_bibdocs():
            if doc.get_icon() is not None:
                original_url = doc.list_latest_files()[0].get_url()
                doc_id = str(doc.get_id())
                icon_url = doc.get_icon(subformat_re=CFG_BIBDOCFILE_ICON_SUBFORMAT_RE_DEFAULT).get_url() # Get "default" icon
                description = ""
                for bibdoc_file in doc.list_latest_files():
                    #format = bibdoc_file.get_format().lstrip('.').upper()
                    #url = bibdoc_file.get_url()
                    #photo_files.append((format, url))
                    if not description and bibdoc_file.get_comment():
                        description = escape(bibdoc_file.get_comment())
                name = bibarchive.get_docname(doc.id)
                photo_manager_descriptions_dict[doc_id] = description
                photo_manager_icons_dict[doc_id] = icon_url
                photo_manager_order_list.append(doc_id) # FIXME: respect order

    # Prepare the list of photos to display.
    photos_img = []
    for doc_id in photo_manager_order_list:
        if doc_id not in photo_manager_icons_dict:
            continue
        icon_url = photo_manager_icons_dict[doc_id]
        if PHOTO_MANAGER_ORDER:
            # Get description from disk only if some changes have been done
            description = escape(read_param_file(curdir, 'PHOTO_MANAGER_DESCRIPTION_' + doc_id))
        else:
            description = escape(photo_manager_descriptions_dict[doc_id])
        photos_img.append('''
        <li id="%(doc_id)s" style="width:%(initial_slider_value)spx;">
            <div class="imgBlock">
                <div class="normalLineHeight" style="margin-left:auto;margin-right:auto;display:inline" >
                    <img id="delete_%(doc_id)s" class="hidden" src="/img/cross_red.gif" alt="Delete" style="position:absolute;top:0;" onclick="delete_photo('%(doc_id)s');"/>
                    <img src="%(icon_url)s" class="imgIcon"/>
                 </div>
                 <div class="normalLineHeight">
                     <textarea style="width:95%%" id="PHOTO_MANAGER_DESCRIPTION_%(doc_id)s" name="PHOTO_MANAGER_DESCRIPTION_%(doc_id)s">%(description)s</textarea>
                 </div>
            </div>
        </li>''' % \
                  {'initial_slider_value': initial_slider_value,
                   'doc_id': doc_id,
                   'icon_url': icon_url,
                   'description': description})

    out += '''
    <link rel="stylesheet" href="%(CFG_SITE_URL)s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css" type="text/css" charset="utf-8"/>
    <link rel="stylesheet" href="%(CFG_SITE_URL)s/vendors/jquery-ui/themes/redmond/theme.css" type="text/css" charset="utf-8"/>
    <style type="text/css">
            #sortable { list-style-type: none; margin: 0; padding: 0; }
            #sortable li { margin: auto 3px; padding: 1px; float: left; width: 180px; font-size:small; text-align: center; position: relative;}
            #sortable .imgIcon {max-height:95%%;max-width:95%%;margin: 2px;max-height:130px;}
            #sortable li div.imgBlock {vertical-align: middle; margin:
    auto;display:inline;display:inline-table;display:inline-block;vertical-align:middle;text-align : center; width:100%%;position:relative}
            #sortable li div.imgBlock .hidden {display:none;}
            %(delete_hover_class)s
            .fileUploadQueue{text-align:left; margin: 0 auto; width:300px;}
            .normalLineHeight {line-height:normal}
    </style>

    <div id="uploadedFiles" style="%(hide_photo_viewer)sborder-left:1px solid #555; border-top:1px solid #555;border-right:1px solid #eee;border-bottom:1px solid #eee;overflow:auto;%(editor_height_style)s%(editor_width_style)sbackground-color:#eee;margin:3px;text-align:left;position:relative"><ul id="sortable">%(photos_img)s</ul></div>
    <div id="grid_slider" style="%(hide_photo_viewer)swidth:300px;">
      <div class='ui-slider-handle'></div>
    </div>


    <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/uploadify/jquery.uploadify.min.js"></script>
    <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/swfobject/swfobject/swfobject.js"></script>
    <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/jquery-ui/jquery-ui.min.js"></script>
    <link rel="stylesheet" href="%(CFG_SITE_URL)s/vendors/uploadify/uploadify.css" type="text/css" />

    <script type="text/javascript">

    $(document).ready(function() {

        /* Uploading */
            if (%(can_upload_photos)s) {
            $('#uploadFile').uploadify({
                    'uploader': '%(CFG_SITE_URL)s/vendors/uploadify/uploadify.swf',
                    'script':    '/submit/uploadfile',
                    'cancelImg': '%(CFG_SITE_URL)s/vendors/uploadify/uploadify-cancel.png',
                    'multi' :    true,
                    'auto' :    true,
                    'simUploadLimit': 2,
                    'scriptData' : {'type': 'File', 'uid': %(uid)s, 'session_id': '%(session_id)s', 'indir': '%(indir)s', 'doctype': '%(doctype)s', 'access': '%(access)s'},
                    'displayDate': 'percentage',
                    'buttonText': 'Browse',
                    'fileDataName': 'NewFile' /* be compatible with CKEditor */,
                    'onSelectOnce': function(event, data) {

                     },
                    'onSelect': function(event, queueID, fileObj, response, data) {
                           $('#loading').css("visibility","visible");
                     },
                    'onAllComplete' : function(event, queueID, fileObj, response, data) {
                           $('#loading').css("visibility","hidden");
                     },
                    /*'onCheck': function(event, checkScript, fileQueue, folder, single) {

                           return false;
                     },*/
                    'onComplete': function(event, queueID, fileObj, response, data) {
                           $('#grid_slider').css("display","block");
                           $('#uploadedFiles').css("display","block");
                           var cur_width = $("#grid_slider").slider('option', 'value');
                           var response_obj = parse_invenio_response(response);
                           icon_url = '%(CFG_SITE_URL)s/img/file-icon-blank-96x128.gif'
                           if ("NewFile" in response_obj) {
                               filename = response_obj["NewFile"]["name"]
                               if ('iconName' in response_obj["NewFile"]){
                                   icon_name = response_obj["NewFile"]["iconName"]
                                   icon_url = '%(CFG_SITE_URL)s/submit/getuploadedfile?indir=%(indir)s&doctype=%(doctype)s&access=%(access)s&key=NewFile&icon=1&filename=' + icon_name
                               }
                           } else {
                               return true;
                           }
                           $('#sortable').append('<li id="'+ queueID +'" style="width:'+cur_width+'px;"><div class="imgBlock"><div class="normalLineHeight" style="margin-left:auto;margin-right:auto;display:inline" ><img id="delete_'+ queueID +'" class="hidden" src="/img/cross_red.gif" alt="Delete" style="position:absolute;top:0;" onclick="delete_photo(\\''+ queueID +'\\');"/><img src="'+ icon_url +'" class="imgIcon"/></div><div class="normalLineHeight"><textarea style="width:95%%" id="PHOTO_MANAGER_DESCRIPTION_'+ queueID +'" name="PHOTO_MANAGER_DESCRIPTION_'+ queueID +'"></textarea></div></div></li>');

                           update_order_field();
                           $('#photo_manager_icons').val($("#photo_manager_icons").val() + '\\n' + queueID + '/' + icon_url);
                           $('#photo_manager_new').val($("#photo_manager_new").val() + '\\n' + queueID + '/' + filename);
                           update_CSS();
                           return true;
                     }
            });
         }

        /* Resizing */
            $("#grid_slider").slider({
                    value: %(initial_slider_value)s,
                    max: %(max_slider_value)s,
                    min: %(min_slider_value)s,
                    slide: function(event, ui) {
                         update_CSS();
                    }
            });

            /* Update CSS to ensure that existing photos get nicely laid out*/
            update_CSS();

    });


    /* Ordering */
            $(function() {
                    if (%(can_reorder_photos)s) {
                        $("#sortable").sortable();
                        $("#sortable").bind('sortupdate', function(event, ui) {
                            update_order_field();
                        });
                    }
            });

            function delete_photo(docid){
                if (confirm("Are you sure you want to delete the photo? (The file will be deleted after you apply all the modifications)")) {
                    $("#" + docid).remove();
                    $("#photo_manager_delete").val($("#photo_manager_delete").val() + '\\n' + docid);
                    update_order_field();
                }
            }

    /* CSS-related */

            function update_CSS(){
                /* Update some style according to the slider size */
                var slider_value = $("#grid_slider").slider('option', 'value');
                $('#uploadedFiles li').css('width', slider_value+"px");
                /*$('#uploadedFiles div.floater').css('width', slider_value+"px");*/
                /* Update height attr accordingly so that image get centered.
                   First we need to get the tallest element of the list.
                 */
                var max_height = 0;
                $('#uploadedFiles li div').each(function() {
                    this_height = $(this).height();
                    if(this_height > max_height) {
                        max_height = this_height;
                    }
                });
                $('#uploadedFiles li').css('height',max_height+"px");
                $('#uploadedFiles li').css('line-height',max_height+"px");
            }

    /* Utils */
             function update_order_field(){
                 $("#photo_manager_order").val($("#sortable").sortable('toArray').join('\\n'));
             }

             function parse_invenio_response(response){
                 /* Return the javascript object included in the
                    the given Invenio message. Really dirty implementation, but ok
                    in this very simple scenario */
                 /*var object_string = response.substring(response.indexOf('<![CDATA[')+9, response.lastIndexOf(']]>'));*/ object_string = response;
                 var object = {};
                 eval('object=' + object_string);
                 return object;
              }

    </script>


    <div style="margin: 0 auto;">
    <img src="%(CFG_SITE_URL)s/img/loading.gif" style="visibility: hidden" id="loading"/>
    <input type="file" size="40" id="uploadFile" name="PHOTO_FILE" style="margin: 0 auto;%(upload_display)s"/>
    </div>

    <!--<a href="javascript:$('#uploadFile').fileUploadStart();">Upload Files</a> -->

    <textarea id="photo_manager_icons" style="display:none" name="PHOTO_MANAGER_ICONS">%(PHOTO_MANAGER_ICONS)s</textarea>
    <textarea id="photo_manager_order" style="display:none" name="PHOTO_MANAGER_ORDER">%(PHOTO_MANAGER_ORDER)s</textarea>
    <textarea id="photo_manager_new" style="display:none" name="PHOTO_MANAGER_NEW">%(PHOTO_MANAGER_NEW)s</textarea>
    <textarea id="photo_manager_delete" style="display:none" name="PHOTO_MANAGER_DELETE">%(PHOTO_MANAGER_DELETE)s</textarea>
    ''' % {'CFG_SITE_URL': CFG_SITE_URL,
           #'curdir': cgi.escape(quote(curdir, safe="")),#quote(curdir, safe=""),
           'uid': uid,
           'access': quote(access, safe=""),
           'doctype': quote(doctype, safe=""),
           'indir': quote(indir, safe=""),
           'session_id': quote(session_id, safe=""),
           'PHOTO_MANAGER_ICONS': '\n'.join([key + '/' + value for key, value in iteritems(photo_manager_icons_dict)]),
           'PHOTO_MANAGER_ORDER': '\n'.join(photo_manager_order_list),
           'PHOTO_MANAGER_DELETE': '\n'.join(photo_manager_delete_list),
           'PHOTO_MANAGER_NEW': '\n'.join([key + '/' + value for key, value in iteritems(photo_manager_new_dict)]),
           'initial_slider_value': initial_slider_value,
           'max_slider_value': max_slider_value,
           'min_slider_value': min_slider_value,
           'photos_img': '\n'.join(photos_img),
           'hide_photo_viewer': (len(photos_img) == 0 and len(photo_manager_new_dict.keys()) == 0) and 'display:none;' or '',
           'delete_hover_class': can_delete_photos and "#sortable li div.imgBlock:hover .hidden {display:inline;}" or '',
           'can_reorder_photos': can_reorder_photos and 'true' or 'false',
           'can_upload_photos': can_upload_photos and 'true' or 'false',
           'upload_display': not can_upload_photos and 'display: none' or '',
           'editor_width_style': editor_width and 'width:%spx;' % editor_width or '',
           'editor_height_style': editor_height and 'height:%spx;' % editor_height or ''}

    return out
