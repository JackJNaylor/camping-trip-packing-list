DROP TABLE IF EXISTS users;

CREATE TABLE users (
    userId INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL
);

DROP TABLE IF EXISTS packingItems;

CREATE TABLE packingItems (
    itemId INTEGER PRIMARY KEY AUTOINCREMENT,
    itemName TEXT NOT NULL,
    weather TEXT NOT NULL,
    required BOOLEAN,
    maxTemp INTEGER NOT NULL,
    minTemp INTEGER NOT NULL,
    description TEXT,
    FOREIGN KEY(userId) REFERENCES users(userId)
);

DROP TABLE IF EXISTS packingLists;

CREATE TABLE packingLists (
    listId INTEGER PRIMARY KEY AUTOINCREMENT,
    dateOrdered NOT NULL DEFAULT CURRENT_DATE,
    status TEXT NOT NULL DEFAULT 'ORDER RECEIVED',
    quantity TEXT NOT NULL,
    orderTotal TEXT NOT NULL,
    imageId INTEGER NOT NULL,
    buyerId TEXT NOT NULL,
    sellerId TEXT NOT NULL,
    FOREIGN KEY (imageId) REFERENCES images(imageId),
    FOREIGN KEY (buyerId) REFERENCES users(userId),
    FOREIGN KEY (sellerId) REFERENCES users(userId)
);