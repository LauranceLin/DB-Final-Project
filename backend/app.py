from flask import Flask, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from schema.database import get_db_session
from schema.models import *
import bcrypt
import datetime
from schema.enums import *
import json
from sqlalchemy import exc, select
from celery import Celery

app = Flask(__name__)
app.secret_key = 'NnSELOhwoPri1o-RZR3d1A'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'

celery = Celery(app.name, broker = app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

NUM_ITEMS_PER_PAGE = 10

@celery.task
def create_notifications(notification_info):
    print("enter create notifications function")
    print(notification_info)
    notificationtype = notification_info["notificationtype"]
    eventid = notification_info["eventid"]
    eventtype = notification_info["eventtype"]
    eventdistrict = notification_info["eventdistrict"]
    eventanimal = notification_info["eventanimals"]

    db_session = get_db_session();
    try:
        note_timestamp = datetime.datetime.now()

        # first select all that match eventtype and eventdistrict
        subscriber_query = select(UserSubscriptionRecord.userid) \
                        .join(Channel, UserSubscriptionRecord.channelid == Channel.channelid) \
                        .filter((Channel.eventtype == eventtype) | (Channel.eventdistrict == eventdistrict)) \
                        .distinct()
        print("created first query")
        # then match all animal types and union the queries
        for animal in eventanimal:
            new_animal_query = select(UserSubscriptionRecord.userid) \
                        .join(Channel, UserSubscriptionRecord.channelid == Channel.channelid) \
                        .filter(Channel.eventanimal == animal) \
                        .distinct()

            # union select only distinct values
            subscriber_query.union(new_animal_query)

        # execute the query andn get resulting userids
        subscribed_users = db_session.execute(subscriber_query).all()

        new_notes = [ UserNotification( \
                            notificationtype=notificationtype, \
                            eventid=eventid, \
                            notifieduserid=user[0], \
                            notificationtimestamp=note_timestamp) \
                    for user in subscribed_users]

        db_session.bulk_save_objects(new_notes)
        db_session.commit()
        print("Successfully Created All Notifications")

    except exc.SQLAlchemyError as e:
        print("Rollback, due to error: ", e._message)
        db_session.rollback()
    db_session.close()

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

@app.route("/notifications/<int:offset>", methods=["GET"])
@login_required
def notifications(offset):

    db_session = get_db_session()

    # get recent history notifications determined by offset
    notified_events = db_session.query(Event) \
        .join(UserNotification, UserNotification.eventid == Event.eventid) \
        .filter(UserNotification.notifieduserid == current_user.userid) \
        .order_by(UserNotification.notificationtimestamp.desc()) \
        .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()

    event_list = []
    for event in notified_events:
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

    db_session.close()

    return jsonify(event_list)

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

        notification_info = {}
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

            notification_info["notificationtype"] = NOTIFICATION_TYPE[NotificationType.EVENT.value]
            notification_info["eventid"] = new_event.eventid
            notification_info["eventdistrict"] = new_event.district
            notification_info["eventtype"] = new_event.eventtype
            notification_info["eventanimals"] = []

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
                notification_info['eventanimals'].append(ANIMAL_TYPE[animal['animaltype']])

            db_session.commit()

        except exc.SQLAlchemyError:
            print(exc.SQLAlchemyError)
            db_session.rollback()

        db_session.close()

        # TODO: Send out notifications with celery app

        create_notifications.delay(notification_info)
        # create_notifications(notification_info)

        return "Created new event and animals"

@app.route("/reported_events/<int:offset>", methods=["GET"])
@login_required
def reported_events(offset):

    db_session = get_db_session()
    # TODO: Query most recent events
    results = db_session.query(Event).order_by(Event.createdat.desc()).offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE)
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
        .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE)

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

@app.route("/subscription", methods=["GET", "POST"])
@login_required
def subscription():
    db_session= get_db_session()
    target_user_id = current_user.userid

    if request.method == "GET":
        result = db_session.query(Channel) \
            .join(UserSubscriptionRecord, Channel.channelid == UserSubscriptionRecord.channelid) \
            .filter(UserSubscriptionRecord.userid == target_user_id).all()

        subscribed_channels = []
        for c in result:
            c_info = {
                "eventanimal": c.eventanimal,
                "eventtype": c.eventtype,
                "eventdistrict": c.eventdistrict
            }
            subscribed_channels.append(c_info)

        db_session.close()
        return jsonify(subscribed_channels)

    else:
        if 'eventdistrict' in request.form:
            eventdistrict = request.values['eventdistrict']
        else:
            eventdistrict = None

        if 'eventtype' in request.form:
            eventtype = request.values['eventtype']
        else:
            eventtype = None

        if 'eventanimal' in request.form:
            eventanimal = request.values['eventanimal']
        else:
            eventanimal = None

        selected_channel = db_session.query(Channel.channelid) \
            .filter(Channel.eventanimal == eventanimal) \
            .filter(Channel.eventtype == eventtype) \
            .filter(Channel.eventdistrict == eventdistrict).first()

        print(f"The selected channel has id={selected_channel.channelid}")

        new_record = UserSubscriptionRecord(userid=current_user.userid, channelid=selected_channel.channelid)

        try:
            db_session.add(new_record)
            db_session.commit()
        except:
            db_session.rollback()
        db_session.close()

        return f"added a new subscription record!"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "logout successful"

if __name__ == '__main__':
    app.run()