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


define([
  'js/remote.autocomplete.field',
  'jasmine-jquery',
], function(autocomplete, jasmineJQuery) {
  "use strict"

  describe("RemoteAutocomplete suite", function() {

    beforeEach(function () {
      $('#test-form').remove()
      jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.base/fixtures/'
      $('body').append(readFixtures('test.html'))
    });

    afterEach(function(){
      $('#test-form').remove()
    })


    it("RemoteAutocomplete input text is as expected", function() {
      autocomplete.attachTo($('input.remote-typeahead-widget'))

      var obj = $('#user_id')
      var iobj = $('#user_id_interface')

      expect(typeof iobj.attr('name')).toEqual('undefined');
      expect(iobj.attr('type')).toEqual('text');
      expect(iobj.data('remoteautocomplete-data-value')).toEqual('nickname');
      expect(iobj.data('remoteautocomplete-data-key')).toEqual('id');
      expect(iobj.data('remoteautocomplete-highlight')).toEqual(true);
      expect(iobj.data('remoteautocomplete-minlength')).toEqual(2);
      expect(iobj.data('remoteautocomplete-remote')).toEqual('spec/invenio.modules.groups/fixtures/users.json?name=%QUERY');

      expect(obj.attr('type')).toEqual('hidden');
      expect(obj.attr('name')).toEqual('user_id');
    });
  });
});
