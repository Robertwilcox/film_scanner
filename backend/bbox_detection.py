import cv2
import os
import numpy as np

# Debug directory
DEBUG_DIR = "debug"

# Ensure the debug directory exists
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# Adjustable parameters
EDGE_DETECTION_PARAMS = {
    "blur_kernel": (5, 5),  # Gaussian blur kernel size
    "median_kernel": 3,  # Median filter kernel size
    "adaptive_threshold_block_size": 11,  # Block size for adaptive thresholding
    "adaptive_threshold_C": 2,  # Constant to subtract in adaptive thresholding
    "canny_threshold1": 30,  # Lower threshold for Canny edge detection
    "canny_threshold2": 100,  # Upper threshold for Canny edge detection
    "sobel_kernel": 3,  # Sobel operator kernel size
}
MORPHOLOGY_PARAMS = {
    "kernel_size": (7, 7),  # Morphological kernel size
    "dilation_iterations": 2,  # Dilation iterations for better edge connection
    "closing_iterations": 1,  # Closing iterations for filling gaps
}
CONTOUR_FILTER_PARAMS = {
    "min_contour_area": 100,  # Minimum contour area to consider
}
NEGATIVE_BOX_PARAMS = {
    "width_multiplier": 9,  # Multiplier for width based on perforation stats
    "height_multiplier": 9,  # Multiplier for height based on perforation stats
    "width_tolerance": 0.4,  # ±30% tolerance for width
    "height_tolerance": 0.4,  # ±30% tolerance for height
    "min_aspect_ratio": 1.3,  # Minimum aspect ratio
    "max_aspect_ratio": 2.0,  # Maximum aspect ratio
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
    sobel_combined = cv2.convertScaleAbs(cv2.addWeighted(sobel_x, 0.5, sobel_y, 0.5, 0))
    _, sobel_threshold = cv2.threshold(sobel_combined, 50, 255, cv2.THRESH_BINARY)
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_sobel_threshold.jpg"), sobel_threshold)

    # Adaptive thresholding for aggressive line detection
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, EDGE_DETECTION_PARAMS["adaptive_threshold_block_size"],
        EDGE_DETECTION_PARAMS["adaptive_threshold_C"]
    )
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_adaptive_threshold.jpg"), adaptive_thresh)

    # Combine adaptive threshold and Sobel results
    combined_edges = cv2.bitwise_or(adaptive_thresh, sobel_threshold)

    # Use dynamic Canny edge detection based on image statistics
    median_intensity = np.median(blurred)
    sigma = 0.33
    lower_canny = int(max(0, (1.0 - sigma) * median_intensity))
    upper_canny = int(min(255, (1.0 + sigma) * median_intensity))
    canny_edges = cv2.Canny(combined_edges, lower_canny, upper_canny)
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_canny_edges.jpg"), canny_edges)

    # Dilate edges to strengthen connectivity
    dilation_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    dilated_edges = cv2.dilate(canny_edges, dilation_kernel, iterations=MORPHOLOGY_PARAMS["dilation_iterations"])
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_dilated_edges.jpg"), dilated_edges)

    # Morphological closing to fill gaps
    closing_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, MORPHOLOGY_PARAMS["kernel_size"])
    closed_edges = cv2.morphologyEx(dilated_edges, cv2.MORPH_CLOSE, closing_kernel, iterations=MORPHOLOGY_PARAMS["closing_iterations"])
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_closed_edges.jpg"), closed_edges)

    # Find contours from the closed edges
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Extract bounding boxes as rotated rectangles
    initial_boxes = []
    for contour in contours:
        # Ensure contour has at least 3 points to avoid errors
        if len(contour) >= 3:
            rot_rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rot_rect)
            box = np.intp(box)  # Convert to integer
            initial_boxes.append(box)

    print(f"Initial bounding boxes detected: {len(initial_boxes)}")

    # Save intermediate debug image for initial boxes
    debug_image = image.copy()
    for box in initial_boxes:
        cv2.drawContours(debug_image, [box], -1, (0, 255, 0), 2)
    cv2.imwrite(os.path.join(DEBUG_DIR, "debug_initial_boxes.jpg"), debug_image)

    return initial_boxes



def filter_boxes_with_perforation_data(bboxes, perf_stats, image_shape):
    """
    Filters bounding boxes using perforation data to refine the selection.

    Args:
        bboxes (list): List of bounding boxes as (x, y, width, height) tuples.
        perf_stats (dict): Perforation statistics.
        image_shape (tuple): Shape of the image (height, width, channels).

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
    print(f"Expected bounding box size: Width: {expected_width:.2f}, Height: {expected_height:.2f}")

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
            x, y, w, h = box
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
                refined_bboxes.append(box)
        except Exception as e:
            print(f"Error processing box {box}: {e}")

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
    refined_boxes = filter_boxes_with_perforation_data(initial_boxes, perf_stats, image.shape)
    return refined_boxes
