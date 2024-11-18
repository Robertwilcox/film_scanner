/*
    Project: 35mm Film Scanner Progressive Web App
    Author: Robert Wilcox
    Course: EE 513
    Description: JavaScript file for the Film Scanner app, responsible for accessing the
                 device's camera, displaying the live video feed, and capturing high-quality images 
                 for further processing.

                 11/18/24 Updated interface

*/

// Select HTML elements: video, canvas, and capture button
const video = document.getElementById('camera'); // Video element for live camera feed
const canvas = document.getElementById('canvas'); // Canvas element for displaying captured images
const captureBtn = document.getElementById('capture-btn'); // Button to trigger high-quality image capture

// Function to access the device's camera with higher resolution
async function startCamera() {
    try {
        // Define constraints for requesting Full HD resolution with the back camera
        const constraints = {
            video: {
                width: { ideal: 1920 },  // Request Full HD width
                height: { ideal: 1080 }, // Request Full HD height
                facingMode: "environment" // Prefer the back camera for better quality
            }
        };
        
        // Access the camera stream with specified constraints
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
    } catch (error) {
        // Log any errors in accessing the camera to the console
        console.error("Error accessing camera:", error);
    }
}

// Function to capture a high-quality image using the Image Capture API
async function captureHighQualityImage() {
    try {
        // Access the first video track from the camera stream
        const track = video.srcObject.getVideoTracks()[0];
        const imageCapture = new ImageCapture(track);
        
        // Capture a high-resolution photo
        const photo = await imageCapture.takePhoto();
        
        // Create a new image element to display the captured photo
        const img = document.createElement("img");
        img.src = URL.createObjectURL(photo); // Convert photo blob to URL
        document.body.appendChild(img); // Append the captured image to the body for viewing
        
    } catch (error) {
        // Log any errors related to image capture to the console
        console.error("Error capturing high-quality image:", error);
    }
}

// Start the camera with high resolution when the page loads
window.addEventListener('load', startCamera);

// Attach event listener to capture button for high-quality image capture
captureBtn.addEventListener('click', captureHighQualityImage);
