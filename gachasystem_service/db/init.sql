CREATE TABLE IF NOT EXISTS memes (
    gacha_id SERIAL PRIMARY KEY,
    meme_name VARCHAR(50) UNIQUE NOT NULL,
    image_path VARCHAR(200) NOT NULL,
    rarity VARCHAR(50) NOT NULL,
    description VARCHAR(100)
);