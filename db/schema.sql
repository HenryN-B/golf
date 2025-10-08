CREATE TABLE rooms (
    room_code TEXT PRIMARY KEY,
    creator_id TEXT,
    game_started BOOLEAN DEFAULT 0
);

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT NOT NULL,
    num_of_players INTEGER,
    hole INTEGER DEFAULT 1,
    fini BOOLEAN DEFAULT 0,
    turn INTEGER DEFAULT 0,
    current_discard_card TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_code) REFERENCES rooms (room_code)
);

CREATE TABLE player (
    room_code TEXT NOT NULL,
    player_name TEXT,
    player_score INTEGER DEFAULT 0,
    PRIMARY KEY (room_code, player_name),
    FOREIGN KEY (room_code) REFERENCES rooms (room_code)
);

CREATE TABLE player_cards (
    game_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    rank TEXT,
    suit TEXT,
    is_revealed BOOLEAN DEFAULT 0,
    room_code TEXT,
    PRIMARY KEY (game_id, player_name, order_index),
    FOREIGN KEY (player_name) REFERENCES player (player_name),
    FOREIGN KEY (room_code) REFERENCES rooms (room_code),
    FOREIGN KEY (game_id) REFERENCES games (game_id)
);

CREATE TABLE deck (
    game_id INTEGER NOT NULL,
    order_index INTEGER NOT NULL,
    rank TEXT,
    suit TEXT,
    PRIMARY KEY (game_id, order_index),
    FOREIGN KEY (game_id) REFERENCES games (game_id)
);

CREATE TABLE discard (
    game_id INTEGER NOT NULL,
    order_index INTEGER NOT NULL,
    rank TEXT,
    suit TEXT,
    PRIMARY KEY (game_id, order_index),
    FOREIGN KEY (game_id) REFERENCES games (game_id)
);