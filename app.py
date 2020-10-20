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


#
# User authenticate
#
bcrypt = Bcrypt()


def generate_password_hash(password):
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
    # register
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
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def get_profile(email):
    db = get_db()
    cursor = db.cursor()

    # query user
    cursor.execute("SELECT email, profile_id FROM users where email=? ", (email,))
    user_record = cursor.fetchone()
    if user_record is None:
        # No such user, error.
        return False

    email, profile_id = user_record
    if profile_id is None or profile_id == None:
        return {}

    # Get profile
    cursor.execute(
        "SELECT username, name, bio, interest, picture FROM profiles WHERE id=?",
        (profile_id,),
    )
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


def update_profile(email, username, name, bio, interest, picture=None):
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
        cursor.execute(
            "UPDATE profiles SET username=?,name=?,bio=?,interest=?,picture=? WHERE id=?",
            (username, name, bio, interest, picture, profile_id),
        )
        db.commit()
    return True

#
# Routes
#
@app.route("/")
def home():
    return render_template('index.html')


@app.route("/auth/login", methods=['GET','POST'])
def login():
    if request.method == "GET":
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
    if request.method == "GET":
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
    if request.method=='POST':
        session.pop('user', None)
        return redirect(url_for('home'))
    return render_template('logout.html')


@app.route("/user/profile", methods=['GET','POST'])
def profile():
    email = session['user']
    if request.method == "GET":
        profile = get_profile(email)
        return render_template("profile.html", profile=profile)
    elif request.method == "POST":
        file = request.files['picture']
        filepath = ''
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            file.save(filepath)
        update_ok = update_profile(
            email,
            request.values['username'],
            request.values['name'],
            request.values['bio'],
            request.values['interest'],
            os.path.basename(filepath),
        )
        if update_ok:
            return redirect(url_for('profile'))

    return "Bad request", HTTP_400_BAD_REQUEST


@app.route("/users", methods=['GET', 'POST'])
def list_users():
    db = get_db()
    cursor = db.cursor()
    users = cursor.execute("SELECT u.email FROM users AS u")
    # 將資料轉為 list
    column_name = [d[0] for d in users.description]
    user_list = [dict(zip(column_name, r)) for r in users.fetchall()]
    return render_template('users.html', users=user_list) 


#
# Main
#
if __name__ == "__main__":
    app.run()

