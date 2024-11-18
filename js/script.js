/*
    Project: 35mm Film Scanner Progressive Web App
    Author: Robert Wilcox
    Course: EE 513
    Description: Handles folder management, viewing folder contents, image capture, and saving images to the local file system using File System Access API.
*/

// UI Elements
const folderView = document.getElementById('folder-view');
const folderContentsView = document.getElementById('folder-contents-view');
const scanningView = document.getElementById('scanning-view');
const folderList = document.getElementById('folders');
const folderImages = document.getElementById('folder-images');
const noFoldersMsg = document.getElementById('no-folders-msg');
const scanBtn = document.getElementById('scan-btn');
const startScanBtn = document.getElementById('start-scan-btn');
const backToMenuBtnContents = document.getElementById('back-to-menu-btn-contents');
const backToMenuBtnScan = document.getElementById('back-to-menu-btn-scan');
const currentFolderName = document.getElementById('current-folder-name');
const camera = document.getElementById('camera');
const canvas = document.getElementById('canvas');
const captureBtn = document.getElementById('capture-btn');

let folderHandle = null; // Store user's selected folder

// Update the folder view
function updateFolderView() {
    if (folderHandle) {
        noFoldersMsg.style.display = 'none';
        folderList.innerHTML = ''; // Clear any previous list

        const li = document.createElement('li');
        li.textContent = `Selected Folder: ${folderHandle.name}`;
        li.addEventListener('click', listImages); // View folder contents
        folderList.appendChild(li);
    } else {
        noFoldersMsg.style.display = 'block';
    }
}

// Return to the main menu
function returnToMainMenu() {
    folderView.style.display = 'flex';
    folderContentsView.style.display = 'none';
    scanningView.style.display = 'none';

    // Stop the camera if active
    const stream = camera.srcObject;
    if (stream) {
        stream.getTracks().forEach((track) => track.stop());
        camera.srcObject = null;
    }

    updateFolderView(); // Ensure the UI is updated
}

// Start scanning
function startScanning() {
    if (!folderHandle) {
        alert('Please select a folder first!');
        return;
    }

    folderContentsView.style.display = 'none';
    scanningView.style.display = 'flex';
    startCamera();
}

// Start the camera
async function startCamera() {
    try {
        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment',
            },
        };
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        camera.srcObject = stream;
    } catch (error) {
        console.error('Error accessing the camera:', error);
    }
}

// Notify the user of a successful capture
function showCaptureNotification() {
    const notification = document.createElement('div');
    notification.textContent = 'Capture Successful!';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.backgroundColor = '#28a745';
    notification.style.color = '#fff';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '5px';
    notification.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.2)';
    notification.style.zIndex = '1000';
    notification.style.fontSize = '16px';

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Select a folder to save images
scanBtn.addEventListener('click', async () => {
    try {
        folderHandle = await window.showDirectoryPicker(); // Ask user to select a folder
        alert('Folder selected! You can now scan and save images.');
        updateFolderView(); // Update UI to reflect folder selection
    } catch (error) {
        console.error('Folder selection canceled:', error);
    }
});

// Capture and save an image
captureBtn.addEventListener('click', async () => {
    if (!folderHandle) {
        alert('Please select a folder first!');
        return;
    }

    // Capture the image from the camera
    canvas.width = camera.videoWidth;
    canvas.height = camera.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(camera, 0, 0, canvas.width, canvas.height);

    // Convert the image to a Blob
    const imageBlob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
    const timestamp = Date.now();
    const fileName = `Image_${timestamp}.png`;

    // Save the image as a file in the selected folder
    try {
        const fileHandle = await folderHandle.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(imageBlob);
        await writable.close();
        alert(`Image saved as ${fileName}`);
        showCaptureNotification();
    } catch (error) {
        console.error('Error saving image:', error);
    }
});

// List images in the selected folder
async function listImages() {
    if (!folderHandle) {
        alert('Please select a folder first!');
        return;
    }

    folderContentsView.style.display = 'flex';
    folderView.style.display = 'none';

    folderImages.innerHTML = ''; // Clear previous images

    for await (const [name, handle] of folderHandle.entries()) {
        if (handle.kind === 'file') {
            const file = await handle.getFile();
            const imageUrl = URL.createObjectURL(file);

            const img = document.createElement('img');
            img.src = imageUrl;
            img.classList.add('folder-image');
            folderImages.appendChild(img);
        }
    }
}

// Button events
startScanBtn.addEventListener('click', startScanning);
backToMenuBtnContents.addEventListener('click', returnToMainMenu);
backToMenuBtnScan.addEventListener('click', returnToMainMenu);

// Initial setup
returnToMainMenu();
