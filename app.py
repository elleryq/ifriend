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
    return True


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/auth/login", methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        # do authenticate.
        pass
        email = request.values['email']
        password = request.values['password']
        if not authenticate(email, password):
            return render_template("login.html")
        return redirect(url_for('home'))

    return "Bad request", HTTP_400_BAD_REQUEST


@app.route("/auth/signup", methods=['GET','POST'])
def signup():
    return "Signup"


@app.route("/user/profile", methods=['GET','POST'])
def profile():
    return "profile"


@app.route("/auth/logout", methods=['GET','POST'])
def logout():
    return "logout"


if __name__ == "__main__":
    app.run()

