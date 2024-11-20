/*
    script.js
    Project: 35mm Film Scanner Progressive Web App
    Author: Robert Wilcox
    Description: JavaScript for managing folder creation, image capture, uploading,
                 processing negatives into positives, and downloading. Includes IndexedDB
                 integration for persistence and camera scanning functionality.
*/

// UI Elements
const folderView = document.getElementById('folder-view');
const folderContentsView = document.getElementById('folder-contents-view');
const scanningView = document.getElementById('scanning-view');
const folderList = document.getElementById('folder-list');
const folderImages = document.getElementById('folder-images');
const scanBtn = document.getElementById('scan-btn');
const startScanBtn = document.getElementById('start-scan-btn');
const captureBtn = document.getElementById('capture-btn');
const currentFolderName = document.getElementById('current-folder-name');
const backToMenuBtnContents = document.getElementById('back-to-menu-btn-contents');
const backToMenuBtnScan = document.getElementById('back-to-menu-btn-scan');
const camera = document.getElementById('camera');
const canvas = document.getElementById('canvas');
const imageModal = document.getElementById('image-modal');
const modalImage = document.getElementById('modal-image');
const closeModal = document.getElementById('close-modal');
const downloadAllBtn = document.getElementById('download-all-btn');

// New UI Elements for Image Upload and Processing
const uploadImageBtn = document.getElementById('upload-image-btn');
const imageUploadInput = document.getElementById('image-upload-input');
const processBtn = document.getElementById('process-btn'); // Process Image Button

let imagesDB = null; // IndexedDB instance
let activeFolder = ''; // Current folder selected

// Initialize IndexedDB
function initIndexedDB() {
    const request = indexedDB.open('FilmScannerDB', 1);

    request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains('images')) {
            db.createObjectStore('images', { keyPath: 'id', autoIncrement: true });
            console.log('Object store "images" created.');
        }
    };

    request.onsuccess = (event) => {
        imagesDB = event.target.result;
        console.log('IndexedDB initialized successfully.');

        // Clear all data on app startup
        clearIndexedDB();
    };

    request.onerror = (event) => {
        console.error('IndexedDB initialization failed:', event.target.error);
    };
}

// Clear all data from IndexedDB
function clearIndexedDB() {
    if (!imagesDB) {
        console.error('Cannot clear: IndexedDB is not initialized.');
        return;
    }

    const transaction = imagesDB.transaction('images', 'readwrite');
    const store = transaction.objectStore('images');
    const clearRequest = store.clear();

    clearRequest.onsuccess = () => {
        console.log('All data cleared from IndexedDB.');
        updateFolderList([]); // Clear folder list in UI
    };

    clearRequest.onerror = (event) => {
        console.error('Error clearing IndexedDB:', event.target.error);
    };
}

// Save image to IndexedDB
function saveToIndexedDB(imageBlob, fileName, folderName = activeFolder) {
    if (!imagesDB) {
        console.error('Cannot save: IndexedDB is not initialized.');
        return;
    }

    const transaction = imagesDB.transaction('images', 'readwrite');
    const store = transaction.objectStore('images');
    store.add({ name: fileName, blob: imageBlob, folder: folderName });

    transaction.oncomplete = () => {
        console.log(`Image saved: ${fileName}`);
        retrieveFromIndexedDB(); // Update folder contents
    };

    transaction.onerror = (event) => {
        console.error('Error saving to IndexedDB:', event.target.error);
        alert('Failed to save image. Please try again.');
    };
}

// Retrieve images and folders from IndexedDB
function retrieveFromIndexedDB() {
    if (!imagesDB) {
        console.error('Cannot retrieve images: IndexedDB is not initialized.');
        return;
    }

    const transaction = imagesDB.transaction('images', 'readonly');
    const store = transaction.objectStore('images');
    const request = store.getAll();

    request.onsuccess = (event) => {
        const images = event.target.result;
        console.log('Images retrieved:', images);

        const folderMap = images.reduce((map, image) => {
            if (!map[image.folder]) {
                map[image.folder] = [];
            }
            map[image.folder].push(image);
            return map;
        }, {});

        updateFolderList(Object.entries(folderMap));

        if (activeFolder) {
            displayFolderContents(folderMap[activeFolder] || []);
        }
    };

    request.onerror = (event) => {
        console.error('Error retrieving from IndexedDB:', event.target.error);
    };
}

// Update folder list in UI
function updateFolderList(folders) {
    folderList.innerHTML = '';

    folders.forEach(([folderName, images]) => {
        const listItem = document.createElement('li');
        listItem.textContent = `${folderName} (${images.length} images)`;
        listItem.addEventListener('click', () => {
            activeFolder = folderName;
            currentFolderName.textContent = `Folder: ${folderName}`;
            folderView.style.display = 'none';
            folderContentsView.style.display = 'flex';
            displayFolderContents(images);
        });
        folderList.appendChild(listItem);
    });
}

// Display folder contents
function displayFolderContents(images) {
    folderImages.innerHTML = '';

    images.forEach((image) => {
        if (!(image.blob instanceof Blob)) {
            console.error('Invalid blob detected. Skipping image:', image);
            return;
        }

        const imageUrl = URL.createObjectURL(image.blob);

        const img = document.createElement('img');
        img.src = imageUrl;
        img.classList.add('folder-image');
        img.addEventListener('click', () => openImageModal(imageUrl));
        folderImages.appendChild(img);
    });
}

// Open image in modal viewer
function openImageModal(imageUrl) {
    modalImage.src = imageUrl;
    imageModal.style.display = 'flex';
}

// Close the modal viewer
closeModal.addEventListener('click', () => {
    imageModal.style.display = 'none';
});

// Handle image uploads
uploadImageBtn.addEventListener('click', () => {
    imageUploadInput.click();
});

imageUploadInput.addEventListener('change', (event) => {
    const file = event.target.files[0];

    if (!file) {
        alert('No file selected. Please choose an image.');
        return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
        const imageBlob = new Blob([e.target.result], { type: file.type });
        const fileName = file.name;

        // Save the image to IndexedDB
        saveToIndexedDB(imageBlob, fileName);
    };

    reader.onerror = (err) => {
        console.error('Error reading file:', err);
        alert('Failed to read file. Please try again.');
    };

    reader.readAsArrayBuffer(file); // Read the file as an ArrayBuffer
});

// Select or create a folder
scanBtn.addEventListener('click', () => {
    const folderName = prompt('Enter a folder name (existing or new):');
    if (folderName) {
        activeFolder = folderName;
        currentFolderName.textContent = `Folder: ${folderName}`;
        folderView.style.display = 'none';
        folderContentsView.style.display = 'flex';
        retrieveFromIndexedDB();
    } else {
        alert('No folder name entered. Please try again.');
    }
});

// Process images in the selected folder
processBtn.addEventListener('click', async () => {
    if (!activeFolder) {
        alert('Please select a folder first.');
        return;
    }

    // Retrieve all images from the current folder
    const transaction = imagesDB.transaction('images', 'readonly');
    const store = transaction.objectStore('images');
    const request = store.getAll();

    request.onsuccess = async (event) => {
        const images = event.target.result.filter(image => image.folder === activeFolder);

        if (images.length === 0) {
            alert('No images to process in this folder.');
            return;
        }

        // Create a new folder for processed images
        const processedFolderName = `processed_${activeFolder}`;
        for (let image of images) {
            // Process each image
            const processedImageBlob = await processImage(image.blob);

            // Save the processed image to the new folder
            saveToIndexedDB(processedImageBlob, `processed_${image.name}`, processedFolderName);
        }

        alert(`Processed images have been saved to the folder: ${processedFolderName}`);
    };

    request.onerror = (event) => {
        console.error('Error retrieving images for processing:', event.target.error);
        alert('Failed to retrieve images for processing.');
    };
});

// Process a single image (convert negative to positive)
async function processImage(imageBlob) {
    return new Promise((resolve) => {
        const img = new Image();
        const ctx = canvas.getContext('2d');

        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;

            for (let i = 0; i < data.length; i += 4) {
                data[i] = 255 - data[i];     // Invert Red
                data[i + 1] = 255 - data[i + 1]; // Invert Green
                data[i + 2] = 255 - data[i + 2]; // Invert Blue
            }

            ctx.putImageData(imageData, 0, 0);

            canvas.toBlob((processedBlob) => {
                resolve(processedBlob);
            }, 'image/jpeg');
        };

        img.onerror = () => {
            console.error('Failed to process image.');
            resolve(null);
        };

        img.src = URL.createObjectURL(imageBlob);
    });
}

// Return to the main menu
backToMenuBtnContents.addEventListener('click', () => {
    folderContentsView.style.display = 'none';
    folderView.style.display = 'flex';
    retrieveFromIndexedDB();
});

backToMenuBtnScan.addEventListener('click', () => {
    scanningView.style.display = 'none';
    folderView.style.display = 'flex';
    retrieveFromIndexedDB();
});

// Start scanning
startScanBtn.addEventListener('click', () => {
    folderContentsView.style.display = 'none';
    scanningView.style.display = 'flex';
    startCamera();
});

// Start camera with tap-to-focus capabilities
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

        // Enable tap-to-focus
        setupTapToFocus(camera);
    } catch (error) {
        console.error('Error starting camera:', error);
        alert('Failed to access the camera.');
    }
}

// Tap-to-Focus Using Built-In Autofocus
function setupTapToFocus(videoElement) {
    videoElement.addEventListener('touchstart', async (event) => {
        if (videoElement.srcObject && videoElement.srcObject.getVideoTracks) {
            const [track] = videoElement.srcObject.getVideoTracks();

            // Check if autofocus is supported
            if (!track.getCapabilities || !track.applyConstraints) {
                console.error('Manual focus is not supported on this device/browser.');
                return;
            }

            const capabilities = track.getCapabilities();
            if (!capabilities.focusMode || !capabilities.focusMode.includes('auto')) {
                console.error('Autofocus is not supported on this camera.');
                return;
            }

            console.log('Triggering autofocus...');

            try {
                // Set focus mode to 'auto' to trigger autofocus
                await track.applyConstraints({
                    advanced: [{ focusMode: 'auto' }],
                });

                console.log('Autofocus triggered successfully.');

                // Optionally reset focus mode to 'continuous' after a short delay
                setTimeout(async () => {
                    if (capabilities.focusMode.includes('continuous')) {
                        await track.applyConstraints({
                            advanced: [{ focusMode: 'continuous' }],
                        });
                        console.log('Focus mode reset to continuous.');
                    }
                }, 2000); // Adjust delay as needed
            } catch (err) {
                console.error('Error triggering autofocus:', err);
            }
        } else {
            console.error('No video track available for autofocus.');
        }
    });
}

// Capture image
captureBtn.addEventListener('click', () => {
    const ctx = canvas.getContext('2d');
    canvas.width = camera.videoWidth;
    canvas.height = camera.videoHeight;
    ctx.drawImage(camera, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        const fileName = `Image_${Date.now()}.png`;
        saveToIndexedDB(blob, fileName);
        alert('Image captured and saved!');
    }, 'image/png');
});

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    folderView.style.display = 'flex'; // Show folder view on load
    initIndexedDB(); // Initialize IndexedDB
});
