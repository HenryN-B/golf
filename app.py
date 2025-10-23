import os
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
import utils.logic as golf
from threading import Lock
import time

from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

pending_removals = {}
lock = Lock()
rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    return code

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join",False)
        create = request.form.get("create",False)
        if not name:
             return render_template("index.html", error="Enter a name plese", code = code, name = name)
        if join != False and not code:
            return render_template("index.html", error="Enter a code",code = code, name = name)
        room = code
        if create != False:
            print("Creating new room")
            room = generate_unique_code(4)
            rooms[room] = {"players": [], "game": golf.Game(room), "Host": name, "code": code}
        elif code not in rooms:
            return render_template("index.html", error="Room does not egg cist",code = code, name = name)
        elif name in rooms[room]["players"]:
            return render_template("index.html", error="Player name already in room",code = code, name = name)
        elif name == room:
             return render_template("index.html", error="Name can not be room code",code = code, name = name)
            
        session["room"] = room
        session["name"] = name
        
        return redirect(url_for("room"))
    return render_template('index.html')

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("index"))
    return render_template("room.html", code=room, name = name, host = rooms[room]["Host"])

@app.route("/game", methods=["POST", "GET"])
def game():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return redirect(url_for("index"))
    if room not in rooms:
        return redirect(url_for("index"))
    
    game = rooms[room]["game"]
    game.reset()

    player_cards = {}
    player_names = []
    for player in game.players:
        player_names.append(player.player_name)
        player_cards[player.player_name] = player.player_hand

    while player_names[0] != name:
        player_names = player_names[1:] + player_names[:1]

    game_data = {
        "name": name,
        "room": room,
        "player_names": player_names,
        "player_cards": player_cards,
        "deck": game.deck,
        "discard": game.discard_pile,
        "players_num": len(player_names)
    }

    return render_template("game.html", game_data=game_data)


@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    
    if room not in rooms:
        return

    with lock:
        if name in pending_removals:
            pending_removals[name]["cancel"] = True
            del pending_removals[name]

    if name not in rooms[room]["players"]:
        rooms[room]["players"].append(name)
        rooms[room]["game"].add_player(name, room)

    join_room(room)
    print(f"{name} connected to room {room}")
    socketio.emit("update_players", {"players": rooms[room]["players"]}, to=room)


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    sid = request.sid

    if not room or not name:
        return

    with lock:
        pending_removals[name] = {
            "room": room,
            "sid": sid,
            "cancel": False,
            "timestamp": time.time(),
        }

    socketio.start_background_task(remove_player_after_delay, name)


def remove_player_after_delay(name):
    socketio.sleep(3)  # Wait 3 seconds

    with lock:
        if name not in pending_removals or pending_removals[name]["cancel"]:
            if name in pending_removals:
                del pending_removals[name]
            return

        info = pending_removals.pop(name)
        room = info["room"]
        sid = info["sid"]

    with app.app_context():
        if room not in rooms:
            return
        if rooms[room]["game"].playing:
            return

        leave_room(room, sid=sid, namespace="/")

        if name in rooms[room]["players"]:
            rooms[room]["players"].remove(name)
            for p in rooms[room]["game"].players:
                if p.player_name == name:
                    rooms[room]["game"].remove_player(p, room)
                    break

        if not rooms[room]["players"]:
            del rooms[room]
            print("Deleting room")
        else:
            socketio.emit("update_players", {"players": rooms[room]["players"]}, to=room)

        print(f"{name} fully disconnected from room {room}")
        
        
@socketio.on("start_game")
def handle_start_game(data):
    room = data.get("room")
    game = rooms[room]["game"]
    print(f"Game started in room {room}")
    # send a message to everyone in the room
    game.reset()
    rooms[room]["game"].playing = True
    game.discard_pile.append(game.draw_top_card())
    socketio.emit("game_started", {"msg": "The game has started!"}, to=room)


if __name__ == '__main__':
    socketio.run(app,debug=True, host='0.0.0.0')