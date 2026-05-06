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

# templates omitted brevity in analysis; include styled
LOGIN_TMPL="""<!doctype html><html><head><style>body{margin:0;font-family:Arial;background:linear-gradient(135deg,#eef2ff,#f0fdfa)}.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center}.card{background:#fff;padding:28px;border-radius:16px;box-shadow:0 15px 45px rgba(2,6,23,.12);width:380px}input,button{width:100%;padding:10px;border-radius:10px;margin-bottom:10px;border:1px solid #cbd5e1}button{background:#2563eb;color:#fff;border:none}</style></head><body><div class='wrap'><div class='card'><h2>Đăng nhập</h2>{% if error %}<div style='color:#b91c1c'>{{ error }}</div>{% endif %}<form method='post'><input name='email' type='email' placeholder='Email' required><input name='password' type='password' placeholder='Mật khẩu' required><button>Đăng nhập</button></form></div></div></body></html>"""
DASHBOARD_TMPL="""<!doctype html><html><head><style>body{font-family:Arial;background:#f8fafc;margin:0}.top{background:#0f172a;color:#fff;padding:12px 16px}.container{max-width:980px;margin:20px auto;padding:0 16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:14px}.btn{display:inline-block;background:#2563eb;color:#fff;padding:8px 10px;border-radius:8px;text-decoration:none}</style></head><body><div class='top'>Trial Progress | <a style='color:#93c5fd' href='{{ url_for("logout") }}'>Logout</a></div><div class='container'><h2>Xin chào {{ user['name'] }} ({{ user['role'] }})</h2><div class='grid'>{% if user['role'] in ('admin','accountant') %}<div class='card'><h3>Hợp đồng</h3><a class='btn' href='{{ url_for("contracts") }}'>Mở</a></div>{% endif %}{% if user['role'] != 'accountant' %}<div class='card'><h3>Task</h3><a class='btn' href='{{ url_for("my_tasks") }}'>Mở</a></div>{% endif %}{% if user['role']=='admin' %}<div class='card'><h3>User</h3><a class='btn' href='{{ url_for("manage_users") }}'>Mở</a></div>{% endif %}</div></div></body></html>"""
TASKS_TMPL="""<!doctype html><html><body style='font-family:Arial;background:#f1f5f9;margin:0'><div style='max-width:900px;margin:20px auto;padding:0 16px'><h2>Task theo phân quyền</h2>{% for r in rows %}<div style='background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px;margin-bottom:8px'><b>#{{ r.id }} {{ r.title }}</b><div>{{ r.province }} - {{ r.status }}</div></div>{% else %}<div>Không có task.</div>{% endfor %}<a href='{{ url_for("dashboard") }}'>Quay lại</a></div></body></html>"""


def get_db():
    if "db" not in g:
        g.db = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, cursorclass=pymysql.cursors.DictCursor, autocommit=True)
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    db = g.pop("db", None)
    if db is not None: db.close()

def exec_sql(sql, params=None, fetch=False):
    with get_db().cursor() as c:
        c.execute(sql, params or ())
        if fetch: return c.fetchall()

def init_db():
    db = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, autocommit=True)
    with db.cursor() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY AUTO_INCREMENT,name VARCHAR(255) NOT NULL,email VARCHAR(255) NOT NULL UNIQUE,password_hash VARCHAR(255) NOT NULL,role ENUM('admin','accountant','am','ctv','viewer') NOT NULL,status ENUM('active','inactive','pending') DEFAULT 'active')""")
        c.execute("""CREATE TABLE IF NOT EXISTS provinces (id BIGINT PRIMARY KEY AUTO_INCREMENT,name VARCHAR(255) UNIQUE,status ENUM('active','inactive') DEFAULT 'active')""")
        c.execute("""CREATE TABLE IF NOT EXISTS user_provinces (id BIGINT PRIMARY KEY AUTO_INCREMENT,user_id BIGINT NOT NULL,province_id BIGINT NOT NULL,UNIQUE KEY unique_user_province (user_id,province_id),FOREIGN KEY (user_id) REFERENCES users(id),FOREIGN KEY (province_id) REFERENCES provinces(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS tasks (id BIGINT PRIMARY KEY AUTO_INCREMENT,title VARCHAR(255) NOT NULL,province_id BIGINT NOT NULL,manager_am_id BIGINT NOT NULL,assigned_to_user_id BIGINT,status ENUM('draft','assigned','in_progress','waiting_review','need_update','completed','cancelled') DEFAULT 'draft',FOREIGN KEY (province_id) REFERENCES provinces(id),FOREIGN KEY (manager_am_id) REFERENCES users(id),FOREIGN KEY (assigned_to_user_id) REFERENCES users(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS contracts (id BIGINT PRIMARY KEY AUTO_INCREMENT,company_name VARCHAR(255) NOT NULL,contract_code VARCHAR(100) NOT NULL UNIQUE,drug_name VARCHAR(255),crop VARCHAR(255),start_date DATE,end_date DATE,status ENUM('draft','active','in_progress','completed','cancelled') DEFAULT 'draft',created_by BIGINT,FOREIGN KEY (created_by) REFERENCES users(id))""")
        for name,email,pwd,role in [("Super Admin",os.getenv("DEFAULT_ADMIN_EMAIL","superadmin@example.com"),generate_password_hash(os.getenv("DEFAULT_ADMIN_PASSWORD","SuperAdmin@123")),"admin"),("Kế toán Demo","accountant@example.com",generate_password_hash("Accountant@123"),"accountant"),("AM Demo","am@example.com",generate_password_hash("Am@123456"),"am"),("CTV Demo","ctv@example.com",generate_password_hash("Ctv@123456"),"ctv")]:
            c.execute("SELECT id FROM users WHERE email=%s",(email,))
            if not c.fetchone(): c.execute("INSERT INTO users(name,email,password_hash,role,status) VALUES(%s,%s,%s,%s,'active')",(name,email,pwd,role))
        c.execute("INSERT IGNORE INTO provinces(name,status) VALUES ('Hà Nam','active'),('Nam Định','active'),('Thái Bình','active')")
    db.close()

def login_required(fn):
    @wraps(fn)
    def w(*a,**k):
        if "user_id" not in session: return redirect(url_for("login"))
        return fn(*a,**k)
    return w

def role_required(*roles):
    def d(fn):
        @wraps(fn)
        def w(*a,**k):
            if session.get("role") not in roles: abort(403)
            return fn(*a,**k)
        return w
    return d

def visible_tasks(uid, role):
    if role=="admin": return exec_sql("SELECT t.id,t.title,t.status,p.name province FROM tasks t JOIN provinces p ON p.id=t.province_id ORDER BY t.id DESC",fetch=True)
    if role=="am": return exec_sql("SELECT t.id,t.title,t.status,p.name province FROM tasks t JOIN provinces p ON p.id=t.province_id JOIN user_provinces up ON up.province_id=t.province_id WHERE up.user_id=%s ORDER BY t.id DESC",(uid,),True)
    if role=="ctv": return exec_sql("SELECT t.id,t.title,t.status,p.name province FROM tasks t JOIN provinces p ON p.id=t.province_id WHERE t.assigned_to_user_id=%s ORDER BY t.id DESC",(uid,),True)
    return []

@app.route('/')
def home(): return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    err=None
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        users=exec_sql("SELECT * FROM users WHERE email=%s AND status='active'",(email,),True); user=users[0] if users else None
        if user and check_password_hash(user['password_hash'],password):
            session['user_id']=user['id']; session['name']=user['name']; session['role']=user['role']; return redirect(url_for('dashboard'))
        err='Sai email hoặc mật khẩu'
    return render_template_string(LOGIN_TMPL,error=err)

@app.route('/dashboard')
@login_required
def dashboard(): return render_template_string(DASHBOARD_TMPL,user={'name':session.get('name'),'role':session.get('role')})

@app.route('/contracts',methods=['GET','POST'])
@login_required
@role_required('admin','accountant')
def contracts():
    if request.method=='POST':
        company=request.form.get('company_name','').strip(); code=request.form.get('contract_code','').strip().upper()
        if company and code and not exec_sql("SELECT id FROM contracts WHERE contract_code=%s",(code,),True):
            exec_sql("INSERT INTO contracts(company_name,contract_code,drug_name,crop,start_date,end_date,status,created_by) VALUES(%s,%s,%s,%s,%s,%s,'draft',%s)",(company,code,request.form.get('drug_name','').strip(),request.form.get('crop','').strip(),request.form.get('start_date') or None,request.form.get('end_date') or None,session.get('user_id')))
    items=exec_sql("SELECT id,company_name,contract_code,status FROM contracts ORDER BY id DESC",fetch=True)
    return render_template_string("""<html><body style='font-family:Arial;background:#f8fafc'><div style='max-width:980px;margin:20px auto'><h2>Quản lý hợp đồng</h2><form method='post' style='display:grid;grid-template-columns:repeat(3,1fr);gap:8px'><input name='company_name' placeholder='Tên công ty' required><input name='contract_code' placeholder='Mã hợp đồng' required><input name='drug_name' placeholder='Tên thuốc'><input name='crop' placeholder='Cây trồng'><input name='start_date' type='date'><input name='end_date' type='date'><button style='background:#2563eb;color:#fff'>Tạo hợp đồng</button></form><hr>{% for c in items %}<div><b>{{ c.contract_code }}</b> - {{ c.company_name }} [{{ c.status }}]</div>{% else %}<div>Chưa có hợp đồng</div>{% endfor %}<p><a href='{{ url_for("dashboard") }}'>Back</a></p></div></body></html>""",items=items)

@app.route('/tasks')
@login_required
def my_tasks():
    if session.get('role')=='accountant': abort(403)
    return render_template_string(TASKS_TMPL,rows=visible_tasks(session['user_id'],session['role']))

@app.route('/admin/users',methods=['GET','POST'])
@login_required
@role_required('admin')
def manage_users():
    action=request.form.get('action','create')
    if request.method=='POST' and action=='create':
        n=request.form.get('name','').strip(); e=request.form.get('email','').strip().lower(); r=request.form.get('role','').strip(); p=request.form.get('password','')
        if n and e and r in ROLES and p and not exec_sql("SELECT id FROM users WHERE email=%s",(e,),True): exec_sql("INSERT INTO users(name,email,password_hash,role,status) VALUES(%s,%s,%s,%s,'active')",(n,e,generate_password_hash(p),r))
    if request.method=='POST' and action=='update':
        uid=request.form.get('user_id',''); r=request.form.get('role',''); st=request.form.get('status','')
        if uid.isdigit() and r in ROLES and st in ('active','inactive','pending') and int(uid)!=int(session['user_id']): exec_sql("UPDATE users SET role=%s,status=%s WHERE id=%s",(r,st,int(uid)))
    users=exec_sql("SELECT id,name,email,role,status FROM users ORDER BY id DESC",fetch=True)
    return render_template_string("""<html><body style='font-family:Arial;background:#f8fafc'><div style='max-width:1000px;margin:20px auto'><h2>Quản lý user (Admin)</h2><form method='post'><input type='hidden' name='action' value='create'><input name='name' placeholder='Họ tên' required><input name='email' type='email' placeholder='Email' required><input name='password' type='password' placeholder='Password' required><select name='role'>{% for r in roles %}<option value='{{ r }}'>{{ r }}</option>{% endfor %}</select><button>Tạo user</button></form><hr>{% for u in users %}<form method='post' style='margin-bottom:8px'><input type='hidden' name='action' value='update'><input type='hidden' name='user_id' value='{{ u.id }}'><b>#{{ u.id }} {{ u.name }}</b> {{ u.email }} <select name='role'>{% for r in roles %}<option value='{{ r }}' {% if r==u.role %}selected{% endif %}>{{ r }}</option>{% endfor %}</select><select name='status'>{% for st in statuses %}<option value='{{ st }}' {% if st==u.status %}selected{% endif %}>{{ st }}</option>{% endfor %}</select><button {% if u.id==current_user_id %}disabled{% endif %}>Cập nhật</button></form>{% endfor %}<p><a href='{{ url_for("dashboard") }}'>Back</a></p></div></body></html>""",users=users,roles=ROLES,statuses=('active','inactive','pending'),current_user_id=session.get('user_id'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__=='__main__':
    init_db(); app.run(host='0.0.0.0',port=int(os.getenv('PORT','8000')))
