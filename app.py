import os
from flask import (
    Flask,
    render_template, session, request, redirect,
    url_for,
)
from flask_wtf.csrf import CSRFProtect as CSRFMiddleware  # MODIFY ME

from config import Config


app = Flask(
    __name__,
    instance_relative_config=True
)
app.config.from_object(Config)

csrf = CSRFMiddleware(app)


HTTP_400_BAD_REQUEST = 400


def authenticate(email, password):
    """Authenticate"""
    # TODO: Implement authenticate
    return True


def register(email, password):
    """Register"""
    # TODO: Implement register
    pass


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


@app.route("/user/profile", methods=['GET','POST'])
def profile():
    return "profile"


@app.route("/auth/logout", methods=['GET','POST'])
def logout():
    return "logout"


if __name__ == "__main__":
    app.run()

