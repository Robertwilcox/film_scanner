'''
Film Scanner Backend Application

This file implements the backend server for the film scanner project. 
The backend is built using Flask and provides endpoints for 
processing 35mm film negatives. It handles the following:

- Receiving uploaded images through HTTP POST requests.
- Automatically detecting and cropping individual film frames 
  from the uploaded images.
- Saving the processed frames to a specified directory.
- Serving the processed frames through a dedicated endpoint.

Author: Robert Wilcox
Email: robertraywilcox@gmail.com
Date: December 9, 2024
'''

from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
import cv2
import numpy as np
import os
import traceback

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Directory to save cropped frames
OUTPUT_DIR = os.path.abspath("processed_frames")

# Create the output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


@app.route('/')
def home():
    '''Default route to confirm the backend is running.'''
    return "Film Scanner Backend is Running"


def auto_crop_negatives(image):
    '''
    Automatically detects and crops individual frames from a 
    35mm film negative image.

    Parameters:
        image (numpy.ndarray): The input image to process.

    Returns:
        list: A list of cropped images (numpy.ndarray).

    Raises:
        ValueError: If no frames are detected in the image.
        Exception: If an error occurs during processing.
    '''
    try:
        print("Starting auto-cropping...")

        # Convert the image to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        print("Converted image to grayscale.")

        # Apply thresholding to isolate frames
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        print("Applied thresholding to isolate frames.")

        # Find contours in the thresholded image
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        print(f"Contours found: {len(contours)}")

        if not contours:
            raise ValueError("No frames detected in the uploaded image.")

        cropped_images = []
        for i, contour in enumerate(contours):
            # Compute bounding box with a small margin
            x, y, w, h = cv2.boundingRect(contour)
            margin = 10
            x, y = max(0, x - margin), max(0, y - margin)
            w, h = min(image.shape[1] - x, w + margin * 2), \
                min(image.shape[0] - y, h + margin * 2)

            # Crop the detected frame
            cropped = image[y:y+h, x:x+w]
            cropped_images.append(cropped)
            print(f"Cropped frame {i}: x={x}, y={y}, w={w}, h={h}")

        print("Auto-cropping complete.")
        return cropped_images

    except ValueError as e:
        print(f"ValueError: {e}")
        raise  # Re-raise the ValueError for handling in the route
    except Exception as e:
        print(f"Error during auto-cropping: {e}")
        traceback.print_exc()
        raise  # Re-raise the exception for handling in the route


@app.route('/process', methods=['POST'])
def process_image():
    '''
    Endpoint to process an uploaded image and crop detected frames.

    Returns:
        tuple: A tuple containing a JSON response and a status code. 
               The JSON response contains URLs of the processed frames 
               or an error message.
    '''
    try:
        print("Request received at /process")

        # Validate uploaded file
        if 'file' not in request.files:
            print("No file part in the request.")
            return jsonify({'error': 'No file uploaded.'}), 400

        file = request.files['file']
        print(f"Processing file: {file.filename}")

        # Decode the uploaded image
        file_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if image is None:
            print("Failed to decode image.")
            return jsonify({'error': 'Invalid image file.'}), 400

        print("Image successfully decoded.")

        # Perform auto-cropping
        cropped_images = auto_crop_negatives(image)

        if not cropped_images:
            print("No negative frames detected in the image.")
            return jsonify({'error': 'No frames detected.'}), 400

        # Save cropped frames
        processed_files = []
        for i, cropped in enumerate(cropped_images):
            try:
                output_path = os.path.join(OUTPUT_DIR, f"frame_{i}.jpg")
                cv2.imwrite(output_path, cropped)
                print(f"Frame saved to: {output_path}")
                processed_files.append(
                    url_for(
                        'serve_processed_frames', 
                        filename=f"frame_{i}.jpg", 
                        _external=True
                    )
                )
            except Exception as e:
                print(f"Failed to save frame {i}: {e}")
                traceback.print_exc()
                continue  # Skip to the next frame

        print(f"Processing complete. Files saved: {processed_files}")
        return jsonify({'processed_files': processed_files}), 200

    except ValueError as e:
        print(f"ValueError: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Unhandled error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'An unexpected error occurred.'}), 500


@app.route('/processed_frames/<filename>', methods=['GET'])
def serve_processed_frames(filename):
    '''
    Endpoint to serve a processed frame by filename.

    Parameters:
        filename (str): The name of the file to retrieve.

    Returns:
        Response: The requested file or an error message if not found.
    '''
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return jsonify({'error': f'File {filename} not found.'}), 404

        print(f"Serving file: {file_path}")
        return send_from_directory(OUTPUT_DIR, filename)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to serve the file.'}), 404


if __name__ == '__main__':
    '''Start the Flask development server.'''
    print(f"Starting Film Scanner Backend...")
    print(f"Output directory: {OUTPUT_DIR}")
    print("Make sure the frontend is pointed to http://127.0.0.1:5000/")
    app.run(debug=True)