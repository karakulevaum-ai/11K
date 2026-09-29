import os
import hmac
import hashlib
import mysql.connector
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": "185.114.247.43",
    "port": 3306,
    "database": "sch688_vvedenie",
    "user": "sch688_vvedenie",
    "password": "Qwerty123",
}

ITERATIONS = 100_000
SALT_LEN = 16
HASH_LEN = 32


def hash_password(password: str) -> str:
    """<salt_hex><hash_hex> — без разделителей."""
    salt = os.urandom(SALT_LEN)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, dklen=HASH_LEN)
    return salt.hex() + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    if not stored or len(stored) < SALT_LEN * 2:
        return False
    try:
        salt = bytes.fromhex(stored[:SALT_LEN * 2])
        expected_bytes = bytes.fromhex(stored[SALT_LEN * 2:])
    except (ValueError, TypeError):
        return False

    if len(expected_bytes) != HASH_LEN:
        return False

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, dklen=HASH_LEN)
    # сравниваем в постоянном времени
    return hmac.compare_digest(dk, expected_bytes)


# ---------- Регистрация ----------
@app.route('/user_register', methods=['POST'])
def user_register():
    req = request.get_json(silent=True) or {}
    name = (req.get('name') or '').strip()
    email = (req.get('email') or '').strip().lower()
    password = req.get('password') or ''

    if not name or not email or not password:
        return jsonify({"result": False, "message": "Заполните все поля"}), 400

    cnx = mysql.connector.connect(**DB_CONFIG)
    cur = cnx.cursor(dictionary=True)
    try:
        # Проверка, что такой email уже не занят
        cur.execute('SELECT id FROM `users` WHERE `email` = %s', (email,))
        if cur.fetchone() is not None:
            return jsonify({"result": False, "message": "Пользователь с таким email уже существует"}), 409

        password_hash = hash_password(password)

        cur.execute(
            'INSERT INTO `users`(`username`, `email`, `password_hash`) VALUES (%s, %s, %s)',
            (name, email, password_hash)
        )
        cnx.commit()
        new_id = cur.lastrowid  # берём ДО закрытия курсора
        return jsonify({"result": True, "id": new_id}), 200
    except mysql.connector.Error as e:
        cnx.rollback()
        return jsonify({"result": False, "message": f"Ошибка БД: {e}"}), 500
    finally:
        cur.close()
        cnx.close()


# ---------- Вход ----------
@app.route('/user_login', methods=['POST'])
def user_login():
    req = request.get_json(silent=True) or {}
    email = (req.get('email') or '').strip().lower()
    password = req.get('password') or ''

    if not email or not password:
        return jsonify({"status": "error", "message": "Заполните все поля"}), 400

    cnx = mysql.connector.connect(**DB_CONFIG)
    cur = cnx.cursor(dictionary=True)
    try:
        cur.execute(
            'SELECT id, username, email, password_hash FROM `users` WHERE `email` = %s',
            (email,)
        )
        user = cur.fetchone()
    finally:
        cur.close()
        cnx.close()

    if user is None:
        return jsonify({"status": "error", "message": "Пользователь не найден"}), 404

    if not verify_password(password, user['password_hash']):
        return jsonify({"status": "error", "message": "Неверный пароль"}), 401

    return jsonify({
        "status": "ok",
        "message": "Успешный вход",
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]}
    }), 200


@app.route("/")
def registration():
    return render_template('registration.html')


@app.route("/login")
def login():
    return render_template('login.html')


if __name__ == "__main__":
    app.run(debug=True)