CREATE TABLE rooms (
    room_code TEXT PRIMARY KEY,
    creator_id TEXT,
    game_started BOOLEAN DEFAULT 0
);

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    room_code TEXT,
    num_of_players INTEGER,
    hole INTEGER,
    fini BOOLEAN DEFAULT 0,
    turn INTEGER,
    current_discard_card TEXT,
    FOREIGN KEY (room_code) REFERENCES rooms (room_code)
);

CREATE TABLE player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code TEXT,
    player_name TEXT,
    game_id INTEGER,
    player_score INTEGER,
    FOREIGN KEY (game_id) REFERENCES games (game_id),
    FOREIGN KEY (room_code) REFERENCES rooms (room_code)
);

CREATE TABLE player_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank TEXT,
    suit TEXT,
    order_index INTEGER,
    is_revealed BOOLEAN DEFAULT 0,
    player_name TEXT REFERENCES player (player_name),
    room_code TEXT,
    FOREIGN KEY (room_code) REFERENCES rooms (room_code)
);

CREATE TABLE deck (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank TEXT,
    suit TEXT,
    order_index INTEGER,
    game_id INTEGER,
    FOREIGN KEY (game_id) REFERENCES games (game_id)
);

CREATE TABLE discard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank TEXT,
    suit TEXT,
    order_index INTEGER,
    game_id INTEGER,
    FOREIGN KEY (game_id) REFERENCES games (game_id)
);



