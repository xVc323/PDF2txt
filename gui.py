# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from pathlib import Path
import threading
from queue import Queue, Empty  # Ajoutez Empty ici
import logging
from converter import PDFConverter

class PDFConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Converter with Graph Analysis")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.api_key_var = tk.StringVar()
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.processing = False
        
        # Load saved settings
        self.settings_file = Path.home() / '.pdf_converter_settings.json'
        self.load_settings()
        
        self.setup_ui()
        
        # Processing queue for thread communication
        self.queue = Queue()
        self.process_queue()

    def setup_ui(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # File Selection Frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        main_frame.columnconfigure(0, weight=1)
        
        # Input File/Directory
        ttk.Label(file_frame, text="Input:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Entry(file_frame, textvariable=self.input_path_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(file_frame, text="Browse File", command=lambda: self.browse_path('input', 'file')).grid(row=0, column=2, padx=2)
        ttk.Button(file_frame, text="Browse Dir", command=lambda: self.browse_path('input', 'dir')).grid(row=0, column=3, padx=2)
        
        # Output Directory
        ttk.Label(file_frame, text="Output:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(file_frame, textvariable=self.output_path_var).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(file_frame, text="Browse Dir", command=lambda: self.browse_path('output', 'dir')).grid(row=1, column=2, columnspan=2, padx=2)
        
        file_frame.columnconfigure(1, weight=1)
        
        # API Key Frame
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding="5")
        api_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Label(api_frame, text="Gemini API Key:").grid(row=0, column=0, sticky="w", padx=5)
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*")
        self.api_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(api_frame, text="Show/Hide", command=self.toggle_api_visibility).grid(row=0, column=2, padx=2)
        ttk.Button(api_frame, text="Test API", command=self.test_api).grid(row=0, column=3, padx=2)
        api_frame.columnconfigure(1, weight=1)
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        self.recursive_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Process Subdirectories", variable=self.recursive_var).grid(row=0, column=0, padx=5)
        ttk.Checkbutton(options_frame, text="Overwrite Existing Files", variable=self.overwrite_var).grid(row=0, column=1, padx=5)
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Label(progress_frame, textvariable=self.status_var).grid(row=1, column=0, sticky="w", padx=5)
        progress_frame.columnconfigure(0, weight=1)
        
        # Log Frame
        log_frame = ttk.LabelFrame(main_frame, text="Processing Log", padding="5")
        log_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(4, weight=1)
        
        # Log Text Widget with Scrollbar
        self.log_text = tk.Text(log_frame, height=10, width=50)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(5, 0))
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 5))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Control Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, sticky="ew", pady=5)
        
        ttk.Button(button_frame, text="Start Processing", command=self.start_processing).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_processing).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log).grid(row=0, column=2, padx=5)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

    def toggle_api_visibility(self):
        current_show = self.api_entry.cget('show')
        self.api_entry.configure(show='' if current_show else '*')

    def test_api(self):
        api_key = self.api_key_var.get()
        if not api_key:
            messagebox.showerror("Error", "Please enter an API key")
            return
        
        try:
            converter = PDFConverter(api_key)
            messagebox.showinfo("Success", "API key is valid!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to validate API key: {str(e)}")

    def browse_path(self, path_type, browse_type):
        if browse_type == 'file':
            path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        else:  # directory
            path = filedialog.askdirectory()
            
        if path:
            if path_type == 'input':
                self.input_path_var.set(path)
            else:
                self.output_path_var.set(path)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def log_message(self, message):
        """Add message to log text widget and ensure it's visible."""
        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
                # Force mise à jour immédiate
                self.log_text.update()
                # Debug print
                print(f"GUI Log: {message}")
        except Exception as e:
            print(f"Error in log_message: {e}")


    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.api_key_var.set(settings.get('api_key', ''))
                    self.input_path_var.set(settings.get('input_path', ''))
                    self.output_path_var.set(settings.get('output_path', ''))
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {
                'api_key': self.api_key_var.get(),
                'input_path': self.input_path_var.get(),
                'output_path': self.output_path_var.get()
            }
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def process_file(self, pdf_path, output_path):
        """Process a single PDF file."""
        try:
            if not self.processing:
                return False
            
            def log_callback(message):
                """Callback pour les logs du convertisseur."""
                self.queue.put(('log', message))
                # Print pour debug
                print(f"Callback Log: {message}")
            
            converter = PDFConverter(self.api_key_var.get(), log_callback=log_callback)
            success = converter.convert_pdf(pdf_path, output_path)
            
            if success:
                self.queue.put(('log', f"Successfully processed: {pdf_path}"))
            else:
                self.queue.put(('log', f"Failed to process: {pdf_path}"))
                
            return success
            
        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            self.queue.put(('log', error_msg))
            self.logger.error(error_msg)
            print(f"Process File Error: {error_msg}")  # Debug print
            return False

    def start_processing(self):
        if not all([self.api_key_var.get(), self.input_path_var.get(), self.output_path_var.get()]):
            messagebox.showerror("Error", "Please fill in all required fields")
            return
            
        self.processing = True
        self.progress_var.set(0)
        processing_thread = threading.Thread(target=self._process_files)
        processing_thread.daemon = True
        processing_thread.start()

    def _process_files(self):
        input_path = self.input_path_var.get()
        output_path = self.output_path_var.get()
        
        # Process single file
        if os.path.isfile(input_path):
            self.status_var.set("Processing single file...")
            self.progress_var.set(0)
            
            output_file = os.path.join(output_path, 
                                     os.path.splitext(os.path.basename(input_path))[0] + '.txt')
            
            if os.path.exists(output_file) and not self.overwrite_var.get():
                self.log_message(f"Skipping existing file: {input_path}")
                return
                
            self.process_file(input_path, output_file)
            self.progress_var.set(100)
            
        # Process directory
        else:
            pdf_files = []
            if self.recursive_var.get():
                for root, _, files in os.walk(input_path):
                    for file in files:
                        if file.lower().endswith('.pdf'):
                            pdf_files.append(os.path.join(root, file))
            else:
                pdf_files = [os.path.join(input_path, f) for f in os.listdir(input_path)
                           if f.lower().endswith('.pdf')]
            
            total_files = len(pdf_files)
            if total_files == 0:
                self.log_message("No PDF files found")
                self.status_var.set("No PDF files found")
                return
            
            self.log_message(f"Found {total_files} PDF files to process")
                
            for i, pdf_path in enumerate(pdf_files, 1):
                if not self.processing:
                    self.log_message("Processing cancelled by user")
                    break
                    
                rel_path = os.path.relpath(pdf_path, input_path)
                output_file = os.path.join(output_path, 
                                         os.path.splitext(rel_path)[0] + '.txt')
                
                if os.path.exists(output_file) and not self.overwrite_var.get():
                    self.log_message(f"Skipping existing file: {rel_path}")
                    continue
                
                self.status_var.set(f"Processing {rel_path} ({i}/{total_files})")
                self.progress_var.set((i / total_files) * 100)
                
                self.process_file(pdf_path, output_file)
        
        self.processing = False
        self.status_var.set("Processing complete")

    def cancel_processing(self):
        self.processing = False
        self.queue.put(('status', "Cancelled"))
        self.queue.put(('log', "Processing cancelled by user"))

    def process_queue(self):
        """Process messages from the queue safely."""
        try:
            while True:
                try:
                    msg_type, value = self.queue.get_nowait()
                    if msg_type == 'status':
                        self.status_var.set(value)
                    elif msg_type == 'progress':
                        self.progress_var.set(value)
                    elif msg_type == 'log':
                        # Utiliser after pour mettre à jour les logs
                        self.root.after(0, lambda m=value: self.log_message(m))
                    self.queue.task_done()
                except Empty:  # Utilisez Empty au lieu de Queue.Empty
                    break
        except Exception as e:
            print(f"Error in process_queue: {e}")
        finally:
            # Continuer le traitement de la queue
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(100, self.process_queue)

    def on_closing(self):
        """Handle application closing."""
        self.save_settings()
        # Cancel any ongoing processing
        if hasattr(self, 'processing') and self.processing:
            self.processing = False
            self.queue.put(('status', "Cancelling..."))
            self.queue.put(('log', "Application closing, cancelling current operations..."))
        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Center window on screen
        self.center_window()
        # Start the main loop
        self.root.mainloop()
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')