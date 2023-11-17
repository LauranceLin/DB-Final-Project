CREATE TABLE Reporter(
    ReporterId SERIAL NOT NULL,
    Password CHAR(60) NOT NULL,
    Name VARCHAR(20) NOT NULL,
    PhoneNumber CHAR(10) NOT NULL UNIQUE,
    Status VARCHAR(15) NOT NULL,
    PRIMARY KEY(ReporterId)
);

CREATE TABLE IF NOT EXISTS Admin(
    AdminId SERIAL NOT NULL,
    Password CHAR(60) NOT NULL,
    PRIMARY KEY(AdminId)
);

CREATE TABLE IF NOT EXISTS Responder(
    ResponderId SERIAL NOT NULL,
    ResponderName VARCHAR(30) NOT NULL UNIQUE,
    Password CHAR(60) NOT NULL,
    Email VARCHAR(20) NOT NULL, -- Add a constraint checking on the email format
    PhoneNumber CHAR(10) NOT NULL UNIQUE,
    ResponderType VARCHAR(30) NOT NULL,
    ResponderAddress VARCHAR(30) NOT NULL,
    PRIMARY KEY(ResponderId)
);

CREATE TABLE IF NOT EXISTS Event(
    EventId SERIAL NOT NULL,
    EventType VARCHAR(30) NOT NULL,
    ReporterId INT NOT NULL,
    ResponderId INT NOT NULL,
    Status VARCHAR(10) NOT NULL,
    ShortDescription VARCHAR(100) NOT NULL,
    City VARCHAR(10) NOT NULL,
    District VARCHAR(10) NOT NULL,
    ShortAddress VARCHAR(20) NOT NULL,
    CreatedAt TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId),
    FOREIGN KEY(ReporterId) REFERENCES Reporter(ReporterId),
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
);

CREATE TABLE IF NOT EXISTS Placement(
    PlacementId INT NOT NULL,
    Name VARCHAR(20) NOT NULL,
    Address VARCHAR(30),
    PhoneNumber CHAR(10),
    PRIMARY KEY(PlacementId)
);

CREATE TABLE IF NOT EXISTS Animal(
    AnimalId SERIAL NOT NULL,
    Type VARCHAR(10) NOT NULL,
    Description VARCHAR(20) NOT NULL,
    Placement INT,
    PRIMARY KEY(AnimalId),
    FOREIGN KEY(Placement) REFERENCES Placement(PlacementId)
);

CREATE TABLE IF NOT EXISTS EventAnimal(
    AnimalId INT NOT NULL,
    EventId INT NOT NULL,
    PRIMARY KEY(AnimalId, EventId),
    FOREIGN KEY(AnimalId) REFERENCES Animal(AnimalId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
);

CREATE TABLE IF NOT EXISTS EventImages(
    EventId INT NOT NULL,
    ImageLink TEXT NOT NULL,
    PRIMARY KEY(EventId, ImageLink),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
);

CREATE TABLE IF NOT EXISTS Channel(
    ChannelId SERIAL NOT NULL,
    EventDistrict VARCHAR(20),
    EventType VARCHAR(30),
    EventAnimalType VARCHAR(10),
    PRIMARY KEY(ChannelId)
);

CREATE TABLE IF NOT EXISTS Warning(
    EventId INT NOT NULL,
    ResponderId INT NOT NULL,
    ShortDescription VARCHAR(300) NOT NULL,
    PRIMARY KEY(EventId, ResponderId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId),
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
);

CREATE TABLE IF NOT EXISTS Report(
    EventId INT NOT NULL,
    ResponderId INT NOT NULL,
    ShortDescription VARCHAR(300) NOT NULL,
    PRIMARY KEY(EventId, ResponderId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId),
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
);

CREATE TABLE IF NOT EXISTS ResponderSubscriptionRecord(
    ChannelId INT NOT NULL,
    ResponderId INT NOT NULL,
    PRIMARY KEY(ChannelId, ResponderId),
    FOREIGN KEY(ChannelId) REFERENCES Channel(ChannelId),
    FOREIGN KEY(ResponderId) REFERENCES Responder(ResponderId)
);

CREATE TABLE IF NOT EXISTS ReporterSubscriptionRecord(
    ChannelId INT NOT NULL,
    ReporterId INT NOT NULL,
    PRIMARY KEY(ChannelId, ReporterId),
    FOREIGN KEY(ChannelId) REFERENCES Channel(ChannelId),
    FOREIGN KEY(ReporterId) REFERENCES Reporter(ReporterId)
);

CREATE TABLE IF NOT EXISTS EventCategory(
    ChannelId INT NOT NULL,
    EventId INT NOT NULL,
    PRIMARY KEY(ChannelId, EventId),
    FOREIGN KEY(ChannelId) REFERENCES Channel(ChannelId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId)
);

CREATE TABLE IF NOT EXISTS ReporterNotification(
    NotificationType VARCHAR(7) NOT NULL,
    EventId INT NOT NULL,
    NotifiedReporterId INT NOT NULL,
    NotificationTimestamp TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId, NotifiedReporterId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId),
    FOREIGN KEY(NotifiedReporterId) REFERENCES Reporter(ReporterId)
);

CREATE TABLE IF NOT EXISTS ResponderNotification(
    NotificationType VARCHAR(7) NOT NULL,
    EventId INT NOT NULL,
    NotifiedResponderId INT NOT NULL,
    NotificationTimestamp TIMESTAMP NOT NULL,
    PRIMARY KEY(EventId, NotifiedResponderId),
    FOREIGN KEY(EventId) REFERENCES Event(EventId),
    FOREIGN KEY(NotifiedResponderId) REFERENCES Responder(ResponderId)
);