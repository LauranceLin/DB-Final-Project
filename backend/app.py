from flask import Flask, request, redirect, url_for, jsonify, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from schema.database import get_db_session
from schema.models import *
import bcrypt
import datetime
from schema.enums import *
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

# check role
def is_user():
    return current_user.role == ROLE[0]

def is_admin():
    return current_user.role == ROLE[1]

def is_responder():
    return current_user.role == ROLE[2]

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
        subscriber_query = select(SubscriptionRecord.userid) \
                        .join(Channel, SubscriptionRecord.channelid == Channel.channelid) \
                        .filter((Channel.eventtype == eventtype) | (Channel.eventdistrict == eventdistrict)) \
                        .distinct()
        print("created first query")
        # then match all animal types and union the queries
        for animal in eventanimal:
            new_animal_query = select(SubscriptionRecord.userid) \
                        .join(Channel, SubscriptionRecord.channelid == Channel.channelid) \
                        .filter(Channel.eventanimal == animal) \
                        .distinct()

            # union select only distinct values
            subscriber_query.union(new_animal_query)

        # execute the query andn get resulting userids
        subscribed_users = db_session.execute(subscriber_query).all()

        new_notes = [ Notification( \
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
        render_template("../frontend/register.html")

    email = request.values['email']
    password = request.values['password']
    name = request.values['name']
    phonenumber = request.values['phonenumber']
    status = USERS_STATUS[UsersStatus.ACTIVE.value]
    db_session = get_db_session()

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    print(new_user)
    try:
        new_user = Users(email=email, password=hashed_password, role=ROLE[0])

        db_session.add(new_user)
        db_session.flush()
        print(f"Created new user with userid={new_user.userid}")

        new_userinfo = UserInfo(userid=new_user.userid, phonenumber=phonenumber, name=name, status=status)

        db_session.add(new_userinfo)
        db_session.commit()

    except exc.SQLAlchemyError as e:
        print("Rollback, due to error: ", e._message)

        db_session.rollback()
        db_session.close()

        return redirect(url_for("register"))

    db_session.close()

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    # GET
    if request.method == "GET":
        render_template("../frontend/login.html")

    # POST
    email = request.values['email']
    password = request.values['password']

    db_session = get_db_session()

    user = db_session.query(Users).filter(Users.email == email).first()

    db_session.close()

    if user and bcrypt.checkpw(password.encode(), user.password.encode()):
        login_user(user)
        print("User logged in!")
        return redirect(url_for("notifications", offset=0))
    else:
        print("Login failed")
        return redirect(url_for("login"))

@app.route("/userinfo", method=["GET"])
def get_userinfo():
    db_session = get_db_session()
    if is_user():
        userinfo = db_session.query(UserInfo).filter(UserInfo.userid == current_user.userid)
        info = {
            "userid": current_user.userid,
            "email": current_user.email,
            "name": userinfo.name,
            "phonenumber": userinfo.phonenumber
        }
        return jsonify(info)
    elif is_responder():
        responderinfo = db_session.query(ResponderInfo).filter(ResponderInfo.userid == current_user.userid)
        info = {
            "userid": current_user.userid,
            "email": current_user.email,
            "name": responderinfo.name,
            "phonenumber": userinfo.phonenumber,
            "type": responderinfo.type,
            "address": responderinfo.address
        }
        return jsonify(info)
    else: # admin
        return jsonify({"userid": current_user.userid, "email": current_user.email})

@app.route("/notifications/<int:offset>", methods=["GET"])
@login_required
def notifications(offset):
    # TODO: Test the url parameter notificationtype

    if 'notificationtype' in request.args:
        notification_type = request.args.get('notificationtype')

        if not check_notificationtype(notification_type):
            return jsonify({"Error": "No such notificationtype"})

        db_session = get_db_session()
        notified_events = db_session.query(Event) \
            .join(Notification, Notification.eventid == Event.eventid) \
            .filter(Notification.notifieduserid == current_user.userid) \
            .filter(Notification.notificationtype == NOTIFICATION_TYPE[notification_type]) \
            .order_by(Notification.notificationtimestamp.desc()) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()
    else:
        db_session = get_db_session()
        # get recent history notifications determined by offset
        notified_events = db_session.query(Event) \
            .join(Notification, Notification.eventid == Event.eventid) \
            .filter(Notification.notifieduserid == current_user.userid) \
            .filter(Notification.notificationtype == NOTIFICATION_TYPE[notification_type]) \
            .order_by(Notification.notificationtimestamp.desc()) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()

    event_list = []

    for event in notified_events:
        animals = db_session.query(Animal).filter(Animal.eventid == event.eventid).all()

        animallist = [animal.__dict__ for animal in animals]

        e = {
            "eventid": event.eventid,
            "eventtype": event.eventtype,
            "userid": event.userid,
            "responderid": event.responderid,
            "status": event.status,
            "shortdescription": event.shortdescription,
            "city": event.city,
            "district": event.district,
            "createdat": str(event.createdat),
            "animals": animallist
        }
        event_list.append(e)

    db_session.close()

    return render_template("../frontend/notifications.html", event_list=event_list)

@app.route("/addevent", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "GET":
        render_template("../frontend/addevent.html")

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

        # error checking for animal
        try:
            eventanimals = request.form.getlist('eventanimals')
        except:
            jsonify({"error": "eventanimals should be a list of dictionaries"})

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

    return render_template("../frontend/reported_events.html", event_list=event_list)

@app.route("/event/<int:eventid>", methods=["GET", "POST"])
@login_required
def event(eventid):
    if request.type == "GET":
        db_session = get_db_session()

        query_event = select(Event, ResponderInfo.name.label("responder_name"), ) \
                .outerjoin(ResponderInfo, ResponderInfo.responderid == Event.responderid) \
                .filter(Event.eventid == eventid).first()

        event = db_session.execute(query_event)
        # test if outerjoin works (includes all events that have responder = Null values)
        query_animals = select(Animal, Placement.name.label("placement_name")) \
            .outerjoin(Placement, Placement.placementid == Animal.placementid) \
            .filter(Animal.eventid == eventid).all()

        eventanimals = db_session.execute(query_animals)

        animallist = [
            {
                "animalid": animal.animalid,
                "placementid": animal.placementid,
                "placementname": animal.placement_name,
                "type": animal.type,
                "description": animal.description
            }
        for animal in eventanimals]

        result = {
            "eventid": event.eventid,
            "eventtype": event.eventtype,
            "userid": event.userid,
            "responderid": event.responderid,
            "respondername": event.responder_name,
            "status": event.status,
            "shortdescription": event.shortdescription,
            "city": event.city,
            "district": event.district,
            "createdat": str(event.createdat),
            "animals": animallist
        }

        if event.status == EVENT_STATUS[EventStatus.RESOLVED.value]:
            # fetch report info
            warning = db_session.query(Warning).filter(Warning.eventid == event.eventid).first()
            result["warning"] = {
                "warninglevel": warning.warninglevel,
                "shortdescription": warning.shortdescription,
                "createdat": warning.createdat
            }
        elif event.status == EVENT_STATUS[EventStatus.FAILED.value]:
            # fetch warning info
            report = db_session.query(Report).filter(Report.eventid == event.eventid).first()
            result["report"] = {
                "shortdescription": report.shortdescription,
                "createdat": report.createdat
            }

        db_session.close()

        return render_template("../frontend/event.html", result=result)

    # POST
    # TODO: Test the responder editing functions
    if is_responder():
        # event info updates
        eventid = request.values["eventid"]

        db_session = get_db_session()

        # get the event item to do some checks
        event = db_session.query(Event).filter(Event.eventid == eventid).first()

        # check the event status
        if event.status == EVENT_STATUS[EventStatus.UNRESOLVED.value]:
            # no responder has accepted this event yet
            if "status" in request.form and request.values["status"] == EVENT_STATUS[EventStatus.ONGOING.value]:
                # responder accepts event
                try:
                    # lock
                    locked_event = db_session.query(Event).with_for_update().filter(Event.eventid == eventid).first()

                    # update
                    locked_event.status = EVENT_STATUS[EventStatus.ONGOING.value]
                    locked_event.responderid = current_user.userid

                    db_session.commit()

                except exc.SQLAlchemyError as e:
                    print("error", e._message)
                    print("failed to accept event")
                    db_session.rollback()

        elif event.status == EVENT_STATUS[EventStatus.ONGOING.value] and event.responderid == current_user.userid:
            # current_user is the responder for this event
            # udpate event info
            try:
                # lock event
                locked_event = db_session.query(Event).with_for_update().filter(Event.eventid == eventid).first()

                if "status" in request.form:
                    if request.values["status"] == EventStatus.UNRESOLVED.value:
                        # responder reverts acceptance of the event
                        # other responders may now accept the event
                        # current responder is only allowed to change the status to unresolved
                        # no other values should be changed
                        locked_event.status = EVENT_STATUS[EventStatus.UNRESOLVED.value]
                        locked_event.responderid = None
                        db_session.commit()

                    if request.values["status"] == EventStatus.FALSE_ALARM.value:
                        # responder can set eventstatus to false alarm and also change other event values
                        locked_event.status = EVENT_STATUS[EventStatus.FALSE_ALARM.value]

                    else:
                        db_session.close()
                        return jsonify({"error", "invalid status update"})

                if "eventtype" in request.form and check_eventtype(request.values["eventtype"]):
                    locked_event.eventtype = EVENT_TYPE[request["eventtype"]]
                else:
                    db_session.close()
                    return jsonify({"error", "invalid eventtype"})

                if "shortdescription" in request.form:
                    locked_event.shortdescription = request.values["shortdescription"]

                if "city" in request.values and "district" in request.values:
                    if check_location(request.values["city"], request.values["district"]):
                        locked_event.city = CITIES[request.values["city"]]
                        locked_event.district = DISTRICTS[request.values["district"]]
                    else:
                        db_session.close()
                        return jsonify({"error", "invalid location"})

                # animal updates
                # animals do not need to be locked
                # animals will not be updated if their corresponding event has not been locked already

                all_animal_updates = []

                if "animals" in request.form:
                    animal_list = request.form.getlist("animals")

                    for animal in animal_list:
                        updated_animal_info = {}
                        updated_animal_info['animalid'] = animal['animalid']
                        if "description" in animal:
                            updated_animal_info["description"] = animal["description"]
                        if "type" in animal:
                            updated_animal_info["type"] = animal["type"]
                        if "placementid" in animal:
                            updated_animal_info["placementid"] = animal["placementid"]

                        all_animal_updates.append(updated_animal_info)

                db_session.bulk_update_mappings(Animal, all_animal_updates)
                db_session.commit()

            except exc.SQLAlchemyError as e:
                print("SQLAlchemyError: ", e._message)

                db_session.rollback()

                return jsonify({"error": "error updating event info"})

        else:
            # responder should not be able to edit this event
            return redirect(url_for("event", eventid=eventid))

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

    return render_template("../frontend/reportrecord.html", event_list=event_list)

@app.route("/subscription/<int:offset>", methods=["GET", "POST"])
@login_required
def subscription(offset):
    db_session= get_db_session()

    if request.method == "GET":
        result = db_session.query(Channel) \
            .join(SubscriptionRecord, Channel.channelid == SubscriptionRecord.channelid) \
            .filter(SubscriptionRecord.userid == current_user.userid) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()

        subscribed_channels = []
        for c in result:
            c_info = {
                "channel_id": c.channelid,
                "eventanimal": c.eventanimal,
                "eventtype": c.eventtype,
                "eventdistrict": c.eventdistrict
            }
            subscribed_channels.append(c_info)

        db_session.close()
        return render_template("../frontend/subscription.html", subscribed_channels)

    # TODO: Test the delete functionality
    # POST (delete subscription)
    if "delete" in request.form:
        channelid = request.values["channelid"]

        # delete subscription
        db_session.query(SubscriptionRecord) \
            .filter(SubscriptionRecord.channelid == channelid) \
            .filter(SubscriptionRecord.userid == current_user.userid) \
            .delete()

        return redirect(url_for("subscription", offset=offset))

    # POST (add subscription)
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

    new_record = SubscriptionRecord(userid=current_user.userid, channelid=selected_channel.channelid)

    try:
        db_session.add(new_record)
        db_session.commit()
    except:
        db_session.rollback()
    db_session.close()

    return redirect(url_for("subscription", offset=offset))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return "logout successful"

# TODO: Test endpoint
# create warnings and reports
@app.route("/event_results/<int:eventid>", methods=["GET", "POST"])
@login_required
def event_results(eventid):

    # only responders can access this page
    if not is_responder():
        redirect(url_for("event", eventid=eventid))

    if request.method == "GET":
        return "return the event result page"

    result_type = request.values["result_type"]

    if not check_resulttype(result_type):
        return jsonify({"error": "no such notification type"})


    if result_type == NotificationType.EVENT.value:
        # create new report
        shortdescription = request.values["shortdescription"]
        createdat = datetime.datetime.now()
        new_report = Report(eventid=eventid, \
                            responderid=current_user.userid, \
                            shortdescription=shortdescription, \
                            createdat=createdat)
        try:
            db_session = get_db_session()
            db_session.add(new_report)

            # update the event status
            db_session = get_db_session().query(Event). \
                        filter(Event.eventid == eventid). \
                        update({"status": EVENT_STATUS[EventStatus.RESOLVED.value]})

            db_session.commit()
        except exc.SQLAlchemyError as e:
            print("Error: ", e._message)

        return redirect(url_for("event", eventid=eventid))

    else:
        # create new warning
        warninglevel = request.values["warninglevel"]
        if not check_warninglevel(warninglevel):
            return jsonify({"Error": "Warning level out of bounds"})

        shortdescription = request.values["shortdescription"]
        createdat = datetime.datetime.now()
        notification_info = {}

        try:
            db_session = get_db_session()

            new_warning = Warning(eventid=eventid, \
                                    responderid=current_user.userid, \
                                    shortdescription=shortdescription, \
                                    warninglevel=warninglevel, \
                                    createdat=createdat)

            # populate nofication_info values
            notification_info["notificationtype"] = NOTIFICATION_TYPE[NotificationType.WARNING.value]
            notification_info["eventid"] = eventid

            event = db_session.query(Event).filter(Event.eventid == eventid).first()

            notification_info["eventtype"] = event.eventtype
            notification_info["eventdistrict"] = event.district

            notification_info["eventanimals"] = db_session.query(Animal.type).filter(Animal.eventid == eventid).distinct().all()

            db_session.add(new_warning)

            # update the event status
            db_session = get_db_session().query(Event). \
                        filter(Event.eventid == eventid). \
                        update({"status": EVENT_STATUS[EventStatus.FAILED.value]})

            db_session.commit()
        except exc.SQLAlchemyError as e:
            print("Error: ", e._message)

        # TODO: create notifications
        create_notifications(notification_info)

        return redirect(url_for("event", eventid=eventid))

@app.route("/respond_record/<int:offset>", methods=["GET"])
def respond_record(offset):
    # only responder should be able to access this endpoint
    if not is_responder():
        return redirect(url_for("login"))

    # TODO: fetch all the events the responder responded to

if __name__ == '__main__':
    app.run()