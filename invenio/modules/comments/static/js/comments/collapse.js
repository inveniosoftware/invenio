'use strict';

$(document).ready(function() {
    // Support for AJAX loaded modal window.
    // Focuses on first input textbox after it loads the window.
    $('[data-toggle="modal"]').click(function(e) {
        e.preventDefault();
        var href = $(this).attr('href');
        if (href.indexOf('#') === 0) {
            $(href).modal('open');
        } else {
            $.get(href, function(data) {
                $('<div class="modal" >' + data + '</div>').modal();
            }).success(function() { $('input:text:visible:first').focus(); });
        }
    });

    $('.collapse').on('show', function(e) {
        $.get($(this).attr('data-action'));
        e.stopPropagation();
    });

    $('.collapse').on('hide', function(e) {
        $.get($(this).attr('data-action')).fail(function() { return; });
        e.stopPropagation();
    });

    $('a.collapse-comment').on('click', function(e) { e.preventDefault(); });

});
