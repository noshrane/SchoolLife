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
    schedule_given = db.Column(db.Boolean)
    color = db.Column(db.String)

class Schedule(db.Model): # defined schedules model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    period = db.Column(db.Integer)
    subject = db.Column(db.String)
    teacher = db.Column(db.String)

class Community(db.Model): # defined communities model
    id = db.Column(db.Integer, primary_key=True)
    community = db.Column(db.String)
    periods = db.Column(db.Integer)

with app.app_context(): # create tabel
    db.drop_all()
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
    user = Users.query.filter_by(id=session.get("user_id")).first()

    if not user:
        return redirect("/login")

    if user.community == "null" or not user.community:
        return redirect("/join_community")
    elif not user.schedule_given:
        return redirect("/schedule")

    filtered_members = Users.query.filter_by(community=user.community, schedule_given=True).all()
    members = [user.username for user in filtered_members]

    comm = Community.query.filter_by(community=user.community).first()

    columns = comm.periods * 2 + 1
    rows = len(members)

    big_list = [[None for _ in range(columns)] for _ in range(rows)]
    # each array in this 2d array will be as follows: member, subject, teacher, subject, teacher (repeat as suitable)
    
    for i in range(len(members)):
        big_list[i][0] = members[i]

        filtered_schedule = Schedule.query.filter_by(username=members[i]).all()
        subjects = [user.subject for user in filtered_schedule]
        teachers = [user.teacher for user in filtered_schedule]

        for a in range(len(subjects)):
            big_list[i][a + 1] = subjects[a]
            big_list[i][a + 1 + comm.periods] = teachers[a]
    
    print(big_list)
    return render_template("home.html", total=big_list, periods=comm.periods, community=user.community, color=user.color)

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
                    schedule_given=False,
                    color="#37a9c0"
                )

                db.session.add(one_user)
                db.session.commit()
            
                session["user_id"] = one_user.id

        return redirect("/")

@app.route("/logout")
def logout():
    
    session.clear() # forget user id
    return redirect("/") 

@app.route("/join_community", methods=["GET", "POST"])
def join_community():
    if request.method=="GET":
        list = [community.community for community in Community.query.all()]
        print(list)

        return render_template("join_community.html", message="", list=list)
    
    else:
        selected_community = request.form.get("community")
        list = [community.community for community in Community.query.all()]

        if selected_community == "null":
            return render_template("join_community.html", message="Please select a community.", list=list)

        user = Users.query.filter_by(id=session.get("user_id")).first()

        user.community = selected_community
        db.session.commit()

        return redirect("/schedule")

@app.route("/create_community", methods=["GET", "POST"])
def create_community():
    if request.method=="GET":
        return render_template("create_community.html", message="")
    
    else:
        if not request.form.get("school") or not request.form.get("periods"):
            return render_template("create_community.html", message="Please fill each field.")
 
    
        one_community = Community(
            community=request.form.get("school"),
            periods=request.form.get("periods"),
        )

        db.session.add(one_community)

        user = Users.query.filter_by(id=session.get("user_id")).first()
        user.community = request.form.get("school")

        db.session.commit()

        return redirect("/schedule")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")

@app.route("/create_schedule", methods=["GET", "POST"])
def create_schedule():
    if request.method == "GET":
        user = Users.query.filter_by(id=session.get("user_id")).first()
        community = Community.query.filter_by(community=user.community).first()

        if not community:
            return redirect("/join_community")

        return render_template("create_schedule.html", periods=community.periods, message="")

    else:
        user = Users.query.filter_by(id=session.get("user_id")).first()
        community = Community.query.filter_by(community=user.community).first()

        for i in range(community.periods):
            if not request.form.get(f"subject_{ i }") or not request.form.get(f"teacher_{ i }"):
                return render_template("create_schedule.html", periods=community.periods, message="Please fill all fields.")
        
        for i in range(community.periods):
            one_row = Schedule(
                username = user.username,
                period = i,
                subject = request.form.get(f"subject_{ i }"),
                teacher = request.form.get(f"teacher_{ i }"),
            )

            db.session.add(one_row)
        
        user.schedule_given = True
        db.session.commit()

        return redirect("/setup")

@app.route("/setup")
def setup():
    user = Users.query.filter_by(id=session.get("user_id")).first()

    if user.community == "null" or not user.community:
        return redirect("/join_community") 
    
    if not user.schedule_given:
        return redirect("/schedule")

    return render_template("setup.html")
    
@app.route("/settings", methods=["GET", "POST"])
def settings():
    user = Users.query.filter_by(id=session.get("user_id")).first()

    if request.method == "GET":
        return render_template("settings.html", username=user.username, community=user.community, color=user.color)

    else:
        former_username = user.username

        if request.form.get("password"):
            user.password = generate_password_hash(request.form.get("password"))
        
        if request.form.get("color"):
            user.color = request.form.get("color")

        if request.form.get("username"):
            user.username = request.form.get("username")

            rows = Schedule.query.filter_by(username=former_username).all()
            for row in rows:
                row.username = request.form.get("username")

        db.session.commit()

        return redirect("/")



    