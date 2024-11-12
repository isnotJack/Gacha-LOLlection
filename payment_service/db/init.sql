
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    payer_us VARCHAR(50) NOT NULL,
    receiver_us VARCHAR(50) NOT NULL,
    amount FLOAT NOT NULL,
    currency VARCHAR(50) NOT NULL,
    date TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS balance (
    username VARCHAR(50) PRIMARY KEY,
    balance FLOAT NOT NULL
);
