$(document).ready(function() {
    $('#start-button').click(function() {
        $('#start-button').prop('disabled', true);
        $('#progress-bar').show();
        $('#result').hide();
        
        $.ajax({
            url: '/trigger',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(response) {
                let thread_id = response.thread_id;
                let progressInterval = setInterval(function() {
                    $.get('/status/' + thread_id, function(data) {
                        if (data.status === 'completed') {
                            clearInterval(progressInterval);
                            $('#progress-percent').text('100%');
                            $('#result').show();
                            $('#result-data').text(JSON.stringify(data.result, null, 2));
                            $('#result-graph').attr('src', data.graph_image);
                            $('#progress-bar').hide();
                            $('#start-button').prop('disabled', false);
                        } else {
                            let progress = Math.min(100, parseInt($('#progress-percent').text()) + 20);
                            $('#progress-percent').text(progress + '%');
                        }
                    });
                }, 1000);
            }
        });
    });
});
