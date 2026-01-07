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

------- PRODUCTS INFORTMATIONS -------

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    publish_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(20) CHECK (status IN ('available', 'borrowed', 'unavailable', 'confirmation_pending')) DEFAULT 'available',
    donator_username VARCHAR(100),
    description VARCHAR(200)

);

CREATE INDEX idx_product_name ON products (product_name);

----------------REQUESTS INFORMATIONS  ---------------------

CREATE TABLE borrow_requests (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES personnal_infos(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    request_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
	returned_date DATE,
    status VARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected', 'returned', 'confirmation_pending')) DEFAULT 'pending', 
);

CREATE INDEX idx_borrow_request_status ON borrow_requests (status);
CREATE INDEX idx_borrow_request_product ON borrow_requests (product_id);

---------------- DONATION INFORMATIONS  ---------------------

CREATE TABLE donation_requests (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(200),
    donator_username VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'donation_pending', -- 'donation_pending', 'donation_approved', 'donation_rejected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

---------------- EXTENSION INFORMATIONS  ---------------------

CREATE TABLE extension_requests (
    id SERIAL PRIMARY KEY,
    borrow_id INT NOT NULL REFERENCES borrow_requests(id) ON DELETE CASCADE,
    new_returned_date DATE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('extension_pending', 'extension_approved', 'extension_rejected')) DEFAULT 'extension_pending',
    request_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(borrow_id, status) 
);

---------------- SYSTEM SETTING INFORMATIONS  ---------------------

CREATE TABLE system_settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value VARCHAR(50)
);

