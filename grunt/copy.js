/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
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

'use strict';

/*jshint laxcomma:true */  // FIXME?


module.exports = {
    css: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>',
        src: ['jquery.bookmark/jquery.bookmark.css'
               ,'datatables-colvis/css/dataTables.colVis.css'
               ,'DataTables-Plugins/integration/bootstrap/3/dataTables.bootstrap.css'
               ,'prism/themes/prism.css'
               ,'bootstrap-tagsinput/dist/bootstrap-tagsinput.css'],
        dest: '<%= globalConfig.installation_path %>/css/'
    },
    img: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['jquery.bookmark/bookmarks.png'
               ,'uploadify/uploadify*'
               ,'!uploadify/uploadify.php'
               ,'DataTables-Plugins/integration/bootstrap/3/images/*.png'],
        dest: '<%= globalConfig.installation_path %>/img/'
    },
    js: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: [
            'bootstrap-tagsinput/dist/bootstrap-tagsinput.min.js',
            'bootstrap-tagsinput/dist/bootstrap-tagsinput.min.js.map',
            'datatables-colvis/js/dataTables.colVis.js',
            'DataTables/media/js/jquery.dataTables.js',
            'DataTables-Plugins/integration/bootstrap/3/dataTables.bootstrap.js',
            'jquery.bookmark/jquery.bookmark.min.js',
            'jquery-flot/excanvas.min.js',
            'jquery-flot/jquery.flot.js',
            'jquery-flot/jquery.flot.selection.js',
            'prism/prism.js',
            'requirejs/require.js',
            'requirejs-hogan-plugin/hgn.js',
            'requirejs-hogan-plugin/text.js',
            'uploadify/jquery.uploadify.min.js'
        ],
        dest: '<%= globalConfig.installation_path %>/js/'
    },
    jqueryTimePicker: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['jquery.ui.timepicker/index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'jquery-ui-timepicker-addon.js');
            return dest + res;
        }
    },
    MultiFile: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['jquery.multifile/index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'jquery.MultiFile.pack.js');
            return dest + res;
        }
    },
    ajaxPager: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['jquery.ajaxpager/index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'jquery.ajaxPager.js');
            return dest + res;
        }
    },
    MathJax: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/MathJax/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/MathJax/'
    },
    jqueryTableSorter: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery.tablesorter/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/js/tablesorter/'
    },
    jqueryMigrate: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery-migrate',
        src: ['index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            if (src == "index.js") {
                src = 'jquery-migrate.js'
            }
            return dest + src;
        }
    }
};
