CREATE TABLE IF NOT EXISTS profiles (
    username VARCHAR(50) PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    profile_image VARCHAR(200),
    currency_balance INTEGER DEFAULT 0
);

-- lasciare in questa tabela solo gacha id collect date (metterlo come data) e infine il numero di quanti ne hai
--
CREATE TABLE IF NOT EXISTS gacha_items (
    gacha_name VARCHAR(50) NOT NULL,
    collected_date TIMESTAMP NOT NULL,
    username VARCHAR(50) REFERENCES profiles(username) ON DELETE CASCADE,
    PRIMARY KEY (gacha_name,collected_date)
);

-- INSERT INTO profiles (username, email, profile_image, currency_balance) VALUES ('player1', 'player1@gmail.it', 'default_image_url', 100);
-- INSERT INTO profiles (username, email, profile_image, currency_balance) VALUES ('player2', 'player2@gmail.it', 'default_image_url', 100);


-- INSERT INTO gacha_items (gacha_name, collected_date, username) VALUES ('Trial gacha Doge-meme.jpg', '2024-12-31 23:59:59', 'player1');
-- INSERT INTO gacha_items (gacha_name, collected_date, username) VALUES ('dog', '2024-12-31 23:59:59', 'player2');
