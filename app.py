import os
import logging
import json
import io
from flask import Flask, request, jsonify, send_file, render_template
import cv2
import numpy as np
import pdf2image
from PIL import Image
from paddleocr import PaddleOCR
import google.generativeai as genai
import fitz  # PyMuPDF for advanced PDF handling
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DocumentInfoExtractor:
    def __init__(self, lang: str = 'en', logging_level: int = logging.INFO):
        # Enhanced logging configuration
        logging.basicConfig(
            level=logging_level, 
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('document_extractor.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

        try:
            # More robust OCR initialization
            self.ocr = PaddleOCR(
                use_angle_cls=True, 
                lang=lang, 
                show_log=False,
                det_db_thresh=0.5,  # Adjust detection threshold
                det_db_box_thresh=0.6,
                det_db_unclip_ratio=1.5,
                use_gpu=False  # Can be changed based on hardware
            )
        except Exception as e:
            self.logger.error(f"OCR Initialization Error: {e}")
            raise

        # Secure Gemini API configuration
        try:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY', ''))
        except Exception as e:
            self.logger.error(f"Gemini API Configuration Error: {e}")
            raise

    def extract_text(self, image_path: str, advanced_processing: bool = True) -> Dict:
        """
        Enhanced text extraction with advanced OCR processing.
        
        Args:
            image_path (str): Path to input image
            advanced_processing (bool): Enable advanced text extraction
        
        Returns:
            Dict containing detailed extracted text information
        """
        try:
            # Perform OCR with advanced options
            result = self.ocr.ocr(image_path, cls=True)

            # Comprehensive text extraction
            extracted_text = {
                "lines": [],
                "full_text": "",
                "bounding_boxes": [],
                "text_regions": [],
                "confidence_score": 0.0
            }

            total_confidence = 0
            line_count = 0

            # Extract detailed text information
            for line_group in result:
                for line in line_group:
                    text, confidence_box = line[1], line[0]
                    if isinstance(confidence_box, tuple) and len(confidence_box) == 2:
                        confidence, box = confidence_box
                    else:
                        # Handle alternative format if needed
                        confidence, box = 0.0, [[0, 0], [0, 0], [0, 0], [0, 0]]
                        self.logger.warning(f"Unexpected OCR result format: {confidence_box}")
                    
                    # Detailed text line information
                    text_info = {
                        "text": text,
                        "confidence": confidence,
                        "bounding_box": box
                    }
                    
                    extracted_text["lines"].append(text_info)
                    extracted_text["bounding_boxes"].append(box)
                    
                    total_confidence += confidence
                    line_count += 1

            # Combine full text
            extracted_text["full_text"] = "\n".join([
                line['text'] for line in extracted_text["lines"]
            ])

            # Calculate average confidence
            extracted_text["confidence_score"] = (total_confidence / line_count) if line_count > 0 else 0.0

            # Advanced text region extraction (if enabled)
            if advanced_processing:
                extracted_text["text_regions"] = self._extract_text_regions(image_path)

            return extracted_text

        except Exception as e:
            self.logger.error(f"Text Extraction Error: {e}")
            return {
                "error": str(e),
                "lines": [],
                "full_text": "",
                "confidence_score": 0.0
            }

    def _extract_text_regions(self, image_path: str) -> List[Dict]:
        """
        Extract text regions with additional context.
        
        Args:
            image_path (str): Path to input image
        
        Returns:
            List of text region dictionaries
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                gray, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )

            # Find contours
            contours, _ = cv2.findContours(
                binary, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )

            text_regions = []
            for contour in contours:
                # Filter small contours
                if cv2.contourArea(contour) > 100:
                    x, y, w, h = cv2.boundingRect(contour)
                    region = {
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "area": cv2.contourArea(contour)
                    }
                    text_regions.append(region)

            return text_regions
        except Exception as e:
            self.logger.error(f"Text Region Extraction Error: {e}")
            return []

    def format_text_with_genai(self, extracted_text: str) -> Dict:
        """
        Enhanced text formatting with Gemini AI.
        
        Args:
            extracted_text (str): Text to be processed
        
        Returns:
            Dict with formatted and labeled text
        """
        prompt = f"""
        Analyze the following OCR-extracted text. Provide a structured JSON output with:
        - Detected document type
        - Extracted key-value pairs
        - Confidence estimate
        - Potential personal information categories

        Extracted Text:
        {extracted_text}
        
        Output Format (JSON):
        {{
            "document_type": "",
            "key_information": {{
                "name": "",
                "id_number": "",
                "date_of_birth": "",
                "address": ""
            }},
            "confidence": 0.0,
            "potential_categories": []
        }}
        """
        
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            
            # Parse response to ensure JSON format
            try:
                parsed_response = json.loads(response.text)
            except json.JSONDecodeError:
                parsed_response = {
                    "document_type": "Unknown",
                    "key_information": {},
                    "confidence": 0.0,
                    "potential_categories": ["Unstructured"]
                }
            
            return parsed_response
        except Exception as e:
            self.logger.error(f"Gemini AI Processing Error: {e}")
            return {
                "document_type": "Error",
                "key_information": {},
                "confidence": 0.0,
                "potential_categories": ["Processing Failed"]
            }

def convert_pdf_to_images(pdf_path: str, output_dir: str = 'uploads') -> List[str]:
    """
    Advanced PDF to image conversion with multiple page support.
    
    Args:
        pdf_path (str): Path to PDF file
        output_dir (str): Directory to save converted images
    
    Returns:
        List of image paths
    """
    try:
        # Use PyMuPDF for more robust PDF handling
        pdf_document = fitz.open(pdf_path)
        image_paths = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # High-quality image rendering
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            
            # Generate image filename
            image_filename = f'page_{page_num + 1}.png'
            image_path = os.path.join(output_dir, image_filename)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Save image
            pix.save(image_path)
            image_paths.append(image_path)

        return image_paths
    except Exception as e:
        logging.error(f"PDF Conversion Error: {e}")
        return []

# Flask Application
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
extractor = DocumentInfoExtractor()

@app.route('/')
def index():
    """
    Render the main application page
    """
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_document_info():
    """
    Comprehensive document information extraction endpoint.
    Supports multiple file types and advanced processing.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    # Secure filename handling
    filename = file.filename.replace('/', '').replace('\\', '')
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
    if file_ext not in allowed_extensions:
        return jsonify({"error": "Unsupported file type. Use PNG, JPEG, or PDF"}), 400
    
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    # Save uploaded file
    save_path = os.path.join('uploads', filename)
    file.save(save_path)
    
    try:
        # Convert PDF to images if needed
        image_paths = [save_path]
        if file_ext == 'pdf':
            image_paths = convert_pdf_to_images(save_path)
            if not image_paths:
                return jsonify({"error": "Failed to convert PDF"}), 500
        
        # Process all pages/images
        all_results = []
        for image_path in image_paths:
            # Extract text
            ocr_results = extractor.extract_text(image_path)
            
            # Format text with Gemini AI
            formatted_text = extractor.format_text_with_genai(ocr_results['full_text'])
            
            # Prepare page results
            page_result = {
                "document_type": file_ext.upper(),
                "page_number": image_paths.index(image_path) + 1,
                "ocr_results": ocr_results,
                "formatted_text": formatted_text
            }
            
            all_results.append(page_result)
        
        return jsonify(all_results), 200
    
    except Exception as e:
        logging.error(f"Extraction Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up uploaded files
        for path in [save_path] + (image_paths if 'image_paths' in locals() else []):
            if os.path.exists(path) and path != save_path:  # Don't remove the original file yet
                os.remove(path)
                
        # Now remove the original file
        if os.path.exists(save_path):
            os.remove(save_path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "ocr": "active",
            "ai": "active"
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)