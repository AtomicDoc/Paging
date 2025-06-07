from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins=["*"])

connected_clients = {}

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
    return jsonify({"status": "failure"}), 401

@app.route('/connected_users')
def get_connected_users():
    return jsonify(connected_clients)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400
    target_group = data.get('group', None)
    target_users = data.get('users', [])
    socketio.emit('alert', {"message": data['message'], "group": target_group, "users": target_users})
    return jsonify({"status": "Alert sent"}), 200

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('register')
def handle_register(data):
    sid = request.sid
    connected_clients[sid] = {
        "name": data.get("name", "Unknown"),
        "group": data.get("group", "None")
    }
    emit('client_registered', {"sid": sid})
    print(f"Registered {connected_clients[sid]}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in connected_clients:
        print(f"Client disconnected: {connected_clients[sid]}")
        del connected_clients[sid]

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
