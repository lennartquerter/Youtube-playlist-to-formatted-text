"""Main application window."""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QProgressBar, QTextEdit,
                             QFileDialog, QMessageBox, QComboBox, QSlider, QApplication)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from datetime import datetime
import os

from src.config import REFINEMENT_PROMPTS, CATEGORY_CHUNK_SIZES, FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_COLOR, \
    BACKGROUND_COLOR, BORDER_COLOR, ACCENT_COLOR, INPUT_BACKGROUND_COLOR, BUTTON_SUCCESS_2, BUTTON_SUCCESS_1, \
    BUTTON_CANCEL_1, BUTTON_CANCEL_2, INPUT_DISABLED_COLOR
from src.providers import AIProviderFactory
from src.workers import TranscriptExtractionThread, AIProcessingThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        # Load prompts and chunk sizes from config
        self.prompts = REFINEMENT_PROMPTS
        self.category_chunk_sizes = CATEGORY_CHUNK_SIZES
        self.selected_category = "Balanced and Detailed"  # Default Category

        self.extraction_thread = None
        self.gemini_thread = None
        self.is_processing = False
        self.selected_provider = os.environ.get("DEFAULT_AI_PROVIDER", "Gemini")  # Default provider
        self.current_provider = None  # Current provider instance
        self.selected_model_name = os.environ.get("DEFAULT_MODEL", "gemini-3-pro-preview")  # Default model

        self.initUI()

    def get_combobox_style(self):
        return f"""
            QComboBox {{
                background-color: {INPUT_BACKGROUND_COLOR};
                border: 2px solid {BORDER_COLOR};
                border-radius: 5px;
                color: {FONT_COLOR};
                padding: 2px;
                font-size: {FONT_SIZE_BODY}pt;
            }}
            QComboBox:!editable, QComboBox::drop-down:editable {{
                 background: {INPUT_BACKGROUND_COLOR};
            }}

            QComboBox:on {{ /* shift the text when the popup opens */
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;

                border-left-width: 1px;
                border-left-color: {BORDER_COLOR};
                border-left-style: solid; /* just a single line */
                border-top-right-radius: 3px; /* same radius as the QComboBox */
                border-bottom-right-radius: 3px;
            }}

            QComboBox::down-arrow {{
                image: url(down_arrow.png); /* Replace with your arrow image if you want a custom one */
            }}

            QComboBox::down-arrow:on {{ /* shift the arrow when popup is open */
                top: 1px;
                left: 1px;
            }}

            QComboBox QAbstractItemView {{
                border: 2px solid #{BORDER_COLOR};
                border-radius: 5px;
                background-color: #{BACKGROUND_COLOR}/;
                color: #{FONT_COLOR};
                selection-background-color: #{BACKGROUND_COLOR};
                selection-color: #{ACCENT_COLOR};
            }}
        """

    def category_changed(self, index):
        category_name = self.category_combo.itemText(index)  # Get selected category name
        self.selected_category = category_name  # Update selected category
        if category_name in self.category_chunk_sizes:
            suggested_chunk_size = self.category_chunk_sizes[category_name]
            self.chunk_size_slider.setValue(suggested_chunk_size)  # Set slider value
            self.update_chunk_size_label(suggested_chunk_size)  # Update label

    def provider_changed(self, index):
        """Handle AI provider selection change"""
        provider_name = self.provider_combo.itemText(index)
        self.selected_provider = provider_name

        # Update API key label
        self.api_key_label.setText(f"{provider_name} API Key: Loaded from .env")

        # Update model combobox with models for this provider
        temp_provider = AIProviderFactory.create_provider(provider_name, "dummy", "dummy")
        available_models = temp_provider.get_available_models()

        # Clear and repopulate model combobox
        self.model_combo.clear()
        self.model_combo.addItems(available_models)

        # Set the first model as default
        self.selected_model_name = available_models[0]
        self.model_combo.setCurrentText(self.selected_model_name)

    def model_changed(self, index):
        """Handle AI model selection change"""
        model_name = self.model_combo.itemText(index)
        self.selected_model_name = model_name

    def get_api_key_for_provider(self, provider_name):
        """Get API key for specified provider from environment variables"""
        key_mapping = {
            "Gemini": os.environ.get("GEMINI_API_KEY", os.environ.get("API_KEY", "")),  # Backward compatible
            "Claude": os.environ.get("CLAUDE_API_KEY", ""),
            "ChatGPT": os.environ.get("CHATGPT_API_KEY", "")
        }
        return key_mapping.get(provider_name, "")

    @pyqtSlot(int)  # Indicate it's a slot and expects an integer (slider value)
    def update_chunk_size_label(self, value):
        self.chunk_size_value_label.setText(str(value))  # Update the label text with the new slider value

    def initUI(self):

        self.setWindowTitle("YouTube Playlist Transcript & AI Refinement Extractor")
        self.setMinimumSize(900, 850)
        self.apply_dark_mode()
        if os.environ.get("ENTER_FULL_SCREEN", "true") == "true":
            self.showFullScreen()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title Section
        title_label = QLabel("YouTube Playlist Transcript & AI Refinement Extractor")
        title_label.setFont(QFont("Segoe UI", FONT_SIZE_TITLE, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            color: {FONT_COLOR};
            padding: 10px;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #1a0d1f, stop:1 {BORDER_COLOR});
        """)
        main_layout.addWidget(title_label)

        # Input Container
        input_container = QWidget()
        input_container.setStyleSheet(f"background-color: {BACKGROUND_COLOR}; border-radius: 10px; padding: 10px;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setSpacing(1)

        # Playlist URL Input
        url_layout = QVBoxLayout()
        url_label = QLabel("YouTube URL (Playlist or Video):")
        url_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold))
        url_label.setStyleSheet(f"color: {FONT_COLOR};")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Enter YouTube playlist or video URL (e.g., https://www.youtube.com/playlist?list=... or https://www.youtube.com/watch?v=...)")
        self.url_input.setFont(QFont("Segoe UI", FONT_SIZE_BODY))
        self.url_input.setStyleSheet(self.get_input_style())
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        input_layout.addLayout(url_layout)

        # Language Input
        language_layout = QVBoxLayout()
        language_label = QLabel("Output Language:")
        language_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold))
        language_label.setStyleSheet(f"color: {FONT_COLOR};")
        self.language_input = QLineEdit()
        self.language_input.setPlaceholderText("e.g., English, Spanish, French")
        self.language_input.setFont(QFont("Segoe UI", FONT_SIZE_BODY))
        self.language_input.setStyleSheet(self.get_input_style())

        self.language_input.setText(os.environ.get("LANGUAGE", ""))
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_input)
        input_layout.addLayout(language_layout)

        # Style Selection
        category_layout = QVBoxLayout()
        category_label = QLabel("Refinement Style:")
        category_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold))
        category_label.setStyleSheet(f"color: {FONT_COLOR};")
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.prompts.keys()))
        self.category_combo.setCurrentText(self.selected_category)
        self.category_combo.currentIndexChanged.connect(self.category_changed)
        self.category_combo.setStyleSheet(self.get_combobox_style())
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        input_layout.addLayout(category_layout)

        # AI Provider Selection
        provider_layout = QVBoxLayout()
        provider_label = QLabel("AI Provider:")
        provider_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold))
        provider_label.setStyleSheet(f"color: {FONT_COLOR};")

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Gemini", "Claude", "ChatGPT"])

        self.provider_combo.setCurrentText(self.selected_provider)
        self.provider_combo.currentIndexChanged.connect(self.provider_changed)
        self.provider_combo.setStyleSheet(self.get_combobox_style())

        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        input_layout.addLayout(provider_layout)

        # AI Model Selection
        model_layout = QVBoxLayout()
        model_label = QLabel("AI Model:")
        model_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold))
        model_label.setStyleSheet(f"color: {FONT_COLOR};")

        self.model_combo = QComboBox()
        # Populate with models for the default provider
        temp_provider = AIProviderFactory.create_provider(self.selected_provider, "dummy", "dummy")
        available_models = temp_provider.get_available_models()
        self.model_combo.addItems(available_models)
        self.model_combo.setCurrentText(self.selected_model_name)
        self.model_combo.currentIndexChanged.connect(self.model_changed)
        self.model_combo.setStyleSheet(self.get_combobox_style())

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        input_layout.addLayout(model_layout)

        # Chunk Size Slider Section
        chunk_size_layout = QVBoxLayout()

        chunk_size_layout.setSpacing(2)
        chunk_size_layout.setContentsMargins(5, 5, 5, 5)

        chunk_size_label = QLabel("Chunk Size:")
        chunk_size_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold))
        chunk_size_label.setStyleSheet(f"color: {FONT_COLOR}; margin-bottom: 4px;")
        chunk_size_layout.addWidget(chunk_size_label)

        self.chunk_size_slider = QSlider(Qt.Horizontal)
        self.chunk_size_slider.setMinimum(2000)
        self.chunk_size_slider.setMaximum(50000)
        self.chunk_size_slider.setValue(AIProcessingThread.chunk_size)
        self.chunk_size_slider.valueChanged.connect(self.update_chunk_size_label)
        self.chunk_size_slider.setStyleSheet("""
            QSlider {
                padding: 0px;  # Reduced padding
            }
            QSlider::groove:horizontal {
                height: 4px;
                margin: 2px 0;  # Add vertical margin
            }
            QSlider::handle:horizontal {
                width: 12px;
                margin: -6px 0px;
            }
        """)
        chunk_size_layout.addWidget(self.chunk_size_slider)

        self.chunk_size_value_label = QLabel(str(AIProcessingThread.chunk_size))
        self.chunk_size_value_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY))
        self.chunk_size_value_label.setStyleSheet(f"color: {FONT_COLOR}; margin-top: 4px;")
        chunk_size_layout.addWidget(self.chunk_size_value_label)

        chunk_size_description = QLabel(
            "(Maximum number of words to be given to the AI provider as content input per API call)"
            "(Default : 3000 words) Bigger chunk size: Fewer API calls, faster execution."
            "Potentially lower detail (good for summarizing longer videos).")
        chunk_size_description.setFont(QFont("Segoe UI", FONT_SIZE_BODY))
        chunk_size_description.setStyleSheet(f"""
            color: {ACCENT_COLOR};
            margin-top: 18px;  
            padding: 2px;
        """)
        chunk_size_description.setWordWrap(True)
        chunk_size_layout.addWidget(chunk_size_description)

        input_layout.addLayout(chunk_size_layout)

        # File Inputs
        self.create_file_input(input_layout, "   Transcript Output:", "Choose File",
                               "transcript_file_input", self.select_transcript_output_file)
        self.create_file_input(input_layout, "   AI Output:", "Choose File",
                               "gemini_file_input", self.select_gemini_output_file)

        # Set default output file paths from environment variables
        self.transcript_file_input.setText(os.environ.get("DEFAULT_TRANSCRIPT_OUTPUT", "./transcript_output.txt"))
        self.gemini_file_input.setText(os.environ.get("DEFAULT_AI_OUTPUT", "./ai_refined_output.md"))

        # API Key Label (keys are loaded from .env)
        api_key_layout = QVBoxLayout()
        self.api_key_label = QLabel(f"{self.selected_provider} API Key: Loaded from .env")
        self.api_key_label.setFont(QFont("Segoe UI", FONT_SIZE_BODY))
        self.api_key_label.setStyleSheet(f"color: {FONT_COLOR};")  # Secondary text color
        api_key_layout.addWidget(self.api_key_label)
        input_layout.addLayout(api_key_layout)

        main_layout.addWidget(input_container)

        # Progress Section
        progress_container = QWidget()
        progress_container.setStyleSheet(f"background-color: {BACKGROUND_COLOR}; border-radius: 10px; padding: 10px;")
        progress_layout = QVBoxLayout(progress_container)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {ACCENT_COLOR};
                border: 2px solid {BORDER_COLOR};
                border-radius: 5px;
                text-align: center;
                color: white;
                font-size: {FONT_SIZE_BODY}px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT_COLOR}, stop:1 #a855f7);
                border-radius: 3px;
            }}
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status Display
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setStyleSheet(f"""
            background-color: {INPUT_BACKGROUND_COLOR};
            border: 2px solid {BORDER_COLOR};
            border-radius: 5px;
            color: {FONT_COLOR};
            font-size: {FONT_SIZE_BODY}px;
            padding: 8px;
        """)
        progress_layout.addWidget(self.status_display)
        main_layout.addWidget(progress_container)

        # Control Buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)

        self.extract_button = QPushButton("Start Processing")
        self.extract_button.setStyleSheet(self.get_button_style(BUTTON_SUCCESS_1, BUTTON_SUCCESS_2))
        self.extract_button.clicked.connect(self.start_extraction_and_refinement)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet(self.get_button_style(BUTTON_CANCEL_1, BUTTON_CANCEL_2))
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.cancel_button.setEnabled(False)

        control_layout.addStretch(1)
        control_layout.addWidget(self.extract_button)
        control_layout.addWidget(self.cancel_button)
        control_layout.addStretch(1)
        main_layout.addLayout(control_layout)

        self.central_widget.setLayout(main_layout)
        self.center()

    def create_file_input(self, parent_layout, label_text, button_text, field_name, handler):
        layout = QHBoxLayout()

        input_field = QLineEdit()
        input_field.setObjectName(field_name)
        input_field.setReadOnly(True)
        input_field.setPlaceholderText(f"Select {label_text.split(':')[0]} file")
        input_field.setStyleSheet(self.get_input_style())

        button = QPushButton(button_text)
        button.setStyleSheet(self.get_button_style(BUTTON_SUCCESS_1, BUTTON_SUCCESS_2))
        button.clicked.connect(handler)

        layout.addWidget(input_field)
        layout.addWidget(button)

        font = QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold)
        label = QLabel(label_text)
        font = QFont("Segoe UI", FONT_SIZE_BODY, QFont.Bold)  # Family, size, weight
        label.setFont(font)

        label.setStyleSheet("padding: 0px;")

        parent_layout.addWidget(label)
        parent_layout.addLayout(layout)

        setattr(self, field_name, input_field)

    def get_input_style(self):
        return f"""
            QLineEdit {{
                background: {BACKGROUND_COLOR};
                border: 2px solid {BORDER_COLOR};
                border-radius: 5px;
                color: {FONT_COLOR};
                padding: 2px;
            }}
            QLineEdit:disabled {{
                background: {INPUT_BACKGROUND_COLOR};
                border-color: {INPUT_DISABLED_COLOR};
            }}
        """

    def get_button_style(self, color1, color2):
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color1}, stop:1 {color2});
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px 24px;
                font-size: {FONT_SIZE_BODY}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color2}, stop:1 {color1});
            }}
            QPushButton:disabled {{
                background: {INPUT_BACKGROUND_COLOR};
                color: {INPUT_DISABLED_COLOR};
            }}
        """

    def apply_dark_mode(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BACKGROUND_COLOR};
            }}
            QLabel {{
                color: {FONT_COLOR};
            }}
        """)

    def center(self):
        frame = self.frameGeometry()
        center_point = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())

    def validate_inputs(self):
        url_text = self.url_input.text()

        if not (url_text.startswith("https://www.youtube.com/playlist") or
                url_text.startswith("https://www.youtube.com/watch?v=")):
            msg_box = QMessageBox()
            msg_box.setStyleSheet(f"color: {FONT_COLOR}; background-color: {BACKGROUND_COLOR};")  # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please enter a valid YouTube playlist URL")
            msg_box.setWindowTitle("Invalid URL")
            msg_box.exec_()
            return False

        if not self.transcript_file_input.text().endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet(f"color: {FONT_COLOR}; background-color: {BACKGROUND_COLOR};")  # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Transcript output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        if not self.gemini_file_input.text().endswith(".txt"):
            msg_box = QMessageBox()
            msg_box.setStyleSheet(f"color: {FONT_COLOR}; background-color: {BACKGROUND_COLOR};")  # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("AI output file must be a .txt file")
            msg_box.setWindowTitle("Invalid File")
            msg_box.exec_()
            return False

        # Check if API key exists in environment for selected provider
        api_key = self.get_api_key_for_provider(self.selected_provider)
        if not api_key.strip():
            msg_box = QMessageBox()
            msg_box.setStyleSheet(f"color: {FONT_COLOR}; background-color: {BACKGROUND_COLOR};")  # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText(f"Please set {self.selected_provider.upper()}_API_KEY in your .env file")
            msg_box.setWindowTitle("API Key Required")
            msg_box.exec_()
            return False

        if not self.language_input.text().strip():  # Validate Language Input
            msg_box = QMessageBox()
            msg_box.setStyleSheet(f"color: {FONT_COLOR}; background-color: {BACKGROUND_COLOR};")  # Style QMessageBox
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("Please specify the output language")
            msg_box.setWindowTitle("Language Required")
            msg_box.exec_()
            return False

        return True

    def set_processing_state(self, processing):
        self.is_processing = processing
        self.extract_button.setEnabled(not processing)
        self.cancel_button.setEnabled(processing)

        inputs = [self.url_input, self.transcript_file_input,
                  self.gemini_file_input, self.language_input]
        for input_field in inputs:
            input_field.setReadOnly(processing)

    def select_ai_model(self):
        # Get current provider
        provider_name = self.selected_provider

        # Create temp provider instance to get available models
        temp_provider = AIProviderFactory.create_provider(provider_name, "dummy", "dummy")
        available_models = temp_provider.get_available_models()

        msg_box = QMessageBox()
        msg_box.setStyleSheet(
            f"color: {FONT_COLOR}; background-color: {BACKGROUND_COLOR};")  # Updated style for new color scheme
        msg_box.setWindowTitle(f"Select {provider_name} Model")
        msg_box.setText(f"Choose a {provider_name} model for refinement:")

        model_combo = QComboBox()
        model_combo.addItems(available_models)
        model_combo.setCurrentText(self.selected_model_name)

        layout = QVBoxLayout()
        layout.addWidget(model_combo)
        widget = QWidget()
        widget.setLayout(layout)
        msg_box.layout().addWidget(widget, 1, 0, msg_box.layout().rowCount(), 1)

        ok_button = msg_box.addButton(QMessageBox.Ok)
        cancel_button = msg_box.addButton(QMessageBox.Cancel)

        msg_box.exec_()

        if msg_box.clickedButton() == ok_button:
            return model_combo.currentText()
        else:
            return None

    def start_extraction_and_refinement(self):
        if not self.validate_inputs():
            return

        # Model is already selected from the UI combobox
        # self.selected_model_name is set by model_changed() method

        self.set_processing_state(True)
        self.progress_bar.setValue(0)
        self.status_display.clear()

        transcript_output = self.transcript_file_input.text() or \
                            f"transcript_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"

        self.extraction_thread = TranscriptExtractionThread(
            self.url_input.text(),
            transcript_output
        )

        self.extraction_thread.progress_update.connect(self.progress_bar.setValue)
        self.extraction_thread.status_update.connect(self.update_status)
        self.extraction_thread.extraction_complete.connect(self.start_ai_processing)
        self.extraction_thread.error_occurred.connect(self.handle_error)

        self.status_display.append("<font color='#c74b94'>Starting transcript extraction...</font>")
        self.extraction_thread.start()

    def start_ai_processing(self, transcript_file):
        self.progress_bar.setValue(0)  # Reset progress bar for AI processing
        self.status_display.append(
            f"<font color='#d946ef'>Transcript extraction complete! Starting {self.selected_provider} processing...</font>")

        output_language = self.language_input.text()  # Get language from input field
        current_chunk_size = self.chunk_size_slider.value()
        selected_prompt = self.prompts[self.selected_category]
        self.gemini_thread = AIProcessingThread(
            transcript_file,
            self.gemini_file_input.text(),
            self.get_api_key_for_provider(self.selected_provider),
            self.selected_model_name,  # Pass selected model name
            output_language,  # Pass output language
            chunk_size=current_chunk_size,
            prompt=selected_prompt,
            provider_name=self.selected_provider  # Pass provider name
        )

        self.gemini_thread.progress_update.connect(
            self.update_gemini_progress)  # Use separate progress update for AI processing
        self.gemini_thread.status_update.connect(self.update_status)
        self.gemini_thread.processing_complete.connect(self.handle_success)
        self.gemini_thread.error_occurred.connect(self.handle_error)

        self.gemini_thread.start()

    def update_gemini_progress(self, progress_percent):
        # Offset the progress bar to start after extraction (assuming extraction takes up to 50%)

        gemini_progress = progress_percent
        self.progress_bar.setValue(gemini_progress)

    def update_status(self, message):
        color = "#c74b94" if "extraction" in message else "#d946ef"
        self.status_display.append(f"<font color='{color}'>{message}</font>")

    def handle_success(self, output_file):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")  # Style QMessageBox
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f"Processing complete!\nOutput saved to: {output_file}")
        msg_box.setWindowTitle("Success")
        msg_box.exec_()
        self.progress_bar.setValue(100)

    def handle_error(self, error):
        self.set_processing_state(False)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("color: #ecf0f1; background-color: #34495e;")  # Style QMessageBox
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(error)
        msg_box.setWindowTitle("Error")
        msg_box.exec_()
        self.progress_bar.setValue(0)

    def cancel_processing(self):
        if self.extraction_thread and self.extraction_thread.isRunning():
            self.extraction_thread.stop()
            self.extraction_thread.quit()
            self.extraction_thread.wait()

        if self.gemini_thread and self.gemini_thread.isRunning():
            self.gemini_thread.stop()
            self.gemini_thread.quit()
            self.gemini_thread.wait()

        self.set_processing_state(False)
        self.status_display.append("<font color='#f472b6'>Processing cancelled by user</font>")
        self.progress_bar.setValue(0)

    def select_transcript_output_file(self):
        self.select_output_file("Select Transcript Output File", self.transcript_file_input)

    def select_gemini_output_file(self):
        self.select_output_file("Select AI Output File", self.gemini_file_input)

    def select_output_file(self, title, field):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, title, "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            if not (file_path.endswith(".txt")):
                file_path += ".txt"  # Default to .txt if no extension is given
            field.setText(file_path)
