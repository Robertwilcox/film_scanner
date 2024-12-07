import cv2
import numpy as np
import os

# Input and output directories
INPUT_DIR = "tst_jpgs"  # Directory containing test images
OUTPUT_DIR = "output"   # Directory to save extracted negatives

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Globals
bboxes = []  # List of bounding boxes
selected_idx = -1  # Currently selected bounding box
dragging = False  # True if dragging a box
resizing = False  # True if resizing a box
current_anchor = None  # Current anchor being dragged
start_point = None  # Start point for dragging
anchor_size = 10  # Size of the anchors for resizing
anchor_radius = 10
anchor_being_dragged = None  # To track which anchor point is being dragged


def resize_to_fit_window(image, window_width, window_height):
    """
    Resizes the image to fit within the specified window dimensions while preserving aspect ratio.
    """
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    resized_image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized_image, scale


def auto_detect_bboxes(image):
    """
    Auto-detect bounding boxes for negatives.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Threshold and clean up noise
    _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY_INV)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on aspect ratio and area
    detected_bboxes = [
        cv2.boundingRect(contour)
        for contour in contours
        if 1.5 < cv2.boundingRect(contour)[2] / cv2.boundingRect(contour)[3] < 3.5  # Aspect ratio range
        and cv2.contourArea(contour) > 5000  # Minimum area threshold
    ]
    return detected_bboxes


def draw_bboxes(image, scale):
    """
    Draw all bounding boxes and their anchor points on the image.
    """
    for bx, by, bw, bh in bboxes:
        scaled_box = (int(bx * scale), int(by * scale), int(bw * scale), int(bh * scale))
        x, y, w, h = scaled_box

        # Draw the bounding box
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Draw anchor points as outlined circles
        anchors = [
            (x, y), (x + w, y), (x, y + h), (x + w, y + h)
        ]  # Top-left, Top-right, Bottom-left, Bottom-right
        for ax, ay in anchors:
            cv2.circle(image, (ax, ay), anchor_radius, (0, 0, 255), 2)  # Outline circle



def get_anchor_under_mouse(x, y, scale):
    """
    Check if the mouse is over a resize anchor.
    """
    for idx, (bx, by, bw, bh) in enumerate(bboxes):
        anchors = [
            (bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)  # Top-left, Top-right, Bottom-left, Bottom-right
        ]
        for i, (ax, ay) in enumerate(anchors):
            if abs(x - int(ax * scale)) < anchor_size and abs(y - int(ay * scale)) < anchor_size:
                return idx, i
    return None, None


# Adjust the size of the interactive area around anchors
anchor_radius = 10  # Radius of the anchor circle

def mouse_callback(event, x, y, flags, param):
    """
    Handle mouse events for interacting with bounding boxes, including resizing anchors,
    moving boxes, adding new boxes, and removing existing boxes.
    """
    global bboxes, selected_idx, anchor_being_dragged

    scale = param  # Scale factor for converting coordinates
    scaled_x, scaled_y = int(x / scale), int(y / scale)

    if event == cv2.EVENT_LBUTTONDOWN:  # Left-click
        anchor_being_dragged = None

        # Check if clicked near an anchor point
        for idx, (bx, by, bw, bh) in enumerate(bboxes):
            anchors = [
                (bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)
            ]  # Top-left, Top-right, Bottom-left, Bottom-right
            for i, (ax, ay) in enumerate(anchors):
                # Check if click is within the anchor circle
                if (scaled_x - ax) ** 2 + (scaled_y - ay) ** 2 <= anchor_radius ** 2:
                    selected_idx = idx
                    anchor_being_dragged = (i, idx)  # Anchor index and bbox index
                    print(f"Dragging anchor {i} of box {idx}")
                    return

        # Check if clicked inside a bounding box for movement
        for idx, (bx, by, bw, bh) in enumerate(bboxes):
            if bx <= scaled_x <= bx + bw and by <= scaled_y <= by + bh:
                selected_idx = idx
                print(f"Selected bounding box {idx} for movement.")
                return

        # Reset selection if no anchor or box is clicked
        selected_idx = -1

    elif event == cv2.EVENT_MOUSEMOVE:  # Mouse movement
        if anchor_being_dragged:  # Resize the box via anchor
            anchor_idx, box_idx = anchor_being_dragged
            bx, by, bw, bh = bboxes[box_idx]

            # Update the bounding box based on the dragged anchor
            if anchor_idx == 0:  # Top-left
                bboxes[box_idx] = (scaled_x, scaled_y, bx + bw - scaled_x, by + bh - scaled_y)
            elif anchor_idx == 1:  # Top-right
                bboxes[box_idx] = (bx, scaled_y, scaled_x - bx, by + bh - scaled_y)
            elif anchor_idx == 2:  # Bottom-left
                bboxes[box_idx] = (scaled_x, by, bx + bw - scaled_x, scaled_y - by)
            elif anchor_idx == 3:  # Bottom-right
                bboxes[box_idx] = (bx, by, scaled_x - bx, scaled_y - by)
            print(f"Resized box {box_idx}: {bboxes[box_idx]}")
            return

        elif selected_idx != -1 and flags == cv2.EVENT_FLAG_LBUTTON:  # Move the box
            # Move the selected bounding box
            bx, by, bw, bh = bboxes[selected_idx]
            dx, dy = scaled_x - bx, scaled_y - by
            bboxes[selected_idx] = (scaled_x - bw // 2, scaled_y - bh // 2, bw, bh)
            print(f"Moved bounding box {selected_idx} to: ({scaled_x}, {scaled_y})")
            return

    elif event == cv2.EVENT_LBUTTONUP:  # Release left-click
        anchor_being_dragged = None

    elif event == cv2.EVENT_RBUTTONDOWN:  # Right-click to add a new box
        box_size = 100  # Increased default size of the new bounding box
        new_box = (scaled_x - box_size // 2, scaled_y - box_size // 2, box_size, box_size)
        bboxes.append(new_box)
        selected_idx = -1  # Reset selection
        print(f"Added new bounding box at: ({scaled_x}, {scaled_y})")

    elif event == cv2.EVENT_LBUTTONDBLCLK:  # Double-click to remove a bounding box
        for idx, (bx, by, bw, bh) in enumerate(bboxes):
            if bx <= scaled_x <= bx + bw and by <= scaled_y <= by + bh:
                print(f"Removed bounding box {idx}: ({bx}, {by}, {bw}, {bh})")
                bboxes.pop(idx)
                selected_idx = -1  # Reset selection
                return

def process_image(image_path):
    """
    Process a single image with GUI for bounding box adjustment.
    """
    global bboxes

    print(f"Processing {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load {image_path}")
        return

    # Auto-detect bounding boxes
    bboxes = auto_detect_bboxes(image)
    print(f"Detected {len(bboxes)} bounding boxes.")

    # Resize the image to fit the window
    resized_image, scale = resize_to_fit_window(image, 800, 600)

    # Set up the main window
    main_window_name = "Adjust Bounding Boxes"
    instruction_window_name = "Instructions"
    cv2.namedWindow(main_window_name)
    cv2.namedWindow(instruction_window_name)
    cv2.setMouseCallback(main_window_name, mouse_callback, scale)

    # Instruction lines
    instruction_lines = [
        "INSTRUCTIONS:",
        "- Drag anchors to resize boxes",
        "- Drag boxes to move them",
        "- Right-click: Add box",
        "- Double-click: Remove box",
        "- Enter: Save and Exit",
        "- ESC: Exit without saving",
        "- Close window: Save and Exit"
    ]

    # Create an instruction image
    instruction_height = 300
    instruction_width = 500
    instruction_panel = np.zeros((instruction_height, instruction_width, 3), dtype=np.uint8)

    # Add instructions to the panel
    for i, line in enumerate(instruction_lines):
        cv2.putText(
            instruction_panel,
            line,
            (10, 30 + i * 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            1,
        )

    saved = False  # Flag to indicate if changes were saved

    try:
        while True:
            # Draw bounding boxes on a copy of the resized image
            display_img = resized_image.copy()
            draw_bboxes(display_img, scale)

            # Show the main image and instructions
            cv2.imshow(main_window_name, display_img)
            cv2.imshow(instruction_window_name, instruction_panel)

            # Handle key press or window closure
            key = cv2.waitKey(1)
            if key == 27:  # ESC to exit without saving
                print("Exiting without saving.")
                saved = False
                break
            elif key == 13:  # Enter to save and exit
                print("Saving and exiting.")
                saved = True
                break
            elif cv2.getWindowProperty(main_window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Main window closed. Saving and exiting.")
                saved = True
                break
            elif cv2.getWindowProperty(instruction_window_name, cv2.WND_PROP_VISIBLE) < 1:
                print("Instruction window closed. Saving and exiting.")
                saved = True
                break
    finally:
        # Save all bounding boxes only if Enter was pressed or window was closed
        if saved:
            for idx, (x, y, w, h) in enumerate(bboxes):
                cropped = image[y:y+h, x:x+w]
                output_path = os.path.join(
                    OUTPUT_DIR, f"{os.path.splitext(os.path.basename(image_path))[0]}_negative_{idx + 1}.jpg"
                )
                cv2.imwrite(output_path, cropped)
                print(f"Saved: {output_path}")

        # Destroy windows only if they are still open
        if cv2.getWindowProperty(main_window_name, cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow(main_window_name)
        if cv2.getWindowProperty(instruction_window_name, cv2.WND_PROP_VISIBLE) >= 1:
            cv2.destroyWindow(instruction_window_name)

if __name__ == "__main__":
    # Process all .jpg files in the INPUT_DIR
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".jpg"):
            process_image(os.path.join(INPUT_DIR, filename))

    print("Processing complete. Check the output directory.")
