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

define(
  [
    'jquery',
    'flight/lib/component',
  ],
  function(
    $,
    defineComponent) {

    return defineComponent(HoldingPenTags);

    /**
    * .. js:class:: HoldingPenTags()
    *
    * Component for handling the filter/search available through the
    * bootstrap-tagsinput element.
    *
    * :param Array tags: list of tags to add from the beginning.
    * :param string versionMenuItemSelector: selector for HoldingPenTagsMenu.
    *
    */
    function HoldingPenTags() {
      this.attributes({
        // URLs
        tags: [],
        versionMenuItemSelector: ".version-selection"
      });

      this.init_tags = function() {
        var $node = this.$node;
        $node.tagsinput({
            tagClass: function (item) {
                switch (item.value) {
                  case 'In process':
                    return 'label label-warning';
                  case 'Need action':
                    return 'label label-danger';
                  case 'Waiting':
                    return 'label label-warning';
                  case 'Done':
                    return 'label label-success';
                  case 'New':
                    return 'label label-info';
                  case 'Error':
                    return 'label label-danger';
                  default:
                    return 'badge badge-warning';
                }
            },
            itemValue: 'value',
            itemText: 'text'
        });
        // Add any existing tags
        this.attr.tags.map(function(item) {
          $node.tagsinput('add', item);
        });
      }

      this.addTagFromMenu = function(ev, data) {
        // Tagsinput already deal with existing tags.
        this.$node.tagsinput('add', data);
      }

      this.addTagFromFreetext = function(ev) {
        // ev.item is the freeinput text
        if (ev.item.length != 0){
          ev.item = {text: ev.item, value: ev.item};
          ev.cancel = false;
        }
      }

      this.onTagsUpdate = function() {
        // Extract first only the "real" value (ignore translated ones)
        var tags = this.$node.tagsinput("items").map(function(currentValue, index, array) {
          return currentValue.value;
        })

        var data = {
          'tags': tags
        };
        this.trigger(document, "reloadHoldingPenTable", data);
      }


      this.after('initialize', function() {
        this.on(document, "initHoldingPenTable", this.init_tags);
        this.on(document, "addTagFromMenu", this.addTagFromMenu);
        this.on(document, "itemAdded", this.onTagsUpdate);
        this.on(document, "itemRemoved", this.onTagsUpdate);
        this.on(document, 'beforeFreeInputItemAdd', this.addTagFromFreetext);
        console.log("Tags init");
      });
    }
});
