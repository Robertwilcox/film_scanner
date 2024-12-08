import cv2
import numpy as np

def resize_to_fit_window(image, window_width, window_height):
    """
    Resizes the image to fit within the specified window dimensions while preserving aspect ratio.
    """
    h, w = image.shape[:2]
    scale = min(window_width / w, window_height / h)
    resized_image = cv2.resize(image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized_image, scale

def draw_bboxes(image, bboxes, scale, anchor_radius=10):
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
