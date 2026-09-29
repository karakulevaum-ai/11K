$(document).ready(function () {

    // ---------- Регистрация ----------
    $('#register-form').on('submit', function (e) {
        e.preventDefault();
        const $msg = $('#msg');
        $msg.removeClass('error ok').text('');

        const name = $('#fullname').val().trim();
        const email = $('#email').val().trim();
        const password = $('#password').val();
        const confirm = $('#confirm_password').val();

        if (!name || !email || !password) {
            $msg.addClass('error').text('Заполните все поля');
            return;
        }
        if (password !== confirm) {
            $msg.addClass('error').text('Пароли не совпадают');
            return;
        }

        $.ajax({
            url: '/user_register',
            method: 'POST',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify({ name: name, email: email, password: password })
        })
        .done(function (resp) {
            if (resp.result) {
                $msg.addClass('ok').text('Регистрация прошла успешно! Сейчас перенаправим на вход...');
                setTimeout(function () { window.location.href = '/login'; }, 1200);
            } else {
                $msg.addClass('error').text(resp.message || 'Ошибка регистрации');
            }
        })
        .fail(function (xhr) {
            let text = 'Ошибка сервера';
            try {
                const r = JSON.parse(xhr.responseText);
                if (r.message) text = r.message;
            } catch (_) {}
            $msg.addClass('error').text(text);
        });
    });

    // ---------- Вход ----------
    $('#login-form').on('submit', function (e) {
        e.preventDefault();
        const $msg = $('#msg');
        $msg.removeClass('error ok').text('');

        const email = $('#email').val().trim();
        const password = $('#password').val();

        if (!email || !password) {
            $msg.addClass('error').text('Заполните все поля');
            return;
        }

        $.ajax({
            url: '/user_login',
            method: 'POST',
            contentType: 'application/json',
            dataType: 'json',
            data: JSON.stringify({ email: email, password: password })
        })
        .done(function (resp) {
            if (resp.status === 'ok') {
                $msg.addClass('ok').text('Успешный вход! Привет, ' + resp.user.username);
                // Здесь можно сохранить данные или перейти на главную:
                // window.location.href = '/dashboard';
            } else {
                $msg.addClass('error').text(resp.message || 'Ошибка входа');
            }
        })
        .fail(function (xhr) {
            let text = 'Ошибка сервера';
            try {
                const r = JSON.parse(xhr.responseText);
                if (r.message) text = r.message;
            } catch (_) {}
            $msg.addClass('error').text(text);
        });
    });

});