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

/* global module */
/* global require */

module.exports = function (grunt) {
    // show elapsed time at the end
    require('time-grunt')(grunt);
    // load all grunt tasks
    require('load-grunt-tasks')(grunt);

    var globalConfig = {
    bower_path: 'bower_components',
    };

    var buildConfig = {
    develop: 'instance/static',
    deploy: 'invenio/base/static'
    };

    // Project configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        globalConfig: globalConfig,
        buildConfig: buildConfig,

        copy: {
            css: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>',
                src: ['bootstrap/dist/css/bootstrap*.css'
                       ,'jquery-tokeninput/styles/token-input-facebook.css'
                       ,'jquery-tokeninput/styles/token-input.css'
                       ,'jquery.bookmark/jquery.bookmark.css'
                       ,'datatables-colvis/media/css/ColVis.css'
                       ,'DataTables-Plugins/integration/bootstrap/3/dataTables.bootstrap.css'],
                dest: '<%= grunt.option(\'target\') %>/css/'
            },

            img: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['jquery.bookmark/bookmarks.png'
                       ,'uploadify/uploadify*'
                       ,'!uploadify/uploadify.php'
                       ,'datatables-colvis/media/images/button.png'
                       ,'DataTables-Plugins/integration/bootstrap/3/images/*.png'],
                dest: '<%= grunt.option(\'target\') %>/img/'
            },

            js: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['bootstrap/dist/js/bootstrap.js'
                     ,'bootstrap/dist/js/bootstrap.min.js'
                     ,'typeahead.js/dist/typeahead.js'
                     ,'typeahead.js/dist/typeahead.min.js'
                     ,'jquery/jquery.min.js'
                     ,'jquery/jquery.min.map'
                     ,'jquery-tokeninput/src/jquery.tokeninput.js'
                     ,'jquery.bookmark/jquery.bookmark.min.js'
                     ,'DataTables/media/js/jquery.dataTables.js'
                     ,'jquery-flot/excanvas.min.js'
                     ,'jquery-flot/jquery.flot.js'
                     ,'jquery-flot/jquery.flot.selection.js'
                     ,'jquery.hotkeys/jquery.hotkeys.js'
                     ,'uploadify/jquery.uploadify.min.js'
                     ,'json2/json2.js'
                     ,'datatables-colvis/media/js/ColVis.js'
                     ,'DataTables-Plugins/integration/bootstrap/3/dataTables.bootstrap.js'],
                dest: '<%= grunt.option(\'target\') %>/js/'
            },

            fonts: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['bootstrap/dist/fonts/glyphicons-halflings-regular.*'],
                dest: '<%= grunt.option(\'target\') %>/fonts/'
            },

            typeaheadJSbootstrap: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['typeahead.js-bootstrap/index.css'],
                dest: '<%= grunt.option(\'target\') %>/css/',
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
                dest: '<%= grunt.option(\'target\') %>/js/',
                rename: function(dest, src) {
                    return dest + src.substring(0, src.indexOf('-')) + '.js';
                }
            },

            jqueryUI: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['jquery.ui/jquery-1.8.2.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                rename: function(dest, src) {
                    return dest + src.substring(0, src.indexOf('-')) + '-ui.js';
                }
            },

            jqueryTimePicker: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['jquery.ui.timepicker/index.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
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
                dest: '<%= grunt.option(\'target\') %>/js/',
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
                dest: '<%= grunt.option(\'target\') %>/js/',
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
                dest: '<%= grunt.option(\'target\') %>/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),
                                          'jquery.form.js');
                    return dest + res;
                }
            },

            prism: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['prism/index.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0), 'prism.js');
                    return dest + res;
                }
            },

            swfobject: {
                expand: true,
                flatten: true,
                cwd: '<%= globalConfig.bower_path %>/',
                src: ['swfobject/index.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0), 'swfobject.js');
                    return dest + res;
                }
            },

            MathJax: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/MathJax/',
                src: ['**'],
                dest: '<%= grunt.option(\'target\') %>/MathJax/'
            },

            ckeditor: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/ckeditor/',
                src: ['**', '!**_samples/**', '!**_source/**', '!**php**',
                      '!**_**', '!**pack**', '!**ckeditor.asp'],
                dest: '<%= grunt.option(\'target\') %>/ckeditor/'
            },

            jqueryTreeview: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/jquery.treeview/',
                src: ['**'],
                dest: '<%= grunt.option(\'target\') %>/js/jquery-treeview/'
            },

            jqueryTableSorter: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/jquery.tablesorter/',
                src: ['**'],
                dest: '<%= grunt.option(\'target\') %>/js/tablesorter/'
            },

            // jqueryUI
            themesUI: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/jquery.ui/themes/',
                src: ['**'],
                dest: '<%= grunt.option(\'target\') %>/img/jquery-ui/'
            },

            imagesUI: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/jquery.ui/themes/base/images/',
                src: ['**'],
                dest: '<%= grunt.option(\'target\') %>/img/images/'
            },

            jeditable: {
                expand: true,
                cwd: '<%= globalConfig.bower_path %>/jquery_jeditable/',
                src: ['index.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                rename: function(dest, src) {
                    if (src === 'index.js') {
                        return dest + 'jquery.jeditable.mini.js';
                    }
                    return dest + src;
                }
            }

        },

        // minification of the JS files
        uglify: {
            jqueryUI: {
                expand: true,
                flatten: true,
                cwd: '<%= grunt.option(\'target\') %>/js/',
                src: ['jquery-ui.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                ext: '.min.js'
            },

            dataTables: {
                expand: true,
                flatten: true,
                cwd: '<%= grunt.option(\'target\') %>/js/',
                src: ['jquery.dataTables.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                ext: '.dataTables.min.js'
            },

            jqueryFlot: {
                expand: true,
                flatten: true,
                cwd: '<%= grunt.option(\'target\') %>/js/',
                src: ['jquery.flot.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                ext: '.flot.min.js'
            },

            jqueryFlotSelection: {
                expand: true,
                flatten: true,
                cwd: '<%= grunt.option(\'target\') %>/js/',
                src: ['jquery.flot.selection.js'],
                dest: '<%= grunt.option(\'target\') %>/js/',
                ext: '.flot.selection.min.js'
            }
        },

        // minification of the CSS files
        cssmin: {
            minify: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/css/',
                src: ['bootstrap*.css', '!bootstrap*.min.css'],
                dest: '<%= grunt.option(\'target\') %>/css/',
                ext: '.min.css'
            }
        },

        //// CLEANING... ////
        actualclean: {
            css: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/css/',
                src: ['bootstrap*.css',
                      'token-input-facebook.css',
                      'token-input.css',
                      'jquery.bookmark.css',
                      'ColVis.css',
                      'typeahead.js-bootstrap.css',
                      'dataTables.bootstrap.css']
            },

            img: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/img/',
                src: ['bookmarks.png', 'uploadify*', 'button.png', 'sort_*.png']
            },

            fonts: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/fonts/',
                src: ['**']
            },

            js: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/js/',
                src: ['bootstrap.js'
                     ,'bootstrap.min.js'
                     ,'typeahead.js'
                     ,'typeahead.min.js'
                     ,'jquery.min.js'
                     ,'jquery.tokeninput.js'
                     ,'hogan.js'
                     ,'jquery.jeditable.mini.js'
                     ,'jquery-ui*.js'
                     ,'jquery-ui-timepicker-addon.js'
                     ,'jquery.MultiFile.pack.js'
                     ,'jquery.ajaxPager.js'
                     ,'jquery.bookmark.min.js'
                     ,'jquery.dataTables*.js'
                     ,'excanvas.min.js'
                     ,'jquery.flot*.js'
                     ,'jquery.form.js'
                     ,'jquery.hotkeys.js'
                     ,'jquery.uploadify.min.js'
                     ,'json2.js'
                     ,'prism.js'
                     ,'swfobject.js'
                     ,'ColVis.js'
                     ,'dataTables.bootstrap.js']
            },

            MathJax: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/MathJax/',
                src: ['**']
            },

            ckeditor: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/ckeditor/',
                src: ['**', '!**plugins/scientificchar/**']
            },

            jqueryTreeview: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/js/jquery-treeview/',
                src: ['**']
            },

            jqueryTableSorter: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/js/tablesorter/',
                src: ['**']
            },

            imagesUI: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/img/images/',
                src: ['**']
            },

            themesUI: {
                expand: true,
                cwd: '<%= grunt.option(\'target\') %>/img/jquery-ui/',
                src: ['**']
            },

            //clean the folder if it's empty
            empty: {
                src: '<%= grunt.option(\'target\') %>/**/*',
                filter: function(filepath) {
                    return (grunt.file.isDir(filepath) &&
                            require('fs').readdirSync(filepath).length === 0);
                }
            }
        }
    });

    // build task
    grunt.registerTask('build', 'Set the output folder for the build.', function () {
        if (grunt.option('path') === undefined) {
            if (grunt.option('target') === 'develop') {
                grunt.option('target', buildConfig.develop);
            } else if (grunt.option('target') === 'deploy') {
                grunt.option('target', buildConfig.deploy);
            } else if (grunt.option('target') === undefined) {
                grunt.option('target', buildConfig.develop);
            } else {
                grunt.task.run('help');
                return;
            }
            grunt.task.run(['copy', 'uglify', 'cssmin']);
        } else {
            grunt.option('target', grunt.option('path'));
            grunt.task.run(['copy', 'uglify', 'cssmin']);
        }
    });

    // clean task
    grunt.renameTask('clean', 'actualclean');

    grunt.registerTask('clean', 'Clean the files.', function () {
        if (grunt.option('path') === undefined) {
            if (grunt.option('target') === 'develop') {
                grunt.option('target', buildConfig.develop);
            } else if (grunt.option('target') === 'deploy') {
                grunt.option('target', buildConfig.deploy);
            } else if (grunt.option('target') === undefined) {
                grunt.option('target', buildConfig.develop);
            } else {
                grunt.task.run('help');
                return;
            }
            grunt.task.run('actualclean');
        } else {
            grunt.option('target', grunt.option('path'));
            grunt.task.run('actualclean');
        }
    });

    // help task
    grunt.registerTask('help', 'Help menu.', function () {
        grunt.log.writeln(
            '\nAvailable options for Grunt' + '\n\n' +
            'Building:' + '\n' +
            'grunt build --target=develop # build for development mode' + '\n' +
            'grunt build --target=deploy  # build for deployment mode' + '\n' +
            'grunt build                  # build for development mode' + '\n\n' +
            'Building with custom paths:' + '\n' +
            'grunt build --path=path/to/folder  # build for custom mode' + '\n\n' +
            'Cleaning:' + '\n' +
            'grunt clean --target=develop # clean for development mode' + '\n' +
            'grunt clean --target=deploy  # clean for deployment mode' + '\n' +
            'grunt clean                  # clean for development mode' + '\n\n' +
            'Cleaning with custom paths:' + '\n' +
            'grunt clean --path=path/to/folder  # clean for custom mode' + '\n');
        });
};
