from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import base64
import threading
import pickle
import cvzone
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

cap = cv2.VideoCapture("carPark.mp4")

with open('CarParkPos', 'rb') as f:
    posList = pickle.load(f)
width, height = 107, 48

# Contador global
frame_count = 0

def video_stream():
    global frame_count
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        imgGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        imgMedian = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        imgDilate = cv2.dilate(imgMedian, kernel, 1)

        spaceCounter = 0

        for pos in posList:
            x, y = pos
            imgCrop = imgDilate[y: y + height, x: x + width]
            count = cv2.countNonZero(imgCrop)

            if count < 950:
                color = (0, 255, 0)
                thickness = 5
                spaceCounter += 1
            else:
                color = (0, 0, 255)
                thickness = 2

            cv2.rectangle(frame, pos, (pos[0] + width, pos[1] + height), color, thickness)
            cvzone.putTextRect(frame, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)

        cvzone.putTextRect(frame, f'Free spaces: {spaceCounter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 210, 0))

        _, buffer = cv2.imencode('.jpg', frame)
        jpg_data = base64.b64encode(buffer).decode('utf-8')

        socketio.emit('video_frame', {'frame': jpg_data, 'count': frame_count})

        socketio.sleep(0.1)

@app.route('/')
def index():
    return render_template('index2.html')

@socketio.on('connect')
def handle_connect():
    if not hasattr(socketio, 'thread'):
        socketio.thread = socketio.start_background_task(target=video_stream)

if __name__ == '__main__':
    socketio.run(app)
