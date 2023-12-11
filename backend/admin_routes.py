from flask import Flask, jsonify, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import exc, select, union, except_, intersect, delete
from schema.database import get_db_session
from schema.models import *
from schema.enums import *

def user_list():

    db_session = get_db_session()

    query_user = select(Userinfo, Users.email)\
        .outerjoin(Users, Users.userid == Userinfo.userid) \
        .filter(Users.role == "user" ) \
        .order_by(Userinfo.userid)
    
    db_session.close()

    userlist = []
    for user in query_user:
        u = {
            "userid": userinfo.userid,
            "name": userinfo.name,
            "email": users.email,
            "phonenumber": userinfo.phonenumber,
            "status": userinfo.status
            }
        userlist.append(u)

    return render_template("../frontend/....", userlist=userlist)
    
    
def responder_list():

    db_session = get_db_session()

    query_responder = select(Responderinfo, Users.email)\
        .outerjoin(Users, Users.userid == Responderinfo.userid) \
        .filter(Users.role == "responder" ) \
        .order_by(Responderinfo.responderid)
    
    db_session.close()

    responderlist = []
    for responder in query_responder:
        r = {
            "responderid": responderinfo.responderid,
            "respondername": responderinfo.name,
            "email": users.email,
            "phonenumber": responderinfo.phonenumber,
            "address": responderinfo.address
            }
        responderlist.append(r)

    return render_template("../frontend/....", responderlist=responderlist)



