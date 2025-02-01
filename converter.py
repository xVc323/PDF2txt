# converter.py
import os
import io
import logging
import time
import tempfile
from PIL import Image
import google.generativeai as genai
import numpy as np
import pytesseract
from datetime import datetime, timedelta
from collections import deque
import fitz  # PyMuPDF
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

class ImageCache:
    """Cache for storing image hashes to avoid reprocessing duplicate images."""
    def __init__(self, cache_size=1000):
        self.cache = {}
        self.cache_size = cache_size

    def get_image_hash(self, image_data):
        """Calculate a hash for the image data."""
        return hashlib.md5(image_data).hexdigest()

    def is_duplicate(self, image_data, analysis):
        """Check if image is duplicate and store analysis if it's new."""
        image_hash = self.get_image_hash(image_data)
        if image_hash in self.cache:
            return True
        if len(self.cache) >= self.cache_size:
            # Remove oldest entry if cache is full
            self.cache.pop(next(iter(self.cache)))
        self.cache[image_hash] = analysis
        return False

class RateLimiter:
    """Enhanced rate limiter with better handling of API limits."""
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.last_request_time = None
        self.min_delay = 1.0  # Minimum delay between requests in seconds

    def wait_if_needed(self):
        """Wait if necessary to comply with rate limits."""
        now = datetime.now()

        # Ensure minimum delay between requests
        if self.last_request_time:
            time_since_last = (now - self.last_request_time).total_seconds()
            if time_since_last < self.min_delay:
                time.sleep(self.min_delay - time_since_last)

        # Clear old requests from the window
        while self.requests and self.requests[0] < now - timedelta(seconds=self.time_window):
            self.requests.popleft()

        # Wait if at rate limit
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()
            if wait_time > 0:
                time.sleep(wait_time)

        self.requests.append(now)
        self.last_request_time = datetime.now()

class PDFConverter:
    def __init__(self, gemini_api_key, log_callback=None):
        self.log_callback = log_callback
        self.gemini_api_key = gemini_api_key
        self.setup_gemini()
        
        # Initialize rate limiter (12 requests per minute to be safe)
        self.rate_limiter = RateLimiter(max_requests=9, time_window=60)
        
        # Initialize image cache
        self.image_cache = ImageCache()
        
        self.log("PDF Converter initialized successfully")

    def setup_gemini(self):
        """Setup Gemini API with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.log("Successfully initialized Gemini model")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    self.log(f"Gemini initialization failed, retrying in {wait_time}s: {str(e)}", "WARNING")
                    time.sleep(wait_time)
                else:
                    self.log(f"Failed to initialize Gemini after {max_retries} attempts", "ERROR")
                    raise

    def log(self, message, level="INFO"):
        """Enhanced logging with better formatting and error handling."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"[{timestamp}] {level}: {message}"
            
            # Log to system logger
            log_func = getattr(logger, level.lower(), logger.info)
            log_func(message)
            
            # Print for debugging
            print(formatted_message)
            
            # Send to GUI if callback exists
            if self.log_callback:
                try:
                    self.log_callback(formatted_message)
                except Exception as e:
                    logger.error(f"Failed to send log to GUI: {e}")
                    print(f"GUI logging error: {e}")
        except Exception as e:
            print(f"Logging system error: {e}")

    def analyze_image(self, image_data, retries=3, base_delay=5):
        """Analyze any image (not just graphs) with smart retry logic."""
        try:
            # Check cache first
            image_hash = self.image_cache.get_image_hash(image_data)
            if image_hash in self.image_cache.cache:
                self.log("Using cached analysis for duplicate image")
                return self.image_cache.cache[image_hash]

            image = Image.open(io.BytesIO(image_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Check for EDHEC logo (you might need to adjust these thresholds)
            if self._is_edhec_logo(image):
                self.log("EDHEC logo detected, skipping analysis")
                return None

            prompt = """
            Please analyze this image and provide a brief description including:
            1. Type of content (e.g., graph, chart, diagram, photo, logo, etc.)
            2. Main elements and subject matter
            3. Key information or data shown (if applicable)
            4. Any text or numbers that are crucial to understanding the content
            
            Be concise but thorough. If it's a graph or chart, include key trends and data points.
            """

            for attempt in range(retries):
                try:
                    self.log(f"Analyzing image (attempt {attempt + 1}/{retries})")
                    self.rate_limiter.wait_if_needed()

                    response = self.model.generate_content(
                        contents=[prompt, image],
                        stream=False
                    )
                    
                    analysis = response.text if response.text else "No analysis generated"
                    self.image_cache.cache[image_hash] = analysis
                    return analysis

                except Exception as e:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                    error_msg = str(e)
                    
                    if "429" in error_msg:  # Rate limit error
                        self.log(f"Rate limit exceeded (attempt {attempt + 1}/{retries})", "WARNING")
                    else:
                        self.log(f"API error (attempt {attempt + 1}/{retries}): {error_msg}", "WARNING")
                    
                    if attempt < retries - 1:
                        self.log(f"Retrying in {wait_time} seconds...", "INFO")
                        time.sleep(wait_time)
                    else:
                        raise

        except Exception as e:
            error_msg = f"Failed to analyze image after {retries} attempts: {str(e)}"
            self.log(error_msg, "ERROR")
            return f"Error: {error_msg}"

    def _is_edhec_logo(self, image):
        """Detect if the image is the EDHEC logo."""
        try:
            # Convert to grayscale for analysis
            img_gray = np.array(image.convert('L'))
            
            # Get image characteristics
            avg_brightness = np.mean(img_gray)
            std_brightness = np.std(img_gray)
            
            # Basic size check (logos tend to be relatively small and square-ish)
            width, height = image.size
            aspect_ratio = width / height
            
            # EDHEC logo characteristics (adjust these based on actual logo)
            is_logo = (
                0.8 < aspect_ratio < 1.2 and  # Nearly square
                avg_brightness > 200 and       # Mostly bright
                std_brightness < 60 and        # Not too much variation
                width < 300 and height < 300   # Relatively small
            )
            
            return is_logo
            
        except Exception as e:
            self.log(f"Error in logo detection: {str(e)}", "WARNING")
            return False

    def convert_pdf(self, pdf_path, output_path):
        """Convert PDF to text with enhanced image analysis and error handling."""
        try:
            if not os.path.exists(pdf_path):
                self.log(f"PDF file not found: {pdf_path}", "ERROR")
                return False

            self.log(f"Starting conversion of: {pdf_path}")
            doc = fitz.open(pdf_path)
            output_text = []
            total_pages = len(doc)
            
            for page_num, page in enumerate(doc, 1):
                try:
                    self.log(f"Processing page {page_num}/{total_pages}")
                    
                    # Extract text
                    text = page.get_text()
                    output_text.append(f"\n=== Page {page_num} ===\n")
                    output_text.append(text)
                    
                    # Process images
                    images = page.get_images()
                    if images:
                        self.log(f"Found {len(images)} images on page {page_num}")
                        output_text.append(f"\n--- Images on Page {page_num} ---\n")
                        
                        for img_idx, img in enumerate(images, 1):
                            try:
                                xref = img[0]
                                base_image = doc.extract_image(xref)
                                image_data = base_image["image"]
                                
                                analysis = self.analyze_image(image_data)
                                if analysis:
                                    output_text.append(f"\n[Image {img_idx} Analysis]\n{analysis}\n")
                                
                            except Exception as e:
                                error_msg = f"Error processing image {img_idx} on page {page_num}: {str(e)}"
                                self.log(error_msg, "ERROR")
                                output_text.append(f"\n[Error] {error_msg}\n")
                    
                    # Add page separator
                    output_text.append("\n" + "="*50 + "\n")
                    
                except Exception as e:
                    error_msg = f"Error processing page {page_num}: {str(e)}"
                    self.log(error_msg, "ERROR")
                    output_text.append(f"\n[Error] {error_msg}\n")
                    continue

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_text))
            
            self.log(f"Successfully converted PDF to: {output_path}")
            return True
            
        except Exception as e:
            self.log(f"Critical error converting PDF: {str(e)}", "ERROR")
            return False