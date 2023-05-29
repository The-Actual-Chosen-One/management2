from operator import truediv
from optparse import Values
from unittest import result
from urllib import response
from urllib.robotparser import RequestRate
import pymysql
import hashlib
import uuid
import os
from flask import Flask, render_template, request, redirect, session, flash
app = Flask(__name__)

app.secret_key = "Kiefer is the killer"

#a
def create_connection():
    return pymysql.connect(
        host="10.0.0.17",
        user="anthsu",
        # host="localhost",
        # user="root",
        password="ANVIL",
        db="anthsu_testtt",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor

    )


def can_access():
    if "logged_in" in session:
        matching_id = session["id"] == int(request.args["id"])
        is_admin = session["role"] == "admin"
        return matching_id or is_admin
    else:
        return False

def encrypt(password):
    return hashlib.sha256(password.encode()).hexdigest()


# This runs before every page request.
# If it returns something, the request will be prevented.
@app.before_request
def restrict():
    restricted = ["admin_only"]
    if request.endpoint in restricted:
        if "logged_in" not in session or session["role"] != "admin":
            flash("Only admin can view that page.")
            return redirect('/')

@app.route("/")
def home():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users"
            cursor.execute(sql)
            result = cursor.fetchall()
    return render_template("home.html", result=result)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """SELECT * FROM users
                    WHERE email = %s AND password = %s"""
                values = (
                    request.form["email"],
                    encrypt(request.form["password"])
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()
        if result:
            session["logged_in"] = True
            session["id"] = result["id"]
            session["first_name"] = result["first_name"]
            session["role"] = result["role"]
            return redirect("/")
        else:
            flash("Wrong username or password!")
            return redirect("/login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                image = request.files["image"]
                if image:
                    # Choose a random filename to prevent clashes
                    ext = os.path.splitext(image.filename)[1]
                    image_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                    image.save(image_path)
                else:
                    image_path = None

                # Any input from the user should be replaced by '%s',
                # so that their input isn't accidentally treated as bits of SQL.
                sql = """INSERT INTO users
                    (first_name, last_name, email, password, BDay, image)
                    VALUES (%s, %s, %s, %s, %s, %s)"""
                values = (
                    request.form["first_name"],
                    request.form["last_name"],
                    request.form["email"],
                    encrypt(request.form["password"]),
                    request.form["BDay"],
                    image_path
                )
                cursor.execute(sql, values)
                connection.commit() # <-- NEW!!! Save to the database
        return redirect("/")
    else:
        return render_template("signup.html")

# VIEWING THEIR DATA
@app.route("/view")
def view():
    if not can_access():
        flash("You don't have permission to do that!")
        return redirect("/")

    with create_connection() as connection:
        with connection.cursor() as cursor:

            sql = "SELECT * FROM users WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values)
            result = cursor.fetchall()
        return render_template("view.html", result=result)


# /post?id=1
@app.route("/post")
def post():
    if not can_access():
        flash("You don't have permission to do that!")
        return redirect("/")

    with create_connection() as connection:
        with connection.cursor() as cursor:

            sql = "SELECT * FROM users WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values)
            result = cursor.fetchall()
    return "here is the post: " + result["content"]

# /update?id=1
@app.route("/update", methods=["GET", "POST"])
def update():
    if not can_access():
        flash("You don't have permission to do that!")
        return redirect("/")

    if request.method == "POST":
        with create_connection() as connection:
            with connection.cursor() as cursor:

                password = request.form["password"]
                if password:
                    encrypted_password = encrypt(password)
                else:
                    encrypted_password = request.form["old_password"]

                image = request.files["image"]
                if image:
                    ext = os.path.splitext(image.filename)[1]
                    # if ext in [".jpg", ".png"]:
                    image_path = "static/images/" + str(uuid.uuid4())[:8] + ext
                    image.save(image_path)
                else: 
                    image_path = request.form["old_image"]

                sql = """UPDATE users SET
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    password = %s,
                    BDay = %s,
                    image = %s
                    WHERE id = %s
                """
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                    request.form['BDay'],
                    image_path,
                    request.form['id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect("/")
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s"
                values = (request.args["id"])
                cursor.execute(sql, values)
                result = cursor.fetchone()
        return render_template("update.html", result=result)

# /delete?id=1
@app.route("/delete")
def delete():
    if not can_access():
        flash("You don't have permission to do that!")
        return redirect("/")
    
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s"
            values = (request.args["id"])
            cursor.execute(sql, values)
            connection.commit()
    return redirect("/")


# /admin?id=1&role=admin
@app.route("/admin")
def toggle_admin():
    if "logged_in" in session and session["role"] == "admin":
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = "UPDATE users SET role = %s WHERE id = %s"
                values = (
                    request.args["role"],
                    request.args["id"]
                )
                cursor.execute(sql, values)
                connection.commit()
    else:
        flash("You don't have permission to do that!")
    return redirect("/")

@app.route("/hidden")

def admin_only():
    return "Here is where I would put restricted content, if I had any."


app.run(debug=True)