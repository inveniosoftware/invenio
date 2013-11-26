'use strict';

$(document).on('hidden.bs.modal', function() {
    // delete any existing modal elements instead of just hiding them
    $('.modal').remove();
    $('.modal-backdrop').remove();
});
