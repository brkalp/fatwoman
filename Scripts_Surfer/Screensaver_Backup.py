""" Created on Sun Jul 23 13:42:59 2023 @author: ripintheblue """
print('\nStarting Screensaver ' + time.strftime("%Y-%m-%d %H:%M:%S"))
import fatwoman_log_setup
from fatwoman_dir_setup import Screensaver_url_dir as url_dir
from fatwoman_dir_setup import CNFG_FILE1, CNFG_FILE2
from fatwoman_dir_setup import firefox_profile1, firefox_profile2
import logging
import time
import os
import signal
import sys
from selenium import webdriver
import pandas as pd
NAME = 'Title'
SCRL = 'ScrollAmount'
WAIT = 'Waittime'
URL  = 'URL'
#folder_data_yfinance = r'C:\Data\yfinance\\' if socket.gethostname() == 'ripintheblue' else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yfinance') + '/'

import socket
# url_dir = r'\\192.168.0.28\fatwoman\15GB\Scripts_Screensaver\\' if socket.gethostname() == 'ripintheblue' else r'/media/fatwoman/15GB/Scripts_Screensaver/'
# CNFG_FILE1 = url_dir + r'URLS_1.csv'
# CNFG_FILE2 = url_dir + r'URLS_2.csv'

def signal_handler(signum, frame):
    print("Gracefully shutting down... " + time.strftime("%Y-%m-%d %H:%M:%S"))
    try:
        if driver1 is not None:
            driver1.quit()
        if driver2 is not None:
            driver2.quit()
    except Exception as e:
        print(f"Error in closing drivers: {e}")
    finally:
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_firefox_driver(profile_path, window_position, i):
    print('Loading Options %i' %i)
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("-profile")
    firefox_options.add_argument(profile_path)
    driver = webdriver.Firefox(options=firefox_options)
    driver.set_window_position(*window_position)
    return driver

def read_configs(CNFG_PATH, configs, previous_size):
    # new_size = os.stat(CNFG_PATH).st_size
    new_size = len(pd.read_csv(CNFG_PATH))
    if configs is None or new_size != previous_size:
        print(f'Reading config from {CNFG_PATH}')
        logging.info(f'Reading config from {CNFG_PATH}')
        configs = pd.read_csv(CNFG_PATH)
    return configs, new_size

def counters(maincounter, url_counter, configfilesize):
    maincounter = maincounter + 1
    url_counter = maincounter % configfilesize
    return url_counter

def load_url(driver, config, i, screennumber):
    print(f"Loading %i: %3i: {config[NAME]}" %(screennumber, i))
    driver.get(config[URL])

driver1 = load_firefox_driver(firefox_profile1, (100, 100), 1)
driver2 = load_firefox_driver(firefox_profile2, (1300, 100), 2)
print('Options Loaded')

filesize1, filesize2, j, k = 0,0,0,0 # j first, k is second counter
configs1, configs2 = None, None
i = -2 # main counter
while 5>0:
    try:
        if i<1: 
            driver1.fullscreen_window()
            driver2.fullscreen_window()
        configs1, filesize1 = read_configs(CNFG_FILE1, configs1, filesize1)
        configs2, filesize2 = read_configs(CNFG_FILE2, configs2, filesize2)
        time.sleep(1)
        # print('Getting, %i' %i)

        i = i + 1
        j = counters(i, j, filesize1)
        k = counters(i, k, filesize2)
        # print('%5i %5i %5i' %(i,j,filesize1))
        # print('%5i %5i %5i' %(i,k,filesize2))
        
        load_url(driver1, configs1.iloc[j,:], i, 1)
        time.sleep(1)
        load_url(driver2, configs2.iloc[k,:], i, 2)
        # print('sleep')
        time.sleep(15)
        sleeptime = (configs1.loc[j,WAIT] + configs2.loc[k,WAIT]) / 2
        time.sleep(sleeptime)

        # print('Get finish\n')
    except Exception as e:
        logging.info(configs1.iloc[j,:][URL])
        logging.info(configs2.iloc[k,:][URL])
        print(e)
        time.sleep(5)

script_end_log()