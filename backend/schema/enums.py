import enum

ROLE = ["user", "responder", "admin"]

class UsersStatus(enum.Enum):
    ACTIVE = 0
    BANNED = 1
    USERS_STATUS_LEN = 2

USERS_STATUS = ["Active", "Banned"]

class EventType(enum.Enum):
    ROADKILL = 0
    ANIMAL_BLOCK_TRAFFIC = 1
    STRAY_ANIMAL = 2
    ANIMAL_ATTACK = 3
    ANIMAL_ABUSE = 4
    DANGEROUS_WILDLIFE_SIGHTING = 5
    OTHER = 6
    EVENT_TYPE_LEN = 7

EVENT_TYPE = [
    "Roadkill", "AnimalBlockingTraffic", "StrayAnimal", "AnimalAttack", "AnimalAbuse", "DangerousWildlifeSighting", "Other"
]

class AnimalType(enum.Enum):
    DOG = 0
    CAT = 1
    BIRD = 2
    SNAKE = 3
    DEER = 4
    MONKEY = 5
    FISH = 6
    BEAR = 7
    OTHER = 8
    ANIMAL_TYPE_LEN = 9

ANIMAL_TYPE = [
    "Dog", "Cat", "Bird", "Snake", "Deer", "Monkey", "Fish", "Bear", "Other"
]

class NotificationType(enum.Enum):
    EVENT = 0
    WARNING = 1
    NOTIFICATION_TYPE_LEN = 2

NOTIFICATION_TYPE = [
    "Event", "Warning"
]

class ResponderType(enum.Enum):
    VET = 0
    POLICE = 1
    FIREAGENCY = 2
    ANIMAL_PROTECTION_GROUP = 3
    DISTRICT_OFFICE = 4
    OTHER = 5
    RESPONDER_TYPE_LEN = 6

RESPONDER_TYPE = [
    "Vet", "PoliceStation", "FireAgency", "AnimalProtectionGroup", "DistrictOffice", "Other"
]

class EventStatus(enum.Enum):
    UNRESOLVED = 0
    RESOLVED = 1
    ONGOING = 2
    FALSE_ALARM = 3
    FAILED = 4
    DELETED = 5
    EVENT_STATUS_LEN = 5

EVENT_STATUS = [
    "Unresolved", "Resolved", "Ongoing", "FalseAlarm", "Failed", "Deleted"
]

class ResultType(enum.Enum):
    REPORT = 0
    WARNING = 1
    RESULT_TYPE_LEN = 2

RESULT_TYPE = [
    "Report", "Warning"
]

class City(enum.Enum):
    TAIPEI = 0
    NEW_TAIPEI = 1
    CITY_LEN = 2

CITIES = ['台北市', '新北市']
DISTRICTS = [
    [
        '中正區', '大同區', '中山區', '松山區', '大安區', '萬華區', '信義區', '士林區', '北投區', '內湖區', '南港區',
        '文山區'
    ],
    [
        '萬里區', '金山區', '板橋區', '汐止區', '深坑區', '石碇區', '瑞芳區', '平溪區', '雙溪區', '貢寮區', '新店區',
        '坪林區', '烏來區', '永和區', '中和區', '土城區', '三峽區', '樹林區', '鶯歌區', '三重區', '新莊區', '泰山區',
        '林口區', '蘆洲區', '五股區', '八里區', '淡水區', '三芝區', '石門區'
    ]
]

WARNING_LEVEL_MAX = 10
WARNING_LEVEL_MIN = 0

def check_warninglevel(level: int):
    if level < WARNING_LEVEL_MIN or level > WARNING_LEVEL_MAX:
        return False
    return True

def check_resulttype(type: int):
    if type < 0 or type >= ResultType.RESULT_TYPE_LEN.value:
        return False
    return True

def get_notification_index(type: str):
    if type == 'event':
        return 0
    elif type == 'warning':
        return 1
    else:
        return -1

def check_notificationtype(type: str):
    if type == 'event' or type == 'warning' or type == 'both':
        return True
    return False

def check_eventstatus(status: int):
    if status < 0 or status >= EventStatus.EVENT_STATUS_LEN.value:
        return False
    return True

# error checking functions
def check_eventtype(eventtype: int):
    if eventtype < 0 or eventtype >= EventType.EVENT_TYPE_LEN.value:
        return False
    return True

def check_location(city: int, district: int):
    if city < 0 or city >= City.CITY_LEN.value:
        return False
    if district < 0 or district >= len(DISTRICTS[city]):
        return False
    return True

def check_animaltype(animaltype: int):
    if animaltype < 0 or animaltype >= AnimalType.ANIMAL_TYPE_LEN.value:
        return False
    return True