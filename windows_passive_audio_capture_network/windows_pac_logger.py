import logging

def configure_logging(log_file='windows_pac.log'):
    """
    Configures basic logging with timestamp, level and message format.
    Logs will be written to both console and the specified log file.

    Args:
        log_file (str): Path to the log file. Defaults to 'windows_pac.log'
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )




