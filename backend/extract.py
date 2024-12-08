import cv2
import os
import numpy as np
from resize_utils import resize_to_fit_window, draw_bboxes
from bbox_detection import auto_detect_bboxes_with_perforations
from perf_wrapper import get_perforation_statistics
from subprocess import run

INPUT_DIR = "tst_jpgs"  # Directory containing test images
OUTPUT_DIR = "output"   # Directory to save extracted negatives

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

bboxes = []  # List of bounding boxes
selected_idx = -1  # Index of the currently selected bounding box
anchor_being_dragged = None
anchor_radius = 10


def mouse_callback(event, x, y, flags, param):
    """
    Handle mouse events for interacting with bounding boxes, including resizing and moving.
    """
    global bboxes, selected_idx, anchor_being_dragged

    scale = param  # Scale factor for adjusting coordinates
    scaled_x, scaled_y = int(x / scale), int(y / scale)

    if event == cv2.EVENT_LBUTTONDOWN:  # Left-click
        anchor_being_dragged = None

        # Check if clicked near an anchor point
        for idx, (bx, by, bw, bh) in enumerate(bboxes):
            anchors = [
                (bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)
            ]  # Top-left, Top-right, Bottom-left, Bottom-right
            for i, (ax, ay) in enumerate(anchors):
                if abs(scaled_x - ax) <= anchor_radius and abs(scaled_y - ay) <= anchor_radius:
                    selected_idx = idx
                    anchor_being_dragged = (i, idx)  # Anchor index and bbox index
                    return

        # Check if clicked inside a bounding box for movement
        for idx, (bx, by, bw, bh) in enumerate(bboxes):
            if bx <= scaled_x <= bx + bw and by <= scaled_y <= by + bh:
                selected_idx = idx
                return

        # Reset selection if no anchor or box is clicked
        selected_idx = -1

    elif event == cv2.EVENT_MOUSEMOVE:  # Mouse movement
        if anchor_being_dragged:  # Resize the box via anchor
            anchor_idx, box_idx = anchor_being_dragged
            bx, by, bw, bh = bboxes[box_idx]

            # Update the bounding box based on the dragged anchor
            if anchor_idx == 0:  # Top-left
                new_x, new_y = scaled_x, scaled_y
                new_w, new_h = bx + bw - new_x, by + bh - new_y
            elif anchor_idx == 1:  # Top-right
                new_x, new_y = bx, scaled_y
                new_w, new_h = scaled_x - bx, by + bh - new_y
            elif anchor_idx == 2:  # Bottom-left
                new_x, new_y = scaled_x, by
                new_w, new_h = bx + bw - new_x, scaled_y - by
            elif anchor_idx == 3:  # Bottom-right
                new_x, new_y = bx, by
                new_w, new_h = scaled_x - bx, scaled_y - by

            # Ensure dimensions remain valid
            if new_w > 0 and new_h > 0:
                bboxes[box_idx] = (new_x, new_y, new_w, new_h)

        elif selected_idx != -1 and flags == cv2.EVENT_FLAG_LBUTTON:  # Move the box
            # Move the selected bounding box
            bx, by, bw, bh = bboxes[selected_idx]
            bboxes[selected_idx] = (scaled_x - bw // 2, scaled_y - bh // 2, bw, bh)

    elif event == cv2.EVENT_LBUTTONUP:  # Release left-click
        anchor_being_dragged = None

    elif event == cv2.EVENT_RBUTTONDOWN:  # Right-click to add a new box
        box_size = 100  # Default size of the new bounding box
        new_box = (scaled_x - box_size // 2, scaled_y - box_size // 2, box_size, box_size)
        bboxes.append(new_box)

    elif event == cv2.EVENT_LBUTTONDBLCLK:  # Double-click to remove a bounding box
        for idx, (bx, by, bw, bh) in enumerate(bboxes):
            if bx <= scaled_x <= bx + bw and by <= scaled_y <= by + bh:
                bboxes.pop(idx)
                selected_idx = -1  # Reset selection
                return

def invert_image(image_path, output_path):
    """
    Invert the colors of an image and save it to the specified output path.

    Args:
        image_path (str): Path to the input image.
        output_path (str): Path to save the inverted image.
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image {image_path}")
        return

    # Invert colors
    inverted_image = cv2.bitwise_not(image)

    # Save the inverted image
    cv2.imwrite(output_path, inverted_image)
    print(f"Saved inverted image: {output_path}")

def adjust_colors(image, output_path):
    """
    Display an image with color adjustment sliders and save the adjusted version.

    Args:
        image (numpy.ndarray): The input image to adjust.
        output_path (str): Path to save the adjusted image.
    """
    def on_trackbar_change(val):
        """Callback to apply color adjustments from the sliders."""
        # Check if trackbars are properly initialized
        if not cv2.getWindowProperty("Adjust Colors", cv2.WND_PROP_VISIBLE):
            return  # Skip if window doesn't exist

        red_adj = cv2.getTrackbarPos("Red", "Adjust Colors") - 128
        green_adj = cv2.getTrackbarPos("Green", "Adjust Colors") - 128
        blue_adj = cv2.getTrackbarPos("Blue", "Adjust Colors") - 128

        adjusted_image = image.copy()
        adjusted_image[:, :, 2] = np.clip(adjusted_image[:, :, 2] + red_adj, 0, 255)  # Red
        adjusted_image[:, :, 1] = np.clip(adjusted_image[:, :, 1] + green_adj, 0, 255)  # Green
        adjusted_image[:, :, 0] = np.clip(adjusted_image[:, :, 0] + blue_adj, 0, 255)  # Blue

        cv2.imshow("Adjust Colors", adjusted_image)

    # Create adjustment window
    cv2.namedWindow("Adjust Colors", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Red", "Adjust Colors", 128, 255, on_trackbar_change)
    cv2.createTrackbar("Green", "Adjust Colors", 128, 255, on_trackbar_change)
    cv2.createTrackbar("Blue", "Adjust Colors", 128, 255, on_trackbar_change)

    # Initial display
    on_trackbar_change(0)
    print("Adjust the colors using sliders. Press 's' to save or 'q' to quit without saving.")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):  # Save the final adjusted image
            red_adj = cv2.getTrackbarPos("Red", "Adjust Colors") - 128
            green_adj = cv2.getTrackbarPos("Green", "Adjust Colors") - 128
            blue_adj = cv2.getTrackbarPos("Blue", "Adjust Colors") - 128

            final_image = image.copy()
            final_image[:, :, 2] = np.clip(final_image[:, :, 2] + red_adj, 0, 255)
            final_image[:, :, 1] = np.clip(final_image[:, :, 1] + green_adj, 0, 255)
            final_image[:, :, 0] = np.clip(final_image[:, :, 0] + blue_adj, 0, 255)

            cv2.imwrite(output_path, final_image)
            print(f"Adjusted image saved to: {output_path}")
            break
        elif key == ord('q'):  # Quit without saving
            print("Exiting without saving.")
            break

    cv2.destroyAllWindows()


def process_image(image_path):
    global bboxes
    print(f"Processing {image_path}")
    image = cv2.imread(image_path)
    if image is None or image.size == 0:
        print(f"Error: Unable to load {image_path}. Skipping.")
        return

    # Get perforation statistics
    perf_stats = get_perforation_statistics(image_path)
    print("Perforation Statistics Retrieved:")
    print(perf_stats)

    # Step 1: Detect initial bounding boxes
    from bbox_detection import detect_initial_boxes
    initial_bboxes = detect_initial_boxes(image)

    # Debug: Print initial bounding boxes
    if not initial_bboxes:
        print(f"No bounding boxes detected for {image_path}. Skipping.")
        return

    # Convert initial bounding boxes to (x, y, w, h) format
    converted_bboxes = []
    for box in initial_bboxes:
        x_coords, y_coords = zip(*box)
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        w, h = x_max - x_min, y_max - y_min
        converted_bboxes.append((x_min, y_min, w, h))

    initial_bboxes = converted_bboxes

    # Debug: Visualize initial bounding boxes
    resized_image, scale = resize_to_fit_window(image, 800, 600)
    debug_initial = resized_image.copy()
    draw_bboxes(debug_initial, initial_bboxes, scale)
    cv2.imshow("Initial Bounding Boxes", debug_initial)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "initial_bboxes.jpg"), debug_initial)
    cv2.waitKey(500)
    cv2.destroyAllWindows()

    print(f"Initial bounding boxes detected: {len(initial_bboxes)}")

    # Step 2: Refine bounding boxes using perforation statistics
    from bbox_detection import filter_boxes_with_perforation_data
    bboxes = filter_boxes_with_perforation_data(initial_bboxes, perf_stats, image.shape)

    # Debug: Visualize refined bounding boxes
    debug_refined = resized_image.copy()
    draw_bboxes(debug_refined, bboxes, scale)
    cv2.imshow("Refined Bounding Boxes", debug_refined)
    cv2.imwrite(os.path.join(OUTPUT_DIR, "refined_bboxes.jpg"), debug_refined)
    cv2.waitKey(500)
    cv2.destroyAllWindows()

    print(f"Refined bounding boxes: {len(bboxes)}")

    # Set up the main window
    main_window_name = "Adjust Bounding Boxes"
    cv2.namedWindow(main_window_name)
    cv2.setMouseCallback(main_window_name, mouse_callback, scale)

    try:
        while True:
            display_img = resized_image.copy()
            draw_bboxes(display_img, bboxes, scale)
            cv2.imshow(main_window_name, display_img)
            key = cv2.waitKey(1)
            if key == 27:  # ESC to exit
                break

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Exiting.")

    finally:
        for idx, (x, y, w, h) in enumerate(bboxes):
            x_end = min(x + w, image.shape[1])
            y_end = min(y + h, image.shape[0])
            x, y = max(x, 0), max(y, 0)

            if x >= x_end or y >= y_end:
                print(f"Skipping invalid box: {x, y, w, h}")
                continue

            cropped = image[y:y_end, x:x_end]
            if cropped.size == 0:
                print(f"Skipping empty crop for box: {x, y, w, h}")
                continue

            # Save the original negative
            negative_path = os.path.join(
                OUTPUT_DIR, f"{os.path.splitext(os.path.basename(image_path))[0]}_negative_{idx + 1}.jpg"
            )
            cv2.imwrite(negative_path, cropped)
            print(f"Saved: {negative_path}")

            # Invert the cropped negative
            inverted_image = cv2.bitwise_not(cropped)

            # Display the inverted image with color adjustment sliders
            adjusted_path = os.path.join(
                OUTPUT_DIR, f"{os.path.splitext(os.path.basename(image_path))[0]}_negative_{idx + 1}_adjusted.jpg"
            )
            adjust_colors(inverted_image, adjusted_path)

        cv2.destroyAllWindows()

if __name__ == "__main__":
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".jpg"):
            process_image(os.path.join(INPUT_DIR, filename))

    print("Processing complete.")
