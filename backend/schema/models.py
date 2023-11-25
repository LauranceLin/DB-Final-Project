import enum
from sqlalchemy import ForeignKey, Integer, String, CHAR, VARCHAR, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from flask_login import UserMixin

from schema.database import Base, engine

class UsersStatus(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Banned"

class EventType(enum.Enum):
    ROADKILL = "Roadkill"
    ANIMAL_BLOCK_TRAFFIC = "AnimalBlockTraffic"
    STRAY_ANIMAL = "StrayAnimal"
    ANIMAL_ATTACK = "AnimalAttack"
    ANIMAL_ABUSE = "AnimalAbuse"
    DANGEROUS_WILDLIFE_SIGHTING = "DangerousWildlifeSighting"
    OTHER = "Other"

class AnimalType(enum.Enum):
    DOG = "Dog"
    CAT = "Cat"
    BIRD = "Bird"
    SNAKE = "Snake"
    DEER = "Deer"
    MONKEY = "Monkey"
    FISH = "Fish"
    BEAR = "Bear"
    OTHER = "Other"

class NotificationType(enum.Enum):
    EVENT = "Event"
    WARNING = "Warning"

class ResponderType(enum.Enum):
    VET = "Vet"
    POLICE = "Police Station"
    FIREAGENCY = "FireAgency"
    ANIMAL_PROTECTION_GROUP = "AnimalProtectionGroup"
    DISTRICT_OFFICE = "DistrictOffice"
    OTHER = "Other"

class Users(Base, UserMixin):
    __tablename__ = "users"

    userid: Mapped[int] = mapped_column('userid', primary_key=True)
    password: Mapped[str] = mapped_column('password', CHAR(60))
    name: Mapped[str] = mapped_column('name', VARCHAR(20))
    email: Mapped[str] = mapped_column('email', VARCHAR(30))
    phonenumber: Mapped[str] = mapped_column('phonenumber', CHAR(10))
    status: Mapped[UsersStatus] = mapped_column('status', VARCHAR(15))

    def __str__(self):
        return f"Users: userid={self.userid}, password={self.password}, name={self.name}, email={self.email}, phonenumber={self.phonenumber}, status={self.status}"

    def is_active(self):
        if self.status == UsersStatus.ACTIVE.value:
            return True
        else:
            return False

    # def is_authenticated(self):
    #     return True

    def get_id(self):
        return str(self.userid)

class Admin(Base):
    __tablename__ = "admin"

    adminid: Mapped[int] = mapped_column('adminid', primary_key=True)
    password: Mapped[str] = mapped_column('password')

    def __str__(self):
        return f"Admin: adminid={self.adminid}, password={self.password}"

class Responder(Base):
    __tablename__ = "responder"

    responderid: Mapped[int] = mapped_column("responderid", primary_key=True)
    name: Mapped[str] = mapped_column("respondername", unique=True)
    password: Mapped[str] = mapped_column("password", CHAR(60))
    email: Mapped[str] = mapped_column("email", VARCHAR(30))
    phonenumber: Mapped[str] = mapped_column("phonenumber", CHAR(10))
    respondertype: Mapped[str] = mapped_column("respondertype", VARCHAR(60))
    address: Mapped[str] = mapped_column("address", VARCHAR(60))

    def __str__(self):
        return f"Responder: responderid={self.responderid}, name={self.name}, password={self.password}, email={self.email}, phonenumber={self.phonenumber}, respondertype={self.respondertype}, address={self.address}"

class Event(Base):
    __tablename__ = "event"

    eventid: Mapped[int] = mapped_column("eventid", Integer, primary_key=True)
    eventtype: Mapped[EventType] = mapped_column("eventtype", VARCHAR(30))

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

class EventImages(Base):
    __tablename__ = "eventimages"
    imageid: Mapped[int] = mapped_column("imageid", primary_key=True)

    # foreign key
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey('event.eventid'))

    # TEXT datatype
    imagelink: Mapped[str] = mapped_column("imagelink", String)

class EventCategory(Base):
    __tablename__ = "eventcategory"
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"), primary_key=True)
    channelid: Mapped[int] = mapped_column("channelid", ForeignKey("channel.channelid"), primary_key=True)

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
    type: Mapped[AnimalType] = mapped_column("type", VARCHAR(6))
    description: Mapped[str] = mapped_column("description", VARCHAR(150))

class Channel(Base):
    __tablename__ = "channel"

    channelid: Mapped[int] = mapped_column("channelid", Integer, primary_key=True)
    eventdistrict: Mapped[str] = mapped_column("eventdistrict", VARCHAR(20))
    eventtype: Mapped[EventType] = mapped_column("eventtype", VARCHAR(30))
    eventanimal: Mapped[AnimalType] = mapped_column("eventanimal", VARCHAR(15))

class Warning(Base):
    __tablename__ = "warning"
    # foreign key
    eventid: Mapped[int] = mapped_column("eventId", ForeignKey("event.eventid"), primary_key=True)
    # foreign key
    responderid: Mapped[int] = mapped_column("responderid", ForeignKey("responder.responderid"), primary_key=True)

    warninglevel: Mapped[int] = mapped_column("warninglevel", Integer)
    shortdescription: Mapped[str] = mapped_column("shortdescription", VARCHAR(150))
    createdat: Mapped[TIMESTAMP] = mapped_column("createdat", TIMESTAMP)

class Report(Base):
    __tablename__ = "report"
    # foreign key
    eventid: Mapped[int] = mapped_column("eventId", ForeignKey("event.eventid"), primary_key=True)
    # foreign key
    responderid: Mapped[int] = mapped_column("responderid", ForeignKey("responder.responderid"), primary_key=True)
    shortdescription: Mapped[str] = mapped_column("shortdescription", VARCHAR(150))
    createdat: Mapped[TIMESTAMP] = mapped_column("createdat", TIMESTAMP)

class UserSubscriptionRecord(Base):
    __tablename__ = "usersubscriptionrecord"
    channelid: Mapped[int] = mapped_column("channelid", ForeignKey("channel.channelid"), primary_key=True)
    userid: Mapped[int] = mapped_column("userid", ForeignKey("users.userid"), primary_key=True)

class ResponderSubscriptionRecord(Base):
    __tablename__ = "respondersubscriptionrecord"
    channelid: Mapped[int] = mapped_column("channelid", ForeignKey("channel.channelid"), primary_key=True)
    responderid: Mapped[int] = mapped_column("responderid", ForeignKey("responder.responderid"), primary_key=True)

class UserNotification(Base):
    __tablename__ = "usernotification"
    notificationtype: Mapped[NotificationType] = mapped_column("notificationtype", VARCHAR(7))
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventid"), primary_key=True)
    notifieduserid: Mapped[int] = mapped_column("notifieduserid", ForeignKey("users.userid"), primary_key=True)
    notificationtimestamp: Mapped[TIMESTAMP] = mapped_column("notificationtimestamp", TIMESTAMP)

class ResponderNotification(Base):
    __tablename__ = "respondernotification"
    notificationtype: Mapped[NotificationType] = mapped_column("notificationtype", VARCHAR(7))
    eventid: Mapped[int] = mapped_column("eventid", ForeignKey("event.eventId"), primary_key=True)
    notifiedresponderid: Mapped[int] = mapped_column("notifiedresponderid", ForeignKey("responder.responderid"), primary_key=True)
    notificationtimestamp: Mapped[TIMESTAMP] = mapped_column("notificationtimestamp", TIMESTAMP)

# create all models
Base.metadata.create_all(engine)
