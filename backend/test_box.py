import cv2
import sys
from box import detect_initial_boxes

def resize_to_fit_window(image, window_width=800, window_height=600):
    """
    Resizes the image to fit within the specified window dimensions, preserving aspect ratio.

    Args:
        image (numpy.ndarray): The input image.
        window_width (int): Maximum allowed width of the window.
        window_height (int): Maximum allowed height of the window.

    Returns:
        numpy.ndarray: The resized image.
    """
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized_image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized_image

def main(image_path):
    # Load the input image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return

    # Detect initial boxes
    print(f"Processing {image_path}")
    initial_boxes = detect_initial_boxes(image)

    # Draw detected boxes on the original image
    for box in initial_boxes:
        cv2.drawContours(image, [box], -1, (0, 255, 0), 2)

    # Resize the image to fit the display window
    resized_image = resize_to_fit_window(image)

    # Display the resized image
    cv2.imshow("Detected Boxes", resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Check for input arguments
    if len(sys.argv) < 2:
        print("Usage: python test_box.py <image_path>")
        sys.exit(1)

    # Run the test
    image_path = sys.argv[1]
    main(image_path)
