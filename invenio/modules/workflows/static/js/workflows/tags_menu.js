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

'use strict';

define(
  [
    'jquery',
    'flight/lib/component'
  ],
  function(
    $,
    defineComponent) {

    return defineComponent(HoldingPenTagsMenu);

    /**
    * .. js:class:: HoldingPenTagsMenu()
    *
    * UI Component for a dropdown menu to add to the tagsinput.
    *
    * :param string menuitemSelector: DOM selector for each menu item.
    *
    */
    function HoldingPenTagsMenu() {

      this.attributes({
        menuitemSelector: "#menu a",
        valuePrefix: ""
      });

      this.triggerAddTagFromMenu = function(ev, data) {
        var value = this.attr.valuePrefix + data.el.name;
        this.trigger(document, "addTagFromMenu", {
          value: value,
          text: value
        });
      };

      this.after('initialize', function() {
        this.on("click", {
          menuitemSelector: this.triggerAddTagFromMenu
        });
        console.log("Tags menu init");
      });
    }
});
