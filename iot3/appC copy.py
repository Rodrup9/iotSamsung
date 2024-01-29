from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import base64
import threading
import pickle
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

video_path = 'carPark.mp4'
cap = cv2.VideoCapture(video_path)

with open('CarParkPos', 'rb') as f:
    posList = pickle.load(f)
width, height = 107, 48

frame_count = 0

def check_parking_space(frame):
    global frame_count

    space_counter = 0

    for pos in posList:
        x, y = pos
        img_crop = frame[y: y + height, x: x + width]
        count = cv2.countNonZero(cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY))

        if count < 950:
            color = (0, 255, 0)
            thickness = 5
            space_counter += 1
        else:
            color = (0, 0, 255)
            thickness = 2
            # Detectar objetos dentro del marcador (asumiendo que el valor de umbral puede variar según tu entorno)
            _, contours, _ = cv2.findContours(cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:
                color = (0, 0, 255)  # Si hay algún objeto, marcar en rojo
                space_counter -= 1  # Restar uno al contador de espacios

        cv2.rectangle(frame, pos, (pos[0] + width, pos[1] + height), color, thickness)
        cv2.putText(frame, str(count), (x, y + height - 3), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

    cv2.putText(frame, f'Free spaces: {space_counter}/{len(posList)}', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 210, 0), 5, cv2.LINE_AA)

    frame_count += 1

    _, buffer = cv2.imencode('.jpg', frame)
    jpg_data = base64.b64encode(buffer).decode('utf-8')

    socketio.emit('video_frame', {'frame': jpg_data, 'count': frame_count})
    socketio.sleep(0.1)

def video_stream():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img_threshold = cv2.adaptiveThreshold(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        img_median = cv2.medianBlur(img_threshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(img_median, kernel, 1)

        check_parking_space(frame)

@app.route('/')
def index():
    return render_template('index2.html')

@socketio.on('connect')
def handle_connect():
    if not hasattr(socketio, 'thread'):
        socketio.thread = socketio.start_background_task(target=video_stream)

if __name__ == '__main__':
    socketio.run(app)
