import flask
import psycopg2
import sys


def add_bookmark(dbc, uid, form):
    with dbc, dbc.cursor() as cur:
        url = form['url'].strip()
        title = form['title'].strip()
        notes = form['notes'].strip()
        if not title:
            title = None
        if not notes:
            notes = None
        cur.execute('''
            INSERT INTO bookmark
              (owner_id, url, title, notes)
            VALUES (%s, %s, %s, %s)
            RETURNING bookmark_id
        ''', (uid, url, title, notes))
        bid = cur.fetchone()[0]

        tags = form['tags'].split(',')
        for tag in tags:
            cur.execute('''
                INSERT INTO bm_tag (bookmark_id, tag) VALUES (%s, %s)
            ''', (bid, tag.strip().lower()))


def update_bookmark(dbc, uid, bid, form):
    ntries = 1
    while ntries < 5:
        try:
            with dbc:
                with dbc.cursor() as cur:
                    cur.execute('''
                      SELECT bookmark_id FROM bookmark
                      WHERE owner_id = %s AND bookmark_id = %s
                    ''', (uid, bid))
                    row = cur.fetchone()
                    if row is None:
                        flask.abort(403)

                    url = form['url'].strip()
                    title = form['title'].strip()
                    notes = form['notes'].strip()
                    if not title:
                        title = None
                    if not notes:
                        notes = None
                    cur.execute('''
                        UPDATE bookmark
                        SET url = %s, title = %s, notes = %s
                        WHERE bookmark_id = %s
                    ''', (url, title, notes, bid))

                    cur.execute('''
                        SELECT tag FROM bm_tag WHERE bookmark_id = %s
                    ''', (bid,))
                    old_tags = []
                    for tag, in cur:
                        old_tags.append(tag)
                    tags = [t.strip().lower() for t in form['tags'].split(',')]
                    for tag in tags:
                        if tag not in old_tags:
                            cur.execute('''
                              INSERT INTO bm_tag (bookmark_id, tag) VALUES (%s, %s)
                            ''', (bid, tag))

                    for tag in old_tags:
                        if tag not in tags:
                            cur.execute('''
                              DELETE FROM bm_tag
                              WHERE bookmark_id = %s AND tag = %s
                            ''', (bid, tag))
                return
        except psycopg2.DatabaseError as dbe:
            print("commit error: {}".format(dbe), file=sys.stderr)
            dbc.rollback()
            ntries += 1

    flask.abort(500)

def get_for_user(dbc, uid):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT bookmark_id, tag
            FROM bookmark JOIN bm_tag USING (bookmark_id)
            WHERE owner_id = %s
        ''', (uid,))
        tag_map = {}
        for bid, tag in cur:
            if bid in tag_map:
                tag_map[bid].append(tag)
            else:
                tag_map[bid] = [tag]

        cur.execute('''
            SELECT bookmark_id, url, COALESCE(title, url),
             notes, create_time
            FROM bookmark
            WHERE owner_id = %s
            ORDER BY create_time DESC
        ''', (uid,))
        marks = []
        for id, url, title, notes, time in cur:
            marks.append({'id': id, 'url': url, 'title': title,
                          'notes': notes, 'create_time': time,
                          'tags': tag_map.get(id, [])})
        return marks


def get_bookmark(dbc, bid, uid):
    with dbc, dbc.cursor() as cur:
        cur.execute('''
            SELECT url, title, notes
            FROM bookmark
            WHERE bookmark_id = %s AND owner_id = %s
        ''', (bid, uid))
        row = cur.fetchone()
        if row is None:
            return None

        url, title, notes = row
        bookmark = {'id': bid, 'url': url, 'title': title,
                    'notes': notes, 'tags': []}
        cur.execute('''
            SELECT tag FROM bm_tag WHERE bookmark_id = %s
        ''', (bid,))
        for tag, in cur:
            bookmark['tags'].append(tag)

        return bookmark
