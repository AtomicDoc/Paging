from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import requests



scheduler = BackgroundScheduler()
scheduler.start()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'CHANGEME'
socketio = SocketIO(app)

# Store connected clients with their names and groups
connected_clients = {}  # Format: {session_id: {"name": "UserName", "ip": "UserIP", "group": None}}

# Password for the webpage
PAGE_PASSWORD = "CHANGEME"


HOME_ASSISTANT_WEBHOOKS = {
    "alert": "CHANGETOLOCALURL",
    "tts": "CHANGETOLOCALURL",
}



def trigger_home_assistant(event_type, message=None):
    url = HOME_ASSISTANT_WEBHOOKS.get(event_type)
    if not url:
        print(f"[HA] Unknown event type: {event_type}")
        return

    payload = {"message": message} if message else {}
    try:
        response = requests.post(url, json=payload, timeout=3)
        print(f"[HA] Triggered {event_type}: {response.status_code}")
    except Exception as e:
        print(f"[HA] Error triggering {event_type}: {e}")



@app.route('/admin')
def index():
    return render_template('index.html')

@app.route('/client')
def client_page():
    return render_template('client.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('password') == 'CHANGEME':
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

    trigger_home_assistant("alert")
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

    trigger_home_assistant("tts", message=message)
    return jsonify({'status': 'success'})

@app.route('/schedule_tts', methods=['POST'])
def schedule_tts():
    data = request.get_json()
    message = data.get('message')
    time_str = data.get('time')  # e.g., "14:30"
    interval = data.get('interval')  # optional
    users = data.get('users', [])

    if not message or not time_str or not users:
        return jsonify({'status': 'error', 'reason': 'Invalid input'}), 400

    # Parse the time into a future datetime object
    now = datetime.now()
    hour, minute = map(int, time_str.split(':'))
    run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if run_time < now:
        run_time += timedelta(days=1)

    def send_tts_job():
        print(f"[Scheduled TTS] Sending to users: {users}")
        for uid in users:
            if uid in connected_clients:
                socketio.emit('speak_tts', {'message': message}, room=uid)

    job_id = f"tts_{datetime.now().timestamp()}"

    if interval:
        scheduler.add_job(send_tts_job, 'interval', minutes=interval, next_run_time=run_time, id=job_id)
    else:
        scheduler.add_job(send_tts_job, 'date', run_date=run_time, id=job_id)

    print(f"Scheduled TTS at {run_time} (interval: {interval})")

    return jsonify({'status': 'scheduled'})


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    key = request.headers.get("X-Webhook-Key")  # simple authentication
    if key != "Super Secret Key!":
        return jsonify({"status": "unauthorized"}), 403

    action = data.get('action')  # "tts" or "alert"
    message = data.get('message')
    users = data.get('users', [])
    group = data.get('group')

    if action == "tts" and message:
        if group:
            for sid, user in connected_clients.items():
                if user.get('group') == group:
                    socketio.emit('speak_tts', {'message': message}, room=sid)
        if users:
            for uid in users:
                if uid in connected_clients:
                    socketio.emit('speak_tts', {'message': message}, room=uid)
        return jsonify({'status': 'tts_sent'})

    elif action == "alert":
        if group:
            for sid, user in connected_clients.items():
                if user.get('group') == group:
                    socketio.emit('play_alert', room=sid)
        if users:
            for uid in users:
                if uid in connected_clients:
                    socketio.emit('play_alert', room=uid)
        return jsonify({'status': 'alert_sent'})

    return jsonify({'status': 'invalid request'}), 400


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
