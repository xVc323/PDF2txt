# main.py
import tkinter as tk
import logging
import sys
import os
from datetime import datetime
import traceback

def setup_logging():
    """Configure logging for the application."""
    # Get the user's home directory
    home_dir = os.path.expanduser('~')
    log_dir = os.path.join(home_dir, 'PDFConverter_logs')
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'pdf_converter_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def check_requirements():
    """Check if all required packages are installed."""
    logger = logging.getLogger(__name__)
    missing_packages = []
    
    # Check PyMuPDF
    try:
        logger.debug("Attempting to import PyMuPDF")
        import fitz
        logger.debug("Successfully imported PyMuPDF")
    except ImportError as e:
        logger.error(f"Failed to import PyMuPDF: {str(e)}")
        missing_packages.append("PyMuPDF")

    # Check Pillow
    try:
        logger.debug("Attempting to import Pillow")
        import PIL
        logger.debug("Successfully imported Pillow")
    except ImportError as e:
        logger.error(f"Failed to import Pillow: {str(e)}")
        missing_packages.append("Pillow")

    # Check pytesseract
    try:
        logger.debug("Attempting to import pytesseract")
        import pytesseract
        logger.debug("Successfully imported pytesseract")
    except ImportError as e:
        logger.error(f"Failed to import pytesseract: {str(e)}")
        missing_packages.append("pytesseract")

    # Check google-generativeai
    try:
        logger.debug("Attempting to import google-generativeai")
        import google.generativeai as genai
        logger.debug("Successfully imported google-generativeai")
        # Test if we can initialize the module
        genai.configure(api_key="test_key")
    except ImportError as e:
        logger.error(f"Failed to import google-generativeai: {str(e)}")
        missing_packages.append("google-generativeai")
    except Exception as e:
        logger.debug(f"Successfully imported google-generativeai but got expected config error: {str(e)}")
    
    return missing_packages

def main():
    """Main entry point of the application."""
    try:
        # Setup logging first
        log_file = setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Application starting...")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Log environment variables
        logger.debug("Environment variables:")
        for key, value in os.environ.items():
            logger.debug(f"{key}: {value}")
        
        # Check requirements
        logger.info("Checking requirements...")
        missing_packages = check_requirements()
        if missing_packages:
            logger.error("Missing required packages: " + ", ".join(missing_packages))
            raise ImportError(f"Missing required packages: {', '.join(missing_packages)}")
        
        # Import gui here to catch any import errors
        logger.info("Importing GUI module...")
        from gui import PDFConverterGUI
        
        # Create and run GUI
        logger.info("Creating GUI...")
        root = tk.Tk()
        app = PDFConverterGUI(root)
        
        logger.info("Starting main loop...")
        app.run()
        
    except Exception as e:
        logger.critical(f"Critical error occurred: {str(e)}")
        logger.critical("Traceback:")
        logger.critical(traceback.format_exc())
        
        # Show error in GUI if possible
        try:
            if 'tk' in sys.modules:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Error", 
                    f"An error occurred. Please check the log file at:\n{log_file}\n\nError: {str(e)}")
        except Exception:
            # If we can't show GUI error, print to console
            print(f"Critical error occurred. Check log file at: {log_file}")
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()