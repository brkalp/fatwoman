import logging
import os
import datetime
import sys
import socket
from fatwoman_dir_setup import default_log_file_path, logging_override

# Determine the log directory based on the hostname
# log_dir = '\\\\192.168.0.28\\fatwoman\\15GB\\logs\\' if socket.gethostname() == 'ripintheblue' else '/media/fatwoman/15GB/logs/'

class ContextFilter(logging.Filter):
    def filter(self, record):
        # if importer att exists, use it, else use script name
        record.importer = os.path.basename(sys.argv[0])[:-3] if not hasattr(record, 'importer') else record.importer
        # Do not log if log message is about overwriting a file
        if "already exists, will be overwritten." in record.getMessage():
            return False  # Do not log
        return True

class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Ensure 'importer' is always present
        if not hasattr(record, 'importer'):
            record.importer = 'unknown_importer'
        return super(SafeFormatter, self).format(record)

def configure_logging(log_file_path = default_log_file_path):
    logger = logging.getLogger()
    # logger.handlers.clear()
    logger.setLevel(logging.INFO)

    try: importer_name = os.path.basename(sys.argv[0])[:-3]
    except : importer_name = 'importer_name'
    log_file_path = logging_override.get(importer_name, default_log_file_path)

    # Create file handler
    fh = logging.FileHandler(log_file_path)
    fh.setLevel(logging.INFO)

    # Create formatter
    formatter = SafeFormatter('%(asctime)s - %(importer)20s - %(levelname)6s - %(message)s', datefmt='%y%m%d %H:%M:%S')
    fh.setFormatter(formatter)

    # Add ContextFilter
    fh.addFilter(ContextFilter())

    # Add handler to the logger
    logger.addHandler(fh)
    logging_import_ignore = [
        'binance_orderbook_save',
        # 'VIX_Central_Scrape', need seperate file as logging is mandatory, and errors are frequent
        # 'ipykernel_launcher',
        ]
    # if importer_name not in logging_override:
    if not importer_name in logging_import_ignore:
        logging.info("Logging setup complete.")
        print("Script Starting %s" %importer_name)

configure_logging()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    print("Uncaught exception, %s %s %s" %(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

def script_end_log(): # os.path.basename(__file__)
    try: importer_name = os.path.basename(sys.argv[0])
    except : importer_name = 'importer_name'
    logging.info("Script %s Finished" %importer_name)
    print("Script Finished %s" %importer_name)