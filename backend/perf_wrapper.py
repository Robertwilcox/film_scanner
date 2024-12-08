import subprocess
import json
import os

def get_perforation_statistics(image_path):
    """
    Runs detect_perf.py on the given image and extracts perforation statistics.

    Args:
        image_path (str): Path to the image file to process.

    Returns:
        dict: A dictionary containing perforation statistics.
              Example:
              {
                  "average_width": 144.86,
                  "std_width": 10.47,
                  "average_height": 210.57,
                  "std_height": 11.90,
                  "average_aspect_ratio": 0.69,
                  "std_aspect_ratio": 0.02,
                  "average_area": 30617.86,
                  "std_area": 3837.84,
                  "valid_perforations": 20
              }
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
        
        # Parse the output to extract statistics
        output_lines = result.stdout.splitlines()
        stats = {}
        for line in output_lines:
            if line.startswith("Average Width"):
                stats["average_width"] = float(line.split(":")[1].split("±")[0].strip())
                stats["std_width"] = float(line.split("±")[1].strip())
            elif line.startswith("Average Height"):
                stats["average_height"] = float(line.split(":")[1].split("±")[0].strip())
                stats["std_height"] = float(line.split("±")[1].strip())
            elif line.startswith("Average Aspect Ratio"):
                stats["average_aspect_ratio"] = float(line.split(":")[1].split("±")[0].strip())
                stats["std_aspect_ratio"] = float(line.split("±")[1].strip())
            elif line.startswith("Average Area"):
                stats["average_area"] = float(line.split(":")[1].split("±")[0].strip())
                stats["std_area"] = float(line.split("±")[1].strip())
            elif line.startswith("Number of Perforations Used"):
                stats["valid_perforations"] = int(line.split(":")[1].strip())

        return stats

    except subprocess.CalledProcessError as e:
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
