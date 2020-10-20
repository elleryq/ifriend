import os
from flask import Flask, render_template


app = Flask(__name__)

DEBUG = os.environ.get('FLASK_DEBUG', "False").lower() == "true"


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/auth/login")
def login():
    return "Login"


@app.route("/auth/signup")
def signup():
    return "Signup"


@app.route("/user/profile")
def profile():
    return "profile"


@app.route("/auth/logout")
def logout():
    return "logout"


if __name__ == "__main__":
    app.run(debug=DEBUG)
