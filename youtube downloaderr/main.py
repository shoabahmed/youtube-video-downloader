from ui.app import App
from utils.logger import setup_logger
import sys

# Setup logging
logger = setup_logger()

def main():
    logger.info("Application starting...")
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
