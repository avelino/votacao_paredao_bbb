/****
 * Functions to be used in the Admin to show the letter counter while user types in the textarea
 */

function update_letter_counter(obj) {
    var counter = obj.parent().find('.counter');

    if (counter.length == 0) {
        var counter = $('<div class="counter"><span class="remaining"></span> remaining</div>').insertAfter(obj);
    }

    counter.find('.count').text(obj.val().length);
    var total = parseInt(obj.attr('rel'));
    counter.find('.remaining').text(total - obj.val().length);
}

$(document).ready(function(){
    $('textarea.letter-counter').live('keyup', function(){
        update_letter_counter($(this));
    }).each(function(){
        update_letter_counter($(this));
    });
});