/*
 * This file is part of Invenio.
 * Copyright (C) 2014, 2015 CERN.
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


define(
  [
    'jquery',
    'bootstrap-tagsinput',
    'flight/lib/component',
  ],
  function(
    $,
    tagsinput,
    defineComponent) {

    'use strict';

    return defineComponent(HoldingPenTags);

    /**
    * .. js:class:: HoldingPenTags()
    *
    * Component for handling the filter/search available through the
    * bootstrap-tagsinput element.
    *
    * :param Array tags: list of tags to add from the beginning.
    *
    */
    function HoldingPenTags() {

      this.addTagFromMenu = function(ev, data) {
        // Tagsinput already deal with existing tags.
        this.$node.tagsinput('add', data);
      };

      this.addTagFromFreetext = function(ev) {
        // ev.item is the freeinput text
        if (ev.item.length != 0){
          ev.item = {text: ev.item, value: ev.item};
          // event.cancel: set to true to prevent the item getting added
          ev.cancel = false;
        }
      };

      this.getCurrentTags = function() {
        // Extract only the "real" value (ignore translated ones)
        return this.$node.tagsinput("items").map(function(currentValue, index, array) {
          return currentValue.value;
        });
      };

      this.onTagsUpdate = function(ev, data) {
        var payload = {};
        payload.tags = this.getCurrentTags();
        this.trigger(document, "reloadHoldingPenTable", payload);
      };


      this.after('initialize', function() {
        this.on(document, "addTagFromMenu", this.addTagFromMenu);
        this.on("itemAdded", this.onTagsUpdate);
        this.on("itemRemoved", this.onTagsUpdate);
        this.on('beforeFreeInputItemAdd', this.addTagFromFreetext);
        console.log("Tags init");
      });
    }
});
