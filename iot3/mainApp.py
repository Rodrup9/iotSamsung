from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import pickle
import cvzone
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

cap = cv2.VideoCapture(0)

with open('CarParkPos', 'rb') as f:
    posList = pickle.load(f)
width, height = 107, 48

def check_parking_space(img_pro):
    space_counter = 0

    for pos in posList:
        x, y = pos
        img_crop = img_pro[y: y + height, x: x + width]
        count = cv2.countNonZero(img_crop)

        if count < 950:
            color = (0, 255, 0)
            thickness = 5
            space_counter += 1
        else:
            color = (0, 0, 255)
            thickness = 2

        cv2.rectangle(img_pro, pos, (pos[0] + width, pos[1] + height), color, thickness)
        cvzone.putTextRect(img_pro, str(count), (x, y + height - 3), scale=1, thickness=2, offset=0, colorR=color)

    cvzone.putTextRect(img_pro, f'Free spaces: {space_counter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20,
                       colorR=(0, 210, 0))

    return img_pro  # Retorna la imagen modificada

def video_stream():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        img_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        img_blur = cv2.GaussianBlur(img_gray, (3, 3), 1)
        img_threshold = cv2.adaptiveThreshold(img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        img_median = cv2.medianBlur(img_threshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        img_dilate = cv2.dilate(img_median, kernel, 1)

        img_with_markers = check_parking_space(img_dilate)

        _, buffer = cv2.imencode('.jpg', img_with_markers)
        jpg_data = buffer.tobytes()

        socketio.emit('video_frame', {'frame': jpg_data})

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
