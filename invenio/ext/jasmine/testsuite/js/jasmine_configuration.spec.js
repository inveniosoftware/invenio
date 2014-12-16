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

define([
  'jasmine/spec/invenio.ext.jasmine/jquery_object_mock',
  'jasmine-jquery',
], function(MockObject) {

  describe('Jasmine configuration', function() {

    describe('Javascript conflicts', function() {

      it('jquery from the tested file doesn\'t conflict with the global one',
        function() {

          var mockObj = new MockObject($('body'));
          var eventSpy = jasmine.jQuery.events.spyOn($('body'), 'event');

          expect(eventSpy).not.toHaveBeenTriggered();
          mockObj.triggersEvent();
          // if there is a conflict this raises an exception,
          // cause the spy handler is added to different instace of jquery
          // than the one in `jquery_object_mock` file where the event is 
          // triggered.
          expect(eventSpy).toHaveBeenTriggered();
        }
      );
    });

  });
});
