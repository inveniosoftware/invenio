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


module.exports = function (grunt) {
    var prefix = process.env.VIRTUAL_ENV || '../..'
      , globalConfig = {
            bower_path: 'bower_components',
            installation_path: prefix + '/var/invenio.base-instance/static'
        };

    // target for custom path
    if (grunt.option('path')) {
        globalConfig.installation_path = grunt.option('target', grunt.option('path'))
    }

    // show elapsed time at the end
    require('time-grunt')(grunt);

    // load all grunt tasks
    require('load-grunt-config')(grunt, {
        config: {
            globalConfig: globalConfig
        }
    });
};
