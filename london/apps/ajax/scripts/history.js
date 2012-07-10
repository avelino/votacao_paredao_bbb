(function(window, undefined){

    History = window.history;

    LondonFuncs.prototype.load_url = function(url, callback) {
        var this_london = this;
        var get_response = function(resp){
            // Cleans context variables references
            for (var k in this_london.context_vars){ this_london.context_vars[k] = null; }
            this_london.context_vars = {};

            this_london.load_response(resp, callback);
        };
        $.get(url, get_response);

        get_response = null;
    }

    LondonFuncs.prototype.createScript = function(el) {
        if(el.nodeName !== 'SCRIPT') {
            return null;
        }
        var script = $(el),
            scriptText = script.text(),
            src = script.attr('src'),
            scriptNode = document.createElement('script');

        scriptNode.type = 'text/javascript';
        if(src) {
            scriptNode.src = src;
        } else if (scriptText) {
            // TODO: review this hack
            if(scriptText.indexOf('window.location') >= 0) {
                // the first <script> element tries to reload the current url!
                // we need to avoid it, otherwise we get stuck in a loop
                return null;
            }
            scriptNode.appendChild(document.createTextNode(scriptText));
        }
        return scriptNode;
    }

    LondonFuncs.prototype.load_response = function(resp, callback) {
        var xml = $('<div>'+resp+'</div>');

        if (xml.find('redirect').length) {
            var url = xml.find('redirect').attr('url');

            // If nohistory is given, loads in window via standard way
            if (xml.find('redirect').attr('rel') == 'nohistory') {
                window.location = url;
            } else {
                //this.load_url(url);
                History.pushState(null, null, url);
                $(window).trigger('popstate');
            }
        } else {
            xml.find('base').remove();
            xml.find('piece').each(function(){
                var container = $('*[container='+$(this).attr('name')+']');
                if (container.attr('container_param')) {
                    container.attr(container.attr('container_param'), $(this).text());
                } else {
                    // Unbind all the events binded to the elements inside -- this avoid memory leaks with circular references
                    container.find('*').unbind();
                    container.empty();
                    container.html($(this).html());
                }
            });

            // jquery puts the scripts in xml as separated items
            xml.each(function(i,el) {
                var scriptNode = london.createScript(el);
                scriptNode && $('body').append(scriptNode);
            });

            london.apply_history_events();

            $('body').trigger('london_ready');
        }

        if (callback) callback();
    }

    LondonFuncs.prototype.apply_history_events = function() {
        // Click event for links to load URLs by history control
        $('a[href^="/"][rel!="nohistory"], a[href^="?"][rel!="nohistory"], a[rel="forcehistory"]').each(function(){
            if (!$(this).data('has-click-event')) {
                $(this).data('has-click-event', true).click(function(e){
                    //london.load_url($(this).attr('href'));
                    History.pushState(null, null, $(this).attr('href'));
                    $(window).trigger('popstate');
                    e.preventDefault();
                });
            }
        });
    }

    $(document).ready(function(){
        london.apply_history_events();

        // Event to load when history is changed (back or forward)
        var first_time = true;
        var previous_url = location.pathname+location.search;
        var popstate_load = function(e) {
            if (!first_time || previous_url != location.pathname+location.search) {
                london.load_url(location.pathname+location.search);
                previous_url = location.pathname+location.search;
            }
            first_time = false;
        }
        $(window).bind("popstate", popstate_load);
        popstate_load = null;

        $('body').trigger('london_ready');
        
        //Browsers tend to handle the popstate event differently on page load. Chrome and Safari always emit a popstate event on 
        //page load, but Firefox and Opera don't
        if (navigator.appVersion.indexOf('AppleWebKit') <= 0) {
            $(window).trigger('popstate');
        }
    });

})(window);

