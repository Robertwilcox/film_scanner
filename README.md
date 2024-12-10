# Automated 35mm Film Negative Digitization

This project is an application for digitizing 35mm film negatives. It uses computer vision and image processing techniques to automate the process of detecting, extracting, and converting film frames into digital images.

**Note:** This project is under active development and is not yet fully functional. The automated frame detection may require manual adjustments to ensure accuracy.

## How to Use

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Robertwilcox/film_scanner](https://github.com/Robertwilcox/film_scanner)
    ```

2.  **Install dependencies:**
    Make sure you have OpenCV installed. You can install it using pip:
    ```bash
    pip install opencv-python
    ```

3.  **Edit folder paths:**
    Open `extract.py` and edit the folder paths to point to your input and output directories.

4.  **Run the application:**
    ```bash
    python extract.py
    ```

## Features

*   Automated perforation detection for frame alignment
*   Manual adjustment tools for refining frame extraction
*   Color inversion and adjustable color enhancement

## Future Work

*   Improve automated frame detection using machine learning
*   Extend support to multiple film formats
*   Optimize performance for real-time processing
*   Develop a web-based interface for easier access

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
```