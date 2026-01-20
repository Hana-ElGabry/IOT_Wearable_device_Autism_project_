from flask import Flask, render_template, request, jsonify
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import json
import ssl
import requests
import time

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['MQTT_BROKER_URL'] = '3ae44b7f9fda4802bfc9e3e325f88463.s1.eu.hivemq.cloud'
app.config['MQTT_BROKER_PORT'] = 8883
app.config['MQTT_USERNAME'] = 'admin_project'
app.config['MQTT_PASSWORD'] = 'Project123!'
app.config['MQTT_TLS_ENABLED'] = True
app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLSv1_2

# --- NOTIFICATION SETTINGS (DISCORD) ---
# Your Discord Webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1462127980905234523/gBbN23WEoIPjEq13tvsEg1nUklsSbcCSmWB7T2BGToFCPLNTqav6-FSWKtsJGFCMfnA8"
NOTIFICATION_COOLDOWN = 300  # 5 Minutes

TOPIC_STATUS = "project/autism/student_status"
TOPIC_CONTROL = "project/autism/room_control"

# Internal state
control_state = {
    "orange": False,
    "yellow": False,
    "music": False,
    "auto": False
}

last_known_status = "relaxed"

# 🔴 TEST MODE: Set to 0 so it notifies IMMEDIATELY upon restart
last_notification_time = 0 

mqtt = Mqtt(app)
socketio = SocketIO(app, async_mode="threading")

def publish_control_state():
    """Publish current state to MQTT and Web UI"""
    payload = {
        "orange_light": control_state['orange'],
        "yellow_light": control_state['yellow'],
        "music": control_state['music']
    }
    mqtt.publish(TOPIC_CONTROL, json.dumps(payload))
    socketio.emit('update_controls', control_state)

def activate_calm_session():
    control_state['orange'] = True
    control_state['yellow'] = False

def activate_focus_session():
    control_state['orange'] = False
    control_state['yellow'] = True

def apply_auto_logic():
    global last_known_status
    if last_known_status == 'stressed':
        activate_calm_session()
        control_state['music'] = True
    else:
        activate_focus_session()
        control_state['music'] = False
    publish_control_state()

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Flask Connected to Cloud!")
        mqtt.subscribe(TOPIC_STATUS)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global last_known_status, last_notification_time
    try:
        data = json.loads(message.payload.decode())
        
        # DEBUG: Print exactly what we received
        # print(f"📩 Message Received: {data}") 

        # 1. Save Status
        if 'status' in data:
            last_known_status = data['status']
            
        # 2. Update Web Dashboards
        socketio.emit('update_status', data)
        socketio.emit('sensor_data', {
            "gsr": data.get("gsr", 0),
            "temperature": data.get("temperature", 0),
            "heartRate": data.get("hr", 0)
        })
        
        # 3. Auto Logic
        if control_state['auto']:
            apply_auto_logic()

        # 4. NOTIFICATIONS (Discord)
        if data.get('status') == 'stressed':
            current_time = time.time()
            time_since_last = current_time - last_notification_time
            
            print(f"🕒 Time since last alert: {int(time_since_last)}s (Cooldown: {NOTIFICATION_COOLDOWN}s)")

            if time_since_last > NOTIFICATION_COOLDOWN:
                try:
                    print("🚀 Attempting to send Discord notification...")
                    msg_text = "⚠️ **Auto-Mode:** Calm Room Activated" if control_state['auto'] else "⚠️ **Alert:** Child is STRESSED"
                    
                    payload = {
                        "content": msg_text,
                        "username": "Autism Alert System"
                    }
                    
                    response = requests.post(
                        DISCORD_WEBHOOK_URL,
                        json=payload
                    )
                    
                    if response.status_code == 204:
                        print(f"✅ Discord Notification SENT! (Check your Discord Channel)")
                        last_notification_time = current_time
                    else:
                        print(f"❌ Discord Failed. Code: {response.status_code}, Response: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Network Error: {e}")
            else:
                print("⏳ Notification SKIPPED (Cooldown active)")
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/sensors')
def sensors():
    return render_template('sensor_dashboard.html')

@app.route('/get_state', methods=['GET'])
def get_state():
    return jsonify(control_state)

@app.route('/control', methods=['POST'])
def control():
    try:
        data = request.get_json()
        control_type = data.get('control')
        state = data.get('state')
        
        if control_type == 'auto':
            control_state['auto'] = state
            if state == True: apply_auto_logic()
            socketio.emit('update_controls', control_state)
            return jsonify({"success": True, "state": control_state})

        elif control_type == 'session_focus':
            activate_focus_session()
            control_state['auto'] = False
            publish_control_state()
            return jsonify({"success": True, "state": control_state})

        elif control_type == 'session_calm':
            activate_calm_session()
            control_state['auto'] = False
            publish_control_state()
            return jsonify({"success": True, "state": control_state})

        elif control_type == 'music':
            control_state['music'] = state
            control_state['auto'] = False
            publish_control_state()
            return jsonify({"success": True, "state": control_state})
            
        return jsonify({"success": False}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
