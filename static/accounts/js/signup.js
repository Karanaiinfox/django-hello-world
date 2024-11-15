function submitSignup() {
    const formData = {
        username: $('#username').val(),
        email: $('#email').val(),
        password: $('#password').val(),
        password_confirm: $('#password_confirm').val()
    };

    $.ajax({
        type: 'POST',
        url: window.location.href,
        data: formData,
        success: function(response) {
            $('#message').text(response.success);
            window.location.href = '/accounts/login/';
        },
        error: function(response) {
            $('#message').text(response.responseJSON.error);
        }
    });
}
