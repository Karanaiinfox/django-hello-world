function submitLogin() {
    const formData = {
        username: $('#username').val(),
        password: $('#password').val()
    };

    $.ajax({
        type: 'POST',
        url: window.location.href,
        data: formData,
        success: function(response) {
            $('#message').text(response.success);
            window.location.href = '/';
        },
        error: function(response) {
            $('#message').text(response.responseJSON.error);
        }
    });
}
