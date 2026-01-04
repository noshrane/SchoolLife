import secrets
import os
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config['SESSION_PERMANENT'] = False # session expires when tab is closed
app.config['SESSION_TYPE'] = "filesystem" # stores data in filesystem rather than cookies

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' # configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(24))
Session(app) # initializes

db = SQLAlchemy(app) # initialize sqlalchemy with app

class Users(db.Model): # defined users model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String) # hash
    community = db.Column(db.String)

class Schedule(db.Model): # defined schedules model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    period = db.Column(db.Integer)
    subject = db.Column(db.String)
    teacher = db.Column(db.String)

with app.app_context(): # create tabel
    db.create_all()

@app.after_request 
def after_request(response): # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    if(session.get("user_id")):
        return redirect("/home")
    else:
        return redirect("/login")

@app.route("/home")
def home():

    return render_template("home.html", message="")

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear() # forget any user id

    if request.method=="GET":
        return render_template("login.html")

    else:

        if "login" in request.form: # if log in form
            
            if not request.form.get("username") or not request.form.get("password"):
                return render_template("login.html", message="Please fill required fields.")
            
            user = Users.query.filter_by(username=request.form.get("username")).first()

            if not user:
                return render_template("login.html", message="Username does not exist")

            if not check_password_hash(user.password, request.form.get("password")):
                return render_template("login.html", message="Incorrect password")

            session["user_id"] = user.id
            
        else: # if register form
            
            if not request.form.get("username-r") or not request.form.get("password-r"):
                return render_template("login.html", message="Please fill required fields")

            user = Users.query.filter_by(username=request.form.get("username-r")).first()

            if user:
                return render_template("login.html", message="Username already exists")
        
            else:
                # insert info into database
                password_hash = generate_password_hash(request.form.get("password-r"))

                one_user = Users(
                    username=request.form.get("username-r"),
                    password=password_hash,
                    community="null",
                )

                db.session.add(one_user)
                db.session.commit()
            
                session["user_id"] = one_user.id

        return redirect("/")

@app.route("/logout")
def logout():
    
    session.clear() # forget user id
    return redirect("/") 