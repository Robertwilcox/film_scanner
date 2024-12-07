import cv2
import numpy as np
import os

# Input and output directories
INPUT_DIR = "tst_jpgs"  # Directory containing test images
OUTPUT_DIR = "output"   # Directory to save debug images

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Adjustable Parameters
PARAMS = {
    # Preprocessing
    "adaptive_thresh_block_size": 15,  # Block size for adaptive thresholding (pixels)
    "adaptive_thresh_c": 2,            # Constant subtracted from the mean in adaptive thresholding (brightness adjustment)
    "morph_kernel_size": (3, 3),       # Kernel size for morphological operations (pixels)

    # Contour Filtering
    "min_contour_area": 50,            # Minimum contour area to be considered (pixels)
    "aspect_ratio_range": (0.5, 3.0),  # Aspect ratio range (width/height) for rectangles
    "rect_size_range": (10, 400),      # Min and max width/height for rectangles (pixels)

    # Alignment Validation
    "spacing_tolerance": 20,           # Allowable gap tolerance between perforations (pixels)

    # Subset Box Validation
    "shrink_factor": 0.2,              # Percentage to shrink each rectangle for brightness validation
}

def resize_to_fit_window(image, window_width, window_height):
    """
    Resizes the image to fit within the specified window dimensions while preserving aspect ratio.
    """
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    resized_image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized_image, scale

def validate_perforation_brightness(image, rectangles, shrink_factor):
    """
    Validates detected rectangles as perforations based on brightness using subset boxes.

    Args:
        image (numpy.ndarray): Input grayscale image.
        rectangles (list): List of detected rectangles (rotated).
        shrink_factor (float): Percentage to shrink each rectangle for subset box validation.

    Returns:
        list: Filtered list of valid perforation rectangles.
    """
    avg_brightness = np.mean(image)
    print(f"Average image brightness: {avg_brightness}")

    validated_rectangles = []
    for box in rectangles:
        # Shrink the rectangle by the specified factor
        x_coords, y_coords = zip(*box)
        center_x, center_y = int(np.mean(x_coords)), int(np.mean(y_coords))
        width = int((max(x_coords) - min(x_coords)) * (1 - shrink_factor))
        height = int((max(y_coords) - min(y_coords)) * (1 - shrink_factor))

        # Define the subset box
        subset_x1 = max(center_x - width // 2, 0)
        subset_y1 = max(center_y - height // 2, 0)
        subset_x2 = min(center_x + width // 2, image.shape[1] - 1)
        subset_y2 = min(center_y + height // 2, image.shape[0] - 1)

        # Calculate the average brightness of the subset box
        subset = image[subset_y1:subset_y2, subset_x1:subset_x2]
        subset_brightness = np.mean(subset)

        if subset_brightness > avg_brightness:
            validated_rectangles.append(box)

    print(f"Validated {len(validated_rectangles)} rectangles based on brightness.")
    return validated_rectangles

def detect_perforations(image, params, window_width=800, window_height=600, debug=False):
    """
    Detect perforations in the film image based on contours and aspect ratio.

    Args:
        image (numpy.ndarray): Input image.
        params (dict): Dictionary of adjustable parameters.
        window_width (int): Width of the display window.
        window_height (int): Height of the display window.
        debug (bool): Whether to save and display debug information.

    Returns:
        list: List of validated perforation bounding boxes (rotated rectangles).
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Adaptive thresholding to isolate bright regions (perforations)
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        params["adaptive_thresh_block_size"],
        params["adaptive_thresh_c"],
    )

    # Morphological operations to clean noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, params["morph_kernel_size"])
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Debug: Save intermediate preprocessing results
    cv2.imwrite(os.path.join(OUTPUT_DIR, "debug_thresh.jpg"), thresh)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "debug_cleaned.jpg"), cleaned)

    # Find contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on rectangularity and rotation
    rectangles = []
    for contour in contours:
        if cv2.contourArea(contour) < params["min_contour_area"]:
            continue

        # Fit a rotated rectangle around the contour
        rot_rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rot_rect)
        box = np.intp(box)  # Convert to integer coordinates

        # Calculate dimensions and aspect ratio
        width = min(rot_rect[1])
        height = max(rot_rect[1])
        aspect_ratio = width / height if height > 0 else 0

        if (
            params["aspect_ratio_range"][0] <= aspect_ratio <= params["aspect_ratio_range"][1]
            and params["rect_size_range"][0] <= width <= params["rect_size_range"][1]
            and params["rect_size_range"][0] <= height <= params["rect_size_range"][1]
        ):
            rectangles.append(box)

    print(f"Detected {len(rectangles)} candidate rectangles.")

    # Validate perforations based on brightness
    validated_rectangles = validate_perforation_brightness(gray, rectangles, params["shrink_factor"])

    # Debugging: Save or display the result
    resized_image, scale = resize_to_fit_window(image, window_width, window_height)
    debug_image = resized_image.copy()

    # Draw contours for debugging
    for box in validated_rectangles:
        scaled_box = (box * scale).astype(int)  # Scale the box coordinates
        cv2.drawContours(debug_image, [scaled_box], -1, (0, 255, 0), 2)  # Draw in green

    if debug:
        cv2.imshow("Detected Perforations", debug_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # Save debug image
        debug_path = os.path.join(OUTPUT_DIR, "detected_perforations.jpg")
        cv2.imwrite(debug_path, debug_image)
        print(f"Debug image saved to: {debug_path}")

    return validated_rectangles

if __name__ == "__main__":
    # Process all .jpg files in the INPUT_DIR
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".jpg"):
            input_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing {input_path}")

            # Load the image
            image = cv2.imread(input_path)
            if image is None:
                print(f"Error: Unable to load {input_path}")
                continue

            # Detect perforations
            perforations = detect_perforations(image, PARAMS, debug=True)
            print(f"Detected perforations: {perforations}")

    print("Processing complete. Check the output directory.")
