from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Store connected clients with their names and groups
connected_clients = {}  # Format: {session_id: {"name": "UserName", "ip": "UserIP", "group": None}}

# Password for the webpage
PAGE_PASSWORD = "FWCFC"

@app.route('/admin')
def index():
    return render_template('index.html')

@app.route('/client')
def client_page():
    return render_template('client.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('password') == 'FWCFC':
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "Wrong Password"}), 401

@app.route('/connected_users')
def get_connected_users():
    return jsonify([
        { "id": sid, "name": info["name"], "group": info["group"] }
        for sid, info in connected_clients.items()
    ])


@app.route('/play_alert', methods=['POST'])
def play_alert():
    data = request.get_json()
    group = data.get('group')
    users = data.get('users', [])

    print(f"Triggering alert - Group: {group}, Users: {users}")

    # Group-based alert
    if group:
        for sid, user in connected_clients.items():
            if user.get('group') == group[-1]:  # Match 'A' or 'B'
                socketio.emit('play_alert', room=sid)

    # Individual user-based alert
    if users:
        for uid in users:
            if uid in connected_clients:
                socketio.emit('play_alert', room=uid)

    return jsonify({'status': 'success'})

@app.route('/send_tts', methods=['POST'])
def send_tts():
    data = request.get_json()
    message = data.get('message')
    group = data.get('group')
    users = data.get('users', [])

    if not message:
        return jsonify({'status': 'error', 'reason': 'No message provided'}), 400

    print(f"Sending TTS - Group: {group}, Users: {users}, Message: {message}")

    # Send to group
    if group:
        for sid, user in connected_clients.items():
            if user.get('group') == group:
                socketio.emit('speak_tts', {'message': message}, room=sid)

    # Send to individual users
    if users:
        for uid in users:
            if uid in connected_clients:
                socketio.emit('speak_tts', {'message': message}, room=uid)

    return jsonify({'status': 'success'})


@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    client_ip = request.remote_addr
    connected_clients[client_id] = {"name": None, "ip": client_ip, "group": None}
    emit('update_users', get_user_list(), broadcast=True)

@socketio.on('register')
def handle_register(data):
    name = data.get('name')
    group = data.get('group')
    connected_clients[request.sid] = {
        'id': request.sid,         # Socket ID for targeting
        'name': name,
        'group': group
    }
    print(f"Registered {connected_clients[request.sid]}")
    emit('update_users', connected_clients, broadcast=True)



@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    connected_clients.pop(client_id, None)
    emit('update_users', get_user_list(), broadcast=True)

def get_user_list():
    return [
        {"id": client_id, "name": info["name"] or client_id, "group": info.get("group", "None")}
        for client_id, info in connected_clients.items()
    ]

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, debug=True,allow_unsafe_werkzeug=True)
