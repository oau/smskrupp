# -*- coding: utf-8 -*-

import sqlite3
from flask import Flask,render_template,request,session,flash,redirect, \
        url_for,abort, g

from config import config
import core


# create our little application :)
app = Flask(__name__)

# TODO: change these lines before production!
app.debug = config.debug
app.secret_key = config.flask_key

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


@app.route('/groups/', methods=['POST', 'GET'])
@app.route('/groups/<name>', methods=['POST', 'GET'])
def groups(name=None):
    if not session.get('logged_in'):
        abort(401)

    data = core.Data()
    error = None

    if request.method == 'POST':
        if name:
            # add member
            number = core.normalize_number(request.form['number'])
            if number:
                group_id = data.get_group_id(name)
                if group_id:
                    mid = data.add_number(number, request.form['alias'], group_id)
                    if 'admin' in request.form:
                        data.set_member_info(mid, sender=True, admin=True)
                    elif 'sender' in request.form:
                        data.set_member_info(mid, sender=True)
                else:
                    error = "group error!"
            else:
                error = "number error!"
        else:
            # add group
            gid = data.add_group(request.form['name'], request.form['keyword'],
                    config.default_phone)
            data.set_webuser_group(session.get('userid'), gid)
            return redirect(url_for('groups')+request.form['name'])

    members = None
    if not session.get('admin'):
        groups = data.get_webuser_groups(session.get('userid'))
    else:
        groups = data.get_groups()

    if name:
        gid = data.get_group_id(name)
        if not gid:
            abort(404)
        if not (session.get('admin') or gid in [g['id'] for g in data.get_webuser_groups(session.get('userid'))]):
            abort(401)

        members = data.get_group_members(gid)

    return render_template('group.html', name=name, members=members, groups=groups, error=error)

@app.route('/removemember/<mid>') 
def remove_member(mid=None):
    data = core.Data()
    info = data.get_member_info(mid)
    if not info:
        abort(404)

    gids = [g['id'] for g in data.get_webuser_groups(session.get('userid'))]
    if not session.get('admin') and info['groupId'] not in gids:
        abort(401)

    data.remove_number(mid)
    return redirect(url_for('groups', name=info['groupName']))

@app.route('/removegroup/<name>') 
def remove_group(name):
    data = core.Data()
    gid = data.get_group_id(name)

    gids = [g.id for g in data.get_webuser_groups(session.get('userid'))]
    if not session.get('admin') and gid not in gids:
        abort(401)

    if data.get_group_members(gid):
        redirect(url_for('groups', name=name))

    data.remove_group(gid)
    return redirect(url_for('groups'))

@app.route("/settings", methods=['POST','GET'])
def settings():
    if not session.get('admin'):
        abort(401)

    data = core.Data()
    if request.method == 'POST':
        if 'group' in request.form:
            data.set_webuser_group(request.form['userid'], request.form['group'])
        elif 'username' in request.form:
            p = 2 if 'admin' in request.form else 1
            data.add_webuser(request.form['username'], request.form['pw'], p)
        elif 'pw' in request.form:
            data.set_webuser_pw(request.form['userid'], request.form['pw'])

    groups = data.get_groups()
    return render_template('settings.html', webusers=data.get_webusers(),groups=groups)

@app.route('/removewebusergroup/<uid>/<gid>') 
def remove_webuser_group(uid,gid):
    if not session.get('admin'):
        abort(401)

    data = core.Data()

    data.remove_webuser_group(uid,gid)
    return redirect(url_for('settings'))

@app.route('/removewebuser/<uid>') 
def remove_webuser(uid):
    if not session.get('admin'):
        abort(401)

    data = core.Data()
    data.remove_webuser(uid)
    return redirect(url_for('settings'))

@app.route("/")
@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        data = core.Data()
        userid,privilege = data.check_webuser_login(request.form['username'],
                       request.form['password'])
        if privilege:
            session['username'] = request.form['username']
            session['userid'] = userid
            session['logged_in'] = True
            session['admin'] = privilege > 1
            flash('You were logged in')
            return redirect(url_for('groups'))
        else:
            error = 'Invalid username/password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('userid', None)
    session.pop('logged_in', None)
    session.pop('admin', None)
    flash('You were logged out')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()

