import logging
import re

class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Remove color codes from the log message using a regular expression
        message = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', record.msg)
        return message

def create_logger(log_file_path):
    # Configure the logger to write to both the terminal and a file
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file_path)
    ])

    # Set a custom formatter for the file handler
    file_handler = next(handler for handler in logging.getLogger().handlers if isinstance(handler, logging.FileHandler))
    file_handler.setFormatter(CustomFormatter())
    logging.getLogger("paramiko").setLevel(logging.WARNING)

def close_logger(logger):
    # Find the file handler in the logger's handlers
    file_handler = next((handler for handler in logger.handlers if isinstance(handler, logging.FileHandler)), None)

    if file_handler:
        # Remove the file handler from the logger
        logger.removeHandler(file_handler)

        # Close the file handler
        file_handler.close()
        print("Logger closed.")