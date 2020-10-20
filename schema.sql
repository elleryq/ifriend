CREATE TABLE users (
    id INTEGER PRIMARY KEY ASC AUTOINCREMENT,
    email TEXT NOT NULL,
    password TEXT NOT NULL
);

CREATE INDEX idx_email ON users (email);
