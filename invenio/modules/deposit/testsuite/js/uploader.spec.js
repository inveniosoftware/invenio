/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
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

define([
  'js/deposit/uploader/uploader',
  'jasmine-flight',
  'jasmine-jquery',
], function(uploader, jasmineFlight, jasmineJQuery) {
  describeComponent('js/deposit/uploader/uploader', function () {

    'use strict';

    jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.modules.deposit/fixtures/';
    var uploaderFixture = readFixtures('uploader.html');

    describe('basic', function () {
      var config = {
        get_file_url: '',
        delete_url: '',
        form_selector: "#submitForm",
        form_files: [],
        resolve_uuid_url: '',
        resolve_uuid: true,
        autoupload: false,
        continue_url: ''
      };

      beforeEach(function () {
        this.setupComponent(uploaderFixture, config);
      });

      it('', function () {

      });
    });

    describe('autoupload', function () {
      it('', function () {
      });
    });

    describe('resolve_uuid', function () {
      it('', function () {
      });
    });
  });
});
