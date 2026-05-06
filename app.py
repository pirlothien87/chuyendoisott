import os
import sqlite3
from functools import wraps
from flask import Flask, g, redirect, render_template_string, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
DB_PATH = os.getenv("DB_PATH", "data/app.db")

LOGIN_TMPL = """
<!doctype html>
<html><body>
<h2>Login</h2>
{% if error %}<p style='color:red'>{{ error }}</p>{% endif %}
<form method="post">
  <label>Username</label><br>
  <input name="username" required><br><br>
  <label>Password</label><br>
  <input type="password" name="password" required><br><br>
  <button type="submit">Sign in</button>
</form>
</body></html>
"""

DASHBOARD_TMPL = """
<!doctype html>
<html><body>
<h2>Dashboard</h2>
<p>Xin chào, <b>{{ username }}</b> ({{ role }})</p>
<ul>
  <li>Trang này dành cho admin sau khi đăng nhập.</li>
  <li>Dùng làm nền để phát triển tiếp theo BA spec.</li>
</ul>
<p><a href="{{ url_for('logout') }}">Logout</a></p>
</body></html>
"""


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """
    )
    default_user = os.getenv("DEFAULT_ADMIN_USERNAME", "superadmin")
    default_pass = os.getenv("DEFAULT_ADMIN_PASSWORD", "SuperAdmin@123")
    role = "super_admin"

    row = db.execute("SELECT id FROM users WHERE username = ?", (default_user,)).fetchone()
    if not row:
        db.execute(
            "INSERT INTO users(username, password_hash, role) VALUES(?,?,?)",
            (default_user, generate_password_hash(default_pass), role),
        )
    db.commit()
    db.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


@app.route("/", methods=["GET"])
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        error = "Sai tài khoản hoặc mật khẩu"
    return render_template_string(LOGIN_TMPL, error=error)


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return render_template_string(
        DASHBOARD_TMPL,
        username=session.get("username"),
        role=session.get("role"),
    )


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
