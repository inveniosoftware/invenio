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
  'hgn!js/search/facets/configuration/links/option',
  'js/search/facets/filter',
  'js/search/facets/states',
  'js/search/facets/option',
], function(optionTemplate, Filter, states) {

  var optionConfiguration = {

    template: optionTemplate,

    on_activated: function($facet_option) {
      var facet_option = $facet_option.data('facet-option');
      facet_option.$toggle_filter_button.addClass('option-active');
    },
    on_deactivated: function($facet_option) {
      $facet_option.data('facet-option').$toggle_filter_button
        .removeClass('option-active');
    },
    on_partially_activated: function($facet_option) {
      $facet_option.data('facet-option').$toggle_filter_button
        .addClass('option-active');
    },

    disable_expansion: function ($row) {}
  };

  var facetsContentMock = [
    {
      "facet": "year",
      "title": "Year",
      "url": "/facet/year/mock"
    },
    {
      "facet": "collection",
      "title": "Collection",
      "url": "/facet/collection/mock"
    }
  ];

  var optionListConfiguration = {
    split_by: 2,
  }

  var filterConfiguration = {
  };

  var optionContent = {
    "id": "2002",
    "is_expandable": false,
    "label": "2002",
    "records_num": 24
  };

  var filter = function($element) {
    return {
      $element: $element,
      events: Filter.events,
      update: function () {},
      url: 'mocked_url',
    };
  };

  var facetEngineGenerator = function($element) {
    return {
      $element: $element,
    }
  };

  var facetOptionGenerator = function($element) {
    return {
      $element: $element,
      getId: function() {
        return 'parentMock';
      },
      getState: function() {
        return states.inactive;
      }
    }
  };

  function optionsListGenerator($element) {
    return {
      $element: $element,
    }
  }

  var collectionResponseMock = {
    facet: [
      {
        id: "Articles & Preprints",
        is_expandable: true,
        label: "Articles & Preprints",
        records_num: 69,
      },
      {
        id: "Reports",
        is_expandable: false,
        label: "Reports",
        records_num: 16,
      },
      {
        id: "Multimedia",
        is_expandable: false,
        label: "Multimedia",
        records_num: 16,
      },
      {
        id: "Photos",
        is_expandable: false,
        label: "Photos",
        records_num: 100,
      },
    ]
  };

  var listEntriesMock = {
    "facet": [
      {
        "id": "2002",
        "is_expandable": false,
        "label": "2002",
        "records_num": 24
      },
      {
        "id": "2000",
        "is_expandable": false,
        "label": "2000",
        "records_num": 6
      },
      {
        "id": "2001",
        "is_expandable": false,
        "label": "2001",
        "records_num": 4
      },
      {
        "id": "1972",
        "is_expandable": false,
        "label": "1972",
        "records_num": 3
      },
      {
        "id": "1982",
        "is_expandable": false,
        "label": "1982",
        "records_num": 3
      },
    ]
  };

  var listEntriesQueryMock = {
    success: {
      status: 200,
      responseText: JSON.stringify(listEntriesMock),
    }
  }

  function getResponse(responseCode, responseObj) {
    return {
      status: responseCode,
      responseText: JSON.stringify(responseObj),
    }
  }

  return {
    optionConfiguration: optionConfiguration,
    facetsContentMock: facetsContentMock,
    optionListConfiguration: optionListConfiguration,
    filterConfiguration: filterConfiguration,
    optionContent: optionContent,
    filter: filter,
    facetEngineGenerator: facetEngineGenerator,
    facetOptionGenerator: facetOptionGenerator,
    optionsListGenerator: optionsListGenerator,
    collectionResponseMock: collectionResponseMock,
    listEntriesMock: listEntriesMock,
    listEntriesQueryMock: listEntriesQueryMock,
    getResponse: getResponse,
  }

});