from flask import Flask, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from schema.database import get_db_session
from schema.models import *
import bcrypt
import datetime
from schema.enums import *
import json
from sqlalchemy import exc

app = Flask(__name__)
app.secret_key = 'NnSELOhwoPri1o-RZR3d1A'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def user_loader(userid):
    db_session = get_db_session()
    user = db_session.query(Users).filter(Users.userid == userid).first()
    db_session.close()
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
    status = UsersStatus.ACTIVE.value
    db_session = get_db_session()

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = Users(email=email, password=hashed_password, phonenumber=phonenumber, name=name, status=status)

    try:
        db_session.add(new_user)
        db_session.commit()
    except exc.SQLAlchemyError:
        db_session.rollback()

    db_session.close()

    return "Created new user"

@app.route("/login", methods=["GET", "POST"])
def login():
    # GET
    if request.method == "GET":
        return "Login page!"

    # POST
    email = request.values['email']
    password = request.values['password']

    db_session = get_db_session()

    user = db_session.query(Users).filter(Users.email == email).first()

    db_session.close()

    if user and bcrypt.checkpw(password.encode(), user.password.encode()):
        login_user(user)
        print("User logged in!")
        return redirect(url_for("notifications"))
    else:
        print("Login failed")
        return redirect(url_for("login"))

@app.route("/notifications", methods=["GET"])
@login_required
def notifications():
    user = current_user
    print(str(user.userid))

    db_session = get_db_session()
    # TODO: get notification history based on user id
    db_session.close()

    return "Retrieved notifications!"

# error checking functions
def check_eventtype(eventtype):
    print(eventtype)
    print(EventType.EVENT_TYPE_LEN.value)
    if eventtype < 0 or eventtype >= EventType.EVENT_TYPE_LEN.value:
        return False
    return True

def check_location(city, district):
    if city < 0 or city >= City.CITY_LEN.value:
        return False
    if district < 0 or district >= len(DISTRICTS[city]):
        return False
    return True

def check_animaltype(animaltype):
    if type(animaltype) is not int or animaltype < 0 or animaltype >= AnimalType.ANIMAL_TYPE_LEN.value:
        return False
    return True

@app.route("/addevent", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "GET":
        return "return the add event page"
    else:
        db_session = get_db_session()

        userid = current_user.userid
        responderid = None
        status = EVENT_STATUS[EventStatus.UNRESOLVED.value]

        eventtype = request.values['eventtype']
        shortdescription = request.values['shortdescription']
        city = request.values['city']
        district = request.values['district']
        shortaddress = request.values['shortaddress']
        createdat = datetime.datetime.now()
        eventanimals = request.values['eventanimals']

        # error checking for event
        if len(shortaddress) > 30:
            return jsonify({"error": "Short address too long"})

        if len(shortdescription) > 100:
            return jsonify({"error": "Short description too long"})

        try:
            eventtype = int(eventtype)
            if not check_eventtype(eventtype=eventtype):
                raise
        except:
            return jsonify({"error": "Eventtype doesn't exist"})

        try:
            city = int(city)
            district = int(district)
            if not check_location(city=city, district=district):
                raise
        except:
            return jsonify({"error": "Location doesn't exist"})

        # error checking for animal
        try:
            eventanimals = json.loads(eventanimals)
        except:
            jsonify({"error": "eventanimals should be a list of dictionaries"})

        for animal in eventanimals:
            animaltype = animal['animaltype']
            animaldescription = animal['animaldescription']
            if not check_animaltype(animaltype=animaltype):
                return jsonify({"error": "AnimalType doesn't exist"})
            if len(animaldescription) > 100:
                return jsonify({"error": "Animal description too long"})

        # create event
        try:
            eventtype = EVENT_TYPE[eventtype]

            district_str = DISTRICTS[city][district]
            city_str = CITIES[city]
            animaltype = ANIMAL_TYPE[animaltype]

            new_event = Event(eventtype=eventtype, \
                userid=userid, \
                responderid=responderid, \
                status=status, \
                shortdescription=shortdescription, \
                city=city_str, district=district_str, \
                shortaddress=shortaddress, \
                createdat=createdat)

            db_session.add(new_event)
            db_session.flush()

            print(f"Created new event with id: {new_event.eventid}")

            # create animals
            for animal in eventanimals:
                new_animaltype = ANIMAL_TYPE[animal['animaltype']]
                new_animaldescription = animal['animaldescription']
                new_animal = Animal(eventid=new_event.eventid, \
                                    placementid=None, \
                                    type=new_animaltype, \
                                    description=new_animaldescription)
                db_session.add(new_animal)
                db_session.flush()
                print(f"Created new animal with id: {new_animal.animalid}")

            db_session.commit()

        except exc.SQLAlchemyError:
            db_session.rollback()

        db_session.close()

        # TODO: Send out notifications (preferably in a separate thread)

        return "Created new event and animals"

@app.route("/reported_events/<int:offset>", methods=["GET"])
@login_required
def reported_events(offset):
    db_session = get_db_session()
    # TODO: Query most recent events
    results = db_session.query(Event).order_by(Event.createdat.desc()).limit(10)
    db_session.close()

    event_list = []

    for event in results:
        e = {
            "eventid": event.eventid,
            "eventtype": event.eventtype,
            "userid": event.userid,
            "responderid": event.responderid,
            "status": event.status,
            "shortdescription": event.shortdescription,
            "city": event.city,
            "district": event.district,
            "createdat": str(event.createdat)
        }
        event_list.append(e)

    return jsonify(event_list)

@app.route("/event/<int:eventid>", methods=["GET"])
@login_required
def event(eventid):
    db_session = get_db_session()

    event = db_session.query(Event).filter(Event.eventid == eventid).first()

    result = {
        "eventid": event.eventid,
        "eventtype": event.eventtype,
        "userid": event.userid,
        "responderid": event.responderid,
        "status": event.status,
        "shortdescription": event.shortdescription,
        "city": event.city,
        "district": event.district,
        "createdat": str(event.createdat)
    }

    db_session.close()

    return jsonify(result)

# current users report record
@app.route('/reportrecord/<int:offset>')
@login_required
def reportrecord(offset):
    db_session = get_db_session()

    reported_events = db_session.query(Event) \
        .filter(Event.userid == current_user.userid) \
        .order_by(Event.createdat.desc()) \
        .offset(offset).limit(10)

    db_session.close()

    event_list = []
    for event in reported_events:
        e = {
            "eventid": event.eventid,
            "eventtype": event.eventtype,
            "userid": event.userid,
            "responderid": event.responderid,
            "status": event.status,
            "shortdescription": event.shortdescription,
            "city": event.city,
            "district": event.district,
            "createdat": str(event.createdat)
        }
        event_list.append(e)

    return jsonify(event_list)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "logout successful"

if __name__ == '__main__':
    app.run()