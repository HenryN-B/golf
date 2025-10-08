import random
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()

USE_DATABASE = os.getenv("USE_DATABASE", "False").lower() == "true"


class Player:
    def __init__(self, n, c) -> None:
        self.player_name = n
        self.room_code = c
        self.player_hand = []
        self.player_score = 0


class Game:
    def __init__(self, room_code):
        self.deck = []
        self.players = []
        self.number_of_players = 0
        self.discard_pile = []
        self.fini = False
        self.turn = 0
        self.hole = 1
        self.room_code = room_code
        self.playing = False
        self.game_id = add_game_db(room_code)

    def update(self, room_code):
        if not USE_DATABASE:
            return self  # Skip DB operations entirely
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch room data
        cur.execute("SELECT * FROM rooms WHERE room_code = ?", (room_code,))
        room_data = cur.fetchone()
        if not room_data:
            raise ValueError(f"No room found with room_code: {room_code}")

        # Fetch game data
        cur.execute("SELECT * FROM games WHERE room_code = ?", (room_code,))
        game_data = cur.fetchone()
        if not game_data:
            raise ValueError(f"No game found for room_code: {room_code}")

        # Fetch players
        cur.execute("SELECT * FROM player WHERE room_code = ?", (room_code,))
        players_data = cur.fetchall()

        # Fetch deck
        cur.execute("""
            SELECT rank, suit, order_index
            FROM deck
            WHERE game_id = ?
        """, (game_data["game_id"],))
        deck_cards = cur.fetchall()

        # Fetch discard pile
        cur.execute("""
            SELECT rank, suit, order_index
            FROM discard
            WHERE game_id = ?
        """, (game_data["game_id"],))
        discard_cards = cur.fetchall()

        self.room_code = room_data["room_code"]
        self.number_of_players = game_data["num_of_players"]
        self.hole = game_data["hole"]
        self.fini = game_data["fini"]
        self.turn = game_data["turn"]
        self.game_id = game_data["game_id"]
        self.players = []
        self.deck = []
        self.discard = []

        # Populate players
        for player in players_data:
            name = player["player_name"]
            score = player["player_score"]
            room_code = room_data["room_code"]
            player_obj = Player(name, room_code)
            player_obj.player_score = score
            cur.execute(
                """
                SELECT rank, suit, order_index, is_revealed
                FROM player_cards
                WHERE room_code = ? AND player_name = ?
                """,
                (room_code, name)
            )
            player_cards = cur.fetchall()
            add_card = {}
            for card in player_cards:
                rank = card["rank"]
                suit = card["suit"]
                order_index = card["order_index"]
                is_rev = card["is_revealed"]
                add_values = [rank, suit]
                add_card[order_index] = [is_rev, add_values]

            for index, cards in enumerate(add_card):
                player_obj.player_hand.append(add_card.get(index))

            self.players.append(player_obj)
        add_card = {}
        for card in deck_cards:
            rank = card["rank"]
            suit = card["suit"]
            order_index = card["order_index"]
            add_values = [rank, suit]
            add_card[order_index] = [add_values]

        for index, cards in enumerate(add_card):
            self.deck.append(add_card.get(index))

        add_card = {}
        for card in discard_cards:
            rank = card["rank"]
            suit = card["suit"]
            order_index = card["order_index"]
            add_values = [rank, suit]
            add_card[order_index] = [add_values]

        for index, cards in enumerate(add_card):
            self.discard_pile.append(add_card.get(index))

        cur.close()
        conn.close()

        return self

    def draw_top_card(self):
        card = self.deck.pop()
        update_game_state(self)
        return card

    def deal_hand(self, player):
        for x in range(6):
            player.player_hand.append((False, self.deck.pop()))
        update_player_state(player, self)

    def flip(self, num, player):
        _, card = player.player_hand[num - 1]
        player.player_hand[num - 1] = ((True, card))

    def flip_all(self):
        for player in self.players:
            _, cards = zip(*player.player_hand)
            for x in range(6):
                player.player_hand[x] = ((True, cards[x]))
            update_player_state(player, self)

    def replace_card(self, player, card, num):
        _, discard = player.player_hand[num - 1]
        self.discard_pile.append(discard)
        player.player_hand[num - 1] = ((True, card))
        update_game_state(self)
        update_player_state(player, self)

    def first_flips(self, player, num1, num2):
        self.flip(num1, player)
        self.flip(num2, player)
        update_player_state(player, self)

    def check_fini(self):
        for player in self.players:
            revealed, _ = zip(*player.player_hand)
            if all(revealed):
                self.fini = True
                update_game_state(self)

    def add_player(self, player_name, room_code):
        player = Player(player_name, room_code)
        self.players.append(player)
        self.number_of_players += 1
        add_player_db(player_name, room_code, self.game_id)
        update_game_state(self)

    def remove_player(self, player, room_code):
        self.players.remove(player)
        self.number_of_players -= 1
        remove_player_db(player, room_code)
        update_game_state(self)

    def play(self):
        while self.hole < 10:
            self.reset()
            print(f"Hole {self.hole}")
            for x, player in enumerate(self.players):
                print(f"\n{player.player_name}'s hand before flipping:")
                self.display_hand(player)
                print(f"{player.player_name}, which card would you like to flip over:", end=" ")
                num1 = int(input())
                print("Pick another:", end=" ")
                num2 = int(input())
                self.first_flips(player, num1, num2)
            rounds = 0
            while not self.fini:
                if rounds == 0:
                    self.discard_pile.append(self.draw_top_card())

                for x, player in enumerate(self.players):
                    if rounds % len(self.players) == x:
                        self.player_turn(player)
                if not self.fini:
                    self.check_fini()
                rounds += 1
            for x, player in enumerate(self.players):
                if player != self.players[(rounds - 1) % len(self.players)]:
                    self.player_turn(player)
            self.flip_all()
            for player in self.players:
                self.score(player)
            for player in self.players:
                print(player.player_score)
            self.hole += 1

    def score(self, player):
        for x, card in enumerate(player.player_hand):
            card_number = card[1][0]
            if card_number == "Jack":
                self.check_for_cancel(player, x, 10)
            elif card_number == "King":
                self.check_for_cancel(player, x, 0)
            elif card_number == "Queen":
                self.check_for_cancel(player, x, -1)
            elif card_number == "Joker":
                self.check_for_cancel(player, x, -5)
            elif card_number == "2":
                self.check_for_cancel(player, x, -2)
            elif card_number == "Ace":
                self.check_for_cancel(player, x, 1)
            else:
                self.check_for_cancel(player, x, int(card_number))

    def check_for_cancel(self, player, card_index, value):
        card_number = player.player_hand[card_index][1][0]
        if card_index < 3:
            if player.player_hand[card_index + 3][1][0] != card_number:
                player.player_score += value
        elif card_index > 2:
            if player.player_hand[card_index - 3][1][0] != card_number:
                player.player_score += value
        update_player_state(player,self)

    def player_turn(self, player):
        self.display_hand(player)
        print(self.discard_pile[-1])
        print(f"{player.player_name}, would you like to:\n1: Take this card\n2: Draw new card\nEnter 1 or 2:")
        input_value = int(input())
        if input_value == 2:
            self.discard_pile.append(self.draw_top_card())
            print(self.discard_pile[-1])
            print(f"{player.player_name}, would you like to:\n1: Take this card\n2: Flip a card\nEnter 1 or 2:")
            input_value = int(input())
            if input_value == 1:
                print(f"{player.player_name}, choose where to put the card.")
                input_value = int(input())
                self.replace_card(player, self.discard_pile.pop(), input_value)
            elif input_value == 2:
                print(f"{player.player_name}, choose a card to flip.")
                input_value = int(input())
                self.flip(input_value, player)
        else:
            print(f"{player.player_name}, choose where to put the card.")
            input_value = int(input())
            self.replace_card(player, self.discard_pile.pop(), input_value)
            
    def display_hand(self, player):
        print(f"\n{player.player_name}'s hand:")
        print("-------------------------")

        # Create two rows of three cards each
        rows = [player.player_hand[:3], player.player_hand[3:]]

        for row in rows:
            line = ""
            for is_revealed, card in row:
                if is_revealed:
                    line += f"[{card[0]} {card[1][0]}]  "  # e.g., [7 H]
                else:
                    line += "[???]  "
            print(line)

        # Show position numbers below for easy selection
        print("  1     2     3")
        print("  4     5     6")
        print("-------------------------")

    def reset(self):
        suits = ("Hearts", "Diamonds", "Clubs", "Spades")
        ranks = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace")
        for suit in suits:
            for rank in ranks:
                self.deck.append((rank, suit))
        self.deck.append(("Joker", "Black"))
        self.deck.append(("Joker", "Red"))
        self.fini = False
        self.turn = 0
        random.shuffle(self.deck)
        for player in self.players:
            player.player_hand = []
            self.deal_hand(player)
        update_game_state(self)

    def get_players(self):
        return [player.player_name for player in self.players]


# ===================== DATABASE FUNCTIONS ===================== #

def get_db_connection():
    if not USE_DATABASE:
        return None
    conn = sqlite3.connect('db/game.db')
    conn.row_factory = sqlite3.Row
    return conn


def clear_database():
    if not USE_DATABASE:
        return
    conn = get_db_connection()
    try:
        with conn:
            conn.execute('DELETE FROM rooms')
            conn.execute('DELETE FROM player')
            conn.execute('DELETE FROM games')
            conn.execute('DELETE FROM player_cards')
            conn.execute('DELETE FROM deck')
            conn.execute('DELETE FROM discard')
        with conn:
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'player'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'player_cards'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'deck'")
            conn.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'discard'")
    finally:
        conn.close()


def add_room_db(room_code, name):
    if not USE_DATABASE:
        return
    conn = get_db_connection()
    with conn:
        conn.execute(
            'INSERT INTO rooms (room_code, creator_id) VALUES (?, ?)',
            (room_code, name)
        )


def add_game_db(room_code):
    if not USE_DATABASE:
        return random.randint(1000, 9999)

    conn = get_db_connection()
    with conn:
        conn.execute(
            'INSERT INTO games ("room_code") VALUES (?)',
            (room_code,)
        )
        cursor = conn.execute(
            'SELECT game_id FROM games WHERE "room_code" = ?',
            (room_code,)
        )
        row = cursor.fetchone()

    conn.close()

    game_id = row['game_id']
    return int(game_id)

def add_player_db(player_name, room_code, game_id):
    if not USE_DATABASE:
        return
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                'INSERT INTO player (player_name, room_code) VALUES (?, ?)',
                (player_name, room_code)
            )
        with conn:
            for x in range(6):
                conn.execute(
                    'INSERT INTO player_cards (game_id, player_name, order_index) VALUES (?,?,?)',
                    (game_id, player_name, x)
                )
    finally:
        conn.close()


def remove_player_db(player, room_code):
    if not USE_DATABASE:
        return
    player_name = player.player_name
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                'DELETE FROM player_cards WHERE player_name = ? AND room_code = ?',
                (player_name, room_code)
            )
        with conn:
            conn.execute(
                'DELETE FROM player WHERE player_name = ? AND room_code = ?',
                (player_name, room_code)
            )
    finally:
        conn.close()


def update_player_state(player, game):
    if not USE_DATABASE:
        return
    room_code = player.room_code
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                '''
                UPDATE player
                SET player_score = ?
                WHERE player_name = ? AND room_code = ?
                ''',
                (player.player_score, player.player_name, player.room_code)
            )
            for index, card in enumerate(player.player_hand):
                is_revealed, values = card
                rank, suit = values
                conn.execute(
                    '''
                    UPDATE player_cards
                    SET is_revealed = ?, rank = ?, suit = ?, room_code = ?
                    WHERE  game_id = ? AND player_name = ? AND order_index = ?
                    ''',
                    (is_revealed, rank, suit, game.room_code, game.game_id, player.player_name, index)
                )
    finally:
        conn.close()


def update_game_state(game):
    if not USE_DATABASE:
        return
    game_id = game.game_id
    conn = get_db_connection()
    with conn:
        conn.execute(
            '''
            UPDATE games
            SET num_of_players = ?, hole = ?, fini = ?, turn = ?
            WHERE game_id = ?
            ''',
            (
                game.number_of_players,
                game.hole,
                game.fini,
                game.turn,
                game_id
            )
        )
        conn.execute("DELETE FROM deck WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM discard WHERE game_id = ?", (game_id,))

        # Insert new deck
        for index, (rank, suit) in enumerate(game.deck):
            conn.execute(
                "INSERT INTO deck (rank, suit, order_index, game_id) VALUES (?, ?, ?, ?)",
                (rank, suit, index, game_id)
            )

        # Insert new discard pile
        for index, (rank, suit) in enumerate(game.discard_pile):
            conn.execute(
                "INSERT INTO discard (rank, suit, order_index, game_id) VALUES (?, ?, ?, ?)",
                (rank, suit, index, game_id)
            )
    conn.close()


def get_players_in_game(room_code):
    if not USE_DATABASE:
        return []
    conn = get_db_connection()
    players_db = conn.execute(
        'SELECT * FROM player WHERE room_code = ?',
        (room_code,)
    ).fetchall()
    conn.close()
    return [player['player_name'] for player in players_db]


# ===================== TESTING ===================== #

# if __name__ == "__main__":
#     test_golf_game = Game("TEST")
#     test_golf_game.add_player("henry", "TEST")
#     test_golf_game.add_player("Klaus", "TEST")
#     test_golf_game.play()