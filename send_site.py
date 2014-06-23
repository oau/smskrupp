# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, g
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
import bcrypt
import sqlite3
import subprocess

import core
from config import config

app = Flask(__name__)
app.secret_key = config.flask_key
app.debug = config.debug

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


def connect_db():
    """Returns a new connection to the database."""
    return sqlite3.connect(config.db)


@app.before_request
def before_request():
    """Make sure we are connected to the database each request."""
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'db'):
        g.db.close()


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    data = core.Data()
    lists = data.get_webuser_groups(current_user.id)
    if request.method == 'POST' and 'text' in request.form and 'list' in request.form:
        list, text = request.form['list'], request.form['text']
        kw = None
        for l in lists:
            if list == l['name']:
                kw = l['keyword']
                break
        else:
            flash("Invalid list")

        if kw:
            data.fake_incoming(core.DUMMY_NUMBER, config.default_phone, "#" + kw + " " + text)
            p = subprocess.Popen(["./onreceive.py"])
            flash("Message will be sent")

    return render_template('send.html', **locals())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'pw' in request.form:
        username, pw = request.form['username'], request.form['pw']
        id = check_user(username, pw)
        if id:
            user = load_user(id)
            if user and login_user(user):
                flash("Logged in!")
                return redirect(url_for('index'))
        flash("Unable to log in")
    return render_template('sendlogin.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


####################
# helper functions #
####################


@login_manager.user_loader
def load_user(id):
    data = core.Data()
    u = data.get_webuser_from_id(id)
    if u:
        return User(u['username'], u['id'])
    return None


def user_exists(username):
    data = core.Data()
    u = data.get_webuser(username)
    return True if u else False


def check_user(username, pw):
    data = core.Data()
    u = data.get_webuser(username)
    if u:
        if bcrypt.hashpw(pw, u['hash']) == u['hash']:
            return u['id']
    return None


# def make_user(username, pw):
#     user, = graph_db.create({
#         'id': str(uuid.uuid4()), 'username': username,
#         'password_hash': generate_password_hash(pw), 'enabled': True})
#     user.add_labels('User')


class User:
    def __init__(self, username, id):
        self.username = username
        self.id = id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.username)


if __name__ == "__main__":
    app.run(host=config.send_site_host, port=config.send_site_port)
