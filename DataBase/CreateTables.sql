CREATE TABLE personnal_infos (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    password TEXT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('admin', 'user','employee')) DEFAULT 'user'
);


CREATE TABLE product (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    publish_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) CHECK (status IN ('available', 'borrowed', 'unavailable')) DEFAULT 'available',
    owner_id INT REFERENCES personnal_infos(id) ON DELETE SET NULL
);
