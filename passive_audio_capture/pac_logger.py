import logging
import time
import os


def configure_logging(log_path='logs', log_file='rpi_pac.log'):
    """
    Configures basic logging with timestamp, level and message format.
    Logs will be written to both console and the specified log file.

    Args:
        log_file (str): Path to the log file. Defaults to 'rpi_pac.log'
    """
    timestamp = time.strftime("%Y_%m_%d_%H_%M_%S")

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file = os.path.join(log_path, f"{timestamp}_rpi_pac.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )




