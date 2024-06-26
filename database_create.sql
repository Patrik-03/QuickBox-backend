CREATE TABLE accounts (
    id SERIAL PRIMARY KEY UNIQUE,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    longitude FLOAT,
    latitude FLOAT
);
CREATE TABLE deliveries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts(id),
    from_id INTEGER REFERENCES accounts(id),
    sent_time TIMESTAMP,
    delivery_time TIMESTAMP,
    delivery_type VARCHAR(50),
    status VARCHAR(50),
    note TEXT,
    latitude FLOAT,
    longitude FLOAT
);
CREATE TABLE history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES accounts(id),
    from_id INTEGER REFERENCES accounts(id),
    sent_time TIMESTAMP,
    delivery_time TIMESTAMP,
    delivery_type VARCHAR(50),
    status VARCHAR(50),
    note TEXT
);
