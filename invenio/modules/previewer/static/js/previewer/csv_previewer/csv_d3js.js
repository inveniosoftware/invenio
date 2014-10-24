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

define(function(require) {
  'use strict';

  /**
   * Module dependencies
   */
  var d3 = require('vendors/d3/d3');

  var previewer = document.querySelector('div[data-previewer="d3csv"]');
  var delimiter = previewer.dataset.csvDelimiter
  var encoding = previewer.dataset.csvEncoding
  var resource = previewer.dataset.source;

  function tabulate(data, target, columns) {

    var table = d3.select(target).append("table").classed({
      'table': true,
      'table-hover': true,
      'table-bordered': true,
    }),
    thead = table.append("thead"),
    tbody = table.append("tbody");

    // append the header row
    thead.append("tr")
    .selectAll("th")
    .data(columns)
    .enter()
    .append("th")
    .text(function(column) { return column; });

    // create a row for each object in the data
    var rows = tbody.selectAll("tr")
    .data(data)
    .enter()
    .append("tr");

    // create a cell in each row for each column
    var cells = rows.selectAll("td")
    .data(function(row) {
      return columns.map(function(column) {
        return {column: column, value: row[column]};
      });
    })
    .enter()
    .append("td")
    .text(function(d) { return d.value; });

    return table;
  }

  var dsv = d3.dsv(delimiter, "text/csv; charset="+encoding);
  dsv(resource, function(data) {
    var col = Object.keys(data[0]);
    tabulate(data, previewer, col);
  });

});
