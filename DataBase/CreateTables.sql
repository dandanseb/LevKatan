--- LOGIN INFORMATIONS ---

CREATE TABLE personnal_infos (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
	email VARCHAR(100) UNIQUE NOT NULL,
    passwd TEXT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('admin', 'user','employee')) DEFAULT 'user'
);

--- PRODUCTS INFORTMATIONS ---

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    publish_date DATE DEFAULT CURRENT_DATE,
    last_status_change TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('available', 'borrowed', 'unavailable', 'confirmation_pending')) DEFAULT 'available',
    owner_id INT REFERENCES personnal_infos(id) ON DELETE SET NULL,
    description VARCHAR(200)

);

CREATE INDEX idx_product_name ON products (product_name);

--------------------------------------------
