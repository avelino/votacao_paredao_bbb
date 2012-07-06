function update_notifications() {
    // Notifications coming via cookies
    
    var cookies = document.cookie.split(';');
    var messages = [];
    if (cookies) {
        for (var iCnt=0; iCnt<cookies.length; iCnt++) {
            var name = cookies[iCnt].substring(0, cookies[iCnt].indexOf('=')).replace(/^\s+|\s+$/g,'');
            if (name.indexOf('{{ notifications_cookie_prefix }}') != 0) continue;

            var id = name.substring(16,name.length);
            var content = cookies[iCnt].substring(cookies[iCnt].indexOf('=')+1, cookies[iCnt].length);

            if (content.charAt(0) == '"' && content.substring(2,content.length).indexOf('"') >= 0) {
                content = content.substring(1,content.length);
                content = content.substring(0,content.indexOf('"'));
            }
            if (content) {
                var level = content.split(':')[0];
                var message_hash = content.split(':')[1];
                var released_at = content.split(':')[2];
                var message = content.substring(level.length+message_hash.length+released_at+4,content.length);

                messages.push(format_notification_message({
                    'id': id,
                    'level': level,
                    'message': message,
                    'message_hash': message_hash,
                    'released_at': released_at
                }));
            }
            document.cookie = name+'=; path=/';
        }
    }
    if (messages.length) {
        $('body').trigger('notifications', [messages]);
    }
}

function format_notification_message(msg) {
    var bits = msg['released_at'].split(' ');
    var bits_date = bits[0].split('-');
    var bits_time = bits[1].split(':');
    msg['released_at'] = {'raw':msg['released_at'], 'date':new Date(bits_date[0],parseInt(bits_date[1])-1,bits_date[2],bits_time[0],bits_time[1])};
    return msg;
}

$(document).ready(function(){
    // Notifications coming via Ajax requests with JSON response
    $(document).ajaxComplete(function(e,xhr,settings){
        if (xhr.responseText.indexOf('"_notifications"') >= 0) {
            var json = JSON.parse(xhr.responseText);
            if (json._notifications) {
                var list = [];
                for (var iMsg=0; iMsg<json._notifications.length; iMsg++) {
                    list.push(format_notification_message(json._notifications[iMsg]));
                }
                $('body').trigger('notifications', [list]);
            }
        }
    });
});

$('body').live('london_ready', update_notifications);

