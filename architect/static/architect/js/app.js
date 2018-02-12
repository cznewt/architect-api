'use strict';

$(window).on('load', function () {
    setTimeout(function () {
        $('.page-loader').fadeOut();
    }, 200);
});

$(window).on('beforeunload', function () {
    $('.page-loader').fadeIn();
});

$(function() {

  $(document).on("click", "a.open-modal", function () {
    var url = $(this).attr('href');
    var modal = $('#modal-container');
    $.ajax({
      url: url,
    }).done(function(response) {
      modal.html(response);
      modal.modal('show');
    });
    event.preventDefault();
  });

});
