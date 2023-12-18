from flask import Flask, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from schema.database import get_db_session
from schema.models import *
from schema.enums import *

NUM_ITEMS_PER_PAGE = 10

def respond_record(offset):
    
    db_session = get_db_session()

    responded_events = db_session.query(Event) \
        .filter(Event.responderid == current_user.responderid) \
        .order_by(Event.createdat.desc()) \
        .offset(offset*NUM_ITEMS_PER_PAGE).limit(NUM_ITEMS_PER_PAGE)

    db_session.close()

    event_list = []
    for event in responded_events:
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

    return render_template("../frontend/respond_record.html", event_list=event_list)

