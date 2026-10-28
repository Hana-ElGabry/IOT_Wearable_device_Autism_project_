# IoT Wearable Device Autism Support Project

This project is an IoT-based monitoring and environmental support system designed to help caregivers respond to changes in a child's physiological state. It connects a Flask web dashboard, an MQTT cloud broker, and a Raspberry Pi room controller so that sensor readings can be monitored and room conditions can be adjusted in real time.

The system can display incoming health data, identify a stressed state, activate a calming room configuration, play calming audio, and send an alert notification. Caregivers can also control the room manually through the dashboard.

## What was implemented

- **Flask web application** for the monitoring and control interface.
- **Live status updates** through Flask-SocketIO.
- **MQTT communication** through HiveMQ Cloud:
  - Receives student status and sensor readings.
  - Publishes room-control commands.
- **Automatic mode** that responds to the reported status:
  - `stressed`: activates the calm session and enables music.
  - Any other status: activates the focus session and disables music.
- **Manual room controls** for:
  - Focus session.
  - Calm session.
  - Music playback.
- **Raspberry Pi actuator controller** using:
  - An orange LED for calm mode.
  - A yellow LED for focus mode.
  - A speaker/audio output for looping calming music.
- **Real-time sensor dashboard** for:
  - Galvanic Skin Response (GSR).
  - Body temperature.
  - Heart rate.
- **Stress notifications** with a five-minute cooldown to prevent repeated alerts.
- **Responsive dashboard UI** with dark mode and mobile-friendly layouts.

## System architecture

```text
Wearable / sensor source
          |
          | MQTT: project/autism/student_status
          v
   Flask application
   - Receives status and sensor values
   - Updates browser clients with Socket.IO
   - Applies automatic room logic
   - Sends notifications
          |
          | MQTT: project/autism/room_control
          v
 Raspberry Pi room controller
 - Orange LED: calm mode
 - Yellow LED: focus mode
 - Music playback
```

## Repository structure

| File | Purpose |
| --- | --- |
| `app.py` | Main Flask server, MQTT subscriber/publisher, Socket.IO events, automatic logic, and notification handling. |
| `room_controller.py` | Raspberry Pi controller that listens for MQTT commands and controls GPIO outputs and music playback. |
| `templates/dashboard.html` | Main caregiver dashboard for status, automatic mode, sessions, music, and navigation. |
| `templates/sensor_dashboard.html` | Live sensor dashboard with charts and current readings. |
| `rainy-day-169690.mp3` | Audio file used for calming music playback. |
| `test.py` | Earlier/test version of the Flask application using ntfy notifications. |
| `test2.py` | Earlier/test version using Discord webhook notifications. |

## MQTT topics and payloads

### Student status topic

The Flask application subscribes to:

```text
project/autism/student_status
```

Example message:

```json
{
  "status": "stressed",
  "gsr": 5.4,
  "temperature": 36.8,
  "hr": 92
}
```

The `status` field drives automatic room behavior. The sensor fields are forwarded to the browser dashboard through Socket.IO.

### Room control topic

The Flask application publishes to:

```text
project/autism/room_control
```

Example message:

```json
{
  "orange_light": true,
  "yellow_light": false,
  "music": true
}
```

## Running the Flask dashboard

### 1. Install Python dependencies

Install the packages used by the application:

```bash
pip install Flask Flask-MQTT Flask-SocketIO requests
```

### 2. Configure the MQTT connection

Update the MQTT broker URL, port, username, and password in `app.py`, or preferably move them to environment variables before deployment.

The application expects a TLS-enabled MQTT connection on port `8883`.

### 3. Start the dashboard

```bash
python app.py
```

The dashboard listens on port `5000` and binds to all network interfaces:

- Main dashboard: `http://<server-ip>:5000/`
- Sensor dashboard: `http://<server-ip>:5000/sensors`

## Running the Raspberry Pi room controller

The room controller must run on a Raspberry Pi with GPIO access, an audio output, and the required Python packages:

```bash
pip install paho-mqtt pygame
```

Then start it from the project directory so the audio file can be found:

```bash
python room_controller.py
```

The GPIO pins currently used are:

| Function | BCM GPIO pin |
| --- | ---: |
| Orange calm-mode LED | 17 |
| Yellow focus-mode LED | 27 |

Adjust these pins in `room_controller.py` if the hardware wiring is different.

## Dashboard controls and API

The Flask application provides these routes:

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Opens the room-control dashboard. |
| `GET` | `/sensors` | Opens the live sensor dashboard. |
| `GET` | `/get_state` | Returns the current control state as JSON. |
| `POST` | `/control` | Changes automatic mode, sessions, or music. |

Example control request:

```bash
curl -X POST http://localhost:5000/control \
  -H "Content-Type: application/json" \
  -d '{"control":"session_calm"}'
```

## Important security notes

Before sharing or deploying this project, rotate any MQTT passwords and notification/webhook credentials that have been committed to source files. Production deployments should load credentials from environment variables or a secrets manager, use certificate verification for MQTT/TLS, and avoid running Flask with `debug=True`.

## Current scope

This repository contains the dashboard, MQTT integration, and Raspberry Pi actuator controller. It does not include the wearable sensor firmware or the sensor hardware data producer; those components must publish messages using the MQTT format described above.

## Future improvements

- Add a dependency file such as `requirements.txt`.
- Move all credentials and notification settings to environment variables.
- Add authentication for the dashboard and authorization for control commands.
- Add automated tests for MQTT message handling and control endpoints.
- Add sensor-device firmware and calibration documentation.
