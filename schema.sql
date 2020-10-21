CREATE TABLE profiles (
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    username TEXT NOT NULL,
    name TEXT NOT NULL,
    bio TEXT,
    interest TEXT,
    picture TEXT
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    profile_id INTEGER
);

CREATE INDEX idx_email ON users (email);

CREATE TABLE visited (
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    self INTEGER NOT NULL,
    visitor INTEGER NOT NULL
);
CREATE INDEX idx_self ON visited (self);
