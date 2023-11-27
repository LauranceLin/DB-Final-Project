import enum

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
    "Roadkill", "AnimalBlockTraffic", "StrayAnimal", "AnimalAttack", "AnimalAbuse", "DangerousWildlifeSighting", "Other"
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

EVENT_STATUS = [
    "Unresolved", "Resolved", "Ongoing", "FalseAlarm", "Failed"
]

class City(enum.Enum):
    TAIPEI = 0
    NEW_TAIPEI = 1
    CITY_LEN = 2

CITIES = [
    "Taipei", "New Taipei"
]

DISTRICTS = [
    [
        'Songshan', 'Xinyi', 'Daan', 'Zhongshan', 'Zhongzheng', 'Datong', 'Wanhua', 'Wenshan', 'Nangang', 'Neihu', 'Shilin', 'Beitou'
    ],
    [
        'Banqiao', 'Sanchong', 'Zhonghe', 'Yonghe', 'Xinzhuang', 'Xindian', 'Tucheng', 'Luzhou', 'Shulin', 'Xizhi', 'Yingge', 'Sanxia', 'Danshui', 'Ruifang', 'Wugu', 'Taishan', 'Linkou', 'Shenkeng', 'Shiding', 'Pinglin', 'Sanzhi', 'Shimen', 'Bali', 'Pingxi', 'Shuangxi', 'Gongliao', 'Jinshan', 'Wanli', 'Wulai'
    ]
]