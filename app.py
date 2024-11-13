from flask import Flask, render_template
from flask_socketio import SocketIO
#from game_logic import Game  # Import your Game class

app = Flask(__name__)
# socketio = SocketIO(app)

# Initialize your game
#game = Game(num_players=2)  # You can adjust the number of players

# Flask routes and SocketIO event handlers
@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/game')
# def game_page():
#     return render_template('game.html')

# @socketio.on('connect')
# def handle_connect():
#     print('A player has connected!')

# @socketio.on('move')
# def handle_move(data):
#     # Your move handling code
#     pass

if __name__ == '__main__':
    app.run(debug=True)
