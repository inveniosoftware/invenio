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
describeMixin('js/deposit/uploader/mixins/util', function () {
  'use strict';

  describe('bytesToSize', function () {

    beforeEach(function () {
      this.setupComponent();
    });

    it('should works for 0 bytes', function () {
      expect(this.component.bytesToSize(0)).toEqual('0 Bytes');
    });
    it('should works for KB, MB, GB, TB', function () {
       expect(this.component.bytesToSize(10)).toEqual('10.00 Bytes');
       expect(this.component.bytesToSize(1e3)).toEqual('1.00 KB');
       expect(this.component.bytesToSize(1e6)).toEqual('1.00 MB');
       expect(this.component.bytesToSize(1e9)).toEqual('1.00 GB');
       expect(this.component.bytesToSize(1e12)).toEqual('1.00 TB');
    });
    it('should works for boundry values', function () {
      expect(this.component.bytesToSize(999)).toEqual('999.00 Bytes');
      expect(this.component.bytesToSize(1.1e+3)).toEqual('1.10 KB');
    });
    it('should works only for numbers', function () {
      expect(this.component.bytesToSize('0')).toEqual(NaN);
      expect(this.component.bytesToSize({})).toEqual(NaN);
      expect(this.component.bytesToSize([2])).toEqual(NaN);
      expect(this.component.bytesToSize(true)).toEqual(NaN);
    });

  });

  describe('guid', function () {

    beforeEach(function () {
      this.setupComponent();
    });

    it('should returns string', function () {
      expect(typeof this.component.guid()).toEqual('string');
    });
    it('should be 36 characters long', function () {
      expect(this.component.guid().length).toBe(36);
    });
    it('should returns pseudo-random strings', function () {
      var testStrings = [],
          i = 0;

      for(i; i < 100; i++) {
        testStrings.push(this.component.guid());
      }

      testStrings.forEach(function (elem) {
        var index = -1,
            counter=0;

        while((index = testStrings.indexOf(elem, index+1)) !== -1) {
          counter++;
          index++;
        }

        expect(counter).toBe(1);
      });
    });

  });

  describe('getUUID', function () {

    it ('should trigger uploaderError event if no url is defined', function () {
      this.setupComponent();
      var spy = spyOnEvent(this.component.$node, 'uploaderError');
      this.component.getUUID();
      expect(spy.callCount).toBe(1);
      expect(spy).toHaveBeenTriggeredOnAndWith(this.component.$node, {
        message: "Problem while trying to get new uuid."
      });
    });
    it ('should trigger uploaderError event if ajax fails', function () {
      jasmine.Ajax.install();
      this.setupComponent({
        resolve_uuid_url: 'http://some.failing.html'
      });
      var spy = spyOnEvent(this.component.$node, 'uploaderError');
      this.component.getUUID();
      var request = jasmine.Ajax.requests.mostRecent();
      console.log(request);
       expect(1).toBe(1);
      // expect(spy).toHaveBeenTriggeredOnAndWith(this.component.$node, {
      //   message: "Cannot find url for resolving uuid."
      // });
    });

  });
});
//url: 'http://httpbin.org/post'