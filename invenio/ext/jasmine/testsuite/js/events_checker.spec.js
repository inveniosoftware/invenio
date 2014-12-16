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
  'jasmine-events',
], function() {

  var $test;

  describe('Events Checker', function() {

    function Class1($element) {
      this.$element = $element;

      var that = this;
      this.$link1 = this.$element.find('.link1');
      this.$link2 = this.$element.find('.link2');
      this.$link3 = this.$element.find('.link3');

      this.$link1.on('clicked', function (event) {
        that.$element.trigger('link1_clicked');
      });

      this.$link2.on('custom_event', function (event) {
        that.$element.trigger('link2_custom_event');
      });

      this.$link3.on('clicked', function (event) {
        that.on_link3Clicked();
      });
    }

    Class1.prototype = {

      update: function () {
        this.$element.trigger('updated');
        this.on_updated();
      },

      on_link3Clicked: function () {
        this.on_link3Clicked2();
      },

      on_link3Clicked2: function () {},

      on_updated: function () {},

      callUpdate: function () {
        this.update();
      },

      updateIfCalledWithTrue: function(arg1, arg2) {
        if (arg1 === true && arg2 === true) {
          this.$element.trigger('updated');
        }
      }
    };

    var obj1;
    var checker;
    var testedConnections;
    var eventEventConnections;

    beforeEach(function () {
      $('body').append('<div id="test"></div>');
      $test = $('#test');
      var links = '<div class="main">' +
          '<a class="link1">1</a>' +
          '<a class="link2">2</a>' +
          '<a class="link3">3</a>' +
        '</div>';

      $test.append(links);

      obj1 = new Class1($test);
      testedConnections = [];

      eventEventConnections = [
        {
          triggered: {
            $element: $test.find('.link1'),
            event: 'clicked'
          },
          expected: {
            $element: $test,
            event: 'link1_clicked'
          }
        },
        {
          triggered: {
            $element: $test.find('.link2'),
            event: 'custom_event'
          },
          expected: {
            $element: $test,
            event: 'link2_custom_event'
          }
        },
      ];
    });

    afterEach(function () {
      $test.remove();
      obj1 = undefined;
      checker = undefined;
      testedConnections = undefined;
    });

    describe('passes a test' , function() {

      afterEach(function() {
        expect(testedConnections).toPassConnectionTests();
      });

      describe('checking of event->event connections', function() {

        afterEach(function () {
          expect(testedConnections).toPassConnectionTests();
        });

        it('with events correctly triggering other events',
          function () {
          }
        );

        it('even if it tests twice the same connections,' +
            'because spies should be reset every run',
          function () {
            expect(eventEventConnections).toPassConnectionTests();
          }
        );
      });

      describe('checking of mixed connections', function() {

        it('with functions correctly triggering events', function () {
          testedConnections.push({
            triggered: {
              object: obj1,
              methodName: 'update',
            },
            expected: {
              $element: obj1.$element,
              event: 'updated'
            }
          },
          {
            triggered: {
              object: obj1,
              methodName: 'updateIfCalledWithTrue',
              args: [true, true]
            },
            expected: {
              $element: obj1.$element,
              event: 'updated',
            }
          });
        });

        it('with functions correctly triggering functions', function () {
          testedConnections.push({
            triggered: {
              object: obj1,
              methodName: 'callUpdate',
            },
            expected: {
              object: obj1,
              methodName: 'update',
              args: ['a']
            }
          });
        });

        it('with events correctly triggering functions', function () {

          testedConnections.push({
            triggered: {
              $element: obj1.$link3,
              event: 'clicked'
            },
            expected: {
              object: obj1,
              methodName: 'on_link3Clicked',
            },
          });
        });

        it('with chained connections the tests doesn\'t interfere', function () {
          obj1.update();

          testedConnections.concat([{
            triggered: {
              $element: obj1.$link3,
              event: 'clicked'
            },
            expected: {
              object: obj1,
              methodName: 'on_link3Clicked'
            }
          },
          {
            triggered: {
              object: obj1,
              methodName: 'on_link3Clicked'
            },
            expected: {
              object: obj1,
              methodName: 'on_link3Clicked2'
            }
          }]);

          testedConnections.concat([{
            triggered: {
              object: obj1,
              methodName: 'callUpdate',
            },
            expected: {
              object: obj1,
              methodName: 'update',
              args: ['a']
            }
          },
          {
            triggered: {
              object: obj1,
              methodName: 'update',
            },
            expected: {
              object: obj1,
              methodName: 'on_updated',
            },
          }]);
        });
      });
    });

    describe('fails a test', function() {
      afterEach(function () {
        expect(testedConnections).not.toPassConnectionTests();
      });

      it('cause there is one not existing connection',
        function () {
          testedConnections.push({
            triggered: {
              $element: $test.find('.link2'),
              event: 'custom_event'
            },
            expected: {
              $element: $test,
              event: 'link3_custom_event'
            }
          });
        }
      );

      it('cause `this` pointer is invalid', function () {
        testedConnections.push({
          triggered: {
            //object: obj1,
            methodName: 'update',
          },
          expected: {
            $element: obj1.$element,
            event: 'updated'
          }
        });
      });
    });

  });

});
