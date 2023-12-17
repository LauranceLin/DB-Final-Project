from sqlalchemy import ForeignKey, Integer, String, CHAR, VARCHAR, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from flask_login import UserMixin

from schema.database import Base, engine
from schema.enums import USERS_STATUS, UsersStatus

class Users(Base, UserMixin):
    __tablename__ = "users"

    userid: Mapped[int] = mapped_column('userid', Integer, primary_key=True)
    password: Mapped[str] = mapped_column('password', CHAR(60))
    email: Mapped[str] = mapped_column('email', VARCHAR(30))
    role: Mapped[str] = mapped_column('role', VARCHAR(9)) # ROLES

    def get_id(self):
        return str(self.userid)

class UserInfo(Base):
    __tablename__ = "userinfo"

    userid: Mapped[int] = mapped_column('userid', ForeignKey('users.userid'), primary_key=True)
    name: Mapped[str] = mapped_column('name', VARCHAR(20))
    phonenumber: Mapped[str] = mapped_column('phonenumber', CHAR(10))
    status: Mapped[str] = mapped_column('status', VARCHAR(15))

    def __str__(self):
        return f"Users: userid={self.userid}, name={self.name}, phonenumber={self.phonenumber}, status={self.status}"

    def is_active(self):
        if self.status == USERS_STATUS[UsersStatus.ACTIVE]:
            return True
        else:
            return False

class ResponderInfo(Base):
    __tablename__ = "responderinfo"

    responderid: Mapped[int] = mapped_column("responderid", ForeignKey('users.userid'), primary_key=True)
    name: Mapped[str] = mapped_column("respondername", unique=True)
    phonenumber: Mapped[str] = mapped_column("phonenumber", CHAR(10))
    respondertype: Mapped[str] = mapped_column("respondertype", VARCHAR(60))
    address: Mapped[str] = mapped_column("address", VARCHAR(60))

    def __str__(self):
        return f"Responder: responderid={self.responderid}, name={self.name}, phonenumber={self.phonenumber}, respondertype={self.respondertype}, address={self.address}"

class Event(Base):
    __tablename__ = "event"

    eventid: Mapped[int] = mapped_column("eventid", Integer, primary_key=True)
    eventtype: Mapped[str] = mapped_column("eventtype", VARCHAR(30))

    # foreign key
    userid: Mapped[int] = mapped_column("userid", ForeignKey("users.userid"))
    # foreign key
    responderid: Mapped[Optional[int]] = mapped_column("responderid", ForeignKey("users.userid"))

    status: Mapped[str] = mapped_column("status", VARCHAR(20), nullable=False)
    shortdescription: Mapped[str] = mapped_column("shortdescription", VARCHAR(100), nullable=False)
    city: Mapped[str] = mapped_column("city", VARCHAR(20), nullable=False)
    district: Mapped[str] = mapped_column("district", VARCHAR(20), nullable=False)
    shortaddress: Mapped[str] = mapped_column("shortaddress", VARCHAR(30), nullable=False)
    createdat: Mapped[TIMESTAMP] = mapped_column("createdat", TIMESTAMP, nullable=False)

    def __str__(self):
        return f"Event: eventid={self.eventid}, eventtype={self.eventtype}, userid={self.userid}, responderid={self.responderid}" \
        f"status={self.status}, shortdescription={self.shortdescription}, city={self.city}" \
        f"district={self.district}, shortaddress={self.shortaddress}, createdat={self.createdat}"

class EventImages(Base):
    __tablename__ = "eventimages"
    imageid: Mapped[int] = mapped_column("imageid", primary_key=True)

    # foreign key
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey('event.eventid'))

    # TEXT datatype
    imagelink: Mapped[str] = mapped_column("imagelink", String)

# class EventCategory(Base):
#     __tablename__ = "eventcategory"
#     eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"), primary_key=True)
#     channelid: Mapped[int] = mapped_column("channelid", ForeignKey("channel.channelid"), primary_key=True)

class Placement(Base):
    __tablename__ = "placement"
    placementid: Mapped[int] = mapped_column("placementid", primary_key=True)
    name: Mapped[str] = mapped_column("name", VARCHAR(40))
    address: Mapped[str] = mapped_column("address", VARCHAR(30))
    phonenumber: Mapped[str] = mapped_column("phonenumber", CHAR(10))

class Animal(Base):
    __tablename__ = "animal"
    animalid: Mapped[int] = mapped_column("animalid", primary_key=True)
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"))
    placementid: Mapped[int] = mapped_column("placementid", ForeignKey("placement.placementid"))
    type: Mapped[str] = mapped_column("type", VARCHAR(6))
    description: Mapped[str] = mapped_column("description", VARCHAR(150))

class Channel(Base):
    __tablename__ = "channel"

    channelid: Mapped[int] = mapped_column("channelid", Integer, primary_key=True)
    eventdistrict: Mapped[str] = mapped_column("eventdistrict", VARCHAR(20))
    eventtype: Mapped[str] = mapped_column("eventtype", VARCHAR(30))
    eventanimal: Mapped[str] = mapped_column("eventanimal", VARCHAR(15))

class Warning(Base):
    __tablename__ = "warning"
    # foreign key
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"), primary_key=True)
    # foreign key
    responderid: Mapped[int] = mapped_column("responderid", ForeignKey("users.userid"), primary_key=True)

    warninglevel: Mapped[int] = mapped_column("warninglevel", Integer)
    shortdescription: Mapped[str] = mapped_column("shortdescription", VARCHAR(150))
    createdat: Mapped[TIMESTAMP] = mapped_column("createdat", TIMESTAMP)

class Report(Base):
    __tablename__ = "report"
    # foreign key
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"), primary_key=True)
    # foreign key
    responderid: Mapped[int] = mapped_column("responderid", ForeignKey("users.userid"), primary_key=True)
    shortdescription: Mapped[str] = mapped_column("shortdescription", VARCHAR(150))
    createdat: Mapped[TIMESTAMP] = mapped_column("createdat", TIMESTAMP)

class SubscriptionRecord(Base):
    __tablename__ = "subscriptionrecord"
    channelid: Mapped[int] = mapped_column("channelid", ForeignKey("channel.channelid"), primary_key=True)
    userid: Mapped[int] = mapped_column("userid", ForeignKey("users.userid"), primary_key=True)

class Notification(Base):
    __tablename__ = "notification"
    notificationtype: Mapped[str] = mapped_column("notificationtype", VARCHAR(7))
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"), primary_key=True)
    notifieduserid: Mapped[int] = mapped_column("notifieduserid", ForeignKey("users.userid"), primary_key=True)
    notificationtimestamp: Mapped[TIMESTAMP] = mapped_column("notificationtimestamp", TIMESTAMP)

# create all models
Base.metadata.create_all(engine)
