'''
Perforation Statistics Wrapper

This module provides a function to extract perforation 
statistics from images by running the `detect_perf.py` 
script and parsing its output.

Author: Robert Wilcox
Email: robertraywilcox@gmail.com
Date: December 9, 2024
'''

import subprocess
import json
import os
import re


def get_perforation_statistics(image_path):
    """
    Runs detect_perf.py on the given image and extracts 
    perforation statistics.

    Args:
        image_path (str): Path to the image file.

    Returns:
        dict: A dictionary containing perforation statistics.

    Raises:
        RuntimeError: If there is an error running detect_perf.py 
                     or parsing the output.
    """
    try:
        # Run detect_perf.py as a subprocess
        result = subprocess.run(
            ["python", "detect_perf.py", image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        # Debug: Print raw output from detect_perf.py
        print("Raw output from detect_perf.py:")
        print(result.stdout)

        # Parse the output to extract statistics
        output_lines = result.stdout.splitlines()
        stats = {}

        # Define regex patterns for parsing
        patterns = {
            "average_width": r"Average Width:\s*([\d.]+)\s*±\s*([\d.]+)",
            "average_height": r"Average Height:\s*([\d.]+)\s*±\s*([\d.]+)",
            "average_aspect_ratio": r"Average Aspect Ratio:\s*([\d.]+)\s*±\s*([\d.]+)",
            "average_area": r"Average Area:\s*([\d.]+)\s*±\s*([\d.]+)",
            "valid_perforations": r"Number of Perforations Used:\s*(\d+)"
        }

        for line in output_lines:
            for key, pattern in patterns.items():
                match = re.search(pattern, line)
                if match:
                    if "±" in pattern:  # Handle keys with value and std dev
                        stats[key] = float(match.group(1))
                        if key == "average_aspect_ratio":
                            stats["std_aspect_ratio"] = float(match.group(2))
                        else:
                            stats[f"std_{key.split('_')[1]}"] = float(match.group(2))
                    else:  # Handle keys with single value
                        if key == "valid_perforations":
                            stats[key] = int(match.group(1)) 
                        else:
                            stats[key] = float(match.group(1))

        # Debug: Print parsed statistics
        print("Parsed Statistics:")
        print(json.dumps(stats, indent=2))

        # Validate parsed statistics
        required_keys = [
            "average_width", "std_width", 
            "average_height", "std_height", 
            "average_aspect_ratio", "std_aspect_ratio", 
            "average_area", "std_area", 
            "valid_perforations"
        ]
        for key in required_keys:
            if key not in stats:
                print(f"Warning: Missing {key} in statistics.")

        return stats

    except subprocess.CalledProcessError as e:
        print("Error output from detect_perf.py:")
        print(e.stderr)
        raise RuntimeError(f"Error running detect_perf.py: {e.stderr}")


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python perf_wrapper.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.isfile(image_path):
        print(f"Error: The file {image_path} does not exist.")
        sys.exit(1)

    try:
        stats = get_perforation_statistics(image_path)
        print("Perforation Statistics:")
        print(json.dumps(stats, indent=2))
    except RuntimeError as e:
        print(e)