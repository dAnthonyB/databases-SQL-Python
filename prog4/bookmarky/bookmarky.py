import flask
from bookmarky import users, bookmarks
from bookmarky.dbutil import db_connect
from contextlib import closing

app = flask.Flask(__name__)
app.config.from_pyfile('settings.py')

#how to make dump file
#pg_dump -h postgresql.cs.txstate.edu -U netid \
#    --clean --no-acl --no-owner \
#    cs4332sm3 >project-dump.sql
#
#to get dump
#psql -h postgresql.cs.txstate.edu -U netid cs4332sm3 <project-dump.sql
@app.route('/')
def hello_world():
    if 'auth_user' in flask.session:
        # we have a user
        with db_connect(app) as dbc:
            uid = flask.session['auth_user']
            user = users.get_user(dbc, uid)
            if user is None:
                app.logger.error('invalid user %d', uid)
                flask.abort(400)

            user_marks = bookmarks.get_for_user(dbc, uid)
            return flask.render_template('home.html', user=user,
                                         bookmarks=user_marks)
    else:
        return flask.render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    username = flask.request.form['user']
    password = flask.request.form['passwd']
    if username is None or password is None:
        flask.abort(400)
    action = flask.request.form['action']
    if action == 'Log in':
        with closing(db_connect(app)) as dbc:
            uid = users.check_auth(dbc, username, password)
            if uid is not None:
                flask.session['auth_user'] = uid
                return flask.redirect('/', code=303)
            else:
                flask.abort(403)
    elif action == 'Create account':
        with closing(db_connect(app)) as dbc:
            uid = users.create_user(dbc, username, password)
            flask.session['auth_user'] = uid
            return flask.redirect('/', code=303)


@app.route('/add', methods=['GET', 'POST'])
def add_bookmark():
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        return flask.render_template('new-bookmark.html')
    else:
        with closing(db_connect(app)) as dbc:
            bookmarks.add_bookmark(dbc, uid, flask.request.form)
        return flask.redirect('/', code=303)

@app.route('/edit/<int:bid>', methods=['GET', 'POST'])
def edit_bookmark(bid):
    if 'auth_user' in flask.session:
        uid = flask.session['auth_user']
    else:
        flask.abort(403)

    if flask.request.method == 'GET':
        with closing(db_connect(app)) as dbc:
            bookmark = bookmarks.get_bookmark(dbc, bid, uid)
        return flask.render_template('edit-bookmark.html',
                                     bookmark=bookmark)
    else:
        with closing(db_connect(app)) as dbc:
            bookmarks.update_bookmark(dbc, uid, bid, flask.request.form)
        return flask.redirect('/', code=303)


if __name__ == '__main__':
    app.run()
