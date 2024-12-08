import cv2
import os
import sys

def invert_image(input_path, output_path):
    """
    Invert the colors of an image and save the result.

    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the inverted image.
    """
    # Read the input image
    image = cv2.imread(input_path, cv2.IMREAD_COLOR)
    if image is None:
        print(f"Error: Unable to load image at {input_path}. Skipping.")
        return

    # Invert the colors of the image
    inverted_image = cv2.bitwise_not(image)

    # Save the inverted image
    cv2.imwrite(output_path, inverted_image)
    print(f"Inverted image saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python invert.py <input_dir> <output_dir>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    # Validate input directory
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a valid directory.")
        sys.exit(1)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Process each image in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".jpg"):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            invert_image(input_path, output_path)

    print("Inversion complete.")
