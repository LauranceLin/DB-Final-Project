from flask import Flask, request, redirect, url_for, jsonify, render_template, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from schema.database import get_db_session
from schema.models import *
import bcrypt
import datetime
from schema.enums import *
from sqlalchemy import exc, select, delete, union
from celery import Celery
from werkzeug.utils import secure_filename
from sqlalchemy.sql.elements import literal_column
from sqlalchemy import func
import os
from PIL import Image
import uuid

app = Flask(__name__, template_folder='../frontend', static_url_path='/', static_folder='../frontend')
app.secret_key = 'NnSELOhwoPri1o-RZR3d1A'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'
app.config['UPLOAD_FOLDER'] = '../frontend/uploads'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png']

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
    eventanimal = notification_info["eventanimals"]
    eventtype = notification_info["eventtype"]
    eventdistrict = notification_info["eventdistrict"]

    db_session = get_db_session();
    try:
        note_timestamp = datetime.datetime.now()

        # first select all that match eventtype and eventdistrict
        subscriber_query = select(SubscriptionRecord.userid) \
                        .join(Channel, Channel.channelid == SubscriptionRecord.channelid) \
                        .filter((Channel.eventtype == eventtype) | (Channel.eventdistrict == eventdistrict)) \
                        .distinct()

        # then match all animal types and union the queries
        for animal in eventanimal:
            new_animal_query = select(SubscriptionRecord.userid) \
                        .join(Channel, SubscriptionRecord.channelid == Channel.channelid) \
                        .filter(Channel.eventanimal == animal) \
                        .distinct()
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

@app.route("/")

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
        if is_user() or is_responder():
            print("User logged in!")
            return redirect(url_for("notifications", offset=0))
        ##### admin redirect #####
        elif is_admin():
            print("Admin logged in!")
            return redirect(url_for("admin_events", offset=0))
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
        db_session.close()
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
        db_session.close()
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
    # print(placement_list)
    db_session.close()
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
            db_session.close()
            return jsonify({"error": "wrong number of animals"})

        eventanimals = [{
            'animaltype': int(request.form.getlist('animaltype')[i]),
            'animaldescription': request.form.getlist('animaldescription')[i]
        } for i in range(num_animals)]

        print(eventanimals)

        # error checking for event
        if len(shortaddress) > 30:
            db_session.close()
            return jsonify({"error": "Short address too long"})

        if len(shortdescription) > 100:
            db_session.close()
            return jsonify({"error": "Short description too long"})

        try:
            eventtype = int(eventtype)
            if not check_eventtype(eventtype=eventtype):
                raise
        except:
            db_session.close()
            return jsonify({"error": "Eventtype doesn't exist"})

        try:
            city = int(city)
            district = int(district)
            if not check_location(city=city, district=district):
                raise
        except:
            db_session.close()
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
            db_session.close()
            return jsonify({"error": "animal data error"})


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

            # event images
            eventimages = []
            if 'eventimages' in request.files:
                files = request.files.getlist('eventimages')

                if len(files) > 3:
                    db_session.rollback()
                    db_session.close()
                    return jsonify({"error": "at most 3 images allowed"})

                for file in files:
                    if file.filename == '':
                        continue
                    # check extension
                    extension = os.path.splitext(secure_filename(file.filename))[1]
                    new_filename = str(uuid.uuid4()) + extension

                    if extension not in app.config['UPLOAD_EXTENSIONS']:
                        print("wrong extension, is not an image")
                        db_session.rollback()
                        db_session.close()
                        return abort(400)

                    path_name = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

                    # resize images
                    image_width = 400
                    img = Image.open(path_name)
                    ratio = float(img.size[0] / image_width)
                    image_height = int(float(img.size[1] / ratio))
                    print("resized image: ", image_width, image_height)
                    img = img.resize((image_width, image_height))
                    img.save(path_name)

                    image_link = app.config['UPLOAD_FOLDER'].split('/')[2] + '/' + new_filename
                    print(image_link)
                    eventimages.append(EventImages(eventid=new_event.eventid, imagelink=image_link))

            if eventimages != []:
                db_session.bulk_save_objects(eventimages)

            print(f"Created new event with id: {new_event.eventid}")

            # save info for notification creation
            notification_info["eventid"] = new_event.eventid
            notification_info["notificationtype"] = NOTIFICATION_TYPE[NotificationType.EVENT.value]
            notification_info["eventdistrict"] = new_event.district
            notification_info["eventtype"] = new_event.eventtype

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
                animal_types.add(ANIMAL_TYPE[animal['animaltype']])

            notification_info['eventanimals'] = list(animal_types)

            db_session.commit()

        except exc.SQLAlchemyError as e:
            print(e._message)
            db_session.rollback()
            db_session.close()
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

    print("filter params: ", eventtype, eventdistrict, animaltype)

    db_session = get_db_session()
    # TODO: Query most recent events
    if eventtype is None and eventdistrict is None and animaltype is None:
        results = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .group_by(Event.eventid).order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()

        db_session.close()
    else:
        # filtered by event districts
        filtered_events = select(Event.eventid).join(Animal, Animal.eventid == Event.eventid)

        if eventdistrict is not None:
            filtered_events = filtered_events.filter(Event.district == eventdistrict)

        if eventtype is not None:
            filtered_events = filtered_events.filter(Event.eventtype == eventtype)

        if animaltype is not None:
            filtered_events = filtered_events.filter(Animal.type == animaltype)

        filtered_events = filtered_events.group_by(Event.eventid) \
            .order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE)

        print(filtered_events)

        matched_events = [e[0] for e in db_session.execute(filtered_events).all()]

        print("ALL MATCHED EVENTS: ", len(matched_events))

        results = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .filter(Event.eventid.in_(matched_events)) \
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

        query_eventimages = select(EventImages.imagelink).filter(EventImages.eventid == eventid)
        imagelinks = [img.imagelink for img in db_session.execute(query_eventimages).all()]

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
            "animals": animallist,
        }

        if imagelinks != []:
            result["imagelinks"] = imagelinks

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

            # responder accepts event
            try:
                # lock
                locked_event = db_session.query(Event).with_for_update().filter(Event.eventid == eventid).first()

                # update
                locked_event.status = EVENT_STATUS[EventStatus.ONGOING.value]
                locked_event.responderid = current_user.userid

                db_session.commit()
                db_session.close()

                print("Unresolved --> Ongoing")
                return redirect(url_for("event", eventid=eventid))

            except exc.SQLAlchemyError as e:
                print("error", e._message)
                print("failed to accept event")
                db_session.rollback()
                db_session.close()

            # responder does not wish to respond to this event
            return redirect(url_for("event", eventid=eventid))

        elif event.status == EVENT_STATUS[EventStatus.ONGOING.value] and event.responderid == current_user.userid:
            # current_user is the responder for this event
            print("Current user is the responder for this event")
            new_city = int(request.values["city"])
            new_district = int(request.values["district"])
            new_status = int(request.values["status"])
            new_shortaddress = request.values["shortaddress"]
            new_eventtype = int(request.values["eventtype"])

            if not check_location(new_city, new_district) or not check_eventtype(new_eventtype):
                db_session.close()
                return jsonify({"error": "error with data fields"})

            # new animals information
            new_animaltypes = request.form.getlist("animaltype")
            new_animaldescriptions = request.form.getlist("animaldescription")
            new_placements = request.form.getlist("placement")

            # udpate event info
            try:
                # lock event
                locked_event = db_session.query(Event).with_for_update().filter(Event.eventid == eventid).first()
                saved_event_id = locked_event.eventid

                # status
                if new_status == EventStatus.ONGOING.value:
                    pass
                elif new_status == EventStatus.UNRESOLVED.value: # 0
                    # responder reverts acceptance of the event
                    # other responders may now accept the event
                    # current responder is only allowed to change the status to unresolved
                    # no other values should be changed
                    locked_event.status = EVENT_STATUS[EventStatus.UNRESOLVED.value]
                    locked_event.responderid = None

                    db_session.commit()
                    db_session.close()
                    print("Ongoing --> Unresolved")
                    return redirect(url_for("event", eventid=saved_event_id))

                elif new_status == EventStatus.FALSE_ALARM.value: # 3
                    # responder can set eventstatus to false alarm and also change other event values
                    print("Ongoing --> False Alarm")
                    locked_event.status = EVENT_STATUS[EventStatus.FALSE_ALARM.value]
                else:
                    # error: no other event status types are allowed
                    db_session.rollback()
                    db_session.close()
                    return redirect(url_for("event", eventid=saved_event_id))

                # eventtype
                if locked_event.eventtype != EVENT_TYPE[new_eventtype]:
                    locked_event.eventtype = EVENT_TYPE[new_eventtype]

                # short description
                locked_event.shortdescription = request.values["shortdescription"]

                # location
                if CITIES[new_city] != locked_event.city or DISTRICTS[new_city][new_district] != locked_event.district:
                    locked_event.city = CITIES[new_city]
                    locked_event.district = DISTRICTS[new_city][new_district]

                # shortaddress
                locked_event.shortaddress = new_shortaddress

                # animal updates
                # animals do not need to be locked
                # animals will not be updated if their corresponding event has not been locked already
                all_animal_updates = []

                animalids = [int(id) for id in request.form.getlist("animalid")]
                new_animaltypes = [int(type) for type in request.form.getlist("animaltype")]
                new_animaldescriptions = request.form.getlist("animaldescription")
                new_placements = [int(placement) for placement in request.form.getlist("placement")]

                for i in range(0, len(new_animaltypes)):
                    if check_animaltype(new_animaltypes[i]):
                        all_animal_updates.append(
                            {
                                "animalid": animalids[i],
                                "type": ANIMAL_TYPE[new_animaltypes[i]],
                                "description": new_animaldescriptions[i],
                                "placementid": new_placements[i]
                            }
                        )
                    else:
                        db_session.close()
                        return jsonify({"error": "error in animal type"})

                db_session.bulk_update_mappings(Animal, all_animal_updates)

                db_session.commit()

                db_session.close()

                return redirect(url_for("event", eventid=eventid))

            except exc.SQLAlchemyError as e:
                print("SQLAlchemyError: ", e._message)

                db_session.rollback()

                return jsonify({"error": "error updating event info"})

    else:
        # others should not be able to edit this event
        return redirect(url_for("event", eventid=eventid))


@app.route("/delete_event/<int:eventid>", methods=["POST"])
@login_required
def delete_event(eventid):
    db_session = get_db_session()
    try:
        event = db_session.query(Event).filter(Event.eventid == eventid).first()

        if event is not None:
            if is_responder() or (is_user() and current_user.userid == event.userid) or is_admin():
                locked_event = db_session.query(Event).filter(Event.eventid == eventid).with_for_update().first()
                locked_event.status = EVENT_STATUS[EventStatus.DELETED.value]
                db_session.commit()
                db_session.close()
        else:
            db_session.close()
    except exc.SQLAlchemyError as e:
        print(e._message)
        db_session.rollback()
        db_session.close()

    if is_responder():
        return redirect(url_for('reported_events', offset=0))
    elif is_user():
        return redirect(url_for('reportrecord', offset=0))
    elif is_admin():
        return redirect(url_for('admin_events', offset=0))

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
                "channelid": c.channelid,
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

    db_session.close()
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
            db_session.rollback()

        db_session.close()
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

            # populate notification_info values
            notification_info["notificationtype"] = NOTIFICATION_TYPE[NotificationType.WARNING.value]
            notification_info["eventid"] = eventid

            animal_types = [animal.Animal.type for animal in db_session.query(Animal.type).filter(Animal.eventid == eventid).distinct().all()]
            print(animal_types)
            notification_info['eventanimals'] = animal_types

            event = db_session.query(Event.district, Event.eventtype).filter(Event.eventid == eventid).first()
            notification_info["eventtype"] = event.Event.eventtype
            notification_info["eventdistrict"] = event.Event.eventdistrict

            db_session.add(new_warning)

            # update the event status
            db_session.query(Event). \
                        filter(Event.eventid == eventid). \
                        update({"status": EVENT_STATUS[EventStatus.FAILED.value]})

            db_session.commit()
        except exc.SQLAlchemyError as e:
            print("Error: ", e._message)
            db_session.rollback()

        db_session.close()

        # TODO: create notifications
        create_notifications.delay(notification_info)
    else:
        return jsonify({"error": "no such result type"})

    return redirect(url_for("event", eventid=eventid))

@app.route("/respond_record/<int:offset>", methods=["GET"])
def respond_record(offset):
    # only responder should be able to access this endpoint
    if not is_responder():
        return redirect(url_for("login"))
    db_session = get_db_session()

    respond_record = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
        .join(Animal, Animal.eventid == Event.eventid) \
        .group_by(Event.eventid) \
        .filter(Event.responderid == current_user.userid) \
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
        for event in respond_record
    ]

    print(event_list)

    return render_template("respond_record.html", event_list=event_list, offset=offset)

# admin view all events
@app.route("/admin_events/<int:offset>", methods=["GET"])
@login_required
def admin_events(offset):
    if is_admin():
        # eventtype
        if 'eventtype' in request.args:
            eventtype = int(request.args.get('eventtype'))
            if check_eventtype(eventtype):
                eventtype = EVENT_TYPE[eventtype]
            else:
                return jsonify({"error": "no such eventtype"})
        else:
            eventtype = None

        # eventdistrict
        if 'eventdistrict' in request.args:
            eventdistrict = request.args.get('eventdistrict')
        else:
            eventdistrict = None

        # animaltype
        if 'animaltype' in request.args:
            animaltype = int(request.args.get('animaltype'))
            if check_animaltype(animaltype):
                animaltype = ANIMAL_TYPE[animaltype]
            else:
                return jsonify({"error": "no such animal type"})
        else:
            animaltype = None

        print("filter params: ", eventtype, eventdistrict, animaltype)

        db_session = get_db_session()


        if eventtype is None and eventdistrict is None and animaltype is None:
            # no filters
            all_event_query = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
                .join(Animal, Animal.eventid == Event.eventid) \
                .group_by(Event.eventid) \
                .order_by(Event.createdat.desc()) \
                .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()

            db_session.close()
        else:
            # with filters
            filtered_events = select(Event.eventid).join(Animal, Animal.eventid == Event.eventid)

            if eventdistrict is not None:
                filtered_events = filtered_events.filter(Event.district == eventdistrict)

            if eventtype is not None:
                filtered_events = filtered_events.filter(Event.eventtype == eventtype)

            if animaltype is not None:
                filtered_events = filtered_events.filter(Animal.type == animaltype)

            filtered_events = filtered_events.group_by(Event.eventid) \
                .order_by(Event.createdat.desc()) \
                .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE)

            print(filtered_events)

            matched_events = [e[0] for e in db_session.execute(filtered_events).all()]

            print("ALL MATCHED EVENTS: ", len(matched_events))

            all_event_query = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
                .join(Animal, Animal.eventid == Event.eventid) \
                .filter(Event.eventid.in_(matched_events)) \
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
            for event in all_event_query
        ]

        db_session.close()
        return render_template("admin_events.html", event_list=event_list, offset=offset)


# admin view all users
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

        return render_template("userlist.html", userlist=userlist, offset=offset)



@app.route("/viewuserinfo/<int:userid>/<int:offset>", methods=["GET"])
@login_required
def viewuserinfo(userid, offset):
    if is_admin():

        db_session = get_db_session()

        user_query = db_session.query(UserInfo, Users) \
            .outerjoin(Users, Users.userid == UserInfo.userid) \
            .filter(Users.role == "user") \
            .filter(UserInfo.userid == userid)
        query_user = db_session.execute(user_query).first()
        user_info = query_user.UserInfo
        user_email = query_user.Users

        user_reportrecord_query = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .group_by(Event.eventid) \
            .filter(Event.userid == userid) \
            .order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()


        db_session.close()

        user_information = {
                "userid": user_info.userid,
                "name": user_info.name,
                "email": user_email.email,
                "phonenumber": user_info.phonenumber,
                "status": user_info.status
                }

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
        return render_template("viewuserinfo.html", user_information=user_information, report_record=report_record, userid=userid, offset=offset)


@app.route("/banuser/<int:userid>", methods=["POST"])
@login_required
def ban_user(userid):
    if is_admin():
        db_session = get_db_session()

        user = db_session.query(UserInfo).filter(UserInfo.userid == userid).with_for_update().first()
        try:
            if user and user.status != "banned":
                user.status = "banned"
                db_session.commit()
        except exc.SQLAlchemyError as e:
            db_session.rollback()

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
        return render_template("responderlist.html", responderlist=responderlist, offset=offset)


@app.route("/responderinfo/<int:responderid>/<int:offset>", methods=["GET"])
@login_required
def responderinfo(responderid, offset):
    if is_admin():
        db_session = get_db_session()

        responder_query = db_session.query(ResponderInfo, Users) \
            .outerjoin(Users, Users.userid == ResponderInfo.responderid) \
            .filter(Users.role == "responder") \
            .filter(ResponderInfo.responderid == responderid)
        query_responder = db_session.execute(responder_query).first()
        responder_info = query_responder.ResponderInfo
        responder_email = query_responder.Users

        respondrecord_query = db_session.query(Event, func.string_agg(Animal.type, literal_column("','"))) \
            .join(Animal, Animal.eventid == Event.eventid) \
            .group_by(Event.eventid) \
            .filter(Event.responderid == responderid) \
            .order_by(Event.createdat.desc()) \
            .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE).all()

        db_session.close()

        responder_information = {
                "responderid": responder_info.responderid,
                "respondername": responder_info.name,
                "email": responder_email.email,
                "phonenumber": responder_info.phonenumber,
                "address": responder_info.address
            }


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
        return render_template("responderinfo.html", responder_information=responder_information, respond_record=respond_record, responderid=responderid, offset=offset)

@app.route("/admin_view_event/<int:eventid>", methods=["GET", "POST"])
@login_required
def admin_view_event(eventid):
    if request.method == "GET" and is_admin():
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
        return render_template("admin_view_event.html", result=result, eventid=eventid)
    else:
        return redirect(url_for("admin_events", eventid=eventid))



if __name__ == '__main__':
    app.run(debug=True)