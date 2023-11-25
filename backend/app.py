from flask import Flask, session, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import json
from schema.database import get_db_session
from schema.models import *

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# class User(UserMixin):
#     def __init__(self, email, password):
#         self.id = email
#         self.password = password

@login_manager.user_loader
def user_loader(user_id):
    db_session = get_db_session()
    # check db for this userid
    user = db_session.query(Users).filter_by(Users.userid == user_id)
    db_session.close()
    # if exists, then return user --> what if doesn't exist?
    return user

@app.route("/")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return "Return register page"

    email = request.values['email']
    password = request.values['password']
    name = request.values['name']
    phonenumber = request.values['phonenumber']
    status = UsersStatus.ACTIVE

    new_user = Users(email=email, password=password, phonenumber=phonenumber, name=name, status=status)

    db_session = get_db_session()
    db_session.add(new_user)
    db_session.commit()
    db_session.close()

    return "<p> Created new user: " + str(new_user) + "</p>"

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
    user = db_session.query(Users).filter(Users.email == email, Users.password == password)

    db_session.close()

    if user is None:
        return redirect(url_for("login"))
    else:
        login_user(user)
        return redirect(url_for("notifications"))


@app.route("/notifications", methods=["GET"])
@login_required
def notifications():
    user = current_user
    # get notification history based on user id
    db_session = get_db_session()
    db_session.close()
    return user.id

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