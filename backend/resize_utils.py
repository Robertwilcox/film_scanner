'''
Image Resizing and Bounding Box Visualization Utilities

This module provides functions for resizing images to fit 
within a specified window while maintaining aspect ratio 
and for drawing bounding boxes with anchor points on images.

Author: Robert Wilcox
Email: robertraywilcox@gmail.com
Date: December 9, 2024
'''

import cv2


def resize_to_fit_window(image, window_width, window_height):
    """
    Resizes the image to fit within the specified window 
    dimensions while preserving aspect ratio.

    Args:
        image (numpy.ndarray): The image to resize.
        window_width (int): The desired width of the window.
        window_height (int): The desired height of the window.

    Returns:
        tuple: A tuple containing the resized image and the scale factor.
    """
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    resized_image = cv2.resize(
        image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
    )
    return resized_image, scale


def draw_bboxes(image, bboxes, scale, anchor_radius=10):
    """
    Draw bounding boxes and their corner anchor points on an image.

    Args:
        image (numpy.ndarray): The image to draw on.
        bboxes (list): A list of bounding boxes, each as a tuple 
                       (x, y, width, height).
        scale (float): The scale factor applied to the image.
        anchor_radius (int): The radius of the anchor points.
    """
    for bx, by, bw, bh in bboxes:
        scaled_box = (
            int(bx * scale), int(by * scale), 
            int(bw * scale), int(bh * scale)
        )
        x, y, w, h = scaled_box

        # Draw the bounding box
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Draw corner anchor points
        corner_anchors = [
            (x, y), (x + w, y), (x, y + h), (x + w, y + h)
        ]  # Top-left, Top-right, Bottom-left, Bottom-right
        for ax, ay in corner_anchors:
            cv2.circle(image, (ax, ay), anchor_radius, (0, 0, 255), 2)


if __name__ == "__main__":
    # Example image and bounding boxes
    image = cv2.imread("example.jpg")  # Replace with your actual image path
    bboxes = [(100, 100, 200, 150), (300, 250, 120, 100)]  # Example bboxes

    # Resize image to fit within a window
    resized_image, scale = resize_to_fit_window(image, 800, 600)

    # Draw bounding boxes
    draw_bboxes(resized_image, bboxes, scale)

    # Display the result
    cv2.imshow("Bounding Boxes", resized_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()