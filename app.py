#need to make it so when join button is clicked all player go to /game 
from flask import Flask, render_template, session, redirect, url_for, request
from flask_socketio import SocketIO, join_room, leave_room, send
from game_logic import Game  # Import your Game class
import random
from string import ascii_uppercase
from datetime import timedelta

app = Flask(__name__)
app.config["SECRET_KEY"]= "henadlksddas[kdry"
app.config["SESSION_COOKIE_SECURE"] = False
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    return code



@app.route('/', methods=['GET'])
def index():
    #session.clear()  # Clear session for new user
    return render_template("index.html")



@socketio.on("create_room")
def create_room(data):
    name = data.get("name")
    session.permanent = True 
    app.permanent_session_lifetime = timedelta(minutes=30)
    if not name:
        socketio.emit("error_message", {"message": "Name is required."}, to=request.sid)
        return

    room = generate_unique_code(4)
    rooms[room] = {
        "creator_id": name,
        "members": 0,
        "game": Game(),
        "game_started": False
    }
    
    session["room"] = room
    session["name"] = name

    join_room(room)
    rooms[room]["game"].add_player(name)
    rooms[room]["members"] += 1

    socketio.emit("created_room", {"url": url_for("room")}, to=request.sid)

@socketio.on("join_room")
def handle_join_room(data):
    room = data.get("room")
    name = data.get("name")
    
    if not name or not room:
        socketio.emit("error_message", {"message": "Name and room code are required."}, to=request.sid)
        return

    if room not in rooms:
        socketio.emit("error_message", {"message": "Room does not exist."}, to=request.sid)
        return

    if name in rooms[room]["game"].get_player_names():
        socketio.emit("error_message", {"message": "Name already taken."}, to=request.sid)
        return
    session["room"] = room
    session["name"] = name


    join_room(room)
    rooms[room]["game"].add_player(name)
    rooms[room]["members"] += 1

    # Update player list for everyone in the room
    players = rooms[room]["game"].get_player_names()
    socketio.emit("update_players", {"players": players}, to=room)
    socketio.emit("redirect_to_room", {"url": "/room"}, to=request.sid)


@app.route('/room', methods=['GET'])
def room():
    print(session.get("name"))
    print(session.get("room"))
    room = session.get("room")
    name = session.get("name")
    


    if not room or not name or room not in rooms or name not in rooms[room]["game"].get_player_names():
        return redirect(url_for("index"))

    return render_template(
        "room.html",
        code=room,
        players=rooms[room]["game"].get_player_names(),
        owner=rooms[room]["creator_id"],
        name=name
    )
    
@socketio.on("start_game")
def start_game():
    room = session.get("room")

    if not room or room not in rooms:
        return

    if rooms[room]["game"].number_of_players < 2:
        socketio.emit("error_message", {"message": "Need at least 2 players to start the game."}, to=request.sid)
        return

    rooms[room]["game_started"] = True

    # Notify all players in the room to redirect to the game page
    socketio.emit("redirect_to_game", {"url": "/game"}, to=room)
    
@app.route("/restore_session", methods=["POST"])
def restore_session():
    data = request.json
    name = data.get("name")
    room = data.get("room")

    if not name or not room:
        return {"success": False, "error": "Missing name or room"}

    if room not in rooms or name not in rooms[room]["game"].get_player_names():
        return {"success": False, "error": "Invalid room or name"}

    session["room"] = room
    session["name"] = name
    return {"success": True}

        
            
    
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    
    
    # @app.route('/', methods=['GET', 'POST'])
# def index():
#     session.clear()
#     if request.method == "POST":
#         name = request.form.get("name")
#         code = request.form.get("code")
#         join = request.form.get("join",False)
#         create = request.form.get("create",False)
#         if not name:
#             return render_template("index.html", error="Enter a name plese", code = code, name = name)
#         if join != False and not code:
#             return render_template("index.html", error="Enter a code",code = code, name = name)
#         room = code
#         if create != False:
#             room = generate_unique_code(4)
#             rooms[room] = {"creator_id": name, "members" : 0, "game" : Game(), "game_started": False }
#         elif code not in rooms:
#             return render_template("index.html", error="Room does not egg cist",code = code, name = name)
#         session["room"] = room
#         session["name"] = name
#         if name in rooms[room]["game"].players:
#             return render_template("index.html", error="Name already taken",code = code, name = name)
            
        
       
#         return redirect(url_for("room"))
#     return render_template("index.html")

# @app.route('/room', methods=['GET', 'POST'])
# def room():
#     room = session.get("room")
#     name = session.get("name")
#     if room is None or session.get("name") is None or room not in rooms or name not in rooms[room]["game"].get_player_names():
#         return redirect(url_for("index"))
#     if  rooms[room]["game_started"]:
#         return redirect(url_for("game"))
#     if request.method == "POST":
#         if 'start' in request.form:
#             print(rooms[room]["game"].number_of_players)
#             if rooms[room]["game"].number_of_players < 2:
#                 start = False;
#                 return render_template(
#                     "room.html",
#                     code=room,
#                     players=rooms[room]["game"].get_player_names(),
#                     owner=rooms[room]["creator_id"],
#                     name=name,
#                     error="Need at least 2 players"
#                 )
#             rooms[room]["game_started"] = True
#             socketio.emit('redirect_to_game', {'url': '/game'}, to=room)
#             return redirect(url_for("game"))
    
#     return render_template("room.html", code=room,players=rooms[room]["game"].get_player_names(), owner = rooms[room]["creator_id"], name = name)

# @app.route('/game', methods=['GET', 'POST'])
# def game():
#     return render_template("game.html")

# @socketio.on("disconnect")
# def disconnect():
#     room = session.get("room")
#     name = session.get("name")
#     print(f"{name} disconnected")
#     # Ensure room and name are defined before proceeding
#     if not room or not name or room not in rooms:
#         if name in rooms[room]["game"].get_player_names():
#             rooms[room]["game"].remove_player(name)
#             print(rooms[room]["game"].get_player_names())
#             rooms[room]["members"] -= 1
#             # Only delete the room if there are no members left
#             if rooms[room]["members"] <= 0:
#                 del rooms[room]
#             else:
#                 # Notify remaining players about the updated player list
#                 socketio.emit("update_players", {"players": rooms[room]["game"].players}, to=room)
#                 leave_room(room)
#                 session.clear()
#                 #return redirect("/")