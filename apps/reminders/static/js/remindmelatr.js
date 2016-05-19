$(document).ready(function() {

    // Focus on text input on load
    $('.basic-reminder-form #id_remind_on').focus();

    // Allow for ctrl+enter in content textarea
    $('.basic-reminder-form #id_content, .basic-reminder-form #id_remind_on, .basic-reminder-form #id_remind_at').keypress(function(e) {
        if ((e.charCode == 10) && (e.ctrlKey)) {
            $(this).parents('form').submit();
        }
    });

    // Center the text in a textarea
    // if there is not text in it
    if ($('.basic-reminder-form #id_content').val() != '') {
        $('.basic-reminder-form #id_content').css('text-align', 'left');
    }
    $('.basic-reminder-form #id_content').focus(function() {
        $(this).css('text-align', 'left');
    }).focusout(function() {
        if ($(this).val() == '') {
            $(this).css('text-align', 'center');
        }
    });

    // The 'on' field autocompletes
    $('#id_remind_on').typeahead({
        source: function(query, process) {
            $.ajax({
                url: '/app/on_options/',
                data: {
                    query: query
                },
                success: function(response) {
                    return process(response);
                }
            });
        }
    })

    // The 'at' field autocompletes
    $('#id_remind_at').typeahead({
        source: function(query, process) {
            $.ajax({
                url: '/app/at_options/',
                data: {
                    query: query
                },
                success: function(response) {
                    return process(response);
                }
            });
        }
    })

});
