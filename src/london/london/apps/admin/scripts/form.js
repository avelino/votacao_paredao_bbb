function apply_admin_form_events() {
    $('form.module-form').submit(function(){
        // Form forms with files to upload, just submits as usual
        if ($(this).attr('enctype') == 'multipart/form-data' || $(this).attr('rel') == 'nohistory') {
            return true;
        }

        var inputs = $(this).find(':input');
        var params = {};
        for (var iInp=0; iInp<inputs.length; iInp++) {
            if (!$(inputs[iInp]).attr('name')) continue;

            var value = $(inputs[iInp]).val();
            if ($(inputs[iInp]).attr('type') == 'checkbox') {
                value = $(inputs[iInp]).is(':checked') ? 'on' : 'off';
            }
            
            params[$(inputs[iInp]).attr('name')] = value;
        }
        $.post($(this).attr('action'), params, function(resp){
            london.load_response(resp);
        });
        return false;
    });

    $('#save-as-new').click(function(){
        $('form').append('<input name="save_as_new" value="1" type="hidden"/>').submit();
    });
}

$('body').live('london_ready', apply_admin_form_events);

