import json
import ssl
import time
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import pygame

# --- CONFIGURATION ---
BROKER = "3ae44b7f9fda4802bfc9e3e325f88463.s1.eu.hivemq.cloud"
PORT = 8883
USER = "admin_project"
PASS = "Project123!" # <--- Verify this matches your Flask app

TOPIC_CONTROL = "project/autism/room_control"

# --- GPIO SETUP ---
PIN_ORANGE = 17  # Calm Mode
PIN_YELLOW = 27  # Focus Mode (Using White LED)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PIN_ORANGE, GPIO.OUT)
GPIO.setup(PIN_YELLOW, GPIO.OUT)

# --- MUSIC SETUP ---
pygame.mixer.init()
try:
    # Ensure you have a file named 'calm_music.mp3' in the folder
    pygame.mixer.music.load("rainy-day-169690.mp3") 
except:
    print("⚠️ Warning: calm_music.mp3 not found!")

# --- HARDWARE LOGIC ---
def update_room(data):
    print(f"⚙️ ACTUATOR UPDATE: {data}")
    
    # 1. Lights
    orange_on = data.get("orange_light", False)
    yellow_on = data.get("yellow_light", False)
    
    GPIO.output(PIN_ORANGE, GPIO.HIGH if orange_on else GPIO.LOW)
    GPIO.output(PIN_YELLOW, GPIO.HIGH if yellow_on else GPIO.LOW)

    # 2. Music
    music_on = data.get("music", False)
    if music_on:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1) # Loop forever
    else:
        pygame.mixer.music.stop()

# --- MQTT HANDLER ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        update_room(payload)
    except Exception as e:
        print(f"Error executing command: {e}")

# --- MAIN LOOP ---
client = mqtt.Client()
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.username_pw_set(USER, PASS)
client.on_message = on_message

print("⏳ Room Controller Connecting...")
client.connect(BROKER, PORT)
client.subscribe(TOPIC_CONTROL)
print("✅ Room Hardware Ready & Listening!")

# Start with everything OFF
update_room({"orange_light": False, "yellow_light": False, "music": False})

client.loop_forever()
