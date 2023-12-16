from flask import Flask, request, redirect, url_for, jsonify, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from schema.database import get_db_session
from schema.models import *
import bcrypt
import datetime
from schema.enums import *
from sqlalchemy import exc, select, except_, intersect, delete, union
from celery import Celery
import json

from sqlalchemy.sql.elements import literal_column
from sqlalchemy import func

app = Flask(__name__, template_folder='../frontend', static_url_path='/', static_folder='../frontend')
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

def is_responder():
    return current_user.role == ROLE[1]

def is_admin():
    return current_user.role == ROLE[2]

@celery.task
def create_notifications(notification_info):
    print("enter create notifications function")
    eventid = notification_info["eventid"]
    notificationtype = notification_info["notificationtype"]

    db_session = get_db_session();
    try:
        note_timestamp = datetime.datetime.now()

        # first select all that match eventtype and eventdistrict
        subscriber_query = select(SubscriptionRecord.userid) \
                        .join(EventCategory, EventCategory.channelid == SubscriptionRecord.channelid) \
                        .filter(EventCategory.eventid == eventid) \
                        .distinct()

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
        return render_template('register.html')

    email = request.values['email']
    password = request.values['password']
    name = request.values['name']
    phonenumber = request.values['phonenumber']
    status = USERS_STATUS[UsersStatus.ACTIVE.value]
    db_session = get_db_session()

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

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
        return render_template("login.html")

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

@app.route("/userinfo", methods=["GET"])
def get_userinfo():
    db_session = get_db_session()
    if is_user():
        userinfo = db_session.query(UserInfo).filter(UserInfo.userid == current_user.userid).first()
        info = {
            "userid": current_user.userid,
            "role": current_user.role,
            "email": current_user.email,
            "name": userinfo.name,
            "phonenumber": userinfo.phonenumber
        }
        return jsonify(info)
    elif is_responder():
        responderinfo = db_session.query(ResponderInfo).filter(ResponderInfo.responderid == current_user.userid).first()
        info = {
            "userid": current_user.userid,
            "role": current_user.role,
            "email": current_user.email,
            "name": responderinfo.name,
            "phonenumber": responderinfo.phonenumber,
            "type": responderinfo.respondertype,
            "address": responderinfo.address
        }
        return jsonify(info)
    else: # admin
        return jsonify({"userid": current_user.userid, "role": current_user.role, "email": current_user.email})

@app.route("/placementinfo", methods=["GET"])
def get_placementinfo():
    db_session = get_db_session()
    placements = db_session.query(Placement.placementid, Placement.name).all()
    print(placements)
    placement_list = [
        {
            "placementid": p.placementid,
            "placementname": p.name
        }
        for p in placements
    ]
    print(placement_list)
    return jsonify(placement_list)

@app.route("/notifications/<int:offset>", methods=["GET"])
@login_required
def notifications(offset):
    # TODO: Test the url parameter notificationtype

    if 'type' in request.args:
        notification_type = request.args.get('type')

        if not check_notificationtype(notification_type):
            return jsonify({"Error": "No such notificationtype"})
    else:
        notification_type = 'both'

    if notification_type == 'event' or notification_type == 'warning':
        notification_index = get_notification_index(notification_type)
        db_session = get_db_session()
        notified_events = db_session.query(Event) \
            .join(Notification, Notification.eventid == Event.eventid) \
            .filter(Notification.notifieduserid == current_user.userid) \
            .filter(Notification.notificationtype == NOTIFICATION_TYPE[notification_index]) \
            .order_by(Notification.notificationtimestamp.desc()) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()
    else: # both
        db_session = get_db_session()
        # get recent history notifications determined by offset
        notified_events = db_session.query(Event) \
            .join(Notification, Notification.eventid == Event.eventid) \
            .filter(Notification.notifieduserid == current_user.userid) \
            .order_by(Notification.notificationtimestamp.desc()) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()

    event_list = []

    if notified_events is not None:
        for event in notified_events:
            animals = db_session.query(Animal).filter(Animal.eventid == event.eventid).all()

            animallist = [ animal.type for animal in animals]

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
    print(event_list)
    return render_template("notifications.html", event_list=event_list, offset=offset)

@app.route("/addevent", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "GET":
        return render_template("addevent.html")

    else:
        db_session = get_db_session()

        userid = current_user.userid
        responderid = None
        status = EVENT_STATUS[EventStatus.UNRESOLVED.value]
        print("ALL REQUEST PARAMETERS: ", request.values)
        eventtype = request.values['eventtype']
        shortdescription = request.values['shortdescription']
        city = request.values['city']
        district = request.values['district']
        shortaddress = request.values['shortaddress']
        createdat = datetime.datetime.now()
        num_animals = len(request.form.getlist('animaltype'))
        if num_animals != len(request.form.getlist('animaldescription')):
            return jsonify({"error": "wrong number of animals"})

        eventanimals = [{
            'animaltype': int(request.form.getlist('animaltype')[i]),
            'animaldescription': request.form.getlist('animaldescription')[i]
        } for i in range(num_animals)]

        print(eventanimals)

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
            for animal in eventanimals:
                animaltype = animal['animaltype']
                animaldescription = animal['animaldescription']
                print(animaltype)
                print(animaldescription)
                if not check_animaltype(animaltype=animaltype):
                    return jsonify({"error": "AnimalType doesn't exist"})
                if len(animaldescription) > 100:
                    return jsonify({"error": "Animal description too long"})
        except:
            jsonify({"error": "eventanimals should be a list of dictionaries"})


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

            # save info for notification creation
            notification_info["eventid"] = new_event.eventid
            notification_info["notificationtype"] = NOTIFICATION_TYPE[NotificationType.EVENT.value]

            channel_query_list = []
            channel_query_list.append(select(Channel.channelid). \
                filter((Channel.eventdistrict == new_event.district) | (Channel.eventtype == new_event.eventtype)).distinct())

            # create animals
            animal_types = set()
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

                animal_types.add(ANIMAL_TYPE[animal['animaltype']])

            for type in animal_types:
                channel_query_list.append(select(Channel.channelid).filter(Channel.eventanimal == type).distinct())

                # notification_info['eventanimals'].append(ANIMAL_TYPE[animal['animaltype']])
            union_channel_query = union(*channel_query_list)
            event_channelids = db_session.execute(union_channel_query).all()

            event_categories = [
                EventCategory(eventid=new_event.eventid, channelid=channelid[0])
                for channelid in event_channelids
            ]

            db_session.bulk_save_objects(event_categories)

            db_session.commit()

        except exc.SQLAlchemyError as e:
            print(e._message)
            db_session.rollback()
            return redirect(url_for('add_event'))

        db_session.close()

        # Send out notifications with celery app

        create_notifications.delay(notification_info)

        return redirect(url_for('event', eventid=notification_info["eventid"]))

@app.route("/reported_events/<int:offset>", methods=["GET"])
@login_required
def reported_events(offset):

    if 'eventtype' in request.args:
        eventtype = int(request.args.get('eventtype'))
        if check_eventtype(eventtype):
            eventtype = EVENT_TYPE[eventtype]
        else:
            return jsonify({"error": "no such eventtype"})
    else:
        eventtype = None

    if 'eventdistrict' in request.args:
        eventdistrict = request.args.get('eventdistrict')
    else:
        eventdistrict = None

    if 'animaltype' in request.args:
        animaltype = int(request.args.get('animaltype'))
        if check_animaltype(animaltype):
            animaltype = ANIMAL_TYPE[animaltype]
        else:
            return jsonify({"error": "no such animal type"})
    else:
        animaltype = None

    db_session = get_db_session()
    # TODO: Query most recent events
    if eventtype is None and eventdistrict is None and animaltype is None:
        results = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .group_by(Event.eventid).order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()

        db_session.close()
    else:
        filter_channel = db_session.query(Channel) \
            .filter(Channel.eventanimal == animaltype) \
            .filter(Channel.eventdistrict == eventdistrict) \
            .filter(Channel.eventtype == eventtype).first()

        results = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .join(EventCategory, EventCategory.eventid == Event.eventid) \
            .filter(EventCategory.channelid == filter_channel.channelid) \
            .group_by(Event.eventid) \
            .order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()

        db_session.close()

    event_list = [
        {
            "eventid": event.Event.eventid,
            "eventtype": event.Event.eventtype,
            "userid": event.Event.userid,
            "responderid": event.Event.responderid,
            "status": event.Event.status,
            "shortdescription": event.Event.shortdescription,
            "city": event.Event.city,
            "district": event.Event.district,
            "createdat": str(event.Event.createdat),
            "animals": event[1].split(',')
        }
        for event in results
    ]
    # return event_list
    return render_template("reported_events.html", event_list=event_list, offset=offset)

@app.route("/event/<int:eventid>", methods=["GET", "POST"])
@login_required
def event(eventid):
    if request.method == "GET":
        db_session = get_db_session()

        query_event = select(Event, ResponderInfo.name) \
                .outerjoin(ResponderInfo, ResponderInfo.responderid == Event.responderid) \
                .filter(Event.eventid == eventid)

        eventinfo = db_session.execute(query_event).first()
        event = eventinfo.Event
        event_responder_name = eventinfo.name
        # test if outerjoin works (includes all events that have responder = Null values)
        query_animals = select(Animal, Placement.name) \
            .outerjoin(Placement, Placement.placementid == Animal.placementid) \
            .filter(Animal.eventid == eventid)

        eventanimals = db_session.execute(query_animals).all()
        print(eventanimals)

        animallist = [
            {
                "animalid": animal.Animal.animalid,
                "placementid": animal.Animal.placementid,
                "placementname": animal.name,
                "type": animal.Animal.type,
                "description": animal.Animal.description
            }
        for animal in eventanimals]

        result = {
            "eventid": event.eventid,
            "eventtype": event.eventtype,
            "userid": event.userid,
            "responderid": event.responderid,
            "respondername": event_responder_name,
            "status": event.status,
            "shortdescription": event.shortdescription,
            "city": event.city,
            "district": event.district,
            "shortaddress": event.shortaddress,
            "createdat": str(event.createdat),
            "animals": animallist
        }

        if event.status == EVENT_STATUS[EventStatus.RESOLVED.value]:
            # fetch report info
            report = db_session.query(Report).filter(Report.eventid == event.eventid).first()
            if report is not None:
                result["report"] = {
                    "shortdescription": report.shortdescription,
                    "createdat": report.createdat
                }
        elif event.status == EVENT_STATUS[EventStatus.FAILED.value]:
            # fetch warning info
            warning = db_session.query(Warning).filter(Warning.eventid == event.eventid).first()
            if warning is not None:
                result["warning"] = {
                    "warninglevel": warning.warninglevel,
                    "shortdescription": warning.shortdescription,
                    "createdat": warning.createdat
                }
        db_session.close()
        print(result)
        # return result
        return render_template("event.html", result=result, eventid=eventid)

    # POST
    # TODO: Test the responder editing functions
    elif request.method == "POST" and is_responder():
        # event info updates

        db_session = get_db_session()

        # get the event item to do some checks
        event = db_session.query(Event).filter(Event.eventid == eventid).first()
        # check the event status
        if event.status == EVENT_STATUS[EventStatus.UNRESOLVED.value]:
            # no responder has accepted this event yet

            if "status" in request.form and int(request.values["status"]) == EventStatus.ONGOING.value:
                # responder accepts event
                try:
                    # lock
                    locked_event = db_session.query(Event).with_for_update().filter(Event.eventid == eventid).first()

                    # update
                    locked_event.status = EVENT_STATUS[EventStatus.ONGOING.value]
                    locked_event.responderid = current_user.userid

                    db_session.commit()
                    print("Unresolved --> Ongoing")
                    return redirect(url_for("event", eventid=eventid))

                except exc.SQLAlchemyError as e:
                    print("error", e._message)
                    print("failed to accept event")
                    db_session.rollback()

            # responder does not wish to respond to this event
            return redirect(url_for("event", eventid=eventid))

        elif event.status == EVENT_STATUS[EventStatus.ONGOING.value] and event.responderid == current_user.userid:
            # current_user is the responder for this event
            print("Current user is the responder for this event")
            # udpate event info
            try:
                # lock event
                locked_event = db_session.query(Event).with_for_update().filter(Event.eventid == eventid).first()
                saved_event_id = locked_event.eventid
                # original channels this event maps to
                event_channels_query = select(EventCategory.channelid).filter(EventCategory.channelid == eventid)

                delete_channel_queries = [] # query channels corresponding to old values
                add_channel_queries = [] # query channels corresponding to new values

                if "status" in request.form:
                    if int(request.values["status"]) == EventStatus.UNRESOLVED.value: # 0
                        # responder reverts acceptance of the event
                        # other responders may now accept the event
                        # current responder is only allowed to change the status to unresolved
                        # no other values should be changed
                        locked_event.status = EVENT_STATUS[EventStatus.UNRESOLVED.value]
                        locked_event.responderid = None

                        db_session.commit()
                        print("Ongoing --> Unresolved")
                        return redirect(url_for("event", eventid=saved_event_id))

                    if int(request.values["status"]) == EventStatus.FALSE_ALARM.value: # 3
                        # responder can set eventstatus to false alarm and also change other event values
                        print("Ongoing --> False Alarm")
                        locked_event.status = EVENT_STATUS[EventStatus.FALSE_ALARM.value]

                    else:
                        db_session.close()
                        error = "error: invalid status update"
                        return redirect(url_for("event", eventid=saved_event_id, error=error))

                # CONTINUE TESTING FROM HERE TOMORROW
                if "eventtype" in request.form and check_eventtype(int(request.values["eventtype"])):
                    old_eventtype = locked_event.eventtype
                    # TODO: delete EventCategory entries
                    delete_channel_queries.append(select(Channel.channelid).filter(Channel.eventtype == old_eventtype))

                    # TODO: add new EventCategory entries
                    add_channel_queries.append(select(Channel.channelid).filter(Channel.eventtype == EVENT_TYPE[request["eventtype"]]))

                    locked_event.eventtype = EVENT_TYPE[request["eventtype"]]
                else:
                    db_session.close()
                    return jsonify({"error", "invalid eventtype"})

                if "shortdescription" in request.form:
                    locked_event.shortdescription = request.values["shortdescription"]

                if "city" in request.values and "district" in request.values:
                    old_district = locked_event.district

                    if check_location(request.values["city"], request.values["district"]):

                        # TODO: delete EventCategory entries
                        delete_channel_queries.append(select(Channel.channelid).filter(Channel.eventdistrict == old_district))

                        # TODO: add new EventCategory entries
                        add_channel_queries.append(select(Channel.channelid).filter(Channel.eventdistrict == DISTRICTS[request.values['district']]))

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
                            if check_animaltype(animal["type"]):
                                updated_animal_info["type"] = ANIMAL_TYPE[animal["type"]]
                                # TODO: update EventCategory entries
                                delete_channel_queries.append(select(Channel.channelid).filter(Channel.eventanimal == ANIMAL_TYPE[animal["type"]]))
                                # TODO: update EventCategory entries
                                add_channel_queries.append(select(Channel.channelid).filter(Channel.eventanimal == ANIMAL_TYPE[animal["type"]]))
                            else:
                                db_session.close()
                                return jsonify({"error": "no such animal type"})
                        if "placementid" in animal:
                            updated_animal_info["placementid"] = animal["placementid"]

                        all_animal_updates.append(updated_animal_info)

                db_session.bulk_update_mappings(Animal, all_animal_updates)

                # deal with EventCategories
                # all delete queries
                if delete_channel_queries:
                    delete_query = delete_channel_queries.pop(0)
                    if delete_channel_queries:
                        delete_query.union_all(*delete_channel_queries)
                else:
                    delete_query = None

                # all add queries
                if add_channel_queries:
                    add_query = add_channel_queries.pop(0)
                    if add_channel_queries:
                        add_query.union_all(*add_channel_queries)
                else:
                    add_query = None

                if add_query is not None:
                    add_deleted = intersect([add_query, delete_query])
                    add_new = except_([add_query, event_channels_query])

                    add_new.union(add_deleted)

                if delete_query is not None:
                    delete_channels = except_([delete_query, add_query])

                all_new_channels = [c.channelid for c in db_session.execute(add_new).all()]
                all_deleted_channels = [c.channelid for c in db_session.execute(delete_channels).all()]

                new_categories = [ EventCategory(eventid=saved_event_id, channelid=cid) for cid in all_new_channels ]

                delete(EventCategory).where(EventCategory.eventid == saved_event_id).where(EventCategory.channelid.in_(all_deleted_channels))

                db_session.bulk_save_objects(new_categories)

                db_session.execute(delete)

                db_session.commit()

                return redirect(url_for("event", eventid=eventid))

            except exc.SQLAlchemyError as e:
                print("SQLAlchemyError: ", e._message)

                db_session.rollback()

                return jsonify({"error": "error updating event info"})

    else:
        # responder should not be able to edit this event
        return redirect(url_for("event", eventid=eventid))

@app.route("/delete_event/<int:eventid>", methods=["POST"])
@login_required
def delete_event(eventid):
    db_session = get_db_session()
    try:
        event = db_session.query(Event).filter(Event.eventid == eventid).first()

        if event is not None:
            if is_responder() or (is_user() and current_user.userid == event.userid):
                db_session.delete(event)
                db_session.commit()
                db_session.close()

    except exc.SQLAlchemyError as e:
        print(e._message)
        db_session.rollback()
        db_session.close()

    if is_responder():
        return redirect(url_for('reported_events', offset=0))
    elif is_user():
        return redirect(url_for('reportrecord', offset=0))

# current users report record
@app.route('/reportrecord/<int:offset>')
@login_required
def reportrecord(offset):
    db_session = get_db_session()

    reported_events = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
        .join(Animal, Animal.eventid == Event.eventid) \
        .group_by(Event.eventid) \
        .filter(Event.userid == current_user.userid) \
        .order_by(Event.createdat.desc()) \
        .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()
    db_session.close()

    event_list = [
        {
            "eventid": event.Event.eventid,
            "eventtype": event.Event.eventtype,
            "userid": event.Event.userid,
            "responderid": event.Event.responderid,
            "status": event.Event.status,
            "shortdescription": event.Event.shortdescription,
            "city": event.Event.city,
            "district": event.Event.district,
            "createdat": str(event.Event.createdat),
            "animals": event[1].split(',')
        }
        for event in reported_events
    ]
    return render_template("reportrecord.html", event_list=event_list, offset=offset)

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
        return render_template("subscription.html", subscribed_channels=subscribed_channels, offset=offset)
        # return subscribed_channels

    # POST (add subscription)
    if 'eventdistrict' in request.form and request.values['eventdistrict'] != '':
        eventdistrict = request.values['eventdistrict']
    else:
        eventdistrict = None

    if 'eventtype' in request.form:
        if request.values['eventtype'] != '' and check_eventtype(int(request.values['eventtype'])):
            eventtype = EVENT_TYPE[int(request.values['eventtype'])]
        else:
            eventtype = None
    else:
        eventtype = None

    if 'eventanimal' in request.form:
        if request.values['eventanimal'] != '' and check_animaltype(int(request.values['eventanimal'])):
            eventanimal = ANIMAL_TYPE[int(request.values['eventanimal'])]
        else:
            eventanimal = None
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

@app.route("/delete_subscription/<int:channelid>", methods=["POST"])
@login_required
def delete_subscription(channelid):
    db_session = get_db_session()
    # delete subscription
    # TODO: we need the previous offset so we redirect back to the same page as before, now we set it to 0

    try:
        db_session.query(SubscriptionRecord) \
            .filter(SubscriptionRecord.channelid == channelid) \
            .filter(SubscriptionRecord.userid == current_user.userid) \
            .delete()

        db_session.commit()
    except exc.SQLAlchemyError as e:
        print(e._message)
        db_session.rollback()

    return redirect(url_for("subscription", offset=0))

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
        return render_template("event_results.html", eventid=eventid)

    result_type = int(request.values["result_type"])

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
            db_session.query(Event). \
                filter(Event.eventid == eventid). \
                update({"status": EVENT_STATUS[EventStatus.RESOLVED.value]})

            db_session.commit()
        except exc.SQLAlchemyError as e:
            print("Error: ", e._message)

        return redirect(url_for("event", eventid=eventid))

    elif result_type == NotificationType.WARNING.value:
        # create new warning
        warninglevel = int(request.values["warninglevel"])
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
    else:
        return jsonify({"error": "no such result type"})

    return redirect(url_for("event", eventid=eventid))

@app.route("/respond_record/<int:offset>", methods=["GET"])
def respond_record(offset):
    # only responder should be able to access this endpoint
    if not is_responder():
        return redirect(url_for("login"))

    # TODO: fetch all the events the responder responded to

@app.route("/userlist/<int:offset>", methods=["GET"])
@login_required
def user_list(offset):
    if is_admin():  
        db_session = get_db_session()
        
        all_user_query = db_session.query(UserInfo, Users) \
            .outerjoin(Users, Users.userid == UserInfo.userid) \
            .filter(Users.role == "user") \
            .order_by(UserInfo.userid) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()
        
        userlist = [
            {
                "userid": user.UserInfo.userid,
                "name": user.UserInfo.name,
                "email": user.Users.email,
                "phonenumber": user.UserInfo.phonenumber,
                "status": user.UserInfo.status
            }
            for user in all_user_query
        ]

        db_session.close()

        return render_template(".html", userlist=userlist, offset=offset)



@app.route("/userinfo/<int:userid>/<int:offset>", methods=["GET"])
@login_required
def user_info(userid, offset):
    if is_admin():

        db_session = get_db_session()

        user_query = db_session.query(UserInfo, Users) \
            .outerjoin(Users, Users.userid == UserInfo.userid) \
            .filter(Users.role == "user") \
            .filter(UserInfo.userid == userid)
        query_user = db_session.execute(user_query).all()

        user_reportrecord_query = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .group_by(Event.eventid) \
            .filter(Event.userid == userid) \
            .order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()


        db_session.close()

        user_information = [
            {
                "userid": u.UserInfo.userid,
                "name": u.UserInfo.name,
                "email": u.Users.email,
                "phonenumber": u.UserInfo.phonenumber,
                "status": u.UserInfo.status
            }
            for u in query_user
        ]

        report_record = [
            {
                "eventid": e.Event.eventid,
                "eventtype": e.Event.eventtype,
                "userid": e.Event.userid,
                "responderid": e.Event.responderid,
                "status": e.Event.status,
                "shortdescription": e.Event.shortdescription,
                "city": e.Event.city,
                "district": e.Event.district,
                "createdat": str(e.Event.createdat),
                "animals": e[1].split(',')
            }
            for e in user_reportrecord_query
        ]
        
        # todo: check frontend html and request
        return render_template(".html", user_information=user_information, report_record=report_record, userid=userid, offset=offset)


@app.route("/banuser/<int:userid>", methods=["POST"])
@login_required
def ban_user(userid):
    if is_admin(): 
        db_session = get_db_session()
   
        user = db_session.query(UserInfo).filter(UserInfo.userid == userid).with_for_update().first()
        
        if user and user.status != "banned":
            user.status = "banned"
            db_session.commit()

        db_session.close()
        return redirect(url_for("user_list", offset = 0))


@app.route("/responderlist/<int:offset>", methods=["GET"])
@login_required
def responder_list(offset):
    if is_admin(): 
        db_session = get_db_session()
       
        all_responder_query = db_session.query(ResponderInfo, Users) \
            .outerjoin(Users, Users.userid == ResponderInfo.responderid) \
            .filter(Users.role == "responder") \
            .order_by(ResponderInfo.responderid) \
            .offset(NUM_ITEMS_PER_PAGE*offset).limit(NUM_ITEMS_PER_PAGE).all()

        db_session.close()

        responderlist = [
            {
                "responderid": r.ResponderInfo.responderid,
                "respondername": r.ResponderInfo.name,
                "email": r.Users.email,
                "phonenumber": r.ResponderInfo.phonenumber,
                "address": r.ResponderInfo.address
            }
            for r in all_responder_query
        ]

        # todo: check frontend html and request
        return render_template(".html", responderlist=responderlist, offset=offset)


@app.route("/responderinfo/<int:responderid>/<int:offset>", methods=["GET"])
@login_required
def responder_info(responderid, offset):
    if is_admin():
        db_session = get_db_session()

        responder_query = db_session.query(ResponderInfo, Users) \
            .outerjoin(Users, Users.userid == ResponderInfo.responderid) \
            .filter(Users.role == "responder") \
            .filter(ResponderInfo.responderid == responderid)
        query_responder = db_session.execute(responder_query).all()

        respondrecord_query = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .group_by(Event.eventid) \
            .filter(Event.responderid == responderid) \
            .order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()
        
        db_session.close()

        responder_information = [
            {
                "responderid": r.ResponderInfo.responderid,
                "respondername": r.ResponderInfo.name,
                "email": r.Users.email,
                "phonenumber": r.ResponderInfo.phonenumber,
                "address": r.ResponderInfo.address
            }
            for r in query_responder
        ]
        
        respond_record = [
            {
                "eventid": e.Event.eventid,
                "eventtype": e.Event.eventtype,
                "userid": e.Event.userid,
                "responderid": e.Event.responderid,
                "status": e.Event.status,
                "shortdescription": e.Event.shortdescription,
                "city": e.Event.city,
                "district": e.Event.district,
                "createdat": str(e.Event.createdat),
                "animals": e[1].split(',')
            }
            for e in respondrecord_query
        ]
        
        # todo: check frontend html and request
        return render_template(".html", responder_information=responder_information, respond_record=respond_record, responderid=responderid, offset=offset)

if __name__ == '__main__':
    app.run(debug=True)