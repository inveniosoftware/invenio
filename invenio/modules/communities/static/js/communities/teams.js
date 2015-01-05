define(
  ['jquery'],
  function () {
    'use strict';

    $('[data-href]').each(function (i, element) {
      $(element).click(function () {
        window.location.href = $(element).data('href');
      });
    });
  }
);
