# PDF2txt

PDF2txt is a Python-based PDF conversion tool featuring an intuitive graphical interface. It extracts text and images from PDF files and performs image analysis using a generative AI model. The application is designed for ease-of-use in a desktop environment.

## Features

* PDF Text Extraction: Extracts text from PDF files.
* Image Extraction & Analysis: Retrieves images from PDFs and analyzes them using a generative AI model to provide insights.
* Graphical User Interface: A simple and interactive GUI built with Tkinter for file selection, API key configuration, and real-time logging.
* Settings Persistence: Automatically saves and loads user settings.
* Multi-File Processing: Process individual PDF files or entire directories, with the option to scan subdirectories recursively.
* Progress Tracking: Displays a visual progress bar and detailed logs during processing.

## Requirements

* Python: Version 3.7 or higher

## Python Dependencies

Install the following Python libraries using pip:

```bash
pip install Pillow
pip install google-generativeai
pip install numpy
pip install pymupdf
```

Note: Tkinter is typically included with Python. If it's not available, refer to your operating system's installation instructions.

## Installation

1. Clone the Repository:
   ```bash
   git clone https://github.com/yourusername/PDF2txt.git
   cd PDF2txt
   ```

2. Set Up a Virtual Environment (Optional but Recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   If you do not have a requirements.txt file, create one with the necessary packages listed above.

## Usage

To launch the application, simply run:

```bash
python main.py
```

This command will open the graphical interface, where you can:

* Select an Input File or Directory: Browse for a PDF file or choose a directory containing PDFs.
* Choose an Output Directory: Specify where the converted text files should be saved.
* Configure the API Key: Enter your API key for enabling image analysis.
* Start Processing: Click "Start Processing" to begin converting PDFs. The progress bar and log window will update in real time.
* Cancel or Clear Logs: Use the provided buttons to cancel ongoing processes or clear the log window.

## Changing the Generative AI Model

To change the generative AI model used by PDF2txt:

1. Locate the Model Configuration:
   Open the converter.py file and locate the setup_gemini method inside the PDFConverter class.

2. Update the Model Identifier:
   Find the following line in the method:
   ```python
   self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
   ```
   Replace 'gemini-2.0-flash-exp' with the identifier of the new generative AI model you wish to use. For example:
   ```python
   self.model = genai.GenerativeModel('new-model-identifier')
   ```

3. Adjust API Parameters if Needed:
   * Consult the new model's documentation
   * If the model requires additional configuration (such as different endpoints or headers), update the relevant sections in the setup_gemini method or within a dedicated configuration file

4. Test Your Changes:
   Run the application to ensure that the new model initializes properly and that image analysis functions as expected.

## Code Overview

* **main.py**: The entry point of the application. Running this file launches the GUI.
* **gui.py**: Contains the Tkinter-based user interface, managing file selection, API key configuration, logging, and progress tracking.
* **converter.py**: Implements the logic for converting PDFs to text, extracting images, and performing image analysis with the generative AI model. This is also where you can modify the generative AI model settings.

## Contributing

Contributions are welcome! If you find issues or have suggestions for improvements, please open an issue or submit a pull request on GitHub.

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes:
   ```bash
   git commit -am 'Add new feature'
   ```
4. Push to your branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgments

* Thanks to the open-source community for the libraries and tools used in this project.
* Special thanks to the contributors of PyMuPDF, Pillow, and the generative AI libraries.