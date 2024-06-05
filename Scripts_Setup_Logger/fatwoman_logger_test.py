# test_logging.py
import fatwoman_log_setup 
import logging

print('Nothing')
# Now you can use logging to log messages
logging.info("This is an info message.")
logging.warning("This is a warning message.")
logging.error("This is an error message.")
logging.debug("This is a debug message - might not appear by default due to log level settings.")
logging.critical("This is a critical message.")

1 / 0
print("Logging example complete. Check the log file for messages.")
