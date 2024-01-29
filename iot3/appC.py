from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import base64
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Inicializa la captura de video desde la cámara (ajusta el índice según tu configuración)
cap = cv2.VideoCapture(0)

# Contador global
frame_count = 0

def video_stream():
    global frame_count
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Incrementa el contador
        frame_count += 1

        # Dibuja el contador en la esquina superior izquierda del video
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, f'Frame Count: {frame_count}', (10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Codifica el marco a formato JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        jpg_data = base64.b64encode(buffer).decode('utf-8')

        # Envía el marco codificado y el contador a través de WebSocket
        socketio.emit('video_frame', {'frame': jpg_data, 'count': frame_count})

        # Espera un breve período de tiempo para no sobrecargar la conexión
        socketio.sleep(0.1)

# Ruta principal para mostrar la página web
@app.route('/')
def index():
    return render_template('index2.html')

# Manejador de conexión para iniciar la transmisión de video en un hilo separado
@socketio.on('connect')
def handle_connect():
    if not hasattr(socketio, 'thread'):
        socketio.thread = socketio.start_background_task(target=video_stream)

if __name__ == '__main__':
    socketio.run(app)
