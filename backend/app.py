from flask import Flask, session, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
from schema.database import get_db_session
from schema.models import *

app = Flask(__name__)
app.secret_key = 'NnSELOhwoPri1o-RZR3d1A'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def user_loader(user_id):
    db_session = get_db_session()
    user = db_session.query(Users).filter(Users.userid == user_id).first()
    db_session.close()
    return user

@app.route("/")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return "Return register page"
    print(request)
    email = request.values['email']
    password = request.values['password']
    name = request.values['name']
    phonenumber = request.values['phonenumber']
    status = UsersStatus.ACTIVE.value
    db_session = get_db_session()

    new_user = Users(email=email, password=password, phonenumber=phonenumber, name=name, status=status)
    user_string = str(new_user)
    db_session.add(new_user)

    # commit causes new_user to expire
    db_session.commit()
    db_session.close()

    return "Created new user: " +  user_string

@app.route("/login", methods=["GET", "POST"])
def login():

    # GET
    if request.method == "GET":
        return "Login page!"

    # POST
    email = request.values['email']
    password = request.values['password']

    db_session = get_db_session()
    # check db for this userid
    # look for the user in the database and return it as a User type
    user = db_session.query(Users).filter(Users.email == email, Users.password == password).first()

    db_session.close()

    if user is None:
        print("User does not exist!")
        return redirect(url_for("login"))
    else:
        login_user(user)
        print("User logged in!")
        return redirect(url_for("notifications"))


@app.route("/notifications", methods=["GET"])
@login_required
def notifications():
    user = current_user
    print(str(user.userid))

    db_session = get_db_session()
    # TODO: get notification history based on user id
    db_session.close()

    return "Retrieved notifications!"

@app.route("/addevent", methods=["GET", "POST"])
@login_required
def add_events():
    if request.method == "GET":
        return "return the add event page"
    else:
        # remember to do type checking here
        db_session = get_db_session()
        db_session.close()
        return "Create an event and insert into the database"

@app.route("/reported_events", methods=["GET"])
@login_required
def reported_events():
    db_session = get_db_session()
    # get recent events
    db_session.close()
    return "return index + 10 reported events, the client must send an index to indicate which page they are on"

@app.route("/event/<eventid>", methods=["GET"])
@login_required
def event():
    db_session = get_db_session()
    # fetch the event information based on the event id
    db_session.close()

    return "return event specifics"

@app.route("/logout")
def logout():
    logout_user()
    return "logged out"

if __name__ == '__main__':
    app.run()