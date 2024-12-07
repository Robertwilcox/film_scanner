from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # Import CORS
import cv2
import numpy as np
import io

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def home():
    return "Film Scanner Backend is Running"

@app.route('/process', methods=['POST'])
def process_image():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    # Read the uploaded file
    file = request.files['file']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Step 1: Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 2: Apply edge detection (or replace with advanced processing)
    edges = cv2.Canny(gray, 50, 150)

    # Step 3: Encode the processed image to bytes
    _, buffer = cv2.imencode('.jpg', edges)
    return send_file(io.BytesIO(buffer), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True)
