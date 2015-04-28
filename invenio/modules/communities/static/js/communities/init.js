/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

'use strict'

require(

  [
    'ckeditor-jquery'
  ],

  function () {

    var CKEDITOR_BASEPATH = '/ckeditor/';

    function init_ckeditor(selector, type) {
        if(type=="simple"){
            CKEDITOR.replace( selector, {
                toolbar: [
                    ['PasteText','PasteFromWord'],
                    ['Bold','Italic','Strike','-','Subscript','Superscript',],
                    ['NumberedList','BulletedList', 'Blockquote'],
                    ['Undo','Redo','-','Find','Replace','-', 'RemoveFormat'],
                    ['Mathjax', 'SpecialChar', 'ScientificChar'],
                    ['Source'], ['Maximize'],
                ],
                extraPlugins: 'scientificchar,mathjax,blockquote',
                disableNativeSpellChecker: false,
                removePlugins: 'elementspath',
                removeButtons: ''
            });
        } else {
            CKEDITOR.replace( selector, {
                toolbar: [
                    ['PasteText','PasteFromWord'],
                    ['Bold','Italic','Strike','-','Subscript','Superscript',],
                    ['NumberedList','BulletedList', 'Blockquote', 'Table', '-', 'Link', 'Anchor'],
                    ['Undo','Redo','-','Find','Replace','-', 'RemoveFormat'],
                    ['Mathjax', 'SpecialChar', 'ScientificChar'],
                    ['Styles', 'Format'], ['Source'], ['Maximize'],
                ],
                extraPlugins: 'scientificchar,mathjax,blockquote',
                disableNativeSpellChecker: false,
                removePlugins: 'elementspath',
                removeButtons: ''
            });
        }
    }

    if ( $('#page').length )
      init_ckeditor("page", 'advanced');
    if ( $('#description').length )
      init_ckeditor("description", 'simple');
  }
);
