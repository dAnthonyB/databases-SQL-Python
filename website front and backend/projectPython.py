import os.path
import flask
import psycopg2
from contextlib import contextmanager
from contextlib import closing
app = flask.Flask(__name__)
app.config.from_pyfile('settings.py')
if os.path.exists('localsettings.py'):
    app.config.from_pyfile('localsettings.py')

def db_connect():

    """
    Create a database connection.
    :param app: The Flask application.
    :return: The database connection
    """
    # Get the database connection from the configuration
    cxn = psycopg2.connect(**app.config['PG_ARGS'])
    #
    cxn.autocommit = False
    return cxn

@contextmanager
def db_cursor():
    # Get the database connection from the configuration
    dbc = psycopg2.connect(**app.config['PG_ARGS'])
    try:
        cur = dbc.cursor()
        try:
            yield cur
        finally:
            cur.close()
    finally:
        dbc.close()

@app.route('/')
def default_page():
    #homepage that has links to:
    # 'Login' /login
    # 'Browse Bugs' /browse/status/all
    # 'Milestones' /milestone
    # 'Register' /reg
    # also has text search box that takes them to /search/text
    return flask.render_template('default.html')

@app.route('/home/<int:user_id>')
def home_page(user_id):
#homepage that has links to:
    # 'Browse Bugs' /browse/status/all
    # 'Browse Your Bugs' /user_browse/user_id/assigned/all
    # 'Milestones' /milestone
    # 'Your Profile' /user/<user_id>
    # 'Create New Bug' /newBug/<user_id>
    # 'Edit a Bug' /editBug/<user_id>
    # 'Newsfeed' /newsfeed/<user_id>
    # also has text search box that takes them to /search/text
    return flask.render_template('home.html', user_id = user_id)

@app.route('/reg', methods=['GET', 'POST'])
def registration():
    with closing(db_connect()) as dbc:
        with dbc:
            with dbc.cursor() as cur:
                # HTML form grabs username, display_name, password, email, role
                if flask.request.method == 'POST':
                    # adds new user; needs to check for unique username/display_name/email
                    username = flask.request.form['username']
                    display_name = flask.request.form['display_name']
                    pw_hash = flask.request.form['pw_hash']
                    email = flask.request.form['email']
                    role = flask.request.form['role']
                    cur.execute('''
                        INSERT INTO "user"(user_id, username, display_name, pw_hash, email, role)
                          VALUES (DEFAULT, %s, %s, %s, %s, %s);
                    ''', (username, display_name, pw_hash, email, role))

    return flask.render_template('reg.html')

@app.route('/login')
def login():
    with closing(db_connect()) as dbc:
        with dbc:
            with dbc.cursor() as cur:
                # user enters username and password and we store into username and password variables
                if flask.request.method == 'POST':
                    username = flask.request.form["user"]
                    pw_hash = flask.request.form["passwd"]

                    cur.execute('''
                        SELECT user_id, pw_hash
                        FROM 'user'
                        WHERE username = %s
                          AND pw_hash = %s
                    ''', (username, pw_hash))
                    row = cur.fetchone()
                    if row is None:
                        flask.abort(404)
                    user_id, pw_hash = row
    return flask.render_template('login.html', user_id, pw_hash)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
# This page should display the user's username, display_name, email, and role
# Then has a list of assigned bug's titles as links to the bug's page
    with db_cursor() as cur:
        #gets info for user object
        cur.execute('''
            SELECT username, display_name, email, role
            FROM "user"
            WHERE user_id = %s; --id of "user" whose profile is being generated
        ''', (user_id,))
        row = cur.fetchone()
        if row is None:
            flask.abort(404)
        username, display_name, email, role = row
        user = {'username': username, 'display_name': display_name, 'email': email,
                'role': role}

        # gets ids and titles of assigned bugs
        cur.execute('''
            SELECT bug_id, bug_title
            FROM bug
            JOIN user_assigned_bug USING (bug_id)
            WHERE user_id = %s --id of "user" whose profile is being generated
            ORDER BY creation_date;
        ''', (user_id,))
        bugs = []
        for id, title in cur:
            bugs.append({'id': id, 'title': title})

    return flask.render_template('userProfile.html', user=user, bugs = bugs)

@app.route('/bug/<int:bug_id>/')
def bug(bug_id):
    with db_cursor() as cur:
        cur.execute('''
            SELECT bug_id, bug_title, display_name AS creator, to_char(creation_date, 'Mon-DD-YYYY'), status, bug_details,
            close_date, user_id
            FROM bug
            JOIN "user" ON (creator_id = user_id)
            WHERE bug_id = %s;
        ''', (bug_id,))
        row = cur.fetchone()
        if row is None:
            flask.abort(404)
        id, title, creator, date, status, details, close_date, user_id = row
        bug = {'id': id, 'title': title, 'creator': creator, 'date': date, 'details': details, 'status': status,
               'close_date': close_date, 'user_id': user_id}

    return flask.render_template('singleBug.html', bug = bug)

@app.route('/bug/<int:bug_id>/<int:user_id>/')
def bug_page(bug_id, user_id):
# displays bug_title, creator (linked to profile), creation date, bug_details, status, and close_date for a bug
# then displays the link to the comments page (/bug/bug_id/comments/user_id/)
# has a subscribe and unsubscribe link
    with db_cursor() as cur:
        #bug info
        cur.execute('''
            SELECT bug_title, display_name AS creator, to_char(creation_date, 'Mon-DD-YYYY'),
                   bug_details, status, close_date
            FROM bug
            JOIN "user" ON (creator_id = user_id)
            WHERE bug_id = %s;
        ''', (bug_id,))
        row = cur.fetchone()
        if row is None:
            flask.abort(404)
        title, creator, date, details, status, close_date = row
        bug = {'title': title, 'creator': creator, 'date': date,
               'details': details, 'status': status, 'close_date': close_date}

    return flask.render_template('bug.html', bug=bug, user_id=user_id, bug_id=bug_id)

@app.route('/bug/<int:bug_id>/comments/<int:user_id>')
def bug_comments(bug_id, user_id):
# displays bug's comments ordered by date
# mentions are hyperlinks to the user that is mentioned profile
# if user is logged in, has 'leave comment' link that takes user to /bug/bug_id/comments/new/user_id
    with db_cursor() as cur:
        #bug comments
        cur.execute('''
            SELECT author_id, comment_text, to_char(comment_date, 'Mon-DD-YYYY')
            FROM bug
            JOIN comment USING (bug_id)
            WHERE bug_id = %s
            ORDER BY comment_date;
        ''', (bug_id,))
        comments = []
        for aid, comment_text, comment_date in cur:
            comments.append({'aid': aid, 'comment_text':comment_text, 'comment_date':comment_date})

    return flask.render_template('bug_comments.html', comments=comments, bug_id=bug_id, user_id=user_id)

@app.route('/bug/<int:bug_id>/comments/new/<int:user_id>', methods=['GET','POST'])
def new_comment(bug_id, user_id):
#user can make a comment on a bug
    with closing(db_connect()) as dbc:
        with dbc:
            with dbc.cursor() as cur:
                if flask.request.method == 'POST':
                    comment_text = flask.request.form["comment"]

                    #add comment
                    cur.execute('''
                        INSERT INTO comment (comment_id, author_id, bug_id, comment_text, comment_date)
                          VALUES(              DEFAULT,    %s,        %s,        %s,        DEFAULT);
                    ''', (user_id, bug_id, comment_text,))

    return flask.render_template('new_comment.html', bug_id=bug_id, user_id=user_id)

@app.route('/bug/<int:bug_id>/<int:user_id>/<string:subscribed>')
def subscribe_Page(bug_id, user_id, subscribed):
#if they subscribe or unsubscribe,
#   display text saying that it did.
    with closing(db_connect()) as dbc:
        with dbc:
            with dbc.cursor() as cur:
                if subscribed == 'subscribe':
                    #subscribe
                    cur.execute('''
                        INSERT INTO user_sub_bug (user_id, bug_id)
                          VALUES (%s, %s);
                    ''', (user_id, bug_id,))

                elif subscribed == 'unsubscribe':
                    #unsubscribe
                    cur.execute('''
                            DELETE FROM user_sub_bug
                            WHERE user_id = %s --current user
                              AND bug_id = %s; --current bug
                        ''', (user_id, bug_id,))
    return flask.render_template('subscribe.html', subscribed=subscribed, user_id=user_id, bug_id=bug_id)

@app.route('/milestone')
def milestoneList():
# lists all milestone names as links to their pages with their description next to them
    with db_cursor() as cur:
        # milestone info
        cur.execute('''
            SELECT milestone_id, milestone_name, milestone_description
            FROM milestone
            ORDER BY milestone_id;
        ''')
        milestones = []
        for id, name, description in cur:
                milestones.append({'id': id, 'name': name,
                'description': description})

    return flask.render_template('milestone.html', milestones=milestones)

@app.route('/milestone/<int:milestone_id>')
def milestone(milestone_id):
#page lists the milestone's name, description, and closed %
#Then lists all the bugs titles (as links to their page) and their status
    with db_cursor() as cur:
        #milestone info
        cur.execute('''
            SELECT milestone_name, milestone_description
            FROM milestone
            WHERE milestone_id = %s;
        ''', (milestone_id,))
        row = cur.fetchone()
        if row is None:
            flask.abort(404)
        name, description = row
        milestone = {'name': name, 'description': description}

        #milestone bugs and progress
        cur.execute('''
                SELECT bug_id, bug_title, status
                FROM bug
                JOIN bug_milestone USING (bug_id)
                WHERE milestone_id = %s
                ORDER BY creation_date;
        ''', (milestone_id,))
        bugs = []
        numClosed = 0
        totalBugs = 0
        for id, title, status in cur:
            if status == 'closed':
                numClosed += 1
            bugs.append({'id': id, 'title': title,'status': status})
            totalBugs += 1

        milestone['progress'] = (numClosed/totalBugs)*100

    return flask.render_template('milestones.html', milestone = milestone, bugs=bugs)

@app.route('/browse/<string:browse>/<string:filter>/')
def browse(browse, filter):
# Users can browse bugs by status, tag, assignee, or creator.
    with db_cursor() as cur:

        if browse == 'status':
            if filter == 'all':
                cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    ORDER BY creation_date;
                ''')
            else:
                cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    WHERE status = %s --=open||closed
                    ORDER BY creation_date;
            ''', (filter,))

        elif browse == 'tag':
            cur.execute('''
                SELECT bug_id, bug_title, tag_name
                FROM bug
                JOIN tag USING (bug_id)
                WHERE tag_name = %s --=tag to look for
                ORDER BY creation_date;
            ''', (filter,))

        elif browse == 'assignee':
            cur.execute('''
                SELECT bug_id, bug_title, display_name AS assignee
                FROM bug
                JOIN user_assigned_bug USING (bug_id)
                JOIN "user" USING (user_id)
                WHERE display_name = %s --=assignee to look for
                ORDER BY creation_date;
            ''', (filter,))

        elif browse == 'creator':
            cur.execute('''
                SELECT bug_id, bug_title, display_name AS creator
                FROM bug
                JOIN "user" ON (user_id=creator_id)
                WHERE display_name = %s --=creator to look for
                ORDER BY creation_date;
            ''', (filter,))
        else: # meaning browse != one of the keywords
            #default page
            cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    ORDER BY creation_date;
                ''')

        bugs = []
        for id, title, filter in cur:
            bugs.append({'id': id, 'title': title, 'filter': filter})

    return flask.render_template('browse.html', bugs = bugs)


@app.route('/user_browse/<int:user_id>/<string:browse>/<string:status>/')
def user_browse(user_id, browse, status):
# Users can easily browse the bugs that they created, and the bugs that are assigned to them;
# they should be able to see open bugs, closed bugs, or all bugs.
    with db_cursor() as cur:
        if browse == 'assigned':
            if status == 'all':
                cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    JOIN user_assigned_bug USING(bug_id)
                    JOIN "user" USING(user_id)
                    WHERE user_id = %s --=current user
                    ORDER BY creation_date;
                ''', (user_id,))
            else:
                cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    JOIN user_assigned_bug USING(bug_id)
                    JOIN "user" USING (user_id)
                    WHERE user_id = %s --=current user
                      AND status = %s --=open||closed
                    ORDER BY creation_date;
                ''', (user_id, status,))
        elif browse == 'created':
            if status == 'all':
                cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    JOIN "user" ON (creator_id = user_id)
                    WHERE user_id = %s --=current user
                    ORDER BY creation_date;
                ''', (user_id,))
            else:
                cur.execute('''
                    SELECT bug_id, bug_title, status
                    FROM bug
                    JOIN "user" ON (creator_id = user_id)
                    WHERE user_id = %s --=current user
                      AND status = %s --=open||closed
                    ORDER BY creation_date;
                ''', (user_id, status,))

        bugs = []
        for id, title, status in cur:
            bugs.append({'id': id, 'title': title, 'status': status})

    return flask.render_template('user_browse.html', bugs = bugs, user_id=user_id)

@app.route('/search/<string:text>')
def search(text):
# Users can search for bugs with text strings.
    with db_cursor() as cur:
        # not sure if it's the right code
        cur.execute('''
                    SELECT bug_id, bug_title
                    FROM bug
                    WHERE bug_title LIKE %s
                    OR    bug_details LIKE %s
                    ORDER BY creation_date;
        ''', (text, text,))

        bugs = []
        for id, title in cur:
            bugs.append({'id': id, 'title': title})

    return flask.render_template('search.html', bugs = bugs)

@app.route('/newbug/<int:user_id>', methods=['GET','POST'])
def createBug(user_id):
    with closing(db_connect()) as dbc:
        with dbc:
            with dbc.cursor() as cur:
                # HTML form grabs new bug's title and details
                if flask.request.method == 'POST':
                    bug_title = flask.request.form["Title"]
                    details = flask.request.form["Details"]
                    # Creates new bug from user entered info
                    cur.execute('''
                        INSERT INTO bug (bug_id, bug_title, creator_id, creation_date, bug_details, status)
                                  VALUES(DEFAULT, %s,        %s,         DEFAULT,         %s,       DEFAULT)
                                  RETURNING bug_id;
                    ''', (bug_title, user_id, details,))

                    #subscribes the bug
                    bug_id = cur.fetchone()
                    cur.execute('''
                                INSERT INTO user_sub_bug (user_id, bug_id)
                                      VALUES (             %s,      %s);
                        ''', (user_id, bug_id,))

    return flask.render_template('newbug.html', user_id=user_id)

@app.route('/newsfeed/user/<int:user_id>/<int:limit>')
def newsfeed(user_id, limit):
# lists subscribed content by 'change' dates
    with db_cursor() as cur:
        if limit is None:
            limit=50
        #query to get all the content in the correct order
        cur.execute('''
            SELECT bug_title AS content, creation_date AS sub_date, 'Subscribed to'
            FROM bug
            JOIN user_sub_bug USING (bug_id)
            JOIN "user" USING(user_id)
            WHERE user_id = %s
            UNION--joins a tables so that we can order them by date properly
            --Bug comments for subscribed bugs
            SELECT comment_text AS content, comment_date AS sub_date, 'Bug comments'
            FROM comment
            JOIN bug USING (bug_id)
            JOIN user_sub_bug USING (bug_id)
            JOIN "user" USING(user_id)
            WHERE user_id = %s
            UNION
            --Bugs users are subscribed and assigned to
            SELECT bug_title AS content, assign_date AS sub_date, 'Assigned to'
            FROM bug
            JOIN user_sub_bug USING (bug_id)
            JOIN user_assigned_bug USING (user_id)
            WHERE user_id = %s
            UNION
            --Comments users are mentioned in
            SELECT comment_text AS content, comment_date AS sub_date, 'Mentioned in'
            FROM comment
            JOIN mention USING (comment_id)
            JOIN "user" USING (user_id)
            WHERE user_id = %s --user getting newsfeed
            ORDER BY sub_date DESC
            LIMIT %s; --=number to show per page
        ''', (user_id, user_id, user_id, user_id, limit,))
        subscriptions = []
        for content, sub_date, description in cur:
               subscriptions.append({'content': content, 'sub_date': sub_date, 'description': description})

    return flask.render_template('newsfeed.html', subscriptions=subscriptions, user_id=user_id)
if __name__ == '__main__':
    app.run()
