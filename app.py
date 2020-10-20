import os
import sqlite3
from flask import (
    Flask,
    render_template, request, redirect,
    url_for,
    session,  # MODIFY ME
    g,
)
from flask_wtf.csrf import CSRFProtect as CSRFMiddleware  # MODIFY ME
from flask_bcrypt import Bcrypt
from login_middleware import LoginMiddleware
from config import Config


app = Flask(
    __name__,
    instance_relative_config=True
)
app.config.from_object(Config)
bcrypt = Bcrypt()

csrf = CSRFMiddleware(app)
LoginMiddleware(app)


HTTP_400_BAD_REQUEST = 400

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
        db.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, generate_password_hash(password))
        )  
        db.commit()
        return True
    return False


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
    return "profile"


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

