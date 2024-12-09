'''
Bounding Box Detection Utilities

This module provides functions for detecting and refining 
bounding boxes in images, particularly for film negatives, 
using edge detection, contour analysis, and perforation 
statistics.

Author: Robert Wilcox
Email: robertraywilcox@gmail.com
Date: December 9, 2024
'''

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
    "blur_kernel": (5, 5),      # Gaussian blur kernel size
    "canny_threshold1": 10,    # Lower threshold for Canny edge detection
    "canny_threshold2": 50,    # Upper threshold for Canny edge detection
    "sobel_kernel": 3,         # Sobel operator kernel size
}
MORPHOLOGY_PARAMS = {
    "kernel_size": (7, 7),      # Morphological kernel size
    "dilation_iterations": 3,  # Dilation iterations for edge connection
}
CONTOUR_FILTER_PARAMS = {
    "min_contour_area": 10,    # Minimum contour area for detection
}
NEGATIVE_BOX_PARAMS = {
    "width_multiplier": 9,     # Multiplier for width based on perf stats
    "height_multiplier": 9,    # Multiplier for height based on perf stats
    "width_tolerance": 0.7,    # Tolerance for width
    "height_tolerance": 0.7,    # Tolerance for height
    "min_aspect_ratio": 1.0,    # Minimum aspect ratio
    "max_aspect_ratio": 2.2,    # Maximum aspect ratio
}


def detect_initial_boxes(image):
    """
    Detect initial bounding boxes using aggressive edge detection 
    and contour techniques.

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
    sobel_x = cv2.Sobel(
        blurred, cv2.CV_64F, 1, 0, ksize=EDGE_DETECTION_PARAMS["sobel_kernel"]
    )
    sobel_y = cv2.Sobel(
        blurred, cv2.CV_64F, 0, 1, ksize=EDGE_DETECTION_PARAMS["sobel_kernel"]
    )
    sobel_combined = cv2.convertScaleAbs(cv2.addWeighted(sobel_x, 1.0, sobel_y, 1.0, 0))
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_sobel_combined.jpg"), sobel_combined)

    # Use aggressive Canny edge detection
    canny_edges = cv2.Canny(
        sobel_combined,
        EDGE_DETECTION_PARAMS["canny_threshold1"],
        EDGE_DETECTION_PARAMS["canny_threshold2"],
    )
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_canny_edges.jpg"), canny_edges)

    # Dilate edges to strengthen connectivity
    dilation_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    dilated_edges = cv2.dilate(
        canny_edges, dilation_kernel, iterations=MORPHOLOGY_PARAMS["dilation_iterations"]
    )
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


def filter_boxes_with_perforation_data(bboxes, perf_stats, image_shape):
    """
    Filters bounding boxes using perforation data to refine the selection.

    Args:
        bboxes (list): List of bounding boxes.
        perf_stats (dict): Perforation statistics.
        image_shape (tuple): Shape of the image.

    Returns:
        list: Refined bounding boxes.
    """
    refined_bboxes = []
    debug_image = np.zeros((image_shape[0], image_shape[1], 3), dtype=np.uint8)

    # Compute orientation-based dimensions
    average_aspect_ratio = perf_stats["average_aspect_ratio"]
    print(f"Average Perforation Aspect Ratio: {average_aspect_ratio}")

    width_multiplier = NEGATIVE_BOX_PARAMS["width_multiplier"]
    height_multiplier = NEGATIVE_BOX_PARAMS["height_multiplier"]

    # Compute expected dimensions for negatives
    expected_width = perf_stats["average_width"] * width_multiplier
    expected_height = perf_stats["average_height"] * height_multiplier

    # Print expected dimensions
    print(
        f"Expected bounding box size: Width: {expected_width:.2f}, "
        f"Height: {expected_height:.2f}"
    )

    # Calculate tolerance ranges
    width_range = (
        (1 - NEGATIVE_BOX_PARAMS["width_tolerance"]) * expected_width,
        (1 + NEGATIVE_BOX_PARAMS["width_tolerance"]) * expected_width,
    )
    height_range = (
        (1 - NEGATIVE_BOX_PARAMS["height_tolerance"]) * expected_height,
        (1 + NEGATIVE_BOX_PARAMS["height_tolerance"]) * expected_height,
    )
    print(f"Filtering with Width range: {width_range}, Height range: {height_range}")

    for box in bboxes:
        try:
            x, y, w, h = cv2.boundingRect(np.array(box))  # Get bounding rect
            if w <= 0 or h <= 0:
                continue

            long_side = max(w, h)
            short_side = min(w, h)
            aspect_ratio = long_side / short_side

            if (
                width_range[0] <= w <= width_range[1]
                and height_range[0] <= h <= height_range[1]
                and NEGATIVE_BOX_PARAMS["min_aspect_ratio"]
                <= aspect_ratio
                <= NEGATIVE_BOX_PARAMS["max_aspect_ratio"]
            ):
                refined_bboxes.append(box)  # Append the original box
                # Draw the refined box on the debug image
                cv2.drawContours(debug_image, [np.intp(box)], -1, (0, 255, 0), 2)
        except Exception as e:
            print(f"Error processing box {box}: {e}")

    print(f"Refined bounding boxes: {len(refined_bboxes)}")
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_refined_boxes.jpg"), debug_image)
    return refined_bboxes


def auto_detect_bboxes_with_perforations(image, perf_stats):
    """
    Auto-detect bounding boxes for negatives.

    Args:
        image (numpy.ndarray): Input image.
        perf_stats (dict): Perforation statistics.

    Returns:
        list: Final bounding boxes.
    """
    initial_boxes = detect_initial_boxes(image)
    refined_boxes = filter_boxes_with_perforation_data(
        initial_boxes, perf_stats, image.shape
    )
    return refined_boxes