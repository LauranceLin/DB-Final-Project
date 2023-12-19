CREATE TABLE IF NOT EXISTS Users(
    UserId SERIAL NOT NULL,
    Password CHAR(60) NOT NULL,
    Email VARCHAR(30) NOT NULL,
    Role VARCHAR(20) NOT NULL,
    PRIMARY KEY(UserId)
);

CREATE TABLE IF NOT EXISTS UserInfo(
    UserId SERIAL NOT NULL,
    Name VARCHAR(20) NOT NULL,
    PhoneNumber CHAR(10) NOT NULL,
    Status VARCHAR(15) NOT NULL,
    PRIMARY KEY(UserId),
    FOREIGN KEY(UserId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS ResponderInfo(
    ResponderId SERIAL NOT NULL,
    ResponderName VARCHAR(60) NOT NULL UNIQUE,
    PhoneNumber CHAR(10) NOT NULL UNIQUE,
    ResponderType VARCHAR(60) NOT NULL,
    Address VARCHAR(60) NOT NULL,
    PRIMARY KEY(ResponderId),
    FOREIGN KEY(ResponderId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
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
    FOREIGN KEY(ResponderId) REFERENCES Users(UserId)
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
    FOREIGN KEY(ResponderId) REFERENCES Users(UserId)
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
    FOREIGN KEY(ResponderId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS SubscriptionRecord(
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

CREATE TABLE IF NOT EXISTS Notification(
    NotificationType VARCHAR(7) NOT NULL,
    EventId INT NOT NULL,
    NotifiedUserId INT NOT NULL,
    NotificationTimestamp TIMESTAMP NOT NULL,
    PRIMARY KEY(NotificationType, EventId, NotifiedUserId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(NotifiedUserId) REFERENCES Users(UserId)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);