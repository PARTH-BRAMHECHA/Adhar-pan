# Document Information Extractor

## Project Description
This project is designed to extract key information from scanned documents, such as Aadhaar cards, PAN cards, and other identity documents. It uses Optical Character Recognition (OCR) powered by **PaddleOCR** to extract text from images and then processes the text to identify specific fields like **Name**, **Date of Birth (DOB)**, **Unique Identifier (e.g., Aadhaar or PAN number)**, and **Gender**. The extracted information is formatted and corrected using **Google's Gemini API** for professional name formatting.

The project is particularly useful for automating document processing tasks in applications like identity verification, KYC (Know Your Customer), and data entry systems.

---

## Tech Stack and Libraries

### Core Libraries
1. **PaddleOCR**:
   - **Purpose**: Optical Character Recognition (OCR) for text extraction from images.
   - **Features**: Supports multiple languages, handles rotated text, and provides confidence scores.
   - **Documentation**: [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)

2. **OpenCV (cv2)**:
   - **Purpose**: Image preprocessing (e.g., grayscale conversion, denoising, thresholding).
   - **Features**: Enhances OCR accuracy by improving image quality.
   - **Documentation**: [OpenCV Documentation](https://docs.opencv.org/)

3. **Google Gemini API**:
   - **Purpose**: Corrects and formats extracted names.
   - **Features**: Removes extra whitespaces, capitalizes name components, and ensures proper spacing.
   - **Documentation**: [Google Cloud Gemini API](https://cloud.google.com/generative-ai)

4. **Regex (re)**:
   - **Purpose**: Pattern matching for extracting specific fields like Aadhaar numbers, PAN numbers, and DOB.
   - **Features**: Matches patterns like DD/MM/YYYY for DOB and 12-digit Aadhaar numbers.
   - **Documentation**: [Python Regex Documentation](https://docs.python.org/3/library/re.html)

5. **NumPy**:
   - **Purpose**: Numerical operations for image preprocessing.
   - **Features**: Used for kernel creation in morphological operations.
   - **Documentation**: [NumPy Documentation](https://numpy.org/doc/)

6. **Logging**:
   - **Purpose**: Logging for debugging and tracking errors.
   - **Features**: Provides timestamps and log levels for better debugging.
   - **Documentation**: [Python Logging Documentation](https://docs.python.org/3/library/logging.html)

---

## Installation Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps
1. **Clone the repository**:
   
bash
   git clone https://github.com/your-repo/document-extractor.git
   cd document-extractor


2. **Set up a virtual environment** (optional but recommended):
   
bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate


3. **Install dependencies**:
   
bash
   pip install -r requirements.txt


4. **Set up Google Gemini API Key**:
   - Obtain an API key from [Google Cloud Console](https://console.cloud.google.com/).
   - Replace the placeholder API key in the code:
     
python
     genai.configure(api_key="YOUR_API_KEY_HERE")


5. **Run the project**:
   
bash
   python main.py


---

## Explanation of Models and Functionalities

### 1. **PaddleOCR**
- **Purpose**: Extracts text from images.
- **Features**:
  - Supports multiple languages.
  - Handles rotated and skewed text.
  - Provides confidence scores for extracted text.

### 2. **Google Gemini API**
- **Purpose**: Corrects and formats extracted names.
- **Features**:
  - Removes extra whitespaces.
  - Capitalizes the first letter of each name component.
  - Ensures proper spacing between name parts.

### 3. **OpenCV**
- **Purpose**: Preprocesses images for better OCR accuracy.
- **Features**:
  - Converts images to grayscale.
  - Applies denoising and adaptive thresholding.

### 4. **Regex (Regular Expressions)**
- **Purpose**: Extracts specific patterns like Aadhaar numbers, PAN numbers, and DOB.
- **Features**:
  - Matches patterns like DD/MM/YYYY for DOB.
  - Identifies Aadhaar numbers (12 digits) and PAN numbers (10 characters).

---

## Example Usage Guidelines

### 1. **Prepare the Document Image**
- Save the document image (e.g., Aadhaar card, PAN card) in the project directory.
- Supported formats: .jpg, .png.

### 2. **Run the Script**
- Update the image_path variable in main.py to point to your document image:
  
python
  image_path = 'aadhar.jpg'  # Replace with your image file name


- Execute the script:
  
bash
  python main.py


### 3. **View the Output**
- The script will print the extracted information in the following format:
  
plaintext
  Extracted Document Information:
  🔍 Document Analysis Results 🔍
  -------------------------
  • Document Type: Aadhar
  • Unique Identifier: 834531128986
  • Full Name: Sahil Sanjay Katkamwar
  • Date of Birth: 26/04/2016
  • Gender: MALE


### 4. **Debugging**
- If the output is incorrect:
  - Check the preprocessed image saved as preprocessed_image.png.
  - Verify the OCR-extracted text printed in the console.

---

## Example Input and Output

### Input Image (aadhar.jpg):
plaintext
Government of India
Issue Date: 26/04/2016
Sahil Sanjay Katkamwar
834531128986


### Output:
plaintext
Extracted Document Information:
🔍 Document Analysis Results 🔍
-------------------------
• Document Type: Aadhar
• Unique Identifier: 834531128986
• Full Name: Sahil Sanjay Katkamwar
• Date of Birth: 26/04/2016
• Gender: MALE


---
