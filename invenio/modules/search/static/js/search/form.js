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


define([
    'jquery',
    'searchtypeahead-configuration',
    'typeahead',
    'js/search/typeahead',
], function($, getParserConf, Bloodhound) {
    "use strict";

    $("form[name=search]").submit(function() {
        $('.add_to_search-form').remove()
        return true; // ensure form still submits
    })

    var spanWidth = "100px"

    // side buttons for results number field
    $('form[name=settings] select[name="of"]').buttonSelect({
        button: '<div class="btn btn-sm btn-default" />',
        span: '<span class="btn btn-sm btn-default" style="width:' + spanWidth +'" />',
        next: '<i class="glyphicon glyphicon-chevron-right"></i>',
        prev: '<i class="glyphicon glyphicon-chevron-left"></i>'
    })

    // side buttons for output format field
    $('form[name=settings] select[name="rg"]').buttonSelect({
        button: '<div class="btn btn-sm btn-default" />',
        span: '<span class="btn btn-sm btn-default" style="width:' + spanWidth +'" />',
        next: '<i class="glyphicon glyphicon-plus"></i>',
        prev: '<i class="glyphicon glyphicon-minus"></i>'
    })

    // if (!("autofocus" in $("form[name=search] input[name=q]"))) {
    //  // ensure we get the focus always in search input
    //  $("form[name=search] input[name=q]").focus();
    // }

    /**
     * Allows to deactivate a radio buttons (like check-buttons)
     * and make them behave as radio ones when the another one is clicked
     */
    $(".invenio-collapsable-tabs a").each(function(elem) {
        $(elem).click(function (){
            var buttons = $(this).siblings();
            if (buttons.hasClass("active")) {
                buttons.click()
            }
        })
    })


    // ------------ typeahead for "Add to search" form ----------------

    $('[data-provide="typeahead-url"]').each(function(index, elem) {

        var field = $(elem),
            source = field.data('source')

        var engine = new Bloodhound({
           datumTokenizer: function(d) {
                return Bloodhound.tokenizers.whitespace(d.value)
            },
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            limit: 10,
            remote: {
                url: source,
                replace: function(url, query) {
                    return url + '?q=' + query
                },
                filter: function(response) {
                    return response.results
                }
            }
        })

        engine.initialize()

        field.typeahead(
            {
                minLength: 3
            },
            {
                source: engine.ttAdapter(),
                displayKey: 'value'
            }
        )
    })

    //---------------------

    return function(form) {

        var operators = {'a': 'AND ', 'o': 'OR ', 'n': 'AND NOT '},
            // the visible search field
            searchQueryField = $('form[name=search] input[name=p]'),
            // all fields containg search query, there are some hidden ones too
            allSearchQueryFields = $('[name=p]')

       /**
         * Sets value of the main search field. Should be used
         * instead of jQuery's val() to update typeahead's
         * internal query.
         *
         * @method setSearchFieldValue
         * @param {String} val value to be set
         */
        function setSearchFieldValue(val) {
            searchQueryField.data('search_typeahead').setFieldValue(val)
            allSearchQueryFields.val(val)
        }


        /**
         * Merges value from 'advanced' tab in 'Add to search' form
         * with the current search query
         *
         * @method addAdvancedQuery
         * @returns {String} search query after adding the form content
         */
        function getAdvancedQuery() {
            var m1 = $('[name=m1]').val(),
                p1 = $('[name=p1]').val(),
                f = $('[name=f]').val(),
                p = $('[name=p]')

            if (p1 === "") {
                return ''
            }
            if (f !== "") {
                f += ':'
            }

            return form.matchingTypes[m1](p1, f)
        }

        /**
         * Removes query value from 'what?' field in 'advanced' tab
         *
         * @method cleanAdvancedQuery
         */
        function cleanAdvancedQueryForm() {
            $('[name=p1]').val('')
        }

        /**
         * Removes query values from all fields in 'simple' tab
         *
         * @method cleanSimpleQueryForm
         */
        function cleanSimpleQueryForm() {
            $(':focus').blur()
            $('#simple-search input').val('')
        }

        /**
         * Creates search query from 'simple' tab in 'Add to search' form
         *
         * @method getSimpleQuery
         * @returns {String} query from the form content
         *
         */
        function getSimpleQuery() {
            var query_str = '';

            // get values
            var p = $('[name=p]'),
                query = [],
                op1 = $('#add_type-btn-group .active').children(':first').val(),
                author = $('#author').val(),
                title = $('#title').val(),
                rn = $('#rn').val(),
                aff = $('#aff').val(),
                cn = $('#cn').val(),
                k = $('#k').val(),
                //eprinttype = $('#eprint-type').val(),
                //eprintnumber = $('#eprint-number').val(),
                j = $('#journal-name').val(),
                jvol = $('#journal-vol').val(),
                jpage = $('#journal-page').val(),
                //match every word or the whole sentence in the quotes
                matcher = /("(?:[^"\\]|\\.)*")|('(?:[^'\\]|\\.)*')|(\S+)/g

            function buildQueryElement(fieldName, input, reg) {
                reg = reg ? reg : matcher;
                var matches = input.match(reg);

                return $.map(matches, function(item) {
                    return fieldName + item;
                }).join(" " + operators[op1] + " ");
            }

            if (author !== '') {
                query.push('author:' + '\"' + author + '\"');
            }
            if (title !== '') {
                query.push('title:' + '\"' + title + '\"');
            }
            if (rn !== '') {
                query.push(buildQueryElement("reportnumber:", rn));
            }
            if (aff !== '') {
                query.push(buildQueryElement("affiliation:", aff));
            }
            if (cn !== '') {
                query.push(buildQueryElement('collaboration:', cn));
            }
            if (k !== '') {
                query.push(buildQueryElement('keyword:', k));
            }

            if (j !== '') { query.push('journal:' + j); }
            if (jvol !== '') { query.push('909C4v:' + jvol); }
            if (jpage !== '') { query.push('909C4c:' + jpage); }

            if (query.length > 0) {
                query_str = query.join(' ' + operators[op1]);
            }

            return query_str;
        }

        /**
         * Adds query from 'advanced' tab to the search field
         *
         * @method addAdvancedQueryToSearch
         */
        function addAdvancedQueryToSearch() {
            var current_query = $.trim(searchQueryField.val());
            var new_part = getAdvancedQuery();
            cleanAdvancedQueryForm();
            setSearchFieldValue(mergeQuery(current_query, new_part));
        }

        /**
         * Merges new part to old query using currently
         * chosen logic function
         *
         * @method mergeQuery
         * @param {String} old_query old query
         * @param {String} new_part a string which user is going to merge
         */
        function mergeQuery(current_query, new_part) {
            if (new_part === "") {
                return current_query;
            }

            var op1 = $('#add_type-btn-group .active').children(':first').val(),
                op = '';

            if (op1 !== 'a' || current_query !== "") {
                op = operators[op1]
            }

            if (current_query + new_part !== "") {
                current_query += ' ' + op;
            }

            return current_query + new_part;
        }

        /**
         * Updates query value in the search field
         *
         * @method makeSearchQuery
         */
        function makeSearchQuery() {
            var active_tab = $('.add_to_search-form .tab-buttons li.active a').attr('href');

            if (active_tab === '#simple-search') {
                var current_query = $.trim(searchQueryField.val())
                var new_part = getSimpleQuery()
                setSearchFieldValue(mergeQuery(current_query, new_part))
                cleanSimpleQueryForm()
            } else {
                addAdvancedQueryToSearch()
                $('.add_to_search-form .appender').trigger('click')
            }
        }

        // search buttons
        $('.add_to_search-form button[name=action_search]').on('click', function(e) {
            makeSearchQuery()
            e.stopPropagation()
        })

        // browse buttons
        $('.add_to_search-form button[name=action_browse]').on('click', function(e) {
            makeSearchQuery()
            var $main_search_button = $('#searchform-input-group button[name=action_search]')
            $main_search_button.attr('name', 'action_browse')
            $main_search_button.trigger('click')
        })

        $('#add_to_search-button').on('click', function(e) {
            addAdvancedQueryToSearch()
            return false
        })

        $('.add_to_search-form #advanced-search input, .add_to_search-form #simple-search input').keypress(function(event) {
            // on 'return' key
            if ( event.which == 13 ) {
                makeSearchQuery()
                return false
            }
        })

        $('.add_to_search-form #advanced-search .appender').on('click', function(e) {
            var op1 = $('#add_type-btn-group .active').children(':first').val(),
                btn = $(this),
                source = $('[name=' + btn.data('source') + ']'),
                target = $('[name=' + btn.data('target') + ']'),
                val = $.trim(target.val()),
                op = (op1 == 'a' && val === '') ? '' : operators[op1]

            if (val !== '') {
                val += ' ' + op
            }
            if (source.val().length > 0) {
                target.val(val + source.attr('name') + ':"' + source.val() + '"')
                source.val('')
            }
            e.stopPropagation()
            return false
        })

        // -------------- SEARCH FIELD TYPEAHEAD ----------------

        var areaKeywords = $.map(form.keywords, function(val, i) {
            return val[0]
        })

        $('form[name=search] input[name=p]').searchTypeahead({
          value_hints_url: form.hintsUrl,
          options_sets: getParserConf(areaKeywords),
          default_set: form.defaultSet
        })
    }
})
