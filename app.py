import os
from functools import wraps
from flask import Flask, abort, g, redirect, render_template_string, request, session, url_for
import pymysql
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "app_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "app_password")
DB_NAME = os.getenv("DB_NAME", "trial_management")

ROLES = ("admin", "accountant", "am", "ctv", "viewer")

LOGIN_TMPL = """
<!doctype html><html><body>
<h2>Đăng nhập hệ thống</h2>
{% if error %}<p style='color:red'>{{ error }}</p>{% endif %}
<form method="post">
  <label>Email</label><br>
  <input type="email" name="email" required><br><br>
  <label>Mật khẩu</label><br>
  <input type="password" name="password" required><br><br>
  <button type="submit">Đăng nhập</button>
</form>
</body></html>
"""

DASHBOARD_TMPL = """
<!doctype html><html><body>
<h2>Dashboard</h2>
<p>Xin chào <b>{{ user['name'] }}</b> ({{ user['role'] }})</p>
<ul>
  <li><a href="{{ url_for('my_tasks') }}">Danh sách task theo phân quyền</a></li>
  {% if user['role'] == 'admin' %}
    <li><a href="{{ url_for('manage_users') }}">Quản lý user</a></li>
  {% endif %}
</ul>
<p><a href="{{ url_for('logout') }}">Logout</a></p>
</body></html>
"""


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    return g.db


@app.teardown_appcontext
def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def exec_sql(sql, params=None, fetch=False, many=False):
    with get_db().cursor() as cursor:
        if many:
            cursor.executemany(sql, params)
        else:
            cursor.execute(sql, params or ())
        if fetch:
            return cursor.fetchall()
    return None


def init_db():
    db = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, autocommit=True)
    with db.cursor() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          name VARCHAR(255) NOT NULL,
          email VARCHAR(255) NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL,
          role ENUM('admin', 'accountant', 'am', 'ctv', 'viewer') NOT NULL,
          status ENUM('active', 'inactive', 'pending') DEFAULT 'active',
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS provinces (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          name VARCHAR(255) NOT NULL UNIQUE,
          status ENUM('active', 'inactive') DEFAULT 'active'
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS user_provinces (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          user_id BIGINT NOT NULL,
          province_id BIGINT NOT NULL,
          UNIQUE KEY unique_user_province (user_id, province_id),
          FOREIGN KEY (user_id) REFERENCES users(id),
          FOREIGN KEY (province_id) REFERENCES provinces(id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          title VARCHAR(255) NOT NULL,
          province_id BIGINT NOT NULL,
          manager_am_id BIGINT NOT NULL,
          assigned_to_user_id BIGINT,
          status ENUM('draft','assigned','in_progress','waiting_review','need_update','completed','cancelled') DEFAULT 'draft',
          due_date DATE,
          FOREIGN KEY (province_id) REFERENCES provinces(id),
          FOREIGN KEY (manager_am_id) REFERENCES users(id),
          FOREIGN KEY (assigned_to_user_id) REFERENCES users(id)
        )
        """)

        defaults = [
            ("Super Admin", os.getenv("DEFAULT_ADMIN_EMAIL", "superadmin@example.com"), generate_password_hash(os.getenv("DEFAULT_ADMIN_PASSWORD", "SuperAdmin@123")), "admin"),
            ("Kế toán Demo", "accountant@example.com", generate_password_hash("Accountant@123"), "accountant"),
            ("AM Demo", "am@example.com", generate_password_hash("Am@123456"), "am"),
            ("CTV Demo", "ctv@example.com", generate_password_hash("Ctv@123456"), "ctv"),
        ]
        for name, email, password_hash, role in defaults:
            c.execute("SELECT id FROM users WHERE email=%s", (email,))
            if not c.fetchone():
                c.execute(
                    "INSERT INTO users(name,email,password_hash,role,status) VALUES(%s,%s,%s,%s,'active')",
                    (name, email, password_hash, role),
                )
        c.execute("INSERT IGNORE INTO provinces(name,status) VALUES ('Hà Nam','active'), ('Nam Định','active'), ('Thái Bình','active')")
    db.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def visible_tasks(user_id, role):
    if role == "admin":
        return exec_sql("SELECT t.id, t.title, t.status, p.name as province FROM tasks t JOIN provinces p ON p.id=t.province_id ORDER BY t.id DESC", fetch=True)
    if role == "am":
        return exec_sql(
            """
            SELECT t.id, t.title, t.status, p.name as province
            FROM tasks t
            JOIN provinces p ON p.id=t.province_id
            JOIN user_provinces up ON up.province_id=t.province_id
            WHERE up.user_id=%s
            ORDER BY t.id DESC
            """,
            (user_id,),
            fetch=True,
        )
    if role == "ctv":
        return exec_sql(
            "SELECT t.id, t.title, t.status, p.name as province FROM tasks t JOIN provinces p ON p.id=t.province_id WHERE t.assigned_to_user_id=%s ORDER BY t.id DESC",
            (user_id,),
            fetch=True,
        )
    return []


@app.route("/")
def home():
    return redirect(url_for("dashboard")) if "user_id" in session else redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        users = exec_sql("SELECT * FROM users WHERE email=%s AND status='active'", (email,), fetch=True)
        user = users[0] if users else None
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        error = "Sai email hoặc mật khẩu"
    return render_template_string(LOGIN_TMPL, error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template_string(DASHBOARD_TMPL, user={"name": session.get("name"), "role": session.get("role")})


@app.route("/tasks")
@login_required
def my_tasks():
    rows = visible_tasks(session["user_id"], session["role"])
    html = "<h2>Danh sách task theo phân quyền</h2><ul>" + "".join([f"<li>#{r['id']} - {r['title']} ({r['province']}) [{r['status']}]</li>" for r in rows]) + "</ul><p><a href='/dashboard'>Back</a></p>"
    return html


@app.route("/admin/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def manage_users():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "").strip()
        password = request.form.get("password", "")
        if name and email and role in ROLES and password:
            exec_sql(
                "INSERT INTO users(name,email,password_hash,role,status) VALUES(%s,%s,%s,%s,'active')",
                (name, email, generate_password_hash(password), role),
            )
    users = exec_sql("SELECT id,name,email,role,status FROM users ORDER BY id DESC", fetch=True)
    form = """
    <h2>Quản lý user</h2>
    <form method='post'>
      <input name='name' placeholder='Họ tên' required>
      <input name='email' type='email' placeholder='Email' required>
      <input name='password' type='password' placeholder='Password' required>
      <select name='role'>""" + "".join([f"<option value='{r}'>{r}</option>" for r in ROLES]) + "</select><button>Tạo user</button></form><hr>"
    table = "<ul>" + "".join([f"<li>{u['name']} - {u['email']} ({u['role']})</li>" for u in users]) + "</ul><p><a href='/dashboard'>Back</a></p>"
    return form + table


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
