$('body').bind('london_ready', function(){
    // General functions
    set_main_width();
    reset_textarea_width();
    apply_pagination_events();
    apply_search_events();
    apply_module_search();

    // Sets home as page type
    if (location.pathname == '/admin/') {
        london_admin.page_type = 'home';
    }

    // List functions
    if (london_admin.page_type == 'module_list' || london_admin.page_type == 'module_form' || london_admin.page_type == 'module_delete') {
        // Loads empty columns
        if ($('#side-bar').length != 0 && $('#side-bar').children().length == 0) {
            $('#side-bar').append('<div></div>');
            london.load_url('{{ admin_site.root_url }}');
        }
    }

    // List functions
    if (london_admin.page_type == 'module_form' || london_admin.page_type == 'module_delete') {
        // Loads empty columns
        if ($('#content').children().length === 0) {
            $('#content').append('<div></div>');
            var exp = new RegExp("^(\/.+?\/.+?\/.+?\/).*");
            var m = exp.exec(location.pathname);
            if (m) {
                london.load_url(m[1] + '?_ignore_module_form=1');
            }
        };
    }

    // The other pages
    if (london_admin.page_type == 'home') {
        $('#content').empty();
        $('#submenu').empty();
        $('#module_form').empty();
    }
});

$(window).resize(function() {
	set_main_width();
	reset_textarea_width();
});

function set_main_width() {
	$('#main').css('left',$('#side-bar').width());

    if ($('#side-nav').length) {
        $('#side-nav').height($('#side-nav').parent().outerHeight() - $('#side-nav').position().top);
    }
}

function set_label_width() {
	$('form').each(function() {
		var width = 0;
		$(this).find('label').each(function() {
			var new_width = $(this).width();
			if (new_width > width) width = new_width;
		});
		$(this).find('label').width(width);
		var textarea_width = $(this).width() - width - 11;
		$(this).find('textarea').width(textarea_width).css('vertical-align','top');
	});
}

function reset_textarea_width() {
	$('form').each(function() {
        var label_width = $(this).find('textarea').prev('label').outerWidth(true);
        var form_width = $(this).width();
		$(this).find('textarea').width(form_width - label_width - 10);
	});
}

function side_nav_click() {
	$('#side-nav .app').click(function() {
		if (!$(this).children('.show-application').hasClass('open')) {
			$('#side-nav .modules').slideUp();
			$('#side-nav .app').children('.show-application').removeClass('open');
			$(this).children('.modules').slideToggle()
			$(this).children('.show-application').toggleClass('open');
		}
	});
}

function apply_pagination_events() {
    function pagination_click(e){
        var url = location.pathname.match(/(\/.*?\/.*?\/.*?\/).*/)[1] + $(this).attr('href');
        london.load_url(url, apply_pagination_events);
        e.preventDefault();
    }

    $('.pagination a').each(function(){
        if ($(this).data('pagination_click')) return;
        $(this).click(pagination_click).data('pagination_click', true);
    });
}

function apply_search_events() {
    $('form.search-form').each(function(){
        var form = $(this);
        if (form.data('search_submit')) return;

        form.submit(function(){
            // Form forms with files to upload, just submits as usual
            if ($(this).attr('rel') == 'nohistory') return true;

            var url = location.pathname.match(/(\/.*?\/.*?\/.*?\/).*/)[1] + '?';
            $(this).find(':input').each(function(idx, field){
                if ($(field).attr('name')) {
                    url += $(field).attr('name') + '=' + $(field).val() + '&';
                }
            });
            
            london.load_url(url, function(){
                apply_pagination_events();
                apply_search_events();
            });
            return false;
        }).data('search_submit',true);
    });
}

function apply_module_search() {
    if ($('#module-selector>input').data('has-event')) return;

    $('#module-selector>input').keyup(function(e){
        // Avoids filter again the same search string
        if ($(this).val() == $(this).data('previous-value')) return;
        $(this).data('previous-value', $(this).val());

        var q = $(this).val().toLowerCase();

        // Filtering
        $('#side-nav li.module-item').each(function(){
            if ($(this).text().toLowerCase().indexOf(q) >= 0) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });

    $('#module-selector>input').data('has-event', true);
}

