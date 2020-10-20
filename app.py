import os
import sqlite3
from flask import (
    Flask,
    render_template, request, redirect,
    url_for,
    session,  # MODIFY ME
    g,
)
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware
from flask_wtf.csrf import CSRFProtect as CSRFMiddleware  # MODIFY ME
from flask_bcrypt import Bcrypt
from login_middleware import LoginMiddleware
from config import Config
from xss import XssFilter


app = Flask(
    __name__,
    instance_relative_config=True
)
app.config.from_object(Config)

csrf = CSRFMiddleware(app)
LoginMiddleware(app)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/media':  app.config['UPLOAD_FOLDER']
})

HTTP_400_BAD_REQUEST = 400
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
xssFilter = XssFilter()


#
# Database
#
DATABASE = "db.sqlite3"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        # Enable foreign key check
        db.execute("PRAGMA foreign_keys = ON")
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


class NotFoundException(Exception):
    pass


#
# User authentication
#

bcrypt = Bcrypt()


def generate_password_hash(password):
    """產生密碼雜湊"""
    return bcrypt.generate_password_hash(password)


def authenticate(email, password):
    """Authenticate"""
    # authenticate
    db = get_db()
    cursor = db.cursor()
    # query user
    cursor.execute("SELECT email, password FROM users where email=? ", (email,))
    record = cursor.fetchone()
    if record is None:
        return False

    email, stored_password = record
    if not bcrypt.check_password_hash(stored_password, password):
        return False

    return True


def register(email, password):
    """Register"""
    # registe
    db = get_db()
    cursor = db.cursor()
    # query user
    cursor.execute("SELECT email FROM users where email=? ", (email,))
    if cursor.fetchone() is None:
        # add user
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, generate_password_hash(password))
        )
        db.commit()
        return True
    return False


def allowed_file(filename):
    """檢查副檔名是否允許"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_profile(email):
    """依指定 email 取得 profile"""
    db = get_db()
    cursor = db.cursor()

    # query user
    cursor.execute("SELECT id, email, profile_id FROM users where email=? ", (email,))
    db.commit()
    user_record = cursor.fetchone()
    if user_record is None:
        # No such user, error.
        return False

    user_id, email, profile_id = user_record
    if profile_id is None or profile_id == None:
        return {}

    # Get profile
    cursor.execute(
        "SELECT username, name, bio, interest, picture FROM profiles WHERE id=?",
        (profile_id,),
    )
    db.commit()
    profile_record = cursor.fetchone()
    if profile_record is None:
        return {}
    username, name, bio, interest, picture = profile_record

    return {
        'username': username,
        'name': name,
        'bio': bio,
        'interest': interest,
        'picture': picture,
    }


def get_user_id_by_email(email):
    """依據 email 取得 user id"""
    db = get_db()
    cursor = db.cursor()

    # query user
    cursor.execute("SELECT id FROM users where email=? ", (email,))
    db.commit()
    user_record = cursor.fetchone()
    if user_record is None:
        raise NotFoundException('No such user.')
    return user_record[0]


def get_visitor_list(email):
    """取得訪客清單"""
    db = get_db()
    cursor = db.cursor()

    # query user
    user_id = get_user_id_by_email(email)

    # Get who visit my profile
    visitors = cursor.execute(
        "SELECT u.email FROM visited as v, users as u WHERE v.self=? AND v.self=u.id",
        (user_id,)
    )
    db.commit()
    column_name = [d[0] for d in visitors.description]
    visitor_list = [dict(zip(column_name, r)) for r in visitors.fetchall()]
    return visitor_list


def update_profile(email, username, name, bio, interest, picture=None):
    """更新 profile"""
    db = get_db()
    cursor = db.cursor()

    # query user
    cursor.execute("SELECT email, profile_id FROM users where email=? ", (email,))
    user_record = cursor.fetchone()
    if user_record is None:
        # No such user, error.
        return False

    email, profile_id = user_record
    if profile_id is None:
        # add profile
        cursor.execute(
            "INSERT INTO profiles (username, name, bio, interest, picture) VALUES (?, ?, ?, ?, ?)",
            (username, name, bio, interest, picture)
        )
        db.commit()
        profile_id = cursor.lastrowid
        cursor.execute(
            "UPDATE users SET profile_id = ? WHERE email=?",
            (profile_id, email)
        )
        db.commit()
    else:
        # Update profile
        if picture:
            sql = "UPDATE profiles SET username=?,name=?,bio=?,interest=?,picture=? WHERE id=?"
            values = (username, name, bio, interest, picture, profile_id)
        else:
            sql = "UPDATE profiles SET username=?,name=?,bio=?,interest=? WHERE id=?"
            values = (username, name, bio, interest, profile_id)
        cursor.execute(
            sql,
            values,
        )
        db.commit()
    return True


def record_visitor(target_email, visitor_email):
    """
    紀錄來察看的使用者

    Args:
      - target_email: 受訪者的 email
      - visitor_email: 訪客的 email
    """
    if target_email == visitor_email:
        return

    # query user
    target_id = get_user_id_by_email(target_email)

    # query user
    visitor_id = get_user_id_by_email(visitor_email)

    db = get_db()
    cursor = db.cursor()

    # 檢查是否已經紀錄過了
    cursor.execute(
        "SELECT COUNT(*) FROM visited WHERE self=? AND visitor=?",
        (target_id, visitor_id, ),
    )
    db.commit()
    result=cursor.fetchone()
    number_of_rows = result[0]
    if number_of_rows > 0:
        return

    # record
    cursor.execute(
        "INSERT INTO visited (self, visitor) VALUES (?, ?)",
        (target_id, visitor_id, ),
    )
    db.commit()

#
# Endpoints
#

@app.route("/")
def home():
    """首頁"""
    return render_template('index.html')


@app.route("/auth/login", methods=['GET','POST'])
def login():
    """登入"""
    if request.method == "GET":
        # 顯示登入表單
        return render_template("login.html")
    elif request.method == "POST":
        # do authenticate.
        email = request.values['email']
        password = request.values['password']
        if not authenticate(email, password):
            return render_template("login.html")
        session['user'] = email
        return redirect(url_for('home'))

    return "Bad request", HTTP_400_BAD_REQUEST


@app.route("/auth/signup", methods=['GET','POST'])
def signup():
    """註冊"""
    if request.method == "GET":
        # 顯示註冊表單
        return render_template("signup.html")
    elif request.method == "POST":
        # do register.
        email = request.values['email']
        password = request.values['password']
        password2 = request.values['password2']
        if password != password2:
            return render_template("signup.html")
        register(email, password)
        return redirect(url_for('home'))

    return "Bad request", HTTP_400_BAD_REQUEST


@app.route("/auth/logout", methods=['GET','POST'])
def logout():
    """登出"""
    if request.method=='POST':
        session.pop('user', None)
        return redirect(url_for('home'))
    return render_template('logout.html')


@app.route("/user/profile", methods=['GET','POST'])
def profile():
    """顯示登入使用者的 profile"""
    email = session['user']
    if not email:
        return redirect(url_for('login'))

    if request.method == "GET":
        # 顯示 profile 表單
        profile = get_profile(email)
        visitor_list = get_visitor_list(email)
        return render_template(
            "profile.html",
            profile=profile,
            visitor_list=visitor_list
        )
    elif request.method == "POST":
        # 更新 profile
        # 先處理照片
        file = request.files['picture']
        filepath = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            file.save(filepath)
            filepath = os.path.basename(filepath)

        # 再更新 profile
        update_ok = update_profile(
            email,
            xssFilter.strip(request.values['username']),
            xssFilter.strip(request.values['name']),
            xssFilter.strip(request.values['bio']),
            xssFilter.strip(request.values['interest']),
            filepath,
        )
        if update_ok:
            return redirect(url_for('profile'))
        else:
            # TODO: 更新發生錯誤的處理
            pass

    return "Bad request", HTTP_400_BAD_REQUEST


@app.route("/user/profileByEmail", methods=['GET'])
def profileByEmail():
    """依指定 email 顯示該使用者的 profile"""
    current_user_email = session['user']
    if not current_user_email:
        return redirect(url_for('login'))

    email = request.args.get('email')
    if request.method == "GET":
        visitor_email = session['user']
        target_email = email
        profile = get_profile(email)
        record_visitor(target_email, visitor_email)
        return render_template("profile_by_email.html", profile=profile)

    return "Bad request", HTTP_400_BAD_REQUEST


@app.route("/users", methods=['GET', 'POST'])
def list_users():
    """列出所有使用者"""
    current_user_email = session['user']
    if not current_user_email:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    users = cursor.execute("SELECT u.email FROM users AS u")
    db.commit()
    # 將資料轉為 list
    column_name = [d[0] for d in users.description]
    user_list = [dict(zip(column_name, r)) for r in users.fetchall()]
    return render_template('users.html', user_list=user_list)


#
# Main
#
if __name__ == "__main__":
    app.run()

