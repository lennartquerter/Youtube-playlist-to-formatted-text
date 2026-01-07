"""Application entry point and bootstrap."""
import sys
from PyQt5.QtWidgets import QApplication
from dotenv import load_dotenv

from src.ui import MainWindow


def main():
    """Initialize and run the application."""
    # Load environment variables
    load_dotenv(".env")

    # Create Qt application
    app = QApplication(sys.argv)

    # Create and show main window
    window = MainWindow()
    window.showMaximized()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
