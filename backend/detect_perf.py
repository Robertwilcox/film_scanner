import cv2
import numpy as np
import os

# Input and output directories
INPUT_DIR = "tst_jpgs"  # Directory containing test images
OUTPUT_DIR = "output"   # Directory to save debug images
DEBUG_LOG_PATH = os.path.join(OUTPUT_DIR, "debug_log.txt")  # Debug log file path
SUMMARY_LOG_PATH = os.path.join(OUTPUT_DIR, "summary_log.txt")  # Summary log file path

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Clear existing logs
if os.path.exists(DEBUG_LOG_PATH):
    os.remove(DEBUG_LOG_PATH)
if os.path.exists(SUMMARY_LOG_PATH):
    os.remove(SUMMARY_LOG_PATH)

# Adjustable Parameters
PARAMS = {
    "adaptive_thresh_block_size": 17,  # Block size for adaptive thresholding (pixels)
    "adaptive_thresh_c": 2,            # Constant subtracted from the mean
    "morph_kernel_size": (3, 3),       # Kernel size for morphological operations (pixels)
    "min_contour_area": 500,             # Minimum contour area to be considered (pixels)
    "aspect_ratio_range": (.5, 3.0),  # Aspect ratio range for rectangles
    "rect_size_range": (20, 600),      # Min and max width/height for rectangles (pixels)
    "shrink_factor": 0.3,              # Percentage to shrink rectangles for brightness validation
    "max_std_dev": 2,                  # Maximum standard deviation inside the subset box
    "brightness_threshold_factor": 0.95,  # Brightness factor for validation relative to average
}

def write_debug_log(message):
    """Appends a message to the detailed debug log."""
    with open(DEBUG_LOG_PATH, "a") as log_file:
        log_file.write(f"{message}\n")

def write_summary_log(message):
    """Appends a message to the summary log."""
    with open(SUMMARY_LOG_PATH, "a") as log_file:
        log_file.write(f"{message}\n")

def resize_to_fit_window(image, window_width, window_height):
    """Resizes the image to fit within the specified window dimensions while preserving aspect ratio."""
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    resized_image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized_image, scale

def validate_perforation_brightness(image, rectangles, params):
    """Validates detected rectangles as perforations based on brightness using subset boxes."""
    avg_brightness = np.mean(image)
    write_debug_log(f"STEP: Average Brightness: {avg_brightness:.2f}")

    validated_rectangles = []
    rejected_by_brightness = 0
    rejected_by_std_dev = 0

    for box in rectangles:
        x_coords, y_coords = zip(*box)
        center_x, center_y = int(np.mean(x_coords)), int(np.mean(y_coords))
        width = int((max(x_coords) - min(x_coords)) * (1 - params["shrink_factor"]))
        height = int((max(y_coords) - min(y_coords)) * (1 - params["shrink_factor"]))

        subset_x1 = max(center_x - width // 2, 0)
        subset_y1 = max(center_y - height // 2, 0)
        subset_x2 = min(center_x + width // 2, image.shape[1] - 1)
        subset_y2 = min(center_y + height // 2, image.shape[0] - 1)

        subset = image[subset_y1:subset_y2, subset_x1:subset_x2]
        subset_brightness = np.mean(subset)
        subset_std_dev = np.std(subset)

        if subset_brightness < avg_brightness * params["brightness_threshold_factor"]:
            rejected_by_brightness += 1
        elif subset_std_dev > params["max_std_dev"]:
            rejected_by_std_dev += 1
        else:
            validated_rectangles.append(box)

    write_summary_log(
        f"Brightness Validation:\n"
        f" - Total rectangles analyzed: {len(rectangles)}\n"
        f" - Validated rectangles: {len(validated_rectangles)}\n"
        f" - Rejected by brightness: {rejected_by_brightness}\n"
        f" - Rejected by standard deviation: {rejected_by_std_dev}"
    )
    return validated_rectangles

def detect_perforations(image, params, debug=False):
    """Detect perforations in the film image based on contours and aspect ratio."""
    write_debug_log("STEP: Detect Perforations - Starting...")
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        params["adaptive_thresh_block_size"],
        params["adaptive_thresh_c"],
    )
    cv2.imwrite(os.path.join(OUTPUT_DIR, "debug_thresh.jpg"), thresh)
    
    # Morphological cleaning
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, params["morph_kernel_size"])
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "debug_cleaned.jpg"), cleaned)
    
    # Find contours using RETR_TREE for comprehensive contour retrieval
    contours, _ = cv2.findContours(cleaned, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    write_debug_log(f"STEP: Found {len(contours)} total contours using RETR_TREE.")
    
    # Debug: Draw all detected contours
    all_contours_image = image.copy()
    cv2.drawContours(all_contours_image, contours, -1, (0, 255, 255), 1)  # Yellow for all contours
    cv2.imwrite(os.path.join(OUTPUT_DIR, "all_contours.jpg"), all_contours_image)
    
    # Initialize image for rejected contours visualization
    rejected_contours_image = image.copy()
    
    # Filtering contours to find rectangles
    rectangles = []
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        
        # Reject based on minimum area
        if contour_area < params["min_contour_area"]:
            write_debug_log(f"Rejected contour: Area={contour_area:.2f} (too small)")
            cv2.drawContours(rejected_contours_image, [contour], -1, (0, 0, 255), 1)  # Red for too small
            continue
        
        # Fit a rotated rectangle
        rot_rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rot_rect)
        box = np.intp(box)  # Convert to integer coordinates
        
        # Calculate width, height, and aspect ratio
        width = np.linalg.norm(box[0] - box[1])
        height = np.linalg.norm(box[1] - box[2])
        aspect_ratio = min(width, height) / max(width, height)
        
        write_debug_log(
            f"Contour: Area={contour_area:.2f}, Width={width:.2f}, Height={height:.2f}, Aspect Ratio={aspect_ratio:.2f}"
        )
        
        # Check aspect ratio and size range
        if not (
            params["aspect_ratio_range"][0] <= aspect_ratio <= params["aspect_ratio_range"][1]
            and params["rect_size_range"][0] <= width <= params["rect_size_range"][1]
            and params["rect_size_range"][0] <= height <= params["rect_size_range"][1]
        ):
            write_debug_log("Rejected contour: Failed aspect ratio or size filter")
            cv2.drawContours(rejected_contours_image, [box], -1, (255, 0, 0), 1)  # Blue for failed size/aspect
            continue
        
        rectangles.append(box)
    
    write_debug_log(f"STEP: Detected {len(rectangles)} candidate rectangles.")
    
    # Debug: Save rejected contours image
    cv2.imwrite(os.path.join(OUTPUT_DIR, "rejected_contours.jpg"), rejected_contours_image)
    
    # Draw candidate rectangles for debugging
    candidate_debug = image.copy()
    for box in rectangles:
        cv2.drawContours(candidate_debug, [box], -1, (0, 255, 0), 1)  # Green for candidates
    cv2.imwrite(os.path.join(OUTPUT_DIR, "candidate_rectangles.jpg"), candidate_debug)
    
    write_summary_log(
        f"Detection Summary:\n"
        f" - Total contours: {len(contours)}\n"
        f" - Candidate rectangles: {len(rectangles)}\n"
        f" - Contours rejected by area or aspect ratio: {len(contours) - len(rectangles)}"
    )
    
    return rectangles


if __name__ == "__main__":
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".jpg"):
            input_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing {input_path}")
            write_summary_log(f"\nProcessing file: {input_path}")

            image = cv2.imread(input_path)
            if image is None:
                write_summary_log(" - Error: Unable to load the image.")
                continue

            perforations = detect_perforations(image, PARAMS, debug=True)
            validated_perforations = validate_perforation_brightness(
                cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), perforations, PARAMS
            )

            # Visualize results
            debug_image, scale = resize_to_fit_window(image, 800, 600)
            for box in validated_perforations:
                scaled_box = (box * scale).astype(int)
                cv2.drawContours(debug_image, [scaled_box], -1, (0, 255, 0), 2)
            cv2.imshow("Detected Perforations", debug_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            write_summary_log(f"Final Results:\n"
                              f" - Total validated perforations: {len(validated_perforations)}")
            print(f"Detected perforations: {validated_perforations}")

    print("Processing complete. Check the output and summary logs.")
    write_summary_log("Processing complete.")
