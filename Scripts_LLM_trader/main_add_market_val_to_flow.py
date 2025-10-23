from data_gathering.flow_market_add import add_values
import logging
import sys, os  # To make it work no matter where it is executed from

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__": 
    add_values()
    logging.info("Finished adding market values to flows.")