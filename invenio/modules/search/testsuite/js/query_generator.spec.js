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
  'js/search/query_generator',
  'jasmine-boot',
], function(QueryGenerator) {

  var generateQuery = QueryGenerator.generateQuery;

  describe('Invenio query generator', function() {

    it('with exclude and limit to', function() {
      expect(generateQuery({
        collection: {
          '+': ['Reports'],
          '-': ['Multimedia']
        }
      })).toEqual('collection:Reports AND NOT collection:Multimedia');
    });

    it('wraps names with spaces in brackets', function() {
      expect(generateQuery({
        collection: {
          '+': ['Articles & Preprints']
        }
      })).toEqual('collection:"Articles & Preprints"');
    });

    it('with two limit to', function() {
      expect(generateQuery({
        collection: {
          '+': ['Reports', 'Multimedia']
        }
      })).toEqual('collection:Reports OR collection:Multimedia');
    });

    it('with two exclude', function() {
      expect(generateQuery({
        collection: {
          '-': ['Reports', 'Multimedia']
        }
      })).toEqual(
        'NOT (collection:Reports OR collection:Multimedia)');
    });

    it('adds parentheses around exclude and limit to parts', function() {
      expect(generateQuery({
        collection: {
          '+': ['Articles & Preprints', 'Photos'],
          '-': ['Reports', 'Multimedia']
        }
      })).toEqual(
        '(collection:"Articles & Preprints" OR collection:Photos) ' +
          'AND NOT (collection:Reports OR collection:Multimedia)');
    });

    it('properly adds parentheses around query when requested',
      function() {
        expect(generateQuery({
          collection: {
            '+': ['Reports', 'Multimedia']
          }
        }, true)).toEqual(
          '(collection:Reports OR collection:Multimedia)');
        expect(generateQuery({
          collection: {
            '+': ['Reports', 'Multimedia']
          },
          year: {
            '+': ['2001', '2000']
          }
        }, true)).toEqual(
          '((collection:Reports OR collection:Multimedia) AND ' +
          '(year:2001 OR year:2000))');
      }
    );

    it('adds parentheses around a filter part consisting of more than one ' +
      'part', function() {
      expect(generateQuery({
          collection: {
            '+': ['Reports', 'Multimedia']
          },
          year: {
            '+': ['2001', '2000']
          }
        })).toEqual(
          '(collection:Reports OR collection:Multimedia) AND ' +
          '(year:2001 OR year:2000)');
      expect(generateQuery({
          collection: {
            '+': ['Reports', 'Multimedia']
          },
          year: {
            '+': ['2001']
          }
        })).toEqual(
          '(collection:Reports OR collection:Multimedia) AND ' +
          'year:2001');
    });

    it('doesn\'t duplicate the parentheses on at NOT expression', function () {
      expect(generateQuery({
        collection: {
          '+': ['Articles & Preprints']
        },
        year: {
          '-': ['2000', '2002']
        }
      })).toEqual(
        'collection:"Articles & Preprints" AND NOT (year:2000 OR year:2002)');
    });

  });

});