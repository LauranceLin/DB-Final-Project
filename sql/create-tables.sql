CREATE TABLE IF NOT EXISTS Users(
    UserId SERIAL NOT NULL,
    Password CHAR(60) NOT NULL,
    Name VARCHAR(20) NOT NULL,
    Email VARCHAR(30) NOT NULL,
    PhoneNumber CHAR(10) NOT NULL UNIQUE,
    Status VARCHAR(15) NOT NULL,
    PRIMARY KEY(UserId)
);

CREATE TABLE IF NOT EXISTS Admin(
    AdminId SERIAL NOT NULL,
    Password CHAR(60) NOT NULL,
    PRIMARY KEY(AdminId)
);

CREATE TABLE IF NOT EXISTS Responder(
    ResponderId SERIAL NOT NULL,
    ResponderName VARCHAR(60) NOT NULL UNIQUE,
    Password CHAR(60) NOT NULL,
    Email VARCHAR(30) NOT NULL, -- Add a constraint checking on the email format
    PhoneNumber CHAR(10) NOT NULL UNIQUE,
    ResponderType VARCHAR(30) NOT NULL,
    Address VARCHAR(30) NOT NULL,
    PRIMARY KEY(ResponderId)
);

CREATE TABLE IF NOT EXISTS Event(
    EventId SERIAL NOT NULL,
    EventType VARCHAR(30) NOT NULL,
    UserId INT NOT NULL,
    ResponderId INT,
    Status VARCHAR(20) NOT NULL,
    ShortDescription VARCHAR(100) NOT NULL,
    City VARCHAR(20) NOT NULL,
    District VARCHAR(20) NOT NULL,
    ShortAddress VARCHAR(30) NOT NULL,
    CreatedAt TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId),
    FOREIGN KEY(UserId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Placement(
    PlacementId INT NOT NULL,
    Name VARCHAR(40) NOT NULL,
    Address VARCHAR(30),
    PhoneNumber CHAR(10),
    PRIMARY KEY(PlacementId)
);

CREATE TABLE IF NOT EXISTS Animal(
    AnimalId SERIAL NOT NULL,
    EventId INT NOT NULL,
    Type VARCHAR(6) NOT NULL,
    Description VARCHAR(150),
    PlacementId INT,
    PRIMARY KEY(AnimalId),
    FOREIGN KEY(PlacementId) REFERENCES Placement(PlacementId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS EventImages(
    ImageId SERIAL NOT NULL,
    EventId INT NOT NULL,
    ImageLink TEXT NOT NULL,
    PRIMARY KEY(ImageId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Channel(
    ChannelId SERIAL NOT NULL,
    EventDistrict VARCHAR(20),
    EventType VARCHAR(30),
    EventAnimal VARCHAR(15),
    PRIMARY KEY(ChannelId)
);

CREATE TABLE IF NOT EXISTS Warning(
    EventId INT NOT NULL,
    ResponderId INT NOT NULL,
    WarningLevel INT NOT NULL,
    ShortDescription VARCHAR(150) NOT NULL,
    CreatedAt TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId, ResponderId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS Report(
    EventId INT NOT NULL,
    ResponderId INT NOT NULL,
    ShortDescription VARCHAR(150),
    CreatedAt TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId, ResponderId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS ResponderSubscriptionRecord(
    ChannelId INT NOT NULL,
    ResponderId INT NOT NULL,
    PRIMARY KEY(ChannelId, ResponderId),
    FOREIGN KEY(ChannelId) REFERENCES Channel(ChannelId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS UserSubscriptionRecord(
    ChannelId INT NOT NULL,
    UserId INT NOT NULL,
    PRIMARY KEY(ChannelId, UserId),
    FOREIGN KEY(ChannelId) REFERENCES Channel(ChannelId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(UserId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS EventCategory(
    ChannelId INT NOT NULL,
    EventId INT NOT NULL,
    PRIMARY KEY(ChannelId, EventId),
    FOREIGN KEY(ChannelId) REFERENCES Channel(ChannelId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS UserNotification(
    NotificationType VARCHAR(7) NOT NULL,
    EventId INT NOT NULL,
    NotifiedUserId INT NOT NULL,
    NotificationTimestamp TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId, NotifiedUserId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(NotifiedUserId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS ResponderNotification(
    NotificationType VARCHAR(7) NOT NULL,
    EventId INT NOT NULL,
    NotifiedResponderId INT NOT NULL,
    NotificationTimestamp TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId, NotifiedResponderId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(NotifiedResponderId) REFERENCES Responder(ResponderId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);