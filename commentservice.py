from flask import Flask, jsonify, request,Response, g
import sqlite3
from flask_api import status
import datetime
from http import HTTPStatus
from flask_httpauth import HTTPBasicAuth
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
auth = HTTPBasicAuth()

DATABASE1 = 'commentdatabase.db'
DATABASE2 = 'articledatabase.db'


def get_db1():
    db = getattr(g, '_database1', None)
    if db is None:
        db = g._database1 = sqlite3.connect(DATABASE1)
        db.cursor().execute("PRAGMA foreign_keys = ON")
        db.commit()
    return db

def get_db2():
    db = getattr(g, '_database2', None)
    if db is None:
        db = g._database2 = sqlite3.connect(DATABASE2)
        db.cursor().execute("PRAGMA foreign_keys = ON")
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database1', None)
    if db is not None:
        print("database 1 closed")
        db.close()
    db = getattr(g, '_database2', None)
    if db is not None:
        print("database 2 closed")
        db.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route("/addcomment/<articleid>", methods=['POST'])
def addcomment(articleid):
    if (request.method == 'POST'):
        try:
            db1 = get_db1()
            c1 = db1.cursor()
            db2 = get_db2()
            c2 = db2.cursor()

            details = request.get_json()
            email = request.authorization.username
            update_time = datetime.datetime.now()

            print("before")
            c2.execute("select article_id from article where article_id=(:articleid)",{"articleid":articleid})
            row = c2.fetchone()
            #sprint(row)
            #row_length = len(row)
            #print(row_length)
            if not row:
                response = Response(status=404, mimetype='application/json')
            else:
                c1.execute("insert into comment (comment_content, email, article_id, create_time, update_time) values (?,?,?,?,?)",
                                    [details['comment_content'], email, articleid, datetime.datetime.now(),datetime.datetime.now()])
                db1.commit()

                c1.execute("select comment_id from comment order by update_time desc limit 1")
                row = c1.fetchone()
                response = Response(status=201, mimetype='application/json')
                response.headers['location'] = 'http://localhost/articles/comments'+str(row[0])

        except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response

@app.route("/articles/comments/countcomment/<articleid>", methods=['GET'])
def countcomment(articleid):
    try:
        db = get_db1()
        c = db.cursor()

        c.execute("select count(*) from comment where article_id=(:articleid)",{"articleid":articleid})
        count_comments = c.fetchall()
        count_comments_length = len(count_comments)
        return jsonify(count_comments)
        if(count_comments_length == 0):
            response = Response(status=404, mimetype='application/json')

    except sqlite3.Error as er:
            print(er)

    return response

@app.route("/deletecomment/<commentid>", methods=['DELETE'])
def deletecomment(commentid):
    try:
        db = get_db1()
        c = db.cursor()
        #commentid = request.args.get('commentid')
        email = request.authorization.username

        c.execute("delete from comment where (email=(:email) and comment_id=(:commentid))", {"email":email,"commentid":commentid})
        if (c.rowcount == 1):
            db.commit()
            response = Response(status=200, mimetype='application/json')
        else:
            response = Response(status=404, mimetype='application/json')
    except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')
    return response

@app.route("/articles/comments/recentcomments/<articleid>/<recent>", methods=['GET'])
def recentcomments(articleid,recent):
    try:
        db = get_db1()
        db.row_factory = dict_factory
        c = db.cursor()
        #recent = request.args.get('recent')

        c.execute("select comment_content from comment where article_id=(:articleid) order by update_time desc limit (:recent)", {"articleid":articleid, "recent":recent})
        recent_comments = c.fetchall()
        recent_comments_length = len(recent_comments)
        print(recent_comments_length)
        if(recent_comments_length == 0):
            response = Response(status=404, mimetype='application/json')
            return response
        return jsonify(recent_comments)

    except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response

if __name__ == '__main__':
    app.run(debug=True)
