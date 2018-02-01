'use strict';

$(window).on('load', function () {
    setTimeout(function () {
        $('.page-loader').fadeOut();
    }, 200);
});

$(window).on('beforeunload', function () {
    $('.page-loader').fadeIn();
});
