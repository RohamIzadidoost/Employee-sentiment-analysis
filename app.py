
import cv2
from deepface import DeepFace
import numpy as np
from flask import Flask, Response, render_template, request
import threading

app = Flask(__name__)

# Load Haar cascade for face detection (optional)
haar_cascade_path = 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(haar_cascade_path)
use_haar_cascade = not face_cascade.empty()

if not use_haar_cascade:
    print("Warning: Could not load Haar cascade file. Falling back to DeepFace face detection.")

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Global variables for stream control
streaming = False
lock = threading.Lock()
last_emotions = []

def generate_frames():
    global streaming, last_emotions
    while True:
        with lock:
            if not streaming:
                continue

            # Capture frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                break

            # Initialize list of face bounding boxes
            faces = []

            if use_haar_cascade:
                # Convert to grayscale for Haar cascade
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray_frame,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
            else:
                # Use DeepFace for face detection
                try:
                    result = DeepFace.analyze(
                        frame,
                        actions=['emotion'],
                        enforce_detection=False,
                        detector_backend='opencv'
                    )
                    faces = [(face_data['region']['x'], face_data['region']['y'],
                              face_data['region']['w'], face_data['region']['h'])
                             for face_data in result]
                except Exception as e:
                    print(f"Error detecting faces with DeepFace: {e}")
                    faces = []

            # Process each detected face
            last_emotions = []
            for (x, y, w, h) in faces:
                face_roi = frame[y:y+h, x:x+w]
                try:
                    result = DeepFace.analyze(
                        face_roi,
                        actions=['emotion'],
                        enforce_detection=False
                    )
                    dominant_emotion = result[0]['dominant_emotion']
                    last_emotions.append(dominant_emotion)

                    # Draw rectangle and emotion label
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        dominant_emotion,
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (0, 255, 0),
                        2
                    )
                except Exception as e:
                    print(f"Error analyzing face: {e}")
                    continue

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start', methods=['POST'])
def start_stream():
    global streaming
    with lock:
        streaming = True
    return {'status': 'Stream started'}

@app.route('/stop', methods=['POST'])
def stop_stream():
    global streaming
    with lock:
        streaming = False
    return {'status': 'Stream stopped'}

@app.route('/emotions', methods=['GET'])
def get_emotions():
    return {'emotions': last_emotions}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)