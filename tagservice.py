from flask import Flask, jsonify, request, Response, g
import sqlite3, json
from flask_api import status
import datetime
from http import HTTPStatus
from flask_httpauth import HTTPBasicAuth
from passlib.hash import sha256_crypt

app = Flask(__name__)
auth = HTTPBasicAuth()

DATABASE1 = 'tagdatabase.db'
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

# Add new tags
@app.route("/tag/addtag", methods=['POST'])
def addTags():
    if (request.method == 'POST'):
        try:
            db1 = get_db1()
            c1 = db1.cursor()

            db2 = get_db2()
            c2 = db2.cursor()

            details = request.get_json()
            update_time = datetime.datetime.now()
            email = request.authorization.username

            tag_Details=details['tag'].split(',')
            articleId=details['articleId']

            c2.execute("SELECT article_id FROM article WHERE article_id=? and email=?",(articleId,email,))
            rec=c2.fetchone()
            #datalen=len(rec)
            if (rec):
                for tags in tag_Details:
                    tag=tags.strip()
                    c1.execute("SELECT tag_id FROM tag_head WHERE tag_name=?",(tag,))
                    rec=c1.fetchall()
                    rowsaffected=len(rec)
                    if rowsaffected == 0:
                        c1.execute("INSERT INTO tag_head (tag_name,create_time,update_time) VALUES (?,?,?)",(tag,datetime.datetime.now(), datetime.datetime.now()))
                        c1.execute("SELECT tag_id FROM tag_head WHERE tag_name=?",(tag,))
                        rec2=c1.fetchall()
                        tid=rec2[0][0]
                        c1.execute("INSERT INTO tag_detail (article_id,tag_id,email,create_time,update_time) VALUES (?,?,?,?,?)",(articleId,tid,email,datetime.datetime.now(), datetime.datetime.now()))
                    else:
                        tid=rec[0][0]
                        c1.execute("INSERT INTO tag_detail VALUES (?,?,?,?,?)",(articleId,tid,email,datetime.datetime.now(), datetime.datetime.now()))

                    if (c1.rowcount == 1):
                        db1.commit()
                        response = Response(status=201, mimetype='application/json')

                    else:
                        response = Response(status=404, mimetype='application/json')
            else:
                response = Response(status=404, mimetype='application/json')

        except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

        return response


#Delete a tag

@app.route("/tag/deletetag", methods=['DELETE'])
def deletetag():
    if (request.method == 'DELETE'):
        try:
            db = get_db1()
            c = db.cursor()
            details = request.get_json()
            artid= details['articleId']
            tag=details['tag']
            email = request.authorization.username
            c.execute("DELETE FROM tag_detail WHERE article_id=? AND email=? AND tag_id IN (SELECT tag_id FROM tag_head WHERE tag_name=?)",(artid,email,str(tag),))
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
#get all the tags related to article by article ID
@app.route("/tag/gettag/<artid>", methods=['GET'])
def getarticle(artid):
    if (request.method == 'GET'):
        try:
            db = get_db1()
            db.row_factory = dict_factory
            c = db.cursor()
            c.execute("SELECT * FROM tag_head WHERE tag_id IN (SELECT tag_id FROM tag_detail WHERE article_id=?)",(artid,))
            row = c.fetchall()
            db.commit()
            if row is not None:
                return jsonify(row)
            else:
                response = Response(status=404, mimetype='application/json')

        except sqlite3.Error as er:
                print(er)
                response = Response(status=409, mimetype='application/json')

    return response

# get all the articles with the given tag
@app.route('/tag/getarticles/<tag>',methods=['GET'])
def getart(tag):
    try:
        db = get_db1()
        db.row_factory = dict_factory
        c = db.cursor()
        c.execute("SELECT article_id FROM tag_detail WHERE tag_id IN (SELECT tag_id FROM tag_head WHERE tag_name=?)",(tag,))
        row = c.fetchall()
        db.commit()
        if row is not None:
            return jsonify(row)
        else:
            response = Response(status=404, mimetype='application/json')

    except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response

if __name__ == '__main__':
    app.run(debug=True)
