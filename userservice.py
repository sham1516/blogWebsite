from flask import Flask, jsonify, request, Response, g
import sqlite3, json
from flask_api import status
import datetime
from http import HTTPStatus
from flask_httpauth import HTTPBasicAuth
from passlib.hash import sha256_crypt

app = Flask(__name__)

DATABASE = 'userdatabase.db'

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


@app.route("/authentication", methods=['POST'])
def authentication():
    try:

        db = get_db()
        c = db.cursor()
        message = {}

        auth = request.authorization
        email = auth.username
        password = auth.password

        c.execute("select password from users where email=(:email)", {'email':email})
        row = c.fetchone()
        if row is not None:
            p = row[0]
            print(p)
            if (sha256_crypt.verify(password,p)):
                return ""
            else:
                return Response(status=401, mimetype='application/json')
        else:
            return Response(status=401, mimetype='application/json')

    except sqlite3.Error as er:
        print(er)

    return ""

@app.route("/createuser", methods=['POST'])
def createuser():
    if (request.method == 'POST'):
        try:
            details = request.get_json()
            db = get_db()
            c = db.cursor()
            update_time = datetime.datetime.now()
            password = sha256_crypt.encrypt((str(details['password'])))
            c.execute("insert into users (name, email, password, create_time, update_time) values (?,?,?,?,?)",
                    [details['name'], details['email'], password, update_time, update_time ])
            db.commit()

            response = Response(status=201, mimetype='application/json')

        except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response



@app.route("/display", methods=['GET'])
def display():

    return "<h1>authentication testing</h1>"


@app.route("/deleteuser", methods=['DELETE'])
def deleteuser():
    try:
        db = get_db()
        c = db.cursor()
        email = request.authorization.username

        c.execute("delete from users where email=(:email)",{'email':email})
        db.commit()

        response = Response(status=200, mimetype='application/json')

    except sqlite3.Error as er:
            print(er)
            response = Response(status=409, mimetype='application/json')

    return response

@app.route("/updatepassword", methods=['PATCH'])
def updatepassword():
    try:
        db = get_db()
        c = db.cursor()
        details = request.get_json()
        new_password = sha256_crypt.encrypt((str(details['new_password'])))
        email = request.authorization.username
        update_time = datetime.datetime.now()

        c.execute("update users set password=(:password), update_time=(:updatetime) where email=(:email)",{'email':email, 'password':new_password, 'updatetime':update_time})
        db.commit()
        response = Response(status=200, mimetype='application/json')

    except sqlite3.Error as er:
        print(er)
        response = Response(status=409, mimetype='application/json')

    return response

if __name__ == '__main__':
    app.run(debug=True)
