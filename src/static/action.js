;$(document).ready(function () {
  $(".participante").click(function () {
    $(".participante .foto").removeClass('selected');
    i = $(this).find('.foto')
    i.addClass('selected');
    $("form [name=result]").val(i.attr('rel'))
  });
});
