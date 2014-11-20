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
  'js/groups/remote.autocomplete.field',
  'jasmine-jquery',
], function(autocomplete, jasmineJQuery) {
  "use strict"

  describe("A suite", function() {

    beforeEach(function () {
      $('#test-form').remove()
      jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.modules.groups/fixtures/'
      $('body').append(readFixtures('test.html'))
    });

    afterEach(function(){
      $('#test-form').remove()
    })


    it("Autocomplete text is as expected", function() {
      autocomplete()

      var obj = $('#user_id')
      var iobj = $('#user_id_interface')

      expect(iobj.attr('type')).toBe('text');
      expect(iobj.attr('data-autocomplete-data-value')).toBe('nickname');
      expect(iobj.attr('data-autocomplete-data-key')).toBe('id');
      expect(iobj.attr('data-autocomplete-highlight')).toBe('true');
      expect(iobj.attr('data-autocomplete-minlength')).toBe('2');
      expect(iobj.attr('data-autocomplete-displaykey')).toBe('nickname');
      expect(iobj.attr('data-autocomplete-remote')).toBe('spec/invenio.modules.groups/fixtures/users.json?name=%QUERY');

      expect(obj.attr('type')).toBe('hidden');
      expect(obj.attr('name')).toBe('user_id');
    });
  });
});
