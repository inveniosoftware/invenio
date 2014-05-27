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
        src: ['jquery-tokeninput/styles/token-input-facebook.css'
               ,'jquery-tokeninput/styles/token-input.css'
               ,'jquery.bookmark/jquery.bookmark.css'
               ,'datatables-colvis/css/dataTables.colVis.css'
               ,'DataTables-Plugins/integration/bootstrap/3/dataTables.bootstrap.css'
               ,'prism/themes/prism.css'
               ,'bootstrap-tagsinput/dist/bootstrap-tagsinput.css'],
        dest: '<%= globalConfig.installation_path %>/css/'
    },
    less_bootstrap: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>',
        src: ['bootstrap/less/*.less'],
        dest: '<%= globalConfig.installation_path %>/less/bootstrap'
    },
    less_fontawesome: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>',
        src: ['font-awesome/less/*.less'],
        dest: '<%= globalConfig.installation_path %>/less/font-awesome'
    },
    jquery_css: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>',
        src: ['jqueryui/themes/base/jquery.ui.datepicker.css'
             ,'jqueryui/themes/base/jquery.ui.theme.css'],
        dest: '<%= globalConfig.installation_path %>/img/jquery-ui/themes/base/'
    },
    jquery_imgs: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>',
        src: ['jqueryui/themes/base/images/ui-bg_flat_75_ffffff_40x100.png'],
        dest: '<%= globalConfig.installation_path %>/img/jquery-ui/themes/base/images/'
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
        src: ['bootstrap/dist/js/bootstrap.js'
             ,'bootstrap/dist/js/bootstrap.min.js'
             ,'jquery/dist/jquery.min.js'
             ,'jquery/dist/jquery.min.map'
             ,'jquery-tokeninput/src/jquery.tokeninput.js'
             ,'jquery.bookmark/jquery.bookmark.min.js'
             ,'DataTables/media/js/jquery.dataTables.js'
             ,'jquery-flot/excanvas.min.js'
             ,'jquery-flot/jquery.flot.js'
             ,'jquery-flot/jquery.flot.selection.js'
             ,'jquery.hotkeys/jquery.hotkeys.js'
             ,'uploadify/jquery.uploadify.min.js'
             ,'json2/json2.js'
             ,'datatables-colvis/js/dataTables.colVis.js'
             ,'DataTables-Plugins/integration/bootstrap/3/dataTables.bootstrap.js'
             ,'prism/prism.js'
             ,'bootstrap-tagsinput/dist/bootstrap-tagsinput.min.js'
             ,'bootstrap-tagsinput/dist/bootstrap-tagsinput.min.js.map'],
        dest: '<%= globalConfig.installation_path %>/js/'
    },
    fonts: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['bootstrap/dist/fonts/glyphicons-halflings-regular.*'
             ,'font-awesome/fonts/*'],
        dest: '<%= globalConfig.installation_path %>/fonts/'
    },
    typeahead: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['typeahead.js/dist/typeahead.bundle.min.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'typeahead.js');
            return dest + res;
        }
    },
    typeaheadBootstrap3Css: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/typeahead.js-bootstrap3.less',
        src: ['typeahead.css'],
        dest: '<%= globalConfig.installation_path %>/css/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'typeahead.js-bootstrap.css');
            return dest + res;
        }
    },
    hogan: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['hogan/web/builds/2.0.0/hogan-2.0.0.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            return dest + src.substring(0, src.indexOf('-')) + '.js';
        }
    },
    jqueryUI: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/jqueryui',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/js/jqueryui'
    },
    jqueryUISortable: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['jquery.ui/ui/jquery.ui.sortable.js'],
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
    jqueryCaret: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['jquery.caret/dist/jquery.caret-1.5.0.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'jquery-caret.js');
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
    form: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['form/index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0),
                                  'jquery.form.js');
            return dest + res;
        }
    },
    swfobject: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.bower_path %>/',
        src: ['swfobject/index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            var res = src.replace(src.substring(0), 'swfobject.js');
            return dest + res;
        }
    },
    MathJax: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/MathJax/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/MathJax/'
    },
    ckeditor: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/ckeditor/',
        src: ['**', '!**_samples/**', '!**_source/**', '!**php**',
              '!**_**', '!**pack**', '!**ckeditor.asp'],
        dest: '<%= globalConfig.installation_path %>/ckeditor/'
    },
    jqueryTreeview: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery.treeview/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/js/jquery-treeview/'
    },
    jqueryTableSorter: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery.tablesorter/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/js/tablesorter/'
    },
    themesUI: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery.ui/themes/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/img/jquery-ui/themes'
    },
    imagesUI: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery.ui/themes/base/images/',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/img/images/'
    },
    jeditable: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/jquery_jeditable/',
        src: ['index.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            if (src === 'index.js') {
                return dest + 'jquery.jeditable.mini.js';
            }
            return dest + src;
        }
    },
    plupload: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/plupload/js',
        src: ['**'],
        dest: '<%= globalConfig.installation_path %>/plupload/'
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
    },
    lesscss: {
        expand: true,
        cwd: '<%= globalConfig.bower_path %>/less/dist',
        src: ['less-1.7.0.*'],
        dest: '<%= globalConfig.installation_path %>/js/',
        rename: function(dest, src) {
            return dest + src.replace(/-\d\.\d\.\d/, '');
        }
    }
};
