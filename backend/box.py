import cv2
import os
import numpy as np

# Debug directory
DEBUG_DIR = "debug"

# Ensure the debug directory exists
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# Parameters for edge detection and contour filtering
EDGE_DETECTION_PARAMS = {
    "blur_kernel": (5, 5),  # Gaussian blur kernel size
    "canny_threshold1": 10,  # Lower threshold for Canny edge detection
    "canny_threshold2": 50,  # Upper threshold for Canny edge detection
    "sobel_kernel": 3,  # Sobel operator kernel size
}
MORPHOLOGY_PARAMS = {
    "kernel_size": (7, 7),  # Morphological kernel size
    "dilation_iterations": 3,  # Dilation iterations for better edge connection
}
CONTOUR_FILTER_PARAMS = {
    "min_contour_area": 10,  # Very small contour area to allow maximum detection
}


def detect_initial_boxes(image):
    """
    Detect initial bounding boxes using aggressive edge detection and contour techniques.

    Args:
        image (numpy.ndarray): Input image.

    Returns:
        list: Detected bounding boxes as rotated rectangles.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply GaussianBlur to reduce noise
    blurred = cv2.GaussianBlur(gray, EDGE_DETECTION_PARAMS["blur_kernel"], 0)

    # Sobel gradient (horizontal and vertical) for edge detection
    sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=EDGE_DETECTION_PARAMS["sobel_kernel"])
    sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=EDGE_DETECTION_PARAMS["sobel_kernel"])
    sobel_combined = cv2.convertScaleAbs(cv2.addWeighted(sobel_x, 1.0, sobel_y, 1.0, 0))
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_sobel_combined.jpg"), sobel_combined)

    # Adaptive thresholding for aggressive line detection
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_adaptive_threshold.jpg"), adaptive_thresh)

    # Combine Sobel and adaptive threshold results
    combined_edges = cv2.bitwise_or(adaptive_thresh, sobel_combined)

    # Use very aggressive Canny edge detection
    canny_edges = cv2.Canny(combined_edges, EDGE_DETECTION_PARAMS["canny_threshold1"], EDGE_DETECTION_PARAMS["canny_threshold2"])
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_canny_edges.jpg"), canny_edges)

    # Dilate edges to strengthen connectivity
    dilation_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    dilated_edges = cv2.dilate(canny_edges, dilation_kernel, iterations=MORPHOLOGY_PARAMS["dilation_iterations"])
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_dilated_edges.jpg"), dilated_edges)

    # Find contours from the dilated edges
    contours, _ = cv2.findContours(dilated_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Extract bounding boxes as rotated rectangles
    initial_boxes = []
    debug_image = image.copy()

    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area > CONTOUR_FILTER_PARAMS["min_contour_area"]:
            rot_rect = cv2.minAreaRect(contour)  # Handles rotated rectangles
            box = cv2.boxPoints(rot_rect)
            box = np.intp(box)  # Convert to integer
            initial_boxes.append(box)
            # Draw the detected box on the debug image
            cv2.drawContours(debug_image, [box], -1, (0, 255, 0), 2)

    print(f"Initial bounding boxes detected: {len(initial_boxes)}")
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_initial_boxes.jpg"), debug_image)

    return initial_boxes
