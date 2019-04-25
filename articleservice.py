from flask import Flask, jsonify, request, Response, g
import sqlite3
from flask_api import status
import datetime
from http import HTTPStatus
from flask_httpauth import HTTPBasicAuth
from passlib.hash import sha256_crypt

app = Flask(__name__)

DATABASE = 'articledatabase.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.cursor().execute("PRAGMA foreign_keys = ON")
        db.commit()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        print("database closed")
        db.close()

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route("/postarticle", methods=['POST'])
def postarticle():
    if (request.method == 'POST'):
        try:
            db = get_db()
            c = db.cursor()
            details = request.get_json()
            email = request.authorization.username

            c.execute("insert into article (title, content, email, create_time, update_time) values (?,?,?,?,?)",
                        [details['title'], details['content'], email, datetime.datetime.now(), datetime.datetime.now() ])
            db.commit()
            c.execute("select article_id from article order by update_time desc limit 1")
            row = c.fetchone()
            response = Response(status=201, mimetype='application/json')
            path = "http://localhost/articles/"+str(row[0])
            c.execute("update article set url=(:path) where article_id=(:articleid)", {"path":path, "articleid":row[0]})
            db.commit()
            response.headers['location'] = path

        except sqlite3.Error as er:
                print(er)
                response = Response(status=409, mimetype='application/json')

        return response

@app.route("/articles/<id>", methods=['GET'])
def getarticle(id):
    if (request.method == 'GET'):
        try:
            db = get_db()
            db.row_factory = dict_factory
            c = db.cursor()

            c.execute("select article_id, title, content, email, create_time, update_time from article where article_id=(:articleid)",{'articleid':id})
            row = c.fetchone()
            if row is not None:
                return jsonify(row)
            else:
                response = Response(status=404, mimetype='application/json')

        except sqlite3.Error as er:
                print(er)
                response = Response(status=409, mimetype='application/json')

    return response


@app.route("/editarticle/<articleid>", methods=['PATCH'])
def editarticle(articleid):
    if (request.method == 'PATCH'):
        try:
            db = get_db()
            c = db.cursor()
            #id = request.args.get('articleid')
            email = request.authorization.username
            details = request.get_json()

            for x in details:
                sql = "update article set "+x+"=(:key), update_time=(:updatetime) where article_id=(:id) and email=(:email)"
                c.execute(sql, {"key":details[x],"updatetime":datetime.datetime.now(), "id":articleid, "email":email})
                if (c.rowcount == 1):
                    db.commit()
                    response = Response(status=200, mimetype='application/json')

                else:
                    response = Response(status=404, mimetype='application/json')

        except sqlite3.Error as er:
                print(er)
                response = Response(status=409, mimetype='application/json')

    return response



@app.route("/deletearticle/<articleid>", methods=['DELETE'])
def deletearticle(articleid):
    if (request.method == 'DELETE'):
        try:
            db = get_db()
            c = db.cursor()
            #id = request.args.get('articleid')
            email = request.authorization.username
            c.execute("delete from article where article_id=(:articleid) and email=(:email)",{"email":email,"articleid":articleid})
            db.commit()
            if (c.rowcount == 1):
                db.commit()
                response = Response(status=200, mimetype='application/json')
            else:
                response = Response(status=404, mimetype='application/json')
        except sqlite3.Error as er:
                print(er)
                response = Response(status=409, mimetype='application/json')

    return response

@app.route("/recentarticle/<recent>", methods=['GET'])
def recentarticle(recent):
    try:
        db = get_db()
        db.row_factory = dict_factory
        c = db.cursor()
        #recent = request.args.get('recent')
        c.execute("select * from article order by create_time desc limit (:recent)", {"recent":recent})
        recent_articles = c.fetchall()
        recent_articles_length = len(recent_articles)
        return jsonify(recent_articles)

        if(recent_articles_length == 0):
            response = Response(status=404, mimetype='application/json')

    except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response

@app.route("/metaarticle/<recent>", methods=['GET'])
def metaarticle(recent):
    try:
        db = get_db()
        db.row_factory = dict_factory
        c = db.cursor()
        #recent = request.args.get('recent')
        c.execute("select title, email, create_time, url, article_id from article order by create_time desc limit (:recent)", {"recent":recent})
        recent_articles = c.fetchall()
        recent_articles_length = len(recent_articles)
        return jsonify(recent_articles)

        if(recent_articles_length == 0):
            response = Response(status=404, mimetype='application/json')

    except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response



@app.route("/display", methods=['POST'])
def display():
    db = get_db()
    c = db.cursor()
    message = {}
    c.execute("select * from article")
    row = c.fetchall()

    return jsonify(row)



if __name__ == '__main__':
    app.run(debug=True)
