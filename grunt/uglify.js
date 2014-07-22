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

module.exports = {
    jqueryUI: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.installation_path %>/js/',
        src: ['jquery-ui.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        ext: '.min.js'
    },
    dataTables: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.installation_path %>/js/',
        src: ['jquery.dataTables.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        ext: '.dataTables.min.js'
    },
    jqueryFlot: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.installation_path %>/js/',
        src: ['jquery.flot.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        ext: '.flot.min.js'
    },
    jqueryFlotSelection: {
        expand: true,
        flatten: true,
        cwd: '<%= globalConfig.installation_path %>/js/',
        src: ['jquery.flot.selection.js'],
        dest: '<%= globalConfig.installation_path %>/js/',
        ext: '.flot.selection.min.js'
    }
}