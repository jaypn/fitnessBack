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

        token = request.args.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        member_id = decoded['member_id']
        role = decoded['role']

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()

            if role == "admin":

                cursor.execute(
                    "SELECT first_name, last_name,DOB,username,created_at,type, members.id FROM members INNER JOIN membership ON membership.id=members.membership_id")
                members = cursor.fetchall()
            else:
                cursor.execute(
                    "SELECT first_name, last_name,DOB,username,created_at,type,members.id FROM members INNER JOIN membership ON membership.id=members.membership_id WHERE members.id=?", [member_id])
                members = cursor.fetchall()
            allMembers = []

            for member in members:
                allMembers.append({

                    "first_name": member[0],
                    "last_name": member[1],
                    "DOB": member[2],
                    "username": member[3],
                    "created_at": member[4],
                    "type": member[5],
                    "id": member[6]
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
        member = None

        first_name = request.json.get("first_name")
        last_name = request.json.get("last_name")
        DOB = request.json.get("DOB")
        username = request.json.get("username")
        password = request.json.get("password")
        membership_id = request.json.get("membership_id")
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
            print(member)
            if user:
                return Response("user with that username already exist", mimetype="text/html", status=501)

            rows = None

            cursor.execute("INSERT INTO members(first_name,last_name,DOB,username,password,membership_id) VALUES(?,?,?,?,?,?)", [
                           first_name, last_name, DOB, username, password, membership_id])
            conn.commit()
            rows = cursor.rowcount

            cursor.execute(
                "SELECT id,first_name, last_name,username, role,membership_id,created_at from members WHERE username=?", [username])
            member = cursor.fetchone()
            print(member)
            token = jwt.encode({'first_name': member[1], 'last_name': member[2], 'member_id': member[0], 'role': member[4], 'membership_id': member[5],
                                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=30)}, app.config['SECRET_KEY']).decode("UTF-8")

            cursor.execute("INSERT INTO session(member_id,token) VALUES(?,?)", [
                           member[0], token])
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
                    "member_id": member[0],
                    "first_name": first_name,
                    "last_name": last_name,
                    "created_at": member[6],
                    "username": username,
                    "role": member[4],
                    "token": token
                }
                return Response(json.dumps(return_data, default=str), mimetype="text/html", status=201)

            else:
                return Response("we are not able to save the token", mimetype="text/html", status=501)

    elif request.method == 'PATCH':
        conn = None
        cursor = None
        token = request.json.get("token")
        first_name = request.json.get("first_name")
        last_name = request.json.get("last_name")
        password = request.json.get("password")
        DOB = request.json.get("DOB")
        username = request.json.get("username")

        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        member_id = decoded['member_id']

        rows = None
        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            if first_name != "" and first_name != None:
                cursor.execute("UPDATE members SET first_name =? WHERE id=?", [
                               first_name, member_id])
            conn.commit()
            if last_name != "" and last_name != None:
                cursor.execute("UPDATE members SET last_name=? WHERE id=?", [
                               last_name, member_id])
            conn.commit()
            if username != "" and username != None:
                cursor.execute("UPDATE members SET username=? WHERE id=?", [
                               username, member_id])
            conn.commit()
            if password != "" and password != None:
                cursor.execute("UPDATE members SET password=? WHERE id=?", [
                               password, member_id])
            conn.commit()
            if DOB != "" and DOB != None:
                cursor.execute("UPDATE members SET =? WHERE id=?", [
                               user_birthdate, user_id])
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
                return Response("member has been updated", mimetype="text/html", status=204)
            else:
                return Response("you have no permission to update this member", mimetype="text/html", status=500)

    elif request.method == 'DELETE':
        conn = None
        cursor = None

        token = request.json.get("token")

        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        member_id = request.json.get("id")

        rows = None
        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM members WHERE id=?", [
                           member_id])
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
                return Response("user DELETED", mimetype="text/html", status=204)
            else:
                return Response("no permission to delete this user", mimetype="text/html", status=500)


@app.route("/api/login", methods=['POST', 'DELETE'])
def login():
    auth = request.authorization
    if request.method == 'POST':

        conn = None
        cursor = None
        rows = None
        username = request.json.get("username")
        password = request.json.get("password")

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute("SELECT id,first_name, last_name,username, role,membership_id FROM members WHERE username=? AND password=?", [
                           username, password])
            member = cursor.fetchone()
            print(member)

        except Exception as error:
            print("something went wrong: ")
            print(error)
        token = jwt.encode({'first_name': member[1], 'last_name': member[2], 'member_id': member[0], 'role': member[4], 'membership_id': member[5],
                            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=30)}, app.config['SECRET_KEY']).decode("UTF-8")

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO session(member_id,token) VALUES(?,?)", [
                           member[0], token])
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
                member = {
                    "member_id": member[0],
                    "first_name": member[1],
                    "last_name": member[2],

                    "username": member[3],
                    "role": member[4],

                    "token": token


                }
                return Response(json.dumps(member, default=str), mimetype="text/html", status=201)

            else:
                return Response("we are not able to save the token", mimetype="text/html", status=501)

    if request.method == 'DELETE':

        conn = None
        cursor = None
        token = request.json.get("token")

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session WHERE token=?", [token])
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
            if(rows != None):

                return Response("you are signed out", mimetype="text/html", status=201)
            else:
                return Response("something went wrong", mimetype="text/html", status=501)


@app.route("/api/workouts", methods=['GET', 'POST', 'PATCH', 'DELETE'])
def workouts_endpoint():
    auth = request.authorization
    if request.method == 'POST':
        conn = None
        cursor = None
        members = None
        rows = None
        video = request.json.get("video")
        description = request.json.get("description")
        name = request.json.get("name")
        token = request.json.get("token")
        membership_id = request.json.get("membership_id")
        print(token)
        print(type(token))
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":
            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()

                cursor.execute("INSERT INTO workout (video,description,name,membership_id) VALUES(?,?,?,?)", [
                               video, description, name, membership_id])
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
                    return Response("you have added a a video", mimetype="text/html", status=201)
                else:
                    return Response("we are not able to create a user for u", mimetype="text/html", status=501)
        else:
            return Response("you are not admin u cant add a video", mimetype="text/html", status=501)

    elif request.method == 'GET':
        conn = None
        cursor = None
        workouts = None
        token = request.args.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        membership_id = decoded['membership_id']
        role = decoded['role']

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            if role == 'admin':
                cursor.execute(
                    "SELECT * FROM workout")
            else:
                cursor.execute(
                    "SELECT * FROM workout WHERE membership_id=?", [membership_id])
            workouts = cursor.fetchall()
            allWorkouts = []
            for workout in workouts:
                allWorkouts.append({
                    "id": workout[0],
                    "video": workout[1],
                    "description": workout[2],
                    "name": workout[3],
                    "created_at": workout[4],
                    "membership_id": workout[5]
                })
            print(allWorkouts)
        except Exception as error:
            print("something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(workouts != None):

                return Response(json.dumps(allWorkouts, default=str), mimetype="application/json", status=200)
            else:
                return Response("something went wrong!", mimetype="application/json", status=500)

    elif request.method == 'PATCH':
        conn = None
        cursor = None
        video = request.json.get("video")
        description = request.json.get("description")
        name = request.json.get("name")
        workout_id = request.json.get("id")
        token = request.json.get("token")
        membership_id = request.json.get("membership_id")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":
            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()
                if video != "" and video is not None:
                    cursor.execute("UPDATE workout SET video =? WHERE id=?", [
                                   video, workout_id])
                conn.commit()
                if description != "" and description != None:
                    cursor.execute("UPDATE workout SET description=? WHERE id=?", [
                                   description, workout_id])
                conn.commit()
                if name != "" and name != None:
                    cursor.execute("UPDATE workout SET name=? WHERE id=?", [
                                   name, workout_id])
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
                    return Response("video has been updated", mimetype="text/html", status=204)
                else:
                    return Response("you have no permission to update this member", mimetype="text/html", status=500)
        else:
            return Response("you have no permission to update a video", mimetype="text/html", status=500)

    elif request.method == 'DELETE':
        conn = None
        cursor = None

        token = request.json.get("token")
        workout_id = request.json.get("id")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":

            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM workout WHERE id=?", [workout_id])
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
                    return Response("video DELETED", mimetype="text/html", status=204)
                else:
                    return Response("no permission to delete this video", mimetype="text/html", status=500)
        else:
            return Response("you have no permission delete a video", mimetype="text/html", status=500)


@app.route("/api/membership", methods=['GET', 'POST', 'PATCH', 'DELETE'])
def membership_endpoint():
    auth = request.authorization
    if request.method == 'POST':
        conn = None
        cursor = None
        rows = None
        m_type = request.json.get("type")
        description = request.json.get("description")
        token = request.json.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":
            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()

                cursor.execute("INSERT INTO membership (type,description) VALUES(?,?)", [
                               m_type, description])
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
                    return Response("you created a membership pachage", mimetype="text/html", status=201)
                else:
                    return Response("we are not able to create a user for u", mimetype="text/html", status=501)
        else:
            return Response("we are not able to create a user for u", mimetype="text/html", status=501)

    elif request.method == 'GET':
        conn = None
        cursor = None
        membership = None

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM membership")
            memberships = cursor.fetchall()
            allMemberships = []
            for membership in memberships:
                allMemberships.append({
                    "id": membership[0],
                    "type": membership[1],
                    "description": membership[2]
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
            if(memberships != None):

                return Response(json.dumps(allMemberships, default=str), mimetype="application/json", status=200)
            else:
                return Response("something went wrong!", mimetype="application/json", status=500)

    elif request.method == 'PATCH':
        conn = None
        cursor = None
        rows = 0
        m_type = request.json.get("type")
        description = request.json.get("description")
        m_id = request.json.get("id")
        token = request.json.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":
            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()
                if m_type != "" and m_type != None:
                    cursor.execute(
                        "UPDATE membership SET type =? WHERE id=?", [m_type, m_id])
                    conn.commit()
                    rows += cursor.rowcount
                if description != "" and description != None:
                    cursor.execute("UPDATE membership SET description=? WHERE id=?", [
                                   description, m_id])
                    conn.commit()
                    rows += cursor.rowcount

                print(rows)
            except Exception as error:
                print("something went wrong: ")
                print(error)
            finally:
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                if(rows > 0):
                    return Response("membership has been updated", mimetype="text/html", status=204)
                else:
                    return Response("you have no permission to update this member", mimetype="text/html", status=500)
        else:
            return Response("we are not able to create a user for u", mimetype="text/html", status=501)

    elif request.method == 'DELETE':
        conn = None
        cursor = None
        rows = None

        token = request.json.get("token")
        video_id = request.json.get("id")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        if role == "admin":

            try:
                conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                       host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
                cursor = conn.cursor()

                cursor.execute("DELETE FROM membership WHERE id=?", [video_id])
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
                    return Response("membership DELETED", mimetype="text/html", status=204)
                else:
                    return Response("no permission to delete this video", mimetype="text/html", status=500)


@app.route("/api/feedback", methods=['GET', 'POST', 'DELETE'])
def feedback():
    auth = request.authorization
    if request.method == 'POST':
        conn = None
        cursor = None
        members = None
        content = request.json.get("content")
        token = request.json.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        member_id = decoded['member_id']

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO feedback (content,member_id) VALUES(?,?)", [
                           content, member_id])
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
                return Response("you have sent a feedback", mimetype="text/html", status=201)
            else:
                return Response("we are not able to create a user for u", mimetype="text/html", status=501)

    elif request.method == 'GET':
        conn = None
        cursor = None
        feedbacks = None
        token = request.args.get("token")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        role = decoded['role']
        member_id = decoded['member_id']

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, content, feedback.created_at,feedback.id FROM feedback INNER JOIN members ON feedback.member_id = members.id")
            feedbacks = cursor.fetchall()
            allFeedbacks = []
            for feedback in feedbacks:
                allFeedbacks.append({

                    "username": feedback[0],
                    "content": feedback[1],
                    "created_at": feedback[2],
                    "id": feedback[3]
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
            if(feedbacks != None):

                return Response(json.dumps(allFeedbacks, default=str), mimetype="application/json", status=200)
            else:
                return Response("something went wrong!", mimetype="application/json", status=500)

    elif request.method == 'DELETE':
        conn = None
        cursor = None
        rows = None

        token = request.json.get("token")
        f_id = request.json.get("id")
        decoded = jwt.decode(token, app.config['SECRET_KEY'])
        member_id = decoded['member_id']
        role = decoded['role']
        print(role)

        try:
            conn = mariadb.connect(user=dbcreds.user, password=dbcreds.password,
                                   host=dbcreds.host, database=dbcreds.database, port=dbcreds.port)
            cursor = conn.cursor()
            if role == "admin":
                cursor.execute("DELETE FROM feedback WHERE id=?", [f_id])
            else:
                cursor.execute("DELETE FROM feedback WHERE id=? AND member_id=?", [
                               f_id, member_id])
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
                return Response("membership DELETED", mimetype="text/html", status=204)
            else:
                return Response("no permission to delete this video", mimetype="text/html", status=500)
