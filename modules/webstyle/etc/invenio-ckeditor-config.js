/*
* -*- mode: text; coding: utf-8; -*-

   This file is part of Invenio.
   Copyright (C) 2011, 2012, 2013, 2014 CERN.

   Invenio is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   Invenio is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with Invenio; if not, write to the Free Software Foundation, Inc.,
   59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
*/

/*Define here the config of the CKEditor used in Invenio.

  Users/admin:
  Since the editor is used in various contexts that require different
  settings, most variables are set up directly in the module that
  calls the editor: variables that you might define here will be
  overriden, excepted notably the toolbar sets.

  Developers:
  Here is the best/only place to define custom toolbar sets.
 */

CKEDITOR.editorConfig = function( config )
{

config.toolbar_WebComment = [
			     ['Preview'],
			     ['PasteText','PasteFromWord'],
			     ['Undo','Redo','-','Find','Replace','-', 'RemoveFormat'],
			     '/',
			     ['Bold','Italic','Underline','Strike','-','Subscript','Superscript'],
			     ['NumberedList','BulletedList','-','Outdent','Indent','Blockquote'],
			     ['Link','Unlink'],
                             ['HorizontalRule','Smiley','SpecialChar','ScientificChar']
			     ];

config.skin = 'v2';
config.resize_dir = 'vertical';

/* Enable browser built-in spellchecker */
config.disableNativeSpellChecker = false;
config.browserContextMenuOnCtrl = true;

/* Remove "status" bar at the bottom of the editor displaying the DOM path*/
config.removePlugins = 'elementspath';

/* Some styling that will only apply inside the CKeditor, including to
   simulate the the ".commentbox" CSS class in WebComment case. */
config.contentsCss = ['/img/invenio.css', '/ckeditor/invenio-ckeditor-content.css'];

/* Load our Scientific Characters panel */
config.extraPlugins = 'scientificchar';

}
