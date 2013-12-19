'use strict';

module.exports = function (grunt) {
    // show elapsed time at the end
    require('time-grunt')(grunt);
    // load all grunt tasks
    require('load-grunt-tasks')(grunt);

    // Project configuration
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),

        copy: {
            // css
            css: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['bootstrap/docs/assets/css/bootstrap*.css'
                     ,'jquery-tokeninput/styles/token-input-facebook.css'
                     ,'jquery-tokeninput/styles/token-input.css'
                     ,'jquery.bookmark/jquery.bookmark.css'
                     ,'datatables-colvis/media/css/ColVis.css'],
                dest: 'invenio/base/static/css/'
            },
            // images
            img: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['bootstrap/docs/assets/img/glyphicons-halflings*.png'
                     ,'jquery.bookmark/bookmarks.png'
                     ,'uploadify/uploadify*'
                     ,'!uploadify/uploadify.php'
                     ,'datatables-colvis/media/images/button.png'],
                dest: 'invenio/base/static/img/'
            },
            // javascript
            js: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['bootstrap/docs/assets/js/bootstrap.js'
                     ,'bootstrap/docs/assets/js/bootstrap.min.js' 
                     ,'jquery/jquery.min.js'
                     ,'jquery-tokeninput/src/jquery.tokeninput.js'
                     ,'jquery.bookmark/jquery.bookmark.min.js'
                     ,'DataTables/media/js/jquery.dataTables.js'
                     ,'jquery-flot/excanvas.min.js'
                     ,'jquery-flot/jquery.flot.js'
                     ,'jquery-flot/jquery.flot.selection.js'
                     ,'jquery.hotkeys/jquery.hotkeys.js'
                     ,'uploadify/jquery.uploadify.min.js'
                     ,'json2/json2.js'
                     ,'datatables-colvis/media/js/ColVis.js'],
                dest: 'invenio/base/static/js/'
            },

            hogan: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['hogan/web/builds/2.0.0/hogan-2.0.0.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    return dest + src.substring(0, src.indexOf('-')) + '.js';
                }
            },

            jqueryUI: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['jquery.ui/jquery-1.8.2.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    return dest + src.substring(0, src.indexOf('-')) + '-ui.js';
                }
            },

            jqueryTimePicker: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['jquery.ui.timepicker/index.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),'jquery-ui-timepicker-addon.js');
                    return dest + res;
                }
            },

            MultiFile: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['jquery.multifile/index.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),'jquery.MultiFile.pack.js');
                    return dest + res;
                }
            },

            ajaxPager: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['jquery.ajaxpager/index.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),'jquery.ajaxPager.js');
                    return dest + res;
                }
            },

            form: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['form/index.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),'jquery.form.js');
                    return dest + res;
                }
            },

            prism: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['prism/index.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),'prism.js');
                    return dest + res;
                }
            },

            swfobject: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/',
                src: ['swfobject/index.js'],
                dest: 'invenio/base/static/js/',
                rename: function(dest, src) {
                    var res = src.replace(src.substring(0),'swfobject.js');
                    return dest + res;
                }
            },

            MathJax: {
                expand: true,
                cwd: 'bower_components/MathJax/',
                src: ['**'],
                dest: 'invenio/base/static/MathJax/'
            },

            ckeditor: {
                expand: true,
                cwd: 'bower_components/ckeditor/',
                src: ['**', '!**_samples/**', '!**_source/**', '!**php**', '!**_**', '!**pack**', '!**ckeditor.asp'],
                dest: 'invenio/base/static/ckeditor/' 
            },

            jqueryTreeview: {
                expand: true,
                cwd: 'bower_components/jquery.treeview/',
                src: ['**'],
                dest: 'invenio/base/static/js/jquery-treeview/'
            },

            jqueryTableSorter: {
                expand: true,
                cwd: 'bower_components/jquery.tablesorter/',
                src: ['**'],
                dest: 'invenio/base/static/js/tablesorter/'
            },

            // jqueryUI 
            themesUI: {
                expand: true,
                cwd: 'bower_components/jquery.ui/themes/',
                src: ['**'],
                dest: 'invenio/base/static/img/jquery-ui/'
            },

            imagesUI: {
                expand: true,
                cwd: 'bower_components/jquery.ui/themes/base/images/',
                src: ['**'],
                dest: 'invenio/base/static/img/images/'
            }
        },

        // minification of the JS files
        uglify: {
            jeditable: {
                expand: true,
                flatten: true,
                cwd: 'bower_components/jquery_jeditable/',
                src: ['js/jquery.jeditable.js'],
                dest: 'invenio/base/static/js/',
                ext: '.jeditable.mini.js'
            },

            jqueryUI: {
                expand: true,
                flatten: true,
                cwd: 'invenio/base/static/js/',
                src: ['jquery-ui.js'],
                dest: 'invenio/base/static/js/',
                ext: '.min.js'
            },

            dataTables: {
                expand: true,
                flatten: true,
                cwd: 'invenio/base/static/js/',
                src: ['jquery.dataTables.js'],
                dest: 'invenio/base/static/js/',
                ext: '.dataTables.min.js'                
            },

            jqueryFlot: {
                expand: true,
                flatten: true,
                cwd: 'invenio/base/static/js/',
                src: ['jquery.flot.js'],
                dest: 'invenio/base/static/js/',
                ext: '.flot.min.js'   
            },

            jqueryFlotSelection: {
                expand: true,
                flatten: true,
                cwd: 'invenio/base/static/js/',
                src: ['jquery.flot.selection.js'],
                dest: 'invenio/base/static/js/',
                ext: '.flot.selection.min.js'   
            }
        },

        // minification of the CSS files
        cssmin: {
            minify: {
                expand: true,
                cwd: 'invenio/base/static/css/',
                src: ['bootstrap*.css', '!bootstrap*.min.css'],
                dest: 'invenio/base/static/css/',
                ext: '.min.css'
            }
        },

        //////////////////////////////////////////////////////////////
        /////////////////////// CLEANING..... ////////////////////////
        //////////////////////////////////////////////////////////////
        clean: {
            css: {
                expand: true,
                cwd: 'invenio/base/static/css/',
                src: ['bootstrap*.css'
                     ,'token-input-facebook.css'
                     ,'token-input.css'
                     ,'jquery.bookmark.css'
                     ,'ColVis.css']
            },

            img: {
                expand: true,
                cwd: 'invenio/base/static/img/',
                src: ['glyphicons-halflings*.png'
                     ,'bookmarks.png'
                     ,'uploadify*'
                     ,'button.png']
            },

            js: {
                expand: true,
                cwd: 'invenio/base/static/js/',
                src: ['bootstrap.js'
                     ,'bootstrap.min.js' 
                     ,'jquery.min.js'
                     ,'jquery.tokeninput.js'
                     ,'hogan.js'// hogan
                     ,'jquery.jeditable.mini.js' // jeditable
                     ,'jquery-ui*.js' // jqueryUI
                     ,'jquery-ui-timepicker-addon.js' // timepicker
                     ,'jquery.MultiFile.pack.js' // multifile
                     ,'jquery.ajaxPager.js' // ajaxpager 
                     ,'jquery.bookmark.min.js' // bookmark 
                     ,'jquery.dataTables*.js' // dataTables
                     ,'excanvas.min.js' // excanvas
                     ,'jquery.flot*.js' // flot
                     ,'jquery.form.js'  // form
                     ,'jquery.hotkeys.js' // hotkeys
                     ,'jquery.uploadify.min.js' // uploadify
                     ,'json2.js' // json2
                     ,'prism.js' // prism
                     ,'swfobject.js' // swfobject
                     ,'ColVis.js']  // ColVis
            },

            MathJax: {
                expand: true,
                cwd: 'invenio/base/static/MathJax/',
                src: ['**']
            },

            // TO DO: make it work keeping the folders included
            // not working properly removes all the files
            ckeditor: {
                expand: true,
                cwd: 'invenio/base/static/ckeditor/',
                src: ["**", '!**plugins/scientificchar/**']
            },

            jqueryTreeview: {
                expand: true,
                cwd: 'invenio/base/static/js/jquery-treeview/',
                src: ['**']
            },

            jqueryTableSorter: {
                expand: true,
                cwd: 'invenio/base/static/js/tablesorter/',
                src: ['**']
            },

            imagesUI: {
                expand: true,
                cwd: 'invenio/base/static/img/images/',
                src: ['**'],
            },

            themesUI: {
                expand: true,
                cwd: 'invenio/base/static/img/jquery-ui/',
                src: ['**'],
            }
        }


    });

    // RUN: `$ grunt clean` to clean all the installed dependencies
    
    grunt.registerTask('default', ['copy', 'uglify', 'cssmin']);

};