#need to make it so when join button is clicked all player go to /game 
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send
from logic import *
import random
from string import ascii_uppercase
from datetime import timedelta
import sqlite3

app = Flask(__name__)
app.config["SECRET_KEY"]= "henadlksddas[kdry"
app.config["SESSION_COOKIE_SECURE"] = False
socketio = SocketIO(app)

def generate_unique_code(length):
    conn = get_db_connection()
    rooms_row = conn.execute("SELECT * FROM rooms").fetchall()
    rooms = []
    for room in rooms_row:
        rooms.append(room.get("room_code"))
        
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    return code


def get_db_connection():
    conn = sqlite3.connect("db/game.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route("/room", methods=['GET'])
def room():
    room_code = request.args.get("room_code")
    name = request.args.get("name")
    if not room_code:
        return redirect(url_for("index"))
    conn = get_db_connection()
    game = Game()
    game.update(room_code)
    
    
    players = game.get_players()
    
    room_owner = conn.execute("SELECT creator_id FROM rooms WHERE room_code = ? ", (room_code,)).fetchone()
    create_id = room_owner["creator_id"]
  
    return render_template("room.html", code=room_code, players=players, owner=create_id, name = name)



@app.route("/api/restore_session", methods=["POST"])
def restore_session():
    data = request.json
    name = data.get("name")
    room = data.get("room")

    if not name or not room:
        return jsonify({"success": False, "error": "Missing name or room"})

    conn = get_db_connection()
    player = conn.execute(
        "SELECT * FROM player WHERE player_name = ? AND room_code = ?", (name, room)
    ).fetchone()
    conn.close()

    if not player:
        return jsonify({"success": False, "error": "Invalid room or name"})

    return jsonify({"success": True})

@socketio.on("create_room")
def create_room(data):
    name = data.get("name")
    if not name:
        socketio.emit("error_message", {"message": "Name is required."}, to=request.sid)
        return

    conn = get_db_connection()
    room = generate_unique_code(4)
    with conn:
        conn.execute(
            "INSERT INTO rooms (room_code, creator_id) VALUES (?, ?)",
            (room, name),
        )
    conn.close()

    game = Game(room)
    game.add_player(name, room, game.game_id, False)
    join_room(room)
    print(f"Player {name} joined room {room}.")

    socketio.emit(
        "created_room", 
        {"url": url_for("room", _external=True), "room": room}, 
        to=request.sid
    )
        
@socketio.on("join_room")
def join_room_event(data):
    room = data.get("room")
    name = data.get("name")
    
    if not name or not room:
        socketio.emit("error_message", {"message": "Name and room code are required."}, to=request.sid)
        return

    conn = get_db_connection()
    try:
        existing_room = conn.execute(
            "SELECT * FROM rooms WHERE room_code = ?", (room,)
        ).fetchone()
        if not existing_room:
            socketio.emit("error_message", {"message": "Room does not exist."}, to=request.sid)
            return

        existing_player = conn.execute(
            "SELECT * FROM player WHERE player_name = ? AND room_code = ?", (name, room)
        ).fetchone()
        if existing_player:
            socketio.emit("error_message", {"message": "Name already taken."}, to=request.sid)
            return
    finally:
        conn.close()
    
        
    join_room(room)
    print(f"Player {name} joined room {room}.")
    game = Game()
    game.update(room)  
    game.add_player(name, room, game.game_id, False)
    players = game.get_players()
    socketio.emit("join", {"url": url_for("room", _external=True)}, to=request.sid)
    socketio.emit("acknowledge_join", {"room": room, "player": name}, to=request.sid)
    socketio.emit("update_players", {"players": players,"code": room}, to=room)
        
        
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)