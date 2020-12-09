import mariadb
from flask import Flask, request, Response
import json
import dbcreds
from flask_cors import CORS
import datetime
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'youarelogedin'
CORS(app)


@app.route("/api/members", methods=['GET', 'POST', 'PATCH', 'DELETE'])
def members():
    auth = request.authorization
    if request.method == 'GET':
        conn = None
        cursor = None
        members = None
        member_id = request.args.get("memberId")
        token = request.args.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":
            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()

                if member_id != None:
                    cursor.execute(
                        "SELECT first name, last name,DOB,username,created_at,type FROM members INNER JOIN membership ON member_id=member.id WHERE id=?", [member_id])
                    member = cursor.fetchone()

                else:
                    cursor.execute(
                        "SELECT first name, last name,DOB,username,created_at,type FROM members INNER JOIN membership ON member_id=member.id")
                    members = cursor.fetchall()
                    allMembers = []

                    for member in members:
                        allMembers.append({

                            "first name": member[0],
                            "last name": member[1],
                            "DOB": member[2],
                            "username": member[3],
                            "created_at": member[4],
                            "type": member[5]
                        })

            except Exception as error:
                print("something went wrong: ")
                print(error)
            finally:
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                if(members != None):

                    return Response(json.dumps(allMembers, default=str), mimetype="application/json", status=200)
                else:
                    return Response("something went wrong!", mimetype="application/json", status=500)

    elif request.method == 'POST':
        conn = None
        cursor = None
        first_name = request.json.get("first_name")
        last_name = request.json.get("last_name")
        DOB = request.json.get("DOB")
        username = request.json.get("username")
        password = request.json.get("password")
        token = None
        if username == password:
            return Response("password shouldnt match with username", mimetype="text/html", status=501)
        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM members WHERE username=?", [username])
            user = cursor.fetchone()
            print(user)
            if user:
                return Response("user with that username already exist", mimetype="text/html", status=501)

        except Exception as error:
            print("something went wrong: ")
            print(error)

        rows = None
        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO members(first_name,last_name,DOB,username,password) VALUES(?,?,?,?,?)", [
                           first_name, last_name, DOB, username, password])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print("something went wrong: ")
            print(error)
        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id,created_at,role FROM members WHERE username=?", [username])
            user = cursor.fetchone()
            print(user)
            token = jwt.encode({'first_name': first_name, 'last_name': last_name, 'role': user[2], 'member_id': user[0],
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=30)}, app.config['SECRET_KEY']).decode("UTF-8")
        except Exception as error:
            print("something went wrong: ")
            print(error)

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO session(member_id,token) VALUES(?,?)", [
                           user[0], token])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print("something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                return_data = {
                    "member_id": user[0],
                    "first_name": first_name,
                    "last_name": last_name,
                    "created_at": user[1],
                    "username": username,
                    "token": token
                }
                return Response(json.dumps(return_data, default=str), mimetype="text/html", status=201)

            else:
                return Response("we are not able to save the token", mimetype="text/html", status=501)
